"""Memory Doctor (All-Features roadmap slice M-168).

Part VII closes its memory run. The roadmap's words:
``mythic doctor gains memory checks (corrupt
stores, orphaned vectors, map drift) with safe
repairs.``

What already ships, and what this slice adds:

* The memory stores themselves already ship as
  data on shipped roads - the project memory
  map (``core/project_memory_map.py``, M-150),
  session memory across days
  (``core/session_memory.py``, M-153),
  cross-project memory
  (``core/cross_project_memory.py``, M-154), the
  self-improving ledger
  (``core/self_improving_ledger.py``, M-155),
  crew memory (``core/crew_memory.py``, M-133),
  the subconscious v2
  (``core/subconscious_v2.py``, M-165), the
  contradiction watch
  (``core/contradiction_watch.py``, M-166) and
  private by architecture
  (``core/private_by_architecture.py``, M-167).
  What none of those layers holds is the health
  of the stores themselves: which stored pieces
  fail their own layer's validation, which
  vector records name memories no store holds,
  and which map entries point at paths that
  moved - and what may safely be done about
  each, in plain words.
* This slice is that health, as a pure layer:
  one memory finding validated as data WITH ITS
  PROVENANCE WHOLE - the check that raised it
  (a corrupt store, an orphaned vector, or map
  drift), the stored memory it stands over,
  named by the kind of holding it stands in and
  the shipped piece's id alone; the store the
  memory lives in; what the check saw, in plain
  words; how far the trouble reaches - one
  contained piece, or the store as a whole -
  who ran the check, the session it ran in and
  where the finding was read from. What may be
  done about a finding is never in question and
  never stored loose: the safe repair is DERIVED
  from the finding - quarantine the corrupt
  piece, drop the orphaned vector, realign the
  drifted map entry - and a finding whose
  trouble reaches the whole store derives no
  repair at all: it is referred to the user,
  plainly, and this layer repairs nothing there.
  Findings are composed BY IMPORT from the
  shipped holdings they stand over, each judged
  by its own layer's validation, ids and refs
  only across the seams; three check roads run
  the checks themselves - a corrupt piece is
  found by its own layer's validator refusing
  it, an orphaned vector by its ref standing in
  no held store, a drifted map entry by the path
  it names standing in no held path. The shipped
  data file
  (``mythic_agent/data/memory_doctor.yaml``)
  holds one example book in exactly the shape a
  real book file takes, a loader reads a book
  file anywhere on disk, the doctor panel is
  DERIVED from the whole book (every finding
  carried whole, in a settled order, its derived
  repair shown on every row), a doctor VERDICT
  is derived for the whole book, the repairs are
  DERIVED from the whole book, findings are
  shaped as session news, and a small in-memory
  registry model holds findings one by one and
  applies the derived safe repairs to its own
  held book. The agent layer owns holding a
  book for a session and running the checks
  over the session's own held memory books.

Honesty rules, enforced here and pinned by tests:

* **Provenance whole, ids only across the seam.**
  A finding names the stored memory it stands
  over - kind and the shipped piece's id - and
  nothing else of the piece crosses: the piece's
  own words stay in its own layer, judged by its
  own layer's validator.
* **Repairs derived, never chosen.** A finding's
  repair is read off its check and its extent
  alone: a contained corrupt piece is
  quarantined, an orphaned vector is dropped, a
  drifted map entry is realigned - and a
  store-wide trouble is referred to the user
  with no repair derived, so the doctor never
  quietly attempts what it should not.
* **A repair touches held data only.** Applying
  a derived repair marks the held finding
  repaired in the registry's own book; it
  rewrites no live store, deletes no memory and
  writes nothing to disk - the live stores are
  the shipped layers' own roads, not this
  slice's, and the ``mythic doctor`` CLI check
  this slice adds reports corrupt shipped
  stores, it does not mend them.
* **One finding per check per memory.** One
  check stands once over one stored memory in a
  book, so a check's word never forks.
* **Data only.** This layer holds findings as
  data: it sends nothing, posts nothing,
  schedules nothing, calls no model, persists
  nothing and writes no live memory - raising a
  finding changes no shipped holding.
"""

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..resources import load_resource
from .contradiction_watch import ContradictionWatch
from .contradiction_watch import validate_watch as _validate_watch
from .crew_members import normalize_member_id
from .crew_memory import MemoryEntry as CrewMemoryEntry
from .crew_memory import validate_entry as _validate_crew_entry
from .cross_project_memory import SharedLesson
from .cross_project_memory import validate_lesson as _validate_lesson
from .private_by_architecture import PrivacyPosting
from .private_by_architecture import validate_posting as _validate_posting
from .project_memory_map import MemoryMapEntry
from .project_memory_map import validate_entry as _validate_map_entry
from .self_improving_ledger import CandidateMemory
from .self_improving_ledger import validate_candidate as _validate_candidate
from .session_memory import CarriedMemory
from .session_memory import validate_note as _validate_note
from .subconscious_v2 import SubconsciousMemory
from .subconscious_v2 import validate_memory as _validate_v2_memory
from .validation import ValidationError

__all__ = [
    "MEMORY_DOCTOR_RESOURCE",
    "MEMORY_DOCTOR_SCHEMA",
    "MEMORY_DOCTOR_SLICE",
    "PLAIN_EXPLANATION",
    "CHECKS",
    "MEMORY_KINDS",
    "STORES",
    "EXTENTS",
    "DISPOSITIONS",
    "REPAIR_ACTIONS",
    "VERDICT_WORDS",
    "REFERRED_ACTION",
    "USAGE",
    "CheckCount",
    "DoctorBook",
    "DoctorPanel",
    "DoctorPanelRow",
    "DoctorRegistry",
    "DoctorRepair",
    "DoctorVerdict",
    "MemoryFinding",
    "build_book",
    "build_finding",
    "build_panel",
    "build_repair",
    "build_row",
    "build_verdict",
    "derive_panel",
    "derive_repairs",
    "derive_verdict",
    "disposition_of",
    "finding_for",
    "finding_from_contradiction_watch",
    "finding_from_corrupt_piece",
    "finding_from_crew_entry",
    "finding_from_cross_project_lesson",
    "finding_from_drifted_map_entry",
    "finding_from_ledger_candidate",
    "finding_from_map_entry",
    "finding_from_orphaned_vector",
    "finding_from_privacy_posting",
    "finding_from_session_note",
    "finding_from_subconscious_memory",
    "finding_record",
    "finding_refs",
    "format_finding",
    "format_findings",
    "format_memory_doctor_screen",
    "format_panel",
    "format_repairs",
    "format_verdict",
    "inspect_finding_source",
    "load_memory_doctor",
    "load_memory_doctor_file",
    "normalize_check",
    "normalize_extent",
    "normalize_memory_kind",
    "normalize_store",
    "panel_plain_words",
    "panel_record",
    "parse_memory_doctor_args",
    "plain_words",
    "book_record",
    "repair_action_of",
    "repair_line",
    "repair_record",
    "repairs_plain_words",
    "total_findings",
    "validate_book",
    "validate_finding",
    "validate_panel",
    "validate_repair",
    "validate_row",
    "validate_verdict",
    "verdict_plain_words",
    "verdict_record",
]

MEMORY_DOCTOR_SLICE = "M-168"

MEMORY_DOCTOR_RESOURCE = "memory_doctor.yaml"

MEMORY_DOCTOR_SCHEMA = "mythic.memory_doctor/1"

#: The checks the memory doctor runs, in the
#: roadmap's own order: a store piece that fails
#: its own layer's validation, a vector record
#: naming a memory no store holds, and a map
#: entry pointing at a path that moved.
CHECKS = ("corrupt-store", "orphaned-vector", "map-drift")

_CHECK_ALIASES = {
    "corrupt-store": "corrupt-store",
    "corrupt_store": "corrupt-store",
    "corrupt": "corrupt-store",
    "corruption": "corrupt-store",
    "orphaned-vector": "orphaned-vector",
    "orphaned_vector": "orphaned-vector",
    "orphan": "orphaned-vector",
    "orphaned": "orphaned-vector",
    "map-drift": "map-drift",
    "map_drift": "map-drift",
    "drift": "map-drift",
}

#: The holdings a checked memory may stand in:
#: the shipped memory layers a finding may stand
#: over - the M-167 kinds, carried whole.
MEMORY_KINDS = (
    "memory-map", "session-note", "cross-project-lesson",
    "ledger-candidate", "crew-fact", "subconscious-memory",
    "contradiction-watch", "vector-record", "manual")

_KIND_ALIASES = {
    "memory-map": "memory-map",
    "memory_map": "memory-map",
    "map": "memory-map",
    "map-entry": "memory-map",
    "session-note": "session-note",
    "session_note": "session-note",
    "note": "session-note",
    "cross-project-lesson": "cross-project-lesson",
    "cross_project_lesson": "cross-project-lesson",
    "cross-project": "cross-project-lesson",
    "lesson": "cross-project-lesson",
    "ledger-candidate": "ledger-candidate",
    "ledger_candidate": "ledger-candidate",
    "ledger": "ledger-candidate",
    "candidate": "ledger-candidate",
    "crew-fact": "crew-fact",
    "crew_fact": "crew-fact",
    "crew": "crew-fact",
    "crew-entry": "crew-fact",
    "subconscious-memory": "subconscious-memory",
    "subconscious_memory": "subconscious-memory",
    "subconscious": "subconscious-memory",
    "v2": "subconscious-memory",
    "v2-memory": "subconscious-memory",
    "contradiction-watch": "contradiction-watch",
    "contradiction_watch": "contradiction-watch",
    "contradiction": "contradiction-watch",
    "watch": "contradiction-watch",
    "vector-record": "vector-record",
    "vector_record": "vector-record",
    "vector": "vector-record",
    "manual": "manual",
    "by-hand": "manual",
}

#: The stores a checked memory may live in, by
#: the roadmap's own words: the workspace store
#: and the user store.
STORES = ("workspace", "user")

_STORE_ALIASES = {
    "workspace": "workspace",
    "workspace-store": "workspace",
    "project": "workspace",
    "project-store": "workspace",
    "user": "user",
    "user-store": "user",
    "personal": "user",
}

#: How far a finding's trouble reaches: one
#: contained piece, or the store as a whole.
#: Only contained trouble derives a safe repair.
EXTENTS = ("contained", "store-wide")

_EXTENT_ALIASES = {
    "contained": "contained",
    "single": "contained",
    "one-piece": "contained",
    "store-wide": "store-wide",
    "store_wide": "store-wide",
    "whole-store": "store-wide",
    "widespread": "store-wide",
}

#: How a finding stands toward repair, derived
#: from its extent alone: safely repairable by
#: the doctor, or referred to the user.
DISPOSITIONS = ("repair-ready", "referred")

#: The safe repairs a finding may derive, one
#: per check - and the one word that names no
#: repair derived at all, for referred trouble.
REPAIR_ACTIONS = (
    "quarantine-piece", "drop-orphan-vector",
    "realign-map-entry", "none-referred")

_REPAIR_BY_CHECK = {
    "corrupt-store": "quarantine-piece",
    "orphaned-vector": "drop-orphan-vector",
    "map-drift": "realign-map-entry",
}

#: The action word that names no repair: a
#: store-wide finding is referred, never repaired.
REFERRED_ACTION = "none-referred"

#: The words a whole book's doctor verdict may
#: carry, quietest first: how much of what the
#: checks found stands beyond safe repair.
VERDICT_WORDS = ("sound", "ailing", "critical")

_FINDING_KEYS = frozenset({
    "finding_id", "id", "title", "name", "subject",
    "check", "check_kind",
    "memory_kind", "kind", "memory_ref", "ref",
    "store", "home",
    "detail", "evidence", "seen",
    "extent", "reach",
    "found_on", "day", "date",
    "recorded_by", "recorder", "by", "who",
    "source", "origin_session", "session",
})

_ROW_KEYS = frozenset({
    "finding_id", "id", "title", "check",
    "memory_kind", "memory_ref", "store",
    "extent", "disposition", "action", "found_on",
})

_CHECK_COUNT_KEYS = frozenset({"check", "items", "count"})

_PANEL_KEYS = frozenset({
    "panel_id", "id", "rows", "findings",
    "total_findings", "total",
    "total_ready", "ready",
    "total_referred", "referred",
    "distinct_memories", "memories",
    "check_counts", "checks",
    "as_of", "day",
    "account", "statements",
})

_VERDICT_KEYS = frozenset({
    "total_findings", "total",
    "total_ready", "ready",
    "total_referred", "referred",
    "distinct_memories", "memories",
    "distinct_kinds", "kinds",
    "earliest_on", "earliest",
    "latest_on", "latest",
    "verdict",
})

_REPAIR_KEYS = frozenset({
    "repair_id", "id", "finding_id", "finding",
    "check", "memory_kind", "memory_ref",
    "action", "disposition",
})

