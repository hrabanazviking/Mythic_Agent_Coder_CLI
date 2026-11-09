"""Cold-Start Kindness (All-Features roadmap slice M-169).

Part VII closes. The roadmap's words: ``opening a
huge, old project rebuilds its map in the
background while the coder is already useful.``

What already ships, and what this slice adds:

* The project's living map already ships as data
  on a shipped road - the project memory map
  (``core/project_memory_map.py``, M-150) - and a
  session's carried situation already ships on
  its own road (``core/session_memory.py``,
  M-153). The memory doctor (M-168) can say a
  map has drifted, but nothing holds the moment
  of OPENING a project: how old and how large
  its map stands against the project itself,
  what may be used at once, and in what order the
  map is rebuilt while the coder works.
* This slice is that opening, as a pure layer:
  one cold-start record validated as data WITH
  ITS EVIDENCE WHOLE - the project it opens,
  named by its project id alone; the map it
  stands over, named by its map id alone; the
  day the project was opened, who opened it and
  the session it was opened in; and the map
  evidence itself: the map's age in days, its
  entry count, the project's file count, how
  many of those files the map covers, and the
  map carried by area - the shipped map's own
  sections - each area naming how many of its
  entries stand stale. What happens next is
  never in question and never stored loose: the
  rebuild plan is DERIVED from the evidence -
  a project with no map at all rebuilds from
  scratch, a project whose map is old, stale or
  short of the project rebuilds in the
  background while the coder works from the
  stale-but-usable map, and a fresh, whole map
  is simply served - and the stages of a rebuild
  stand in derived order, the stalest area
  first. The readiness panel is DERIVED from
  the whole book (what is usable now beside what
  is still rebuilding, record by record), a
  cold-start VERDICT is derived for the whole
  book, and rebuild progress is judged stage by
  stage against the derived plan, in order.
  Records are composed BY IMPORT from the
  shipped holdings they stand over - a project
  memory map book or entry (M-150) and a session
  situation (M-153) - each judged by its own
  layer's validation, ids and refs only across
  the seams. The shipped data file
  (``mythic_agent/data/cold_start.yaml``) holds
  one example book in exactly the shape a real
  book file takes, a loader reads a book file
  anywhere on disk, records are shaped as
  session news, and a small in-memory registry
  model holds records one by one and marks
  derived rebuild stages done on its own held
  book. The agent layer owns holding a book for
  a session and opening a project over the
  session's own held map.

Honesty rules, enforced here and pinned by tests:

* **Ids only across the seam.** A record names
  the project and the map by id alone; the map's
  own facts stay in the map's own layer, judged
  by its own layer's validator. What crosses is
  evidence - counts and ages - never map text.
* **The plan is derived, never chosen.** A
  record's mode and its stage order are read off
  its evidence alone: no map, a from-scratch
  rebuild; stale, old or short evidence, a
  background rebuild served from the stale map
  meanwhile; fresh and whole evidence, no
  rebuild at all. A stored mode or plan naming
  anything else refuses.
* **Progress walks the plan in order.** A stage
  is marked done only when it is the plan's next
  stage, so progress can never skip the stalest
  area or claim a stage the plan never derived.
* **One opening per project in a book.** One
  record stands for one project in a book, so a
  project's opening never forks.
* **Data only.** This layer holds openings as
  data: it starts no thread, rebuilds no live
  map, opens no live project, sends nothing,
  posts nothing, schedules nothing, calls no
  model and persists nothing - marking a stage
  done marks it on the held book only.
"""

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..resources import load_resource
from .crew_members import normalize_member_id
from .project_memory_map import MAP_SECTIONS
from .project_memory_map import MemoryMapBook
from .project_memory_map import MemoryMapEntry
from .project_memory_map import normalize_section
from .project_memory_map import validate_book as _validate_map_book
from .project_memory_map import validate_entry as _validate_map_entry
from .session_memory import SessionSituation
from .session_memory import validate_situation as _validate_situation
from .validation import ValidationError

__all__ = [
    "AREAS",
    "COLD_START_RESOURCE",
    "COLD_START_SCHEMA",
    "COLD_START_SLICE",
    "MODES",
    "PLAIN_EXPLANATION",
    "USAGE",
    "VERDICT_WORDS",
    "ColdStartArea",
    "ColdStartBook",
    "ColdStartPanel",
    "ColdStartPanelRow",
    "ColdStartProgress",
    "ColdStartRecord",
    "ColdStartRegistry",
    "ColdStartVerdict",
    "ModeCount",
    "book_record",
    "build_area",
    "build_book",
    "build_panel",
    "build_progress",
    "build_record",
    "build_row",
    "build_verdict",
    "derive_panel",
    "derive_progress",
    "derive_verdict",
    "format_cold_start_screen",
    "format_panel",
    "format_progress",
    "format_record",
    "format_records",
    "format_verdict",
    "inspect_opening_source",
    "load_cold_start",
    "load_cold_start_file",
    "mode_of",
    "normalize_mode",
    "panel_plain_words",
    "panel_record",
    "parse_cold_start_args",
    "plain_words",
    "progress_plain_words",
    "progress_record",
    "record_for",
    "record_from_map_book",
    "record_from_map_entry",
    "record_from_session_situation",
    "record_record",
    "record_refs",
    "stage_plan_of",
    "total_records",
    "usable_entries_of",
    "validate_area",
    "validate_book",
    "validate_panel",
    "validate_progress",
    "validate_record",
    "validate_row",
    "validate_verdict",
    "verdict_plain_words",
    "verdict_record",
]

COLD_START_SLICE = "M-169"

COLD_START_RESOURCE = "cold_start.yaml"

COLD_START_SCHEMA = "mythic.cold_start/1"

#: The areas a carried map is counted by: the
#: shipped project memory map's own sections
#: (M-150), composed by import - architecture,
#: decision, gotcha and location.
AREAS = MAP_SECTIONS

#: The modes an opening may derive, in panel
#: order: no map at all, a background rebuild
#: behind a stale-but-usable map, and a fresh map
#: served as it stands.
MODES = ("rebuild-from-scratch", "background-rebuild", "serve-fresh")

_MODE_ALIASES = {
    "rebuild-from-scratch": "rebuild-from-scratch",
    "rebuild_from_scratch": "rebuild-from-scratch",
    "from-scratch": "rebuild-from-scratch",
    "scratch": "rebuild-from-scratch",
    "background-rebuild": "background-rebuild",
    "background_rebuild": "background-rebuild",
    "background": "background-rebuild",
    "stale": "background-rebuild",
    "serve-fresh": "serve-fresh",
    "serve_fresh": "serve-fresh",
    "fresh": "serve-fresh",
}

#: The words a whole book's cold-start verdict
#: may carry, kindest last in derivation: cold
#: while any project stands with no map at all,
#: warming while any map rebuilds in the
#: background, kind while every map stands fresh.
VERDICT_WORDS = ("cold", "warming", "kind")

#: A map this many days old or older derives a
#: background rebuild on age alone, however whole
#: its coverage stands.
STALE_AGE_DAYS = 30

_AREA_KEYS = frozenset({
    "section", "area", "entries", "count",
    "stale_entries", "stale"})

_RECORD_KEYS = frozenset({
    "record_id", "id", "title", "name", "subject",
    "project_ref", "project", "map_ref", "map",
    "map_age_days", "age_days", "age",
    "map_entries", "entries",
    "project_files", "files",
    "covered_files", "covered",
    "areas", "opened_on", "day", "date",
    "opened_by", "recorder", "by", "who",
    "source", "origin_session", "session",
})

_ROW_KEYS = frozenset({
    "record_id", "id", "title", "project_ref",
    "mode", "usable_entries", "usable",
    "total_stale", "stale",
    "rebuilding_areas", "rebuilding",
    "stage_count", "stages", "first_stage",
    "opened_on"})

_MODE_COUNT_KEYS = frozenset({"mode", "items", "count"})

_PANEL_KEYS = frozenset({
    "panel_id", "id", "rows", "records",
    "total_records", "total",
    "total_fresh", "fresh",
    "total_warming", "warming",
    "total_cold", "cold",
    "distinct_projects", "projects",
    "mode_counts", "modes",
    "as_of", "day", "account", "statements",
})

_VERDICT_KEYS = frozenset({
    "total_records", "total",
    "total_fresh", "fresh",
    "total_warming", "warming",
    "total_cold", "cold",
    "distinct_projects", "projects",
    "earliest_on", "earliest",
    "latest_on", "latest", "verdict",
})

_PROGRESS_KEYS = frozenset({
    "record_id", "id", "stages", "plan",
    "completed", "done", "next_stage", "next",
    "complete", "finished",
})

_BOOK_KEYS = frozenset({"title", "name"})

_COLD_BOOK_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "canon_note", "guide", "records", "openings", "panels",
})

_EXAMPLE_TITLE = "Cold-Start Kindness at the M-168 slice boundary"

_EXAMPLE_RECORD_IDS = (
    "opening-mythic-hammer", "opening-old-sagas",
    "opening-fresh-notes")

_EXAMPLE_FIRST_RECORD_ID = "opening-mythic-hammer"

_EXAMPLE_FIRST_RECORD_TITLE = (
    "the mythic hammer campaign home opens cold")

_EXAMPLE_PANEL_ID = "panel-m168-boundary"

_EXAMPLE_AS_OF = "2026-11-09"

_EXAMPLE_PANEL_ROW_IDS = (
    "opening-old-sagas", "opening-mythic-hammer",
    "opening-fresh-notes")

PLAIN_EXPLANATION = (
    "Cold-Start Kindness: opening a huge, old "
    "project rebuilds its map in the background "
    "while the coder is already useful. A record "
    "names the project and its map by id alone "
    "and carries the map evidence whole - its age "
    "in days, its entries, the project's files, "
    "the files the map covers, and the map counted "
    "by area with each area's stale entries. The "
    "rebuild plan is derived, never chosen: no "
    "map derives a rebuild from scratch, old, "
    "stale or short evidence derives a background "
    "rebuild served from the stale-but-usable map "
    "meanwhile, and fresh, whole evidence derives "
    "no rebuild at all - and the stages stand in "
    "derived order, the stalest area first. The "
    "readiness panel is derived from the book at "
    "call time, the cold-start verdict is derived "
    "for the whole book, and progress walks the "
    "derived plan stage by stage, in order. This "
    "layer holds openings as data only: it starts "
    "no thread, rebuilds no live map, opens no "
    "live project, sends nothing, posts nothing, "
    "schedules nothing, calls no model and "
    "persists nothing - a stage marked done is "
    "marked on the held book alone."
)

