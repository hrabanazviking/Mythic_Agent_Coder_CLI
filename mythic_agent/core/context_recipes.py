"""Context recipes (All-Features roadmap slice M-158).

Part VII continues. The roadmap's words:
``saved bundles ("the auth stack", "the Mojo build")
summonable by name into any session.``

What already shipped, and what this slice adds:

* Context already ships as data in the memory
  holdings: the project memory map
  (``core/project_memory_map.py``, M-150), session
  memory across days (``core/session_memory.py``,
  M-153), cross-project memory
  (``core/cross_project_memory.py``, M-154), the
  self-improving ledger
  (``core/self_improving_ledger.py``, M-155),
  decision records (``core/decision_records.py``,
  M-156) and the forget journal
  (``core/forget_quarantine.py``, M-157), with crew
  memory (``core/crew_memory.py``, M-133) beside
  them. Each holding answers through its own roads.
  What no shipped layer holds is the saved bundle
  itself: a named set of pieces - "the auth stack",
  "the Mojo build" - that a session can summon by
  name, so the same working context is named once
  and brought back whole, by its name, in any
  session.
* This slice is that bundle, as a pure layer: a
  context recipe is one named saved bundle,
  validated as data WITH ITS PROVENANCE WHOLE - the
  session it was saved in, the day, and where it was
  read from - whose pieces are the shipped holdings'
  own pieces read onto this layer BY IMPORT and
  judged by each holding's own validation. The
  shipped data file
  (``mythic_agent/data/context_recipes.yaml``) holds
  one example book in exactly the shape a real book
  file takes, a loader reads a book file anywhere on
  disk, the recipe panel is DERIVED from the whole
  book (every recipe standing whole, in a settled
  order), recipes are shaped as session news, and a
  small in-memory registry model holds recipes one
  by one. The agent layer owns holding a book for a
  session, bundling the session's carried memory
  into a recipe, and summoning a recipe by name.

Honesty rules, enforced here and pinned by tests:

* **A name summons one bundle, never two.** A book
  holds at most one recipe under one name: two
  recipes sharing a name (in any letter case) refuse,
  in a book and in the registry alike, so a name
  spoken in a session can never be ambiguous.
* **Composed, never duplicated.** A recipe's pieces
  are the shipped holdings' own pieces - session-
  memory notes, cross-project lessons, ledger
  candidates, decision records, memory-map entries
  and crew memory entries - read onto this layer by
  import and judged by each layer's own validation.
  No second taxonomy of context is invented here:
  the piece kinds are the shipped holdings' own
  names. A piece stands in a recipe by its kind and
  the reference it stands under in its holding, with
  the plain-words reason it belongs in the bundle;
  the piece itself is never copied into the recipe.
* **No piece twice in one bundle.** One recipe names
  one piece once: the same kind and reference named
  twice in one recipe refuses. The same piece may
  stand in many recipes - bundles overlap freely.
* **The panel is derived, never stored loose.** Its
  rows are the book's recipes carried whole, in
  settled order (by recipe name, then recipe id), its
  totals are the recipes' own counts and its kind
  counts the pieces' own tallies; a stored panel or
  book whose rows, totals, counts or account disagree
  with the derived shape refuses.
* **Data only - summoning assembles nothing.** A
  recipe here is validated data about a saved bundle:
  no model is called, no live context is assembled,
  no code is edited, no workspace file is touched,
  and nothing persists beyond the session journal
  news the agent layer publishes. Summoning a recipe
  names the bundle and its pieces, whole; what a
  session does with those pieces is the session's own
  roads, never this layer's.
* **Malformed refuses.** A duplicate recipe id or
  recipe name in one book, the same piece named twice
  in one recipe, a recipe with no pieces, a recipe
  with no provenance, and unknown keys in a recipe, a
  panel or a book mapping all raise instead of being
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
    "CONTEXT_RECIPES_RESOURCE",
    "CONTEXT_RECIPES_SCHEMA",
    "CONTEXT_RECIPES_SLICE",
    "PLAIN_EXPLANATION",
    "RECIPE_ITEM_KINDS",
    "USAGE",
    "ContextRecipe",
    "ContextRecipeBook",
    "ContextRecipePanel",
    "ContextRecipeRegistry",
    "RecipeItem",
    "RecipeKindCount",
    "RecipePanelRow",
    "book_record",
    "build_book",
    "build_item",
    "build_panel",
    "build_recipe",
    "build_row",
    "derive_panel",
    "format_context_recipes_screen",
    "format_panel",
    "format_recipe",
    "format_recipes",
    "format_summon",
    "inspect_piece",
    "item_from_cross_project",
    "item_from_decision_record",
    "item_from_ledger_candidate",
    "item_from_memory_map",
    "item_from_session_memory",
    "items_from_memory_map",
    "items_from_session_memory",
    "load_context_recipes",
    "load_context_recipes_file",
    "normalize_item_kind",
    "panel_plain_words",
    "panel_record",
    "parse_recipe_args",
    "plain_words",
    "recipe_record",
    "validate_book",
    "validate_item",
    "validate_panel",
    "validate_recipe",
    "validate_row",
]

CONTEXT_RECIPES_SLICE = "M-158"

#: The packaged data resource holding the example book.
CONTEXT_RECIPES_RESOURCE = "context_recipes.yaml"

#: The schema word a context-recipes file must carry.
CONTEXT_RECIPES_SCHEMA = "mythic.context_recipes/1"

#: The kinds of piece one recipe may bundle: the
#: shipped holdings' own names - a fact carried in
#: session memory across days (``session-memory``),
#: a lesson shared between projects
#: (``cross-project``), a candidate in the
#: self-improving ledger (``ledger-candidate``), a
#: choice held as a decision record
#: (``decision-record``), a fact in the project
#: memory map (``memory-map``), or an entry in a crew
#: member's notebook (``crew-memory``). No other kind
#: is bundled here.
RECIPE_ITEM_KINDS = (
    "session-memory", "cross-project", "ledger-candidate",
    "decision-record", "memory-map", "crew-memory")

_KIND_ALIASES = {
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

_ITEM_KEYS = frozenset({
    "kind", "memory_class", "class",
    "ref", "memory_ref", "reference",
    "why", "note", "reason",
})

_RECIPE_KEYS = frozenset({
    "recipe_id", "id", "name", "title",
    "purpose", "why", "description",
    "items", "pieces",
    "session_ref", "session",
    "created_on", "day", "date",
    "source",
})

_ROW_KEYS = frozenset({
    "recipe_id", "id", "name", "purpose",
    "session_ref", "piece_count", "pieces", "kinds",
})

_KIND_COUNT_KEYS = frozenset({"kind", "items", "count"})

_PANEL_KEYS = frozenset({
    "panel_id", "id", "rows", "recipes",
    "total_items", "total", "total_pieces",
    "kind_counts", "kinds",
    "account", "statements",
})

_BOOK_KEYS = frozenset({"title", "name"})

_RECIPE_BOOK_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "canon_note", "guide", "recipes", "panels",
})

#: The shipped example book's title, held to this
#: by the loader's example check.
_EXAMPLE_TITLE = "Context recipes at the M-157 slice boundary"

#: The shipped example's recipe ids, in held order,
#: pinned by the loader.
_EXAMPLE_RECIPE_IDS = (
    "recipe-auth-stack", "recipe-mojo-build",
    "recipe-provider-ocean")

#: The shipped example's first recipe and the name
#: it is summoned by, pinned by the loader.
_EXAMPLE_FIRST_RECIPE_ID = "recipe-auth-stack"

_EXAMPLE_FIRST_RECIPE_NAME = "the auth stack"

#: The shipped example's one panel id, and its rows
#: in panel order, pinned by the loader.
_EXAMPLE_PANEL_ID = "panel-m157-boundary"

_EXAMPLE_PANEL_ROW_IDS = (
    "recipe-auth-stack", "recipe-mojo-build",
    "recipe-provider-ocean")

_EXAMPLE_PANEL_ACCOUNT = (
    "The recipe panel holds 3 recipes bundling 8 "
    "pieces: cross-project 2, decision-record 2, "
    "ledger-candidate 1, memory-map 2, session-memory 1.",
    "Recipes stand by name, then recipe id - so two "
    "panels of one book diff cleanly, line by line.",
    "Every recipe is summoned by its name alone, and "
    "no name in a book names two recipes - a name "
    "spoken in a session is never ambiguous.",
    "The panel is read off the book at call time - "
    "it is derived, never stored loose.",
)

PLAIN_EXPLANATION = (
    "Context recipes: saved bundles of context - "
    "\"the auth stack\", \"the Mojo build\" - "
    "summonable by name into any session. A recipe is "
    "one named bundle carried with its provenance "
    "whole - the session it was saved in, the day, "
    "and where it was read from - whose pieces are "
    "the shipped memory holdings' own pieces, named "
    "by kind and reference with the reason each "
    "belongs. The recipe panel is derived from the "
    "book at call time: every recipe standing whole, "
    "by name, then recipe id. This layer holds "
    "recipes as data only: it calls no model, "
    "assembles no live context, edits no code, "
    "writes no project files and persists nothing."
)

USAGE = (
    "Usage: /recipes, /recipes show, "
    "/recipes recipe <recipe-id>, "
    "/recipes summon <recipe name>, "
    "/recipes panel"
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
        raise ValueError(f"a recipe names two different {what}")
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
    text = _clean_text(value, "a recipe's created-on day")
    try:
        parsed = date.fromisoformat(text)
    except ValueError:
        raise ValueError(
            f"a recipe's created-on day must be an ISO "
            f"date (YYYY-MM-DD), got {text!r}") from None
    if parsed.isoformat() != text:
        raise ValueError(
            f"a recipe's created-on day must be an ISO "
            f"date (YYYY-MM-DD), got {text!r}")
    return text


def normalize_item_kind(value: Any) -> str:
    """The canonical piece kind a word names.

    A kind is one of :data:`RECIPE_ITEM_KINDS` - the
    shipped holdings' own names - read
    case-insensitively, with the holdings' short
    faces (``session``, ``cross``, ``ledger``,
    ``decision``, ``map``, ``crew`` and their command
    faces) read onto them. Anything else raises,
    plainly naming the six.
    """
    if isinstance(value, str):
        wanted = _KIND_ALIASES.get(value.strip().lower())
        if wanted is not None:
            return wanted
    raise ValueError(
        "a piece kind must be one of %s, got %r"
        % ("/".join(RECIPE_ITEM_KINDS), value))


# ---------------------------------------------------------------------
# The recipe item: one shipped piece named into a bundle.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class RecipeItem:
    """One piece named into a recipe, by kind and reference.

    ``kind`` is the piece's holding, one of the
    shipped holdings' own names; ``ref`` is the
    reference (id) the piece stands under in its
    holding; ``why`` is the plain-words reason this
    piece belongs in the bundle. The piece itself is
    never copied here: a recipe names pieces, and the
    holdings keep them.
    """

    kind: str
    ref: str
    why: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "kind", normalize_item_kind(self.kind))
        object.__setattr__(
            self, "ref",
            _check_word(self.ref, "an item's piece reference"))
        object.__setattr__(
            self, "why",
            _check_long_text(self.why, "an item's reason"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "ref": self.ref,
            "why": self.why,
        }


def _check_item_ref(value: Any) -> RecipeItem:
    if isinstance(value, RecipeItem):
        return value
    if isinstance(value, dict):
        return validate_item(value)
    raise ValueError(f"a recipe item is needed, got {value!r}")


def validate_item(item: Any) -> RecipeItem:
    """Validate one recipe item into a RecipeItem.

    Accepts an item or a mapping naming a ``kind``
    (or ``memory_class`` / ``class``), a ``ref`` (or
    ``memory_ref`` / ``reference``) and a ``why`` (or
    ``note`` / ``reason``). Unknown keys refuse.
    """
    if isinstance(item, RecipeItem):
        return item
    if not isinstance(item, dict):
        raise ValueError(f"a recipe item must be a mapping, got {item!r}")
    unknown = set(item) - _ITEM_KEYS
    if unknown:
        raise ValueError(
            "unknown item keys: %s" % ", ".join(sorted(unknown)))

    def _needed(spellings: Tuple[str, ...], what: str) -> Any:
        value = _pick_any(item, spellings, what)
        if value is None:
            raise ValueError(f"a recipe item is missing its {what}")
        return value

    return RecipeItem(
        kind=_needed(("kind", "memory_class", "class"), "piece kind"),
        ref=_needed(("ref", "memory_ref", "reference"),
                    "piece reference"),
        why=_needed(("why", "note", "reason"), "reason"))


def build_item(item: Any = None, **kwargs: Any) -> RecipeItem:
    """Build one validated item, from a mapping or field words."""
    if isinstance(item, RecipeItem) and not kwargs:
        return item
    if isinstance(item, dict) or item is None:
        merged: Dict[str, Any] = {}
        if isinstance(item, dict):
            merged.update(item)
        merged.update(kwargs)
        return validate_item(merged)
    raise ValueError(f"a recipe item must be a mapping, got {item!r}")


def _item_for(kind: str, ref: Optional[str], *, why: Any) -> RecipeItem:
    """One item for one shipped piece, by kind and reference alone.

    The piece's own words are never read here: only
    its kind and the reference it stands under. The
    reason the piece belongs is named beside it - a
    piece bundled for no named reason refuses. A
    piece with no reference refuses: a recipe must
    name which standing thing it bundles.
    """
    if why is None:
        raise ValueError(
            "a recipe item must carry its reason: why this "
            "piece belongs in the bundle - nothing is "
            "bundled for no named reason")
    if ref is None or (isinstance(ref, str) and not ref.strip()):
        raise ValueError(
            "a recipe item names the reference the piece "
            "stood under - a piece with no reference cannot "
            "be bundled, by kind alone or otherwise")
    return RecipeItem(kind=kind, ref=ref, why=why)


def inspect_piece(piece: Any) -> Dict[str, Any]:
    """Inspect one shipped piece: its kind and reference only.

    The piece is judged by the layer that owns its
    type, never by whichever validator happens to
    accept its shape first - exactly as the forget
    journal's inspection road judges. A piece with no
    reference, or a value no shipped layer owns,
    refuses.
    """
    if isinstance(piece, RecipeItem):
        return {"kind": piece.kind, "ref": piece.ref}
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
    for kind_type, validator, kind, attr in owned:
        if isinstance(piece, kind_type):
            validated = validator(piece)
            ref = getattr(validated, attr, None)
            if ref is None or (
                    isinstance(ref, str) and not ref.strip()):
                raise ValueError(
                    "an inspected piece names the reference "
                    "it stands under - this piece carries none")
            return {"kind": kind, "ref": ref}
    if isinstance(piece, dict):
        if "kind" in piece and "ref" in piece:
            checked = validate_item(piece)
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
            return {"kind": kind, "ref": ref}
    raise ValueError(
        f"no shipped layer owns this piece, got {piece!r}")


def item_from_session_memory(note: Any, *, why: Any) -> RecipeItem:
    """Build one item from a shipped session-memory carried note.

    The note - session memory's own record, judged by
    that layer's own validation - is read onto an item
    BY IMPORT by its kind and reference alone: its id
    stands as the item's reference. Its title and
    detail are never read here. The reason the note
    belongs in the bundle is named beside it.
    """
    validated = _validate_note(note)
    return _item_for("session-memory", validated.note_id, why=why)


def item_from_cross_project(lesson: Any, *, why: Any) -> RecipeItem:
    """Build one item from a shipped cross-project shared lesson.

    The lesson - cross-project memory's own record,
    judged by that layer's own validation - is read
    onto an item BY IMPORT by its kind and reference
    alone. Its title, detail and evidence are never
    read here. The reason is named beside it, exactly
    as for a note.
    """
    validated = _validate_lesson(lesson)
    return _item_for("cross-project", validated.lesson_id, why=why)


def item_from_ledger_candidate(candidate: Any, *, why: Any) -> RecipeItem:
    """Build one item from a shipped self-improving ledger candidate.

    The candidate - the ledger's own record, judged by
    that layer's own validation - is read onto an item
    BY IMPORT by its kind and reference alone. Its
    title and detail are never read here. The reason
    is named beside it, exactly as for a note.
    """
    validated = _validate_candidate(candidate)
    return _item_for(
        "ledger-candidate", validated.candidate_id, why=why)


def item_from_decision_record(record: Any, *, why: Any) -> RecipeItem:
    """Build one item from a shipped decision record.

    The record - decision records' own record, judged
    by that layer's own validation - is read onto an
    item BY IMPORT by its kind and reference alone.
    Its title, decision and rationale are never read
    here. The reason is named beside it, exactly as
    for a note.
    """
    validated = _validate_decision(record)
    return _item_for("decision-record", validated.record_id, why=why)


def item_from_memory_map(entry: Any, *, why: Any) -> RecipeItem:
    """Build one item from a shipped project memory-map entry.

    The entry - the memory map's own record, judged by
    the map's own validation - is read onto an item BY
    IMPORT by its kind and reference alone: any section
    of the map may be bundled into a recipe, so no
    section is refused here. Its title and detail are
    never read here. The reason is named beside it,
    exactly as for a note.
    """
    validated = _validate_map_entry(entry)
    return _item_for("memory-map", validated.entry_id, why=why)


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


def items_from_session_memory(source: Any, *, why: Any
                              ) -> Tuple[RecipeItem, ...]:
    """Items read off the shipped session memory.

    The carried notes of a session situation - or of a
    whole session-memory book or registry - are read
    onto items BY IMPORT, judged by session memory's
    own validation on the way, under one named reason.
    Every note's title and detail stay in session
    memory: only ids cross.
    """
    return tuple(
        item_from_session_memory(note, why=why)
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


def items_from_memory_map(source: Any, *, why: Any
                          ) -> Tuple[RecipeItem, ...]:
    """Items read off the shipped project memory map.

    The map's entries - every section, for any fact of
    the project may be bundled into a recipe - are read
    onto items BY IMPORT, judged by the map's own
    validation on the way, under one named reason,
    exactly as for session memory. Only ids cross.
    """
    return tuple(
        item_from_memory_map(entry, why=why)
        for entry in _map_entries(source))


# ---------------------------------------------------------------------
# The context recipe: one named saved bundle, provenance whole.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class ContextRecipe:
    """One named saved bundle of context pieces.

    ``name`` is the name the bundle is summoned by -
    ``the auth stack``, ``the Mojo build`` - plain
    words a session speaks; ``purpose`` is what the
    bundle is for, in plain words; ``items`` are the
    bundle's pieces, each naming one shipped piece by
    kind and reference with the reason it belongs. The
    provenance stands whole beside the bundle:
    ``session_ref`` names the session it was saved in,
    ``created_on`` is the day, and ``source`` names
    where it was read from. A recipe with any
    provenance word missing, with no pieces, or with
    one piece named twice is no recipe at all.
    """

    name: str
    purpose: str
    items: Tuple[RecipeItem, ...]
    session_ref: str
    created_on: str
    source: str
    recipe_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.recipe_id is not None:
            object.__setattr__(
                self, "recipe_id",
                normalize_member_id(self.recipe_id))
        object.__setattr__(
            self, "name", _check_title(self.name, "a recipe's name"))
        object.__setattr__(
            self, "purpose",
            _check_long_text(self.purpose, "a recipe's purpose"))
        if isinstance(self.items, (str, bytes)) \
                or not isinstance(self.items, (list, tuple)):
            raise ValueError(
                f"a recipe's items must be a list of items, "
                f"got {self.items!r}")
        items = tuple(_check_item_ref(item) for item in self.items)
        if not items:
            raise ValueError("a recipe bundles at least one piece")
        seen = set()
        for item in items:
            key = (item.kind, item.ref)
            if key in seen:
                raise ValueError(
                    f"the {item.kind} piece {item.ref!r} is "
                    f"already named in this recipe")
            seen.add(key)
        object.__setattr__(self, "items", items)
        object.__setattr__(
            self, "session_ref",
            _check_word(self.session_ref, "a recipe's session"))
        object.__setattr__(
            self, "created_on", _check_day(self.created_on))
        object.__setattr__(
            self, "source",
            _check_title(self.source, "a recipe's source"))

    @property
    def piece_count(self) -> int:
        """How many pieces this recipe bundles (derived)."""
        return len(self.items)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "context_recipe",
            "slice": CONTEXT_RECIPES_SLICE,
            "recipe_id": self.recipe_id,
            "name": self.name,
            "purpose": self.purpose,
            "items": [item.to_record() for item in self.items],
            "session_ref": self.session_ref,
            "created_on": self.created_on,
            "source": self.source,
        }


def _check_recipe_ref(value: Any) -> ContextRecipe:
    if isinstance(value, ContextRecipe):
        return value
    if isinstance(value, dict):
        return validate_recipe(value)
    raise ValueError(f"a context recipe is needed, got {value!r}")


def validate_recipe(recipe: Any) -> ContextRecipe:
    """Validate one context recipe into a ContextRecipe.

    Accepts a recipe or a mapping naming a ``name``
    (or ``title``), a ``purpose`` (or ``why`` /
    ``description``), an ``items`` list (or
    ``pieces``), a ``session_ref`` (or ``session``), a
    ``created_on`` (or ``day`` / ``date``), a
    ``source`` and an optional ``recipe_id`` (or
    ``id``). Naming two spellings of one field with
    different values refuses, and unknown keys refuse.
    A shipped memory piece is not a recipe: pieces
    become a recipe only through the item roads, with
    the bundle's own frame words named with them.
    """
    if isinstance(recipe, ContextRecipe):
        return recipe
    if not isinstance(recipe, dict):
        raise ValueError(
            f"a context recipe must be a mapping, got {recipe!r}")
    unknown = set(recipe) - _RECIPE_KEYS
    if unknown:
        raise ValueError(
            "unknown recipe keys: %s" % ", ".join(sorted(unknown)))

    def _needed(spellings: Tuple[str, ...], what: str) -> Any:
        value = _pick_any(recipe, spellings, what)
        if value is None:
            raise ValueError(f"a context recipe is missing its {what}")
        return value

    kwargs: Dict[str, Any] = {
        "name": _needed(("name", "title"), "name"),
        "purpose": _needed(
            ("purpose", "why", "description"), "purpose"),
        "items": _needed(("items", "pieces"), "items"),
        "session_ref": _needed(("session_ref", "session"), "session"),
        "created_on": _needed(
            ("created_on", "day", "date"), "created-on day"),
        "source": _needed(("source",), "source"),
    }
    named_id = _pick_any(recipe, ("recipe_id", "id"), "recipe ids")
    if named_id is not None:
        kwargs["recipe_id"] = named_id
    return ContextRecipe(**kwargs)


def build_recipe(recipe: Any = None, **kwargs: Any) -> ContextRecipe:
    """Build one validated recipe, from a mapping or field words."""
    if isinstance(recipe, ContextRecipe) and not kwargs:
        return recipe
    if isinstance(recipe, dict) or recipe is None:
        merged: Dict[str, Any] = {}
        if isinstance(recipe, dict):
            merged.update(recipe)
        merged.update(kwargs)
        return validate_recipe(merged)
    raise ValueError(
        f"a context recipe must be a mapping, got {recipe!r}")


# ---------------------------------------------------------------------
# The recipe panel: every recipe carried whole, derived.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class RecipePanelRow:
    """One recipe carried whole into the panel.

    ``recipe_id`` names the recipe; ``name`` is the
    name it is summoned by; ``purpose`` is what the
    bundle is for; ``session_ref`` is the recipe's
    provenance head - the session it was saved in;
    ``piece_count`` is the recipe's own piece count;
    ``kinds`` are the kinds of its pieces, in bundle
    order, each named once per piece it stands for.
    :func:`validate_row` judged against its recipe
    refuses a row whose fields disagree with the row
    they derive.
    """

    recipe_id: str
    name: str
    purpose: str
    session_ref: str
    piece_count: int
    kinds: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "recipe_id", normalize_member_id(self.recipe_id))
        object.__setattr__(
            self, "name", _check_title(self.name, "a row's name"))
        object.__setattr__(
            self, "purpose",
            _check_long_text(self.purpose, "a row's purpose"))
        object.__setattr__(
            self, "session_ref",
            _check_word(self.session_ref, "a row's session"))
        object.__setattr__(
            self, "piece_count",
            _check_count(self.piece_count, "a row's piece count"))
        if isinstance(self.kinds, (str, bytes)) \
                or not isinstance(self.kinds, (list, tuple)):
            raise ValueError(
                f"a row's kinds must be a list of kinds, "
                f"got {self.kinds!r}")
        kinds = tuple(normalize_item_kind(k) for k in self.kinds)
        if len(kinds) != self.piece_count:
            raise ValueError(
                "a row's kinds must name one kind per piece "
                "the recipe bundles")
        object.__setattr__(self, "kinds", kinds)

    @property
    def sort_key(self) -> Tuple[str, str]:
        """This row's place in panel order (derived).

        Rows stand by recipe name, then recipe id.
        """
        return (self.name.lower(), self.recipe_id)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "context_recipe_panel_row",
            "slice": CONTEXT_RECIPES_SLICE,
            "recipe_id": self.recipe_id,
            "name": self.name,
            "purpose": self.purpose,
            "session_ref": self.session_ref,
            "piece_count": self.piece_count,
            "kinds": list(self.kinds),
        }


def _row_for_recipe(recipe: ContextRecipe) -> RecipePanelRow:
    return RecipePanelRow(
        recipe_id=recipe.recipe_id, name=recipe.name,
        purpose=recipe.purpose, session_ref=recipe.session_ref,
        piece_count=len(recipe.items),
        kinds=tuple(item.kind for item in recipe.items))


def _check_row_ref(value: Any) -> RecipePanelRow:
    if isinstance(value, RecipePanelRow):
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

        return RecipePanelRow(
            recipe_id=_needed(("recipe_id", "id"), "recipe id"),
            name=_needed(("name",), "name"),
            purpose=_needed(("purpose",), "purpose"),
            session_ref=_needed(("session_ref",), "session"),
            piece_count=_needed(
                ("piece_count", "pieces"), "piece count"),
            kinds=_needed(("kinds",), "kinds"))
    raise ValueError(f"a panel row is needed, got {value!r}")


def validate_row(row: Any, recipe: Any = None) -> RecipePanelRow:
    """Validate one panel row into a RecipePanelRow.

    Accepts a row or a mapping naming a ``recipe_id``
    (or ``id``), a ``name``, a ``purpose``, a
    ``session_ref``, a ``piece_count`` (or ``pieces``)
    and its ``kinds``. With *recipe* given, the row is
    judged against the row derived from that recipe: a
    stored row whose fields disagree with the derived
    row refuses.
    """
    current = _check_row_ref(row)
    if recipe is not None:
        checked_recipe = _check_recipe_ref(recipe)
        derived = _row_for_recipe(checked_recipe)
        if current != derived:
            raise ValueError(
                "a stored row disagrees with the row "
                "derived from its recipe")
    return current


def build_row(row: Any = None, recipe: Any = None,
              **kwargs: Any) -> RecipePanelRow:
    """Build one validated row, from a mapping or field words."""
    if isinstance(row, RecipePanelRow) and not kwargs:
        return validate_row(row, recipe)
    if isinstance(row, dict) or row is None:
        merged: Dict[str, Any] = {}
        if isinstance(row, dict):
            merged.update(row)
        merged.update(kwargs)
        return validate_row(merged, recipe)
    return validate_row(row, recipe)


@dataclass(frozen=True)
class RecipeKindCount:
    """One kind's count in a panel: its pieces tallied."""

    kind: str
    items: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "kind", normalize_item_kind(self.kind))
        object.__setattr__(
            self, "items",
            _check_count(self.items, "a kind count's items"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "items": self.items,
        }


def _check_kind_count_ref(value: Any) -> RecipeKindCount:
    if isinstance(value, RecipeKindCount):
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
        return RecipeKindCount(kind=kind, items=items)
    raise ValueError(f"a kind count is needed, got {value!r}")


def _panel_account(total_items: int, total_pieces: int,
                   kind_counts: Tuple[RecipeKindCount, ...]
                   ) -> Tuple[str, ...]:
    tallies = ", ".join(
        f"{count.kind} {count.items}"
        for count in sorted(
            kind_counts, key=lambda count: count.kind))
    return (
        f"The recipe panel holds {total_items} recipes "
        f"bundling {total_pieces} pieces: {tallies}.",
        "Recipes stand by name, then recipe id - so two "
        "panels of one book diff cleanly, line by line.",
        "Every recipe is summoned by its name alone, and "
        "no name in a book names two recipes - a name "
        "spoken in a session is never ambiguous.",
        "The panel is read off the book at call time - "
        "it is derived, never stored loose.",
    )


@dataclass(frozen=True)
class ContextRecipePanel:
    """The recipe panel of one book, derived from the whole book.

    ``rows`` are the book's recipes carried whole, in
    panel order (by recipe name, then recipe id, so two
    panels of one book diff cleanly); ``total_items``
    is the recipe count and ``total_pieces`` the rows'
    own piece counts summed; ``kind_counts`` are the
    per-kind tallies of every piece in the book, in the
    order their kinds first appear in the panel;
    ``account`` is read off those numbers. A panel
    whose rows stand out of panel order, or whose
    totals are not its own rows' counts, refuses at
    construction; :func:`validate_panel` judged against
    a book refuses a stored panel that disagrees with
    the derived one.
    """

    rows: Tuple[RecipePanelRow, ...] = ()
    total_items: int = 0
    total_pieces: int = 0
    kind_counts: Tuple[RecipeKindCount, ...] = ()
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
            if row.recipe_id in seen:
                raise ValueError(
                    f"a panel row for recipe {row.recipe_id!r} "
                    f"already exists")
            seen.add(row.recipe_id)
        keys = [row.sort_key for row in rows]
        if keys != sorted(keys):
            raise ValueError(
                "a panel's rows must stand in panel order "
                "(by recipe name, then recipe id)")
        object.__setattr__(self, "rows", rows)
        object.__setattr__(
            self, "total_pieces",
            _check_count(self.total_pieces, "a panel's total pieces"))
        if self.total_pieces != sum(r.piece_count for r in rows):
            raise ValueError(
                "a panel's total pieces must be its own "
                "rows' piece counts")
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
        if sum(c.items for c in kind_counts) != self.total_pieces:
            raise ValueError(
                "a panel's kind counts must sum to its own "
                "total pieces")
        tallies: Dict[str, int] = {}
        for row in rows:
            for kind in row.kinds:
                tallies[kind] = tallies.get(kind, 0) + 1
        for count in kind_counts:
            if count.items != tallies.get(count.kind, 0):
                raise ValueError(
                    "a panel's kind counts must be its own "
                    "rows' counts")
        if set(tallies) != {c.kind for c in kind_counts}:
            raise ValueError(
                "a panel's kind counts must name every kind "
                "its rows carry")
        object.__setattr__(self, "account", _check_account(self.account))

    def row_for(self, recipe_id: Any) -> RecipePanelRow:
        """The panel row one recipe names in this panel."""
        wanted = normalize_member_id(recipe_id)
        for row in self.rows:
            if row.recipe_id == wanted:
                return row
        raise KeyError(f"no row in the panel: recipe {wanted!r}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "context_recipe_panel",
            "slice": CONTEXT_RECIPES_SLICE,
            "panel_id": self.panel_id,
            "rows": [row.to_record() for row in self.rows],
            "total_items": self.total_items,
            "total_pieces": self.total_pieces,
            "kind_counts": [c.to_record() for c in self.kind_counts],
            "account": list(self.account),
        }


def _held_recipes(source: Any) -> Tuple[ContextRecipe, ...]:
    """The recipes one source holds, in held order."""
    if isinstance(source, ContextRecipeBook):
        return source.recipes
    if isinstance(source, ContextRecipeRegistry):
        return source.list_recipes()
    if isinstance(source, (list, tuple)):
        return tuple(_check_recipe_ref(item) for item in source)
    raise ValueError(f"context recipes are needed, got {source!r}")


def derive_panel(source: Any) -> ContextRecipePanel:
    """Derive the recipe panel from one book.

    The rows are the book's recipes carried whole, in
    panel order: by recipe name, then recipe id.
    *source* is a book or a registry. A source holding
    no recipe refuses - a panel of nothing is no panel.
    """
    recipes = _held_recipes(source)
    if not recipes:
        raise ValueError("a panel needs at least one recipe")
    rows = []
    for recipe in recipes:
        if recipe.recipe_id is None:
            raise ValueError(
                "a panel row must name its recipe - a "
                "recipe with no id refuses derivation")
        rows.append(_row_for_recipe(recipe))
    rows = tuple(sorted(rows, key=lambda r: r.sort_key))
    order: list = []
    tally: Dict[str, int] = {}
    for row in rows:
        for kind in row.kinds:
            if kind not in tally:
                tally[kind] = 0
                order.append(kind)
            tally[kind] += 1
    kind_counts = tuple(
        RecipeKindCount(kind=kind, items=tally[kind])
        for kind in order)
    total_pieces = sum(row.piece_count for row in rows)
    return ContextRecipePanel(
        rows=rows, total_items=len(rows),
        total_pieces=total_pieces,
        kind_counts=kind_counts,
        account=_panel_account(len(rows), total_pieces, kind_counts))


def validate_panel(panel: Any, source: Any = None
                   ) -> ContextRecipePanel:
    """Validate one panel into a ContextRecipePanel.

    Accepts a panel or a mapping naming ``rows`` (or
    ``recipes``), a ``total_items`` (or ``total``), a
    ``total_pieces``, ``kind_counts`` (or ``kinds``), an
    ``account`` (or ``statements``) and an optional
    ``panel_id`` (or ``id``). With *source* given (a
    book), the panel is judged against the panel derived
    from that book: a stored panel whose rows, totals,
    kind counts or account disagree with the derived
    panel refuses. A panel naming no account refuses too.
    """
    if isinstance(panel, ContextRecipePanel):
        current = panel
    elif isinstance(panel, dict):
        unknown = set(panel) - _PANEL_KEYS
        if unknown:
            raise ValueError(
                "unknown panel keys: %s" % ", ".join(sorted(unknown)))
        rows = _pick_any(panel, ("rows", "recipes"), "rows")
        if rows is None:
            raise ValueError("a panel is missing its rows")
        total = _pick_any(panel, ("total_items", "total"), "totals")
        if total is None:
            raise ValueError("a panel is missing its total items")
        total_pieces = _pick_any(panel, ("total_pieces",), "totals")
        if total_pieces is None:
            raise ValueError("a panel is missing its total pieces")
        kind_counts = _pick_any(
            panel, ("kind_counts", "kinds"), "kind counts")
        if kind_counts is None:
            raise ValueError("a panel is missing its kind counts")
        account = _pick_any(panel, ("account", "statements"), "accounts")
        if account is None:
            raise ValueError("a panel names no account of its own")
        kwargs: Dict[str, Any] = {
            "rows": rows, "total_items": total,
            "total_pieces": total_pieces,
            "kind_counts": kind_counts, "account": account}
        panel_id = _pick_any(panel, ("panel_id", "id"), "panel ids")
        if panel_id is not None:
            kwargs["panel_id"] = panel_id
        current = ContextRecipePanel(**kwargs)
    else:
        raise ValueError(f"a panel must be a mapping, got {panel!r}")
    if source is not None:
        derived = derive_panel(source)
        if (current.rows != derived.rows
                or current.total_items != derived.total_items
                or current.total_pieces != derived.total_pieces
                or current.kind_counts != derived.kind_counts
                or current.account != derived.account):
            raise ValueError(
                "a stored panel disagrees with the panel "
                "derived from its book")
    return current


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> ContextRecipePanel:
    """Build one validated panel, from a mapping or field words."""
    if isinstance(panel, ContextRecipePanel) and not kwargs:
        return validate_panel(panel, source)
    if isinstance(panel, dict) or panel is None:
        merged: Dict[str, Any] = {}
        if isinstance(panel, dict):
            merged.update(panel)
        merged.update(kwargs)
        return validate_panel(merged, source)
    return validate_panel(panel, source)


# ---------------------------------------------------------------------
# The book: recipes in held order, panels judged.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class ContextRecipeBook:
    """One context-recipe book: its recipes, in held order.

    ``recipes`` are the context recipes, in held order,
    each with its provenance whole; no two recipes of
    one book share a name - a name summons one bundle,
    never two. ``panels`` are the book's derivations -
    recipe panels of the whole book, each judged
    against the book by :func:`validate_book`;
    ``canon_note`` is the book's own note. The total is
    the recipes' own count, judged at construction.
    This book is the book file's shape: the shipped
    example is one book, and a real book file is a new
    file in this shape.
    """

    title: str = ""
    recipes: Tuple[ContextRecipe, ...] = ()
    panels: Tuple[ContextRecipePanel, ...] = ()
    canon_note: str = ""
    total_recipes: Optional[int] = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_title(self.title, "a book's title"))
        if isinstance(self.recipes, (str, bytes)) \
                or not isinstance(self.recipes, (list, tuple)):
            raise ValueError(
                f"a book's recipes must be a list of "
                f"context recipes, got {self.recipes!r}")
        recipes = tuple(_check_recipe_ref(item) for item in self.recipes)
        if not recipes:
            raise ValueError("a recipe book holds at least one recipe")
        seen_ids = set()
        seen_names = set()
        for recipe in recipes:
            if recipe.recipe_id is not None:
                if recipe.recipe_id in seen_ids:
                    raise ValueError(
                        f"a recipe named {recipe.recipe_id!r} "
                        f"already exists")
                seen_ids.add(recipe.recipe_id)
            lowered = recipe.name.lower()
            if lowered in seen_names:
                raise ValueError(
                    f"a recipe named {recipe.name!r} already "
                    f"stands in this book - a name summons "
                    f"one bundle, never two")
            seen_names.add(lowered)
        object.__setattr__(self, "recipes", recipes)
        if isinstance(self.panels, (str, bytes)) \
                or not isinstance(self.panels, (list, tuple)):
            raise ValueError(
                f"a book's panels must be a list of panels, "
                f"got {self.panels!r}")
        panels = tuple(
            p if isinstance(p, ContextRecipePanel)
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
        given = self.total_recipes
        if given is None:
            object.__setattr__(self, "total_recipes", len(recipes))
        else:
            checked = _check_count(given, "a book's total recipes")
            if checked != len(recipes):
                raise ValueError(
                    "a book's total recipes must be its own "
                    "recipes' count")
            object.__setattr__(self, "total_recipes", checked)

    def recipe_for(self, recipe_id: Any) -> ContextRecipe:
        """The recipe one id names in this book."""
        wanted = normalize_member_id(recipe_id)
        for recipe in self.recipes:
            if recipe.recipe_id == wanted:
                return recipe
        raise KeyError(f"no recipe in the book: {wanted!r}")

    def recipe_named(self, name: Any) -> ContextRecipe:
        """The recipe one name summons in this book.

        Names match whole, in any letter case: the name
        a session speaks is the name the recipe was
        saved under. A name no recipe of the book
        carries raises KeyError - a summoning that
        names nothing held is refused, never guessed.
        """
        if not isinstance(name, str) or not name.strip():
            raise ValueError(
                f"a recipe name must be plain words, got {name!r}")
        wanted = name.strip().lower()
        for recipe in self.recipes:
            if recipe.name.lower() == wanted:
                return recipe
        raise KeyError(f"no recipe in the book named {name.strip()!r}")

    def panel_for(self, panel_id: Any) -> ContextRecipePanel:
        """The stored panel one id names in this book."""
        wanted = normalize_member_id(panel_id)
        for panel in self.panels:
            if panel.panel_id == wanted:
                return panel
        raise KeyError(f"no panel in the book: {wanted!r}")

    def recipe_ids(self) -> Tuple[str, ...]:
        """Every held recipe id, in held order."""
        return tuple(
            item.recipe_id for item in self.recipes if item.recipe_id)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "context_recipe_book",
            "slice": CONTEXT_RECIPES_SLICE,
            "title": self.title,
            "recipe_ids": list(self.recipe_ids()),
            "recipe_count": len(self.recipes),
            "panel_count": len(self.panels),
        }


