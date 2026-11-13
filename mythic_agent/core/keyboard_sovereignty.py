"""Keyboard sovereignty (All-Features roadmap slice M-187).

Part VIII - The Beautiful Face - builds here. The
roadmap's words: *every act reachable by keyboard;
a printable keymap; vim-mode prompt option for
those whose hands speak it.*

What already ships, and what this slice adds:

* The shipped tree already carries keyboard roads
  (the terminal loop is keyboard-only in
  construction - the M-171 charter's terminal-loop
  row, S-08, says so in its evidence, and its
  direction orders that construction to stay
  exactly as it is). What nothing held is
  *keyboard sovereignty*, as checkable data: one
  record per act, held whole with the keyboard
  road that reaches it; the printable keymap,
  derived from those held records; and the
  vim-mode prompt option, held as data beside
  them. This slice is that book, in its own
  module.
* An act is held whole: the act it names, the
  area it lives in (a closed vocabulary - chat,
  terminal, editor, review, settings, onboarding,
  lessons, command palace), the key that reaches
  it, named as data, and its detail. An act
  naming no key is held honestly with an empty
  key: it stands unreachable, named in its gaps
  - reachability is judged from the held records
  alone, never claimed live. Two acts standing
  under one key refuse by name: one act stands
  per key, or the keymap could not be read.
* The printable keymap is DERIVED at call time
  from the held acts' keys - never a second
  stored copy that could drift from the acts
  themselves. A stored keymap, reachability
  verdict or coverage judgement on any record
  refuses by name.
* The vim-mode prompt option is held as data: a
  mode record naming the mode - off or modal, a
  closed vocabulary - its title, its detail and
  its key grammar, the lines that say what the
  keys do in that mode. A book holds at most one
  record per mode word. Holding the option
  changes no live prompt: the rule stands as
  data (:data:`KEYBOARD_RULE`) and a record
  claiming a live key press, a live UI render or
  a live prompt-mode change refuses BY NAME.
* The shipped data file (``mythic_agent/data/
  keyboard_sovereignty.yaml``) holds one example
  book in exactly the shape a real keymap file
  takes, a loader reads a keymap file anywhere on
  disk, acts and views are shaped as session
  news, and a small in-memory registry holds
  records one by one. The agent layer owns
  holding a keymap book for a session and
  printing from it. This layer reaches no live
  road: it presses no keys, renders no live UI,
  changes no live prompt mode and writes
  nothing - it holds keyboard sovereignty as
  data and tells it.

Honesty rules, enforced here and pinned by tests:

* **Reachability from records alone.** Every
  reachability telling is derived from the held
  act records; a claim of a live key press, a
  live UI or a live prompt change refuses by
  name.
* **Unreachable stands unreachable.** An act
  naming no key stands unreachable, named in its
  gaps - no key is invented for it.
* **The keymap is derived, never stored.** The
  printable keymap is derived from the held
  acts at call time; a stored keymap refuses by
  name, so it can never drift.
* **One act per key.** Two acts standing under
  one key refuse by name.
* **The vim option is data alone.** The mode
  records hold the option; holding, viewing or
  printing them switches no prompt mode.
"""

from __future__ import annotations

__all__ = [
    "AREAS",
    "EXAMPLE_KEY",
    "KEYBOARD_RULE",
    "KEYBOARD_SOVEREIGNTY_RESOURCE",
    "KEYBOARD_SOVEREIGNTY_SCHEMA",
    "KEYBOARD_SOVEREIGNTY_SLICE",
    "MODES",
    "PLAIN_EXPLANATION",
    "PRINT_ACTION",
    "REACH_WORDS",
    "THE_KEYBOARD_SOVEREIGNTY_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "VIEW_FILTERS",
    "Any",
    "Dict",
    "List",
    "Optional",
    "ActRecord",
    "KeyboardBook",
    "KeyboardKeymap",
    "KeyboardPanel",
    "KeyboardPanelRow",
    "KeyboardRegistry",
    "KeyboardVerdict",
    "KeyboardView",
    "KeymapEntry",
    "ModeRecord",
    "ReachCount",
    "act_for_key",
    "act_gaps",
    "act_passes",
    "act_plain_words",
    "act_record",
    "acts_for_area",
    "book_record",
    "build_act",
    "build_book",
    "build_mode",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "derive_keymap",
    "derive_panel",
    "derive_verdict",
    "format_act",
    "format_book",
    "format_key",
    "format_keyboard_screen",
    "format_keymap",
    "format_mode",
    "format_panel",
    "format_verdict",
    "format_view",
    "inspect_keyboard_source",
    "keymap_plain_words",
    "keymap_record",
    "load_keyboard_sovereignty",
    "load_keyboard_sovereignty_file",
    "mode_for_word",
    "mode_plain_words",
    "mode_record",
    "normalize_area",
    "normalize_mode",
    "normalize_view_filter",
    "panel_plain_words",
    "panel_record",
    "parse_keyboard_args",
    "passing_acts",
    "plain_lines",
    "plain_words",
    "segment_of",
    "shown_acts",
    "total_acts",
    "validate_act",
    "validate_book",
    "validate_mode",
    "validate_panel",
    "validate_row",
    "validate_verdict",
    "validate_view",
    "verdict_plain_words",
    "verdict_record",
    "view_plain_words",
    "view_record",
    "vim_mode",
]

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource

