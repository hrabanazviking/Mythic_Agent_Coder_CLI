"""Compaction glass-box (All-Features roadmap slice M-151).

Part VII continues. The roadmap's words:
``when context compacts, the summary is shown,
editable, and kept in the journal beside what it
replaced; nothing the coder "forgets" is
unrecoverable.``

What already shipped, and what this slice adds:

* Context already compacts in this repo, on three
  shipped roads. The context pruner
  (``agents/llm.py``) archives older complete turns
  to the VectorDB and journals a
  ``context_compacted`` checkpoint through the
  write-ahead journal (``core/journal.py``,
  M-010's session road); the context builder
  (``agents/context.py``) condenses low-priority
  turns through its summarizer into a recap
  message; and the bounded transcript
  (``core/transcript.py``) spills the oldest turns
  to disk when it runs over budget. The context
  compiler (``context/compiler.py``) assembles
  what the model sees, and the context budget
  account (M-147, ``core/context_budget.py``)
  already makes what is in the context - and why -
  visible as data, composing the shipped
  ``TokenEstimator`` (``context/budget.py``) BY
  IMPORT, as this slice does too. What none of
  those roads holds is the compaction itself as
  shown, editable DATA: the summary the coder can
  read, the material it replaced kept beside it,
  and an edit that never rewrites silently.
* This slice is that glass box, as a pure layer:
  a compaction record validated as data (what was
  compacted - the replaced material, kept whole or
  by journal reference; the summary that replaced
  it, held as its versions in order; and the
  record's journal position, beside what it
  replaced), a book holding records in held order,
  a panel DERIVED from the records in journal
  order (every record carried whole, its totals
  the records' own counts), the shipped data file
  (``mythic_agent/data/compaction_glassbox.yaml``)
  holding one example book in exactly the shape a
  real book file takes, a loader for a book file
  anywhere on disk, a road that builds a record
  from archived messages in the live pruner's own
  shape, records shaped as session news, and a
  small in-memory registry model whose edit road
  keeps every summary version. The agent layer
  owns holding a book for a session.

Honesty rules, enforced here and pinned by tests:

* **Nothing forgotten is unrecoverable.** A
  record holds its replaced material whole, or
  names the journal reference where the whole
  material stands (``replaced_ref``) - a record
  holding neither refuses. The record itself
  stands at a journal position, beside what it
  replaced: its ``journal_ref`` and
  ``journal_position`` name that place.
* **The summary is shown, and editable as
  data.** The current summary is the last of the
  record's summary versions, derived at call
  time. An edit APPENDS a new version: the
  original summary and every edit are all held,
  in order, forever - an edit is a new judged
  version, never a silent rewrite, and an edit
  that changes nothing refuses.
* **The panel is derived, never stored loose.**
  Its rows are the records carried whole, in
  journal order (journal position first, then
  record id), so two panels of one book stand in
  the same order. A stored panel whose rows,
  totals, counts or account disagree with the
  panel derived from its records refuses, and a
  stored record whose named counts or current
  summary disagree with its own versions and
  replaced material refuses too.
* **Data only - holding a record compacts no
  live context.** A record here is a validated
  record held as data: no live context is
  compacted, no model is called, no message is
  archived, and nothing persists beyond the
  session journal news the agent layer publishes.
* **Malformed refuses.** A duplicate record id
  in one book, two records at one journal
  position, and unknown keys in a record, a row,
  a panel or a book mapping all raise instead of
  being skipped or guessed at.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..context.budget import TokenEstimator
from ..resources import load_resource
from .crew_members import normalize_member_id
from .validation import ValidationError

__all__ = [
    "PLAIN_EXPLANATION",
    "COMPACTION_GLASSBOX_RESOURCE",
    "COMPACTION_GLASSBOX_SCHEMA",
    "COMPACTION_GLASSBOX_SLICE",
    "USAGE",
    "CompactionBook",
    "CompactionPanel",
    "CompactionPanelRow",
    "CompactionRecord",
    "CompactionRegistry",
    "CompactionSourceCount",
    "book_record",
    "build_book",
    "build_panel",
    "build_record",
    "build_row",
    "derive_panel",
    "edit_record",
    "format_compaction_glassbox_screen",
    "format_panel",
    "format_record",
    "format_records",
    "format_versions",
    "load_compaction_glassbox",
    "load_compaction_glassbox_file",
    "panel_plain_words",
    "panel_record",
    "parse_glassbox_args",
    "plain_words",
    "record_from_archived",
    "record_record",
    "validate_book",
    "validate_panel",
    "validate_record",
    "validate_row",
]

COMPACTION_GLASSBOX_SLICE = "M-151"

#: The packaged data resource holding the example book.
COMPACTION_GLASSBOX_RESOURCE = "compaction_glassbox.yaml"

#: The schema word a compaction-glassbox file must carry.
COMPACTION_GLASSBOX_SCHEMA = "mythic.compaction_glassbox/1"

_RECORD_KEYS = frozenset({
    "record_id", "id", "title", "name", "source",
    "replaced", "archived", "replaced_material",
    "replaced_ref", "journal_ref",
    "journal_position", "position",
    "summary", "summary_versions", "versions",
    "version_count", "replaced_count",
})

_ROW_KEYS = frozenset({
    "record_id", "id", "title", "source",
    "journal_ref", "journal_position", "position",
    "replaced_count", "version_count", "summary",
})

_SOURCE_COUNT_KEYS = frozenset({
    "source", "records", "count",
})

_PANEL_KEYS = frozenset({
    "panel_id", "id", "rows", "records",
    "total_records", "total", "total_replaced",
    "total_versions", "source_counts", "sources",
    "account", "statements",
})

_BOOK_KEYS = frozenset({"title", "name"})

_COMPACTION_GLASSBOX_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "canon_note", "guide", "records", "panels",
})

#: The shipped example book's title, held to this
#: by the loader's example check.
_EXAMPLE_TITLE = "Compaction glass-box at the M-150 slice boundary"

#: The shipped example's record ids, in held order,
#: pinned by the loader.
_EXAMPLE_RECORD_IDS = (
    "compact-pruner-boundary", "compact-archiver-boundary",
    "compact-summarizer-boundary")

#: The shipped example's journal positions, in held
#: order, pinned by the loader.
_EXAMPLE_POSITIONS = (12, 27, 41)

#: The shipped example's one panel id, and its rows
#: in journal order, pinned by the loader.
_EXAMPLE_PANEL_ID = "panel-m150-boundary"

_EXAMPLE_PANEL_ROW_IDS = (
    "compact-pruner-boundary", "compact-archiver-boundary",
    "compact-summarizer-boundary")

_EXAMPLE_PANEL_ACCOUNT = (
    "The panel holds 3 compaction records: "
    "context-pruner 1, history-archiver 1, "
    "context-summarizer 1.",
    "Together they replaced 5 pieces of context, "
    "kept whole or by journal reference beside what "
    "they replaced - nothing the coder forgets is "
    "unrecoverable.",
    "1 of them carries an edited summary: every "
    "version is held, in order, the original first.",
    "Summaries are shown and editable as data: an "
    "edit adds a new version and keeps every earlier "
    "version - never a silent rewrite.",
    "The panel is read off the held records at "
    "call time - it is derived, never stored "
    "loose.",
)

PLAIN_EXPLANATION = (
    "Compaction v2, glass-box: when context "
    "compacts, the summary is shown, editable, and "
    "kept in the journal beside what it replaced; "
    "nothing the coder forgets is unrecoverable. A "
    "compaction record names one compaction: what "
    "was compacted (the replaced material, kept "
    "whole or by journal reference), the summary "
    "that replaced it - held as its versions, in "
    "order, the current summary the last of them - "
    "its source, and its journal position, beside "
    "what it replaced. The panel is derived from "
    "the whole book - its rows the records carried "
    "whole, in journal order, and its totals the "
    "records' own counts - so a stored panel that "
    "disagrees refuses. An edit appends a new "
    "summary version and keeps every earlier one: "
    "the original and every edit are all held, in "
    "order, never a silent rewrite. This layer "
    "holds compactions as data only: it compacts "
    "no live context, calls no model, archives no "
    "message and persists nothing."
)

USAGE = (
    "Usage: /glassbox, /glassbox show, "
    "/glassbox record <record-id>, "
    "/glassbox versions <record-id>, "
    "/glassbox panel"
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


def _check_ref(value: Any, what: str) -> str:
    text = _clean_text(value, what)
    if len(text) > 300 or "\x00" in text:
        raise ValueError(
            f"{what} must be plain text of at most "
            f"300 characters, got {len(text)} characters")
    if any(ch.isspace() for ch in text):
        raise ValueError(
            f"{what} names no spaces, got {text!r}")
    return text


def _check_replaced(value: Any) -> Tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes)) \
            or not isinstance(value, (list, tuple)):
        raise ValueError(
            f"a record's replaced material must be a list "
            f"of pieces, got {value!r}")
    pieces = tuple(
        _check_long_text(p, "a piece of replaced material")
        for p in value)
    if len(pieces) > 32:
        raise ValueError(
            f"a record holds at most 32 pieces of replaced "
            f"material whole, got {len(pieces)} - hold the "
            f"rest by journal reference")
    return pieces


def _check_versions(value: Any) -> Tuple[str, ...]:
    if isinstance(value, (str, bytes)) \
            or not isinstance(value, (list, tuple)):
        raise ValueError(
            f"a record's summary versions must be a list, "
            f"got {value!r}")
    versions = tuple(
        _check_long_text(v, "a summary version") for v in value)
    if not versions:
        raise ValueError(
            "a record carries at least one summary version - "
            "the summary that replaced the material")
    if len(versions) > 16:
        raise ValueError(
            f"a record carries at most 16 summary versions, "
            f"got {len(versions)}")
    for earlier, later in zip(versions, versions[1:]):
        if earlier == later:
            raise ValueError(
                "a summary version repeats the version "
                "before it - an edit that changes nothing "
                "is no version")
    return versions


def _estimate_tokens(text: str) -> int:
    """One text's token count, off the shipped estimator.

    Composed BY IMPORT from the shipped context
    budget road (``context/budget.py``), with
    tiktoken declined - the deterministic heuristic
    backend - so a figure read here is the same on
    every machine, exactly as M-147 reads it.
    """
    return TokenEstimator(prefer_tiktoken=False).count(text)


# ---------------------------------------------------------------------
# The record: one compaction, as data - what it replaced,
# the summary that stands in its place, its journal position.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class CompactionRecord:
    """One compaction, as a validated record.

    ``title`` names the compaction; ``source`` names
    the shipped road that compacted (the context
    pruner, the history archiver, the context
    summarizer); ``replaced`` is the material the
    summary replaced, kept whole, piece by piece -
    or, when the whole material stands elsewhere,
    ``replaced_ref`` names the journal reference
    where it stands, and one of the two must hold
    or the record refuses: nothing forgotten is
    unrecoverable. ``journal_ref`` and
    ``journal_position`` name the record's place in
    the journal, beside what it replaced.
    ``summary_versions`` holds the summary as its
    versions, in order: the first is the summary as
    compaction wrote it, and every edit appends a
    new one - the current summary is the last,
    derived at call time, and no version is ever
    rewritten or dropped.
    """

    title: str
    source: str
    journal_ref: str
    journal_position: int
    summary_versions: Tuple[str, ...]
    replaced: Tuple[str, ...] = ()
    replaced_ref: Optional[str] = None
    record_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.record_id is not None:
            object.__setattr__(
                self, "record_id",
                normalize_member_id(self.record_id))
        object.__setattr__(
            self, "title", _check_title(self.title, "a record's title"))
        object.__setattr__(
            self, "source",
            _check_title(self.source, "a record's source"))
        object.__setattr__(
            self, "journal_ref",
            _check_ref(self.journal_ref, "a record's journal reference"))
        object.__setattr__(
            self, "journal_position",
            _check_count(
                self.journal_position, "a record's journal position"))
        object.__setattr__(
            self, "summary_versions",
            _check_versions(self.summary_versions))
        replaced = _check_replaced(self.replaced)
        object.__setattr__(self, "replaced", replaced)
        if self.replaced_ref is not None:
            object.__setattr__(
                self, "replaced_ref",
                _check_ref(
                    self.replaced_ref,
                    "a record's replaced-material reference"))
        if not replaced and self.replaced_ref is None:
            raise ValueError(
                "a record holds its replaced material whole "
                "or names the journal reference where the "
                "whole material stands - a record holding "
                "neither forgets unrecoverably, and refuses")

    @property
    def summary(self) -> str:
        """The current summary: the last version, derived."""
        return self.summary_versions[-1]

    @property
    def version_count(self) -> int:
        """How many summary versions stand, derived."""
        return len(self.summary_versions)

    @property
    def replaced_count(self) -> int:
        """How many pieces stand replaced, derived."""
        return len(self.replaced)

    @property
    def edited(self) -> bool:
        """Whether the summary has ever been edited, derived."""
        return len(self.summary_versions) > 1

    @property
    def replaced_tokens(self) -> int:
        """The replaced material's token count, derived.

        Read off the shipped ``TokenEstimator`` at
        call time; a record holding its material by
        journal reference alone counts zero here -
        the material stands in the journal, not in
        this record.
        """
        return sum(_estimate_tokens(p) for p in self.replaced)

    @property
    def summary_tokens(self) -> int:
        """The current summary's token count, derived."""
        return _estimate_tokens(self.summary)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "compaction_glassbox_record",
            "slice": COMPACTION_GLASSBOX_SLICE,
            "record_id": self.record_id,
            "title": self.title,
            "source": self.source,
            "journal_ref": self.journal_ref,
            "journal_position": self.journal_position,
            "replaced": list(self.replaced),
            "replaced_ref": self.replaced_ref,
            "replaced_count": self.replaced_count,
            "summary": self.summary,
            "summary_versions": list(self.summary_versions),
            "version_count": self.version_count,
            "edited": self.edited,
        }


