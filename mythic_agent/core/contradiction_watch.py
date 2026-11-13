"""Contradiction watch (All-Features roadmap slice M-166).

Part VII continues. The roadmap's words:
``when new evidence contradicts a stored memory,
the newer truth wins *visibly* - the map shows
the correction.``

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
  crew memory (``core/crew_memory.py``, M-133)
  and the subconscious v2
  (``core/subconscious_v2.py``, M-165), which
  holds a memory with its provenance, confidence
  and decay. What none of those layers holds is
  the correction itself: the moment newer
  evidence contradicts one of those stored
  memories, which truth stands, and how the map
  shows it.
* This slice is that correction, as a pure
  layer: one contradiction watch validated as
  data WITH ITS PROVENANCE WHOLE - the stored
  memory it stands over, named by the kind of
  holding it stands in and the shipped piece's
  id alone, and the stored claim in the
  watcher's own words; the newer evidence
  against it, in its own words, where it was
  read from and the day the contradiction was
  found; who recorded the watch, the session it
  was raised in and where the watch was read
  from. The winner is never in question and
  never stored loose: the newer truth wins, by
  the roadmap's own words, so the correction the
  map shows is DERIVED from the watch - the
  stored claim struck through by the evidence
  that replaces it - and a stored panel or
  verdict whose word is not its own tallies'
  word refuses. Watches are composed BY IMPORT
  from the shipped holdings they stand over (a
  map entry, a session note, a ledger candidate,
  a crew fact, a cross-project lesson, a v2
  memory), each judged by its own layer's
  validation, ids and refs only across the
  seams. The shipped data file
  (``mythic_agent/data/contradiction_watch.yaml``)
  holds one example book in exactly the shape a
  real book file takes, a loader reads a book
  file anywhere on disk, the contradiction panel
  is DERIVED from the whole book (every watch
  carried whole, in a settled order, the
  correction shown on every row), a correction
  VERDICT is derived for the whole book, watches
  are shaped as session news, and a small
  in-memory registry model holds watches one by
  one. The agent layer owns holding a book for a
  session and raising a watch over one of the
  session's own subconscious memories.

Honesty rules, enforced here and pinned by tests:

* **Provenance whole, ids only across the seam.**
  A watch names the stored memory it stands
  over - kind and the shipped piece's id - and
  nothing else of the piece crosses: the piece's
  own words stay in its own layer, judged by its
  own layer's validator. The stored claim stands
  in the watcher's own words, recorded when the
  watch is raised.
* **The newer truth wins, visibly.** The winner
  is derived, never chosen: on every watch, on
  every panel row and in every verdict, the
  evidence wins and the stored claim is shown
  corrected - never silently replaced, never
  left standing beside its contradiction as if
  both were true.
* **The stored memory's fate is this layer's
  stated rule only.** A watch corrects the map:
  the stored memory stands corrected ON THIS
  LAYER's panel, and its own holding is not
  touched - no live memory is overwritten,
  edited or deleted by a watch, silently or
  otherwise. What its own layer does with the
  correction is that layer's road, not this
  slice's.
* **One correction per memory.** A stored memory
  is corrected once in a book: one watch per
  memory kind and memory ref stands, so the
  correction the map shows never forks.
* **Data only.** This layer holds corrections
  as data: it sends nothing, posts nothing,
  schedules nothing, calls no model, persists
  nothing and writes no live memory - raising a
  watch changes no shipped holding.
"""

from dataclasses import dataclass
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
from .subconscious_v2 import SubconsciousMemory
from .subconscious_v2 import validate_memory as _validate_v2_memory
from .validation import ValidationError

__all__ = [
    "CONTRADICTION_WATCH_RESOURCE",
    "CONTRADICTION_WATCH_SCHEMA",
    "CONTRADICTION_WATCH_SLICE",
    "PLAIN_EXPLANATION",
    "MEMORY_KINDS",
    "VERDICT_WORDS",
    "WINNER",
    "USAGE",
    "ContradictionBook",
    "ContradictionPanel",
    "ContradictionPanelRow",
    "ContradictionRegistry",
    "ContradictionWatch",
    "CorrectionVerdict",
    "KindCount",
    "build_book",
    "build_panel",
    "build_verdict",
    "build_watch",
    "correction_line",
    "derive_panel",
    "derive_verdict",
    "format_contradiction_screen",
    "format_panel",
    "format_verdict",
    "format_watch",
    "format_watches",
    "inspect_watch_source",
    "load_contradiction_watch",
    "load_contradiction_watch_file",
    "normalize_memory_kind",
    "panel_plain_words",
    "panel_record",
    "plain_words",
    "parse_contradiction_args",
    "book_record",
    "total_watches",
    "validate_book",
    "validate_panel",
    "validate_verdict",
    "validate_watch",
    "verdict_plain_words",
    "verdict_record",
    "watch_for",
    "watch_from_crew_entry",
    "watch_from_cross_project_lesson",
    "watch_from_ledger_candidate",
    "watch_from_map_entry",
    "watch_from_session_note",
    "watch_from_subconscious_memory",
    "watch_record",
    "watch_refs",
    "winner_of",
]

CONTRADICTION_WATCH_SLICE = "M-166"

CONTRADICTION_WATCH_RESOURCE = "contradiction_watch.yaml"

CONTRADICTION_WATCH_SCHEMA = "mythic.contradiction_watch/1"

#: The holdings a stored memory may stand in:
#: the shipped memory layers a watch may stand
#: over, by the kind of piece it names.
MEMORY_KINDS = (
    "memory-map", "session-note", "cross-project-lesson",
    "ledger-candidate", "crew-fact", "subconscious-memory",
    "vector-record", "manual")

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
    "vector-record": "vector-record",
    "vector_record": "vector-record",
    "vector": "vector-record",
    "manual": "manual",
    "by-hand": "manual",
}

#: Who wins a contradiction, by the roadmap's
#: own words: the newer truth - the evidence -
#: wins, always. Derived, never stored loose.
WINNER = "evidence"

#: The words a whole book's correction verdict
#: may carry, quietest first: how much of the
#: map the corrections touch.
VERDICT_WORDS = ("correcting", "contested", "overturned")

_WATCH_KEYS = frozenset({
    "watch_id", "id", "title", "name", "subject",
    "memory_kind", "kind", "memory_ref", "ref",
    "stored_claim", "claim", "stored",
    "evidence_claim", "evidence", "newer",
    "evidence_source", "evidence_from",
    "evidence_ref",
    "found_on", "day", "date",
    "recorded_by", "recorder", "by", "who",
    "source", "origin_session", "session",
})

_ROW_KEYS = frozenset({
    "watch_id", "id", "title",
    "memory_kind", "memory_ref",
    "stored_claim", "evidence_claim",
    "winner", "found_on",
})

_KIND_COUNT_KEYS = frozenset({"kind", "items", "count"})

_PANEL_KEYS = frozenset({
    "panel_id", "id", "rows", "watches",
    "total_watches", "total",
    "total_corrected", "corrected",
    "distinct_memories", "memories",
    "kind_counts", "kinds",
    "as_of", "day",
    "account", "statements",
})

_VERDICT_KEYS = frozenset({
    "total_watches", "total",
    "total_corrected", "corrected",
    "distinct_memories", "memories",
    "distinct_kinds", "kinds",
    "earliest_on", "earliest",
    "latest_on", "latest",
    "verdict",
})

_BOOK_KEYS = frozenset({"title", "name"})

_CONTRADICTION_BOOK_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "canon_note", "guide", "watches", "records", "panels",
})

_EXAMPLE_TITLE = "Contradiction watch at the M-165 slice boundary"

_EXAMPLE_WATCH_IDS = (
    "watch-verify-on-devices", "watch-kubuntu-lts",
    "watch-muse-renewal", "watch-reap-at-bank")

_EXAMPLE_FIRST_WATCH_ID = "watch-verify-on-devices"

_EXAMPLE_FIRST_WATCH_TITLE = (
    "verify on his devices, not the VM")

_EXAMPLE_PANEL_ID = "panel-m165-boundary"

_EXAMPLE_AS_OF = "2026-11-09"

_EXAMPLE_PANEL_ROW_IDS = (
    "watch-verify-on-devices", "watch-muse-renewal",
    "watch-reap-at-bank", "watch-kubuntu-lts")

