"""Pinning and protection (All-Features roadmap slice M-159).

Part VII continues. The roadmap's words:
``files/facts the compaction may never drop (the
task, the laws, the failing test) - pins are
visible.``

What already shipped, and what this slice adds:

* Context already compacts in this repo, on shipped
  roads: the context pruner (``agents/llm.py``)
  archives older turns, the compaction glass-box
  (``core/compaction_glassbox.py``, M-151) holds
  every compaction as shown, editable data, and the
  context budget account
  (``core/context_budget.py``, M-147) makes what is
  in the context - and why - visible as data. The
  memory holdings stand beside them: the project
  memory map (``core/project_memory_map.py``,
  M-150), session memory across days
  (``core/session_memory.py``, M-153), cross-project
  memory (``core/cross_project_memory.py``, M-154),
  the self-improving ledger
  (``core/self_improving_ledger.py``, M-155),
  decision records (``core/decision_records.py``,
  M-156), the forget journal
  (``core/forget_quarantine.py``, M-157) and context
  recipes (``core/context_recipes.py``, M-158), with
  crew memory (``core/crew_memory.py``, M-133) beside
  them. What none of those layers holds is the pin
  itself: the declaration, as data, that one file or
  fact is protected - that the compaction may never
  drop it - held where anyone can see it.
* This slice is that declaration, as a pure layer:
  a pin is one protected file or fact, validated as
  data WITH ITS PROVENANCE WHOLE - what is pinned,
  its kind, the reference it stands under, why it is
  protected, who pinned it, the day, and where it
  was read from - composed BY IMPORT from the
  shipped holdings it protects (a compaction record,
  a context-budget item, a carried note, a shared
  lesson, a ledger candidate, a decision record, a
  memory-map entry), each judged by its own layer's
  validation. The shipped data file
  (``mythic_agent/data/pinning_protection.yaml``)
  holds one example book in exactly the shape a real
  book file takes, a loader reads a book file
  anywhere on disk, the pin panel is DERIVED from
  the whole book (every pin standing whole, in a
  settled order - pins are VISIBLE, so the panel is
  the visible surface of what protection holds),
  pins are shaped as session news, and a small
  in-memory registry model holds pins one by one.
  The agent layer owns holding a book for a session
  and pinning the session's own compactions.

Honesty rules, enforced here and pinned by tests:

* **Pins are visible.** Every pin a book holds
  stands whole on the derived panel - its subject,
  its kind, the reference it protects, who pinned
  it and the day - in settled order, so what
  protection holds is never hidden, partial or
  stale: the panel is read off the book at call
  time, and a stored panel whose rows, totals,
  counts or account disagree with the derived one
  refuses.
* **Composed, never duplicated.** A pin that
  protects a shipped holding's piece is that piece
  read onto this layer by import and judged by its
  own layer's validation. Only the piece's kind and
  the reference it stands under cross the seam -
  the piece's own words are never copied into the
  pin. The pin's subject and its reason are named
  beside the reference by whoever pins it.
* **One thing is pinned once.** One book pins one
  standing thing once: the same kind and reference
  named twice in one book refuses, in a book and in
  the registry alike. The same kind and reference
  may be pinned again in another book - protection
  is declared per book, per session.
* **Data only - a pin compacts nothing and drops
  nothing.** A pin here is validated data DECLARING
  protection: it compacts no live context, drops no
  message, calls no model, edits no code, writes no
  workspace file and persists nothing beyond the
  session journal news the agent layer publishes.
  This layer declares protection; it does not itself
  rewrite the live pruner's behaviour - a pruner
  road honours pins only where a shipped road
  already composes this layer by import.
* **Malformed refuses.** A duplicate pin id in one
  book, the same thing pinned twice in one book, a
  pin with no provenance, and unknown keys in a
  pin, a panel or a book mapping all raise instead
  of being skipped or guessed at.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..resources import load_resource
from .compaction_glassbox import CompactionRecord
from .compaction_glassbox import validate_record as _validate_compaction
from .context_budget import ContextItem
from .context_budget import validate_item as _validate_context_item
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
    "PINNING_PROTECTION_RESOURCE",
    "PINNING_PROTECTION_SCHEMA",
    "PINNING_PROTECTION_SLICE",
    "PIN_KINDS",
    "PLAIN_EXPLANATION",
    "USAGE",
    "Pin",
    "PinKindCount",
    "PinPanelRow",
    "PinningBook",
    "PinningPanel",
    "PinningRegistry",
    "book_record",
    "build_book",
    "build_panel",
    "build_pin",
    "build_row",
    "derive_panel",
    "format_panel",
    "format_pin",
    "format_pinning_protection_screen",
    "format_pins",
    "inspect_pin_source",
    "is_protected",
    "load_pinning_protection",
    "load_pinning_protection_file",
    "normalize_pin_kind",
    "panel_plain_words",
    "panel_record",
    "parse_pin_args",
    "pin_from_compaction_record",
    "pin_from_context_item",
    "pin_from_cross_project",
    "pin_from_decision_record",
    "pin_from_ledger_candidate",
    "pin_from_memory_map",
    "pin_from_session_memory",
    "pin_record",
    "pinned_refs",
    "pins_from_memory_map",
    "pins_from_session_memory",
    "plain_words",
    "validate_book",
    "validate_panel",
    "validate_pin",
    "validate_row",
]

PINNING_PROTECTION_SLICE = "M-159"

#: The packaged data resource holding the example book.
PINNING_PROTECTION_RESOURCE = "pinning_protection.yaml"

#: The schema word a pinning-protection file must carry.
PINNING_PROTECTION_SCHEMA = "mythic.pinning_protection/1"

#: The classes of thing one pin may protect, in
#: panel order: the task the session is working on
#: (``task``), a law the work stands under (``law``),
#: the failing test that names what is still broken
#: (``failing-test``), a file (``file``), or any other
#: fact the compaction may never drop (``fact``) -
#: the roadmap's own classes: files and facts, the
#: task, the laws, the failing test. No other class
#: is pinned here.
PIN_KINDS = (
    "task", "law", "failing-test", "file", "fact")

_KIND_RANK = {kind: rank for rank, kind in enumerate(PIN_KINDS)}

_KIND_ALIASES = {
    "task": "task",
    "tasks": "task",
    "law": "law",
    "laws": "law",
    "rule": "law",
    "rules": "law",
    "failing-test": "failing-test",
    "failing": "failing-test",
    "test": "failing-test",
    "file": "file",
    "files": "file",
    "fact": "fact",
    "facts": "fact",
}

_PIN_KEYS = frozenset({
    "pin_id", "id", "subject", "title", "what",
    "kind", "class",
    "ref", "reference",
    "why", "reason",
    "pinned_by", "by", "who",
    "pinned_on", "day", "date",
    "source",
})

_ROW_KEYS = frozenset({
    "pin_id", "id", "subject", "kind", "class",
    "ref", "reference", "pinned_by", "pinned_on",
})

_KIND_COUNT_KEYS = frozenset({"kind", "pins", "count"})

_PANEL_KEYS = frozenset({
    "panel_id", "id", "rows", "pins",
    "total_pins", "total",
    "kind_counts", "kinds",
    "account", "statements",
})

_BOOK_KEYS = frozenset({"title", "name"})

_PINNING_BOOK_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "canon_note", "guide", "pins", "panels",
})

#: The shipped example book's title, held to this
#: by the loader's example check.
_EXAMPLE_TITLE = "Pinning and protection at the M-158 slice boundary"

#: The shipped example's pin ids, in held order,
#: pinned by the loader.
_EXAMPLE_PIN_IDS = (
    "pin-the-task", "pin-forge-laws",
    "pin-failing-test", "pin-recipes-module")

#: The shipped example's first pin and the subject
#: it protects, pinned by the loader.
_EXAMPLE_FIRST_PIN_ID = "pin-the-task"

_EXAMPLE_FIRST_PIN_SUBJECT = (
    "the task the session is working on: "
    "M-159, pinning and protection")

#: The shipped example's one panel id, and its rows
#: in panel order, pinned by the loader.
_EXAMPLE_PANEL_ID = "panel-m158-boundary"

_EXAMPLE_PANEL_ROW_IDS = (
    "pin-the-task", "pin-forge-laws",
    "pin-failing-test", "pin-recipes-module")

_EXAMPLE_PANEL_ACCOUNT = (
    "The pin panel holds 4 pins protecting what "
    "compaction may never drop: failing-test 1, "
    "file 1, law 1, task 1.",
    "Pins stand by kind - the task first, then the "
    "laws, the failing test, the files, the facts - "
    "then by subject, then pin id, so two panels of "
    "one book diff cleanly, line by line.",
    "Every pin is visible: the panel shows each "
    "protected file and fact whole - what is pinned, "
    "its kind, who pinned it and the day.",
    "The panel is read off the book at call time - "
    "it is derived, never stored loose.",
)

PLAIN_EXPLANATION = (
    "Pinning and protection: files and facts the "
    "compaction may never drop - the task, the laws, "
    "the failing test - and pins are visible. A pin "
    "is one protected file or fact carried with its "
    "provenance whole: what is pinned, its kind, the "
    "reference it stands under, why it is protected, "
    "who pinned it, the day, and where it was read "
    "from. The pin panel is derived from the book at "
    "call time: every pin standing whole, by kind, "
    "then subject, then pin id. This layer holds "
    "pins as data only: it compacts nothing, drops "
    "nothing, calls no model, writes no project "
    "files and persists nothing."
)

USAGE = (
    "Usage: /pins, /pins show, "
    "/pins pin <pin-id>, "
    "/pins kind <kind>, "
    "/pins panel"
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
        raise ValueError(f"a pin names two different {what}")
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
    text = _clean_text(value, "a pin's pinned-on day")
    try:
        parsed = date.fromisoformat(text)
    except ValueError:
        raise ValueError(
            f"a pin's pinned-on day must be an ISO "
            f"date (YYYY-MM-DD), got {text!r}") from None
    if parsed.isoformat() != text:
        raise ValueError(
            f"a pin's pinned-on day must be an ISO "
            f"date (YYYY-MM-DD), got {text!r}")
    return text


def normalize_pin_kind(value: Any) -> str:
    """The canonical pin kind a word names.

    A kind is one of :data:`PIN_KINDS` - the
    roadmap's own classes of protected thing - read
    case-insensitively, with their plain faces
    (``tasks``, ``laws`` / ``rules``, ``failing`` /
    ``test``, ``files``, ``facts``) read onto them.
    Anything else raises, plainly naming the five.
    """
    if isinstance(value, str):
        wanted = _KIND_ALIASES.get(value.strip().lower())
        if wanted is not None:
            return wanted
    raise ValueError(
        "a pin kind must be one of %s, got %r"
        % ("/".join(PIN_KINDS), value))



# ---------------------------------------------------------------------
# The pin: one protected file or fact, provenance whole.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class Pin:
    """One protected file or fact, declared as data.

    ``subject`` is what is pinned, in plain words -
    the task, the laws, the failing test, a file, a
    fact; ``kind`` is its class, one of the roadmap's
    own classes; ``ref`` is the reference the pinned
    thing stands under; ``why`` is the plain-words
    reason it is protected - why the compaction may
    never drop it. The provenance stands whole beside
    the pin: ``pinned_by`` names who pinned it,
    ``pinned_on`` is the day, and ``source`` names
    where it was read from. A pin with any provenance
    word missing is no pin at all.
    """

    subject: str
    kind: str
    ref: str
    why: str
    pinned_by: str
    pinned_on: str
    source: str
    pin_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.pin_id is not None:
            object.__setattr__(
                self, "pin_id", normalize_member_id(self.pin_id))
        object.__setattr__(
            self, "subject",
            _check_title(self.subject, "a pin's subject"))
        object.__setattr__(self, "kind", normalize_pin_kind(self.kind))
        object.__setattr__(
            self, "ref", _check_word(self.ref, "a pin's reference"))
        object.__setattr__(
            self, "why",
            _check_long_text(self.why, "a pin's reason"))
        object.__setattr__(
            self, "pinned_by",
            _check_title(self.pinned_by, "a pin's pinner"))
        object.__setattr__(self, "pinned_on", _check_day(self.pinned_on))
        object.__setattr__(
            self, "source",
            _check_title(self.source, "a pin's source"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "pinning_protection_pin",
            "slice": PINNING_PROTECTION_SLICE,
            "pin_id": self.pin_id,
            "subject": self.subject,
            "kind": self.kind,
            "ref": self.ref,
            "why": self.why,
            "pinned_by": self.pinned_by,
            "pinned_on": self.pinned_on,
            "source": self.source,
        }


def _check_pin_ref(value: Any) -> Pin:
    if isinstance(value, Pin):
        return value
    if isinstance(value, dict):
        return validate_pin(value)
    raise ValueError(f"a pin is needed, got {value!r}")


def validate_pin(pin: Any) -> Pin:
    """Validate one pin into a Pin.

    Accepts a pin or a mapping naming a ``subject``
    (or ``title`` / ``what``), a ``kind`` (or
    ``class``), a ``ref`` (or ``reference``), a
    ``why`` (or ``reason``), a ``pinned_by`` (or
    ``by`` / ``who``), a ``pinned_on`` (or ``day`` /
    ``date``), a ``source`` and an optional
    ``pin_id`` (or ``id``). Naming two spellings of
    one field with different values refuses, and
    unknown keys refuse.
    """
    if isinstance(pin, Pin):
        return pin
    if not isinstance(pin, dict):
        raise ValueError(f"a pin must be a mapping, got {pin!r}")
    unknown = set(pin) - _PIN_KEYS
    if unknown:
        raise ValueError(
            "unknown pin keys: %s" % ", ".join(sorted(unknown)))

    def _needed(spellings: Tuple[str, ...], what: str) -> Any:
        value = _pick_any(pin, spellings, what)
        if value is None:
            raise ValueError(f"a pin is missing its {what}")
        return value

    kwargs: Dict[str, Any] = {
        "subject": _needed(("subject", "title", "what"), "subject"),
        "kind": _needed(("kind", "class"), "kind"),
        "ref": _needed(("ref", "reference"), "reference"),
        "why": _needed(("why", "reason"), "reason"),
        "pinned_by": _needed(("pinned_by", "by", "who"), "pinner"),
        "pinned_on": _needed(
            ("pinned_on", "day", "date"), "pinned-on day"),
        "source": _needed(("source",), "source"),
    }
    named_id = _pick_any(pin, ("pin_id", "id"), "pin ids")
    if named_id is not None:
        kwargs["pin_id"] = named_id
    return Pin(**kwargs)


def build_pin(pin: Any = None, **kwargs: Any) -> Pin:
    """Build one validated pin, from a mapping or field words."""
    if isinstance(pin, Pin) and not kwargs:
        return pin
    if isinstance(pin, dict) or pin is None:
        merged: Dict[str, Any] = {}
        if isinstance(pin, dict):
            merged.update(pin)
        merged.update(kwargs)
        return validate_pin(merged)
    raise ValueError(f"a pin must be a mapping, got {pin!r}")


def _pin_for(kind: str, ref: Optional[str], *, subject: Any,
             why: Any, pinned_by: Any, pinned_on: Any,
             source: Any) -> Pin:
    """One pin for one shipped piece, by kind and reference alone.

    The piece's own words are never read here: only
    its kind and the reference it stands under. The
    pin's subject, the reason it is protected, who
    pinned it, the day and the source are named beside
    the reference - a piece protected for no named
    reason, or by no named pinner, refuses. A piece
    with no reference refuses: a pin must name which
    standing thing it protects.
    """
    if why is None:
        raise ValueError(
            "a pin must carry its reason: why this thing "
            "is protected - nothing is protected for no "
            "named reason")
    if pinned_by is None:
        raise ValueError(
            "a pin must name who pinned it - protection "
            "declared by no one is no protection")
    if ref is None or (isinstance(ref, str) and not ref.strip()):
        raise ValueError(
            "a pin names the reference the protected "
            "thing stood under - a thing with no reference "
            "cannot be pinned, by kind alone or otherwise")
    return Pin(
        subject=subject, kind=kind, ref=ref, why=why,
        pinned_by=pinned_by, pinned_on=pinned_on, source=source)


def inspect_pin_source(piece: Any) -> Dict[str, Any]:
    """Inspect one shipped piece: its pin kind and reference only.

    The piece is judged by the layer that owns its
    type, never by whichever validator happens to
    accept its shape first - exactly as the sibling
    layers' inspection roads judge. A piece with no
    reference, or a value no shipped layer owns,
    refuses.
    """
    if isinstance(piece, Pin):
        return {"kind": piece.kind, "ref": piece.ref}
    owned = (
        (CompactionRecord, _validate_compaction, "fact", "record_id"),
        (ContextItem, _validate_context_item, None, "item_id"),
        (CarriedMemory, _validate_note, "fact", "note_id"),
        (SharedLesson, _validate_lesson, "law", "lesson_id"),
        (CandidateMemory, _validate_candidate,
         "fact", "candidate_id"),
        (DecisionRecord, _validate_decision, "law", "record_id"),
        (MemoryMapEntry, _validate_map_entry, "fact", "entry_id"),
        (CrewMemoryEntry, _validate_crew_entry, "fact", "entry_id"),
    )
    for kind_type, validator, kind, attr in owned:
        if isinstance(piece, kind_type):
            validated = validator(piece)
            ref = getattr(validated, attr, None)
            if ref is None or (
                    isinstance(ref, str) and not ref.strip()):
                raise ValueError(
                    "an inspected piece names the reference "
                    "it stands under - this piece carries none")
            if kind is None:
                kind = (
                    "file" if validated.kind == "file" else "fact")
            return {"kind": kind, "ref": ref}
    if isinstance(piece, dict):
        if "kind" in piece and "ref" in piece:
            checked = validate_pin({
                "subject": "an inspected pin", "kind": piece["kind"],
                "ref": piece["ref"], "why": "inspected",
                "pinned_by": "inspection", "pinned_on": "2026-01-01",
                "source": "inspection"})
            return {"kind": checked.kind, "ref": checked.ref}
        for kind_type, validator, kind, attr in owned:
            try:
                validated = validator(piece)
            except Exception:
                continue
            ref = getattr(validated, attr, None)
            if ref is None or (
                    isinstance(ref, str) and not ref.strip()):
                continue
            if kind is None:
                kind = (
                    "file" if validated.kind == "file" else "fact")
            return {"kind": kind, "ref": ref}
    raise ValueError(
        f"no shipped layer owns this piece, got {piece!r}")


def pin_from_compaction_record(record: Any, *, why: Any,
                               pinned_by: Any, pinned_on: Any,
                               source: Any = "compaction glass-box",
                               subject: Any = None) -> Pin:
    """Build one pin from a shipped compaction-glassbox record.

    The record - the glass-box's own record, judged by
    that layer's own validation - is read onto a pin
    BY IMPORT by its kind and reference alone: its id
    stands as the pin's reference, and the pin's
    subject names the compaction record by that id
    unless a subject is named. Its title, summary and
    replaced material are never read here. The reason
    it is protected and who pinned it are named beside
    it.
    """
    validated = _validate_compaction(record)
    return _pin_for(
        "fact", validated.record_id,
        subject=subject if subject is not None else (
            f"compaction record {validated.record_id}"),
        why=why, pinned_by=pinned_by, pinned_on=pinned_on,
        source=source)


def pin_from_context_item(item: Any, *, why: Any, pinned_by: Any,
                          pinned_on: Any,
                          source: Any = "context budget",
                          subject: Any = None) -> Pin:
    """Build one pin from a shipped context-budget item.

    The item - the context budget's own record, judged
    by that layer's own validation - is read onto a
    pin BY IMPORT by its kind and reference alone: a
    file item pins as a file, every other item as a
    fact. Its title, source and reason in the budget
    are never read here. The reason it is protected
    and who pinned it are named beside it, exactly as
    for a compaction record.
    """
    validated = _validate_context_item(item)
    kind = "file" if validated.kind == "file" else "fact"
    return _pin_for(
        kind, validated.item_id,
        subject=subject if subject is not None else (
            f"context item {validated.item_id}"),
        why=why, pinned_by=pinned_by, pinned_on=pinned_on,
        source=source)


def pin_from_session_memory(note: Any, *, why: Any, pinned_by: Any,
                            pinned_on: Any,
                            source: Any = "session memory",
                            subject: Any = None) -> Pin:
    """Build one pin from a shipped session-memory carried note.

    The note - session memory's own record, judged by
    that layer's own validation - is read onto a pin
    BY IMPORT by its kind and reference alone: its id
    stands as the pin's reference. Its title and
    detail are never read here. The reason it is
    protected and who pinned it are named beside it.
    """
    validated = _validate_note(note)
    return _pin_for(
        "fact", validated.note_id,
        subject=subject if subject is not None else (
            f"carried memory {validated.note_id}"),
        why=why, pinned_by=pinned_by, pinned_on=pinned_on,
        source=source)


def pin_from_cross_project(lesson: Any, *, why: Any, pinned_by: Any,
                           pinned_on: Any,
                           source: Any = "cross-project memory",
                           subject: Any = None) -> Pin:
    """Build one pin from a shipped cross-project shared lesson.

    The lesson - cross-project memory's own record,
    judged by that layer's own validation - is read
    onto a pin BY IMPORT by its kind and reference
    alone: a shared lesson stands in a session as a
    law, so it pins as one. Its title, detail and
    evidence are never read here. The reason and the
    pinner are named beside it, exactly as for a note.
    """
    validated = _validate_lesson(lesson)
    return _pin_for(
        "law", validated.lesson_id,
        subject=subject if subject is not None else (
            f"shared lesson {validated.lesson_id}"),
        why=why, pinned_by=pinned_by, pinned_on=pinned_on,
        source=source)


def pin_from_ledger_candidate(candidate: Any, *, why: Any,
                              pinned_by: Any, pinned_on: Any,
                              source: Any = "self-improving ledger",
                              subject: Any = None) -> Pin:
    """Build one pin from a shipped self-improving ledger candidate.

    The candidate - the ledger's own record, judged by
    that layer's own validation - is read onto a pin
    BY IMPORT by its kind and reference alone. Its
    title and detail are never read here. The reason
    and the pinner are named beside it, exactly as
    for a note.
    """
    validated = _validate_candidate(candidate)
    return _pin_for(
        "fact", validated.candidate_id,
        subject=subject if subject is not None else (
            f"ledger candidate {validated.candidate_id}"),
        why=why, pinned_by=pinned_by, pinned_on=pinned_on,
        source=source)


def pin_from_decision_record(record: Any, *, why: Any,
                             pinned_by: Any, pinned_on: Any,
                             source: Any = "decision records",
                             subject: Any = None) -> Pin:
    """Build one pin from a shipped decision record.

    The record - decision records' own record, judged
    by that layer's own validation - is read onto a
    pin BY IMPORT by its kind and reference alone: an
    accepted choice stands in a session as a law, so
    it pins as one. Its title, decision and rationale
    are never read here. The reason and the pinner are
    named beside it, exactly as for a note.
    """
    validated = _validate_decision(record)
    return _pin_for(
        "law", validated.record_id,
        subject=subject if subject is not None else (
            f"decision record {validated.record_id}"),
        why=why, pinned_by=pinned_by, pinned_on=pinned_on,
        source=source)


def pin_from_memory_map(entry: Any, *, why: Any, pinned_by: Any,
                        pinned_on: Any,
                        source: Any = "project memory map",
                        subject: Any = None) -> Pin:
    """Build one pin from a shipped project memory-map entry.

    The entry - the memory map's own record, judged by
    the map's own validation - is read onto a pin BY
    IMPORT by its kind and reference alone: any
    section of the map may be pinned, so no section is
    refused here. Its title and detail are never read
    here. The reason and the pinner are named beside
    it, exactly as for a note.
    """
    validated = _validate_map_entry(entry)
    return _pin_for(
        "fact", validated.entry_id,
        subject=subject if subject is not None else (
            f"memory-map entry {validated.entry_id}"),
        why=why, pinned_by=pinned_by, pinned_on=pinned_on,
        source=source)


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


def pins_from_session_memory(source: Any, *, why: Any,
                             pinned_by: Any, pinned_on: Any
                             ) -> Tuple[Pin, ...]:
    """Pins read off the shipped session memory.

    The carried notes of a session situation - or of a
    whole session-memory book or registry - are read
    onto pins BY IMPORT, judged by session memory's
    own validation on the way, under one named reason
    and one named pinner. Every note's title and
    detail stay in session memory: only ids cross.
    """
    return tuple(
        pin_from_session_memory(
            note, why=why, pinned_by=pinned_by,
            pinned_on=pinned_on)
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


def pins_from_memory_map(source: Any, *, why: Any,
                         pinned_by: Any, pinned_on: Any
                         ) -> Tuple[Pin, ...]:
    """Pins read off the shipped project memory map.

    The map's entries - every section, for any fact of
    the project may be pinned - are read onto pins BY
    IMPORT, judged by the map's own validation on the
    way, under one named reason and one named pinner,
    exactly as for session memory. Only ids cross.
    """
    return tuple(
        pin_from_memory_map(
            entry, why=why, pinned_by=pinned_by,
            pinned_on=pinned_on)
        for entry in _map_entries(source))



# ---------------------------------------------------------------------
# The pin panel: every pin carried whole, derived - pins are visible.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class PinPanelRow:
    """One pin carried whole into the panel.

    ``pin_id`` names the pin; ``subject`` is what is
    pinned; ``kind`` is its class; ``ref`` is the
    reference it protects; ``pinned_by`` and
    ``pinned_on`` are the pin's provenance head - who
    pinned it and the day. :func:`validate_row` judged
    against its pin refuses a row whose fields
    disagree with the row they derive.
    """

    pin_id: str
    subject: str
    kind: str
    ref: str
    pinned_by: str
    pinned_on: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "pin_id", normalize_member_id(self.pin_id))
        object.__setattr__(
            self, "subject",
            _check_title(self.subject, "a row's subject"))
        object.__setattr__(self, "kind", normalize_pin_kind(self.kind))
        object.__setattr__(
            self, "ref", _check_word(self.ref, "a row's reference"))
        object.__setattr__(
            self, "pinned_by",
            _check_title(self.pinned_by, "a row's pinner"))
        object.__setattr__(self, "pinned_on", _check_day(self.pinned_on))

    @property
    def sort_key(self) -> Tuple[int, str, str]:
        """This row's place in panel order (derived).

        Rows stand by kind - the task first, then the
        laws, the failing test, the files, the facts -
        then by subject, then pin id.
        """
        return (_KIND_RANK[self.kind], self.subject.lower(), self.pin_id)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "pinning_protection_panel_row",
            "slice": PINNING_PROTECTION_SLICE,
            "pin_id": self.pin_id,
            "subject": self.subject,
            "kind": self.kind,
            "ref": self.ref,
            "pinned_by": self.pinned_by,
            "pinned_on": self.pinned_on,
        }


def _row_for_pin(pin: Pin) -> PinPanelRow:
    return PinPanelRow(
        pin_id=pin.pin_id, subject=pin.subject, kind=pin.kind,
        ref=pin.ref, pinned_by=pin.pinned_by, pinned_on=pin.pinned_on)


def _check_row_ref(value: Any) -> PinPanelRow:
    if isinstance(value, PinPanelRow):
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

        return PinPanelRow(
            pin_id=_needed(("pin_id", "id"), "pin id"),
            subject=_needed(("subject",), "subject"),
            kind=_needed(("kind", "class"), "kind"),
            ref=_needed(("ref", "reference"), "reference"),
            pinned_by=_needed(("pinned_by",), "pinner"),
            pinned_on=_needed(("pinned_on",), "pinned-on day"))
    raise ValueError(f"a panel row is needed, got {value!r}")


def validate_row(row: Any, pin: Any = None) -> PinPanelRow:
    """Validate one panel row into a PinPanelRow.

    Accepts a row or a mapping naming a ``pin_id``
    (or ``id``), a ``subject``, a ``kind`` (or
    ``class``), a ``ref`` (or ``reference``), a
    ``pinned_by`` and a ``pinned_on``. With *pin*
    given, the row is judged against the row derived
    from that pin: a stored row whose fields disagree
    with the derived row refuses.
    """
    current = _check_row_ref(row)
    if pin is not None:
        checked_pin = _check_pin_ref(pin)
        derived = _row_for_pin(checked_pin)
        if current != derived:
            raise ValueError(
                "a stored row disagrees with the row "
                "derived from its pin")
    return current


def build_row(row: Any = None, pin: Any = None,
              **kwargs: Any) -> PinPanelRow:
    """Build one validated row, from a mapping or field words."""
    if isinstance(row, PinPanelRow) and not kwargs:
        return validate_row(row, pin)
    if isinstance(row, dict) or row is None:
        merged: Dict[str, Any] = {}
        if isinstance(row, dict):
            merged.update(row)
        merged.update(kwargs)
        return validate_row(merged, pin)
    return validate_row(row, pin)


@dataclass(frozen=True)
class PinKindCount:
    """One kind's count in a panel: its pins tallied."""

    kind: str
    pins: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", normalize_pin_kind(self.kind))
        object.__setattr__(
            self, "pins",
            _check_count(self.pins, "a kind count's pins"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "pins": self.pins,
        }


def _check_kind_count_ref(value: Any) -> PinKindCount:
    if isinstance(value, PinKindCount):
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
        pins = _pick_any(value, ("pins", "count"), "counts")
        if pins is None:
            raise ValueError("a kind count is missing its pins")
        return PinKindCount(kind=kind, pins=pins)
    raise ValueError(f"a kind count is needed, got {value!r}")


def _panel_account(total_pins: int,
                   kind_counts: Tuple[PinKindCount, ...]
                   ) -> Tuple[str, ...]:
    tallies = ", ".join(
        f"{count.kind} {count.pins}"
        for count in sorted(
            kind_counts, key=lambda count: count.kind))
    return (
        f"The pin panel holds {total_pins} pins "
        f"protecting what compaction may never drop: "
        f"{tallies}.",
        "Pins stand by kind - the task first, then the "
        "laws, the failing test, the files, the facts - "
        "then by subject, then pin id, so two panels of "
        "one book diff cleanly, line by line.",
        "Every pin is visible: the panel shows each "
        "protected file and fact whole - what is pinned, "
        "its kind, who pinned it and the day.",
        "The panel is read off the book at call time - "
        "it is derived, never stored loose.",
    )


@dataclass(frozen=True)
class PinningPanel:
    """The pin panel of one book, derived from the whole book.

    ``rows`` are the book's pins carried whole, in
    panel order (by kind, then subject, then pin id,
    so two panels of one book diff cleanly);
    ``total_pins`` is the rows' own count;
    ``kind_counts`` are the per-kind tallies of every
    pin in the book, in the order their kinds first
    appear in the panel; ``account`` is read off those
    numbers. A panel whose rows stand out of panel
    order, or whose totals are not its own rows'
    counts, refuses at construction;
    :func:`validate_panel` judged against a book
    refuses a stored panel that disagrees with the
    derived one.
    """

    rows: Tuple[PinPanelRow, ...] = ()
    total_pins: int = 0
    kind_counts: Tuple[PinKindCount, ...] = ()
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
            if row.pin_id in seen:
                raise ValueError(
                    f"a panel row for pin {row.pin_id!r} "
                    f"already exists")
            seen.add(row.pin_id)
        keys = [row.sort_key for row in rows]
        if keys != sorted(keys):
            raise ValueError(
                "a panel's rows must stand in panel order "
                "(by kind, then subject, then pin id)")
        object.__setattr__(self, "rows", rows)
        object.__setattr__(
            self, "total_pins",
            _check_count(self.total_pins, "a panel's total pins"))
        if self.total_pins != len(rows):
            raise ValueError(
                "a panel's total pins must be its own "
                "rows' count")
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
        if sum(c.pins for c in kind_counts) != self.total_pins:
            raise ValueError(
                "a panel's kind counts must sum to its own "
                "total pins")
        tallies: Dict[str, int] = {}
        for row in rows:
            tallies[row.kind] = tallies.get(row.kind, 0) + 1
        for count in kind_counts:
            if count.pins != tallies.get(count.kind, 0):
                raise ValueError(
                    "a panel's kind counts must be its own "
                    "rows' counts")
        if set(tallies) != {c.kind for c in kind_counts}:
            raise ValueError(
                "a panel's kind counts must name every kind "
                "its rows carry")
        object.__setattr__(self, "account", _check_account(self.account))

    def row_for(self, pin_id: Any) -> PinPanelRow:
        """The panel row one pin names in this panel."""
        wanted = normalize_member_id(pin_id)
        for row in self.rows:
            if row.pin_id == wanted:
                return row
        raise KeyError(f"no row in the panel: pin {wanted!r}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "pinning_protection_panel",
            "slice": PINNING_PROTECTION_SLICE,
            "panel_id": self.panel_id,
            "rows": [row.to_record() for row in self.rows],
            "total_pins": self.total_pins,
            "kind_counts": [c.to_record() for c in self.kind_counts],
            "account": list(self.account),
        }


def _held_pins(source: Any) -> Tuple[Pin, ...]:
    """The pins one source holds, in held order."""
    if isinstance(source, PinningBook):
        return source.pins
    if isinstance(source, PinningRegistry):
        return source.list_pins()
    if isinstance(source, (list, tuple)):
        return tuple(_check_pin_ref(item) for item in source)
    raise ValueError(f"pins are needed, got {source!r}")


def derive_panel(source: Any) -> PinningPanel:
    """Derive the pin panel from one book.

    The rows are the book's pins carried whole, in
    panel order: by kind, then subject, then pin id.
    *source* is a book or a registry. A source holding
    no pin refuses - a panel of nothing is no panel.
    """
    pins = _held_pins(source)
    if not pins:
        raise ValueError("a panel needs at least one pin")
    rows = []
    for pin in pins:
        if pin.pin_id is None:
            raise ValueError(
                "a panel row must name its pin - a "
                "pin with no id refuses derivation")
        rows.append(_row_for_pin(pin))
    rows = tuple(sorted(rows, key=lambda r: r.sort_key))
    order: list = []
    tally: Dict[str, int] = {}
    for row in rows:
        if row.kind not in tally:
            tally[row.kind] = 0
            order.append(row.kind)
        tally[row.kind] += 1
    kind_counts = tuple(
        PinKindCount(kind=kind, pins=tally[kind])
        for kind in order)
    return PinningPanel(
        rows=rows, total_pins=len(rows),
        kind_counts=kind_counts,
        account=_panel_account(len(rows), kind_counts))


def validate_panel(panel: Any, source: Any = None
                   ) -> PinningPanel:
    """Validate one panel into a PinningPanel.

    Accepts a panel or a mapping naming ``rows`` (or
    ``pins``), a ``total_pins`` (or ``total``),
    ``kind_counts`` (or ``kinds``), an ``account``
    (or ``statements``) and an optional ``panel_id``
    (or ``id``). With *source* given (a book), the
    panel is judged against the panel derived from
    that book: a stored panel whose rows, totals,
    kind counts or account disagree with the derived
    panel refuses. A panel naming no account refuses
    too.
    """
    if isinstance(panel, PinningPanel):
        current = panel
    elif isinstance(panel, dict):
        unknown = set(panel) - _PANEL_KEYS
        if unknown:
            raise ValueError(
                "unknown panel keys: %s" % ", ".join(sorted(unknown)))
        rows = _pick_any(panel, ("rows", "pins"), "rows")
        if rows is None:
            raise ValueError("a panel is missing its rows")
        total = _pick_any(panel, ("total_pins", "total"), "totals")
        if total is None:
            raise ValueError("a panel is missing its total pins")
        kind_counts = _pick_any(
            panel, ("kind_counts", "kinds"), "kind counts")
        if kind_counts is None:
            raise ValueError("a panel is missing its kind counts")
        account = _pick_any(panel, ("account", "statements"), "accounts")
        if account is None:
            raise ValueError("a panel names no account of its own")
        kwargs: Dict[str, Any] = {
            "rows": rows, "total_pins": total,
            "kind_counts": kind_counts, "account": account}
        panel_id = _pick_any(panel, ("panel_id", "id"), "panel ids")
        if panel_id is not None:
            kwargs["panel_id"] = panel_id
        current = PinningPanel(**kwargs)
    else:
        raise ValueError(f"a panel must be a mapping, got {panel!r}")
    if source is not None:
        derived = derive_panel(source)
        if (current.rows != derived.rows
                or current.total_pins != derived.total_pins
                or current.kind_counts != derived.kind_counts
                or current.account != derived.account):
            raise ValueError(
                "a stored panel disagrees with the panel "
                "derived from its book")
    return current


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> PinningPanel:
    """Build one validated panel, from a mapping or field words."""
    if isinstance(panel, PinningPanel) and not kwargs:
        return validate_panel(panel, source)
    if isinstance(panel, dict) or panel is None:
        merged: Dict[str, Any] = {}
        if isinstance(panel, dict):
            merged.update(panel)
        merged.update(kwargs)
        return validate_panel(merged, source)
    return validate_panel(panel, source)



# ---------------------------------------------------------------------
# The book: pins in held order, panels judged.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class PinningBook:
    """One pinning-protection book: its pins, in held order.

    ``pins`` are the pins, in held order, each with
    its provenance whole; no two pins of one book
    protect the same standing thing - one thing is
    pinned once in a book. ``panels`` are the book's
    derivations - pin panels of the whole book, each
    judged against the book by :func:`validate_book`;
    ``canon_note`` is the book's own note. The total
    is the pins' own count, judged at construction.
    This book is the book file's shape: the shipped
    example is one book, and a real book file is a new
    file in this shape.
    """

    title: str = ""
    pins: Tuple[Pin, ...] = ()
    panels: Tuple[PinningPanel, ...] = ()
    canon_note: str = ""
    total_pins: Optional[int] = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_title(self.title, "a book's title"))
        if isinstance(self.pins, (str, bytes)) \
                or not isinstance(self.pins, (list, tuple)):
            raise ValueError(
                f"a book's pins must be a list of "
                f"pins, got {self.pins!r}")
        pins = tuple(_check_pin_ref(item) for item in self.pins)
        if not pins:
            raise ValueError("a pinning book holds at least one pin")
        seen_ids = set()
        seen_refs = set()
        for pin in pins:
            if pin.pin_id is not None:
                if pin.pin_id in seen_ids:
                    raise ValueError(
                        f"a pin named {pin.pin_id!r} "
                        f"already exists")
                seen_ids.add(pin.pin_id)
            key = (pin.kind, pin.ref)
            if key in seen_refs:
                raise ValueError(
                    f"the {pin.kind} standing as {pin.ref!r} "
                    f"is already pinned in this book - one "
                    f"thing is pinned once in a book")
            seen_refs.add(key)
        object.__setattr__(self, "pins", pins)
        if isinstance(self.panels, (str, bytes)) \
                or not isinstance(self.panels, (list, tuple)):
            raise ValueError(
                f"a book's panels must be a list of panels, "
                f"got {self.panels!r}")
        panels = tuple(
            p if isinstance(p, PinningPanel)
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
        given = self.total_pins
        if given is None:
            object.__setattr__(self, "total_pins", len(pins))
        else:
            checked = _check_count(given, "a book's total pins")
            if checked != len(pins):
                raise ValueError(
                    "a book's total pins must be its own "
                    "pins' count")
            object.__setattr__(self, "total_pins", checked)

    def pin_for(self, pin_id: Any) -> Pin:
        """The pin one id names in this book."""
        wanted = normalize_member_id(pin_id)
        for pin in self.pins:
            if pin.pin_id == wanted:
                return pin
        raise KeyError(f"no pin in the book: {wanted!r}")

    def pin_for_ref(self, kind: Any, ref: Any) -> Pin:
        """The pin protecting one standing thing in this book.

        The kind is read through the kind aliases and
        the reference matched as it stands. A thing no
        pin of the book protects raises KeyError -
        protection is declared, never guessed.
        """
        wanted_kind = normalize_pin_kind(kind)
        wanted_ref = _check_word(ref, "a pin's reference")
        for pin in self.pins:
            if pin.kind == wanted_kind and pin.ref == wanted_ref:
                return pin
        raise KeyError(
            f"no pin in the book protects the {wanted_kind} "
            f"standing as {wanted_ref!r}")

    def panel_for(self, panel_id: Any) -> PinningPanel:
        """The stored panel one id names in this book."""
        wanted = normalize_member_id(panel_id)
        for panel in self.panels:
            if panel.panel_id == wanted:
                return panel
        raise KeyError(f"no panel in the book: {wanted!r}")

    def pin_ids(self) -> Tuple[str, ...]:
        """Every held pin id, in held order."""
        return tuple(
            item.pin_id for item in self.pins if item.pin_id)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "pinning_protection_book",
            "slice": PINNING_PROTECTION_SLICE,
            "title": self.title,
            "pin_ids": list(self.pin_ids()),
            "pin_count": len(self.pins),
            "panel_count": len(self.panels),
        }


