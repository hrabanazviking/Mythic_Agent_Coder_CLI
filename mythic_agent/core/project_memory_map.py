"""Project Memory Map (All-Features roadmap slice M-150).

Part VII continues. The roadmap's words:
``every project grows a living map - architecture,
decisions, gotchas, where things live - maintained
by the Scribe as work proceeds, diffs reviewable.``

What already shipped, and what this slice adds:

* The map itself already lives in this repo as a
  convention: ``PROJECT_MEMORY_MAP.md`` at the repo
  root - a living markdown map, seeded 2026-10-30,
  kept by the Scribe's discipline (Mythic law: the
  map is updated in the same session as each banked
  slice), under the headings ``What this is``,
  ``Where things live``, ``The two roads``,
  ``Working facts & gotchas`` and ``Campaign
  state``. The method charter (M-005,
  ``core/method_charter.py``) already carries the
  law as its F-03 plug, ``PROJECT_MEMORY_MAP``:
  identity, architecture, canonical paths,
  contracts, capabilities, limits, decisions -
  updated in the same session as the change it
  records. What nothing holds is the map as
  validated DATA: one canon of the sections a map
  entry may stand in, a panel derived from the
  whole map in a settled order (so two panels of
  the same map diff cleanly, reviewably), and a
  registry the Scribe's session work can hold.
* This slice is that canon, as a pure layer: a
  map entry validated as data (one fact of the
  map - its section in the closed set this slice
  names, its title, the fact itself in plain
  words, its source, and the reference where the
  thing it names lives), a book holding entries
  in held order, a panel DERIVED from the entries
  (every entry carried whole, in map order, its
  totals the entries' own counts), the shipped
  data file
  (``mythic_agent/data/project_memory_map.yaml``)
  holding one example book in exactly the shape a
  real book file takes, a loader for a book file
  anywhere on disk, a scan road that reads a real
  workspace's ``PROJECT_MEMORY_MAP.md`` convention
  file and turns its headings into entries, the
  Scribe's own charter directives read off the
  shipped method charter BY IMPORT, records shaped
  as session news, and a small in-memory registry
  model. The agent layer owns holding a book for
  a session.

Honesty rules, enforced here and pinned by tests:

* **The Scribe keeps the map.** The panel's
  keeper is always the Scribe - the shipped
  casting's memory & docs office - and a panel
  naming any other keeper refuses. The map is
  maintained as work proceeds: this layer records
  the map as data; it does not itself do the
  work the map describes.
* **The panel is derived, never stored loose.**
  Its rows are the entries carried whole, sorted
  into map order (section first, in the order
  :data:`MAP_SECTIONS` names - architecture,
  decision, gotcha, location - then title), so
  two panels of one map stand in the same order
  and their diff is reviewable line by line. A
  stored panel whose rows, totals, counts,
  keeper or account disagree with the panel
  derived from its entries refuses.
* **Sections are a closed set.** An entry stands
  in exactly one of the roadmap's own sections -
  architecture, decision, gotcha, location
  (where things live). The shipped markdown map's
  headings compose onto those sections through
  :data:`MAP_SECTION_HEADINGS`, never a second
  taxonomy.
* **Data only - holding a map writes no project
  file.** An entry here is a validated record
  held as data, and a panel is that account read
  off the entries: no project file is written,
  edited or moved by this layer, and scanning a
  workspace's convention file reads it and leaves
  every file byte-identical. Holding a map
  persists nothing.
* **Malformed refuses.** A duplicate entry id in
  one book, the same title named twice in one
  section, a section outside the closed set, and
  unknown keys in an entry, a row, a panel or a
  book mapping all raise instead of being skipped
  or guessed at.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..resources import load_resource
from .crew_members import normalize_member_id
from .method_charter import load_charter
from .validation import ValidationError

__all__ = [
    "PLAIN_EXPLANATION",
    "PROJECT_MEMORY_MAP_RESOURCE",
    "PROJECT_MEMORY_MAP_SCHEMA",
    "PROJECT_MEMORY_MAP_SLICE",
    "MAP_KEEPER",
    "MAP_SECTIONS",
    "MAP_SECTION_HEADINGS",
    "USAGE",
    "MemoryMapBook",
    "MemoryMapEntry",
    "MemoryMapPanel",
    "MemoryMapPanelRow",
    "MemoryMapRegistry",
    "MemoryMapSectionCount",
    "book_record",
    "build_book",
    "build_entry",
    "build_panel",
    "build_row",
    "derive_panel",
    "entry_record",
    "format_entries",
    "format_entry",
    "format_panel",
    "format_project_memory_map_screen",
    "load_project_memory_map",
    "load_project_memory_map_file",
    "normalize_section",
    "panel_plain_words",
    "panel_record",
    "parse_memory_map_args",
    "plain_words",
    "scan_workspace",
    "scribe_directives",
    "validate_book",
    "validate_entry",
    "validate_panel",
    "validate_row",
]

PROJECT_MEMORY_MAP_SLICE = "M-150"

#: The packaged data resource holding the example book.
PROJECT_MEMORY_MAP_RESOURCE = "project_memory_map.yaml"

#: The schema word a project-memory-map file must carry.
PROJECT_MEMORY_MAP_SCHEMA = "mythic.project_memory_map/1"

#: The sections one map entry may stand in, in map
#: order: the roadmap's own four - architecture,
#: decisions, gotchas, and where things live
#: (locations). Panel rows stand in this order.
MAP_SECTIONS = ("architecture", "decision", "gotcha", "location")

#: The shipped markdown map's own headings, composed
#: onto the closed sections: ``PROJECT_MEMORY_MAP.md``
#: at a repo root is the convention this slice holds
#: as data, and its headings are its sections' faces.
MAP_SECTION_HEADINGS = {
    "What this is": "architecture",
    "Where things live": "location",
    "The two roads (both binding)": "architecture",
    "Working facts & gotchas": "gotcha",
    "Campaign state": "decision",
}

#: The map's keeper: the Scribe, the shipped
#: casting's memory & docs office, named by this
#: slice's roadmap words ("maintained by the
#: Scribe"). A panel kept by anyone else refuses.
MAP_KEEPER = "Scribe"

_ENTRY_KEYS = frozenset({
    "entry_id", "id", "section", "kind",
    "title", "name", "detail", "body",
    "source", "ref", "path", "reference",
})

_ROW_KEYS = frozenset({
    "entry_id", "id", "section", "title",
    "source", "ref", "path",
})

_SECTION_COUNT_KEYS = frozenset({
    "section", "entries", "count",
})

_PANEL_KEYS = frozenset({
    "panel_id", "id", "rows", "entries",
    "total_entries", "total", "section_counts", "sections",
    "account", "statements", "keeper",
})

_BOOK_KEYS = frozenset({"title", "name"})

_PROJECT_MEMORY_MAP_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "canon_note", "guide", "entries", "panels",
})

#: Plural and face spellings of the closed sections,
#: read onto their canonical singular words.
_SECTION_ALIASES = {
    "architecture": "architecture",
    "decision": "decision",
    "decisions": "decision",
    "gotcha": "gotcha",
    "gotchas": "gotcha",
    "location": "location",
    "locations": "location",
    "where-things-live": "location",
}

#: The shipped example book's title, held to this
#: by the loader's example check.
_EXAMPLE_TITLE = "Project memory map at the M-149 slice boundary"

#: The shipped example's entry ids, in held order,
#: pinned by the loader.
_EXAMPLE_ENTRY_IDS = (
    "map-package", "map-agents", "map-tests",
    "map-two-roads", "map-offices", "map-ci-manual",
    "map-scribe-law", "map-no-docker", "map-suite-extras")

#: The shipped example's entry sections, in held
#: order, pinned by the loader.
_EXAMPLE_SECTIONS = (
    "location", "location", "location",
    "architecture", "architecture", "decision",
    "decision", "gotcha", "gotcha")

#: The shipped example's one panel id, and its rows
#: in map order, pinned by the loader.
_EXAMPLE_PANEL_ID = "panel-m149-boundary"

_EXAMPLE_PANEL_ROW_IDS = (
    "map-offices", "map-two-roads", "map-ci-manual",
    "map-scribe-law", "map-no-docker", "map-suite-extras",
    "map-agents", "map-package", "map-tests")

_EXAMPLE_PANEL_ACCOUNT = (
    "The panel holds 9 project memory map entries: "
    "architecture 2, decision 2, gotcha 2, location 3.",
    "Sections stand in map order (architecture, then "
    "decision, then gotcha, then location) and, inside "
    "one section, by title - so two panels of the same "
    "map diff cleanly, line by line.",
    "The Scribe keeps this map as work proceeds: the "
    "map is updated in the same session as the work it "
    "records, never as a later chore.",
    "The panel is read off the held entries at "
    "call time - it is derived, never stored "
    "loose.",
)

PLAIN_EXPLANATION = (
    "Project Memory Map (Mythic law): every project "
    "grows a living map - architecture, decisions, "
    "gotchas, where things live - maintained by the "
    "Scribe as work proceeds, diffs reviewable. An "
    "entry names one fact of the map: its section in "
    "the closed set this slice names (architecture, "
    "decision, gotcha, location), its title, the fact "
    "itself in plain words, its source, and the "
    "reference where the thing it names lives. The "
    "panel is derived from the whole book - its rows "
    "the entries carried whole, in map order (section "
    "first, then title), and its totals the entries' "
    "own counts - so a stored panel that disagrees "
    "refuses, and two panels of the same map diff "
    "cleanly. The shipped PROJECT_MEMORY_MAP.md "
    "convention is composed, not duplicated: its "
    "headings stand as the sections' faces, and the "
    "Scribe's directives are read off the shipped "
    "method charter's PROJECT_MEMORY_MAP plug. This "
    "layer holds the map as data only: it writes and "
    "edits no project file, and persists nothing."
)

USAGE = (
    "Usage: /memorymap, /memorymap show, "
    "/memorymap entry <entry-id>, "
    "/memorymap section <section>, "
    "/memorymap panel"
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


def normalize_section(value: Any) -> str:
    """The canonical map section a word names.

    A section is one of :data:`MAP_SECTIONS` -
    ``architecture``, ``decision``, ``gotcha`` or
    ``location`` - read case-insensitively, with the
    roadmap's plural faces (``decisions``,
    ``gotchas``, ``locations``) read onto their
    canonical words. Anything else raises, plainly
    naming the four.
    """
    if isinstance(value, str):
        wanted = _SECTION_ALIASES.get(value.strip().lower())
        if wanted is not None:
            return wanted
    raise ValueError(
        "a map section must be one of %s, got %r"
        % ("/".join(MAP_SECTIONS), value))


def _check_ref(value: Any) -> str:
    text = _clean_text(value, "a map entry's reference")
    if len(text) > 300 or "\x00" in text:
        raise ValueError(
            f"a map entry's reference must be plain text "
            f"of at most 300 characters, got {len(text)} characters")
    if any(ch.isspace() for ch in text):
        raise ValueError(
            f"a map entry's reference names no spaces, "
            f"got {text!r}")
    return text


# ---------------------------------------------------------------------
# The entry: one fact of the living map, as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class MemoryMapEntry:
    """One fact of the project's living map, as a validated record.

    ``section`` is the entry's section in the closed
    set this slice names; ``title`` names the fact;
    ``detail`` is the fact itself, in plain words;
    ``source`` names where the entry was read from;
    ``ref`` is where the thing the entry names lives
    (a path, a file, a heading - the entry's answer
    to "where does it live"). The record is a map
    fact held as data: it describes the project, it
    does not change it.
    """

    section: str
    title: str
    detail: str
    source: str
    ref: str
    entry_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.entry_id is not None:
            object.__setattr__(
                self, "entry_id",
                normalize_member_id(self.entry_id))
        object.__setattr__(
            self, "section", normalize_section(self.section))
        object.__setattr__(
            self, "title", _check_title(self.title, "an entry's title"))
        object.__setattr__(
            self, "detail",
            _check_long_text(self.detail, "an entry's detail"))
        object.__setattr__(
            self, "source",
            _check_title(self.source, "an entry's source"))
        object.__setattr__(self, "ref", _check_ref(self.ref))

    @property
    def section_index(self) -> int:
        """This entry's section's place in map order (derived)."""
        return MAP_SECTIONS.index(self.section)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "project_memory_map_entry",
            "slice": PROJECT_MEMORY_MAP_SLICE,
            "entry_id": self.entry_id,
            "section": self.section,
            "title": self.title,
            "detail": self.detail,
            "source": self.source,
            "ref": self.ref,
        }


def validate_entry(entry: Any) -> MemoryMapEntry:
    """Validate one entry record into a MemoryMapEntry.

    Accepts an entry or a mapping naming a ``section``
    (or ``kind``), a ``title`` (or ``name``), a
    ``detail`` (or ``body``), a ``source``, a ``ref``
    (or ``path`` / ``reference``) and an optional
    ``entry_id`` (or ``id``). Naming two spellings of
    one field with different values refuses, and
    unknown keys refuse.
    """
    if isinstance(entry, MemoryMapEntry):
        return entry
    if not isinstance(entry, dict):
        raise ValueError(
            f"an entry record must be a mapping, "
            f"got {entry!r}")
    unknown = set(entry) - _ENTRY_KEYS
    if unknown:
        raise ValueError(
            "unknown entry keys: %s"
            % ", ".join(sorted(unknown)))
    section = _pick_any(entry, ("section", "kind"), "sections")
    if section is None:
        raise ValueError("an entry record is missing its section")
    title = _pick_any(entry, ("title", "name"), "titles")
    if title is None:
        raise ValueError("an entry record is missing its title")
    detail = _pick_any(entry, ("detail", "body"), "details")
    if detail is None:
        raise ValueError("an entry record is missing its detail")
    source = _pick_any(entry, ("source",), "sources")
    if source is None:
        raise ValueError("an entry record is missing its source")
    ref = _pick_any(entry, ("ref", "path", "reference"), "references")
    if ref is None:
        raise ValueError("an entry record is missing its reference")
    kwargs: Dict[str, Any] = {
        "section": section, "title": title, "detail": detail,
        "source": source, "ref": ref}
    entry_id = _pick_any(entry, ("entry_id", "id"), "entry ids")
    if entry_id is not None:
        kwargs["entry_id"] = entry_id
    return MemoryMapEntry(**kwargs)


def build_entry(entry: Any = None, **kwargs: Any) -> MemoryMapEntry:
    """Build one validated entry, from a mapping or field words."""
    if isinstance(entry, MemoryMapEntry) and not kwargs:
        return entry
    if isinstance(entry, dict) or entry is None:
        merged: Dict[str, Any] = {}
        if isinstance(entry, dict):
            merged.update(entry)
        merged.update(kwargs)
        return validate_entry(merged)
    raise ValueError(
        f"an entry record must be a mapping, got {entry!r}")


def _check_entry_ref(value: Any) -> MemoryMapEntry:
    if isinstance(value, MemoryMapEntry):
        return value
    if isinstance(value, dict):
        return validate_entry(value)
    raise ValueError(f"an entry record is needed, got {value!r}")


def _held_entries(source: Any) -> Tuple[MemoryMapEntry, ...]:
    """The entries one source holds, in held order."""
    if isinstance(source, MemoryMapBook):
        return source.entries
    if isinstance(source, MemoryMapRegistry):
        return source.list_entries()
    if isinstance(source, (list, tuple)):
        return tuple(_check_entry_ref(e) for e in source)
    raise ValueError(f"entries are needed, got {source!r}")


# ---------------------------------------------------------------------
# The panel: the whole map accounted for, in map order, derived.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class MemoryMapPanelRow:
    """One entry carried whole into the panel.

    Every field is the entry's own: its section, its
    title, its source and the reference where the
    thing it names lives. :func:`validate_row` judged
    against an entry refuses a row whose fields
    disagree with the row that entry derives.
    """

    section: str
    title: str
    source: str
    ref: str
    entry_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.entry_id is not None:
            object.__setattr__(
                self, "entry_id",
                normalize_member_id(self.entry_id))
        object.__setattr__(
            self, "section", normalize_section(self.section))
        object.__setattr__(
            self, "title", _check_title(self.title, "a row's title"))
        object.__setattr__(
            self, "source",
            _check_title(self.source, "a row's source"))
        object.__setattr__(self, "ref", _check_ref(self.ref))

    @property
    def sort_key(self) -> Tuple[int, str]:
        """This row's place in map order (derived)."""
        return (MAP_SECTIONS.index(self.section), self.title)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "project_memory_map_row",
            "slice": PROJECT_MEMORY_MAP_SLICE,
            "entry_id": self.entry_id,
            "section": self.section,
            "title": self.title,
            "source": self.source,
            "ref": self.ref,
        }


