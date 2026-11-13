"""Private by architecture (All-Features roadmap slice M-167).

Part VII continues. The roadmap's words:
``memories live in the workspace/ user stores;
nothing syncs anywhere unless Part X's bridges
are explicitly opened by the user.``

What already ships, and what this slice adds:

* The stored memories themselves already ship
  as data on shipped roads - the project memory
  map (``core/project_memory_map.py``, M-150),
  session memory across days
  (``core/session_memory.py``, M-153),
  cross-project memory
  (``core/cross_project_memory.py``, M-154), the
  self-improving ledger
  (``core/self_improving_ledger.py``, M-155),
  crew memory (``core/crew_memory.py``, M-133),
  the subconscious v2
  (``core/subconscious_v2.py``, M-165) and the
  contradiction watch
  (``core/contradiction_watch.py``, M-166). What
  none of those layers holds is the privacy
  standing of a stored memory itself: which
  store it lives in, and whether anything at all
  may carry it out of that store.
* This slice is that standing, as a pure layer:
  one privacy posting validated as data WITH ITS
  PROVENANCE WHOLE - the stored memory it stands
  over, named by the kind of holding it stands
  in and the shipped piece's id alone; the store
  the memory lives in, the workspace store or
  the user store; the one Part X bridge the user
  has explicitly opened over it - which bridge,
  who opened it, and the day - or that no bridge
  stands open over it at all; who recorded the
  posting, the session it was raised in and
  where the posting was read from. A memory's
  standing is never in question and never stored
  loose: sealed while no bridge stands open over
  it, bridge-open only through the one named
  bridge the user opened, so the boundary the
  panel shows is DERIVED from the posting - and
  a stored panel or verdict whose word is not
  its own tallies' word refuses. Postings are
  composed BY IMPORT from the shipped holdings
  they stand over (a map entry, a session note,
  a ledger candidate, a crew fact, a
  cross-project lesson, a v2 memory, a
  contradiction watch), each judged by its own
  layer's validation, ids and refs only across
  the seams. The shipped data file
  (``mythic_agent/data/private_by_architecture.yaml``)
  holds one example book in exactly the shape a
  real book file takes, a loader reads a book
  file anywhere on disk, the privacy panel is
  DERIVED from the whole book (every posting
  carried whole, in a settled order, its
  boundary shown on every row), a privacy
  VERDICT is derived for the whole book, postings
  are shaped as session news, and a small
  in-memory registry model holds postings one by
  one. The agent layer owns holding a book for a
  session and raising a posting over one of the
  session's own contradiction watches.

Honesty rules, enforced here and pinned by tests:

* **Provenance whole, ids only across the seam.**
  A posting names the stored memory it stands
  over - kind and the shipped piece's id - and
  nothing else of the piece crosses: the piece's
  own words stay in its own layer, judged by its
  own layer's validator.
* **Sealed unless the user opens a bridge.**
  The standing is derived, never chosen: a
  memory stands sealed on every posting that
  names no bridge, and bridge-open only where a
  posting names the one Part X bridge the user
  explicitly opened - who opened it and the day
  stand in the posting, so an opening is never
  silent and never implied.
* **A posting moves nothing.** A posting states
  where a memory lives and the one road out the
  user opened: it carries no memory anywhere,
  opens no bridge itself and syncs nothing - the
  bridges themselves are Part X's roads, not
  this slice's.
* **One posting per memory.** A stored memory
  is posted once in a book: one posting per
  memory kind and memory ref stands, so the
  memory's privacy standing never forks.
* **Data only.** This layer holds postings as
  data: it sends nothing, posts nothing,
  schedules nothing, calls no model, persists
  nothing, syncs nothing and writes no live
  memory - raising a posting changes no shipped
  holding.
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
    "PRIVATE_BY_ARCHITECTURE_RESOURCE",
    "PRIVATE_BY_ARCHITECTURE_SCHEMA",
    "PRIVATE_BY_ARCHITECTURE_SLICE",
    "PLAIN_EXPLANATION",
    "MEMORY_KINDS",
    "HOMES",
    "BRIDGES",
    "STANDINGS",
    "VERDICT_WORDS",
    "SEALED_BRIDGE",
    "USAGE",
    "HomeCount",
    "PrivacyBook",
    "PrivacyPanel",
    "PrivacyPanelRow",
    "PrivacyPosting",
    "PrivacyRegistry",
    "PrivacyVerdict",
    "boundary_line",
    "build_book",
    "build_panel",
    "build_posting",
    "build_verdict",
    "derive_panel",
    "derive_verdict",
    "format_panel",
    "format_posting",
    "format_postings",
    "format_privacy_screen",
    "format_verdict",
    "inspect_posting_source",
    "load_private_by_architecture",
    "load_private_by_architecture_file",
    "normalize_bridge",
    "normalize_home",
    "normalize_memory_kind",
    "panel_plain_words",
    "panel_record",
    "parse_privacy_args",
    "plain_words",
    "book_record",
    "posting_for",
    "posting_from_contradiction_watch",
    "posting_from_crew_entry",
    "posting_from_cross_project_lesson",
    "posting_from_ledger_candidate",
    "posting_from_map_entry",
    "posting_from_session_note",
    "posting_from_subconscious_memory",
    "posting_record",
    "posting_refs",
    "standing_of",
    "total_postings",
    "validate_book",
    "validate_panel",
    "validate_posting",
    "validate_verdict",
    "verdict_plain_words",
    "verdict_record",
]

PRIVATE_BY_ARCHITECTURE_SLICE = "M-167"

PRIVATE_BY_ARCHITECTURE_RESOURCE = "private_by_architecture.yaml"

PRIVATE_BY_ARCHITECTURE_SCHEMA = "mythic.private_by_architecture/1"

#: The holdings a stored memory may stand in:
#: the shipped memory layers a posting may stand
#: over, by the kind of piece it names - the
#: M-166 kinds, and the contradiction watch book
#: itself, the newest holding.
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

#: The stores a memory may live in, by the
#: roadmap's own words: the workspace store and
#: the user store. Panel order stands the
#: workspace store first.
HOMES = ("workspace", "user")

_HOME_ALIASES = {
    "workspace": "workspace",
    "workspace-store": "workspace",
    "project": "workspace",
    "project-store": "workspace",
    "user": "user",
    "user-store": "user",
    "personal": "user",
}

#: The Part X bridges a user may explicitly open
#: over a memory - and the one word that names no
#: bridge standing open at all. The bridges
#: themselves ship in Part X; this layer names
#: only which one the user opened.
BRIDGES = (
    "none", "mcp", "samverk", "samtal", "ide",
    "forge", "ci", "tracker", "wyrd", "webhook",
    "export")

_BRIDGE_ALIASES = {
    "none": "none",
    "closed": "none",
    "sealed": "none",
    "no-bridge": "none",
    "mcp": "mcp",
    "samverk": "samverk",
    "samtal": "samtal",
    "ide": "ide",
    "ide-companion": "ide",
    "editor": "ide",
    "forge": "forge",
    "forge-host": "forge",
    "ci": "ci",
    "ci-bridge": "ci",
    "tracker": "tracker",
    "issue-tracker": "tracker",
    "wyrd": "wyrd",
    "wyrd-seam": "wyrd",
    "webhook": "webhook",
    "webhook-door": "webhook",
    "export": "export",
    "export-file": "export",
    "portable-file": "export",
}

#: The bridge word that names no bridge standing
#: open: a memory under it syncs nowhere.
SEALED_BRIDGE = "none"

#: How a stored memory stands, quietest first:
#: sealed while no bridge stands open over it,
#: bridge-open only through the one named bridge
#: the user explicitly opened. Derived, never
#: stored loose.
STANDINGS = ("sealed", "bridge-open")

#: The words a whole book's privacy verdict may
#: carry, quietest first: how much of the book
#: stands open at the user's own hand.
VERDICT_WORDS = ("sealed", "guarded", "bridged")

_POSTING_KEYS = frozenset({
    "posting_id", "id", "title", "name", "subject",
    "memory_kind", "kind", "memory_ref", "ref",
    "home", "store",
    "bridge",
    "opened_by", "opener",
    "opened_on",
    "posted_on", "day", "date",
    "recorded_by", "recorder", "by", "who",
    "source", "origin_session", "session",
})

_ROW_KEYS = frozenset({
    "posting_id", "id", "title",
    "memory_kind", "memory_ref",
    "home", "bridge", "standing", "posted_on",
})

_HOME_COUNT_KEYS = frozenset({"home", "items", "count"})

_PANEL_KEYS = frozenset({
    "panel_id", "id", "rows", "postings",
    "total_postings", "total",
    "total_sealed", "sealed",
    "total_open", "open",
    "distinct_memories", "memories",
    "home_counts", "homes",
    "as_of", "day",
    "account", "statements",
})

_VERDICT_KEYS = frozenset({
    "total_postings", "total",
    "total_sealed", "sealed",
    "total_open", "open",
    "distinct_memories", "memories",
    "distinct_kinds", "kinds",
    "earliest_on", "earliest",
    "latest_on", "latest",
    "verdict",
})

_BOOK_KEYS = frozenset({"title", "name"})

_PRIVACY_BOOK_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "canon_note", "guide", "postings", "records", "panels",
})

_EXAMPLE_TITLE = "Private by architecture at the M-166 slice boundary"

_EXAMPLE_POSTING_IDS = (
    "posting-no-docker-map", "posting-lesson-export",
    "posting-samtal-wal", "posting-campaign-home",
    "posting-verify-remote")

_EXAMPLE_FIRST_POSTING_ID = "posting-no-docker-map"

_EXAMPLE_FIRST_POSTING_TITLE = (
    "the no-Docker law stays in the workspace")

_EXAMPLE_PANEL_ID = "panel-m166-boundary"

_EXAMPLE_AS_OF = "2026-11-09"

_EXAMPLE_PANEL_ROW_IDS = (
    "posting-lesson-export", "posting-no-docker-map",
    "posting-samtal-wal", "posting-campaign-home",
    "posting-verify-remote")

PLAIN_EXPLANATION = (
    "Private by architecture: memories live in "
    "the workspace and user stores; nothing syncs "
    "anywhere unless Part X's bridges are "
    "explicitly opened by the user. A posting "
    "stands over one stored memory, named by the "
    "kind of holding it stands in and the shipped "
    "piece's id alone, and carries its provenance "
    "whole: the store the memory lives in, the one "
    "bridge the user has explicitly opened over "
    "it - which bridge, who opened it and the "
    "day - or that no bridge stands open over it "
    "at all, who recorded the posting and the "
    "session it was raised in. A memory's standing "
    "is derived, never chosen - sealed while no "
    "bridge stands open over it, bridge-open only "
    "through the one named bridge the user "
    "opened. The privacy panel is derived from "
    "the book at call time, and the privacy "
    "verdict is derived for the whole book. This "
    "layer holds postings as data only: it sends "
    "nothing, posts nothing, schedules nothing, "
    "calls no model, persists nothing, syncs "
    "nothing and moves no memory - a posting opens "
    "no road and carries nothing anywhere."
)

USAGE = (
    "Usage: /private, /private show, "
    "/private posting <posting-id>, "
    "/private kind <memory-kind>, "
    "/private home <home>, "
    "/private panel, /private verdict"
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


def normalize_memory_kind(value: Any) -> str:
    """The canonical memory kind a word names.

    A kind is one of :data:`MEMORY_KINDS` - the
    holding a stored memory stands in - read
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