def validate_book(data: Any, *, require_example: bool = False
                  ) -> ContextRecipeBook:
    """Validate one context-recipes mapping into a book.

    The mapping names a ``schema`` (the context-recipes
    schema word), a ``guide`` mapping (its ``title``), a
    ``recipes`` list and an optional ``panels`` list.
    Every recipe stands on its own validation, then the
    whole is judged: recipe ids unique, no name naming
    two recipes, and every stored panel judged against
    the book (a panel the book does not derive refuses).
    With ``require_example`` the shipped example is held
    to its pinned shape: the pinned title, recipes and
    panel, and the panel's pinned rows and account
    word-for-word. Problems raise
    :class:`ValidationError` or ``ValueError``.
    """
    if isinstance(data, ContextRecipeBook):
        return data
    if not isinstance(data, dict):
        raise ValidationError(
            f"a recipe book must be a mapping, got {data!r}")
    unknown = set(data) - _RECIPE_BOOK_KEYS
    if unknown:
        raise ValidationError(
            "unknown recipe-book keys: %s" % ", ".join(sorted(unknown)))
    if data.get("schema") != CONTEXT_RECIPES_SCHEMA:
        raise ValidationError(
            f"a recipe book must carry schema "
            f"{CONTEXT_RECIPES_SCHEMA!r}, got {data.get('schema')!r}")
    recipes = _pick_any(data, ("recipes",), "recipes")
    if recipes is None:
        raise ValidationError("a recipe book is missing its recipes")
    if not isinstance(recipes, (list, tuple)):
        raise ValidationError("a recipe book's recipes must be a list")
    if data.get("panels") is not None \
            and not isinstance(data["panels"], (list, tuple)):
        raise ValidationError("a recipe book's panels must be a list")
    head = data.get("guide") or {}
    if not isinstance(head, dict):
        raise ValidationError("a recipe book's guide must be a mapping")
    unknown_head = set(head) - _BOOK_KEYS
    if unknown_head:
        raise ValidationError(
            "unknown guide keys: %s" % ", ".join(sorted(unknown_head)))
    try:
        title = _pick_any(head, ("title", "name"), "titles")
        if title is None:
            raise ValidationError("a recipe book is missing its title")
        note = data.get("canon_note") or ""
        if not isinstance(note, str):
            raise ValidationError("a recipe book's note must be text")
        book = ContextRecipeBook(
            title=title, recipes=tuple(recipes),
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
                "the shipped example recipe book's title is "
                "not the pinned title")
        if book.recipe_ids() != _EXAMPLE_RECIPE_IDS:
            raise ValidationError(
                "the shipped example's recipes are not the "
                "pinned recipes")
        panel = book.panel_for(_EXAMPLE_PANEL_ID)
        if tuple(r.recipe_id for r in panel.rows) != _EXAMPLE_PANEL_ROW_IDS:
            raise ValidationError(
                "the shipped example panel does not name its "
                "pinned rows in panel order")
        if panel.account != _EXAMPLE_PANEL_ACCOUNT:
            raise ValidationError(
                "the shipped example panel does not carry its "
                "pinned account word-for-word")
        first = book.recipes[0]
        if first.recipe_id != _EXAMPLE_FIRST_RECIPE_ID \
                or first.name != _EXAMPLE_FIRST_RECIPE_NAME:
            raise ValidationError(
                "the shipped example's first recipe is not "
                "its pinned recipe of its pinned name")
    return book


