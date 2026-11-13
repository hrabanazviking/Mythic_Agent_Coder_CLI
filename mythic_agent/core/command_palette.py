"""Command palette (All-Features roadmap slice M-197).

Part VIII - The Beautiful Face - builds here. The
roadmap words: *Ctrl-K over everything - commands,
actions, navigation, settings - the one door
frequent hands use.*

What already ships, and what this slice adds:

* A Ctrl-K key already stands named in the
  shortcuts and the accessibility baseline, and a
  command palace already browses the commands as
  a court. What nothing held is *the palette
  itself, as a book*: every door held as checkable
  data - one card per entry, held whole with its
  title, its kind (a closed vocabulary - command,
  action, navigation, setting), its shortcut held
  honestly, and the search words it carries, named
  as data; the palette index, derived from those
  held entries; the views, which show every entry,
  the ready or the incomplete; and the notes on
  entries, held as data beside them - note,
  concern, praise and question named as stances,
  each feeding back to the user as data, never
  applied by this layer. This slice is that book,
  in its own module, standing in the M-196
  settings-room book shape. The M-171 charter
  names NO row for this slice - the grep stands
  empty and the slice tests pin that live - so
  there is no charter verdict for this slice to
  honour; the slice is built to the roadmap words
  alone, in the M-194/M-195 manner.

* An entry is held whole: the title it stands
  under, its kind, its shortcut - held honestly,
  an unknown shortcut standing empty, never
  invented - the search words it carries, named
  as data, and its detail. An entry naming no
  search words is held honestly with empty words:
  it stands incomplete, named in its gaps -
  completeness is judged from the held records
  alone, never claimed live.
* The palette index is DERIVED at call time from
  the held entries - never a second stored copy
  that could drift from the entries themselves.
  A stored index, completeness verdict or coverage
  judgement on any record refuses by name.
* The notes are held as data: a note record naming
  its entry, its stance - note, concern, praise
  or question, a closed vocabulary - and what it
  feeds back toward. A book holds at most one note
  record per entry stance. Holding a note applies
  none of it: the rule stands as data
  (:data:`PALETTE_RULE`) and a record claiming a
  command was actually executed, an action actually
  run, or a navigation actually taken, refuses
  BY NAME.
* The shipped data file holds one example book in
  exactly the shape a real palette file takes, a
  loader reads a palette file anywhere on disk,
  entries and views are shaped as session news,
  and a small in-memory registry holds records one
  by one. The agent layer owns holding a palette
  book for a session and telling from it. This
  layer reaches no live road: it executes nothing,
  runs no command, navigates nowhere, opens no
  network and writes nothing - it holds the palette
  as data and tells it.

Honesty rules, enforced here and pinned by tests:

* **Completeness from records alone.** Every
  completeness telling is derived from the held
  entry records; a claim of a live execution, run
  or navigation refuses by name.
* **Incomplete stands incomplete.** An entry
  naming no search words stands incomplete, named
  in its gaps - no words are invented for it.
* **Unknown stays unknown.** A shortcut that is
  not known stands empty on its entry - no key
  is invented for it.
* **The index is derived, never stored.** The
  palette index is derived from the held entries
  at call time; a stored index refuses by name, so
  it can never drift.
* **One entry per entry.** Two entries standing
  for one entry id refuse by name, and one note
  record stands per entry stance.
"""


from __future__ import annotations

__all__ = [
    "KINDS",
    "EXAMPLE_KEYWORDS",
    "STANCES",
    "INDEX_ACTION",
    "COMMAND_PALETTE_RESOURCE",
    "COMMAND_PALETTE_SCHEMA",
    "COMMAND_PALETTE_SLICE",
    "PALETTE_RULE",
    "PLAIN_EXPLANATION",
    "THE_COMMAND_PALETTE_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "VIEW_FILTERS",
    "READY_WORDS",
    "Any",
    "Dict",
    "List",
    "Optional",
    "EntryCard",
    "IndexEntry",
    "NoteRecord",
    "PaletteBook",
    "PaletteIndex",
    "PalettePanel",
    "PalettePanelRow",
    "CommandPaletteRegistry",
    "PaletteVerdict",
    "PaletteView",
    "TargetCount",
    "book_record",
    "build_book",
    "build_entry",
    "build_note",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "derive_index",
    "derive_panel",
    "derive_verdict",
    "first_note",
    "format_book",
    "format_entry",
    "format_index",
    "format_note",
    "format_palette_screen",
    "format_panel",
    "format_keywords",
    "format_verdict",
    "format_view",
    "entry_for_keywords",
    "entry_gaps",
    "entry_passes",
    "entry_plain_words",
    "entry_record",
    "entries_for_kind",
    "index_plain_words",
    "index_record",
    "inspect_entry_source",
    "note_for_entry",
    "note_plain_words",
    "note_record",
    "load_command_palette",
    "load_command_palette_file",
    "normalize_kind",
    "normalize_stance",
    "normalize_view_filter",
    "panel_plain_words",
    "panel_record",
    "parse_palette_args",
    "passing_entries",
    "plain_lines",
    "plain_words",
    "segment_of",
    "shown_entries",
    "total_entries",
    "validate_book",
    "validate_entry",
    "validate_note",
    "validate_panel",
    "validate_row",
    "validate_verdict",
    "validate_view",
    "verdict_plain_words",
    "verdict_record",
    "view_plain_words",
    "view_record",
]

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource

