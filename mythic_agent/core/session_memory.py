"""Session memory across days (All-Features roadmap slice M-153).

Part VII continues. The roadmap's words:
``resumable sessions carry their memory map, open
slices, and standing decisions; `--resume` restores
the *situation*, not just the transcript.``

What already shipped, and what this slice adds:

* The session store (``core/sessions.py``, M-010)
  already persists a session whole - its ordered
  transcript, its status, its token count - and
  ``SessionStore.resume`` / ``export`` already read
  it back. What resume restores today is the
  transcript: the messages, replayed. Nothing holds
  the *situation* around those messages as data -
  what the session had learned into the project's
  memory map, which roadmap slices stood open when
  the day ended, and which decisions stood as
  settled law for the next day.
* The memory map itself already ships as data
  (``core/project_memory_map.py``, M-150): entries
  in the closed sections (architecture, decision,
  gotcha, location), a panel derived in map order,
  kept by the Scribe. The roadmap itself ships as
  data (``core/roadmap_slices.py``, M-017): every
  slice's title, summary and ledger status, with
  the queued slices the open work.
* This slice is the situation those two maps and
  the session store compose into, as a pure layer:
  one resumable session's situation validated as
  data - the session it names (by the shipped
  store's own reference), the day it was saved, its
  stored status, the count of transcript messages
  it also held (counted, never carried - the
  situation is not the transcript), its carried
  memory-map facts (the shipped map's entries,
  composed BY IMPORT onto this layer's notes), its
  open slices (the shipped roadmap's queued
  slices, composed BY IMPORT), and its standing
  decisions (the map's decision entries, standing
  as decisions) - a panel DERIVED from the
  situation (every carried piece whole, in a
  settled order, so two panels of one situation
  diff cleanly), the shipped data file
  (``mythic_agent/data/session_memory.yaml``)
  holding one example book in exactly the shape a
  real book file takes, a loader for a book file
  anywhere on disk, a restore road that builds a
  situation from a shipped session export BY
  IMPORT (the store's own id and message
  validation, the map's entries, the roadmap's
  queued slices), records shaped as session news,
  and a small in-memory registry model. The agent
  layer owns holding situations for a session and
  restoring one from a stored session.

Honesty rules, enforced here and pinned by tests:

* **The situation, not the transcript.** A
  situation carries the memory map, the open
  slices and the standing decisions as structured
  data, and counts the transcript messages the
  session held - it never carries the messages
  themselves. Restoring a situation returns those
  pieces; it replays no conversation.
* **Composed, never duplicated.** Carried memory
  is the shipped project memory map's entries read
  onto this layer by import (their sections stay
  the map's closed set, judged by the map's own
  normaliser), open slices are the shipped
  roadmap's queued slices read by import, standing
  decisions are the map's decision entries
  standing as decisions, and a situation built
  from a session export is judged by the shipped
  store's own session-id and message validation.
  No second taxonomy, ledger or session format is
  invented here.
* **The panel is derived, never stored loose.**
  Its rows are the situation's pieces carried
  whole, in settled order (memory first, in map
  order; then open slices in roadmap order; then
  standing decisions by title), and its totals are
  the pieces' own counts; a stored panel or
  situation whose rows, totals, counts or account
  disagree with the derived shape refuses.
* **Data only - restoring changes no live
  session.** A situation here is validated data:
  no model is called, no session is attached,
  resumed or checkpointed, no live context is
  assembled, and nothing persists beyond the
  session journal news the agent layer publishes.
  The shipped roads are composed as data: an
  export is read, never written back.
* **Malformed refuses.** A duplicate situation id
  in one book, the same memory fact named twice in
  one section of one situation, a slice id that is
  no roadmap id, a saved-on day that is no ISO
  date, a status the shipped store does not know,
  and unknown keys in a note, a slice, a decision,
  a situation, a panel or a book mapping all raise
  instead of being skipped or guessed at.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from datetime import date
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
from .roadmap_slices import RoadmapSlice, load_roadmap
from .sessions import SessionStore, validate_messages, validate_session_id
from .validation import ValidationError

__all__ = [
    "PLAIN_EXPLANATION",
    "SESSION_MEMORY_RESOURCE",
    "SESSION_MEMORY_SCHEMA",
    "SESSION_MEMORY_SLICE",
    "OPEN_SLICE_STATES",
    "PANEL_KINDS",
    "SESSION_STATUSES",
    "USAGE",
    "CarriedMemory",
    "OpenSlice",
    "SessionMemoryBook",
    "SessionMemoryRegistry",
    "SessionSituation",
    "SituationKindCount",
    "SituationPanel",
    "SituationPanelRow",
    "StandingDecision",
    "book_record",
    "build_book",
    "build_decision",
    "build_note",
    "build_panel",
    "build_row",
    "build_situation",
    "build_slice",
    "decisions_from_memory_map",
    "derive_panel",
    "format_decisions",
    "format_memory",
    "format_panel",
    "format_session_memory_screen",
    "format_situation",
    "format_slices",
    "load_session_memory",
    "load_session_memory_file",
    "normalize_slice_state",
    "note_record",
    "notes_from_memory_map",
    "open_slices_from_roadmap",
    "panel_plain_words",
    "panel_record",
    "parse_session_memory_args",
    "plain_words",
    "situation_from_export",
    "situation_record",
    "validate_book",
    "validate_decision",
    "validate_note",
    "validate_panel",
    "validate_row",
    "validate_situation",
    "validate_slice",
]

SESSION_MEMORY_SLICE = "M-153"

#: The packaged data resource holding the example book.
SESSION_MEMORY_RESOURCE = "session_memory.yaml"

#: The schema word a session-memory file must carry.
SESSION_MEMORY_SCHEMA = "mythic.session_memory/1"

#: The states one open slice may stand in: named on
#: the roadmap's ledger as queued work, it stands
#: open, in progress, or blocked where it stands.
OPEN_SLICE_STATES = ("open", "in-progress", "blocked")

_SLICE_STATE_ALIASES = {
    "open": "open",
    "queued": "open",
    "in-progress": "in-progress",
    "in_progress": "in-progress",
    "in progress": "in-progress",
    "blocked": "blocked",
}

#: The kinds one panel row may carry, in panel
#: order: the memory map first, then the open
#: slices, then the standing decisions.
PANEL_KINDS = ("memory", "slice", "decision")

#: The session statuses the shipped store knows, in
#: the store's own order of business. Membership is
#: judged against ``SessionStore.STATUSES`` itself.
SESSION_STATUSES = (
    "idle", "running", "completed", "failed",
    "cancelled", "interrupted")

_SLICE_ID_RE = re.compile(r"^M-\d{3}$")

_NOTE_KEYS = frozenset({
    "note_id", "id", "section", "kind",
    "title", "name", "detail", "body",
    "source", "ref", "path", "reference",
})

_SLICE_KEYS = frozenset({
    "slice_id", "id", "title", "name",
    "state", "status", "note", "detail",
})

_DECISION_KEYS = frozenset({
    "decision_id", "id", "title", "name",
    "decision", "detail", "body", "source",
})

_SITUATION_KEYS = frozenset({
    "situation_id", "id", "session_ref", "session_id",
    "workspace", "title", "name", "saved_on", "day",
    "status", "transcript_messages", "transcript_count",
    "memory", "notes", "open_slices", "slices",
    "decisions", "total_memory", "total_slices",
    "total_decisions",
})

_ROW_KEYS = frozenset({
    "kind", "item_id", "id", "title", "detail",
})

_KIND_COUNT_KEYS = frozenset({"kind", "items", "count"})

_PANEL_KEYS = frozenset({
    "panel_id", "id", "rows", "pieces",
    "total_items", "total", "total_memory",
    "total_slices", "total_decisions",
    "kind_counts", "kinds", "account", "statements",
})

_BOOK_KEYS = frozenset({"title", "name"})

_SESSION_MEMORY_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "canon_note", "guide", "situations", "panels",
})

#: The shipped example book's title, held to this
#: by the loader's example check.
_EXAMPLE_TITLE = "Session memory across days at the M-152 slice boundary"

#: The shipped example's situation ids, in held
#: order, pinned by the loader.
_EXAMPLE_SITUATION_IDS = ("situation-m152-boundary",)

#: The shipped example situation's session
#: reference and saved-on day, pinned by the loader.
_EXAMPLE_SESSION_REF = "session-m152-graph-retrieval"

_EXAMPLE_SAVED_ON = "2026-11-08"

#: The shipped example's one panel id, and its rows
#: in panel order, pinned by the loader.
_EXAMPLE_PANEL_ID = "panel-m152-boundary"

_EXAMPLE_PANEL_ROW_IDS = (
    "note-connected-code", "note-reap-at-bank",
    "note-campaign-home", "M-153", "M-154",
    "decision-banking-order", "decision-no-docker")

_EXAMPLE_PANEL_ACCOUNT = (
    "The panel holds 7 carried pieces: memory 3, "
    "open slices 2, standing decisions 2.",
    "Pieces stand memory first (in map order), then "
    "open slices in roadmap order, then standing "
    "decisions by title - so two panels of one "
    "situation diff cleanly, line by line.",
    "Restoring a situation returns these pieces as "
    "structured data - the memory map, the open "
    "slices and the standing decisions - not a "
    "replay of the transcript.",
    "The panel is read off the situation at call "
    "time - it is derived, never stored loose.",
)

PLAIN_EXPLANATION = (
    "Session memory across days: a resumable "
    "session carries its situation - its memory "
    "map, its open slices, and its standing "
    "decisions - so --resume restores the situation, "
    "not just the transcript. A situation names one "
    "stored session (by the shipped store's own "
    "reference), the day it was saved, its stored "
    "status, and the count of transcript messages it "
    "also held - counted, never carried. Its memory "
    "is the shipped project memory map's entries "
    "composed by import, its open slices are the "
    "shipped roadmap's queued slices, and its "
    "standing decisions are the map's decision "
    "entries standing as decisions. The panel is "
    "derived from the situation at call time: every "
    "piece carried whole, memory first in map order, "
    "then open slices in roadmap order, then "
    "standing decisions by title. This layer holds "
    "situations as data only: it calls no model, "
    "attaches or resumes no live session, assembles "
    "no live context and persists nothing."
)

USAGE = (
    "Usage: /daymemory, /daymemory show, "
    "/daymemory situation <situation-id>, "
    "/daymemory memory, /daymemory slices, "
    "/daymemory decisions, /daymemory panel"
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
    text = _clean_text(value, "a memory note's reference")
    if len(text) > 300 or "\x00" in text:
        raise ValueError(
            f"a memory note's reference must be plain text "
            f"of at most 300 characters, got {len(text)} characters")
    if any(ch.isspace() for ch in text):
        raise ValueError(
            f"a memory note's reference names no spaces, "
            f"got {text!r}")
    return text


def _check_session_ref(value: Any) -> str:
    text = _clean_text(value, "a situation's session reference")
    if len(text) > 64 or "\x00" in text:
        raise ValueError(
            f"a situation's session reference must be plain "
            f"text of at most 64 characters, got {len(text)}")
    if any(ch.isspace() for ch in text):
        raise ValueError(
            f"a situation's session reference names no "
            f"spaces, got {text!r}")
    return text


def _check_workspace(value: Any) -> str:
    text = _clean_text(value, "a situation's workspace")
    if len(text) > 300 or "\x00" in text:
        raise ValueError(
            f"a situation's workspace must be plain text "
            f"of at most 300 characters, got {len(text)}")
    return text


def _check_saved_on(value: Any) -> str:
    text = _clean_text(value, "a situation's saved-on day")
    try:
        parsed = date.fromisoformat(text)
    except ValueError:
        raise ValueError(
            f"a situation's saved-on day must be an ISO "
            f"date (YYYY-MM-DD), got {text!r}") from None
    if parsed.isoformat() != text:
        raise ValueError(
            f"a situation's saved-on day must be an ISO "
            f"date (YYYY-MM-DD), got {text!r}")
    return text


def _check_status(value: Any) -> str:
    text = _clean_text(value, "a situation's session status")
    if text not in SessionStore.STATUSES:
        raise ValueError(
            "a situation's session status must be one of "
            "%s, got %r" % ("/".join(SESSION_STATUSES), text))
    return text


def _check_slice_id(value: Any) -> str:
    text = _clean_text(value, "an open slice's id")
    if not _SLICE_ID_RE.match(text):
        raise ValueError(
            f"an open slice's id must be a roadmap slice "
            f"id (M-NNN), got {text!r}")
    return text


def normalize_slice_state(value: Any) -> str:
    """The canonical open-slice state a word names.

    A state is one of :data:`OPEN_SLICE_STATES` -
    ``open``, ``in-progress`` or ``blocked`` - read
    case-insensitively, with the roadmap ledger's own
    word (``queued``) read onto ``open``. Anything
    else raises, plainly naming the three.
    """
    if isinstance(value, str):
        wanted = _SLICE_STATE_ALIASES.get(value.strip().lower())
        if wanted is not None:
            return wanted
    raise ValueError(
        "an open slice's state must be one of %s, got %r"
        % ("/".join(OPEN_SLICE_STATES), value))


# ---------------------------------------------------------------------
# The carried memory: one fact of the map, carried across days.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class CarriedMemory:
    """One fact of the project's memory map, carried in a situation.

    ``section`` is the fact's section in the shipped
    map's closed set (architecture, decision, gotcha,
    location), judged by the map's own normaliser;
    ``title`` names the fact; ``detail`` is the fact
    itself, in plain words; ``source`` names where it
    was read from; ``ref`` is where the thing it names
    lives. The record is the map's own entry shape,
    carried: :func:`notes_from_memory_map` reads the
    shipped entries onto it by import.
    """

    section: str
    title: str
    detail: str
    source: str
    ref: str
    note_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.note_id is not None:
            object.__setattr__(
                self, "note_id",
                normalize_member_id(self.note_id))
        object.__setattr__(
            self, "section", normalize_section(self.section))
        object.__setattr__(
            self, "title", _check_title(self.title, "a note's title"))
        object.__setattr__(
            self, "detail",
            _check_long_text(self.detail, "a note's detail"))
        object.__setattr__(
            self, "source",
            _check_title(self.source, "a note's source"))
        object.__setattr__(self, "ref", _check_ref(self.ref))

    @property
    def section_index(self) -> int:
        """This note's section's place in map order (derived)."""
        return MAP_SECTIONS.index(self.section)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "session_memory_note",
            "slice": SESSION_MEMORY_SLICE,
            "note_id": self.note_id,
            "section": self.section,
            "title": self.title,
            "detail": self.detail,
            "source": self.source,
            "ref": self.ref,
        }


def validate_note(note: Any) -> CarriedMemory:
    """Validate one carried-memory record into a CarriedMemory.

    Accepts a note, a shipped memory-map entry (whose
    fields are read onto the note - the map composed
    by import), or a mapping naming a ``section`` (or
    ``kind``), a ``title`` (or ``name``), a ``detail``
    (or ``body``), a ``source``, a ``ref`` (or ``path``
    / ``reference``) and an optional ``note_id`` (or
    ``id``). Naming two spellings of one field with
    different values refuses, and unknown keys refuse.
    """
    if isinstance(note, CarriedMemory):
        return note
    if isinstance(note, MemoryMapEntry):
        return CarriedMemory(
            section=note.section, title=note.title,
            detail=note.detail, source=note.source,
            ref=note.ref, note_id=note.entry_id)
    if not isinstance(note, dict):
        raise ValueError(
            f"a carried-memory record must be a mapping, "
            f"got {note!r}")
    unknown = set(note) - _NOTE_KEYS
    if unknown:
        raise ValueError(
            "unknown note keys: %s"
            % ", ".join(sorted(unknown)))
    section = _pick_any(note, ("section", "kind"), "sections")
    if section is None:
        raise ValueError("a note record is missing its section")
    title = _pick_any(note, ("title", "name"), "titles")
    if title is None:
        raise ValueError("a note record is missing its title")
    detail = _pick_any(note, ("detail", "body"), "details")
    if detail is None:
        raise ValueError("a note record is missing its detail")
    source = _pick_any(note, ("source",), "sources")
    if source is None:
        raise ValueError("a note record is missing its source")
    ref = _pick_any(note, ("ref", "path", "reference"), "references")
    if ref is None:
        raise ValueError("a note record is missing its reference")
    kwargs: Dict[str, Any] = {
        "section": section, "title": title, "detail": detail,
        "source": source, "ref": ref}
    note_id = _pick_any(note, ("note_id", "id"), "note ids")
    if note_id is not None:
        kwargs["note_id"] = note_id
    return CarriedMemory(**kwargs)


def build_note(note: Any = None, **kwargs: Any) -> CarriedMemory:
    """Build one validated note, from a mapping or field words."""
    if isinstance(note, (CarriedMemory, MemoryMapEntry)) and not kwargs:
        return validate_note(note)
    if isinstance(note, dict) or note is None:
        merged: Dict[str, Any] = {}
        if isinstance(note, dict):
            merged.update(note)
        merged.update(kwargs)
        return validate_note(merged)
    raise ValueError(
        f"a carried-memory record must be a mapping, got {note!r}")


def _check_note_ref(value: Any) -> CarriedMemory:
    if isinstance(value, (CarriedMemory, MemoryMapEntry)):
        return validate_note(value)
    if isinstance(value, dict):
        return validate_note(value)
    raise ValueError(f"a note record is needed, got {value!r}")


# ---------------------------------------------------------------------
# The open slice: one piece of roadmap work still standing open.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class OpenSlice:
    """One roadmap slice standing open when the day ended.

    ``slice_id`` is the shipped roadmap's own id
    (``M-NNN``); ``title`` is the roadmap's own title
    for it; ``state`` is where the work stands (open,
    in progress, or blocked); ``note`` says what the
    next day needs to know about it, in plain words.
    """

    slice_id: str
    title: str
    state: str
    note: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "slice_id", _check_slice_id(self.slice_id))
        object.__setattr__(
            self, "title", _check_title(self.title, "a slice's title"))
        object.__setattr__(
            self, "state", normalize_slice_state(self.state))
        object.__setattr__(
            self, "note",
            _check_long_text(self.note, "a slice's note"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "session_memory_open_slice",
            "slice": SESSION_MEMORY_SLICE,
            "slice_id": self.slice_id,
            "title": self.title,
            "state": self.state,
            "note": self.note,
        }


def validate_slice(slice_: Any) -> OpenSlice:
    """Validate one open-slice record into an OpenSlice.

    Accepts a slice, a shipped roadmap slice (whose id
    and title are read across, its ledger status read
    onto a state and its summary standing as the note
    - the roadmap composed by import), or a mapping
    naming a ``slice_id`` (or ``id``), a ``title`` (or
    ``name``), a ``state`` (or ``status``) and a
    ``note`` (or ``detail``). Naming two spellings of
    one field with different values refuses, and
    unknown keys refuse.
    """
    if isinstance(slice_, OpenSlice):
        return slice_
    if isinstance(slice_, RoadmapSlice):
        return OpenSlice(
            slice_id=slice_.id, title=slice_.title,
            state=normalize_slice_state(slice_.status),
            note=slice_.summary)
    if not isinstance(slice_, dict):
        raise ValueError(
            f"an open-slice record must be a mapping, "
            f"got {slice_!r}")
    unknown = set(slice_) - _SLICE_KEYS
    if unknown:
        raise ValueError(
            "unknown open-slice keys: %s"
            % ", ".join(sorted(unknown)))
    slice_id = _pick_any(slice_, ("slice_id", "id"), "slice ids")
    if slice_id is None:
        raise ValueError("an open-slice record is missing its slice id")
    title = _pick_any(slice_, ("title", "name"), "titles")
    if title is None:
        raise ValueError("an open-slice record is missing its title")
    state = _pick_any(slice_, ("state", "status"), "states")
    if state is None:
        raise ValueError("an open-slice record is missing its state")
    note = _pick_any(slice_, ("note", "detail"), "notes")
    if note is None:
        raise ValueError("an open-slice record is missing its note")
    return OpenSlice(
        slice_id=slice_id, title=title, state=state, note=note)


def build_slice(slice_: Any = None, **kwargs: Any) -> OpenSlice:
    """Build one validated open slice, from a mapping or field words."""
    if isinstance(slice_, (OpenSlice, RoadmapSlice)) and not kwargs:
        return validate_slice(slice_)
    if isinstance(slice_, dict) or slice_ is None:
        merged: Dict[str, Any] = {}
        if isinstance(slice_, dict):
            merged.update(slice_)
        merged.update(kwargs)
        return validate_slice(merged)
    raise ValueError(
        f"an open-slice record must be a mapping, got {slice_!r}")


def _check_slice_ref(value: Any) -> OpenSlice:
    if isinstance(value, (OpenSlice, RoadmapSlice)):
        return validate_slice(value)
    if isinstance(value, dict):
        return validate_slice(value)
    raise ValueError(f"an open-slice record is needed, got {value!r}")


# ---------------------------------------------------------------------
# The standing decision: one settled word the next day stands under.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class StandingDecision:
    """One decision standing as settled when the day ended.

    ``title`` names the decision; ``decision`` is the
    decision itself, in plain words; ``source`` names
    where it was settled. A standing decision is the
    memory map's decision entry standing as a
    decision: :func:`decisions_from_memory_map` reads
    the map's decision entries onto it by import.
    """

    title: str
    decision: str
    source: str
    decision_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.decision_id is not None:
            object.__setattr__(
                self, "decision_id",
                normalize_member_id(self.decision_id))
        object.__setattr__(
            self, "title",
            _check_title(self.title, "a decision's title"))
        object.__setattr__(
            self, "decision",
            _check_long_text(self.decision, "a decision's words"))
        object.__setattr__(
            self, "source",
            _check_title(self.source, "a decision's source"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "session_memory_decision",
            "slice": SESSION_MEMORY_SLICE,
            "decision_id": self.decision_id,
            "title": self.title,
            "decision": self.decision,
            "source": self.source,
        }


def validate_decision(decision: Any) -> StandingDecision:
    """Validate one standing-decision record into a StandingDecision.

    Accepts a decision, a shipped memory-map entry
    standing in the decision section (whose title,
    detail and source are read across - the map
    composed by import; an entry of any other section
    refuses, plainly), or a mapping naming a ``title``
    (or ``name``), a ``decision`` (or ``detail`` /
    ``body``), a ``source`` and an optional
    ``decision_id`` (or ``id``). Naming two spellings
    of one field with different values refuses, and
    unknown keys refuse.
    """
    if isinstance(decision, StandingDecision):
        return decision
    if isinstance(decision, MemoryMapEntry):
        if decision.section != "decision":
            raise ValueError(
                "only a memory map entry in the decision "
                "section stands as a standing decision, got "
                f"a {decision.section} entry")
        return StandingDecision(
            title=decision.title, decision=decision.detail,
            source=decision.source, decision_id=decision.entry_id)
    if not isinstance(decision, dict):
        raise ValueError(
            f"a standing-decision record must be a mapping, "
            f"got {decision!r}")
    unknown = set(decision) - _DECISION_KEYS
    if unknown:
        raise ValueError(
            "unknown decision keys: %s"
            % ", ".join(sorted(unknown)))
    title = _pick_any(decision, ("title", "name"), "titles")
    if title is None:
        raise ValueError("a decision record is missing its title")
    words = _pick_any(
        decision, ("decision", "detail", "body"), "decisions")
    if words is None:
        raise ValueError("a decision record is missing its decision")
    source = _pick_any(decision, ("source",), "sources")
    if source is None:
        raise ValueError("a decision record is missing its source")
    kwargs: Dict[str, Any] = {
        "title": title, "decision": words, "source": source}
    decision_id = _pick_any(
        decision, ("decision_id", "id"), "decision ids")
    if decision_id is not None:
        kwargs["decision_id"] = decision_id
    return StandingDecision(**kwargs)


def build_decision(decision: Any = None, **kwargs: Any) -> StandingDecision:
    """Build one validated decision, from a mapping or field words."""
    if isinstance(decision, (StandingDecision, MemoryMapEntry)) \
            and not kwargs:
        return validate_decision(decision)
    if isinstance(decision, dict) or decision is None:
        merged: Dict[str, Any] = {}
        if isinstance(decision, dict):
            merged.update(decision)
        merged.update(kwargs)
        return validate_decision(merged)
    raise ValueError(
        f"a standing-decision record must be a mapping, "
        f"got {decision!r}")


def _check_decision_ref(value: Any) -> StandingDecision:
    if isinstance(value, (StandingDecision, MemoryMapEntry)):
        return validate_decision(value)
    if isinstance(value, dict):
        return validate_decision(value)
    raise ValueError(f"a decision record is needed, got {value!r}")


# ---------------------------------------------------------------------
# The situation: one resumable session's whole standing, as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class SessionSituation:
    """One resumable session's situation, as a validated record.

    ``session_ref`` names the stored session this
    situation belongs to (the shipped store's own
    session id, or a session's standing name);
    ``workspace`` names where that session lives;
    ``title`` names the situation in plain words;
    ``saved_on`` is the day it was saved (an ISO
    date); ``status`` is the session's stored status,
    in the shipped store's own set;
    ``transcript_messages`` counts the transcript
    messages the session also held - counted, never
    carried, so the situation is never the transcript;
    ``memory`` are the carried memory-map facts, in
    held order; ``open_slices`` the roadmap work
    standing open, in held order; ``decisions`` the
    standing decisions, in held order. The totals are
    the pieces' own counts, judged at construction.
    """

    session_ref: str
    workspace: str
    title: str
    saved_on: str
    status: str
    transcript_messages: int
    memory: Tuple[CarriedMemory, ...] = ()
    open_slices: Tuple[OpenSlice, ...] = ()
    decisions: Tuple[StandingDecision, ...] = ()
    total_memory: Optional[int] = None
    total_slices: Optional[int] = None
    total_decisions: Optional[int] = None
    situation_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.situation_id is not None:
            object.__setattr__(
                self, "situation_id",
                normalize_member_id(self.situation_id))
        object.__setattr__(
            self, "session_ref", _check_session_ref(self.session_ref))
        object.__setattr__(
            self, "workspace", _check_workspace(self.workspace))
        object.__setattr__(
            self, "title", _check_title(self.title, "a situation's title"))
        object.__setattr__(
            self, "saved_on", _check_saved_on(self.saved_on))
        object.__setattr__(self, "status", _check_status(self.status))
        object.__setattr__(
            self, "transcript_messages",
            _check_count(
                self.transcript_messages,
                "a situation's transcript message count"))
        for field_name, checker, what in (
                ("memory", _check_note_ref, "memory notes"),
                ("open_slices", _check_slice_ref, "open slices"),
                ("decisions", _check_decision_ref, "standing decisions")):
            value = getattr(self, field_name)
            if isinstance(value, (str, bytes)) \
                    or not isinstance(value, (list, tuple)):
                raise ValueError(
                    f"a situation's {what} must be a list, "
                    f"got {value!r}")
            object.__setattr__(
                self, field_name, tuple(checker(v) for v in value))
        seen_notes = set()
        seen_facts = set()
        for note in self.memory:
            if note.note_id is not None:
                if note.note_id in seen_notes:
                    raise ValueError(
                        f"a memory note named {note.note_id!r} "
                        f"already exists")
                seen_notes.add(note.note_id)
            key = (note.section, note.title)
            if key in seen_facts:
                raise ValueError(
                    f"the fact {note.title!r} already stands "
                    f"in this situation in the {note.section} section")
            seen_facts.add(key)
        seen_slices = set()
        for slice_ in self.open_slices:
            if slice_.slice_id in seen_slices:
                raise ValueError(
                    f"an open slice named {slice_.slice_id!r} "
                    f"already exists")
            seen_slices.add(slice_.slice_id)
        seen_decisions = set()
        seen_titles = set()
        for decision in self.decisions:
            if decision.decision_id is not None:
                if decision.decision_id in seen_decisions:
                    raise ValueError(
                        f"a standing decision named "
                        f"{decision.decision_id!r} already exists")
                seen_decisions.add(decision.decision_id)
            if decision.title in seen_titles:
                raise ValueError(
                    f"the decision {decision.title!r} already "
                    f"stands in this situation")
            seen_titles.add(decision.title)
        for field_name, held, what in (
                ("total_memory", self.memory, "memory"),
                ("total_slices", self.open_slices, "open slices"),
                ("total_decisions", self.decisions, "decisions")):
            given = getattr(self, field_name)
            if given is None:
                object.__setattr__(self, field_name, len(held))
            else:
                checked = _check_count(given, f"a situation's total {what}")
                if checked != len(held):
                    raise ValueError(
                        f"a situation's total {what} must be its "
                        f"own pieces' count")
                object.__setattr__(self, field_name, checked)

    def note_for(self, note_id: Any) -> CarriedMemory:
        """The carried memory note one id names in this situation."""
        wanted = normalize_member_id(note_id)
        for note in self.memory:
            if note.note_id == wanted:
                return note
        raise KeyError(f"no memory note in the situation: {wanted!r}")

    def slice_for(self, slice_id: Any) -> OpenSlice:
        """The open slice one roadmap id names in this situation."""
        wanted = _check_slice_id(slice_id)
        for slice_ in self.open_slices:
            if slice_.slice_id == wanted:
                return slice_
        raise KeyError(f"no open slice in the situation: {wanted!r}")

    def decision_for(self, decision_id: Any) -> StandingDecision:
        """The standing decision one id names in this situation."""
        wanted = normalize_member_id(decision_id)
        for decision in self.decisions:
            if decision.decision_id == wanted:
                return decision
        raise KeyError(f"no standing decision in the situation: {wanted!r}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "session_memory_situation",
            "slice": SESSION_MEMORY_SLICE,
            "situation_id": self.situation_id,
            "session_ref": self.session_ref,
            "workspace": self.workspace,
            "title": self.title,
            "saved_on": self.saved_on,
            "status": self.status,
            "transcript_messages": self.transcript_messages,
            "total_memory": self.total_memory,
            "total_slices": self.total_slices,
            "total_decisions": self.total_decisions,
            "memory": [n.to_record() for n in self.memory],
            "open_slices": [s.to_record() for s in self.open_slices],
            "decisions": [d.to_record() for d in self.decisions],
        }


def validate_situation(situation: Any) -> SessionSituation:
    """Validate one situation record into a SessionSituation.

    Accepts a situation or a mapping naming a
    ``session_ref`` (or ``session_id``), a
    ``workspace``, a ``title`` (or ``name``), a
    ``saved_on`` (or ``day``), a ``status``, a
    ``transcript_messages`` (or ``transcript_count``),
    ``memory`` (or ``notes``), ``open_slices`` (or
    ``slices``), ``decisions``, the optional totals and
    an optional ``situation_id`` (or ``id``). Naming
    two spellings of one field with different values
    refuses, unknown keys refuse, and the totals are
    judged against the pieces themselves.
    """
    if isinstance(situation, SessionSituation):
        return situation
    if not isinstance(situation, dict):
        raise ValueError(
            f"a situation record must be a mapping, "
            f"got {situation!r}")
    unknown = set(situation) - _SITUATION_KEYS
    if unknown:
        raise ValueError(
            "unknown situation keys: %s"
            % ", ".join(sorted(unknown)))

    def _needed(spellings: Tuple[str, ...], what: str) -> Any:
        value = _pick_any(situation, spellings, what)
        if value is None:
            raise ValueError(f"a situation record is missing its {what}")
        return value

    kwargs: Dict[str, Any] = {
        "session_ref": _needed(
            ("session_ref", "session_id"), "session reference"),
        "workspace": _needed(("workspace",), "workspace"),
        "title": _needed(("title", "name"), "title"),
        "saved_on": _needed(("saved_on", "day"), "saved-on day"),
        "status": _needed(("status",), "status"),
        "transcript_messages": _needed(
            ("transcript_messages", "transcript_count"),
            "transcript message count"),
        "memory": _needed(("memory", "notes"), "memory"),
        "open_slices": _needed(
            ("open_slices", "slices"), "open slices"),
        "decisions": _needed(("decisions",), "decisions"),
    }
    for field_name, spellings in (
            ("total_memory", ("total_memory",)),
            ("total_slices", ("total_slices",)),
            ("total_decisions", ("total_decisions",)),
            ("situation_id", ("situation_id", "id"))):
        value = _pick_any(situation, spellings, field_name)
        if value is not None:
            kwargs[field_name] = value
    return SessionSituation(**kwargs)


def build_situation(situation: Any = None, **kwargs: Any) -> SessionSituation:
    """Build one validated situation, from a mapping or field words."""
    if isinstance(situation, SessionSituation) and not kwargs:
        return situation
    if isinstance(situation, dict) or situation is None:
        merged: Dict[str, Any] = {}
        if isinstance(situation, dict):
            merged.update(situation)
        merged.update(kwargs)
        return validate_situation(merged)
    raise ValueError(
        f"a situation record must be a mapping, got {situation!r}")


def _check_situation_ref(value: Any) -> SessionSituation:
    if isinstance(value, SessionSituation):
        return value
    if isinstance(value, dict):
        return validate_situation(value)
    raise ValueError(f"a situation record is needed, got {value!r}")


def _held_situations(source: Any) -> Tuple[SessionSituation, ...]:
    """The situations one source holds, in held order."""
    if isinstance(source, SessionMemoryBook):
        return source.situations
    if isinstance(source, SessionMemoryRegistry):
        return source.list_situations()
    if isinstance(source, SessionSituation):
        return (source,)
    if isinstance(source, (list, tuple)):
        return tuple(_check_situation_ref(s) for s in source)
    raise ValueError(f"situations are needed, got {source!r}")


# ---------------------------------------------------------------------
# The panel: the whole situation accounted for, in settled order, derived.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class SituationPanelRow:
    """One carried piece carried whole into the panel.

    ``kind`` is the piece's kind in panel order
    (memory, slice, decision); ``item_id`` names the
    piece (a note id, a roadmap slice id, or a
    decision id); ``title`` and ``detail`` are the
    piece's own words - for a slice, its note on the
    work; for a decision, the decision itself.
    :func:`validate_row` judged against its piece
    refuses a row whose fields disagree with the row
    that piece derives.
    """

    kind: str
    item_id: str
    title: str
    detail: str

    def __post_init__(self) -> None:
        kind = _clean_text(self.kind, "a row's kind")
        if kind not in PANEL_KINDS:
            raise ValueError(
                "a panel row's kind must be one of %s, got %r"
                % ("/".join(PANEL_KINDS), kind))
        object.__setattr__(self, "kind", kind)
        if kind == "slice":
            object.__setattr__(
                self, "item_id", _check_slice_id(self.item_id))
        else:
            object.__setattr__(
                self, "item_id", normalize_member_id(self.item_id))
        object.__setattr__(
            self, "title", _check_title(self.title, "a row's title"))
        object.__setattr__(
            self, "detail",
            _check_long_text(self.detail, "a row's detail"))

    @property
    def sort_key(self) -> Tuple[int, Any]:
        """This row's place in panel order (derived).

        Rows stand kind first (memory, then slices,
        then decisions, in :data:`PANEL_KINDS` order);
        the within-kind place is judged against the
        situation by :func:`derive_panel` itself, which
        builds the rows in settled order.
        """
        return (PANEL_KINDS.index(self.kind), self.item_id)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "session_memory_row",
            "slice": SESSION_MEMORY_SLICE,
            "kind": self.kind,
            "item_id": self.item_id,
            "title": self.title,
            "detail": self.detail,
        }


def _row_for_note(note: CarriedMemory) -> SituationPanelRow:
    if note.note_id is None:
        raise ValueError(
            "a panel row needs its memory note to carry an id")
    return SituationPanelRow(
        kind="memory", item_id=note.note_id,
        title=note.title, detail=note.detail)


def _row_for_slice(slice_: OpenSlice) -> SituationPanelRow:
    return SituationPanelRow(
        kind="slice", item_id=slice_.slice_id,
        title=slice_.title, detail=slice_.note)


def _row_for_decision(decision: StandingDecision) -> SituationPanelRow:
    if decision.decision_id is None:
        raise ValueError(
            "a panel row needs its standing decision to carry an id")
    return SituationPanelRow(
        kind="decision", item_id=decision.decision_id,
        title=decision.title, detail=decision.decision)


def _derive_row(piece: Any) -> SituationPanelRow:
    if isinstance(piece, CarriedMemory):
        return _row_for_note(piece)
    if isinstance(piece, OpenSlice):
        return _row_for_slice(piece)
    if isinstance(piece, StandingDecision):
        return _row_for_decision(piece)
    raise ValueError(f"a carried piece is needed, got {piece!r}")


def _check_row_ref(value: Any) -> SituationPanelRow:
    if isinstance(value, SituationPanelRow):
        return value
    if isinstance(value, (CarriedMemory, OpenSlice, StandingDecision)):
        return _derive_row(value)
    if isinstance(value, dict):
        unknown = set(value) - _ROW_KEYS
        if unknown:
            raise ValueError(
                "unknown row keys: %s" % ", ".join(sorted(unknown)))
        kind = _pick_any(value, ("kind",), "kinds")
        if kind is None:
            raise ValueError("a row is missing its kind")
        item_id = _pick_any(value, ("item_id", "id"), "item ids")
        if item_id is None:
            raise ValueError("a row is missing its item id")
        title = _pick_any(value, ("title",), "titles")
        if title is None:
            raise ValueError("a row is missing its title")
        detail = _pick_any(value, ("detail",), "details")
        if detail is None:
            raise ValueError("a row is missing its detail")
        return SituationPanelRow(
            kind=kind, item_id=item_id, title=title, detail=detail)
    raise ValueError(f"a panel row is needed, got {value!r}")


def validate_row(row: Any, piece: Any = None) -> SituationPanelRow:
    """Validate one panel row into a SituationPanelRow.

    Accepts a row, a carried piece (whose derived row
    is the row), or a mapping naming a ``kind``, an
    ``item_id`` (or ``id``), a ``title`` and a
    ``detail``. With *piece* given, the row is judged
    against the row derived from that piece: a stored
    row whose fields disagree with the derived row
    refuses.
    """
    current = _check_row_ref(row)
    if piece is not None:
        derived = _derive_row(piece)
        if current != derived:
            raise ValueError(
                "a stored row disagrees with the row "
                "derived from its piece")
    return current


def build_row(row: Any = None, piece: Any = None,
              **kwargs: Any) -> SituationPanelRow:
    """Build one validated row, from a mapping or field words."""
    if isinstance(row, SituationPanelRow) and not kwargs:
        return validate_row(row, piece)
    if isinstance(row, dict) or row is None:
        merged: Dict[str, Any] = {}
        if isinstance(row, dict):
            merged.update(row)
        merged.update(kwargs)
        return validate_row(merged, piece)
    return validate_row(row, piece)


@dataclass(frozen=True)
class SituationKindCount:
    """One kind's count in a panel: its pieces tallied."""

    kind: str
    items: int

    def __post_init__(self) -> None:
        kind = _clean_text(self.kind, "a kind count's kind")
        if kind not in PANEL_KINDS:
            raise ValueError(
                "a kind count's kind must be one of %s, got %r"
                % ("/".join(PANEL_KINDS), kind))
        object.__setattr__(self, "kind", kind)
        object.__setattr__(
            self, "items",
            _check_count(self.items, "a kind count's items"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "items": self.items,
        }


def _check_kind_count_ref(value: Any) -> SituationKindCount:
    if isinstance(value, SituationKindCount):
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
            raise ValueError("a kind count is missing its items")
        return SituationKindCount(kind=kind, items=items)
    raise ValueError(f"a kind count is needed, got {value!r}")


def _panel_account(total_items: int, total_memory: int,
                   total_slices: int,
                   total_decisions: int) -> Tuple[str, ...]:
    return (
        f"The panel holds {total_items} carried pieces: "
        f"memory {total_memory}, open slices {total_slices}, "
        f"standing decisions {total_decisions}.",
        "Pieces stand memory first (in map order), then "
        "open slices in roadmap order, then standing "
        "decisions by title - so two panels of one "
        "situation diff cleanly, line by line.",
        "Restoring a situation returns these pieces as "
        "structured data - the memory map, the open "
        "slices and the standing decisions - not a "
        "replay of the transcript.",
        "The panel is read off the situation at call "
        "time - it is derived, never stored loose.",
    )


@dataclass(frozen=True)
class SituationPanel:
    """The panel of one situation, derived from the whole situation.

    ``rows`` are the situation's pieces carried whole,
    in panel order (memory first, in map order - section
    first, then title; then open slices in roadmap
    order; then standing decisions by title, so two
    panels of one situation diff cleanly);
    ``total_items`` is the piece count and the three
    kind totals are the rows' own counts;
    ``kind_counts`` are the per-kind tallies in the
    order their kinds first appear in the panel;
    ``account`` is read off those numbers. A panel
    whose rows stand out of panel order, or whose
    totals are not its own rows' counts, refuses at
    construction; :func:`validate_panel` judged
    against a situation refuses a stored panel that
    disagrees with the derived one.
    """

    rows: Tuple[SituationPanelRow, ...] = ()
    total_items: int = 0
    total_memory: int = 0
    total_slices: int = 0
    total_decisions: int = 0
    kind_counts: Tuple[SituationKindCount, ...] = ()
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
            key = (row.kind, row.item_id)
            if key in seen:
                raise ValueError(
                    f"a panel row named {row.item_id!r} "
                    f"already exists")
            seen.add(key)
        kinds = [PANEL_KINDS.index(row.kind) for row in rows]
        if kinds != sorted(kinds):
            raise ValueError(
                "a panel's rows must stand in panel order "
                "(memory, then slices, then decisions)")
        object.__setattr__(self, "rows", rows)
        for field_name, kind, what in (
                ("total_memory", "memory", "memory total"),
                ("total_slices", "slice", "open-slice total"),
                ("total_decisions", "decision", "decision total")):
            checked = _check_count(
                getattr(self, field_name), f"a panel's {what}")
            if checked != sum(1 for r in rows if r.kind == kind):
                raise ValueError(
                    f"a panel's {what} must be its own rows' count")
            object.__setattr__(self, field_name, checked)
        object.__setattr__(
            self, "total_items",
            _check_count(self.total_items, "a panel's total"))
        if self.total_items != len(rows):
            raise ValueError(
                "a panel's total must be its own rows' count")
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
        if sum(c.items for c in kind_counts) != self.total_items:
            raise ValueError(
                "a panel's kind counts must sum to its own total")
        for count in kind_counts:
            if count.items != sum(
                    1 for r in rows if r.kind == count.kind):
                raise ValueError(
                    "a panel's kind counts must be its own "
                    "rows' counts")
        object.__setattr__(self, "account", _check_account(self.account))

    def row_for(self, item_id: Any) -> SituationPanelRow:
        """The panel row one item id names in this panel."""
        for row in self.rows:
            if row.item_id == item_id:
                return row
        raise KeyError(f"no row in the panel: item {item_id!r}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "session_memory_panel",
            "slice": SESSION_MEMORY_SLICE,
            "panel_id": self.panel_id,
            "rows": [row.to_record() for row in self.rows],
            "total_items": self.total_items,
            "total_memory": self.total_memory,
            "total_slices": self.total_slices,
            "total_decisions": self.total_decisions,
            "kind_counts": [c.to_record() for c in self.kind_counts],
            "account": list(self.account),
        }


def derive_panel(source: Any) -> SituationPanel:
    """Derive the panel from one situation.

    The rows are the situation's pieces carried whole,
    in panel order: memory notes first, in map order
    (section first, in the shipped map's section
    order, then title), then open slices in roadmap
    order (slice id ascending), then standing
    decisions by title. *source* is a situation, a
    book (whose latest situation is derived), a
    registry (whose latest held situation is derived)
    or the situations themselves (whose last is
    derived). A source holding no situation refuses -
    a panel of nothing is no panel. A carried piece
    with no id refuses too: a panel row must name its
    piece.
    """
    situations = _held_situations(source)
    if not situations:
        raise ValueError("a panel needs at least one situation")
    situation = situations[-1]
    memory_rows = [
        _row_for_note(note) for note in sorted(
            situation.memory,
            key=lambda n: (n.section_index, n.title))]
    slice_rows = [
        _row_for_slice(slice_) for slice_ in sorted(
            situation.open_slices, key=lambda s: s.slice_id)]
    decision_rows = [
        _row_for_decision(decision) for decision in sorted(
            situation.decisions, key=lambda d: d.title)]
    rows = tuple(memory_rows + slice_rows + decision_rows)
    if not rows:
        raise ValueError(
            "a panel needs at least one carried piece")
    order: list = []
    tally: Dict[str, int] = {}
    for row in rows:
        if row.kind not in tally:
            tally[row.kind] = 0
            order.append(row.kind)
        tally[row.kind] += 1
    kind_counts = tuple(
        SituationKindCount(kind=kind, items=tally[kind])
        for kind in order)
    return SituationPanel(
        rows=rows,
        total_items=len(rows),
        total_memory=len(memory_rows),
        total_slices=len(slice_rows),
        total_decisions=len(decision_rows),
        kind_counts=kind_counts,
        account=_panel_account(
            len(rows), len(memory_rows),
            len(slice_rows), len(decision_rows)))


def validate_panel(panel: Any, source: Any = None) -> SituationPanel:
    """Validate one panel into a SituationPanel.

    Accepts a panel or a mapping naming ``rows`` (or
    ``pieces``), a ``total_items`` (or ``total``), the
    three kind totals, ``kind_counts`` (or ``kinds``),
    an ``account`` (or ``statements``) and an optional
    ``panel_id`` (or ``id``). With *source* given (a
    situation), the panel is judged against the panel
    derived from that situation: a stored panel whose
    rows, totals, kind counts or account disagree with
    the derived panel refuses. A panel naming no
    account refuses too.
    """
    if isinstance(panel, SituationPanel):
        current = panel
    elif isinstance(panel, dict):
        unknown = set(panel) - _PANEL_KEYS
        if unknown:
            raise ValueError(
                "unknown panel keys: %s" % ", ".join(sorted(unknown)))
        rows = _pick_any(panel, ("rows", "pieces"), "rows")
        if rows is None:
            raise ValueError("a panel is missing its rows")
        total = _pick_any(
            panel, ("total_items", "total"), "totals")
        if total is None:
            raise ValueError("a panel is missing its total items")
        kind_counts = _pick_any(
            panel, ("kind_counts", "kinds"), "kind counts")
        if kind_counts is None:
            raise ValueError("a panel is missing its kind counts")
        account = _pick_any(panel, ("account", "statements"), "accounts")
        if account is None:
            raise ValueError("a panel names no account of its own")
        kwargs: Dict[str, Any] = {
            "rows": rows, "total_items": total,
            "kind_counts": kind_counts, "account": account}
        for field_name in (
                "total_memory", "total_slices", "total_decisions"):
            value = _pick_any(panel, (field_name,), field_name)
            if value is None:
                raise ValueError(f"a panel is missing its {field_name}")
            kwargs[field_name] = value
        panel_id = _pick_any(panel, ("panel_id", "id"), "panel ids")
        if panel_id is not None:
            kwargs["panel_id"] = panel_id
        current = SituationPanel(**kwargs)
    else:
        raise ValueError(f"a panel must be a mapping, got {panel!r}")
    if source is not None:
        derived = derive_panel(source)
        if (current.rows != derived.rows
                or current.total_items != derived.total_items
                or current.total_memory != derived.total_memory
                or current.total_slices != derived.total_slices
                or current.total_decisions != derived.total_decisions
                or current.kind_counts != derived.kind_counts
                or current.account != derived.account):
            raise ValueError(
                "a stored panel disagrees with the panel "
                "derived from its situation")
    return current


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> SituationPanel:
    """Build one validated panel, from a mapping or field words."""
    if isinstance(panel, SituationPanel) and not kwargs:
        return validate_panel(panel, source)
    if isinstance(panel, dict) or panel is None:
        merged: Dict[str, Any] = {}
        if isinstance(panel, dict):
            merged.update(panel)
        merged.update(kwargs)
        return validate_panel(merged, source)
    return validate_panel(panel, source)


# ---------------------------------------------------------------------
# The composition roads: the shipped map, roadmap and store, by import.
# ---------------------------------------------------------------------


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


def notes_from_memory_map(source: Any) -> Tuple[CarriedMemory, ...]:
    """Carried memory read off the shipped project memory map.

    Every entry of the shipped map - a book, a
    registry, the entries themselves, or one entry -
    is read onto a carried note BY IMPORT, judged by
    the map's own validation on the way: its section
    (the map's closed set), its title, its detail, its
    source and its reference stand exactly as the map
    holds them. Nothing here re-names a section or
    re-words a fact.
    """
    return tuple(validate_note(e) for e in _map_entries(source))


def decisions_from_memory_map(source: Any) -> Tuple[StandingDecision, ...]:
    """Standing decisions read off the shipped project memory map.

    The map's entries standing in its decision section
    - and only those - are read onto standing
    decisions BY IMPORT: the entry's title names the
    decision, its detail stands as the decision
    itself, and its source stands as where it was
    settled. Entries of other sections are the map's
    other facts, never silently promoted to law.
    """
    return tuple(
        validate_decision(e) for e in _map_entries(source)
        if e.section == "decision")


def open_slices_from_roadmap(roadmap: Any = None, *,
                             limit: Any = None) -> Tuple[OpenSlice, ...]:
    """Open slices read off the shipped roadmap, by import.

    The roadmap's queued slices - the work the ledger
    still holds open - are read onto open slices BY
    IMPORT through :func:`load_roadmap` (or off a
    roadmap already loaded): each slice's own id and
    title, its queued status read onto the open state,
    and its summary standing as the note. With *limit*
    given, only the first *limit* open slices in road
    order are read - the next work the campaign faces.
    """
    if limit is not None:
        limit = _check_count(limit, "an open-slice limit")
        if limit < 1:
            raise ValueError("an open-slice limit must be at least one")
    road = roadmap if roadmap is not None else load_roadmap()
    queued = tuple(
        s for s in road.slices if s.status == "queued")
    if limit is not None:
        queued = queued[:limit]
    return tuple(validate_slice(s) for s in queued)


def situation_from_export(export: Any, *, memory: Any = (),
                          open_slices: Any = (), decisions: Any = (),
                          title: Any = None, saved_on: Any = None,
                          situation_id: Any = None) -> SessionSituation:
    """Build one situation from a shipped session export, by import.

    *export* is a session record in the shipped
    store's export shape (``SessionStore.export``):
    its ``id`` is judged by the store's own
    :func:`validate_session_id`, its ``context`` by
    the store's own :func:`validate_messages`, and
    its ``workspace`` and ``status`` stand as the
    situation's own. The transcript itself is never
    carried: only its message count stands in the
    situation. *memory*, *open_slices* and *decisions*
    are the carried pieces, each read through this
    layer's own composition (map entries onto notes
    and decisions, roadmap slices onto open slices,
    or this layer's records as they stand). *saved_on*
    defaults to the export's own ``updated_at`` day;
    *title* defaults to a plain naming of the session.
    The export is read, never written back: building
    a situation checkpoints nothing and resumes no
    live session.
    """
    if not isinstance(export, dict):
        raise ValueError(
            f"a session export must be a mapping, got {export!r}")
    session_id = export.get("id")
    if session_id is None:
        raise ValueError("a session export is missing its session id")
    session_ref = validate_session_id(session_id)
    context = export.get("context")
    if context is None:
        raise ValueError("a session export is missing its context")
    validate_messages(context)
    workspace = export.get("workspace")
    if workspace is None:
        raise ValueError("a session export is missing its workspace")
    status = export.get("status")
    if status is None:
        raise ValueError("a session export is missing its status")
    if saved_on is None:
        updated = export.get("updated_at")
        if not isinstance(updated, str) or len(updated) < 10:
            raise ValueError(
                "a situation built from an export needs its "
                "saved-on day, or an export carrying one")
        saved_on = updated[:10]
    if title is None:
        title = f"Session {session_ref[:8]} situation"
    notes = tuple(_check_note_ref(n) for n in memory)
    slices = tuple(_check_slice_ref(s) for s in open_slices)
    standing = tuple(_check_decision_ref(d) for d in decisions)
    kwargs: Dict[str, Any] = {
        "session_ref": session_ref,
        "workspace": workspace,
        "title": title,
        "saved_on": saved_on,
        "status": status,
        "transcript_messages": len(context),
        "memory": notes,
        "open_slices": slices,
        "decisions": standing,
    }
    if situation_id is not None:
        kwargs["situation_id"] = situation_id
    return SessionSituation(**kwargs)


# ---------------------------------------------------------------------
# The book: situations in held order, panels judged.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class SessionMemoryBook:
    """One session-memory book: its situations, in held order.

    ``situations`` are the situation records, in held
    order; ``panels`` are the book's derivations -
    panels of the book's situations, each judged
    against a situation of the book by
    :func:`validate_book`; ``canon_note`` is the
    book's own note. This book is the book file's
    shape: the shipped example is one book, and a
    real book file is a new file in this shape.
    """

    title: str = ""
    situations: Tuple[SessionSituation, ...] = ()
    panels: Tuple[SituationPanel, ...] = ()
    canon_note: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_title(self.title, "a book's title"))
        if isinstance(self.situations, (str, bytes)) \
                or not isinstance(self.situations, (list, tuple)):
            raise ValueError(
                f"a book's situations must be a list of "
                f"situation records, got {self.situations!r}")
        situations = tuple(
            _check_situation_ref(s) for s in self.situations)
        if not situations:
            raise ValueError(
                "a session-memory book holds at least one situation")
        seen_ids = set()
        for situation in situations:
            if situation.situation_id is not None:
                if situation.situation_id in seen_ids:
                    raise ValueError(
                        f"a situation named "
                        f"{situation.situation_id!r} already exists")
                seen_ids.add(situation.situation_id)
        object.__setattr__(self, "situations", situations)
        if isinstance(self.panels, (str, bytes)) \
                or not isinstance(self.panels, (list, tuple)):
            raise ValueError(
                f"a book's panels must be a list of panels, "
                f"got {self.panels!r}")
        panels = tuple(
            p if isinstance(p, SituationPanel) else validate_panel(p)
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

    def situation_for(self, situation_id: Any) -> SessionSituation:
        """The situation one id names in this book."""
        wanted = normalize_member_id(situation_id)
        for situation in self.situations:
            if situation.situation_id == wanted:
                return situation
        raise KeyError(f"no situation in the book: {wanted!r}")

    def panel_for(self, panel_id: Any) -> SituationPanel:
        """The stored panel one id names in this book."""
        wanted = normalize_member_id(panel_id)
        for panel in self.panels:
            if panel.panel_id == wanted:
                return panel
        raise KeyError(f"no panel in the book: {wanted!r}")

    def situation_ids(self) -> Tuple[str, ...]:
        """Every held situation id, in held order."""
        return tuple(
            s.situation_id for s in self.situations if s.situation_id)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "session_memory_book",
            "slice": SESSION_MEMORY_SLICE,
            "title": self.title,
            "situation_ids": list(self.situation_ids()),
            "situation_count": len(self.situations),
            "panel_count": len(self.panels),
        }


def validate_book(data: Any, *, require_example: bool = False
                  ) -> SessionMemoryBook:
    """Validate one session-memory mapping into a book.

    The mapping names a ``schema`` (the session-memory
    schema word), a ``guide`` mapping (its ``title``),
    a ``situations`` list and an optional ``panels``
    list. Every record stands on its own validation,
    then the whole is judged: situation ids unique,
    and every stored panel judged against a situation
    of the book (a panel no situation of the book
    derives refuses). With ``require_example`` the
    shipped example is held to its pinned shape: the
    pinned title, situations and panel, and the
    panel's pinned rows and account word-for-word.
    Problems raise :class:`ValidationError` or
    ``ValueError``.
    """
    if isinstance(data, SessionMemoryBook):
        return data
    if not isinstance(data, dict):
        raise ValidationError(
            f"a session memory book must be a mapping, got {data!r}")
    unknown = set(data) - _SESSION_MEMORY_KEYS
    if unknown:
        raise ValidationError(
            "unknown session-memory keys: %s"
            % ", ".join(sorted(unknown)))
    if data.get("schema") != SESSION_MEMORY_SCHEMA:
        raise ValidationError(
            f"a session memory book must carry schema "
            f"{SESSION_MEMORY_SCHEMA!r}, got {data.get('schema')!r}")
    situations = _pick_any(data, ("situations",), "situations")
    if situations is None:
        raise ValidationError("a session memory book is missing its situations")
    if not isinstance(situations, (list, tuple)):
        raise ValidationError("a session memory book's situations must be a list")
    if data.get("panels") is not None \
            and not isinstance(data["panels"], (list, tuple)):
        raise ValidationError("a session memory book's panels must be a list")
    head = data.get("guide") or {}
    if not isinstance(head, dict):
        raise ValidationError("a session memory book's guide must be a mapping")
    unknown_head = set(head) - _BOOK_KEYS
    if unknown_head:
        raise ValidationError(
            "unknown guide keys: %s" % ", ".join(sorted(unknown_head)))
    try:
        title = _pick_any(head, ("title", "name"), "titles")
        if title is None:
            raise ValidationError("a session memory book is missing its title")
        note = data.get("canon_note") or ""
        if not isinstance(note, str):
            raise ValidationError("a session memory book's note must be text")
        book = SessionMemoryBook(
            title=title, situations=tuple(situations),
            panels=tuple(data.get("panels") or ()),
            canon_note=note)
        for panel in book.panels:
            judged = False
            for situation in book.situations:
                try:
                    validate_panel(panel, situation)
                    judged = True
                    break
                except ValueError:
                    continue
            if not judged:
                raise ValidationError(
                    "a stored panel disagrees with every "
                    "situation in its book")
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    if require_example:
        if book.title != _EXAMPLE_TITLE:
            raise ValidationError(
                "the shipped example session memory book's title "
                "is not the pinned title")
        if book.situation_ids() != _EXAMPLE_SITUATION_IDS:
            raise ValidationError(
                "the shipped example's situations are not "
                "the pinned records")
        panel = book.panel_for(_EXAMPLE_PANEL_ID)
        if tuple(r.item_id for r in panel.rows) != _EXAMPLE_PANEL_ROW_IDS:
            raise ValidationError(
                "the shipped example panel does not name "
                "its pinned rows in panel order")
        if panel.account != _EXAMPLE_PANEL_ACCOUNT:
            raise ValidationError(
                "the shipped example panel does not carry "
                "its pinned account word-for-word")
        first = book.situations[0]
        if first.session_ref != _EXAMPLE_SESSION_REF \
                or first.saved_on != _EXAMPLE_SAVED_ON:
            raise ValidationError(
                "the shipped example's first situation is not "
                "its pinned session at its pinned day")
    return book


def build_book(book: Any = None, **kwargs: Any) -> SessionMemoryBook:
    """Build one validated book, from a mapping or field words."""
    if isinstance(book, SessionMemoryBook) and not kwargs:
        return book
    if isinstance(book, dict):
        if "schema" in book:
            return validate_book(book)
        merged: Dict[str, Any] = dict(book)
        merged.update(kwargs)
        return SessionMemoryBook(**merged)
    if book is None:
        return SessionMemoryBook(**kwargs)
    raise ValueError(f"a session memory book is needed, got {book!r}")


def _book_from(data: Any, *, require_example: bool) -> SessionMemoryBook:
    try:
        return validate_book(data, require_example=require_example)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def load_session_memory(
        data: Optional[Dict[str, Any]] = None) -> SessionMemoryBook:
    """Load and validate the shipped example book (or *data*).

    The shipped file is held to the example check:
    the pinned title, situation records and panel -
    the M-152 slice boundary book - so the shipped
    book covers the canon this slice exists to hold.
    """
    raw = data if data is not None else load_resource(SESSION_MEMORY_RESOURCE)
    return _book_from(raw, require_example=True)


def load_session_memory_file(path: Any) -> SessionMemoryBook:
    """Load and validate a session-memory book from a file at *path*.

    Any file in the session-memory shape, anywhere
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
# The registry model: one book held situation by situation, in held order.
# ---------------------------------------------------------------------


class SessionMemoryRegistry:
    """One session's situations, held situation by situation.

    The registry holds situation records, never panels:
    the panel is a derivation, read off the latest held
    situation at call time, so nothing here can hold a
    figure stale.
    """

    def __init__(self, book: Any = None) -> None:
        self._title: Optional[str] = None
        self._situations: Dict[str, SessionSituation] = {}
        self._order: list = []
        self._next_situation = 1
        if book is not None:
            self.register_book(book)

    def _fresh_situation_id(self, held_ids: Any) -> str:
        while f"situation-{self._next_situation}" in held_ids:
            self._next_situation += 1
        fresh = f"situation-{self._next_situation}"
        self._next_situation += 1
        return fresh

    def register_situation(self, situation: Any) -> SessionSituation:
        """Register one situation into the held book.

        A record with no id is given a deterministic
        ``situation-N`` id. A record id already standing
        here refuses.
        """
        validated = _check_situation_ref(situation)
        held_ids = set(self._situations)
        if validated.situation_id is not None \
                and validated.situation_id in held_ids:
            raise ValueError(
                f"a situation named "
                f"{validated.situation_id!r} already exists")
        if validated.situation_id is None:
            validated = replace(
                validated,
                situation_id=self._fresh_situation_id(held_ids))
        self._situations[validated.situation_id] = validated
        self._order.append(validated.situation_id)
        return validated

    def register_book(self, book: Any) -> SessionMemoryBook:
        """Register every situation of one book, in order.

        The first book held sets the title; a later
        book under a different title refuses, as does
        a book naming a held situation id. The book's
        panels are derivations, not holdings, and are
        not held.
        """
        validated = build_book(book)
        if self._title is not None and validated.title != self._title:
            raise ValueError(
                "this registry already holds a session "
                "memory book under a different title")
        for situation in validated.situations:
            if situation.situation_id in self._situations:
                raise ValueError(
                    f"a situation named "
                    f"{situation.situation_id!r} already exists")
        self._title = validated.title
        for situation in validated.situations:
            self.register_situation(situation)
        return self.book()

    def get_situation(self, situation_id: Any) -> SessionSituation:
        """The situation one id names among the held records."""
        wanted = normalize_member_id(situation_id)
        if wanted not in self._situations:
            raise KeyError(f"unknown situation: {wanted!r}")
        return self._situations[wanted]

    def latest_situation(self) -> SessionSituation:
        """The most recently held situation."""
        if not self._order:
            raise ValueError("no situation is held yet")
        return self._situations[self._order[-1]]

    def list_situations(self) -> Tuple[SessionSituation, ...]:
        """Every held situation, in the order they were held."""
        return tuple(self._situations[s] for s in self._order)

    def book(self) -> SessionMemoryBook:
        """The held situations as one validated book."""
        if self._title is None:
            raise ValueError("no session memory book is held yet")
        return SessionMemoryBook(
            title=self._title, situations=self.list_situations())

    def panel(self) -> SituationPanel:
        """Derive the panel of the latest held situation."""
        return derive_panel(self)


# ---------------------------------------------------------------------
# Situation news, shaped as session records.
# ---------------------------------------------------------------------


def note_record(note: Any) -> Dict[str, Any]:
    """The session-news record of one carried memory note."""
    current = note if isinstance(note, CarriedMemory) \
        else build_note(note)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"{current.title} ({current.section}) stands in the "
        f"session's memory at {current.ref}: "
        f"{current.detail}")
    return record


def situation_record(situation: Any) -> Dict[str, Any]:
    """The session-news record of one situation."""
    current = situation if isinstance(situation, SessionSituation) \
        else build_situation(situation)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Session situation {current.title}: "
        f"{current.total_memory} memory fact(s), "
        f"{current.total_slices} open slice(s) and "
        f"{current.total_decisions} standing decision(s) "
        f"carried from {current.saved_on} - the situation, "
        f"not the {current.transcript_messages}-message "
        f"transcript.")
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
        f"Session memory panel: {current.total_items} "
        f"carried pieces in panel order - memory "
        f"{current.total_memory}, open slices "
        f"{current.total_slices}, standing decisions "
        f"{current.total_decisions}.")
    return record


def book_record(book: Any) -> Dict[str, Any]:
    """The session-news record of one session-memory book."""
    current = book if isinstance(book, SessionMemoryBook) \
        else build_book(book)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Session memory {current.title}: "
        f"{record['situation_count']} situations named.")
    return record


def plain_words(situation: Any) -> str:
    """One situation, in one plain sentence."""
    current = situation if isinstance(situation, SessionSituation) \
        else build_situation(situation)
    return (
        f"{current.title} - session {current.session_ref} "
        f"in {current.workspace}, saved {current.saved_on} "
        f"as {current.status}: {current.total_memory} "
        f"memory fact(s), {current.total_slices} open "
        f"slice(s), {current.total_decisions} standing "
        f"decision(s); its transcript held "
        f"{current.transcript_messages} message(s), "
        f"counted and not carried.")


def panel_plain_words(source: Any) -> str:
    """The panel in plain words, in full.

    Accepts a SituationPanel or a SessionMemoryBook
    (whose latest situation's panel is told). The
    panel is told whole - its rows in panel order and
    its account.
    """
    if isinstance(source, SituationPanel):
        panel = validate_panel(source)
        title = None
    elif isinstance(source, SessionMemoryBook):
        panel = derive_panel(source)
        title = source.title
    else:
        raise ValueError(
            f"a session memory source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    lines.append("Carried pieces, in panel order:")
    for row in panel.rows:
        lines.append(
            f"{row.item_id}: {row.kind} - {row.title}: "
            f"{row.detail}")
    lines.extend(panel.account)
    return "\n".join(lines)


# ---------------------------------------------------------------------
# Screens: the formatters and the shared /daymemory grammar.
# ---------------------------------------------------------------------


def _source_book(source: Any) -> SessionMemoryBook:
    if source is None:
        return load_session_memory()
    if isinstance(source, SessionMemoryRegistry):
        return source.book()
    if isinstance(source, SessionMemoryBook):
        return source
    if isinstance(source, SessionSituation):
        return SessionMemoryBook(
            title="One session situation", situations=(source,))
    raise ValueError(
        f"a session memory book is needed, got {source!r}")


def _source_situation(source: Any) -> SessionSituation:
    if isinstance(source, SessionSituation):
        return source
    return _source_book(source).situations[-1]


def format_situation(situation: Any) -> str:
    """One situation as a screen block."""
    current = situation if isinstance(situation, SessionSituation) \
        else build_situation(situation)
    lines = [
        f"{current.situation_id or '-'}: {current.title} - "
        f"session {current.session_ref} in {current.workspace}, "
        f"saved {current.saved_on}, status {current.status}",
        f"Its transcript held {current.transcript_messages} "
        f"message(s) - counted, not carried. Its situation: "
        f"{current.total_memory} memory fact(s), "
        f"{current.total_slices} open slice(s), "
        f"{current.total_decisions} standing decision(s).",
    ]
    for note in current.memory:
        lines.append(
            f"memory {note.note_id or '-'}: {note.title} - "
            f"{note.section} ({note.ref} from {note.source}): "
            f"{note.detail}")
    for slice_ in current.open_slices:
        lines.append(
            f"slice {slice_.slice_id}: {slice_.title} - "
            f"{slice_.state}: {slice_.note}")
    for decision in current.decisions:
        lines.append(
            f"decision {decision.decision_id or '-'}: "
            f"{decision.title} - {decision.decision} "
            f"(from {decision.source})")
    return "\n".join(lines)


def format_memory(source: Any = None) -> str:
    """Carried memory of one situation, in held order."""
    situation = _source_situation(source)
    lines = [
        f"{note.note_id or '-'}: {note.title} - "
        f"{note.section} ({note.ref} from {note.source}): "
        f"{note.detail}"
        for note in situation.memory]
    if not lines:
        lines.append("No memory is carried.")
    return "\n".join(lines)


def format_slices(source: Any = None) -> str:
    """Open slices of one situation, in held order."""
    situation = _source_situation(source)
    lines = [
        f"{slice_.slice_id}: {slice_.title} - "
        f"{slice_.state}: {slice_.note}"
        for slice_ in situation.open_slices]
    if not lines:
        lines.append("No open slices are carried.")
    return "\n".join(lines)


def format_decisions(source: Any = None) -> str:
    """Standing decisions of one situation, in held order."""
    situation = _source_situation(source)
    lines = [
        f"{decision.decision_id or '-'}: {decision.title} - "
        f"{decision.decision} (from {decision.source})"
        for decision in situation.decisions]
    if not lines:
        lines.append("No standing decisions are carried.")
    return "\n".join(lines)


def format_panel(source: Any = None) -> str:
    """The panel as a screen block: every row and the account.

    Accepts a SituationPanel or a SessionMemoryBook; a
    book shows the panel its latest situation derives.
    """
    if isinstance(source, SituationPanel):
        panel = validate_panel(source)
        lines: list = []
    else:
        book = _source_book(source)
        panel = derive_panel(book)
        lines = [f"Panel in {book.title}:"]
    lines.append("Carried pieces, in panel order:")
    for row in panel.rows:
        lines.append(
            f"{row.item_id}: {row.kind} - {row.title}: "
            f"{row.detail}")
    lines.extend(panel.account)
    return "\n".join(lines)


def format_session_memory_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /daymemory.

    With nothing named, the shipped example session
    memory book is shown - the example this slice
    ships - so the screen is never empty.
    """
    book = _source_book(source)
    lines = ["Session Memory Across Days (M-153) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_situation(book.situations[-1]))
    lines.append("")
    lines.append(format_panel(book))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_session_memory_args(args: Any) -> Tuple[str, Any]:
    """Parse the /daymemory grammar both surfaces share.

    No words (or ``show`` / ``list``) shows the session
    memory book; ``situation <situation-id>`` shows one
    situation; ``memory`` shows the latest situation's
    carried memory; ``slices`` its open slices;
    ``decisions`` its standing decisions; ``panel``
    shows the panel derived from the latest situation.
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
    if head in ("memory", "slices", "decisions", "panel") \
            and len(words) == 1:
        return (head, None)
    if head == "situation" and len(words) == 2:
        try:
            return (head, normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
