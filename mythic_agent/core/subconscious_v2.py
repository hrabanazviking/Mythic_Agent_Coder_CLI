"""The subconscious v2 (All-Features roadmap slice M-165).

Part VII continues. The roadmap's words:
``the dual-layer vector memory gains provenance
(where each memory came from), confidence, and
decay - stale memories fade unless re-earned.``

What already ships, and what this slice adds:

* The dual-layer memory itself already ships:
  the vector RAG subconscious
  (``memory/vector_db.py``) searches archived
  text by embedding, married to graph retrieval
  (M-146), and the core memory ships as data on
  shipped roads - the project memory map
  (``core/project_memory_map.py``, M-150), session
  memory across days (``core/session_memory.py``,
  M-153), cross-project memory
  (``core/cross_project_memory.py``, M-154), the
  self-improving ledger
  (``core/self_improving_ledger.py``, M-155) and
  crew memory (``core/crew_memory.py``, M-133).
  What none of those layers holds is the v2
  account of a memory itself: where it came from,
  how far it is trusted, and how far it has faded
  since it was last earned.
* This slice is that account, as a pure layer:
  one subconscious memory record validated as
  data WITH ITS PROVENANCE WHOLE - the layer it
  stands in (``core`` or ``subconscious``, the
  dual layers themselves), where it came from
  (its source kind and the shipped piece it
  names, by id alone), the session it was earned
  in and the day, who recorded it and where it
  was read from - its CONFIDENCE (how far the
  memory is trusted, from 0 to 1), and its DECAY
  (a half-life in days and the day it was last
  earned or re-earned, with its re-earn count):
  a memory's effective confidence halves every
  half-life since it was last earned, so a stale
  memory fades - fresh, fading, stale, faded -
  unless it is re-earned, and re-earning resets
  the decay clock without inflating the trust
  the memory was earned with. Memories are
  composed BY IMPORT from the shipped layers
  they extend (a map entry, a session note, a
  ledger candidate, a crew fact, a cross-project
  lesson, a vector record), each judged by its
  own layer's validation, ids and refs only
  across the seams. The shipped data file
  (``mythic_agent/data/subconscious_v2.yaml``)
  holds one example book in exactly the shape a
  real book file takes, a loader reads a book
  file anywhere on disk, the subconscious panel
  is DERIVED from the whole book as of a day
  (every memory carried whole, in a settled
  order, with its effective confidence and
  freshness read off its own decay), a freshness
  VERDICT is derived for the whole book, memories
  are shaped as session news, and a small
  in-memory registry model holds memories one by
  one. The agent layer owns holding a book for a
  session, harvesting the session's holdings onto
  v2 memories, and re-earning a held memory.

Honesty rules, enforced here and pinned by tests:

* **Provenance whole, ids only across the seam.**
  A v2 memory names where it came from - kind,
  the shipped piece's id, the session and day it
  was earned, who recorded it, where it was read
  from - and nothing else of the piece crosses:
  the piece's own words stay in its own layer,
  judged by its own layer's validator.
* **Decay is derived, never stored.** A memory
  stores the confidence it was earned with, its
  half-life and its last-earned day; its
  effective confidence and freshness are read
  off those at call time, as of a named day. A
  stored panel or verdict that disagrees with
  the derived shape refuses.
* **Faded unless re-earned.** Re-earning is the
  only road back: it moves the last-earned day
  and counts the re-earn, and it never raises
  the stored confidence - a re-earned memory is
  fresh again at exactly the trust it was earned
  with, no more.
* **One earning per piece.** A shipped piece is
  earned into a book once: one memory per source
  kind and source ref stands in a book, so
  provenance never forks.
* **Data only.** This layer holds memories as
  data: it sends nothing, posts nothing,
  schedules nothing, calls no model, persists
  nothing and writes no live memory - earning a
  v2 memory changes no shipped holding.
"""

from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..resources import load_resource
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
from .validation import ValidationError

__all__ = [
    "SUBCONSCIOUS_V2_RESOURCE",
    "SUBCONSCIOUS_V2_SCHEMA",
    "SUBCONSCIOUS_V2_SLICE",
    "PLAIN_EXPLANATION",
    "MEMORY_LAYERS",
    "SOURCE_KINDS",
    "FRESHNESS_STATES",
    "VERDICT_WORDS",
    "USAGE",
    "FreshnessVerdict",
    "StateCount",
    "SubconsciousBook",
    "SubconsciousMemory",
    "SubconsciousPanel",
    "SubconsciousPanelRow",
    "SubconsciousRegistry",
    "age_days",
    "book_record",
    "build_book",
    "build_memory",
    "build_panel",
    "build_verdict",
    "derive_panel",
    "derive_verdict",
    "effective_confidence",
    "format_memories",
    "format_memory",
    "format_panel",
    "format_subconscious_screen",
    "format_verdict",
    "freshness_state",
    "inspect_memory_source",
    "load_subconscious_v2",
    "load_subconscious_v2_file",
    "memories_from_crew_memory",
    "memories_from_cross_project",
    "memories_from_ledger",
    "memories_from_memory_map",
    "memories_from_session_memory",
    "memory_from_crew_entry",
    "memory_from_cross_project_lesson",
    "memory_from_ledger_candidate",
    "memory_from_map_entry",
    "memory_from_session_note",
    "memory_from_vector_record",
    "memory_record",
    "memory_refs",
    "normalize_freshness_state",
    "normalize_memory_layer",
    "normalize_source_kind",
    "panel_plain_words",
    "panel_record",
    "parse_subconscious_args",
    "plain_words",
    "reearn_memory",
    "total_memories",
    "validate_book",
    "validate_memory",
    "validate_panel",
    "validate_verdict",
    "verdict_plain_words",
    "verdict_record",
]

SUBCONSCIOUS_V2_SLICE = "M-165"

SUBCONSCIOUS_V2_RESOURCE = "subconscious_v2.yaml"

SUBCONSCIOUS_V2_SCHEMA = "mythic.subconscious_v2/1"

#: The dual layers a memory stands in: the
#: deliberate core memory and the vector RAG
#: subconscious beneath it.
MEMORY_LAYERS = ("core", "subconscious")

_LAYER_ALIASES = {
    "core": "core",
    "core-memory": "core",
    "core_memory": "core",
    "subconscious": "subconscious",
    "vector": "subconscious",
    "vector-rag": "subconscious",
    "rag": "subconscious",
}

#: Where a memory came from: the shipped layers a
#: v2 memory's provenance may name.
SOURCE_KINDS = (
    "memory-map", "session-note", "ledger-candidate",
    "crew-fact", "cross-project-lesson", "vector-record",
    "manual")

_SOURCE_KIND_ALIASES = {
    "memory-map": "memory-map",
    "memory_map": "memory-map",
    "map": "memory-map",
    "map-entry": "memory-map",
    "session-note": "session-note",
    "session_note": "session-note",
    "note": "session-note",
    "ledger-candidate": "ledger-candidate",
    "ledger_candidate": "ledger-candidate",
    "ledger": "ledger-candidate",
    "candidate": "ledger-candidate",
    "crew-fact": "crew-fact",
    "crew_fact": "crew-fact",
    "crew": "crew-fact",
    "crew-entry": "crew-fact",
    "cross-project-lesson": "cross-project-lesson",
    "cross_project_lesson": "cross-project-lesson",
    "cross-project": "cross-project-lesson",
    "lesson": "cross-project-lesson",
    "vector-record": "vector-record",
    "vector_record": "vector-record",
    "vector": "vector-record",
    "manual": "manual",
    "by-hand": "manual",
}

#: How far a memory has faded, freshest first.
FRESHNESS_STATES = ("fresh", "fading", "stale", "faded")

_FRESHNESS_ALIASES = {
    "fresh": "fresh",
    "fading": "fading",
    "faded-away": "faded",
    "stale": "stale",
    "faded": "faded",
    "gone": "faded",
}

#: The words a whole book's freshness verdict
#: may carry, best kept first.
VERDICT_WORDS = ("well-kept", "fading", "going-stale", "neglected")

_MEMORY_KEYS = frozenset({
    "memory_id", "id", "title", "name", "subject",
    "layer", "source_kind", "kind", "source_ref", "ref",
    "origin_session", "session",
    "earned_on", "day", "date",
    "recorded_by", "recorder", "by", "who",
    "source", "confidence", "trust",
    "half_life_days", "half_life",
    "last_earned_on", "last_earned", "reearned_on",
    "reearn_count", "reearns",
})

_ROW_KEYS = frozenset({
    "memory_id", "id", "title", "layer",
    "source_kind", "source_ref",
    "confidence", "effective_confidence", "effective",
    "freshness", "state", "age_days", "age",
    "reearn_count", "reearns",
})

_STATE_COUNT_KEYS = frozenset({"state", "items", "count"})

_PANEL_KEYS = frozenset({
    "panel_id", "id", "rows", "memories",
    "total_memories", "total",
    "total_core", "core", "total_subconscious", "subconscious",
    "total_reearned", "reearned",
    "state_counts", "states", "as_of", "day",
    "account", "statements",
})

_VERDICT_KEYS = frozenset({
    "total_memories", "total",
    "total_fresh", "fresh", "total_fading", "fading",
    "total_stale", "stale", "total_faded", "faded",
    "total_core", "core", "total_subconscious", "subconscious",
    "distinct_sources", "sources", "as_of", "day", "verdict",
})

_BOOK_KEYS = frozenset({"title", "name"})

_SUBCONSCIOUS_BOOK_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "canon_note", "guide", "memories", "records", "panels",
})

_EXAMPLE_TITLE = "The subconscious v2 at the M-164 slice boundary"

_EXAMPLE_MEMORY_IDS = (
    "memory-no-docker-law", "memory-commit-before-answer",
    "memory-suite-extras", "memory-samtal-wal",
    "memory-reap-at-bank", "memory-two-roads")

_EXAMPLE_FIRST_MEMORY_ID = "memory-no-docker-law"

_EXAMPLE_FIRST_MEMORY_TITLE = (
    "no Docker ever, earned from the memory map")

_EXAMPLE_PANEL_ID = "panel-m164-boundary"

_EXAMPLE_AS_OF = "2026-11-09"

_EXAMPLE_PANEL_ROW_IDS = (
    "memory-commit-before-answer", "memory-no-docker-law",
    "memory-suite-extras", "memory-reap-at-bank",
    "memory-samtal-wal", "memory-two-roads")

