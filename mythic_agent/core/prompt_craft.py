"""The prompt craft (All-Features roadmap slice M-177).

Part VIII - The Beautiful Face - builds here. The
roadmap's words: *multi-line editing, history per
project, image paste, file drop, dictation (M-180)
- the input box is a small editor, not a slot.*

What already ships, and what this slice adds:

* The shipped tree's input box is a slot: one line
  is typed, sent and gone. Nothing holds the
  box's own craft as data - the multi-line draft
  being shaped, the prompts a project has already
  sent (its history), the image a user pasted
  toward the box, or the file a user dropped on
  it - so none of it can be looked at, counted or
  judged in one room, in plain words.
* The M-171 TUI redesign charter names NO screen
  row for this slice: the input lives on the main
  chat screen (its S-03 row), whose owning slices
  are M-172, M-173 and M-178, and no row names
  M-177 at all. This slice is therefore built to
  the roadmap words alone, honouring the charter's
  standing law the way every Part VIII slice does:
  plain words first.
* Dictation stands in the roadmap words with its
  own slice named beside it - (M-180) - and is
  NOT built here: there is no dictation kind, no
  dictation record and no dictation road in this
  layer. Voice in and out is M-180's road.
* This slice is that one room, as a pure layer:
  one craft item validated as data WITH ITS
  PROVENANCE WHOLE - its kind in the closed kind
  set (draft, history, image, file: the roadmap's
  own order), the one project it stands in (history
  is per project, so an item stands in exactly one
  named project), its title and its words held
  whole, multi-line where the words run so. A
  pasted image is first held as its own record,
  judged whole - its name, its format and the
  plain words that describe it - and joins the
  book as an item of the image kind; a dropped
  file is first held as its own record, judged
  whole - its path and the plain words that
  describe it - and joins as an item of the file
  kind. A view is held as its own record - the one
  project it looks at, or every project at once.
  The panel is DERIVED for one held view (its rows
  the shown items in held order, carrying their
  derived lines and line counts, its totals the
  items' own counts), and a verdict is DERIVED for
  the whole book under one view. The shipped data
  file (``mythic_agent/data/prompt_craft.yaml``)
  holds one example book in exactly the shape a
  real craft file takes, a loader reads a craft
  file anywhere on disk, items and views are
  shaped as session news, and a small in-memory
  registry model holds items and views one by one.
  The agent layer owns holding items for a
  session and standing a view on them.

Honesty rules, enforced here and pinned by tests:

* **History is per project.** An item stands in
  exactly one named project, never in the every-
  project filter - that filter is a view's alone.
  A view narrows which items stand in its panel,
  never how they are judged.
* **The line is derived, never stored.** An item
  carries no line and no line count: a mapping
  naming one refuses. A line and a count exist
  only as the derivation of the item's own title,
  kind, project and words, and a panel row is
  judged against that derivation: a stored row
  whose line or count disagrees refuses.
* **Dictation is M-180's road, not built here.**
  The kind set is closed without it: a dictation
  kind, field or record refuses plainly. Naming
  dictation in the roadmap words builds nothing.
* **Data only.** This layer holds items and views
  as data: it edits no live input box, pastes
  nothing, drops nothing, dictates nothing, opens
  no dropped file, reads no dropped file, sends
  nothing, calls no model and persists nothing -
  an item held here is a finding, never the act
  of typing, pasting or sending the prompt found.
"""

from __future__ import annotations

__all__ = [
    "IMAGE_FORMATS",
    "ITEM_KINDS",
    "PLAIN_EXPLANATION",
    "PROMPT_CRAFT_RESOURCE",
    "PROMPT_CRAFT_SCHEMA",
    "PROMPT_CRAFT_SLICE",
    "THE_PROMPT_CRAFT_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "Any",
    "Dict",
    "DroppedFile",
    "List",
    "Optional",
    "PastedImage",
    "PromptCraftBook",
    "PromptCraftRegistry",
    "PromptItem",
    "PromptKindCount",
    "PromptPanel",
    "PromptPanelRow",
    "PromptVerdict",
    "PromptView",
    "Tuple",
    "book_record",
    "build_book",
    "build_file",
    "build_image",
    "build_item",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "derive_panel",
    "derive_verdict",
    "file_record",
    "format_book",
    "format_item",
    "format_panel",
    "format_prompt_craft_screen",
    "format_verdict",
    "format_view",
    "image_record",
    "inspect_item_source",
    "item_from_draft_text",
    "item_from_dropped_file",
    "item_from_history_entry",
    "item_from_pasted_image",
    "item_record",
    "items_for_project",
    "items_with_kind",
    "line_count_of",
    "line_of",
    "load_prompt_craft",
    "load_prompt_craft_file",
    "normalize_image_format",
    "normalize_kind",
    "normalize_project_filter",
    "panel_plain_words",
    "panel_record",
    "parse_prompt_craft_args",
    "plain_words",
    "shown_items",
    "total_items",
    "validate_book",
    "validate_file",
    "validate_image",
    "validate_item",
    "validate_panel",
    "validate_row",
    "validate_verdict",
    "validate_view",
    "verdict_plain_words",
    "verdict_record",
    "view_plain_words",
    "view_record",
]

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource
from .crew_members import normalize_member_id

PROMPT_CRAFT_SLICE = "M-177"

#: The longer name other layers cite for this slice.
THE_PROMPT_CRAFT_SLICE = PROMPT_CRAFT_SLICE

PROMPT_CRAFT_RESOURCE = "prompt_craft.yaml"

PROMPT_CRAFT_SCHEMA = "mythic.prompt_craft/1"

#: The kinds one item may stand under, in the
#: roadmap's own order: the multi-line draft being
#: shaped, the per-project history, the pasted
#: image and the dropped file. Dictation is not a
#: kind here - it is M-180's road, not built.
ITEM_KINDS = ("draft", "history", "image", "file")

_KIND_ALIASES = {
    "draft": "draft", "drafts": "draft",
    "multiline": "draft", "editing": "draft",
    "history": "history", "past": "history",
    "sent": "history",
    "image": "image", "images": "image",
    "paste": "image", "pasted": "image",
    "picture": "image",
    "file": "file", "files": "file",
    "drop": "file", "dropped": "file",
}

#: The formats one pasted image may stand in, in
#: order: the shapes a paste toward the box takes.
IMAGE_FORMATS = ("png", "jpeg", "gif", "webp")

_FORMAT_ALIASES = {
    "png": "png", "jpeg": "jpeg", "jpg": "jpeg",
    "gif": "gif", "webp": "webp",
}

#: The words a whole book's verdict under one view
#: may carry: shared while the shown items stand
#: in more than one project, held while they stand
#: in one project alone, empty while no item shows.
VERDICT_WORDS = ("shared", "held", "empty")

_ITEM_KEYS = frozenset({
    "item_id", "id", "kind", "type_of",
    "project", "project_ref",
    "title", "name", "label",
    "body", "text", "words",
    "recorded_on", "day", "date",
    "actor", "by", "who", "source",
    "origin_session", "session"})

_IMAGE_KEYS = frozenset({
    "image_id", "id", "name", "label",
    "format", "image_format",
    "note", "detail", "description",
    "recorded_on", "day", "date",
    "actor", "by", "who", "source",
    "origin_session", "session"})

_FILE_KEYS = frozenset({
    "file_id", "id", "path", "file_path",
    "note", "detail", "description",
    "recorded_on", "day", "date",
    "actor", "by", "who", "source",
    "origin_session", "session"})

_ROW_KEYS = frozenset({
    "item_id", "id", "kind", "project",
    "line", "line_count", "lines", "recorded_on"})

_KIND_COUNT_KEYS = frozenset({"kind", "items", "count"})

_PANEL_KEYS = frozenset({
    "panel_id", "id", "view_id", "view",
    "project_filter", "filter", "project",
    "rows", "shown",
    "total_items", "items",
    "total_shown", "matched",
    "kind_counts", "kinds",
    "as_of", "day", "account", "statements"})

_VIEW_KEYS = frozenset({
    "view_id", "id", "seq", "sequence", "order",
    "project_filter", "filter", "project",
    "detail", "reason",
    "recorded_on", "day", "date",
    "actor", "by", "who", "source",
    "origin_session", "session"})

_VERDICT_KEYS = frozenset({
    "total_items", "items",
    "total_shown", "matched",
    "distinct_projects", "projects",
    "earliest_on", "earliest", "latest_on", "latest",
    "verdict"})

_BOOK_KEYS = frozenset({"title", "name"})

_PROMPT_CRAFT_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "canon_note", "guide", "items", "views",
    "panels"})

_EXAMPLE_TITLE = "Prompt Craft at the M-176 slice boundary"

_EXAMPLE_ITEM_IDS = (
    "item-opening-draft", "item-palace-note",
    "item-first-prompt", "item-standup-prompt",
    "item-longship-sketch", "item-harbour-photo",
    "item-roadmap-drop", "item-verses-drop")

_EXAMPLE_FIRST_ITEM_ID = "item-opening-draft"

_EXAMPLE_FIRST_ITEM_KIND = "draft"

_EXAMPLE_FIRST_ITEM_PROJECT = "mythic-coder"

_EXAMPLE_PANEL_ID = "panel-m176-boundary"

_EXAMPLE_AS_OF = "2026-11-09"