_BOOK_KEYS = frozenset({"title", "name"})

_DOCTOR_BOOK_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "canon_note", "guide", "findings", "records", "panels",
})

_EXAMPLE_TITLE = "Memory Doctor at the M-167 slice boundary"

_EXAMPLE_FINDING_IDS = (
    "finding-verify-remote-corrupt", "finding-archival-alpha-orphan",
    "finding-no-docker-drift", "finding-samtal-wal-store",
    "finding-campaign-home-drift")

_EXAMPLE_FIRST_FINDING_ID = "finding-verify-remote-corrupt"

_EXAMPLE_FIRST_FINDING_TITLE = (
    "the verify-remote candidate fails its own ledger validation")

_EXAMPLE_PANEL_ID = "panel-m167-boundary"

_EXAMPLE_AS_OF = "2026-11-09"

_EXAMPLE_PANEL_ROW_IDS = (
    "finding-samtal-wal-store", "finding-verify-remote-corrupt",
    "finding-archival-alpha-orphan", "finding-campaign-home-drift",
    "finding-no-docker-drift")

PLAIN_EXPLANATION = (
    "Memory Doctor: mythic doctor gains memory "
    "checks - corrupt stores, orphaned vectors "
    "and map drift - with safe repairs. A finding "
    "stands over one stored memory, named by the "
    "kind of holding it stands in and the shipped "
    "piece's id alone, and carries its provenance "
    "whole: the check that raised it, the store "
    "the memory lives in, what the check saw, how "
    "far the trouble reaches, who ran the check "
    "and the session it ran in. A finding's repair "
    "is derived, never chosen - quarantine a "
    "contained corrupt piece, drop an orphaned "
    "vector, realign a drifted map entry - and a "
    "store-wide trouble derives no repair at all: "
    "it is referred to the user, plainly. The "
    "doctor panel is derived from the book at "
    "call time, the doctor verdict is derived for "
    "the whole book, and the repairs are derived "
    "from the whole book. This layer holds "
    "findings as data only: it sends nothing, "
    "posts nothing, schedules nothing, calls no "
    "model, persists nothing and writes no live "
    "memory - a repair applied here marks a held "
    "finding repaired in the session's own book "
    "and rewrites no live store."
)

