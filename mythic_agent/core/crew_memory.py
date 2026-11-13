"""Crew memory (All-Features roadmap slice M-133).

Part VI continues here. The roadmap's words:
``shared project memory (Part VII) with
per-member notebooks; a member's hard-won fact
is findable by all.``

What already shipped, and what this slice adds:

* The crew itself is already data
  (``core/crew_members.py``, M-121), the crew's
  hand-offs are data (M-126), heterogeneous crews
  hold who rides which model (M-129), research
  swarms (M-131) and review panels (M-132) are
  data. What nothing held is what the crew has
  *learned*: a fact one member won the hard way
  lived only in that member's own context, so
  every other member could pay for it again.
* This slice is that memory, as a pure layer:
  a shared project memory validated as data -
  per-member notebooks, each holding that
  member's entries (one fact per entry: a title,
  the fact itself in plain words, the tags that
  name its topics, and its provenance, where the
  fact came from) - the shipped data file
  (``mythic_agent/data/crew_memory.yaml``)
  holding one example memory in exactly the
  shape a real memory file takes, a loader for
  a memory file anywhere on disk, a deterministic
  search over every notebook at once, a record
  shaped as session news, and a small in-memory
  registry model. The shared memory is the union
  view over all notebooks: an entry lives in
  exactly one member's notebook, and the shared
  search finds it no matter whose notebook holds
  it or who asks. This module persists nothing,
  syncs nothing, spawns no crew, calls no model
  and imports no agent / UI code; the agent
  layer owns holding the memory for a session.

Honesty rules, enforced here and pinned by tests:

* **One notebook per member, one home per
  fact.** Every entry belongs to exactly one
  member's notebook; its member is an M-121
  member id read exactly as the M-121 layer
  reads one (``core/crew_members.py``) -
  composed by import, never re-read here. A
  memory holds at most one notebook per member.
* **Findable by all, deterministically.** Search
  is exact + substring matching over entry ids,
  titles, fact text, tags and member ids, run
  over the union of all notebooks, and its
  results come back in one deterministic order
  (member id, then entry id). There are no
  embeddings, no model calls and no relevance
  scores: a fact is found because its words or
  tags match the query, whoever recorded it and
  whoever asks - the asking member never
  narrows the search.
* **Search is derived, never stored.** Nothing
  in a memory file or a record holds a search
  result or an index; every search is computed
  from the entries held at that moment, so it
  can never disagree with them.
* **Malformed refuses.** An empty fact, an
  empty title, a malformed member id, a
  duplicate entry id anywhere in the memory, a
  duplicate fact inside one notebook (the same
  fact text, read case-insensitively with
  whitespace folded - the same fact in two
  *different* notebooks is two members'
  records and stands), a duplicated tag on one
  entry, two notebooks for one member, and
  unknown keys in an entry, a notebook, or a
  memory mapping all raise instead of being
  skipped or guessed at.
* **Data only.** No persistence, no sync, no
  spawning and no model call is claimed or
  attempted here: a memory here is a validated
  record of facts the crew holds, not the
  learning itself.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..resources import load_resource
from .crew_members import normalize_member_id
from .validation import ValidationError

__all__ = [
    "MEMORY_RESOURCE",
    "MEMORY_SCHEMA",
    "MEMORY_SLICE",
    "PLAIN_EXPLANATION",
    "USAGE",
    "CrewMemory",
    "CrewMemoryRegistry",
    "MemberNotebook",
    "MemoryEntry",
    "build_entry",
    "build_memory",
    "build_notebook",
    "entry_record",
    "find_entries",
    "format_entries",
    "format_entry",
    "format_memory_screen",
    "format_notebook",
    "format_notebooks",
    "load_crew_memory",
    "load_crew_memory_file",
    "memory_record",
    "normalize_tag",
    "notebook_record",
    "parse_memory_args",
    "plain_words",
    "search_memory",
    "validate_entry",
    "validate_memory",
    "validate_notebook",
]

MEMORY_SLICE = "M-133"

#: The packaged data resource holding the example memory.
MEMORY_RESOURCE = "crew_memory.yaml"

#: The schema word a memory file must carry.
MEMORY_SCHEMA = "mythic.crew_memory/1"

_ENTRY_KEYS = frozenset({
    "id", "entry_id", "member", "member_id", "owner",
    "title", "name", "fact", "body", "text",
    "tags", "topics", "tag", "topic",
    "provenance", "source", "origin",
})

_NOTEBOOK_KEYS = frozenset({
    "member", "member_id", "owner", "entries", "facts",
})

_MEMORY_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "memory_note", "notebooks",
})

#: The shipped example memory's members, in file
#: order: three notebooks, held to this by the
#: loader's example check.
_EXAMPLE_MEMBERS = ("auditor", "guardian", "scribe")

#: The shipped example memory's entry ids, in
#: shared (member, entry id) order.
_EXAMPLE_ENTRY_IDS = (
    "broken-checkpoint-chain", "portaudio-env-import",
    "verify-remote-moved")

PLAIN_EXPLANATION = (
    "Crew memory: one shared project memory "
    "held as per-member notebooks. Each entry "
    "is one fact in exactly one member's "
    "notebook - its title, the fact in plain "
    "words, its tags and where it came from - "
    "and the shared memory is the union of all "
    "notebooks, so a fact one member won the "
    "hard way is findable by all: search runs "
    "over every notebook at once, in one "
    "deterministic order, whoever recorded the "
    "fact and whoever asks. This layer holds "
    "the memory as data only; it persists "
    "nothing, syncs nothing, spawns no crew "
    "and calls no model itself."
)

USAGE = (
    "Usage: /memory, /memory show, "
    "/memory show <member>, /memory search <words>, "
    "/memory tag <tag>, /memory entry <entry-id>, "
    "/memory members"
)


def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_short_text(value: Any, what: str) -> str:
    text = _clean_text(value, what)
    if len(text) > 200 or "\x00" in text:
        raise ValueError(
            f"{what} must be plain text of at most "
            f"200 characters, got {len(text)} characters")
    return text


def _check_long_text(value: Any, what: str) -> str:
    text = _clean_text(value, what)
    if len(text) > 2000 or "\x00" in text:
        raise ValueError(
            f"{what} must be plain text of at most "
            f"2000 characters, got {len(text)} characters")
    return text


def normalize_tag(value: Any) -> str:
    """The canonical tag word a word names.

    A tag is one word of letters, digits, dashes,
    underscores and dots, read in lower case with
    dashes read as underscores - ``Checkpoint-
    Chain`` reads as ``checkpoint_chain``.
    Anything else raises.
    """
    if isinstance(value, str):
        wanted = value.strip().lower().replace("-", "_")
        if wanted:
            return normalize_member_id(wanted)
    raise ValueError(f"a tag must be one word, got {value!r}")


def _check_tags(value: Any) -> Tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        items = [value]
    elif isinstance(value, (list, tuple)):
        items = list(value)
    else:
        raise ValueError(f"an entry's tags must be a list, got {value!r}")
    tags = tuple(normalize_tag(item) for item in items)
    if len(set(tags)) != len(tags):
        raise ValueError("an entry names one tag twice")
    return tags


def _fact_key(fact: str) -> str:
    """The comparison key of one fact's text."""
    return " ".join(fact.lower().split())