def validate_record(record: Any) -> CompactionRecord:
    """Validate one record into a CompactionRecord.

    Accepts a record or a mapping naming a ``title``
    (or ``name``), a ``source``, a ``journal_ref``,
    a ``journal_position`` (or ``position``), the
    summary - as ``summary_versions`` (or
    ``versions``), or as one ``summary``, which
    stands as the first and only version - the
    ``replaced`` material (or ``archived`` /
    ``replaced_material``) and/or a ``replaced_ref``,
    and an optional ``record_id`` (or ``id``). A
    mapping naming a ``summary`` beside
    ``summary_versions`` is judged: the named
    summary must be the versions' last, the current
    one, or the record refuses. Named
    ``version_count`` / ``replaced_count`` figures
    are judged against the record's own versions
    and material and refuse on disagreement.
    Naming two spellings of one field with
    different values refuses, and unknown keys
    refuse.
    """
    if isinstance(record, CompactionRecord):
        return record
    if not isinstance(record, dict):
        raise ValueError(
            f"a compaction record must be a mapping, "
            f"got {record!r}")
    unknown = set(record) - _RECORD_KEYS
    if unknown:
        raise ValueError(
            "unknown record keys: %s"
            % ", ".join(sorted(unknown)))
    title = _pick_any(record, ("title", "name"), "titles")
    if title is None:
        raise ValueError("a compaction record is missing its title")
    source = _pick_any(record, ("source",), "sources")
    if source is None:
        raise ValueError("a compaction record is missing its source")
    journal_ref = _pick_any(record, ("journal_ref",), "journal references")
    if journal_ref is None:
        raise ValueError(
            "a compaction record is missing its journal reference")
    position = _pick_any(
        record, ("journal_position", "position"), "journal positions")
    if position is None:
        raise ValueError(
            "a compaction record is missing its journal position")
    versions = _pick_any(
        record, ("summary_versions", "versions"), "summary versions")
    summary = _pick_any(record, ("summary",), "summaries")
    if versions is None and summary is None:
        raise ValueError(
            "a compaction record is missing its summary - "
            "the summary that replaced the material")
    if versions is None:
        versions = (summary,)
    else:
        versions = _check_versions(versions)
        if summary is not None and summary != versions[-1]:
            raise ValueError(
                "a stored summary disagrees with the last "
                "of its record's summary versions - the "
                "current summary is the last version, "
                "derived, never stored loose")
    replaced = _pick_any(
        record, ("replaced", "archived", "replaced_material"),
        "replaced material")
    replaced_ref = _pick_any(record, ("replaced_ref",), "replaced refs")
    kwargs: Dict[str, Any] = {
        "title": title, "source": source,
        "journal_ref": journal_ref, "journal_position": position,
        "summary_versions": versions}
    if replaced is not None:
        kwargs["replaced"] = replaced
    if replaced_ref is not None:
        kwargs["replaced_ref"] = replaced_ref
    record_id = _pick_any(record, ("record_id", "id"), "record ids")
    if record_id is not None:
        kwargs["record_id"] = record_id
    current = CompactionRecord(**kwargs)
    named_versions = _pick_any(record, ("version_count",), "version counts")
    if named_versions is not None \
            and _check_count(named_versions, "a version count") \
            != current.version_count:
        raise ValueError(
            "a stored version count disagrees with the "
            "record's own summary versions")
    named_replaced = _pick_any(record, ("replaced_count",), "replaced counts")
    if named_replaced is not None \
            and _check_count(named_replaced, "a replaced count") \
            != current.replaced_count:
        raise ValueError(
            "a stored replaced count disagrees with the "
            "record's own replaced material")
    return current


