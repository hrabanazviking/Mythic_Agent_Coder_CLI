"""Cross-project memory (All-Features roadmap slice M-154).

Part VII continues. The roadmap's words:
``lessons learned in one repo (a flaky test's true
cause, a library's trap) are offerable to other
projects - with provenance, never as silent
contamination.``

What already shipped, and what this slice adds:

* A project's own memory already ships as data:
  the project memory map (``core/project_memory_map.py``,
  M-150) holds a project's facts in its closed
  sections (architecture, decision, gotcha,
  location), and session memory across days
  (``core/session_memory.py``, M-153) carries those
  facts across a session's days. Both stay inside
  the one project: nothing yet lets a lesson
  learned in one repo travel to another.
* This slice is that travelling, as a pure layer:
  a lesson learned in one project, validated as
  data WITH ITS PROVENANCE WHOLE - the project it
  was learned in, the context it was learned in,
  the evidence it stands on, and where in the
  source project it was read from - offered to a
  target project through an offer whose state is
  explicit (offered, accepted, declined or
  withdrawn), never by silent copying. A lesson
  stands in a target project only through an
  accepted offer, and it stands there with its
  provenance still whole, so the receiving project
  can judge it by where it came from. The shipped
  data file (``mythic_agent/data/cross_project_memory.yaml``)
  holds one example book in exactly the shape a
  real book file takes, a loader reads a book file
  anywhere on disk, the composition roads read the
  shipped project memory map and session memory
  onto lessons BY IMPORT, the exchange panel is
  DERIVED from the whole book (every offer standing
  with its lesson whole, in a settled order),
  records are shaped as session news, and a small
  in-memory registry model holds lessons and
  offers one by one. The agent layer owns holding
  a book for a session and offering the session's
  own memory-map lessons onward.

Honesty rules, enforced here and pinned by tests:

* **Provenance, always.** A lesson carries where
  it was learned (its source project), the context
  it was learned in and the evidence it stands on.
  A lesson with no provenance refuses - lessons do
  not travel anonymously, and a bare memory-map
  entry becomes a lesson only when the provenance
  words are named with it.
* **Never silent contamination.** A lesson enters
  another project's memory only through an offer
  in the accepted state. There is no road here
  that copies a lesson into a target project's own
  records: offers are explicit structured states,
  an offer to the lesson's own project refuses
  (that is not cross-project), and what stands
  accepted is derived at call time, provenance
  whole.
* **Composed, never duplicated.** Lessons are the
  shipped project memory map's entries, and the
  shipped session memory's carried notes, read
  onto this layer by import - their sections stay
  the map's closed set, judged by the map's own
  normaliser. No second taxonomy of project facts
  is invented here.
* **The panel is derived, never stored loose.**
  Its rows are the book's offers with their
  lessons carried whole, in settled order
  (accepted first, then offered, then declined,
  then withdrawn; within a state, by source
  project, then lesson title), and its totals are
  the offers' own counts; a stored panel or book
  whose rows, totals, counts or account disagree
  with the derived shape refuses.
* **Data only - offering changes no project.**
  A lesson or an offer here is validated data: no
  model is called, no project's files are written,
  no live memory is updated in any project, and
  nothing persists beyond the session journal news
  the agent layer publishes.
* **Malformed refuses.** A duplicate lesson or
  offer id in one book, the same fact named twice
  by one project, an offer naming a lesson the
  book does not hold, an offer to the lesson's own
  project, the same lesson offered twice to one
  target, a lesson with no provenance, and unknown
  keys in a lesson, an offer, a panel or a book
  mapping all raise instead of being skipped or
  guessed at.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..resources import load_resource
from .crew_members import normalize_member_id
from .project_memory_map import (
    MAP_SECTIONS,
    MemoryMapEntry,
    normalize_section,
)
from .project_memory_map import validate_entry as _validate_map_entry
from .session_memory import CarriedMemory, SessionSituation
from .session_memory import validate_note as _validate_session_note
from .validation import ValidationError

__all__ = [
    "PLAIN_EXPLANATION",
    "CROSS_PROJECT_RESOURCE",
    "CROSS_PROJECT_SCHEMA",
    "CROSS_PROJECT_SLICE",
    "OFFER_STATES",
    "USAGE",
    "CrossProjectBook",
    "CrossProjectRegistry",
    "ExchangePanel",
    "ExchangePanelRow",
    "LessonOffer",
    "OfferStateCount",
    "SharedLesson",
    "accepted_lessons",
    "book_record",
    "build_book",
    "build_lesson",
    "build_offer",
    "build_panel",
    "build_row",
    "derive_panel",
    "format_accepted",
    "format_cross_project_screen",
    "format_lesson",
    "format_lessons",
    "format_offers",
    "format_panel",
    "lesson_from_map_entry",
    "lesson_record",
    "lessons_from_memory_map",
    "lessons_from_session_memory",
    "load_cross_project_memory",
    "load_cross_project_memory_file",
    "normalize_offer_state",
    "offer_record",
    "panel_plain_words",
    "panel_record",
    "parse_cross_project_args",
    "plain_words",
    "validate_book",
    "validate_lesson",
    "validate_offer",
    "validate_panel",
    "validate_row",
]

CROSS_PROJECT_SLICE = "M-154"

#: The packaged data resource holding the example book.
CROSS_PROJECT_RESOURCE = "cross_project_memory.yaml"

#: The schema word a cross-project-memory file must carry.
CROSS_PROJECT_SCHEMA = "mythic.cross_project_memory/1"

#: The states one offer may stand in: a lesson is
#: offered to a target project, and then stands
#: accepted (it may enter that project's memory,
#: provenance whole), declined (the target said no)
#: or withdrawn (the source took the offer back).
OFFER_STATES = ("offered", "accepted", "declined", "withdrawn")

_OFFER_STATE_ALIASES = {
    "offered": "offered",
    "pending": "offered",
    "accepted": "accepted",
    "taken": "accepted",
    "declined": "declined",
    "rejected": "declined",
    "withdrawn": "withdrawn",
    "retracted": "withdrawn",
}

#: The order offers stand in on the exchange panel:
#: what a target holds first, then what awaits its
#: word, then what it refused and what was taken back.
_PANEL_STATE_ORDER = ("accepted", "offered", "declined", "withdrawn")

_LESSON_KEYS = frozenset({
    "lesson_id", "id", "section", "kind",
    "title", "name", "detail", "body",
    "source_project", "from_project", "project",
    "context", "learned_in", "situation",
    "evidence", "proof", "backing",
    "source", "ref", "path", "reference",
})

_OFFER_KEYS = frozenset({
    "offer_id", "id", "lesson_id", "lesson",
    "target_project", "to_project", "target",
    "state", "status", "note", "detail",
})

_ROW_KEYS = frozenset({
    "state", "lesson_id", "id", "title", "detail",
    "source_project", "target_project",
})

_STATE_COUNT_KEYS = frozenset({"state", "items", "count"})

_PANEL_KEYS = frozenset({
    "panel_id", "id", "rows", "offers",
    "total_items", "total", "total_accepted",
    "total_offered", "total_declined",
    "total_withdrawn", "state_counts", "states",
    "account", "statements",
})

_BOOK_KEYS = frozenset({"title", "name"})

_CROSS_PROJECT_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "canon_note", "guide", "lessons", "offers", "panels",
})

#: The shipped example book's title, held to this
#: by the loader's example check.
_EXAMPLE_TITLE = "Cross-project memory at the M-153 slice boundary"

#: The shipped example's lesson ids, in held
#: order, pinned by the loader.
_EXAMPLE_LESSON_IDS = (
    "lesson-commit-before-answer", "lesson-reap-at-bank",
    "lesson-bank-incrementally")

#: The shipped example's first lesson and the
#: project it was learned in, pinned by the loader.
_EXAMPLE_FIRST_LESSON_ID = "lesson-commit-before-answer"

_EXAMPLE_FIRST_LESSON_PROJECT = "samtal"

#: The shipped example's one panel id, and its rows
#: in panel order, pinned by the loader.
_EXAMPLE_PANEL_ID = "panel-m153-boundary"

_EXAMPLE_PANEL_ROW_IDS = (
    "lesson-reap-at-bank", "lesson-commit-before-answer",
    "lesson-bank-incrementally")

_EXAMPLE_PANEL_ACCOUNT = (
    "The exchange panel holds 3 offers: accepted 1, "
    "offered 1, declined 1, withdrawn 0.",
    "Offers stand accepted first, then offered, "
    "then declined, then withdrawn; within a state, "
    "by source project, then lesson title - so two "
    "panels of one book diff cleanly, line by line.",
    "A lesson stands in a target project only "
    "through an accepted offer, and it stands there "
    "with its provenance whole - where it was "
    "learned, in what context, and on what evidence.",
    "The panel is read off the book at call time - "
    "it is derived, never stored loose.",
)

PLAIN_EXPLANATION = (
    "Cross-project memory: a lesson learned in one "
    "project is offerable to other projects - with "
    "provenance, never as silent contamination. A "
    "shared lesson is one fact of a project's memory "
    "map carried with where it was learned (its "
    "source project), the context it was learned in "
    "and the evidence it stands on. A lesson enters "
    "another project only through an offer, an "
    "explicit state - offered, accepted, declined or "
    "withdrawn - and only an accepted offer lets it "
    "stand in the target, provenance whole. The "
    "exchange panel is derived from the book at call "
    "time: every offer standing with its lesson "
    "whole, accepted first, then offered, declined "
    "and withdrawn. This layer holds lessons and "
    "offers as data only: it calls no model, writes "
    "no project's files, updates no live memory and "
    "persists nothing."
)

USAGE = (
    "Usage: /crossmemory, /crossmemory show, "
    "/crossmemory lesson <lesson-id>, "
    "/crossmemory offers, "
    "/crossmemory accepted <project>, "
    "/crossmemory panel"
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


def _check_ref(value: Any) -> str:
    text = _clean_text(value, "a lesson's reference")
    if len(text) > 300 or "\x00" in text:
        raise ValueError(
            f"a lesson's reference must be plain text "
            f"of at most 300 characters, got {len(text)} characters")
    if any(ch.isspace() for ch in text):
        raise ValueError(
            f"a lesson's reference names no spaces, "
            f"got {text!r}")
    return text


def _check_project(value: Any, what: str = "a project") -> str:
    """One project name, judged as one plain word.

    Project names on this layer are the shipped id
    shape (letters, digits, dashes, underscores and
    dots, case kept) - the same word a registry id
    takes - so a source and a target can be compared
    exactly: an offer whose target equals its
    lesson's source is no cross-project offer at all.
    """
    try:
        return normalize_member_id(value)
    except ValueError:
        raise ValueError(
            f"{what} must be one plain project word, "
            f"got {value!r}") from None


def normalize_offer_state(value: Any) -> str:
    """The canonical offer state a word names.

    A state is one of :data:`OFFER_STATES` -
    ``offered``, ``accepted``, ``declined`` or
    ``withdrawn`` - read case-insensitively, with
    ``pending`` read onto ``offered``, ``taken``
    onto ``accepted``, ``rejected`` onto ``declined``
    and ``retracted`` onto ``withdrawn``. Anything
    else raises, plainly naming the four.
    """
    if isinstance(value, str):
        wanted = _OFFER_STATE_ALIASES.get(value.strip().lower())
        if wanted is not None:
            return wanted
    raise ValueError(
        "an offer's state must be one of %s, got %r"
        % ("/".join(OFFER_STATES), value))


# ---------------------------------------------------------------------
# The shared lesson: one project's fact, with its provenance whole.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class SharedLesson:
    """One lesson learned in one project, offerable to others.

    ``section`` is the lesson's section in the
    shipped project memory map's closed set
    (architecture, decision, gotcha, location),
    judged by the map's own normaliser; ``title``
    names the lesson; ``detail`` is the lesson
    itself, in plain words. The provenance stands
    whole beside it: ``source_project`` is the
    project it was learned in, ``context`` is the
    situation it was learned in, ``evidence`` is
    what it stands on, ``source`` names where in
    the source project it was read from, and
    ``ref`` is where the thing it names lives. A
    lesson with any provenance word missing is no
    lesson at all - lessons never travel
    anonymously.
    """

    section: str
    title: str
    detail: str
    source_project: str
    context: str
    evidence: str
    source: str
    ref: str
    lesson_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.lesson_id is not None:
            object.__setattr__(
                self, "lesson_id",
                normalize_member_id(self.lesson_id))
        object.__setattr__(
            self, "section", normalize_section(self.section))
        object.__setattr__(
            self, "title", _check_title(self.title, "a lesson's title"))
        object.__setattr__(
            self, "detail",
            _check_long_text(self.detail, "a lesson's detail"))
        object.__setattr__(
            self, "source_project",
            _check_project(
                self.source_project, "a lesson's source project"))
        object.__setattr__(
            self, "context",
            _check_long_text(self.context, "a lesson's context"))
        object.__setattr__(
            self, "evidence",
            _check_long_text(self.evidence, "a lesson's evidence"))
        object.__setattr__(
            self, "source",
            _check_title(self.source, "a lesson's source"))
        object.__setattr__(self, "ref", _check_ref(self.ref))

    @property
    def section_index(self) -> int:
        """This lesson's section's place in map order (derived)."""
        return MAP_SECTIONS.index(self.section)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "cross_project_lesson",
            "slice": CROSS_PROJECT_SLICE,
            "lesson_id": self.lesson_id,
            "section": self.section,
            "title": self.title,
            "detail": self.detail,
            "source_project": self.source_project,
            "context": self.context,
            "evidence": self.evidence,
            "source": self.source,
            "ref": self.ref,
        }


def _provenance_words(source_project: Any, context: Any,
                      evidence: Any) -> Tuple[str, str, str]:
    """The provenance a composed lesson must carry, or a refusal.

    A memory-map entry or a carried session note
    becomes a cross-project lesson only when the
    words are named with it: where it was learned,
    in what context, and on what evidence. A missing
    word refuses plainly - never a guessed or empty
    provenance.
    """
    if source_project is None or context is None or evidence is None:
        raise ValueError(
            "a lesson offered across projects must carry "
            "its provenance: the source project it was "
            "learned in, the context it was learned in "
            "and the evidence it stands on")
    return (
        _check_project(source_project, "a lesson's source project"),
        _check_long_text(context, "a lesson's context"),
        _check_long_text(evidence, "a lesson's evidence"))


def validate_lesson(lesson: Any, *, source_project: Any = None,
                    context: Any = None,
                    evidence: Any = None) -> SharedLesson:
    """Validate one lesson record into a SharedLesson.

    Accepts a lesson; a shipped memory-map entry or
    a session-memory carried note (whose section,
    title, detail, source and reference are read
    onto the lesson - the shipped memory layers
    composed by import - with the provenance words
    named beside it: *source_project*, *context*
    and *evidence*, all three required); or a
    mapping naming a ``section`` (or ``kind``), a
    ``title`` (or ``name``), a ``detail`` (or
    ``body``), a ``source_project`` (or
    ``from_project`` / ``project``), a ``context``
    (or ``learned_in`` / ``situation``), an
    ``evidence`` (or ``proof`` / ``backing``), a
    ``source``, a ``ref`` (or ``path`` /
    ``reference``) and an optional ``lesson_id``
    (or ``id``). Naming two spellings of one field
    with different values refuses, and unknown keys
    refuse.
    """
    if isinstance(lesson, SharedLesson):
        return lesson
    if isinstance(lesson, (MemoryMapEntry, CarriedMemory)):
        project, learned_in, stands_on = _provenance_words(
            source_project, context, evidence)
        lesson_id = lesson.entry_id if isinstance(
            lesson, MemoryMapEntry) else lesson.note_id
        return SharedLesson(
            section=lesson.section, title=lesson.title,
            detail=lesson.detail, source_project=project,
            context=learned_in, evidence=stands_on,
            source=lesson.source, ref=lesson.ref,
            lesson_id=lesson_id)
    if not isinstance(lesson, dict):
        raise ValueError(
            f"a shared-lesson record must be a mapping, "
            f"got {lesson!r}")
    unknown = set(lesson) - _LESSON_KEYS
    if unknown:
        raise ValueError(
            "unknown lesson keys: %s"
            % ", ".join(sorted(unknown)))

    def _needed(spellings: Tuple[str, ...], what: str) -> Any:
        value = _pick_any(lesson, spellings, what)
        if value is None:
            raise ValueError(f"a lesson record is missing its {what}")
        return value

    kwargs: Dict[str, Any] = {
        "section": _needed(("section", "kind"), "section"),
        "title": _needed(("title", "name"), "title"),
        "detail": _needed(("detail", "body"), "detail"),
        "source_project": _needed(
            ("source_project", "from_project", "project"),
            "source project"),
        "context": _needed(
            ("context", "learned_in", "situation"), "context"),
        "evidence": _needed(
            ("evidence", "proof", "backing"), "evidence"),
        "source": _needed(("source",), "source"),
        "ref": _needed(("ref", "path", "reference"), "reference"),
    }
    named_id = _pick_any(lesson, ("lesson_id", "id"), "lesson ids")
    if named_id is not None:
        kwargs["lesson_id"] = named_id
    return SharedLesson(**kwargs)


def build_lesson(lesson: Any = None, **kwargs: Any) -> SharedLesson:
    """Build one validated lesson, from a mapping or field words.

    Provenance words for a composed entry or note
    (``source_project``, ``context``, ``evidence``)
    may ride in the field words; in a mapping they
    are the record's own fields.
    """
    provenance = {
        key: kwargs.pop(key)
        for key in ("source_project", "context", "evidence")
        if key in kwargs}
    if isinstance(lesson, SharedLesson) and not kwargs and not provenance:
        return lesson
    if isinstance(lesson, (MemoryMapEntry, CarriedMemory)):
        if kwargs:
            raise ValueError(
                "a composed lesson takes only its provenance words")
        return validate_lesson(lesson, **provenance)
    if isinstance(lesson, dict) or lesson is None:
        merged: Dict[str, Any] = {}
        if isinstance(lesson, dict):
            merged.update(lesson)
        merged.update(provenance)
        merged.update(kwargs)
        return validate_lesson(merged)
    raise ValueError(
        f"a shared-lesson record must be a mapping, got {lesson!r}")


def _check_lesson_ref(value: Any) -> SharedLesson:
    if isinstance(value, SharedLesson):
        return value
    if isinstance(value, dict):
        return validate_lesson(value)
    raise ValueError(f"a lesson record is needed, got {value!r}")


# ---------------------------------------------------------------------
# The offer: one lesson's explicit standing with one target project.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class LessonOffer:
    """One lesson offered to one target project, as an explicit state.

    ``lesson_id`` names the lesson (a book or a
    registry judges that the lesson stands there -
    an offer names a real lesson or it is no offer);
    ``target_project`` is the project it is offered
    to, never the lesson's own project; ``state``
    is where the offer stands - offered, accepted,
    declined or withdrawn; ``note`` says, in plain
    words, what the next reader needs to know about
    the offer. Nothing here enters the target's
    memory: the state is the whole act, and only
    the accepted state lets a lesson stand in a
    target, derived at call time by
    :func:`accepted_lessons`.
    """

    lesson_id: str
    target_project: str
    state: str
    note: str
    offer_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.offer_id is not None:
            object.__setattr__(
                self, "offer_id",
                normalize_member_id(self.offer_id))
        object.__setattr__(
            self, "lesson_id",
            normalize_member_id(self.lesson_id))
        object.__setattr__(
            self, "target_project",
            _check_project(
                self.target_project, "an offer's target project"))
        object.__setattr__(
            self, "state", normalize_offer_state(self.state))
        object.__setattr__(
            self, "note",
            _check_long_text(self.note, "an offer's note"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "cross_project_offer",
            "slice": CROSS_PROJECT_SLICE,
            "offer_id": self.offer_id,
            "lesson_id": self.lesson_id,
            "target_project": self.target_project,
            "state": self.state,
            "note": self.note,
        }


def validate_offer(offer: Any) -> LessonOffer:
    """Validate one offer record into a LessonOffer.

    Accepts an offer, a lesson standing as the offer
    of itself (its id names the lesson, with the
    target, state and note named beside it as field
    words through :func:`build_offer`), or a mapping
    naming a ``lesson_id`` (or ``lesson``), a
    ``target_project`` (or ``to_project`` /
    ``target``), a ``state`` (or ``status``), a
    ``note`` (or ``detail``) and an optional
    ``offer_id`` (or ``id``). Naming two spellings
    of one field with different values refuses, and
    unknown keys refuse.
    """
    if isinstance(offer, LessonOffer):
        return offer
    if not isinstance(offer, dict):
        raise ValueError(
            f"a lesson-offer record must be a mapping, "
            f"got {offer!r}")
    unknown = set(offer) - _OFFER_KEYS
    if unknown:
        raise ValueError(
            "unknown offer keys: %s"
            % ", ".join(sorted(unknown)))

    def _needed(spellings: Tuple[str, ...], what: str) -> Any:
        value = _pick_any(offer, spellings, what)
        if value is None:
            raise ValueError(f"an offer record is missing its {what}")
        return value

    kwargs: Dict[str, Any] = {
        "lesson_id": _needed(("lesson_id", "lesson"), "lesson id"),
        "target_project": _needed(
            ("target_project", "to_project", "target"),
            "target project"),
        "state": _needed(("state", "status"), "state"),
        "note": _needed(("note", "detail"), "note"),
    }
    offer_id = _pick_any(offer, ("offer_id", "id"), "offer ids")
    if offer_id is not None:
        kwargs["offer_id"] = offer_id
    return LessonOffer(**kwargs)


def build_offer(offer: Any = None, **kwargs: Any) -> LessonOffer:
    """Build one validated offer, from a mapping or field words."""
    if isinstance(offer, LessonOffer) and not kwargs:
        return offer
    if isinstance(offer, SharedLesson):
        merged: Dict[str, Any] = {}
        if offer.lesson_id is None:
            raise ValueError(
                "an offer built from a lesson needs the "
                "lesson to carry an id")
        merged["lesson_id"] = offer.lesson_id
        merged.update(kwargs)
        return validate_offer(merged)
    if isinstance(offer, dict) or offer is None:
        merged = {}
        if isinstance(offer, dict):
            merged.update(offer)
        merged.update(kwargs)
        return validate_offer(merged)
    raise ValueError(
        f"a lesson-offer record must be a mapping, got {offer!r}")


def _check_offer_ref(value: Any) -> LessonOffer:
    if isinstance(value, LessonOffer):
        return value
    if isinstance(value, dict):
        return validate_offer(value)
    raise ValueError(f"an offer record is needed, got {value!r}")


# ---------------------------------------------------------------------
# The exchange panel: every offer with its lesson whole, derived.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class ExchangePanelRow:
    """One offer carried whole into the panel, with its lesson.

    ``state`` is the offer's standing; ``lesson_id``
    names the lesson; ``title`` and ``detail`` are
    the lesson's own words; ``source_project`` is
    the lesson's provenance head - the project it
    was learned in; ``target_project`` is the
    project it stands offered to. :func:`validate_row`
    judged against its offer and lesson refuses a
    row whose fields disagree with the row they
    derive - a panel row can never re-home a lesson
    or soften its standing.
    """

    state: str
    lesson_id: str
    title: str
    detail: str
    source_project: str
    target_project: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "state", normalize_offer_state(self.state))
        object.__setattr__(
            self, "lesson_id",
            normalize_member_id(self.lesson_id))
        object.__setattr__(
            self, "title", _check_title(self.title, "a row's title"))
        object.__setattr__(
            self, "detail",
            _check_long_text(self.detail, "a row's detail"))
        object.__setattr__(
            self, "source_project",
            _check_project(
                self.source_project, "a row's source project"))
        object.__setattr__(
            self, "target_project",
            _check_project(
                self.target_project, "a row's target project"))

    @property
    def sort_key(self) -> Tuple[int, str, str]:
        """This row's place in panel order (derived).

        Rows stand state first (accepted, offered,
        declined, withdrawn, in that settled order);
        within a state, by source project, then
        lesson title.
        """
        return (
            _PANEL_STATE_ORDER.index(self.state),
            self.source_project, self.title)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "cross_project_row",
            "slice": CROSS_PROJECT_SLICE,
            "state": self.state,
            "lesson_id": self.lesson_id,
            "title": self.title,
            "detail": self.detail,
            "source_project": self.source_project,
            "target_project": self.target_project,
        }


def _row_for_offer(offer: LessonOffer,
                   lesson: SharedLesson) -> ExchangePanelRow:
    if lesson.lesson_id != offer.lesson_id:
        raise ValueError(
            "a panel row's lesson must be the offer's own lesson")
    return ExchangePanelRow(
        state=offer.state, lesson_id=lesson.lesson_id,
        title=lesson.title, detail=lesson.detail,
        source_project=lesson.source_project,
        target_project=offer.target_project)


def _check_row_ref(value: Any) -> ExchangePanelRow:
    if isinstance(value, ExchangePanelRow):
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

        return ExchangePanelRow(
            state=_needed(("state",), "state"),
            lesson_id=_needed(("lesson_id", "id"), "lesson id"),
            title=_needed(("title",), "title"),
            detail=_needed(("detail",), "detail"),
            source_project=_needed(
                ("source_project",), "source project"),
            target_project=_needed(
                ("target_project",), "target project"))
    raise ValueError(f"a panel row is needed, got {value!r}")


def validate_row(row: Any, offer: Any = None,
                 lesson: Any = None) -> ExchangePanelRow:
    """Validate one panel row into an ExchangePanelRow.

    Accepts a row or a mapping naming a ``state``,
    a ``lesson_id`` (or ``id``), a ``title``, a
    ``detail``, a ``source_project`` and a
    ``target_project``. With *offer* and *lesson*
    given, the row is judged against the row derived
    from that offer and its lesson: a stored row
    whose fields disagree with the derived row
    refuses.
    """
    current = _check_row_ref(row)
    if offer is not None or lesson is not None:
        if offer is None or lesson is None:
            raise ValueError(
                "a row is judged against its offer and "
                "its lesson together")
        derived = _row_for_offer(
            _check_offer_ref(offer), _check_lesson_ref(lesson))
        if current != derived:
            raise ValueError(
                "a stored row disagrees with the row "
                "derived from its offer and lesson")
    return current


def build_row(row: Any = None, offer: Any = None,
              lesson: Any = None,
              **kwargs: Any) -> ExchangePanelRow:
    """Build one validated row, from a mapping or field words."""
    if isinstance(row, ExchangePanelRow) and not kwargs:
        return validate_row(row, offer, lesson)
    if isinstance(row, dict) or row is None:
        merged: Dict[str, Any] = {}
        if isinstance(row, dict):
            merged.update(row)
        merged.update(kwargs)
        return validate_row(merged, offer, lesson)
    return validate_row(row, offer, lesson)


@dataclass(frozen=True)
class OfferStateCount:
    """One state's count in a panel: its offers tallied."""

    state: str
    items: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "state", normalize_offer_state(self.state))
        object.__setattr__(
            self, "items",
            _check_count(self.items, "a state count's items"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "state": self.state,
            "items": self.items,
        }


def _check_state_count_ref(value: Any) -> OfferStateCount:
    if isinstance(value, OfferStateCount):
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
            raise ValueError("a state count is missing its items")
        return OfferStateCount(state=state, items=items)
    raise ValueError(f"a state count is needed, got {value!r}")


def _panel_account(total_items: int, total_accepted: int,
                   total_offered: int, total_declined: int,
                   total_withdrawn: int) -> Tuple[str, ...]:
    return (
        f"The exchange panel holds {total_items} offers: "
        f"accepted {total_accepted}, offered {total_offered}, "
        f"declined {total_declined}, withdrawn {total_withdrawn}.",
        "Offers stand accepted first, then offered, "
        "then declined, then withdrawn; within a state, "
        "by source project, then lesson title - so two "
        "panels of one book diff cleanly, line by line.",
        "A lesson stands in a target project only "
        "through an accepted offer, and it stands there "
        "with its provenance whole - where it was "
        "learned, in what context, and on what evidence.",
        "The panel is read off the book at call time - "
        "it is derived, never stored loose.",
    )


@dataclass(frozen=True)
class ExchangePanel:
    """The exchange panel of one book, derived from the whole book.

    ``rows`` are the book's offers with their
    lessons carried whole, in panel order (accepted
    first, then offered, then declined, then
    withdrawn; within a state, by source project,
    then lesson title, so two panels of one book
    diff cleanly); ``total_items`` is the offer
    count and the four state totals are the rows'
    own counts; ``state_counts`` are the per-state
    tallies in the order their states first appear
    in the panel; ``account`` is read off those
    numbers. A panel whose rows stand out of panel
    order, or whose totals are not its own rows'
    counts, refuses at construction;
    :func:`validate_panel` judged against a book
    refuses a stored panel that disagrees with the
    derived one.
    """

    rows: Tuple[ExchangePanelRow, ...] = ()
    total_items: int = 0
    total_accepted: int = 0
    total_offered: int = 0
    total_declined: int = 0
    total_withdrawn: int = 0
    state_counts: Tuple[OfferStateCount, ...] = ()
    account: Tuple[str, ...] = ()
    panel_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.panel_id is not None:
            object.__setattr__(
                self, "panel_id",
                normalize_member_id(self.panel_id))
        if isinstance(self.rows, (str, bytes)) \
                or not isinstance(self.rows, (list, tuple)):
            raise ValueError(
                f"a panel's rows must be a list of rows, "
                f"got {self.rows!r}")
        rows = tuple(_check_row_ref(r) for r in self.rows)
        seen = set()
        for row in rows:
            key = (row.lesson_id, row.target_project)
            if key in seen:
                raise ValueError(
                    f"a panel row for lesson {row.lesson_id!r} "
                    f"to {row.target_project!r} already exists")
            seen.add(key)
        order = [_PANEL_STATE_ORDER.index(r.state) for r in rows]
        if order != sorted(order):
            raise ValueError(
                "a panel's rows must stand in panel order "
                "(accepted, then offered, then declined, "
                "then withdrawn)")
        object.__setattr__(self, "rows", rows)
        for field_name, state, what in (
                ("total_accepted", "accepted", "accepted total"),
                ("total_offered", "offered", "offered total"),
                ("total_declined", "declined", "declined total"),
                ("total_withdrawn", "withdrawn", "withdrawn total")):
            checked = _check_count(
                getattr(self, field_name), f"a panel's {what}")
            if checked != sum(1 for r in rows if r.state == state):
                raise ValueError(
                    f"a panel's {what} must be its own rows' count")
            object.__setattr__(self, field_name, checked)
        object.__setattr__(
            self, "total_items",
            _check_count(self.total_items, "a panel's total"))
        if self.total_items != len(rows):
            raise ValueError(
                "a panel's total must be its own rows' count")
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
        if sum(c.items for c in state_counts) != self.total_items:
            raise ValueError(
                "a panel's state counts must sum to its own total")
        for count in state_counts:
            if count.items != sum(
                    1 for r in rows if r.state == count.state):
                raise ValueError(
                    "a panel's state counts must be its own "
                    "rows' counts")
        object.__setattr__(self, "account", _check_account(self.account))

    def row_for(self, lesson_id: Any,
                target_project: Any) -> ExchangePanelRow:
        """The panel row one lesson and target name in this panel."""
        wanted_lesson = normalize_member_id(lesson_id)
        wanted_target = _check_project(
            target_project, "a row's target project")
        for row in self.rows:
            if row.lesson_id == wanted_lesson \
                    and row.target_project == wanted_target:
                return row
        raise KeyError(
            f"no row in the panel: lesson {wanted_lesson!r} "
            f"to {wanted_target!r}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "cross_project_panel",
            "slice": CROSS_PROJECT_SLICE,
            "panel_id": self.panel_id,
            "rows": [row.to_record() for row in self.rows],
            "total_items": self.total_items,
            "total_accepted": self.total_accepted,
            "total_offered": self.total_offered,
            "total_declined": self.total_declined,
            "total_withdrawn": self.total_withdrawn,
            "state_counts": [c.to_record() for c in self.state_counts],
            "account": list(self.account),
        }


def _held_lessons(source: Any) -> Tuple[SharedLesson, ...]:
    """The lessons one source holds, in held order."""
    if isinstance(source, CrossProjectBook):
        return source.lessons
    if isinstance(source, CrossProjectRegistry):
        return source.list_lessons()
    if isinstance(source, (list, tuple)):
        return tuple(_check_lesson_ref(item) for item in source)
    raise ValueError(f"lessons are needed, got {source!r}")


def _held_offers(source: Any) -> Tuple[LessonOffer, ...]:
    """The offers one source holds, in held order."""
    if isinstance(source, CrossProjectBook):
        return source.offers
    if isinstance(source, CrossProjectRegistry):
        return source.list_offers()
    if isinstance(source, (list, tuple)):
        return tuple(_check_offer_ref(item) for item in source)
    raise ValueError(f"offers are needed, got {source!r}")


def derive_panel(source: Any) -> ExchangePanel:
    """Derive the exchange panel from one book.

    The rows are the book's offers with their
    lessons carried whole, in panel order: accepted
    first, then offered, then declined, then
    withdrawn; within a state, by the lesson's
    source project, then its title. *source* is a
    book or a registry. A source holding no offer
    refuses - a panel of nothing is no panel - and
    an offer naming a lesson the source does not
    hold refuses too: a panel row must name a real
    lesson, with its provenance.
    """
    lessons = _held_lessons(source)
    offers = _held_offers(source)
    if not offers:
        raise ValueError("a panel needs at least one offer")
    by_id = {lesson.lesson_id: lesson for lesson in lessons}
    rows = []
    for offer in offers:
        lesson = by_id.get(offer.lesson_id)
        if lesson is None:
            raise ValueError(
                f"an offer names a lesson the book does "
                f"not hold: {offer.lesson_id!r}")
        rows.append(_row_for_offer(offer, lesson))
    rows = tuple(sorted(rows, key=lambda r: r.sort_key))
    order: list = []
    tally: Dict[str, int] = {}
    for row in rows:
        if row.state not in tally:
            tally[row.state] = 0
            order.append(row.state)
        tally[row.state] += 1
    state_counts = tuple(
        OfferStateCount(state=state, items=tally[state])
        for state in order)
    totals = {
        state: tally.get(state, 0) for state in OFFER_STATES}
    return ExchangePanel(
        rows=rows,
        total_items=len(rows),
        total_accepted=totals["accepted"],
        total_offered=totals["offered"],
        total_declined=totals["declined"],
        total_withdrawn=totals["withdrawn"],
        state_counts=state_counts,
        account=_panel_account(
            len(rows), totals["accepted"], totals["offered"],
            totals["declined"], totals["withdrawn"]))


def validate_panel(panel: Any, source: Any = None) -> ExchangePanel:
    """Validate one panel into an ExchangePanel.

    Accepts a panel or a mapping naming ``rows``
    (or ``offers``), a ``total_items`` (or
    ``total``), the four state totals,
    ``state_counts`` (or ``states``), an ``account``
    (or ``statements``) and an optional ``panel_id``
    (or ``id``). With *source* given (a book), the
    panel is judged against the panel derived from
    that book: a stored panel whose rows, totals,
    state counts or account disagree with the
    derived panel refuses. A panel naming no
    account refuses too.
    """
    if isinstance(panel, ExchangePanel):
        current = panel
    elif isinstance(panel, dict):
        unknown = set(panel) - _PANEL_KEYS
        if unknown:
            raise ValueError(
                "unknown panel keys: %s" % ", ".join(sorted(unknown)))
        rows = _pick_any(panel, ("rows", "offers"), "rows")
        if rows is None:
            raise ValueError("a panel is missing its rows")
        total = _pick_any(
            panel, ("total_items", "total"), "totals")
        if total is None:
            raise ValueError("a panel is missing its total items")
        state_counts = _pick_any(
            panel, ("state_counts", "states"), "state counts")
        if state_counts is None:
            raise ValueError("a panel is missing its state counts")
        account = _pick_any(panel, ("account", "statements"), "accounts")
        if account is None:
            raise ValueError("a panel names no account of its own")
        kwargs: Dict[str, Any] = {
            "rows": rows, "total_items": total,
            "state_counts": state_counts, "account": account}
        for field_name in (
                "total_accepted", "total_offered",
                "total_declined", "total_withdrawn"):
            value = _pick_any(panel, (field_name,), field_name)
            if value is None:
                raise ValueError(f"a panel is missing its {field_name}")
            kwargs[field_name] = value
        panel_id = _pick_any(panel, ("panel_id", "id"), "panel ids")
        if panel_id is not None:
            kwargs["panel_id"] = panel_id
        current = ExchangePanel(**kwargs)
    else:
        raise ValueError(f"a panel must be a mapping, got {panel!r}")
    if source is not None:
        derived = derive_panel(source)
        if (current.rows != derived.rows
                or current.total_items != derived.total_items
                or current.total_accepted != derived.total_accepted
                or current.total_offered != derived.total_offered
                or current.total_declined != derived.total_declined
                or current.total_withdrawn != derived.total_withdrawn
                or current.state_counts != derived.state_counts
                or current.account != derived.account):
            raise ValueError(
                "a stored panel disagrees with the panel "
                "derived from its book")
    return current


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> ExchangePanel:
    """Build one validated panel, from a mapping or field words."""
    if isinstance(panel, ExchangePanel) and not kwargs:
        return validate_panel(panel, source)
    if isinstance(panel, dict) or panel is None:
        merged: Dict[str, Any] = {}
        if isinstance(panel, dict):
            merged.update(panel)
        merged.update(kwargs)
        return validate_panel(merged, source)
    return validate_panel(panel, source)


# ---------------------------------------------------------------------
# The composition roads: the shipped memory layers, by import.
# ---------------------------------------------------------------------


def lesson_from_map_entry(entry: Any, *, source_project: Any,
                          context: Any,
                          evidence: Any) -> SharedLesson:
    """Build one shared lesson from a shipped memory-map entry.

    The entry - the project memory map's own record,
    judged by the map's own validation - is read onto
    a lesson BY IMPORT: its section (the map's closed
    set), its title, its detail, its source and its
    reference stand exactly as the map holds them.
    The provenance words are named beside it: the
    project the lesson was learned in, the context
    it was learned in, and the evidence it stands
    on. Without all three, the entry stays a fact of
    its own project - it does not travel.
    """
    validated = _validate_map_entry(entry)
    return validate_lesson(
        validated, source_project=source_project,
        context=context, evidence=evidence)


def _map_entries(source: Any) -> Tuple[MemoryMapEntry, ...]:
    """The shipped map entries one source holds, judged by the map."""
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


def lessons_from_memory_map(source: Any, *, source_project: Any,
                            context: Any,
                            evidence: Any) -> Tuple[SharedLesson, ...]:
    """Shared lessons read off the shipped project memory map.

    Every entry of the shipped map - a book, a
    registry, the entries themselves, or one entry -
    is read onto a shared lesson BY IMPORT, judged
    by the map's own validation on the way, under
    one provenance frame: the project the lessons
    were learned in, the context they were learned
    in, and the evidence they stand on. Nothing here
    re-names a section or re-words a fact, and no
    entry travels without the frame.
    """
    return tuple(
        validate_lesson(
            entry, source_project=source_project,
            context=context, evidence=evidence)
        for entry in _map_entries(source))


def _carried_notes(source: Any) -> Tuple[CarriedMemory, ...]:
    """The carried notes one session-memory source holds."""
    from .session_memory import SessionMemoryBook, SessionMemoryRegistry
    if isinstance(source, SessionSituation):
        return source.memory
    if isinstance(source, SessionMemoryBook):
        notes: list = []
        for situation in source.situations:
            notes.extend(situation.memory)
        return tuple(notes)
    if isinstance(source, SessionMemoryRegistry):
        notes = []
        for situation in source.list_situations():
            notes.extend(situation.memory)
        return tuple(notes)
    if isinstance(source, (list, tuple)):
        return tuple(
            note if isinstance(note, CarriedMemory)
            else _validate_session_note(note)
            for note in source)
    raise ValueError(f"carried notes are needed, got {source!r}")


def lessons_from_session_memory(source: Any, *, source_project: Any,
                                context: Any, evidence: Any
                                ) -> Tuple[SharedLesson, ...]:
    """Shared lessons read off the shipped session memory.

    The carried notes of a session situation - or of
    a whole session-memory book or registry - are
    read onto shared lessons BY IMPORT: a fact a
    session carried across its days can be offered
    onward across projects, under one provenance
    frame (the project, the context and the
    evidence, all three required). The note's own
    section, title, detail, source and reference
    stand exactly as the situation holds them.
    """
    return tuple(
        validate_lesson(
            note, source_project=source_project,
            context=context, evidence=evidence)
        for note in _carried_notes(source))


def accepted_lessons(source: Any,
                     target_project: Any) -> Tuple[SharedLesson, ...]:
    """The lessons standing accepted into one target project.

    This derivation is the ONLY road by which a
    lesson stands in another project on this layer:
    the offers of *source* (a book or a registry)
    whose state is accepted and whose target is the
    named project, read in panel order, each lesson
    carried whole - its provenance standing beside
    it exactly as it was learned. An offered,
    declined or withdrawn lesson stands nowhere in
    the target: not yet, or not at all. Nothing is
    copied into the target's own records - the
    standing is derived at call time.
    """
    target = _check_project(
        target_project, "a target project")
    lessons = _held_lessons(source)
    offers = _held_offers(source)
    by_id = {lesson.lesson_id: lesson for lesson in lessons}
    standing = []
    for offer in offers:
        if offer.state != "accepted" or offer.target_project != target:
            continue
        lesson = by_id.get(offer.lesson_id)
        if lesson is None:
            raise ValueError(
                f"an offer names a lesson the book does "
                f"not hold: {offer.lesson_id!r}")
        standing.append(lesson)
    return tuple(sorted(
        standing,
        key=lambda lesson: (
            lesson.source_project, lesson.title)))


# ---------------------------------------------------------------------
# The book: lessons and offers in held order, panels judged.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class CrossProjectBook:
    """One cross-project book: its lessons and offers, in held order.

    ``lessons`` are the shared lessons, in held
    order, each with its provenance whole;
    ``offers`` are the offers, in held order, each
    judged against the book's lessons at
    construction: an offer names a lesson the book
    holds, its target is never the lesson's own
    project, and no lesson is offered twice to one
    target. ``panels`` are the book's derivations -
    exchange panels of the whole book, each judged
    against the book by :func:`validate_book`;
    ``canon_note`` is the book's own note. The
    totals are the records' own counts, judged at
    construction. This book is the book file's
    shape: the shipped example is one book, and a
    real book file is a new file in this shape.
    """

    title: str = ""
    lessons: Tuple[SharedLesson, ...] = ()
    offers: Tuple[LessonOffer, ...] = ()
    panels: Tuple[ExchangePanel, ...] = ()
    canon_note: str = ""
    total_lessons: Optional[int] = None
    total_offers: Optional[int] = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_title(self.title, "a book's title"))
        if isinstance(self.lessons, (str, bytes)) \
                or not isinstance(self.lessons, (list, tuple)):
            raise ValueError(
                f"a book's lessons must be a list of "
                f"lesson records, got {self.lessons!r}")
        lessons = tuple(_check_lesson_ref(item) for item in self.lessons)
        if not lessons:
            raise ValueError(
                "a cross-project book holds at least one lesson")
        seen_ids = set()
        seen_facts = set()
        for lesson in lessons:
            if lesson.lesson_id is not None:
                if lesson.lesson_id in seen_ids:
                    raise ValueError(
                        f"a lesson named {lesson.lesson_id!r} "
                        f"already exists")
                seen_ids.add(lesson.lesson_id)
            key = (lesson.source_project, lesson.section, lesson.title)
            if key in seen_facts:
                raise ValueError(
                    f"the lesson {lesson.title!r} already stands "
                    f"in this book from {lesson.source_project}")
            seen_facts.add(key)
        object.__setattr__(self, "lessons", lessons)
        if isinstance(self.offers, (str, bytes)) \
                or not isinstance(self.offers, (list, tuple)):
            raise ValueError(
                f"a book's offers must be a list of "
                f"offer records, got {self.offers!r}")
        offers = tuple(_check_offer_ref(item) for item in self.offers)
        by_id = {lesson.lesson_id: lesson for lesson in lessons}
        seen_offers = set()
        seen_pairs = set()
        for offer in offers:
            if offer.offer_id is not None:
                if offer.offer_id in seen_offers:
                    raise ValueError(
                        f"an offer named {offer.offer_id!r} "
                        f"already exists")
                seen_offers.add(offer.offer_id)
            lesson = by_id.get(offer.lesson_id)
            if lesson is None:
                raise ValueError(
                    f"an offer names a lesson the book does "
                    f"not hold: {offer.lesson_id!r}")
            if offer.target_project == lesson.source_project:
                raise ValueError(
                    f"a lesson from {lesson.source_project} "
                    f"offered to {offer.target_project} is no "
                    f"cross-project offer - it never left home")
            pair = (offer.lesson_id, offer.target_project)
            if pair in seen_pairs:
                raise ValueError(
                    f"the lesson {offer.lesson_id!r} is already "
                    f"offered to {offer.target_project!r}")
            seen_pairs.add(pair)
        object.__setattr__(self, "offers", offers)
        if isinstance(self.panels, (str, bytes)) \
                or not isinstance(self.panels, (list, tuple)):
            raise ValueError(
                f"a book's panels must be a list of panels, "
                f"got {self.panels!r}")
        panels = tuple(
            p if isinstance(p, ExchangePanel) else validate_panel(p)
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
        for field_name, held, what in (
                ("total_lessons", lessons, "lessons"),
                ("total_offers", offers, "offers")):
            given = getattr(self, field_name)
            if given is None:
                object.__setattr__(self, field_name, len(held))
            else:
                checked = _check_count(
                    given, f"a book's total {what}")
                if checked != len(held):
                    raise ValueError(
                        f"a book's total {what} must be its "
                        f"own records' count")
                object.__setattr__(self, field_name, checked)

    def lesson_for(self, lesson_id: Any) -> SharedLesson:
        """The lesson one id names in this book."""
        wanted = normalize_member_id(lesson_id)
        for lesson in self.lessons:
            if lesson.lesson_id == wanted:
                return lesson
        raise KeyError(f"no lesson in the book: {wanted!r}")

    def offer_for(self, offer_id: Any) -> LessonOffer:
        """The offer one id names in this book."""
        wanted = normalize_member_id(offer_id)
        for offer in self.offers:
            if offer.offer_id == wanted:
                return offer
        raise KeyError(f"no offer in the book: {wanted!r}")

    def panel_for(self, panel_id: Any) -> ExchangePanel:
        """The stored panel one id names in this book."""
        wanted = normalize_member_id(panel_id)
        for panel in self.panels:
            if panel.panel_id == wanted:
                return panel
        raise KeyError(f"no panel in the book: {wanted!r}")

    def lesson_ids(self) -> Tuple[str, ...]:
        """Every held lesson id, in held order."""
        return tuple(
            item.lesson_id for item in self.lessons if item.lesson_id)

    def offer_ids(self) -> Tuple[str, ...]:
        """Every held offer id, in held order."""
        return tuple(
            item.offer_id for item in self.offers if item.offer_id)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "cross_project_book",
            "slice": CROSS_PROJECT_SLICE,
            "title": self.title,
            "lesson_ids": list(self.lesson_ids()),
            "lesson_count": len(self.lessons),
            "offer_ids": list(self.offer_ids()),
            "offer_count": len(self.offers),
            "panel_count": len(self.panels),
        }