def build_book(book: Any = None, **kwargs: Any) -> ContextRecipeBook:
    """Build one validated book, from a mapping or field words."""
    if isinstance(book, ContextRecipeBook) and not kwargs:
        return book
    if isinstance(book, dict):
        if "schema" in book:
            return validate_book(book)
        merged: Dict[str, Any] = dict(book)
        merged.update(kwargs)
        return ContextRecipeBook(**merged)
    if book is None:
        return ContextRecipeBook(**kwargs)
    raise ValueError(f"a recipe book is needed, got {book!r}")


def _book_from(data: Any, *, require_example: bool) -> ContextRecipeBook:
    try:
        return validate_book(data, require_example=require_example)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def load_context_recipes(
        data: Optional[Dict[str, Any]] = None) -> ContextRecipeBook:
    """Load and validate the shipped example book (or *data*).

    The shipped file is held to the example check: the
    pinned title, recipes and panel - the M-157 slice
    boundary book - so the shipped book covers the
    canon this slice exists to hold.
    """
    raw = data if data is not None else load_resource(
        CONTEXT_RECIPES_RESOURCE)
    return _book_from(raw, require_example=True)


def load_context_recipes_file(path: Any) -> ContextRecipeBook:
    """Load and validate a recipe book from a file at *path*.

    Any file in the context-recipes shape, anywhere on
    disk, validated whole - a malformed file raises
    :class:`ValidationError` naming the problem, and a
    missing file raises ``FileNotFoundError``. The
    example check is not held: a real book stands on its
    own recipes.
    """
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _book_from(raw, require_example=False)