def _pick_any(mapping: Dict[str, Any], spellings: Tuple[str, ...],
              what: str) -> Any:
    values = [mapping[s] for s in spellings if s in mapping]
    if not values:
        return None
    if any(value != values[0] for value in values[1:]):
        raise ValueError(f"a record names two different {what}")
    return values[0]


# ---------------------------------------------------------------------
# The entry: one fact in one member's notebook.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class MemoryEntry:
    """One fact held in one member's notebook, as data.

    ``member`` is the M-121 member whose notebook
    holds the fact; ``title`` names it; ``fact``
    is the fact itself in plain words; ``tags``
    name its topics, each once, possibly none;
    ``provenance`` says where the fact came from.
    Constructing one validates its shape only:
    whether its id or fact already stands in its
    notebook is the notebook's / memory's concern.
    """

    entry_id: Optional[str] = None
    member: str = ""
    title: str = ""
    fact: str = ""
    tags: Tuple[str, ...] = ()
    provenance: str = ""

    def __post_init__(self) -> None:
        if self.entry_id is not None:
            object.__setattr__(
                self, "entry_id", normalize_member_id(self.entry_id))
        object.__setattr__(
            self, "member", normalize_member_id(self.member))
        object.__setattr__(
            self, "title", _check_short_text(self.title, "a title"))
        object.__setattr__(
            self, "fact", _check_long_text(self.fact, "a fact"))
        object.__setattr__(self, "tags", _check_tags(self.tags))
        object.__setattr__(
            self, "provenance",
            _check_short_text(self.provenance, "a provenance"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "crew_memory_entry",
            "slice": MEMORY_SLICE,
            "entry_id": self.entry_id,
            "member": self.member,
            "title": self.title,
            "fact": self.fact,
            "tags": list(self.tags),
            "provenance": self.provenance,
        }


def validate_entry(entry: Any) -> MemoryEntry:
    """Validate one entry into a MemoryEntry.

    Accepts a MemoryEntry or a mapping naming a
    ``member`` (or ``member_id`` / ``owner``), a
    ``title`` (or ``name``), a ``fact`` (or
    ``body`` / ``text``), a ``provenance`` (or
    ``source`` / ``origin``), optional ``tags``
    (or ``topics`` / a single ``tag`` / ``topic``)
    and an optional ``entry_id`` (or ``id``).
    Naming two spellings of one field with
    different values refuses, and unknown keys
    refuse.
    """
    if isinstance(entry, MemoryEntry):
        return entry
    if not isinstance(entry, dict):
        raise ValueError(f"an entry must be a mapping, got {entry!r}")
    unknown = set(entry) - _ENTRY_KEYS
    if unknown:
        raise ValueError(
            "unknown entry keys: %s" % ", ".join(sorted(unknown)))
    member = _pick_any(entry, ("member", "member_id", "owner"), "members")
    if member is None:
        raise ValueError("an entry is missing its member")
    title = _pick_any(entry, ("title", "name"), "titles")
    if title is None:
        raise ValueError("an entry is missing its title")
    fact = _pick_any(entry, ("fact", "body", "text"), "facts")
    if fact is None:
        raise ValueError("an entry is missing its fact")
    provenance = _pick_any(
        entry, ("provenance", "source", "origin"), "provenances")
    if provenance is None:
        raise ValueError("an entry is missing its provenance")
    kwargs: Dict[str, Any] = {
        "member": member, "title": title, "fact": fact,
        "provenance": provenance}
    tags = _pick_any(entry, ("tags", "topics", "tag", "topic"), "tags")
    if tags is not None:
        kwargs["tags"] = tags
    entry_id = _pick_any(entry, ("entry_id", "id"), "entry ids")
    if entry_id is not None:
        kwargs["entry_id"] = entry_id
    return MemoryEntry(**kwargs)


def build_entry(entry: Any = None, **kwargs: Any) -> MemoryEntry:
    """Build one validated entry, from a mapping or field words."""
    if isinstance(entry, MemoryEntry) and not kwargs:
        return entry
    if isinstance(entry, dict) or entry is None:
        merged: Dict[str, Any] = {}
        if isinstance(entry, dict):
            merged.update(entry)
        merged.update(kwargs)
        return validate_entry(merged)
    raise ValueError(f"an entry must be a mapping, got {entry!r}")


# ---------------------------------------------------------------------
# The notebook: one member's entries, whole.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class MemberNotebook:
    """One member's notebook: their entries, in file order.

    Every entry's member must be the notebook's
    member - an entry lives in exactly one
    notebook, its own member's. Entry ids are
    unique inside the notebook, and no fact text
    stands twice inside it.
    """

    member: str = ""
    entries: Tuple[MemoryEntry, ...] = ()

    def __post_init__(self) -> None:
        member = normalize_member_id(self.member)
        object.__setattr__(self, "member", member)
        entries = tuple(
            e if isinstance(e, MemoryEntry) else validate_entry(e)
            for e in self.entries)
        for entry in entries:
            if entry.member != member:
                raise ValueError(
                    f"an entry of {entry.member} cannot live in "
                    f"{member}'s notebook")
        ids = [e.entry_id for e in entries if e.entry_id is not None]
        if len(set(ids)) != len(ids):
            raise ValueError("a notebook holds one entry id twice")
        keys = [_fact_key(e.fact) for e in entries]
        if len(set(keys)) != len(keys):
            raise ValueError(
                "a notebook holds the same fact twice: "
                "a fact is recorded once in its notebook")
        object.__setattr__(self, "entries", entries)

    def entry_for(self, entry_id: Any) -> MemoryEntry:
        """The entry one id names in this notebook; unknown raises."""
        wanted = normalize_member_id(entry_id)
        for entry in self.entries:
            if entry.entry_id == wanted:
                return entry
        raise KeyError(f"no entry {wanted!r} in {self.member}'s notebook")

    def entry_ids(self) -> Tuple[str, ...]:
        """Every held entry id, in notebook order (id-less skipped)."""
        return tuple(e.entry_id for e in self.entries if e.entry_id)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "member_notebook",
            "slice": MEMORY_SLICE,
            "member": self.member,
            "entry_ids": list(self.entry_ids()),
            "entry_count": len(self.entries),
        }


