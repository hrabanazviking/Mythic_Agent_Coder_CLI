"""Instruction files unified (All-Features roadmap slice M-149).

Part VII continues. The roadmap's words:
``AGENTS.md (the AAIF standard), RULES.AI.md
(ours), CLAUDE.md and kin read in one precedence
order, shown in the panel with their sources -
foreign projects' files are honoured on their
own turf.``

What already shipped, and what this slice adds:

* Reading instruction files already has a shipped
  road: the context compiler's instruction
  resolver (``context/instructions.py``, Slices
  054/055 - :class:`InstructionResolver` discovers
  ``AGENTS.md``, ``CLAUDE.md``, ``.mythic.md``,
  ``.mythic``, ``.muserules``, ``.cursorrules``
  and ``.aider.rules.md`` inside one workspace,
  size-capped, with symlink and cross-workspace
  escapes blocked, and :func:`apply_precedence`
  merges the layers ``system > repo > dir >
  file``). That road READS and MERGES. What
  nothing holds is the one canon that NAMES every
  instruction file as data: every known filename
  with the turf it comes from, one precedence
  order across all of them, and the panel of the
  files in force, each with its source. The elder
  resolver's filename set also lacks
  ``RULES.AI.md`` - this house's own rules file -
  and that gap is part of this slice.
* This slice is that canon, as a pure layer: an
  instruction-file entry validated as data (one
  file in force - its filename in the closed set
  this canon names, the origin that filename
  truly carries, its path, its source, its layer,
  and the plain-words reason it stands), a book
  holding entries in held order, a panel DERIVED
  from the entries (every entry carried whole
  with its precedence rank, in precedence order,
  its totals the entries' own counts), the
  shipped data file
  (``mythic_agent/data/instruction_files.yaml``)
  holding one example book in exactly the shape a
  real book file takes, a loader for a book file
  anywhere on disk, a live scan road that walks a
  real workspace through the shipped
  :class:`InstructionResolver` BY IMPORT - with
  this canon's filename set, ``RULES.AI.md``
  included - and turns its discoveries into
  entries, records shaped as session news, and a
  small in-memory registry model. The agent layer
  owns holding a book for a session.

Honesty rules, enforced here and pinned by tests:

* **One precedence order, stated plainly.** A
  file's rank is derived, never stored on the
  entry: the layer ranks first, in the elder
  road's own order (``system``, then ``repo``,
  then ``dir``, then ``file`` - the higher layer
  wins), and inside one layer the filenames rank
  in :data:`INSTRUCTION_PRECEDENCE` order
  (``RULES.AI.md``, ``AGENTS.md``, ``.mythic.md``,
  ``.mythic``, ``CLAUDE.md``, ``.muserules``,
  ``.cursorrules``, ``.aider.rules.md``). The
  panel stands in that order; a stored panel
  whose rows, ranks, totals or account disagree
  with the panel derived from its entries
  refuses.
* **Every filename carries its true origin.**
  ``RULES.AI.md``, ``.mythic.md`` and ``.mythic``
  are ours; ``AGENTS.md`` is the AAIF standard;
  ``CLAUDE.md`` and the cursor / aider kin are
  foreign tools' files. An entry naming a
  filename with any other origin refuses - a
  foreign file is never claimed as ours, not even
  by a stored record.
* **Foreign files are honoured on their own
  turf.** A foreign file's directives are read in
  its own terms: this layer records where such a
  file stands and the precedence it carries, and
  never rewrites, renames or re-labels it. An
  entry holds no file content at all, so there is
  nothing here that could restate a foreign
  file's words as ours.
* **The elder road is composed, never
  duplicated.** The scan road imports the shipped
  resolver and its layer order; it re-implements
  no discovery, no size cap and no workspace
  guard. The one thing this canon adds to the
  road is the filename the elder set lacks.
* **Data only - holding a panel changes no
  file.** An entry here is a validated record
  held as data, and a panel is that account read
  off the entries: no file is written, renamed,
  moved or applied by this layer, beyond the
  reading the elder resolver already does when a
  workspace is scanned. Scanning a workspace
  leaves every file in it byte-identical.
* **Malformed refuses.** A duplicate entry id in
  one book, the same file named twice at one
  layer and path, a filename outside the canon,
  an origin that is not its filename's own, a
  layer outside the elder order, and unknown keys
  in an entry, a row, a panel or a book mapping
  all raise instead of being skipped or guessed
  at.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..context.instructions import (
    LAYER_ORDER,
    InstructionResolver,
)
from ..resources import load_resource
from .crew_members import normalize_member_id
from .validation import ValidationError

__all__ = [
    "PLAIN_EXPLANATION",
    "INSTRUCTION_FILES_RESOURCE",
    "INSTRUCTION_FILES_SCHEMA",
    "INSTRUCTION_FILES_SLICE",
    "INSTRUCTION_FILENAMES",
    "INSTRUCTION_LAYERS",
    "INSTRUCTION_ORIGINS",
    "INSTRUCTION_PRECEDENCE",
    "ORIGIN_KINDS",
    "USAGE",
    "InstructionFileEntry",
    "InstructionFilesBook",
    "InstructionFilesRegistry",
    "InstructionOriginCount",
    "InstructionPanel",
    "InstructionPanelRow",
    "book_record",
    "build_book",
    "build_entry",
    "build_panel",
    "build_row",
    "derive_panel",
    "entry_record",
    "format_entries",
    "format_entry",
    "format_instruction_files_screen",
    "format_panel",
    "load_instruction_files",
    "load_instruction_files_file",
    "normalize_filename",
    "normalize_layer",
    "normalize_origin",
    "origin_for",
    "panel_plain_words",
    "panel_record",
    "parse_instruction_files_args",
    "plain_words",
    "precedence_rank",
    "scan_workspace",
    "validate_book",
    "validate_entry",
    "validate_panel",
    "validate_row",
]

INSTRUCTION_FILES_SLICE = "M-149"

#: The packaged data resource holding the example book.
INSTRUCTION_FILES_RESOURCE = "instruction_files.yaml"

#: The schema word an instruction-files file must carry.
INSTRUCTION_FILES_SCHEMA = "mythic.instruction_files/1"

#: Every instruction filename this canon knows, in
#: precedence order within one layer: our own rules
#: file first, then the AAIF standard, then our own
#: mythic files, then the foreign kin in the elder
#: resolver's own order. The elder resolver's set is
#: this set minus ``RULES.AI.md`` - the gap this
#: slice closes - and a test pins exactly that.
INSTRUCTION_PRECEDENCE = (
    "RULES.AI.md", "AGENTS.md", ".mythic.md", ".mythic",
    "CLAUDE.md", ".muserules", ".cursorrules",
    ".aider.rules.md")

#: The known filenames, as a set-shaped tuple in
#: the same precedence order.
INSTRUCTION_FILENAMES = INSTRUCTION_PRECEDENCE

#: The turf each known filename comes from, as this
#: canon names it: ``ours`` (this house's own
#: files), ``standard`` (the AAIF standard file) or
#: ``foreign`` (another tool's file, honoured on
#: its own turf). An entry may name no other origin
#: for a filename than the one standing here.
INSTRUCTION_ORIGINS = {
    "RULES.AI.md": "ours",
    "AGENTS.md": "standard",
    ".mythic.md": "ours",
    ".mythic": "ours",
    "CLAUDE.md": "foreign",
    ".muserules": "foreign",
    ".cursorrules": "foreign",
    ".aider.rules.md": "foreign",
}

#: The origins one entry may carry, in panel order
#: of first mention: ours, the standard, foreign.
ORIGIN_KINDS = ("ours", "standard", "foreign")

#: The layers one entry may stand in, in the elder
#: road's precedence order (highest first): the
#: order :data:`LAYER_ORDER` of the shipped
#: instructions module numbers.
INSTRUCTION_LAYERS = ("system", "repo", "dir", "file")

#: The plain-words reason a scanned entry of each
#: origin carries, until a fuller reason is named
#: for it.
_ORIGIN_REASONS = {
    "ours": (
        "Our own instruction file, found by the "
        "workspace scan; its directives steer work "
        "here as our own rules."),
    "standard": (
        "The AAIF standard instruction file, found "
        "by the workspace scan; honoured as the "
        "shared standard it is."),
    "foreign": (
        "A foreign tool's instruction file, found "
        "by the workspace scan; honoured on its own "
        "turf, in its own terms, never rewritten or "
        "claimed as ours."),
}

_ENTRY_KEYS = frozenset({
    "file_id", "id", "filename", "name",
    "origin", "path", "source", "origin_source",
    "layer", "reason", "why", "rank", "precedence",
})

_ROW_KEYS = frozenset({
    "file_id", "id", "filename", "origin",
    "path", "source", "layer", "rank", "precedence",
})

_ORIGIN_COUNT_KEYS = frozenset({
    "origin", "files", "count",
})

_PANEL_KEYS = frozenset({
    "panel_id", "id", "rows", "entries",
    "total_files", "total", "origin_counts", "origins",
    "account", "statements",
})

_BOOK_KEYS = frozenset({"title", "name"})

_INSTRUCTION_FILES_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "canon_note", "guide", "entries", "files",
    "panels",
})

#: The shipped example book's title, held to this
#: by the loader's example check.
_EXAMPLE_TITLE = "Instruction files at the M-148 slice boundary"

#: The shipped example's entry ids, in held order,
#: pinned by the loader.
_EXAMPLE_ENTRY_IDS = (
    "instr-rules-root", "instr-agents-root",
    "instr-claude-root", "instr-mythic-package",
    "instr-cursor-package", "instr-mythic-plain")

#: The shipped example's filenames, in held order,
#: pinned by the loader.
_EXAMPLE_FILENAMES = (
    "RULES.AI.md", "AGENTS.md", "CLAUDE.md",
    ".mythic.md", ".cursorrules", ".mythic")

#: The shipped example's one panel id, and its rows
#: in precedence order, pinned by the loader.
_EXAMPLE_PANEL_ID = "panel-m148-boundary"

_EXAMPLE_PANEL_ROW_IDS = (
    "instr-rules-root", "instr-agents-root",
    "instr-claude-root", "instr-mythic-package",
    "instr-mythic-plain", "instr-cursor-package")

_EXAMPLE_PANEL_ACCOUNT = (
    "The panel holds 6 instruction file(s) in "
    "force: ours 3, standard 1, foreign 2.",
    "Precedence runs layer first (system, then "
    "repo, then dir, then file) and, inside one "
    "layer, RULES.AI.md, AGENTS.md, .mythic.md, "
    ".mythic, CLAUDE.md, .muserules, .cursorrules, "
    ".aider.rules.md.",
    "Foreign files are honoured on their own turf: "
    "read in their own terms, never rewritten, "
    "renamed or claimed as ours.",
    "The panel is read off the held entries at "
    "call time - it is derived, never stored "
    "loose.",
)

PLAIN_EXPLANATION = (
    "Instruction files unified: AGENTS.md (the "
    "AAIF standard), RULES.AI.md (ours), CLAUDE.md "
    "and kin read in one precedence order, shown "
    "in the panel with their sources. An entry "
    "names one instruction file in force: its "
    "filename in the canon this slice names, the "
    "origin that filename truly carries (ours, "
    "standard or foreign - a filename named with "
    "any other origin refuses, so a foreign file "
    "is never claimed as ours), its path, its "
    "source and its layer. A file's precedence "
    "rank is derived, never stored on the entry: "
    "the layer ranks first, in the shipped order "
    "system, repo, dir, file, and inside one layer "
    "the filenames rank as RULES.AI.md, AGENTS.md, "
    ".mythic.md, .mythic, CLAUDE.md, .muserules, "
    ".cursorrules, .aider.rules.md. The panel is "
    "derived from the whole book likewise - its "
    "rows the entries carried whole with their "
    "ranks, in precedence order, and its totals "
    "the entries' own counts - so a stored panel "
    "that disagrees refuses. Foreign files are "
    "honoured on their own turf: read in their own "
    "terms, never rewritten, renamed or claimed "
    "as ours. This layer holds the account as data "
    "only: it writes, renames and applies no file "
    "itself, beyond the reading the shipped "
    "instruction resolver already does when a "
    "workspace is scanned - and a scan leaves "
    "every file byte-identical."
)

USAGE = (
    "Usage: /instructionfiles, /instructionfiles show, "
    "/instructionfiles entry <file-id>, "
    "/instructionfiles origin <origin>, "
    "/instructionfiles layer <layer>, "
    "/instructionfiles panel"
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


def normalize_filename(value: Any) -> str:
    """The canonical instruction filename a word names.

    A filename is one of :data:`INSTRUCTION_PRECEDENCE`
    - the canon this slice names, the elder resolver's
    seven plus ``RULES.AI.md`` - read exactly, because
    filenames are case-sensitive on disk. Anything else
    raises, plainly naming the canon.
    """
    if isinstance(value, str):
        wanted = value.strip()
        if wanted in INSTRUCTION_ORIGINS:
            return wanted
    raise ValueError(
        "an instruction filename must be one of %s, got %r"
        % ("/".join(INSTRUCTION_PRECEDENCE), value))


def normalize_origin(value: Any) -> str:
    """The canonical origin kind a word names.

    An origin is one of :data:`ORIGIN_KINDS` - ``ours``,
    ``standard`` or ``foreign`` - read case-insensitively.
    Anything else raises, plainly naming the three.
    """
    if isinstance(value, str):
        wanted = value.strip().lower()
        if wanted in ORIGIN_KINDS:
            return wanted
    raise ValueError(
        "an instruction origin must be one of %s, got %r"
        % ("/".join(ORIGIN_KINDS), value))


def normalize_layer(value: Any) -> str:
    """The canonical layer a word names.

    A layer is one of :data:`INSTRUCTION_LAYERS` - the
    elder road's own order, ``system``, ``repo``,
    ``dir``, ``file`` - read case-insensitively.
    Anything else raises, plainly naming the four.
    """
    if isinstance(value, str):
        wanted = value.strip().lower()
        if wanted in LAYER_ORDER:
            return wanted
    raise ValueError(
        "an instruction layer must be one of %s, got %r"
        % ("/".join(INSTRUCTION_LAYERS), value))


def origin_for(filename: Any) -> str:
    """The true origin one known filename carries.

    The origin standing in :data:`INSTRUCTION_ORIGINS`
    for that filename - the only origin an entry for
    that filename may ever name.
    """
    return INSTRUCTION_ORIGINS[normalize_filename(filename)]


def precedence_rank(filename: Any, layer: Any) -> int:
    """The derived precedence rank of one file.

    The layer ranks first, in the elder road's own
    order (``system`` 0, ``repo`` 1, ``dir`` 2,
    ``file`` 3, from the shipped ``LAYER_ORDER``),
    times ten, plus the filename's position in
    :data:`INSTRUCTION_PRECEDENCE`. A lower rank
    outranks a higher one. The rank is read off the
    filename and layer alone - it is derived at call
    time, never stored on an entry.
    """
    name = normalize_filename(filename)
    layer_word = normalize_layer(layer)
    return LAYER_ORDER[layer_word] * 10 \
        + INSTRUCTION_PRECEDENCE.index(name)


def _check_path(value: Any) -> str:
    text = _clean_text(value, "an instruction file's path")
    if len(text) > 300 or "\x00" in text:
        raise ValueError(
            f"an instruction file's path must be plain text "
            f"of at most 300 characters, got {len(text)} characters")
    if any(ch.isspace() for ch in text):
        raise ValueError(
            f"an instruction file's path names no spaces, "
            f"got {text!r}")
    return text


# ---------------------------------------------------------------------
# The entry: one instruction file in force, as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class InstructionFileEntry:
    """One instruction file in force, as a validated record.

    ``filename`` is the file's name in the closed canon
    this slice names; ``origin`` is the turf that
    filename truly comes from, and must be the origin
    :func:`origin_for` names for it - a foreign file
    named as ours refuses at construction; ``path`` is
    where the file stands (workspace-relative, or the
    name a system-layer source stands under); ``source``
    names where the entry was read from; ``layer`` is
    the file's layer in the elder order; ``reason`` says
    in plain words WHY the file stands. The record
    names NO rank of its own: the rank is derived from
    the filename and layer at call time (see the
    ``rank`` property), so an entry can never claim a
    precedence its filename and layer do not give it.
    The record holds no file content, so no foreign
    file's words can be restated here as ours.
    """

    filename: str
    origin: str
    path: str
    source: str
    layer: str
    reason: str
    file_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.file_id is not None:
            object.__setattr__(
                self, "file_id",
                normalize_member_id(self.file_id))
        filename = normalize_filename(self.filename)
        object.__setattr__(self, "filename", filename)
        origin = normalize_origin(self.origin)
        if origin != INSTRUCTION_ORIGINS[filename]:
            raise ValueError(
                f"{filename} is a {INSTRUCTION_ORIGINS[filename]} "
                f"file, not {origin}: a filename carries its true "
                f"origin, and a foreign file is never claimed "
                f"as ours")
        object.__setattr__(self, "origin", origin)
        object.__setattr__(self, "path", _check_path(self.path))
        object.__setattr__(
            self, "source",
            _check_title(self.source, "an entry's source"))
        object.__setattr__(self, "layer", normalize_layer(self.layer))
        object.__setattr__(
            self, "reason",
            _check_long_text(self.reason, "an entry's reason"))

    @property
    def rank(self) -> int:
        """This entry's derived precedence rank (lower wins)."""
        return precedence_rank(self.filename, self.layer)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "instruction_files_entry",
            "slice": INSTRUCTION_FILES_SLICE,
            "file_id": self.file_id,
            "filename": self.filename,
            "origin": self.origin,
            "path": self.path,
            "source": self.source,
            "layer": self.layer,
            "rank": self.rank,
            "reason": self.reason,
        }