def build_record(record: Any = None, **kwargs: Any) -> CompactionRecord:
    """Build one validated record, from a mapping or field words."""
    if isinstance(record, CompactionRecord) and not kwargs:
        return record
    if isinstance(record, dict) or record is None:
        merged: Dict[str, Any] = {}
        if isinstance(record, dict):
            merged.update(record)
        merged.update(kwargs)
        return validate_record(merged)
    raise ValueError(
        f"a compaction record must be a mapping, got {record!r}")


def edit_record(record: Any, new_summary: Any) -> CompactionRecord:
    """Edit one record's summary: a new version, appended.

    The edited record carries every version the
    record already held, in order, with the new
    summary standing last as the current one - the
    original and every earlier edit are kept, so
    nothing an edit replaces is unrecoverable
    either. An edit naming the current summary
    refuses: it would change nothing, and a version
    that changes nothing is no version. The record
    itself is untouched - records are frozen data,
    and the edit is a new record.
    """
    current = _check_record_ref(record)
    text = _check_long_text(new_summary, "an edited summary")
    if text == current.summary:
        raise ValueError(
            "an edit naming the current summary changes "
            "nothing - an edit is a new version, and a "
            "version that changes nothing is no version")
    return replace(
        current,
        summary_versions=current.summary_versions + (text,))


def _check_record_ref(value: Any) -> CompactionRecord:
    if isinstance(value, CompactionRecord):
        return value
    if isinstance(value, dict):
        return validate_record(value)
    raise ValueError(f"a compaction record is needed, got {value!r}")


def _held_records(source: Any) -> Tuple[CompactionRecord, ...]:
    """The records one source holds, in held order."""
    if isinstance(source, CompactionBook):
        return source.records
    if isinstance(source, CompactionRegistry):
        return source.list_records()
    if isinstance(source, (list, tuple)):
        return tuple(_check_record_ref(r) for r in source)
    raise ValueError(f"compaction records are needed, got {source!r}")


def record_from_archived(archived: Any, *, title: Any, source: Any,
                         journal_ref: Any, journal_position: Any,
                         summary: Any = None,
                         record_id: Any = None) -> CompactionRecord:
    """Build one record from archived messages, in the live shape.

    The live pruner (``agents/llm.py``) archives
    older complete turns - message mappings with a
    ``role`` and a ``content`` - and journals its
    ``context_compacted`` checkpoint beside them.
    This road takes that same shape as data: each
    archived message becomes one piece of replaced
    material, kept whole as ``role: content`` (a
    bare string stands as its own piece), and with
    no *summary* named, a plain deterministic recap
    stands as the first version - no model is
    called, here or anywhere in this layer.
    """
    if isinstance(archived, (str, bytes)) \
            or not isinstance(archived, (list, tuple)):
        raise ValueError(
            f"archived messages must be a list, got {archived!r}")
    pieces = []
    for message in archived:
        if isinstance(message, str):
            pieces.append(message)
        elif isinstance(message, dict):
            role = message.get("role") or "message"
            content = message.get("content")
            if not isinstance(content, str):
                raise ValueError(
                    "an archived message names no text "
                    f"content, got {message!r}")
            pieces.append(f"{role}: {content}")
        else:
            raise ValueError(
                f"an archived message must be a mapping "
                f"or text, got {message!r}")
    if summary is None:
        summary = (
            f"Archived {len(pieces)} earlier messages "
            f"beside {journal_ref}.")
    kwargs: Dict[str, Any] = {
        "title": title, "source": source,
        "journal_ref": journal_ref,
        "journal_position": journal_position,
        "summary_versions": (summary,),
        "replaced": tuple(pieces)}
    if record_id is not None:
        kwargs["record_id"] = record_id
    return CompactionRecord(**kwargs)