COMMAND_PALETTE_SCHEMA = "mythic.command_palette/1"
COMMAND_PALETTE_SLICE = "M-197"
THE_COMMAND_PALETTE_SLICE = COMMAND_PALETTE_SLICE
COMMAND_PALETTE_RESOURCE = "command_palette.yaml"
INDEX_ACTION = "index"
EXAMPLE_KEYWORDS = "the one door frequent hands use"
READY_WORDS = ("ready", "unready")
KINDS = ("command", "action", "navigation", "setting")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "ready", "unready")
VERDICT_WORDS = ("open", "strained", "shut")
PALETTE_RULE = (
    "command palette is held as data alone: "
    "holding, viewing and telling the palette "
    "executes nothing, runs no command, navigates "
    "nowhere, opens no network and writes "
    "nothing - completeness is judged from the "
    "held records alone, never claimed live")
PLAIN_EXPLANATION = (
    "Command palette (M-197): "
    "every door stands held as a card "
    "with its title, its kind, its shortcut "
    "honestly held, the search words it "
    "carries, and the views that arrange the "
    "entries - Ctrl-K over everything, "
    "commands, actions, navigation and "
    "settings, the one door frequent hands use.")
USAGE = (
    "Usage: /commandpalette | /commandpalette entry <entry-id> | "
    "/commandpalette keywords <keywords> | /commandpalette kind <kind> | "
    "/commandpalette view <view-id> | /commandpalette note <note-id> | "
    "/commandpalette index | /commandpalette panel | /commandpalette verdict")

_PROVENANCE = ("recorded_on", "actor", "source", "origin_session")
_ENTRY_KEYS = frozenset({
    "entry_id", "seq", "title", "kind", "shortcut",
    "keywords", "detail",
} | set(_PROVENANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_PROVENANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "entry_id", "stance", "target", "title",
    "detail",
} | set(_PROVENANCE))
_DERIVED_KEYS = frozenset({
    "standing", "ready", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "entries", "coverage", "covered", "uncovered"})
_LIVE_KEYS = (
    "live_entry", "live_view", "shows_entry",
    "show_entry", "shown_entry", "executes_command",
    "executed_command", "execute_command", "runs_action",
    "ran_action", "run_action", "navigates_now",
    "navigated", "navigate_now", "opens_palette",
    "opened_palette", "open_palette", "invokes_command",
    "invoked_command", "invoke_command", "executes_now",
    "runs_now", "performs_action", "performed_action",
    "opens_network", "writes_file", "write_file",
    "renders_now", "posts_note", "posted_note")


# ---------------------------------------------------------------------
# Small judges, in the sibling shape.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_keywords(value: Any) -> str:
    """Held search words: named as data, or honestly empty.

    An entry naming no search words is held with
    empty words and stands incomplete in its
    gaps; words that are not a string at all
    refuse.
    """
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError("keywords must be a string naming the search words")
    return value.strip()


def _check_measure(value: Any, what: str) -> str:
    """A held measure: a shortcut, named as data or honestly empty.

    An entry whose shortcut is not known is
    held with an empty shortcut: unknown stays unknown,
    and no key is invented for it. A shortcut that
    is not a string at all refuses.
    """
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError(f"{what} must be a string naming it, or empty")
    return value.strip()