def validate_entry(entry: Any) -> InstructionFileEntry:
    """Validate one entry record into an InstructionFileEntry.

    Accepts an entry or a mapping naming a ``filename``
    (or ``name``), an ``origin``, a ``path``, a ``source``
    (or ``origin_source``), a ``layer``, a ``reason``
    (or ``why``), an optional ``file_id`` (or ``id``)
    and an optional stated ``rank`` (or ``precedence``).
    A stated rank is judged against the rank derived
    from the filename and layer: a stored rank that
    disagrees refuses, because the rank is derived,
    never stored loose. Naming two spellings of one
    field with different values refuses, and unknown
    keys refuse.
    """
    if isinstance(entry, InstructionFileEntry):
        return entry
    if not isinstance(entry, dict):
        raise ValueError(
            f"an entry record must be a mapping, "
            f"got {entry!r}")
    unknown = set(entry) - _ENTRY_KEYS
    if unknown:
        raise ValueError(
            "unknown entry keys: %s"
            % ", ".join(sorted(unknown)))
    filename = _pick_any(entry, ("filename", "name"), "filenames")
    if filename is None:
        raise ValueError("an entry record is missing its filename")
    origin = _pick_any(entry, ("origin",), "origins")
    if origin is None:
        raise ValueError("an entry record is missing its origin")
    path = _pick_any(entry, ("path",), "paths")
    if path is None:
        raise ValueError("an entry record is missing its path")
    source = _pick_any(entry, ("source", "origin_source"), "sources")
    if source is None:
        raise ValueError("an entry record is missing its source")
    layer = _pick_any(entry, ("layer",), "layers")
    if layer is None:
        raise ValueError("an entry record is missing its layer")
    reason = _pick_any(entry, ("reason", "why"), "reasons")
    if reason is None:
        raise ValueError("an entry record is missing its reason")
    kwargs: Dict[str, Any] = {
        "filename": filename, "origin": origin, "path": path,
        "source": source, "layer": layer, "reason": reason}
    file_id = _pick_any(entry, ("file_id", "id"), "file ids")
    if file_id is not None:
        kwargs["file_id"] = file_id
    current = InstructionFileEntry(**kwargs)
    stated = _pick_any(entry, ("rank", "precedence"), "ranks")
    if stated is not None and stated != current.rank:
        raise ValueError(
            "a stored entry rank disagrees with the rank "
            "derived from its filename and layer")
    return current


