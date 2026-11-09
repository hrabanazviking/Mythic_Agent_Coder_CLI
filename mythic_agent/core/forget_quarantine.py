"""Forget and quarantine (All-Features roadmap slice M-157).

Part VII continues. The roadmap's words:
``any memory can be inspected, edited, or forgotten
on the user's word, with the forgetting itself
journaled (what class of thing, never its content).``

What already shipped, and what this slice adds:

* Memories already ship as data in five holdings:
  the project memory map (``core/project_memory_map.py``,
  M-150), session memory across days
  (``core/session_memory.py``, M-153), cross-project
  memory (``core/cross_project_memory.py``, M-154),
  the self-improving ledger
  (``core/self_improving_ledger.py``, M-155) and
  decision records (``core/decision_records.py``,
  M-156), with crew memory
  (``core/crew_memory.py``, M-133) beside them. Each
  holding can be inspected through its own roads.
  Two smaller forget roads also ship: the long-term
  memory's and the preferences' ``forget`` methods
  drop one named fact, and ``/remember forget <id>``
  (M-096) revokes one remembered approval, journaled
  first. What no shipped layer holds is the
  forgetting itself as one journal across every
  class of memory: what class of thing was
  forgotten, quarantined or restored, on whose word,
  and when - with the thing's content kept nowhere.
* This slice is that journal, as a pure layer: a
  forget entry is one act of forgetting, validated
  as data WITH ITS PROVENANCE WHOLE - the class of
  memory it names, the reference (id) of the thing,
  the word it was done on, the day, and where the
  memory stood - standing in a closed set of actions
  (forgotten, quarantined, restored). The shipped
  data file (``mythic_agent/data/forget_quarantine.yaml``)
  holds one example book in exactly the shape a real
  book file takes, a loader reads a book file anywhere
  on disk, the composition roads read the shipped
  memory layers' pieces onto entries BY IMPORT -
  taking each piece's class and reference alone and
  discarding its words at the seam - the forget panel
  is DERIVED from the whole book (every entry standing
  whole, in a settled order), entries are shaped as
  session news, and a small in-memory registry model
  holds entries one by one. The agent layer owns
  holding a book for a session and journaling the
  forgetting of the session's carried memory.

Honesty rules, enforced here and pinned by tests:

* **Class and reference, never content.** An entry
  carries what class of thing was forgotten and the
  reference it stood under - never its title, its
  detail, its fact or any of its words. A mapping
  naming a content key (``title``, ``detail``,
  ``content``, ``text``, ``fact``, ``decision`` and
  their kin) refuses outright, and no record, event
  or surface this layer produces carries a forgotten
  thing's words: the composition roads read a piece's
  id and class alone, at the seam, and the piece's
  own words never enter an entry.
* **On the user's word, always.** Every entry names
  who asked for the act (``requested_by``) and the
  day it was done. An entry with no word refuses -
  nothing is forgotten, quarantined or restored
  anonymously, silently, by age or by count, and a
  shipped memory piece becomes an entry only when
  the frame words are named with it.
* **Restoring answers a quarantine.** A restored
  entry names a memory of the same class and
  reference that a quarantined entry in the same
  book holds apart: what was forgotten is gone and
  cannot be restored on this layer, and what was
  never quarantined cannot be restored either.
  Quarantine is the only road back, and it is
  explicit, never silent.
* **Composed, never duplicated.** Entries are the
  shipped memory layers' own pieces - session-memory
  notes, cross-project lessons, ledger candidates,
  decision records, memory-map entries and crew
  memory entries - read onto this layer by import
  and judged by each layer's own validation. No
  second taxonomy of memories is invented here: the
  classes are the shipped holdings' own names.
* **The panel is derived, never stored loose.**
  Its rows are the book's entries carried whole, in
  settled order (forgotten first, then quarantined,
  then restored; within an action, by memory class,
  then memory reference), and its totals are the
  entries' own counts; a stored panel or book whose
  rows, totals, counts or account disagree with the
  derived shape refuses.
* **Journal only - data only.** An entry here is
  validated data about an act of forgetting: no
  model is called, no live memory in any holding is
  mutated, no project file is written, and nothing
  persists beyond the session journal news the agent
  layer publishes. Deleting the thing itself from
  its own holding is that holding's own road (the
  long-term memory's ``forget``, ``/remember forget``);
  this layer is the journal every such act can be
  recorded in, by class and reference alone.
* **Malformed refuses.** A duplicate entry id in
  one book, the same memory named twice for one
  action in one book, a restored entry naming no
  quarantined memory in the book, a content key in
  any mapping, and unknown keys in an entry, a panel
  or a book mapping all raise instead of being
  skipped or guessed at.
"""

from __future__ import annotations

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
from .decision_records import DecisionRecord
from .decision_records import validate_record as _validate_decision
from .project_memory_map import MemoryMapEntry
from .project_memory_map import validate_entry as _validate_map_entry
from .self_improving_ledger import CandidateMemory
from .self_improving_ledger import (
    validate_candidate as _validate_candidate)
from .session_memory import CarriedMemory
from .session_memory import validate_note as _validate_note
from .validation import ValidationError

__all__ = [
    "FORGET_ACTIONS",
    "FORGET_QUARANTINE_RESOURCE",
    "FORGET_QUARANTINE_SCHEMA",
    "FORGET_QUARANTINE_SLICE",
    "MEMORY_CLASSES",
    "PLAIN_EXPLANATION",
    "USAGE",
    "ForgetActionCount",
    "ForgetBook",
    "ForgetEntry",
    "ForgetPanel",
    "ForgetPanelRow",
    "ForgetRegistry",
    "book_record",
    "build_book",
    "build_entry",
    "build_panel",
    "build_row",
    "derive_panel",
    "entries_from_memory_map",
    "entries_from_session_memory",
    "entry_from_cross_project",
    "entry_from_decision_record",
    "entry_from_ledger_candidate",
    "entry_from_memory_map",
    "entry_from_session_memory",
    "entry_record",
    "forgotten_entries",
    "format_entries",
    "format_entry",
    "format_forget_quarantine_screen",
    "format_forgotten",
    "format_panel",
    "format_quarantined",
    "inspect_memory",
    "load_forget_quarantine",
    "load_forget_quarantine_file",
    "normalize_forget_action",
    "normalize_memory_class",
    "panel_plain_words",
    "panel_record",
    "parse_forget_args",
    "plain_words",
    "validate_book",
    "validate_entry",
    "validate_panel",
    "validate_row",
]

FORGET_QUARANTINE_SLICE = "M-157"

#: The packaged data resource holding the example book.
FORGET_QUARANTINE_RESOURCE = "forget_quarantine.yaml"

#: The schema word a forget-quarantine file must carry.
FORGET_QUARANTINE_SCHEMA = "mythic.forget_quarantine/1"

#: The classes of memory one entry may name: the
#: shipped holdings' own names - a fact carried in
#: session memory across days (``session-memory``),
#: a lesson shared between projects
#: (``cross-project``), a candidate in the
#: self-improving ledger (``ledger-candidate``), a
#: choice held as a decision record
#: (``decision-record``), a fact in the project
#: memory map (``memory-map``), or an entry in a crew
#: member's notebook (``crew-memory``). No other
#: class is journaled here.
MEMORY_CLASSES = (
    "session-memory", "cross-project", "ledger-candidate",
    "decision-record", "memory-map", "crew-memory")

_CLASS_ALIASES = {
    "session-memory": "session-memory",
    "session": "session-memory",
    "daymemory": "session-memory",
    "cross-project": "cross-project",
    "cross": "cross-project",
    "crossmemory": "cross-project",
    "ledger-candidate": "ledger-candidate",
    "ledger": "ledger-candidate",
    "candidate": "ledger-candidate",
    "decision-record": "decision-record",
    "decision": "decision-record",
    "decisions": "decision-record",
    "memory-map": "memory-map",
    "memorymap": "memory-map",
    "map": "memory-map",
    "crew-memory": "crew-memory",
    "crew": "crew-memory",
}

#: The acts one forget entry may journal: a memory
#: forgotten on the user's word (``forgotten``), a
#: memory held apart until its standing is decided
#: (``quarantined``), or a quarantined memory stood
#: again on the user's word (``restored``).
FORGET_ACTIONS = ("forgotten", "quarantined", "restored")

_ACTION_ALIASES = {
    "forgotten": "forgotten",
    "forget": "forgotten",
    "forgot": "forgotten",
    "quarantined": "quarantined",
    "quarantine": "quarantined",
    "held": "quarantined",
    "restored": "restored",
    "restore": "restored",
}

#: The order entries stand in on the forget panel:
#: what is gone first, then what is held apart, then
#: what stands again.
_PANEL_ACTION_ORDER = ("forgotten", "quarantined", "restored")