def _check_count(value: Any, what: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{what} must be a whole number")
    if value < 0:
        raise ValueError(f"{what} must not be negative")
    return value


def _check_seq(value: Any, what: str = "a sequence") -> int:
    number = _check_count(value, what)
    if number < 1:
        raise ValueError(f"{what} must stand at 1 or later")
    return number


def _provenance(mapping: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key in _PROVENANCE:
        if key == "recorded_on":
            out[key] = _clean_text(mapping.get(key), "a recorded_on day")
        else:
            out[key] = _clean_text(mapping.get(key), f"a {key}")
    return out


def _needed(mapping: Dict[str, Any], allowed: frozenset,
            what: str) -> None:
    if not isinstance(mapping, dict):
        raise ValueError(f"{what} must be a mapping")
    for key in _LIVE_KEYS:
        if key in mapping:
            raise ValueError(
                f"{what} claims a live palette execution "
                f"({key!r} is named on it): "
                f"{PALETTE_RULE}")
    for key in mapping:
        if key in _DERIVED_KEYS:
            raise ValueError(
                f"{what} carries {key!r}, which is derived from its "
                f"own fields and never stored")
        if key not in allowed:
            raise ValueError(f"{what} carries unknown field {key!r}")


def normalize_kind(value: Any) -> str:
    kind = _clean_text(value, "a kind").lower()
    if kind not in KINDS:
        raise ValueError(
            f"kind {kind!r} is not one of the named kinds: "
            + ", ".join(KINDS))
    return kind


def normalize_stance(value: Any) -> str:
    stance = _clean_text(value, "an stance").lower()
    if stance not in STANCES:
        raise ValueError(
            f"stance {stance!r} is not one of the held "
            f"notes: " + ", ".join(STANCES))
    return stance


def normalize_view_filter(value: Any) -> str:
    view_filter = _clean_text(value, "a view filter").lower()
    if view_filter not in VIEW_FILTERS:
        raise ValueError(
            f"view filter {view_filter!r} is not one of the held "
            f"filters: " + ", ".join(VIEW_FILTERS))
    return view_filter


# ---------------------------------------------------------------------
# The held entry: one door, with the words that find it.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class EntryCard:
    """One palette entry, held as data with its search words.

    The entry names its plain title, the kind it
    lives in - one of the closed kind vocabulary -
    its shortcut, the search words it carries, named
    as data, and its detail. An entry naming no
    search words is held with empty words: it stands
    incomplete, named in its gaps, and no words are
    invented for it. The entry is local data alone -
    no live execution stands behind it: holding it
    executes nothing.
    """

    entry_id: str
    seq: int
    title: str
    kind: str
    shortcut: str = ""
    keywords: str = ""
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "entry_id", _clean_text(self.entry_id, "an entry id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a title"))
        object.__setattr__(self, "kind", normalize_kind(self.kind))
        object.__setattr__(
            self, "shortcut", _check_measure(self.shortcut, "a shortcut"))
        object.__setattr__(
            self, "keywords", _check_keywords(self.keywords))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "an entry detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.entry_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "entry_id": self.entry_id, "seq": self.seq,
            "title": self.title, "kind": self.kind,
            "shortcut": self.shortcut,
            "keywords": self.keywords, "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_entry_ref(value: Any) -> EntryCard:
    if not isinstance(value, EntryCard):
        raise ValueError("an entry must be an EntryCard")
    return value


def validate_entry(entry: Any) -> EntryCard:
    return _check_entry_ref(entry)


def build_entry(record: Any = None, **kwargs: Any) -> EntryCard:
    """Build one held entry from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, EntryCard):
        if kwargs:
            raise ValueError("an entry stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("an entry must be a mapping or an EntryCard")
    _needed(data, _ENTRY_KEYS, "an entry")
    return EntryCard(
        entry_id=data.get("entry_id"), seq=data.get("seq"),
        title=data.get("title"), kind=data.get("kind"),
        shortcut=data.get("shortcut"),
        keywords=data.get("keywords"), detail=data.get("detail"),
        **_provenance(data))


def entry_gaps(entry: Any) -> Tuple[str, ...]:
    """The gaps that keep an entry from completeness."""
    checked = _check_entry_ref(entry)
    return () if checked.keywords else ("no search words",)


def entry_passes(entry: Any) -> bool:
    return not entry_gaps(entry)


def plain_lines(entry: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the entry's own fields."""
    checked = _check_entry_ref(entry)
    return (
        f"Entry: {checked.title}",
        f"Kind: {checked.kind}",
        f"Shortcut: {checked.shortcut if checked.shortcut else 'unknown'}",
        f"Keywords: {checked.keywords if checked.keywords else 'none'}",
    )


def segment_of(entry: Any) -> str:
    checked = _check_entry_ref(entry)
    gaps = entry_gaps(checked)
    return (
        f"{checked.entry_id}: {checked.title} - kind: "
        f"'{checked.kind}' - shortcut: "
        f"'{checked.shortcut if checked.shortcut else 'unknown'}' - "
        f"keywords: '{checked.keywords if checked.keywords else 'none'}' - "
        f"detail: '{checked.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held stance: a note on an entry, as data.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class NoteRecord:
    """One palette note, held as data.

    The record names its entry, its stance and
    what it feeds back toward, with its title and
    its detail. One record stands per entry
    stance in a book. The record is data alone:
    holding it executes no command and runs no
    action, ever.
    """

    note_id: str
    seq: int
    entry_id: str
    stance: str
    target: str
    title: str
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "note_id", _clean_text(self.note_id, "a stance id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "entry_id", _clean_text(self.entry_id, "an entry id"))
        object.__setattr__(self, "stance", normalize_stance(self.stance))
        object.__setattr__(
            self, "target", _clean_text(self.target, "an stance target"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a stance title"))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a stance detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.note_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "note_id": self.note_id, "seq": self.seq,
            "entry_id": self.entry_id, "stance": self.stance,
            "target": self.target, "title": self.title,
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_note_ref(value: Any) -> NoteRecord:
    if not isinstance(value, NoteRecord):
        raise ValueError("a stance must be a NoteRecord")
    return value


def validate_note(stance: Any) -> NoteRecord:
    return _check_note_ref(stance)


def build_note(stance: Any = None, **kwargs: Any) -> NoteRecord:
    if stance is None:
        data = dict(kwargs)
    elif isinstance(stance, NoteRecord):
        if kwargs:
            raise ValueError("a stance stands whole or by fields, not both")
        return stance
    elif isinstance(stance, dict):
        data = dict(stance)
        data.update(kwargs)
    else:
        raise ValueError("a stance must be a mapping or a NoteRecord")
    _needed(data, _ACTION_KEYS, "a stance")
    return NoteRecord(
        note_id=data.get("note_id"), seq=data.get("seq"),
        entry_id=data.get("entry_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held view: which entries a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class PaletteView:
    """A view over the book: every entry, the ready, the rest."""

    view_id: str
    seq: int
    view_filter: str
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "view_id", _clean_text(self.view_id, "a view id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "view_filter", normalize_view_filter(self.view_filter))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a view detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    def to_record(self) -> Dict[str, Any]:
        record = {
            "view_id": self.view_id, "seq": self.seq,
            "view_filter": self.view_filter, "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_view_ref(value: Any) -> PaletteView:
    if not isinstance(value, PaletteView):
        raise ValueError("a view must be a PaletteView")
    return value


def validate_view(view: Any) -> PaletteView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> PaletteView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, PaletteView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or a PaletteView")
    _needed(data, _VIEW_KEYS, "a view")
    return PaletteView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_provenance(data))


def inspect_entry_source(piece: Any) -> Dict[str, Any]:
    """Name what one entry source piece is, without judging it."""
    if isinstance(piece, EntryCard):
        return {"kind": "entry", "entry_id": piece.entry_id}
    if isinstance(piece, dict):
        if "note_id" in piece:
            return {"kind": "note", "note_id": piece.get("note_id")}
        if "view_id" in piece:
            return {"kind": "view", "view_id": piece.get("view_id")}
        if "entry_id" in piece:
            return {"kind": "entry", "entry_id": piece.get("entry_id")}
    return {"kind": "unknown", "entry_id": None}


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class PalettePanelRow:
    item_id: str
    standing: str
    label: str
    segment: str
    recorded_on: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id, "standing": self.standing,
            "label": self.label, "segment": self.segment,
            "recorded_on": self.recorded_on,
        }


def _row_for_entry(entry: EntryCard) -> PalettePanelRow:
    return PalettePanelRow(
        item_id=entry.entry_id,
        standing="ready" if entry_passes(entry) else "unready",
        label=entry.title, segment=segment_of(entry),
        recorded_on=entry.recorded_on)


def _check_row_ref(value: Any) -> PalettePanelRow:
    if not isinstance(value, PalettePanelRow):
        raise ValueError("a panel row must be a PalettePanelRow")
    return value


def validate_row(row: Any, entry: Any = None) -> PalettePanelRow:
    checked = _check_row_ref(row)
    if entry is not None:
        derived = _row_for_entry(_check_entry_ref(entry))
        if checked != derived:
            raise ValueError(
                f"panel row {checked.item_id!r} does not agree with "
                f"the row derived from its entry")
    return checked


def build_row(row: Any = None, entry: Any = None,
              **kwargs: Any) -> PalettePanelRow:
    if entry is not None:
        derived = _row_for_entry(_check_entry_ref(entry))
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            PalettePanelRow(**kwargs))
        return validate_row(built, entry)
    if isinstance(row, PalettePanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in READY_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return PalettePanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on day"))
    if row is None and kwargs:
        return PalettePanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or a PalettePanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[PalettePanelRow, ...]
                 ) -> Tuple[TargetCount, ...]:
    counts: List[TargetCount] = []
    for standing in READY_WORDS:
        number = sum(1 for row in rows if row.standing == standing)
        if number:
            counts.append(TargetCount(standing=standing, items=number))
    return tuple(counts)


def _panel_account(total_items: int, total_shown: int,
                   passing_shown: int,
                   target_counts: Tuple[TargetCount, ...],
                   view_filter: str, as_of: str) -> Tuple[str, ...]:
    standing_words = ", ".join(
        f"{count.standing} {count.items}"
        for count in target_counts) or "none"
    return (
        f"The command palette book holds {total_items} entries as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {passing_shown} of the shown entries "
        f"stand ready.",
        "Rows stand in held order, the order the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its entry's own fields "
        "- the title, the kind, the shortcut honestly held "
        "and the search words it honestly carries - and no "
        "judgement is stored on any entry.",
        "Completeness is judged from the held records alone: "
        "an entry naming no search words stands unready, and the "
        "palette index is derived from the held entries, "
        "never stored where it could drift.",
    )


@dataclass(frozen=True)
class PalettePanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[PalettePanelRow, ...]
    total_items: int
    total_shown: int
    target_counts: Tuple[TargetCount, ...]
    as_of: str
    account: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "panel_id": self.panel_id, "view_id": self.view_id,
            "view_filter": self.view_filter,
            "rows": [row.to_record() for row in self.rows],
            "total_items": self.total_items,
            "total_shown": self.total_shown,
            "target_counts": [c.to_record() for c in self.target_counts],
            "as_of": self.as_of, "account": list(self.account),
        }


def _resolve_view(source: Any, view: Any) -> PaletteView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, PaletteView):
        return view
    return book.view_for(view)


def shown_entries(source: Any, view: Any = None
                   ) -> Tuple[EntryCard, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.entries
    if resolved.view_filter == "ready":
        return tuple(g for g in book.entries if entry_passes(g))
    return tuple(g for g in book.entries if not entry_passes(g))


def entries_for_kind(source: Any, kind: Any
                      ) -> Tuple[EntryCard, ...]:
    wanted = normalize_kind(kind)
    return tuple(
        g for g in _source_book(source).entries if g.kind == wanted)


def passing_entries(source: Any) -> Tuple[EntryCard, ...]:
    return tuple(
        g for g in _source_book(source).entries if entry_passes(g))


def total_entries(source: Any) -> int:
    return len(_source_book(source).entries)


def derive_panel(source: Any, view: Any = None) -> PalettePanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_entries(book, resolved)
    rows = tuple(_row_for_entry(entry) for entry in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.entries), default="")
    passing = sum(1 for g in shown if entry_passes(g))
    return PalettePanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.entries), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.entries), len(shown), passing, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> PalettePanel:
    if not isinstance(value, PalettePanel):
        raise ValueError("a panel must be a PalettePanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> PalettePanel:
    """Judge a stored panel against the panel derived from its book.

    Every derived field must agree; the stored
    panel's own name is its identity, not derived
    content (the M-182 lesson).
    """
    checked = _check_panel_ref(panel)
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(checked.view_id)
                if checked.view_id is not None else None)
        derived = derive_panel(book, view)
        for attr in ("view_id", "view_filter", "rows", "total_items",
                     "total_shown", "target_counts", "as_of", "account"):
            if getattr(checked, attr) != getattr(derived, attr):
                raise ValueError(
                    f"panel {checked.panel_id!r} disagrees with the "
                    f"panel derived from its book on {attr}")
    return checked


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> PalettePanel:
    if isinstance(panel, PalettePanel):
        if kwargs:
            raise ValueError("a panel stands whole or by fields, not both")
        return validate_panel(panel, source)
    if isinstance(panel, dict):
        data = dict(panel)
        data.update(kwargs)
        rows = tuple(build_row(row) for row in data.get("rows") or ())
        counts = tuple(
            TargetCount(
                standing=_clean_text(
                    c.get("standing"), "a standing count word").lower(),
                items=_check_count(c.get("items"), "a standing count"))
            for c in data.get("target_counts") or ()
            if isinstance(c, dict))
        built = PalettePanel(
            panel_id=_clean_text(data.get("panel_id"), "a panel id"),
            view_id=data.get("view_id"),
            view_filter=normalize_view_filter(data.get("view_filter")),
            rows=rows,
            total_items=_check_count(
                data.get("total_items"), "a total_items count"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            target_counts=counts,
            as_of=_clean_text(data.get("as_of"), "an as_of day"),
            account=_check_lines(data.get("account"), "the account"))
        return validate_panel(built, source)
    if panel is None and source is not None:
        return derive_panel(source, kwargs.get("view"))
    raise ValueError("a panel must be a mapping, a PalettePanel, or derived")


def _check_lines(value: Any, what: str) -> Tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError(f"{what} must be a list of lines")
    lines = []
    for line in value:
        lines.append(_clean_text(line, f"a line of {what}"))
    return tuple(lines)


def _verdict_word(total_shown: int, passing_shown: int) -> str:
    if total_shown > 0 and passing_shown == total_shown:
        return "open"
    if passing_shown == 0:
        return "shut"
    return "strained"


@dataclass(frozen=True)
class PaletteVerdict:
    verdict: str
    view_id: Optional[str]
    total_shown: int
    passing_shown: int
    latest_on: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict, "view_id": self.view_id,
            "total_shown": self.total_shown,
            "passing_shown": self.passing_shown,
            "latest_on": self.latest_on,
        }


def derive_verdict(source: Any, view: Any = None) -> PaletteVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_entries(book, resolved)
    passing = sum(1 for g in shown if entry_passes(g))
    latest = max((g.recorded_on for g in shown), default="")
    return PaletteVerdict(
        verdict=_verdict_word(len(shown), passing),
        view_id=resolved.view_id, total_shown=len(shown),
        passing_shown=passing, latest_on=latest)


def _check_verdict_ref(value: Any) -> PaletteVerdict:
    if not isinstance(value, PaletteVerdict):
        raise ValueError("a verdict must be a PaletteVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> PaletteVerdict:
    checked = _check_verdict_ref(verdict)
    if checked.verdict not in VERDICT_WORDS:
        raise ValueError(f"verdict {checked.verdict!r} is not a held word")
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(checked.view_id)
                if checked.view_id is not None else None)
        derived = derive_verdict(book, view)
        if checked != derived:
            raise ValueError(
                "the stored verdict disagrees with the verdict "
                "derived from its book")
    return checked


def build_verdict(verdict: Any = None, source: Any = None,
                  **kwargs: Any) -> PaletteVerdict:
    if isinstance(verdict, PaletteVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = PaletteVerdict(
            verdict=_clean_text(data.get("verdict"), "a verdict"),
            view_id=data.get("view_id"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            passing_shown=_check_count(
                data.get("passing_shown"), "a passing_shown count"),
            latest_on=_clean_text(data.get("latest_on"), "a latest day"))
        return validate_verdict(built, source)
    if verdict is None and source is not None:
        return derive_verdict(source, kwargs.get("view"))
    raise ValueError(
        "a verdict must be a mapping, a PaletteVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held entries' words at call time, and
# the stance targets: which entry notes the book holds, derived too.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexEntry:
    keywords: str
    entry_id: str
    title: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "keywords": self.keywords, "entry_id": self.entry_id,
            "title": self.title,
        }


@dataclass(frozen=True)
class PaletteIndex:
    """The palette index, derived from the held entries.

    The index names one entry per complete entry, in
    held order - the entry's own search words, its id and
    its title - and the entries that stand incomplete,
    named in its gaps. Nothing here is stored on any
    entry: the index is derived at call time from the
    held records alone, so it can never drift from them.
    """

    entries: Tuple[IndexEntry, ...]
    gaps: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "entries": [e.to_record() for e in self.entries],
            "gaps": list(self.gaps),
        }


def derive_index(source: Any) -> PaletteIndex:
    """Derive the palette index from the book's held entries."""
    book = _source_book(source)
    entries = tuple(
        IndexEntry(keywords=g.keywords, entry_id=g.entry_id, title=g.title)
        for g in book.entries if entry_passes(g))
    gaps = tuple(
        g.entry_id for g in book.entries if not entry_passes(g))
    return PaletteIndex(entries=entries, gaps=gaps)


def entry_for_keywords(source: Any, keywords: Any) -> Optional[EntryCard]:
    """The first held entry one set of words reaches, or none - honestly."""
    wanted = _check_keywords(keywords)
    if not wanted:
        return None
    for entry in _source_book(source).entries:
        if entry.keywords == wanted:
            return entry
    return None


def note_for_entry(source: Any, entry_id: Any,
                       stance: Any = None) -> Optional[NoteRecord]:
    """The held stance target for one entry (and stance, when named)."""
    wanted = _clean_text(entry_id, "an entry id")
    for record in _source_book(source).notes:
        if record.entry_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_note(source: Any) -> Optional[NoteRecord]:
    """The first held stance target, standing for the entry targets, or none."""
    notes = _source_book(source).notes
    return notes[0] if notes else None


# ---------------------------------------------------------------------
# The book: entries, views and notes held together, one pinned panel
# at most per telling, and no verdict or index ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class PaletteBook:
    title: str
    entries: Tuple[EntryCard, ...] = ()
    views: Tuple[PaletteView, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    panels: Tuple[PalettePanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        entries = tuple(_check_entry_ref(g) for g in self.entries)
        views = tuple(_check_view_ref(v) for v in self.views)
        notes = tuple(_check_note_ref(m) for m in self.notes)
        panels = tuple(_check_panel_ref(p) for p in self.panels)
        seen_ids = set()
        seen_seqs = set()
        for entry in entries:
            if entry.entry_id in seen_ids:
                raise ValueError(
                    f"two entries stand under id {entry.entry_id!r}")
            if entry.seq in seen_seqs:
                raise ValueError(
                    f"two entries stand at sequence {entry.seq}")
            seen_ids.add(entry.entry_id)
            seen_seqs.add(entry.seq)
        view_ids = set()
        view_seqs = set()
        for view in views:
            if view.view_id in view_ids:
                raise ValueError(
                    f"two views stand under id {view.view_id!r}")
            if view.seq in view_seqs:
                raise ValueError(
                    f"two views stand at sequence {view.seq}")
            view_ids.add(view.view_id)
            view_seqs.add(view.seq)
        note_ids = set()
        note_seqs = set()
        note_targets = set()
        for record in notes:
            if record.note_id in note_ids:
                raise ValueError(
                    f"two notes stand under id {record.note_id!r}")
            if record.seq in note_seqs:
                raise ValueError(
                    f"two notes stand at sequence {record.seq}")
            target = (record.entry_id, record.stance)
            if target in note_targets:
                raise ValueError(
                    f"two stance records stand for entry "
                    f"{record.entry_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per entry target")
            note_ids.add(record.note_id)
            note_seqs.add(record.seq)
            note_targets.add(target)
        object.__setattr__(
            self, "entries", tuple(sorted(entries, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "notes", tuple(sorted(notes, key=lambda m: m.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.entries + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.entry_id for g in self.entries) + tuple(
            v.view_id for v in self.views)

    def entry_ids(self) -> Tuple[str, ...]:
        return tuple(g.entry_id for g in self.entries)

    def entry_for(self, entry_id: Any) -> EntryCard:
        wanted = _clean_text(entry_id, "an entry id")
        for entry in self.entries:
            if entry.entry_id == wanted:
                return entry
        raise KeyError(f"no entry named {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> PaletteView:
        wanted = _clean_text(view_id, "a view id")
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no view named {wanted!r} stands in this book")

    def note_for(self, note_id: Any) -> NoteRecord:
        wanted = _clean_text(note_id, "a stance id")
        for record in self.notes:
            if record.note_id == wanted:
                return record
        raise KeyError(f"no stance named {wanted!r} stands in this book")

    def item_for(self, item_id: Any) -> Any:
        wanted = _clean_text(item_id, "an item id")
        for entry in self.entries:
            if entry.entry_id == wanted:
                return entry
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "entries": [g.to_record() for g in self.entries],
            "views": [v.to_record() for v in self.views],
            "notes": [m.to_record() for m in self.notes],
            "panels": [p.to_record() for p in self.panels],
        }


def _judge_book_panels(book: PaletteBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: PaletteBook) -> None:
    if book.title != "Command palette at the M-196 slice boundary":
        raise ValueError("the shipped example book carries another title")
    if len(book.entries) != 6 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold six entries and two views")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-m196-boundary":
        raise ValueError("the pinned panel is panel-m196-boundary")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "strained" or verdict.passing_shown != 5:
        raise ValueError("the shipped example book verdict must stand strained at five ready of six")
    index = derive_index(book)
    if [e.keywords for e in index.entries] != ["the one door frequent hands use", "keep the work safe", "return to the first screen", "the model that answers you", "help when you are stuck"]:
        raise ValueError("the shipped example book index must derive the five held words in held order")
    if index.gaps != ("entry-quiet-main",):
        raise ValueError("the shipped example book must leave the quiet entry honestly incomplete, named in its gaps")
    found = entry_for_keywords(book, EXAMPLE_KEYWORDS)
    if found is None or found.entry_id != "entry-open-main":
        raise ValueError("the shipped example book must reach its open entry under the example words")
    first = first_note(book)
    if first is None or first.note_id != "note-note-open":
        raise ValueError("the shipped example book must hold the open note as its first note road")


def validate_book(data: Any, *, require_example: bool = False) -> PaletteBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, PaletteBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a palette book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live palette execution "
                f"({key!r} is named on it): {PALETTE_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its entries under a view")
    if "palette_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held entries at call time")
    if data.get("schema") is not None and (
            data["schema"] != COMMAND_PALETTE_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{COMMAND_PALETTE_SCHEMA!r}")
    if data.get("slice") is not None and (
            data["slice"] != COMMAND_PALETTE_SLICE):
        raise ValueError(
            f"a book's slice must be {COMMAND_PALETTE_SLICE!r}")
    head = data.get("command_palette") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's palette head must be a mapping")
    title = head.get("title") or data.get("title")
    entries = tuple(build_entry(g) for g in data.get("entries") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    book = PaletteBook(
        title=title, entries=entries, views=views, notes=notes, panels=())
    panels = tuple(
        build_panel(p, book) for p in data.get("panels") or ())
    book = PaletteBook(
        title=book.title, entries=book.entries, views=book.views,
        notes=book.notes, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> PaletteBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (PaletteBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or a PaletteBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> PaletteBook:
    return validate_book(data, require_example=require_example)


def load_command_palette(
        data: Optional[Dict[str, Any]] = None) -> PaletteBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(COMMAND_PALETTE_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_command_palette_file(path: Any) -> PaletteBook:
    """Load one palette file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: entries and views held one by one.
# ---------------------------------------------------------------------

class CommandPaletteRegistry:
    """An in-memory holding of entries and views.

    The registry is the pure layer's model of a
    session's palette book: entries are held under
    their ids, one entry per id and per sequence,
    and views are held in recorded order, one view
    per sequence and per id. Holding is data only -
    nothing held here executes a command, runs an
    action, or navigates anywhere.
    """

    def __init__(self, book: Any = None) -> None:
        self._entries: List[EntryCard] = []
        self._views: List[PaletteView] = []
        self._title: Optional[str] = None
        if book is not None:
            self.register_book(book)

    def title(self) -> Optional[str]:
        return self._title

    def _fresh_view_id(self, held_ids: Any) -> str:
        n = 1
        while f"view-{n}" in held_ids:
            n += 1
        return f"view-{n}"

    def _register(self, held: List[Any], item: Any,
                  id_attr: str, what: str) -> Any:
        for other in held:
            if getattr(other, id_attr) == getattr(item, id_attr):
                raise ValueError(
                    f"a {what} already stands under id "
                    f"{getattr(item, id_attr)!r}")
            if other.seq == item.seq:
                raise ValueError(
                    f"a {what} already stands at sequence {item.seq}")
        held.append(item)
        held.sort(key=lambda held_item: held_item.seq)
        return item

    def register_entry(self, item: Any) -> EntryCard:
        """Hold one entry, judged whole before held."""
        checked = _check_entry_ref(item)
        return self._register(
            self._entries, checked, "entry_id", "entry")

    def register_view(self, view: Any) -> PaletteView:
        """Hold one view; a view naming no id takes a fresh one."""
        checked = _check_view_ref(view)
        if not checked.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            checked = build_view({**checked.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, checked, "view_id", "view")

    def register_book(self, book: Any) -> PaletteBook:
        """Hold a whole book's entries and views, under its title."""
        checked = build_book(book)
        if self._title is not None and checked.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {checked.title!r}")
        for entry in checked.entries:
            self.register_entry(entry)
        for view in checked.views:
            self.register_view(view)
        self._title = checked.title
        return self.book()

    def book(self) -> PaletteBook:
        return PaletteBook(
            title=self._title or "An unheld palette book",
            entries=tuple(self._entries), views=tuple(self._views),
            notes=(), panels=())

    def list_entries(self) -> Tuple[EntryCard, ...]:
        return tuple(self._entries)

    def list_views(self) -> Tuple[PaletteView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._entries) + tuple(self._views)

    def get_entry(self, entry_id: Any) -> EntryCard:
        return self.book().entry_for(entry_id)

    def get_view(self, view_id: Any) -> PaletteView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records shaped for the journal target.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> PaletteBook:
    if source is None:
        return load_command_palette()
    if isinstance(source, PaletteBook):
        return source
    if isinstance(source, CommandPaletteRegistry):
        return source.book()
    return build_book(source)


def _provenance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _PROVENANCE}


def entry_record(entry: Any, source: Any = None) -> Dict[str, Any]:
    checked = _check_entry_ref(entry)
    record = {
        "type": "palette_entry",
        "slice": COMMAND_PALETTE_SLICE,
        "entry_id": checked.entry_id,
        "title": checked.title,
        "segment": segment_of(checked),
        "passes": entry_passes(checked),
        "gaps": list(entry_gaps(checked)),
    }
    record.update(_provenance_record(checked))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    checked = _check_view_ref(view)
    record = {
        "type": "palette_view",
        "slice": COMMAND_PALETTE_SLICE,
        "view_id": checked.view_id, "seq": checked.seq,
        "view_filter": checked.view_filter,
    }
    record.update(_provenance_record(checked))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    checked = _check_note_ref(record_in)
    record = {
        "type": "palette_note",
        "slice": COMMAND_PALETTE_SLICE,
        "note_id": checked.note_id,
        "entry_id": checked.entry_id,
        "stance": checked.stance,
    }
    record.update(_provenance_record(checked))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    checked = validate_panel(panel, source)
    record = {"type": "palette_panel",
              "slice": COMMAND_PALETTE_SLICE}
    record.update(checked.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, PaletteVerdict):
        checked = validate_verdict(verdict, source)
    else:
        checked = derive_verdict(_source_book(verdict), view)
    record = {"type": "palette_verdict",
              "slice": COMMAND_PALETTE_SLICE}
    record.update(checked.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, PaletteIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "palette_index",
              "slice": COMMAND_PALETTE_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    checked = _source_book(book)
    record = {"type": "palette_book",
              "slice": COMMAND_PALETTE_SLICE,
              "title": checked.title}
    record.update(checked.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(entry: Any, source: Any = None) -> str:
    checked = _check_entry_ref(entry)
    return (
        f"{checked.title} - kind {checked.kind}: "
        f"shortcut {checked.shortcut if checked.shortcut else 'unknown'}, "
        f"keywords {checked.keywords if checked.keywords else 'none'}. "
        f"{checked.detail}")


def entry_plain_words(entry: Any, source: Any = None) -> str:
    return plain_words(entry, source)


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The command palette stands {verdict.verdict}: "
        f"{verdict.passing_shown} of {verdict.total_shown} shown "
        f"entries stand ready.")


def view_plain_words(view: Any) -> str:
    checked = _check_view_ref(view)
    return f"View {checked.view_id}: shows {checked.view_filter} entries."


def note_plain_words(record_in: Any) -> str:
    checked = _check_note_ref(record_in)
    return (
        f"Note {checked.note_id}: {checked.stance} "
        f"{checked.entry_id}, toward {checked.target}. "
        f"{checked.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, PaletteIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.entries)} search words for "
        f"{len(index.entries)} entries; incomplete, named in "
        f"its gaps: {gaps}.")


def format_entry(entry: Any, source: Any = None) -> str:
    checked = _check_entry_ref(entry)
    lines = [f"{checked.title} ({checked.entry_id})"]
    lines.extend(plain_lines(checked))
    lines.append(checked.detail)
    if entry_passes(checked):
        lines.append(
            "This entry stands ready - it carries the search "
            "words its record names.")
    else:
        lines.append(
            "This entry stands unready - it names no search "
            "words, stands named in its gaps, and no words are "
            "invented for it.")
    return "\n".join(lines)


def format_view(view: Any) -> str:
    checked = _check_view_ref(view)
    return (
        f"View {checked.view_id}: filter {checked.view_filter} - "
        f"{checked.detail}")


def format_note(record_in: Any) -> str:
    checked = _check_note_ref(record_in)
    lines = [
        f"Palette note {checked.stance} {checked.entry_id} "
        f"({checked.note_id}): {checked.title}. {checked.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or reading it executes no command, runs no action "
        "and posts no note.")
    return "\n".join(lines)


def format_keywords(source: Any, keywords: Any) -> str:
    entry = entry_for_keywords(source, keywords)
    if entry is not None:
        return format_entry(entry)
    wanted = _check_keywords(keywords)
    return (
        f"No held entry stands under keywords {wanted!r} yet - the "
        f"keywords reaches nothing in this book, and no entry is "
        f"invented for them.")


def format_book(source: Any = None, kind: Any = None) -> str:
    book = _source_book(source)
    entries = (entries_for_kind(book, kind)
                if kind is not None else book.entries)
    lines = [f"Command Palette (M-197) - {book.title}"]
    lines.extend(segment_of(entry) for entry in entries)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Palette panel under view {panel.view_id}:"]
    lines.extend(row.segment for row in panel.rows)
    lines.extend(panel.account)
    return "\n".join(lines)


def format_verdict(source: Any = None, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return verdict_plain_words(source, view) + (
        f" (view {verdict.view_id}, as of {verdict.latest_on})")


def format_index(source: Any = None) -> str:
    book = _source_book(source)
    index = derive_index(book)
    lines = ["Palette index, derived from the held entries:"]
    for entry in index.entries:
        lines.append(f"{entry.keywords} - {entry.title} ({entry.entry_id})")
    if index.gaps:
        lines.append(
            "Incomplete, named honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "executes no command and opens no network.")
    return "\n".join(lines)


def format_palette_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "Command Palette (M-197)",
        f"{book.title}: {len(book.entries)} entries held, "
        f"{len(passing_entries(book))} entries standing ready, "
        f"{len(book.notes)} notes held.",
    ]
    if book.views:
        panel = derive_panel(book, book.views[0])
        lines.append(
            f"{panel.total_shown} of {panel.total_items} items show "
            f"under the first view.")
        lines.extend(row.segment for row in panel.rows)
    lines.append(index_plain_words(book))
    lines.append(PLAIN_EXPLANATION)
    return "\n".join(lines)


def parse_palette_args(args: Any) -> Tuple[str, Any]:
    """Parse the /commandpalette grammar into (action, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("entry", "view", "note"):
        if len(parts) != 2:
            raise ValueError(USAGE)
        return (head, parts[1])
    if head in ("keywords", "kind"):
        if len(parts) < 2:
            raise ValueError(USAGE)
        return (head, " ".join(parts[1:]))
    if head in ("index", "panel", "verdict") and len(parts) == 1:
        return (head, None)
    raise ValueError(USAGE)