def validate_book(data: Any, *, require_example: bool = False
                  ) -> PinningBook:
    """Validate one pinning-protection mapping into a book.

    The mapping names a ``schema`` (the
    pinning-protection schema word), a ``guide``
    mapping (its ``title``), a ``pins`` list and an
    optional ``panels`` list. Every pin stands on its
    own validation, then the whole is judged: pin ids
    unique, no thing pinned twice, and every stored
    panel judged against the book (a panel the book
    does not derive refuses). With ``require_example``
    the shipped example is held to its pinned shape:
    the pinned title, pins and panel, and the panel's
    pinned rows and account word-for-word. Problems
    raise :class:`ValidationError` or ``ValueError``.
    """
    if isinstance(data, PinningBook):
        return data
    if not isinstance(data, dict):
        raise ValidationError(
            f"a pinning book must be a mapping, got {data!r}")
    unknown = set(data) - _PINNING_BOOK_KEYS
    if unknown:
        raise ValidationError(
            "unknown pinning-book keys: %s" % ", ".join(sorted(unknown)))
    if data.get("schema") != PINNING_PROTECTION_SCHEMA:
        raise ValidationError(
            f"a pinning book must carry schema "
            f"{PINNING_PROTECTION_SCHEMA!r}, got {data.get('schema')!r}")
    pins = _pick_any(data, ("pins",), "pins")
    if pins is None:
        raise ValidationError("a pinning book is missing its pins")
    if not isinstance(pins, (list, tuple)):
        raise ValidationError("a pinning book's pins must be a list")
    if data.get("panels") is not None \
            and not isinstance(data["panels"], (list, tuple)):
        raise ValidationError("a pinning book's panels must be a list")
    head = data.get("guide") or {}
    if not isinstance(head, dict):
        raise ValidationError("a pinning book's guide must be a mapping")
    unknown_head = set(head) - _BOOK_KEYS
    if unknown_head:
        raise ValidationError(
            "unknown guide keys: %s" % ", ".join(sorted(unknown_head)))
    try:
        title = _pick_any(head, ("title", "name"), "titles")
        if title is None:
            raise ValidationError("a pinning book is missing its title")
        note = data.get("canon_note") or ""
        if not isinstance(note, str):
            raise ValidationError("a pinning book's note must be text")
        book = PinningBook(
            title=title, pins=tuple(pins),
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
                "the shipped example pinning book's title is "
                "not the pinned title")
        if book.pin_ids() != _EXAMPLE_PIN_IDS:
            raise ValidationError(
                "the shipped example's pins are not the "
                "pinned pins")
        panel = book.panel_for(_EXAMPLE_PANEL_ID)
        if tuple(r.pin_id for r in panel.rows) != _EXAMPLE_PANEL_ROW_IDS:
            raise ValidationError(
                "the shipped example panel does not name its "
                "pinned rows in panel order")
        if panel.account != _EXAMPLE_PANEL_ACCOUNT:
            raise ValidationError(
                "the shipped example panel does not carry its "
                "pinned account word-for-word")
        first = book.pins[0]
        if first.pin_id != _EXAMPLE_FIRST_PIN_ID \
                or first.subject != _EXAMPLE_FIRST_PIN_SUBJECT:
            raise ValidationError(
                "the shipped example's first pin is not "
                "its pinned pin of its pinned subject")
    return book