#: Keys that would carry a forgotten thing's own
#: words. An entry naming any of them refuses by
#: name: the journal holds class and reference only.
_CONTENT_KEYS = frozenset({
    "title", "name", "detail", "details", "content",
    "text", "body", "fact", "facts", "decision",
    "choice", "note_text", "value",
})

_ENTRY_KEYS = frozenset({
    "entry_id", "id", "action", "state",
    "memory_class", "class", "kind",
    "memory_ref", "ref", "memory_id",
    "reason", "why",
    "requested_by", "by", "actor",
    "acted_on", "day", "date",
    "source",
})

_ROW_KEYS = frozenset({
    "action", "entry_id", "id", "memory_class",
    "memory_ref", "requested_by",
})

_ACTION_COUNT_KEYS = frozenset({"action", "items", "count"})

_PANEL_KEYS = frozenset({
    "panel_id", "id", "rows", "entries",
    "total_items", "total", "total_forgotten",
    "total_quarantined", "total_restored",
    "action_counts", "actions",
    "account", "statements",
})

_BOOK_KEYS = frozenset({"title", "name"})

_FORGET_BOOK_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "canon_note", "guide", "entries", "panels",
})

#: The shipped example book's title, held to this
#: by the loader's example check.
_EXAMPLE_TITLE = "Forget and quarantine at the M-156 slice boundary"

#: The shipped example's entry ids, in held order,
#: pinned by the loader.
_EXAMPLE_ENTRY_IDS = (
    "entry-lesson-forgotten", "entry-note-quarantined",
    "entry-note-restored", "entry-record-forgotten")

#: The shipped example's first entry and the class
#: it names, pinned by the loader.
_EXAMPLE_FIRST_ENTRY_ID = "entry-lesson-forgotten"

_EXAMPLE_FIRST_ENTRY_CLASS = "cross-project"

#: The shipped example's one panel id, and its rows
#: in panel order, pinned by the loader.
_EXAMPLE_PANEL_ID = "panel-m156-boundary"

_EXAMPLE_PANEL_ROW_IDS = (
    "entry-lesson-forgotten", "entry-record-forgotten",
    "entry-note-quarantined", "entry-note-restored")

_EXAMPLE_PANEL_ACCOUNT = (
    "The forget panel holds 4 entries: forgotten 2, "
    "quarantined 1, restored 1.",
    "Entries stand forgotten first, then quarantined, "
    "then restored; within an action, by memory class, "
    "then memory reference - so two panels of one book "
    "diff cleanly, line by line.",
    "Every entry journals what class of thing was "
    "forgotten, quarantined or restored, and the "
    "reference it stood under - never its content: no "
    "title, detail or fact of the thing stands "
    "anywhere in this book.",
    "The panel is read off the book at call time - "
    "it is derived, never stored loose.",
)

PLAIN_EXPLANATION = (
    "Forget and quarantine: any memory can be "
    "inspected, edited, or forgotten on the user's "
    "word, and the forgetting itself is journaled - "
    "what class of thing, never its content. A forget "
    "entry is one act carried with the class of memory "
    "it names, the reference the thing stood under, "
    "the word it was done on, the day, and where the "
    "memory stood, standing forgotten, quarantined or "
    "restored; a restored entry answers a quarantined "
    "entry for the same memory. The forget panel is "
    "derived from the book at call time: every entry "
    "standing whole, forgotten first, then quarantined "
    "and restored. This layer journals acts of "
    "forgetting as data only: it calls no model, "
    "mutates no live memory in any holding, writes no "
    "project files and persists nothing."
)