def build_entry(entry: Any = None, **kwargs: Any) -> InstructionFileEntry:
    """Build one validated entry, from a mapping or field words."""
    if isinstance(entry, InstructionFileEntry) and not kwargs:
        return entry
    if isinstance(entry, dict) or entry is None:
        merged: Dict[str, Any] = {}
        if isinstance(entry, dict):
            merged.update(entry)
        merged.update(kwargs)
        return validate_entry(merged)
    raise ValueError(
        f"an entry record must be a mapping, got {entry!r}")


def _check_entry_ref(value: Any) -> InstructionFileEntry:
    if isinstance(value, InstructionFileEntry):
        return value
    if isinstance(value, dict):
        return validate_entry(value)
    raise ValueError(f"an entry record is needed, got {value!r}")


def _held_entries(source: Any) -> Tuple[InstructionFileEntry, ...]:
    """The entries one source holds, in held order."""
    if isinstance(source, InstructionFilesBook):
        return source.entries
    if isinstance(source, InstructionFilesRegistry):
        return source.list_entries()
    if isinstance(source, (list, tuple)):
        return tuple(_check_entry_ref(e) for e in source)
    raise ValueError(f"entries are needed, got {source!r}")


# ---------------------------------------------------------------------
# The panel: the whole book accounted for, in precedence order, derived.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class InstructionPanelRow:
    """One entry carried whole into the panel, with its rank.

    Every field is the entry's own: its filename, its
    true origin, its path, its source and its layer,
    and the ``rank`` derived from that filename and
    layer. :func:`validate_row` judged against an entry
    refuses a row whose fields or rank disagree with
    the row that entry derives.
    """

    filename: str
    origin: str
    path: str
    source: str
    layer: str
    rank: int
    file_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.file_id is not None:
            object.__setattr__(
                self, "file_id",
                normalize_member_id(self.file_id))
        filename = normalize_filename(self.filename)
        object.__setattr__(self, "filename", filename)
        origin = normalize_origin(self.origin)
        if origin != INSTRUCTION_ORIGINS[filename]:
            raise ValueError(
                f"{filename} is a {INSTRUCTION_ORIGINS[filename]} "
                f"file, not {origin}: a filename carries its true "
                f"origin, and a foreign file is never claimed "
                f"as ours")
        object.__setattr__(self, "origin", origin)
        object.__setattr__(self, "path", _check_path(self.path))
        object.__setattr__(
            self, "source",
            _check_title(self.source, "a row's source"))
        layer = normalize_layer(self.layer)
        object.__setattr__(self, "layer", layer)
        object.__setattr__(
            self, "rank",
            _check_count(self.rank, "a row's rank"))
        if self.rank != precedence_rank(filename, layer):
            raise ValueError(
                "a panel row's rank must be the rank derived "
                "from its filename and layer")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "instruction_files_row",
            "slice": INSTRUCTION_FILES_SLICE,
            "file_id": self.file_id,
            "filename": self.filename,
            "origin": self.origin,
            "path": self.path,
            "source": self.source,
            "layer": self.layer,
            "rank": self.rank,
        }