_EXAMPLE_VIEW_IDS = ("view-all", "view-mythic-coder")

PLAIN_EXPLANATION = (
    "Prompt Craft: the input box is a small "
    "editor, not a slot - multi-line drafts, "
    "history per project, pasted images and "
    "dropped files, each held as data. An item "
    "is one piece of that craft held whole - its "
    "kind (draft, history, image or file), the "
    "one project it stands in, its title and its "
    "words, with its provenance whole. A pasted "
    "image is first held as its own record, "
    "judged whole, and joins as an item of the "
    "image kind; a dropped file likewise joins "
    "as an item of the file kind, its path named "
    "and never opened. A view looks at one "
    "project, or at every project at once, and "
    "an item's line and line count are derived "
    "from its own title, kind, project and words "
    "- never stored, never counted by hand. "
    "Dictation is M-180's road and is not built "
    "here. No M-171 charter row names this "
    "slice, so it is built to the roadmap words "
    "alone, plain words first. This layer holds "
    "items and views as data only: it edits no "
    "live input box, pastes nothing, drops "
    "nothing, dictates nothing, opens no dropped "
    "file, sends nothing, calls no model and "
    "persists nothing - an item held here is a "
    "finding, never the act of typing, pasting "
    "or sending the prompt found."
)

USAGE = (
    "Usage: /promptcraft, /promptcraft show, "
    "/promptcraft item <item-id>, "
    "/promptcraft view <view-id>, "
    "/promptcraft project <project>, "
    "/promptcraft kind <kind>, "
    "/promptcraft panel, /promptcraft verdict"
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


def _check_body(value: Any, what: str = "an item's words") -> str:
    """One item's words, held whole, multi-line where they run so."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be non-empty text")
    text = value.strip()
    if len(text) > 4000 or "\x00" in text:
        raise ValueError(
            f"{what} must be plain text of at most "
            f"4000 characters, got {len(text)} characters")
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


def _check_seq(value: Any) -> int:
    seq = _check_count(value, "a view's sequence")
    if seq < 1:
        raise ValueError(
            f"a view's sequence stands from 1, got {value!r}")
    return seq


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


def _check_project(value: Any, what: str = "a project") -> str:
    project = _check_word(value, what)
    if project.lower() == "all":
        raise ValueError(
            "an item stands in one named project, never "
            "in the every-project filter - that filter "
            "is a view's alone")
    return project


def normalize_kind(value: Any) -> str:
    """One kind word, read onto the closed kind set."""
    if not isinstance(value, str):
        raise ValueError(f"a kind must be a word, got {value!r}")
    kind = _KIND_ALIASES.get(value.strip().lower())
    if kind is None:
        raise ValueError(
            "a kind is one of %s, got %r - dictation "
            "is M-180's road and is not a kind here"
            % ("/".join(ITEM_KINDS), value))
    return kind


def normalize_image_format(value: Any) -> str:
    """One image-format word, read onto the closed format set."""
    if not isinstance(value, str):
        raise ValueError(
            f"an image format must be a word, got {value!r}")
    image_format = _FORMAT_ALIASES.get(value.strip().lower())
    if image_format is None:
        raise ValueError(
            "an image format is one of %s, got %r"
            % ("/".join(IMAGE_FORMATS), value))
    return image_format


def normalize_project_filter(value: Any) -> str:
    """One project-filter word: every project, or one named project."""
    if not isinstance(value, str):
        raise ValueError(
            f"a project filter must be a word, got {value!r}")
    if value.strip().lower() == "all":
        return "all"
    return _check_word(value, "a project filter")


def line_count_of(item: Any) -> int:
    """How many lines one item's words run to, derived.

    Read off the item's own words alone: the count
    of the lines they stand in. The count is
    derived at call time - it is never a field of
    the item.
    """
    current = _check_item_ref(item)
    return len(current.body.splitlines())


def line_of(item: Any) -> str:
    """The item line one craft item derives.

    Read off the item's title, kind and project
    alone: what the piece is called, the kind it
    stands under, and the one project it stands in.
    """
    current = _check_item_ref(item)
    return f"{current.title} - {current.kind} in {current.project}"


def _lines_word(count: int) -> str:
    return "line" if count == 1 else "lines"


# ---------------------------------------------------------------------
# The item: one piece of prompt craft, held whole.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class PromptItem:
    """One craft item: one piece of prompt craft, held whole.

    ``kind`` is the item's kind in the closed kind
    set; ``project`` is the one project the item
    stands in (history is per project); ``title``
    is the item's own name in plain words; ``body``
    is the item's words held whole - the draft's
    multi-line text, the history entry's prompt,
    the pasted image's describing words, or the
    dropped file's describing words. The item
    carries NO line and NO line count - those are
    derived from the item at call time, never
    fields. The provenance - the day it was
    recorded, who recorded it, its source and the
    session it was recorded in - rides whole.
    """

    item_id: str
    kind: str
    project: str
    title: str
    body: str
    recorded_on: str
    actor: str
    source: str
    origin_session: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "item_id",
            _check_word(self.item_id, "an item id"))
        object.__setattr__(self, "kind", normalize_kind(self.kind))
        object.__setattr__(
            self, "project", _check_project(self.project))
        object.__setattr__(
            self, "title", _check_title(self.title, "an item title"))
        object.__setattr__(self, "body", _check_body(self.body))
        object.__setattr__(
            self, "recorded_on", _check_day(self.recorded_on))
        object.__setattr__(
            self, "actor", _check_title(self.actor, "an actor"))
        object.__setattr__(
            self, "source", _check_title(self.source, "a source"))
        object.__setattr__(
            self, "origin_session",
            _check_word(self.origin_session, "an origin session"))

    @property
    def line(self) -> str:
        """The derived item line of this item."""
        return line_of(self)

    @property
    def line_count(self) -> int:
        """The derived line count of this item's words."""
        return line_count_of(self)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "prompt_craft_item",
            "slice": PROMPT_CRAFT_SLICE,
            "item_id": self.item_id,
            "kind": self.kind,
            "project": self.project,
            "title": self.title,
            "body": self.body,
            "line": self.line,
            "line_count": self.line_count,
            "recorded_on": self.recorded_on,
            "actor": self.actor,
            "source": self.source,
            "origin_session": self.origin_session,
        }


def _check_item_ref(value: Any) -> PromptItem:
    if isinstance(value, PromptItem):
        return value
    return validate_item(value)


def validate_item(item: Any) -> PromptItem:
    """Judge one craft item whole and return it.

    A mapping is read through its spellings: a
    derived key (``line`` or ``line_count``)
    refuses - those are derived, never stored - as
    does any key the item does not carry, and two
    spellings naming two different values.
    """
    if isinstance(item, PromptItem):
        return item
    if not isinstance(item, dict):
        raise ValueError(
            f"a craft item must be a mapping, got {item!r}")
    unknown = set(item) - _ITEM_KEYS
    if unknown:
        raise ValueError(
            f"a craft item carries unknown keys: "
            f"{sorted(unknown)}")
    if "type" in item:
        raise ValueError(
            "a craft item is judged without its news keys")

    def _needed(spellings: Tuple[str, ...], what: str) -> Any:
        value = _pick_any(item, spellings, what)
        if value is None:
            raise ValueError(f"a craft item names no {what}")
        return value

    return PromptItem(
        item_id=_needed(("item_id", "id"), "item id"),
        kind=_needed(("kind", "type_of"), "kind"),
        project=_needed(("project", "project_ref"), "project"),
        title=_needed(("title", "name", "label"), "title"),
        body=_needed(("body", "text", "words"), "words"),
        recorded_on=_needed(
            ("recorded_on", "day", "date"), "day it was recorded"),
        actor=_needed(("actor", "by", "who"), "actor"),
        source=_needed(("source",), "source"),
        origin_session=_needed(
            ("origin_session", "session"), "origin session"),
    )


def build_item(item: Any = None, **kwargs: Any) -> PromptItem:
    """Build one item from a mapping, an item, or fields."""
    if kwargs:
        if item is not None:
            raise ValueError("an item is built one way at a time")
        item = kwargs
    return validate_item(item)