USAGE = (
    "Usage: /forget, /forget show, "
    "/forget entry <entry-id>, "
    "/forget forgotten, "
    "/forget quarantined, "
    "/forget panel"
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
        raise ValueError(f"an entry names two different {what}")
    return values[0]


def _check_count(value: Any, what: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{what} must be a count, got {value!r}")
    if value < 0:
        raise ValueError(f"{what} must not be negative, got {value!r}")
    return value


def _check_word(value: Any, what: str) -> str:
    """One plain id word, judged as a registry id is."""
    try:
        return normalize_member_id(value)
    except ValueError:
        raise ValueError(
            f"{what} must be one plain word, "
            f"got {value!r}") from None


def _check_day(value: Any) -> str:
    text = _clean_text(value, "an entry's acted-on day")
    try:
        parsed = date.fromisoformat(text)
    except ValueError:
        raise ValueError(
            f"an entry's acted-on day must be an ISO "
            f"date (YYYY-MM-DD), got {text!r}") from None
    if parsed.isoformat() != text:
        raise ValueError(
            f"an entry's acted-on day must be an ISO "
            f"date (YYYY-MM-DD), got {text!r}")
    return text


def normalize_memory_class(value: Any) -> str:
    """The canonical memory class a word names.

    A class is one of :data:`MEMORY_CLASSES` - the
    shipped holdings' own names - read
    case-insensitively, with the holdings' short
    faces (``session``, ``cross``, ``ledger``,
    ``decision``, ``map``, ``crew`` and their command
    faces) read onto them. Anything else raises,
    plainly naming the six.
    """
    if isinstance(value, str):
        wanted = _CLASS_ALIASES.get(value.strip().lower())
        if wanted is not None:
            return wanted
    raise ValueError(
        "a memory class must be one of %s, got %r"
        % ("/".join(MEMORY_CLASSES), value))


def normalize_forget_action(value: Any) -> str:
    """The canonical forget action a word names.

    An action is one of :data:`FORGET_ACTIONS` -
    ``forgotten`` (gone on the user's word),
    ``quarantined`` (held apart until its standing
    is decided) or ``restored`` (a quarantined
    memory stood again) - read case-insensitively,
    with ``forget`` / ``forgot`` read onto
    ``forgotten``, ``quarantine`` / ``held`` onto
    ``quarantined`` and ``restore`` onto
    ``restored``. Anything else raises, plainly
    naming the three.
    """
    if isinstance(value, str):
        wanted = _ACTION_ALIASES.get(value.strip().lower())
        if wanted is not None:
            return wanted
    raise ValueError(
        "an entry's action must be one of %s, got %r"
        % ("/".join(FORGET_ACTIONS), value))


# ---------------------------------------------------------------------
# The forget entry: one act of forgetting, class and reference only.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class ForgetEntry:
    """One act of forgetting, quarantining or restoring a memory.

    ``action`` is the act's standing in the closed
    set - ``forgotten``, ``quarantined`` or
    ``restored``; ``memory_class`` is the class of
    thing the act names, one of the shipped
    holdings; ``memory_ref`` is the reference (id)
    the thing stood under in its holding. That is
    all the entry says about the thing itself: its
    title, its detail and its words stand nowhere
    here, by construction - there is no field to
    hold them. The provenance stands whole beside
    the act: ``reason`` is the class-level reason
    the act was asked for, in plain words;
    ``requested_by`` names whose word the act was
    done on; ``acted_on`` is the day; and ``source``
    names where the memory stood. An entry with any
    provenance word missing is no entry at all.
    """

    action: str
    memory_class: str
    memory_ref: str
    reason: str
    requested_by: str
    acted_on: str
    source: str
    entry_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.entry_id is not None:
            object.__setattr__(
                self, "entry_id",
                normalize_member_id(self.entry_id))
        object.__setattr__(
            self, "action", normalize_forget_action(self.action))
        object.__setattr__(
            self, "memory_class",
            normalize_memory_class(self.memory_class))
        object.__setattr__(
            self, "memory_ref",
            _check_word(self.memory_ref, "an entry's memory reference"))
        object.__setattr__(
            self, "reason",
            _check_long_text(self.reason, "an entry's reason"))
        object.__setattr__(
            self, "requested_by",
            _check_word(
                self.requested_by, "the word an entry was done on"))
        object.__setattr__(
            self, "acted_on", _check_day(self.acted_on))
        object.__setattr__(
            self, "source",
            _check_title(self.source, "an entry's source"))

    @property
    def action_index(self) -> int:
        """This entry's action's place in panel order (derived)."""
        return _PANEL_ACTION_ORDER.index(self.action)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "forget_entry",
            "slice": FORGET_QUARANTINE_SLICE,
            "entry_id": self.entry_id,
            "action": self.action,
            "memory_class": self.memory_class,
            "memory_ref": self.memory_ref,
            "reason": self.reason,
            "requested_by": self.requested_by,
            "acted_on": self.acted_on,
            "source": self.source,
        }


def _frame_words(action: Any, requested_by: Any, acted_on: Any,
                 reason: Any, source: Any
                 ) -> Tuple[str, str, str, str, Optional[str]]:
    """The words a composed entry must carry, or a refusal.

    A shipped memory piece becomes an entry only
    when the words are named with it: the act, the
    word it is done on, the day, and the class-level
    reason. A missing word refuses plainly - never a
    guessed word, and never the piece's own words
    standing in for any of them.
    """
    if requested_by is None or acted_on is None or reason is None:
        raise ValueError(
            "a forget entry must carry its frame: the word "
            "it is done on, the day it is done, and the "
            "class-level reason it was asked for - nothing "
            "is forgotten on no one's word")
    return (
        "forgotten" if action is None
        else normalize_forget_action(action),
        _check_word(requested_by, "the word an entry was done on"),
        _check_day(acted_on),
        _check_long_text(reason, "an entry's reason"),
        None if source is None
        else _check_title(source, "an entry's source"))


def _entry_for(memory_class: str, memory_ref: Optional[str],
               piece_source: Optional[str], *, action: Any,
               requested_by: Any, acted_on: Any, reason: Any,
               source: Any, entry_id: Any = None) -> ForgetEntry:
    """One entry for one shipped piece, by class and reference alone.

    The piece's own words are never read here: only
    its class, the reference it stands under and -
    where the caller names no source - the place it
    stood, carried by the piece as its provenance
    label. A piece with no reference refuses: an act
    of forgetting must name what class of thing and
    which standing thing, or it is no journal entry.
    """
    act, word, day, why, named_source = _frame_words(
        action, requested_by, acted_on, reason, source)
    if memory_ref is None or (
            isinstance(memory_ref, str) and not memory_ref.strip()):
        raise ValueError(
            "a forget entry names the reference the memory "
            "stood under - a piece with no reference cannot "
            "be journaled, by class alone or otherwise")
    standing = named_source if named_source is not None else piece_source
    if standing is None or (
            isinstance(standing, str) and not standing.strip()):
        raise ValueError(
            "a forget entry names where the memory stood")
    return ForgetEntry(
        action=act, memory_class=memory_class,
        memory_ref=memory_ref, reason=why, requested_by=word,
        acted_on=day, source=standing, entry_id=entry_id)


def validate_entry(entry: Any, *, action: Any = None,
                   requested_by: Any = None, acted_on: Any = None,
                   reason: Any = None, source: Any = None
                   ) -> ForgetEntry:
    """Validate one forget entry into a ForgetEntry.

    Accepts an entry; a shipped memory piece - a
    session-memory carried note (M-153), a
    cross-project shared lesson (M-154), a
    self-improving ledger candidate (M-155), a
    decision record (M-156), a project memory-map
    entry (M-150) or a crew-memory entry (M-133),
    judged by its own layer's validation and read
    onto an entry BY IMPORT by its class and
    reference alone, with the frame words named
    beside it (*action*, *requested_by*, *acted_on*,
    *reason* and an optional *source*); or a mapping
    naming an ``action`` (or ``state``), a
    ``memory_class`` (or ``class`` / ``kind``), a
    ``memory_ref`` (or ``ref`` / ``memory_id``), a
    ``reason`` (or ``why``), a ``requested_by`` (or
    ``by`` / ``actor``), an ``acted_on`` (or ``day``
    / ``date``), a ``source`` and an optional
    ``entry_id`` (or ``id``). A mapping naming a
    content key - the forgotten thing's own words -
    refuses by name: the journal holds class and
    reference, never content. Naming two spellings
    of one field with different values refuses, and
    unknown keys refuse.
    """
    if isinstance(entry, ForgetEntry):
        return entry
    if isinstance(entry, CarriedMemory):
        validated = _validate_note(entry)
        return _entry_for(
            "session-memory", validated.note_id,
            validated.source, action=action,
            requested_by=requested_by, acted_on=acted_on,
            reason=reason, source=source)
    if isinstance(entry, SharedLesson):
        validated = _validate_lesson(entry)
        return _entry_for(
            "cross-project", validated.lesson_id,
            validated.source, action=action,
            requested_by=requested_by, acted_on=acted_on,
            reason=reason, source=source)
    if isinstance(entry, CandidateMemory):
        validated = _validate_candidate(entry)
        return _entry_for(
            "ledger-candidate", validated.candidate_id,
            validated.source, action=action,
            requested_by=requested_by, acted_on=acted_on,
            reason=reason, source=source)
    if isinstance(entry, DecisionRecord):
        validated = _validate_decision(entry)
        return _entry_for(
            "decision-record", validated.record_id,
            validated.source, action=action,
            requested_by=requested_by, acted_on=acted_on,
            reason=reason, source=source)
    if isinstance(entry, MemoryMapEntry):
        validated = _validate_map_entry(entry)
        return _entry_for(
            "memory-map", validated.entry_id,
            validated.source, action=action,
            requested_by=requested_by, acted_on=acted_on,
            reason=reason, source=source)
    if isinstance(entry, CrewMemoryEntry):
        validated = _validate_crew_entry(entry)
        provenance = validated.provenance
        piece_source = provenance if isinstance(provenance, str) \
            and provenance.strip() else None
        return _entry_for(
            "crew-memory", validated.entry_id, piece_source,
            action=action, requested_by=requested_by,
            acted_on=acted_on, reason=reason, source=source)
    if not isinstance(entry, dict):
        raise ValueError(
            f"a forget entry must be a mapping, got {entry!r}")
    content = set(entry) & _CONTENT_KEYS
    if content:
        raise ValueError(
            "a forget entry never carries the forgotten "
            "thing's content - journaled by class and "
            "reference only; refusing content keys: %s"
            % ", ".join(sorted(content)))
    unknown = set(entry) - _ENTRY_KEYS
    if unknown:
        raise ValueError(
            "unknown entry keys: %s" % ", ".join(sorted(unknown)))

    def _needed(spellings: Tuple[str, ...], what: str) -> Any:
        value = _pick_any(entry, spellings, what)
        if value is None:
            raise ValueError(f"a forget entry is missing its {what}")
        return value

    kwargs: Dict[str, Any] = {
        "action": _needed(("action", "state"), "action"),
        "memory_class": _needed(
            ("memory_class", "class", "kind"), "memory class"),
        "memory_ref": _needed(
            ("memory_ref", "ref", "memory_id"), "memory reference"),
        "reason": _needed(("reason", "why"), "reason"),
        "requested_by": _needed(
            ("requested_by", "by", "actor"), "requesting word"),
        "acted_on": _needed(
            ("acted_on", "day", "date"), "acted-on day"),
        "source": _needed(("source",), "source"),
    }
    named_id = _pick_any(entry, ("entry_id", "id"), "entry ids")
    if named_id is not None:
        kwargs["entry_id"] = named_id
    return ForgetEntry(**kwargs)


_FRAME_KEYS = (
    "action", "requested_by", "acted_on", "reason", "source")


def build_entry(entry: Any = None, **kwargs: Any) -> ForgetEntry:
    """Build one validated entry, from a mapping or field words.

    Frame words for a composed piece (``action``,
    ``requested_by``, ``acted_on``, ``reason`` and an
    optional ``source``) may ride in the field words;
    in a mapping they are the entry's own fields.
    """
    frame = {
        key: kwargs.pop(key) for key in _FRAME_KEYS if key in kwargs}
    if isinstance(entry, ForgetEntry) and not kwargs and not frame:
        return entry
    if isinstance(entry, (CarriedMemory, SharedLesson, CandidateMemory,
                          DecisionRecord, MemoryMapEntry,
                          CrewMemoryEntry)):
        if kwargs:
            raise ValueError(
                "a composed entry takes only its frame words")
        return validate_entry(entry, **frame)
    if isinstance(entry, dict) or entry is None:
        merged: Dict[str, Any] = {}
        if isinstance(entry, dict):
            merged.update(entry)
        merged.update(frame)
        merged.update(kwargs)
        return validate_entry(merged)
    raise ValueError(
        f"a forget entry must be a mapping, got {entry!r}")


def _check_entry_ref(value: Any) -> ForgetEntry:
    if isinstance(value, ForgetEntry):
        return value
    if isinstance(value, dict):
        return validate_entry(value)
    raise ValueError(f"a forget entry is needed, got {value!r}")


def inspect_memory(piece: Any) -> Dict[str, Any]:
    """Inspect one shipped memory piece: its class and reference only.

    This is the inspection road the roadmap words
    name: any memory can be inspected - and what an
    inspection of a piece for the forgetting journal
    returns is the piece's class (its shipped
    holding's own name) and the reference it stands
    under, judged by its own layer's validation BY
    IMPORT. The piece is judged by the layer that
    owns its type, never by whichever validator
    happens to accept its shape first. The piece's
    title, detail and words are never read onto the
    result: inspection for this journal is by class
    and reference, and the piece's own surfaces are
    where its words are inspected. A piece with no
    reference, or a value no shipped layer owns,
    refuses.
    """
    if isinstance(piece, ForgetEntry):
        return {
            "memory_class": piece.memory_class,
            "memory_ref": piece.memory_ref}
    owned = (
        (CarriedMemory, _validate_note, "session-memory", "note_id"),
        (SharedLesson, _validate_lesson, "cross-project", "lesson_id"),
        (CandidateMemory, _validate_candidate,
         "ledger-candidate", "candidate_id"),
        (DecisionRecord, _validate_decision,
         "decision-record", "record_id"),
        (MemoryMapEntry, _validate_map_entry, "memory-map", "entry_id"),
        (CrewMemoryEntry, _validate_crew_entry,
         "crew-memory", "entry_id"),
    )
    for kind, validator, memory_class, attr in owned:
        if isinstance(piece, kind):
            validated = validator(piece)
            ref = getattr(validated, attr, None)
            if ref is None or (
                    isinstance(ref, str) and not ref.strip()):
                raise ValueError(
                    "an inspected memory names the reference "
                    "it stands under - this piece carries none")
            return {"memory_class": memory_class, "memory_ref": ref}
    if isinstance(piece, dict):
        if "memory_class" in piece and (
                "memory_ref" in piece or "ref" in piece):
            checked = validate_entry(piece)
            return {
                "memory_class": checked.memory_class,
                "memory_ref": checked.memory_ref}
        for kind, validator, memory_class, attr in owned:
            try:
                validated = validator(piece)
            except Exception:
                continue
            ref = getattr(validated, attr, None)
            if ref is None or (
                    isinstance(ref, str) and not ref.strip()):
                continue
            return {"memory_class": memory_class, "memory_ref": ref}
    raise ValueError(
        f"no shipped memory layer owns this piece, got {piece!r}")


def entry_from_session_memory(note: Any, *, action: Any = None,
                              requested_by: Any, acted_on: Any,
                              reason: Any, source: Any = None
                              ) -> ForgetEntry:
    """Build one entry from a shipped session-memory carried note.

    The note - session memory's own record, judged by
    that layer's own validation - is read onto an
    entry BY IMPORT by its class and reference alone:
    its id stands as the entry's reference and its
    source as where the memory stood. Its title and
    detail are never read here. The frame words are
    named beside it: the act, the word it is done on,
    the day and the class-level reason.
    """
    validated = _validate_note(note)
    return _entry_for(
        "session-memory", validated.note_id, validated.source,
        action=action, requested_by=requested_by,
        acted_on=acted_on, reason=reason, source=source)


def entry_from_cross_project(lesson: Any, *, action: Any = None,
                             requested_by: Any, acted_on: Any,
                             reason: Any, source: Any = None
                             ) -> ForgetEntry:
    """Build one entry from a shipped cross-project shared lesson.

    The lesson - cross-project memory's own record,
    judged by that layer's own validation - is read
    onto an entry BY IMPORT by its class and reference
    alone: its id stands as the reference. Its title,
    detail and evidence are never read here. The frame
    words are named beside it, exactly as for a note.
    """
    validated = _validate_lesson(lesson)
    return _entry_for(
        "cross-project", validated.lesson_id, validated.source,
        action=action, requested_by=requested_by,
        acted_on=acted_on, reason=reason, source=source)


def entry_from_ledger_candidate(candidate: Any, *, action: Any = None,
                                requested_by: Any, acted_on: Any,
                                reason: Any, source: Any = None
                                ) -> ForgetEntry:
    """Build one entry from a shipped self-improving ledger candidate.

    The candidate - the ledger's own record, judged by
    that layer's own validation - is read onto an entry
    BY IMPORT by its class and reference alone. Its
    title and detail are never read here. The frame
    words are named beside it, exactly as for a note.
    """
    validated = _validate_candidate(candidate)
    return _entry_for(
        "ledger-candidate", validated.candidate_id,
        validated.source, action=action,
        requested_by=requested_by, acted_on=acted_on,
        reason=reason, source=source)


def entry_from_decision_record(record: Any, *, action: Any = None,
                               requested_by: Any, acted_on: Any,
                               reason: Any, source: Any = None
                               ) -> ForgetEntry:
    """Build one entry from a shipped decision record.

    The record - decision records' own record, judged
    by that layer's own validation - is read onto an
    entry BY IMPORT by its class and reference alone.
    Its title, decision and rationale are never read
    here. The frame words are named beside it, exactly
    as for a note.
    """
    validated = _validate_decision(record)
    return _entry_for(
        "decision-record", validated.record_id, validated.source,
        action=action, requested_by=requested_by,
        acted_on=acted_on, reason=reason, source=source)


def entry_from_memory_map(entry: Any, *, action: Any = None,
                          requested_by: Any, acted_on: Any,
                          reason: Any, source: Any = None
                          ) -> ForgetEntry:
    """Build one entry from a shipped project memory-map entry.

    The entry - the memory map's own record, judged by
    the map's own validation - is read onto an entry BY
    IMPORT by its class and reference alone: any section
    of the map may be forgotten on the user's word, so
    no section is refused here. Its title and detail are
    never read here. The frame words are named beside
    it, exactly as for a note.
    """
    validated = _validate_map_entry(entry)
    return _entry_for(
        "memory-map", validated.entry_id, validated.source,
        action=action, requested_by=requested_by,
        acted_on=acted_on, reason=reason, source=source)


def _session_notes(source: Any) -> Tuple[CarriedMemory, ...]:
    """The carried notes one session-memory source holds."""
    from .session_memory import (
        SessionMemoryBook, SessionMemoryRegistry, SessionSituation)
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
        return tuple(_validate_note(item) for item in source)
    if isinstance(source, (CarriedMemory, dict)):
        return (_validate_note(source),)
    raise ValueError(f"session-memory notes are needed, got {source!r}")


def entries_from_session_memory(source: Any, *, action: Any = None,
                                requested_by: Any, acted_on: Any,
                                reason: Any
                                ) -> Tuple[ForgetEntry, ...]:
    """Entries read off the shipped session memory.

    The carried notes of a session situation - or of a
    whole session-memory book or registry - are read
    onto entries BY IMPORT, judged by session memory's
    own validation on the way, under one frame: the
    act, the word it is done on, the day and the
    class-level reason, all named. Every note's title
    and detail stay in session memory: only ids cross.
    """
    return tuple(
        entry_from_session_memory(
            note, action=action, requested_by=requested_by,
            acted_on=acted_on, reason=reason)
        for note in _session_notes(source))


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


def entries_from_memory_map(source: Any, *, action: Any = None,
                            requested_by: Any, acted_on: Any,
                            reason: Any
                            ) -> Tuple[ForgetEntry, ...]:
    """Entries read off the shipped project memory map.

    The map's entries - every section, for any fact of
    the project may be forgotten on the user's word -
    are read onto entries BY IMPORT, judged by the
    map's own validation on the way, under one frame,
    exactly as for session memory. Only ids cross.
    """
    return tuple(
        entry_from_memory_map(
            entry, action=action, requested_by=requested_by,
            acted_on=acted_on, reason=reason)
        for entry in _map_entries(source))


def forgotten_entries(source: Any) -> Tuple[ForgetEntry, ...]:
    """The entries standing forgotten in one source.

    Read off the source (a book or a registry) at call
    time, in panel order, each entry carried whole -
    its provenance standing beside it exactly as it
    was journaled. A quarantined or restored entry
    stands nowhere here. Nothing is deleted by this
    derivation: the standing is read, never performed.
    """
    entries = _held_entries(source)
    standing = [item for item in entries if item.action == "forgotten"]
    return tuple(sorted(
        standing,
        key=lambda item: (item.memory_class, item.memory_ref)))


# ---------------------------------------------------------------------
# The forget panel: every entry carried whole, derived.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class ForgetPanelRow:
    """One entry carried whole into the panel, with its act.

    ``action`` is the entry's own act; ``entry_id``
    names the entry; ``memory_class`` and
    ``memory_ref`` are the journaled class and
    reference - the whole of what the panel says
    about the thing itself, for a panel row carries
    no content either; ``requested_by`` is the
    entry's provenance head - the word the act was
    done on. :func:`validate_row` judged against its
    entry refuses a row whose fields disagree with
    the row they derive.
    """

    action: str
    entry_id: str
    memory_class: str
    memory_ref: str
    requested_by: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "action", normalize_forget_action(self.action))
        object.__setattr__(
            self, "entry_id", normalize_member_id(self.entry_id))
        object.__setattr__(
            self, "memory_class",
            normalize_memory_class(self.memory_class))
        object.__setattr__(
            self, "memory_ref",
            _check_word(self.memory_ref, "a row's memory reference"))
        object.__setattr__(
            self, "requested_by",
            _check_word(self.requested_by, "a row's requesting word"))

    @property
    def sort_key(self) -> Tuple[int, str, str]:
        """This row's place in panel order (derived).

        Rows stand action first (forgotten, quarantined,
        restored, in that settled order); within an
        action, by memory class, then memory reference.
        """
        return (
            _PANEL_ACTION_ORDER.index(self.action),
            self.memory_class, self.memory_ref)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "forget_panel_row",
            "slice": FORGET_QUARANTINE_SLICE,
            "action": self.action,
            "entry_id": self.entry_id,
            "memory_class": self.memory_class,
            "memory_ref": self.memory_ref,
            "requested_by": self.requested_by,
        }