def validate_book(data: Any, *, require_example: bool = False
                  ) -> CrossProjectBook:
    """Validate one cross-project mapping into a book.

    The mapping names a ``schema`` (the
    cross-project schema word), a ``guide`` mapping
    (its ``title``), a ``lessons`` list, an
    ``offers`` list and an optional ``panels`` list.
    Every record stands on its own validation, then
    the whole is judged: lesson and offer ids
    unique, every offer judged against the book's
    lessons (a real lesson, never its own project,
    never twice to one target), and every stored
    panel judged against the book (a panel the book
    does not derive refuses). With
    ``require_example`` the shipped example is held
    to its pinned shape: the pinned title, lessons
    and panel, and the panel's pinned rows and
    account word-for-word. Problems raise
    :class:`ValidationError` or ``ValueError``.
    """
    if isinstance(data, CrossProjectBook):
        return data
    if not isinstance(data, dict):
        raise ValidationError(
            f"a cross-project book must be a mapping, got {data!r}")
    unknown = set(data) - _CROSS_PROJECT_KEYS
    if unknown:
        raise ValidationError(
            "unknown cross-project keys: %s"
            % ", ".join(sorted(unknown)))
    if data.get("schema") != CROSS_PROJECT_SCHEMA:
        raise ValidationError(
            f"a cross-project book must carry schema "
            f"{CROSS_PROJECT_SCHEMA!r}, got {data.get('schema')!r}")
    lessons = _pick_any(data, ("lessons",), "lessons")
    if lessons is None:
        raise ValidationError("a cross-project book is missing its lessons")
    if not isinstance(lessons, (list, tuple)):
        raise ValidationError("a cross-project book's lessons must be a list")
    offers = _pick_any(data, ("offers",), "offers")
    if offers is None:
        raise ValidationError("a cross-project book is missing its offers")
    if not isinstance(offers, (list, tuple)):
        raise ValidationError("a cross-project book's offers must be a list")
    if data.get("panels") is not None \
            and not isinstance(data["panels"], (list, tuple)):
        raise ValidationError("a cross-project book's panels must be a list")
    head = data.get("guide") or {}
    if not isinstance(head, dict):
        raise ValidationError("a cross-project book's guide must be a mapping")
    unknown_head = set(head) - _BOOK_KEYS
    if unknown_head:
        raise ValidationError(
            "unknown guide keys: %s" % ", ".join(sorted(unknown_head)))
    try:
        title = _pick_any(head, ("title", "name"), "titles")
        if title is None:
            raise ValidationError("a cross-project book is missing its title")
        note = data.get("canon_note") or ""
        if not isinstance(note, str):
            raise ValidationError("a cross-project book's note must be text")
        book = CrossProjectBook(
            title=title, lessons=tuple(lessons),
            offers=tuple(offers),
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
                "the shipped example cross-project book's title "
                "is not the pinned title")
        if book.lesson_ids() != _EXAMPLE_LESSON_IDS:
            raise ValidationError(
                "the shipped example's lessons are not "
                "the pinned records")
        panel = book.panel_for(_EXAMPLE_PANEL_ID)
        if tuple(r.lesson_id for r in panel.rows) \
                != _EXAMPLE_PANEL_ROW_IDS:
            raise ValidationError(
                "the shipped example panel does not name "
                "its pinned rows in panel order")
        if panel.account != _EXAMPLE_PANEL_ACCOUNT:
            raise ValidationError(
                "the shipped example panel does not carry "
                "its pinned account word-for-word")
        first = book.lessons[0]
        if first.lesson_id != _EXAMPLE_FIRST_LESSON_ID \
                or first.source_project != _EXAMPLE_FIRST_LESSON_PROJECT:
            raise ValidationError(
                "the shipped example's first lesson is not "
                "its pinned lesson from its pinned project")
    return book