def _derive_row(entry: MemoryMapEntry) -> MemoryMapPanelRow:
    return MemoryMapPanelRow(
        section=entry.section, title=entry.title,
        source=entry.source, ref=entry.ref,
        entry_id=entry.entry_id)


def _check_row_ref(value: Any) -> MemoryMapPanelRow:
    if isinstance(value, MemoryMapPanelRow):
        return value
    if isinstance(value, MemoryMapEntry):
        return _derive_row(value)
    if isinstance(value, dict):
        unknown = set(value) - _ROW_KEYS
        if unknown:
            raise ValueError(
                "unknown row keys: %s" % ", ".join(sorted(unknown)))
        section = _pick_any(value, ("section",), "sections")
        if section is None:
            raise ValueError("a row is missing its section")
        title = _pick_any(value, ("title",), "titles")
        if title is None:
            raise ValueError("a row is missing its title")
        source = _pick_any(value, ("source",), "sources")
        if source is None:
            raise ValueError("a row is missing its source")
        ref = _pick_any(value, ("ref", "path"), "references")
        if ref is None:
            raise ValueError("a row is missing its reference")
        kwargs: Dict[str, Any] = {
            "section": section, "title": title,
            "source": source, "ref": ref}
        entry_id = _pick_any(value, ("entry_id", "id"), "entry ids")
        if entry_id is not None:
            kwargs["entry_id"] = entry_id
        return MemoryMapPanelRow(**kwargs)
    raise ValueError(f"a panel row is needed, got {value!r}")


