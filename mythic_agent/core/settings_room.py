"""Settings as one room (All-Features roadmap slice M-196).

Part VIII - The Beautiful Face - builds here. The
roadmap words: *every setting in one searchable
screen, each with its plain-language meaning and
its current source (default/project/user/session)
shown.*

What already ships, and what this slice adds:

* Settings already stand scattered - the setup
  wizard's nine sections, the GitHub config modal,
  the config files themselves. What nothing held
  is *the settings gathered as one room, as a
  book*: every setting held as checkable data -
  one card per setting, held whole with its name,
  its section (a closed vocabulary - model, keys,
  display, behaviour, privacy), its current value
  and its current source layer (a closed
  vocabulary - default, project, user, session),
  held honestly, and the plain-language meaning
  it carries, named as data; the settings index,
  derived from those held settings; the views,
  which show every setting, the ready or the
  incomplete; and the notes on settings, held as
  data beside them - note, concern, praise and
  question named as stances, each feeding back to
  the user as data, never applied by this layer.
  This slice is that book, in its own module,
  standing in the M-195 copy-and-share book shape.
  The M-171 charter names this slice on TWO rows:
  S-02, the setup wizard (verdict rebuild,
  co-owned with M-184 and M-182), and S-05, the
  GitHub config modal (verdict keep, sole owner
  M-196; its direction: the card folds into the
  one room unchanged in shape, its unnamed-
  overwrite and unexplained-save-failure strains
  repaired there) - the slice tests pin that
  ownership live.

* A setting is held whole: the name it stands
  under, its section, its current value and its
  source layer - held honestly, an unknown value
  standing empty, never invented - the plain
  meaning it carries, named as data, and its
  detail. A setting naming no plain meaning is
  held honestly with an empty meaning: it stands
  incomplete, named in its gaps - completeness is
  judged from the held records alone, never
  claimed live.
* The settings index is DERIVED at call time from
  the held settings - never a second stored copy
  that could drift from the settings themselves.
  A stored index, completeness verdict or coverage
  judgement on any record refuses by name.
* The notes are held as data: a note record naming
  its setting, its stance - note, concern, praise
  or question, a closed vocabulary - and what it
  feeds back toward. A book holds at most one note
  record per setting stance. Holding a note
  applies none of it: the rule stands as data
  (:data:`ROOM_RULE`) and a record claiming a
  setting was actually changed, applied or saved,
  or that a config was actually written, refuses
  BY NAME.
* The shipped data file holds one example book in
  exactly the shape a real settings file takes, a
  loader reads a settings file anywhere on disk,
  settings and views are shaped as session news,
  and a small in-memory registry holds records one
  by one. The agent layer owns holding a settings
  book for a session and telling from it. This
  layer reaches no live road: it changes nothing,
  applies nothing, saves nothing, writes no config
  and opens no network - it holds the settings as
  data and tells it.

Honesty rules, enforced here and pinned by tests:

* **Completeness from records alone.** Every
  completeness telling is derived from the held
  setting records; a claim of a live change, apply,
  save or config write refuses by name.
* **Incomplete stands incomplete.** A setting
  naming no plain meaning stands incomplete, named
  in its gaps - no meaning is invented for it.
* **Unknown stays unknown.** A current value that
  is not known stands empty on its setting - no
  figure is invented for it.
* **The index is derived, never stored.** The
  settings index is derived from the held settings
  at call time; a stored index refuses by name, so
  it can never drift.
* **One setting per setting.** Two settings
  standing for one setting id refuse by name, and
  one note record stands per setting stance.
* **The notes are data alone.** The records hold
  the feedback; holding, viewing or telling them
  changes nothing, applies nothing and saves
  nothing.
"""


from __future__ import annotations