KEYBOARD_SOVEREIGNTY_SCHEMA = "mythic.keyboard_sovereignty/1"
KEYBOARD_SOVEREIGNTY_SLICE = "M-187"
THE_KEYBOARD_SOVEREIGNTY_SLICE = KEYBOARD_SOVEREIGNTY_SLICE
KEYBOARD_SOVEREIGNTY_RESOURCE = "keyboard_sovereignty.yaml"
PRINT_ACTION = "print"
EXAMPLE_KEY = "Ctrl-K"
REACH_WORDS = ("reachable", "unreachable")
AREAS = (
    "chat", "terminal", "editor", "review", "settings",
    "onboarding", "lessons", "command palace")
MODES = ("off", "modal")
VIEW_FILTERS = ("all", "reachable", "unreachable")
VERDICT_WORDS = ("open", "strained", "shut")
KEYBOARD_RULE = (
    "keyboard sovereignty is held as data alone: "
    "holding, viewing and printing the keymap press "
    "no keys, render no live UI and change no live "
    "prompt mode - reachability is judged from the "
    "held records alone, never claimed live")
PLAIN_EXPLANATION = (
    "Keyboard sovereignty (M-187): every act stands "
    "held with the key that reaches it, the keymap "
    "prints from those held keys, and the vim-mode "
    "prompt option stands held as data beside them.")
USAGE = (
    "Usage: /keymap | /keymap act <act-id> | "
    "/keymap key <key> | /keymap area <area> | "
    "/keymap view <view-id> | /keymap mode <mode-id> | "
    "/keymap print | /keymap panel | /keymap verdict")

_PROVENANCE = ("recorded_on", "actor", "source", "origin_session")
_ACT_KEYS = frozenset({
    "act_id", "seq", "title", "area", "key", "detail",
} | set(_PROVENANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_PROVENANCE))
_MODE_KEYS = frozenset({
    "mode_id", "seq", "mode", "title", "detail", "grammar",
} | set(_PROVENANCE))
_DERIVED_KEYS = frozenset({
    "reach", "reachable", "gaps", "segment",
    "plain_lines", "telling", "verdict", "keymap",
    "entries", "coverage", "covered", "uncovered"})
_LIVE_KEYS = (
    "live_keys", "press_key", "presses_keys",
    "key_press", "live_ui", "render_ui",
    "live_prompt", "prompt_mode_change",
    "changes_prompt", "applies_mode", "enables_vim",
    "switches_mode")


# ---------------------------------------------------------------------
# Small judges, in the sibling shape.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_key(value: Any) -> str:
    """A held key road: a chord named as data, or honestly empty.

    An act naming no key is held with an empty key
    and stands unreachable in its gaps; a key that
    is not a string at all refuses.
    """
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError("a key must be a string naming the key road")
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


def _check_lines(value: Any, what: str) -> Tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError(f"{what} must be a list of lines")
    lines = []
    for line in value:
        lines.append(_clean_text(line, f"a line of {what}"))
    return tuple(lines)


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
                f"{what} claims a live keyboard road "
                f"({key!r} is named on it): "
                f"{KEYBOARD_RULE}")
    for key in mapping:
        if key in _DERIVED_KEYS:
            raise ValueError(
                f"{what} carries {key!r}, which is derived from its "
                f"own fields and never stored")
        if key not in allowed:
            raise ValueError(f"{what} carries unknown field {key!r}")


def normalize_area(value: Any) -> str:
    area = _clean_text(value, "an area").lower()
    if area not in AREAS:
        raise ValueError(
            f"area {area!r} is not one of the named areas: "
            + ", ".join(AREAS))
    return area


def normalize_mode(value: Any) -> str:
    mode = _clean_text(value, "a prompt mode").lower()
    if mode not in MODES:
        raise ValueError(
            f"prompt mode {mode!r} is not one of the held "
            f"modes: " + ", ".join(MODES))
    return mode


def normalize_view_filter(value: Any) -> str:
    view_filter = _clean_text(value, "a view filter").lower()
    if view_filter not in VIEW_FILTERS:
        raise ValueError(
            f"view filter {view_filter!r} is not one of the held "
            f"filters: " + ", ".join(VIEW_FILTERS))
    return view_filter


# ---------------------------------------------------------------------
# The held act: one act, with the key that reaches it.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ActRecord:
    """One act, held as data with its keyboard road.

    The act names its title, the area it lives in
    - one of the closed area vocabulary - the key
    that reaches it, named as data, and its
    detail. An act naming no key is held with an
    empty key: it stands unreachable, named in
    its gaps, and no key is invented for it. The
    act is local data alone - no live road stands
    behind it: holding it presses nothing.
    """

    act_id: str
    seq: int
    title: str
    area: str
    key: str = ""
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "act_id", _clean_text(self.act_id, "an act id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a title"))
        object.__setattr__(self, "area", normalize_area(self.area))
        object.__setattr__(self, "key", _check_key(self.key))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "an act detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.act_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "act_id": self.act_id, "seq": self.seq,
            "title": self.title, "area": self.area,
            "key": self.key, "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_act_ref(value: Any) -> ActRecord:
    if not isinstance(value, ActRecord):
        raise ValueError("an act must be an ActRecord")
    return value