def normalize_home(value: Any) -> str:
    """The canonical store a word names.

    A home is one of :data:`HOMES` - the
    workspace store or the user store - read
    case-insensitively, with the long spellings
    (``workspace-store``, ``user-store``) read
    onto their stores. Anything else raises,
    plainly naming the set.
    """
    if isinstance(value, str):
        wanted = _HOME_ALIASES.get(value.strip().lower())
        if wanted is not None:
            return wanted
    raise ValueError(
        "a memory's home must be one of %s, got %r"
        % ("/".join(HOMES), value))


def normalize_bridge(value: Any) -> str:
    """The canonical bridge a word names.

    A bridge is one of :data:`BRIDGES` - a Part X
    bridge the user may explicitly open, or
    ``none`` when no bridge stands open - read
    case-insensitively, with plain spellings
    (``sealed``, ``ide-companion``, ``export-file``)
    read onto their bridges. Anything else
    raises, plainly naming the set.
    """
    if isinstance(value, str):
        wanted = _BRIDGE_ALIASES.get(value.strip().lower())
        if wanted is not None:
            return wanted
    raise ValueError(
        "a bridge must be one of %s, got %r"
        % ("/".join(BRIDGES), value))


# ---------------------------------------------------------------------
# The privacy posting: a stored memory, its store, as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class PrivacyPosting:
    """One privacy standing: a stored memory, posted private.

    ``title`` names the posting in plain words;
    the stored memory it stands over is named by
    ``memory_kind`` (the holding it stands in)
    and ``memory_ref`` (the shipped piece's id
    alone - the piece's own words never cross
    into this record). ``home`` is the store the
    memory lives in - the workspace store or the
    user store. ``bridge`` is the one Part X
    bridge the user has explicitly opened over
    the memory, or ``none`` when no bridge stands
    open; an opened bridge stands whole beside
    it: ``opened_by`` who opened it and
    ``opened_on`` the day - and a posting naming
    no bridge names no opener and no opening day,
    so an opening is never implied. The
    provenance stands whole beside those:
    ``posted_on`` the day the posting was raised,
    ``recorded_by`` who recorded it,
    ``origin_session`` the session it was raised
    in and ``source`` where the posting was read
    from. How the memory stands is never a field:
    it is derived by :func:`standing_of`, and the
    boundary the panel shows is derived by
    :func:`boundary_line`.
    """

    title: str
    memory_kind: str
    memory_ref: str
    home: str
    posted_on: str
    recorded_by: str
    source: str
    origin_session: str
    bridge: str = SEALED_BRIDGE
    opened_by: Optional[str] = None
    opened_on: Optional[str] = None
    posting_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.posting_id is not None:
            object.__setattr__(
                self, "posting_id",
                normalize_member_id(self.posting_id))
        object.__setattr__(
            self, "title", _check_title(self.title, "a posting's title"))
        object.__setattr__(
            self, "memory_kind", normalize_memory_kind(self.memory_kind))
        object.__setattr__(
            self, "memory_ref",
            _check_word(self.memory_ref, "a posting's memory ref"))
        object.__setattr__(
            self, "home", normalize_home(self.home))
        object.__setattr__(
            self, "bridge", normalize_bridge(self.bridge))
        if self.bridge == SEALED_BRIDGE:
            if self.opened_by is not None or self.opened_on is not None:
                raise ValueError(
                    "a sealed posting names no bridge opening "
                    "- no bridge stands open over this memory, "
                    "so no opener and no opening day stand")
        else:
            if self.opened_by is None or self.opened_on is None:
                raise ValueError(
                    "a bridge stands open only where the user "
                    "explicitly opened it - an opened bridge "
                    "names who opened it and the day")
            object.__setattr__(
                self, "opened_by",
                _check_title(self.opened_by, "a posting's opener"))
            object.__setattr__(
                self, "opened_on",
                _check_day(self.opened_on, "a posting's opening day"))
        object.__setattr__(
            self, "posted_on",
            _check_day(self.posted_on, "a posting's posted-on day"))
        object.__setattr__(
            self, "recorded_by",
            _check_title(self.recorded_by, "a posting's recorder"))
        object.__setattr__(
            self, "source",
            _check_title(self.source, "a posting's source"))
        object.__setattr__(
            self, "origin_session",
            _check_word(self.origin_session, "a posting's origin session"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "private_by_architecture_posting",
            "slice": PRIVATE_BY_ARCHITECTURE_SLICE,
            "posting_id": self.posting_id,
            "title": self.title,
            "memory_kind": self.memory_kind,
            "memory_ref": self.memory_ref,
            "home": self.home,
            "bridge": self.bridge,
            "opened_by": self.opened_by,
            "opened_on": self.opened_on,
            "posted_on": self.posted_on,
            "recorded_by": self.recorded_by,
            "source": self.source,
            "origin_session": self.origin_session,
            "standing": standing_of(self),
            "boundary": boundary_line(self),
        }


def _check_posting_ref(value: Any) -> "PrivacyPosting":
    if isinstance(value, PrivacyPosting):
        return value
    if isinstance(value, dict):
        return validate_posting(value)
    raise ValueError(f"a privacy posting is needed, got {value!r}")


def validate_posting(posting: Any) -> PrivacyPosting:
    """Validate one posting into a PrivacyPosting.

    Accepts a posting or a mapping naming a
    ``title`` (or ``name`` / ``subject``), a
    ``memory_kind`` (or ``kind``), a ``memory_ref``
    (or ``ref``), a ``home`` (or ``store``), a
    ``posted_on`` (or ``day`` / ``date``), a
    ``recorded_by`` (or ``recorder`` / ``by`` /
    ``who``), a ``source``, an ``origin_session``
    (or ``session``) and, optionally, a ``bridge``
    (``none`` when it stands unnamed), an
    ``opened_by`` (or ``opener``) and
    ``opened_on`` pair naming the user's explicit
    opening, and a ``posting_id`` (or ``id``).
    Derived keys a posting record carries
    (``standing``, ``boundary``, ``type``,
    ``slice``) are not posting fields and refuse
    as unknown keys. Naming two spellings of one
    field with different values refuses, and
    unknown keys refuse.
    """
    if isinstance(posting, PrivacyPosting):
        return posting
    if not isinstance(posting, dict):
        raise ValueError(f"a privacy posting is needed, got {posting!r}")
    unknown = set(posting) - _POSTING_KEYS
    if unknown:
        raise ValueError(
            "unknown posting keys: %s" % ", ".join(sorted(unknown)))

    def _needed(spellings: Tuple[str, ...], what: str) -> Any:
        value = _pick_any(posting, spellings, what)
        if value is None:
            raise ValueError(f"a posting is missing its {what}")
        return value

    kwargs: Dict[str, Any] = {
        "title": _needed(("title", "name", "subject"), "title"),
        "memory_kind": _needed(("memory_kind", "kind"), "memory kind"),
        "memory_ref": _needed(("memory_ref", "ref"), "memory ref"),
        "home": _needed(("home", "store"), "home"),
        "posted_on": _needed(("posted_on", "day", "date"), "posted day"),
        "recorded_by": _needed(
            ("recorded_by", "recorder", "by", "who"), "recorder"),
        "source": _needed(("source",), "source"),
        "origin_session": _needed(
            ("origin_session", "session"), "origin session"),
    }
    bridge = _pick_any(posting, ("bridge",), "bridges")
    if bridge is not None:
        kwargs["bridge"] = bridge
    opened_by = _pick_any(posting, ("opened_by", "opener"), "openers")
    if opened_by is not None:
        kwargs["opened_by"] = opened_by
    opened_on = _pick_any(posting, ("opened_on",), "opening days")
    if opened_on is not None:
        kwargs["opened_on"] = opened_on
    posting_id = _pick_any(posting, ("posting_id", "id"), "posting ids")
    if posting_id is not None:
        kwargs["posting_id"] = posting_id
    return PrivacyPosting(**kwargs)


def build_posting(posting: Any = None, **kwargs: Any) -> PrivacyPosting:
    """Build one validated posting, from a mapping or field words."""
    if isinstance(posting, PrivacyPosting) and not kwargs:
        return posting
    if isinstance(posting, dict) or posting is None:
        merged: Dict[str, Any] = {}
        if isinstance(posting, dict):
            merged.update(posting)
        merged.update(kwargs)
        return validate_posting(merged)
    raise ValueError(f"a privacy posting is needed, got {posting!r}")


def standing_of(posting: Any) -> str:
    """How one posted memory stands: derived, never chosen.

    Sealed while no bridge stands open over the
    memory - nothing syncs anywhere - and
    bridge-open only where the posting names the
    one Part X bridge the user explicitly opened.
    """
    current = _check_posting_ref(posting)
    if current.bridge == SEALED_BRIDGE:
        return "sealed"
    return "bridge-open"


def boundary_line(posting: Any) -> str:
    """The boundary one posting shows on the panel, derived.

    A sealed memory lives in its store and syncs
    nowhere; a bridge-open memory may leave only
    through the one bridge the user opened over
    it - every other road stays shut.
    """
    current = _check_posting_ref(posting)
    if current.bridge == SEALED_BRIDGE:
        return (
            f"the {current.memory_kind} memory "
            f"{current.memory_ref} lives in the "
            f"{current.home} store and syncs nowhere - "
            f"no bridge stands open over it")
    return (
        f"the {current.memory_kind} memory "
        f"{current.memory_ref} lives in the "
        f"{current.home} store and may leave only "
        f"through the {current.bridge} bridge, "
        f"opened by {current.opened_by} on "
        f"{current.opened_on} - every other road "
        f"stays shut")


# ---------------------------------------------------------------------
# Composition: shipped holdings read onto postings, by import.
# ---------------------------------------------------------------------


def _raised_posting(*, memory_kind: str, memory_ref: Optional[str],
                    piece_word: str, title: Any, home: Any,
                    bridge: Any, opened_by: Any, opened_on: Any,
                    posted_on: Any, recorded_by: Any, source: Any,
                    origin_session: Any,
                    posting_id: Any) -> PrivacyPosting:
    if memory_ref is None:
        raise ValueError(
            f"a {piece_word} with no id cannot be posted "
            f"- a privacy posting names its stored "
            f"memory by id")
    return PrivacyPosting(
        title=title if title is not None else (
            f"the {memory_kind} memory {memory_ref}, posted private"),
        memory_kind=memory_kind, memory_ref=memory_ref,
        home=home, bridge=bridge, opened_by=opened_by,
        opened_on=opened_on, posted_on=posted_on,
        recorded_by=recorded_by, source=source,
        origin_session=origin_session,
        posting_id=posting_id if posting_id is not None else (
            f"posting-{memory_ref}"))


def posting_from_map_entry(entry: Any, *, home: Any,
                           posted_on: Any, recorded_by: Any,
                           origin_session: Any,
                           source: Any = "private by architecture",
                           title: Any = None,
                           bridge: Any = SEALED_BRIDGE,
                           opened_by: Any = None, opened_on: Any = None,
                           posting_id: Any = None) -> PrivacyPosting:
    """Raise one posting over a project memory-map entry, by import.

    The entry (M-150) is judged by the map's own
    ``validate_entry``; only its id crosses - it
    stands as the posting's memory ref, of kind
    ``memory-map``. The entry's own title, detail
    and reference are never read here: the
    posting names the store the memory lives in
    and the one bridge the user opened, if any.
    """
    checked = _validate_map_entry(entry)
    return _raised_posting(
        memory_kind="memory-map", memory_ref=checked.entry_id,
        piece_word="memory map entry", title=title, home=home,
        bridge=bridge, opened_by=opened_by, opened_on=opened_on,
        posted_on=posted_on, recorded_by=recorded_by, source=source,
        origin_session=origin_session, posting_id=posting_id)


def posting_from_session_note(note: Any, *, home: Any,
                              posted_on: Any, recorded_by: Any,
                              origin_session: Any,
                              source: Any = "private by architecture",
                              title: Any = None,
                              bridge: Any = SEALED_BRIDGE,
                              opened_by: Any = None,
                              opened_on: Any = None,
                              posting_id: Any = None) -> PrivacyPosting:
    """Raise one posting over a session-memory note, by import.

    The carried note (M-153) is judged by the
    session layer's own ``validate_note``; only
    its id crosses - it stands as the posting's
    memory ref, of kind ``session-note``.
    """
    checked = _validate_note(note)
    return _raised_posting(
        memory_kind="session-note", memory_ref=checked.note_id,
        piece_word="session note", title=title, home=home,
        bridge=bridge, opened_by=opened_by, opened_on=opened_on,
        posted_on=posted_on, recorded_by=recorded_by, source=source,
        origin_session=origin_session, posting_id=posting_id)


def posting_from_cross_project_lesson(lesson: Any, *, home: Any,
                                      posted_on: Any,
                                      recorded_by: Any,
                                      origin_session: Any,
                                      source: Any = "private by architecture",
                                      title: Any = None,
                                      bridge: Any = SEALED_BRIDGE,
                                      opened_by: Any = None,
                                      opened_on: Any = None,
                                      posting_id: Any = None
                                      ) -> PrivacyPosting:
    """Raise one posting over a cross-project lesson, by import.

    The lesson (M-154) is judged by the
    cross-project layer's own ``validate_lesson``;
    only its id crosses - it stands as the
    posting's memory ref, of kind
    ``cross-project-lesson``.
    """
    checked = _validate_lesson(lesson)
    return _raised_posting(
        memory_kind="cross-project-lesson",
        memory_ref=checked.lesson_id,
        piece_word="cross-project lesson", title=title, home=home,
        bridge=bridge, opened_by=opened_by, opened_on=opened_on,
        posted_on=posted_on, recorded_by=recorded_by, source=source,
        origin_session=origin_session, posting_id=posting_id)


def posting_from_ledger_candidate(candidate: Any, *, home: Any,
                                  posted_on: Any, recorded_by: Any,
                                  origin_session: Any,
                                  source: Any = "private by architecture",
                                  title: Any = None,
                                  bridge: Any = SEALED_BRIDGE,
                                  opened_by: Any = None,
                                  opened_on: Any = None,
                                  posting_id: Any = None
                                  ) -> PrivacyPosting:
    """Raise one posting over a self-improving ledger candidate.

    The candidate (M-155) is judged by the
    ledger's own ``validate_candidate``; only its
    id crosses - it stands as the posting's
    memory ref, of kind ``ledger-candidate``.
    """
    checked = _validate_candidate(candidate)
    return _raised_posting(
        memory_kind="ledger-candidate",
        memory_ref=checked.candidate_id,
        piece_word="ledger candidate", title=title, home=home,
        bridge=bridge, opened_by=opened_by, opened_on=opened_on,
        posted_on=posted_on, recorded_by=recorded_by, source=source,
        origin_session=origin_session, posting_id=posting_id)


def posting_from_crew_entry(entry: Any, *, home: Any,
                            posted_on: Any, recorded_by: Any,
                            origin_session: Any,
                            source: Any = "private by architecture",
                            title: Any = None,
                            bridge: Any = SEALED_BRIDGE,
                            opened_by: Any = None,
                            opened_on: Any = None,
                            posting_id: Any = None) -> PrivacyPosting:
    """Raise one posting over a crew-memory entry, by import.

    The entry (M-133) is judged by crew memory's
    own ``validate_entry``; only its id crosses -
    it stands as the posting's memory ref, of kind
    ``crew-fact``. The fact's own words never
    cross.
    """
    checked = _validate_crew_entry(entry)
    return _raised_posting(
        memory_kind="crew-fact", memory_ref=checked.entry_id,
        piece_word="crew entry", title=title, home=home,
        bridge=bridge, opened_by=opened_by, opened_on=opened_on,
        posted_on=posted_on, recorded_by=recorded_by, source=source,
        origin_session=origin_session, posting_id=posting_id)


def posting_from_subconscious_memory(memory: Any, *, home: Any,
                                     posted_on: Any,
                                     recorded_by: Any,
                                     origin_session: Any,
                                     source: Any = "private by architecture",
                                     title: Any = None,
                                     bridge: Any = SEALED_BRIDGE,
                                     opened_by: Any = None,
                                     opened_on: Any = None,
                                     posting_id: Any = None
                                     ) -> PrivacyPosting:
    """Raise one posting over a subconscious v2 memory, by import.

    The v2 memory (M-165) is judged by its own
    layer's ``validate_memory``; only its id
    crosses - it stands as the posting's memory
    ref, of kind ``subconscious-memory``. A v2
    memory with no id cannot be posted. The
    memory's own title and provenance words never
    cross into the posting.
    """
    checked = _validate_v2_memory(memory)
    return _raised_posting(
        memory_kind="subconscious-memory",
        memory_ref=checked.memory_id,
        piece_word="subconscious memory", title=title, home=home,
        bridge=bridge, opened_by=opened_by, opened_on=opened_on,
        posted_on=posted_on, recorded_by=recorded_by, source=source,
        origin_session=origin_session, posting_id=posting_id)


def posting_from_contradiction_watch(watch: Any, *, home: Any,
                                     posted_on: Any,
                                     recorded_by: Any,
                                     origin_session: Any,
                                     source: Any = "private by architecture",
                                     title: Any = None,
                                     bridge: Any = SEALED_BRIDGE,
                                     opened_by: Any = None,
                                     opened_on: Any = None,
                                     posting_id: Any = None
                                     ) -> PrivacyPosting:
    """Raise one posting over a contradiction watch, by import.

    The watch (M-166) is judged by the watch
    layer's own ``validate_watch``; only its id
    crosses - it stands as the posting's memory
    ref, of kind ``contradiction-watch``. A watch
    with no id cannot be posted. The watch's own
    claims never cross into the posting.
    """
    checked = _validate_watch(watch)
    return _raised_posting(
        memory_kind="contradiction-watch",
        memory_ref=checked.watch_id,
        piece_word="contradiction watch", title=title, home=home,
        bridge=bridge, opened_by=opened_by, opened_on=opened_on,
        posted_on=posted_on, recorded_by=recorded_by, source=source,
        origin_session=origin_session, posting_id=posting_id)


def inspect_posting_source(piece: Any) -> Dict[str, Any]:
    """Inspect one shipped piece: its kind and ref only.

    The piece is judged by the layer that owns its
    type, never by whichever validator happens to
    accept its shape first. A posting reports the
    memory it stands over; each shipped holding
    reports the kind and ref a posting raised over
    it would carry. A piece no shipped layer owns
    refuses.
    """
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
                (_validate_v2_memory, "subconscious-memory")):
            try:
                checked = road(piece)
            except Exception:
                continue
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
# The privacy panel: every posting carried whole, derived.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class PrivacyPanelRow:
    """One posting carried whole into the panel, its boundary shown.

    Every field is the posting's own head - its
    id, title, the memory it stands over (kind
    and ref), the store the memory lives in, the
    bridge the user opened over it and the day
    the posting was raised - beside the standing
    read off the posting itself: sealed, or
    bridge-open through that one bridge.
    :func:`validate_row` judged against its
    posting refuses a row whose fields disagree
    with the row it derives.
    """

    posting_id: str
    title: str
    memory_kind: str
    memory_ref: str
    home: str
    bridge: str
    standing: str
    posted_on: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "posting_id", normalize_member_id(self.posting_id))
        object.__setattr__(
            self, "title", _check_title(self.title, "a row's title"))
        object.__setattr__(
            self, "memory_kind", normalize_memory_kind(self.memory_kind))
        object.__setattr__(
            self, "memory_ref",
            _check_word(self.memory_ref, "a row's memory ref"))
        object.__setattr__(
            self, "home", normalize_home(self.home))
        object.__setattr__(
            self, "bridge", normalize_bridge(self.bridge))
        word = _clean_text(self.standing, "a row's standing")
        derived = "sealed" if self.bridge == SEALED_BRIDGE else "bridge-open"
        if word != derived:
            raise ValueError(
                f"a row's standing must be the standing "
                f"its own bridge derives ({derived!r}) - a "
                f"memory with no bridge open over it stands "
                f"sealed, got {word!r}")
        object.__setattr__(self, "standing", word)
        object.__setattr__(
            self, "posted_on",
            _check_day(self.posted_on, "a row's posted-on day"))

    @property
    def sort_key(self) -> Tuple[int, str, str]:
        """This row's place in panel order (derived).

        Rows stand by home - the workspace store
        first, then the user store - then title,
        then posting id: the book's stores in the
        roadmap's own order.
        """
        return (HOMES.index(self.home), self.title.lower(), self.posting_id)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "private_by_architecture_panel_row",
            "slice": PRIVATE_BY_ARCHITECTURE_SLICE,
            "posting_id": self.posting_id,
            "title": self.title,
            "memory_kind": self.memory_kind,
            "memory_ref": self.memory_ref,
            "home": self.home,
            "bridge": self.bridge,
            "standing": self.standing,
            "posted_on": self.posted_on,
        }