__all__ = [
    "SECTIONS",
    "LAYERS",
    "EXAMPLE_MEANING",
    "STANCES",
    "INDEX_ACTION",
    "SETTINGS_ROOM_RESOURCE",
    "SETTINGS_ROOM_SCHEMA",
    "SETTINGS_ROOM_SLICE",
    "ROOM_RULE",
    "PLAIN_EXPLANATION",
    "THE_SETTINGS_ROOM_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "VIEW_FILTERS",
    "READY_WORDS",
    "Any",
    "Dict",
    "List",
    "Optional",
    "SettingCard",
    "IndexEntry",
    "NoteRecord",
    "RoomBook",
    "RoomIndex",
    "RoomPanel",
    "RoomPanelRow",
    "SettingsRoomRegistry",
    "RoomVerdict",
    "RoomView",
    "TargetCount",
    "book_record",
    "build_book",
    "build_setting",
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
    "format_setting",
    "format_index",
    "format_note",
    "format_room_screen",
    "format_panel",
    "format_meaning",
    "format_verdict",
    "format_view",
    "setting_for_meaning",
    "setting_gaps",
    "setting_passes",
    "setting_plain_words",
    "setting_record",
    "settings_for_section",
    "index_plain_words",
    "index_record",
    "inspect_setting_source",
    "note_for_setting",
    "note_plain_words",
    "note_record",
    "load_settings_room",
    "load_settings_room_file",
    "normalize_section",
    "normalize_layer",
    "normalize_stance",
    "normalize_view_filter",
    "panel_plain_words",
    "panel_record",
    "parse_room_args",
    "passing_settings",
    "plain_lines",
    "plain_words",
    "segment_of",
    "shown_settings",
    "total_settings",
    "validate_book",
    "validate_setting",
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

SETTINGS_ROOM_SCHEMA = "mythic.settings_room/1"
SETTINGS_ROOM_SLICE = "M-196"
THE_SETTINGS_ROOM_SLICE = SETTINGS_ROOM_SLICE
SETTINGS_ROOM_RESOURCE = "settings_room.yaml"
INDEX_ACTION = "index"
EXAMPLE_MEANING = "the model that answers you"
READY_WORDS = ("ready", "unready")
SECTIONS = ("model", "keys", "display", "behaviour", "privacy")
LAYERS = ("default", "project", "user", "session")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "ready", "unready")
VERDICT_WORDS = ("open", "strained", "shut")
ROOM_RULE = (
    "settings as one room is held as data alone: "
    "holding, viewing and reading the settings "
    "changes nothing, applies nothing, saves "
    "nothing, writes no config and opens no "
    "network - completeness is judged from the "
    "held records alone, never claimed live")
PLAIN_EXPLANATION = (
    "Settings as one room (M-196): "
    "every setting stands held as a card "
    "with its name, its section, its current "
    "value and source layer honestly held, the "
    "plain-language meaning it carries, and the "
    "views that arrange the settings - every "
    "setting in one searchable screen, each "
    "with its plain-language meaning and its "
    "current source shown.")
USAGE = (
    "Usage: /settingsroom | /settingsroom setting <setting-id> | "
    "/settingsroom meaning <meaning> | /settingsroom section <section> | "
    "/settingsroom view <view-id> | /settingsroom note <note-id> | "
    "/settingsroom index | /settingsroom panel | /settingsroom verdict")

_PROVENANCE = ("recorded_on", "actor", "source", "origin_session")
_SETTING_KEYS = frozenset({
    "setting_id", "seq", "name", "section", "value", "layer",
    "meaning", "detail",
} | set(_PROVENANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_PROVENANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "setting_id", "stance", "target", "title",
    "detail",
} | set(_PROVENANCE))
_DERIVED_KEYS = frozenset({
    "standing", "ready", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "entries", "coverage", "covered", "uncovered"})
_LIVE_KEYS = (
    "live_setting", "live_view", "shows_setting",
    "show_setting", "shown_setting", "changes_setting",
    "changed_setting", "change_setting", "applies_setting",
    "applied_setting", "apply_setting", "saves_setting",
    "saved_setting", "save_setting", "writes_config",
    "wrote_config", "write_config", "config_write",
    "sets_setting", "set_setting", "setting_now",
    "applies_now", "changes_now", "saves_now",
    "opens_network", "writes_file", "write_file",
    "renders_now", "posts_note", "posted_note")