def build_book(book: Any = None, **kwargs: Any) -> CrossProjectBook:
    """Build one validated book, from a mapping or field words."""
    if isinstance(book, CrossProjectBook) and not kwargs:
        return book
    if isinstance(book, dict):
        if "schema" in book:
            return validate_book(book)
        merged: Dict[str, Any] = dict(book)
        merged.update(kwargs)
        return CrossProjectBook(**merged)
    if book is None:
        return CrossProjectBook(**kwargs)
    raise ValueError(f"a cross-project book is needed, got {book!r}")


def _book_from(data: Any, *, require_example: bool) -> CrossProjectBook:
    try:
        return validate_book(data, require_example=require_example)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def load_cross_project_memory(
        data: Optional[Dict[str, Any]] = None) -> CrossProjectBook:
    """Load and validate the shipped example book (or *data*).

    The shipped file is held to the example check:
    the pinned title, lesson records and panel -
    the M-153 slice boundary book - so the shipped
    book covers the canon this slice exists to hold.
    """
    raw = data if data is not None else load_resource(
        CROSS_PROJECT_RESOURCE)
    return _book_from(raw, require_example=True)


def load_cross_project_memory_file(path: Any) -> CrossProjectBook:
    """Load and validate a cross-project book from a file at *path*.

    Any file in the cross-project shape, anywhere on
    disk, validated whole - a malformed file raises
    :class:`ValidationError` naming the problem, and
    a missing file raises ``FileNotFoundError``. The
    example check is not held: a real book stands on
    its own records.
    """
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _book_from(raw, require_example=False)