PLAIN_EXPLANATION = (
    "The subconscious v2: the dual-layer vector "
    "memory gains provenance (where each memory "
    "came from), confidence, and decay - stale "
    "memories fade unless re-earned. A v2 memory "
    "stands in one of the dual layers, core or "
    "subconscious, and carries its provenance "
    "whole: the shipped piece it came from, by id "
    "alone, the session and day it was earned, who "
    "recorded it and where it was read from. Its "
    "confidence is the trust it was earned with; "
    "its effective confidence halves every "
    "half-life in days since it was last earned, "
    "so it stands fresh, fading, stale or faded "
    "as of any named day, and re-earning it resets "
    "the decay clock at the same trust - it never "
    "inflates it. The subconscious panel is "
    "derived from the book at call time, and the "
    "freshness verdict is derived for the whole "
    "book. This layer holds memories as data "
    "only: it sends nothing, posts nothing, "
    "schedules nothing, calls no model, persists "
    "nothing and writes no live memory."
)

USAGE = (
    "Usage: /subconscious, /subconscious show, "
    "/subconscious memory <memory-id>, "
    "/subconscious layer <core|subconscious>, "
    "/subconscious source <source-kind>, "
    "/subconscious panel, /subconscious verdict"
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


def _day_of(text: str) -> date:
    return date.fromisoformat(text)


def _check_confidence(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(
            f"a memory's confidence must be a number "
            f"from 0 to 1, got {value!r}")
    number = float(value)
    if number != number or number < 0.0 or number > 1.0:
        raise ValueError(
            f"a memory's confidence must be a number "
            f"from 0 to 1, got {value!r}")
    return number


def _check_half_life(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(
            f"a memory's half-life must be a whole "
            f"number of days, got {value!r}")
    if value < 1 or value > 3650:
        raise ValueError(
            f"a memory's half-life must stand between "
            f"1 and 3650 days, got {value!r}")
    return value


def normalize_memory_layer(value: Any) -> str:
    """The canonical layer a word names.

    A layer is one of :data:`MEMORY_LAYERS` -
    ``core`` (the deliberate core memory) or
    ``subconscious`` (the vector RAG subconscious),
    read case-insensitively, with ``vector`` and
    ``rag`` read onto ``subconscious``. Anything
    else raises, plainly naming the two.
    """
    if isinstance(value, str):
        wanted = _LAYER_ALIASES.get(value.strip().lower())
        if wanted is not None:
            return wanted
    raise ValueError(
        "a memory layer must be one of %s, got %r"
        % ("/".join(MEMORY_LAYERS), value))


def normalize_source_kind(value: Any) -> str:
    """The canonical source kind a word names.

    A source kind is one of :data:`SOURCE_KINDS` -
    where a memory came from - read
    case-insensitively, with short spellings
    (``map``, ``note``, ``ledger``, ``crew``,
    ``lesson``, ``vector``) read onto their kinds.
    Anything else raises, plainly naming the set.
    """
    if isinstance(value, str):
        wanted = _SOURCE_KIND_ALIASES.get(value.strip().lower())
        if wanted is not None:
            return wanted
    raise ValueError(
        "a source kind must be one of %s, got %r"
        % ("/".join(SOURCE_KINDS), value))


def normalize_freshness_state(value: Any) -> str:
    """The canonical freshness state a word names.

    A state is one of :data:`FRESHNESS_STATES` -
    ``fresh``, ``fading``, ``stale`` or ``faded`` -
    read case-insensitively. Anything else raises,
    plainly naming the four.
    """
    if isinstance(value, str):
        wanted = _FRESHNESS_ALIASES.get(value.strip().lower())
        if wanted is not None:
            return wanted
    raise ValueError(
        "a freshness state must be one of %s, got %r"
        % ("/".join(FRESHNESS_STATES), value))


# ---------------------------------------------------------------------
# The subconscious memory: provenance, confidence and decay, as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class SubconsciousMemory:
    """One memory of the dual-layer memory, at v2.

    ``title`` names the memory in plain words;
    ``layer`` is the dual layer it stands in -
    ``core`` or ``subconscious``. The provenance
    stands whole beside it: ``source_kind`` names
    where it came from and ``source_ref`` the
    shipped piece it came from, by id alone;
    ``origin_session`` names the session it was
    earned in, ``earned_on`` the day, ``recorded_by``
    who recorded it and ``source`` where it was
    read from. ``confidence`` is the trust it was
    earned with, from 0 to 1. Its decay stands
    beside that: ``half_life_days`` is how fast it
    fades, ``last_earned_on`` the day it was last
    earned or re-earned (never before the day it
    was earned), and ``reearn_count`` how many
    times it has been re-earned. The effective
    confidence and freshness are never stored -
    they are derived from these fields as of a
    named day.
    """

    title: str
    layer: str
    source_kind: str
    source_ref: str
    origin_session: str
    earned_on: str
    recorded_by: str
    source: str
    confidence: float
    half_life_days: int = 30
    last_earned_on: Optional[str] = None
    reearn_count: int = 0
    memory_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.memory_id is not None:
            object.__setattr__(
                self, "memory_id", normalize_member_id(self.memory_id))
        object.__setattr__(
            self, "title", _check_title(self.title, "a memory's title"))
        object.__setattr__(
            self, "layer", normalize_memory_layer(self.layer))
        object.__setattr__(
            self, "source_kind", normalize_source_kind(self.source_kind))
        object.__setattr__(
            self, "source_ref",
            _check_word(self.source_ref, "a memory's source ref"))
        object.__setattr__(
            self, "origin_session",
            _check_word(self.origin_session, "a memory's origin session"))
        earned = _check_day(self.earned_on, "a memory's earned-on day")
        object.__setattr__(self, "earned_on", earned)
        object.__setattr__(
            self, "recorded_by",
            _check_title(self.recorded_by, "a memory's recorder"))
        object.__setattr__(
            self, "source",
            _check_title(self.source, "a memory's source"))
        object.__setattr__(
            self, "confidence", _check_confidence(self.confidence))
        object.__setattr__(
            self, "half_life_days", _check_half_life(self.half_life_days))
        last = self.last_earned_on
        if last is None:
            last = earned
        last = _check_day(last, "a memory's last-earned day")
        if _day_of(last) < _day_of(earned):
            raise ValueError(
                "a memory's last-earned day must not "
                "stand before the day it was earned")
        object.__setattr__(self, "last_earned_on", last)
        object.__setattr__(
            self, "reearn_count",
            _check_count(self.reearn_count, "a memory's re-earn count"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "subconscious_v2_memory",
            "slice": SUBCONSCIOUS_V2_SLICE,
            "memory_id": self.memory_id,
            "title": self.title,
            "layer": self.layer,
            "source_kind": self.source_kind,
            "source_ref": self.source_ref,
            "origin_session": self.origin_session,
            "earned_on": self.earned_on,
            "recorded_by": self.recorded_by,
            "source": self.source,
            "confidence": self.confidence,
            "half_life_days": self.half_life_days,
            "last_earned_on": self.last_earned_on,
            "reearn_count": self.reearn_count,
        }


def _check_memory_ref(value: Any) -> SubconsciousMemory:
    if isinstance(value, SubconsciousMemory):
        return value
    if isinstance(value, dict):
        return validate_memory(value)
    raise ValueError(f"a subconscious memory is needed, got {value!r}")


def validate_memory(memory: Any) -> SubconsciousMemory:
    """Validate one memory into a SubconsciousMemory.

    Accepts a memory or a mapping naming a ``title``
    (or ``name`` / ``subject``), a ``layer``, a
    ``source_kind`` (or ``kind``), a ``source_ref``
    (or ``ref``), an ``origin_session`` (or
    ``session``), an ``earned_on`` (or ``day`` /
    ``date``), a ``recorded_by`` (or ``recorder`` /
    ``by`` / ``who``), a ``source``, a
    ``confidence`` (or ``trust``) and, optionally, a
    ``half_life_days`` (or ``half_life``), a
    ``last_earned_on`` (or ``last_earned`` /
    ``reearned_on``), a ``reearn_count`` (or
    ``reearns``) and a ``memory_id`` (or ``id``).
    Naming two spellings of one field with
    different values refuses, and unknown keys
    refuse.
    """
    if isinstance(memory, SubconsciousMemory):
        return memory
    if not isinstance(memory, dict):
        raise ValueError(f"a subconscious memory is needed, got {memory!r}")
    unknown = set(memory) - _MEMORY_KEYS
    if unknown:
        raise ValueError(
            "unknown memory keys: %s" % ", ".join(sorted(unknown)))

    def _needed(spellings: Tuple[str, ...], what: str) -> Any:
        value = _pick_any(memory, spellings, what)
        if value is None:
            raise ValueError(f"a memory is missing its {what}")
        return value

    kwargs: Dict[str, Any] = {
        "title": _needed(("title", "name", "subject"), "title"),
        "layer": _needed(("layer",), "layer"),
        "source_kind": _needed(("source_kind", "kind"), "source kind"),
        "source_ref": _needed(("source_ref", "ref"), "source ref"),
        "origin_session": _needed(
            ("origin_session", "session"), "origin session"),
        "earned_on": _needed(("earned_on", "day", "date"), "earned day"),
        "recorded_by": _needed(
            ("recorded_by", "recorder", "by", "who"), "recorder"),
        "source": _needed(("source",), "source"),
        "confidence": _needed(("confidence", "trust"), "confidence"),
    }
    half_life = _pick_any(
        memory, ("half_life_days", "half_life"), "half-lives")
    if half_life is not None:
        kwargs["half_life_days"] = half_life
    last = _pick_any(
        memory, ("last_earned_on", "last_earned", "reearned_on"),
        "last-earned days")
    if last is not None:
        kwargs["last_earned_on"] = last
    reearns = _pick_any(
        memory, ("reearn_count", "reearns"), "re-earn counts")
    if reearns is not None:
        kwargs["reearn_count"] = reearns
    memory_id = _pick_any(memory, ("memory_id", "id"), "memory ids")
    if memory_id is not None:
        kwargs["memory_id"] = memory_id
    return SubconsciousMemory(**kwargs)


def build_memory(memory: Any = None, **kwargs: Any) -> SubconsciousMemory:
    """Build one validated memory, from a mapping or field words."""
    if isinstance(memory, SubconsciousMemory) and not kwargs:
        return memory
    if isinstance(memory, dict) or memory is None:
        merged: Dict[str, Any] = {}
        if isinstance(memory, dict):
            merged.update(memory)
        merged.update(kwargs)
        return validate_memory(merged)
    raise ValueError(f"a subconscious memory is needed, got {memory!r}")


# ---------------------------------------------------------------------
# Decay: effective confidence and freshness, derived as of a day.
# ---------------------------------------------------------------------


def age_days(memory: Any, as_of: Any) -> int:
    """How many days stand between a memory's last earning and *as_of*."""
    current = _check_memory_ref(memory)
    day = _check_day(as_of, "an as-of day")
    age = (_day_of(day) - _day_of(current.last_earned_on)).days
    if age < 0:
        raise ValueError(
            "a memory cannot be judged before the day "
            "it was last earned")
    return age


def effective_confidence(memory: Any, as_of: Any) -> float:
    """A memory's confidence as of a day, decayed by its half-life.

    The trust a memory was earned with, halved once
    per half-life since the day it was last earned
    or re-earned, rounded to four places so two
    readings of one memory on one day agree exactly.
    """
    current = _check_memory_ref(memory)
    age = age_days(current, as_of)
    decayed = current.confidence * (0.5 ** (age / current.half_life_days))
    return round(decayed, 4)


def freshness_state(memory: Any, as_of: Any) -> str:
    """How far a memory has faded as of a day.

    ``fresh`` at an effective confidence of 0.6 or
    more, ``fading`` at 0.3 or more, ``stale`` at
    0.1 or more, and ``faded`` below that - a faded
    memory stands in the book still, named plainly
    as faded, until it is re-earned.
    """
    effective = effective_confidence(memory, as_of)
    if effective >= 0.6:
        return "fresh"
    if effective >= 0.3:
        return "fading"
    if effective >= 0.1:
        return "stale"
    return "faded"


def reearn_memory(memory: Any, *, on: Any) -> SubconsciousMemory:
    """Re-earn one memory as of a day: the decay clock resets.

    The returned memory is the same memory - same
    provenance, same confidence it was earned with,
    same half-life - with its last-earned day moved
    to *on* and its re-earn count grown by one.
    Re-earning never raises the stored confidence:
    a re-earned memory is fresh again at exactly
    the trust it was earned with. A day before the
    memory's last earning refuses.
    """
    current = _check_memory_ref(memory)
    day = _check_day(on, "a re-earn day")
    if _day_of(day) < _day_of(current.last_earned_on):
        raise ValueError(
            "a memory cannot be re-earned before the "
            "day it was last earned")
    return replace(
        current, last_earned_on=day,
        reearn_count=current.reearn_count + 1)


# ---------------------------------------------------------------------
# Composition: shipped holdings read onto v2 memories, by import.
# ---------------------------------------------------------------------


def _earned_memory(*, source_kind: str, source_ref: Optional[str],
                   piece_word: str, layer: Any, title: Any,
                   origin_session: Any, earned_on: Any,
                   recorded_by: Any, source: Any,
                   confidence: Any, half_life_days: Any,
                   memory_id: Any) -> SubconsciousMemory:
    if source_ref is None:
        raise ValueError(
            f"a {piece_word} with no id cannot be earned "
            f"into the subconscious - a v2 memory carries "
            f"its provenance by id")
    return SubconsciousMemory(
        title=title if title is not None else (
            f"{source_kind} memory {source_ref}"),
        layer=layer, source_kind=source_kind, source_ref=source_ref,
        origin_session=origin_session, earned_on=earned_on,
        recorded_by=recorded_by, source=source,
        confidence=confidence, half_life_days=half_life_days,
        memory_id=memory_id if memory_id is not None else (
            f"memory-{source_ref}"))


def memory_from_map_entry(entry: Any, *, origin_session: Any,
                          earned_on: Any, recorded_by: Any,
                          source: Any = "project memory map",
                          layer: Any = "core", title: Any = None,
                          confidence: Any = 0.9, half_life_days: Any = 30,
                          memory_id: Any = None) -> SubconsciousMemory:
    """Earn one project memory-map entry into v2, by import.

    The entry (M-150) is judged by the map's own
    ``validate_entry``; only its id crosses - it
    stands as the memory's source ref, of kind
    ``memory-map``, in the core layer by default.
    The entry's own title, detail and reference are
    never read here.
    """
    checked = _validate_map_entry(entry)
    return _earned_memory(
        source_kind="memory-map", source_ref=checked.entry_id,
        piece_word="memory map entry", layer=layer, title=title,
        origin_session=origin_session, earned_on=earned_on,
        recorded_by=recorded_by, source=source,
        confidence=confidence, half_life_days=half_life_days,
        memory_id=memory_id)


def memory_from_session_note(note: Any, *, origin_session: Any,
                             earned_on: Any, recorded_by: Any,
                             source: Any = "session memory",
                             layer: Any = "subconscious",
                             title: Any = None,
                             confidence: Any = 0.8,
                             half_life_days: Any = 21,
                             memory_id: Any = None) -> SubconsciousMemory:
    """Earn one session-memory note into v2, by import.

    The carried note (M-153) is judged by the
    session layer's own ``validate_note``; only its
    id crosses - it stands as the memory's source
    ref, of kind ``session-note``, in the
    subconscious layer by default.
    """
    checked = _validate_note(note)
    return _earned_memory(
        source_kind="session-note", source_ref=checked.note_id,
        piece_word="session note", layer=layer, title=title,
        origin_session=origin_session, earned_on=earned_on,
        recorded_by=recorded_by, source=source,
        confidence=confidence, half_life_days=half_life_days,
        memory_id=memory_id)


def memory_from_ledger_candidate(candidate: Any, *, origin_session: Any,
                                 earned_on: Any, recorded_by: Any,
                                 source: Any = "self-improving ledger",
                                 layer: Any = "core", title: Any = None,
                                 confidence: Any = 0.85,
                                 half_life_days: Any = 30,
                                 memory_id: Any = None
                                 ) -> SubconsciousMemory:
    """Earn one self-improving ledger candidate into v2, by import.

    The candidate (M-155) is judged by the ledger's
    own ``validate_candidate``; only its id crosses
    - it stands as the memory's source ref, of kind
    ``ledger-candidate``, in the core layer by
    default.
    """
    checked = _validate_candidate(candidate)
    return _earned_memory(
        source_kind="ledger-candidate",
        source_ref=checked.candidate_id,
        piece_word="ledger candidate", layer=layer, title=title,
        origin_session=origin_session, earned_on=earned_on,
        recorded_by=recorded_by, source=source,
        confidence=confidence, half_life_days=half_life_days,
        memory_id=memory_id)


def memory_from_crew_entry(entry: Any, *, origin_session: Any,
                           earned_on: Any, recorded_by: Any,
                           source: Any = "crew memory",
                           layer: Any = "subconscious", title: Any = None,
                           confidence: Any = 0.8, half_life_days: Any = 21,
                           memory_id: Any = None) -> SubconsciousMemory:
    """Earn one crew-memory entry into v2, by import.

    The entry (M-133) is judged by crew memory's
    own ``validate_entry``; only its id crosses -
    it stands as the memory's source ref, of kind
    ``crew-fact``, in the subconscious layer by
    default. The fact's own words never cross.
    """
    checked = _validate_crew_entry(entry)
    return _earned_memory(
        source_kind="crew-fact", source_ref=checked.entry_id,
        piece_word="crew entry", layer=layer, title=title,
        origin_session=origin_session, earned_on=earned_on,
        recorded_by=recorded_by, source=source,
        confidence=confidence, half_life_days=half_life_days,
        memory_id=memory_id)


def memory_from_cross_project_lesson(lesson: Any, *, origin_session: Any,
                                     earned_on: Any, recorded_by: Any,
                                     source: Any = "cross-project memory",
                                     layer: Any = "subconscious",
                                     title: Any = None,
                                     confidence: Any = 0.8,
                                     half_life_days: Any = 21,
                                     memory_id: Any = None
                                     ) -> SubconsciousMemory:
    """Earn one cross-project lesson into v2, by import.

    The lesson (M-154) is judged by the
    cross-project layer's own ``validate_lesson``;
    only its id crosses - it stands as the memory's
    source ref, of kind ``cross-project-lesson``,
    in the subconscious layer by default.
    """
    checked = _validate_lesson(lesson)
    return _earned_memory(
        source_kind="cross-project-lesson",
        source_ref=checked.lesson_id,
        piece_word="cross-project lesson", layer=layer, title=title,
        origin_session=origin_session, earned_on=earned_on,
        recorded_by=recorded_by, source=source,
        confidence=confidence, half_life_days=half_life_days,
        memory_id=memory_id)


def memory_from_vector_record(record: Any, *, origin_session: Any,
                              earned_on: Any, recorded_by: Any,
                              source: Any = "vector memory",
                              layer: Any = "subconscious",
                              title: Any = None, ref: Any = None,
                              confidence: Any = 0.75,
                              half_life_days: Any = 14,
                              memory_id: Any = None) -> SubconsciousMemory:
    """Earn one shipped vector-memory record into v2, by import.

    The record stands in the shipped vector
    layer's own shape (``memory/vector_db.py``): a
    mapping with a ``text``, a ``vector`` of
    numbers and a ``metadata`` mapping. The record
    is judged in that shape; only a ref crosses -
    the *ref* named beside it, or the metadata's
    own ``id``, ``name`` or ``path`` word - and it
    stands as the memory's source ref, of kind
    ``vector-record``. The text and the vector
    themselves never cross into the v2 record.
    """
    if not isinstance(record, dict):
        raise ValueError(f"a vector record is needed, got {record!r}")
    text = record.get("text")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("a vector record must carry its text")
    vector = record.get("vector")
    if not isinstance(vector, (list, tuple)) or not vector or any(
            isinstance(v, bool) or not isinstance(v, (int, float))
            for v in vector):
        raise ValueError(
            "a vector record must carry a vector of numbers")
    metadata = record.get("metadata") or {}
    if not isinstance(metadata, dict):
        raise ValueError("a vector record's metadata must be a mapping")
    source_ref = ref
    if source_ref is None:
        for key in ("id", "name", "path"):
            if metadata.get(key):
                source_ref = metadata[key]
                break
    if source_ref is not None and not isinstance(source_ref, str):
        source_ref = str(source_ref)
    return _earned_memory(
        source_kind="vector-record", source_ref=source_ref,
        piece_word="vector record", layer=layer, title=title,
        origin_session=origin_session, earned_on=earned_on,
        recorded_by=recorded_by, source=source,
        confidence=confidence, half_life_days=half_life_days,
        memory_id=memory_id)


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


def memories_from_memory_map(source: Any, **kwargs: Any
                             ) -> Tuple[SubconsciousMemory, ...]:
    """Earn every entry of a memory map into v2, by import.

    The map - a book, a registry, entries or one
    entry (M-150) - is read entry by entry through
    :func:`memory_from_map_entry`, each judged by
    the map's own validation; the earning words
    (session, day, recorder and the rest) ride as
    keyword arguments shared by every memory.
    """
    return tuple(
        memory_from_map_entry(entry, **kwargs)
        for entry in _map_entries(source))


def _session_notes(source: Any) -> Tuple[CarriedMemory, ...]:
    """The shipped carried notes one source holds, judged by M-153."""
    from .session_memory import SessionMemoryBook, SessionMemoryRegistry
    if isinstance(source, SessionMemoryBook):
        return tuple(
            note for situation in source.situations
            for note in situation.memory)
    if isinstance(source, SessionMemoryRegistry):
        return tuple(
            note for situation in source.list_situations()
            for note in situation.memory)
    if isinstance(source, (list, tuple)):
        return tuple(_validate_note(n) for n in source)
    if isinstance(source, (CarriedMemory, dict)):
        return (_validate_note(source),)
    raise ValueError(f"session notes are needed, got {source!r}")


def memories_from_session_memory(source: Any, **kwargs: Any
                                 ) -> Tuple[SubconsciousMemory, ...]:
    """Earn every carried note of a session-memory book, by import.

    The book (M-153) is read situation by situation
    through :func:`memory_from_session_note`, each
    note judged by the session layer's own
    validation.
    """
    return tuple(
        memory_from_session_note(note, **kwargs)
        for note in _session_notes(source))


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


def memories_from_ledger(source: Any, **kwargs: Any
                         ) -> Tuple[SubconsciousMemory, ...]:
    """Earn every candidate of a self-improving ledger, by import."""
    return tuple(
        memory_from_ledger_candidate(candidate, **kwargs)
        for candidate in _ledger_candidates(source))


def _cross_lessons(source: Any) -> Tuple[SharedLesson, ...]:
    """The shipped shared lessons one source holds, judged by M-154."""
    from .cross_project_memory import CrossProjectBook, CrossProjectRegistry
    if isinstance(source, CrossProjectBook):
        return source.lessons
    if isinstance(source, CrossProjectRegistry):
        return source.list_lessons()
    if isinstance(source, (list, tuple)):
        return tuple(_validate_lesson(item) for item in source)
    if isinstance(source, (SharedLesson, dict)):
        return (_validate_lesson(source),)
    raise ValueError(f"cross-project lessons are needed, got {source!r}")


def memories_from_cross_project(source: Any, **kwargs: Any
                                ) -> Tuple[SubconsciousMemory, ...]:
    """Earn every shared lesson of a cross-project book, by import."""
    return tuple(
        memory_from_cross_project_lesson(lesson, **kwargs)
        for lesson in _cross_lessons(source))


def _crew_entries(source: Any) -> Tuple[CrewMemoryEntry, ...]:
    """The shipped crew entries one source holds, judged by M-133."""
    from .crew_memory import CrewMemory, CrewMemoryRegistry
    if isinstance(source, CrewMemory):
        return tuple(
            entry for notebook in source.notebooks
            for entry in notebook.entries)
    if isinstance(source, CrewMemoryRegistry):
        return source.list_entries()
    if isinstance(source, (list, tuple)):
        return tuple(_validate_crew_entry(e) for e in source)
    if isinstance(source, (CrewMemoryEntry, dict)):
        return (_validate_crew_entry(source),)
    raise ValueError(f"crew entries are needed, got {source!r}")


def memories_from_crew_memory(source: Any, **kwargs: Any
                              ) -> Tuple[SubconsciousMemory, ...]:
    """Earn every entry of a crew memory into v2, by import."""
    return tuple(
        memory_from_crew_entry(entry, **kwargs)
        for entry in _crew_entries(source))


def inspect_memory_source(piece: Any) -> Dict[str, Any]:
    """Inspect one shipped piece: its kind and ref only.

    The piece is judged by the layer that owns its
    type, never by whichever validator happens to
    accept its shape first. A v2 memory reports
    itself; each shipped holding reports the kind
    and ref a v2 memory earned from it would carry.
    A piece no shipped layer owns refuses.
    """
    if isinstance(piece, SubconsciousMemory):
        return {"source_kind": piece.source_kind,
                "source_ref": piece.source_ref}
    if isinstance(piece, MemoryMapEntry):
        return {"source_kind": "memory-map",
                "source_ref": piece.entry_id}
    if isinstance(piece, CandidateMemory):
        return {"source_kind": "ledger-candidate",
                "source_ref": piece.candidate_id}
    if isinstance(piece, CarriedMemory):
        return {"source_kind": "session-note",
                "source_ref": piece.note_id}
    if isinstance(piece, CrewMemoryEntry):
        return {"source_kind": "crew-fact",
                "source_ref": piece.entry_id}
    if isinstance(piece, SharedLesson):
        return {"source_kind": "cross-project-lesson",
                "source_ref": piece.lesson_id}
    if isinstance(piece, dict):
        if "vector" in piece and "text" in piece:
            checked = memory_from_vector_record(
                piece, origin_session="session-inspect",
                earned_on="2026-01-01", recorded_by="inspect")
            return {"source_kind": "vector-record",
                    "source_ref": checked.source_ref}
        for road, kind in (
                (_validate_map_entry, "memory-map"),
                (_validate_candidate, "ledger-candidate"),
                (_validate_note, "session-note"),
                (_validate_crew_entry, "crew-fact"),
                (_validate_lesson, "cross-project-lesson")):
            try:
                checked = road(piece)
            except Exception:
                continue
            ref = getattr(checked, "entry_id", None) or getattr(
                checked, "candidate_id", None) or getattr(
                checked, "note_id", None) or getattr(
                checked, "lesson_id", None)
            return {"source_kind": kind, "source_ref": ref}
    raise ValueError(
        f"no shipped layer owns this piece, got {piece!r}")


# ---------------------------------------------------------------------
# The subconscious panel: every memory carried whole, derived as of a day.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class SubconsciousPanelRow:
    """One memory carried whole into the panel, as of a day.

    Every field is the memory's own head - its id,
    title, layer and provenance ref - beside its
    decay read off as of the panel's day: the
    confidence it was earned with, its effective
    confidence, its freshness, its age in days and
    its re-earn count. :func:`validate_row` judged
    against its memory and day refuses a row whose
    fields disagree with the row they derive.
    """

    memory_id: str
    title: str
    layer: str
    source_kind: str
    source_ref: str
    confidence: float
    effective_confidence: float
    freshness: str
    age_days: int
    reearn_count: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "memory_id", normalize_member_id(self.memory_id))
        object.__setattr__(
            self, "title", _check_title(self.title, "a row's title"))
        object.__setattr__(
            self, "layer", normalize_memory_layer(self.layer))
        object.__setattr__(
            self, "source_kind", normalize_source_kind(self.source_kind))
        object.__setattr__(
            self, "source_ref",
            _check_word(self.source_ref, "a row's source ref"))
        object.__setattr__(
            self, "confidence", _check_confidence(self.confidence))
        effective = _check_confidence(self.effective_confidence)
        if effective > self.confidence:
            raise ValueError(
                "a row's effective confidence must not "
                "stand above the confidence its memory "
                "was earned with - decay never adds trust")
        object.__setattr__(self, "effective_confidence", effective)
        state = normalize_freshness_state(self.freshness)
        object.__setattr__(self, "freshness", state)
        object.__setattr__(
            self, "age_days",
            _check_count(self.age_days, "a row's age in days"))
        object.__setattr__(
            self, "reearn_count",
            _check_count(self.reearn_count, "a row's re-earn count"))

    @property
    def sort_key(self) -> Tuple[int, str, str]:
        """This row's place in panel order (derived).

        Rows stand by layer (core first, in the dual
        layers' own order), then title, then memory
        id.
        """
        return (MEMORY_LAYERS.index(self.layer),
                self.title.lower(), self.memory_id)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "subconscious_v2_panel_row",
            "slice": SUBCONSCIOUS_V2_SLICE,
            "memory_id": self.memory_id,
            "title": self.title,
            "layer": self.layer,
            "source_kind": self.source_kind,
            "source_ref": self.source_ref,
            "confidence": self.confidence,
            "effective_confidence": self.effective_confidence,
            "freshness": self.freshness,
            "age_days": self.age_days,
            "reearn_count": self.reearn_count,
        }


def _row_for_memory(memory: SubconsciousMemory, as_of: str
                    ) -> SubconsciousPanelRow:
    return SubconsciousPanelRow(
        memory_id=memory.memory_id, title=memory.title,
        layer=memory.layer, source_kind=memory.source_kind,
        source_ref=memory.source_ref, confidence=memory.confidence,
        effective_confidence=effective_confidence(memory, as_of),
        freshness=freshness_state(memory, as_of),
        age_days=age_days(memory, as_of),
        reearn_count=memory.reearn_count)


def _check_row_ref(value: Any) -> SubconsciousPanelRow:
    if isinstance(value, SubconsciousPanelRow):
        return value
    if isinstance(value, dict):
        return validate_row(value)
    raise ValueError(f"a panel row is needed, got {value!r}")


def validate_row(row: Any, memory: Any = None, as_of: Any = None
                 ) -> SubconsciousPanelRow:
    """Validate one panel row into a SubconsciousPanelRow.

    Accepts a row or a mapping naming its fields
    (``effective`` reads onto ``effective_confidence``,
    ``state`` onto ``freshness``, ``age`` onto
    ``age_days``, ``reearns`` onto ``reearn_count``).
    With *memory* and *as_of* given, the row is
    judged against the row that memory derives on
    that day.
    """
    if isinstance(row, SubconsciousPanelRow):
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

        current = SubconsciousPanelRow(
            memory_id=_needed(("memory_id", "id"), "memory id"),
            title=_needed(("title",), "title"),
            layer=_needed(("layer",), "layer"),
            source_kind=_needed(("source_kind",), "source kind"),
            source_ref=_needed(("source_ref",), "source ref"),
            confidence=_needed(("confidence",), "confidence"),
            effective_confidence=_needed(
                ("effective_confidence", "effective"),
                "effective confidence"),
            freshness=_needed(("freshness", "state"), "freshness"),
            age_days=_needed(("age_days", "age"), "age in days"),
            reearn_count=_needed(
                ("reearn_count", "reearns"), "re-earn count"))
    else:
        raise ValueError(f"a panel row must be a mapping, got {row!r}")
    if memory is not None:
        if as_of is None:
            raise ValueError(
                "a row judged against its memory must "
                "name the day it is judged as of")
        derived = _row_for_memory(_check_memory_ref(memory), as_of)
        if current != derived:
            raise ValueError(
                "a stored row disagrees with the row "
                "its memory derives on that day")
    return current


def build_row(row: Any = None, memory: Any = None, as_of: Any = None,
              **kwargs: Any) -> SubconsciousPanelRow:
    """Build one validated row, from a mapping or field words."""
    if isinstance(row, SubconsciousPanelRow) and not kwargs:
        return validate_row(row, memory, as_of)
    if isinstance(row, dict) or row is None:
        merged: Dict[str, Any] = {}
        if isinstance(row, dict):
            merged.update(row)
        merged.update(kwargs)
        return validate_row(merged, memory, as_of)
    return validate_row(row, memory, as_of)


@dataclass(frozen=True)
class StateCount:
    """How many of a panel's memories stand in one freshness state."""

    state: str
    items: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "state", normalize_freshness_state(self.state))
        object.__setattr__(
            self, "items", _check_count(self.items, "a state count"))

    def to_record(self) -> Dict[str, Any]:
        return {"state": self.state, "items": self.items}


def _check_state_count_ref(value: Any) -> StateCount:
    if isinstance(value, StateCount):
        return value
    if isinstance(value, dict):
        unknown = set(value) - _STATE_COUNT_KEYS
        if unknown:
            raise ValueError(
                "unknown state-count keys: %s"
                % ", ".join(sorted(unknown)))
        state = _pick_any(value, ("state",), "states")
        if state is None:
            raise ValueError("a state count is missing its state")
        items = _pick_any(value, ("items", "count"), "counts")
        if items is None:
            raise ValueError("a state count is missing its count")
        return StateCount(state=state, items=items)
    raise ValueError(f"a state count is needed, got {value!r}")


def _panel_account(total_memories: int, total_core: int,
                   total_subconscious: int,
                   state_counts: Tuple[StateCount, ...], as_of: str
                   ) -> Tuple[str, ...]:
    tallies = ", ".join(
        f"{count.state} {count.items}"
        for count in sorted(state_counts, key=lambda count: count.state))
    return (
        f"The subconscious panel holds {total_memories} "
        f"memories as of {as_of}: {total_core} in the "
        f"core layer and {total_subconscious} in the "
        f"subconscious layer: {tallies}.",
        "Rows stand by layer, then title, then memory "
        "id, so two panels of one book on one day diff "
        "cleanly, line by line.",
        "Every row's effective confidence and freshness "
        "are read off its memory's own decay - its "
        "confidence, its half-life and the day it was "
        "last earned - and a row that disagrees with "
        "that reading is refused.",
        "The panel is read off the book at call time, "
        "as of a named day - it is derived, never "
        "stored loose.",
    )


@dataclass(frozen=True)
class SubconsciousPanel:
    """The subconscious panel of one book, derived as of a day.

    ``rows`` are the book's memories carried whole,
    in panel order (by layer, then title, then
    memory id), each with its decay read off as of
    ``as_of``; ``total_memories`` is the rows' own
    count, ``total_core`` and ``total_subconscious``
    the rows standing in each of the dual layers,
    ``total_reearned`` the sum of their re-earn
    counts, and ``state_counts`` the per-state
    tallies of their freshness. ``account`` is read
    off those numbers. A panel whose rows stand out
    of panel order, or whose tallies are not its
    own rows' tallies, refuses at construction;
    :func:`validate_panel` judged against a book
    refuses a stored panel that disagrees with the
    derived one.
    """

    rows: Tuple[SubconsciousPanelRow, ...] = ()
    total_memories: int = 0
    total_core: int = 0
    total_subconscious: int = 0
    total_reearned: int = 0
    state_counts: Tuple[StateCount, ...] = ()
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
            if row.memory_id in seen:
                raise ValueError(
                    f"a panel row for memory {row.memory_id!r} "
                    f"already exists")
            seen.add(row.memory_id)
        keys = [row.sort_key for row in rows]
        if keys != sorted(keys):
            raise ValueError(
                "a panel's rows must stand in panel order "
                "(by layer, then title, then memory id)")
        object.__setattr__(self, "rows", rows)
        object.__setattr__(
            self, "total_memories",
            _check_count(self.total_memories, "a panel's total memories"))
        if self.total_memories != len(rows):
            raise ValueError(
                "a panel's total memories must be its own "
                "rows' count")
        object.__setattr__(
            self, "total_core",
            _check_count(self.total_core, "a panel's total core"))
        if self.total_core != sum(
                1 for r in rows if r.layer == "core"):
            raise ValueError(
                "a panel's total core must be its own "
                "rows' core count")
        object.__setattr__(
            self, "total_subconscious",
            _check_count(
                self.total_subconscious, "a panel's total subconscious"))
        if self.total_subconscious != sum(
                1 for r in rows if r.layer == "subconscious"):
            raise ValueError(
                "a panel's total subconscious must be its "
                "own rows' subconscious count")
        if self.total_memories != (
                self.total_core + self.total_subconscious):
            raise ValueError(
                "a panel's total memories must be its own "
                "layer totals' sum")
        object.__setattr__(
            self, "total_reearned",
            _check_count(self.total_reearned, "a panel's total re-earned"))
        if self.total_reearned != sum(r.reearn_count for r in rows):
            raise ValueError(
                "a panel's total re-earned must be its own "
                "rows' re-earn sum")
        if isinstance(self.state_counts, (str, bytes)) \
                or not isinstance(self.state_counts, (list, tuple)):
            raise ValueError(
                f"a panel's state counts must be a list, "
                f"got {self.state_counts!r}")
        state_counts = tuple(
            _check_state_count_ref(c) for c in self.state_counts)
        seen_states = set()
        for count in state_counts:
            if count.state in seen_states:
                raise ValueError(
                    f"a state count named {count.state!r} "
                    f"already exists")
            seen_states.add(count.state)
        object.__setattr__(self, "state_counts", state_counts)
        if sum(c.items for c in state_counts) != self.total_memories:
            raise ValueError(
                "a panel's state counts must sum to its "
                "own total memories")
        tallies = {
            state: sum(1 for r in rows if r.freshness == state)
            for state in FRESHNESS_STATES}
        for count in state_counts:
            if count.items != tallies.get(count.state, 0):
                raise ValueError(
                    "a panel's state counts must be its "
                    "own rows' counts")
        if {s for s, v in tallies.items() if v} != {
                c.state for c in state_counts}:
            raise ValueError(
                "a panel's state counts must name every "
                "state its rows stand in")
        object.__setattr__(self, "account", _check_account(self.account))

    def row_for(self, memory_id: Any) -> SubconsciousPanelRow:
        """The panel row one memory names in this panel."""
        wanted = normalize_member_id(memory_id)
        for row in self.rows:
            if row.memory_id == wanted:
                return row
        raise KeyError(f"no row in the panel: memory {wanted!r}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "subconscious_v2_panel",
            "slice": SUBCONSCIOUS_V2_SLICE,
            "panel_id": self.panel_id,
            "rows": [row.to_record() for row in self.rows],
            "total_memories": self.total_memories,
            "total_core": self.total_core,
            "total_subconscious": self.total_subconscious,
            "total_reearned": self.total_reearned,
            "state_counts": [c.to_record() for c in self.state_counts],
            "as_of": self.as_of,
            "account": list(self.account),
        }


def _held_memories(source: Any) -> Tuple[SubconsciousMemory, ...]:
    if isinstance(source, SubconsciousBook):
        return source.memories
    if isinstance(source, SubconsciousRegistry):
        return source.list_memories()
    if isinstance(source, (list, tuple)):
        return tuple(_check_memory_ref(item) for item in source)
    raise ValueError(f"subconscious memories are needed, got {source!r}")


def _default_as_of(memories: Tuple[SubconsciousMemory, ...]) -> str:
    """The day a book is read as of when none is named.

    The latest day any of its memories was earned
    or last earned - the book's own latest day, so
    a derivation with no day named is still read
    off the book alone.
    """
    days = []
    for memory in memories:
        days.append(memory.earned_on)
        days.append(memory.last_earned_on)
    return max(days)


def derive_panel(source: Any, as_of: Any = None) -> SubconsciousPanel:
    """Derive the subconscious panel from one book, as of a day.

    The rows are the book's memories carried whole,
    in panel order: by layer, then title, then
    memory id, each with its effective confidence
    and freshness read off its own decay as of
    *as_of* (the book's own latest day when none is
    named). *source* is a book or a registry. A
    source holding no memory refuses - a panel of
    nothing is no panel.
    """
    memories = _held_memories(source)
    if not memories:
        raise ValueError("a panel needs at least one subconscious memory")
    day = _check_day(as_of, "an as-of day") if as_of is not None \
        else _default_as_of(memories)
    rows = []
    for memory in memories:
        if memory.memory_id is None:
            raise ValueError(
                "a panel row must name its memory - a "
                "memory with no id refuses derivation")
        rows.append(_row_for_memory(memory, day))
    rows = tuple(sorted(rows, key=lambda r: r.sort_key))
    tallies = {
        state: sum(1 for r in rows if r.freshness == state)
        for state in FRESHNESS_STATES}
    state_counts = tuple(
        StateCount(state=state, items=tallies[state])
        for state in FRESHNESS_STATES if tallies[state])
    total_core = sum(1 for r in rows if r.layer == "core")
    return SubconsciousPanel(
        rows=rows, total_memories=len(rows),
        total_core=total_core,
        total_subconscious=len(rows) - total_core,
        total_reearned=sum(r.reearn_count for r in rows),
        state_counts=state_counts,
        account=_panel_account(
            len(rows), total_core, len(rows) - total_core,
            state_counts, day),
        as_of=day)


def validate_panel(panel: Any, source: Any = None
                   ) -> SubconsciousPanel:
    """Validate one panel into a SubconsciousPanel.

    Accepts a panel or a mapping naming ``rows`` (or
    ``memories``), a ``total_memories`` (or
    ``total``), ``total_core``, ``total_subconscious``,
    a ``total_reearned``, ``state_counts`` (or
    ``states``), an ``as_of`` (or ``day``), an
    ``account`` (or ``statements``) and an optional
    ``panel_id`` (or ``id``). With *source* given (a
    book), the panel is judged against the panel
    derived from that book as of the panel's own
    day.
    """
    if isinstance(panel, SubconsciousPanel):
        current = panel
    elif isinstance(panel, dict):
        unknown = set(panel) - _PANEL_KEYS
        if unknown:
            raise ValueError(
                "unknown panel keys: %s" % ", ".join(sorted(unknown)))
        rows = _pick_any(panel, ("rows", "memories"), "rows")
        if rows is None:
            raise ValueError("a panel is missing its rows")
        total = _pick_any(panel, ("total_memories", "total"), "totals")
        if total is None:
            raise ValueError("a panel is missing its total memories")
        core = _pick_any(panel, ("total_core", "core"), "core totals")
        if core is None:
            raise ValueError("a panel is missing its total core")
        sub = _pick_any(
            panel, ("total_subconscious", "subconscious"),
            "subconscious totals")
        if sub is None:
            raise ValueError("a panel is missing its total subconscious")
        reearned = _pick_any(
            panel, ("total_reearned", "reearned"), "re-earn totals")
        if reearned is None:
            raise ValueError("a panel is missing its total re-earned")
        state_counts = _pick_any(
            panel, ("state_counts", "states"), "state counts")
        if state_counts is None:
            raise ValueError("a panel is missing its state counts")
        as_of = _pick_any(panel, ("as_of", "day"), "as-of days")
        if as_of is None:
            raise ValueError("a panel is missing its as-of day")
        account = _pick_any(panel, ("account", "statements"), "accounts")
        if account is None:
            raise ValueError("a panel names no account of its own")
        kwargs: Dict[str, Any] = {
            "rows": rows, "total_memories": total,
            "total_core": core, "total_subconscious": sub,
            "total_reearned": reearned, "state_counts": state_counts,
            "as_of": as_of, "account": account}
        panel_id = _pick_any(panel, ("panel_id", "id"), "panel ids")
        if panel_id is not None:
            kwargs["panel_id"] = panel_id
        current = SubconsciousPanel(**kwargs)
    else:
        raise ValueError(f"a panel must be a mapping, got {panel!r}")
    if source is not None:
        derived = derive_panel(source, current.as_of)
        if (current.rows != derived.rows
                or current.total_memories != derived.total_memories
                or current.total_core != derived.total_core
                or current.total_subconscious != derived.total_subconscious
                or current.total_reearned != derived.total_reearned
                or current.state_counts != derived.state_counts
                or current.account != derived.account):
            raise ValueError(
                "a stored panel disagrees with the panel "
                "derived from its book")
    return current


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> SubconsciousPanel:
    """Build one validated panel, from a mapping or field words."""
    if isinstance(panel, SubconsciousPanel) and not kwargs:
        return validate_panel(panel, source)
    if isinstance(panel, dict) or panel is None:
        merged: Dict[str, Any] = {}
        if isinstance(panel, dict):
            merged.update(panel)
        merged.update(kwargs)
        return validate_panel(merged, source)
    return validate_panel(panel, source)


# ---------------------------------------------------------------------
# The freshness verdict: the whole book judged, as data.
# ---------------------------------------------------------------------


def _verdict_word(total_fading: int, total_stale: int,
                  total_faded: int) -> str:
    """The verdict word a book's own tallies derive."""
    if total_faded:
        return "neglected"
    if total_stale:
        return "going-stale"
    if total_fading:
        return "fading"
    return "well-kept"


@dataclass(frozen=True)
class FreshnessVerdict:
    """One freshness verdict: a whole book judged, as data.

    ``total_memories`` counts the book's memories;
    ``total_fresh`` / ``total_fading`` /
    ``total_stale`` / ``total_faded`` count them by
    the freshness each stands in as of ``as_of``;
    ``total_core`` and ``total_subconscious`` count
    them by layer; ``distinct_sources`` counts how
    many shipped pieces the book's provenance
    names; ``verdict`` is the word those tallies
    derive - ``well-kept`` when every memory stands
    fresh, ``fading`` when some fade and none stand
    stale or faded, ``going-stale`` when any stands
    stale, and ``neglected`` when any has faded
    away un-re-earned.
    """

    total_memories: int
    total_fresh: int
    total_fading: int
    total_stale: int
    total_faded: int
    total_core: int
    total_subconscious: int
    distinct_sources: int
    as_of: str
    verdict: str

    def __post_init__(self) -> None:
        for field, what in (
                ("total_memories", "total memories"),
                ("total_fresh", "total fresh"),
                ("total_fading", "total fading"),
                ("total_stale", "total stale"),
                ("total_faded", "total faded"),
                ("total_core", "total core"),
                ("total_subconscious", "total subconscious"),
                ("distinct_sources", "distinct sources")):
            object.__setattr__(
                self, field, _check_count(getattr(self, field), what))
        if self.total_memories != (
                self.total_fresh + self.total_fading
                + self.total_stale + self.total_faded):
            raise ValueError(
                "a verdict's total memories must be its "
                "own freshness tallies' sum")
        if self.total_memories != (
                self.total_core + self.total_subconscious):
            raise ValueError(
                "a verdict's total memories must be its "
                "own layer tallies' sum")
        if self.distinct_sources > self.total_memories:
            raise ValueError(
                "a verdict's distinct sources must not "
                "outnumber its memories")
        object.__setattr__(
            self, "as_of", _check_day(self.as_of, "a verdict's as-of day"))
        word = _clean_text(self.verdict, "a verdict")
        if word not in VERDICT_WORDS:
            raise ValueError(
                "a verdict must be one of %s, got %r"
                % ("/".join(VERDICT_WORDS), word))
        derived = _verdict_word(
            self.total_fading, self.total_stale, self.total_faded)
        if word != derived:
            raise ValueError(
                f"a verdict's word must be the word its "
                f"own tallies derive ({derived!r}), got {word!r}")
        object.__setattr__(self, "verdict", word)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "subconscious_v2_verdict",
            "slice": SUBCONSCIOUS_V2_SLICE,
            "total_memories": self.total_memories,
            "total_fresh": self.total_fresh,
            "total_fading": self.total_fading,
            "total_stale": self.total_stale,
            "total_faded": self.total_faded,
            "total_core": self.total_core,
            "total_subconscious": self.total_subconscious,
            "distinct_sources": self.distinct_sources,
            "as_of": self.as_of,
            "verdict": self.verdict,
        }