# ---------------------------------------------------------------------
# The pasted image and the dropped file: held as their own records.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class PastedImage:
    """One pasted image, held as its own record.

    ``name`` is the image's own name; ``format`` is
    its format in the closed format set; ``note``
    is the plain words that describe the image -
    the image itself is never held here, never
    decoded and never pasted anywhere by this
    layer: the record is the paste, held as data.
    The provenance rides whole. A pasted image
    joins the book as an item of the image kind.
    """

    image_id: str
    name: str
    format: str
    note: str
    recorded_on: str
    actor: str
    source: str
    origin_session: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "image_id",
            _check_word(self.image_id, "a pasted image id"))
        object.__setattr__(
            self, "name", _check_title(self.name, "an image name"))
        object.__setattr__(
            self, "format", normalize_image_format(self.format))
        object.__setattr__(
            self, "note",
            _check_long_text(self.note, "the image's words"))
        object.__setattr__(
            self, "recorded_on", _check_day(self.recorded_on))
        object.__setattr__(
            self, "actor", _check_title(self.actor, "an actor"))
        object.__setattr__(
            self, "source", _check_title(self.source, "a source"))
        object.__setattr__(
            self, "origin_session",
            _check_word(self.origin_session, "an origin session"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "prompt_craft_image",
            "slice": PROMPT_CRAFT_SLICE,
            "image_id": self.image_id,
            "name": self.name,
            "format": self.format,
            "note": self.note,
            "recorded_on": self.recorded_on,
            "actor": self.actor,
            "source": self.source,
            "origin_session": self.origin_session,
        }


def validate_image(image: Any) -> PastedImage:
    """Judge one pasted-image record whole and return it."""
    if isinstance(image, PastedImage):
        return image
    if not isinstance(image, dict):
        raise ValueError(
            f"a pasted image must be a mapping, got {image!r}")
    unknown = set(image) - _IMAGE_KEYS
    if unknown:
        raise ValueError(
            f"a pasted image carries unknown keys: "
            f"{sorted(unknown)}")
    if "type" in image:
        raise ValueError(
            "a pasted image is judged without its news keys")

    def _needed(spellings: Tuple[str, ...], what: str) -> Any:
        value = _pick_any(image, spellings, what)
        if value is None:
            raise ValueError(f"a pasted image names no {what}")
        return value

    return PastedImage(
        image_id=_needed(("image_id", "id"), "pasted image id"),
        name=_needed(("name", "label"), "image name"),
        format=_needed(("format", "image_format"), "image format"),
        note=_needed(
            ("note", "detail", "description"), "the image's words"),
        recorded_on=_needed(
            ("recorded_on", "day", "date"), "day it was recorded"),
        actor=_needed(("actor", "by", "who"), "actor"),
        source=_needed(("source",), "source"),
        origin_session=_needed(
            ("origin_session", "session"), "origin session"),
    )


def build_image(image: Any = None, **kwargs: Any) -> PastedImage:
    """Build one pasted image from a mapping, a record, or fields."""
    if kwargs:
        if image is not None:
            raise ValueError(
                "a pasted image is built one way at a time")
        image = kwargs
    return validate_image(image)


@dataclass(frozen=True)
class DroppedFile:
    """One dropped file, held as its own record.

    ``path`` is the path the file was dropped
    under, named and never opened, never read and
    never followed by this layer; ``note`` is the
    plain words that describe the drop. The
    provenance rides whole. A dropped file joins
    the book as an item of the file kind.
    """

    file_id: str
    path: str
    note: str
    recorded_on: str
    actor: str
    source: str
    origin_session: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "file_id",
            _check_word(self.file_id, "a dropped file id"))
        object.__setattr__(
            self, "path",
            _check_long_text(self.path, "the dropped file's path"))
        object.__setattr__(
            self, "note",
            _check_long_text(self.note, "the dropped file's words"))
        object.__setattr__(
            self, "recorded_on", _check_day(self.recorded_on))
        object.__setattr__(
            self, "actor", _check_title(self.actor, "an actor"))
        object.__setattr__(
            self, "source", _check_title(self.source, "a source"))
        object.__setattr__(
            self, "origin_session",
            _check_word(self.origin_session, "an origin session"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "prompt_craft_file",
            "slice": PROMPT_CRAFT_SLICE,
            "file_id": self.file_id,
            "path": self.path,
            "note": self.note,
            "recorded_on": self.recorded_on,
            "actor": self.actor,
            "source": self.source,
            "origin_session": self.origin_session,
        }


def validate_file(dropped: Any) -> DroppedFile:
    """Judge one dropped-file record whole and return it."""
    if isinstance(dropped, DroppedFile):
        return dropped
    if not isinstance(dropped, dict):
        raise ValueError(
            f"a dropped file must be a mapping, got {dropped!r}")
    unknown = set(dropped) - _FILE_KEYS
    if unknown:
        raise ValueError(
            f"a dropped file carries unknown keys: "
            f"{sorted(unknown)}")
    if "type" in dropped:
        raise ValueError(
            "a dropped file is judged without its news keys")

    def _needed(spellings: Tuple[str, ...], what: str) -> Any:
        value = _pick_any(dropped, spellings, what)
        if value is None:
            raise ValueError(f"a dropped file names no {what}")
        return value

    return DroppedFile(
        file_id=_needed(("file_id", "id"), "dropped file id"),
        path=_needed(("path", "file_path"), "the dropped file's path"),
        note=_needed(
            ("note", "detail", "description"),
            "the dropped file's words"),
        recorded_on=_needed(
            ("recorded_on", "day", "date"), "day it was recorded"),
        actor=_needed(("actor", "by", "who"), "actor"),
        source=_needed(("source",), "source"),
        origin_session=_needed(
            ("origin_session", "session"), "origin session"),
    )


def build_file(dropped: Any = None, **kwargs: Any) -> DroppedFile:
    """Build one dropped file from a mapping, a record, or fields."""
    if kwargs:
        if dropped is not None:
            raise ValueError(
                "a dropped file is built one way at a time")
        dropped = kwargs
    return validate_file(dropped)


# ---------------------------------------------------------------------
# Composition: the box's own pieces, judged whole.
# ---------------------------------------------------------------------


def item_from_draft_text(
        text: Any = None, *,
        item_id: Any, project: Any, title: Any,
        recorded_on: Any = "2026-11-09",
        actor: Any = "the coordinator",
        source: Any = "prompt craft",
        origin_session: Any = "session-m177") -> PromptItem:
    """Raise one draft item over multi-line draft text.

    The text is the draft's own words, held whole:
    a draft is the input box working as a small
    editor - its lines are counted by derivation,
    never edited here.
    """
    return PromptItem(
        item_id=item_id, kind="draft",
        project=project, title=title,
        body=_check_body(text, "the draft's words"),
        recorded_on=recorded_on, actor=actor,
        source=source, origin_session=origin_session)


def item_from_history_entry(
        entry: Any = None, *,
        item_id: Any, title: Any = None,
        recorded_on: Any = None,
        actor: Any = None,
        source: Any = None,
        origin_session: Any = None) -> PromptItem:
    """Raise one history item over a past prompt, judged whole.

    The entry is a mapping naming its project and
    the prompt's own words: history is per project,
    so the entry's project is the item's project,
    and the words stand byte for byte as they were
    sent. The title is the caller's plain name for
    the prompt, or its first line when none is
    named.
    """
    if not isinstance(entry, dict):
        raise ValueError(
            f"a history entry must be a mapping, got {entry!r}")
    unknown = set(entry) - _ITEM_KEYS - {"kind", "type_of"}
    if unknown:
        raise ValueError(
            f"a history entry carries unknown keys: "
            f"{sorted(unknown)}")
    project = _pick_any(
        entry, ("project", "project_ref"), "project")
    if project is None:
        raise ValueError("a history entry names no project")
    body = _pick_any(entry, ("body", "text", "words"), "words")
    if body is None:
        raise ValueError("a history entry names no words")
    held_body = _check_body(body, "the history entry's words")
    held_title = title if title is not None else _pick_any(
        entry, ("title", "name", "label"), "title")
    if held_title is None:
        held_title = held_body.splitlines()[0]
    return PromptItem(
        item_id=item_id, kind="history",
        project=project, title=held_title, body=held_body,
        recorded_on=(
            recorded_on if recorded_on is not None else _pick_any(
                entry, ("recorded_on", "day", "date"),
                "day it was recorded") or "2026-11-09"),
        actor=actor if actor is not None else (
            _pick_any(entry, ("actor", "by", "who"), "actor")
            or "the coordinator"),
        source=source if source is not None else (
            _pick_any(entry, ("source",), "source")
            or "prompt craft"),
        origin_session=(
            origin_session if origin_session is not None
            else _pick_any(
                entry, ("origin_session", "session"),
                "origin session") or "session-m177"))


def item_from_pasted_image(
        image: Any = None, *,
        item_id: Any, project: Any, title: Any = None,
        recorded_on: Any = None,
        actor: Any = None,
        source: Any = None,
        origin_session: Any = None) -> PromptItem:
    """Raise one image item over a pasted-image record.

    The record is judged whole first, on its own
    terms: the item's title is the image's own name
    unless the caller names it afresh, its words
    are the record's describing words, and its
    provenance is the record's own unless named
    afresh. The image itself is NOT carried into
    the item - this layer holds the paste as data:
    no image is decoded, rendered or pasted here.
    """
    if image is None:
        raise ValueError(
            "a pasted-image record is needed to raise an item")
    held = validate_image(image)
    return PromptItem(
        item_id=item_id, kind="image",
        project=project,
        title=title if title is not None else held.name,
        body=held.note,
        recorded_on=(
            recorded_on if recorded_on is not None
            else held.recorded_on),
        actor=actor if actor is not None else held.actor,
        source=source if source is not None else held.source,
        origin_session=(
            origin_session if origin_session is not None
            else held.origin_session))


def item_from_dropped_file(
        dropped: Any = None, *,
        item_id: Any, project: Any, title: Any = None,
        recorded_on: Any = None,
        actor: Any = None,
        source: Any = None,
        origin_session: Any = None) -> PromptItem:
    """Raise one file item over a dropped-file record.

    The record is judged whole first, on its own
    terms: the item's title is the dropped path's
    own last part unless the caller names it
    afresh, its words are the record's describing
    words, and its provenance is the record's own
    unless named afresh. The file itself is NOT
    opened or read here - the drop stands as data.
    """
    if dropped is None:
        raise ValueError(
            "a dropped-file record is needed to raise an item")
    held = validate_file(dropped)
    held_title = title
    if held_title is None:
        held_title = held.path.rstrip("/").rsplit("/", 1)[-1] \
            or held.path
    return PromptItem(
        item_id=item_id, kind="file",
        project=project, title=held_title, body=held.note,
        recorded_on=(
            recorded_on if recorded_on is not None
            else held.recorded_on),
        actor=actor if actor is not None else held.actor,
        source=source if source is not None else held.source,
        origin_session=(
            origin_session if origin_session is not None
            else held.origin_session))


def inspect_item_source(piece: Any) -> Dict[str, Any]:
    """Judge one raw item piece and name what it is.

    A piece shaped like an item - a mapping carrying
    a ``kind`` and a ``project`` - is read onto its
    closed kind without holding an item. Anything
    else is named not-an-item.
    """
    if not isinstance(piece, dict):
        return {"kind": None,
                "reason": "not a mapping - no item stands here"}
    kind_in = _pick_any(piece, ("kind", "type_of"), "kind")
    project = _pick_any(
        piece, ("project", "project_ref"), "project")
    if kind_in is None or project is None:
        return {"kind": None,
                "reason": "no kind or no project named - no item "
                          "stands here"}
    try:
        kind = normalize_kind(kind_in)
    except ValueError as exc:
        return {"kind": None, "project": project, "reason": str(exc)}
    return {
        "kind": kind, "project": project,
        "reason": "an item piece in the closed kind set"}


# ---------------------------------------------------------------------
# The view record: the one project a panel looks at, held whole.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class PromptView:
    """One view, held as its own record.

    ``project_filter`` is the one project the view
    looks at, or ``all`` for every project at once -
    it narrows which items stand in the view's
    panel, never how they are judged; ``detail`` is
    the view's own words. ``seq`` is the view's
    place in the book's recorded order, from 1. The
    provenance rides whole. A view carries no
    results of its own: its panel and the book's
    verdict under it are derived.
    """

    seq: int
    project_filter: str
    detail: str
    recorded_on: str
    actor: str
    source: str
    origin_session: str
    view_id: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "project_filter",
            normalize_project_filter(self.project_filter))
        object.__setattr__(
            self, "detail",
            _check_long_text(self.detail, "the view's words"))
        object.__setattr__(
            self, "recorded_on", _check_day(self.recorded_on))
        object.__setattr__(
            self, "actor", _check_title(self.actor, "an actor"))
        object.__setattr__(
            self, "source", _check_title(self.source, "a source"))
        object.__setattr__(
            self, "origin_session",
            _check_word(self.origin_session, "an origin session"))
        if self.view_id is not None:
            object.__setattr__(
                self, "view_id",
                _check_word(self.view_id, "a view id"))

    def shows(self, item: Any) -> bool:
        """True when this view shows the item."""
        current = _check_item_ref(item)
        return (self.project_filter == "all"
                or current.project == self.project_filter)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "prompt_craft_view",
            "slice": PROMPT_CRAFT_SLICE,
            "view_id": self.view_id,
            "seq": self.seq,
            "project_filter": self.project_filter,
            "detail": self.detail,
            "recorded_on": self.recorded_on,
            "actor": self.actor,
            "source": self.source,
            "origin_session": self.origin_session,
        }