USAGE = (
    "Usage: /memorydoctor, /memorydoctor show, "
    "/memorydoctor finding <finding-id>, "
    "/memorydoctor check <check>, "
    "/memorydoctor store <store>, "
    "/memorydoctor panel, /memorydoctor verdict, "
    "/memorydoctor repairs"
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


def normalize_check(value: Any) -> str:
    """The canonical check a word names.

    A check is one of :data:`CHECKS` - the checks
    the memory doctor runs - read
    case-insensitively, with short spellings
    (``corrupt``, ``orphan``, ``drift``) read onto
    their checks. Anything else raises, plainly
    naming the set.
    """
    if isinstance(value, str):
        wanted = _CHECK_ALIASES.get(value.strip().lower())
        if wanted is not None:
            return wanted
    raise ValueError(
        "a check must be one of %s, got %r"
        % ("/".join(CHECKS), value))


def normalize_memory_kind(value: Any) -> str:
    """The canonical memory kind a word names.

    A kind is one of :data:`MEMORY_KINDS` - the
    holding a checked memory stands in - read
    case-insensitively, with short spellings
    (``map``, ``note``, ``ledger``, ``crew``,
    ``lesson``, ``subconscious``, ``watch``,
    ``vector``) read onto their kinds. Anything
    else raises, plainly naming the set.
    """
    if isinstance(value, str):
        wanted = _KIND_ALIASES.get(value.strip().lower())
        if wanted is not None:
            return wanted
    raise ValueError(
        "a memory kind must be one of %s, got %r"
        % ("/".join(MEMORY_KINDS), value))


def normalize_store(value: Any) -> str:
    """The canonical store a word names.

    A store is one of :data:`STORES` - the
    workspace store or the user store - read
    case-insensitively, with the long spellings
    (``workspace-store``, ``user-store``) read
    onto their stores. Anything else raises,
    plainly naming the set.
    """
    if isinstance(value, str):
        wanted = _STORE_ALIASES.get(value.strip().lower())
        if wanted is not None:
            return wanted
    raise ValueError(
        "a memory's store must be one of %s, got %r"
        % ("/".join(STORES), value))


def normalize_extent(value: Any) -> str:
    """The canonical extent a word names.

    An extent is one of :data:`EXTENTS` - one
    contained piece, or the store as a whole -
    read case-insensitively, with plain spellings
    (``single``, ``whole-store``) read onto their
    extents. Anything else raises, plainly naming
    the set.
    """
    if isinstance(value, str):
        wanted = _EXTENT_ALIASES.get(value.strip().lower())
        if wanted is not None:
            return wanted
    raise ValueError(
        "an extent must be one of %s, got %r"
        % ("/".join(EXTENTS), value))


# ---------------------------------------------------------------------
# The memory finding: one check over one stored memory, as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class MemoryFinding:
    """One memory finding: a check, stood over one stored memory.

    ``title`` names the finding in plain words;
    ``check`` is the check that raised it - a
    corrupt store, an orphaned vector, or map
    drift; the stored memory it stands over is
    named by ``memory_kind`` (the holding it
    stands in) and ``memory_ref`` (the shipped
    piece's id alone - the piece's own words never
    cross into this record). ``store`` is the
    store the memory lives in - the workspace
    store or the user store. ``detail`` is what
    the check saw, in plain words. ``extent`` is
    how far the trouble reaches - one contained
    piece, or the store as a whole. The
    provenance stands whole beside those:
    ``found_on`` the day the check ran,
    ``recorded_by`` who ran it, ``origin_session``
    the session it ran in and ``source`` where
    the finding was read from. What may be done
    is never a field: the disposition is derived
    by :func:`disposition_of`, the safe repair by
    :func:`repair_action_of`, and the plain line
    by :func:`repair_line`.
    """

    title: str
    check: str
    memory_kind: str
    memory_ref: str
    store: str
    detail: str
    found_on: str
    recorded_by: str
    source: str
    origin_session: str
    extent: str = "contained"
    finding_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.finding_id is not None:
            object.__setattr__(
                self, "finding_id",
                normalize_member_id(self.finding_id))
        object.__setattr__(
            self, "title", _check_title(self.title, "a finding's title"))
        object.__setattr__(
            self, "check", normalize_check(self.check))
        object.__setattr__(
            self, "memory_kind", normalize_memory_kind(self.memory_kind))
        object.__setattr__(
            self, "memory_ref",
            _check_word(self.memory_ref, "a finding's memory ref"))
        object.__setattr__(
            self, "store", normalize_store(self.store))
        object.__setattr__(
            self, "detail",
            _check_long_text(self.detail, "a finding's detail"))
        object.__setattr__(
            self, "extent", normalize_extent(self.extent))
        object.__setattr__(
            self, "found_on",
            _check_day(self.found_on, "a finding's found-on day"))
        object.__setattr__(
            self, "recorded_by",
            _check_title(self.recorded_by, "a finding's recorder"))
        object.__setattr__(
            self, "source",
            _check_title(self.source, "a finding's source"))
        object.__setattr__(
            self, "origin_session",
            _check_word(self.origin_session, "a finding's origin session"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "memory_doctor_finding",
            "slice": MEMORY_DOCTOR_SLICE,
            "finding_id": self.finding_id,
            "title": self.title,
            "check": self.check,
            "memory_kind": self.memory_kind,
            "memory_ref": self.memory_ref,
            "store": self.store,
            "detail": self.detail,
            "extent": self.extent,
            "found_on": self.found_on,
            "recorded_by": self.recorded_by,
            "source": self.source,
            "origin_session": self.origin_session,
            "disposition": disposition_of(self),
            "action": repair_action_of(self),
            "repair": repair_line(self),
        }


def _check_finding_ref(value: Any) -> "MemoryFinding":
    if isinstance(value, MemoryFinding):
        return value
    if isinstance(value, dict):
        return validate_finding(value)
    raise ValueError(f"a memory finding is needed, got {value!r}")


def validate_finding(finding: Any) -> MemoryFinding:
    """Validate one finding into a MemoryFinding.

    Accepts a finding or a mapping naming a
    ``title`` (or ``name`` / ``subject``), a
    ``check`` (or ``check_kind``), a
    ``memory_kind`` (or ``kind``), a ``memory_ref``
    (or ``ref``), a ``store`` (or ``home``), a
    ``detail`` (or ``evidence`` / ``seen``), a
    ``found_on`` (or ``day`` / ``date``), a
    ``recorded_by`` (or ``recorder`` / ``by`` /
    ``who``), a ``source``, an ``origin_session``
    (or ``session``) and, optionally, an
    ``extent`` (or ``reach``, ``contained`` when
    it stands unnamed) and a ``finding_id`` (or
    ``id``). Derived keys a finding record
    carries (``disposition``, ``action``,
    ``repair``, ``type``, ``slice``) are not
    finding fields and refuse as unknown keys.
    Naming two spellings of one field with
    different values refuses, and unknown keys
    refuse.
    """
    if isinstance(finding, MemoryFinding):
        return finding
    if not isinstance(finding, dict):
        raise ValueError(f"a memory finding is needed, got {finding!r}")
    unknown = set(finding) - _FINDING_KEYS
    if unknown:
        raise ValueError(
            "unknown finding keys: %s" % ", ".join(sorted(unknown)))

    def _needed(spellings: Tuple[str, ...], what: str) -> Any:
        value = _pick_any(finding, spellings, what)
        if value is None:
            raise ValueError(f"a finding is missing its {what}")
        return value

    kwargs: Dict[str, Any] = {
        "title": _needed(("title", "name", "subject"), "title"),
        "check": _needed(("check", "check_kind"), "check"),
        "memory_kind": _needed(("memory_kind", "kind"), "memory kind"),
        "memory_ref": _needed(("memory_ref", "ref"), "memory ref"),
        "store": _needed(("store", "home"), "store"),
        "detail": _needed(("detail", "evidence", "seen"), "detail"),
        "found_on": _needed(("found_on", "day", "date"), "found day"),
        "recorded_by": _needed(
            ("recorded_by", "recorder", "by", "who"), "recorder"),
        "source": _needed(("source",), "source"),
        "origin_session": _needed(
            ("origin_session", "session"), "origin session"),
    }
    extent = _pick_any(finding, ("extent", "reach"), "extents")
    if extent is not None:
        kwargs["extent"] = extent
    finding_id = _pick_any(finding, ("finding_id", "id"), "finding ids")
    if finding_id is not None:
        kwargs["finding_id"] = finding_id
    return MemoryFinding(**kwargs)


def build_finding(finding: Any = None, **kwargs: Any) -> MemoryFinding:
    """Build one validated finding, from a mapping or field words."""
    if isinstance(finding, MemoryFinding) and not kwargs:
        return finding
    if isinstance(finding, dict) or finding is None:
        merged: Dict[str, Any] = {}
        if isinstance(finding, dict):
            merged.update(finding)
        merged.update(kwargs)
        return validate_finding(merged)
    raise ValueError(f"a memory finding is needed, got {finding!r}")


def disposition_of(finding: Any) -> str:
    """How one finding stands toward repair: derived, never chosen.

    Repair-ready while the trouble is contained
    to one piece - the doctor's derived repair
    may be applied to the held book - and
    referred while the trouble reaches the store
    as a whole: no repair is derived there, and
    the user is told plainly.
    """
    current = _check_finding_ref(finding)
    if current.extent == "store-wide":
        return "referred"
    return "repair-ready"


def repair_action_of(finding: Any) -> str:
    """The safe repair one finding derives: derived, never chosen.

    A contained corrupt piece is quarantined, a
    contained orphaned vector is dropped, a
    contained drifted map entry is realigned -
    and a store-wide finding derives
    :data:`REFERRED_ACTION`, no repair at all.
    """
    current = _check_finding_ref(finding)
    if current.extent == "store-wide":
        return REFERRED_ACTION
    return _REPAIR_BY_CHECK[current.check]


def repair_line(finding: Any) -> str:
    """The repair one finding shows on the panel, derived.

    A repair-ready finding names its one safe
    repair and the held book it lands on; a
    referred finding names that the doctor will
    not repair it and why - store-wide trouble is
    the user's call, never the doctor's quiet fix.
    """
    current = _check_finding_ref(finding)
    if current.extent == "store-wide":
        return (
            f"the {current.check} trouble over the "
            f"{current.memory_kind} memory "
            f"{current.memory_ref} reaches the whole "
            f"{current.store} store - the doctor will "
            f"not repair it; it is referred to the user")
    action = _REPAIR_BY_CHECK[current.check]
    return (
        f"safe repair for the {current.memory_kind} "
        f"memory {current.memory_ref} in the "
        f"{current.store} store: {action} - applied "
        f"to the held book only, no live store is "
        f"rewritten")


# ---------------------------------------------------------------------
# Composition: shipped holdings read onto findings, by import.
# ---------------------------------------------------------------------


def _raised_finding(*, check: str, memory_kind: str,
                    memory_ref: Optional[str], piece_word: str,
                    title: Any, store: Any, detail: Any,
                    extent: Any, found_on: Any, recorded_by: Any,
                    source: Any, origin_session: Any,
                    finding_id: Any) -> MemoryFinding:
    if memory_ref is None:
        raise ValueError(
            f"a {piece_word} with no id cannot be checked "
            f"- a memory finding names its stored "
            f"memory by id")
    return MemoryFinding(
        title=title if title is not None else (
            f"the {memory_kind} memory {memory_ref}, "
            f"found by the {check} check"),
        check=check, memory_kind=memory_kind,
        memory_ref=memory_ref, store=store, detail=detail,
        extent=extent, found_on=found_on,
        recorded_by=recorded_by, source=source,
        origin_session=origin_session,
        finding_id=finding_id if finding_id is not None else (
            f"finding-{check}-{memory_ref}"))


def finding_from_map_entry(entry: Any, *, check: Any, store: Any,
                           detail: Any, found_on: Any,
                           recorded_by: Any, origin_session: Any,
                           source: Any = "memory doctor",
                           title: Any = None,
                           extent: Any = "contained",
                           finding_id: Any = None) -> MemoryFinding:
    """Raise one finding over a project memory-map entry, by import.

    The entry (M-150) is judged by the map's own
    ``validate_entry``; only its id crosses - it
    stands as the finding's memory ref, of kind
    ``memory-map``. The entry's own title, detail
    and reference are never read here: the
    finding names the check that ran and what it
    saw, in the caller's plain words.
    """
    checked = _validate_map_entry(entry)
    return _raised_finding(
        check=normalize_check(check), memory_kind="memory-map",
        memory_ref=checked.entry_id, piece_word="memory map entry",
        title=title, store=store, detail=detail, extent=extent,
        found_on=found_on, recorded_by=recorded_by, source=source,
        origin_session=origin_session, finding_id=finding_id)


def finding_from_session_note(note: Any, *, check: Any, store: Any,
                              detail: Any, found_on: Any,
                              recorded_by: Any, origin_session: Any,
                              source: Any = "memory doctor",
                              title: Any = None,
                              extent: Any = "contained",
                              finding_id: Any = None) -> MemoryFinding:
    """Raise one finding over a session-memory note, by import.

    The carried note (M-153) is judged by the
    session layer's own ``validate_note``; only
    its id crosses - it stands as the finding's
    memory ref, of kind ``session-note``.
    """
    checked = _validate_note(note)
    return _raised_finding(
        check=normalize_check(check), memory_kind="session-note",
        memory_ref=checked.note_id, piece_word="session note",
        title=title, store=store, detail=detail, extent=extent,
        found_on=found_on, recorded_by=recorded_by, source=source,
        origin_session=origin_session, finding_id=finding_id)


def finding_from_cross_project_lesson(lesson: Any, *, check: Any,
                                      store: Any, detail: Any,
                                      found_on: Any,
                                      recorded_by: Any,
                                      origin_session: Any,
                                      source: Any = "memory doctor",
                                      title: Any = None,
                                      extent: Any = "contained",
                                      finding_id: Any = None
                                      ) -> MemoryFinding:
    """Raise one finding over a cross-project lesson, by import.

    The lesson (M-154) is judged by the
    cross-project layer's own ``validate_lesson``;
    only its id crosses - it stands as the
    finding's memory ref, of kind
    ``cross-project-lesson``.
    """
    checked = _validate_lesson(lesson)
    return _raised_finding(
        check=normalize_check(check),
        memory_kind="cross-project-lesson",
        memory_ref=checked.lesson_id,
        piece_word="cross-project lesson", title=title, store=store,
        detail=detail, extent=extent, found_on=found_on,
        recorded_by=recorded_by, source=source,
        origin_session=origin_session, finding_id=finding_id)


def finding_from_ledger_candidate(candidate: Any, *, check: Any,
                                  store: Any, detail: Any,
                                  found_on: Any, recorded_by: Any,
                                  origin_session: Any,
                                  source: Any = "memory doctor",
                                  title: Any = None,
                                  extent: Any = "contained",
                                  finding_id: Any = None
                                  ) -> MemoryFinding:
    """Raise one finding over a self-improving ledger candidate.

    The candidate (M-155) is judged by the
    ledger's own ``validate_candidate``; only its
    id crosses - it stands as the finding's
    memory ref, of kind ``ledger-candidate``.
    """
    checked = _validate_candidate(candidate)
    return _raised_finding(
        check=normalize_check(check),
        memory_kind="ledger-candidate",
        memory_ref=checked.candidate_id,
        piece_word="ledger candidate", title=title, store=store,
        detail=detail, extent=extent, found_on=found_on,
        recorded_by=recorded_by, source=source,
        origin_session=origin_session, finding_id=finding_id)


def finding_from_crew_entry(entry: Any, *, check: Any, store: Any,
                            detail: Any, found_on: Any,
                            recorded_by: Any, origin_session: Any,
                            source: Any = "memory doctor",
                            title: Any = None,
                            extent: Any = "contained",
                            finding_id: Any = None) -> MemoryFinding:
    """Raise one finding over a crew-memory entry, by import.

    The entry (M-133) is judged by crew memory's
    own ``validate_entry``; only its id crosses -
    it stands as the finding's memory ref, of
    kind ``crew-fact``. The fact's own words never
    cross.
    """
    checked = _validate_crew_entry(entry)
    return _raised_finding(
        check=normalize_check(check), memory_kind="crew-fact",
        memory_ref=checked.entry_id, piece_word="crew entry",
        title=title, store=store, detail=detail, extent=extent,
        found_on=found_on, recorded_by=recorded_by, source=source,
        origin_session=origin_session, finding_id=finding_id)


def finding_from_subconscious_memory(memory: Any, *, check: Any,
                                     store: Any, detail: Any,
                                     found_on: Any,
                                     recorded_by: Any,
                                     origin_session: Any,
                                     source: Any = "memory doctor",
                                     title: Any = None,
                                     extent: Any = "contained",
                                     finding_id: Any = None
                                     ) -> MemoryFinding:
    """Raise one finding over a subconscious v2 memory, by import.

    The v2 memory (M-165) is judged by its own
    layer's ``validate_memory``; only its id
    crosses - it stands as the finding's memory
    ref, of kind ``subconscious-memory``. A v2
    memory with no id cannot be checked. The
    memory's own title and provenance words never
    cross into the finding.
    """
    checked = _validate_v2_memory(memory)
    return _raised_finding(
        check=normalize_check(check),
        memory_kind="subconscious-memory",
        memory_ref=checked.memory_id,
        piece_word="subconscious memory", title=title, store=store,
        detail=detail, extent=extent, found_on=found_on,
        recorded_by=recorded_by, source=source,
        origin_session=origin_session, finding_id=finding_id)


def finding_from_contradiction_watch(watch: Any, *, check: Any,
                                     store: Any, detail: Any,
                                     found_on: Any,
                                     recorded_by: Any,
                                     origin_session: Any,
                                     source: Any = "memory doctor",
                                     title: Any = None,
                                     extent: Any = "contained",
                                     finding_id: Any = None
                                     ) -> MemoryFinding:
    """Raise one finding over a contradiction watch, by import.

    The watch (M-166) is judged by the watch
    layer's own ``validate_watch``; only its id
    crosses - it stands as the finding's memory
    ref, of kind ``contradiction-watch``. A watch
    with no id cannot be checked. The watch's own
    claims never cross into the finding.
    """
    checked = _validate_watch(watch)
    return _raised_finding(
        check=normalize_check(check),
        memory_kind="contradiction-watch",
        memory_ref=checked.watch_id,
        piece_word="contradiction watch", title=title, store=store,
        detail=detail, extent=extent, found_on=found_on,
        recorded_by=recorded_by, source=source,
        origin_session=origin_session, finding_id=finding_id)


def finding_from_privacy_posting(posting: Any, *, check: Any,
                                 store: Any = None, detail: Any,
                                 found_on: Any, recorded_by: Any,
                                 origin_session: Any,
                                 source: Any = "memory doctor",
                                 title: Any = None,
                                 extent: Any = "contained",
                                 finding_id: Any = None
                                 ) -> MemoryFinding:
    """Raise one finding over a privacy posting, by import.

    The posting (M-167) is judged by the privacy
    layer's own ``validate_posting``; the memory
    it stands over crosses - its kind and its ref
    alone - and stands as the finding's memory.
    The store defaults to the posting's own home:
    the finding stands over the memory the
    posting names, in the store the posting says
    it lives in. The posting's own boundary words
    never cross into the finding.
    """
    checked = _validate_posting(posting)
    return _raised_finding(
        check=normalize_check(check),
        memory_kind=checked.memory_kind,
        memory_ref=checked.memory_ref,
        piece_word="privacy posting", title=title,
        store=store if store is not None else checked.home,
        detail=detail, extent=extent, found_on=found_on,
        recorded_by=recorded_by, source=source,
        origin_session=origin_session, finding_id=finding_id)


# ---------------------------------------------------------------------
# The checks themselves: run by import, findings raised only on failure.
# ---------------------------------------------------------------------

#: The shipped holdings the corrupt-store check
#: can judge, by the kind a raw store piece
#: stands under: each holding's own validator
#: and the id field its pieces carry.
_CORRUPT_ROADS = {
    "memory-map": (_validate_map_entry, "entry_id", ("entry_id", "id")),
    "session-note": (_validate_note, "note_id", ("note_id", "id")),
    "cross-project-lesson": (
        _validate_lesson, "lesson_id", ("lesson_id", "id")),
    "ledger-candidate": (
        _validate_candidate, "candidate_id", ("candidate_id", "id")),
    "crew-fact": (_validate_crew_entry, "entry_id", ("entry_id", "id")),
    "subconscious-memory": (
        _validate_v2_memory, "memory_id", ("memory_id", "id")),
    "contradiction-watch": (
        _validate_watch, "watch_id", ("watch_id", "id")),
}


def finding_from_corrupt_piece(holding: Any, raw: Any, *, store: Any,
                               found_on: Any, recorded_by: Any,
                               origin_session: Any,
                               source: Any = "memory doctor",
                               title: Any = None,
                               extent: Any = "contained",
                               finding_id: Any = None
                               ) -> MemoryFinding:
    """Run the corrupt-store check over one raw store piece.

    The raw piece - a mapping as a store file
    carries it - is judged by the validator of
    the holding it stands under (``holding`` is
    one of the shipped holdings the check knows).
    A piece its own layer accepts is no finding:
    the check raises, plainly saying the piece
    stands sound. A piece its own layer refuses
    raises a ``corrupt-store`` finding whose
    detail carries the validator's own refusal,
    shortened to its first words; only the
    piece's id crosses into the finding.
    """
    kind = normalize_memory_kind(holding)
    road = _CORRUPT_ROADS.get(kind)
    if road is None:
        raise ValueError(
            f"the corrupt-store check knows no holding "
            f"road for {kind!r} - it judges %s"
            % "/".join(sorted(_CORRUPT_ROADS)))
    validator, _id_attr, id_keys = road
    ref = None
    if isinstance(raw, dict):
        for key in id_keys:
            if raw.get(key):
                ref = str(raw[key])
                break
    try:
        checked = validator(raw)
    except Exception as exc:
        detail = (
            f"the {kind} piece "
            f"{ref or 'with no id'} fails its own "
            f"layer's validation: {exc}")
        return _raised_finding(
            check="corrupt-store", memory_kind=kind,
            memory_ref=ref, piece_word=f"{kind} piece",
            title=title, store=store, detail=detail[:480],
            extent=extent, found_on=found_on,
            recorded_by=recorded_by, source=source,
            origin_session=origin_session,
            finding_id=finding_id)
    raise ValueError(
        f"no corruption found: the {kind} piece "
        f"{getattr(checked, _id_attr, None)!r} stands "
        f"sound under its own layer's validation")


def finding_from_orphaned_vector(record: Any, known_refs: Any, *,
                                 store: Any, found_on: Any,
                                 recorded_by: Any,
                                 origin_session: Any,
                                 source: Any = "memory doctor",
                                 title: Any = None,
                                 extent: Any = "contained",
                                 finding_id: Any = None
                                 ) -> MemoryFinding:
    """Run the orphaned-vector check over one vector record.

    The record - a vector record mapping, or a
    privacy posting standing over a vector
    record - names its memory by ref alone. A ref
    standing in *known_refs* (the refs the held
    stores actually carry) is no finding: the
    check raises, plainly saying the vector is
    held. A ref no held store carries raises an
    ``orphaned-vector`` finding over that ref.
    """
    info = inspect_finding_source(record)
    if info["memory_kind"] != "vector-record":
        raise ValueError(
            f"the orphaned-vector check judges vector "
            f"records, got a {info['memory_kind']} piece")
    ref = info["memory_ref"]
    if ref is None:
        raise ValueError(
            "a vector record with no id cannot be checked "
            "- a memory finding names its stored "
            "memory by id")
    known = {_check_word(item, "a known ref") for item in known_refs}
    if ref in known:
        raise ValueError(
            f"no orphan found: the vector record {ref!r} "
            f"names a memory a held store carries")
    return _raised_finding(
        check="orphaned-vector", memory_kind="vector-record",
        memory_ref=ref, piece_word="vector record", title=title,
        store=store,
        detail=(
            f"the vector record's metadata names {ref}, "
            f"and no held memory store carries a memory "
            f"under that ref"),
        extent=extent, found_on=found_on,
        recorded_by=recorded_by, source=source,
        origin_session=origin_session, finding_id=finding_id)


def finding_from_drifted_map_entry(entry: Any, present_refs: Any, *,
                                   store: Any, found_on: Any,
                                   recorded_by: Any,
                                   origin_session: Any,
                                   source: Any = "memory doctor",
                                   title: Any = None,
                                   extent: Any = "contained",
                                   finding_id: Any = None
                                   ) -> MemoryFinding:
    """Run the map-drift check over one project memory-map entry.

    The entry (M-150) is judged by the map's own
    ``validate_entry``; the path its ``ref`` names
    is stood against *present_refs* (the paths
    the project actually carries). A path still
    present is no finding: the check raises,
    plainly saying the entry stands true. A path
    no longer present raises a ``map-drift``
    finding over the entry, its id alone crossing.
    """
    checked = _validate_map_entry(entry)
    present = {str(item) for item in present_refs}
    if checked.ref in present:
        raise ValueError(
            f"no drift found: the map entry "
            f"{checked.entry_id!r} names {checked.ref}, "
            f"which the project still carries")
    return _raised_finding(
        check="map-drift", memory_kind="memory-map",
        memory_ref=checked.entry_id,
        piece_word="memory map entry", title=title, store=store,
        detail=(
            f"the map entry names {checked.ref}, and "
            f"no held store path carries that path "
            f"any longer"),
        extent=extent, found_on=found_on,
        recorded_by=recorded_by, source=source,
        origin_session=origin_session, finding_id=finding_id)


def inspect_finding_source(piece: Any) -> Dict[str, Any]:
    """Inspect one shipped piece: its kind and ref only.

    The piece is judged by the layer that owns its
    type, never by whichever validator happens to
    accept its shape first. A finding reports the
    memory it stands over; each shipped holding
    reports the kind and ref a finding raised over
    it would carry. A piece no shipped layer owns
    refuses.
    """
    if isinstance(piece, MemoryFinding):
        return {"memory_kind": piece.memory_kind,
                "memory_ref": piece.memory_ref}
    if isinstance(piece, PrivacyPosting):
        return {"memory_kind": piece.memory_kind,
                "memory_ref": piece.memory_ref}
    if isinstance(piece, ContradictionWatch):
        return {"memory_kind": "contradiction-watch",
                "memory_ref": piece.watch_id}
    if isinstance(piece, SubconsciousMemory):
        return {"memory_kind": "subconscious-memory",
                "memory_ref": piece.memory_id}
    if isinstance(piece, MemoryMapEntry):
        return {"memory_kind": "memory-map",
                "memory_ref": piece.entry_id}
    if isinstance(piece, CandidateMemory):
        return {"memory_kind": "ledger-candidate",
                "memory_ref": piece.candidate_id}
    if isinstance(piece, CarriedMemory):
        return {"memory_kind": "session-note",
                "memory_ref": piece.note_id}
    if isinstance(piece, CrewMemoryEntry):
        return {"memory_kind": "crew-fact",
                "memory_ref": piece.entry_id}
    if isinstance(piece, SharedLesson):
        return {"memory_kind": "cross-project-lesson",
                "memory_ref": piece.lesson_id}
    if isinstance(piece, dict):
        if "vector" in piece and "text" in piece:
            metadata = piece.get("metadata") or {}
            if not isinstance(metadata, dict):
                raise ValueError(
                    "a vector record's metadata must be a mapping")
            ref = None
            for key in ("id", "name", "path"):
                if metadata.get(key):
                    ref = metadata[key]
                    break
            if ref is not None and not isinstance(ref, str):
                ref = str(ref)
            return {"memory_kind": "vector-record", "memory_ref": ref}
        for road, kind in (
                (_validate_map_entry, "memory-map"),
                (_validate_watch, "contradiction-watch"),
                (_validate_candidate, "ledger-candidate"),
                (_validate_note, "session-note"),
                (_validate_crew_entry, "crew-fact"),
                (_validate_lesson, "cross-project-lesson"),
                (_validate_v2_memory, "subconscious-memory"),
                (_validate_posting, "privacy-posting")):
            try:
                checked = road(piece)
            except Exception:
                continue
            if kind == "privacy-posting":
                return {"memory_kind": checked.memory_kind,
                        "memory_ref": checked.memory_ref}
            ref = getattr(checked, "entry_id", None) or getattr(
                checked, "candidate_id", None) or getattr(
                checked, "note_id", None) or getattr(
                checked, "lesson_id", None) or getattr(
                checked, "memory_id", None) or getattr(
                checked, "watch_id", None)
            return {"memory_kind": kind, "memory_ref": ref}
    raise ValueError(
        f"no shipped layer owns this piece, got {piece!r}")


# ---------------------------------------------------------------------
# The doctor panel: every finding carried whole, derived.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class DoctorPanelRow:
    """One finding carried whole into the panel, its repair shown.

    Every field is the finding's own head - its
    id, title, the check that raised it, the
    memory it stands over (kind and ref), the
    store the memory lives in, how far the
    trouble reaches and the day the check ran -
    beside the disposition and the repair read
    off the finding itself: repair-ready with its
    one safe repair, or referred with none.
    :func:`validate_row` judged against its
    finding refuses a row whose fields disagree
    with the row it derives.
    """

    finding_id: str
    title: str
    check: str
    memory_kind: str
    memory_ref: str
    store: str
    extent: str
    disposition: str
    action: str
    found_on: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "finding_id", normalize_member_id(self.finding_id))
        object.__setattr__(
            self, "title", _check_title(self.title, "a row's title"))
        object.__setattr__(
            self, "check", normalize_check(self.check))
        object.__setattr__(
            self, "memory_kind", normalize_memory_kind(self.memory_kind))
        object.__setattr__(
            self, "memory_ref",
            _check_word(self.memory_ref, "a row's memory ref"))
        object.__setattr__(
            self, "store", normalize_store(self.store))
        object.__setattr__(
            self, "extent", normalize_extent(self.extent))
        word = _clean_text(self.disposition, "a row's disposition")
        derived = "referred" if self.extent == "store-wide" else "repair-ready"
        if word != derived:
            raise ValueError(
                f"a row's disposition must be the "
                f"disposition its own extent derives "
                f"({derived!r}) - a store-wide finding "
                f"stands referred, got {word!r}")
        object.__setattr__(self, "disposition", word)
        action = _clean_text(self.action, "a row's action")
        derived_action = (
            REFERRED_ACTION if self.extent == "store-wide"
            else _REPAIR_BY_CHECK[self.check])
        if action != derived_action:
            raise ValueError(
                f"a row's action must be the repair its "
                f"own check and extent derive "
                f"({derived_action!r}), got {action!r}")
        object.__setattr__(self, "action", action)
        object.__setattr__(
            self, "found_on",
            _check_day(self.found_on, "a row's found-on day"))

    @property
    def sort_key(self) -> Tuple[int, str, str]:
        """This row's place in panel order (derived).

        Rows stand by check - corrupt stores first,
        then orphaned vectors, then map drift, in
        the roadmap's own order - then title, then
        finding id.
        """
        return (CHECKS.index(self.check), self.title.lower(), self.finding_id)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "memory_doctor_panel_row",
            "slice": MEMORY_DOCTOR_SLICE,
            "finding_id": self.finding_id,
            "title": self.title,
            "check": self.check,
            "memory_kind": self.memory_kind,
            "memory_ref": self.memory_ref,
            "store": self.store,
            "extent": self.extent,
            "disposition": self.disposition,
            "action": self.action,
            "found_on": self.found_on,
        }