def derive_verdict(source: Any, as_of: Any = None) -> FreshnessVerdict:
    """Derive the freshness verdict for one whole book, as of a day."""
    memories = _held_memories(source)
    if not memories:
        raise ValueError(
            "a verdict needs at least one subconscious memory")
    day = _check_day(as_of, "an as-of day") if as_of is not None \
        else _default_as_of(memories)
    tallies = {state: 0 for state in FRESHNESS_STATES}
    for memory in memories:
        tallies[freshness_state(memory, day)] += 1
    total_core = sum(1 for m in memories if m.layer == "core")
    return FreshnessVerdict(
        total_memories=len(memories),
        total_fresh=tallies["fresh"], total_fading=tallies["fading"],
        total_stale=tallies["stale"], total_faded=tallies["faded"],
        total_core=total_core,
        total_subconscious=len(memories) - total_core,
        distinct_sources=len({
            (m.source_kind, m.source_ref) for m in memories}),
        as_of=day,
        verdict=_verdict_word(
            tallies["fading"], tallies["stale"], tallies["faded"]))


def _check_verdict_ref(value: Any) -> FreshnessVerdict:
    if isinstance(value, FreshnessVerdict):
        return value
    if isinstance(value, dict):
        return validate_verdict(value)
    raise ValueError(f"a freshness verdict is needed, got {value!r}")