USAGE = (
    "Usage: /coldstart, /coldstart show, "
    "/coldstart record <record-id>, "
    "/coldstart project <project-ref>, "
    "/coldstart panel, /coldstart verdict, "
    "/coldstart stages"
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


def _check_day(value: Any, what: str = "a day") -> str:
    text = _clean_text(value, what)
    try:
        parsed = date.fromisoformat(text)
    except ValueError:
        raise ValueError(
            f"{what} must be an ISO date "
            f"(YYYY-MM-DD), got {text!r}") from None
    if parsed.isoformat() != text:
        raise ValueError(
            f"{what} must be an ISO date "
            f"(YYYY-MM-DD), got {text!r}")
    return text


def _check_stage(value: Any) -> str:
    text = _clean_text(value, "a stage")
    if text in ("serve-fresh-map", "serve-stale-map",
                "rebuild-whole-map", "verify-map"):
        return text
    if text.startswith("rebuild-area:"):
        section = text.split(":", 1)[1]
        try:
            normalize_section(section)
        except ValueError:
            raise ValueError(
                f"a stage must name a shipped map area, "
                f"got {text!r}") from None
        return text
    raise ValueError(f"a stage is not a derived stage word, got {text!r}")


def normalize_mode(value: Any) -> str:
    """One mode word, read onto the closed mode set."""
    if not isinstance(value, str):
        raise ValueError(f"a mode must be a word, got {value!r}")
    mode = _MODE_ALIASES.get(value.strip().lower())
    if mode is None:
        raise ValueError(
            "a mode is one of %s, got %r"
            % ("/".join(MODES), value))
    return mode


# ---------------------------------------------------------------------
# The area evidence: one map area, counted.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class ColdStartArea:
    """One area of a carried map, counted as evidence.

    ``section`` is the area's section in the
    shipped map's own closed set (M-150), judged
    by the map's own normaliser; ``entries`` is
    how many map entries the area carries;
    ``stale_entries`` is how many of those entries
    stand stale - never more than the area
    carries. The area is evidence only: it counts
    the map, it carries none of the map's words.
    """

    section: str
    entries: int
    stale_entries: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "section", normalize_section(self.section))
        object.__setattr__(
            self, "entries", _check_count(self.entries, "an area's entries"))
        object.__setattr__(
            self, "stale_entries",
            _check_count(self.stale_entries, "an area's stale entries"))
        if self.stale_entries > self.entries:
            raise ValueError(
                "an area's stale entries cannot outnumber "
                "its entries")

    @property
    def usable_entries(self) -> int:
        """Entries usable at once in this area (derived)."""
        return self.entries - self.stale_entries

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "cold_start_area",
            "slice": COLD_START_SLICE,
            "section": self.section,
            "entries": self.entries,
            "stale_entries": self.stale_entries,
        }


def _check_area_ref(value: Any) -> ColdStartArea:
    if isinstance(value, ColdStartArea):
        return value
    return validate_area(value)


def validate_area(area: Any) -> ColdStartArea:
    """Validate one area record into a ColdStartArea.

    Accepts an area or a mapping naming a
    ``section`` (or ``area``), ``entries`` (or
    ``count``) and ``stale_entries`` (or
    ``stale``). Naming two spellings of one field
    with different values refuses, and unknown
    keys refuse.
    """
    if isinstance(area, ColdStartArea):
        return area
    if not isinstance(area, dict):
        raise ValueError(f"an area record must be a mapping, got {area!r}")
    unknown = set(area) - _AREA_KEYS
    if unknown:
        raise ValueError(
            "unknown area keys: %s" % ", ".join(sorted(unknown)))
    section = _pick_any(area, ("section", "area"), "sections")
    if section is None:
        raise ValueError("an area is missing its section")
    entries = _pick_any(area, ("entries", "count"), "entry counts")
    if entries is None:
        raise ValueError("an area is missing its entries")
    stale = _pick_any(area, ("stale_entries", "stale"), "stale counts")
    return ColdStartArea(
        section=section, entries=entries,
        stale_entries=0 if stale is None else stale)


def build_area(area: Any = None, **kwargs: Any) -> ColdStartArea:
    """Build one validated area, from a mapping or field words."""
    if isinstance(area, ColdStartArea) and not kwargs:
        return area
    if isinstance(area, dict) or area is None:
        merged: Dict[str, Any] = {}
        if isinstance(area, dict):
            merged.update(area)
        merged.update(kwargs)
        return validate_area(merged)
    return validate_area(area)


# ---------------------------------------------------------------------
# The cold-start record: one opening, with its evidence whole.
# ---------------------------------------------------------------------


def _areas_of(value: Any) -> Tuple[ColdStartArea, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, (list, tuple)):
        raise ValueError(f"a record's areas must be a list, got {value!r}")
    areas = tuple(_check_area_ref(item) for item in value)
    seen = set()
    for area in areas:
        if area.section in seen:
            raise ValueError(
                f"the {area.section} area stands twice in one record")
        seen.add(area.section)
    return areas


@dataclass(frozen=True)
class ColdStartRecord:
    """One project's opening, validated as data with its evidence whole.

    ``project_ref`` names the project by its id
    alone and ``map_ref`` the map it stands over
    by its id alone - the map's own facts never
    cross. The evidence is whole: ``map_age_days``
    the map's age in days, ``map_entries`` its
    entry count, ``project_files`` the project's
    file count, ``covered_files`` how many of
    those files the map covers, and ``areas`` the
    map counted by area, whose entry counts must
    sum to the map's own. ``opened_on`` is the
    day the project was opened (an ISO date),
    ``opened_by`` who opened it, ``source`` where
    the record was read from and
    ``origin_session`` the session it opened in.
    The record's mode and stage plan are derived
    from this evidence alone - they are never
    fields, so they can never be chosen.
    """

    title: str
    project_ref: str
    map_ref: str
    map_age_days: int
    map_entries: int
    project_files: int
    covered_files: int
    areas: Tuple[ColdStartArea, ...] = ()
    opened_on: str = "2026-11-09"
    opened_by: str = "Volmarr"
    source: str = "cold start"
    origin_session: str = "session-m169"
    record_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.record_id is not None:
            object.__setattr__(
                self, "record_id", _check_word(self.record_id, "a record id"))
        object.__setattr__(
            self, "title", _check_title(self.title, "a record's title"))
        object.__setattr__(
            self, "project_ref", _check_word(self.project_ref, "a project ref"))
        object.__setattr__(
            self, "map_ref", _check_word(self.map_ref, "a map ref"))
        object.__setattr__(
            self, "map_age_days",
            _check_count(self.map_age_days, "a map's age in days"))
        object.__setattr__(
            self, "map_entries",
            _check_count(self.map_entries, "a map's entries"))
        object.__setattr__(
            self, "project_files",
            _check_count(self.project_files, "a project's files"))
        object.__setattr__(
            self, "covered_files",
            _check_count(self.covered_files, "a map's covered files"))
        if self.covered_files > self.project_files:
            raise ValueError(
                "a map cannot cover more files than the project holds")
        areas = _areas_of(self.areas)
        object.__setattr__(self, "areas", areas)
        if sum(a.entries for a in areas) != self.map_entries:
            raise ValueError(
                "a record's areas must count the map whole: "
                "their entries sum to the map's entries")
        if self.map_entries and not areas:
            raise ValueError(
                "a record with a map carries its areas")
        object.__setattr__(
            self, "opened_on", _check_day(self.opened_on, "an opening day"))
        object.__setattr__(
            self, "opened_by", _check_title(self.opened_by, "an opener"))
        object.__setattr__(
            self, "source", _check_title(self.source, "a record's source"))
        object.__setattr__(
            self, "origin_session",
            _check_word(self.origin_session, "an origin session"))

    @property
    def total_stale(self) -> int:
        """Stale entries across the whole map (derived)."""
        return sum(a.stale_entries for a in self.areas)

    @property
    def mode(self) -> str:
        """This opening's derived mode (see :func:`mode_of`)."""
        return mode_of(self)

    @property
    def stage_plan(self) -> Tuple[str, ...]:
        """This opening's derived stage plan (see :func:`stage_plan_of`)."""
        return stage_plan_of(self)

    def area_for(self, section: Any) -> ColdStartArea:
        """The one area of this record a section names."""
        wanted = normalize_section(section)
        for area in self.areas:
            if area.section == wanted:
                return area
        raise KeyError(f"no {wanted} area stands in this record")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "cold_start_record",
            "slice": COLD_START_SLICE,
            "record_id": self.record_id,
            "title": self.title,
            "project_ref": self.project_ref,
            "map_ref": self.map_ref,
            "map_age_days": self.map_age_days,
            "map_entries": self.map_entries,
            "project_files": self.project_files,
            "covered_files": self.covered_files,
            "areas": [
                {"section": a.section, "entries": a.entries,
                 "stale_entries": a.stale_entries}
                for a in self.areas],
            "mode": self.mode,
            "stage_plan": list(self.stage_plan),
            "opened_on": self.opened_on,
            "opened_by": self.opened_by,
            "source": self.source,
            "origin_session": self.origin_session,
        }


def mode_of(record: Any) -> str:
    """The mode one record's evidence derives, never chosen.

    No map at all derives ``rebuild-from-scratch``;
    a map that stands stale in any area, covers
    fewer files than the project holds, or has
    stood for :data:`STALE_AGE_DAYS` days or more
    derives ``background-rebuild`` - the coder
    works from the stale-but-usable map while it
    rebuilds; a fresh, whole map derives
    ``serve-fresh`` and no rebuild at all.
    """
    current = record if isinstance(record, ColdStartRecord) \
        else validate_record(record)
    if current.map_entries == 0:
        return "rebuild-from-scratch"
    if current.total_stale > 0 \
            or current.covered_files < current.project_files \
            or current.map_age_days >= STALE_AGE_DAYS:
        return "background-rebuild"
    return "serve-fresh"


def _stage_order(areas: Tuple[ColdStartArea, ...],
                 stale_only: bool) -> Tuple[ColdStartArea, ...]:
    picked = [a for a in areas if a.stale_entries > 0] if stale_only \
        else list(areas)
    return tuple(sorted(
        picked,
        key=lambda a: (-a.stale_entries, -a.entries,
                       AREAS.index(a.section))))