PLAIN_EXPLANATION = (
    "Contradiction watch: when new evidence "
    "contradicts a stored memory, the newer truth "
    "wins visibly - the map shows the correction. "
    "A watch stands over one stored memory, named "
    "by the kind of holding it stands in and the "
    "shipped piece's id alone, and carries its "
    "provenance whole: the stored claim in the "
    "watcher's own words, the newer evidence in "
    "its own words, where the evidence was read "
    "from, the day the contradiction was found, "
    "who recorded the watch and the session it was "
    "raised in. The winner is derived, never "
    "chosen - the evidence wins, and the panel "
    "shows the stored claim corrected by it, so a "
    "correction is never silent and the stored "
    "claim never stands beside its contradiction "
    "as if both were true. The stored memory's own "
    "holding is not touched: the correction stands "
    "on this layer's map only. The contradiction "
    "panel is derived from the book at call time, "
    "and the correction verdict is derived for the "
    "whole book. This layer holds corrections as "
    "data only: it sends nothing, posts nothing, "
    "schedules nothing, calls no model, persists "
    "nothing and writes no live memory."
)

USAGE = (
    "Usage: /contradiction, /contradiction show, "
    "/contradiction watch <watch-id>, "
    "/contradiction kind <memory-kind>, "
    "/contradiction panel, /contradiction verdict"
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
    ``lesson``, ``subconscious``, ``vector``) read
    onto their kinds. Anything else raises,
    plainly naming the set.
    """
    if isinstance(value, str):
        wanted = _KIND_ALIASES.get(value.strip().lower())
        if wanted is not None:
            return wanted
    raise ValueError(
        "a memory kind must be one of %s, got %r"
        % ("/".join(MEMORY_KINDS), value))


# ---------------------------------------------------------------------
# The contradiction watch: a stored memory, its evidence, as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class ContradictionWatch:
    """One contradiction: a stored memory, corrected visibly.

    ``title`` names the watch in plain words;
    the stored memory it stands over is named by
    ``memory_kind`` (the holding it stands in)
    and ``memory_ref`` (the shipped piece's id
    alone - the piece's own words never cross
    into this record). ``stored_claim`` is what
    the stored memory says, in the watcher's own
    words, recorded when the watch was raised.
    The newer truth stands beside it:
    ``evidence_claim`` is what the newer evidence
    says, ``evidence_source`` where that evidence
    was read from, and ``evidence_ref`` the
    shipped piece the evidence stands in, by id
    alone, when it stands in one. The provenance
    stands whole beside those: ``found_on`` the
    day the contradiction was found,
    ``recorded_by`` who recorded the watch,
    ``origin_session`` the session it was raised
    in and ``source`` where the watch was read
    from. Who wins is never a field: the newer
    truth wins, derived by :func:`winner_of`, and
    the correction the map shows is derived by
    :func:`correction_line`.
    """

    title: str
    memory_kind: str
    memory_ref: str
    stored_claim: str
    evidence_claim: str
    evidence_source: str
    found_on: str
    recorded_by: str
    source: str
    origin_session: str
    evidence_ref: Optional[str] = None
    watch_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.watch_id is not None:
            object.__setattr__(
                self, "watch_id", normalize_member_id(self.watch_id))
        object.__setattr__(
            self, "title", _check_title(self.title, "a watch's title"))
        object.__setattr__(
            self, "memory_kind", normalize_memory_kind(self.memory_kind))
        object.__setattr__(
            self, "memory_ref",
            _check_word(self.memory_ref, "a watch's memory ref"))
        object.__setattr__(
            self, "stored_claim",
            _check_long_text(self.stored_claim, "a stored claim"))
        object.__setattr__(
            self, "evidence_claim",
            _check_long_text(self.evidence_claim, "an evidence claim"))
        if self.stored_claim == self.evidence_claim:
            raise ValueError(
                "a watch whose evidence repeats its stored "
                "claim contradicts nothing")
        object.__setattr__(
            self, "evidence_source",
            _check_title(
                self.evidence_source, "a watch's evidence source"))
        if self.evidence_ref is not None:
            object.__setattr__(
                self, "evidence_ref",
                _check_word(self.evidence_ref, "a watch's evidence ref"))
        object.__setattr__(
            self, "found_on",
            _check_day(self.found_on, "a watch's found-on day"))
        object.__setattr__(
            self, "recorded_by",
            _check_title(self.recorded_by, "a watch's recorder"))
        object.__setattr__(
            self, "source",
            _check_title(self.source, "a watch's source"))
        object.__setattr__(
            self, "origin_session",
            _check_word(self.origin_session, "a watch's origin session"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "contradiction_watch_watch",
            "slice": CONTRADICTION_WATCH_SLICE,
            "watch_id": self.watch_id,
            "title": self.title,
            "memory_kind": self.memory_kind,
            "memory_ref": self.memory_ref,
            "stored_claim": self.stored_claim,
            "evidence_claim": self.evidence_claim,
            "evidence_source": self.evidence_source,
            "evidence_ref": self.evidence_ref,
            "found_on": self.found_on,
            "recorded_by": self.recorded_by,
            "source": self.source,
            "origin_session": self.origin_session,
            "winner": WINNER,
            "correction": correction_line(self),
        }


def _check_watch_ref(value: Any) -> "ContradictionWatch":
    if isinstance(value, ContradictionWatch):
        return value
    if isinstance(value, dict):
        return validate_watch(value)
    raise ValueError(f"a contradiction watch is needed, got {value!r}")


def validate_watch(watch: Any) -> ContradictionWatch:
    """Validate one watch into a ContradictionWatch.

    Accepts a watch or a mapping naming a ``title``
    (or ``name`` / ``subject``), a ``memory_kind``
    (or ``kind``), a ``memory_ref`` (or ``ref``), a
    ``stored_claim`` (or ``claim`` / ``stored``), an
    ``evidence_claim`` (or ``evidence`` /
    ``newer``), an ``evidence_source`` (or
    ``evidence_from``), a ``found_on`` (or ``day``
    / ``date``), a ``recorded_by`` (or ``recorder``
    / ``by`` / ``who``), a ``source``, an
    ``origin_session`` (or ``session``) and,
    optionally, an ``evidence_ref`` and a
    ``watch_id`` (or ``id``). Derived keys a watch
    record carries (``winner``, ``correction``,
    ``type``, ``slice``) are not watch fields and
    refuse as unknown keys. Naming two spellings
    of one field with different values refuses,
    and unknown keys refuse.
    """
    if isinstance(watch, ContradictionWatch):
        return watch
    if not isinstance(watch, dict):
        raise ValueError(f"a contradiction watch is needed, got {watch!r}")
    unknown = set(watch) - _WATCH_KEYS
    if unknown:
        raise ValueError(
            "unknown watch keys: %s" % ", ".join(sorted(unknown)))

    def _needed(spellings: Tuple[str, ...], what: str) -> Any:
        value = _pick_any(watch, spellings, what)
        if value is None:
            raise ValueError(f"a watch is missing its {what}")
        return value

    kwargs: Dict[str, Any] = {
        "title": _needed(("title", "name", "subject"), "title"),
        "memory_kind": _needed(("memory_kind", "kind"), "memory kind"),
        "memory_ref": _needed(("memory_ref", "ref"), "memory ref"),
        "stored_claim": _needed(
            ("stored_claim", "claim", "stored"), "stored claim"),
        "evidence_claim": _needed(
            ("evidence_claim", "evidence", "newer"), "evidence claim"),
        "evidence_source": _needed(
            ("evidence_source", "evidence_from"), "evidence source"),
        "found_on": _needed(("found_on", "day", "date"), "found day"),
        "recorded_by": _needed(
            ("recorded_by", "recorder", "by", "who"), "recorder"),
        "source": _needed(("source",), "source"),
        "origin_session": _needed(
            ("origin_session", "session"), "origin session"),
    }
    evidence_ref = _pick_any(
        watch, ("evidence_ref",), "evidence refs")
    if evidence_ref is not None:
        kwargs["evidence_ref"] = evidence_ref
    watch_id = _pick_any(watch, ("watch_id", "id"), "watch ids")
    if watch_id is not None:
        kwargs["watch_id"] = watch_id
    return ContradictionWatch(**kwargs)


def build_watch(watch: Any = None, **kwargs: Any) -> ContradictionWatch:
    """Build one validated watch, from a mapping or field words."""
    if isinstance(watch, ContradictionWatch) and not kwargs:
        return watch
    if isinstance(watch, dict) or watch is None:
        merged: Dict[str, Any] = {}
        if isinstance(watch, dict):
            merged.update(watch)
        merged.update(kwargs)
        return validate_watch(merged)
    raise ValueError(f"a contradiction watch is needed, got {watch!r}")


def winner_of(watch: Any) -> str:
    """Who wins one watch: the newer truth, always.

    The winner is derived from the roadmap's own
    words - when new evidence contradicts a stored
    memory, the newer truth wins - so it is the
    evidence on every watch, never a stored choice
    and never the stored memory.
    """
    _check_watch_ref(watch)
    return WINNER


def correction_line(watch: Any) -> str:
    """The correction one watch shows on the map, derived.

    The stored claim, struck through by the newer
    evidence that replaces it - the visible shape
    of the newer truth winning.
    """
    current = _check_watch_ref(watch)
    return (
        f"{current.stored_claim} -> corrected: "
        f"{current.evidence_claim} "
        f"(the newer truth stands, found "
        f"{current.found_on} in {current.evidence_source})")


# ---------------------------------------------------------------------
# Composition: shipped holdings read onto watches, by import.
# ---------------------------------------------------------------------


def _raised_watch(*, memory_kind: str, memory_ref: Optional[str],
                  piece_word: str, title: Any, stored_claim: Any,
                  evidence_claim: Any, evidence_source: Any,
                  evidence_ref: Any, found_on: Any,
                  recorded_by: Any, source: Any,
                  origin_session: Any,
                  watch_id: Any) -> ContradictionWatch:
    if memory_ref is None:
        raise ValueError(
            f"a {piece_word} with no id cannot be watched "
            f"- a contradiction watch names its stored "
            f"memory by id")
    return ContradictionWatch(
        title=title if title is not None else (
            f"the {memory_kind} memory {memory_ref}, corrected"),
        memory_kind=memory_kind, memory_ref=memory_ref,
        stored_claim=stored_claim, evidence_claim=evidence_claim,
        evidence_source=evidence_source, evidence_ref=evidence_ref,
        found_on=found_on, recorded_by=recorded_by, source=source,
        origin_session=origin_session,
        watch_id=watch_id if watch_id is not None else (
            f"watch-{memory_ref}"))


def watch_from_map_entry(entry: Any, *, stored_claim: Any,
                         evidence_claim: Any, evidence_source: Any,
                         found_on: Any, recorded_by: Any,
                         origin_session: Any,
                         source: Any = "contradiction watch",
                         title: Any = None, evidence_ref: Any = None,
                         watch_id: Any = None) -> ContradictionWatch:
    """Raise one watch over a project memory-map entry, by import.

    The entry (M-150) is judged by the map's own
    ``validate_entry``; only its id crosses - it
    stands as the watch's memory ref, of kind
    ``memory-map``. The entry's own title, detail
    and reference are never read here: the stored
    claim stands in the watcher's own words,
    named beside the piece.
    """
    checked = _validate_map_entry(entry)
    return _raised_watch(
        memory_kind="memory-map", memory_ref=checked.entry_id,
        piece_word="memory map entry", title=title,
        stored_claim=stored_claim, evidence_claim=evidence_claim,
        evidence_source=evidence_source, evidence_ref=evidence_ref,
        found_on=found_on, recorded_by=recorded_by, source=source,
        origin_session=origin_session, watch_id=watch_id)


def watch_from_session_note(note: Any, *, stored_claim: Any,
                            evidence_claim: Any,
                            evidence_source: Any, found_on: Any,
                            recorded_by: Any, origin_session: Any,
                            source: Any = "contradiction watch",
                            title: Any = None,
                            evidence_ref: Any = None,
                            watch_id: Any = None) -> ContradictionWatch:
    """Raise one watch over a session-memory note, by import.

    The carried note (M-153) is judged by the
    session layer's own ``validate_note``; only
    its id crosses - it stands as the watch's
    memory ref, of kind ``session-note``.
    """
    checked = _validate_note(note)
    return _raised_watch(
        memory_kind="session-note", memory_ref=checked.note_id,
        piece_word="session note", title=title,
        stored_claim=stored_claim, evidence_claim=evidence_claim,
        evidence_source=evidence_source, evidence_ref=evidence_ref,
        found_on=found_on, recorded_by=recorded_by, source=source,
        origin_session=origin_session, watch_id=watch_id)


def watch_from_cross_project_lesson(lesson: Any, *, stored_claim: Any,
                                    evidence_claim: Any,
                                    evidence_source: Any,
                                    found_on: Any, recorded_by: Any,
                                    origin_session: Any,
                                    source: Any = "contradiction watch",
                                    title: Any = None,
                                    evidence_ref: Any = None,
                                    watch_id: Any = None
                                    ) -> ContradictionWatch:
    """Raise one watch over a cross-project lesson, by import.

    The lesson (M-154) is judged by the
    cross-project layer's own ``validate_lesson``;
    only its id crosses - it stands as the watch's
    memory ref, of kind ``cross-project-lesson``.
    """
    checked = _validate_lesson(lesson)
    return _raised_watch(
        memory_kind="cross-project-lesson",
        memory_ref=checked.lesson_id,
        piece_word="cross-project lesson", title=title,
        stored_claim=stored_claim, evidence_claim=evidence_claim,
        evidence_source=evidence_source, evidence_ref=evidence_ref,
        found_on=found_on, recorded_by=recorded_by, source=source,
        origin_session=origin_session, watch_id=watch_id)


def watch_from_ledger_candidate(candidate: Any, *, stored_claim: Any,
                                evidence_claim: Any,
                                evidence_source: Any, found_on: Any,
                                recorded_by: Any, origin_session: Any,
                                source: Any = "contradiction watch",
                                title: Any = None,
                                evidence_ref: Any = None,
                                watch_id: Any = None
                                ) -> ContradictionWatch:
    """Raise one watch over a self-improving ledger candidate.

    The candidate (M-155) is judged by the
    ledger's own ``validate_candidate``; only its
    id crosses - it stands as the watch's memory
    ref, of kind ``ledger-candidate``.
    """
    checked = _validate_candidate(candidate)
    return _raised_watch(
        memory_kind="ledger-candidate",
        memory_ref=checked.candidate_id,
        piece_word="ledger candidate", title=title,
        stored_claim=stored_claim, evidence_claim=evidence_claim,
        evidence_source=evidence_source, evidence_ref=evidence_ref,
        found_on=found_on, recorded_by=recorded_by, source=source,
        origin_session=origin_session, watch_id=watch_id)


def watch_from_crew_entry(entry: Any, *, stored_claim: Any,
                          evidence_claim: Any, evidence_source: Any,
                          found_on: Any, recorded_by: Any,
                          origin_session: Any,
                          source: Any = "contradiction watch",
                          title: Any = None, evidence_ref: Any = None,
                          watch_id: Any = None) -> ContradictionWatch:
    """Raise one watch over a crew-memory entry, by import.

    The entry (M-133) is judged by crew memory's
    own ``validate_entry``; only its id crosses -
    it stands as the watch's memory ref, of kind
    ``crew-fact``. The fact's own words never
    cross.
    """
    checked = _validate_crew_entry(entry)
    return _raised_watch(
        memory_kind="crew-fact", memory_ref=checked.entry_id,
        piece_word="crew entry", title=title,
        stored_claim=stored_claim, evidence_claim=evidence_claim,
        evidence_source=evidence_source, evidence_ref=evidence_ref,
        found_on=found_on, recorded_by=recorded_by, source=source,
        origin_session=origin_session, watch_id=watch_id)


def watch_from_subconscious_memory(memory: Any, *, stored_claim: Any,
                                   evidence_claim: Any,
                                   evidence_source: Any,
                                   found_on: Any, recorded_by: Any,
                                   origin_session: Any,
                                   source: Any = "contradiction watch",
                                   title: Any = None,
                                   evidence_ref: Any = None,
                                   watch_id: Any = None
                                   ) -> ContradictionWatch:
    """Raise one watch over a subconscious v2 memory, by import.

    The v2 memory (M-165) is judged by its own
    layer's ``validate_memory``; only its id
    crosses - it stands as the watch's memory
    ref, of kind ``subconscious-memory``. A v2
    memory with no id cannot be watched. The
    memory's own title and provenance words never
    cross into the watch.
    """
    checked = _validate_v2_memory(memory)
    return _raised_watch(
        memory_kind="subconscious-memory",
        memory_ref=checked.memory_id,
        piece_word="subconscious memory", title=title,
        stored_claim=stored_claim, evidence_claim=evidence_claim,
        evidence_source=evidence_source, evidence_ref=evidence_ref,
        found_on=found_on, recorded_by=recorded_by, source=source,
        origin_session=origin_session, watch_id=watch_id)


def inspect_watch_source(piece: Any) -> Dict[str, Any]:
    """Inspect one shipped piece: its kind and ref only.

    The piece is judged by the layer that owns its
    type, never by whichever validator happens to
    accept its shape first. A watch reports the
    memory it stands over; each shipped holding
    reports the kind and ref a watch raised over
    it would carry. A piece no shipped layer owns
    refuses.
    """
    if isinstance(piece, ContradictionWatch):
        return {"memory_kind": piece.memory_kind,
                "memory_ref": piece.memory_ref}
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
                checked, "memory_id", None)
            return {"memory_kind": kind, "memory_ref": ref}
    raise ValueError(
        f"no shipped layer owns this piece, got {piece!r}")


# ---------------------------------------------------------------------
# The contradiction panel: every watch carried whole, derived.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class ContradictionPanelRow:
    """One watch carried whole into the panel, its correction shown.

    Every field is the watch's own head - its id,
    title, the memory it stands over (kind and
    ref), both claims and the day the
    contradiction was found - beside the winner
    read off the watch itself: the evidence, by
    the roadmap's own words. :func:`validate_row`
    judged against its watch refuses a row whose
    fields disagree with the row it derives.
    """

    watch_id: str
    title: str
    memory_kind: str
    memory_ref: str
    stored_claim: str
    evidence_claim: str
    winner: str
    found_on: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "watch_id", normalize_member_id(self.watch_id))
        object.__setattr__(
            self, "title", _check_title(self.title, "a row's title"))
        object.__setattr__(
            self, "memory_kind", normalize_memory_kind(self.memory_kind))
        object.__setattr__(
            self, "memory_ref",
            _check_word(self.memory_ref, "a row's memory ref"))
        object.__setattr__(
            self, "stored_claim",
            _check_long_text(self.stored_claim, "a row's stored claim"))
        object.__setattr__(
            self, "evidence_claim",
            _check_long_text(
                self.evidence_claim, "a row's evidence claim"))
        word = _clean_text(self.winner, "a row's winner")
        if word != WINNER:
            raise ValueError(
                f"a row's winner must be the newer truth "
                f"({WINNER!r}) - the stored memory never "
                f"wins its own contradiction, got {word!r}")
        object.__setattr__(self, "winner", word)
        object.__setattr__(
            self, "found_on",
            _check_day(self.found_on, "a row's found-on day"))

    @property
    def sort_key(self) -> Tuple[str, str, str]:
        """This row's place in panel order (derived).

        Rows stand by the day the contradiction was
        found, then title, then watch id - the
        corrections in the order they landed.
        """
        return (self.found_on, self.title.lower(), self.watch_id)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "contradiction_watch_panel_row",
            "slice": CONTRADICTION_WATCH_SLICE,
            "watch_id": self.watch_id,
            "title": self.title,
            "memory_kind": self.memory_kind,
            "memory_ref": self.memory_ref,
            "stored_claim": self.stored_claim,
            "evidence_claim": self.evidence_claim,
            "winner": self.winner,
            "found_on": self.found_on,
        }


def _row_for_watch(watch: ContradictionWatch) -> ContradictionPanelRow:
    return ContradictionPanelRow(
        watch_id=watch.watch_id, title=watch.title,
        memory_kind=watch.memory_kind, memory_ref=watch.memory_ref,
        stored_claim=watch.stored_claim,
        evidence_claim=watch.evidence_claim,
        winner=winner_of(watch), found_on=watch.found_on)


def _check_row_ref(value: Any) -> ContradictionPanelRow:
    if isinstance(value, ContradictionPanelRow):
        return value
    if isinstance(value, dict):
        return validate_row(value)
    raise ValueError(f"a panel row is needed, got {value!r}")


def validate_row(row: Any, watch: Any = None) -> ContradictionPanelRow:
    """Validate one panel row into a ContradictionPanelRow.

    Accepts a row or a mapping naming its fields.
    With *watch* given, the row is judged against
    the row that watch derives.
    """
    if isinstance(row, ContradictionPanelRow):
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

        current = ContradictionPanelRow(
            watch_id=_needed(("watch_id", "id"), "watch id"),
            title=_needed(("title",), "title"),
            memory_kind=_needed(("memory_kind",), "memory kind"),
            memory_ref=_needed(("memory_ref",), "memory ref"),
            stored_claim=_needed(("stored_claim",), "stored claim"),
            evidence_claim=_needed(
                ("evidence_claim",), "evidence claim"),
            winner=_needed(("winner",), "winner"),
            found_on=_needed(("found_on",), "found-on day"))
    else:
        raise ValueError(f"a panel row must be a mapping, got {row!r}")
    if watch is not None:
        derived = _row_for_watch(_check_watch_ref(watch))
        if current != derived:
            raise ValueError(
                "a stored row disagrees with the row "
                "its watch derives")
    return current


def build_row(row: Any = None, watch: Any = None,
              **kwargs: Any) -> ContradictionPanelRow:
    """Build one validated row, from a mapping or field words."""
    if isinstance(row, ContradictionPanelRow) and not kwargs:
        return validate_row(row, watch)
    if isinstance(row, dict) or row is None:
        merged: Dict[str, Any] = {}
        if isinstance(row, dict):
            merged.update(row)
        merged.update(kwargs)
        return validate_row(merged, watch)
    return validate_row(row, watch)


@dataclass(frozen=True)
class KindCount:
    """How many of a panel's watches stand over one memory kind."""

    kind: str
    items: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "kind", normalize_memory_kind(self.kind))
        object.__setattr__(
            self, "items", _check_count(self.items, "a kind count"))

    def to_record(self) -> Dict[str, Any]:
        return {"kind": self.kind, "items": self.items}