def build_book(book: Any = None, **kwargs: Any) -> PinningBook:
    """Build one validated book, from a mapping or field words."""
    if isinstance(book, PinningBook) and not kwargs:
        return book
    if isinstance(book, dict):
        if "schema" in book:
            return validate_book(book)
        merged: Dict[str, Any] = dict(book)
        merged.update(kwargs)
        return PinningBook(**merged)
    if book is None:
        return PinningBook(**kwargs)
    raise ValueError(f"a pinning book is needed, got {book!r}")


def _book_from(data: Any, *, require_example: bool) -> PinningBook:
    try:
        return validate_book(data, require_example=require_example)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def load_pinning_protection(
        data: Optional[Dict[str, Any]] = None) -> PinningBook:
    """Load and validate the shipped example book (or *data*).

    The shipped file is held to the example check: the
    pinned title, pins and panel - the M-158 slice
    boundary book - so the shipped book covers the
    canon this slice exists to hold.
    """
    raw = data if data is not None else load_resource(
        PINNING_PROTECTION_RESOURCE)
    return _book_from(raw, require_example=True)


def load_pinning_protection_file(path: Any) -> PinningBook:
    """Load and validate a pinning book from a file at *path*.

    Any file in the pinning-protection shape, anywhere
    on disk, validated whole - a malformed file raises
    :class:`ValidationError` naming the problem, and a
    missing file raises ``FileNotFoundError``. The
    example check is not held: a real book stands on
    its own pins.
    """
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _book_from(raw, require_example=False)