def validate_notebook(notebook: Any) -> MemberNotebook:
    """Validate one notebook into a MemberNotebook.

    Accepts a MemberNotebook or a mapping naming
    a ``member`` (or ``member_id`` / ``owner``)
    and its ``entries`` (or ``facts``). Unknown
    keys refuse.
    """
    if isinstance(notebook, MemberNotebook):
        return notebook
    if not isinstance(notebook, dict):
        raise ValueError(f"a notebook must be a mapping, got {notebook!r}")
    unknown = set(notebook) - _NOTEBOOK_KEYS
    if unknown:
        raise ValueError(
            "unknown notebook keys: %s" % ", ".join(sorted(unknown)))
    member = _pick_any(
        notebook, ("member", "member_id", "owner"), "members")
    if member is None:
        raise ValueError("a notebook is missing its member")
    raw = _pick_any(notebook, ("entries", "facts"), "entries")
    if raw is None:
        raw = []
    if not isinstance(raw, (list, tuple)):
        raise ValueError("a notebook's entries must be a list")
    return MemberNotebook(
        member=member, entries=tuple(validate_entry(e) for e in raw))


def build_notebook(notebook: Any = None, **kwargs: Any) -> MemberNotebook:
    """Build one validated notebook, from a mapping or field words."""
    if isinstance(notebook, MemberNotebook) and not kwargs:
        return notebook
    if isinstance(notebook, dict) or notebook is None:
        merged: Dict[str, Any] = {}
        if isinstance(notebook, dict):
            merged.update(notebook)
        merged.update(kwargs)
        return validate_notebook(merged)
    raise ValueError(f"a notebook must be a mapping, got {notebook!r}")