def _derive_row(entry: InstructionFileEntry) -> InstructionPanelRow:
    return InstructionPanelRow(
        filename=entry.filename, origin=entry.origin,
        path=entry.path, source=entry.source, layer=entry.layer,
        rank=entry.rank, file_id=entry.file_id)


def _check_row_ref(value: Any) -> InstructionPanelRow:
    if isinstance(value, InstructionPanelRow):
        return value
    if isinstance(value, InstructionFileEntry):
        return _derive_row(value)
    if isinstance(value, dict):
        unknown = set(value) - _ROW_KEYS
        if unknown:
            raise ValueError(
                "unknown row keys: %s" % ", ".join(sorted(unknown)))
        filename = _pick_any(value, ("filename",), "filenames")
        if filename is None:
            raise ValueError("a row is missing its filename")
        origin = _pick_any(value, ("origin",), "origins")
        if origin is None:
            raise ValueError("a row is missing its origin")
        path = _pick_any(value, ("path",), "paths")
        if path is None:
            raise ValueError("a row is missing its path")
        source = _pick_any(value, ("source",), "sources")
        if source is None:
            raise ValueError("a row is missing its source")
        layer = _pick_any(value, ("layer",), "layers")
        if layer is None:
            raise ValueError("a row is missing its layer")
        rank = _pick_any(value, ("rank", "precedence"), "ranks")
        if rank is None:
            raise ValueError("a row is missing its rank")
        kwargs: Dict[str, Any] = {
            "filename": filename, "origin": origin, "path": path,
            "source": source, "layer": layer, "rank": rank}
        file_id = _pick_any(value, ("file_id", "id"), "file ids")
        if file_id is not None:
            kwargs["file_id"] = file_id
        return InstructionPanelRow(**kwargs)
    raise ValueError(f"a panel row is needed, got {value!r}")


def validate_row(row: Any, entry: Any = None) -> InstructionPanelRow:
    """Validate one panel row into an InstructionPanelRow.

    Accepts a row, an entry (whose derived row is the
    row), or a mapping naming a ``filename``, an
    ``origin``, a ``path``, a ``source``, a ``layer``,
    a ``rank`` (or ``precedence``) and an optional
    ``file_id`` (or ``id``). With *entry* given, the row
    is judged against the row derived from that entry:
    a stored row whose fields or rank disagree with
    the derived row refuses.
    """
    current = _check_row_ref(row)
    if entry is not None:
        derived = _derive_row(_check_entry_ref(entry))
        if current != derived:
            raise ValueError(
                "a stored row disagrees with the row "
                "derived from its entry")
    return current


def build_row(row: Any = None, entry: Any = None,
              **kwargs: Any) -> InstructionPanelRow:
    """Build one validated row, from a mapping or field words."""
    if isinstance(row, InstructionPanelRow) and not kwargs:
        return validate_row(row, entry)
    if isinstance(row, dict) or row is None:
        merged: Dict[str, Any] = {}
        if isinstance(row, dict):
            merged.update(row)
        merged.update(kwargs)
        return validate_row(merged, entry)
    return validate_row(row, entry)