# ---------------------------------------------------------------------
# The panel: the whole book accounted for, in journal order, derived.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class CompactionPanelRow:
    """One record carried whole into the panel.

    Every field is the record's own: its title, its
    source, its journal reference and position, how
    much it replaced, how many summary versions
    stand, and the current summary itself - shown,
    as the roadmap asks. :func:`validate_row` judged
    against a record refuses a row whose fields
    disagree with the row that record derives.
    """

    title: str
    source: str
    journal_ref: str
    journal_position: int
    replaced_count: int
    version_count: int
    summary: str
    record_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.record_id is not None:
            object.__setattr__(
                self, "record_id",
                normalize_member_id(self.record_id))
        object.__setattr__(
            self, "title", _check_title(self.title, "a row's title"))
        object.__setattr__(
            self, "source",
            _check_title(self.source, "a row's source"))
        object.__setattr__(
            self, "journal_ref",
            _check_ref(self.journal_ref, "a row's journal reference"))
        object.__setattr__(
            self, "journal_position",
            _check_count(
                self.journal_position, "a row's journal position"))
        object.__setattr__(
            self, "replaced_count",
            _check_count(
                self.replaced_count, "a row's replaced count"))
        object.__setattr__(
            self, "version_count",
            _check_count(
                self.version_count, "a row's version count"))
        if self.version_count < 1:
            raise ValueError(
                "a row's record carries at least one "
                "summary version")
        object.__setattr__(
            self, "summary",
            _check_long_text(self.summary, "a row's summary"))

    @property
    def sort_key(self) -> Tuple[int, str]:
        """This row's place in journal order (derived)."""
        return (self.journal_position, self.record_id or "")

    @property
    def edited(self) -> bool:
        """Whether this row's summary has been edited, derived."""
        return self.version_count > 1

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "compaction_glassbox_row",
            "slice": COMPACTION_GLASSBOX_SLICE,
            "record_id": self.record_id,
            "title": self.title,
            "source": self.source,
            "journal_ref": self.journal_ref,
            "journal_position": self.journal_position,
            "replaced_count": self.replaced_count,
            "version_count": self.version_count,
            "summary": self.summary,
        }


def _derive_row(record: CompactionRecord) -> CompactionPanelRow:
    return CompactionPanelRow(
        title=record.title, source=record.source,
        journal_ref=record.journal_ref,
        journal_position=record.journal_position,
        replaced_count=record.replaced_count,
        version_count=record.version_count,
        summary=record.summary,
        record_id=record.record_id)


def _check_row_ref(value: Any) -> CompactionPanelRow:
    if isinstance(value, CompactionPanelRow):
        return value
    if isinstance(value, CompactionRecord):
        return _derive_row(value)
    if isinstance(value, dict):
        unknown = set(value) - _ROW_KEYS
        if unknown:
            raise ValueError(
                "unknown row keys: %s" % ", ".join(sorted(unknown)))
        title = _pick_any(value, ("title",), "titles")
        if title is None:
            raise ValueError("a row is missing its title")
        source = _pick_any(value, ("source",), "sources")
        if source is None:
            raise ValueError("a row is missing its source")
        journal_ref = _pick_any(value, ("journal_ref",), "journal references")
        if journal_ref is None:
            raise ValueError("a row is missing its journal reference")
        position = _pick_any(
            value, ("journal_position", "position"), "journal positions")
        if position is None:
            raise ValueError("a row is missing its journal position")
        replaced_count = _pick_any(
            value, ("replaced_count",), "replaced counts")
        if replaced_count is None:
            raise ValueError("a row is missing its replaced count")
        version_count = _pick_any(
            value, ("version_count",), "version counts")
        if version_count is None:
            raise ValueError("a row is missing its version count")
        summary = _pick_any(value, ("summary",), "summaries")
        if summary is None:
            raise ValueError("a row is missing its summary")
        kwargs: Dict[str, Any] = {
            "title": title, "source": source,
            "journal_ref": journal_ref, "journal_position": position,
            "replaced_count": replaced_count,
            "version_count": version_count, "summary": summary}
        record_id = _pick_any(value, ("record_id", "id"), "record ids")
        if record_id is not None:
            kwargs["record_id"] = record_id
        return CompactionPanelRow(**kwargs)
    raise ValueError(f"a panel row is needed, got {value!r}")


def validate_row(row: Any, record: Any = None) -> CompactionPanelRow:
    """Validate one panel row into a CompactionPanelRow.

    Accepts a row, a record (whose derived row is
    the row), or a mapping naming a ``title``, a
    ``source``, a ``journal_ref``, a
    ``journal_position`` (or ``position``), a
    ``replaced_count``, a ``version_count``, a
    ``summary`` and an optional ``record_id`` (or
    ``id``). With *record* given, the row is judged
    against the row derived from that record: a
    stored row whose fields disagree with the
    derived row refuses.
    """
    current = _check_row_ref(row)
    if record is not None:
        derived = _derive_row(_check_record_ref(record))
        if current != derived:
            raise ValueError(
                "a stored row disagrees with the row "
                "derived from its record")
    return current


def build_row(row: Any = None, record: Any = None,
              **kwargs: Any) -> CompactionPanelRow:
    """Build one validated row, from a mapping or field words."""
    if isinstance(row, CompactionPanelRow) and not kwargs:
        return validate_row(row, record)
    if isinstance(row, dict) or row is None:
        merged: Dict[str, Any] = {}
        if isinstance(row, dict):
            merged.update(row)
        merged.update(kwargs)
        return validate_row(merged, record)
    return validate_row(row, record)