# ---------------------------------------------------------------------
# The registry model: one book held pin by pin.
# ---------------------------------------------------------------------


class PinningRegistry:
    """One session's pins, held one by one.

    The registry holds pins, never panels: the panel
    is a derivation, read off the whole held book at
    call time, so nothing here can hold a figure
    stale. A whole book is judged as a book judges
    it - its ids and its protected things against the
    whole book - before its pins are held in book
    order. A thing held here is pinned once: a second
    pin of a held kind and reference refuses.
    """

    def __init__(self, book: Any = None) -> None:
        self._title: Optional[str] = None
        self._pins: Dict[str, Pin] = {}
        self._pin_order: list = []
        self._next_pin = 1
        if book is not None:
            self.register_book(book)

    def _fresh_pin_id(self, held_ids: Any) -> str:
        while f"pin-{self._next_pin}" in held_ids:
            self._next_pin += 1
        fresh = f"pin-{self._next_pin}"
        self._next_pin += 1
        return fresh

    def _check_ref_free(self, pin: Pin) -> None:
        for held in self._pins.values():
            if held.kind == pin.kind and held.ref == pin.ref:
                raise ValueError(
                    f"the {pin.kind} standing as {pin.ref!r} "
                    f"is already pinned in this book - one "
                    f"thing is pinned once in a book")

    def register_pin(self, pin: Any) -> Pin:
        """Register one pin into the held book.

        A pin with no id is given a deterministic
        ``pin-N`` id. A pin id already standing here
        refuses, as does a pin of a thing a held pin
        already protects.
        """
        validated = _check_pin_ref(pin)
        if validated.pin_id is not None \
                and validated.pin_id in self._pins:
            raise ValueError(
                f"a pin named {validated.pin_id!r} "
                f"already exists")
        self._check_ref_free(validated)
        return self._hold_pin(validated)

    def _hold_pin(self, validated: Pin) -> Pin:
        """Hold one judged pin, in held order.

        The caller has already judged the pin against
        the held book (its id and its protected thing);
        this is the holding alone, with a deterministic
        ``pin-N`` id given to a pin carrying none.
        """
        if validated.pin_id is None:
            validated = replace(
                validated,
                pin_id=self._fresh_pin_id(set(self._pins)))
        self._pins[validated.pin_id] = validated
        self._pin_order.append(validated.pin_id)
        return validated

    def register_book(self, book: Any) -> PinningBook:
        """Register every pin of one book, in order.

        The first book held sets the title; a later
        book under a different title refuses, as does a
        book naming a held pin id or a held protected
        thing. The book is judged whole before anything
        is held, and the pins are then held in the
        book's own order. The book's panels are
        derivations, not holdings, and are not held.
        """
        validated = build_book(book)
        if self._title is not None and validated.title != self._title:
            raise ValueError(
                "this registry already holds a pinning book "
                "under a different title")
        for pin in validated.pins:
            if pin.pin_id in self._pins:
                raise ValueError(
                    f"a pin named {pin.pin_id!r} "
                    f"already exists")
            self._check_ref_free(pin)
        self._title = validated.title
        for pin in validated.pins:
            self._hold_pin(pin)
        return self.book()

    def get_pin(self, pin_id: Any) -> Pin:
        """The pin one id names among the held pins."""
        wanted = normalize_member_id(pin_id)
        if wanted not in self._pins:
            raise KeyError(f"unknown pin: {wanted!r}")
        return self._pins[wanted]

    def pin_for_ref(self, kind: Any, ref: Any) -> Pin:
        """The held pin protecting one standing thing."""
        wanted_kind = normalize_pin_kind(kind)
        wanted_ref = _check_word(ref, "a pin's reference")
        for pin_id in self._pin_order:
            pin = self._pins[pin_id]
            if pin.kind == wanted_kind and pin.ref == wanted_ref:
                return pin
        raise KeyError(
            f"no pin held protects the {wanted_kind} "
            f"standing as {wanted_ref!r}")

    def latest_pin(self) -> Pin:
        """The most recently held pin."""
        if not self._pin_order:
            raise ValueError("no pin is held yet")
        return self._pins[self._pin_order[-1]]

    def list_pins(self) -> Tuple[Pin, ...]:
        """Every held pin, in the order they were held."""
        return tuple(self._pins[item] for item in self._pin_order)

    def book(self) -> PinningBook:
        """The held pins as one validated book."""
        if self._title is None:
            raise ValueError("no pinning book is held yet")
        return PinningBook(
            title=self._title, pins=self.list_pins())

    def panel(self) -> PinningPanel:
        """Derive the pin panel of the whole held book."""
        return derive_panel(self)