def _row_for_posting(posting: PrivacyPosting) -> PrivacyPanelRow:
    return PrivacyPanelRow(
        posting_id=posting.posting_id, title=posting.title,
        memory_kind=posting.memory_kind, memory_ref=posting.memory_ref,
        home=posting.home, bridge=posting.bridge,
        standing=standing_of(posting), posted_on=posting.posted_on)


def _check_row_ref(value: Any) -> PrivacyPanelRow:
    if isinstance(value, PrivacyPanelRow):
        return value
    if isinstance(value, dict):
        return validate_row(value)
    raise ValueError(f"a panel row is needed, got {value!r}")


def validate_row(row: Any, posting: Any = None) -> PrivacyPanelRow:
    """Validate one panel row into a PrivacyPanelRow.

    Accepts a row or a mapping naming its fields.
    With *posting* given, the row is judged
    against the row that posting derives.
    """
    if isinstance(row, PrivacyPanelRow):
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

        current = PrivacyPanelRow(
            posting_id=_needed(("posting_id", "id"), "posting id"),
            title=_needed(("title",), "title"),
            memory_kind=_needed(("memory_kind",), "memory kind"),
            memory_ref=_needed(("memory_ref",), "memory ref"),
            home=_needed(("home",), "home"),
            bridge=_needed(("bridge",), "bridge"),
            standing=_needed(("standing",), "standing"),
            posted_on=_needed(("posted_on",), "posted-on day"))
    else:
        raise ValueError(f"a panel row must be a mapping, got {row!r}")
    if posting is not None:
        derived = _row_for_posting(_check_posting_ref(posting))
        if current != derived:
            raise ValueError(
                "a stored row disagrees with the row "
                "its posting derives")
    return current