def stage_plan_of(record: Any) -> Tuple[str, ...]:
    """The stage plan one record's evidence derives, in order.

    A fresh map derives the one stage
    ``serve-fresh-map``. A background rebuild
    derives ``serve-stale-map`` first - the coder
    is useful at once - then one ``rebuild-area``
    stage per stale area, the stalest area first
    (then the largest, then map order), and
    ``verify-map`` last. A from-scratch rebuild
    derives one ``rebuild-area`` stage per area
    in the same derived order and ``verify-map``
    last - or ``rebuild-whole-map`` when no area
    evidence stands at all.
    """
    current = record if isinstance(record, ColdStartRecord) \
        else validate_record(record)
    mode = mode_of(current)
    if mode == "serve-fresh":
        return ("serve-fresh-map",)
    if mode == "background-rebuild":
        stages = ["serve-stale-map"]
        stages.extend(
            f"rebuild-area:{a.section}"
            for a in _stage_order(current.areas, stale_only=True))
        stages.append("verify-map")
        return tuple(stages)
    if not current.areas:
        return ("rebuild-whole-map", "verify-map")
    stages = [
        f"rebuild-area:{a.section}"
        for a in _stage_order(current.areas, stale_only=False)]
    stages.append("verify-map")
    return tuple(stages)


def usable_entries_of(record: Any) -> int:
    """Map entries usable at once under one record (derived).

    A fresh or stale-but-usable map serves every
    entry that does not stand stale; a project
    with no map serves none.
    """
    current = record if isinstance(record, ColdStartRecord) \
        else validate_record(record)
    if current.map_entries == 0:
        return 0
    return sum(a.usable_entries for a in current.areas)


def _check_record_ref(value: Any) -> ColdStartRecord:
    if isinstance(value, ColdStartRecord):
        return value
    return validate_record(value)


def validate_record(record: Any) -> ColdStartRecord:
    """Validate one record record into a ColdStartRecord.

    Accepts a record or a mapping naming a
    ``title`` (or ``name`` / ``subject``), a
    ``project_ref`` (or ``project``), a ``map_ref``
    (or ``map``), the evidence - ``map_age_days``
    (or ``age_days`` / ``age``), ``map_entries``
    (or ``entries``), ``project_files`` (or
    ``files``) and ``covered_files`` (or
    ``covered``) - ``areas``, an ``opened_on`` (or
    ``day`` / ``date``), an ``opened_by`` (or
    ``recorder`` / ``by`` / ``who``), a ``source``,
    an ``origin_session`` (or ``session``) and an
    optional ``record_id`` (or ``id``). Naming two
    spellings of one field with different values
    refuses, and unknown keys refuse. A stored
    ``mode`` or ``stage_plan`` is NOT a field: the
    plan is derived, and a mapping naming one
    refuses as an unknown key.
    """
    if isinstance(record, ColdStartRecord):
        return record
    if not isinstance(record, dict):
        raise ValueError(
            f"a record record must be a mapping, got {record!r}")
    unknown = set(record) - _RECORD_KEYS
    if unknown:
        raise ValueError(
            "unknown record keys: %s" % ", ".join(sorted(unknown)))

    def _needed(spellings: Tuple[str, ...], what: str) -> Any:
        value = _pick_any(record, spellings, what)
        if value is None:
            raise ValueError(f"a record is missing its {what}")
        return value

    kwargs: Dict[str, Any] = {
        "title": _needed(("title", "name", "subject"), "title"),
        "project_ref": _needed(("project_ref", "project"), "project ref"),
        "map_ref": _needed(("map_ref", "map"), "map ref"),
        "map_age_days": _needed(
            ("map_age_days", "age_days", "age"), "map age"),
        "map_entries": _needed(("map_entries", "entries"), "map entries"),
        "project_files": _needed(
            ("project_files", "files"), "project files"),
        "covered_files": _needed(
            ("covered_files", "covered"), "covered files"),
    }
    areas = _pick_any(record, ("areas",), "areas")
    if areas is not None:
        kwargs["areas"] = areas
    for field, spellings in (
            ("opened_on", ("opened_on", "day", "date")),
            ("opened_by", ("opened_by", "recorder", "by", "who")),
            ("source", ("source",)),
            ("origin_session", ("origin_session", "session"))):
        value = _pick_any(record, spellings, field)
        if value is not None:
            kwargs[field] = value
    record_id = _pick_any(record, ("record_id", "id"), "record ids")
    if record_id is not None:
        kwargs["record_id"] = record_id
    return ColdStartRecord(**kwargs)


def build_record(record: Any = None, **kwargs: Any) -> ColdStartRecord:
    """Build one validated record, from a mapping or field words."""
    if isinstance(record, ColdStartRecord) and not kwargs:
        return record
    if isinstance(record, dict) or record is None:
        merged: Dict[str, Any] = {}
        if isinstance(record, dict):
            merged.update(record)
        merged.update(kwargs)
        return validate_record(merged)
    return validate_record(record)


def _areas_from_counts(counts: Dict[str, int],
                       stale: Any) -> Tuple[ColdStartArea, ...]:
    stale_map: Dict[str, int] = {}
    if stale is not None:
        if not isinstance(stale, dict):
            raise ValueError(
                f"stale evidence must be a mapping by area, got {stale!r}")
        for section, count in stale.items():
            stale_map[normalize_section(section)] = _check_count(
                count, "an area's stale entries")
    areas = []
    for section in AREAS:
        if section not in counts and section not in stale_map:
            continue
        areas.append(ColdStartArea(
            section=section, entries=counts.get(section, 0),
            stale_entries=stale_map.get(section, 0)))
    for section in stale_map:
        if section not in counts:
            raise ValueError(
                f"stale evidence names the {section} area, "
                f"which the map does not carry")
    return tuple(areas)


def record_from_map_book(book: Any, *, project_ref: Any, map_ref: Any,
                         map_age_days: Any, project_files: Any,
                         covered_files: Any, stale: Any = None,
                         opened_on: Any = "2026-11-09",
                         opened_by: Any = "Volmarr",
                         origin_session: Any = "session-m169",
                         source: Any = "cold start",
                         title: Any = None,
                         record_id: Any = None) -> ColdStartRecord:
    """Raise a cold-start record over one project memory map book.

    The book is judged by the map layer's own
    validator (M-150); its entries are counted by
    area and nothing else of the book crosses -
    no entry title, detail or ref is carried. The
    caller's evidence - the map's age, the
    project's files, the map's coverage and, per
    area, how many entries stand stale - is the
    record's evidence whole.
    """
    current = _validate_map_book(book) if not isinstance(book, MemoryMapBook) \
        else book
    counts: Dict[str, int] = {}
    for entry in current.entries:
        counts[entry.section] = counts.get(entry.section, 0) + 1
    return ColdStartRecord(
        title=title if title is not None else (
            f"opening {project_ref} over its held map"),
        project_ref=project_ref, map_ref=map_ref,
        map_age_days=map_age_days, map_entries=len(current.entries),
        project_files=project_files, covered_files=covered_files,
        areas=_areas_from_counts(counts, stale),
        opened_on=opened_on, opened_by=opened_by,
        origin_session=origin_session, source=source,
        record_id=record_id)


def record_from_map_entry(entry: Any, *, project_ref: Any, map_ref: Any,
                          map_age_days: Any, project_files: Any,
                          covered_files: Any, stale: Any = False,
                          opened_on: Any = "2026-11-09",
                          opened_by: Any = "Volmarr",
                          origin_session: Any = "session-m169",
                          source: Any = "cold start",
                          title: Any = None,
                          record_id: Any = None) -> ColdStartRecord:
    """Raise a cold-start record over one project memory map entry.

    The entry is judged by the map layer's own
    validator (M-150); the record's map is the one
    area the entry stands in, counted once - its
    id alone crosses, in ``map_ref``'s naming by
    the caller, and the entry's own words never
    cross. ``stale`` says whether that one entry
    stands stale, as evidence.
    """
    current = _validate_map_entry(entry) if not isinstance(
        entry, MemoryMapEntry) else entry
    return ColdStartRecord(
        title=title if title is not None else (
            f"opening {project_ref} over one map entry"),
        project_ref=project_ref, map_ref=map_ref,
        map_age_days=map_age_days, map_entries=1,
        project_files=project_files, covered_files=covered_files,
        areas=(ColdStartArea(
            section=current.section, entries=1,
            stale_entries=1 if stale else 0),),
        opened_on=opened_on, opened_by=opened_by,
        origin_session=origin_session, source=source,
        record_id=record_id)


def record_from_session_situation(situation: Any, *, map_ref: Any,
                                  map_age_days: Any, project_files: Any,
                                  covered_files: Any, stale: Any = None,
                                  opened_on: Any = "2026-11-09",
                                  opened_by: Any = "Volmarr",
                                  origin_session: Any = None,
                                  source: Any = "cold start",
                                  title: Any = None,
                                  record_id: Any = None) -> ColdStartRecord:
    """Raise a cold-start record over one session situation.

    The situation is judged by the session-memory
    layer's own validator (M-153); the project it
    names is its own session ref, the map is the
    memory it carries - counted by area, the
    notes' own words never crossing - and the
    session it opened in defaults to the
    situation's own session ref.
    """
    current = _validate_situation(situation) if not isinstance(
        situation, SessionSituation) else situation
    counts: Dict[str, int] = {}
    for note in current.memory:
        counts[note.section] = counts.get(note.section, 0) + 1
    return ColdStartRecord(
        title=title if title is not None else (
            f"opening {current.session_ref} over its carried memory"),
        project_ref=current.session_ref, map_ref=map_ref,
        map_age_days=map_age_days, map_entries=len(current.memory),
        project_files=project_files, covered_files=covered_files,
        areas=_areas_from_counts(counts, stale),
        opened_on=opened_on, opened_by=opened_by,
        origin_session=(origin_session if origin_session is not None
                        else current.session_ref),
        source=source, record_id=record_id)