@dataclass(frozen=True)
class InstructionOriginCount:
    """One origin's count in a panel: its files tallied."""

    origin: str
    files: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "origin", normalize_origin(self.origin))
        object.__setattr__(
            self, "files",
            _check_count(self.files, "an origin count's files"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "origin": self.origin,
            "files": self.files,
        }


def _check_origin_count_ref(value: Any) -> InstructionOriginCount:
    if isinstance(value, InstructionOriginCount):
        return value
    if isinstance(value, dict):
        unknown = set(value) - _ORIGIN_COUNT_KEYS
        if unknown:
            raise ValueError(
                "unknown origin-count keys: %s"
                % ", ".join(sorted(unknown)))
        origin = _pick_any(value, ("origin",), "origins")
        if origin is None:
            raise ValueError("an origin count is missing its origin")
        files = _pick_any(value, ("files", "count"), "counts")
        if files is None:
            raise ValueError("an origin count is missing its files")
        return InstructionOriginCount(origin=origin, files=files)
    raise ValueError(f"an origin count is needed, got {value!r}")


def _panel_account(rows: Tuple[InstructionPanelRow, ...],
                   origin_counts: Tuple[InstructionOriginCount, ...]
                   ) -> Tuple[str, ...]:
    if origin_counts:
        by_origin = ", ".join(
            f"{row.origin} {row.files}" for row in origin_counts)
        first = (
            f"The panel holds {len(rows)} instruction "
            f"file(s) in force: {by_origin}.")
    else:
        first = "The panel holds 0 instruction file(s) in force."
    return (
        first,
        "Precedence runs layer first (system, then "
        "repo, then dir, then file) and, inside one "
        "layer, RULES.AI.md, AGENTS.md, .mythic.md, "
        ".mythic, CLAUDE.md, .muserules, .cursorrules, "
        ".aider.rules.md.",
        "Foreign files are honoured on their own turf: "
        "read in their own terms, never rewritten, "
        "renamed or claimed as ours.",
        "The panel is read off the held entries at "
        "call time - it is derived, never stored "
        "loose.",
    )


@dataclass(frozen=True)
class InstructionPanel:
    """The instruction panel, derived from the whole book.

    ``rows`` are the entries carried whole with their
    derived ranks, in precedence order (rank first,
    then path, so two files of one name at one layer
    in different directories stand in a settled
    order); ``total_files`` is the entry count;
    ``origin_counts`` are the per-origin tallies in
    the order the origins first appear in the panel;
    ``account`` is read off those numbers. A panel
    whose rows stand out of precedence order, or
    whose totals are not its own rows' counts,
    refuses at construction; :func:`validate_panel`
    judged against entries refuses a stored panel
    that disagrees with the derived one.
    """

    rows: Tuple[InstructionPanelRow, ...] = ()
    total_files: int = 0
    origin_counts: Tuple[InstructionOriginCount, ...] = ()
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
        seen_ids = set()
        for row in rows:
            if row.file_id is not None:
                if row.file_id in seen_ids:
                    raise ValueError(
                        f"a panel row named {row.file_id!r} "
                        f"already exists")
                seen_ids.add(row.file_id)
        keys = [(row.rank, row.path) for row in rows]
        if keys != sorted(keys):
            raise ValueError(
                "a panel's rows must stand in precedence "
                "order (rank, then path)")
        object.__setattr__(self, "rows", rows)
        object.__setattr__(
            self, "total_files",
            _check_count(self.total_files, "a panel's total"))
        if isinstance(self.origin_counts, (str, bytes)) \
                or not isinstance(self.origin_counts, (list, tuple)):
            raise ValueError(
                f"a panel's origin counts must be a list, "
                f"got {self.origin_counts!r}")
        origin_counts = tuple(
            _check_origin_count_ref(c) for c in self.origin_counts)
        seen_origins = set()
        for count in origin_counts:
            if count.origin in seen_origins:
                raise ValueError(
                    f"an origin count named {count.origin!r} "
                    f"already exists")
            seen_origins.add(count.origin)
        object.__setattr__(self, "origin_counts", origin_counts)
        if self.total_files != len(rows):
            raise ValueError(
                "a panel's total must be its own rows' count")
        if sum(c.files for c in origin_counts) != self.total_files:
            raise ValueError(
                "a panel's origin counts must sum to its own total")
        object.__setattr__(self, "account", _check_account(self.account))

    def row_for(self, file_id: Any) -> InstructionPanelRow:
        """The panel row one file id names in this panel."""
        wanted = normalize_member_id(file_id)
        for row in self.rows:
            if row.file_id == wanted:
                return row
        raise KeyError(f"no row in the panel: file {wanted!r}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "instruction_files_panel",
            "slice": INSTRUCTION_FILES_SLICE,
            "panel_id": self.panel_id,
            "rows": [row.to_record() for row in self.rows],
            "total_files": self.total_files,
            "origin_counts": [c.to_record() for c in self.origin_counts],
            "account": list(self.account),
        }


def derive_panel(source: Any) -> InstructionPanel:
    """Derive the panel from entries.

    The rows are the entries carried whole with their
    derived ranks, sorted into precedence order (rank,
    then path), and the per-origin tallies are read off
    the rows in the order their origins first appear in
    the panel. *source* is a book, a registry or the
    entries themselves. An empty source refuses - a
    panel of nothing is no panel.
    """
    entries = _held_entries(source)
    if not entries:
        raise ValueError("a panel needs at least one entry")
    rows = tuple(sorted(
        (_derive_row(entry) for entry in entries),
        key=lambda row: (row.rank, row.path)))
    order: list = []
    tally: Dict[str, int] = {}
    for row in rows:
        if row.origin not in tally:
            tally[row.origin] = 0
            order.append(row.origin)
        tally[row.origin] += 1
    origin_counts = tuple(
        InstructionOriginCount(origin=origin, files=tally[origin])
        for origin in order)
    return InstructionPanel(
        rows=rows,
        total_files=len(entries),
        origin_counts=origin_counts,
        account=_panel_account(rows, origin_counts))


def validate_panel(panel: Any, source: Any = None) -> InstructionPanel:
    """Validate one panel into an InstructionPanel.

    Accepts a panel or a mapping naming ``rows`` (or
    ``entries``), a ``total_files`` (or ``total``),
    ``origin_counts`` (or ``origins``), an ``account``
    (or ``statements``) and an optional ``panel_id``
    (or ``id``). With *source* given (entries), the
    panel is judged against the panel derived from
    those entries: a stored panel whose rows, totals,
    origin counts or account disagree with the derived
    panel refuses. A panel naming no account refuses
    too.
    """
    if isinstance(panel, InstructionPanel):
        current = panel
    elif isinstance(panel, dict):
        unknown = set(panel) - _PANEL_KEYS
        if unknown:
            raise ValueError(
                "unknown panel keys: %s" % ", ".join(sorted(unknown)))
        rows = _pick_any(panel, ("rows", "entries"), "rows")
        if rows is None:
            raise ValueError("a panel is missing its rows")
        total = _pick_any(
            panel, ("total_files", "total"), "totals")
        if total is None:
            raise ValueError("a panel is missing its total files")
        origin_counts = _pick_any(
            panel, ("origin_counts", "origins"), "origin counts")
        if origin_counts is None:
            raise ValueError("a panel is missing its origin counts")
        account = _pick_any(panel, ("account", "statements"), "accounts")
        if account is None:
            raise ValueError("a panel names no account of its own")
        kwargs: Dict[str, Any] = {
            "rows": rows, "total_files": total,
            "origin_counts": origin_counts, "account": account}
        panel_id = _pick_any(panel, ("panel_id", "id"), "panel ids")
        if panel_id is not None:
            kwargs["panel_id"] = panel_id
        current = InstructionPanel(**kwargs)
    else:
        raise ValueError(f"a panel must be a mapping, got {panel!r}")
    if source is not None:
        derived = derive_panel(source)
        if (current.rows != derived.rows
                or current.total_files != derived.total_files
                or current.origin_counts != derived.origin_counts
                or current.account != derived.account):
            raise ValueError(
                "a stored panel disagrees with the panel "
                "derived from its entries")
    return current


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> InstructionPanel:
    """Build one validated panel, from a mapping or field words."""
    if isinstance(panel, InstructionPanel) and not kwargs:
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
class InstructionFilesBook:
    """One instruction-files book: its entries, in held order.

    ``entries`` are the entry records, in held order;
    ``panels`` are the book's derivations - panels of
    the book, judged against the book's records by
    :func:`validate_book`; ``canon_note`` is the book's
    own note. This book is the book file's shape: the
    shipped example is one book, and a real book file
    is a new file in this shape.
    """

    title: str = ""
    entries: Tuple[InstructionFileEntry, ...] = ()
    panels: Tuple[InstructionPanel, ...] = ()
    canon_note: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_title(self.title, "a book's title"))
        if isinstance(self.entries, (str, bytes)) \
                or not isinstance(self.entries, (list, tuple)):
            raise ValueError(
                f"a book's entries must be a list of entry "
                f"records, got {self.entries!r}")
        entries = tuple(_check_entry_ref(e) for e in self.entries)
        if not entries:
            raise ValueError(
                "an instruction-files book holds at least one entry")
        seen_ids = set()
        seen_files = set()
        for entry in entries:
            if entry.file_id is not None:
                if entry.file_id in seen_ids:
                    raise ValueError(
                        f"an entry named {entry.file_id!r} "
                        f"already exists")
                seen_ids.add(entry.file_id)
            key = (entry.filename, entry.layer, entry.path)
            if key in seen_files:
                raise ValueError(
                    f"the file {entry.path!r} already stands "
                    f"in this book at the {entry.layer} layer")
            seen_files.add(key)
        object.__setattr__(self, "entries", entries)
        if isinstance(self.panels, (str, bytes)) \
                or not isinstance(self.panels, (list, tuple)):
            raise ValueError(
                f"a book's panels must be a list of panels, "
                f"got {self.panels!r}")
        panels = tuple(
            p if isinstance(p, InstructionPanel) else validate_panel(p)
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

    def entry_for(self, file_id: Any) -> InstructionFileEntry:
        """The entry one id names in this book."""
        wanted = normalize_member_id(file_id)
        for entry in self.entries:
            if entry.file_id == wanted:
                return entry
        raise KeyError(f"no entry in the book: {wanted!r}")

    def entries_for_origin(
            self, origin: Any) -> Tuple[InstructionFileEntry, ...]:
        """Every entry of one origin, in held order."""
        wanted = normalize_origin(origin)
        return tuple(e for e in self.entries if e.origin == wanted)

    def entries_for_layer(
            self, layer: Any) -> Tuple[InstructionFileEntry, ...]:
        """Every entry at one layer, in held order."""
        wanted = normalize_layer(layer)
        return tuple(e for e in self.entries if e.layer == wanted)

    def panel_for(self, panel_id: Any) -> InstructionPanel:
        """The stored panel one id names in this book."""
        wanted = normalize_member_id(panel_id)
        for panel in self.panels:
            if panel.panel_id == wanted:
                return panel
        raise KeyError(f"no panel in the book: {wanted!r}")

    def entry_ids(self) -> Tuple[str, ...]:
        """Every held entry id, in held order."""
        return tuple(e.file_id for e in self.entries if e.file_id)

    def filenames(self) -> Tuple[str, ...]:
        """Every held entry's filename, in held order."""
        return tuple(e.filename for e in self.entries)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "instruction_files_book",
            "slice": INSTRUCTION_FILES_SLICE,
            "title": self.title,
            "entry_ids": list(self.entry_ids()),
            "entry_count": len(self.entries),
            "panel_count": len(self.panels),
        }