def validate_verdict(verdict: Any, source: Any = None) -> FreshnessVerdict:
    """Validate one verdict into a FreshnessVerdict.

    Accepts a verdict or a mapping naming its
    tallies (short spellings read onto the totals),
    an ``as_of`` (or ``day``) and its ``verdict``
    word. With *source* given (a book), the verdict
    is judged against the verdict derived from that
    book as of the verdict's own day.
    """
    if isinstance(verdict, FreshnessVerdict):
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

        current = FreshnessVerdict(
            total_memories=_needed(
                ("total_memories", "total"), "total memories"),
            total_fresh=_needed(("total_fresh", "fresh"), "total fresh"),
            total_fading=_needed(
                ("total_fading", "fading"), "total fading"),
            total_stale=_needed(("total_stale", "stale"), "total stale"),
            total_faded=_needed(("total_faded", "faded"), "total faded"),
            total_core=_needed(("total_core", "core"), "total core"),
            total_subconscious=_needed(
                ("total_subconscious", "subconscious"),
                "total subconscious"),
            distinct_sources=_needed(
                ("distinct_sources", "sources"), "distinct sources"),
            as_of=_needed(("as_of", "day"), "as-of day"),
            verdict=_needed(("verdict",), "verdict"))
    else:
        raise ValueError(f"a verdict must be a mapping, got {verdict!r}")
    if source is not None:
        derived = derive_verdict(source, current.as_of)
        if current != derived:
            raise ValueError(
                "a stored verdict disagrees with the "
                "verdict derived from its book")
    return current