# ---------------------------------------------------------------------
# The visible surface: what protection holds, read off any book.
# ---------------------------------------------------------------------


def pinned_refs(source: Any) -> Tuple[Tuple[str, str], ...]:
    """Every protected thing one source holds, in panel order.

    The visible list of protection: each held pin's
    kind and the reference it protects, in the order
    the derived panel shows them. *source* is a book
    or a registry.
    """
    panel = derive_panel(source)
    return tuple((row.kind, row.ref) for row in panel.rows)


def is_protected(source: Any, kind: Any, ref: Any) -> bool:
    """Whether one standing thing is pinned in *source*.

    The kind is read through the kind aliases; the
    reference is matched as it stands. An unpinned
    thing answers False - protection is declared,
    never guessed, and its absence is a plain answer,
    not a refusal.
    """
    wanted_kind = normalize_pin_kind(kind)
    wanted_ref = _check_word(ref, "a pin's reference")
    for pin in _held_pins(source):
        if pin.kind == wanted_kind and pin.ref == wanted_ref:
            return True
    return False


# ---------------------------------------------------------------------
# Pin news, shaped as session records.
# ---------------------------------------------------------------------


def pin_record(pin: Any) -> Dict[str, Any]:
    """The session-news record of one pin."""
    current = pin if isinstance(pin, Pin) \
        else build_pin(pin)
    record_out = current.to_record()
    record_out["news"] = True
    record_out["headline"] = (
        f"Pin protects \"{current.subject}\" "
        f"({current.kind} {current.ref}), pinned by "
        f"{current.pinned_by} on {current.pinned_on}.")
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
        f"Pin panel: {current.total_pins} pins - "
        f"every protected file and fact, visible.")
    return record_out