def _check_kind_count_ref(value: Any) -> KindCount:
    if isinstance(value, KindCount):
        return value
    if isinstance(value, dict):
        unknown = set(value) - _KIND_COUNT_KEYS
        if unknown:
            raise ValueError(
                "unknown kind-count keys: %s"
                % ", ".join(sorted(unknown)))
        kind = _pick_any(value, ("kind",), "kinds")
        if kind is None:
            raise ValueError("a kind count is missing its kind")
        items = _pick_any(value, ("items", "count"), "counts")
        if items is None:
            raise ValueError("a kind count is missing its count")
        return KindCount(kind=kind, items=items)
    raise ValueError(f"a kind count is needed, got {value!r}")


def _panel_account(total_watches: int, total_corrected: int,
                   distinct_memories: int,
                   kind_counts: Tuple[KindCount, ...], as_of: str
                   ) -> Tuple[str, ...]:
    tallies = ", ".join(
        f"{count.kind} {count.items}"
        for count in sorted(kind_counts, key=lambda count: count.kind))
    return (
        f"The contradiction panel holds {total_watches} "
        f"watches as of {as_of}: {total_corrected} "
        f"corrections shown over {distinct_memories} "
        f"stored memories: {tallies}.",
        "Rows stand by the day the contradiction was "
        "found, then title, then watch id, so two panels "
        "of one book diff cleanly, line by line.",
        "Every row shows its correction: the stored "
        "claim and the newer evidence that replaces it, "
        "with the evidence named the winner - the newer "
        "truth wins visibly, and no stored claim stands "
        "beside its contradiction as if both were true.",
        "The panel is read off the book at call time - "
        "it is derived, never stored loose - and a "
        "watch corrects the map only: no stored "
        "memory's own holding is overwritten by it.",
    )