# ---------------------------------------------------------------------
# Small judges, in the sibling shape.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_meaning(value: Any) -> str:
    """A held plain meaning: named as data, or honestly empty.

    A setting naming no plain meaning is held with
    an empty meaning and stands incomplete in its
    gaps; a meaning that is not a string at all
    refuses.
    """
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError("a meaning must be a string naming the plain meaning")
    return value.strip()


def _check_measure(value: Any, what: str) -> str:
    """A held measure: a current value, named as data or honestly empty.

    A setting whose current value is not known is
    held with an empty value: unknown stays unknown,
    and no figure is invented for it. A value that
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
                f"{what} claims a live setting change "
                f"({key!r} is named on it): "
                f"{ROOM_RULE}")
    for key in mapping:
        if key in _DERIVED_KEYS:
            raise ValueError(
                f"{what} carries {key!r}, which is derived from its "
                f"own fields and never stored")
        if key not in allowed:
            raise ValueError(f"{what} carries unknown field {key!r}")


def normalize_section(value: Any) -> str:
    section = _clean_text(value, "a section").lower()
    if section not in SECTIONS:
        raise ValueError(
            f"section {section!r} is not one of the named sections: "
            + ", ".join(SECTIONS))
    return section


def normalize_layer(value: Any) -> str:
    layer = _clean_text(value, "a layer").lower()
    if layer not in LAYERS:
        raise ValueError(
            f"layer {layer!r} is not one of the named layers: "
            + ", ".join(LAYERS))
    return layer


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
# The held setting: one setting, with the meaning that explains it.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class SettingCard:
    """One setting, held as data with its plain meaning.

    The setting names its plain name, the section it
    lives in - one of the closed section vocabulary -
    its current value and its source layer, the plain
    meaning it carries, named as data, and its detail.
    A setting naming no plain meaning is held with an
    empty meaning: it stands incomplete, named in its
    gaps, and no meaning is invented for it. The
    setting is local data alone - no live change stands
    behind it: holding it changes nothing.
    """

    setting_id: str
    seq: int
    name: str
    section: str
    value: str = ""
    layer: str = "default"
    meaning: str = ""
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "setting_id", _clean_text(self.setting_id, "a setting id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "name", _clean_text(self.name, "a name"))
        object.__setattr__(self, "section", normalize_section(self.section))
        object.__setattr__(
            self, "value", _check_measure(self.value, "a value"))
        object.__setattr__(self, "layer", normalize_layer(self.layer))
        object.__setattr__(
            self, "meaning", _check_meaning(self.meaning))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a setting detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.setting_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "setting_id": self.setting_id, "seq": self.seq,
            "name": self.name, "section": self.section,
            "value": self.value, "layer": self.layer,
            "meaning": self.meaning, "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_setting_ref(value: Any) -> SettingCard:
    if not isinstance(value, SettingCard):
        raise ValueError("a setting must be a SettingCard")
    return value


def validate_setting(setting: Any) -> SettingCard:
    return _check_setting_ref(setting)


def build_setting(record: Any = None, **kwargs: Any) -> SettingCard:
    """Build one held setting from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, SettingCard):
        if kwargs:
            raise ValueError("a setting stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a setting must be a mapping or a SettingCard")
    _needed(data, _SETTING_KEYS, "a setting")
    return SettingCard(
        setting_id=data.get("setting_id"), seq=data.get("seq"),
        name=data.get("name"), section=data.get("section"),
        value=data.get("value"), layer=data.get("layer"),
        meaning=data.get("meaning"), detail=data.get("detail"),
        **_provenance(data))


def setting_gaps(setting: Any) -> Tuple[str, ...]:
    """The gaps that keep a setting from completeness."""
    checked = _check_setting_ref(setting)
    return () if checked.meaning else ("no plain meaning",)


def setting_passes(setting: Any) -> bool:
    return not setting_gaps(setting)