def _row_for_finding(finding: MemoryFinding) -> DoctorPanelRow:
    return DoctorPanelRow(
        finding_id=finding.finding_id, title=finding.title,
        check=finding.check, memory_kind=finding.memory_kind,
        memory_ref=finding.memory_ref, store=finding.store,
        extent=finding.extent, disposition=disposition_of(finding),
        action=repair_action_of(finding), found_on=finding.found_on)


def _check_row_ref(value: Any) -> DoctorPanelRow:
    if isinstance(value, DoctorPanelRow):
        return value
    if isinstance(value, dict):
        return validate_row(value)
    raise ValueError(f"a panel row is needed, got {value!r}")


def validate_row(row: Any, finding: Any = None) -> DoctorPanelRow:
    """Validate one panel row into a DoctorPanelRow.

    Accepts a row or a mapping naming its fields.
    With *finding* given, the row is judged
    against the row that finding derives.
    """
    if isinstance(row, DoctorPanelRow):
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

        current = DoctorPanelRow(
            finding_id=_needed(("finding_id", "id"), "finding id"),
            title=_needed(("title",), "title"),
            check=_needed(("check",), "check"),
            memory_kind=_needed(("memory_kind",), "memory kind"),
            memory_ref=_needed(("memory_ref",), "memory ref"),
            store=_needed(("store",), "store"),
            extent=_needed(("extent",), "extent"),
            disposition=_needed(("disposition",), "disposition"),
            action=_needed(("action",), "action"),
            found_on=_needed(("found_on",), "found-on day"))
    else:
        raise ValueError(f"a panel row must be a mapping, got {row!r}")
    if finding is not None:
        derived = _row_for_finding(_check_finding_ref(finding))
        if current != derived:
            raise ValueError(
                "a stored row disagrees with the row "
                "its finding derives")
    return current


def build_row(row: Any = None, finding: Any = None,
              **kwargs: Any) -> DoctorPanelRow:
    """Build one validated row, from a mapping or field words."""
    if isinstance(row, DoctorPanelRow) and not kwargs:
        return validate_row(row, finding)
    if isinstance(row, dict) or row is None:
        merged: Dict[str, Any] = {}
        if isinstance(row, dict):
            merged.update(row)
        merged.update(kwargs)
        return validate_row(merged, finding)
    return validate_row(row, finding)


@dataclass(frozen=True)
class CheckCount:
    """How many of a panel's findings one check raised."""

    check: str
    items: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "check", normalize_check(self.check))
        object.__setattr__(
            self, "items", _check_count(self.items, "a check count"))

    def to_record(self) -> Dict[str, Any]:
        return {"check": self.check, "items": self.items}


def _check_check_count_ref(value: Any) -> CheckCount:
    if isinstance(value, CheckCount):
        return value
    if isinstance(value, dict):
        unknown = set(value) - _CHECK_COUNT_KEYS
        if unknown:
            raise ValueError(
                "unknown check-count keys: %s"
                % ", ".join(sorted(unknown)))
        check = _pick_any(value, ("check",), "checks")
        if check is None:
            raise ValueError("a check count is missing its check")
        items = _pick_any(value, ("items", "count"), "counts")
        if items is None:
            raise ValueError("a check count is missing its count")
        return CheckCount(check=check, items=items)
    raise ValueError(f"a check count is needed, got {value!r}")


def _panel_account(total_findings: int, total_ready: int,
                   total_referred: int, distinct_memories: int,
                   check_counts: Tuple[CheckCount, ...], as_of: str
                   ) -> Tuple[str, ...]:
    tallies = ", ".join(
        f"{count.check} {count.items}"
        for count in sorted(check_counts, key=lambda count: count.check))
    return (
        f"The memory doctor panel holds {total_findings} "
        f"findings as of {as_of}: {total_ready} "
        f"safely repairable and {total_referred} "
        f"referred beyond the doctor over "
        f"{distinct_memories} stored memories: "
        f"{tallies}.",
        "Rows stand by check - corrupt stores first, "
        "then orphaned vectors, then map drift - "
        "then title, then finding id, so two panels "
        "of one book diff cleanly, line by line.",
        "Every row shows its repair: a contained "
        "finding names its one derived safe repair, "
        "and a store-wide finding names none - it is "
        "referred to the user, and the doctor will "
        "not repair it.",
        "The panel is read off the book at call "
        "time - it is derived, never stored loose - "
        "and a repair applied here marks a held "
        "finding repaired in this book only: no live "
        "store is rewritten by standing on this panel.",
    )