@dataclass(frozen=True)
class ContradictionPanel:
    """The contradiction panel of one book, derived.

    ``rows`` are the book's watches carried whole,
    in panel order (by the day each contradiction
    was found, then title, then watch id), each
    showing its correction; ``total_watches`` is
    the rows' own count, ``total_corrected`` the
    corrections shown - every watch corrects, by
    the roadmap's words, so the two counts stand
    equal and a panel that says otherwise refuses;
    ``distinct_memories`` counts the stored
    memories the rows stand over, and
    ``kind_counts`` the per-kind tallies of their
    holdings. ``as_of`` is the rows' own latest
    found day. ``account`` is read off those
    numbers. A panel whose rows stand out of
    panel order, or whose tallies are not its own
    rows' tallies, refuses at construction;
    :func:`validate_panel` judged against a book
    refuses a stored panel that disagrees with
    the derived one.
    """

    rows: Tuple[ContradictionPanelRow, ...] = ()
    total_watches: int = 0
    total_corrected: int = 0
    distinct_memories: int = 0
    kind_counts: Tuple[KindCount, ...] = ()
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
            if row.watch_id in seen:
                raise ValueError(
                    f"a panel row for watch {row.watch_id!r} "
                    f"already exists")
            seen.add(row.watch_id)
        keys = [row.sort_key for row in rows]
        if keys != sorted(keys):
            raise ValueError(
                "a panel's rows must stand in panel order "
                "(by found day, then title, then watch id)")
        object.__setattr__(self, "rows", rows)
        object.__setattr__(
            self, "total_watches",
            _check_count(self.total_watches, "a panel's total watches"))
        if self.total_watches != len(rows):
            raise ValueError(
                "a panel's total watches must be its own "
                "rows' count")
        object.__setattr__(
            self, "total_corrected",
            _check_count(
                self.total_corrected, "a panel's total corrected"))
        if self.total_corrected != self.total_watches:
            raise ValueError(
                "a panel's corrections must be its own "
                "watches' count - every watch corrects, "
                "the newer truth always wins")
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
        if isinstance(self.kind_counts, (str, bytes)) \
                or not isinstance(self.kind_counts, (list, tuple)):
            raise ValueError(
                f"a panel's kind counts must be a list, "
                f"got {self.kind_counts!r}")
        kind_counts = tuple(
            _check_kind_count_ref(c) for c in self.kind_counts)
        seen_kinds = set()
        for count in kind_counts:
            if count.kind in seen_kinds:
                raise ValueError(
                    f"a kind count named {count.kind!r} "
                    f"already exists")
            seen_kinds.add(count.kind)
        object.__setattr__(self, "kind_counts", kind_counts)
        if sum(c.items for c in kind_counts) != self.total_watches:
            raise ValueError(
                "a panel's kind counts must sum to its "
                "own total watches")
        tallies = {
            kind: sum(1 for r in rows if r.memory_kind == kind)
            for kind in MEMORY_KINDS}
        for count in kind_counts:
            if count.items != tallies.get(count.kind, 0):
                raise ValueError(
                    "a panel's kind counts must be its "
                    "own rows' counts")
        if {k for k, v in tallies.items() if v} != {
                c.kind for c in kind_counts}:
            raise ValueError(
                "a panel's kind counts must name every "
                "kind its rows stand over")
        object.__setattr__(self, "account", _check_account(self.account))

    def row_for(self, watch_id: Any) -> ContradictionPanelRow:
        """The panel row one watch names in this panel."""
        wanted = normalize_member_id(watch_id)
        for row in self.rows:
            if row.watch_id == wanted:
                return row
        raise KeyError(f"no row in the panel: watch {wanted!r}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "contradiction_watch_panel",
            "slice": CONTRADICTION_WATCH_SLICE,
            "panel_id": self.panel_id,
            "rows": [row.to_record() for row in self.rows],
            "total_watches": self.total_watches,
            "total_corrected": self.total_corrected,
            "distinct_memories": self.distinct_memories,
            "kind_counts": [c.to_record() for c in self.kind_counts],
            "as_of": self.as_of,
            "account": list(self.account),
        }