def _check_view_ref(value: Any) -> PromptView:
    if isinstance(value, PromptView):
        return value
    return validate_view(value)


def validate_view(view: Any) -> PromptView:
    """Judge one view record whole and return it."""
    if isinstance(view, PromptView):
        return view
    if not isinstance(view, dict):
        raise ValueError(
            f"a view record must be a mapping, got {view!r}")
    unknown = set(view) - _VIEW_KEYS
    if unknown:
        raise ValueError(
            f"a view record carries unknown keys: "
            f"{sorted(unknown)}")
    if "type" in view:
        raise ValueError(
            "a view record is judged without its news keys")

    def _needed(spellings: Tuple[str, ...], what: str) -> Any:
        value = _pick_any(view, spellings, what)
        if value is None:
            raise ValueError(f"a view record names no {what}")
        return value

    return PromptView(
        view_id=_pick_any(view, ("view_id", "id"), "view id"),
        seq=_needed(("seq", "sequence", "order"), "sequence"),
        project_filter=_needed(
            ("project_filter", "filter", "project"),
            "project filter"),
        detail=_needed(("detail", "reason"), "the view's words"),
        recorded_on=_needed(
            ("recorded_on", "day", "date"), "day it was recorded"),
        actor=_needed(("actor", "by", "who"), "actor"),
        source=_needed(("source",), "source"),
        origin_session=_needed(
            ("origin_session", "session"), "origin session"),
    )


def build_view(view: Any = None, **kwargs: Any) -> PromptView:
    """Build one view record from a mapping, a record, or fields."""
    if kwargs:
        if view is not None:
            raise ValueError("a view record is built one way at a time")
        view = kwargs
    return validate_view(view)


def shown_items(items: Any, view: Any) -> Tuple[PromptItem, ...]:
    """The items one view shows, in held order."""
    held_view = _check_view_ref(view)
    return tuple(
        current for current in (
            _check_item_ref(item) for item in items)
        if held_view.shows(current))


# ---------------------------------------------------------------------
# The panel row: one shown item as the panel carries it.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class PromptPanelRow:
    """One shown item as the panel carries it.

    The row carries the item's id, its kind, its
    project, its DERIVED item line, its DERIVED line
    count and its recorded day. The item's words
    never stand in a row - the panel is the craft
    at a glance.
    """

    item_id: str
    kind: str
    project: str
    line: str
    line_count: int
    recorded_on: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "item_id",
            _check_word(self.item_id, "an item id"))
        object.__setattr__(self, "kind", normalize_kind(self.kind))
        object.__setattr__(
            self, "project", _check_project(self.project))
        object.__setattr__(
            self, "line", _check_long_text(self.line, "an item line"))
        object.__setattr__(
            self, "line_count",
            _check_count(self.line_count, "a row's line count"))
        if self.line_count < 1:
            raise ValueError(
                "a panel row stands only for a held item - "
                "its words stand in at least one line")
        object.__setattr__(
            self, "recorded_on", _check_day(self.recorded_on))

    def to_record(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "kind": self.kind,
            "project": self.project,
            "line": self.line,
            "line_count": self.line_count,
            "recorded_on": self.recorded_on,
        }


def _row_for_item(item: PromptItem) -> PromptPanelRow:
    return PromptPanelRow(
        item_id=item.item_id, kind=item.kind,
        project=item.project, line=line_of(item),
        line_count=line_count_of(item),
        recorded_on=item.recorded_on)


def _check_row_ref(value: Any) -> PromptPanelRow:
    if isinstance(value, PromptPanelRow):
        return value
    return validate_row(value)


def validate_row(row: Any, item: Any = None) -> PromptPanelRow:
    """Judge one panel row, against its item when named."""
    if isinstance(row, PromptPanelRow):
        current = row
    elif isinstance(row, dict):
        unknown = set(row) - _ROW_KEYS
        if unknown:
            raise ValueError(
                f"a prompt-craft panel row carries unknown keys: "
                f"{sorted(unknown)}")

        def _needed(spellings: Tuple[str, ...], what: str) -> Any:
            value = _pick_any(row, spellings, what)
            if value is None:
                raise ValueError(f"a prompt-craft panel row names no {what}")
            return value

        current = PromptPanelRow(
            item_id=_needed(("item_id", "id"), "item id"),
            kind=_needed(("kind",), "kind"),
            project=_needed(("project",), "project"),
            line=_needed(("line",), "item line"),
            line_count=_needed(
                ("line_count", "lines"), "line count"),
            recorded_on=_needed(("recorded_on",), "day it was recorded"))
    else:
        raise ValueError(
            f"a prompt-craft panel row must be a mapping, got {row!r}")
    if item is not None:
        held = _check_item_ref(item)
        wanted = _row_for_item(held)
        if current != wanted:
            raise ValueError(
                "a prompt-craft panel row must be its item's own "
                "row - the line and the line count are derived "
                "from the item, never written beside it")
    return current


def build_row(row: Any = None, item: Any = None,
              **kwargs: Any) -> PromptPanelRow:
    """Build one panel row from a mapping, a row, or its item."""
    if item is not None:
        if row is not None or kwargs:
            return validate_row(
                row if row is not None else kwargs, item)
        return _row_for_item(_check_item_ref(item))
    if kwargs:
        if row is not None:
            raise ValueError("a row is built one way at a time")
        row = kwargs
    return validate_row(row)


@dataclass(frozen=True)
class PromptKindCount:
    """How many shown items of one kind a panel holds."""

    kind: str
    items: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", normalize_kind(self.kind))
        object.__setattr__(
            self, "items", _check_count(self.items, "a kind's items"))

    def to_record(self) -> Dict[str, Any]:
        return {"kind": self.kind, "items": self.items}


def _check_kind_count_ref(value: Any) -> PromptKindCount:
    if isinstance(value, PromptKindCount):
        return value
    if isinstance(value, dict):
        unknown = set(value) - _KIND_COUNT_KEYS
        if unknown:
            raise ValueError(
                f"a kind count carries unknown keys: "
                f"{sorted(unknown)}")
        kind = _pick_any(value, ("kind",), "kind")
        items = _pick_any(value, ("items", "count"), "items")
        if kind is None or items is None:
            raise ValueError("a kind count names its kind and its items")
        return PromptKindCount(kind=kind, items=items)
    raise ValueError(f"a kind count must be a mapping, got {value!r}")