# ---------------------------------------------------------------------
# The registry model: one book held lesson and offer by offer.
# ---------------------------------------------------------------------


class CrossProjectRegistry:
    """One session's lessons and offers, held one by one.

    The registry holds lesson and offer records,
    never panels: the panel is a derivation, read
    off the whole held book at call time, so nothing
    here can hold a figure stale. An offer is held
    only against a lesson already standing here, to
    a project that is not the lesson's own, and
    never twice to one target - the registry judges
    an offer exactly as a book does.
    """

    def __init__(self, book: Any = None) -> None:
        self._title: Optional[str] = None
        self._lessons: Dict[str, SharedLesson] = {}
        self._lesson_order: list = []
        self._offers: Dict[str, LessonOffer] = {}
        self._offer_order: list = []
        self._next_lesson = 1
        self._next_offer = 1
        if book is not None:
            self.register_book(book)

    def _fresh_lesson_id(self, held_ids: Any) -> str:
        while f"lesson-{self._next_lesson}" in held_ids:
            self._next_lesson += 1
        fresh = f"lesson-{self._next_lesson}"
        self._next_lesson += 1
        return fresh

    def _fresh_offer_id(self, held_ids: Any) -> str:
        while f"offer-{self._next_offer}" in held_ids:
            self._next_offer += 1
        fresh = f"offer-{self._next_offer}"
        self._next_offer += 1
        return fresh

    def register_lesson(self, lesson: Any) -> SharedLesson:
        """Register one lesson into the held book.

        A record with no id is given a deterministic
        ``lesson-N`` id. A record id already standing
        here refuses, as does a fact one project
        already stands in this book.
        """
        validated = _check_lesson_ref(lesson)
        held_ids = set(self._lessons)
        if validated.lesson_id is not None \
                and validated.lesson_id in held_ids:
            raise ValueError(
                f"a lesson named "
                f"{validated.lesson_id!r} already exists")
        for held in self._lessons.values():
            if (held.source_project, held.section, held.title) == (
                    validated.source_project, validated.section,
                    validated.title):
                raise ValueError(
                    f"the lesson {validated.title!r} already "
                    f"stands in this book from "
                    f"{validated.source_project}")
        if validated.lesson_id is None:
            validated = replace(
                validated,
                lesson_id=self._fresh_lesson_id(held_ids))
        self._lessons[validated.lesson_id] = validated
        self._lesson_order.append(validated.lesson_id)
        return validated

    def register_offer(self, offer: Any) -> LessonOffer:
        """Register one offer into the held book.

        The offer is judged as a book judges it: its
        lesson must already stand here, its target is
        never the lesson's own project, no lesson is
        offered twice to one target, and a record with
        no id is given a deterministic ``offer-N`` id.
        A refusal holds nothing new.
        """
        validated = _check_offer_ref(offer)
        lesson = self._lessons.get(validated.lesson_id)
        if lesson is None:
            raise ValueError(
                f"an offer names a lesson the book does "
                f"not hold: {validated.lesson_id!r}")
        if validated.target_project == lesson.source_project:
            raise ValueError(
                f"a lesson from {lesson.source_project} "
                f"offered to {validated.target_project} is no "
                f"cross-project offer - it never left home")
        for held in self._offers.values():
            if (held.lesson_id, held.target_project) == (
                    validated.lesson_id, validated.target_project):
                raise ValueError(
                    f"the lesson {validated.lesson_id!r} is "
                    f"already offered to "
                    f"{validated.target_project!r}")
        held_ids = set(self._offers)
        if validated.offer_id is not None \
                and validated.offer_id in held_ids:
            raise ValueError(
                f"an offer named "
                f"{validated.offer_id!r} already exists")
        if validated.offer_id is None:
            validated = replace(
                validated,
                offer_id=self._fresh_offer_id(held_ids))
        self._offers[validated.offer_id] = validated
        self._offer_order.append(validated.offer_id)
        return validated

    def register_book(self, book: Any) -> CrossProjectBook:
        """Register every lesson and offer of one book, in order.

        The first book held sets the title; a later
        book under a different title refuses, as does
        a book naming a held lesson or offer id. The
        book's panels are derivations, not holdings,
        and are not held.
        """
        validated = build_book(book)
        if self._title is not None and validated.title != self._title:
            raise ValueError(
                "this registry already holds a cross-project "
                "book under a different title")
        for lesson in validated.lessons:
            if lesson.lesson_id in self._lessons:
                raise ValueError(
                    f"a lesson named "
                    f"{lesson.lesson_id!r} already exists")
        for offer in validated.offers:
            if offer.offer_id in self._offers:
                raise ValueError(
                    f"an offer named "
                    f"{offer.offer_id!r} already exists")
        self._title = validated.title
        for lesson in validated.lessons:
            self.register_lesson(lesson)
        for offer in validated.offers:
            self.register_offer(offer)
        return self.book()

    def get_lesson(self, lesson_id: Any) -> SharedLesson:
        """The lesson one id names among the held records."""
        wanted = normalize_member_id(lesson_id)
        if wanted not in self._lessons:
            raise KeyError(f"unknown lesson: {wanted!r}")
        return self._lessons[wanted]

    def get_offer(self, offer_id: Any) -> LessonOffer:
        """The offer one id names among the held records."""
        wanted = normalize_member_id(offer_id)
        if wanted not in self._offers:
            raise KeyError(f"unknown offer: {wanted!r}")
        return self._offers[wanted]

    def latest_lesson(self) -> SharedLesson:
        """The most recently held lesson."""
        if not self._lesson_order:
            raise ValueError("no lesson is held yet")
        return self._lessons[self._lesson_order[-1]]

    def list_lessons(self) -> Tuple[SharedLesson, ...]:
        """Every held lesson, in the order they were held."""
        return tuple(self._lessons[item] for item in self._lesson_order)

    def list_offers(self) -> Tuple[LessonOffer, ...]:
        """Every held offer, in the order they were held."""
        return tuple(self._offers[item] for item in self._offer_order)

    def book(self) -> CrossProjectBook:
        """The held lessons and offers as one validated book."""
        if self._title is None:
            raise ValueError("no cross-project book is held yet")
        return CrossProjectBook(
            title=self._title, lessons=self.list_lessons(),
            offers=self.list_offers())

    def panel(self) -> ExchangePanel:
        """Derive the exchange panel of the whole held book."""
        return derive_panel(self)

    def accepted_lessons(
            self, target_project: Any) -> Tuple[SharedLesson, ...]:
        """The lessons standing accepted into one target project."""
        return accepted_lessons(self, target_project)