def validate_act(act: Any) -> ActRecord:
    return _check_act_ref(act)


def build_act(act: Any = None, **kwargs: Any) -> ActRecord:
    """Build one held act from a mapping or fields."""
    if act is None:
        data = dict(kwargs)
    elif isinstance(act, ActRecord):
        if kwargs:
            raise ValueError("an act stands whole or by fields, not both")
        return act
    elif isinstance(act, dict):
        data = dict(act)
        data.update(kwargs)
    else:
        raise ValueError("an act must be a mapping or an ActRecord")
    _needed(data, _ACT_KEYS, "an act")
    return ActRecord(
        act_id=data.get("act_id"), seq=data.get("seq"),
        title=data.get("title"), area=data.get("area"),
        key=data.get("key"), detail=data.get("detail"),
        **_provenance(data))


def act_gaps(act: Any) -> Tuple[str, ...]:
    """The gaps that keep an act from keyboard reach."""
    checked = _check_act_ref(act)
    return () if checked.key else ("no key",)


def act_passes(act: Any) -> bool:
    return not act_gaps(act)


def plain_lines(act: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the act's own fields."""
    checked = _check_act_ref(act)
    return (
        f"Act: {checked.title}",
        f"Area: {checked.area}",
        f"Key: {checked.key if checked.key else 'none'}",
    )


def segment_of(act: Any) -> str:
    checked = _check_act_ref(act)
    gaps = act_gaps(checked)
    return (
        f"{checked.act_id}: {checked.title} in area "
        f"'{checked.area}' - key: "
        f"'{checked.key if checked.key else 'none'}' - "
        f"detail: '{checked.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held mode: the vim-mode prompt option, as data.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ModeRecord:
    """One prompt-mode option, held as data.

    The record names the mode - off or modal, one
    of the closed mode vocabulary - with its
    title, its detail and its key grammar, the
    lines that say what the keys do in that mode.
    One record stands per mode word in a book.
    The record is data alone: holding it switches
    no live prompt mode, ever.
    """

    mode_id: str
    seq: int
    mode: str
    title: str
    detail: str = ""
    grammar: Tuple[str, ...] = ()
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "mode_id", _clean_text(self.mode_id, "a mode id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(self, "mode", normalize_mode(self.mode))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a mode title"))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a mode detail"))
        object.__setattr__(
            self, "grammar", _check_lines(self.grammar, "grammar"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.mode_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "mode_id": self.mode_id, "seq": self.seq,
            "mode": self.mode, "title": self.title,
            "detail": self.detail, "grammar": list(self.grammar),
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_mode_ref(value: Any) -> ModeRecord:
    if not isinstance(value, ModeRecord):
        raise ValueError("a mode must be a ModeRecord")
    return value


def validate_mode(mode: Any) -> ModeRecord:
    return _check_mode_ref(mode)


def build_mode(mode: Any = None, **kwargs: Any) -> ModeRecord:
    if mode is None:
        data = dict(kwargs)
    elif isinstance(mode, ModeRecord):
        if kwargs:
            raise ValueError("a mode stands whole or by fields, not both")
        return mode
    elif isinstance(mode, dict):
        data = dict(mode)
        data.update(kwargs)
    else:
        raise ValueError("a mode must be a mapping or a ModeRecord")
    _needed(data, _MODE_KEYS, "a mode")
    return ModeRecord(
        mode_id=data.get("mode_id"), seq=data.get("seq"),
        mode=data.get("mode"), title=data.get("title"),
        detail=data.get("detail"), grammar=data.get("grammar"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held view: which acts a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class KeyboardView:
    """A view over the book: every act, the reachable, the rest."""

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


def _check_view_ref(value: Any) -> KeyboardView:
    if not isinstance(value, KeyboardView):
        raise ValueError("a view must be a KeyboardView")
    return value


def validate_view(view: Any) -> KeyboardView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> KeyboardView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, KeyboardView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or a KeyboardView")
    _needed(data, _VIEW_KEYS, "a view")
    return KeyboardView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_provenance(data))


def inspect_keyboard_source(piece: Any) -> Dict[str, Any]:
    """Name what one keyboard source piece is, without judging it."""
    if isinstance(piece, ActRecord):
        return {"kind": "act", "act_id": piece.act_id}
    if isinstance(piece, dict):
        if "act_id" in piece:
            return {"kind": "act", "act_id": piece.get("act_id")}
        if "view_id" in piece:
            return {"kind": "view", "view_id": piece.get("view_id")}
        if "mode_id" in piece:
            return {"kind": "mode", "mode_id": piece.get("mode_id")}
    return {"kind": "unknown", "act_id": None}


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class KeyboardPanelRow:
    item_id: str
    reach: str
    label: str
    segment: str
    recorded_on: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id, "reach": self.reach,
            "label": self.label, "segment": self.segment,
            "recorded_on": self.recorded_on,
        }


def _row_for_act(act: ActRecord) -> KeyboardPanelRow:
    return KeyboardPanelRow(
        item_id=act.act_id,
        reach="reachable" if act_passes(act) else "unreachable",
        label=act.title, segment=segment_of(act),
        recorded_on=act.recorded_on)


def _check_row_ref(value: Any) -> KeyboardPanelRow:
    if not isinstance(value, KeyboardPanelRow):
        raise ValueError("a panel row must be a KeyboardPanelRow")
    return value


def validate_row(row: Any, act: Any = None) -> KeyboardPanelRow:
    checked = _check_row_ref(row)
    if act is not None:
        derived = _row_for_act(_check_act_ref(act))
        if checked != derived:
            raise ValueError(
                f"panel row {checked.item_id!r} does not agree with "
                f"the row derived from its act")
    return checked


def build_row(row: Any = None, act: Any = None,
              **kwargs: Any) -> KeyboardPanelRow:
    if act is not None:
        derived = _row_for_act(_check_act_ref(act))
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            KeyboardPanelRow(**kwargs))
        return validate_row(built, act)
    if isinstance(row, KeyboardPanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        reach = _clean_text(data.get("reach"), "a row reach").lower()
        if reach not in REACH_WORDS:
            raise ValueError(f"row reach {reach!r} is not a held word")
        return KeyboardPanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            reach=reach,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on day"))
    if row is None and kwargs:
        return KeyboardPanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or a KeyboardPanelRow")


@dataclass(frozen=True)
class ReachCount:
    reach: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"reach": self.reach, "items": self.items}


def _reach_counts(rows: Tuple[KeyboardPanelRow, ...]
                  ) -> Tuple[ReachCount, ...]:
    counts: List[ReachCount] = []
    for reach in REACH_WORDS:
        number = sum(1 for row in rows if row.reach == reach)
        if number:
            counts.append(ReachCount(reach=reach, items=number))
    return tuple(counts)


def _panel_account(total_items: int, total_shown: int,
                   passing_shown: int,
                   reach_counts: Tuple[ReachCount, ...],
                   view_filter: str, as_of: str) -> Tuple[str, ...]:
    reach_words = ", ".join(
        f"{count.reach} {count.items}"
        for count in reach_counts) or "none"
    return (
        f"The keymap book holds {total_items} acts as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {reach_words}; {passing_shown} of the shown acts "
        f"stand reachable by keyboard.",
        "Rows stand in held order, the order the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its act's own fields "
        "- the title, the area it lives in and "
        "the key that honestly reaches it - and no "
        "judgement is stored on any act.",
        "Reachability is judged from the held records alone: "
        "an act naming no key stands unreachable, and the "
        "printable keymap is derived from the held keys, "
        "never stored where it could drift.",
    )


@dataclass(frozen=True)
class KeyboardPanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[KeyboardPanelRow, ...]
    total_items: int
    total_shown: int
    reach_counts: Tuple[ReachCount, ...]
    as_of: str
    account: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "panel_id": self.panel_id, "view_id": self.view_id,
            "view_filter": self.view_filter,
            "rows": [row.to_record() for row in self.rows],
            "total_items": self.total_items,
            "total_shown": self.total_shown,
            "reach_counts": [c.to_record() for c in self.reach_counts],
            "as_of": self.as_of, "account": list(self.account),
        }


def _resolve_view(source: Any, view: Any) -> KeyboardView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, KeyboardView):
        return view
    return book.view_for(view)