def validate_row(row: Any, entry: Any = None) -> MemoryMapPanelRow:
    """Validate one panel row into a MemoryMapPanelRow.

    Accepts a row, an entry (whose derived row is the
    row), or a mapping naming a ``section``, a
    ``title``, a ``source``, a ``ref`` (or ``path``)
    and an optional ``entry_id`` (or ``id``). With
    *entry* given, the row is judged against the row
    derived from that entry: a stored row whose
    fields disagree with the derived row refuses.
    """
    current = _check_row_ref(row)
    if entry is not None:
        derived = _derive_row(_check_entry_ref(entry))
        if current != derived:
            raise ValueError(
                "a stored row disagrees with the row "
                "derived from its entry")
    return current


def build_row(row: Any = None, entry: Any = None,
              **kwargs: Any) -> MemoryMapPanelRow:
    """Build one validated row, from a mapping or field words."""
    if isinstance(row, MemoryMapPanelRow) and not kwargs:
        return validate_row(row, entry)
    if isinstance(row, dict) or row is None:
        merged: Dict[str, Any] = {}
        if isinstance(row, dict):
            merged.update(row)
        merged.update(kwargs)
        return validate_row(merged, entry)
    return validate_row(row, entry)


@dataclass(frozen=True)
class MemoryMapSectionCount:
    """One section's count in a panel: its entries tallied."""

    section: str
    entries: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "section", normalize_section(self.section))
        object.__setattr__(
            self, "entries",
            _check_count(self.entries, "a section count's entries"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "section": self.section,
            "entries": self.entries,
        }


def _check_section_count_ref(value: Any) -> MemoryMapSectionCount:
    if isinstance(value, MemoryMapSectionCount):
        return value
    if isinstance(value, dict):
        unknown = set(value) - _SECTION_COUNT_KEYS
        if unknown:
            raise ValueError(
                "unknown section-count keys: %s"
                % ", ".join(sorted(unknown)))
        section = _pick_any(value, ("section",), "sections")
        if section is None:
            raise ValueError("a section count is missing its section")
        entries = _pick_any(value, ("entries", "count"), "counts")
        if entries is None:
            raise ValueError("a section count is missing its entries")
        return MemoryMapSectionCount(section=section, entries=entries)
    raise ValueError(f"a section count is needed, got {value!r}")


def _panel_account(rows: Tuple[MemoryMapPanelRow, ...],
                   section_counts: Tuple[MemoryMapSectionCount, ...]
                   ) -> Tuple[str, ...]:
    if section_counts:
        by_section = ", ".join(
            f"{row.section} {row.entries}" for row in section_counts)
        first = (
            f"The panel holds {len(rows)} project memory "
            f"map entries: {by_section}.")
    else:
        first = "The panel holds 0 project memory map entries."
    return (
        first,
        "Sections stand in map order (architecture, then "
        "decision, then gotcha, then location) and, inside "
        "one section, by title - so two panels of the same "
        "map diff cleanly, line by line.",
        "The Scribe keeps this map as work proceeds: the "
        "map is updated in the same session as the work it "
        "records, never as a later chore.",
        "The panel is read off the held entries at "
        "call time - it is derived, never stored "
        "loose.",
    )


@dataclass(frozen=True)
class MemoryMapPanel:
    """The project memory map panel, derived from the whole book.

    ``rows`` are the entries carried whole, in map
    order (section first, in :data:`MAP_SECTIONS`
    order, then title, so two panels of one map diff
    cleanly); ``total_entries`` is the entry count;
    ``section_counts`` are the per-section tallies in
    the order their sections first appear in the
    panel; ``keeper`` is always the Scribe;
    ``account`` is read off those numbers. A panel
    whose rows stand out of map order, whose keeper
    is not the Scribe, or whose totals are not its
    own rows' counts, refuses at construction;
    :func:`validate_panel` judged against entries
    refuses a stored panel that disagrees with the
    derived one.
    """

    rows: Tuple[MemoryMapPanelRow, ...] = ()
    total_entries: int = 0
    section_counts: Tuple[MemoryMapSectionCount, ...] = ()
    account: Tuple[str, ...] = ()
    keeper: str = MAP_KEEPER
    panel_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.panel_id is not None:
            object.__setattr__(
                self, "panel_id",
                normalize_member_id(self.panel_id))
        keeper = _clean_text(self.keeper, "a panel's keeper")
        if keeper != MAP_KEEPER:
            raise ValueError(
                "the project memory map is kept by the "
                "Scribe - a panel kept by anyone else refuses")
        object.__setattr__(self, "keeper", keeper)
        if isinstance(self.rows, (str, bytes)) \
                or not isinstance(self.rows, (list, tuple)):
            raise ValueError(
                f"a panel's rows must be a list of rows, "
                f"got {self.rows!r}")
        rows = tuple(_check_row_ref(r) for r in self.rows)
        seen_ids = set()
        for row in rows:
            if row.entry_id is not None:
                if row.entry_id in seen_ids:
                    raise ValueError(
                        f"a panel row named {row.entry_id!r} "
                        f"already exists")
                seen_ids.add(row.entry_id)
        keys = [row.sort_key for row in rows]
        if keys != sorted(keys):
            raise ValueError(
                "a panel's rows must stand in map "
                "order (section, then title)")
        object.__setattr__(self, "rows", rows)
        object.__setattr__(
            self, "total_entries",
            _check_count(self.total_entries, "a panel's total"))
        if isinstance(self.section_counts, (str, bytes)) \
                or not isinstance(self.section_counts, (list, tuple)):
            raise ValueError(
                f"a panel's section counts must be a list, "
                f"got {self.section_counts!r}")
        section_counts = tuple(
            _check_section_count_ref(c) for c in self.section_counts)
        seen_sections = set()
        for count in section_counts:
            if count.section in seen_sections:
                raise ValueError(
                    f"a section count named {count.section!r} "
                    f"already exists")
            seen_sections.add(count.section)
        object.__setattr__(self, "section_counts", section_counts)
        if self.total_entries != len(rows):
            raise ValueError(
                "a panel's total must be its own rows' count")
        if sum(c.entries for c in section_counts) != self.total_entries:
            raise ValueError(
                "a panel's section counts must sum to its own total")
        object.__setattr__(self, "account", _check_account(self.account))

    def row_for(self, entry_id: Any) -> MemoryMapPanelRow:
        """The panel row one entry id names in this panel."""
        wanted = normalize_member_id(entry_id)
        for row in self.rows:
            if row.entry_id == wanted:
                return row
        raise KeyError(f"no row in the panel: entry {wanted!r}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "project_memory_map_panel",
            "slice": PROJECT_MEMORY_MAP_SLICE,
            "panel_id": self.panel_id,
            "keeper": self.keeper,
            "rows": [row.to_record() for row in self.rows],
            "total_entries": self.total_entries,
            "section_counts": [c.to_record() for c in self.section_counts],
            "account": list(self.account),
        }


def derive_panel(source: Any) -> MemoryMapPanel:
    """Derive the panel from entries.

    The rows are the entries carried whole, sorted
    into map order (section first, then title), and
    the per-section tallies are read off the rows in
    the order their sections first appear in the
    panel. *source* is a book, a registry or the
    entries themselves. An empty source refuses - a
    panel of nothing is no panel.
    """
    entries = _held_entries(source)
    if not entries:
        raise ValueError("a panel needs at least one entry")
    rows = tuple(sorted(
        (_derive_row(entry) for entry in entries),
        key=lambda row: row.sort_key))
    order: list = []
    tally: Dict[str, int] = {}
    for row in rows:
        if row.section not in tally:
            tally[row.section] = 0
            order.append(row.section)
        tally[row.section] += 1
    section_counts = tuple(
        MemoryMapSectionCount(section=section, entries=tally[section])
        for section in order)
    return MemoryMapPanel(
        rows=rows,
        total_entries=len(entries),
        section_counts=section_counts,
        account=_panel_account(rows, section_counts))


def validate_panel(panel: Any, source: Any = None) -> MemoryMapPanel:
    """Validate one panel into a MemoryMapPanel.

    Accepts a panel or a mapping naming ``rows`` (or
    ``entries``), a ``total_entries`` (or ``total``),
    ``section_counts`` (or ``sections``), an
    ``account`` (or ``statements``), an optional
    ``keeper`` and an optional ``panel_id`` (or
    ``id``). With *source* given (entries), the panel
    is judged against the panel derived from those
    entries: a stored panel whose rows, totals,
    section counts, keeper or account disagree with
    the derived panel refuses. A panel naming no
    account refuses too.
    """
    if isinstance(panel, MemoryMapPanel):
        current = panel
    elif isinstance(panel, dict):
        unknown = set(panel) - _PANEL_KEYS
        if unknown:
            raise ValueError(
                "unknown panel keys: %s" % ", ".join(sorted(unknown)))
        rows = _pick_any(panel, ("rows", "entries"), "rows")
        if rows is None:
            raise ValueError("a panel is missing its rows")
        total = _pick_any(
            panel, ("total_entries", "total"), "totals")
        if total is None:
            raise ValueError("a panel is missing its total entries")
        section_counts = _pick_any(
            panel, ("section_counts", "sections"), "section counts")
        if section_counts is None:
            raise ValueError("a panel is missing its section counts")
        account = _pick_any(panel, ("account", "statements"), "accounts")
        if account is None:
            raise ValueError("a panel names no account of its own")
        kwargs: Dict[str, Any] = {
            "rows": rows, "total_entries": total,
            "section_counts": section_counts, "account": account}
        keeper = _pick_any(panel, ("keeper",), "keepers")
        if keeper is not None:
            kwargs["keeper"] = keeper
        panel_id = _pick_any(panel, ("panel_id", "id"), "panel ids")
        if panel_id is not None:
            kwargs["panel_id"] = panel_id
        current = MemoryMapPanel(**kwargs)
    else:
        raise ValueError(f"a panel must be a mapping, got {panel!r}")
    if source is not None:
        derived = derive_panel(source)
        if (current.rows != derived.rows
                or current.total_entries != derived.total_entries
                or current.section_counts != derived.section_counts
                or current.keeper != derived.keeper
                or current.account != derived.account):
            raise ValueError(
                "a stored panel disagrees with the panel "
                "derived from its entries")
    return current


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> MemoryMapPanel:
    """Build one validated panel, from a mapping or field words."""
    if isinstance(panel, MemoryMapPanel) and not kwargs:
        return validate_panel(panel, source)
    if isinstance(panel, dict) or panel is None:
        merged: Dict[str, Any] = {}
        if isinstance(panel, dict):
            merged.update(panel)
        merged.update(kwargs)
        return validate_panel(merged, source)
    return validate_panel(panel, source)


# ---------------------------------------------------------------------
# The book: entries in held order, panels judged.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class MemoryMapBook:
    """One project memory map book: its entries, in held order.

    ``entries`` are the entry records, in held order;
    ``panels`` are the book's derivations - panels of
    the book, judged against the book's records by
    :func:`validate_book`; ``canon_note`` is the
    book's own note. This book is the book file's
    shape: the shipped example is one book, and a
    real book file is a new file in this shape.
    """

    title: str = ""
    entries: Tuple[MemoryMapEntry, ...] = ()
    panels: Tuple[MemoryMapPanel, ...] = ()
    canon_note: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_title(self.title, "a book's title"))
        if isinstance(self.entries, (str, bytes)) \
                or not isinstance(self.entries, (list, tuple)):
            raise ValueError(
                f"a book's entries must be a list of entry "
                f"records, got {self.entries!r}")
        entries = tuple(_check_entry_ref(e) for e in self.entries)
        if not entries:
            raise ValueError(
                "a project memory map book holds at least one entry")
        seen_ids = set()
        seen_facts = set()
        for entry in entries:
            if entry.entry_id is not None:
                if entry.entry_id in seen_ids:
                    raise ValueError(
                        f"an entry named {entry.entry_id!r} "
                        f"already exists")
                seen_ids.add(entry.entry_id)
            key = (entry.section, entry.title)
            if key in seen_facts:
                raise ValueError(
                    f"the fact {entry.title!r} already stands "
                    f"in this book in the {entry.section} section")
            seen_facts.add(key)
        object.__setattr__(self, "entries", entries)
        if isinstance(self.panels, (str, bytes)) \
                or not isinstance(self.panels, (list, tuple)):
            raise ValueError(
                f"a book's panels must be a list of panels, "
                f"got {self.panels!r}")
        panels = tuple(
            p if isinstance(p, MemoryMapPanel) else validate_panel(p)
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
        object.__setattr__(
            self, "canon_note", self.canon_note.strip())

    def entry_for(self, entry_id: Any) -> MemoryMapEntry:
        """The entry one id names in this book."""
        wanted = normalize_member_id(entry_id)
        for entry in self.entries:
            if entry.entry_id == wanted:
                return entry
        raise KeyError(f"no entry in the book: {wanted!r}")

    def entries_for_section(
            self, section: Any) -> Tuple[MemoryMapEntry, ...]:
        """Every entry of one section, in held order."""
        wanted = normalize_section(section)
        return tuple(e for e in self.entries if e.section == wanted)

    def panel_for(self, panel_id: Any) -> MemoryMapPanel:
        """The stored panel one id names in this book."""
        wanted = normalize_member_id(panel_id)
        for panel in self.panels:
            if panel.panel_id == wanted:
                return panel
        raise KeyError(f"no panel in the book: {wanted!r}")

    def entry_ids(self) -> Tuple[str, ...]:
        """Every held entry id, in held order."""
        return tuple(e.entry_id for e in self.entries if e.entry_id)

    def sections(self) -> Tuple[str, ...]:
        """Every held entry's section, in held order."""
        return tuple(e.section for e in self.entries)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "project_memory_map_book",
            "slice": PROJECT_MEMORY_MAP_SLICE,
            "title": self.title,
            "entry_ids": list(self.entry_ids()),
            "entry_count": len(self.entries),
            "panel_count": len(self.panels),
        }