# ---------------------------------------------------------------------
# The registry model: one book held recipe by recipe.
# ---------------------------------------------------------------------


class ContextRecipeRegistry:
    """One session's context recipes, held one by one.

    The registry holds recipes, never panels: the panel
    is a derivation, read off the whole held book at
    call time, so nothing here can hold a figure stale.
    A whole book is judged as a book judges it - its
    ids and names against the whole book - before its
    recipes are held in book order. A name held here
    names one recipe: a second recipe under a held name
    (in any letter case) refuses, so a summoning in the
    session is never ambiguous.
    """

    def __init__(self, book: Any = None) -> None:
        self._title: Optional[str] = None
        self._recipes: Dict[str, ContextRecipe] = {}
        self._recipe_order: list = []
        self._next_recipe = 1
        if book is not None:
            self.register_book(book)

    def _fresh_recipe_id(self, held_ids: Any) -> str:
        while f"recipe-{self._next_recipe}" in held_ids:
            self._next_recipe += 1
        fresh = f"recipe-{self._next_recipe}"
        self._next_recipe += 1
        return fresh

    def _check_name_free(self, recipe: ContextRecipe) -> None:
        for held in self._recipes.values():
            if held.name.lower() == recipe.name.lower():
                raise ValueError(
                    f"a recipe named {recipe.name!r} already "
                    f"stands in this book - a name summons "
                    f"one bundle, never two")

    def register_recipe(self, recipe: Any) -> ContextRecipe:
        """Register one recipe into the held book.

        A recipe with no id is given a deterministic
        ``recipe-N`` id. A recipe id already standing
        here refuses, as does a name a held recipe
        already carries.
        """
        validated = _check_recipe_ref(recipe)
        if validated.recipe_id is not None \
                and validated.recipe_id in self._recipes:
            raise ValueError(
                f"a recipe named {validated.recipe_id!r} "
                f"already exists")
        self._check_name_free(validated)
        return self._hold_recipe(validated)

    def _hold_recipe(self, validated: ContextRecipe) -> ContextRecipe:
        """Hold one judged recipe, in held order.

        The caller has already judged the recipe against
        the held book (its id and its name); this is the
        holding alone, with a deterministic ``recipe-N``
        id given to a recipe carrying none.
        """
        if validated.recipe_id is None:
            validated = replace(
                validated,
                recipe_id=self._fresh_recipe_id(set(self._recipes)))
        self._recipes[validated.recipe_id] = validated
        self._recipe_order.append(validated.recipe_id)
        return validated

    def register_book(self, book: Any) -> ContextRecipeBook:
        """Register every recipe of one book, in order.

        The first book held sets the title; a later book
        under a different title refuses, as does a book
        naming a held recipe id or a held recipe name.
        The book is judged whole before anything is
        held, and the recipes are then held in the
        book's own order. The book's panels are
        derivations, not holdings, and are not held.
        """
        validated = build_book(book)
        if self._title is not None and validated.title != self._title:
            raise ValueError(
                "this registry already holds a recipe book "
                "under a different title")
        for recipe in validated.recipes:
            if recipe.recipe_id in self._recipes:
                raise ValueError(
                    f"a recipe named {recipe.recipe_id!r} "
                    f"already exists")
            self._check_name_free(recipe)
        self._title = validated.title
        for recipe in validated.recipes:
            self._hold_recipe(recipe)
        return self.book()

    def get_recipe(self, recipe_id: Any) -> ContextRecipe:
        """The recipe one id names among the held recipes."""
        wanted = normalize_member_id(recipe_id)
        if wanted not in self._recipes:
            raise KeyError(f"unknown recipe: {wanted!r}")
        return self._recipes[wanted]

    def recipe_named(self, name: Any) -> ContextRecipe:
        """The recipe one name summons among the held recipes."""
        if not isinstance(name, str) or not name.strip():
            raise ValueError(
                f"a recipe name must be plain words, got {name!r}")
        wanted = name.strip().lower()
        for recipe_id in self._recipe_order:
            recipe = self._recipes[recipe_id]
            if recipe.name.lower() == wanted:
                return recipe
        raise KeyError(f"no recipe held named {name.strip()!r}")

    def latest_recipe(self) -> ContextRecipe:
        """The most recently held recipe."""
        if not self._recipe_order:
            raise ValueError("no recipe is held yet")
        return self._recipes[self._recipe_order[-1]]

    def list_recipes(self) -> Tuple[ContextRecipe, ...]:
        """Every held recipe, in the order they were held."""
        return tuple(self._recipes[item] for item in self._recipe_order)

    def book(self) -> ContextRecipeBook:
        """The held recipes as one validated book."""
        if self._title is None:
            raise ValueError("no recipe book is held yet")
        return ContextRecipeBook(
            title=self._title, recipes=self.list_recipes())

    def panel(self) -> ContextRecipePanel:
        """Derive the recipe panel of the whole held book."""
        return derive_panel(self)