# ---------------------------------------------------------------------
# The shared memory: the union view over all notebooks.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class CrewMemory:
    """The shared project memory, whole, as data.

    ``notebooks`` are the per-member notebooks, in
    file order, at most one per member; entry ids
    are unique across the whole memory, so one id
    always names one fact in one member's
    notebook. The shared views (``entries``,
    ``entry_for``, search) are derived from the
    notebooks held, never stored.
    """

    notebooks: Tuple[MemberNotebook, ...] = ()
    memory_note: str = ""

    def __post_init__(self) -> None:
        notebooks = tuple(
            n if isinstance(n, MemberNotebook) else validate_notebook(n)
            for n in self.notebooks)
        members = [n.member for n in notebooks]
        if len(set(members)) != len(members):
            raise ValueError("a memory holds one notebook per member")
        seen: Dict[str, str] = {}
        for notebook in notebooks:
            for entry in notebook.entries:
                if entry.entry_id is None:
                    continue
                if entry.entry_id in seen:
                    raise ValueError(
                        f"entry id {entry.entry_id!r} stands in two "
                        f"notebooks ({seen[entry.entry_id]} and "
                        f"{notebook.member})")
                seen[entry.entry_id] = notebook.member
        object.__setattr__(self, "notebooks", notebooks)
        if not isinstance(self.memory_note, str):
            raise ValueError("a memory's note must be text")
        object.__setattr__(self, "memory_note", self.memory_note.strip())

    def members(self) -> Tuple[str, ...]:
        """Every member holding a notebook, in file order."""
        return tuple(n.member for n in self.notebooks)

    def notebook_for(self, member: Any) -> MemberNotebook:
        """One member's notebook; a member with none raises."""
        wanted = normalize_member_id(member)
        for notebook in self.notebooks:
            if notebook.member == wanted:
                return notebook
        raise KeyError(f"no notebook for member: {wanted!r}")

    def entries(self) -> Tuple[MemoryEntry, ...]:
        """Every entry in the shared memory, in shared order.

        Shared order is deterministic: by member id,
        then by entry id (id-less entries last in
        their notebook, by title). This is the union
        view - every notebook's entries, findable
        from the one shared memory.
        """
        all_entries = [e for n in self.notebooks for e in n.entries]
        return tuple(sorted(
            all_entries,
            key=lambda e: (e.member, e.entry_id or "~", e.title)))

    def entry_for(self, entry_id: Any) -> MemoryEntry:
        """The entry one id names, in whichever notebook holds it."""
        wanted = normalize_member_id(entry_id)
        for entry in self.entries():
            if entry.entry_id == wanted:
                return entry
        raise KeyError(f"no entry in the shared memory: {wanted!r}")

    def entries_for(self, member: Any) -> Tuple[MemoryEntry, ...]:
        """One member's entries, in notebook order; none raises."""
        return self.notebook_for(member).entries

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "crew_memory",
            "slice": MEMORY_SLICE,
            "members": list(self.members()),
            "entry_ids": [
                e.entry_id for e in self.entries() if e.entry_id],
            "entry_count": len(self.entries()),
        }