def validate_book(data: Any, *, require_example: bool = False) -> MemoryMapBook:
    """Validate one project-memory-map mapping into a book.

    The mapping names a ``schema`` (the
    project-memory-map schema word), a ``guide``
    mapping (its ``title``), an ``entries`` list and
    an optional ``panels`` list. Every record stands
    on its own validation, then the whole is judged:
    entry ids unique, no fact standing twice in one
    section, and every stored panel judged against
    the book's own entries. With ``require_example``
    the shipped example is held to its pinned shape:
    the pinned title, records and sections, and the
    panel's pinned rows and account word-for-word.
    Problems raise :class:`ValidationError` or
    ``ValueError``.
    """
    if isinstance(data, MemoryMapBook):
        return data
    if not isinstance(data, dict):
        raise ValidationError(
            f"a project memory map book must be a mapping, got {data!r}")
    unknown = set(data) - _PROJECT_MEMORY_MAP_KEYS
    if unknown:
        raise ValidationError(
            "unknown project-memory-map keys: %s"
            % ", ".join(sorted(unknown)))
    if data.get("schema") != PROJECT_MEMORY_MAP_SCHEMA:
        raise ValidationError(
            f"a project memory map book must carry schema "
            f"{PROJECT_MEMORY_MAP_SCHEMA!r}, got {data.get('schema')!r}")
    entries = _pick_any(data, ("entries",), "entries")
    if entries is None:
        raise ValidationError("a project memory map book is missing its entries")
    if not isinstance(entries, (list, tuple)):
        raise ValidationError("a project memory map book's entries must be a list")
    if data.get("panels") is not None \
            and not isinstance(data["panels"], (list, tuple)):
        raise ValidationError("a project memory map book's panels must be a list")
    head = data.get("guide") or {}
    if not isinstance(head, dict):
        raise ValidationError("a project memory map book's guide must be a mapping")
    unknown_head = set(head) - _BOOK_KEYS
    if unknown_head:
        raise ValidationError(
            "unknown guide keys: %s" % ", ".join(sorted(unknown_head)))
    try:
        title = _pick_any(head, ("title", "name"), "titles")
        if title is None:
            raise ValidationError("a project memory map book is missing its title")
        note = data.get("canon_note") or ""
        if not isinstance(note, str):
            raise ValidationError("a project memory map book's note must be text")
        book = MemoryMapBook(
            title=title, entries=tuple(entries),
            panels=tuple(data.get("panels") or ()),
            canon_note=note)
        for panel in book.panels:
            validate_panel(panel, book)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    if require_example:
        if book.title != _EXAMPLE_TITLE:
            raise ValidationError(
                "the shipped example project memory map book's title "
                "is not the pinned title")
        if book.entry_ids() != _EXAMPLE_ENTRY_IDS:
            raise ValidationError(
                "the shipped example's entries are not "
                "the pinned records")
        if book.sections() != _EXAMPLE_SECTIONS:
            raise ValidationError(
                "the shipped example's sections are not "
                "the pinned sections")
        panel = book.panel_for(_EXAMPLE_PANEL_ID)
        if tuple(r.entry_id for r in panel.rows) != _EXAMPLE_PANEL_ROW_IDS:
            raise ValidationError(
                "the shipped example panel does not name "
                "its pinned rows in map order")
        if panel.account != _EXAMPLE_PANEL_ACCOUNT:
            raise ValidationError(
                "the shipped example panel does not carry "
                "its pinned account word-for-word")
        first = book.entries[0]
        if first.section != "location" \
                or first.title != "The package":
            raise ValidationError(
                "the shipped example's first entry is not "
                "its pinned package entry")
    return book