def book_record(book: Any) -> Dict[str, Any]:
    """The session-news record of one pinning book."""
    current = book if isinstance(book, PinningBook) \
        else build_book(book)
    record_out = current.to_record()
    record_out["news"] = True
    record_out["headline"] = (
        f"Pinning and protection {current.title}: "
        f"{record_out['pin_count']} pins held.")
    return record_out


def plain_words(pin: Any) -> str:
    """One pin, in one plain sentence."""
    current = pin if isinstance(pin, Pin) \
        else build_pin(pin)
    return (
        f"\"{current.subject}\" is pinned as a "
        f"{current.kind} ({current.ref}): "
        f"{current.why} It was pinned by "
        f"{current.pinned_by} on {current.pinned_on} "
        f"(read from {current.source}).")


def panel_plain_words(source: Any) -> str:
    """The pin panel in plain words, in full.

    Accepts a PinningPanel or a PinningBook (whose
    derived panel is told). The panel is told whole -
    its rows in panel order and its account.
    """
    if isinstance(source, PinningPanel):
        panel = validate_panel(source)
        title = None
    elif isinstance(source, PinningBook):
        panel = derive_panel(source)
        title = source.title
    else:
        raise ValueError(
            f"a pinning-protection source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    lines.append("Pins, in panel order:")
    for row in panel.rows:
        lines.append(
            f"{row.pin_id}: \"{row.subject}\" - "
            f"a {row.kind} ({row.ref}), pinned by "
            f"{row.pinned_by} on {row.pinned_on}")
    lines.extend(panel.account)
    return "\n".join(lines)


# ---------------------------------------------------------------------
# Screens: the formatters and the /pins grammar.
# ---------------------------------------------------------------------


def _source_book(source: Any) -> PinningBook:
    if source is None:
        return load_pinning_protection()
    if isinstance(source, PinningRegistry):
        return source.book()
    if isinstance(source, PinningBook):
        return source
    raise ValueError(f"a pinning book is needed, got {source!r}")


def format_pin(pin: Any) -> str:
    """One pin as a screen block, provenance whole."""
    current = pin if isinstance(pin, Pin) \
        else build_pin(pin)
    lines = [
        f"{current.pin_id or '-'}: \"{current.subject}\" - "
        f"a {current.kind} ({current.ref}), pinned by "
        f"{current.pinned_by} on {current.pinned_on}",
        f"Why it is protected: {current.why}",
        f"(read from {current.source})",
        "This pin declares protection as data - it "
        "compacts nothing and drops nothing itself.",
    ]
    return "\n".join(lines)


def format_pins(source: Any = None, kind: Any = None) -> str:
    """Pins of one book, in held order.

    With *kind* named, only the pins of that kind
    stand - read through the kind aliases, so a kind
    nothing holds shows its own empty line.
    """
    book = _source_book(source)
    wanted = normalize_pin_kind(kind) if kind is not None else None
    lines = [
        f"{item.pin_id or '-'}: \"{item.subject}\" - "
        f"a {item.kind} ({item.ref}), pinned by "
        f"{item.pinned_by}"
        for item in book.pins
        if wanted is None or item.kind == wanted]
    if not lines:
        lines.append("No pins are held.")
    return "\n".join(lines)


def format_panel(source: Any = None) -> str:
    """The pin panel as a screen block: every row and the account.

    Accepts a PinningPanel or a PinningBook; a book
    shows the panel it derives.
    """
    if isinstance(source, PinningPanel):
        panel = validate_panel(source)
        lines: list = []
    else:
        book = _source_book(source)
        if not book.pins:
            return (f"Pin panel in {book.title}:\n"
                    f"No pins are held.")
        panel = derive_panel(book)
        lines = [f"Pin panel in {book.title}:"]
    lines.append("Pins, in panel order:")
    for row in panel.rows:
        lines.append(
            f"{row.pin_id}: \"{row.subject}\" - "
            f"a {row.kind} ({row.ref}), pinned by "
            f"{row.pinned_by} on {row.pinned_on}")
    lines.extend(panel.account)
    return "\n".join(lines)


def format_pinning_protection_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /pins.

    With nothing named, the shipped example pinning
    book is shown - the example this slice ships - so
    the screen is never empty.
    """
    book = _source_book(source)
    lines = ["Pinning and Protection (M-159) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_pins(book))
    lines.append("")
    lines.append(format_panel(book))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_pin_args(args: Any) -> Tuple[str, Any]:
    """Parse the /pins grammar both surfaces share.

    No words (or ``show`` / ``list``) shows the pinning
    book; ``pin <pin-id>`` shows one pin with its
    provenance whole; ``kind <kind>`` shows the pins
    of one kind, the kind read through the kind
    aliases; ``panel`` shows the pin panel derived
    from the whole book. Anything else is a usage
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
    if head == "panel" and len(words) == 1:
        return (head, None)
    if head == "pin" and len(words) == 2:
        try:
            return (head, normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "kind" and len(words) == 2:
        try:
            return (head, normalize_pin_kind(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