def _row_for_entry(entry: ForgetEntry) -> ForgetPanelRow:
    return ForgetPanelRow(
        action=entry.action, entry_id=entry.entry_id,
        memory_class=entry.memory_class,
        memory_ref=entry.memory_ref,
        requested_by=entry.requested_by)


def _check_row_ref(value: Any) -> ForgetPanelRow:
    if isinstance(value, ForgetPanelRow):
        return value
    if isinstance(value, dict):
        content = set(value) & _CONTENT_KEYS
        if content:
            raise ValueError(
                "a forget panel row never carries the forgotten "
                "thing's content - refusing content keys: %s"
                % ", ".join(sorted(content)))
        unknown = set(value) - _ROW_KEYS
        if unknown:
            raise ValueError(
                "unknown row keys: %s" % ", ".join(sorted(unknown)))

        def _needed(spellings: Tuple[str, ...], what: str) -> Any:
            picked = _pick_any(value, spellings, what)
            if picked is None:
                raise ValueError(f"a row is missing its {what}")
            return picked

        return ForgetPanelRow(
            action=_needed(("action",), "action"),
            entry_id=_needed(("entry_id", "id"), "entry id"),
            memory_class=_needed(("memory_class",), "memory class"),
            memory_ref=_needed(("memory_ref",), "memory reference"),
            requested_by=_needed(("requested_by",), "requesting word"))
    raise ValueError(f"a panel row is needed, got {value!r}")