def _kind_counts(
        rows: Tuple[PromptPanelRow, ...]) -> Tuple[PromptKindCount, ...]:
    counts: Dict[str, int] = {}
    for row in rows:
        counts[row.kind] = counts.get(row.kind, 0) + 1
    return tuple(
        PromptKindCount(kind=kind, items=counts[kind])
        for kind in ITEM_KINDS if kind in counts)


def _panel_account(total_items: int, total_shown: int,
                   kind_counts: Tuple[PromptKindCount, ...],
                   project_filter: str,
                   as_of: str) -> Tuple[str, ...]:
    kinds = ", ".join(
        f"{count.kind} {count.items}" for count in kind_counts) or "none"
    return (
        f"The prompt craft holds {total_items} items as of "
        f"{as_of}: the view {project_filter!r} shows "
        f"{total_shown} of them: {kinds}.",
        "Rows stand in held order, the order the items were "
        "held in, so two panels of one view diff cleanly, "
        "line by line.",
        "Every line and line count is derived from the item's "
        "own title, kind, project and words - no line is "
        "stored on any item, and no order is chosen by hand.",
        "The input box is a small editor, not a slot, and "
        "this layer holds its craft as data only: it edits "
        "no live input box, pastes nothing, drops nothing, "
        "dictates nothing (dictation is M-180's road, not "
        "built here) and sends nothing.",
    )


@dataclass(frozen=True)
class PromptPanel:
    """The derived panel of one book under one view.

    Rows stand in held order - the order the items
    stand in the book, narrowed by the view; the
    totals are the rows' own counts and the kind
    counts stand in the roadmap's kind order. A
    stored panel is judged whole in
    ``__post_init__``: its totals, its kind counts
    and its account must all be the rows' own
    derived shape - a panel may not soften its view.
    """

    panel_id: Optional[str]
    view_id: Optional[str]
    project_filter: str
    rows: Tuple[PromptPanelRow, ...]
    total_items: int
    total_shown: int
    kind_counts: Tuple[PromptKindCount, ...]
    as_of: str
    account: Tuple[str, ...]

    def __post_init__(self) -> None:
        if self.panel_id is not None:
            object.__setattr__(
                self, "panel_id",
                _check_word(self.panel_id, "a panel id"))
        if self.view_id is not None:
            object.__setattr__(
                self, "view_id",
                _check_word(self.view_id, "a view id"))
        object.__setattr__(
            self, "project_filter",
            normalize_project_filter(self.project_filter))
        rows = tuple(_check_row_ref(r) for r in self.rows)
        object.__setattr__(self, "rows", rows)
        ids = [r.item_id for r in rows]
        if len(set(ids)) != len(ids):
            raise ValueError("panel rows stand one row per item")
        for row in rows:
            if self.project_filter != "all" and (
                    row.project != self.project_filter):
                raise ValueError(
                    "a panel row stands outside its view's "
                    "project - the view narrows the panel, "
                    "never widens it")
        for field in ("total_items", "total_shown"):
            object.__setattr__(
                self, field,
                _check_count(getattr(self, field), f"a panel's {field}"))
        counts = tuple(
            _check_kind_count_ref(c) for c in self.kind_counts)
        object.__setattr__(self, "kind_counts", counts)
        object.__setattr__(self, "as_of", _check_day(self.as_of, "an as-of day"))
        object.__setattr__(self, "account", _check_account(self.account))
        if self.total_shown != len(rows):
            raise ValueError("a panel's shown total is its rows' own count")
        if self.total_items < self.total_shown:
            raise ValueError(
                "a panel's item total cannot stand below "
                "its shown total")
        if counts != _kind_counts(rows):
            raise ValueError("a panel's kind counts are its rows' own counts")
        if rows and self.as_of < max(r.recorded_on for r in rows):
            raise ValueError(
                "a panel's as-of day precedes one of its rows")
        if self.account != _panel_account(
                self.total_items, self.total_shown, counts,
                self.project_filter, self.as_of):
            raise ValueError(
                "a panel's account is its rows' own account, "
                "derived, never written loose")

    def row_for(self, item_id: Any) -> PromptPanelRow:
        """The row one item id names (KeyError if absent)."""
        wanted = _check_word(item_id, "an item id")
        for row in self.rows:
            if row.item_id == wanted:
                return row
        raise KeyError(f"no row named {wanted!r} stands on the panel")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "prompt_craft_panel",
            "slice": PROMPT_CRAFT_SLICE,
            "panel_id": self.panel_id,
            "view_id": self.view_id,
            "project_filter": self.project_filter,
            "rows": [r.to_record() for r in self.rows],
            "total_items": self.total_items,
            "total_shown": self.total_shown,
            "kind_counts": [c.to_record() for c in self.kind_counts],
            "as_of": self.as_of,
            "account": list(self.account),
        }


def _held_items(source: Any) -> Tuple[PromptItem, ...]:
    if isinstance(source, PromptCraftBook):
        return source.items
    if isinstance(source, PromptCraftRegistry):
        return source.list_items()
    if isinstance(source, PromptItem):
        return (source,)
    raise ValueError(f"a prompt-craft source is needed, got {source!r}")


def _held_views(source: Any) -> Tuple[PromptView, ...]:
    if isinstance(source, PromptCraftBook):
        return source.views
    if isinstance(source, PromptCraftRegistry):
        return source.list_views()
    return ()


def _resolve_view(source: Any, view: Any) -> PromptView:
    if view is None:
        raise ValueError(
            "a panel or verdict is derived under a named view")
    if isinstance(view, str):
        wanted = _check_word(view, "a view id")
        for held in _held_views(source):
            if held.view_id == wanted:
                return held
        raise ValueError(
            f"no view named {wanted!r} stands in the source")
    return _check_view_ref(view)


def _default_view(source: Any) -> PromptView:
    """The view a book's own panel stands under, or its first."""
    if isinstance(source, (PromptCraftBook, PromptCraftRegistry)):
        book = source if isinstance(source, PromptCraftBook) else source.book()
        for panel in book.panels:
            if panel.view_id is not None:
                for held in book.views:
                    if held.view_id == panel.view_id:
                        return held
        if book.views:
            return book.views[0]
    raise ValueError("no view stands in the source to derive under")


def derive_panel(source: Any, view: Any = None) -> PromptPanel:
    """Derive the panel of a book under one view."""
    held_view = _resolve_view(source, view)
    items = _held_items(source)
    shown = shown_items(items, held_view)
    rows = tuple(_row_for_item(item) for item in shown)
    counts = _kind_counts(rows)
    as_of = max((i.recorded_on for i in items), default=_EXAMPLE_AS_OF)
    return PromptPanel(
        panel_id=None, view_id=held_view.view_id,
        project_filter=held_view.project_filter,
        rows=rows, total_items=len(items),
        total_shown=len(rows), kind_counts=counts, as_of=as_of,
        account=_panel_account(
            len(items), len(rows), counts,
            held_view.project_filter, as_of))


def validate_panel(panel: Any, source: Any = None) -> PromptPanel:
    """Judge one panel whole, against its source when named."""
    if isinstance(panel, PromptPanel):
        current = panel
    elif isinstance(panel, dict):
        data = dict(panel)
        data.pop("type", None)
        data.pop("slice", None)
        unknown = set(data) - _PANEL_KEYS
        if unknown:
            raise ValueError(
                f"a prompt-craft panel carries unknown keys: "
                f"{sorted(unknown)}")

        def _needed(spellings: Tuple[str, ...], what: str) -> Any:
            value = _pick_any(data, spellings, what)
            if value is None:
                raise ValueError(f"a prompt-craft panel names no {what}")
            return value

        rows_in = _needed(("rows", "shown"), "rows")
        counts_in = _needed(("kind_counts", "kinds"), "kind counts")
        current = PromptPanel(
            panel_id=_pick_any(data, ("panel_id", "id"), "panel id"),
            view_id=_pick_any(data, ("view_id", "view"), "view id"),
            project_filter=_needed(
                ("project_filter", "filter", "project"),
                "project filter"),
            rows=tuple(validate_row(r) for r in rows_in),
            total_items=_needed(
                ("total_items", "items"), "item total"),
            total_shown=_needed(("total_shown", "matched"), "shown total"),
            kind_counts=tuple(
                _check_kind_count_ref(c) for c in counts_in),
            as_of=_needed(("as_of", "day"), "as-of day"),
            account=tuple(_needed(("account", "statements"), "account")))
    else:
        raise ValueError(f"a prompt-craft panel must be a mapping, got {panel!r}")
    if source is not None:
        held_view = _resolve_view(source, current.view_id)
        derived = derive_panel(source, held_view)
        if (current.view_id != derived.view_id
                or current.project_filter != derived.project_filter
                or current.rows != derived.rows
                or current.total_items != derived.total_items
                or current.total_shown != derived.total_shown
                or current.kind_counts != derived.kind_counts
                or current.as_of != derived.as_of
                or current.account != derived.account):
            raise ValueError(
                "a stored panel must equal the panel its book "
                "derives under its view - the panel is "
                "derived, never stored loose")
    return current