def validate_memory(data: Any, *, require_example: bool = False) -> CrewMemory:
    """Validate one memory mapping into a CrewMemory.

    The mapping names a ``schema`` (the memory
    schema word) and a ``notebooks`` list. Every
    notebook is validated, then the whole is
    judged: one notebook per member, entry ids
    unique across the memory. With
    ``require_example`` the shipped example is
    held to its pinned shape: the three pinned
    members' notebooks holding the three pinned
    entry ids, so the shipped facts include one
    member's hard-won fact findable by all.
    Problems raise :class:`ValidationError` or
    ``ValueError`` naming the problem.
    """
    if isinstance(data, CrewMemory):
        return data
    if not isinstance(data, dict):
        raise ValidationError(f"a crew memory must be a mapping, got {data!r}")
    unknown = set(data) - _MEMORY_KEYS
    if unknown:
        raise ValidationError(
            "unknown memory keys: %s" % ", ".join(sorted(unknown)))
    if data.get("schema") != MEMORY_SCHEMA:
        raise ValidationError(
            f"a crew memory must carry schema {MEMORY_SCHEMA!r}, "
            f"got {data.get('schema')!r}")
    if "notebooks" not in data:
        raise ValidationError("a crew memory is missing its notebooks")
    raw = data["notebooks"]
    if not isinstance(raw, (list, tuple)):
        raise ValidationError("a memory's notebooks must be a list")
    try:
        notebooks = tuple(validate_notebook(n) for n in raw)
        note = data.get("memory_note") or ""
        if not isinstance(note, str):
            raise ValidationError("a memory's note must be text")
        memory = CrewMemory(notebooks=notebooks, memory_note=note)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    if require_example:
        if memory.members() != _EXAMPLE_MEMBERS:
            raise ValidationError(
                "the shipped example memory's members are not "
                "the pinned three, in order")
        ids = tuple(e.entry_id for e in memory.entries())
        if ids != _EXAMPLE_ENTRY_IDS:
            raise ValidationError(
                "the shipped example memory's entry ids are not "
                "the pinned three, in shared order")
    return memory