def validate_row(row: Any, entry: Any = None) -> ForgetPanelRow:
    """Validate one panel row into a ForgetPanelRow.

    Accepts a row or a mapping naming an ``action``, an
    ``entry_id`` (or ``id``), a ``memory_class``, a
    ``memory_ref`` and a ``requested_by``. With *entry*
    given, the row is judged against the row derived
    from that entry: a stored row whose fields disagree
    with the derived row refuses.
    """
    current = _check_row_ref(row)
    if entry is not None:
        checked_entry = _check_entry_ref(entry)
        derived = _row_for_entry(checked_entry)
        if current != derived:
            raise ValueError(
                "a stored row disagrees with the row "
                "derived from its entry")
    return current


def build_row(row: Any = None, entry: Any = None,
              **kwargs: Any) -> ForgetPanelRow:
    """Build one validated row, from a mapping or field words."""
    if isinstance(row, ForgetPanelRow) and not kwargs:
        return validate_row(row, entry)
    if isinstance(row, dict) or row is None:
        merged: Dict[str, Any] = {}
        if isinstance(row, dict):
            merged.update(row)
        merged.update(kwargs)
        return validate_row(merged, entry)
    return validate_row(row, entry)


@dataclass(frozen=True)
class ForgetActionCount:
    """One action's count in a panel: its entries tallied."""

    action: str
    items: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "action", normalize_forget_action(self.action))
        object.__setattr__(
            self, "items",
            _check_count(self.items, "an action count's items"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "items": self.items,
        }


def _check_action_count_ref(value: Any) -> ForgetActionCount:
    if isinstance(value, ForgetActionCount):
        return value
    if isinstance(value, dict):
        unknown = set(value) - _ACTION_COUNT_KEYS
        if unknown:
            raise ValueError(
                "unknown action-count keys: %s"
                % ", ".join(sorted(unknown)))
        action = _pick_any(value, ("action",), "actions")
        if action is None:
            raise ValueError("an action count is missing its action")
        items = _pick_any(value, ("items", "count"), "counts")
        if items is None:
            raise ValueError("an action count is missing its items")
        return ForgetActionCount(action=action, items=items)
    raise ValueError(f"an action count is needed, got {value!r}")


def _panel_account(total_items: int, total_forgotten: int,
                   total_quarantined: int, total_restored: int
                   ) -> Tuple[str, ...]:
    return (
        f"The forget panel holds {total_items} entries: "
        f"forgotten {total_forgotten}, quarantined "
        f"{total_quarantined}, restored {total_restored}.",
        "Entries stand forgotten first, then quarantined, "
        "then restored; within an action, by memory class, "
        "then memory reference - so two panels of one book "
        "diff cleanly, line by line.",
        "Every entry journals what class of thing was "
        "forgotten, quarantined or restored, and the "
        "reference it stood under - never its content: no "
        "title, detail or fact of the thing stands "
        "anywhere in this book.",
        "The panel is read off the book at call time - "
        "it is derived, never stored loose.",
    )


@dataclass(frozen=True)
class ForgetPanel:
    """The forget panel of one book, derived from the whole book.

    ``rows`` are the book's entries carried whole, in
    panel order (forgotten first, then quarantined,
    then restored; within an action, by memory class,
    then memory reference, so two panels of one book
    diff cleanly); ``total_items`` is the entry count
    and the three action totals are the rows' own
    counts; ``action_counts`` are the per-action
    tallies in the order their actions first appear in
    the panel; ``account`` is read off those numbers.
    A panel whose rows stand out of panel order, or
    whose totals are not its own rows' counts, refuses
    at construction; :func:`validate_panel` judged
    against a book refuses a stored panel that
    disagrees with the derived one.
    """

    rows: Tuple[ForgetPanelRow, ...] = ()
    total_items: int = 0
    total_forgotten: int = 0
    total_quarantined: int = 0
    total_restored: int = 0
    action_counts: Tuple[ForgetActionCount, ...] = ()
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
            if row.entry_id in seen:
                raise ValueError(
                    f"a panel row for entry {row.entry_id!r} "
                    f"already exists")
            seen.add(row.entry_id)
        order = [_PANEL_ACTION_ORDER.index(r.action) for r in rows]
        if order != sorted(order):
            raise ValueError(
                "a panel's rows must stand in panel order "
                "(forgotten, then quarantined, then restored)")
        object.__setattr__(self, "rows", rows)
        for field_name, act, what in (
                ("total_forgotten", "forgotten", "forgotten total"),
                ("total_quarantined", "quarantined",
                 "quarantined total"),
                ("total_restored", "restored", "restored total")):
            checked = _check_count(
                getattr(self, field_name), f"a panel's {what}")
            if checked != sum(1 for r in rows if r.action == act):
                raise ValueError(
                    f"a panel's {what} must be its own rows' count")
            object.__setattr__(self, field_name, checked)
        object.__setattr__(
            self, "total_items",
            _check_count(self.total_items, "a panel's total"))
        if self.total_items != len(rows):
            raise ValueError(
                "a panel's total must be its own rows' count")
        if isinstance(self.action_counts, (str, bytes)) \
                or not isinstance(self.action_counts, (list, tuple)):
            raise ValueError(
                f"a panel's action counts must be a list, "
                f"got {self.action_counts!r}")
        action_counts = tuple(
            _check_action_count_ref(c) for c in self.action_counts)
        seen_actions = set()
        for count in action_counts:
            if count.action in seen_actions:
                raise ValueError(
                    f"an action count named {count.action!r} "
                    f"already exists")
            seen_actions.add(count.action)
        object.__setattr__(self, "action_counts", action_counts)
        if sum(c.items for c in action_counts) != self.total_items:
            raise ValueError(
                "a panel's action counts must sum to its own total")
        for count in action_counts:
            if count.items != sum(
                    1 for r in rows if r.action == count.action):
                raise ValueError(
                    "a panel's action counts must be its own "
                    "rows' counts")
        object.__setattr__(self, "account", _check_account(self.account))

    def row_for(self, entry_id: Any) -> ForgetPanelRow:
        """The panel row one entry names in this panel."""
        wanted = normalize_member_id(entry_id)
        for row in self.rows:
            if row.entry_id == wanted:
                return row
        raise KeyError(f"no row in the panel: entry {wanted!r}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "forget_panel",
            "slice": FORGET_QUARANTINE_SLICE,
            "panel_id": self.panel_id,
            "rows": [row.to_record() for row in self.rows],
            "total_items": self.total_items,
            "total_forgotten": self.total_forgotten,
            "total_quarantined": self.total_quarantined,
            "total_restored": self.total_restored,
            "action_counts": [c.to_record() for c in self.action_counts],
            "account": list(self.account),
        }


def _held_entries(source: Any) -> Tuple[ForgetEntry, ...]:
    """The entries one source holds, in held order."""
    if isinstance(source, ForgetBook):
        return source.entries
    if isinstance(source, ForgetRegistry):
        return source.list_entries()
    if isinstance(source, (list, tuple)):
        return tuple(_check_entry_ref(item) for item in source)
    raise ValueError(f"forget entries are needed, got {source!r}")


def derive_panel(source: Any) -> ForgetPanel:
    """Derive the forget panel from one book.

    The rows are the book's entries carried whole, in
    panel order: forgotten first, then quarantined,
    then restored; within an action, by the entry's
    memory class, then its reference. *source* is a
    book or a registry. A source holding no entry
    refuses - a panel of nothing is no panel.
    """
    entries = _held_entries(source)
    if not entries:
        raise ValueError("a panel needs at least one entry")
    rows = []
    for entry in entries:
        if entry.entry_id is None:
            raise ValueError(
                "a panel row must name its entry - an "
                "entry with no id refuses derivation")
        rows.append(_row_for_entry(entry))
    rows = tuple(sorted(rows, key=lambda r: r.sort_key))
    order: list = []
    tally: Dict[str, int] = {}
    for row in rows:
        if row.action not in tally:
            tally[row.action] = 0
            order.append(row.action)
        tally[row.action] += 1
    action_counts = tuple(
        ForgetActionCount(action=action, items=tally[action])
        for action in order)
    totals = {act: tally.get(act, 0) for act in FORGET_ACTIONS}
    return ForgetPanel(
        rows=rows, total_items=len(rows),
        total_forgotten=totals["forgotten"],
        total_quarantined=totals["quarantined"],
        total_restored=totals["restored"],
        action_counts=action_counts,
        account=_panel_account(
            len(rows), totals["forgotten"],
            totals["quarantined"], totals["restored"]))


def validate_panel(panel: Any, source: Any = None) -> ForgetPanel:
    """Validate one panel into a ForgetPanel.

    Accepts a panel or a mapping naming ``rows`` (or
    ``entries``), a ``total_items`` (or ``total``), the
    three action totals, ``action_counts`` (or
    ``actions``), an ``account`` (or ``statements``) and
    an optional ``panel_id`` (or ``id``). With *source*
    given (a book), the panel is judged against the
    panel derived from that book: a stored panel whose
    rows, totals, action counts or account disagree
    with the derived panel refuses. A panel naming no
    account refuses too.
    """
    if isinstance(panel, ForgetPanel):
        current = panel
    elif isinstance(panel, dict):
        content = set(panel) & _CONTENT_KEYS
        if content:
            raise ValueError(
                "a forget panel never carries the forgotten "
                "thing's content - refusing content keys: %s"
                % ", ".join(sorted(content)))
        unknown = set(panel) - _PANEL_KEYS
        if unknown:
            raise ValueError(
                "unknown panel keys: %s" % ", ".join(sorted(unknown)))
        rows = _pick_any(panel, ("rows", "entries"), "rows")
        if rows is None:
            raise ValueError("a panel is missing its rows")
        total = _pick_any(panel, ("total_items", "total"), "totals")
        if total is None:
            raise ValueError("a panel is missing its total items")
        action_counts = _pick_any(
            panel, ("action_counts", "actions"), "action counts")
        if action_counts is None:
            raise ValueError("a panel is missing its action counts")
        account = _pick_any(panel, ("account", "statements"), "accounts")
        if account is None:
            raise ValueError("a panel names no account of its own")
        kwargs: Dict[str, Any] = {
            "rows": rows, "total_items": total,
            "action_counts": action_counts, "account": account}
        for field_name in (
                "total_forgotten", "total_quarantined", "total_restored"):
            value = _pick_any(panel, (field_name,), field_name)
            if value is None:
                raise ValueError(f"a panel is missing its {field_name}")
            kwargs[field_name] = value
        panel_id = _pick_any(panel, ("panel_id", "id"), "panel ids")
        if panel_id is not None:
            kwargs["panel_id"] = panel_id
        current = ForgetPanel(**kwargs)
    else:
        raise ValueError(f"a panel must be a mapping, got {panel!r}")
    if source is not None:
        derived = derive_panel(source)
        if (current.rows != derived.rows
                or current.total_items != derived.total_items
                or current.total_forgotten != derived.total_forgotten
                or current.total_quarantined != derived.total_quarantined
                or current.total_restored != derived.total_restored
                or current.action_counts != derived.action_counts
                or current.account != derived.account):
            raise ValueError(
                "a stored panel disagrees with the panel "
                "derived from its book")
    return current


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> ForgetPanel:
    """Build one validated panel, from a mapping or field words."""
    if isinstance(panel, ForgetPanel) and not kwargs:
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
class ForgetBook:
    """One forget book: its entries, in held order.

    ``entries`` are the forget entries, in held order,
    each with its provenance whole; a restored entry
    is judged against the book at construction: its
    class and reference name a memory a quarantined
    entry of the book holds apart. ``panels`` are the
    book's derivations - forget panels of the whole
    book, each judged against the book by
    :func:`validate_book`; ``canon_note`` is the book's
    own note. The total is the entries' own count,
    judged at construction. This book is the book
    file's shape: the shipped example is one book, and
    a real book file is a new file in this shape.
    """

    title: str = ""
    entries: Tuple[ForgetEntry, ...] = ()
    panels: Tuple[ForgetPanel, ...] = ()
    canon_note: str = ""
    total_entries: Optional[int] = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_title(self.title, "a book's title"))
        if isinstance(self.entries, (str, bytes)) \
                or not isinstance(self.entries, (list, tuple)):
            raise ValueError(
                f"a book's entries must be a list of "
                f"forget entries, got {self.entries!r}")
        entries = tuple(_check_entry_ref(item) for item in self.entries)
        if not entries:
            raise ValueError("a forget book holds at least one entry")
        seen_ids = set()
        seen_acts = set()
        quarantined = set()
        for entry in entries:
            if entry.entry_id is not None:
                if entry.entry_id in seen_ids:
                    raise ValueError(
                        f"an entry named {entry.entry_id!r} "
                        f"already exists")
                seen_ids.add(entry.entry_id)
            key = (entry.action, entry.memory_class, entry.memory_ref)
            if key in seen_acts:
                raise ValueError(
                    f"the {entry.memory_class} memory "
                    f"{entry.memory_ref!r} already stands "
                    f"{entry.action} in this book")
            seen_acts.add(key)
            if entry.action == "quarantined":
                quarantined.add((entry.memory_class, entry.memory_ref))
        for entry in entries:
            if entry.action == "restored" and (
                    entry.memory_class, entry.memory_ref) not in quarantined:
                raise ValueError(
                    f"a restored entry names a memory no "
                    f"quarantined entry of this book holds "
                    f"apart: {entry.memory_ref!r} - what was "
                    f"forgotten is gone, and what was never "
                    f"quarantined cannot be restored")
        object.__setattr__(self, "entries", entries)
        if isinstance(self.panels, (str, bytes)) \
                or not isinstance(self.panels, (list, tuple)):
            raise ValueError(
                f"a book's panels must be a list of panels, "
                f"got {self.panels!r}")
        panels = tuple(
            p if isinstance(p, ForgetPanel) else validate_panel(p)
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
        given = self.total_entries
        if given is None:
            object.__setattr__(self, "total_entries", len(entries))
        else:
            checked = _check_count(given, "a book's total entries")
            if checked != len(entries):
                raise ValueError(
                    "a book's total entries must be its own "
                    "entries' count")
            object.__setattr__(self, "total_entries", checked)

    def entry_for(self, entry_id: Any) -> ForgetEntry:
        """The entry one id names in this book."""
        wanted = normalize_member_id(entry_id)
        for entry in self.entries:
            if entry.entry_id == wanted:
                return entry
        raise KeyError(f"no entry in the book: {wanted!r}")

    def panel_for(self, panel_id: Any) -> ForgetPanel:
        """The stored panel one id names in this book."""
        wanted = normalize_member_id(panel_id)
        for panel in self.panels:
            if panel.panel_id == wanted:
                return panel
        raise KeyError(f"no panel in the book: {wanted!r}")

    def entry_ids(self) -> Tuple[str, ...]:
        """Every held entry id, in held order."""
        return tuple(item.entry_id for item in self.entries if item.entry_id)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "forget_book",
            "slice": FORGET_QUARANTINE_SLICE,
            "title": self.title,
            "entry_ids": list(self.entry_ids()),
            "entry_count": len(self.entries),
            "panel_count": len(self.panels),
        }