def inspect_opening_source(piece: Any) -> Dict[str, Any]:
    """Judge one opening source piece by its own layer's validator.

    A project memory map book, a single map entry
    and a session situation are each judged by
    their own layer (M-150 / M-153); the answer
    names the kind of piece and the ids and counts
    that may cross - never the piece's own words.
    Anything else refuses.
    """
    if isinstance(piece, MemoryMapBook):
        book = _validate_map_book(piece)
        return {"kind": "project-memory-map-book",
                "title": book.title,
                "map_entries": len(book.entries)}
    if isinstance(piece, MemoryMapEntry):
        entry = _validate_map_entry(piece)
        return {"kind": "project-memory-map-entry",
                "entry_id": entry.entry_id, "section": entry.section}
    if isinstance(piece, SessionSituation):
        situation = _validate_situation(piece)
        return {"kind": "session-situation",
                "session_ref": situation.session_ref,
                "map_entries": len(situation.memory)}
    if isinstance(piece, dict):
        for road, kind in (
                (_validate_map_entry, "project-memory-map-entry"),
                (_validate_situation, "session-situation")):
            try:
                judged = road(piece)
            except Exception:
                continue
            return inspect_opening_source(judged)
        raise ValueError(
            "an opening source must be a map book, a map entry "
            "or a session situation")
    raise ValueError(
        f"an opening source must be a map book, a map entry "
        f"or a session situation, got {piece!r}")


# ---------------------------------------------------------------------
# The readiness panel: the whole book, derived.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class ColdStartPanelRow:
    """One record carried whole on the readiness panel.

    Every field is read off its record: the mode
    the evidence derives, the entries usable now,
    the stale entries still rebuilding, how many
    areas the plan rebuilds, the plan's stage
    count and its first stage. A row naming a
    value its record does not derive refuses when
    judged against that record.
    """

    record_id: str
    title: str
    project_ref: str
    mode: str
    usable_entries: int
    total_stale: int
    rebuilding_areas: int
    stage_count: int
    first_stage: str
    opened_on: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "record_id", _check_word(self.record_id, "a record id"))
        object.__setattr__(
            self, "title", _check_title(self.title, "a row's title"))
        object.__setattr__(
            self, "project_ref", _check_word(self.project_ref, "a project ref"))
        object.__setattr__(self, "mode", normalize_mode(self.mode))
        for field in ("usable_entries", "total_stale",
                      "rebuilding_areas", "stage_count"):
            object.__setattr__(
                self, field, _check_count(getattr(self, field), f"a row's {field}"))
        object.__setattr__(
            self, "first_stage", _check_stage(self.first_stage))
        object.__setattr__(
            self, "opened_on", _check_day(self.opened_on, "an opening day"))

    @property
    def sort_key(self) -> Tuple[int, str, str]:
        return (MODES.index(self.mode), self.title, self.record_id)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "cold_start_panel_row",
            "slice": COLD_START_SLICE,
            "record_id": self.record_id,
            "title": self.title,
            "project_ref": self.project_ref,
            "mode": self.mode,
            "usable_entries": self.usable_entries,
            "total_stale": self.total_stale,
            "rebuilding_areas": self.rebuilding_areas,
            "stage_count": self.stage_count,
            "first_stage": self.first_stage,
            "opened_on": self.opened_on,
        }


def _row_for_record(record: ColdStartRecord) -> ColdStartPanelRow:
    if record.record_id is None:
        raise ValueError(
            "a panel row must name its record - a record "
            "with no id refuses derivation")
    plan = stage_plan_of(record)
    rebuilding = sum(1 for s in plan if s.startswith("rebuild-area:"))
    if "rebuild-whole-map" in plan:
        rebuilding = 1
    return ColdStartPanelRow(
        record_id=record.record_id, title=record.title,
        project_ref=record.project_ref, mode=mode_of(record),
        usable_entries=usable_entries_of(record),
        total_stale=record.total_stale,
        rebuilding_areas=rebuilding, stage_count=len(plan),
        first_stage=plan[0], opened_on=record.opened_on)


def _check_row_ref(value: Any) -> ColdStartPanelRow:
    if isinstance(value, ColdStartPanelRow):
        return value
    return validate_row(value)


def validate_row(row: Any, record: Any = None) -> ColdStartPanelRow:
    """Validate one panel row into a ColdStartPanelRow.

    Accepts a row or a mapping naming its fields
    (``usable_entries`` or ``usable``,
    ``total_stale`` or ``stale``,
    ``rebuilding_areas`` or ``rebuilding``,
    ``stage_count`` or ``stages``). With *record*
    given, the row is judged against the row that
    record derives.
    """
    if isinstance(row, ColdStartPanelRow):
        current = row
    elif isinstance(row, dict):
        unknown = set(row) - _ROW_KEYS
        if unknown:
            raise ValueError(
                "unknown row keys: %s" % ", ".join(sorted(unknown)))

        def _needed(spellings: Tuple[str, ...], what: str) -> Any:
            value = _pick_any(row, spellings, what)
            if value is None:
                raise ValueError(f"a row is missing its {what}")
            return value

        current = ColdStartPanelRow(
            record_id=_needed(("record_id", "id"), "record id"),
            title=_needed(("title",), "title"),
            project_ref=_needed(("project_ref",), "project ref"),
            mode=_needed(("mode",), "mode"),
            usable_entries=_needed(
                ("usable_entries", "usable"), "usable entries"),
            total_stale=_needed(("total_stale", "stale"), "total stale"),
            rebuilding_areas=_needed(
                ("rebuilding_areas", "rebuilding"), "rebuilding areas"),
            stage_count=_needed(("stage_count", "stages"), "stage count"),
            first_stage=_needed(("first_stage",), "first stage"),
            opened_on=_needed(("opened_on",), "opening day"))
    else:
        raise ValueError(f"a row must be a mapping, got {row!r}")
    if record is not None:
        derived = _row_for_record(_check_record_ref(record))
        if current != derived:
            raise ValueError(
                "a stored row disagrees with the row its "
                "record derives")
    return current


def build_row(row: Any = None, record: Any = None,
              **kwargs: Any) -> ColdStartPanelRow:
    """Build one validated row, from a mapping or field words."""
    if isinstance(row, ColdStartPanelRow) and not kwargs:
        return validate_row(row, record)
    if isinstance(row, dict) or row is None:
        merged: Dict[str, Any] = {}
        if isinstance(row, dict):
            merged.update(row)
        merged.update(kwargs)
        return validate_row(merged, record)
    return validate_row(row, record)


@dataclass(frozen=True)
class ModeCount:
    """How many panel rows stand in one mode."""

    mode: str
    items: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "mode", normalize_mode(self.mode))
        object.__setattr__(
            self, "items", _check_count(self.items, "a mode count"))

    def to_record(self) -> Dict[str, Any]:
        return {"mode": self.mode, "items": self.items}


def _check_mode_count_ref(value: Any) -> ModeCount:
    if isinstance(value, ModeCount):
        return value
    if not isinstance(value, dict):
        raise ValueError(f"a mode count must be a mapping, got {value!r}")
    unknown = set(value) - _MODE_COUNT_KEYS
    if unknown:
        raise ValueError(
            "unknown mode count keys: %s" % ", ".join(sorted(unknown)))
    mode = _pick_any(value, ("mode",), "modes")
    items = _pick_any(value, ("items", "count"), "counts")
    if mode is None or items is None:
        raise ValueError("a mode count names its mode and its count")
    return ModeCount(mode=mode, items=items)


def _panel_account(total_records: int, total_fresh: int,
                   total_warming: int, total_cold: int,
                   distinct_projects: int,
                   mode_counts: Tuple[ModeCount, ...],
                   as_of: str) -> Tuple[str, ...]:
    modes = ", ".join(
        f"{count.mode} {count.items}" for count in mode_counts)
    return (
        f"The cold-start panel holds {total_records} openings "
        f"as of {as_of}: {total_fresh} served fresh, "
        f"{total_warming} rebuilding in the background and "
        f"{total_cold} rebuilding from scratch over "
        f"{distinct_projects} projects: {modes}.",
        "Rows stand by mode - from-scratch rebuilds first, "
        "then background rebuilds, then fresh servings - then "
        "title, then record id, so two panels of one book diff "
        "cleanly, line by line.",
        "Every row shows what is usable now beside what is "
        "still rebuilding: a background opening serves its "
        "stale-but-usable map at once while its plan rebuilds "
        "the stalest areas first.",
        "The panel is read off the book at call time - it is "
        "derived, never stored loose - and standing on this "
        "panel starts no rebuild: stages are marked done on "
        "the held book alone.",
    )


@dataclass(frozen=True)
class ColdStartPanel:
    """The readiness panel of one book, derived whole.

    ``rows`` are the book's records carried whole,
    in panel order; the totals are the rows' own
    counts, judged at construction, and the
    ``account`` is the panel's own derived telling
    of itself. A panel whose stored shape
    disagrees with its rows refuses.
    """

    rows: Tuple[ColdStartPanelRow, ...]
    total_records: int
    total_fresh: int
    total_warming: int
    total_cold: int
    distinct_projects: int
    mode_counts: Tuple[ModeCount, ...]
    as_of: str
    account: Tuple[str, ...]
    panel_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.panel_id is not None:
            object.__setattr__(
                self, "panel_id", _check_word(self.panel_id, "a panel id"))
        if isinstance(self.rows, (str, bytes)) \
                or not isinstance(self.rows, (list, tuple)):
            raise ValueError(f"a panel's rows must be a list, got {self.rows!r}")
        rows = tuple(_check_row_ref(r) for r in self.rows)
        if not rows:
            raise ValueError("a panel holds at least one row")
        if rows != tuple(sorted(rows, key=lambda r: r.sort_key)):
            raise ValueError("a panel's rows must stand in panel order")
        seen = set()
        for row in rows:
            if row.record_id in seen:
                raise ValueError(
                    f"a record named {row.record_id!r} stands twice "
                    f"on one panel")
            seen.add(row.record_id)
        object.__setattr__(self, "rows", rows)
        for field in ("total_records", "total_fresh", "total_warming",
                      "total_cold", "distinct_projects"):
            object.__setattr__(
                self, field, _check_count(getattr(self, field), f"a panel's {field}"))
        if self.total_records != len(rows):
            raise ValueError("a panel's total must be its rows' count")
        fresh = sum(1 for r in rows if r.mode == "serve-fresh")
        warming = sum(1 for r in rows if r.mode == "background-rebuild")
        cold = sum(1 for r in rows if r.mode == "rebuild-from-scratch")
        if (self.total_fresh, self.total_warming, self.total_cold) != (
                fresh, warming, cold):
            raise ValueError("a panel's mode totals must be its rows' own")
        if self.distinct_projects != len({r.project_ref for r in rows}):
            raise ValueError(
                "a panel's distinct projects must be its rows' own")
        tallies = {mode: sum(1 for r in rows if r.mode == mode)
                   for mode in MODES}
        expected_counts = tuple(
            ModeCount(mode=mode, items=tallies[mode])
            for mode in MODES if tallies[mode])
        counts = tuple(_check_mode_count_ref(c) for c in self.mode_counts)
        if counts != expected_counts:
            raise ValueError("a panel's mode counts must be its rows' own")
        object.__setattr__(self, "mode_counts", counts)
        object.__setattr__(
            self, "as_of", _check_day(self.as_of, "an as-of day"))
        if self.as_of != max(r.opened_on for r in rows):
            raise ValueError("a panel's as-of day is its latest opening")
        account = _check_account(self.account)
        if account != _panel_account(
                self.total_records, self.total_fresh, self.total_warming,
                self.total_cold, self.distinct_projects, counts, self.as_of):
            raise ValueError("a panel's account must be its derived account")
        object.__setattr__(self, "account", account)

    def row_for(self, record_id: Any) -> ColdStartPanelRow:
        """The row one record id names on this panel."""
        wanted = _check_word(record_id, "a record id")
        for row in self.rows:
            if row.record_id == wanted:
                return row
        raise KeyError(f"no row for record {wanted!r}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "cold_start_panel",
            "slice": COLD_START_SLICE,
            "panel_id": self.panel_id,
            "rows": [
                {key: value for key, value in row.to_record().items()
                 if key not in ("type", "slice")}
                for row in self.rows],
            "total_records": self.total_records,
            "total_fresh": self.total_fresh,
            "total_warming": self.total_warming,
            "total_cold": self.total_cold,
            "distinct_projects": self.distinct_projects,
            "mode_counts": [c.to_record() for c in self.mode_counts],
            "as_of": self.as_of,
            "account": list(self.account),
        }