# ---------------------------------------------------------------------
# Recipe news, shaped as session records.
# ---------------------------------------------------------------------


def recipe_record(recipe: Any) -> Dict[str, Any]:
    """The session-news record of one context recipe."""
    current = recipe if isinstance(recipe, ContextRecipe) \
        else build_recipe(recipe)
    record_out = current.to_record()
    record_out["news"] = True
    record_out["headline"] = (
        f"Context recipe \"{current.name}\" bundles "
        f"{len(current.items)} pieces, saved in "
        f"{current.session_ref} on {current.created_on}.")
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
        f"Recipe panel: {current.total_items} recipes - "
        f"{current.total_pieces} pieces bundled.")
    return record_out


def book_record(book: Any) -> Dict[str, Any]:
    """The session-news record of one recipe book."""
    current = book if isinstance(book, ContextRecipeBook) \
        else build_book(book)
    record_out = current.to_record()
    record_out["news"] = True
    record_out["headline"] = (
        f"Context recipes {current.title}: "
        f"{record_out['recipe_count']} recipes named.")
    return record_out


def plain_words(recipe: Any) -> str:
    """One context recipe, in one plain sentence."""
    current = recipe if isinstance(recipe, ContextRecipe) \
        else build_recipe(recipe)
    kinds = ", ".join(item.kind for item in current.items)
    return (
        f"\"{current.name}\" bundles {len(current.items)} "
        f"pieces ({kinds}) for this purpose: "
        f"{current.purpose} It was saved in "
        f"{current.session_ref} on {current.created_on} "
        f"(read from {current.source}).")