@dataclass(frozen=True)
class CompactionSourceCount:
    """One source's count in a panel: its records tallied."""

    source: str
    records: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "source",
            _check_title(self.source, "a source count's source"))
        object.__setattr__(
            self, "records",
            _check_count(self.records, "a source count's records"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "records": self.records,
        }


def _check_source_count_ref(value: Any) -> CompactionSourceCount:
    if isinstance(value, CompactionSourceCount):
        return value
    if isinstance(value, dict):
        unknown = set(value) - _SOURCE_COUNT_KEYS
        if unknown:
            raise ValueError(
                "unknown source-count keys: %s"
                % ", ".join(sorted(unknown)))
        source = _pick_any(value, ("source",), "sources")
        if source is None:
            raise ValueError("a source count is missing its source")
        records = _pick_any(value, ("records", "count"), "counts")
        if records is None:
            raise ValueError("a source count is missing its records")
        return CompactionSourceCount(source=source, records=records)
    raise ValueError(f"a source count is needed, got {value!r}")


def _panel_account(rows: Tuple[CompactionPanelRow, ...],
                   source_counts: Tuple[CompactionSourceCount, ...]
                   ) -> Tuple[str, ...]:
    if source_counts:
        by_source = ", ".join(
            f"{row.source} {row.records}" for row in source_counts)
        first = (
            f"The panel holds {len(rows)} compaction "
            f"records: {by_source}.")
    else:
        first = "The panel holds 0 compaction records."
    total_replaced = sum(row.replaced_count for row in rows)
    edited = sum(1 for row in rows if row.edited)
    if edited:
        third = (
            f"{edited} of them carries an edited summary: "
            f"every version is held, in order, the "
            f"original first." if edited == 1 else
            f"{edited} of them carry edited summaries: "
            f"every version is held, in order, the "
            f"originals first.")
    else:
        third = (
            "None of them carries an edited summary yet: "
            "each summary stands as its first version.")
    return (
        first,
        f"Together they replaced {total_replaced} pieces "
        f"of context, kept whole or by journal reference "
        f"beside what they replaced - nothing the coder "
        f"forgets is unrecoverable.",
        third,
        "Summaries are shown and editable as data: an "
        "edit adds a new version and keeps every earlier "
        "version - never a silent rewrite.",
        "The panel is read off the held records at "
        "call time - it is derived, never stored "
        "loose.",
    )


@dataclass(frozen=True)
class CompactionPanel:
    """The compaction glass-box panel, derived from the whole book.

    ``rows`` are the records carried whole, in
    journal order (journal position first, then
    record id - the order the journal itself keeps,
    beside what each record replaced);
    ``total_records`` is the record count;
    ``total_replaced`` and ``total_versions`` are
    the rows' own sums; ``source_counts`` are the
    per-source tallies in the order their sources
    first appear in the panel; ``account`` is read
    off those numbers. A panel whose rows stand out
    of journal order, or whose totals are not its
    own rows' sums, refuses at construction;
    :func:`validate_panel` judged against records
    refuses a stored panel that disagrees with the
    derived one.
    """

    rows: Tuple[CompactionPanelRow, ...] = ()
    total_records: int = 0
    total_replaced: int = 0
    total_versions: int = 0
    source_counts: Tuple[CompactionSourceCount, ...] = ()
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
        seen_positions = set()
        for row in rows:
            if row.record_id is not None:
                if row.record_id in seen_ids:
                    raise ValueError(
                        f"a panel row named {row.record_id!r} "
                        f"already exists")
                seen_ids.add(row.record_id)
            if row.journal_position in seen_positions:
                raise ValueError(
                    f"two panel rows stand at journal "
                    f"position {row.journal_position} - one "
                    f"compaction stands at one position, "
                    f"beside what it replaced")
            seen_positions.add(row.journal_position)
        keys = [row.sort_key for row in rows]
        if keys != sorted(keys):
            raise ValueError(
                "a panel's rows must stand in journal "
                "order (journal position, then record id)")
        object.__setattr__(self, "rows", rows)
        object.__setattr__(
            self, "total_records",
            _check_count(self.total_records, "a panel's total records"))
        object.__setattr__(
            self, "total_replaced",
            _check_count(self.total_replaced, "a panel's total replaced"))
        object.__setattr__(
            self, "total_versions",
            _check_count(self.total_versions, "a panel's total versions"))
        if isinstance(self.source_counts, (str, bytes)) \
                or not isinstance(self.source_counts, (list, tuple)):
            raise ValueError(
                f"a panel's source counts must be a list, "
                f"got {self.source_counts!r}")
        source_counts = tuple(
            _check_source_count_ref(c) for c in self.source_counts)
        seen_sources = set()
        for count in source_counts:
            if count.source in seen_sources:
                raise ValueError(
                    f"a source count named {count.source!r} "
                    f"already exists")
            seen_sources.add(count.source)
        object.__setattr__(self, "source_counts", source_counts)
        if self.total_records != len(rows):
            raise ValueError(
                "a panel's total records must be its own "
                "rows' count")
        if sum(r.replaced_count for r in rows) != self.total_replaced:
            raise ValueError(
                "a panel's total replaced must be its own "
                "rows' replaced counts summed")
        if sum(r.version_count for r in rows) != self.total_versions:
            raise ValueError(
                "a panel's total versions must be its own "
                "rows' version counts summed")
        if sum(c.records for c in source_counts) != self.total_records:
            raise ValueError(
                "a panel's source counts must sum to its "
                "own total records")
        object.__setattr__(self, "account", _check_account(self.account))

    def row_for(self, record_id: Any) -> CompactionPanelRow:
        """The panel row one record id names in this panel."""
        wanted = normalize_member_id(record_id)
        for row in self.rows:
            if row.record_id == wanted:
                return row
        raise KeyError(f"no row in the panel: record {wanted!r}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "compaction_glassbox_panel",
            "slice": COMPACTION_GLASSBOX_SLICE,
            "panel_id": self.panel_id,
            "rows": [row.to_record() for row in self.rows],
            "total_records": self.total_records,
            "total_replaced": self.total_replaced,
            "total_versions": self.total_versions,
            "source_counts": [c.to_record() for c in self.source_counts],
            "account": list(self.account),
        }


def derive_panel(source: Any) -> CompactionPanel:
    """Derive the panel from records.

    The rows are the records carried whole, sorted
    into journal order (journal position first, then
    record id), and the per-source tallies are read
    off the rows in the order their sources first
    appear in the panel. *source* is a book, a
    registry or the records themselves. An empty
    source refuses - a panel of nothing is no panel.
    """
    records = _held_records(source)
    if not records:
        raise ValueError("a panel needs at least one record")
    rows = tuple(sorted(
        (_derive_row(record) for record in records),
        key=lambda row: row.sort_key))
    order: list = []
    tally: Dict[str, int] = {}
    for row in rows:
        if row.source not in tally:
            tally[row.source] = 0
            order.append(row.source)
        tally[row.source] += 1
    source_counts = tuple(
        CompactionSourceCount(source=source, records=tally[source])
        for source in order)
    return CompactionPanel(
        rows=rows,
        total_records=len(records),
        total_replaced=sum(r.replaced_count for r in rows),
        total_versions=sum(r.version_count for r in rows),
        source_counts=source_counts,
        account=_panel_account(rows, source_counts))


def validate_panel(panel: Any, source: Any = None) -> CompactionPanel:
    """Validate one panel into a CompactionPanel.

    Accepts a panel or a mapping naming ``rows`` (or
    ``records``), a ``total_records`` (or ``total``),
    a ``total_replaced``, a ``total_versions``,
    ``source_counts`` (or ``sources``), an
    ``account`` (or ``statements``) and an optional
    ``panel_id`` (or ``id``). With *source* given
    (records), the panel is judged against the panel
    derived from those records: a stored panel whose
    rows, totals, source counts or account disagree
    with the derived panel refuses. A panel naming
    no account refuses too.
    """
    if isinstance(panel, CompactionPanel):
        current = panel
    elif isinstance(panel, dict):
        unknown = set(panel) - _PANEL_KEYS
        if unknown:
            raise ValueError(
                "unknown panel keys: %s" % ", ".join(sorted(unknown)))
        rows = _pick_any(panel, ("rows", "records"), "rows")
        if rows is None:
            raise ValueError("a panel is missing its rows")
        total = _pick_any(
            panel, ("total_records", "total"), "total records")
        if total is None:
            raise ValueError("a panel is missing its total records")
        total_replaced = _pick_any(
            panel, ("total_replaced",), "total replaced")
        if total_replaced is None:
            raise ValueError("a panel is missing its total replaced")
        total_versions = _pick_any(
            panel, ("total_versions",), "total versions")
        if total_versions is None:
            raise ValueError("a panel is missing its total versions")
        source_counts = _pick_any(
            panel, ("source_counts", "sources"), "source counts")
        if source_counts is None:
            raise ValueError("a panel is missing its source counts")
        account = _pick_any(panel, ("account", "statements"), "accounts")
        if account is None:
            raise ValueError("a panel names no account of its own")
        kwargs: Dict[str, Any] = {
            "rows": rows, "total_records": total,
            "total_replaced": total_replaced,
            "total_versions": total_versions,
            "source_counts": source_counts, "account": account}
        panel_id = _pick_any(panel, ("panel_id", "id"), "panel ids")
        if panel_id is not None:
            kwargs["panel_id"] = panel_id
        current = CompactionPanel(**kwargs)
    else:
        raise ValueError(f"a panel must be a mapping, got {panel!r}")
    if source is not None:
        derived = derive_panel(source)
        if (current.rows != derived.rows
                or current.total_records != derived.total_records
                or current.total_replaced != derived.total_replaced
                or current.total_versions != derived.total_versions
                or current.source_counts != derived.source_counts
                or current.account != derived.account):
            raise ValueError(
                "a stored panel disagrees with the panel "
                "derived from its records")
    return current


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> CompactionPanel:
    """Build one validated panel, from a mapping or field words."""
    if isinstance(panel, CompactionPanel) and not kwargs:
        return validate_panel(panel, source)
    if isinstance(panel, dict) or panel is None:
        merged: Dict[str, Any] = {}
        if isinstance(panel, dict):
            merged.update(panel)
        merged.update(kwargs)
        return validate_panel(merged, source)
    return validate_panel(panel, source)


# ---------------------------------------------------------------------
# The book: records in held order, panels judged.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class CompactionBook:
    """One compaction glass-box book: its records, in held order.

    ``records`` are the compaction records, in held
    order; ``panels`` are the book's derivations -
    panels of the book, judged against the book's
    records by :func:`validate_book`; ``canon_note``
    is the book's own note. This book is the book
    file's shape: the shipped example is one book,
    and a real book file is a new file in this shape.
    """

    title: str = ""
    records: Tuple[CompactionRecord, ...] = ()
    panels: Tuple[CompactionPanel, ...] = ()
    canon_note: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_title(self.title, "a book's title"))
        if isinstance(self.records, (str, bytes)) \
                or not isinstance(self.records, (list, tuple)):
            raise ValueError(
                f"a book's records must be a list of "
                f"compaction records, got {self.records!r}")
        records = tuple(_check_record_ref(r) for r in self.records)
        if not records:
            raise ValueError(
                "a compaction glass-box book holds at least one record")
        seen_ids = set()
        seen_positions = set()
        for record in records:
            if record.record_id is not None:
                if record.record_id in seen_ids:
                    raise ValueError(
                        f"a record named {record.record_id!r} "
                        f"already exists")
                seen_ids.add(record.record_id)
            if record.journal_position in seen_positions:
                raise ValueError(
                    f"two records stand at journal position "
                    f"{record.journal_position} - one "
                    f"compaction stands at one position, "
                    f"beside what it replaced")
            seen_positions.add(record.journal_position)
        object.__setattr__(self, "records", records)
        if isinstance(self.panels, (str, bytes)) \
                or not isinstance(self.panels, (list, tuple)):
            raise ValueError(
                f"a book's panels must be a list of panels, "
                f"got {self.panels!r}")
        panels = tuple(
            p if isinstance(p, CompactionPanel) else validate_panel(p)
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

    def record_for(self, record_id: Any) -> CompactionRecord:
        """The record one id names in this book."""
        wanted = normalize_member_id(record_id)
        for record in self.records:
            if record.record_id == wanted:
                return record
        raise KeyError(f"no record in the book: {wanted!r}")

    def records_for_source(
            self, source: Any) -> Tuple[CompactionRecord, ...]:
        """Every record of one source, in held order.

        A source word is read case-insensitively
        against the records' own sources - the source
        a record names is a plain word, not a closed
        set this slice invents.
        """
        wanted = _check_title(source, "a source word")
        return tuple(
            r for r in self.records
            if r.source.lower() == wanted.lower())

    def panel_for(self, panel_id: Any) -> CompactionPanel:
        """The stored panel one id names in this book."""
        wanted = normalize_member_id(panel_id)
        for panel in self.panels:
            if panel.panel_id == wanted:
                return panel
        raise KeyError(f"no panel in the book: {wanted!r}")

    def record_ids(self) -> Tuple[str, ...]:
        """Every held record id, in held order."""
        return tuple(r.record_id for r in self.records if r.record_id)

    def positions(self) -> Tuple[int, ...]:
        """Every held record's journal position, in held order."""
        return tuple(r.journal_position for r in self.records)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "compaction_glassbox_book",
            "slice": COMPACTION_GLASSBOX_SLICE,
            "title": self.title,
            "record_ids": list(self.record_ids()),
            "record_count": len(self.records),
            "panel_count": len(self.panels),
        }