def build_book(book: Any = None, **kwargs: Any) -> MemoryMapBook:
    """Build one validated book, from a mapping or field words."""
    if isinstance(book, MemoryMapBook) and not kwargs:
        return book
    if isinstance(book, dict):
        if "schema" in book:
            return validate_book(book)
        merged: Dict[str, Any] = dict(book)
        merged.update(kwargs)
        return MemoryMapBook(**merged)
    if book is None:
        return MemoryMapBook(**kwargs)
    raise ValueError(f"a project memory map book is needed, got {book!r}")


def _book_from(data: Any, *, require_example: bool) -> MemoryMapBook:
    try:
        return validate_book(data, require_example=require_example)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def load_project_memory_map(
        data: Optional[Dict[str, Any]] = None) -> MemoryMapBook:
    """Load and validate the shipped example book (or *data*).

    The shipped file is held to the example check:
    the pinned title, entry records and panel - the
    M-149 slice boundary book - so the shipped book
    covers the canon this slice exists to hold.
    """
    raw = data if data is not None else load_resource(PROJECT_MEMORY_MAP_RESOURCE)
    return _book_from(raw, require_example=True)


def load_project_memory_map_file(path: Any) -> MemoryMapBook:
    """Load and validate a project-memory-map book from a file at *path*.

    Any file in the project-memory-map shape, anywhere
    on disk, validated whole - a malformed file raises
    :class:`ValidationError` naming the problem, and a
    missing file raises ``FileNotFoundError``. The
    example check is not held: a real book stands on
    its own records.
    """
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _book_from(raw, require_example=False)