# ---------------------------------------------------------------------
# Lesson news, shaped as session records.
# ---------------------------------------------------------------------


def lesson_record(lesson: Any) -> Dict[str, Any]:
    """The session-news record of one shared lesson."""
    current = lesson if isinstance(lesson, SharedLesson) \
        else build_lesson(lesson)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"{current.title} ({current.section}) learned in "
        f"{current.source_project} at {current.ref}: "
        f"{current.detail}")
    return record


def offer_record(offer: Any) -> Dict[str, Any]:
    """The session-news record of one lesson offer."""
    current = offer if isinstance(offer, LessonOffer) \
        else build_offer(offer)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Lesson {current.lesson_id} offered to "
        f"{current.target_project}: {current.state} - "
        f"{current.note}")
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
        f"Cross-project exchange panel: {current.total_items} "
        f"offers - accepted {current.total_accepted}, "
        f"offered {current.total_offered}, declined "
        f"{current.total_declined}, withdrawn "
        f"{current.total_withdrawn}.")
    return record


def book_record(book: Any) -> Dict[str, Any]:
    """The session-news record of one cross-project book."""
    current = book if isinstance(book, CrossProjectBook) \
        else build_book(book)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Cross-project memory {current.title}: "
        f"{record['lesson_count']} lessons named, "
        f"{record['offer_count']} offers standing.")
    return record