def plain_lines(setting: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the setting's own fields."""
    checked = _check_setting_ref(setting)
    return (
        f"Setting: {checked.name}",
        f"Section: {checked.section}",
        f"Value: {checked.value if checked.value else 'unknown'}",
        f"Layer: {checked.layer}",
        f"Meaning: {checked.meaning if checked.meaning else 'none'}",
    )


def segment_of(setting: Any) -> str:
    checked = _check_setting_ref(setting)
    gaps = setting_gaps(checked)
    return (
        f"{checked.setting_id}: {checked.name} - section: "
        f"'{checked.section}' - value: "
        f"'{checked.value if checked.value else 'unknown'}' - "
        f"layer: '{checked.layer}' - "
        f"meaning: '{checked.meaning if checked.meaning else 'none'}' - "
        f"detail: '{checked.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held stance: a note on a setting, as data.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class NoteRecord:
    """One setting note, held as data.

    The record names its setting, its stance and
    what it feeds back toward, with its title and
    its detail. One record stands per setting
    stance in a book. The record is data alone:
    holding it changes no setting and saves no
    config, ever.
    """

    note_id: str
    seq: int
    setting_id: str
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
            self, "setting_id", _clean_text(self.setting_id, "a setting id"))
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
            "setting_id": self.setting_id, "stance": self.stance,
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
        setting_id=data.get("setting_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held view: which settings a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class RoomView:
    """A view over the book: every setting, the ready, the rest."""

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


def _check_view_ref(value: Any) -> RoomView:
    if not isinstance(value, RoomView):
        raise ValueError("a view must be a RoomView")
    return value


def validate_view(view: Any) -> RoomView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> RoomView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, RoomView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or a RoomView")
    _needed(data, _VIEW_KEYS, "a view")
    return RoomView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_provenance(data))


def inspect_setting_source(piece: Any) -> Dict[str, Any]:
    """Name what one setting source piece is, without judging it."""
    if isinstance(piece, SettingCard):
        return {"kind": "setting", "setting_id": piece.setting_id}
    if isinstance(piece, dict):
        if "note_id" in piece:
            return {"kind": "note", "note_id": piece.get("note_id")}
        if "view_id" in piece:
            return {"kind": "view", "view_id": piece.get("view_id")}
        if "setting_id" in piece:
            return {"kind": "setting", "setting_id": piece.get("setting_id")}
    return {"kind": "unknown", "setting_id": None}


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class RoomPanelRow:
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


def _row_for_setting(setting: SettingCard) -> RoomPanelRow:
    return RoomPanelRow(
        item_id=setting.setting_id,
        standing="ready" if setting_passes(setting) else "unready",
        label=setting.name, segment=segment_of(setting),
        recorded_on=setting.recorded_on)


def _check_row_ref(value: Any) -> RoomPanelRow:
    if not isinstance(value, RoomPanelRow):
        raise ValueError("a panel row must be a RoomPanelRow")
    return value


def validate_row(row: Any, setting: Any = None) -> RoomPanelRow:
    checked = _check_row_ref(row)
    if setting is not None:
        derived = _row_for_setting(_check_setting_ref(setting))
        if checked != derived:
            raise ValueError(
                f"panel row {checked.item_id!r} does not agree with "
                f"the row derived from its setting")
    return checked


def build_row(row: Any = None, setting: Any = None,
              **kwargs: Any) -> RoomPanelRow:
    if setting is not None:
        derived = _row_for_setting(_check_setting_ref(setting))
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            RoomPanelRow(**kwargs))
        return validate_row(built, setting)
    if isinstance(row, RoomPanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in READY_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return RoomPanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on day"))
    if row is None and kwargs:
        return RoomPanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or a RoomPanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[RoomPanelRow, ...]
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
        f"The settings book holds {total_items} settings as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {passing_shown} of the shown settings "
        f"stand ready.",
        "Rows stand in held order, the order the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its setting's own fields "
        "- the name, the section, the value and layer "
        "honestly held and the plain meaning it honestly "
        "carries - and no judgement is stored on any setting.",
        "Completeness is judged from the held records alone: "
        "a setting naming no plain meaning stands unready, and the "
        "settings index is derived from the held settings, "
        "never stored where it could drift.",
    )


@dataclass(frozen=True)
class RoomPanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[RoomPanelRow, ...]
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


def _resolve_view(source: Any, view: Any) -> RoomView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, RoomView):
        return view
    return book.view_for(view)