def validate_book(data: Any, *, require_example: bool = False) -> CompactionBook:
    """Validate one compaction-glassbox mapping into a book.

    The mapping names a ``schema`` (the
    compaction-glassbox schema word), a ``guide``
    mapping (its ``title``), a ``records`` list and
    an optional ``panels`` list. Every record stands
    on its own validation, then the whole is judged:
    record ids unique, no two records at one journal
    position, and every stored panel judged against
    the book's own records. With ``require_example``
    the shipped example is held to its pinned shape:
    the pinned title, records and positions, and the
    panel's pinned rows and account word-for-word.
    Problems raise :class:`ValidationError` or
    ``ValueError``.
    """
    if isinstance(data, CompactionBook):
        return data
    if not isinstance(data, dict):
        raise ValidationError(
            f"a compaction glass-box book must be a mapping, got {data!r}")
    unknown = set(data) - _COMPACTION_GLASSBOX_KEYS
    if unknown:
        raise ValidationError(
            "unknown compaction-glassbox keys: %s"
            % ", ".join(sorted(unknown)))
    if data.get("schema") != COMPACTION_GLASSBOX_SCHEMA:
        raise ValidationError(
            f"a compaction glass-box book must carry schema "
            f"{COMPACTION_GLASSBOX_SCHEMA!r}, got {data.get('schema')!r}")
    records = _pick_any(data, ("records",), "records")
    if records is None:
        raise ValidationError("a compaction glass-box book is missing its records")
    if not isinstance(records, (list, tuple)):
        raise ValidationError("a compaction glass-box book's records must be a list")
    if data.get("panels") is not None \
            and not isinstance(data["panels"], (list, tuple)):
        raise ValidationError("a compaction glass-box book's panels must be a list")
    head = data.get("guide") or {}
    if not isinstance(head, dict):
        raise ValidationError("a compaction glass-box book's guide must be a mapping")
    unknown_head = set(head) - _BOOK_KEYS
    if unknown_head:
        raise ValidationError(
            "unknown guide keys: %s" % ", ".join(sorted(unknown_head)))
    try:
        title = _pick_any(head, ("title", "name"), "titles")
        if title is None:
            raise ValidationError("a compaction glass-box book is missing its title")
        note = data.get("canon_note") or ""
        if not isinstance(note, str):
            raise ValidationError("a compaction glass-box book's note must be text")
        book = CompactionBook(
            title=title, records=tuple(records),
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
                "the shipped example compaction glass-box book's title "
                "is not the pinned title")
        if book.record_ids() != _EXAMPLE_RECORD_IDS:
            raise ValidationError(
                "the shipped example's records are not "
                "the pinned records")
        if book.positions() != _EXAMPLE_POSITIONS:
            raise ValidationError(
                "the shipped example's journal positions are not "
                "the pinned positions")
        panel = book.panel_for(_EXAMPLE_PANEL_ID)
        if tuple(r.record_id for r in panel.rows) != _EXAMPLE_PANEL_ROW_IDS:
            raise ValidationError(
                "the shipped example panel does not name "
                "its pinned rows in journal order")
        if panel.account != _EXAMPLE_PANEL_ACCOUNT:
            raise ValidationError(
                "the shipped example panel does not carry "
                "its pinned account word-for-word")
        first = book.records[0]
        if first.source != "context-pruner" \
                or first.title != "The pruner's first pass":
            raise ValidationError(
                "the shipped example's first record is not "
                "its pinned pruner record")
    return book