def _held_records(source: Any) -> Tuple[ColdStartRecord, ...]:
    if isinstance(source, ColdStartBook):
        return source.records
    if isinstance(source, ColdStartRegistry):
        return source.list_records()
    if isinstance(source, (list, tuple)):
        return tuple(_check_record_ref(item) for item in source)
    raise ValueError(f"cold-start records are needed, got {source!r}")


def derive_panel(source: Any) -> ColdStartPanel:
    """Derive the readiness panel from one book.

    The rows are the book's records carried whole,
    in panel order: by mode - from-scratch first,
    then background rebuilds, then fresh servings
    - then title, then record id, each showing
    what is usable now beside what is still
    rebuilding. *source* is a book or a registry.
    A source holding no record refuses - a panel
    of nothing is no panel.
    """
    records = _held_records(source)
    if not records:
        raise ValueError("a panel needs at least one cold-start record")
    rows = tuple(sorted(
        (_row_for_record(r) for r in records), key=lambda r: r.sort_key))
    tallies = {mode: sum(1 for r in rows if r.mode == mode) for mode in MODES}
    mode_counts = tuple(
        ModeCount(mode=mode, items=tallies[mode])
        for mode in MODES if tallies[mode])
    distinct = len({r.project_ref for r in rows})
    as_of = max(r.opened_on for r in rows)
    return ColdStartPanel(
        rows=rows, total_records=len(rows),
        total_fresh=tallies["serve-fresh"],
        total_warming=tallies["background-rebuild"],
        total_cold=tallies["rebuild-from-scratch"],
        distinct_projects=distinct, mode_counts=mode_counts,
        account=_panel_account(
            len(rows), tallies["serve-fresh"],
            tallies["background-rebuild"],
            tallies["rebuild-from-scratch"], distinct, mode_counts, as_of),
        as_of=as_of)


def validate_panel(panel: Any, source: Any = None) -> ColdStartPanel:
    """Validate one panel into a ColdStartPanel.

    Accepts a panel or a mapping naming ``rows``
    (or ``records``), the totals, ``mode_counts``
    (or ``modes``), an ``as_of`` (or ``day``), an
    ``account`` (or ``statements``) and an optional
    ``panel_id`` (or ``id``). With *source* given
    (a book), the panel is judged against the
    panel derived from that book.
    """
    if isinstance(panel, ColdStartPanel):
        current = panel
    elif isinstance(panel, dict):
        unknown = set(panel) - _PANEL_KEYS
        if unknown:
            raise ValueError(
                "unknown panel keys: %s" % ", ".join(sorted(unknown)))

        def _needed(spellings: Tuple[str, ...], what: str) -> Any:
            value = _pick_any(panel, spellings, what)
            if value is None:
                raise ValueError(f"a panel is missing its {what}")
            return value

        kwargs: Dict[str, Any] = {
            "rows": _needed(("rows", "records"), "rows"),
            "total_records": _needed(("total_records", "total"), "total"),
            "total_fresh": _needed(("total_fresh", "fresh"), "fresh total"),
            "total_warming": _needed(
                ("total_warming", "warming"), "warming total"),
            "total_cold": _needed(("total_cold", "cold"), "cold total"),
            "distinct_projects": _needed(
                ("distinct_projects", "projects"), "distinct projects"),
            "mode_counts": _needed(("mode_counts", "modes"), "mode counts"),
            "as_of": _needed(("as_of", "day"), "as-of day"),
            "account": _needed(("account", "statements"), "account"),
        }
        panel_id = _pick_any(panel, ("panel_id", "id"), "panel ids")
        if panel_id is not None:
            kwargs["panel_id"] = panel_id
        current = ColdStartPanel(**kwargs)
    else:
        raise ValueError(f"a panel must be a mapping, got {panel!r}")
    if source is not None:
        derived = derive_panel(source)
        if (current.rows != derived.rows
                or current.total_records != derived.total_records
                or current.total_fresh != derived.total_fresh
                or current.total_warming != derived.total_warming
                or current.total_cold != derived.total_cold
                or current.distinct_projects != derived.distinct_projects
                or current.mode_counts != derived.mode_counts
                or current.as_of != derived.as_of
                or current.account != derived.account):
            raise ValueError(
                "a stored panel disagrees with the panel "
                "derived from its book")
    return current


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> ColdStartPanel:
    """Build one validated panel, from a mapping or field words."""
    if isinstance(panel, ColdStartPanel) and not kwargs:
        return validate_panel(panel, source)
    if isinstance(panel, dict) or panel is None:
        merged: Dict[str, Any] = {}
        if isinstance(panel, dict):
            merged.update(panel)
        merged.update(kwargs)
        return validate_panel(merged, source)
    return validate_panel(panel, source)


# ---------------------------------------------------------------------
# The cold-start verdict: the whole book judged, as data.
# ---------------------------------------------------------------------


def _verdict_word(total_cold: int, total_warming: int) -> str:
    """The verdict word a book's own tallies derive.

    ``cold`` while any project stands with no map
    at all; ``warming`` while any map rebuilds in
    the background; ``kind`` while every opening
    serves a fresh map.
    """
    if total_cold >= 1:
        return "cold"
    if total_warming >= 1:
        return "warming"
    return "kind"


@dataclass(frozen=True)
class ColdStartVerdict:
    """One book's cold-start verdict, derived from its records.

    The tallies are the records' own, judged at
    construction, and ``verdict`` is the word
    those tallies derive - a stored verdict naming
    any other word refuses.
    """

    total_records: int
    total_fresh: int
    total_warming: int
    total_cold: int
    distinct_projects: int
    earliest_on: str
    latest_on: str
    verdict: str

    def __post_init__(self) -> None:
        for field in ("total_records", "total_fresh", "total_warming",
                      "total_cold", "distinct_projects"):
            object.__setattr__(
                self, field, _check_count(getattr(self, field), f"a verdict's {field}"))
        if self.total_records < 1:
            raise ValueError("a verdict stands over at least one record")
        if self.total_fresh + self.total_warming + self.total_cold != (
                self.total_records):
            raise ValueError("a verdict's mode tallies must sum to its total")
        object.__setattr__(
            self, "earliest_on", _check_day(self.earliest_on, "an earliest day"))
        object.__setattr__(
            self, "latest_on", _check_day(self.latest_on, "a latest day"))
        if self.latest_on < self.earliest_on:
            raise ValueError("a verdict's latest day precedes its earliest")
        word = _clean_text(self.verdict, "a verdict")
        if word not in VERDICT_WORDS:
            raise ValueError(
                "a verdict is one of %s, got %r"
                % ("/".join(VERDICT_WORDS), word))
        if word != _verdict_word(self.total_cold, self.total_warming):
            raise ValueError(
                "a verdict's word must be the word its tallies derive")
        object.__setattr__(self, "verdict", word)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "cold_start_verdict",
            "slice": COLD_START_SLICE,
            "total_records": self.total_records,
            "total_fresh": self.total_fresh,
            "total_warming": self.total_warming,
            "total_cold": self.total_cold,
            "distinct_projects": self.distinct_projects,
            "earliest_on": self.earliest_on,
            "latest_on": self.latest_on,
            "verdict": self.verdict,
        }


def derive_verdict(source: Any) -> ColdStartVerdict:
    """Derive the cold-start verdict for one whole book."""
    records = _held_records(source)
    if not records:
        raise ValueError("a verdict needs at least one cold-start record")
    tallies = {mode: 0 for mode in MODES}
    for record in records:
        tallies[mode_of(record)] += 1
    days = [r.opened_on for r in records]
    return ColdStartVerdict(
        total_records=len(records),
        total_fresh=tallies["serve-fresh"],
        total_warming=tallies["background-rebuild"],
        total_cold=tallies["rebuild-from-scratch"],
        distinct_projects=len({r.project_ref for r in records}),
        earliest_on=min(days), latest_on=max(days),
        verdict=_verdict_word(
            tallies["rebuild-from-scratch"],
            tallies["background-rebuild"]))


def _check_verdict_ref(value: Any) -> ColdStartVerdict:
    if isinstance(value, ColdStartVerdict):
        return value
    return validate_verdict(value)