def _held_watches(source: Any) -> Tuple[ContradictionWatch, ...]:
    if isinstance(source, ContradictionBook):
        return source.watches
    if isinstance(source, ContradictionRegistry):
        return source.list_watches()
    if isinstance(source, (list, tuple)):
        return tuple(_check_watch_ref(item) for item in source)
    raise ValueError(f"contradiction watches are needed, got {source!r}")


def derive_panel(source: Any) -> ContradictionPanel:
    """Derive the contradiction panel from one book.

    The rows are the book's watches carried whole,
    in panel order: by the day each contradiction
    was found, then title, then watch id, each
    showing its correction with the evidence
    named the winner. *source* is a book or a
    registry. A source holding no watch refuses -
    a panel of nothing is no panel.
    """
    watches = _held_watches(source)
    if not watches:
        raise ValueError("a panel needs at least one contradiction watch")
    rows = []
    for watch in watches:
        if watch.watch_id is None:
            raise ValueError(
                "a panel row must name its watch - a "
                "watch with no id refuses derivation")
        rows.append(_row_for_watch(watch))
    rows = tuple(sorted(rows, key=lambda r: r.sort_key))
    tallies = {
        kind: sum(1 for r in rows if r.memory_kind == kind)
        for kind in MEMORY_KINDS}
    kind_counts = tuple(
        KindCount(kind=kind, items=tallies[kind])
        for kind in MEMORY_KINDS if tallies[kind])
    distinct = len({(r.memory_kind, r.memory_ref) for r in rows})
    as_of = max(r.found_on for r in rows)
    return ContradictionPanel(
        rows=rows, total_watches=len(rows),
        total_corrected=len(rows),
        distinct_memories=distinct,
        kind_counts=kind_counts,
        account=_panel_account(
            len(rows), len(rows), distinct, kind_counts, as_of),
        as_of=as_of)


def validate_panel(panel: Any, source: Any = None
                   ) -> ContradictionPanel:
    """Validate one panel into a ContradictionPanel.

    Accepts a panel or a mapping naming ``rows``
    (or ``watches``), a ``total_watches`` (or
    ``total``), a ``total_corrected`` (or
    ``corrected``), a ``distinct_memories`` (or
    ``memories``), ``kind_counts`` (or ``kinds``),
    an ``as_of`` (or ``day``), an ``account`` (or
    ``statements``) and an optional ``panel_id``
    (or ``id``). With *source* given (a book), the
    panel is judged against the panel derived
    from that book.
    """
    if isinstance(panel, ContradictionPanel):
        current = panel
    elif isinstance(panel, dict):
        unknown = set(panel) - _PANEL_KEYS
        if unknown:
            raise ValueError(
                "unknown panel keys: %s" % ", ".join(sorted(unknown)))
        rows = _pick_any(panel, ("rows", "watches"), "rows")
        if rows is None:
            raise ValueError("a panel is missing its rows")
        total = _pick_any(panel, ("total_watches", "total"), "totals")
        if total is None:
            raise ValueError("a panel is missing its total watches")
        corrected = _pick_any(
            panel, ("total_corrected", "corrected"), "corrected totals")
        if corrected is None:
            raise ValueError("a panel is missing its total corrected")
        distinct = _pick_any(
            panel, ("distinct_memories", "memories"),
            "distinct memories")
        if distinct is None:
            raise ValueError("a panel is missing its distinct memories")
        kind_counts = _pick_any(
            panel, ("kind_counts", "kinds"), "kind counts")
        if kind_counts is None:
            raise ValueError("a panel is missing its kind counts")
        as_of = _pick_any(panel, ("as_of", "day"), "as-of days")
        if as_of is None:
            raise ValueError("a panel is missing its as-of day")
        account = _pick_any(panel, ("account", "statements"), "accounts")
        if account is None:
            raise ValueError("a panel names no account of its own")
        kwargs: Dict[str, Any] = {
            "rows": rows, "total_watches": total,
            "total_corrected": corrected,
            "distinct_memories": distinct,
            "kind_counts": kind_counts,
            "as_of": as_of, "account": account}
        panel_id = _pick_any(panel, ("panel_id", "id"), "panel ids")
        if panel_id is not None:
            kwargs["panel_id"] = panel_id
        current = ContradictionPanel(**kwargs)
    else:
        raise ValueError(f"a panel must be a mapping, got {panel!r}")
    if source is not None:
        derived = derive_panel(source)
        if (current.rows != derived.rows
                or current.total_watches != derived.total_watches
                or current.total_corrected != derived.total_corrected
                or current.distinct_memories != derived.distinct_memories
                or current.kind_counts != derived.kind_counts
                or current.as_of != derived.as_of
                or current.account != derived.account):
            raise ValueError(
                "a stored panel disagrees with the panel "
                "derived from its book")
    return current


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> ContradictionPanel:
    """Build one validated panel, from a mapping or field words."""
    if isinstance(panel, ContradictionPanel) and not kwargs:
        return validate_panel(panel, source)
    if isinstance(panel, dict) or panel is None:
        merged: Dict[str, Any] = {}
        if isinstance(panel, dict):
            merged.update(panel)
        merged.update(kwargs)
        return validate_panel(merged, source)
    return validate_panel(panel, source)


# ---------------------------------------------------------------------
# The correction verdict: the whole book judged, as data.
# ---------------------------------------------------------------------


def _verdict_word(distinct_memories: int) -> str:
    """The verdict word a book's own tallies derive.

    ``correcting`` while one stored memory stands
    corrected, ``contested`` when two or three
    stand corrected, and ``overturned`` when four
    or more of the map's stored memories have been
    overturned by newer evidence.
    """
    if distinct_memories >= 4:
        return "overturned"
    if distinct_memories >= 2:
        return "contested"
    return "correcting"