def build_memory(memory: Any = None, **kwargs: Any) -> CrewMemory:
    """Build one validated memory, from a CrewMemory or notebooks."""
    if isinstance(memory, CrewMemory) and not kwargs:
        return memory
    if isinstance(memory, (list, tuple)) and not kwargs:
        return CrewMemory(notebooks=tuple(memory))
    if memory is None or isinstance(memory, dict):
        notebooks = kwargs.pop("notebooks", None)
        if isinstance(memory, dict):
            if "notebooks" in memory:
                return validate_memory(memory)
            notebooks = memory.get("notebooks", notebooks)
        if notebooks is None:
            raise ValueError("a memory needs its notebooks")
        return CrewMemory(notebooks=tuple(notebooks), **kwargs)
    raise ValueError(f"a crew memory is needed, got {memory!r}")


def _memory_from(data: Any, *, require_example: bool) -> CrewMemory:
    try:
        return validate_memory(data, require_example=require_example)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def load_crew_memory(data: Optional[Dict[str, Any]] = None) -> CrewMemory:
    """Load and validate the shipped example memory (or *data*).

    The shipped file is held to the example check:
    exactly the three pinned members' notebooks
    holding the three pinned entry ids.
    """
    raw = data if data is not None else load_resource(MEMORY_RESOURCE)
    return _memory_from(raw, require_example=True)


def load_crew_memory_file(path: Any) -> CrewMemory:
    """Load and validate a crew memory from a file at *path*.

    Any file in the memory shape, anywhere on
    disk, validated whole - a malformed file
    raises :class:`ValidationError` naming the
    problem, and a missing file raises
    ``FileNotFoundError``. The example check is
    not held: a real memory holds its own crew.
    """
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _memory_from(raw, require_example=False)


# ---------------------------------------------------------------------
# Search: derived from the held entries, never stored. Exact +
# substring matching over ids, titles, facts, tags and members.
# ---------------------------------------------------------------------


def _source_entries(source: Any) -> Tuple[MemoryEntry, ...]:
    if isinstance(source, CrewMemoryRegistry):
        return source.list_entries()
    if isinstance(source, CrewMemory):
        return source.entries()
    if isinstance(source, MemberNotebook):
        return tuple(sorted(
            source.entries,
            key=lambda e: (e.member, e.entry_id or "~", e.title)))
    raise ValueError(f"a crew memory is needed, got {source!r}")


def _entry_matches(entry: MemoryEntry, needle: str) -> bool:
    if needle in (entry.entry_id or "").lower():
        return True
    if needle in entry.member.lower():
        return True
    if needle in entry.title.lower():
        return True
    if needle in entry.fact.lower():
        return True
    return any(needle in tag or tag in needle for tag in entry.tags)


def search_memory(source: Any, query: Any, *, asking_member: Any = None) -> Tuple[MemoryEntry, ...]:
    """Search the shared memory for *query*, findable by all.

    Accepts a CrewMemory, a MemberNotebook or a
    CrewMemoryRegistry. The query's words must
    all match one entry (exact + substring over
    its id, member, title, fact and tags) for the
    entry to be found. ``asking_member``, when
    given, is validated as a member id and then
    deliberately does not narrow the search: a
    fact recorded by one member is found when
    queried as another - that is the roadmap's
    word, pinned by tests. Results are in shared
    order (member id, then entry id), derived
    from the held entries at call time.
    """
    if asking_member is not None:
        normalize_member_id(asking_member)
    if not isinstance(query, str) or not query.strip():
        raise ValueError("a search needs its query words")
    words = tuple(query.lower().split())
    return tuple(
        entry for entry in _source_entries(source)
        if all(_entry_matches(entry, word) for word in words))


def find_entries(source: Any, tag: Any) -> Tuple[MemoryEntry, ...]:
    """Every entry carrying one tag, in shared order, by all."""
    wanted = normalize_tag(tag)
    return tuple(
        entry for entry in _source_entries(source)
        if wanted in entry.tags)


# ---------------------------------------------------------------------
# The registry model: notebooks held entry by entry, in order.
# ---------------------------------------------------------------------