def validate_verdict(verdict: Any, source: Any = None) -> ColdStartVerdict:
    """Validate one verdict into a ColdStartVerdict.

    Accepts a verdict or a mapping naming its
    tallies. With *source* given, the verdict is
    judged against the verdict derived for that
    book.
    """
    if isinstance(verdict, ColdStartVerdict):
        current = verdict
    elif isinstance(verdict, dict):
        unknown = set(verdict) - _VERDICT_KEYS
        if unknown:
            raise ValueError(
                "unknown verdict keys: %s" % ", ".join(sorted(unknown)))

        def _needed(spellings: Tuple[str, ...], what: str) -> Any:
            value = _pick_any(verdict, spellings, what)
            if value is None:
                raise ValueError(f"a verdict is missing its {what}")
            return value

        current = ColdStartVerdict(
            total_records=_needed(("total_records", "total"), "total"),
            total_fresh=_needed(("total_fresh", "fresh"), "fresh total"),
            total_warming=_needed(
                ("total_warming", "warming"), "warming total"),
            total_cold=_needed(("total_cold", "cold"), "cold total"),
            distinct_projects=_needed(
                ("distinct_projects", "projects"), "distinct projects"),
            earliest_on=_needed(("earliest_on", "earliest"), "earliest day"),
            latest_on=_needed(("latest_on", "latest"), "latest day"),
            verdict=_needed(("verdict",), "verdict"))
    else:
        raise ValueError(f"a verdict must be a mapping, got {verdict!r}")
    if source is not None:
        if current != derive_verdict(source):
            raise ValueError(
                "a stored verdict disagrees with the verdict "
                "derived for its book")
    return current


def build_verdict(verdict: Any = None, source: Any = None,
                  **kwargs: Any) -> ColdStartVerdict:
    """Build one validated verdict, from a mapping or field words."""
    if isinstance(verdict, ColdStartVerdict) and not kwargs:
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict) or verdict is None:
        merged: Dict[str, Any] = {}
        if isinstance(verdict, dict):
            merged.update(verdict)
        merged.update(kwargs)
        return validate_verdict(merged, source)
    return validate_verdict(verdict, source)


# ---------------------------------------------------------------------
# Rebuild progress: the derived plan, walked in order.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class ColdStartProgress:
    """One record's rebuild progress, judged against its plan.

    ``stages`` is the record's derived plan whole;
    ``completed`` is a PREFIX of that plan - the
    stages marked done, in plan order, never
    skipping one; ``next_stage`` is the stage the
    plan names next, or ``None`` when the plan
    stands complete, and ``complete`` says so.
    A progress naming any other shape refuses.
    """

    record_id: str
    stages: Tuple[str, ...]
    completed: Tuple[str, ...] = ()
    next_stage: Optional[str] = None
    complete: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "record_id", _check_word(self.record_id, "a record id"))
        if isinstance(self.stages, (str, bytes)) \
                or not isinstance(self.stages, (list, tuple)) or not self.stages:
            raise ValueError("a progress carries its stage plan")
        stages = tuple(_check_stage(s) for s in self.stages)
        object.__setattr__(self, "stages", stages)
        if isinstance(self.completed, (str, bytes)) \
                or not isinstance(self.completed, (list, tuple)):
            raise ValueError("a progress's completed stages must be a list")
        completed = tuple(_check_stage(s) for s in self.completed)
        if completed != stages[:len(completed)]:
            raise ValueError(
                "completed stages must walk the plan in order, "
                "as its prefix - no stage is skipped")
        object.__setattr__(self, "completed", completed)
        expected_next = stages[len(completed)] if len(completed) < len(stages) else None
        if self.next_stage is not None:
            object.__setattr__(
                self, "next_stage", _check_stage(self.next_stage))
            if self.next_stage != expected_next:
                raise ValueError(
                    "a progress's next stage must be the plan's next stage")
        elif expected_next is not None:
            object.__setattr__(self, "next_stage", expected_next)
        expected_complete = expected_next is None
        if not isinstance(self.complete, bool):
            raise ValueError("a progress's complete flag must be a boolean")
        if self.complete != expected_complete:
            raise ValueError(
                "a progress's complete flag must be its plan's own")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "cold_start_progress",
            "slice": COLD_START_SLICE,
            "record_id": self.record_id,
            "stages": list(self.stages),
            "completed": list(self.completed),
            "next_stage": self.next_stage,
            "complete": self.complete,
        }


def derive_progress(record: Any, completed: Any = ()) -> ColdStartProgress:
    """Derive one record's progress from its plan and its done stages."""
    current = _check_record_ref(record)
    if current.record_id is None:
        raise ValueError("progress names its record - a record with no id refuses")
    return ColdStartProgress(
        record_id=current.record_id, stages=stage_plan_of(current),
        completed=tuple(completed),
        complete=len(tuple(completed)) == len(stage_plan_of(current)))


def _check_progress_ref(value: Any) -> ColdStartProgress:
    if isinstance(value, ColdStartProgress):
        return value
    return validate_progress(value)


def validate_progress(progress: Any, record: Any = None) -> ColdStartProgress:
    """Validate one progress into a ColdStartProgress.

    Accepts a progress or a mapping naming a
    ``record_id`` (or ``id``), ``stages`` (or
    ``plan``), ``completed`` (or ``done``), a
    ``next_stage`` (or ``next``) and a ``complete``
    (or ``finished``) flag. With *record* given,
    the progress is judged against the progress
    that record's plan derives.
    """
    if isinstance(progress, ColdStartProgress):
        current = progress
    elif isinstance(progress, dict):
        unknown = set(progress) - _PROGRESS_KEYS
        if unknown:
            raise ValueError(
                "unknown progress keys: %s" % ", ".join(sorted(unknown)))
        record_id = _pick_any(progress, ("record_id", "id"), "record ids")
        stages = _pick_any(progress, ("stages", "plan"), "stage plans")
        if record_id is None or stages is None:
            raise ValueError("a progress names its record and its plan")
        completed = _pick_any(progress, ("completed", "done"), "done stages")
        kwargs: Dict[str, Any] = {
            "record_id": record_id, "stages": stages,
            "completed": () if completed is None else completed}
        next_stage = _pick_any(progress, ("next_stage", "next"), "next stages")
        if next_stage is not None:
            kwargs["next_stage"] = next_stage
        complete = _pick_any(progress, ("complete", "finished"), "flags")
        if complete is not None:
            kwargs["complete"] = complete
        current = ColdStartProgress(**kwargs)
    else:
        raise ValueError(f"a progress must be a mapping, got {progress!r}")
    if record is not None:
        derived = derive_progress(record, current.completed)
        if current != derived:
            raise ValueError(
                "a stored progress disagrees with the progress "
                "its record's plan derives")
    return current


def build_progress(progress: Any = None, record: Any = None,
                   **kwargs: Any) -> ColdStartProgress:
    """Build one validated progress, from a mapping or field words."""
    if isinstance(progress, ColdStartProgress) and not kwargs:
        return validate_progress(progress, record)
    if isinstance(progress, dict) or progress is None:
        merged: Dict[str, Any] = {}
        if isinstance(progress, dict):
            merged.update(progress)
        merged.update(kwargs)
        return validate_progress(merged, record)
    return validate_progress(progress, record)


# ---------------------------------------------------------------------
# The book: openings held whole.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class ColdStartBook:
    """One cold-start book: its records, in held order.

    ``records`` are the opening records, in held
    order - one per project, so an opening never
    forks; ``panels`` are the book's derivations -
    panels of the book, judged against the book's
    records by :func:`validate_book`;
    ``canon_note`` is the book's own note. This
    book is the book file's shape: the shipped
    example is one book, and a real book file is a
    new file in this shape.
    """

    title: str = ""
    records: Tuple[ColdStartRecord, ...] = ()
    panels: Tuple[ColdStartPanel, ...] = ()
    canon_note: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_title(self.title, "a book's title"))
        if isinstance(self.records, (str, bytes)) \
                or not isinstance(self.records, (list, tuple)):
            raise ValueError(
                f"a book's records must be a list of records, "
                f"got {self.records!r}")
        records = tuple(_check_record_ref(r) for r in self.records)
        if not records:
            raise ValueError("a cold-start book holds at least one record")
        seen_ids = set()
        seen_projects = set()
        for record in records:
            if record.record_id is not None:
                if record.record_id in seen_ids:
                    raise ValueError(
                        f"a record named {record.record_id!r} already exists")
                seen_ids.add(record.record_id)
            if record.project_ref in seen_projects:
                raise ValueError(
                    f"the project {record.project_ref!r} already "
                    f"stands open in this book - one opening per project")
            seen_projects.add(record.project_ref)
        object.__setattr__(self, "records", records)
        if isinstance(self.panels, (str, bytes)) \
                or not isinstance(self.panels, (list, tuple)):
            raise ValueError(
                f"a book's panels must be a list of panels, "
                f"got {self.panels!r}")
        panels = tuple(
            p if isinstance(p, ColdStartPanel) else validate_panel(p)
            for p in self.panels)
        seen_panels = set()
        for panel in panels:
            if panel.panel_id is not None:
                if panel.panel_id in seen_panels:
                    raise ValueError(
                        f"a panel named {panel.panel_id!r} already exists")
                seen_panels.add(panel.panel_id)
        object.__setattr__(self, "panels", panels)
        if not isinstance(self.canon_note, str):
            raise ValueError("a book's note must be text")
        object.__setattr__(self, "canon_note", self.canon_note.strip())

    def record_for(self, record_id: Any) -> ColdStartRecord:
        """The record one id names in this book."""
        wanted = _check_word(record_id, "a record id")
        for record in self.records:
            if record.record_id == wanted:
                return record
        raise KeyError(f"no record named {wanted!r}")

    def record_for_project(self, project_ref: Any) -> ColdStartRecord:
        """The record one project names in this book."""
        wanted = _check_word(project_ref, "a project ref")
        for record in self.records:
            if record.project_ref == wanted:
                return record
        raise KeyError(f"no opening stands for project {wanted!r}")

    def panel_for(self, panel_id: Any) -> ColdStartPanel:
        """The panel one id names in this book."""
        wanted = _check_word(panel_id, "a panel id")
        for panel in self.panels:
            if panel.panel_id == wanted:
                return panel
        raise KeyError(f"no panel named {wanted!r}")

    def record_ids(self) -> Tuple[str, ...]:
        """Every record id this book names, in held order."""
        return tuple(r.record_id for r in self.records
                     if r.record_id is not None)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "cold_start_book",
            "slice": COLD_START_SLICE,
            "title": self.title,
            "records": [
                {key: value for key, value in r.to_record().items()
                 if key not in ("type", "slice", "mode", "stage_plan")}
                for r in self.records],
            "panels": [p.to_record() for p in self.panels],
            "record_count": len(self.records),
            "canon_note": self.canon_note,
        }