def shown_settings(source: Any, view: Any = None
                   ) -> Tuple[SettingCard, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.settings
    if resolved.view_filter == "ready":
        return tuple(g for g in book.settings if setting_passes(g))
    return tuple(g for g in book.settings if not setting_passes(g))


def settings_for_section(source: Any, section: Any
                      ) -> Tuple[SettingCard, ...]:
    wanted = normalize_section(section)
    return tuple(
        g for g in _source_book(source).settings if g.section == wanted)


def passing_settings(source: Any) -> Tuple[SettingCard, ...]:
    return tuple(
        g for g in _source_book(source).settings if setting_passes(g))


def total_settings(source: Any) -> int:
    return len(_source_book(source).settings)


def derive_panel(source: Any, view: Any = None) -> RoomPanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_settings(book, resolved)
    rows = tuple(_row_for_setting(setting) for setting in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.settings), default="")
    passing = sum(1 for g in shown if setting_passes(g))
    return RoomPanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.settings), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.settings), len(shown), passing, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> RoomPanel:
    if not isinstance(value, RoomPanel):
        raise ValueError("a panel must be a RoomPanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> RoomPanel:
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
                **kwargs: Any) -> RoomPanel:
    if isinstance(panel, RoomPanel):
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
        built = RoomPanel(
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
    raise ValueError("a panel must be a mapping, a RoomPanel, or derived")


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
class RoomVerdict:
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


def derive_verdict(source: Any, view: Any = None) -> RoomVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_settings(book, resolved)
    passing = sum(1 for g in shown if setting_passes(g))
    latest = max((g.recorded_on for g in shown), default="")
    return RoomVerdict(
        verdict=_verdict_word(len(shown), passing),
        view_id=resolved.view_id, total_shown=len(shown),
        passing_shown=passing, latest_on=latest)


def _check_verdict_ref(value: Any) -> RoomVerdict:
    if not isinstance(value, RoomVerdict):
        raise ValueError("a verdict must be a RoomVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> RoomVerdict:
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
                  **kwargs: Any) -> RoomVerdict:
    if isinstance(verdict, RoomVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = RoomVerdict(
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
        "a verdict must be a mapping, a RoomVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held settings' meanings at call time, and
# the stance targets: which setting notes the book holds, derived too.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexEntry:
    meaning: str
    setting_id: str
    name: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "meaning": self.meaning, "setting_id": self.setting_id,
            "name": self.name,
        }


@dataclass(frozen=True)
class RoomIndex:
    """The settings index, derived from the held settings.

    The index names one entry per complete setting, in
    held order - the setting's own meaning, its id and
    its name - and the settings that stand incomplete,
    named in its gaps. Nothing here is stored on any
    setting: the index is derived at call time from the
    held records alone, so it can never drift from them.
    """

    entries: Tuple[IndexEntry, ...]
    gaps: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "entries": [e.to_record() for e in self.entries],
            "gaps": list(self.gaps),
        }


def derive_index(source: Any) -> RoomIndex:
    """Derive the settings index from the book's held settings."""
    book = _source_book(source)
    entries = tuple(
        IndexEntry(meaning=g.meaning, setting_id=g.setting_id, name=g.name)
        for g in book.settings if setting_passes(g))
    gaps = tuple(
        g.setting_id for g in book.settings if not setting_passes(g))
    return RoomIndex(entries=entries, gaps=gaps)


def setting_for_meaning(source: Any, meaning: Any) -> Optional[SettingCard]:
    """The first held setting one meaning reaches, or none - honestly."""
    wanted = _check_meaning(meaning)
    if not wanted:
        return None
    for setting in _source_book(source).settings:
        if setting.meaning == wanted:
            return setting
    return None


def note_for_setting(source: Any, setting_id: Any,
                       stance: Any = None) -> Optional[NoteRecord]:
    """The held stance target for one setting (and stance, when named)."""
    wanted = _clean_text(setting_id, "a setting id")
    for record in _source_book(source).notes:
        if record.setting_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_note(source: Any) -> Optional[NoteRecord]:
    """The first held stance target, standing for the setting targets, or none."""
    notes = _source_book(source).notes
    return notes[0] if notes else None


# ---------------------------------------------------------------------
# The book: settings, views and notes held together, one pinned panel
# at most per telling, and no verdict or index ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class RoomBook:
    title: str
    settings: Tuple[SettingCard, ...] = ()
    views: Tuple[RoomView, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    panels: Tuple[RoomPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        settings = tuple(_check_setting_ref(g) for g in self.settings)
        views = tuple(_check_view_ref(v) for v in self.views)
        notes = tuple(_check_note_ref(m) for m in self.notes)
        panels = tuple(_check_panel_ref(p) for p in self.panels)
        seen_ids = set()
        seen_seqs = set()
        for setting in settings:
            if setting.setting_id in seen_ids:
                raise ValueError(
                    f"two settings stand under id {setting.setting_id!r}")
            if setting.seq in seen_seqs:
                raise ValueError(
                    f"two settings stand at sequence {setting.seq}")
            seen_ids.add(setting.setting_id)
            seen_seqs.add(setting.seq)
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
            target = (record.setting_id, record.stance)
            if target in note_targets:
                raise ValueError(
                    f"two stance records stand for setting "
                    f"{record.setting_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per setting target")
            note_ids.add(record.note_id)
            note_seqs.add(record.seq)
            note_targets.add(target)
        object.__setattr__(
            self, "settings", tuple(sorted(settings, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "notes", tuple(sorted(notes, key=lambda m: m.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.settings + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.setting_id for g in self.settings) + tuple(
            v.view_id for v in self.views)

    def setting_ids(self) -> Tuple[str, ...]:
        return tuple(g.setting_id for g in self.settings)

    def setting_for(self, setting_id: Any) -> SettingCard:
        wanted = _clean_text(setting_id, "a setting id")
        for setting in self.settings:
            if setting.setting_id == wanted:
                return setting
        raise KeyError(f"no setting named {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> RoomView:
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
        for setting in self.settings:
            if setting.setting_id == wanted:
                return setting
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "settings": [g.to_record() for g in self.settings],
            "views": [v.to_record() for v in self.views],
            "notes": [m.to_record() for m in self.notes],
            "panels": [p.to_record() for p in self.panels],
        }


def _judge_book_panels(book: RoomBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: RoomBook) -> None:
    if book.title != "Settings as one room at the M-195 slice boundary":
        raise ValueError("the shipped example book carries another title")
    if len(book.settings) != 6 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold six settings and two views")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-m195-boundary":
        raise ValueError("the pinned panel is panel-m195-boundary")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "strained" or verdict.passing_shown != 5:
        raise ValueError("the shipped example book verdict must stand strained at five ready of six")
    index = derive_index(book)
    if [e.meaning for e in index.entries] != ["the model that answers you", "the key that opens your provider", "the colours the screen wears", "whether your work is saved as you go", "how large the letters stand"]:
        raise ValueError("the shipped example book index must derive the five held meanings in held order")
    if index.gaps != ("setting-telemetry-main",):
        raise ValueError("the shipped example book must leave the telemetry setting honestly incomplete, named in its gaps")
    found = setting_for_meaning(book, EXAMPLE_MEANING)
    if found is None or found.setting_id != "setting-model-main":
        raise ValueError("the shipped example book must reach its model setting under the example meaning")
    first = first_note(book)
    if first is None or first.note_id != "note-note-model":
        raise ValueError("the shipped example book must hold the model note as its first note road")


def validate_book(data: Any, *, require_example: bool = False) -> RoomBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, RoomBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a settings book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live setting change "
                f"({key!r} is named on it): {ROOM_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its settings under a view")
    if "room_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held settings at call time")
    if data.get("schema") is not None and (
            data["schema"] != SETTINGS_ROOM_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{SETTINGS_ROOM_SCHEMA!r}")
    if data.get("slice") is not None and (
            data["slice"] != SETTINGS_ROOM_SLICE):
        raise ValueError(
            f"a book's slice must be {SETTINGS_ROOM_SLICE!r}")
    head = data.get("settings_room") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's settings head must be a mapping")
    title = head.get("title") or data.get("title")
    settings = tuple(build_setting(g) for g in data.get("settings") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    book = RoomBook(
        title=title, settings=settings, views=views, notes=notes, panels=())
    panels = tuple(
        build_panel(p, book) for p in data.get("panels") or ())
    book = RoomBook(
        title=book.title, settings=book.settings, views=book.views,
        notes=book.notes, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> RoomBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (RoomBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or a RoomBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> RoomBook:
    return validate_book(data, require_example=require_example)


def load_settings_room(
        data: Optional[Dict[str, Any]] = None) -> RoomBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(SETTINGS_ROOM_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_settings_room_file(path: Any) -> RoomBook:
    """Load one settings file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: settings and views held one by one.
# ---------------------------------------------------------------------

class SettingsRoomRegistry:
    """An in-memory holding of settings and views.

    The registry is the pure layer's model of a
    session's settings book: settings are held under
    their ids, one setting per id and per sequence,
    and views are held in recorded order, one view
    per sequence and per id. Holding is data only -
    nothing held here changes a setting, applies
    anything, or writes a config.
    """

    def __init__(self, book: Any = None) -> None:
        self._settings: List[SettingCard] = []
        self._views: List[RoomView] = []
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

    def register_setting(self, item: Any) -> SettingCard:
        """Hold one setting, judged whole before held."""
        checked = _check_setting_ref(item)
        return self._register(
            self._settings, checked, "setting_id", "setting")

    def register_view(self, view: Any) -> RoomView:
        """Hold one view; a view naming no id takes a fresh one."""
        checked = _check_view_ref(view)
        if not checked.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            checked = build_view({**checked.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, checked, "view_id", "view")

    def register_book(self, book: Any) -> RoomBook:
        """Hold a whole book's settings and views, under its title."""
        checked = build_book(book)
        if self._title is not None and checked.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {checked.title!r}")
        for setting in checked.settings:
            self.register_setting(setting)
        for view in checked.views:
            self.register_view(view)
        self._title = checked.title
        return self.book()

    def book(self) -> RoomBook:
        return RoomBook(
            title=self._title or "An unheld settings book",
            settings=tuple(self._settings), views=tuple(self._views),
            notes=(), panels=())

    def list_settings(self) -> Tuple[SettingCard, ...]:
        return tuple(self._settings)

    def list_views(self) -> Tuple[RoomView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._settings) + tuple(self._views)

    def get_setting(self, setting_id: Any) -> SettingCard:
        return self.book().setting_for(setting_id)

    def get_view(self, view_id: Any) -> RoomView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records shaped for the journal target.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> RoomBook:
    if source is None:
        return load_settings_room()
    if isinstance(source, RoomBook):
        return source
    if isinstance(source, SettingsRoomRegistry):
        return source.book()
    return build_book(source)


def _provenance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _PROVENANCE}


def setting_record(setting: Any, source: Any = None) -> Dict[str, Any]:
    checked = _check_setting_ref(setting)
    record = {
        "type": "room_setting",
        "slice": SETTINGS_ROOM_SLICE,
        "setting_id": checked.setting_id,
        "name": checked.name,
        "segment": segment_of(checked),
        "passes": setting_passes(checked),
        "gaps": list(setting_gaps(checked)),
    }
    record.update(_provenance_record(checked))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    checked = _check_view_ref(view)
    record = {
        "type": "room_view",
        "slice": SETTINGS_ROOM_SLICE,
        "view_id": checked.view_id, "seq": checked.seq,
        "view_filter": checked.view_filter,
    }
    record.update(_provenance_record(checked))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    checked = _check_note_ref(record_in)
    record = {
        "type": "room_note",
        "slice": SETTINGS_ROOM_SLICE,
        "note_id": checked.note_id,
        "setting_id": checked.setting_id,
        "stance": checked.stance,
    }
    record.update(_provenance_record(checked))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    checked = validate_panel(panel, source)
    record = {"type": "room_panel",
              "slice": SETTINGS_ROOM_SLICE}
    record.update(checked.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, RoomVerdict):
        checked = validate_verdict(verdict, source)
    else:
        checked = derive_verdict(_source_book(verdict), view)
    record = {"type": "room_verdict",
              "slice": SETTINGS_ROOM_SLICE}
    record.update(checked.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, RoomIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "room_index",
              "slice": SETTINGS_ROOM_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    checked = _source_book(book)
    record = {"type": "room_book",
              "slice": SETTINGS_ROOM_SLICE,
              "title": checked.title}
    record.update(checked.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(setting: Any, source: Any = None) -> str:
    checked = _check_setting_ref(setting)
    return (
        f"{checked.name} - section {checked.section}: "
        f"value {checked.value if checked.value else 'unknown'}, "
        f"layer {checked.layer}, "
        f"meaning {checked.meaning if checked.meaning else 'none'}. "
        f"{checked.detail}")


def setting_plain_words(setting: Any, source: Any = None) -> str:
    return plain_words(setting, source)


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The settings room stands {verdict.verdict}: "
        f"{verdict.passing_shown} of {verdict.total_shown} shown "
        f"settings stand ready.")


def view_plain_words(view: Any) -> str:
    checked = _check_view_ref(view)
    return f"View {checked.view_id}: shows {checked.view_filter} settings."


def note_plain_words(record_in: Any) -> str:
    checked = _check_note_ref(record_in)
    return (
        f"Note {checked.note_id}: {checked.stance} "
        f"{checked.setting_id}, toward {checked.target}. "
        f"{checked.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, RoomIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.entries)} plain meanings for "
        f"{len(index.entries)} settings; incomplete, named in "
        f"its gaps: {gaps}.")


def format_setting(setting: Any, source: Any = None) -> str:
    checked = _check_setting_ref(setting)
    lines = [f"{checked.name} ({checked.setting_id})"]
    lines.extend(plain_lines(checked))
    lines.append(checked.detail)
    if setting_passes(checked):
        lines.append(
            "This setting stands ready - it carries the plain "
            "meaning its record names.")
    else:
        lines.append(
            "This setting stands unready - it names no plain "
            "meaning, stands named in its gaps, and no meaning is "
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
        f"Setting note {checked.stance} {checked.setting_id} "
        f"({checked.note_id}): {checked.title}. {checked.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or reading it changes no setting, applies nothing "
        "and posts no note.")
    return "\n".join(lines)


def format_meaning(source: Any, meaning: Any) -> str:
    setting = setting_for_meaning(source, meaning)
    if setting is not None:
        return format_setting(setting)
    wanted = _check_meaning(meaning)
    return (
        f"No held setting stands under meaning {wanted!r} yet - the "
        f"meaning reaches nothing in this book, and no setting is "
        f"invented for it.")


def format_book(source: Any = None, section: Any = None) -> str:
    book = _source_book(source)
    settings = (settings_for_section(book, section)
                if section is not None else book.settings)
    lines = [f"Settings as One Room (M-196) - {book.title}"]
    lines.extend(segment_of(setting) for setting in settings)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Room panel under view {panel.view_id}:"]
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
    lines = ["Settings index, derived from the held settings:"]
    for entry in index.entries:
        lines.append(f"{entry.meaning} - {entry.name} ({entry.setting_id})")
    if index.gaps:
        lines.append(
            "Incomplete, named honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "changes no setting and opens no network.")
    return "\n".join(lines)


def format_room_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "Settings as One Room (M-196)",
        f"{book.title}: {len(book.settings)} settings held, "
        f"{len(passing_settings(book))} settings standing ready, "
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


def parse_room_args(args: Any) -> Tuple[str, Any]:
    """Parse the /settingsroom grammar into (action, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("setting", "view", "note"):
        if len(parts) != 2:
            raise ValueError(USAGE)
        return (head, parts[1])
    if head in ("meaning", "section"):
        if len(parts) < 2:
            raise ValueError(USAGE)
        return (head, " ".join(parts[1:]))
    if head in ("index", "panel", "verdict") and len(parts) == 1:
        return (head, None)
    raise ValueError(USAGE)