# ---------------------------------------------------------------------
# The Scribe's charter road: the shipped method charter, by import.
# ---------------------------------------------------------------------


def scribe_directives() -> Tuple[str, ...]:
    """The Scribe's own directives for keeping this map.

    Read off the shipped method charter BY IMPORT -
    the ``PROJECT_MEMORY_MAP`` plug (F-03) of
    ``core/method_charter.py`` (M-005) - never a
    second copy of the law: keep the map current
    (identity, architecture, canonical paths,
    contracts, capabilities, limits, decisions),
    update it in the same session as the change it
    records, and read it before exploring.
    """
    charter = load_charter()
    return tuple(charter.tenet("project-memory-map").directives)


# ---------------------------------------------------------------------
# The live scan road: a real workspace's convention file, read.
# ---------------------------------------------------------------------


def _scan_entry_id(heading: str) -> str:
    slug = "".join(
        ch.lower() if ch.isalnum() else "-"
        for ch in heading).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return f"scan-{slug}"


def scan_workspace(workspace: Any) -> Tuple[MemoryMapEntry, ...]:
    """Scan one real workspace's convention file into map entries.

    The workspace's ``PROJECT_MEMORY_MAP.md`` - the
    shipped convention file this slice holds as
    data - is READ (never written): each ``## ``
    heading becomes one entry, its section read off
    :data:`MAP_SECTION_HEADINGS` (a heading the
    table does not name stands in the architecture
    section, the map's own first section), its title
    the heading itself, its detail the first words
    standing under the heading, its source and
    reference the convention file itself, and its id
    ``scan-<slug of the heading>``. A workspace with
    no convention file scans to no entries - the
    absence is honest, never invented. Every file in
    the workspace is left byte-identical.
    """
    path = Path(workspace) / "PROJECT_MEMORY_MAP.md"
    if not path.is_file():
        return ()
    lines = path.read_text(encoding="utf-8").splitlines()
    entries = []
    heading: Optional[str] = None
    detail: Optional[str] = None

    def _flush() -> None:
        if heading is None:
            return
        text = (detail or "").strip()
        if text.startswith("- "):
            text = text[2:].strip()
        if not text:
            text = f"The {heading} section of the project's living map."
        if len(text) > 500:
            text = text[:500].rstrip()
        entries.append(MemoryMapEntry(
            section=MAP_SECTION_HEADINGS.get(heading, "architecture"),
            title=heading,
            detail=text,
            source="PROJECT_MEMORY_MAP.md",
            ref="PROJECT_MEMORY_MAP.md",
            entry_id=_scan_entry_id(heading)))

    for line in lines:
        if line.startswith("## ") and not line.startswith("### "):
            _flush()
            heading = line[3:].strip()
            detail = None
        elif heading is not None and detail is None:
            if line.strip():
                detail = line.strip()
    _flush()
    return tuple(entries)