def build_row(row: Any = None, posting: Any = None,
              **kwargs: Any) -> PrivacyPanelRow:
    """Build one validated row, from a mapping or field words."""
    if isinstance(row, PrivacyPanelRow) and not kwargs:
        return validate_row(row, posting)
    if isinstance(row, dict) or row is None:
        merged: Dict[str, Any] = {}
        if isinstance(row, dict):
            merged.update(row)
        merged.update(kwargs)
        return validate_row(merged, posting)
    return validate_row(row, posting)


@dataclass(frozen=True)
class HomeCount:
    """How many of a panel's postings live in one store."""

    home: str
    items: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "home", normalize_home(self.home))
        object.__setattr__(
            self, "items", _check_count(self.items, "a home count"))

    def to_record(self) -> Dict[str, Any]:
        return {"home": self.home, "items": self.items}


def _check_home_count_ref(value: Any) -> HomeCount:
    if isinstance(value, HomeCount):
        return value
    if isinstance(value, dict):
        unknown = set(value) - _HOME_COUNT_KEYS
        if unknown:
            raise ValueError(
                "unknown home-count keys: %s"
                % ", ".join(sorted(unknown)))
        home = _pick_any(value, ("home",), "homes")
        if home is None:
            raise ValueError("a home count is missing its home")
        items = _pick_any(value, ("items", "count"), "counts")
        if items is None:
            raise ValueError("a home count is missing its count")
        return HomeCount(home=home, items=items)
    raise ValueError(f"a home count is needed, got {value!r}")


def _panel_account(total_postings: int, total_sealed: int,
                   total_open: int, distinct_memories: int,
                   home_counts: Tuple[HomeCount, ...], as_of: str
                   ) -> Tuple[str, ...]:
    tallies = ", ".join(
        f"{count.home} {count.items}"
        for count in sorted(home_counts, key=lambda count: count.home))
    return (
        f"The privacy panel holds {total_postings} "
        f"postings as of {as_of}: {total_sealed} "
        f"sealed and {total_open} standing bridge-open "
        f"over {distinct_memories} stored memories: "
        f"{tallies}.",
        "Rows stand by home - the workspace store "
        "first, then the user store - then title, "
        "then posting id, so two panels of one book "
        "diff cleanly, line by line.",
        "Every row shows its boundary: a sealed "
        "memory syncs nowhere, and a bridge-open "
        "memory may leave only through the one "
        "bridge the user explicitly opened over it "
        "- no posting opens a road it does not name.",
        "The panel is read off the book at call "
        "time - it is derived, never stored loose - "
        "and a posting moves nothing: no memory "
        "leaves its store by standing on this panel.",
    )