def build_verdict(verdict: Any = None, source: Any = None,
                  **kwargs: Any) -> FreshnessVerdict:
    """Build one validated verdict, from a mapping or field words."""
    if isinstance(verdict, FreshnessVerdict) and not kwargs:
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict) or verdict is None:
        merged: Dict[str, Any] = {}
        if isinstance(verdict, dict):
            merged.update(verdict)
        merged.update(kwargs)
        return validate_verdict(merged, source)
    return validate_verdict(verdict, source)


# ---------------------------------------------------------------------
# The book: one book of v2 memories, and its loaders.
# ---------------------------------------------------------------------


def _judge_memories(memories: Tuple[SubconsciousMemory, ...],
                    held: Tuple[SubconsciousMemory, ...] = ()) -> None:
    """Judge memories against held memories: the book's laws.

    One memory per shipped piece - one source kind
    and source ref is earned once - so a memory's
    provenance never forks inside a book. *held*
    names memories already standing (a registry's),
    judged alongside.
    """
    owners: Dict[Tuple[str, str], str] = {}
    for memory in tuple(held) + tuple(memories):
        key = (memory.source_kind, memory.source_ref)
        if key in owners:
            raise ValueError(
                f"a piece earned twice: {key[0]} "
                f"{key[1]!r} already stands as "
                f"{owners[key]!r} - one earning per piece")
        owners[key] = memory.memory_id or memory.title