def validate_book(data: Any, *, require_example: bool = False
                  ) -> ForgetBook:
    """Validate one forget-quarantine mapping into a book.

    The mapping names a ``schema`` (the
    forget-quarantine schema word), a ``guide``
    mapping (its ``title``), an ``entries`` list and
    an optional ``panels`` list. Every entry stands on
    its own validation, then the whole is judged:
    entry ids unique, no memory named twice for one
    action, every restored entry judged against the
    book's quarantined entries, and every stored panel
    judged against the book (a panel the book does not
    derive refuses). With ``require_example`` the
    shipped example is held to its pinned shape: the
    pinned title, entries and panel, and the panel's
    pinned rows and account word-for-word. Problems
    raise :class:`ValidationError` or ``ValueError``.
    """
    if isinstance(data, ForgetBook):
        return data
    if not isinstance(data, dict):
        raise ValidationError(
            f"a forget book must be a mapping, got {data!r}")
    content = set(data) & _CONTENT_KEYS
    if content:
        raise ValidationError(
            "a forget book never carries the forgotten "
            "thing's content - refusing content keys: %s"
            % ", ".join(sorted(content)))
    unknown = set(data) - _FORGET_BOOK_KEYS
    if unknown:
        raise ValidationError(
            "unknown forget-book keys: %s" % ", ".join(sorted(unknown)))
    if data.get("schema") != FORGET_QUARANTINE_SCHEMA:
        raise ValidationError(
            f"a forget book must carry schema "
            f"{FORGET_QUARANTINE_SCHEMA!r}, got {data.get('schema')!r}")
    entries = _pick_any(data, ("entries",), "entries")
    if entries is None:
        raise ValidationError("a forget book is missing its entries")
    if not isinstance(entries, (list, tuple)):
        raise ValidationError("a forget book's entries must be a list")
    if data.get("panels") is not None \
            and not isinstance(data["panels"], (list, tuple)):
        raise ValidationError("a forget book's panels must be a list")
    head = data.get("guide") or {}
    if not isinstance(head, dict):
        raise ValidationError("a forget book's guide must be a mapping")
    unknown_head = set(head) - _BOOK_KEYS
    if unknown_head:
        raise ValidationError(
            "unknown guide keys: %s" % ", ".join(sorted(unknown_head)))
    try:
        title = _pick_any(head, ("title", "name"), "titles")
        if title is None:
            raise ValidationError("a forget book is missing its title")
        note = data.get("canon_note") or ""
        if not isinstance(note, str):
            raise ValidationError("a forget book's note must be text")
        book = ForgetBook(
            title=title, entries=tuple(entries),
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
                "the shipped example forget book's title is "
                "not the pinned title")
        if book.entry_ids() != _EXAMPLE_ENTRY_IDS:
            raise ValidationError(
                "the shipped example's entries are not the "
                "pinned entries")
        panel = book.panel_for(_EXAMPLE_PANEL_ID)
        if tuple(r.entry_id for r in panel.rows) != _EXAMPLE_PANEL_ROW_IDS:
            raise ValidationError(
                "the shipped example panel does not name its "
                "pinned rows in panel order")
        if panel.account != _EXAMPLE_PANEL_ACCOUNT:
            raise ValidationError(
                "the shipped example panel does not carry its "
                "pinned account word-for-word")
        first = book.entries[0]
        if first.entry_id != _EXAMPLE_FIRST_ENTRY_ID \
                or first.memory_class != _EXAMPLE_FIRST_ENTRY_CLASS:
            raise ValidationError(
                "the shipped example's first entry is not its "
                "pinned entry of its pinned class")
    return book