@dataclass(frozen=True)
class DoctorPanel:
    """The doctor panel of one book, derived.

    ``rows`` are the book's findings carried
    whole, in panel order (by check - corrupt
    stores first, then orphaned vectors, then map
    drift - then title, then finding id), each
    showing its derived repair; ``total_findings``
    is the rows' own count, ``total_ready`` the
    rows standing repair-ready and
    ``total_referred`` the rows standing referred
    - the two dispositions' counts stand summing
    to the total, and a panel that says otherwise
    refuses; ``distinct_memories`` counts the
    stored memories the rows stand over, and
    ``check_counts`` the per-check tallies of
    their checks. ``as_of`` is the rows' own
    latest found day. ``account`` is read off
    those numbers. A panel whose rows stand out
    of panel order, or whose tallies are not its
    own rows' tallies, refuses at construction;
    :func:`validate_panel` judged against a book
    refuses a stored panel that disagrees with
    the derived one.
    """

    rows: Tuple[DoctorPanelRow, ...] = ()
    total_findings: int = 0
    total_ready: int = 0
    total_referred: int = 0
    distinct_memories: int = 0
    check_counts: Tuple[CheckCount, ...] = ()
    account: Tuple[str, ...] = ()
    as_of: str = ""
    panel_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.panel_id is not None:
            object.__setattr__(
                self, "panel_id", normalize_member_id(self.panel_id))
        object.__setattr__(
            self, "as_of", _check_day(self.as_of, "a panel's as-of day"))
        if isinstance(self.rows, (str, bytes)) \
                or not isinstance(self.rows, (list, tuple)):
            raise ValueError(
                f"a panel's rows must be a list of rows, "
                f"got {self.rows!r}")
        rows = tuple(_check_row_ref(r) for r in self.rows)
        seen = set()
        for row in rows:
            if row.finding_id in seen:
                raise ValueError(
                    f"a panel row for finding {row.finding_id!r} "
                    f"already exists")
            seen.add(row.finding_id)
        keys = [row.sort_key for row in rows]
        if keys != sorted(keys):
            raise ValueError(
                "a panel's rows must stand in panel order "
                "(by check, then title, then finding id)")
        object.__setattr__(self, "rows", rows)
        object.__setattr__(
            self, "total_findings",
            _check_count(self.total_findings, "a panel's total findings"))
        if self.total_findings != len(rows):
            raise ValueError(
                "a panel's total findings must be its own "
                "rows' count")
        object.__setattr__(
            self, "total_ready",
            _check_count(self.total_ready, "a panel's total ready"))
        if self.total_ready != sum(
                1 for r in rows if r.disposition == "repair-ready"):
            raise ValueError(
                "a panel's ready count must be its own "
                "rows' repair-ready count")
        object.__setattr__(
            self, "total_referred",
            _check_count(self.total_referred, "a panel's total referred"))
        if self.total_referred != sum(
                1 for r in rows if r.disposition == "referred"):
            raise ValueError(
                "a panel's referred count must be its "
                "own rows' referred count")
        if self.total_ready + self.total_referred != self.total_findings:
            raise ValueError(
                "a panel's dispositions must sum to its "
                "own total findings - every finding "
                "stands repair-ready or referred")
        object.__setattr__(
            self, "distinct_memories",
            _check_count(
                self.distinct_memories, "a panel's distinct memories"))
        if self.distinct_memories != len({
                (r.memory_kind, r.memory_ref) for r in rows}):
            raise ValueError(
                "a panel's distinct memories must be its "
                "own rows' distinct memories")
        if rows and self.as_of != max(r.found_on for r in rows):
            raise ValueError(
                "a panel's as-of day must be its own "
                "rows' latest found day")
        if isinstance(self.check_counts, (str, bytes)) \
                or not isinstance(self.check_counts, (list, tuple)):
            raise ValueError(
                f"a panel's check counts must be a list, "
                f"got {self.check_counts!r}")
        check_counts = tuple(
            _check_check_count_ref(c) for c in self.check_counts)
        seen_checks = set()
        for count in check_counts:
            if count.check in seen_checks:
                raise ValueError(
                    f"a check count named {count.check!r} "
                    f"already exists")
            seen_checks.add(count.check)
        object.__setattr__(self, "check_counts", check_counts)
        if sum(c.items for c in check_counts) != self.total_findings:
            raise ValueError(
                "a panel's check counts must sum to its "
                "own total findings")
        tallies = {
            check: sum(1 for r in rows if r.check == check)
            for check in CHECKS}
        for count in check_counts:
            if count.items != tallies.get(count.check, 0):
                raise ValueError(
                    "a panel's check counts must be its "
                    "own rows' counts")
        if {k for k, v in tallies.items() if v} != {
                c.check for c in check_counts}:
            raise ValueError(
                "a panel's check counts must name every "
                "check its rows were raised by")
        object.__setattr__(self, "account", _check_account(self.account))

    def row_for(self, finding_id: Any) -> DoctorPanelRow:
        """The panel row one finding names in this panel."""
        wanted = normalize_member_id(finding_id)
        for row in self.rows:
            if row.finding_id == wanted:
                return row
        raise KeyError(f"no row in the panel: finding {wanted!r}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "memory_doctor_panel",
            "slice": MEMORY_DOCTOR_SLICE,
            "panel_id": self.panel_id,
            "rows": [row.to_record() for row in self.rows],
            "total_findings": self.total_findings,
            "total_ready": self.total_ready,
            "total_referred": self.total_referred,
            "distinct_memories": self.distinct_memories,
            "check_counts": [c.to_record() for c in self.check_counts],
            "as_of": self.as_of,
            "account": list(self.account),
        }


def _held_findings(source: Any) -> Tuple[MemoryFinding, ...]:
    if isinstance(source, DoctorBook):
        return source.findings
    if isinstance(source, DoctorRegistry):
        return source.list_findings()
    if isinstance(source, (list, tuple)):
        return tuple(_check_finding_ref(item) for item in source)
    raise ValueError(f"memory findings are needed, got {source!r}")


def derive_panel(source: Any) -> DoctorPanel:
    """Derive the doctor panel from one book.

    The rows are the book's findings carried
    whole, in panel order: by check - corrupt
    stores first, then orphaned vectors, then map
    drift - then title, then finding id, each
    showing its derived repair with its
    disposition read off its own extent. *source*
    is a book or a registry. A source holding no
    finding refuses - a panel of nothing is no
    panel.
    """
    findings = _held_findings(source)
    if not findings:
        raise ValueError("a panel needs at least one memory finding")
    rows = []
    for finding in findings:
        if finding.finding_id is None:
            raise ValueError(
                "a panel row must name its finding - a "
                "finding with no id refuses derivation")
        rows.append(_row_for_finding(finding))
    rows = tuple(sorted(rows, key=lambda r: r.sort_key))
    tallies = {
        check: sum(1 for r in rows if r.check == check)
        for check in CHECKS}
    check_counts = tuple(
        CheckCount(check=check, items=tallies[check])
        for check in CHECKS if tallies[check])
    distinct = len({(r.memory_kind, r.memory_ref) for r in rows})
    ready = sum(1 for r in rows if r.disposition == "repair-ready")
    referred = len(rows) - ready
    as_of = max(r.found_on for r in rows)
    return DoctorPanel(
        rows=rows, total_findings=len(rows),
        total_ready=ready, total_referred=referred,
        distinct_memories=distinct,
        check_counts=check_counts,
        account=_panel_account(
            len(rows), ready, referred, distinct, check_counts, as_of),
        as_of=as_of)


def validate_panel(panel: Any, source: Any = None
                   ) -> DoctorPanel:
    """Validate one panel into a DoctorPanel.

    Accepts a panel or a mapping naming ``rows``
    (or ``findings``), a ``total_findings`` (or
    ``total``), a ``total_ready`` (or ``ready``),
    a ``total_referred`` (or ``referred``), a
    ``distinct_memories`` (or ``memories``),
    ``check_counts`` (or ``checks``), an ``as_of``
    (or ``day``), an ``account`` (or
    ``statements``) and an optional ``panel_id``
    (or ``id``). With *source* given (a book), the
    panel is judged against the panel derived
    from that book.
    """
    if isinstance(panel, DoctorPanel):
        current = panel
    elif isinstance(panel, dict):
        unknown = set(panel) - _PANEL_KEYS
        if unknown:
            raise ValueError(
                "unknown panel keys: %s" % ", ".join(sorted(unknown)))
        rows = _pick_any(panel, ("rows", "findings"), "rows")
        if rows is None:
            raise ValueError("a panel is missing its rows")
        total = _pick_any(panel, ("total_findings", "total"), "totals")
        if total is None:
            raise ValueError("a panel is missing its total findings")
        ready = _pick_any(
            panel, ("total_ready", "ready"), "ready totals")
        if ready is None:
            raise ValueError("a panel is missing its total ready")
        referred = _pick_any(
            panel, ("total_referred", "referred"), "referred totals")
        if referred is None:
            raise ValueError("a panel is missing its total referred")
        distinct = _pick_any(
            panel, ("distinct_memories", "memories"),
            "distinct memories")
        if distinct is None:
            raise ValueError("a panel is missing its distinct memories")
        check_counts = _pick_any(
            panel, ("check_counts", "checks"), "check counts")
        if check_counts is None:
            raise ValueError("a panel is missing its check counts")
        as_of = _pick_any(panel, ("as_of", "day"), "as-of days")
        if as_of is None:
            raise ValueError("a panel is missing its as-of day")
        account = _pick_any(panel, ("account", "statements"), "accounts")
        if account is None:
            raise ValueError("a panel names no account of its own")
        kwargs: Dict[str, Any] = {
            "rows": rows, "total_findings": total,
            "total_ready": ready, "total_referred": referred,
            "distinct_memories": distinct,
            "check_counts": check_counts,
            "as_of": as_of, "account": account}
        panel_id = _pick_any(panel, ("panel_id", "id"), "panel ids")
        if panel_id is not None:
            kwargs["panel_id"] = panel_id
        current = DoctorPanel(**kwargs)
    else:
        raise ValueError(f"a panel must be a mapping, got {panel!r}")
    if source is not None:
        derived = derive_panel(source)
        if (current.rows != derived.rows
                or current.total_findings != derived.total_findings
                or current.total_ready != derived.total_ready
                or current.total_referred != derived.total_referred
                or current.distinct_memories != derived.distinct_memories
                or current.check_counts != derived.check_counts
                or current.as_of != derived.as_of
                or current.account != derived.account):
            raise ValueError(
                "a stored panel disagrees with the panel "
                "derived from its book")
    return current


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> DoctorPanel:
    """Build one validated panel, from a mapping or field words."""
    if isinstance(panel, DoctorPanel) and not kwargs:
        return validate_panel(panel, source)
    if isinstance(panel, dict) or panel is None:
        merged: Dict[str, Any] = {}
        if isinstance(panel, dict):
            merged.update(panel)
        merged.update(kwargs)
        return validate_panel(merged, source)
    return validate_panel(panel, source)


# ---------------------------------------------------------------------
# The doctor verdict: the whole book judged, as data.
# ---------------------------------------------------------------------


def _verdict_word(total_referred: int) -> str:
    """The verdict word a book's own tallies derive.

    ``sound`` while nothing the checks found
    stands beyond safe repair; ``ailing`` while
    one or two findings are referred to the user;
    and ``critical`` when three or more stand
    referred - the stores need the user's hand,
    not the doctor's.
    """
    if total_referred >= 3:
        return "critical"
    if total_referred >= 1:
        return "ailing"
    return "sound"