@dataclass(frozen=True)
class PrivacyPanel:
    """The privacy panel of one book, derived.

    ``rows`` are the book's postings carried
    whole, in panel order (by home - the workspace
    store first, then the user store - then title,
    then posting id), each showing its boundary;
    ``total_postings`` is the rows' own count,
    ``total_sealed`` the rows standing sealed and
    ``total_open`` the rows standing bridge-open -
    the two standings' counts stand summing to
    the total, and a panel that says otherwise
    refuses; ``distinct_memories`` counts the
    stored memories the rows stand over, and
    ``home_counts`` the per-store tallies of their
    homes. ``as_of`` is the rows' own latest
    posted day. ``account`` is read off those
    numbers. A panel whose rows stand out of
    panel order, or whose tallies are not its own
    rows' tallies, refuses at construction;
    :func:`validate_panel` judged against a book
    refuses a stored panel that disagrees with
    the derived one.
    """

    rows: Tuple[PrivacyPanelRow, ...] = ()
    total_postings: int = 0
    total_sealed: int = 0
    total_open: int = 0
    distinct_memories: int = 0
    home_counts: Tuple[HomeCount, ...] = ()
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
            if row.posting_id in seen:
                raise ValueError(
                    f"a panel row for posting {row.posting_id!r} "
                    f"already exists")
            seen.add(row.posting_id)
        keys = [row.sort_key for row in rows]
        if keys != sorted(keys):
            raise ValueError(
                "a panel's rows must stand in panel order "
                "(by home, then title, then posting id)")
        object.__setattr__(self, "rows", rows)
        object.__setattr__(
            self, "total_postings",
            _check_count(self.total_postings, "a panel's total postings"))
        if self.total_postings != len(rows):
            raise ValueError(
                "a panel's total postings must be its own "
                "rows' count")
        object.__setattr__(
            self, "total_sealed",
            _check_count(self.total_sealed, "a panel's total sealed"))
        if self.total_sealed != sum(
                1 for r in rows if r.standing == "sealed"):
            raise ValueError(
                "a panel's sealed count must be its own "
                "rows' sealed count")
        object.__setattr__(
            self, "total_open",
            _check_count(self.total_open, "a panel's total open"))
        if self.total_open != sum(
                1 for r in rows if r.standing == "bridge-open"):
            raise ValueError(
                "a panel's bridge-open count must be its "
                "own rows' bridge-open count")
        if self.total_sealed + self.total_open != self.total_postings:
            raise ValueError(
                "a panel's standings must sum to its own "
                "total postings - every posting stands "
                "sealed or bridge-open")
        object.__setattr__(
            self, "distinct_memories",
            _check_count(
                self.distinct_memories, "a panel's distinct memories"))
        if self.distinct_memories != len({
                (r.memory_kind, r.memory_ref) for r in rows}):
            raise ValueError(
                "a panel's distinct memories must be its "
                "own rows' distinct memories")
        if rows and self.as_of != max(r.posted_on for r in rows):
            raise ValueError(
                "a panel's as-of day must be its own "
                "rows' latest posted day")
        if isinstance(self.home_counts, (str, bytes)) \
                or not isinstance(self.home_counts, (list, tuple)):
            raise ValueError(
                f"a panel's home counts must be a list, "
                f"got {self.home_counts!r}")
        home_counts = tuple(
            _check_home_count_ref(c) for c in self.home_counts)
        seen_homes = set()
        for count in home_counts:
            if count.home in seen_homes:
                raise ValueError(
                    f"a home count named {count.home!r} "
                    f"already exists")
            seen_homes.add(count.home)
        object.__setattr__(self, "home_counts", home_counts)
        if sum(c.items for c in home_counts) != self.total_postings:
            raise ValueError(
                "a panel's home counts must sum to its "
                "own total postings")
        tallies = {
            home: sum(1 for r in rows if r.home == home)
            for home in HOMES}
        for count in home_counts:
            if count.items != tallies.get(count.home, 0):
                raise ValueError(
                    "a panel's home counts must be its "
                    "own rows' counts")
        if {k for k, v in tallies.items() if v} != {
                c.home for c in home_counts}:
            raise ValueError(
                "a panel's home counts must name every "
                "store its rows live in")
        object.__setattr__(self, "account", _check_account(self.account))

    def row_for(self, posting_id: Any) -> PrivacyPanelRow:
        """The panel row one posting names in this panel."""
        wanted = normalize_member_id(posting_id)
        for row in self.rows:
            if row.posting_id == wanted:
                return row
        raise KeyError(f"no row in the panel: posting {wanted!r}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "private_by_architecture_panel",
            "slice": PRIVATE_BY_ARCHITECTURE_SLICE,
            "panel_id": self.panel_id,
            "rows": [row.to_record() for row in self.rows],
            "total_postings": self.total_postings,
            "total_sealed": self.total_sealed,
            "total_open": self.total_open,
            "distinct_memories": self.distinct_memories,
            "home_counts": [c.to_record() for c in self.home_counts],
            "as_of": self.as_of,
            "account": list(self.account),
        }


def _held_postings(source: Any) -> Tuple[PrivacyPosting, ...]:
    if isinstance(source, PrivacyBook):
        return source.postings
    if isinstance(source, PrivacyRegistry):
        return source.list_postings()
    if isinstance(source, (list, tuple)):
        return tuple(_check_posting_ref(item) for item in source)
    raise ValueError(f"privacy postings are needed, got {source!r}")


def derive_panel(source: Any) -> PrivacyPanel:
    """Derive the privacy panel from one book.

    The rows are the book's postings carried
    whole, in panel order: by home - the workspace
    store first, then the user store - then title,
    then posting id, each showing its boundary
    with its standing read off its own bridge.
    *source* is a book or a registry. A source
    holding no posting refuses - a panel of
    nothing is no panel.
    """
    postings = _held_postings(source)
    if not postings:
        raise ValueError("a panel needs at least one privacy posting")
    rows = []
    for posting in postings:
        if posting.posting_id is None:
            raise ValueError(
                "a panel row must name its posting - a "
                "posting with no id refuses derivation")
        rows.append(_row_for_posting(posting))
    rows = tuple(sorted(rows, key=lambda r: r.sort_key))
    tallies = {
        home: sum(1 for r in rows if r.home == home)
        for home in HOMES}
    home_counts = tuple(
        HomeCount(home=home, items=tallies[home])
        for home in HOMES if tallies[home])
    distinct = len({(r.memory_kind, r.memory_ref) for r in rows})
    sealed = sum(1 for r in rows if r.standing == "sealed")
    opened = len(rows) - sealed
    as_of = max(r.posted_on for r in rows)
    return PrivacyPanel(
        rows=rows, total_postings=len(rows),
        total_sealed=sealed, total_open=opened,
        distinct_memories=distinct,
        home_counts=home_counts,
        account=_panel_account(
            len(rows), sealed, opened, distinct, home_counts, as_of),
        as_of=as_of)


def validate_panel(panel: Any, source: Any = None
                   ) -> PrivacyPanel:
    """Validate one panel into a PrivacyPanel.

    Accepts a panel or a mapping naming ``rows``
    (or ``postings``), a ``total_postings`` (or
    ``total``), a ``total_sealed`` (or ``sealed``),
    a ``total_open`` (or ``open``), a
    ``distinct_memories`` (or ``memories``),
    ``home_counts`` (or ``homes``), an ``as_of``
    (or ``day``), an ``account`` (or
    ``statements``) and an optional ``panel_id``
    (or ``id``). With *source* given (a book), the
    panel is judged against the panel derived
    from that book.
    """
    if isinstance(panel, PrivacyPanel):
        current = panel
    elif isinstance(panel, dict):
        unknown = set(panel) - _PANEL_KEYS
        if unknown:
            raise ValueError(
                "unknown panel keys: %s" % ", ".join(sorted(unknown)))
        rows = _pick_any(panel, ("rows", "postings"), "rows")
        if rows is None:
            raise ValueError("a panel is missing its rows")
        total = _pick_any(panel, ("total_postings", "total"), "totals")
        if total is None:
            raise ValueError("a panel is missing its total postings")
        sealed = _pick_any(
            panel, ("total_sealed", "sealed"), "sealed totals")
        if sealed is None:
            raise ValueError("a panel is missing its total sealed")
        opened = _pick_any(panel, ("total_open", "open"), "open totals")
        if opened is None:
            raise ValueError("a panel is missing its total open")
        distinct = _pick_any(
            panel, ("distinct_memories", "memories"),
            "distinct memories")
        if distinct is None:
            raise ValueError("a panel is missing its distinct memories")
        home_counts = _pick_any(
            panel, ("home_counts", "homes"), "home counts")
        if home_counts is None:
            raise ValueError("a panel is missing its home counts")
        as_of = _pick_any(panel, ("as_of", "day"), "as-of days")
        if as_of is None:
            raise ValueError("a panel is missing its as-of day")
        account = _pick_any(panel, ("account", "statements"), "accounts")
        if account is None:
            raise ValueError("a panel names no account of its own")
        kwargs: Dict[str, Any] = {
            "rows": rows, "total_postings": total,
            "total_sealed": sealed, "total_open": opened,
            "distinct_memories": distinct,
            "home_counts": home_counts,
            "as_of": as_of, "account": account}
        panel_id = _pick_any(panel, ("panel_id", "id"), "panel ids")
        if panel_id is not None:
            kwargs["panel_id"] = panel_id
        current = PrivacyPanel(**kwargs)
    else:
        raise ValueError(f"a panel must be a mapping, got {panel!r}")
    if source is not None:
        derived = derive_panel(source)
        if (current.rows != derived.rows
                or current.total_postings != derived.total_postings
                or current.total_sealed != derived.total_sealed
                or current.total_open != derived.total_open
                or current.distinct_memories != derived.distinct_memories
                or current.home_counts != derived.home_counts
                or current.as_of != derived.as_of
                or current.account != derived.account):
            raise ValueError(
                "a stored panel disagrees with the panel "
                "derived from its book")
    return current


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> PrivacyPanel:
    """Build one validated panel, from a mapping or field words."""
    if isinstance(panel, PrivacyPanel) and not kwargs:
        return validate_panel(panel, source)
    if isinstance(panel, dict) or panel is None:
        merged: Dict[str, Any] = {}
        if isinstance(panel, dict):
            merged.update(panel)
        merged.update(kwargs)
        return validate_panel(merged, source)
    return validate_panel(panel, source)


# ---------------------------------------------------------------------
# The privacy verdict: the whole book judged, as data.
# ---------------------------------------------------------------------


def _verdict_word(total_open: int) -> str:
    """The verdict word a book's own tallies derive.

    ``sealed`` while no posting in the book stands
    bridge-open - nothing syncs anywhere;
    ``guarded`` while one or two stand open at the
    user's own hand; and ``bridged`` when three
    or more of the book's memories stand open
    through bridges the user opened.
    """
    if total_open >= 3:
        return "bridged"
    if total_open >= 1:
        return "guarded"
    return "sealed"