def validate_book(data: Any, *, require_example: bool = False) -> InstructionFilesBook:
    """Validate one instruction-files mapping into a book.

    The mapping names a ``schema`` (the instruction-files
    schema word), a ``guide`` mapping (its ``title``), an
    ``entries`` list (or ``files``) and an optional
    ``panels`` list. Every record stands on its own
    validation, then the whole is judged: entry ids
    unique, no file standing twice at one layer and
    path, and every stored panel judged against the
    book's own entries. With ``require_example`` the
    shipped example is held to its pinned shape: the
    pinned title, records and filenames, and the
    panel's pinned rows and account word-for-word.
    Problems raise :class:`ValidationError` or
    ``ValueError``.
    """
    if isinstance(data, InstructionFilesBook):
        return data
    if not isinstance(data, dict):
        raise ValidationError(
            f"an instruction-files book must be a mapping, got {data!r}")
    unknown = set(data) - _INSTRUCTION_FILES_KEYS
    if unknown:
        raise ValidationError(
            "unknown instruction-files keys: %s"
            % ", ".join(sorted(unknown)))
    if data.get("schema") != INSTRUCTION_FILES_SCHEMA:
        raise ValidationError(
            f"an instruction-files book must carry schema "
            f"{INSTRUCTION_FILES_SCHEMA!r}, got {data.get('schema')!r}")
    entries = _pick_any(data, ("entries", "files"), "entries")
    if entries is None:
        raise ValidationError("an instruction-files book is missing its entries")
    if not isinstance(entries, (list, tuple)):
        raise ValidationError("an instruction-files book's entries must be a list")
    if data.get("panels") is not None \
            and not isinstance(data["panels"], (list, tuple)):
        raise ValidationError("an instruction-files book's panels must be a list")
    head = data.get("guide") or {}
    if not isinstance(head, dict):
        raise ValidationError("an instruction-files book's guide must be a mapping")
    unknown_head = set(head) - _BOOK_KEYS
    if unknown_head:
        raise ValidationError(
            "unknown guide keys: %s" % ", ".join(sorted(unknown_head)))
    try:
        title = _pick_any(head, ("title", "name"), "titles")
        if title is None:
            raise ValidationError("an instruction-files book is missing its title")
        note = data.get("canon_note") or ""
        if not isinstance(note, str):
            raise ValidationError("an instruction-files book's note must be text")
        book = InstructionFilesBook(
            title=title, entries=tuple(entries),
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
                "the shipped example instruction-files book's title "
                "is not the pinned title")
        if book.entry_ids() != _EXAMPLE_ENTRY_IDS:
            raise ValidationError(
                "the shipped example's entries are not "
                "the pinned records")
        if book.filenames() != _EXAMPLE_FILENAMES:
            raise ValidationError(
                "the shipped example's filenames are not "
                "the pinned filenames")
        panel = book.panel_for(_EXAMPLE_PANEL_ID)
        if tuple(r.file_id for r in panel.rows) != _EXAMPLE_PANEL_ROW_IDS:
            raise ValidationError(
                "the shipped example panel does not name "
                "its pinned rows in precedence order")
        if panel.account != _EXAMPLE_PANEL_ACCOUNT:
            raise ValidationError(
                "the shipped example panel does not carry "
                "its pinned account word-for-word")
        first = book.entries[0]
        if first.filename != "RULES.AI.md" \
                or first.origin != "ours":
            raise ValidationError(
                "the shipped example's first entry is not "
                "its pinned RULES.AI.md entry")
    return book