@dataclass(frozen=True)
class DoctorVerdict:
    """One doctor verdict: a whole book judged, as data.

    ``total_findings`` counts the book's findings;
    ``total_ready`` counts the findings standing
    repair-ready and ``total_referred`` the
    findings standing referred - the two stand
    summing to the total; ``distinct_memories``
    counts the stored memories checked and
    ``distinct_kinds`` the holdings they stand in;
    ``earliest_on`` and ``latest_on`` bound the
    days the checks ran; ``verdict`` is the word
    those tallies derive - ``sound`` while nothing
    stands referred, ``ailing`` while one or two
    stand referred, and ``critical`` when three
    or more stand referred.
    """

    total_findings: int
    total_ready: int
    total_referred: int
    distinct_memories: int
    distinct_kinds: int
    earliest_on: str
    latest_on: str
    verdict: str

    def __post_init__(self) -> None:
        for field, what in (
                ("total_findings", "total findings"),
                ("total_ready", "total ready"),
                ("total_referred", "total referred"),
                ("distinct_memories", "distinct memories"),
                ("distinct_kinds", "distinct kinds")):
            object.__setattr__(
                self, field, _check_count(getattr(self, field), what))
        if self.total_ready + self.total_referred != self.total_findings:
            raise ValueError(
                "a verdict's dispositions must sum to "
                "its own findings' count - every finding "
                "stands repair-ready or referred")
        if self.distinct_memories > self.total_findings:
            raise ValueError(
                "a verdict's distinct memories must not "
                "outnumber its findings")
        if self.distinct_kinds > self.distinct_memories:
            raise ValueError(
                "a verdict's distinct kinds must not "
                "outnumber its distinct memories")
        earliest = _check_day(self.earliest_on, "a verdict's earliest day")
        latest = _check_day(self.latest_on, "a verdict's latest day")
        if latest < earliest:
            raise ValueError(
                "a verdict's latest day must not stand "
                "before its earliest day")
        object.__setattr__(self, "earliest_on", earliest)
        object.__setattr__(self, "latest_on", latest)
        word = _clean_text(self.verdict, "a verdict")
        if word not in VERDICT_WORDS:
            raise ValueError(
                "a verdict must be one of %s, got %r"
                % ("/".join(VERDICT_WORDS), word))
        derived = _verdict_word(self.total_referred)
        if word != derived:
            raise ValueError(
                f"a verdict's word must be the word its "
                f"own tallies derive ({derived!r}), got {word!r}")
        object.__setattr__(self, "verdict", word)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "memory_doctor_verdict",
            "slice": MEMORY_DOCTOR_SLICE,
            "total_findings": self.total_findings,
            "total_ready": self.total_ready,
            "total_referred": self.total_referred,
            "distinct_memories": self.distinct_memories,
            "distinct_kinds": self.distinct_kinds,
            "earliest_on": self.earliest_on,
            "latest_on": self.latest_on,
            "verdict": self.verdict,
        }


def derive_verdict(source: Any) -> DoctorVerdict:
    """Derive the doctor verdict for one whole book."""
    findings = _held_findings(source)
    if not findings:
        raise ValueError(
            "a verdict needs at least one memory finding")
    distinct = len({(f.memory_kind, f.memory_ref) for f in findings})
    referred = sum(
        1 for f in findings if disposition_of(f) == "referred")
    return DoctorVerdict(
        total_findings=len(findings),
        total_ready=len(findings) - referred,
        total_referred=referred,
        distinct_memories=distinct,
        distinct_kinds=len({f.memory_kind for f in findings}),
        earliest_on=min(f.found_on for f in findings),
        latest_on=max(f.found_on for f in findings),
        verdict=_verdict_word(referred))


def _check_verdict_ref(value: Any) -> DoctorVerdict:
    if isinstance(value, DoctorVerdict):
        return value
    if isinstance(value, dict):
        return validate_verdict(value)
    raise ValueError(f"a doctor verdict is needed, got {value!r}")


def validate_verdict(verdict: Any, source: Any = None) -> DoctorVerdict:
    """Validate one verdict into a DoctorVerdict.

    Accepts a verdict or a mapping naming its
    tallies (short spellings read onto the
    totals), its ``earliest_on`` (or ``earliest``)
    and ``latest_on`` (or ``latest``) days and its
    ``verdict`` word. With *source* given (a
    book), the verdict is judged against the
    verdict derived from that book.
    """
    if isinstance(verdict, DoctorVerdict):
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

        current = DoctorVerdict(
            total_findings=_needed(
                ("total_findings", "total"), "total findings"),
            total_ready=_needed(
                ("total_ready", "ready"), "total ready"),
            total_referred=_needed(
                ("total_referred", "referred"), "total referred"),
            distinct_memories=_needed(
                ("distinct_memories", "memories"), "distinct memories"),
            distinct_kinds=_needed(
                ("distinct_kinds", "kinds"), "distinct kinds"),
            earliest_on=_needed(
                ("earliest_on", "earliest"), "earliest day"),
            latest_on=_needed(
                ("latest_on", "latest"), "latest day"),
            verdict=_needed(("verdict",), "verdict"))
    else:
        raise ValueError(f"a verdict must be a mapping, got {verdict!r}")
    if source is not None:
        derived = derive_verdict(source)
        if current != derived:
            raise ValueError(
                "a stored verdict disagrees with the "
                "verdict derived from its book")
    return current


def build_verdict(verdict: Any = None, source: Any = None,
                  **kwargs: Any) -> DoctorVerdict:
    """Build one validated verdict, from a mapping or field words."""
    if isinstance(verdict, DoctorVerdict) and not kwargs:
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict) or verdict is None:
        merged: Dict[str, Any] = {}
        if isinstance(verdict, dict):
            merged.update(verdict)
        merged.update(kwargs)
        return validate_verdict(merged, source)
    return validate_verdict(verdict, source)


# ---------------------------------------------------------------------
# The repairs: derived from the whole book, never chosen.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class DoctorRepair:
    """One derived repair: what may safely be done about one finding.

    ``repair_id`` is read off the finding it
    answers (``repair-<finding-id>``); ``check``,
    ``memory_kind`` and ``memory_ref`` are the
    finding's own head; ``action`` is the one
    safe repair the finding's check and extent
    derive - or :data:`REFERRED_ACTION` when the
    finding stands referred - and ``disposition``
    is the finding's own. A repair is never built
    loose: :func:`validate_repair` judged against
    its finding refuses a repair whose fields
    disagree with the repair that finding derives.
    """

    repair_id: str
    finding_id: str
    check: str
    memory_kind: str
    memory_ref: str
    action: str
    disposition: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "repair_id", normalize_member_id(self.repair_id))
        object.__setattr__(
            self, "finding_id", normalize_member_id(self.finding_id))
        if self.repair_id != f"repair-{self.finding_id}":
            raise ValueError(
                "a repair's id must be the id its own "
                "finding derives (repair-<finding-id>)")
        object.__setattr__(
            self, "check", normalize_check(self.check))
        object.__setattr__(
            self, "memory_kind", normalize_memory_kind(self.memory_kind))
        object.__setattr__(
            self, "memory_ref",
            _check_word(self.memory_ref, "a repair's memory ref"))
        word = _clean_text(self.disposition, "a repair's disposition")
        if word not in DISPOSITIONS:
            raise ValueError(
                "a disposition must be one of %s, got %r"
                % ("/".join(DISPOSITIONS), word))
        object.__setattr__(self, "disposition", word)
        action = _clean_text(self.action, "a repair's action")
        derived = (
            REFERRED_ACTION if word == "referred"
            else _REPAIR_BY_CHECK[self.check])
        if action != derived:
            raise ValueError(
                f"a repair's action must be the repair "
                f"its own check and disposition derive "
                f"({derived!r}), got {action!r}")
        object.__setattr__(self, "action", action)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "memory_doctor_repair",
            "slice": MEMORY_DOCTOR_SLICE,
            "repair_id": self.repair_id,
            "finding_id": self.finding_id,
            "check": self.check,
            "memory_kind": self.memory_kind,
            "memory_ref": self.memory_ref,
            "action": self.action,
            "disposition": self.disposition,
        }


def _repair_for_finding(finding: MemoryFinding) -> DoctorRepair:
    if finding.finding_id is None:
        raise ValueError(
            "a repair must name its finding - a finding "
            "with no id derives no repair")
    return DoctorRepair(
        repair_id=f"repair-{finding.finding_id}",
        finding_id=finding.finding_id, check=finding.check,
        memory_kind=finding.memory_kind,
        memory_ref=finding.memory_ref,
        action=repair_action_of(finding),
        disposition=disposition_of(finding))


def derive_repairs(source: Any) -> Tuple[DoctorRepair, ...]:
    """Derive the repairs of one whole book, in held order.

    Every finding of the book derives exactly one
    repair record: a repair-ready finding its one
    safe repair, a referred finding the record
    that names no repair - so what the doctor
    will not repair stands on the same page as
    what it will.
    """
    return tuple(
        _repair_for_finding(finding)
        for finding in _held_findings(source))


def _check_repair_ref(value: Any) -> DoctorRepair:
    if isinstance(value, DoctorRepair):
        return value
    if isinstance(value, dict):
        return validate_repair(value)
    raise ValueError(f"a doctor repair is needed, got {value!r}")


def validate_repair(repair: Any, finding: Any = None) -> DoctorRepair:
    """Validate one repair into a DoctorRepair.

    Accepts a repair or a mapping naming its
    fields. With *finding* given, the repair is
    judged against the repair that finding
    derives.
    """
    if isinstance(repair, DoctorRepair):
        current = repair
    elif isinstance(repair, dict):
        unknown = set(repair) - _REPAIR_KEYS
        if unknown:
            raise ValueError(
                "unknown repair keys: %s" % ", ".join(sorted(unknown)))

        def _needed(spellings: Tuple[str, ...], what: str) -> Any:
            value = _pick_any(repair, spellings, what)
            if value is None:
                raise ValueError(f"a repair is missing its {what}")
            return value

        current = DoctorRepair(
            repair_id=_needed(("repair_id", "id"), "repair id"),
            finding_id=_needed(("finding_id", "finding"), "finding id"),
            check=_needed(("check",), "check"),
            memory_kind=_needed(("memory_kind",), "memory kind"),
            memory_ref=_needed(("memory_ref",), "memory ref"),
            action=_needed(("action",), "action"),
            disposition=_needed(("disposition",), "disposition"))
    else:
        raise ValueError(f"a repair must be a mapping, got {repair!r}")
    if finding is not None:
        derived = _repair_for_finding(_check_finding_ref(finding))
        if current != derived:
            raise ValueError(
                "a stored repair disagrees with the "
                "repair its finding derives")
    return current


def build_repair(repair: Any = None, finding: Any = None,
                 **kwargs: Any) -> DoctorRepair:
    """Build one validated repair, from a mapping or field words."""
    if isinstance(repair, DoctorRepair) and not kwargs:
        return validate_repair(repair, finding)
    if isinstance(repair, dict) or repair is None:
        merged: Dict[str, Any] = {}
        if isinstance(repair, dict):
            merged.update(repair)
        merged.update(kwargs)
        return validate_repair(merged, finding)
    return validate_repair(repair, finding)


# ---------------------------------------------------------------------
# The book: one book of findings, and its loaders.
# ---------------------------------------------------------------------


def _judge_findings(findings: Tuple[MemoryFinding, ...],
                    held: Tuple[MemoryFinding, ...] = ()) -> None:
    """Judge findings against held findings: the book's laws.

    One finding per check per stored memory - one
    check and one memory kind and memory ref
    stands once - so a check's word never forks
    inside a book. *held* names findings already
    standing (a registry's), judged alongside.
    """
    owners: Dict[Tuple[str, str, str], str] = {}
    for finding in tuple(held) + tuple(findings):
        key = (finding.check, finding.memory_kind, finding.memory_ref)
        if key in owners:
            raise ValueError(
                f"a memory checked twice by one check: "
                f"{key[0]} over {key[1]} {key[2]!r} "
                f"already stands found by {owners[key]!r} "
                f"- one finding per check per memory")
        owners[key] = finding.finding_id or finding.title


@dataclass(frozen=True)
class DoctorBook:
    """One doctor book: its findings, in held order.

    ``findings`` are the memory findings, in held
    order, each with its provenance whole, one per
    check per stored memory. ``panels`` are the
    book's derivations - doctor panels of the
    whole book, each judged against the book by
    :func:`validate_book`; ``canon_note`` is the
    book's own note. The total is the findings'
    own count, judged at construction.
    """

    title: str = ""
    findings: Tuple[MemoryFinding, ...] = ()
    panels: Tuple[DoctorPanel, ...] = ()
    canon_note: str = ""
    total_findings: Optional[int] = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_title(self.title, "a book's title"))
        if isinstance(self.findings, (str, bytes)) \
                or not isinstance(self.findings, (list, tuple)):
            raise ValueError(
                f"a book's findings must be a list of "
                f"findings, got {self.findings!r}")
        findings = tuple(_check_finding_ref(item) for item in self.findings)
        if not findings:
            raise ValueError("a doctor book holds at least one finding")
        seen_ids = set()
        for finding in findings:
            if finding.finding_id is not None:
                if finding.finding_id in seen_ids:
                    raise ValueError(
                        f"a finding named "
                        f"{finding.finding_id!r} already exists")
                seen_ids.add(finding.finding_id)
        _judge_findings(findings)
        object.__setattr__(self, "findings", findings)
        if isinstance(self.panels, (str, bytes)) \
                or not isinstance(self.panels, (list, tuple)):
            raise ValueError(
                f"a book's panels must be a list of panels, "
                f"got {self.panels!r}")
        panels = tuple(
            p if isinstance(p, DoctorPanel)
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
        given = self.total_findings
        if given is None:
            object.__setattr__(self, "total_findings", len(findings))
        else:
            checked = _check_count(given, "a book's total findings")
            if checked != len(findings):
                raise ValueError(
                    "a book's total findings must be its "
                    "own findings' count")
            object.__setattr__(self, "total_findings", checked)

    def finding_for(self, finding_id: Any) -> MemoryFinding:
        """The finding one id names in this book."""
        wanted = normalize_member_id(finding_id)
        for finding in self.findings:
            if finding.finding_id == wanted:
                return finding
        raise KeyError(f"no finding in the book: {wanted!r}")

    def finding_for_check(self, check: Any, memory_kind: Any,
                          memory_ref: Any) -> MemoryFinding:
        """The finding one check raised over one stored memory."""
        wanted_check = normalize_check(check)
        kind = normalize_memory_kind(memory_kind)
        wanted = _check_word(memory_ref, "a memory ref")
        for finding in self.findings:
            if finding.check == wanted_check \
                    and finding.memory_kind == kind \
                    and finding.memory_ref == wanted:
                return finding
        raise KeyError(
            f"no finding in the book by {wanted_check} "
            f"over {kind} {wanted!r}")

    def panel_for(self, panel_id: Any) -> DoctorPanel:
        """The stored panel one id names in this book."""
        wanted = normalize_member_id(panel_id)
        for panel in self.panels:
            if panel.panel_id == wanted:
                return panel
        raise KeyError(f"no panel in the book: {wanted!r}")

    def finding_ids(self) -> Tuple[str, ...]:
        """Every held finding id, in held order."""
        return tuple(
            item.finding_id for item in self.findings if item.finding_id)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "memory_doctor_book",
            "slice": MEMORY_DOCTOR_SLICE,
            "title": self.title,
            "finding_ids": list(self.finding_ids()),
            "finding_count": len(self.findings),
            "panel_count": len(self.panels),
        }