def shown_acts(source: Any, view: Any = None
               ) -> Tuple[ActRecord, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.acts
    if resolved.view_filter == "reachable":
        return tuple(a for a in book.acts if act_passes(a))
    return tuple(a for a in book.acts if not act_passes(a))


def acts_for_area(source: Any, area: Any
                  ) -> Tuple[ActRecord, ...]:
    wanted = normalize_area(area)
    return tuple(
        a for a in _source_book(source).acts if a.area == wanted)


def passing_acts(source: Any) -> Tuple[ActRecord, ...]:
    return tuple(
        a for a in _source_book(source).acts if act_passes(a))


def total_acts(source: Any) -> int:
    return len(_source_book(source).acts)


def derive_panel(source: Any, view: Any = None) -> KeyboardPanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_acts(book, resolved)
    rows = tuple(_row_for_act(act) for act in shown)
    counts = _reach_counts(rows)
    as_of = max((a.recorded_on for a in book.acts), default="")
    passing = sum(1 for a in shown if act_passes(a))
    return KeyboardPanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.acts), total_shown=len(shown),
        reach_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.acts), len(shown), passing, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> KeyboardPanel:
    if not isinstance(value, KeyboardPanel):
        raise ValueError("a panel must be a KeyboardPanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> KeyboardPanel:
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
                     "total_shown", "reach_counts", "as_of", "account"):
            if getattr(checked, attr) != getattr(derived, attr):
                raise ValueError(
                    f"panel {checked.panel_id!r} disagrees with the "
                    f"panel derived from its book on {attr}")
    return checked


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> KeyboardPanel:
    if isinstance(panel, KeyboardPanel):
        if kwargs:
            raise ValueError("a panel stands whole or by fields, not both")
        return validate_panel(panel, source)
    if isinstance(panel, dict):
        data = dict(panel)
        data.update(kwargs)
        rows = tuple(build_row(row) for row in data.get("rows") or ())
        counts = tuple(
            ReachCount(
                reach=_clean_text(
                    c.get("reach"), "a reach count word").lower(),
                items=_check_count(c.get("items"), "a reach count"))
            for c in data.get("reach_counts") or ()
            if isinstance(c, dict))
        built = KeyboardPanel(
            panel_id=_clean_text(data.get("panel_id"), "a panel id"),
            view_id=data.get("view_id"),
            view_filter=normalize_view_filter(data.get("view_filter")),
            rows=rows,
            total_items=_check_count(
                data.get("total_items"), "a total_items count"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            reach_counts=counts,
            as_of=_clean_text(data.get("as_of"), "an as_of day"),
            account=_check_lines(data.get("account"), "the account"))
        return validate_panel(built, source)
    if panel is None and source is not None:
        return derive_panel(source, kwargs.get("view"))
    raise ValueError("a panel must be a mapping, a KeyboardPanel, or derived")


def _verdict_word(total_shown: int, passing_shown: int) -> str:
    if total_shown > 0 and passing_shown == total_shown:
        return "open"
    if passing_shown == 0:
        return "shut"
    return "strained"


@dataclass(frozen=True)
class KeyboardVerdict:
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


def derive_verdict(source: Any, view: Any = None) -> KeyboardVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_acts(book, resolved)
    passing = sum(1 for a in shown if act_passes(a))
    latest = max((a.recorded_on for a in shown), default="")
    return KeyboardVerdict(
        verdict=_verdict_word(len(shown), passing),
        view_id=resolved.view_id, total_shown=len(shown),
        passing_shown=passing, latest_on=latest)


def _check_verdict_ref(value: Any) -> KeyboardVerdict:
    if not isinstance(value, KeyboardVerdict):
        raise ValueError("a verdict must be a KeyboardVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> KeyboardVerdict:
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
                  **kwargs: Any) -> KeyboardVerdict:
    if isinstance(verdict, KeyboardVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = KeyboardVerdict(
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
        "a verdict must be a mapping, a KeyboardVerdict, or derived")


# ---------------------------------------------------------------------
# The keymap: derived from the held acts' keys at call time, and the
# mode roads: which prompt-mode records the book holds, derived too.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class KeymapEntry:
    key: str
    act_id: str
    title: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "key": self.key, "act_id": self.act_id,
            "title": self.title,
        }


@dataclass(frozen=True)
class KeyboardKeymap:
    """The printable keymap, derived from the held acts.

    The keymap names one entry per reachable act,
    in held order - the act's own key, its id and
    its title - and the acts that stand
    unreachable, named in its gaps. Nothing here
    is stored on any act: the keymap is derived
    at call time from the held records alone, so
    it can never drift from them.
    """

    entries: Tuple[KeymapEntry, ...]
    gaps: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "entries": [e.to_record() for e in self.entries],
            "gaps": list(self.gaps),
        }