# ---------------------------------------------------------------------
# The registry model: one book held entry by entry, in held order.
# ---------------------------------------------------------------------


class MemoryMapRegistry:
    """One session's project memory map, held entry by entry.

    The registry holds entry records, never panels:
    the panel is a derivation, read off held entries
    at call time, so nothing here can hold a figure
    stale.
    """

    def __init__(self, book: Any = None) -> None:
        self._title: Optional[str] = None
        self._entries: Dict[str, MemoryMapEntry] = {}
        self._order: list = []
        self._next_entry = 1
        if book is not None:
            self.register_book(book)

    def _fresh_entry_id(self, held_ids: Any) -> str:
        while f"map-{self._next_entry}" in held_ids:
            self._next_entry += 1
        fresh = f"map-{self._next_entry}"
        self._next_entry += 1
        return fresh

    def register_entry(self, entry: Any) -> MemoryMapEntry:
        """Register one entry into the held book.

        A record with no id is given a deterministic
        ``map-N`` id. A record id already standing
        here refuses, as does the same fact already
        standing here in the same section - one fact
        of the map is named once.
        """
        validated = build_entry(entry)
        held_ids = set(self._entries)
        if validated.entry_id is not None \
                and validated.entry_id in held_ids:
            raise ValueError(
                f"an entry named "
                f"{validated.entry_id!r} already exists")
        for held in self._entries.values():
            if (held.section, held.title) == (
                    validated.section, validated.title):
                raise ValueError(
                    f"the fact {validated.title!r} already "
                    f"stands here in the {validated.section} section")
        if validated.entry_id is None:
            validated = replace(
                validated,
                entry_id=self._fresh_entry_id(held_ids))
        self._entries[validated.entry_id] = validated
        self._order.append(validated.entry_id)
        return validated

    def register_book(self, book: Any) -> MemoryMapBook:
        """Register every entry of one book, in order.

        The first book held sets the title; a later
        book under a different title refuses, as does
        a book naming a held entry id or a held fact.
        The book's panels are derivations, not
        holdings, and are not held.
        """
        validated = build_book(book)
        if self._title is not None and validated.title != self._title:
            raise ValueError(
                "this registry already holds a project "
                "memory map book under a different title")
        for entry in validated.entries:
            if entry.entry_id in self._entries:
                raise ValueError(
                    f"an entry named "
                    f"{entry.entry_id!r} already exists")
        self._title = validated.title
        for entry in validated.entries:
            self.register_entry(entry)
        return self.book()

    def get_entry(self, entry_id: Any) -> MemoryMapEntry:
        """The entry one id names among the held records."""
        wanted = normalize_member_id(entry_id)
        if wanted not in self._entries:
            raise KeyError(f"unknown entry: {wanted!r}")
        return self._entries[wanted]

    def list_entries(self) -> Tuple[MemoryMapEntry, ...]:
        """Every held entry, in the order they were held."""
        return tuple(self._entries[e] for e in self._order)

    def book(self) -> MemoryMapBook:
        """The held entries as one validated book."""
        if self._title is None:
            raise ValueError("no project memory map book is held yet")
        return MemoryMapBook(
            title=self._title, entries=self.list_entries())

    def panel(self) -> MemoryMapPanel:
        """Derive the panel of the held entries, at call time."""
        return derive_panel(self)