# The pinned example panel's account is filled in
# below, once the panel machinery stands.
_EXAMPLE_PANEL_ACCOUNT: Tuple[str, ...] = (
    "The memory doctor panel holds 5 findings as of "
    "2026-11-09: 4 safely repairable and 1 "
    "referred beyond the doctor over 5 stored "
    "memories: corrupt-store 2, map-drift 2, "
    "orphaned-vector 1.",
    "Rows stand by check - corrupt stores first, "
    "then orphaned vectors, then map drift - "
    "then title, then finding id, so two panels "
    "of one book diff cleanly, line by line.",
    "Every row shows its repair: a contained "
    "finding names its one derived safe repair, "
    "and a store-wide finding names none - it is "
    "referred to the user, and the doctor will "
    "not repair it.",
    "The panel is read off the book at call "
    "time - it is derived, never stored loose - "
    "and a repair applied here marks a held "
    "finding repaired in this book only: no live "
    "store is rewritten by standing on this panel.",
)


def validate_book(data: Any, *, require_example: bool = False
                  ) -> DoctorBook:
    """Validate one doctor mapping into a book.

    The mapping names a ``schema``, a ``guide``
    mapping (its ``title``), a ``findings`` list
    (or ``records``) and an optional ``panels``
    list. Every finding stands on its own
    validation, then the whole is judged: finding
    ids unique, one finding per check per stored
    memory, and every stored panel judged against
    the book. With ``require_example`` the shipped
    example is held to its pinned shape.
    """
    if isinstance(data, DoctorBook):
        return data
    if not isinstance(data, dict):
        raise ValidationError(
            f"a doctor book must be a mapping, got {data!r}")
    unknown = set(data) - _DOCTOR_BOOK_KEYS
    if unknown:
        raise ValidationError(
            "unknown doctor-book keys: %s"
            % ", ".join(sorted(unknown)))
    if data.get("schema") != MEMORY_DOCTOR_SCHEMA:
        raise ValidationError(
            f"a doctor book must carry schema "
            f"{MEMORY_DOCTOR_SCHEMA!r}, "
            f"got {data.get('schema')!r}")
    findings = _pick_any(data, ("findings", "records"), "findings")
    if findings is None:
        raise ValidationError("a doctor book is missing its findings")
    if not isinstance(findings, (list, tuple)):
        raise ValidationError("a doctor book's findings must be a list")
    if data.get("panels") is not None \
            and not isinstance(data["panels"], (list, tuple)):
        raise ValidationError("a doctor book's panels must be a list")
    head = data.get("guide") or {}
    if not isinstance(head, dict):
        raise ValidationError("a doctor book's guide must be a mapping")
    unknown_head = set(head) - _BOOK_KEYS
    if unknown_head:
        raise ValidationError(
            "unknown guide keys: %s" % ", ".join(sorted(unknown_head)))
    try:
        title = _pick_any(head, ("title", "name"), "titles")
        if title is None:
            raise ValidationError("a doctor book is missing its title")
        note = data.get("canon_note") or ""
        if not isinstance(note, str):
            raise ValidationError("a doctor book's note must be text")
        book = DoctorBook(
            title=title, findings=tuple(findings),
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
                "the shipped example doctor book's "
                "title is not the pinned title")
        if book.finding_ids() != _EXAMPLE_FINDING_IDS:
            raise ValidationError(
                "the shipped example's findings are not "
                "the pinned findings")
        panel = book.panel_for(_EXAMPLE_PANEL_ID)
        if panel.as_of != _EXAMPLE_AS_OF:
            raise ValidationError(
                "the shipped example panel does not stand "
                "as of its pinned day")
        if tuple(r.finding_id for r in panel.rows) != _EXAMPLE_PANEL_ROW_IDS:
            raise ValidationError(
                "the shipped example panel does not name "
                "its pinned rows in panel order")
        if _EXAMPLE_PANEL_ACCOUNT and panel.account != _EXAMPLE_PANEL_ACCOUNT:
            raise ValidationError(
                "the shipped example panel does not carry "
                "its pinned account word-for-word")
        first = book.findings[0]
        if first.finding_id != _EXAMPLE_FIRST_FINDING_ID \
                or first.title != _EXAMPLE_FIRST_FINDING_TITLE:
            raise ValidationError(
                "the shipped example's first finding is "
                "not its pinned finding of its pinned title")
    return book


def build_book(book: Any = None, **kwargs: Any) -> DoctorBook:
    """Build one validated book, from a mapping or field words."""
    if isinstance(book, DoctorBook) and not kwargs:
        return book
    if isinstance(book, dict):
        if "schema" in book:
            return validate_book(book)
        merged: Dict[str, Any] = dict(book)
        merged.update(kwargs)
        return DoctorBook(**merged)
    if book is None:
        return DoctorBook(**kwargs)
    raise ValueError(f"a doctor book is needed, got {book!r}")


def _book_from(data: Any, *, require_example: bool) -> DoctorBook:
    try:
        return validate_book(data, require_example=require_example)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def load_memory_doctor(
        data: Optional[Dict[str, Any]] = None) -> DoctorBook:
    """Load and validate the shipped example book (or *data*)."""
    raw = data if data is not None else load_resource(
        MEMORY_DOCTOR_RESOURCE)
    return _book_from(raw, require_example=True)


def load_memory_doctor_file(path: Any) -> DoctorBook:
    """Load and validate a doctor book from a file at *path*."""
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _book_from(raw, require_example=False)


# ---------------------------------------------------------------------
# The registry model: one book held finding by finding.
# ---------------------------------------------------------------------


class DoctorRegistry:
    """One book's findings, held one by one.

    The registry holds findings, never panels or
    verdicts: the panel, the verdict and the
    repairs are derivations, read off the whole
    held book at call time. A whole book is judged
    whole - as a book judges it, and against
    everything already held - before its findings
    are held in book order, so a raising never
    lands partially. A finding held here stands
    apart: a second finding by the same check over
    a held memory refuses - one finding per check
    per memory. The registry also holds which
    derived repairs have been applied to its own
    book: applying a repair marks its finding
    repaired here, and here only - no live store
    is touched, and a referred finding's repair
    refuses here as everywhere.
    """

    def __init__(self, book: Any = None) -> None:
        self._title: Optional[str] = None
        self._findings: Dict[str, MemoryFinding] = {}
        self._finding_order: list = []
        self._next_finding = 1
        self._applied: set = set()
        if book is not None:
            self.register_book(book)

    def _fresh_finding_id(self, held_ids: Any) -> str:
        while f"finding-{self._next_finding}" in held_ids:
            self._next_finding += 1
        fresh = f"finding-{self._next_finding}"
        self._next_finding += 1
        return fresh

    def _check_standing_free(self, finding: MemoryFinding) -> None:
        _judge_findings((finding,), held=self.list_findings())

    def register_finding(self, finding: Any) -> MemoryFinding:
        """Register one finding into the held book."""
        validated = _check_finding_ref(finding)
        if validated.finding_id is not None \
                and validated.finding_id in self._findings:
            raise ValueError(
                f"a finding named "
                f"{validated.finding_id!r} already exists")
        self._check_standing_free(validated)
        return self._hold_finding(validated)

    def _hold_finding(self, validated: MemoryFinding
                      ) -> MemoryFinding:
        if validated.finding_id is None:
            from dataclasses import replace
            validated = replace(
                validated,
                finding_id=self._fresh_finding_id(set(self._findings)))
        self._findings[validated.finding_id] = validated
        self._finding_order.append(validated.finding_id)
        return validated

    def register_book(self, book: Any) -> DoctorBook:
        """Register every finding of one book, in order.

        The book is judged whole, and against the
        held book, before any of its findings is
        held: a refusal holds nothing new.
        """
        validated = build_book(book)
        if self._title is not None and validated.title != self._title:
            raise ValueError(
                "this registry already holds a doctor "
                "book under a different title")
        for finding in validated.findings:
            if finding.finding_id in self._findings:
                raise ValueError(
                    f"a finding named "
                    f"{finding.finding_id!r} already exists")
        _judge_findings(validated.findings, held=self.list_findings())
        self._title = validated.title
        for finding in validated.findings:
            self._hold_finding(finding)
        return self.book()

    def get_finding(self, finding_id: Any) -> MemoryFinding:
        """The finding one id names among the held findings."""
        wanted = normalize_member_id(finding_id)
        if wanted not in self._findings:
            raise KeyError(f"unknown finding: {wanted!r}")
        return self._findings[wanted]

    def finding_for_check(self, check: Any, memory_kind: Any,
                          memory_ref: Any) -> MemoryFinding:
        """The held finding one check raised over one stored memory."""
        wanted_check = normalize_check(check)
        kind = normalize_memory_kind(memory_kind)
        wanted = _check_word(memory_ref, "a memory ref")
        for finding_id in self._finding_order:
            finding = self._findings[finding_id]
            if finding.check == wanted_check \
                    and finding.memory_kind == kind \
                    and finding.memory_ref == wanted:
                return finding
        raise KeyError(
            f"no finding held by {wanted_check} over "
            f"{kind} {wanted!r}")

    def latest_finding(self) -> MemoryFinding:
        """The most recently held finding."""
        if not self._finding_order:
            raise ValueError("no finding is held yet")
        return self._findings[self._finding_order[-1]]

    def list_findings(self) -> Tuple[MemoryFinding, ...]:
        """Every held finding, in the order they were held."""
        return tuple(self._findings[item] for item in self._finding_order)

    def book(self) -> DoctorBook:
        """The held findings as one validated book."""
        if self._title is None:
            raise ValueError("no doctor book is held yet")
        return DoctorBook(
            title=self._title, findings=self.list_findings())

    def panel(self) -> DoctorPanel:
        """Derive the doctor panel of the whole held book."""
        return derive_panel(self)

    def verdict(self) -> DoctorVerdict:
        """Derive the doctor verdict of the whole held book."""
        return derive_verdict(self)

    def repairs(self) -> Tuple[DoctorRepair, ...]:
        """Derive the repairs of the whole held book."""
        return derive_repairs(self)

    def is_repaired(self, finding_id: Any) -> bool:
        """Whether one held finding's repair stands applied here."""
        wanted = normalize_member_id(finding_id)
        return wanted in self._applied

    def applied_repairs(self) -> Tuple[DoctorRepair, ...]:
        """Every repair applied to this book, in held order."""
        return tuple(
            repair for repair in derive_repairs(self)
            if repair.finding_id in self._applied)

    def apply_repairs(self) -> Tuple[DoctorRepair, ...]:
        """Apply the held book's derived safe repairs, here only.

        Only repair-ready findings are applied, and
        only repairs not already applied: a referred
        finding derives no repair and is never
        applied, and a repair applied once is not
        applied twice. Applying marks the finding
        repaired in this registry's own book - no
        live store is rewritten, no memory is
        deleted, nothing is written to disk.
        Returns the repairs newly applied, in held
        order.
        """
        newly = []
        for repair in derive_repairs(self):
            if repair.disposition != "repair-ready":
                continue
            if repair.finding_id in self._applied:
                continue
            self._applied.add(repair.finding_id)
            newly.append(repair)
        return tuple(newly)