class CrewMemoryRegistry:
    """One session's crew memory, held entry by entry."""

    def __init__(self, memory: Any = None) -> None:
        self._notebooks: Dict[str, MemberNotebook] = {}
        self._next_entry = 1
        if memory is not None:
            self.register_memory(memory)

    def _fresh_entry_id(self, held_ids: Any) -> str:
        while f"entry-{self._next_entry}" in held_ids:
            self._next_entry += 1
        fresh = f"entry-{self._next_entry}"
        self._next_entry += 1
        return fresh

    def _held_ids(self) -> Any:
        return {
            e.entry_id for n in self._notebooks.values()
            for e in n.entries if e.entry_id}

    def register_entry(self, entry: Any) -> MemoryEntry:
        """Register one entry into its member's notebook.

        The member's notebook is opened on first
        use. A duplicate entry id anywhere in the
        memory refuses, as does the same fact
        already standing in that member's notebook
        (the MemberNotebook judge enforces both
        notebook-local rules on every rebuild).
        """
        validated = build_entry(entry)
        if validated.entry_id is not None \
                and validated.entry_id in self._held_ids():
            raise ValueError(
                f"an entry named {validated.entry_id!r} already exists")
        if validated.entry_id is None:
            validated = replace(
                validated, entry_id=self._fresh_entry_id(self._held_ids()))
        notebook = self._notebooks.get(validated.member)
        entries = (notebook.entries if notebook else ()) + (validated,)
        self._notebooks[validated.member] = MemberNotebook(
            member=validated.member, entries=entries)
        return validated

    def register_notebook(self, notebook: Any) -> MemberNotebook:
        """Register every entry of one notebook, in order.

        A member who already holds a notebook here
        refuses: one notebook per member.
        """
        validated = build_notebook(notebook)
        if validated.member in self._notebooks:
            raise ValueError(
                f"{validated.member} already holds a notebook here")
        for entry in validated.entries:
            self.register_entry(entry)
        if validated.member not in self._notebooks:
            self._notebooks[validated.member] = validated
        return self._notebooks[validated.member]

    def register_memory(self, memory: Any) -> CrewMemory:
        """Register every notebook of one memory, in order."""
        if not isinstance(memory, CrewMemory):
            raise ValueError(f"a crew memory is needed, got {memory!r}")
        for notebook in memory.notebooks:
            self.register_notebook(notebook)
        return self.memory()

    def get_entry(self, entry_id: Any) -> MemoryEntry:
        """The entry one id names, in whichever notebook holds it."""
        wanted = normalize_member_id(entry_id)
        for entry in self.list_entries():
            if entry.entry_id == wanted:
                return entry
        raise KeyError(f"unknown entry: {wanted!r}")

    def get_notebook(self, member: Any) -> MemberNotebook:
        """One member's held notebook; a member with none raises."""
        wanted = normalize_member_id(member)
        if wanted not in self._notebooks:
            raise KeyError(f"no notebook for member: {wanted!r}")
        return self._notebooks[wanted]

    def list_notebooks(self) -> Tuple[MemberNotebook, ...]:
        """Every held notebook, in member order."""
        return tuple(self._notebooks[m] for m in sorted(self._notebooks))

    def list_entries(self) -> Tuple[MemoryEntry, ...]:
        """Every held entry, in shared order."""
        return self.memory().entries()

    def entries_for(self, member: Any) -> Tuple[MemoryEntry, ...]:
        """One member's held entries, in notebook order."""
        return self.get_notebook(member).entries

    def search(self, query: Any, *, asking_member: Any = None) -> Tuple[MemoryEntry, ...]:
        """Search every held notebook at once (see search_memory)."""
        return search_memory(self.memory(), query, asking_member=asking_member)

    def find_by_tag(self, tag: Any) -> Tuple[MemoryEntry, ...]:
        """Every held entry carrying one tag, in shared order."""
        return find_entries(self.memory(), tag)

    def memory(self) -> CrewMemory:
        """The held notebooks as one validated shared memory."""
        return CrewMemory(notebooks=self.list_notebooks())


# ---------------------------------------------------------------------
# Memory news, shaped as session records.
# ---------------------------------------------------------------------


def entry_record(entry: Any) -> Dict[str, Any]:
    """The session-news record of one entry."""
    current = entry if isinstance(entry, MemoryEntry) else build_entry(entry)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"{current.member} records a fact in their notebook: "
        f"{current.title}")
    return record