@dataclass(frozen=True)
class CorrectionVerdict:
    """One correction verdict: a whole book judged, as data.

    ``total_watches`` counts the book's watches;
    ``total_corrected`` counts the corrections
    shown - every watch corrects, so the two stand
    equal; ``distinct_memories`` counts the stored
    memories corrected and ``distinct_kinds`` the
    holdings they stand in; ``earliest_on`` and
    ``latest_on`` bound the days the
    contradictions were found; ``verdict`` is the
    word those tallies derive - ``correcting``
    while one stored memory stands corrected,
    ``contested`` when two or three stand
    corrected, and ``overturned`` when four or
    more have been overturned by newer evidence.
    """

    total_watches: int
    total_corrected: int
    distinct_memories: int
    distinct_kinds: int
    earliest_on: str
    latest_on: str
    verdict: str

    def __post_init__(self) -> None:
        for field, what in (
                ("total_watches", "total watches"),
                ("total_corrected", "total corrected"),
                ("distinct_memories", "distinct memories"),
                ("distinct_kinds", "distinct kinds")):
            object.__setattr__(
                self, field, _check_count(getattr(self, field), what))
        if self.total_corrected != self.total_watches:
            raise ValueError(
                "a verdict's corrections must be its own "
                "watches' count - every watch corrects")
        if self.distinct_memories > self.total_watches:
            raise ValueError(
                "a verdict's distinct memories must not "
                "outnumber its watches")
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
        derived = _verdict_word(self.distinct_memories)
        if word != derived:
            raise ValueError(
                f"a verdict's word must be the word its "
                f"own tallies derive ({derived!r}), got {word!r}")
        object.__setattr__(self, "verdict", word)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "contradiction_watch_verdict",
            "slice": CONTRADICTION_WATCH_SLICE,
            "total_watches": self.total_watches,
            "total_corrected": self.total_corrected,
            "distinct_memories": self.distinct_memories,
            "distinct_kinds": self.distinct_kinds,
            "earliest_on": self.earliest_on,
            "latest_on": self.latest_on,
            "verdict": self.verdict,
        }


def derive_verdict(source: Any) -> CorrectionVerdict:
    """Derive the correction verdict for one whole book."""
    watches = _held_watches(source)
    if not watches:
        raise ValueError(
            "a verdict needs at least one contradiction watch")
    distinct = len({(w.memory_kind, w.memory_ref) for w in watches})
    return CorrectionVerdict(
        total_watches=len(watches),
        total_corrected=len(watches),
        distinct_memories=distinct,
        distinct_kinds=len({w.memory_kind for w in watches}),
        earliest_on=min(w.found_on for w in watches),
        latest_on=max(w.found_on for w in watches),
        verdict=_verdict_word(distinct))


def _check_verdict_ref(value: Any) -> CorrectionVerdict:
    if isinstance(value, CorrectionVerdict):
        return value
    if isinstance(value, dict):
        return validate_verdict(value)
    raise ValueError(f"a correction verdict is needed, got {value!r}")


def validate_verdict(verdict: Any, source: Any = None) -> CorrectionVerdict:
    """Validate one verdict into a CorrectionVerdict.

    Accepts a verdict or a mapping naming its
    tallies (short spellings read onto the
    totals), its ``earliest_on`` (or ``earliest``)
    and ``latest_on`` (or ``latest``) days and its
    ``verdict`` word. With *source* given (a
    book), the verdict is judged against the
    verdict derived from that book.
    """
    if isinstance(verdict, CorrectionVerdict):
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

        current = CorrectionVerdict(
            total_watches=_needed(
                ("total_watches", "total"), "total watches"),
            total_corrected=_needed(
                ("total_corrected", "corrected"), "total corrected"),
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
                  **kwargs: Any) -> CorrectionVerdict:
    """Build one validated verdict, from a mapping or field words."""
    if isinstance(verdict, CorrectionVerdict) and not kwargs:
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict) or verdict is None:
        merged: Dict[str, Any] = {}
        if isinstance(verdict, dict):
            merged.update(verdict)
        merged.update(kwargs)
        return validate_verdict(merged, source)
    return validate_verdict(verdict, source)


# ---------------------------------------------------------------------
# The book: one book of watches, and its loaders.
# ---------------------------------------------------------------------


def _judge_watches(watches: Tuple[ContradictionWatch, ...],
                   held: Tuple[ContradictionWatch, ...] = ()) -> None:
    """Judge watches against held watches: the book's laws.

    One correction per stored memory - one memory
    kind and memory ref is corrected once - so the
    correction the map shows never forks inside a
    book. *held* names watches already standing (a
    registry's), judged alongside.
    """
    owners: Dict[Tuple[str, str], str] = {}
    for watch in tuple(held) + tuple(watches):
        key = (watch.memory_kind, watch.memory_ref)
        if key in owners:
            raise ValueError(
                f"a memory corrected twice: {key[0]} "
                f"{key[1]!r} already stands corrected by "
                f"{owners[key]!r} - one correction per memory")
        owners[key] = watch.watch_id or watch.title


@dataclass(frozen=True)
class ContradictionBook:
    """One contradiction watch book: its watches, in held order.

    ``watches`` are the contradiction watches, in
    held order, each with its provenance whole,
    one per stored memory. ``panels`` are the
    book's derivations - contradiction panels of
    the whole book, each judged against the book
    by :func:`validate_book`; ``canon_note`` is
    the book's own note. The total is the watches'
    own count, judged at construction.
    """

    title: str = ""
    watches: Tuple[ContradictionWatch, ...] = ()
    panels: Tuple[ContradictionPanel, ...] = ()
    canon_note: str = ""
    total_watches: Optional[int] = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_title(self.title, "a book's title"))
        if isinstance(self.watches, (str, bytes)) \
                or not isinstance(self.watches, (list, tuple)):
            raise ValueError(
                f"a book's watches must be a list of "
                f"watches, got {self.watches!r}")
        watches = tuple(_check_watch_ref(item) for item in self.watches)
        if not watches:
            raise ValueError("a contradiction book holds at least one watch")
        seen_ids = set()
        for watch in watches:
            if watch.watch_id is not None:
                if watch.watch_id in seen_ids:
                    raise ValueError(
                        f"a watch named "
                        f"{watch.watch_id!r} already exists")
                seen_ids.add(watch.watch_id)
        _judge_watches(watches)
        object.__setattr__(self, "watches", watches)
        if isinstance(self.panels, (str, bytes)) \
                or not isinstance(self.panels, (list, tuple)):
            raise ValueError(
                f"a book's panels must be a list of panels, "
                f"got {self.panels!r}")
        panels = tuple(
            p if isinstance(p, ContradictionPanel)
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
        given = self.total_watches
        if given is None:
            object.__setattr__(self, "total_watches", len(watches))
        else:
            checked = _check_count(given, "a book's total watches")
            if checked != len(watches):
                raise ValueError(
                    "a book's total watches must be its "
                    "own watches' count")
            object.__setattr__(self, "total_watches", checked)

    def watch_for(self, watch_id: Any) -> ContradictionWatch:
        """The watch one id names in this book."""
        wanted = normalize_member_id(watch_id)
        for watch in self.watches:
            if watch.watch_id == wanted:
                return watch
        raise KeyError(f"no watch in the book: {wanted!r}")

    def watch_for_memory(self, memory_kind: Any, memory_ref: Any
                         ) -> ContradictionWatch:
        """The watch standing over one stored memory in this book."""
        kind = normalize_memory_kind(memory_kind)
        wanted = _check_word(memory_ref, "a memory ref")
        for watch in self.watches:
            if watch.memory_kind == kind and watch.memory_ref == wanted:
                return watch
        raise KeyError(f"no watch in the book over {kind} {wanted!r}")

    def panel_for(self, panel_id: Any) -> ContradictionPanel:
        """The stored panel one id names in this book."""
        wanted = normalize_member_id(panel_id)
        for panel in self.panels:
            if panel.panel_id == wanted:
                return panel
        raise KeyError(f"no panel in the book: {wanted!r}")

    def watch_ids(self) -> Tuple[str, ...]:
        """Every held watch id, in held order."""
        return tuple(
            item.watch_id for item in self.watches if item.watch_id)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "contradiction_watch_book",
            "slice": CONTRADICTION_WATCH_SLICE,
            "title": self.title,
            "watch_ids": list(self.watch_ids()),
            "watch_count": len(self.watches),
            "panel_count": len(self.panels),
        }


# The pinned example panel's account is filled in
# below, once the panel machinery stands.
_EXAMPLE_PANEL_ACCOUNT: Tuple[str, ...] = (
    "The contradiction panel holds 4 watches as of "
    "2026-11-09: 4 corrections shown over 4 stored "
    "memories: crew-fact 1, memory-map 1, "
    "session-note 1, subconscious-memory 1.",
    "Rows stand by the day the contradiction was "
    "found, then title, then watch id, so two panels "
    "of one book diff cleanly, line by line.",
    "Every row shows its correction: the stored "
    "claim and the newer evidence that replaces it, "
    "with the evidence named the winner - the newer "
    "truth wins visibly, and no stored claim stands "
    "beside its contradiction as if both were true.",
    "The panel is read off the book at call time - "
    "it is derived, never stored loose - and a "
    "watch corrects the map only: no stored "
    "memory's own holding is overwritten by it.",
)