def build_panel(panel: Any = None, source: Any = None,
                view: Any = None, **kwargs: Any) -> PromptPanel:
    """Build one panel from a mapping, a panel, or its source."""
    if kwargs:
        if panel is not None:
            raise ValueError("a panel is built one way at a time")
        panel = kwargs
    if panel is None and source is not None:
        return derive_panel(source, view)
    return validate_panel(panel, source)


# ---------------------------------------------------------------------
# The verdict: the whole book under one view, in one word.
# ---------------------------------------------------------------------


def _verdict_word(total_shown: int, distinct_projects: int) -> str:
    if total_shown == 0:
        return "empty"
    if distinct_projects > 1:
        return "shared"
    return "held"


@dataclass(frozen=True)
class PromptVerdict:
    """The derived verdict of one whole book under one view.

    The word is read off the shown items alone:
    empty while no item is shown, held while the
    shown items stand in one project alone, shared
    while they span more than one project. A stored
    verdict is judged against those tallies in
    ``__post_init__``.
    """

    total_items: int
    total_shown: int
    distinct_projects: int
    earliest_on: str
    latest_on: str
    verdict: str

    def __post_init__(self) -> None:
        for field in ("total_items", "total_shown",
                      "distinct_projects"):
            object.__setattr__(
                self, field,
                _check_count(getattr(self, field), f"a verdict's {field}"))
        object.__setattr__(
            self, "earliest_on", _check_day(self.earliest_on, "an earliest day"))
        object.__setattr__(
            self, "latest_on", _check_day(self.latest_on, "a latest day"))
        if self.latest_on < self.earliest_on:
            raise ValueError("a verdict's latest day precedes its earliest")
        if self.total_shown > self.total_items:
            raise ValueError(
                "a verdict's shown tally cannot exceed its "
                "item total")
        if self.total_shown == 0 and self.distinct_projects != 0:
            raise ValueError(
                "an empty verdict names no project among its shown")
        if self.total_shown > 0 and self.distinct_projects == 0:
            raise ValueError(
                "a verdict with shown items names the projects they span")
        if self.distinct_projects > self.total_shown:
            raise ValueError(
                "a verdict's projects cannot exceed its shown items")
        word = _clean_text(self.verdict, "a verdict")
        if word not in VERDICT_WORDS:
            raise ValueError(
                f"a verdict is one of {VERDICT_WORDS}, got {word!r}")
        object.__setattr__(self, "verdict", word)
        if word != _verdict_word(self.total_shown, self.distinct_projects):
            raise ValueError(
                "a verdict's word is derived from its tallies, "
                "never chosen")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "prompt_craft_verdict",
            "slice": PROMPT_CRAFT_SLICE,
            "total_items": self.total_items,
            "total_shown": self.total_shown,
            "distinct_projects": self.distinct_projects,
            "earliest_on": self.earliest_on,
            "latest_on": self.latest_on,
            "verdict": self.verdict,
        }


def derive_verdict(source: Any, view: Any = None) -> PromptVerdict:
    """Derive the verdict of a book under one view."""
    held_view = _resolve_view(source, view)
    items = _held_items(source)
    shown = shown_items(items, held_view)
    distinct = len({item.project for item in shown})
    days = [item.recorded_on for item in items]
    return PromptVerdict(
        total_items=len(items), total_shown=len(shown),
        distinct_projects=distinct,
        earliest_on=min(days) if days else _EXAMPLE_AS_OF,
        latest_on=max(days) if days else _EXAMPLE_AS_OF,
        verdict=_verdict_word(len(shown), distinct))


def _check_verdict_ref(value: Any) -> PromptVerdict:
    if isinstance(value, PromptVerdict):
        return value
    return validate_verdict(value)


def validate_verdict(verdict: Any, source: Any = None,
                     view: Any = None) -> PromptVerdict:
    """Judge one verdict whole, against its source when named."""
    if isinstance(verdict, PromptVerdict):
        current = verdict
    elif isinstance(verdict, dict):
        data = dict(verdict)
        data.pop("type", None)
        data.pop("slice", None)
        unknown = set(data) - _VERDICT_KEYS
        if unknown:
            raise ValueError(
                f"a prompt-craft verdict carries unknown keys: "
                f"{sorted(unknown)}")

        def _needed(spellings: Tuple[str, ...], what: str) -> Any:
            value = _pick_any(data, spellings, what)
            if value is None:
                raise ValueError(f"a prompt-craft verdict names no {what}")
            return value

        current = PromptVerdict(
            total_items=_needed(
                ("total_items", "items"), "item total"),
            total_shown=_needed(("total_shown", "matched"), "shown total"),
            distinct_projects=_needed(
                ("distinct_projects", "projects"), "distinct projects"),
            earliest_on=_needed(("earliest_on", "earliest"), "earliest day"),
            latest_on=_needed(("latest_on", "latest"), "latest day"),
            verdict=_needed(("verdict",), "verdict"))
    else:
        raise ValueError(f"a prompt-craft verdict must be a mapping, got {verdict!r}")
    if source is not None:
        derived = derive_verdict(source, view)
        if current != derived:
            raise ValueError(
                "a stored verdict must equal the verdict its "
                "book derives under its view - the verdict "
                "is derived, never stored loose")
    return current


def build_verdict(verdict: Any = None, source: Any = None,
                  view: Any = None, **kwargs: Any) -> PromptVerdict:
    """Build one verdict from a mapping, a verdict, or its source."""
    if kwargs:
        if verdict is not None:
            raise ValueError("a verdict is built one way at a time")
        verdict = kwargs
    if verdict is None and source is not None:
        return derive_verdict(source, view)
    return validate_verdict(verdict, source, view)


# ---------------------------------------------------------------------
# The book: one set of items and views, held whole.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class PromptCraftBook:
    """One set of craft items and views, held whole.

    Items stand in held order - one item per item
    id - views stand in recorded order, one view
    per sequence and per id, and every stored panel
    is judged against the book and the view it
    stands under.
    """

    title: str
    items: Tuple[PromptItem, ...] = ()
    views: Tuple[PromptView, ...] = ()
    panels: Tuple[PromptPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_title(self.title, "a book title"))
        items = tuple(_check_item_ref(i) for i in self.items)
        object.__setattr__(self, "items", items)
        ids = [i.item_id for i in items]
        if len(set(ids)) != len(ids):
            raise ValueError("a book holds one item per item id")
        views = tuple(_check_view_ref(v) for v in self.views)
        object.__setattr__(self, "views", views)
        seqs = [v.seq for v in views]
        if seqs != sorted(seqs) or len(set(seqs)) != len(seqs):
            raise ValueError(
                "a book's views stand in recorded order, "
                "one view per sequence")
        view_ids = [
            v.view_id for v in views if v.view_id is not None]
        if len(set(view_ids)) != len(view_ids):
            raise ValueError("a book holds one view per view id")
        panels = tuple(validate_panel(p, self) for p in self.panels)
        object.__setattr__(self, "panels", panels)

    def item_for(self, item_id: Any) -> PromptItem:
        """The item one id names (KeyError if absent)."""
        wanted = _check_word(item_id, "an item id")
        for item in self.items:
            if item.item_id == wanted:
                return item
        raise KeyError(f"no item named {wanted!r} stands in the book")

    def view_for(self, view_id: Any) -> PromptView:
        """The view one id names (KeyError if absent)."""
        wanted = _check_word(view_id, "a view id")
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no view named {wanted!r} stands in the book")

    def panel_for(self, panel_id: Any) -> PromptPanel:
        """The panel one id names (KeyError if absent)."""
        wanted = _check_word(panel_id, "a panel id")
        for panel in self.panels:
            if panel.panel_id == wanted:
                return panel
        raise KeyError(f"no panel named {wanted!r} stands in the book")

    def item_ids(self) -> Tuple[str, ...]:
        """The book's item ids, in held order."""
        return tuple(i.item_id for i in self.items)

    def view_ids(self) -> Tuple[Optional[str], ...]:
        """The book's view ids, in recorded order."""
        return tuple(v.view_id for v in self.views)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "prompt_craft_book",
            "slice": PROMPT_CRAFT_SLICE,
            "title": self.title,
            "items": [i.to_record() for i in self.items],
            "views": [v.to_record() for v in self.views],
            "panels": [p.to_record() for p in self.panels],
            "item_count": len(self.items),
            "view_count": len(self.views),
        }