def build_book(book: Any = None, **kwargs: Any) -> ForgetBook:
    """Build one validated book, from a mapping or field words."""
    if isinstance(book, ForgetBook) and not kwargs:
        return book
    if isinstance(book, dict):
        if "schema" in book:
            return validate_book(book)
        merged: Dict[str, Any] = dict(book)
        merged.update(kwargs)
        return ForgetBook(**merged)
    if book is None:
        return ForgetBook(**kwargs)
    raise ValueError(f"a forget book is needed, got {book!r}")


def _book_from(data: Any, *, require_example: bool) -> ForgetBook:
    try:
        return validate_book(data, require_example=require_example)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def load_forget_quarantine(
        data: Optional[Dict[str, Any]] = None) -> ForgetBook:
    """Load and validate the shipped example book (or *data*).

    The shipped file is held to the example check: the
    pinned title, entries and panel - the M-156 slice
    boundary book - so the shipped book covers the
    canon this slice exists to hold.
    """
    raw = data if data is not None else load_resource(
        FORGET_QUARANTINE_RESOURCE)
    return _book_from(raw, require_example=True)


def load_forget_quarantine_file(path: Any) -> ForgetBook:
    """Load and validate a forget book from a file at *path*.

    Any file in the forget-quarantine shape, anywhere on
    disk, validated whole - a malformed file raises
    :class:`ValidationError` naming the problem, and a
    missing file raises ``FileNotFoundError``. The
    example check is not held: a real book stands on its
    own entries.
    """
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _book_from(raw, require_example=False)


# ---------------------------------------------------------------------
# The registry model: one book held entry by entry.
# ---------------------------------------------------------------------


class ForgetRegistry:
    """One session's forget entries, held one by one.

    The registry holds entries, never panels: the panel
    is a derivation, read off the whole held book at
    call time, so nothing here can hold a figure stale.
    A restored entry held one by one names a memory a
    quarantined entry already standing here holds
    apart; a whole book is judged as a book judges it,
    against the whole book, before its entries are held
    in book order. Nothing is forgotten by capture, by
    age or by count: an entry held here stands in the
    act it was held in, on the word it names.
    """

    def __init__(self, book: Any = None) -> None:
        self._title: Optional[str] = None
        self._entries: Dict[str, ForgetEntry] = {}
        self._entry_order: list = []
        self._next_entry = 1
        if book is not None:
            self.register_book(book)

    def _fresh_entry_id(self, held_ids: Any) -> str:
        while f"entry-{self._next_entry}" in held_ids:
            self._next_entry += 1
        fresh = f"entry-{self._next_entry}"
        self._next_entry += 1
        return fresh

    def register_entry(self, entry: Any) -> ForgetEntry:
        """Register one entry into the held book.

        An entry with no id is given a deterministic
        ``entry-N`` id. An entry id already standing here
        refuses, as does a memory one action already
        stands for in this book, and a restored entry
        naming a memory no quarantined entry held here
        holds apart.
        """
        validated = _check_entry_ref(entry)
        held_ids = set(self._entries)
        if validated.entry_id is not None \
                and validated.entry_id in held_ids:
            raise ValueError(
                f"an entry named {validated.entry_id!r} "
                f"already exists")
        for held in self._entries.values():
            if (held.action, held.memory_class, held.memory_ref) == (
                    validated.action, validated.memory_class,
                    validated.memory_ref):
                raise ValueError(
                    f"the {validated.memory_class} memory "
                    f"{validated.memory_ref!r} already stands "
                    f"{validated.action} in this book")
        if validated.action == "restored" and not any(
                held.action == "quarantined"
                and held.memory_class == validated.memory_class
                and held.memory_ref == validated.memory_ref
                for held in self._entries.values()):
            raise ValueError(
                f"a restored entry names a memory no "
                f"quarantined entry of this book holds apart: "
                f"{validated.memory_ref!r}")
        return self._hold_entry(validated)

    def _hold_entry(self, validated: ForgetEntry) -> ForgetEntry:
        """Hold one judged entry, in held order.

        The caller has already judged the entry against
        the held book (its id, its act and its restore
        law); this is the holding alone, with a
        deterministic ``entry-N`` id given to an entry
        carrying none.
        """
        if validated.entry_id is None:
            validated = replace(
                validated,
                entry_id=self._fresh_entry_id(set(self._entries)))
        self._entries[validated.entry_id] = validated
        self._entry_order.append(validated.entry_id)
        return validated

    def register_book(self, book: Any) -> ForgetBook:
        """Register every entry of one book, in order.

        The first book held sets the title; a later book
        under a different title refuses, as does a book
        naming a held entry id or a memory a held action
        already stands for here. The book is judged whole
        before anything is held - as a book judges a
        restored entry against the whole book, a restored
        entry may answer a quarantined entry the same book
        holds later in held order - and the entries are
        then held in the book's own order. The book's
        panels are derivations, not holdings, and are not
        held.
        """
        validated = build_book(book)
        if self._title is not None and validated.title != self._title:
            raise ValueError(
                "this registry already holds a forget book "
                "under a different title")
        for entry in validated.entries:
            if entry.entry_id in self._entries:
                raise ValueError(
                    f"an entry named {entry.entry_id!r} "
                    f"already exists")
            for held in self._entries.values():
                if (held.action, held.memory_class, held.memory_ref) == (
                        entry.action, entry.memory_class,
                        entry.memory_ref):
                    raise ValueError(
                        f"the {entry.memory_class} memory "
                        f"{entry.memory_ref!r} already stands "
                        f"{entry.action} in this book")
        known_quarantined = {
            (held.memory_class, held.memory_ref)
            for held in self._entries.values()
            if held.action == "quarantined"} | {
            (item.memory_class, item.memory_ref)
            for item in validated.entries
            if item.action == "quarantined"}
        for entry in validated.entries:
            if entry.action == "restored" and (
                    entry.memory_class, entry.memory_ref) \
                    not in known_quarantined:
                raise ValueError(
                    f"a restored entry names a memory no "
                    f"quarantined entry of this book holds "
                    f"apart: {entry.memory_ref!r}")
        self._title = validated.title
        for entry in validated.entries:
            self._hold_entry(entry)
        return self.book()

    def get_entry(self, entry_id: Any) -> ForgetEntry:
        """The entry one id names among the held entries."""
        wanted = normalize_member_id(entry_id)
        if wanted not in self._entries:
            raise KeyError(f"unknown entry: {wanted!r}")
        return self._entries[wanted]

    def latest_entry(self) -> ForgetEntry:
        """The most recently held entry."""
        if not self._entry_order:
            raise ValueError("no entry is held yet")
        return self._entries[self._entry_order[-1]]

    def list_entries(self) -> Tuple[ForgetEntry, ...]:
        """Every held entry, in the order they were held."""
        return tuple(self._entries[item] for item in self._entry_order)

    def book(self) -> ForgetBook:
        """The held entries as one validated book."""
        if self._title is None:
            raise ValueError("no forget book is held yet")
        return ForgetBook(title=self._title, entries=self.list_entries())

    def panel(self) -> ForgetPanel:
        """Derive the forget panel of the whole held book."""
        return derive_panel(self)

    def forgotten_entries(self) -> Tuple[ForgetEntry, ...]:
        """The held entries standing forgotten."""
        return forgotten_entries(self)