@dataclass(frozen=True)
class SubconsciousBook:
    """One subconscious v2 book: its memories, in held order.

    ``memories`` are the v2 memories, in held order,
    each with its provenance whole, one per shipped
    piece. ``panels`` are the book's derivations -
    subconscious panels of the whole book, each
    judged against the book by :func:`validate_book`;
    ``canon_note`` is the book's own note. The total
    is the memories' own count, judged at
    construction.
    """

    title: str = ""
    memories: Tuple[SubconsciousMemory, ...] = ()
    panels: Tuple[SubconsciousPanel, ...] = ()
    canon_note: str = ""
    total_memories: Optional[int] = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_title(self.title, "a book's title"))
        if isinstance(self.memories, (str, bytes)) \
                or not isinstance(self.memories, (list, tuple)):
            raise ValueError(
                f"a book's memories must be a list of "
                f"memories, got {self.memories!r}")
        memories = tuple(_check_memory_ref(item) for item in self.memories)
        if not memories:
            raise ValueError("a subconscious book holds at least one memory")
        seen_ids = set()
        for memory in memories:
            if memory.memory_id is not None:
                if memory.memory_id in seen_ids:
                    raise ValueError(
                        f"a memory named "
                        f"{memory.memory_id!r} already exists")
                seen_ids.add(memory.memory_id)
        _judge_memories(memories)
        object.__setattr__(self, "memories", memories)
        if isinstance(self.panels, (str, bytes)) \
                or not isinstance(self.panels, (list, tuple)):
            raise ValueError(
                f"a book's panels must be a list of panels, "
                f"got {self.panels!r}")
        panels = tuple(
            p if isinstance(p, SubconsciousPanel)
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
        given = self.total_memories
        if given is None:
            object.__setattr__(self, "total_memories", len(memories))
        else:
            checked = _check_count(given, "a book's total memories")
            if checked != len(memories):
                raise ValueError(
                    "a book's total memories must be its "
                    "own memories' count")
            object.__setattr__(self, "total_memories", checked)

    def memory_for(self, memory_id: Any) -> SubconsciousMemory:
        """The memory one id names in this book."""
        wanted = normalize_member_id(memory_id)
        for memory in self.memories:
            if memory.memory_id == wanted:
                return memory
        raise KeyError(f"no memory in the book: {wanted!r}")

    def memory_for_source(self, source_kind: Any, source_ref: Any
                          ) -> SubconsciousMemory:
        """The memory earned from one shipped piece in this book."""
        kind = normalize_source_kind(source_kind)
        wanted = _check_word(source_ref, "a source ref")
        for memory in self.memories:
            if memory.source_kind == kind and memory.source_ref == wanted:
                return memory
        raise KeyError(f"no memory in the book from {kind} {wanted!r}")

    def panel_for(self, panel_id: Any) -> SubconsciousPanel:
        """The stored panel one id names in this book."""
        wanted = normalize_member_id(panel_id)
        for panel in self.panels:
            if panel.panel_id == wanted:
                return panel
        raise KeyError(f"no panel in the book: {wanted!r}")

    def memory_ids(self) -> Tuple[str, ...]:
        """Every held memory id, in held order."""
        return tuple(
            item.memory_id for item in self.memories if item.memory_id)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "subconscious_v2_book",
            "slice": SUBCONSCIOUS_V2_SLICE,
            "title": self.title,
            "memory_ids": list(self.memory_ids()),
            "memory_count": len(self.memories),
            "panel_count": len(self.panels),
        }