def _judge_book_panels(book: PromptCraftBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def validate_book(data: Any, *, require_example: bool = False) -> PromptCraftBook:
    """Judge one prompt-craft file's data whole and return its book."""
    if isinstance(data, PromptCraftBook):
        book = data
        _judge_book_panels(book)
        if require_example:
            _check_example(book)
        return book
    if not isinstance(data, dict):
        raise ValueError(f"a prompt-craft book must be a mapping, got {data!r}")
    unknown = set(data) - _PROMPT_CRAFT_KEYS
    if unknown:
        raise ValueError(
            f"a prompt-craft book carries unknown keys: {sorted(unknown)}")
    if data.get("schema") != PROMPT_CRAFT_SCHEMA:
        raise ValueError(
            f"a prompt-craft book's schema must be "
            f"{PROMPT_CRAFT_SCHEMA!r}, got {data.get('schema')!r}")
    if data.get("slice") != PROMPT_CRAFT_SLICE:
        raise ValueError(
            f"a prompt-craft book's slice must be "
            f"{PROMPT_CRAFT_SLICE!r}, got {data.get('slice')!r}")
    guide = data.get("guide") or {}
    title = _pick_any(guide, ("title", "name"), "title")
    if title is None:
        title = _pick_any(data, ("title", "name"), "title")
    items_in = _pick_any(data, ("items",), "items")
    if items_in is None:
        raise ValueError("a prompt-craft book names no items")
    views_in = data.get("views") or []
    panels_in = data.get("panels") or []
    items = []
    for raw in items_in:
        stored = dict(raw)
        stored.pop("type", None)
        stored.pop("slice", None)
        for derived_key in ("line", "line_count"):
            stored.pop(derived_key, None)
        items.append(validate_item(stored))
    views = []
    for raw in views_in:
        stored = dict(raw)
        stored.pop("type", None)
        stored.pop("slice", None)
        views.append(validate_view(stored))
    book = PromptCraftBook(
        title=title,
        items=tuple(items),
        views=tuple(views),
        panels=tuple(validate_panel(p) for p in panels_in))
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def _check_example(book: PromptCraftBook) -> None:
    if book.title != _EXAMPLE_TITLE:
        raise ValueError(
            f"the shipped example book is {_EXAMPLE_TITLE!r}, "
            f"got {book.title!r}")
    if book.item_ids() != _EXAMPLE_ITEM_IDS:
        raise ValueError("the shipped example book's items differ")
    first = book.items[0]
    if first.item_id != _EXAMPLE_FIRST_ITEM_ID or (
            first.kind != _EXAMPLE_FIRST_ITEM_KIND) or (
            first.project != _EXAMPLE_FIRST_ITEM_PROJECT):
        raise ValueError("the shipped example book's first item differs")
    if book.view_ids() != _EXAMPLE_VIEW_IDS:
        raise ValueError("the shipped example book's views differ")
    if len(book.panels) != 1 or (
            book.panels[0].panel_id != _EXAMPLE_PANEL_ID):
        raise ValueError("the shipped example book's panel differs")
    if book.panels[0].as_of != _EXAMPLE_AS_OF:
        raise ValueError("the shipped example book's as-of day differs")
    derived = derive_panel(book, book.panels[0].view_id)
    if tuple(r.item_id for r in book.panels[0].rows) != tuple(
            r.item_id for r in derived.rows):
        raise ValueError("the shipped example book's panel rows differ")


def build_book(book: Any = None, **kwargs: Any) -> PromptCraftBook:
    """Build one book from a mapping, a book, or fields."""
    if isinstance(book, PromptCraftBook) and not kwargs:
        return validate_book(book)
    if kwargs:
        if book is not None:
            raise ValueError("a book is built one way at a time")
        fields = dict(kwargs)
    elif isinstance(book, dict) and (
            "items" in book) and (
            "schema" not in book and "guide" not in book
            and "canon_note" not in book):
        fields = dict(book)
    else:
        return _book_from(book, require_example=False)
    unknown = set(fields) - _BOOK_KEYS - {
        "items", "views", "panels"}
    if unknown:
        raise ValueError(
            f"a prompt-craft book carries unknown keys: "
            f"{sorted(unknown)}")
    title = _pick_any(fields, ("title", "name"), "title")
    if title is None:
        raise ValueError("a prompt-craft book names no title")
    items_in = _pick_any(fields, ("items",), "items") or ()
    return PromptCraftBook(
        title=title,
        items=tuple(_check_item_ref(i) for i in items_in),
        views=tuple(
            _check_view_ref(v) for v in fields.get("views") or ()),
        panels=tuple(
            validate_panel(p) for p in fields.get("panels") or ()))


def _book_from(data: Any, *, require_example: bool) -> PromptCraftBook:
    if isinstance(data, PromptCraftBook):
        return validate_book(data, require_example=require_example)
    if isinstance(data, dict):
        return validate_book(data, require_example=require_example)
    raise ValueError(f"a prompt-craft book must be a mapping, got {data!r}")


def load_prompt_craft(data: Optional[Dict[str, Any]] = None) -> PromptCraftBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(PROMPT_CRAFT_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_prompt_craft_file(path: Any) -> PromptCraftBook:
    """Load one prompt-craft file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: items and views held one by one.
# ---------------------------------------------------------------------


class PromptCraftRegistry:
    """An in-memory holding of craft items and views.

    The registry is the pure layer's model of a
    session's prompt craft: items are held under
    their item ids, one item per id, in held order,
    and views are held in recorded order, one view
    per sequence and per id. Holding is data only -
    no item held here is typed into a live box,
    pasted, dropped or sent.
    """

    def __init__(self, book: Any = None) -> None:
        self._items: List[PromptItem] = []
        self._views: List[PromptView] = []
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

    def _check_item_free(self, item: PromptItem) -> None:
        for held in self._items:
            if held.item_id == item.item_id:
                raise ValueError(
                    f"an item already stands under id "
                    f"{item.item_id!r}")

    def register_item(self, item: Any) -> PromptItem:
        """Hold one item, judged whole before it is held."""
        validated = _check_item_ref(item)
        self._check_item_free(validated)
        self._items.append(validated)
        return validated

    def _check_view_free(self, view: PromptView) -> None:
        for held in self._views:
            if view.view_id is not None and (
                    held.view_id == view.view_id):
                raise ValueError(
                    f"a view already stands under id "
                    f"{view.view_id!r}")
            if held.seq == view.seq:
                raise ValueError(
                    f"a view already stands at sequence "
                    f"{view.seq} - the book holds one "
                    f"view per place")

    def register_view(self, view: Any) -> PromptView:
        """Hold one view record, judged whole first.

        A view id or a sequence already standing here
        refuses and holds nothing new. A held view
        only ever looks: standing it derives its
        panel, edits no live box and sends nothing.
        """
        validated = _check_view_ref(view)
        self._check_view_free(validated)
        if validated.view_id is None:
            validated = PromptView(
                view_id=self._fresh_view_id(
                    {v.view_id for v in self._views}),
                seq=validated.seq,
                project_filter=validated.project_filter,
                detail=validated.detail,
                recorded_on=validated.recorded_on,
                actor=validated.actor, source=validated.source,
                origin_session=validated.origin_session)
        self._views.append(validated)
        self._views.sort(key=lambda v: v.seq)
        return validated

    def register_book(self, book: Any) -> PromptCraftBook:
        """Hold a whole book, judged whole first."""
        validated = build_book(book)
        for item in validated.items:
            self._check_item_free(item)
        if self._title is None:
            self._title = validated.title
        elif validated.title != self._title:
            raise ValueError(
                "a second book under a different title refuses - "
                "one book stands in one registry")
        for item in validated.items:
            self._items.append(item)
        for view in validated.views:
            self.register_view(view)
        return self.book()

    def get_item(self, item_id: Any) -> PromptItem:
        """The item one id names (KeyError if absent)."""
        wanted = _check_word(item_id, "an item id")
        for item in self._items:
            if item.item_id == wanted:
                return item
        raise KeyError(f"no item named {wanted!r} stands held")

    def get_view(self, view_id: Any) -> PromptView:
        """The view record one id names (KeyError if absent)."""
        wanted = _check_word(view_id, "a view id")
        for view in self._views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no view named {wanted!r} stands held")

    def latest_view(self) -> PromptView:
        """The last view recorded (KeyError if none)."""
        if not self._views:
            raise KeyError("no view stands held")
        return self._views[-1]

    def list_items(self) -> Tuple[PromptItem, ...]:
        return tuple(self._items)

    def list_views(self) -> Tuple[PromptView, ...]:
        return tuple(self._views)

    def book(self) -> PromptCraftBook:
        return PromptCraftBook(
            title=self._title or "Prompt Craft",
            items=tuple(self._items),
            views=tuple(self._views))

    def panel(self, view: Any = None) -> PromptPanel:
        return derive_panel(self.book(), view)

    def verdict(self, view: Any = None) -> PromptVerdict:
        return derive_verdict(self.book(), view)


def items_with_kind(source: Any, kind: Any) -> Tuple[PromptItem, ...]:
    """The items of one kind, in held order."""
    wanted = normalize_kind(kind)
    return tuple(
        i for i in _held_items(source) if i.kind == wanted)


def items_for_project(source: Any, project: Any) -> Tuple[PromptItem, ...]:
    """The items standing in one project, in held order.

    The every-project filter names every item in
    held order - the view's own reading, shared here.
    """
    wanted = normalize_project_filter(project)
    if wanted == "all":
        return _held_items(source)
    return tuple(
        i for i in _held_items(source) if i.project == wanted)


def total_items(source: Any) -> int:
    """How many items a source holds."""
    return len(_held_items(source))


# ---------------------------------------------------------------------
# Session news, plain words, and the screens.
# ---------------------------------------------------------------------


def item_record(item: Any) -> Dict[str, Any]:
    """The session-news record of one craft item."""
    current = _check_item_ref(item)
    record_out = current.to_record()
    record_out["news"] = True
    record_out["headline"] = (
        f"Prompt craft item {current.item_id}: "
        f"{line_of(current)} - {current.line_count} "
        f"{_lines_word(current.line_count)} held as words.")
    return record_out


def image_record(image: Any) -> Dict[str, Any]:
    """The session-news record of one pasted image."""
    current = validate_image(image)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Prompt craft pasted image {current.image_id}: "
        f"{current.name} ({current.format}) - "
        f"{current.note}")
    return record


def file_record(dropped: Any) -> Dict[str, Any]:
    """The session-news record of one dropped file."""
    current = validate_file(dropped)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Prompt craft dropped file {current.file_id}: "
        f"{current.path} - {current.note}")
    return record


def view_record(view: Any) -> Dict[str, Any]:
    """The session-news record of one view record."""
    current = _check_view_ref(view)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Prompt craft view {current.view_id or current.seq}: "
        f"project {current.project_filter!r} - "
        f"{current.detail}")
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of one derived panel."""
    current = validate_panel(panel, source)
    record = current.to_record()
    record["news"] = True
    kinds = ", ".join(
        f"{c.kind} {c.items}" for c in current.kind_counts)
    record["headline"] = (
        f"Prompt craft panel as of {current.as_of}: "
        f"{current.total_shown} of {current.total_items} "
        f"items show for project {current.project_filter!r} "
        f"({kinds}).")
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    """The session-news record of one derived verdict."""
    current = validate_verdict(verdict, source, view)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Prompt craft verdict: {current.verdict} - "
        f"{current.total_shown} of {current.total_items} "
        f"items shown across {current.distinct_projects} "
        f"projects, from {current.earliest_on} to "
        f"{current.latest_on}.")
    return record


def book_record(book: Any) -> Dict[str, Any]:
    """The session-news record of one prompt-craft book."""
    current = book if isinstance(book, PromptCraftBook) else build_book(book)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Prompt craft {current.title}: "
        f"{record['item_count']} items named, "
        f"{record['view_count']} views held.")
    return record