@dataclass(frozen=True)
class PrivacyVerdict:
    """One privacy verdict: a whole book judged, as data.

    ``total_postings`` counts the book's postings;
    ``total_sealed`` counts the postings standing
    sealed and ``total_open`` the postings
    standing bridge-open - the two stand summing
    to the total; ``distinct_memories`` counts the
    stored memories posted and ``distinct_kinds``
    the holdings they stand in; ``earliest_on``
    and ``latest_on`` bound the days the postings
    were raised; ``verdict`` is the word those
    tallies derive - ``sealed`` while nothing
    stands open, ``guarded`` while one or two
    stand open at the user's own hand, and
    ``bridged`` when three or more stand open.
    """

    total_postings: int
    total_sealed: int
    total_open: int
    distinct_memories: int
    distinct_kinds: int
    earliest_on: str
    latest_on: str
    verdict: str

    def __post_init__(self) -> None:
        for field, what in (
                ("total_postings", "total postings"),
                ("total_sealed", "total sealed"),
                ("total_open", "total open"),
                ("distinct_memories", "distinct memories"),
                ("distinct_kinds", "distinct kinds")):
            object.__setattr__(
                self, field, _check_count(getattr(self, field), what))
        if self.total_sealed + self.total_open != self.total_postings:
            raise ValueError(
                "a verdict's standings must sum to its "
                "own postings' count - every posting "
                "stands sealed or bridge-open")
        if self.distinct_memories > self.total_postings:
            raise ValueError(
                "a verdict's distinct memories must not "
                "outnumber its postings")
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
        derived = _verdict_word(self.total_open)
        if word != derived:
            raise ValueError(
                f"a verdict's word must be the word its "
                f"own tallies derive ({derived!r}), got {word!r}")
        object.__setattr__(self, "verdict", word)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "private_by_architecture_verdict",
            "slice": PRIVATE_BY_ARCHITECTURE_SLICE,
            "total_postings": self.total_postings,
            "total_sealed": self.total_sealed,
            "total_open": self.total_open,
            "distinct_memories": self.distinct_memories,
            "distinct_kinds": self.distinct_kinds,
            "earliest_on": self.earliest_on,
            "latest_on": self.latest_on,
            "verdict": self.verdict,
        }


def derive_verdict(source: Any) -> PrivacyVerdict:
    """Derive the privacy verdict for one whole book."""
    postings = _held_postings(source)
    if not postings:
        raise ValueError(
            "a verdict needs at least one privacy posting")
    distinct = len({(p.memory_kind, p.memory_ref) for p in postings})
    opened = sum(1 for p in postings if standing_of(p) == "bridge-open")
    return PrivacyVerdict(
        total_postings=len(postings),
        total_sealed=len(postings) - opened,
        total_open=opened,
        distinct_memories=distinct,
        distinct_kinds=len({p.memory_kind for p in postings}),
        earliest_on=min(p.posted_on for p in postings),
        latest_on=max(p.posted_on for p in postings),
        verdict=_verdict_word(opened))


def _check_verdict_ref(value: Any) -> PrivacyVerdict:
    if isinstance(value, PrivacyVerdict):
        return value
    if isinstance(value, dict):
        return validate_verdict(value)
    raise ValueError(f"a privacy verdict is needed, got {value!r}")


def validate_verdict(verdict: Any, source: Any = None) -> PrivacyVerdict:
    """Validate one verdict into a PrivacyVerdict.

    Accepts a verdict or a mapping naming its
    tallies (short spellings read onto the
    totals), its ``earliest_on`` (or ``earliest``)
    and ``latest_on`` (or ``latest``) days and its
    ``verdict`` word. With *source* given (a
    book), the verdict is judged against the
    verdict derived from that book.
    """
    if isinstance(verdict, PrivacyVerdict):
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

        current = PrivacyVerdict(
            total_postings=_needed(
                ("total_postings", "total"), "total postings"),
            total_sealed=_needed(
                ("total_sealed", "sealed"), "total sealed"),
            total_open=_needed(
                ("total_open", "open"), "total open"),
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
                  **kwargs: Any) -> PrivacyVerdict:
    """Build one validated verdict, from a mapping or field words."""
    if isinstance(verdict, PrivacyVerdict) and not kwargs:
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict) or verdict is None:
        merged: Dict[str, Any] = {}
        if isinstance(verdict, dict):
            merged.update(verdict)
        merged.update(kwargs)
        return validate_verdict(merged, source)
    return validate_verdict(verdict, source)


# ---------------------------------------------------------------------
# The book: one book of postings, and its loaders.
# ---------------------------------------------------------------------


def _judge_postings(postings: Tuple[PrivacyPosting, ...],
                    held: Tuple[PrivacyPosting, ...] = ()) -> None:
    """Judge postings against held postings: the book's laws.

    One posting per stored memory - one memory
    kind and memory ref is posted once - so the
    memory's privacy standing never forks inside
    a book. *held* names postings already standing
    (a registry's), judged alongside.
    """
    owners: Dict[Tuple[str, str], str] = {}
    for posting in tuple(held) + tuple(postings):
        key = (posting.memory_kind, posting.memory_ref)
        if key in owners:
            raise ValueError(
                f"a memory posted twice: {key[0]} "
                f"{key[1]!r} already stands posted by "
                f"{owners[key]!r} - one posting per memory")
        owners[key] = posting.posting_id or posting.title


@dataclass(frozen=True)
class PrivacyBook:
    """One privacy book: its postings, in held order.

    ``postings`` are the privacy postings, in held
    order, each with its provenance whole, one per
    stored memory. ``panels`` are the book's
    derivations - privacy panels of the whole
    book, each judged against the book by
    :func:`validate_book`; ``canon_note`` is the
    book's own note. The total is the postings'
    own count, judged at construction.
    """

    title: str = ""
    postings: Tuple[PrivacyPosting, ...] = ()
    panels: Tuple[PrivacyPanel, ...] = ()
    canon_note: str = ""
    total_postings: Optional[int] = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_title(self.title, "a book's title"))
        if isinstance(self.postings, (str, bytes)) \
                or not isinstance(self.postings, (list, tuple)):
            raise ValueError(
                f"a book's postings must be a list of "
                f"postings, got {self.postings!r}")
        postings = tuple(_check_posting_ref(item) for item in self.postings)
        if not postings:
            raise ValueError("a privacy book holds at least one posting")
        seen_ids = set()
        for posting in postings:
            if posting.posting_id is not None:
                if posting.posting_id in seen_ids:
                    raise ValueError(
                        f"a posting named "
                        f"{posting.posting_id!r} already exists")
                seen_ids.add(posting.posting_id)
        _judge_postings(postings)
        object.__setattr__(self, "postings", postings)
        if isinstance(self.panels, (str, bytes)) \
                or not isinstance(self.panels, (list, tuple)):
            raise ValueError(
                f"a book's panels must be a list of panels, "
                f"got {self.panels!r}")
        panels = tuple(
            p if isinstance(p, PrivacyPanel)
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
        given = self.total_postings
        if given is None:
            object.__setattr__(self, "total_postings", len(postings))
        else:
            checked = _check_count(given, "a book's total postings")
            if checked != len(postings):
                raise ValueError(
                    "a book's total postings must be its "
                    "own postings' count")
            object.__setattr__(self, "total_postings", checked)

    def posting_for(self, posting_id: Any) -> PrivacyPosting:
        """The posting one id names in this book."""
        wanted = normalize_member_id(posting_id)
        for posting in self.postings:
            if posting.posting_id == wanted:
                return posting
        raise KeyError(f"no posting in the book: {wanted!r}")

    def posting_for_memory(self, memory_kind: Any, memory_ref: Any
                           ) -> PrivacyPosting:
        """The posting standing over one stored memory in this book."""
        kind = normalize_memory_kind(memory_kind)
        wanted = _check_word(memory_ref, "a memory ref")
        for posting in self.postings:
            if posting.memory_kind == kind and posting.memory_ref == wanted:
                return posting
        raise KeyError(f"no posting in the book over {kind} {wanted!r}")

    def panel_for(self, panel_id: Any) -> PrivacyPanel:
        """The stored panel one id names in this book."""
        wanted = normalize_member_id(panel_id)
        for panel in self.panels:
            if panel.panel_id == wanted:
                return panel
        raise KeyError(f"no panel in the book: {wanted!r}")

    def posting_ids(self) -> Tuple[str, ...]:
        """Every held posting id, in held order."""
        return tuple(
            item.posting_id for item in self.postings if item.posting_id)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "private_by_architecture_book",
            "slice": PRIVATE_BY_ARCHITECTURE_SLICE,
            "title": self.title,
            "posting_ids": list(self.posting_ids()),
            "posting_count": len(self.postings),
            "panel_count": len(self.panels),
        }


# The pinned example panel's account is filled in
# below, once the panel machinery stands.
_EXAMPLE_PANEL_ACCOUNT: Tuple[str, ...] = (
    "The privacy panel holds 5 postings as of "
    "2026-11-09: 4 sealed and 1 standing bridge-open "
    "over 5 stored memories: user 2, workspace 3.",
    "Rows stand by home - the workspace store "
    "first, then the user store - then title, "
    "then posting id, so two panels of one book "
    "diff cleanly, line by line.",
    "Every row shows its boundary: a sealed "
    "memory syncs nowhere, and a bridge-open "
    "memory may leave only through the one "
    "bridge the user explicitly opened over it "
    "- no posting opens a road it does not name.",
    "The panel is read off the book at call "
    "time - it is derived, never stored loose - "
    "and a posting moves nothing: no memory "
    "leaves its store by standing on this panel.",
)