def validate_book(data: Any, *, require_example: bool = False
                  ) -> ContradictionBook:
    """Validate one contradiction mapping into a book.

    The mapping names a ``schema``, a ``guide``
    mapping (its ``title``), a ``watches`` list (or
    ``records``) and an optional ``panels`` list.
    Every watch stands on its own validation, then
    the whole is judged: watch ids unique, one
    watch per stored memory, and every stored
    panel judged against the book. With
    ``require_example`` the shipped example is held
    to its pinned shape.
    """
    if isinstance(data, ContradictionBook):
        return data
    if not isinstance(data, dict):
        raise ValidationError(
            f"a contradiction book must be a mapping, got {data!r}")
    unknown = set(data) - _CONTRADICTION_BOOK_KEYS
    if unknown:
        raise ValidationError(
            "unknown contradiction-book keys: %s"
            % ", ".join(sorted(unknown)))
    if data.get("schema") != CONTRADICTION_WATCH_SCHEMA:
        raise ValidationError(
            f"a contradiction book must carry schema "
            f"{CONTRADICTION_WATCH_SCHEMA!r}, "
            f"got {data.get('schema')!r}")
    watches = _pick_any(data, ("watches", "records"), "watches")
    if watches is None:
        raise ValidationError("a contradiction book is missing its watches")
    if not isinstance(watches, (list, tuple)):
        raise ValidationError("a contradiction book's watches must be a list")
    if data.get("panels") is not None \
            and not isinstance(data["panels"], (list, tuple)):
        raise ValidationError("a contradiction book's panels must be a list")
    head = data.get("guide") or {}
    if not isinstance(head, dict):
        raise ValidationError("a contradiction book's guide must be a mapping")
    unknown_head = set(head) - _BOOK_KEYS
    if unknown_head:
        raise ValidationError(
            "unknown guide keys: %s" % ", ".join(sorted(unknown_head)))
    try:
        title = _pick_any(head, ("title", "name"), "titles")
        if title is None:
            raise ValidationError("a contradiction book is missing its title")
        note = data.get("canon_note") or ""
        if not isinstance(note, str):
            raise ValidationError("a contradiction book's note must be text")
        book = ContradictionBook(
            title=title, watches=tuple(watches),
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
                "the shipped example contradiction book's "
                "title is not the pinned title")
        if book.watch_ids() != _EXAMPLE_WATCH_IDS:
            raise ValidationError(
                "the shipped example's watches are not "
                "the pinned watches")
        panel = book.panel_for(_EXAMPLE_PANEL_ID)
        if panel.as_of != _EXAMPLE_AS_OF:
            raise ValidationError(
                "the shipped example panel does not stand "
                "as of its pinned day")
        if tuple(r.watch_id for r in panel.rows) != _EXAMPLE_PANEL_ROW_IDS:
            raise ValidationError(
                "the shipped example panel does not name "
                "its pinned rows in panel order")
        if _EXAMPLE_PANEL_ACCOUNT and panel.account != _EXAMPLE_PANEL_ACCOUNT:
            raise ValidationError(
                "the shipped example panel does not carry "
                "its pinned account word-for-word")
        first = book.watches[0]
        if first.watch_id != _EXAMPLE_FIRST_WATCH_ID \
                or first.title != _EXAMPLE_FIRST_WATCH_TITLE:
            raise ValidationError(
                "the shipped example's first watch is "
                "not its pinned watch of its pinned title")
    return book


def build_book(book: Any = None, **kwargs: Any) -> ContradictionBook:
    """Build one validated book, from a mapping or field words."""
    if isinstance(book, ContradictionBook) and not kwargs:
        return book
    if isinstance(book, dict):
        if "schema" in book:
            return validate_book(book)
        merged: Dict[str, Any] = dict(book)
        merged.update(kwargs)
        return ContradictionBook(**merged)
    if book is None:
        return ContradictionBook(**kwargs)
    raise ValueError(f"a contradiction book is needed, got {book!r}")


def _book_from(data: Any, *, require_example: bool) -> ContradictionBook:
    try:
        return validate_book(data, require_example=require_example)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def load_contradiction_watch(
        data: Optional[Dict[str, Any]] = None) -> ContradictionBook:
    """Load and validate the shipped example book (or *data*)."""
    raw = data if data is not None else load_resource(
        CONTRADICTION_WATCH_RESOURCE)
    return _book_from(raw, require_example=True)


def load_contradiction_watch_file(path: Any) -> ContradictionBook:
    """Load and validate a contradiction book from a file at *path*."""
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _book_from(raw, require_example=False)


# ---------------------------------------------------------------------
# The registry model: one book held watch by watch.
# ---------------------------------------------------------------------


class ContradictionRegistry:
    """One book's watches, held one by one.

    The registry holds watches, never panels or
    verdicts: the panel and the correction verdict
    are derivations, read off the whole held book
    at call time. A whole book is judged whole -
    as a book judges it, and against everything
    already held - before its watches are held in
    book order, so a raising never lands partially.
    A watch held here stands apart: a second watch
    over a held memory refuses - one correction
    per memory.
    """

    def __init__(self, book: Any = None) -> None:
        self._title: Optional[str] = None
        self._watches: Dict[str, ContradictionWatch] = {}
        self._watch_order: list = []
        self._next_watch = 1
        if book is not None:
            self.register_book(book)

    def _fresh_watch_id(self, held_ids: Any) -> str:
        while f"watch-{self._next_watch}" in held_ids:
            self._next_watch += 1
        fresh = f"watch-{self._next_watch}"
        self._next_watch += 1
        return fresh

    def _check_standing_free(self, watch: ContradictionWatch) -> None:
        _judge_watches((watch,), held=self.list_watches())

    def register_watch(self, watch: Any) -> ContradictionWatch:
        """Register one watch into the held book."""
        validated = _check_watch_ref(watch)
        if validated.watch_id is not None \
                and validated.watch_id in self._watches:
            raise ValueError(
                f"a watch named "
                f"{validated.watch_id!r} already exists")
        self._check_standing_free(validated)
        return self._hold_watch(validated)

    def _hold_watch(self, validated: ContradictionWatch
                    ) -> ContradictionWatch:
        if validated.watch_id is None:
            from dataclasses import replace
            validated = replace(
                validated,
                watch_id=self._fresh_watch_id(set(self._watches)))
        self._watches[validated.watch_id] = validated
        self._watch_order.append(validated.watch_id)
        return validated

    def register_book(self, book: Any) -> ContradictionBook:
        """Register every watch of one book, in order.

        The book is judged whole, and against the
        held book, before any of its watches is
        held: a refusal holds nothing new.
        """
        validated = build_book(book)
        if self._title is not None and validated.title != self._title:
            raise ValueError(
                "this registry already holds a contradiction "
                "book under a different title")
        for watch in validated.watches:
            if watch.watch_id in self._watches:
                raise ValueError(
                    f"a watch named "
                    f"{watch.watch_id!r} already exists")
        _judge_watches(validated.watches, held=self.list_watches())
        self._title = validated.title
        for watch in validated.watches:
            self._hold_watch(watch)
        return self.book()

    def get_watch(self, watch_id: Any) -> ContradictionWatch:
        """The watch one id names among the held watches."""
        wanted = normalize_member_id(watch_id)
        if wanted not in self._watches:
            raise KeyError(f"unknown watch: {wanted!r}")
        return self._watches[wanted]

    def watch_for_memory(self, memory_kind: Any, memory_ref: Any
                         ) -> ContradictionWatch:
        """The held watch standing over one stored memory."""
        kind = normalize_memory_kind(memory_kind)
        wanted = _check_word(memory_ref, "a memory ref")
        for watch_id in self._watch_order:
            watch = self._watches[watch_id]
            if watch.memory_kind == kind and watch.memory_ref == wanted:
                return watch
        raise KeyError(f"no watch held over {kind} {wanted!r}")

    def latest_watch(self) -> ContradictionWatch:
        """The most recently held watch."""
        if not self._watch_order:
            raise ValueError("no watch is held yet")
        return self._watches[self._watch_order[-1]]

    def list_watches(self) -> Tuple[ContradictionWatch, ...]:
        """Every held watch, in the order they were held."""
        return tuple(self._watches[item] for item in self._watch_order)

    def book(self) -> ContradictionBook:
        """The held watches as one validated book."""
        if self._title is None:
            raise ValueError("no contradiction book is held yet")
        return ContradictionBook(
            title=self._title, watches=self.list_watches())

    def panel(self) -> ContradictionPanel:
        """Derive the contradiction panel of the whole held book."""
        return derive_panel(self)

    def verdict(self) -> CorrectionVerdict:
        """Derive the correction verdict of the whole held book."""
        return derive_verdict(self)


# ---------------------------------------------------------------------
# The visible surface: how the book stands, read off any book.
# ---------------------------------------------------------------------