def build_book(book: Any = None, **kwargs: Any) -> InstructionFilesBook:
    """Build one validated book, from a mapping or field words."""
    if isinstance(book, InstructionFilesBook) and not kwargs:
        return book
    if isinstance(book, dict):
        if "schema" in book:
            return validate_book(book)
        merged: Dict[str, Any] = dict(book)
        merged.update(kwargs)
        return InstructionFilesBook(**merged)
    if book is None:
        return InstructionFilesBook(**kwargs)
    raise ValueError(f"an instruction-files book is needed, got {book!r}")


def _book_from(data: Any, *, require_example: bool) -> InstructionFilesBook:
    try:
        return validate_book(data, require_example=require_example)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def load_instruction_files(
        data: Optional[Dict[str, Any]] = None) -> InstructionFilesBook:
    """Load and validate the shipped example book (or *data*).

    The shipped file is held to the example check:
    the pinned title, entry records and panel - the
    M-148 slice boundary book - so the shipped book
    covers the canon this slice exists to hold.
    """
    raw = data if data is not None else load_resource(INSTRUCTION_FILES_RESOURCE)
    return _book_from(raw, require_example=True)


def load_instruction_files_file(path: Any) -> InstructionFilesBook:
    """Load and validate an instruction-files book from a file at *path*.

    Any file in the instruction-files shape, anywhere
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
# The live scan road: a real workspace, through the shipped resolver.
# ---------------------------------------------------------------------


def _scan_file_id(relative: str) -> str:
    slug = "".join(
        ch.lower() if ch.isalnum() else "-"
        for ch in relative).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return f"scan-{slug}"


def scan_workspace(workspace: Any) -> Tuple[InstructionFileEntry, ...]:
    """Scan one real workspace into instruction-file entries.

    The workspace is walked by the shipped
    :class:`InstructionResolver` BY IMPORT, with this
    canon's filename set - the elder set plus
    ``RULES.AI.md``, the one filename the elder set
    lacks - so discovery, size caps and the workspace
    guards are the shipped road's own, never a second
    implementation. Each discovery becomes one entry:
    its filename, the true origin that filename
    carries, its workspace-relative path, the scan as
    its source, the layer the resolver found it at,
    and its origin's plain-words reason. Entries stand
    in held order (the resolver's own layer-then-path
    order). The scan reads through the elder road and
    writes nothing: every file in the workspace is
    left byte-identical, foreign files included, and
    no entry holds any file's content.
    """
    resolver = InstructionResolver(
        workspace, filenames=INSTRUCTION_PRECEDENCE)
    entries = []
    for found in resolver.discover():
        relative = str(found.provenance.get("relative")
                       or found.path.name)
        filename = found.path.name
        entries.append(InstructionFileEntry(
            filename=filename,
            origin=INSTRUCTION_ORIGINS[filename],
            path=relative,
            source="workspace scan",
            layer=found.layer,
            reason=_ORIGIN_REASONS[INSTRUCTION_ORIGINS[filename]],
            file_id=_scan_file_id(relative)))
    return tuple(entries)


# ---------------------------------------------------------------------
# The registry model: one book held entry by entry, in held order.
# ---------------------------------------------------------------------


class InstructionFilesRegistry:
    """One session's instruction-files book, held entry by entry.

    The registry holds entry records, never panels:
    the panel is a derivation, read off held entries
    at call time, so nothing here can hold a figure
    stale.
    """

    def __init__(self, book: Any = None) -> None:
        self._title: Optional[str] = None
        self._entries: Dict[str, InstructionFileEntry] = {}
        self._order: list = []
        self._next_entry = 1
        if book is not None:
            self.register_book(book)

    def _fresh_file_id(self, held_ids: Any) -> str:
        while f"instruction-{self._next_entry}" in held_ids:
            self._next_entry += 1
        fresh = f"instruction-{self._next_entry}"
        self._next_entry += 1
        return fresh

    def register_entry(self, entry: Any) -> InstructionFileEntry:
        """Register one entry into the held book.

        A record with no id is given a deterministic
        ``instruction-N`` id. A record id already
        standing here refuses, as does the same file
        already standing here at the same layer and
        path - one file in force is named once.
        """
        validated = build_entry(entry)
        held_ids = set(self._entries)
        if validated.file_id is not None \
                and validated.file_id in held_ids:
            raise ValueError(
                f"an entry named "
                f"{validated.file_id!r} already exists")
        for held in self._entries.values():
            if (held.filename, held.layer, held.path) == (
                    validated.filename, validated.layer,
                    validated.path):
                raise ValueError(
                    f"the file {validated.path!r} already "
                    f"stands here at the {validated.layer} layer")
        if validated.file_id is None:
            validated = replace(
                validated,
                file_id=self._fresh_file_id(held_ids))
        self._entries[validated.file_id] = validated
        self._order.append(validated.file_id)
        return validated

    def register_book(self, book: Any) -> InstructionFilesBook:
        """Register every entry of one book, in order.

        The first book held sets the title; a later
        book under a different title refuses, as does
        a book naming a held entry id or a held file.
        The book's panels are derivations, not
        holdings, and are not held.
        """
        validated = build_book(book)
        if self._title is not None and validated.title != self._title:
            raise ValueError(
                "this registry already holds an instruction-"
                "files book under a different title")
        for entry in validated.entries:
            if entry.file_id in self._entries:
                raise ValueError(
                    f"an entry named "
                    f"{entry.file_id!r} already exists")
        self._title = validated.title
        for entry in validated.entries:
            self.register_entry(entry)
        return self.book()

    def get_entry(self, file_id: Any) -> InstructionFileEntry:
        """The entry one id names among the held records."""
        wanted = normalize_member_id(file_id)
        if wanted not in self._entries:
            raise KeyError(f"unknown entry: {wanted!r}")
        return self._entries[wanted]

    def list_entries(self) -> Tuple[InstructionFileEntry, ...]:
        """Every held entry, in the order they were held."""
        return tuple(self._entries[e] for e in self._order)

    def book(self) -> InstructionFilesBook:
        """The held entries as one validated book."""
        if self._title is None:
            raise ValueError("no instruction-files book is held yet")
        return InstructionFilesBook(
            title=self._title, entries=self.list_entries())

    def panel(self) -> InstructionPanel:
        """Derive the panel of the held entries, at call time."""
        return derive_panel(self)


# ---------------------------------------------------------------------
# Instruction news, shaped as session records.
# ---------------------------------------------------------------------


def entry_record(entry: Any) -> Dict[str, Any]:
    """The session-news record of one entry."""
    current = entry if isinstance(entry, InstructionFileEntry) \
        else build_entry(entry)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"{current.filename} ({current.origin}) stands at the "
        f"{current.layer} layer, rank {current.rank}: "
        f"{current.reason}")
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
        f"Instruction panel: {current.total_files} "
        f"file(s) in force, in precedence order.")
    return record


def book_record(book: Any) -> Dict[str, Any]:
    """The session-news record of one instruction-files book."""
    current = book if isinstance(book, InstructionFilesBook) \
        else build_book(book)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Instruction files {current.title}: "
        f"{record['entry_count']} file(s) named.")
    return record


def plain_words(entry: Any) -> str:
    """One entry, in one plain sentence."""
    current = entry if isinstance(entry, InstructionFileEntry) \
        else build_entry(entry)
    return (
        f"{current.filename} - {current.origin}, "
        f"{current.layer} layer, rank {current.rank}, "
        f"at {current.path} from {current.source}: "
        f"{current.reason}")


def panel_plain_words(source: Any) -> str:
    """The panel in plain words, in full.

    Accepts an InstructionPanel or an
    InstructionFilesBook. The panel is told whole -
    its rows in precedence order and its account.
    """
    if isinstance(source, InstructionPanel):
        panel = validate_panel(source)
        title = None
    elif isinstance(source, InstructionFilesBook):
        panel = derive_panel(source)
        title = source.title
    else:
        raise ValueError(f"an instruction-files source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    lines.append("Instruction files in force, in precedence order:")
    for row in panel.rows:
        lines.append(
            f"rank {row.rank}: {row.filename} ({row.origin}) "
            f"at {row.path}, {row.layer} layer, "
            f"from {row.source}")
    lines.extend(panel.account)
    return "\n".join(lines)


# ---------------------------------------------------------------------
# Screens: the formatters and the shared /instructionfiles grammar.
# ---------------------------------------------------------------------


def _source_book(source: Any) -> InstructionFilesBook:
    if source is None:
        return load_instruction_files()
    if isinstance(source, InstructionFilesRegistry):
        return source.book()
    if isinstance(source, InstructionFilesBook):
        return source
    raise ValueError(f"an instruction-files book is needed, got {source!r}")


def format_entry(entry: Any) -> str:
    """One entry as a screen line."""
    current = entry if isinstance(entry, InstructionFileEntry) \
        else build_entry(entry)
    return (
        f"{current.file_id or '-'}: {current.filename} - "
        f"{current.origin}, {current.layer} layer, "
        f"rank {current.rank} ({current.path} "
        f"from {current.source})")


def format_entries(source: Any = None, origin: Any = None) -> str:
    """Entries of one book, in held order.

    With *origin* given, only the entries of that
    origin are shown.
    """
    book = _source_book(source)
    entries = book.entries
    if origin is not None:
        wanted = normalize_origin(origin)
        entries = tuple(e for e in entries if e.origin == wanted)
    lines = [format_entry(entry) for entry in entries]
    if not lines:
        lines.append("No instruction files are held.")
    return "\n".join(lines)


def format_panel(source: Any = None) -> str:
    """The panel as a screen block: every row and the account.

    Accepts an InstructionPanel or an
    InstructionFilesBook; a book shows the panel it
    derives.
    """
    if isinstance(source, InstructionPanel):
        panel = validate_panel(source)
        lines: list = []
    else:
        book = _source_book(source)
        panel = derive_panel(book)
        lines = [f"Panel in {book.title}:"]
    lines.append("Instruction files in force, in precedence order:")
    for row in panel.rows:
        lines.append(
            f"{row.file_id or '-'}: rank {row.rank} - "
            f"{row.filename} ({row.origin}) at {row.path}, "
            f"{row.layer} layer, from {row.source}")
    lines.extend(panel.account)
    return "\n".join(lines)


def format_instruction_files_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /instructionfiles.

    With nothing named, the shipped example
    instruction-files book is shown - the example
    this slice ships - so the screen is never empty.
    """
    book = _source_book(source)
    lines = ["Instruction files unified (M-149) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_entries(book))
    lines.append("")
    lines.append(format_panel(book))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_instruction_files_args(args: Any) -> Tuple[str, Any]:
    """Parse the /instructionfiles grammar both surfaces share.

    No words (or ``show`` / ``list``) shows the
    instruction-files book; ``entry <file-id>`` shows
    one entry; ``origin <origin>`` shows the entries
    of one origin; ``layer <layer>`` shows the
    entries at one layer; ``panel`` shows the panel
    derived from the whole book. Anything else is a
    usage error naming the grammar. Returns
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
    if head == "entry" and len(words) == 2:
        try:
            return (head, normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "origin" and len(words) == 2:
        try:
            return (head, normalize_origin(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "layer" and len(words) == 2:
        try:
            return (head, normalize_layer(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