# ---------------------------------------------------------------------
# The visible surface: how the book stands, read off any book.
# ---------------------------------------------------------------------


def finding_refs(source: Any) -> Tuple[Tuple[str, str, str], ...]:
    """Every (check, memory kind, memory ref) one source's findings name."""
    return tuple(
        (finding.check, finding.memory_kind, finding.memory_ref)
        for finding in _held_findings(source))


def finding_for(source: Any, check: Any, memory_kind: Any,
                memory_ref: Any) -> MemoryFinding:
    """The finding one source holds by one check over one memory."""
    wanted_check = normalize_check(check)
    kind = normalize_memory_kind(memory_kind)
    wanted = _check_word(memory_ref, "a memory ref")
    for finding in _held_findings(source):
        if finding.check == wanted_check \
                and finding.memory_kind == kind \
                and finding.memory_ref == wanted:
            return finding
    raise KeyError(
        f"no finding by {wanted_check} over {kind} {wanted!r}")


def total_findings(source: Any) -> int:
    """How many findings one source holds."""
    return len(_held_findings(source))


def finding_record(finding: Any) -> Dict[str, Any]:
    """The session-news record of one memory finding."""
    current = finding if isinstance(finding, MemoryFinding) \
        else build_finding(finding)
    record = current.to_record()
    record["news"] = True
    if current.extent == "store-wide":
        record["headline"] = (
            f"Memory doctor over {current.memory_kind} "
            f"{current.memory_ref}: {current.check} "
            f"reaches the whole {current.store} store - "
            f"referred to the user, no repair derived.")
    else:
        record["headline"] = (
            f"Memory doctor over {current.memory_kind} "
            f"{current.memory_ref}: {current.check} in "
            f"the {current.store} store - safe repair "
            f"derived: {repair_action_of(current)}.")
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
        f"Memory doctor panel as of {current.as_of}: "
        f"{current.total_findings} findings - "
        f"{current.total_ready} safely repairable, "
        f"{current.total_referred} referred over "
        f"{current.distinct_memories} stored "
        f"memories.")
    return record


def verdict_record(verdict: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of one derived verdict."""
    current = validate_verdict(verdict, source)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Memory doctor verdict: {current.verdict} - "
        f"{current.total_ready} of "
        f"{current.total_findings} findings safely "
        f"repairable, {current.total_referred} "
        f"referred, from {current.earliest_on} to "
        f"{current.latest_on}.")
    return record


def repair_record(repair: Any, finding: Any = None) -> Dict[str, Any]:
    """The session-news record of one derived repair."""
    current = validate_repair(repair, finding)
    record = current.to_record()
    record["news"] = True
    if current.disposition == "referred":
        record["headline"] = (
            f"Memory repair over {current.memory_kind} "
            f"{current.memory_ref}: none - the finding "
            f"stands referred and the doctor will not "
            f"repair it.")
    else:
        record["headline"] = (
            f"Memory repair over {current.memory_kind} "
            f"{current.memory_ref}: {current.action} "
            f"applied to the held book.")
    return record


def book_record(book: Any) -> Dict[str, Any]:
    """The session-news record of one doctor book."""
    current = book if isinstance(book, DoctorBook) \
        else build_book(book)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Memory doctor book {current.title}: "
        f"{record['finding_count']} findings named.")
    return record


def plain_words(finding: Any) -> str:
    """One finding, in one plain sentence."""
    current = finding if isinstance(finding, MemoryFinding) \
        else build_finding(finding)
    if current.extent == "store-wide":
        return (
            f"{current.title} - the {current.check} "
            f"check over the {current.memory_kind} "
            f"memory {current.memory_ref} reaches the "
            f"whole {current.store} store: referred to "
            f"the user, and the doctor derives no repair.")
    return (
        f"{current.title} - the {current.check} check "
        f"over the {current.memory_kind} memory "
        f"{current.memory_ref} in the {current.store} "
        f"store: safely repairable by "
        f"{repair_action_of(current)} on the held book.")


def panel_plain_words(source: Any) -> str:
    """The panel in plain words, in full.

    Accepts a DoctorPanel or a book (whose panel
    is derived). The panel is told whole - its
    rows in panel order and its account.
    """
    if isinstance(source, DoctorPanel):
        panel = validate_panel(source)
        title = None
    elif isinstance(source, (DoctorBook, DoctorRegistry)):
        panel = derive_panel(source)
        title = source.title if isinstance(
            source, DoctorBook) else None
    else:
        raise ValueError(
            f"a doctor source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    lines.append("Findings, in panel order:")
    for row in panel.rows:
        lines.append(
            f"{row.finding_id}: {row.check}/"
            f"{row.memory_kind}/{row.memory_ref} - "
            f"store: {row.store} store, repair: "
            f"{row.action} (disposition: "
            f"{row.disposition}, found {row.found_on})")
    lines.extend(panel.account)
    return "\n".join(lines)


def verdict_plain_words(source: Any) -> str:
    """The doctor verdict in plain words, in full."""
    if isinstance(source, DoctorVerdict):
        verdict = validate_verdict(source)
    elif isinstance(source, (DoctorBook, DoctorRegistry)):
        verdict = derive_verdict(source)
    else:
        raise ValueError(
            f"a doctor source is needed, got {source!r}")
    return (
        f"Memory doctor verdict: {verdict.verdict} - "
        f"{verdict.total_ready} findings safely "
        f"repairable and {verdict.total_referred} "
        f"referred to the user over "
        f"{verdict.distinct_memories} stored memories "
        f"in {verdict.distinct_kinds} holdings, "
        f"checked from {verdict.earliest_on} to "
        f"{verdict.latest_on}, of "
        f"{verdict.total_findings} findings - the "
        f"doctor repairs only what its findings "
        f"derive, and refers the rest plainly.")


def repairs_plain_words(source: Any) -> str:
    """The derived repairs in plain words, in full.

    Every repair of the book is told - what will
    be repaired on the held book, and what will
    not be repaired at all and why.
    """
    repairs = derive_repairs(source)
    lines = ["Repairs derived from the whole book:"]
    for repair in repairs:
        if repair.disposition == "referred":
            lines.append(
                f"{repair.repair_id}: over "
                f"{repair.memory_kind}/{repair.memory_ref} "
                f"- no repair: the finding stands "
                f"referred and the doctor will not "
                f"repair store-wide trouble.")
        else:
            lines.append(
                f"{repair.repair_id}: over "
                f"{repair.memory_kind}/{repair.memory_ref} "
                f"- {repair.action}, applied to the "
                f"held book only.")
    return "\n".join(lines)


def _source_book(source: Any) -> DoctorBook:
    if source is None:
        return load_memory_doctor()
    if isinstance(source, DoctorRegistry):
        return source.book()
    if isinstance(source, DoctorBook):
        return source
    if isinstance(source, MemoryFinding):
        return DoctorBook(
            title="One memory finding", findings=(source,))
    raise ValueError(
        f"a doctor book is needed, got {source!r}")


def format_finding(finding: Any) -> str:
    """One finding as a screen block, its repair shown."""
    current = finding if isinstance(finding, MemoryFinding) \
        else build_finding(finding)
    lines = [
        f"{current.finding_id or '-'}: {current.title} - "
        f"{current.check} over {current.memory_kind} "
        f"{current.memory_ref} (read from {current.source})",
        f"Store: the {current.store} store "
        f"(found {current.found_on} by "
        f"{current.recorded_by} in "
        f"{current.origin_session})",
        f"What the check saw: {current.detail}",
    ]
    if current.extent == "store-wide":
        lines.append(
            "Extent: the whole store - referred to "
            "the user; the doctor derives no repair.")
    else:
        lines.append(
            f"Extent: one contained piece - safe "
            f"repair derived: {repair_action_of(current)}.")
    lines.append(f"The repair stands: {repair_line(current)}")
    return "\n".join(lines)


def format_findings(source: Any = None, check: Any = None,
                    store: Any = None) -> str:
    """Findings of one book, in held order, optionally filtered.

    With *check* named, only the findings that
    check raised show; with *store* named, only
    the findings over memories living in that
    store show.
    """
    book = _source_book(source)
    wanted_check = normalize_check(check) if check is not None else None
    wanted_store = normalize_store(store) if store is not None else None
    lines = [
        f"{finding.finding_id or '-'}: {finding.title} - "
        f"{finding.check} over {finding.memory_kind} "
        f"{finding.memory_ref}: store: {finding.store} "
        f"store, repair: {repair_action_of(finding)} "
        f"(disposition: {disposition_of(finding)}, "
        f"found {finding.found_on})"
        for finding in book.findings
        if (wanted_check is None or finding.check == wanted_check)
        and (wanted_store is None or finding.store == wanted_store)]
    if not lines:
        lines.append("No findings stand in the book on that reading.")
    return "\n".join(lines)


def format_panel(source: Any = None) -> str:
    """The panel as a screen block: every row and the account.

    Accepts a DoctorPanel or a book; a book shows
    the panel derived from it.
    """
    if isinstance(source, DoctorPanel):
        panel = validate_panel(source)
        lines: list = []
    else:
        book = _source_book(source)
        panel = derive_panel(book)
        lines = [f"Panel in {book.title}:"]
    lines.append("Findings, in panel order:")
    for row in panel.rows:
        lines.append(
            f"{row.finding_id}: {row.check}/"
            f"{row.memory_kind}/{row.memory_ref} - "
            f"store: {row.store} store, repair: "
            f"{row.action} (disposition: "
            f"{row.disposition}, found {row.found_on})")
    lines.extend(panel.account)
    return "\n".join(lines)


def format_verdict(source: Any = None) -> str:
    """The doctor verdict as a screen block."""
    if isinstance(source, DoctorVerdict):
        verdict = validate_verdict(source)
        lines: list = []
    else:
        book = _source_book(source)
        verdict = derive_verdict(book)
        lines = [f"Verdict in {book.title}:"]
    lines.append(
        f"{verdict.verdict}: {verdict.total_ready} "
        f"findings safely repairable and "
        f"{verdict.total_referred} referred to the "
        f"user over {verdict.distinct_memories} "
        f"stored memories in {verdict.distinct_kinds} "
        f"holdings, checked from {verdict.earliest_on} "
        f"to {verdict.latest_on}, of "
        f"{verdict.total_findings} findings. The "
        f"doctor repairs only the repairs its "
        f"findings derive, on the held book alone, "
        f"and refers store-wide trouble plainly.")
    return "\n".join(lines)


def format_repairs(source: Any = None) -> str:
    """The derived repairs as a screen block.

    What the doctor will repair on the held book
    stands beside what it will not repair, in
    held order.
    """
    book = _source_book(source)
    lines = [f"Repairs in {book.title}:"]
    for repair in derive_repairs(book):
        if repair.disposition == "referred":
            lines.append(
                f"{repair.repair_id}: over "
                f"{repair.memory_kind}/{repair.memory_ref} "
                f"- no repair will be applied: the "
                f"finding stands referred, and the "
                f"doctor will not repair store-wide "
                f"trouble.")
        else:
            lines.append(
                f"{repair.repair_id}: over "
                f"{repair.memory_kind}/{repair.memory_ref} "
                f"- {repair.action}, applied to the "
                f"held book only; no live store is "
                f"rewritten.")
    return "\n".join(lines)


def format_memory_doctor_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /memorydoctor.

    With nothing named, the shipped example
    doctor book is shown - the example this slice
    ships - so the screen is never empty.
    """
    book = _source_book(source)
    lines = ["Memory Doctor (M-168) - " + PLAIN_EXPLANATION, ""]
    for finding in book.findings:
        lines.append(format_finding(finding))
    lines.append("")
    lines.append(format_panel(book))
    lines.append("")
    lines.append(format_verdict(book))
    lines.append("")
    lines.append(format_repairs(book))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_memory_doctor_args(args: Any) -> Tuple[str, Any]:
    """Parse the /memorydoctor grammar both surfaces share.

    No words (or ``show`` / ``list``) shows the
    doctor book; ``finding <finding-id>`` shows
    one finding with its repair shown; ``check
    <check>`` shows the findings one check
    raised; ``store <store>`` shows the findings
    over memories living in one store; ``panel``
    shows the panel derived from the whole book;
    ``verdict`` shows the doctor verdict derived
    for the whole book; ``repairs`` shows the
    repairs derived from the whole book - what
    will be repaired and what will not. Anything
    else is a usage error naming the grammar.
    Returns ``(action, value-or-None)``.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() in ("show", "list"):
        return ("show", None)
    words = text.split()
    head = words[0].lower()
    if head in ("panel", "verdict", "repairs") and len(words) == 1:
        return (head, None)
    if head == "finding" and len(words) == 2:
        try:
            return (head, normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "check" and len(words) == 2:
        try:
            return (head, normalize_check(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "store" and len(words) == 2:
        try:
            return (head, normalize_store(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