def _judge_book_panels(book: ColdStartBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def validate_book(data: Any, *, require_example: bool = False) -> ColdStartBook:
    """Validate one book record into a ColdStartBook.

    Accepts a book or a mapping naming a ``schema``,
    a ``guide`` (its ``title``), ``records`` (or
    ``openings``) and ``panels``. Every stored panel
    is judged against the panel derived from the
    book's own records. With ``require_example``,
    the book must be the shipped example book
    exactly. Structural failures raise
    :class:`ValidationError`.
    """
    if isinstance(data, ColdStartBook):
        book = data
        _judge_book_panels(book)
        if require_example:
            _check_example(book)
        return book
    if not isinstance(data, dict):
        raise ValidationError(f"a book must be a mapping, got {data!r}")
    unknown = set(data) - _COLD_BOOK_KEYS
    if unknown:
        raise ValidationError(
            "unknown book keys: %s" % ", ".join(sorted(unknown)))
    if data.get("schema") != COLD_START_SCHEMA:
        raise ValidationError(
            f"a cold-start book must carry schema "
            f"{COLD_START_SCHEMA!r}, got {data.get('schema')!r}")
    records = _pick_any(data, ("records", "openings"), "records")
    if records is None:
        raise ValidationError("a book is missing its records")
    guide = data.get("guide") or {}
    if not isinstance(guide, dict):
        raise ValidationError("a book's guide must be a mapping")
    unknown_guide = set(guide) - _BOOK_KEYS
    if unknown_guide:
        raise ValidationError(
            "unknown guide keys: %s" % ", ".join(sorted(unknown_guide)))
    title = _pick_any(guide, ("title", "name"), "titles")
    if title is None:
        raise ValidationError("a book is missing its title")
    panels = data.get("panels") or ()
    note = data.get("canon_note") or ""
    try:
        book = ColdStartBook(
            title=title, records=records, panels=panels,
            canon_note=note)
        _judge_book_panels(book)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    if require_example:
        _check_example(book)
    return book


def _check_example(book: ColdStartBook) -> None:
    if book.title != _EXAMPLE_TITLE:
        raise ValueError("the shipped example book carries its own title")
    if book.record_ids() != _EXAMPLE_RECORD_IDS:
        raise ValueError("the shipped example book carries its own records")
    first = book.records[0]
    if first.title != _EXAMPLE_FIRST_RECORD_TITLE:
        raise ValueError("the shipped example book opens with its own record")
    if len(book.panels) != 1 or book.panels[0].panel_id != _EXAMPLE_PANEL_ID:
        raise ValueError("the shipped example book carries its one panel")
    panel = book.panels[0]
    if tuple(r.record_id for r in panel.rows) != _EXAMPLE_PANEL_ROW_IDS:
        raise ValueError("the shipped example panel stands in its own order")
    if panel.as_of != _EXAMPLE_AS_OF:
        raise ValueError("the shipped example panel carries its own day")


def build_book(book: Any = None, **kwargs: Any) -> ColdStartBook:
    """Build one validated book, from a mapping or field words."""
    if isinstance(book, ColdStartBook) and not kwargs:
        return validate_book(book)
    if isinstance(book, dict):
        if "schema" in book:
            return validate_book(book)
        merged: Dict[str, Any] = dict(book)
        merged.update(kwargs)
        built = ColdStartBook(**merged)
        _judge_book_panels(built)
        return built
    if book is None:
        built = ColdStartBook(**kwargs)
        _judge_book_panels(built)
        return built
    return validate_book(book)


def _book_from(data: Any, *, require_example: bool) -> ColdStartBook:
    try:
        return validate_book(data, require_example=require_example)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def load_cold_start(data: Optional[Dict[str, Any]] = None) -> ColdStartBook:
    """Load and validate the shipped example book (or *data*)."""
    raw = data if data is not None else load_resource(COLD_START_RESOURCE)
    return _book_from(raw, require_example=True)


def load_cold_start_file(path: Any) -> ColdStartBook:
    """Load and validate a cold-start book from a file at *path*."""
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _book_from(raw, require_example=False)


# ---------------------------------------------------------------------
# The registry model: one book held record by record.
# ---------------------------------------------------------------------


class ColdStartRegistry:
    """One book's records, held one by one.

    The registry holds records, never panels or
    verdicts: the panel and the verdict are
    derivations, read off the whole held book at
    call time. A whole book is judged whole - as
    a book judges it, and against everything
    already held - before its records are held in
    book order, so a raising never lands
    partially. One opening per project stands
    here, as in a book. The registry also holds
    which derived stages stand marked done on its
    own book: a stage is marked only when it is
    its record's plan's next stage, and marking it
    touches no live map - the held book only.
    """

    def __init__(self, book: Any = None) -> None:
        self._title: Optional[str] = None
        self._records: list = []
        self._done: Dict[str, list] = {}
        if book is not None:
            self.register_book(book)

    @property
    def title(self) -> Optional[str]:
        return self._title

    def _fresh_record_id(self, held_ids: Any) -> str:
        n = 1
        while f"record-{n}" in held_ids:
            n += 1
        return f"record-{n}"

    def _check_standing_free(self, record: ColdStartRecord) -> None:
        for held in self._records:
            if record.record_id is not None \
                    and held.record_id == record.record_id:
                raise ValueError(
                    f"a record named {record.record_id!r} already stands here")
            if held.project_ref == record.project_ref:
                raise ValueError(
                    f"the project {record.project_ref!r} already "
                    f"stands open here - one opening per project")

    def register_record(self, record: Any) -> ColdStartRecord:
        """Hold one record, judged whole, under its id or a fresh one."""
        from dataclasses import replace
        validated = _check_record_ref(record)
        if validated.record_id is None:
            held_ids = {r.record_id for r in self._records}
            validated = replace(
                validated, record_id=self._fresh_record_id(held_ids))
        self._check_standing_free(validated)
        self._hold_record(validated)
        return validated

    def _hold_record(self, validated: ColdStartRecord) -> None:
        if self._title is None:
            self._title = "Cold Start"
        self._records.append(validated)
        self._done[validated.record_id] = []

    def register_book(self, book: Any) -> ColdStartBook:
        """Hold a whole book's records, judged whole before any is held."""
        validated = build_book(book)
        if self._title is not None and validated.title \
                and validated.title != self._title \
                and self._records:
            raise ValueError(
                "a book under a different title refuses this registry")
        for record in validated.records:
            self._check_standing_free(record)
        if validated.title:
            self._title = validated.title
        for record in validated.records:
            if record.record_id is None:
                record = self.register_record(record)
            else:
                self._hold_record(record)
        return validated

    def get_record(self, record_id: Any) -> ColdStartRecord:
        """The record one id names in this registry."""
        wanted = _check_word(record_id, "a record id")
        for record in self._records:
            if record.record_id == wanted:
                return record
        raise KeyError(f"no record named {wanted!r}")

    def record_for_project(self, project_ref: Any) -> ColdStartRecord:
        """The record one project names in this registry."""
        wanted = _check_word(project_ref, "a project ref")
        for record in self._records:
            if record.project_ref == wanted:
                return record
        raise KeyError(f"no opening stands for project {wanted!r}")

    def latest_record(self) -> ColdStartRecord:
        """The most recently held record."""
        if not self._records:
            raise ValueError("no record stands held yet")
        return self._records[-1]

    def list_records(self) -> Tuple[ColdStartRecord, ...]:
        """Every held record, in held order."""
        return tuple(self._records)

    def book(self) -> ColdStartBook:
        """The held records as one book."""
        if not self._records:
            raise ValueError("no record stands held yet")
        return ColdStartBook(
            title=self._title or "Cold Start", records=tuple(self._records))

    def panel(self) -> ColdStartPanel:
        """The readiness panel derived from the held book."""
        return derive_panel(self.book())

    def verdict(self) -> ColdStartVerdict:
        """The cold-start verdict derived for the held book."""
        return derive_verdict(self.book())

    def progress_for(self, record_id: Any) -> ColdStartProgress:
        """One held record's progress, derived from its plan."""
        record = self.get_record(record_id)
        return derive_progress(record, tuple(self._done[record.record_id]))

    def completed_stages(self, record_id: Any) -> Tuple[str, ...]:
        """The stages marked done for one held record, in plan order."""
        record = self.get_record(record_id)
        return tuple(self._done[record.record_id])

    def is_complete(self, record_id: Any) -> bool:
        """Whether one held record's plan stands fully marked done."""
        return self.progress_for(record_id).complete

    def mark_stage(self, record_id: Any, stage: Any = None) -> ColdStartProgress:
        """Mark one stage of one held record done, in derived order.

        With no stage named, the plan's next stage
        is marked. A stage that is not the plan's
        next refuses - progress walks the plan stage
        by stage, the stalest area first, and a
        completed plan marks nothing more. Marking
        touches the held book only: no live map is
        rebuilt here.
        """
        record = self.get_record(record_id)
        progress = self.progress_for(record.record_id)
        if progress.complete:
            raise ValueError(
                "the plan stands complete - no stage remains to mark")
        wanted = progress.next_stage if stage is None else _check_stage(stage)
        if wanted != progress.next_stage:
            raise ValueError(
                f"the plan's next stage is {progress.next_stage!r}; "
                f"stages are marked in derived order, never skipped")
        self._done[record.record_id].append(wanted)
        return self.progress_for(record.record_id)


def record_refs(source: Any) -> Tuple[Tuple[str, str], ...]:
    """Every (project ref, map ref) one source's records name."""
    return tuple(
        (record.project_ref, record.map_ref)
        for record in _held_records(source))


def record_for(source: Any, project_ref: Any) -> ColdStartRecord:
    """The record one source holds for one project."""
    wanted = _check_word(project_ref, "a project ref")
    for record in _held_records(source):
        if record.project_ref == wanted:
            return record
    raise KeyError(f"no opening stands for project {wanted!r}")


def total_records(source: Any) -> int:
    """How many records one source holds."""
    return len(_held_records(source))


# ---------------------------------------------------------------------
# Session news, plain words and screens.
# ---------------------------------------------------------------------


def record_record(record: Any) -> Dict[str, Any]:
    """The session-news record of one cold-start record."""
    current = _check_record_ref(record)
    record_out = current.to_record()
    record_out["news"] = True
    mode = mode_of(current)
    if mode == "rebuild-from-scratch":
        record_out["headline"] = (
            f"Cold start over {current.project_ref}: no map "
            f"stands - the plan rebuilds it from scratch, "
            f"staged by area.")
    elif mode == "background-rebuild":
        record_out["headline"] = (
            f"Cold start over {current.project_ref}: the "
            f"stale-but-usable map serves at once while the "
            f"plan rebuilds {current.total_stale} stale "
            f"entries in the background.")
    else:
        record_out["headline"] = (
            f"Cold start over {current.project_ref}: the map "
            f"stands fresh and whole - served as it stands, "
            f"no rebuild derived.")
    return record_out


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of one derived panel."""
    current = validate_panel(panel, source)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Cold-start panel as of {current.as_of}: "
        f"{current.total_records} openings - "
        f"{current.total_fresh} fresh, {current.total_warming} "
        f"warming in the background, {current.total_cold} "
        f"from scratch, over {current.distinct_projects} "
        f"projects.")
    return record


def verdict_record(verdict: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of one derived verdict."""
    current = validate_verdict(verdict, source)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Cold-start verdict: {current.verdict} - "
        f"{current.total_fresh} of {current.total_records} "
        f"openings serve fresh maps, {current.total_warming} "
        f"rebuild in the background and {current.total_cold} "
        f"from scratch, from {current.earliest_on} to "
        f"{current.latest_on}.")
    return record