def panel_plain_words(source: Any) -> str:
    """The recipe panel in plain words, in full.

    Accepts a ContextRecipePanel or a
    ContextRecipeBook (whose derived panel is told).
    The panel is told whole - its rows in panel order
    and its account.
    """
    if isinstance(source, ContextRecipePanel):
        panel = validate_panel(source)
        title = None
    elif isinstance(source, ContextRecipeBook):
        panel = derive_panel(source)
        title = source.title
    else:
        raise ValueError(
            f"a context-recipes source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    lines.append("Recipes, in panel order:")
    for row in panel.rows:
        lines.append(
            f"{row.recipe_id}: \"{row.name}\" - "
            f"{row.piece_count} pieces, saved in "
            f"{row.session_ref}")
    lines.extend(panel.account)
    return "\n".join(lines)


# ---------------------------------------------------------------------
# Screens: the formatters and the /recipes grammar.
# ---------------------------------------------------------------------


def _source_book(source: Any) -> ContextRecipeBook:
    if source is None:
        return load_context_recipes()
    if isinstance(source, ContextRecipeRegistry):
        return source.book()
    if isinstance(source, ContextRecipeBook):
        return source
    raise ValueError(f"a recipe book is needed, got {source!r}")


def format_recipe(recipe: Any) -> str:
    """One context recipe as a screen block, provenance whole."""
    current = recipe if isinstance(recipe, ContextRecipe) \
        else build_recipe(recipe)
    lines = [
        f"{current.recipe_id or '-'}: \"{current.name}\" - "
        f"{len(current.items)} pieces, saved in "
        f"{current.session_ref} on {current.created_on}",
        f"Purpose: {current.purpose}",
        f"(read from {current.source})",
        "Pieces, in bundle order:",
    ]
    for item in current.items:
        lines.append(
            f"- a {item.kind} piece ({item.ref}): {item.why}")
    lines.append(
        "Summoning names this bundle and its pieces only - "
        "no live context is assembled here.")
    return "\n".join(lines)


def format_recipes(source: Any = None) -> str:
    """Context recipes of one book, in held order."""
    book = _source_book(source)
    lines = [
        f"{item.recipe_id or '-'}: \"{item.name}\" - "
        f"{len(item.items)} pieces, saved in {item.session_ref}"
        for item in book.recipes]
    if not lines:
        lines.append("No recipes are held.")
    return "\n".join(lines)


def format_summon(recipe: Any) -> str:
    """One recipe summoned by name, as a screen block.

    The summoning names the bundle and every piece it
    carries, whole - and that is all it does here: the
    pieces themselves stand in their own holdings, and
    no live context is assembled by this layer.
    """
    current = recipe if isinstance(recipe, ContextRecipe) \
        else build_recipe(recipe)
    lines = [
        f"Summoned \"{current.name}\" "
        f"({current.recipe_id or '-'}): "
        f"{len(current.items)} pieces.",
        f"Purpose: {current.purpose}",
        "Bring in, in bundle order:",
    ]
    for item in current.items:
        lines.append(f"- the {item.kind} piece {item.ref}")
    lines.append(
        "The pieces stand in their own holdings; summoning "
        "names them, it assembles no live context.")
    return "\n".join(lines)


def format_panel(source: Any = None) -> str:
    """The recipe panel as a screen block: every row and the account.

    Accepts a ContextRecipePanel or a
    ContextRecipeBook; a book shows the panel it derives.
    """
    if isinstance(source, ContextRecipePanel):
        panel = validate_panel(source)
        lines: list = []
    else:
        book = _source_book(source)
        if not book.recipes:
            return (f"Recipe panel in {book.title}:\n"
                    f"No recipes are held.")
        panel = derive_panel(book)
        lines = [f"Recipe panel in {book.title}:"]
    lines.append("Recipes, in panel order:")
    for row in panel.rows:
        lines.append(
            f"{row.recipe_id}: \"{row.name}\" - "
            f"{row.piece_count} pieces, saved in "
            f"{row.session_ref}")
    lines.extend(panel.account)
    return "\n".join(lines)


def format_context_recipes_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /recipes.

    With nothing named, the shipped example recipe book
    is shown - the example this slice ships - so the
    screen is never empty.
    """
    book = _source_book(source)
    lines = ["Context Recipes (M-158) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_recipes(book))
    lines.append("")
    lines.append(format_panel(book))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_recipe_args(args: Any) -> Tuple[str, Any]:
    """Parse the /recipes grammar both surfaces share.

    No words (or ``show`` / ``list``) shows the recipe
    book; ``recipe <recipe-id>`` shows one context
    recipe with its provenance whole; ``summon <recipe
    name...>`` summons the recipe the name names - a
    recipe's name is plain words, so every word after
    ``summon`` is the name; ``panel`` shows the recipe
    panel derived from the whole book. Anything else is
    a usage error naming the grammar. Returns
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
    if head == "recipe" and len(words) == 2:
        try:
            return (head, normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "summon" and len(words) >= 2:
        return (head, " ".join(words[1:]))
    raise ValueError(USAGE)