def validate_book(data: Any, *, require_example: bool = False
                  ) -> PrivacyBook:
    """Validate one privacy mapping into a book.

    The mapping names a ``schema``, a ``guide``
    mapping (its ``title``), a ``postings`` list
    (or ``records``) and an optional ``panels``
    list. Every posting stands on its own
    validation, then the whole is judged: posting
    ids unique, one posting per stored memory,
    and every stored panel judged against the
    book. With ``require_example`` the shipped
    example is held to its pinned shape.
    """
    if isinstance(data, PrivacyBook):
        return data
    if not isinstance(data, dict):
        raise ValidationError(
            f"a privacy book must be a mapping, got {data!r}")
    unknown = set(data) - _PRIVACY_BOOK_KEYS
    if unknown:
        raise ValidationError(
            "unknown privacy-book keys: %s"
            % ", ".join(sorted(unknown)))
    if data.get("schema") != PRIVATE_BY_ARCHITECTURE_SCHEMA:
        raise ValidationError(
            f"a privacy book must carry schema "
            f"{PRIVATE_BY_ARCHITECTURE_SCHEMA!r}, "
            f"got {data.get('schema')!r}")
    postings = _pick_any(data, ("postings", "records"), "postings")
    if postings is None:
        raise ValidationError("a privacy book is missing its postings")
    if not isinstance(postings, (list, tuple)):
        raise ValidationError("a privacy book's postings must be a list")
    if data.get("panels") is not None \
            and not isinstance(data["panels"], (list, tuple)):
        raise ValidationError("a privacy book's panels must be a list")
    head = data.get("guide") or {}
    if not isinstance(head, dict):
        raise ValidationError("a privacy book's guide must be a mapping")
    unknown_head = set(head) - _BOOK_KEYS
    if unknown_head:
        raise ValidationError(
            "unknown guide keys: %s" % ", ".join(sorted(unknown_head)))
    try:
        title = _pick_any(head, ("title", "name"), "titles")
        if title is None:
            raise ValidationError("a privacy book is missing its title")
        note = data.get("canon_note") or ""
        if not isinstance(note, str):
            raise ValidationError("a privacy book's note must be text")
        book = PrivacyBook(
            title=title, postings=tuple(postings),
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
                "the shipped example privacy book's "
                "title is not the pinned title")
        if book.posting_ids() != _EXAMPLE_POSTING_IDS:
            raise ValidationError(
                "the shipped example's postings are not "
                "the pinned postings")
        panel = book.panel_for(_EXAMPLE_PANEL_ID)
        if panel.as_of != _EXAMPLE_AS_OF:
            raise ValidationError(
                "the shipped example panel does not stand "
                "as of its pinned day")
        if tuple(r.posting_id for r in panel.rows) != _EXAMPLE_PANEL_ROW_IDS:
            raise ValidationError(
                "the shipped example panel does not name "
                "its pinned rows in panel order")
        if _EXAMPLE_PANEL_ACCOUNT and panel.account != _EXAMPLE_PANEL_ACCOUNT:
            raise ValidationError(
                "the shipped example panel does not carry "
                "its pinned account word-for-word")
        first = book.postings[0]
        if first.posting_id != _EXAMPLE_FIRST_POSTING_ID \
                or first.title != _EXAMPLE_FIRST_POSTING_TITLE:
            raise ValidationError(
                "the shipped example's first posting is "
                "not its pinned posting of its pinned title")
    return book


def build_book(book: Any = None, **kwargs: Any) -> PrivacyBook:
    """Build one validated book, from a mapping or field words."""
    if isinstance(book, PrivacyBook) and not kwargs:
        return book
    if isinstance(book, dict):
        if "schema" in book:
            return validate_book(book)
        merged: Dict[str, Any] = dict(book)
        merged.update(kwargs)
        return PrivacyBook(**merged)
    if book is None:
        return PrivacyBook(**kwargs)
    raise ValueError(f"a privacy book is needed, got {book!r}")


def _book_from(data: Any, *, require_example: bool) -> PrivacyBook:
    try:
        return validate_book(data, require_example=require_example)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def load_private_by_architecture(
        data: Optional[Dict[str, Any]] = None) -> PrivacyBook:
    """Load and validate the shipped example book (or *data*)."""
    raw = data if data is not None else load_resource(
        PRIVATE_BY_ARCHITECTURE_RESOURCE)
    return _book_from(raw, require_example=True)


def load_private_by_architecture_file(path: Any) -> PrivacyBook:
    """Load and validate a privacy book from a file at *path*."""
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _book_from(raw, require_example=False)


# ---------------------------------------------------------------------
# The registry model: one book held posting by posting.
# ---------------------------------------------------------------------


class PrivacyRegistry:
    """One book's postings, held one by one.

    The registry holds postings, never panels or
    verdicts: the panel and the privacy verdict
    are derivations, read off the whole held book
    at call time. A whole book is judged whole -
    as a book judges it, and against everything
    already held - before its postings are held in
    book order, so a raising never lands partially.
    A posting held here stands apart: a second
    posting over a held memory refuses - one
    posting per memory.
    """

    def __init__(self, book: Any = None) -> None:
        self._title: Optional[str] = None
        self._postings: Dict[str, PrivacyPosting] = {}
        self._posting_order: list = []
        self._next_posting = 1
        if book is not None:
            self.register_book(book)

    def _fresh_posting_id(self, held_ids: Any) -> str:
        while f"posting-{self._next_posting}" in held_ids:
            self._next_posting += 1
        fresh = f"posting-{self._next_posting}"
        self._next_posting += 1
        return fresh

    def _check_standing_free(self, posting: PrivacyPosting) -> None:
        _judge_postings((posting,), held=self.list_postings())

    def register_posting(self, posting: Any) -> PrivacyPosting:
        """Register one posting into the held book."""
        validated = _check_posting_ref(posting)
        if validated.posting_id is not None \
                and validated.posting_id in self._postings:
            raise ValueError(
                f"a posting named "
                f"{validated.posting_id!r} already exists")
        self._check_standing_free(validated)
        return self._hold_posting(validated)

    def _hold_posting(self, validated: PrivacyPosting
                      ) -> PrivacyPosting:
        if validated.posting_id is None:
            from dataclasses import replace
            validated = replace(
                validated,
                posting_id=self._fresh_posting_id(set(self._postings)))
        self._postings[validated.posting_id] = validated
        self._posting_order.append(validated.posting_id)
        return validated

    def register_book(self, book: Any) -> PrivacyBook:
        """Register every posting of one book, in order.

        The book is judged whole, and against the
        held book, before any of its postings is
        held: a refusal holds nothing new.
        """
        validated = build_book(book)
        if self._title is not None and validated.title != self._title:
            raise ValueError(
                "this registry already holds a privacy "
                "book under a different title")
        for posting in validated.postings:
            if posting.posting_id in self._postings:
                raise ValueError(
                    f"a posting named "
                    f"{posting.posting_id!r} already exists")
        _judge_postings(validated.postings, held=self.list_postings())
        self._title = validated.title
        for posting in validated.postings:
            self._hold_posting(posting)
        return self.book()

    def get_posting(self, posting_id: Any) -> PrivacyPosting:
        """The posting one id names among the held postings."""
        wanted = normalize_member_id(posting_id)
        if wanted not in self._postings:
            raise KeyError(f"unknown posting: {wanted!r}")
        return self._postings[wanted]

    def posting_for_memory(self, memory_kind: Any, memory_ref: Any
                           ) -> PrivacyPosting:
        """The held posting standing over one stored memory."""
        kind = normalize_memory_kind(memory_kind)
        wanted = _check_word(memory_ref, "a memory ref")
        for posting_id in self._posting_order:
            posting = self._postings[posting_id]
            if posting.memory_kind == kind and posting.memory_ref == wanted:
                return posting
        raise KeyError(f"no posting held over {kind} {wanted!r}")

    def latest_posting(self) -> PrivacyPosting:
        """The most recently held posting."""
        if not self._posting_order:
            raise ValueError("no posting is held yet")
        return self._postings[self._posting_order[-1]]

    def list_postings(self) -> Tuple[PrivacyPosting, ...]:
        """Every held posting, in the order they were held."""
        return tuple(self._postings[item] for item in self._posting_order)

    def book(self) -> PrivacyBook:
        """The held postings as one validated book."""
        if self._title is None:
            raise ValueError("no privacy book is held yet")
        return PrivacyBook(
            title=self._title, postings=self.list_postings())

    def panel(self) -> PrivacyPanel:
        """Derive the privacy panel of the whole held book."""
        return derive_panel(self)

    def verdict(self) -> PrivacyVerdict:
        """Derive the privacy verdict of the whole held book."""
        return derive_verdict(self)


# ---------------------------------------------------------------------
# The visible surface: how the book stands, read off any book.
# ---------------------------------------------------------------------


def posting_refs(source: Any) -> Tuple[Tuple[str, str], ...]:
    """Every (memory kind, memory ref) one source's postings name."""
    return tuple(
        (posting.memory_kind, posting.memory_ref)
        for posting in _held_postings(source))


def posting_for(source: Any, memory_kind: Any, memory_ref: Any
                ) -> PrivacyPosting:
    """The posting one source holds over one stored memory."""
    kind = normalize_memory_kind(memory_kind)
    wanted = _check_word(memory_ref, "a memory ref")
    for posting in _held_postings(source):
        if posting.memory_kind == kind and posting.memory_ref == wanted:
            return posting
    raise KeyError(f"no posting over {kind} {wanted!r}")