def build_book(book: Any = None, **kwargs: Any) -> CompactionBook:
    """Build one validated book, from a mapping or field words."""
    if isinstance(book, CompactionBook) and not kwargs:
        return book
    if isinstance(book, dict):
        if "schema" in book:
            return validate_book(book)
        merged: Dict[str, Any] = dict(book)
        merged.update(kwargs)
        return CompactionBook(**merged)
    if book is None:
        return CompactionBook(**kwargs)
    raise ValueError(f"a compaction glass-box book is needed, got {book!r}")


def _book_from(data: Any, *, require_example: bool) -> CompactionBook:
    try:
        return validate_book(data, require_example=require_example)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def load_compaction_glassbox(
        data: Optional[Dict[str, Any]] = None) -> CompactionBook:
    """Load and validate the shipped example book (or *data*).

    The shipped file is held to the example check:
    the pinned title, record records and panel - the
    M-150 slice boundary book - so the shipped book
    covers the canon this slice exists to hold.
    """
    raw = data if data is not None else load_resource(COMPACTION_GLASSBOX_RESOURCE)
    return _book_from(raw, require_example=True)


def load_compaction_glassbox_file(path: Any) -> CompactionBook:
    """Load and validate a compaction-glassbox book from a file at *path*.

    Any file in the compaction-glassbox shape,
    anywhere on disk, validated whole - a malformed
    file raises :class:`ValidationError` naming the
    problem, and a missing file raises
    ``FileNotFoundError``. The example check is not
    held: a real book stands on its own records.
    """
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _book_from(raw, require_example=False)


# ---------------------------------------------------------------------
# The registry model: one book held record by record, in held order.
# ---------------------------------------------------------------------


class CompactionRegistry:
    """One session's compaction glass-box, held record by record.

    The registry holds compaction records, never
    panels: the panel is a derivation, read off held
    records at call time, so nothing here can hold a
    figure stale. An edit replaces the held record
    with its edited version - every earlier version
    kept, in order - under the same id and in the
    same held place.
    """

    def __init__(self, book: Any = None) -> None:
        self._title: Optional[str] = None
        self._records: Dict[str, CompactionRecord] = {}
        self._order: list = []
        self._next_record = 1
        if book is not None:
            self.register_book(book)

    def _fresh_record_id(self, held_ids: Any) -> str:
        while f"compact-{self._next_record}" in held_ids:
            self._next_record += 1
        fresh = f"compact-{self._next_record}"
        self._next_record += 1
        return fresh

    def register_record(self, record: Any) -> CompactionRecord:
        """Register one record into the held book.

        A record with no id is given a deterministic
        ``compact-N`` id. A record id already standing
        here refuses, as does a record standing at a
        journal position a held record already
        stands at - one compaction stands at one
        position, beside what it replaced.
        """
        validated = build_record(record)
        held_ids = set(self._records)
        if validated.record_id is not None \
                and validated.record_id in held_ids:
            raise ValueError(
                f"a record named "
                f"{validated.record_id!r} already exists")
        for held in self._records.values():
            if held.journal_position == validated.journal_position:
                raise ValueError(
                    f"a record already stands at journal "
                    f"position {validated.journal_position} - "
                    f"one compaction stands at one position")
        if validated.record_id is None:
            validated = replace(
                validated,
                record_id=self._fresh_record_id(held_ids))
        self._records[validated.record_id] = validated
        self._order.append(validated.record_id)
        return validated

    def register_book(self, book: Any) -> CompactionBook:
        """Register every record of one book, in order.

        The first book held sets the title; a later
        book under a different title refuses, as does
        a book naming a held record id or a held
        journal position. The book's panels are
        derivations, not holdings, and are not held.
        """
        validated = build_book(book)
        if self._title is not None and validated.title != self._title:
            raise ValueError(
                "this registry already holds a compaction "
                "glass-box book under a different title")
        for record in validated.records:
            if record.record_id in self._records:
                raise ValueError(
                    f"a record named "
                    f"{record.record_id!r} already exists")
        self._title = validated.title
        for record in validated.records:
            self.register_record(record)
        return self.book()

    def get_record(self, record_id: Any) -> CompactionRecord:
        """The record one id names among the held records."""
        wanted = normalize_member_id(record_id)
        if wanted not in self._records:
            raise KeyError(f"unknown compaction record: {wanted!r}")
        return self._records[wanted]

    def edit_summary(self, record_id: Any, new_summary: Any) -> CompactionRecord:
        """Edit one held record's summary: a new version, appended.

        The held record is replaced by its edited
        version - the same id, the same held place,
        every earlier summary version kept in order
        and the new summary standing last as the
        current one. The edit is data only: it
        compacts no live context and rewrites no
        earlier version. An unknown id raises
        KeyError; an edit that changes nothing
        refuses, as the pure edit road refuses.
        """
        wanted = normalize_member_id(record_id)
        if wanted not in self._records:
            raise KeyError(f"unknown compaction record: {wanted!r}")
        edited = edit_record(self._records[wanted], new_summary)
        self._records[wanted] = edited
        return edited

    def list_records(self) -> Tuple[CompactionRecord, ...]:
        """Every held record, in the order they were held."""
        return tuple(self._records[r] for r in self._order)

    def book(self) -> CompactionBook:
        """The held records as one validated book."""
        if self._title is None:
            raise ValueError("no compaction glass-box book is held yet")
        return CompactionBook(
            title=self._title, records=self.list_records())

    def panel(self) -> CompactionPanel:
        """Derive the panel of the held records, at call time."""
        return derive_panel(self)