# The pinned example panel's account is filled in
# below, once the panel machinery stands.
_EXAMPLE_PANEL_ACCOUNT: Tuple[str, ...] = (
    "The subconscious panel holds 6 memories as of "
    "2026-11-09: 3 in the core layer and 3 in the "
    "subconscious layer: faded 1, fading 1, fresh 3, "
    "stale 1.",
    "Rows stand by layer, then title, then memory "
    "id, so two panels of one book on one day diff "
    "cleanly, line by line.",
    "Every row's effective confidence and freshness "
    "are read off its memory's own decay - its "
    "confidence, its half-life and the day it was "
    "last earned - and a row that disagrees with "
    "that reading is refused.",
    "The panel is read off the book at call time, "
    "as of a named day - it is derived, never "
    "stored loose.",
)


def validate_book(data: Any, *, require_example: bool = False
                  ) -> SubconsciousBook:
    """Validate one subconscious mapping into a book.

    The mapping names a ``schema``, a ``guide``
    mapping (its ``title``), a ``memories`` list (or
    ``records``) and an optional ``panels`` list.
    Every memory stands on its own validation, then
    the whole is judged: memory ids unique, one
    memory per shipped piece, and every stored
    panel judged against the book. With
    ``require_example`` the shipped example is held
    to its pinned shape.
    """
    if isinstance(data, SubconsciousBook):
        return data
    if not isinstance(data, dict):
        raise ValidationError(
            f"a subconscious book must be a mapping, got {data!r}")
    unknown = set(data) - _SUBCONSCIOUS_BOOK_KEYS
    if unknown:
        raise ValidationError(
            "unknown subconscious-book keys: %s"
            % ", ".join(sorted(unknown)))
    if data.get("schema") != SUBCONSCIOUS_V2_SCHEMA:
        raise ValidationError(
            f"a subconscious book must carry schema "
            f"{SUBCONSCIOUS_V2_SCHEMA!r}, "
            f"got {data.get('schema')!r}")
    memories = _pick_any(data, ("memories", "records"), "memories")
    if memories is None:
        raise ValidationError("a subconscious book is missing its memories")
    if not isinstance(memories, (list, tuple)):
        raise ValidationError("a subconscious book's memories must be a list")
    if data.get("panels") is not None \
            and not isinstance(data["panels"], (list, tuple)):
        raise ValidationError("a subconscious book's panels must be a list")
    head = data.get("guide") or {}
    if not isinstance(head, dict):
        raise ValidationError("a subconscious book's guide must be a mapping")
    unknown_head = set(head) - _BOOK_KEYS
    if unknown_head:
        raise ValidationError(
            "unknown guide keys: %s" % ", ".join(sorted(unknown_head)))
    try:
        title = _pick_any(head, ("title", "name"), "titles")
        if title is None:
            raise ValidationError("a subconscious book is missing its title")
        note = data.get("canon_note") or ""
        if not isinstance(note, str):
            raise ValidationError("a subconscious book's note must be text")
        book = SubconsciousBook(
            title=title, memories=tuple(memories),
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
                "the shipped example subconscious book's "
                "title is not the pinned title")
        if book.memory_ids() != _EXAMPLE_MEMORY_IDS:
            raise ValidationError(
                "the shipped example's memories are not "
                "the pinned memories")
        panel = book.panel_for(_EXAMPLE_PANEL_ID)
        if panel.as_of != _EXAMPLE_AS_OF:
            raise ValidationError(
                "the shipped example panel does not stand "
                "as of its pinned day")
        if tuple(r.memory_id for r in panel.rows) != _EXAMPLE_PANEL_ROW_IDS:
            raise ValidationError(
                "the shipped example panel does not name "
                "its pinned rows in panel order")
        if _EXAMPLE_PANEL_ACCOUNT and panel.account != _EXAMPLE_PANEL_ACCOUNT:
            raise ValidationError(
                "the shipped example panel does not carry "
                "its pinned account word-for-word")
        first = book.memories[0]
        if first.memory_id != _EXAMPLE_FIRST_MEMORY_ID \
                or first.title != _EXAMPLE_FIRST_MEMORY_TITLE:
            raise ValidationError(
                "the shipped example's first memory is "
                "not its pinned memory of its pinned title")
    return book


def build_book(book: Any = None, **kwargs: Any) -> SubconsciousBook:
    """Build one validated book, from a mapping or field words."""
    if isinstance(book, SubconsciousBook) and not kwargs:
        return book
    if isinstance(book, dict):
        if "schema" in book:
            return validate_book(book)
        merged: Dict[str, Any] = dict(book)
        merged.update(kwargs)
        return SubconsciousBook(**merged)
    if book is None:
        return SubconsciousBook(**kwargs)
    raise ValueError(f"a subconscious book is needed, got {book!r}")


def _book_from(data: Any, *, require_example: bool) -> SubconsciousBook:
    try:
        return validate_book(data, require_example=require_example)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def load_subconscious_v2(
        data: Optional[Dict[str, Any]] = None) -> SubconsciousBook:
    """Load and validate the shipped example book (or *data*)."""
    raw = data if data is not None else load_resource(
        SUBCONSCIOUS_V2_RESOURCE)
    return _book_from(raw, require_example=True)


def load_subconscious_v2_file(path: Any) -> SubconsciousBook:
    """Load and validate a subconscious book from a file at *path*."""
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _book_from(raw, require_example=False)


# ---------------------------------------------------------------------
# The registry model: one book held memory by memory.
# ---------------------------------------------------------------------


class SubconsciousRegistry:
    """One book's memories, held one by one.

    The registry holds memories, never panels or
    verdicts: the panel and the freshness verdict
    are derivations, read off the whole held book at
    call time, as of a named day. A whole book is
    judged whole - as a book judges it, and against
    everything already held - before its memories
    are held in book order, so an earning never
    lands partially. A memory held here stands
    apart: a second memory earned from a held piece
    refuses - one earning per piece.
    """

    def __init__(self, book: Any = None) -> None:
        self._title: Optional[str] = None
        self._memories: Dict[str, SubconsciousMemory] = {}
        self._memory_order: list = []
        self._next_memory = 1
        if book is not None:
            self.register_book(book)

    def _fresh_memory_id(self, held_ids: Any) -> str:
        while f"memory-{self._next_memory}" in held_ids:
            self._next_memory += 1
        fresh = f"memory-{self._next_memory}"
        self._next_memory += 1
        return fresh

    def _check_standing_free(self, memory: SubconsciousMemory) -> None:
        _judge_memories((memory,), held=self.list_memories())

    def register_memory(self, memory: Any) -> SubconsciousMemory:
        """Register one memory into the held book."""
        validated = _check_memory_ref(memory)
        if validated.memory_id is not None \
                and validated.memory_id in self._memories:
            raise ValueError(
                f"a memory named "
                f"{validated.memory_id!r} already exists")
        self._check_standing_free(validated)
        return self._hold_memory(validated)

    def _hold_memory(self, validated: SubconsciousMemory
                     ) -> SubconsciousMemory:
        if validated.memory_id is None:
            validated = replace(
                validated,
                memory_id=self._fresh_memory_id(set(self._memories)))
        self._memories[validated.memory_id] = validated
        self._memory_order.append(validated.memory_id)
        return validated

    def register_book(self, book: Any) -> SubconsciousBook:
        """Register every memory of one book, in order.

        The book is judged whole, and against the
        held book, before any of its memories is
        held: a refusal holds nothing new.
        """
        validated = build_book(book)
        if self._title is not None and validated.title != self._title:
            raise ValueError(
                "this registry already holds a subconscious "
                "book under a different title")
        for memory in validated.memories:
            if memory.memory_id in self._memories:
                raise ValueError(
                    f"a memory named "
                    f"{memory.memory_id!r} already exists")
        _judge_memories(validated.memories, held=self.list_memories())
        self._title = validated.title
        for memory in validated.memories:
            self._hold_memory(memory)
        return self.book()

    def reearn_memory(self, memory_id: Any, *, on: Any
                      ) -> SubconsciousMemory:
        """Re-earn one held memory as of a day.

        The held memory is replaced by its re-earned
        shape - same provenance, same confidence,
        the decay clock reset and the re-earn count
        grown - in its own held place.
        """
        held = self.get_memory(memory_id)
        renewed = reearn_memory(held, on=on)
        self._memories[held.memory_id] = renewed
        return renewed

    def get_memory(self, memory_id: Any) -> SubconsciousMemory:
        """The memory one id names among the held memories."""
        wanted = normalize_member_id(memory_id)
        if wanted not in self._memories:
            raise KeyError(f"unknown memory: {wanted!r}")
        return self._memories[wanted]

    def memory_for_source(self, source_kind: Any, source_ref: Any
                          ) -> SubconsciousMemory:
        """The held memory earned from one shipped piece."""
        kind = normalize_source_kind(source_kind)
        wanted = _check_word(source_ref, "a source ref")
        for memory_id in self._memory_order:
            memory = self._memories[memory_id]
            if memory.source_kind == kind and memory.source_ref == wanted:
                return memory
        raise KeyError(f"no memory held from {kind} {wanted!r}")

    def latest_memory(self) -> SubconsciousMemory:
        """The most recently held memory."""
        if not self._memory_order:
            raise ValueError("no memory is held yet")
        return self._memories[self._memory_order[-1]]

    def list_memories(self) -> Tuple[SubconsciousMemory, ...]:
        """Every held memory, in the order they were held."""
        return tuple(self._memories[item] for item in self._memory_order)

    def book(self) -> SubconsciousBook:
        """The held memories as one validated book."""
        if self._title is None:
            raise ValueError("no subconscious book is held yet")
        return SubconsciousBook(
            title=self._title, memories=self.list_memories())

    def panel(self, as_of: Any = None) -> SubconsciousPanel:
        """Derive the subconscious panel of the whole held book."""
        return derive_panel(self, as_of)

    def verdict(self, as_of: Any = None) -> FreshnessVerdict:
        """Derive the freshness verdict of the whole held book."""
        return derive_verdict(self, as_of)