def plain_words(lesson: Any) -> str:
    """One shared lesson, in one plain sentence."""
    current = lesson if isinstance(lesson, SharedLesson) \
        else build_lesson(lesson)
    return (
        f"{current.title} - a {current.section} lesson "
        f"learned in {current.source_project} "
        f"({current.context}), standing on "
        f"{current.evidence}: {current.detail} "
        f"(read from {current.source} at {current.ref}).")


def panel_plain_words(source: Any) -> str:
    """The exchange panel in plain words, in full.

    Accepts an ExchangePanel or a CrossProjectBook
    (whose derived panel is told). The panel is told
    whole - its rows in panel order and its account.
    """
    if isinstance(source, ExchangePanel):
        panel = validate_panel(source)
        title = None
    elif isinstance(source, CrossProjectBook):
        panel = derive_panel(source)
        title = source.title
    else:
        raise ValueError(
            f"a cross-project source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    lines.append("Offers, in panel order:")
    for row in panel.rows:
        lines.append(
            f"{row.lesson_id}: {row.state} - {row.title} "
            f"(from {row.source_project} to "
            f"{row.target_project}): {row.detail}")
    lines.extend(panel.account)
    return "\n".join(lines)


# ---------------------------------------------------------------------
# Screens: the formatters and the shared /crossmemory grammar.
# ---------------------------------------------------------------------


def _source_book(source: Any) -> CrossProjectBook:
    if source is None:
        return load_cross_project_memory()
    if isinstance(source, CrossProjectRegistry):
        return source.book()
    if isinstance(source, CrossProjectBook):
        return source
    raise ValueError(
        f"a cross-project book is needed, got {source!r}")


def format_lesson(lesson: Any) -> str:
    """One shared lesson as a screen block, provenance whole."""
    current = lesson if isinstance(lesson, SharedLesson) \
        else build_lesson(lesson)
    return "\n".join([
        f"{current.lesson_id or '-'}: {current.title} - "
        f"{current.section}, learned in {current.source_project}",
        f"Learned in this context: {current.context}",
        f"Standing on this evidence: {current.evidence}",
        f"{current.detail} (from {current.source} "
        f"at {current.ref})",
    ])


def format_lessons(source: Any = None) -> str:
    """Shared lessons of one book, in held order."""
    book = _source_book(source)
    lines = [
        f"{lesson.lesson_id or '-'}: {lesson.title} - "
        f"{lesson.section} (learned in "
        f"{lesson.source_project}): {lesson.detail}"
        for lesson in book.lessons]
    if not lines:
        lines.append("No lessons are held.")
    return "\n".join(lines)


def format_offers(source: Any = None) -> str:
    """Offers of one book, in held order."""
    book = _source_book(source)
    lines = []
    for offer in book.offers:
        lesson = book.lesson_for(offer.lesson_id)
        lines.append(
            f"{offer.offer_id or '-'}: {offer.lesson_id} "
            f"({lesson.title}) from {lesson.source_project} "
            f"to {offer.target_project} - {offer.state}: "
            f"{offer.note}")
    if not lines:
        lines.append("No offers are standing.")
    return "\n".join(lines)


def format_accepted(source: Any = None,
                    target_project: Any = None) -> str:
    """The lessons standing accepted into one target project."""
    if target_project is None:
        raise ValueError("an accepted view names its target project")
    target = _check_project(target_project, "a target project")
    standing = accepted_lessons(_source_book(source), target)
    lines = [
        f"{lesson.lesson_id or '-'}: {lesson.title} - "
        f"learned in {lesson.source_project} "
        f"({lesson.context}), standing on "
        f"{lesson.evidence}: {lesson.detail}"
        for lesson in standing]
    if not lines:
        lines.append(
            f"No lessons stand accepted into {target}.")
    return "\n".join(lines)


def format_panel(source: Any = None) -> str:
    """The exchange panel as a screen block: every row and the account.

    Accepts an ExchangePanel or a CrossProjectBook; a
    book shows the panel it derives.
    """
    if isinstance(source, ExchangePanel):
        panel = validate_panel(source)
        lines: list = []
    else:
        book = _source_book(source)
        if not book.offers:
            return (f"Exchange panel in {book.title}:\n"
                    f"No offers are standing.")
        panel = derive_panel(book)
        lines = [f"Exchange panel in {book.title}:"]
    lines.append("Offers, in panel order:")
    for row in panel.rows:
        lines.append(
            f"{row.lesson_id}: {row.state} - {row.title} "
            f"(from {row.source_project} to "
            f"{row.target_project}): {row.detail}")
    lines.extend(panel.account)
    return "\n".join(lines)


def format_cross_project_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /crossmemory.

    With nothing named, the shipped example
    cross-project book is shown - the example this
    slice ships - so the screen is never empty.
    """
    book = _source_book(source)
    lines = ["Cross-Project Memory (M-154) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_lessons(book))
    lines.append("")
    lines.append(format_panel(book))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_cross_project_args(args: Any) -> Tuple[str, Any]:
    """Parse the /crossmemory grammar both surfaces share.

    No words (or ``show`` / ``list``) shows the
    cross-project book; ``lesson <lesson-id>`` shows
    one shared lesson with its provenance whole;
    ``offers`` shows the book's offers in held order;
    ``accepted <project>`` shows the lessons standing
    accepted into one target project; ``panel`` shows
    the exchange panel derived from the whole book.
    Anything else is a usage error naming the grammar.
    Returns ``(action, value-or-None)``.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() in ("show", "list"):
        return ("show", None)
    words = text.split()
    head = words[0].lower()
    if head == "offers" and len(words) == 1:
        return (head, None)
    if head == "panel" and len(words) == 1:
        return (head, None)
    if head == "lesson" and len(words) == 2:
        try:
            return (head, normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "accepted" and len(words) == 2:
        try:
            return (head, _check_project(words[1], "a target project"))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