# ---------------------------------------------------------------------
# Forget news, shaped as session records.
# ---------------------------------------------------------------------


def entry_record(entry: Any) -> Dict[str, Any]:
    """The session-news record of one forget entry.

    The headline names the class and the reference
    alone: the forgotten thing's words stand in no
    headline, here or anywhere on this layer.
    """
    current = entry if isinstance(entry, ForgetEntry) \
        else build_entry(entry)
    record_out = current.to_record()
    record_out["news"] = True
    record_out["headline"] = (
        f"A {current.memory_class} memory "
        f"({current.memory_ref}) was {current.action} on "
        f"the word of {current.requested_by} on "
        f"{current.acted_on}.")
    return record_out


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of one derived panel.

    With *source* given, the panel is first judged
    against the panel that source derives.
    """
    current = validate_panel(panel, source)
    record_out = current.to_record()
    record_out["news"] = True
    record_out["headline"] = (
        f"Forget panel: {current.total_items} entries - "
        f"forgotten {current.total_forgotten}, quarantined "
        f"{current.total_quarantined}, restored "
        f"{current.total_restored}.")
    return record_out


def book_record(book: Any) -> Dict[str, Any]:
    """The session-news record of one forget book."""
    current = book if isinstance(book, ForgetBook) else build_book(book)
    record_out = current.to_record()
    record_out["news"] = True
    record_out["headline"] = (
        f"Forget and quarantine {current.title}: "
        f"{record_out['entry_count']} entries named.")
    return record_out


def plain_words(entry: Any) -> str:
    """One forget entry, in one plain sentence."""
    current = entry if isinstance(entry, ForgetEntry) \
        else build_entry(entry)
    return (
        f"A {current.memory_class} memory "
        f"({current.memory_ref}) was {current.action} on "
        f"the word of {current.requested_by} on "
        f"{current.acted_on}: {current.reason} Its content "
        f"is not kept here. (journaled from {current.source}).")


def panel_plain_words(source: Any) -> str:
    """The forget panel in plain words, in full.

    Accepts a ForgetPanel or a ForgetBook (whose derived
    panel is told). The panel is told whole - its rows in
    panel order and its account.
    """
    if isinstance(source, ForgetPanel):
        panel = validate_panel(source)
        title = None
    elif isinstance(source, ForgetBook):
        panel = derive_panel(source)
        title = source.title
    else:
        raise ValueError(
            f"a forget-quarantine source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    lines.append("Entries, in panel order:")
    for row in panel.rows:
        lines.append(
            f"{row.entry_id}: {row.action} - a "
            f"{row.memory_class} memory ({row.memory_ref}), "
            f"on the word of {row.requested_by}")
    lines.extend(panel.account)
    return "\n".join(lines)


# ---------------------------------------------------------------------
# Screens: the formatters and the /forget grammar.
# ---------------------------------------------------------------------


def _source_book(source: Any) -> ForgetBook:
    if source is None:
        return load_forget_quarantine()
    if isinstance(source, ForgetRegistry):
        return source.book()
    if isinstance(source, ForgetBook):
        return source
    raise ValueError(f"a forget book is needed, got {source!r}")


def format_entry(entry: Any) -> str:
    """One forget entry as a screen block, provenance whole."""
    current = entry if isinstance(entry, ForgetEntry) \
        else build_entry(entry)
    return "\n".join([
        f"{current.entry_id or '-'}: a {current.memory_class} "
        f"memory ({current.memory_ref}) - {current.action}, on "
        f"the word of {current.requested_by} on {current.acted_on}",
        f"Why (class only): {current.reason}",
        f"(journaled from {current.source})",
        "Content: not kept - the forgetting is journaled by "
        "class and reference only.",
    ])


def format_entries(source: Any = None) -> str:
    """Forget entries of one book, in held order."""
    book = _source_book(source)
    lines = [
        f"{item.entry_id or '-'}: {item.action} - a "
        f"{item.memory_class} memory ({item.memory_ref}), on "
        f"the word of {item.requested_by}"
        for item in book.entries]
    if not lines:
        lines.append("No entries are held.")
    return "\n".join(lines)


def format_forgotten(source: Any = None) -> str:
    """The entries standing forgotten in one book."""
    standing = forgotten_entries(_source_book(source))
    lines = [
        f"{item.entry_id or '-'}: a {item.memory_class} memory "
        f"({item.memory_ref}) - forgotten on the word of "
        f"{item.requested_by} on {item.acted_on}"
        for item in standing]
    if not lines:
        lines.append("No memories stand forgotten yet.")
    return "\n".join(lines)


def format_quarantined(source: Any = None) -> str:
    """The entries standing quarantined in one book, net of restores.

    A quarantined memory a later restored entry of the
    same book stands again stands nowhere here: the
    quarantine was answered. Only memories still held
    apart are listed.
    """
    book = _source_book(source)
    restored = {
        (item.memory_class, item.memory_ref)
        for item in book.entries if item.action == "restored"}
    standing = [
        item for item in book.entries
        if item.action == "quarantined"
        and (item.memory_class, item.memory_ref) not in restored]
    lines = [
        f"{item.entry_id or '-'}: a {item.memory_class} memory "
        f"({item.memory_ref}) - quarantined on the word of "
        f"{item.requested_by} on {item.acted_on}"
        for item in standing]
    if not lines:
        lines.append("No memories stand quarantined.")
    return "\n".join(lines)


def format_panel(source: Any = None) -> str:
    """The forget panel as a screen block: every row and the account.

    Accepts a ForgetPanel or a ForgetBook; a book shows
    the panel it derives.
    """
    if isinstance(source, ForgetPanel):
        panel = validate_panel(source)
        lines: list = []
    else:
        book = _source_book(source)
        if not book.entries:
            return (f"Forget panel in {book.title}:\n"
                    f"No entries are held.")
        panel = derive_panel(book)
        lines = [f"Forget panel in {book.title}:"]
    lines.append("Entries, in panel order:")
    for row in panel.rows:
        lines.append(
            f"{row.entry_id}: {row.action} - a "
            f"{row.memory_class} memory ({row.memory_ref}), "
            f"on the word of {row.requested_by}")
    lines.extend(panel.account)
    return "\n".join(lines)


def format_forget_quarantine_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /forget.

    With nothing named, the shipped example forget book
    is shown - the example this slice ships - so the
    screen is never empty.
    """
    book = _source_book(source)
    lines = ["Forget and Quarantine (M-157) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_entries(book))
    lines.append("")
    lines.append(format_panel(book))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_forget_args(args: Any) -> Tuple[str, Any]:
    """Parse the /forget grammar both surfaces share.

    No words (or ``show`` / ``list``) shows the forget
    book; ``entry <entry-id>`` shows one forget entry
    with its provenance whole; ``forgotten`` shows the
    entries standing forgotten; ``quarantined`` shows
    the memories still held apart; ``panel`` shows the
    forget panel derived from the whole book. Anything
    else is a usage error naming the grammar. Returns
    ``(action, value-or-None)``.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() in ("show", "list"):
        return ("show", None)
    words = text.split()
    head = words[0].lower()
    if head in ("forgotten", "quarantined", "panel") and len(words) == 1:
        return (head, None)
    if head == "entry" and len(words) == 2:
        try:
            return (head, normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