def total_postings(source: Any) -> int:
    """How many postings one source holds."""
    return len(_held_postings(source))


def posting_record(posting: Any) -> Dict[str, Any]:
    """The session-news record of one privacy posting."""
    current = posting if isinstance(posting, PrivacyPosting) \
        else build_posting(posting)
    record = current.to_record()
    record["news"] = True
    if current.bridge == SEALED_BRIDGE:
        record["headline"] = (
            f"Privacy over {current.memory_kind} "
            f"{current.memory_ref}: sealed in the "
            f"{current.home} store - it syncs nowhere.")
    else:
        record["headline"] = (
            f"Privacy over {current.memory_kind} "
            f"{current.memory_ref}: bridge-open in the "
            f"{current.home} store - it may leave only "
            f"through the {current.bridge} bridge, "
            f"opened by {current.opened_by} on "
            f"{current.opened_on}.")
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
        f"Privacy panel as of {current.as_of}: "
        f"{current.total_postings} postings - "
        f"{current.total_sealed} sealed, "
        f"{current.total_open} bridge-open over "
        f"{current.distinct_memories} stored "
        f"memories.")
    return record


def verdict_record(verdict: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of one derived verdict."""
    current = validate_verdict(verdict, source)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Privacy verdict: {current.verdict} - "
        f"{current.total_sealed} of "
        f"{current.total_postings} postings sealed, "
        f"{current.total_open} standing bridge-open, "
        f"from {current.earliest_on} to "
        f"{current.latest_on}.")
    return record


def book_record(book: Any) -> Dict[str, Any]:
    """The session-news record of one privacy book."""
    current = book if isinstance(book, PrivacyBook) \
        else build_book(book)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Privacy book {current.title}: "
        f"{record['posting_count']} postings named.")
    return record


def plain_words(posting: Any) -> str:
    """One posting, in one plain sentence."""
    current = posting if isinstance(posting, PrivacyPosting) \
        else build_posting(posting)
    if current.bridge == SEALED_BRIDGE:
        return (
            f"{current.title} - the {current.memory_kind} "
            f"memory {current.memory_ref} lives in the "
            f"{current.home} store, sealed: no bridge "
            f"stands open over it, and it syncs nowhere.")
    return (
        f"{current.title} - the {current.memory_kind} "
        f"memory {current.memory_ref} lives in the "
        f"{current.home} store, bridge-open through "
        f"the {current.bridge} bridge alone, opened "
        f"by {current.opened_by} on {current.opened_on} "
        f"- every other road stays shut.")


def panel_plain_words(source: Any) -> str:
    """The panel in plain words, in full.

    Accepts a PrivacyPanel or a book (whose panel
    is derived). The panel is told whole - its
    rows in panel order and its account.
    """
    if isinstance(source, PrivacyPanel):
        panel = validate_panel(source)
        title = None
    elif isinstance(source, (PrivacyBook, PrivacyRegistry)):
        panel = derive_panel(source)
        title = source.title if isinstance(
            source, PrivacyBook) else None
    else:
        raise ValueError(
            f"a privacy source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    lines.append("Boundaries, in panel order:")
    for row in panel.rows:
        lines.append(
            f"{row.posting_id}: {row.memory_kind}/"
            f"{row.memory_ref} - home: {row.home} "
            f"store, bridge: {row.bridge} "
            f"(standing: {row.standing}, posted {row.posted_on})")
    lines.extend(panel.account)
    return "\n".join(lines)


def verdict_plain_words(source: Any) -> str:
    """The privacy verdict in plain words, in full."""
    if isinstance(source, PrivacyVerdict):
        verdict = validate_verdict(source)
    elif isinstance(source, (PrivacyBook, PrivacyRegistry)):
        verdict = derive_verdict(source)
    else:
        raise ValueError(
            f"a privacy source is needed, got {source!r}")
    return (
        f"Privacy verdict: {verdict.verdict} - "
        f"{verdict.total_sealed} postings sealed and "
        f"{verdict.total_open} standing bridge-open "
        f"over {verdict.distinct_memories} stored "
        f"memories in {verdict.distinct_kinds} "
        f"holdings, posted from {verdict.earliest_on} "
        f"to {verdict.latest_on}, of "
        f"{verdict.total_postings} postings - nothing "
        f"syncs anywhere except through a bridge the "
        f"user explicitly opened.")


def _source_book(source: Any) -> PrivacyBook:
    if source is None:
        return load_private_by_architecture()
    if isinstance(source, PrivacyRegistry):
        return source.book()
    if isinstance(source, PrivacyBook):
        return source
    if isinstance(source, PrivacyPosting):
        return PrivacyBook(
            title="One privacy posting", postings=(source,))
    raise ValueError(
        f"a privacy book is needed, got {source!r}")


def format_posting(posting: Any) -> str:
    """One posting as a screen block, its boundary shown."""
    current = posting if isinstance(posting, PrivacyPosting) \
        else build_posting(posting)
    lines = [
        f"{current.posting_id or '-'}: {current.title} - "
        f"over {current.memory_kind} {current.memory_ref} "
        f"(read from {current.source})",
        f"Home: the {current.home} store "
        f"(posted {current.posted_on} by "
        f"{current.recorded_by} in "
        f"{current.origin_session})",
    ]
    if current.bridge == SEALED_BRIDGE:
        lines.append(
            "Bridge: none stands open - this memory "
            "syncs nowhere.")
    else:
        lines.append(
            f"Bridge: {current.bridge}, opened by "
            f"{current.opened_by} on {current.opened_on} "
            f"- the one road out the user opened.")
    lines.append(
        f"The boundary stands: {boundary_line(current)}")
    return "\n".join(lines)


def format_postings(source: Any = None, kind: Any = None,
                    home: Any = None) -> str:
    """Postings of one book, in held order, optionally filtered.

    With *kind* named, only the postings standing
    over that holding show; with *home* named,
    only the postings living in that store show.
    """
    book = _source_book(source)
    wanted_kind = normalize_memory_kind(kind) if kind is not None else None
    wanted_home = normalize_home(home) if home is not None else None
    lines = [
        f"{posting.posting_id or '-'}: {posting.title} - "
        f"{posting.memory_kind} {posting.memory_ref}: "
        f"home: {posting.home} store, bridge: "
        f"{posting.bridge} (standing: "
        f"{standing_of(posting)}, posted {posting.posted_on})"
        for posting in book.postings
        if (wanted_kind is None or posting.memory_kind == wanted_kind)
        and (wanted_home is None or posting.home == wanted_home)]
    if not lines:
        lines.append("No postings stand in the book on that reading.")
    return "\n".join(lines)


def format_panel(source: Any = None) -> str:
    """The panel as a screen block: every row and the account.

    Accepts a PrivacyPanel or a book; a book shows
    the panel derived from it.
    """
    if isinstance(source, PrivacyPanel):
        panel = validate_panel(source)
        lines: list = []
    else:
        book = _source_book(source)
        panel = derive_panel(book)
        lines = [f"Panel in {book.title}:"]
    lines.append("Boundaries, in panel order:")
    for row in panel.rows:
        lines.append(
            f"{row.posting_id}: {row.memory_kind}/"
            f"{row.memory_ref} - home: {row.home} "
            f"store, bridge: {row.bridge} "
            f"(standing: {row.standing}, posted {row.posted_on})")
    lines.extend(panel.account)
    return "\n".join(lines)


def format_verdict(source: Any = None) -> str:
    """The privacy verdict as a screen block."""
    if isinstance(source, PrivacyVerdict):
        verdict = validate_verdict(source)
        lines: list = []
    else:
        book = _source_book(source)
        verdict = derive_verdict(book)
        lines = [f"Verdict in {book.title}:"]
    lines.append(
        f"{verdict.verdict}: {verdict.total_sealed} "
        f"postings sealed and {verdict.total_open} "
        f"standing bridge-open over "
        f"{verdict.distinct_memories} stored memories "
        f"in {verdict.distinct_kinds} holdings, "
        f"posted from {verdict.earliest_on} to "
        f"{verdict.latest_on}, of "
        f"{verdict.total_postings} postings. Nothing "
        f"syncs anywhere except through a bridge the "
        f"user explicitly opened, and no memory "
        f"leaves its store by standing in this book.")
    return "\n".join(lines)


def format_privacy_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /private.

    With nothing named, the shipped example
    privacy book is shown - the example this slice
    ships - so the screen is never empty.
    """
    book = _source_book(source)
    lines = ["Private by Architecture (M-167) - " + PLAIN_EXPLANATION, ""]
    for posting in book.postings:
        lines.append(format_posting(posting))
    lines.append("")
    lines.append(format_panel(book))
    lines.append("")
    lines.append(format_verdict(book))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_privacy_args(args: Any) -> Tuple[str, Any]:
    """Parse the /private grammar both surfaces share.

    No words (or ``show`` / ``list``) shows the
    privacy book; ``posting <posting-id>`` shows
    one posting with its boundary shown; ``kind
    <memory-kind>`` shows the postings standing
    over one holding; ``home <home>`` shows the
    postings living in one store; ``panel`` shows
    the panel derived from the whole book;
    ``verdict`` shows the privacy verdict derived
    for the whole book. Anything else is a usage
    error naming the grammar. Returns
    ``(action, value-or-None)``.
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
    if head == "posting" and len(words) == 2:
        try:
            return (head, normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "kind" and len(words) == 2:
        try:
            return (head, normalize_memory_kind(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "home" and len(words) == 2:
        try:
            return (head, normalize_home(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