def progress_record(progress: Any, record: Any = None) -> Dict[str, Any]:
    """The session-news record of one record's progress."""
    current = validate_progress(progress, record)
    record_out = current.to_record()
    record_out["news"] = True
    if current.complete:
        record_out["headline"] = (
            f"Cold-start progress over {current.record_id}: "
            f"the derived plan stands complete - "
            f"{len(current.completed)} stages marked done "
            f"on the held book.")
    else:
        record_out["headline"] = (
            f"Cold-start progress over {current.record_id}: "
            f"{len(current.completed)} of {len(current.stages)} "
            f"stages marked done; next stands "
            f"{current.next_stage}.")
    return record_out


def book_record(book: Any) -> Dict[str, Any]:
    """The session-news record of one cold-start book."""
    current = book if isinstance(book, ColdStartBook) else build_book(book)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Cold-start book {current.title}: "
        f"{record['record_count']} openings named.")
    return record


def plain_words(record: Any) -> str:
    """One record, in one plain sentence."""
    current = _check_record_ref(record)
    mode = mode_of(current)
    if mode == "rebuild-from-scratch":
        return (
            f"{current.title} - opening {current.project_ref} "
            f"finds no map at all: the plan rebuilds it from "
            f"scratch, staged by area, and nothing is usable "
            f"until the first area lands.")
    if mode == "background-rebuild":
        return (
            f"{current.title} - opening {current.project_ref} "
            f"serves its stale-but-usable map at once "
            f"({usable_entries_of(current)} of "
            f"{current.map_entries} entries) while the plan "
            f"rebuilds {current.total_stale} stale entries in "
            f"the background, stalest area first.")
    return (
        f"{current.title} - opening {current.project_ref} "
        f"serves its fresh, whole map as it stands: "
        f"{usable_entries_of(current)} entries usable, no "
        f"rebuild derived.")


def panel_plain_words(source: Any) -> str:
    """The panel in plain words, in full."""
    if isinstance(source, ColdStartPanel):
        panel = validate_panel(source)
        title = None
    elif isinstance(source, (ColdStartBook, ColdStartRegistry)):
        panel = derive_panel(source)
        title = source.title if isinstance(source, ColdStartBook) else None
    else:
        raise ValueError(f"a cold-start source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    lines.append("Openings, in panel order:")
    for row in panel.rows:
        lines.append(
            f"{row.record_id}: {row.mode}/{row.project_ref} - "
            f"usable now: {row.usable_entries} entries, still "
            f"rebuilding: {row.total_stale} stale entries in "
            f"{row.rebuilding_areas} areas (opened {row.opened_on})")
    lines.extend(panel.account)
    return "\n".join(lines)


def verdict_plain_words(source: Any) -> str:
    """The cold-start verdict in plain words, in full."""
    if isinstance(source, ColdStartVerdict):
        verdict = validate_verdict(source)
    elif isinstance(source, (ColdStartBook, ColdStartRegistry)):
        verdict = derive_verdict(source)
    else:
        raise ValueError(f"a cold-start source is needed, got {source!r}")
    return (
        f"Cold-start verdict: {verdict.verdict} - "
        f"{verdict.total_fresh} openings serve fresh maps, "
        f"{verdict.total_warming} rebuild in the background "
        f"and {verdict.total_cold} from scratch, over "
        f"{verdict.distinct_projects} projects, opened from "
        f"{verdict.earliest_on} to {verdict.latest_on}, of "
        f"{verdict.total_records} openings - every plan is "
        f"derived from its evidence, and no live map is "
        f"rebuilt by standing on this verdict.")


def progress_plain_words(progress: Any) -> str:
    """One record's progress in plain words, in full."""
    current = _check_progress_ref(progress)
    if current.complete:
        return (
            f"Progress over {current.record_id}: all "
            f"{len(current.stages)} derived stages stand marked "
            f"done on the held book - the plan is complete "
            f"here, and no live map was rebuilt.")
    return (
        f"Progress over {current.record_id}: "
        f"{len(current.completed)} of {len(current.stages)} "
        f"derived stages marked done on the held book; the "
        f"next stage stands {current.next_stage}, in derived "
        f"order.")


def _source_book(source: Any) -> ColdStartBook:
    if source is None:
        return load_cold_start()
    if isinstance(source, ColdStartRegistry):
        return source.book()
    if isinstance(source, ColdStartBook):
        return source
    if isinstance(source, ColdStartRecord):
        return ColdStartBook(title="One cold-start record", records=(source,))
    raise ValueError(f"a cold-start book is needed, got {source!r}")


def format_record(record: Any) -> str:
    """One record as a screen block, its derived plan shown."""
    current = _check_record_ref(record)
    plan = stage_plan_of(current)
    lines = [
        f"{current.record_id or '-'}: {current.title} - opening "
        f"{current.project_ref} over map {current.map_ref} "
        f"(read from {current.source})",
        f"Evidence: map {current.map_age_days} days old, "
        f"{current.map_entries} entries over "
        f"{current.project_files} project files, "
        f"{current.covered_files} files covered "
        f"(opened {current.opened_on} by {current.opened_by} "
        f"in {current.origin_session})",
        f"Mode derived: {mode_of(current)} - "
        f"{usable_entries_of(current)} entries usable now, "
        f"{current.total_stale} stale.",
        "Plan, in derived order: " + ", ".join(plan),
    ]
    return "\n".join(lines)


def format_records(source: Any = None, mode: Any = None) -> str:
    """Records of one book, in held order, optionally filtered by mode."""
    book = _source_book(source)
    wanted = normalize_mode(mode) if mode is not None else None
    lines = [
        f"{r.record_id or '-'}: {r.title} - {mode_of(r)} over "
        f"{r.project_ref}: usable {usable_entries_of(r)} of "
        f"{r.map_entries} entries, {r.total_stale} stale "
        f"(opened {r.opened_on})"
        for r in book.records
        if wanted is None or mode_of(r) == wanted]
    if not lines:
        lines.append("No openings stand in the book on that reading.")
    return "\n".join(lines)


def format_panel(source: Any = None) -> str:
    """The panel as a screen block: every row and the account."""
    if isinstance(source, ColdStartPanel):
        panel = validate_panel(source)
        lines: list = []
    else:
        book = _source_book(source)
        panel = derive_panel(book)
        lines = [f"Panel in {book.title}:"]
    lines.append("Openings, in panel order:")
    for row in panel.rows:
        lines.append(
            f"{row.record_id}: {row.mode}/{row.project_ref} - "
            f"usable now: {row.usable_entries} entries, still "
            f"rebuilding: {row.total_stale} stale entries in "
            f"{row.rebuilding_areas} areas (opened {row.opened_on})")
    lines.extend(panel.account)
    return "\n".join(lines)


def format_verdict(source: Any = None) -> str:
    """The cold-start verdict as a screen block."""
    if isinstance(source, ColdStartVerdict):
        verdict = validate_verdict(source)
        lines: list = []
    else:
        book = _source_book(source)
        verdict = derive_verdict(book)
        lines = [f"Verdict in {book.title}:"]
    lines.append(
        f"{verdict.verdict}: {verdict.total_fresh} openings "
        f"serve fresh maps, {verdict.total_warming} rebuild "
        f"in the background and {verdict.total_cold} from "
        f"scratch over {verdict.distinct_projects} projects, "
        f"opened from {verdict.earliest_on} to "
        f"{verdict.latest_on}, of {verdict.total_records} "
        f"openings. Every plan is derived from its evidence "
        f"alone, and no live map is rebuilt here.")
    return "\n".join(lines)


def format_progress(progress: Any) -> str:
    """One record's progress as a screen block."""
    current = _check_progress_ref(progress)
    lines = [f"Progress over {current.record_id}:"]
    for stage in current.stages:
        mark = "done" if stage in current.completed else "standing"
        lines.append(f"{stage}: {mark}")
    if current.complete:
        lines.append("The derived plan stands complete on the held book.")
    else:
        lines.append(f"Next stage: {current.next_stage}")
    return "\n".join(lines)


def format_cold_start_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /coldstart.

    With nothing named, the shipped example book
    is shown - the example this slice ships - so
    the screen is never empty.
    """
    book = _source_book(source)
    lines = ["Cold-Start Kindness (M-169) - " + PLAIN_EXPLANATION, ""]
    for record in book.records:
        lines.append(format_record(record))
    lines.append("")
    lines.append(format_panel(book))
    lines.append("")
    lines.append(format_verdict(book))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_cold_start_args(args: Any) -> Tuple[str, Any]:
    """Parse the /coldstart grammar both surfaces share.

    No words (or ``show`` / ``list``) shows the
    book; ``record <record-id>`` shows one record
    with its derived plan shown; ``project
    <project-ref>`` shows the opening one project
    stands under; ``panel`` shows the readiness
    panel derived from the whole book; ``verdict``
    shows the verdict derived for the whole book;
    ``stages`` shows every record's derived stage
    plan. Anything else is a usage error naming
    the grammar. Returns ``(action, value-or-None)``.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() in ("show", "list"):
        return ("show", None)
    words = text.split()
    head = words[0].lower()
    if head in ("panel", "verdict", "stages") and len(words) == 1:
        return (head, None)
    if head in ("record", "project") and len(words) == 2:
        try:
            return (head, normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