def notebook_record(notebook: Any) -> Dict[str, Any]:
    """The session-news record of one notebook."""
    current = notebook if isinstance(
        notebook, MemberNotebook) else build_notebook(notebook)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"{current.member}'s notebook holds "
        f"{len(current.entries)} fact(s) for the crew.")
    return record


def memory_record(memory: Any) -> Dict[str, Any]:
    """The session-news record of one shared memory."""
    current = memory if isinstance(memory, CrewMemory) else build_memory(memory)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"The crew memory holds {record['entry_count']} fact(s) "
        f"across {len(record['members'])} notebook(s), findable by all.")
    return record


def plain_words(entry: Any) -> str:
    """One entry, in one plain sentence."""
    current = entry if isinstance(entry, MemoryEntry) else build_entry(entry)
    return f"{current.member} remembers: {current.title} - {current.fact}"


# ---------------------------------------------------------------------
# Screens: the formatters and the shared /memory grammar.
# ---------------------------------------------------------------------


def _source_memory(source: Any) -> CrewMemory:
    if source is None:
        return load_crew_memory()
    if isinstance(source, CrewMemoryRegistry):
        return source.memory()
    if isinstance(source, CrewMemory):
        return source
    raise ValueError(f"a crew memory is needed, got {source!r}")


def format_entry(entry: Any) -> str:
    """One entry as a screen line, with its tags."""
    current = entry if isinstance(entry, MemoryEntry) else build_entry(entry)
    line = (
        f"{current.member} / {current.entry_id or '-'}: "
        f"{current.title} - {current.fact} "
        f"(from: {current.provenance})")
    if current.tags:
        line += f" [tags: {', '.join(current.tags)}]"
    return line


def format_entries(source: Any = None) -> str:
    """Every entry of the shared memory, in shared order."""
    memory = _source_memory(source)
    lines = [format_entry(entry) for entry in memory.entries()]
    if not lines:
        lines.append("No facts are held yet.")
    return "\n".join(lines)


def format_notebook(notebook: Any) -> str:
    """One notebook as screen lines: its member and its entries."""
    current = notebook if isinstance(
        notebook, MemberNotebook) else build_notebook(notebook)
    lines = [f"{current.member}'s notebook ({len(current.entries)} fact(s)):"]
    lines.extend(format_entry(entry) for entry in current.entries)
    if not current.entries:
        lines.append("No facts are held yet.")
    return "\n".join(lines)


def format_notebooks(source: Any = None) -> str:
    """Every notebook of the shared memory, in file order."""
    memory = _source_memory(source)
    if not memory.notebooks:
        return "No notebooks are held yet."
    return "\n".join(format_notebook(n) for n in memory.notebooks)


def format_memory_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /memory.

    With nothing named, the shipped example
    memory is shown - the example this slice
    ships - so the screen is never empty.
    """
    memory = _source_memory(source)
    lines = ["Crew memory (M-133) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_notebooks(memory))
    lines.append("")
    lines.append(format_entries(memory))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_memory_args(args: Any) -> Tuple[str, Optional[str]]:
    """Parse the /memory grammar both surfaces share.

    No words (or ``show`` / ``list``) shows the
    shared memory; ``show <member>`` shows one
    member's notebook; ``search <words>`` searches
    every notebook; ``tag <tag>`` finds by tag;
    ``entry <entry-id>`` shows one entry;
    ``members`` lists the notebook holders.
    Anything else is a usage error naming the
    grammar. Returns ``(action, value-or-None)``;
    for ``search`` the value is the query words
    joined by single spaces.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() in ("show", "list"):
        return ("show", None)
    words = text.split()
    head = words[0].lower()
    if head == "show" and len(words) == 2:
        try:
            return ("show", normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "search" and len(words) >= 2:
        return ("search", " ".join(words[1:]))
    if head == "tag" and len(words) == 2:
        try:
            return ("tag", normalize_tag(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "entry" and len(words) == 2:
        try:
            return ("entry", normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "members" and len(words) == 1:
        return ("members", None)
    if head in ("show", "search", "tag", "entry", "members", "list"):
        raise ValueError(USAGE)
    if len(words) == 1:
        try:
            return ("show", normalize_member_id(words[0]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