# ---------------------------------------------------------------------
# Map news, shaped as session records.
# ---------------------------------------------------------------------


def entry_record(entry: Any) -> Dict[str, Any]:
    """The session-news record of one entry."""
    current = entry if isinstance(entry, MemoryMapEntry) \
        else build_entry(entry)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"{current.title} ({current.section}) stands in the "
        f"project memory map at {current.ref}: "
        f"{current.detail}")
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of one derived panel.

    With *source* given, the panel is first judged
    against the panel that source derives.
    """
    current = validate_panel(panel, source)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Project memory map panel: {current.total_entries} "
        f"entries in map order, kept by the Scribe.")
    return record


def book_record(book: Any) -> Dict[str, Any]:
    """The session-news record of one project memory map book."""
    current = book if isinstance(book, MemoryMapBook) \
        else build_book(book)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Project memory map {current.title}: "
        f"{record['entry_count']} entries named.")
    return record


def plain_words(entry: Any) -> str:
    """One entry, in one plain sentence."""
    current = entry if isinstance(entry, MemoryMapEntry) \
        else build_entry(entry)
    return (
        f"{current.title} - {current.section}, "
        f"at {current.ref} from {current.source}: "
        f"{current.detail}")


def panel_plain_words(source: Any) -> str:
    """The panel in plain words, in full.

    Accepts a MemoryMapPanel or a MemoryMapBook. The
    panel is told whole - its rows in map order and
    its account.
    """
    if isinstance(source, MemoryMapPanel):
        panel = validate_panel(source)
        title = None
    elif isinstance(source, MemoryMapBook):
        panel = derive_panel(source)
        title = source.title
    else:
        raise ValueError(f"a project memory map source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    lines.append("Project memory map entries, in map order:")
    for row in panel.rows:
        lines.append(
            f"{row.section}: {row.title} "
            f"at {row.ref}, from {row.source}")
    lines.extend(panel.account)
    return "\n".join(lines)


# ---------------------------------------------------------------------
# Screens: the formatters and the shared /memorymap grammar.
# ---------------------------------------------------------------------


def _source_book(source: Any) -> MemoryMapBook:
    if source is None:
        return load_project_memory_map()
    if isinstance(source, MemoryMapRegistry):
        return source.book()
    if isinstance(source, MemoryMapBook):
        return source
    raise ValueError(f"a project memory map book is needed, got {source!r}")


def format_entry(entry: Any) -> str:
    """One entry as a screen line."""
    current = entry if isinstance(entry, MemoryMapEntry) \
        else build_entry(entry)
    return (
        f"{current.entry_id or '-'}: {current.title} - "
        f"{current.section} ({current.ref} "
        f"from {current.source})")


def format_entries(source: Any = None, section: Any = None) -> str:
    """Entries of one book, in held order.

    With *section* given, only the entries of that
    section are shown.
    """
    book = _source_book(source)
    entries = book.entries
    if section is not None:
        wanted = normalize_section(section)
        entries = tuple(e for e in entries if e.section == wanted)
    lines = [format_entry(entry) for entry in entries]
    if not lines:
        lines.append("No project memory map entries are held.")
    return "\n".join(lines)


def format_panel(source: Any = None) -> str:
    """The panel as a screen block: every row and the account.

    Accepts a MemoryMapPanel or a MemoryMapBook; a
    book shows the panel it derives.
    """
    if isinstance(source, MemoryMapPanel):
        panel = validate_panel(source)
        lines: list = []
    else:
        book = _source_book(source)
        panel = derive_panel(book)
        lines = [f"Panel in {book.title}:"]
    lines.append("Project memory map entries, in map order:")
    for row in panel.rows:
        lines.append(
            f"{row.entry_id or '-'}: {row.section} - "
            f"{row.title} at {row.ref}, from {row.source}")
    lines.extend(panel.account)
    return "\n".join(lines)


def format_project_memory_map_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /memorymap.

    With nothing named, the shipped example project
    memory map book is shown - the example this slice
    ships - so the screen is never empty.
    """
    book = _source_book(source)
    lines = ["Project Memory Map (M-150) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_entries(book))
    lines.append("")
    lines.append(format_panel(book))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_memory_map_args(args: Any) -> Tuple[str, Any]:
    """Parse the /memorymap grammar both surfaces share.

    No words (or ``show`` / ``list``) shows the
    project memory map book; ``entry <entry-id>``
    shows one entry; ``section <section>`` shows the
    entries of one section; ``panel`` shows the panel
    derived from the whole book. Anything else is a
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
    if head == "panel" and len(words) == 1:
        return (head, None)
    if head == "entry" and len(words) == 2:
        try:
            return (head, normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "section" and len(words) == 2:
        try:
            return (head, normalize_section(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