def plain_words(item: Any) -> str:
    """One item, in one plain sentence."""
    current = _check_item_ref(item)
    return (
        f"{line_of(current)} - one piece of prompt craft on "
        f"item {current.item_id}: {current.line_count} "
        f"{_lines_word(current.line_count)} of words held "
        f"whole in the {current.project} project. Holding "
        f"it here edits nothing, pastes nothing, drops "
        f"nothing and sends nothing.")


def view_plain_words(view: Any) -> str:
    """One view record, in one plain sentence."""
    current = _check_view_ref(view)
    return (
        f"View {current.view_id or current.seq} looks at "
        f"project {current.project_filter!r}, recorded on "
        f"{current.recorded_on} by {current.actor}: "
        f"{current.detail} A view only ever looks - it "
        f"edits no live input box and sends nothing.")


def panel_plain_words(source: Any, view: Any = None) -> str:
    """The panel in plain words, in full."""
    if isinstance(source, PromptPanel):
        panel = validate_panel(source)
        title = None
    elif isinstance(source, (PromptCraftBook, PromptCraftRegistry)):
        book = source if isinstance(
            source, PromptCraftBook) else source.book()
        panel = derive_panel(
            book, view if view is not None
            else _default_view(book))
        title = book.title
    else:
        raise ValueError(f"a prompt-craft source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    lines.append("Shown, in held order:")
    for row in panel.rows:
        lines.append(
            f"{row.item_id}: {row.line} "
            f"({row.line_count} {_lines_word(row.line_count)}, "
            f"{row.recorded_on})")
    lines.extend(panel.account)
    return "\n".join(lines)


def verdict_plain_words(source: Any, view: Any = None) -> str:
    """The book verdict in plain words, in full."""
    if isinstance(source, PromptVerdict):
        verdict = validate_verdict(source)
    elif isinstance(source, (PromptCraftBook, PromptCraftRegistry)):
        book = source if isinstance(
            source, PromptCraftBook) else source.book()
        verdict = derive_verdict(
            book, view if view is not None
            else _default_view(book))
    else:
        raise ValueError(f"a prompt-craft source is needed, got {source!r}")
    return (
        f"Prompt craft verdict: {verdict.verdict} - "
        f"{verdict.total_shown} of {verdict.total_items} "
        f"items shown, across {verdict.distinct_projects} "
        f"projects, from {verdict.earliest_on} to "
        f"{verdict.latest_on} - every line and line count "
        f"is derived from the items' own fields.")


def _source_book(source: Any) -> PromptCraftBook:
    if source is None:
        return load_prompt_craft()
    if isinstance(source, PromptCraftRegistry):
        return source.book()
    if isinstance(source, PromptCraftBook):
        return source
    if isinstance(source, PromptItem):
        return PromptCraftBook(title="One craft item", items=(source,))
    raise ValueError(f"a prompt-craft book is needed, got {source!r}")


def format_item(item: Any) -> str:
    """One craft item as a screen block.

    The item's kind, project, title and words stand
    as their own lines, and its provenance stands
    whole - an item held here is a finding, never
    the act of typing, pasting or sending it.
    """
    current = _check_item_ref(item)
    lines = [
        f"{current.item_id}: {line_of(current)}",
        f"Kind: {current.kind}",
        f"Project: {current.project}",
        f"Title: {current.title}",
        f"Lines: {current.line_count}",
        f"Words: {current.body}",
        f"Recorded: on {current.recorded_on} by {current.actor} "
        f"from {current.source} in {current.origin_session}.",
    ]
    return "\n".join(lines)


def format_view(view: Any) -> str:
    """One view record as a screen block."""
    current = _check_view_ref(view)
    lines = [
        f"{current.view_id or '-'}: project "
        f"{current.project_filter!r}",
        f"Words: {current.detail}",
        f"Recorded: on {current.recorded_on} by {current.actor} "
        f"from {current.source} in {current.origin_session}.",
    ]
    return "\n".join(lines)


def format_book(source: Any = None, kind: Any = None) -> str:
    """The book as derived lines, in held order.

    By default the lines are every item's derived
    line. With ``kind`` only that kind's items
    stand in the list.
    """
    book = _source_book(source)
    wanted = normalize_kind(kind) if kind is not None else None
    lines = []
    for item in book.items:
        if wanted is not None and item.kind != wanted:
            continue
        lines.append(f"{item.item_id}: {line_of(item)}")
    if not lines:
        lines.append("No items stand in the book on that reading.")
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    """The panel as a screen block: every row and the account."""
    if isinstance(source, PromptPanel):
        panel = validate_panel(source)
        lines: list = []
    else:
        book = _source_book(source)
        panel = derive_panel(
            book, view if view is not None
            else _default_view(book))
        lines = [f"Panel in {book.title}:"]
    lines.append("Shown, in held order:")
    for row in panel.rows:
        lines.append(
            f"{row.item_id}: {row.line} - "
            f"{row.line_count} {_lines_word(row.line_count)} "
            f"({row.recorded_on})")
    lines.extend(panel.account)
    return "\n".join(lines)


def format_verdict(source: Any = None, view: Any = None) -> str:
    """The verdict as a screen block."""
    if isinstance(source, PromptVerdict):
        verdict = validate_verdict(source)
        title = "the book"
    else:
        book = _source_book(source)
        verdict = derive_verdict(
            book, view if view is not None
            else _default_view(book))
        title = book.title
    return (
        f"Verdict in Prompt Craft over {title}: "
        f"{verdict.verdict} - {verdict.total_shown} of "
        f"{verdict.total_items} items shown, "
        f"across {verdict.distinct_projects} projects, from "
        f"{verdict.earliest_on} to {verdict.latest_on}.")


def format_prompt_craft_screen(source: Any = None) -> str:
    """The whole prompt-craft screen for one book."""
    book = _source_book(source)
    view = _default_view(book)
    panel = derive_panel(book, view)
    verdict = derive_verdict(book, view)
    lines = [
        f"Prompt Craft (M-177) - {book.title}",
        format_book(book),
        f"Panel: {panel.total_shown} of "
        f"{panel.total_items} items show "
        f"for project {panel.project_filter!r}.",
        f"Verdict: {verdict.verdict}.",
        "This layer holds prompt craft as data only - "
        "it edits no live input box, pastes nothing, "
        "drops nothing, dictates nothing (dictation "
        "is M-180's road) and sends nothing.",
    ]
    return "\n".join(lines)


def parse_prompt_craft_args(args: Any) -> Tuple[str, Any]:
    """Parse the /promptcraft grammar into (action, target).

    ``""``/``show``/``list`` show the book;
    ``item <item-id>`` shows one item whole;
    ``view <view-id>`` shows one held view record;
    ``project <project>`` derives the panel of an
    ad-hoc view over one project (``all`` names
    every project); ``kind <kind>`` shows one
    kind's items; ``panel`` and ``verdict`` show
    the derived panel and verdict under the book's
    own view. Anything else raises ValueError
    carrying the usage line.
    """
    if args is None:
        return ("show", None)
    if not isinstance(args, str):
        raise ValueError(USAGE)
    parts = args.split()
    if not parts or parts == ["show"] or parts == ["list"]:
        return ("show", None)
    if parts[0] == "item" and len(parts) == 2:
        return ("item", _check_word(parts[1], "an item id"))
    if parts[0] == "view" and len(parts) == 2:
        return ("view", _check_word(parts[1], "a view id"))
    if parts[0] == "project" and len(parts) == 2:
        try:
            return ("project", normalize_project_filter(parts[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if parts[0] == "kind" and len(parts) == 2:
        try:
            return ("kind", normalize_kind(parts[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if parts == ["panel"]:
        return ("panel", None)
    if parts == ["verdict"]:
        return ("verdict", None)
    raise ValueError(USAGE)