def derive_keymap(source: Any) -> KeyboardKeymap:
    """Derive the printable keymap from the book's held acts."""
    book = _source_book(source)
    entries = tuple(
        KeymapEntry(key=act.key, act_id=act.act_id, title=act.title)
        for act in book.acts if act_passes(act))
    gaps = tuple(
        act.act_id for act in book.acts if not act_passes(act))
    return KeyboardKeymap(entries=entries, gaps=gaps)


def act_for_key(source: Any, key: Any) -> Optional[ActRecord]:
    """The held act one key reaches, or none - honestly."""
    wanted = _check_key(key)
    if not wanted:
        return None
    for act in _source_book(source).acts:
        if act.key == wanted:
            return act
    return None


def mode_for_word(source: Any, mode: Any) -> Optional[ModeRecord]:
    """The held mode record for one mode word, or none."""
    wanted = normalize_mode(mode)
    for record in _source_book(source).modes:
        if record.mode == wanted:
            return record
    return None


def vim_mode(source: Any) -> Optional[ModeRecord]:
    """The held vim-mode (modal) prompt option, or none."""
    return mode_for_word(source, "modal")


# ---------------------------------------------------------------------
# The book: acts, views and modes held together, one pinned panel at
# most per telling, and no verdict or keymap ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class KeyboardBook:
    title: str
    acts: Tuple[ActRecord, ...] = ()
    views: Tuple[KeyboardView, ...] = ()
    modes: Tuple[ModeRecord, ...] = ()
    panels: Tuple[KeyboardPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        acts = tuple(_check_act_ref(a) for a in self.acts)
        views = tuple(_check_view_ref(v) for v in self.views)
        modes = tuple(_check_mode_ref(m) for m in self.modes)
        panels = tuple(_check_panel_ref(p) for p in self.panels)
        seen_ids = set()
        seen_seqs = set()
        seen_keys = set()
        for act in acts:
            if act.act_id in seen_ids:
                raise ValueError(
                    f"two acts stand under id {act.act_id!r}")
            if act.seq in seen_seqs:
                raise ValueError(
                    f"two acts stand at sequence {act.seq}")
            if act.key:
                if act.key in seen_keys:
                    raise ValueError(
                        f"two acts stand under key {act.key!r}: "
                        f"one act stands per key")
                seen_keys.add(act.key)
            seen_ids.add(act.act_id)
            seen_seqs.add(act.seq)
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
        mode_ids = set()
        mode_seqs = set()
        mode_words = set()
        for record in modes:
            if record.mode_id in mode_ids:
                raise ValueError(
                    f"two modes stand under id {record.mode_id!r}")
            if record.seq in mode_seqs:
                raise ValueError(
                    f"two modes stand at sequence {record.seq}")
            if record.mode in mode_words:
                raise ValueError(
                    f"two mode records stand for mode "
                    f"{record.mode!r}: one mode record stands "
                    f"per mode")
            mode_ids.add(record.mode_id)
            mode_seqs.add(record.seq)
            mode_words.add(record.mode)
        object.__setattr__(
            self, "acts", tuple(sorted(acts, key=lambda a: a.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "modes", tuple(sorted(modes, key=lambda m: m.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.acts + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(a.act_id for a in self.acts) + tuple(
            v.view_id for v in self.views)

    def act_ids(self) -> Tuple[str, ...]:
        return tuple(a.act_id for a in self.acts)

    def act_for(self, act_id: Any) -> ActRecord:
        wanted = _clean_text(act_id, "an act id")
        for act in self.acts:
            if act.act_id == wanted:
                return act
        raise KeyError(f"no act named {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> KeyboardView:
        wanted = _clean_text(view_id, "a view id")
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no view named {wanted!r} stands in this book")

    def mode_for(self, mode_id: Any) -> ModeRecord:
        wanted = _clean_text(mode_id, "a mode id")
        for record in self.modes:
            if record.mode_id == wanted:
                return record
        raise KeyError(f"no mode named {wanted!r} stands in this book")

    def item_for(self, item_id: Any) -> Any:
        wanted = _clean_text(item_id, "an item id")
        for act in self.acts:
            if act.act_id == wanted:
                return act
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "acts": [a.to_record() for a in self.acts],
            "views": [v.to_record() for v in self.views],
            "modes": [m.to_record() for m in self.modes],
            "panels": [p.to_record() for p in self.panels],
        }


def _judge_book_panels(book: KeyboardBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: KeyboardBook) -> None:
    if book.title != "Keyboard sovereignty at the M-186 slice boundary":
        raise ValueError("the shipped example book carries another title")
    if len(book.acts) != 6 or len(book.views) != 2:
        raise ValueError(
            "the shipped example book must hold six acts and two views")
    if len(book.modes) != 2:
        raise ValueError(
            "the shipped example book must hold two mode records")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-m186-boundary":
        raise ValueError("the pinned panel is panel-m186-boundary")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "strained" or verdict.passing_shown != 5:
        raise ValueError(
            "the shipped example book's verdict must stand strained "
            "at five reachable of six")
    keymap = derive_keymap(book)
    if [e.key for e in keymap.entries] != [
            "Enter", "Ctrl-Z", "Ctrl-K", "y", "Ctrl-P"]:
        raise ValueError(
            "the shipped example book's keymap must derive the "
            "five held keys in held order")
    if keymap.gaps != ("act-drag-select",):
        raise ValueError(
            "the shipped example book must leave the drag-select "
            "act honestly unreachable, named in its gaps")
    found = act_for_key(book, EXAMPLE_KEY)
    if found is None or found.act_id != "act-open-keymap":
        raise ValueError(
            "the shipped example book must reach its keymap act "
            "under the example key")
    modal = vim_mode(book)
    if modal is None or modal.mode_id != "mode-vim":
        raise ValueError(
            "the shipped example book must hold the vim-mode "
            "prompt option as its modal record")


def validate_book(data: Any, *, require_example: bool = False) -> KeyboardBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, KeyboardBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a keyboard book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live keyboard road "
                f"({key!r} is named on it): {KEYBOARD_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its acts under a view")
    if "keymap" in data or "keymaps" in data:
        raise ValueError(
            "a book stores no keymap: the keymap is derived from "
            "its held acts at call time")
    if data.get("schema") is not None and (
            data["schema"] != KEYBOARD_SOVEREIGNTY_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{KEYBOARD_SOVEREIGNTY_SCHEMA!r}")
    if data.get("slice") is not None and (
            data["slice"] != KEYBOARD_SOVEREIGNTY_SLICE):
        raise ValueError(
            f"a book's slice must be {KEYBOARD_SOVEREIGNTY_SLICE!r}")
    guide = data.get("guide") or {}
    if not isinstance(guide, dict):
        raise ValueError("a book's guide must be a mapping")
    title = guide.get("title") or data.get("title")
    acts = tuple(build_act(a) for a in data.get("acts") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    modes = tuple(build_mode(m) for m in data.get("modes") or ())
    book = KeyboardBook(
        title=title, acts=acts, views=views, modes=modes, panels=())
    panels = tuple(
        build_panel(p, book) for p in data.get("panels") or ())
    book = KeyboardBook(
        title=book.title, acts=book.acts, views=book.views,
        modes=book.modes, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> KeyboardBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (KeyboardBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or a KeyboardBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> KeyboardBook:
    return validate_book(data, require_example=require_example)


def load_keyboard_sovereignty(
        data: Optional[Dict[str, Any]] = None) -> KeyboardBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(KEYBOARD_SOVEREIGNTY_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_keyboard_sovereignty_file(path: Any) -> KeyboardBook:
    """Load one keymap file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: acts and views held one by one.
# ---------------------------------------------------------------------

class KeyboardRegistry:
    """An in-memory holding of acts and views.

    The registry is the pure layer's model of a
    session's keymap book: acts are held under
    their ids, one act per id, per sequence and
    per key, and views are held in recorded order,
    one view per sequence and per id. Holding is
    data only - nothing held here presses a key,
    renders a live UI, or changes a prompt mode.
    """

    def __init__(self, book: Any = None) -> None:
        self._acts: List[ActRecord] = []
        self._views: List[KeyboardView] = []
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

    def register_act(self, item: Any) -> ActRecord:
        """Hold one act, judged whole before held."""
        checked = _check_act_ref(item)
        for other in self._acts:
            if checked.key and other.key == checked.key:
                raise ValueError(
                    f"an act already stands under key "
                    f"{checked.key!r}: one act stands per key")
        return self._register(
            self._acts, checked, "act_id", "act")

    def register_view(self, view: Any) -> KeyboardView:
        """Hold one view; a view naming no id takes a fresh one."""
        checked = _check_view_ref(view)
        if not checked.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            checked = build_view({**checked.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, checked, "view_id", "view")

    def register_book(self, book: Any) -> KeyboardBook:
        """Hold a whole book's acts and views, under its title."""
        checked = build_book(book)
        if self._title is not None and checked.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {checked.title!r}")
        for act in checked.acts:
            self.register_act(act)
        for view in checked.views:
            self.register_view(view)
        self._title = checked.title
        return self.book()

    def book(self) -> KeyboardBook:
        return KeyboardBook(
            title=self._title or "An unheld keyboard book",
            acts=tuple(self._acts), views=tuple(self._views),
            modes=(), panels=())

    def list_acts(self) -> Tuple[ActRecord, ...]:
        return tuple(self._acts)

    def list_views(self) -> Tuple[KeyboardView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._acts) + tuple(self._views)

    def get_act(self, act_id: Any) -> ActRecord:
        return self.book().act_for(act_id)

    def get_view(self, view_id: Any) -> KeyboardView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records shaped for the journal road.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> KeyboardBook:
    if source is None:
        return load_keyboard_sovereignty()
    if isinstance(source, KeyboardBook):
        return source
    if isinstance(source, KeyboardRegistry):
        return source.book()
    return build_book(source)


def _provenance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _PROVENANCE}


def act_record(act: Any, source: Any = None) -> Dict[str, Any]:
    checked = _check_act_ref(act)
    record = {
        "type": "keyboard_act",
        "slice": KEYBOARD_SOVEREIGNTY_SLICE,
        "act_id": checked.act_id,
        "title": checked.title,
        "segment": segment_of(checked),
        "passes": act_passes(checked),
        "gaps": list(act_gaps(checked)),
    }
    record.update(_provenance_record(checked))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    checked = _check_view_ref(view)
    record = {
        "type": "keyboard_view",
        "slice": KEYBOARD_SOVEREIGNTY_SLICE,
        "view_id": checked.view_id, "seq": checked.seq,
        "view_filter": checked.view_filter,
    }
    record.update(_provenance_record(checked))
    return record


def mode_record(record_in: Any) -> Dict[str, Any]:
    checked = _check_mode_ref(record_in)
    record = {
        "type": "keyboard_mode",
        "slice": KEYBOARD_SOVEREIGNTY_SLICE,
        "mode_id": checked.mode_id,
        "mode": checked.mode,
    }
    record.update(_provenance_record(checked))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    checked = validate_panel(panel, source)
    record = {"type": "keyboard_panel",
              "slice": KEYBOARD_SOVEREIGNTY_SLICE}
    record.update(checked.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, KeyboardVerdict):
        checked = validate_verdict(verdict, source)
    else:
        checked = derive_verdict(_source_book(verdict), view)
    record = {"type": "keyboard_verdict",
              "slice": KEYBOARD_SOVEREIGNTY_SLICE}
    record.update(checked.to_record())
    return record


def keymap_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, KeyboardKeymap):
        keymap = source
    else:
        keymap = derive_keymap(source)
    record = {"type": "keyboard_keymap",
              "slice": KEYBOARD_SOVEREIGNTY_SLICE}
    record.update(keymap.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    checked = _source_book(book)
    record = {"type": "keyboard_book",
              "slice": KEYBOARD_SOVEREIGNTY_SLICE,
              "title": checked.title}
    record.update(checked.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(act: Any, source: Any = None) -> str:
    checked = _check_act_ref(act)
    return (
        f"{checked.title} - in area {checked.area}: "
        f"key {checked.key if checked.key else 'none'}. "
        f"{checked.detail}")


def act_plain_words(act: Any, source: Any = None) -> str:
    return plain_words(act, source)


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The keymap book stands {verdict.verdict}: "
        f"{verdict.passing_shown} of {verdict.total_shown} shown "
        f"acts stand reachable by keyboard.")


def view_plain_words(view: Any) -> str:
    checked = _check_view_ref(view)
    return f"View {checked.view_id}: shows {checked.view_filter} acts."


def mode_plain_words(record_in: Any) -> str:
    checked = _check_mode_ref(record_in)
    return (
        f"Mode {checked.mode_id}: the {checked.mode} prompt "
        f"option. {checked.detail}")


def keymap_plain_words(source: Any) -> str:
    keymap = (source if isinstance(source, KeyboardKeymap)
              else derive_keymap(source))
    gaps = ", ".join(keymap.gaps) or "none"
    return (
        f"The keymap holds {len(keymap.entries)} keys for "
        f"{len(keymap.entries)} acts; unreachable, named in "
        f"its gaps: {gaps}.")


def format_act(act: Any, source: Any = None) -> str:
    checked = _check_act_ref(act)
    lines = [f"{checked.title} ({checked.act_id})"]
    lines.extend(plain_lines(checked))
    lines.append(checked.detail)
    if act_passes(checked):
        lines.append(
            "This act stands reachable by keyboard, under "
            "the key its record names.")
    else:
        lines.append(
            "This act stands unreachable - it names no key, "
            "stands named in its gaps, and no key is "
            "invented for it.")
    return "\n".join(lines)


def format_view(view: Any) -> str:
    checked = _check_view_ref(view)
    return (
        f"View {checked.view_id}: filter {checked.view_filter} - "
        f"{checked.detail}")


def format_mode(record_in: Any) -> str:
    checked = _check_mode_ref(record_in)
    lines = [
        f"Prompt mode {checked.mode} ({checked.mode_id}): "
        f"{checked.title}. {checked.detail}"]
    lines.extend(f"  {line}" for line in checked.grammar)
    lines.append(
        "This option stands held as data alone - holding "
        "or reading it switches no live prompt mode.")
    return "\n".join(lines)


def format_key(source: Any, key: Any) -> str:
    act = act_for_key(source, key)
    if act is not None:
        return format_act(act)
    wanted = _check_key(key)
    return (
        f"No held act stands under key {wanted!r} yet - the "
        f"key reaches nothing in this book, and no act is "
        f"invented for it.")


def format_book(source: Any = None, area: Any = None) -> str:
    book = _source_book(source)
    acts = (acts_for_area(book, area)
            if area is not None else book.acts)
    lines = [f"Keyboard Sovereignty (M-187) - {book.title}"]
    lines.extend(segment_of(act) for act in acts)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Keyboard panel under view {panel.view_id}:"]
    lines.extend(row.segment for row in panel.rows)
    lines.extend(panel.account)
    return "\n".join(lines)


def format_verdict(source: Any = None, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return verdict_plain_words(source, view) + (
        f" (view {verdict.view_id}, as of {verdict.latest_on})")


def format_keymap(source: Any = None) -> str:
    book = _source_book(source)
    keymap = derive_keymap(book)
    lines = ["Printable keymap, derived from the held acts:"]
    for entry in keymap.entries:
        lines.append(f"{entry.key} - {entry.title} ({entry.act_id})")
    if keymap.gaps:
        lines.append(
            "Unreachable by keyboard, named honestly: "
            + ", ".join(keymap.gaps) + ".")
    lines.append(
        "Printed from the held records alone - printing "
        "presses no keys and changes no prompt mode.")
    return "\n".join(lines)


def format_keyboard_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "Keyboard Sovereignty (M-187)",
        f"{book.title}: {len(book.acts)} acts held, "
        f"{len(passing_acts(book))} acts standing reachable, "
        f"{len(book.modes)} prompt modes held.",
    ]
    if book.views:
        panel = derive_panel(book, book.views[0])
        lines.append(
            f"{panel.total_shown} of {panel.total_items} items show "
            f"under the first view.")
        lines.extend(row.segment for row in panel.rows)
    lines.append(keymap_plain_words(book))
    lines.append(PLAIN_EXPLANATION)
    return "\n".join(lines)


def parse_keyboard_args(args: Any) -> Tuple[str, Any]:
    """Parse the /keymap grammar into (action, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("act", "view", "mode"):
        if len(parts) != 2:
            raise ValueError(USAGE)
        return (head, parts[1])
    if head in ("key", "area"):
        if len(parts) < 2:
            raise ValueError(USAGE)
        return (head, " ".join(parts[1:]))
    if head in ("print", "panel", "verdict") and len(parts) == 1:
        return (head, None)
    raise ValueError(USAGE)