def watch_refs(source: Any) -> Tuple[Tuple[str, str], ...]:
    """Every (memory kind, memory ref) one source's watches name."""
    return tuple(
        (watch.memory_kind, watch.memory_ref)
        for watch in _held_watches(source))


def watch_for(source: Any, memory_kind: Any, memory_ref: Any
              ) -> ContradictionWatch:
    """The watch one source holds over one stored memory."""
    kind = normalize_memory_kind(memory_kind)
    wanted = _check_word(memory_ref, "a memory ref")
    for watch in _held_watches(source):
        if watch.memory_kind == kind and watch.memory_ref == wanted:
            return watch
    raise KeyError(f"no watch over {kind} {wanted!r}")


def total_watches(source: Any) -> int:
    """How many watches one source holds."""
    return len(_held_watches(source))


def watch_record(watch: Any) -> Dict[str, Any]:
    """The session-news record of one contradiction watch."""
    current = watch if isinstance(watch, ContradictionWatch) \
        else build_watch(watch)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Correction over {current.memory_kind} "
        f"{current.memory_ref}: {current.stored_claim} "
        f"-> corrected: {current.evidence_claim} - the "
        f"newer truth wins, found {current.found_on} in "
        f"{current.evidence_source}.")
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
        f"Contradiction panel as of {current.as_of}: "
        f"{current.total_watches} watches - "
        f"{current.total_corrected} corrections shown "
        f"over {current.distinct_memories} stored "
        f"memories.")
    return record


def verdict_record(verdict: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of one derived verdict."""
    current = validate_verdict(verdict, source)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Contradiction verdict: {current.verdict} - "
        f"{current.total_corrected} corrections over "
        f"{current.distinct_memories} stored memories "
        f"from {current.earliest_on} to "
        f"{current.latest_on}.")
    return record


def book_record(book: Any) -> Dict[str, Any]:
    """The session-news record of one contradiction book."""
    current = book if isinstance(book, ContradictionBook) \
        else build_book(book)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Contradiction book {current.title}: "
        f"{record['watch_count']} watches named.")
    return record


def plain_words(watch: Any) -> str:
    """One watch, in one plain sentence."""
    current = watch if isinstance(watch, ContradictionWatch) \
        else build_watch(watch)
    return (
        f"{current.title} - the {current.memory_kind} "
        f"memory {current.memory_ref} said: "
        f"{current.stored_claim}; the newer evidence "
        f"from {current.evidence_source} says: "
        f"{current.evidence_claim} - the newer truth "
        f"wins, and the map shows the correction.")


def panel_plain_words(source: Any) -> str:
    """The panel in plain words, in full.

    Accepts a ContradictionPanel or a book (whose
    panel is derived). The panel is told whole -
    its rows in panel order and its account.
    """
    if isinstance(source, ContradictionPanel):
        panel = validate_panel(source)
        title = None
    elif isinstance(source, (ContradictionBook, ContradictionRegistry)):
        panel = derive_panel(source)
        title = source.title if isinstance(
            source, ContradictionBook) else None
    else:
        raise ValueError(
            f"a contradiction source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    lines.append("Corrections, in panel order:")
    for row in panel.rows:
        lines.append(
            f"{row.watch_id}: {row.memory_kind}/"
            f"{row.memory_ref} - was: {row.stored_claim} "
            f"now: {row.evidence_claim} "
            f"(winner: {row.winner}, found {row.found_on})")
    lines.extend(panel.account)
    return "\n".join(lines)


def verdict_plain_words(source: Any) -> str:
    """The correction verdict in plain words, in full."""
    if isinstance(source, CorrectionVerdict):
        verdict = validate_verdict(source)
    elif isinstance(source, (ContradictionBook, ContradictionRegistry)):
        verdict = derive_verdict(source)
    else:
        raise ValueError(
            f"a contradiction source is needed, got {source!r}")
    return (
        f"Correction verdict: {verdict.verdict} - "
        f"{verdict.total_corrected} corrections over "
        f"{verdict.distinct_memories} stored memories "
        f"in {verdict.distinct_kinds} holdings, found "
        f"from {verdict.earliest_on} to "
        f"{verdict.latest_on}, of {verdict.total_watches} "
        f"watches - the newer truth wins on every one.")


def _source_book(source: Any) -> ContradictionBook:
    if source is None:
        return load_contradiction_watch()
    if isinstance(source, ContradictionRegistry):
        return source.book()
    if isinstance(source, ContradictionBook):
        return source
    if isinstance(source, ContradictionWatch):
        return ContradictionBook(
            title="One contradiction watch", watches=(source,))
    raise ValueError(
        f"a contradiction book is needed, got {source!r}")


def format_watch(watch: Any) -> str:
    """One watch as a screen block, its correction shown."""
    current = watch if isinstance(watch, ContradictionWatch) \
        else build_watch(watch)
    lines = [
        f"{current.watch_id or '-'}: {current.title} - "
        f"over {current.memory_kind} {current.memory_ref} "
        f"(read from {current.source})",
        f"Stored: {current.stored_claim}",
        f"Newer evidence (from {current.evidence_source}, "
        f"found {current.found_on} by "
        f"{current.recorded_by} in "
        f"{current.origin_session}): "
        f"{current.evidence_claim}",
        f"The map shows the correction: "
        f"{correction_line(current)}",
    ]
    return "\n".join(lines)


def format_watches(source: Any = None, kind: Any = None) -> str:
    """Watches of one book, in held order, optionally filtered.

    With *kind* named, only the watches standing
    over that holding show.
    """
    book = _source_book(source)
    wanted_kind = normalize_memory_kind(kind) if kind is not None else None
    lines = [
        f"{watch.watch_id or '-'}: {watch.title} - "
        f"{watch.memory_kind} {watch.memory_ref}: "
        f"was: {watch.stored_claim} now: "
        f"{watch.evidence_claim} (found {watch.found_on})"
        for watch in book.watches
        if (wanted_kind is None or watch.memory_kind == wanted_kind)]
    if not lines:
        lines.append("No watches stand in the book on that reading.")
    return "\n".join(lines)


def format_panel(source: Any = None) -> str:
    """The panel as a screen block: every row and the account.

    Accepts a ContradictionPanel or a book; a book
    shows the panel derived from it.
    """
    if isinstance(source, ContradictionPanel):
        panel = validate_panel(source)
        lines: list = []
    else:
        book = _source_book(source)
        panel = derive_panel(book)
        lines = [f"Panel in {book.title}:"]
    lines.append("Corrections, in panel order:")
    for row in panel.rows:
        lines.append(
            f"{row.watch_id}: {row.memory_kind}/"
            f"{row.memory_ref} - was: {row.stored_claim} "
            f"now: {row.evidence_claim} "
            f"(winner: {row.winner}, found {row.found_on})")
    lines.extend(panel.account)
    return "\n".join(lines)


def format_verdict(source: Any = None) -> str:
    """The correction verdict as a screen block."""
    if isinstance(source, CorrectionVerdict):
        verdict = validate_verdict(source)
        lines: list = []
    else:
        book = _source_book(source)
        verdict = derive_verdict(book)
        lines = [f"Verdict in {book.title}:"]
    lines.append(
        f"{verdict.verdict}: {verdict.total_corrected} "
        f"corrections over {verdict.distinct_memories} "
        f"stored memories in {verdict.distinct_kinds} "
        f"holdings, found from {verdict.earliest_on} to "
        f"{verdict.latest_on}, of {verdict.total_watches} "
        f"watches. The newer truth wins on every watch: "
        f"the stored claim is shown corrected on the "
        f"map, and its own holding is left exactly as "
        f"it stood.")
    return "\n".join(lines)


def format_contradiction_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /contradiction.

    With nothing named, the shipped example
    contradiction book is shown - the example this
    slice ships - so the screen is never empty.
    """
    book = _source_book(source)
    lines = ["Contradiction Watch (M-166) - " + PLAIN_EXPLANATION, ""]
    for watch in book.watches:
        lines.append(format_watch(watch))
    lines.append("")
    lines.append(format_panel(book))
    lines.append("")
    lines.append(format_verdict(book))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_contradiction_args(args: Any) -> Tuple[str, Any]:
    """Parse the /contradiction grammar both surfaces share.

    No words (or ``show`` / ``list``) shows the
    contradiction book; ``watch <watch-id>`` shows
    one watch with its correction shown; ``kind
    <memory-kind>`` shows the watches standing
    over one holding; ``panel`` shows the panel
    derived from the whole book; ``verdict`` shows
    the correction verdict derived for the whole
    book. Anything else is a usage error naming
    the grammar. Returns ``(action, value-or-None)``.
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
    if head == "watch" and len(words) == 2:
        try:
            return (head, normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "kind" and len(words) == 2:
        try:
            return (head, normalize_memory_kind(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