# ---------------------------------------------------------------------
# Glass-box news, shaped as session records.
# ---------------------------------------------------------------------


def record_record(record: Any) -> Dict[str, Any]:
    """The session-news record of one compaction record."""
    current = record if isinstance(record, CompactionRecord) \
        else build_record(record)
    news = current.to_record()
    news["news"] = True
    news["headline"] = (
        f"{current.title} ({current.source}) stands at "
        f"{current.journal_ref} beside what it replaced: "
        f"summary version {current.version_count} shown - "
        f"{current.summary}")
    return news


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of one derived panel.

    With *source* given, the panel is first judged
    against the panel that source derives.
    """
    current = validate_panel(panel, source)
    news = current.to_record()
    news["news"] = True
    news["headline"] = (
        f"Compaction glass-box panel: {current.total_records} "
        f"records in journal order, {current.total_replaced} "
        f"pieces replaced, all recoverable.")
    return news


def book_record(book: Any) -> Dict[str, Any]:
    """The session-news record of one compaction glass-box book."""
    current = book if isinstance(book, CompactionBook) \
        else build_book(book)
    news = current.to_record()
    news["news"] = True
    news["headline"] = (
        f"Compaction glass-box {current.title}: "
        f"{news['record_count']} records named.")
    return news


def plain_words(record: Any) -> str:
    """One record, in one plain sentence."""
    current = record if isinstance(record, CompactionRecord) \
        else build_record(record)
    if current.replaced:
        kept = (
            f"{current.replaced_count} pieces kept whole")
    else:
        kept = f"the whole material kept at {current.replaced_ref}"
    return (
        f"{current.title} - {current.source}, at "
        f"{current.journal_ref} (journal position "
        f"{current.journal_position}), {kept}: "
        f"{current.summary}")


def panel_plain_words(source: Any) -> str:
    """The panel in plain words, in full.

    Accepts a CompactionPanel or a CompactionBook.
    The panel is told whole - its rows in journal
    order and its account.
    """
    if isinstance(source, CompactionPanel):
        panel = validate_panel(source)
        title = None
    elif isinstance(source, CompactionBook):
        panel = derive_panel(source)
        title = source.title
    else:
        raise ValueError(f"a compaction glass-box source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    lines.append("Compaction records, in journal order:")
    for row in panel.rows:
        lines.append(
            f"position {row.journal_position}: {row.title} "
            f"({row.source}) - {row.summary}")
    lines.extend(panel.account)
    return "\n".join(lines)


# ---------------------------------------------------------------------
# Screens: the formatters and the shared /glassbox grammar.
# ---------------------------------------------------------------------


def _source_book(source: Any) -> CompactionBook:
    if source is None:
        return load_compaction_glassbox()
    if isinstance(source, CompactionRegistry):
        return source.book()
    if isinstance(source, CompactionBook):
        return source
    raise ValueError(f"a compaction glass-box book is needed, got {source!r}")


def format_record(record: Any) -> str:
    """One record as a screen line."""
    current = record if isinstance(record, CompactionRecord) \
        else build_record(record)
    return (
        f"{current.record_id or '-'}: {current.title} - "
        f"{current.source} at {current.journal_ref} "
        f"(position {current.journal_position}): "
        f"{current.summary}")


def format_records(source: Any = None, source_word: Any = None) -> str:
    """Records of one book, in held order.

    With *source_word* given, only the records of
    that source are shown.
    """
    book = _source_book(source)
    records = book.records
    if source_word is not None:
        records = book.records_for_source(source_word)
    lines = [format_record(record) for record in records]
    if not lines:
        lines.append("No compaction records are held.")
    return "\n".join(lines)


def format_versions(record: Any) -> str:
    """One record's summary versions, in order, as a screen block.

    Every version is shown - the original first and
    the current summary last, marked as current -
    so an edit's whole history stands in the open:
    the glass box shows what the summary was, not
    only what it is.
    """
    current = record if isinstance(record, CompactionRecord) \
        else build_record(record)
    lines = [
        f"Summary versions of {current.record_id or '-'} "
        f"({current.title}), in order:"]
    for index, version in enumerate(current.summary_versions, start=1):
        marker = " (current)" if index == len(current.summary_versions) else ""
        lines.append(f"v{index}{marker}: {version}")
    return "\n".join(lines)


def format_panel(source: Any = None) -> str:
    """The panel as a screen block: every row and the account.

    Accepts a CompactionPanel or a CompactionBook; a
    book shows the panel it derives.
    """
    if isinstance(source, CompactionPanel):
        panel = validate_panel(source)
        lines: list = []
    else:
        book = _source_book(source)
        panel = derive_panel(book)
        lines = [f"Panel in {book.title}:"]
    lines.append("Compaction records, in journal order:")
    for row in panel.rows:
        lines.append(
            f"{row.record_id or '-'}: position "
            f"{row.journal_position} - {row.title} "
            f"({row.source}) at {row.journal_ref}: "
            f"{row.summary}")
    lines.extend(panel.account)
    return "\n".join(lines)


def format_compaction_glassbox_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /glassbox.

    With nothing named, the shipped example
    compaction glass-box book is shown - the example
    this slice ships - so the screen is never empty.
    """
    book = _source_book(source)
    lines = ["Compaction Glass-Box (M-151) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_records(book))
    lines.append("")
    lines.append(format_panel(book))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_glassbox_args(args: Any) -> Tuple[str, Any]:
    """Parse the /glassbox grammar both surfaces share.

    No words (or ``show`` / ``list``) shows the
    compaction glass-box book; ``record <record-id>``
    shows one record; ``versions <record-id>`` shows
    one record's summary versions, in order;
    ``panel`` shows the panel derived from the whole
    book. Anything else is a usage error naming the
    grammar. Returns ``(action, value-or-None)``.
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
    if head in ("record", "versions") and len(words) == 2:
        try:
            return (head, normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