# ---------------------------------------------------------------------
# The visible surface: how the book stands, read off any book.
# ---------------------------------------------------------------------


def memory_refs(source: Any) -> Tuple[Tuple[str, str], ...]:
    """Every (source kind, source ref) one source's memories name."""
    return tuple(
        (memory.source_kind, memory.source_ref)
        for memory in _held_memories(source))


def total_memories(source: Any) -> int:
    """How many memories one source holds."""
    return len(_held_memories(source))


def memory_record(memory: Any) -> Dict[str, Any]:
    """The session-news record of one subconscious memory."""
    current = memory if isinstance(memory, SubconsciousMemory) \
        else build_memory(memory)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"{current.title} stands in the {current.layer} "
        f"layer, earned from {current.source_kind} "
        f"{current.source_ref} in {current.origin_session} "
        f"on {current.earned_on} at confidence "
        f"{current.confidence} - last earned "
        f"{current.last_earned_on}, re-earned "
        f"{current.reearn_count} time(s).")
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
        f"Subconscious panel as of {current.as_of}: "
        f"{current.total_memories} memories - "
        f"{current.total_core} core, "
        f"{current.total_subconscious} subconscious.")
    return record


def verdict_record(verdict: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of one derived verdict."""
    current = validate_verdict(verdict, source)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Subconscious freshness verdict as of "
        f"{current.as_of}: {current.verdict} - "
        f"{current.total_fresh} fresh, "
        f"{current.total_fading} fading, "
        f"{current.total_stale} stale, "
        f"{current.total_faded} faded of "
        f"{current.total_memories} memories.")
    return record


def book_record(book: Any) -> Dict[str, Any]:
    """The session-news record of one subconscious book."""
    current = book if isinstance(book, SubconsciousBook) \
        else build_book(book)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Subconscious book {current.title}: "
        f"{record['memory_count']} memories named.")
    return record


def plain_words(memory: Any) -> str:
    """One memory, in one plain sentence."""
    current = memory if isinstance(memory, SubconsciousMemory) \
        else build_memory(memory)
    return (
        f"{current.title} - a {current.layer} memory "
        f"from {current.source_kind} {current.source_ref}, "
        f"earned in {current.origin_session} on "
        f"{current.earned_on} by {current.recorded_by} "
        f"at confidence {current.confidence}, fading "
        f"with a half-life of {current.half_life_days} "
        f"days; last earned {current.last_earned_on}, "
        f"re-earned {current.reearn_count} time(s).")


def panel_plain_words(source: Any, as_of: Any = None) -> str:
    """The panel in plain words, in full.

    Accepts a SubconsciousPanel or a book (whose
    panel is derived as of *as_of*, or the book's
    own latest day). The panel is told whole - its
    rows in panel order and its account.
    """
    if isinstance(source, SubconsciousPanel):
        panel = validate_panel(source)
        title = None
    elif isinstance(source, (SubconsciousBook, SubconsciousRegistry)):
        panel = derive_panel(source, as_of)
        title = source.title if isinstance(source, SubconsciousBook) else None
    else:
        raise ValueError(
            f"a subconscious source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    lines.append("Memories, in panel order:")
    for row in panel.rows:
        lines.append(
            f"{row.memory_id}: {row.layer}/{row.freshness} - "
            f"{row.title}: from {row.source_kind} "
            f"{row.source_ref} at {row.effective_confidence} "
            f"of {row.confidence}, {row.age_days} day(s) old")
    lines.extend(panel.account)
    return "\n".join(lines)


def verdict_plain_words(source: Any, as_of: Any = None) -> str:
    """The freshness verdict in plain words, in full."""
    if isinstance(source, FreshnessVerdict):
        verdict = validate_verdict(source)
    elif isinstance(source, (SubconsciousBook, SubconsciousRegistry)):
        verdict = derive_verdict(source, as_of)
    else:
        raise ValueError(
            f"a subconscious source is needed, got {source!r}")
    return (
        f"Freshness verdict as of {verdict.as_of}: "
        f"{verdict.verdict} - {verdict.total_fresh} fresh, "
        f"{verdict.total_fading} fading, "
        f"{verdict.total_stale} stale and "
        f"{verdict.total_faded} faded of "
        f"{verdict.total_memories} memories "
        f"({verdict.total_core} core, "
        f"{verdict.total_subconscious} subconscious) "
        f"from {verdict.distinct_sources} distinct sources.")


def _source_book(source: Any) -> SubconsciousBook:
    if source is None:
        return load_subconscious_v2()
    if isinstance(source, SubconsciousRegistry):
        return source.book()
    if isinstance(source, SubconsciousBook):
        return source
    if isinstance(source, SubconsciousMemory):
        return SubconsciousBook(
            title="One subconscious memory", memories=(source,))
    raise ValueError(
        f"a subconscious book is needed, got {source!r}")


def format_memory(memory: Any, as_of: Any = None) -> str:
    """One memory as a screen block, with its decay as of a day."""
    current = memory if isinstance(memory, SubconsciousMemory) \
        else build_memory(memory)
    day = as_of if as_of is not None else current.last_earned_on
    lines = [
        f"{current.memory_id or '-'}: {current.title} - "
        f"{current.layer} layer, from {current.source_kind} "
        f"{current.source_ref} (read from {current.source})",
        f"Earned in {current.origin_session} on "
        f"{current.earned_on} by {current.recorded_by} at "
        f"confidence {current.confidence}; half-life "
        f"{current.half_life_days} day(s), last earned "
        f"{current.last_earned_on}, re-earned "
        f"{current.reearn_count} time(s).",
        f"As of {day}: effective confidence "
        f"{effective_confidence(current, day)}, "
        f"{freshness_state(current, day)}, "
        f"{age_days(current, day)} day(s) since it was "
        f"last earned.",
    ]
    return "\n".join(lines)


def format_memories(source: Any = None, layer: Any = None,
                    source_kind: Any = None, as_of: Any = None) -> str:
    """Memories of one book, in held order, optionally filtered.

    With *layer* named, only that layer's memories
    show; with *source_kind* named, only memories
    earned from that kind.
    """
    book = _source_book(source)
    wanted_layer = normalize_memory_layer(layer) if layer is not None else None
    wanted_kind = normalize_source_kind(source_kind) \
        if source_kind is not None else None
    lines = [
        f"{memory.memory_id or '-'}: {memory.title} - "
        f"{memory.layer}/{memory.source_kind} "
        f"{memory.source_ref} at confidence {memory.confidence}, "
        f"last earned {memory.last_earned_on}"
        for memory in book.memories
        if (wanted_layer is None or memory.layer == wanted_layer)
        and (wanted_kind is None or memory.source_kind == wanted_kind)]
    if not lines:
        lines.append("No memories stand in the book on that reading.")
    return "\n".join(lines)


def format_panel(source: Any = None, as_of: Any = None) -> str:
    """The panel as a screen block: every row and the account.

    Accepts a SubconsciousPanel or a book; a book
    shows the panel derived from it as of *as_of*
    (its own latest day when none is named).
    """
    if isinstance(source, SubconsciousPanel):
        panel = validate_panel(source)
        lines: list = []
    else:
        book = _source_book(source)
        panel = derive_panel(book, as_of)
        lines = [f"Panel in {book.title}:"]
    lines.append("Memories, in panel order:")
    for row in panel.rows:
        lines.append(
            f"{row.memory_id}: {row.layer}/{row.freshness} - "
            f"{row.title}: from {row.source_kind} "
            f"{row.source_ref} at {row.effective_confidence} "
            f"of {row.confidence}, {row.age_days} day(s) old, "
            f"re-earned {row.reearn_count} time(s)")
    lines.extend(panel.account)
    return "\n".join(lines)


def format_verdict(source: Any = None, as_of: Any = None) -> str:
    """The freshness verdict as a screen block."""
    if isinstance(source, FreshnessVerdict):
        verdict = validate_verdict(source)
        lines: list = []
    else:
        book = _source_book(source)
        verdict = derive_verdict(book, as_of)
        lines = [f"Verdict in {book.title}:"]
    lines.append(
        f"{verdict.verdict}: {verdict.total_fresh} fresh, "
        f"{verdict.total_fading} fading, {verdict.total_stale} "
        f"stale, {verdict.total_faded} faded of "
        f"{verdict.total_memories} memories as of "
        f"{verdict.as_of} - {verdict.total_core} core, "
        f"{verdict.total_subconscious} subconscious, from "
        f"{verdict.distinct_sources} distinct sources. "
        f"A faded memory stands until it is re-earned: "
        f"re-earning resets its decay clock at the "
        f"trust it was earned with.")
    return "\n".join(lines)


def format_subconscious_screen(source: Any = None, as_of: Any = None) -> str:
    """The whole slice, in plain words, for /subconscious.

    With nothing named, the shipped example
    subconscious book is shown - the example this
    slice ships - so the screen is never empty.
    """
    book = _source_book(source)
    lines = ["The Subconscious v2 (M-165) - " + PLAIN_EXPLANATION, ""]
    for memory in book.memories:
        lines.append(format_memory(memory, as_of))
    lines.append("")
    lines.append(format_panel(book, as_of))
    lines.append("")
    lines.append(format_verdict(book, as_of))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_subconscious_args(args: Any) -> Tuple[str, Any]:
    """Parse the /subconscious grammar both surfaces share.

    No words (or ``show`` / ``list``) shows the
    subconscious book; ``memory <memory-id>`` shows
    one memory with its provenance whole; ``layer
    <core|subconscious>`` shows one layer's
    memories; ``source <source-kind>`` shows the
    memories earned from one kind; ``panel`` shows
    the panel derived from the whole book;
    ``verdict`` shows the freshness verdict derived
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
    if head == "memory" and len(words) == 2:
        try:
            return (head, normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "layer" and len(words) == 2:
        try:
            return (head, normalize_memory_layer(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "source" and len(words) == 2:
        try:
            return (head, normalize_source_kind(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
