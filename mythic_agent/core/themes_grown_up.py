"""Themes grown up (All-Features roadmap slice M-179).

Part VIII - The Beautiful Face - builds here. The
roadmap's words: *the theme system gains the
Design Lawbook's discipline (darkness ladders,
accent budgets), plus a high-contrast and a
no-colour theme that lose nothing.*

What already ships, and what this slice adds:

* The shipped tree carries three named themes in
  ``mythic_agent/ui/themes.py`` (tokyo_night,
  viking_dark, light) as plain colour tables -
  ten semantic roles each, and nothing that
  judges them: no ladder is counted, no budget
  is checked, no one can say what a theme loses
  when colour falls away.
* No row of the M-171 TUI redesign charter names
  M-179 (checked live by the tests, as M-177 was
  checked), so this slice is built to the roadmap
  words alone, with the house Design Lawbook's
  numbers binding: at least four distinct dark
  surface values on the ladder separating
  background, panel and foreground; accents held
  to 5-12% of area and ambient ornament to 1-5%;
  colour never the only signal - every state a
  colour names is also named in text or shape -
  and the book staying coherent in grayscale.
* This slice is the judging room, as a pure
  layer: one theme validated as data WITH ITS
  PROVENANCE WHOLE - its name, its mode (full
  colour, high contrast or no colour), its
  colours role by role in the shipped role
  order, the non-colour cue each state it names
  carries, its declared accent and ornament
  shares, and its own words. Every judgement -
  the ladder count, the budget word, whether
  colour is the only signal, whether the theme
  loses anything when colour falls away, and
  whether the theme stands disciplined whole -
  is DERIVED from the theme's own colours, cues
  and shares at call time, never stored. A view
  is held as its own record (the one mode it
  looks at, or every mode at once); the panel is
  DERIVED for one held view and a verdict is
  DERIVED for the whole book under one view
  (disciplined while every shown theme stands
  disciplined, strained while some do, bare
  while none does). The shipped data file
  (``mythic_agent/data/themes_grown_up.yaml``)
  holds one example book in exactly the shape a
  real theme file takes - the three shipped
  themes judged as data beside the two new
  themes this slice authors, high-contrast and
  no-colour, each derived to lose nothing - a
  loader reads a theme file anywhere on disk,
  themes and views are shaped as session news,
  and a small in-memory registry holds themes
  and views one by one. The agent layer owns
  holding themes for a session and standing a
  view on them.

Honesty rules, enforced here and pinned by tests:

* **Judgements are derived, never stored.** A
  theme carries no ladder count, no budget word,
  no verdict and no summary: a mapping naming
  one refuses. A segment exists only as the
  derivation of the theme's own colours, cues
  and shares, and a panel row is judged against
  that derivation: a stored row whose segment
  disagrees refuses.
* **Unmeasured shares stay honestly unknown.**
  A theme whose accent or ornament share is not
  measured stands with the budget word
  ``unknown``: the shipped colour tables carry
  no area measurement, so the shipped themes
  stand honestly unknown on budget here, and no
  share is invented for them. What the colours
  themselves prove - the ladder, the cues, what
  falls away in grayscale - is derived and
  named, theme by theme.
* **Data only.** This layer holds themes and
  views as data: it repaints no live UI, applies
  no theme live, renders no live screen and
  measures no running screen - a theme held here
  is a finding, never the live face of the app,
  and anything unmeasured stands honestly
  unknown.
"""

from __future__ import annotations

__all__ = [
    "ACCENT_MAX_PERCENT",
    "ACCENT_MIN_PERCENT",
    "BUDGET_WORDS",
    "MIN_LADDER_RUNGS",
    "MIN_VALUE_GAP",
    "MODES",
    "ORNAMENT_MAX_PERCENT",
    "ORNAMENT_MIN_PERCENT",
    "PLAIN_EXPLANATION",
    "ROLES",
    "STATE_ROLES",
    "SURFACE_ROLES",
    "THEMES_GROWN_UP_RESOURCE",
    "THEMES_GROWN_UP_SCHEMA",
    "THEMES_GROWN_UP_SLICE",
    "THE_THEMES_GROWN_UP_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "Any",
    "Dict",
    "List",
    "Optional",
    "ThemeBook",
    "ThemeModeCount",
    "ThemePanel",
    "ThemePanelRow",
    "ThemeProfile",
    "ThemeRegistry",
    "ThemeVerdict",
    "ThemeView",
    "Tuple",
    "book_record",
    "budget_word",
    "build_book",
    "build_panel",
    "build_row",
    "build_theme",
    "build_verdict",
    "build_view",
    "colliding_pairs",
    "colour_not_only_signal",
    "colour_value",
    "cued_states",
    "derive_panel",
    "derive_verdict",
    "format_book",
    "format_panel",
    "format_theme",
    "format_themes_grown_up_screen",
    "format_verdict",
    "format_view",
    "inspect_theme_source",
    "ladder_count",
    "ladder_holds",
    "load_themes_grown_up",
    "load_themes_grown_up_file",
    "loses_nothing",
    "lost_labels",
    "measured_theme",
    "missing_roles",
    "normalize_mode",
    "normalize_mode_filter",
    "normalize_role",
    "panel_plain_words",
    "panel_record",
    "parse_themes_grown_up_args",
    "passing_themes",
    "plain_words",
    "segment_of",
    "shown_themes",
    "theme_passes",
    "theme_record",
    "themes_for_mode",
    "total_themes",
    "unmeasured_theme",
    "validate_book",
    "validate_panel",
    "validate_row",
    "validate_theme",
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

THEMES_GROWN_UP_SLICE = "M-179"

#: The longer name other layers cite for this slice.
THE_THEMES_GROWN_UP_SLICE = THEMES_GROWN_UP_SLICE

THEMES_GROWN_UP_RESOURCE = "themes_grown_up.yaml"

THEMES_GROWN_UP_SCHEMA = "mythic.themes_grown_up/1"

#: The semantic colour roles one theme may name,
#: in the shipped theme table's own order.
ROLES = ("background", "surface", "primary",
         "secondary", "accent", "text", "muted",
         "success", "warning", "error")

_ROLE_ALIASES = {
    "background": "background", "bg": "background",
    "surface": "surface", "panel": "surface",
    "primary": "primary", "secondary": "secondary",
    "accent": "accent", "text": "text",
    "foreground": "text", "muted": "muted",
    "dim": "muted", "success": "success",
    "ok": "success", "warning": "warning",
    "warn": "warning", "error": "error",
    "danger": "error"}

#: The surface rungs of the darkness ladder: the
#: values that separate background, panel and
#: foreground. The Lawbook holds a theme to at
#: least four distinct dark surface values here.
SURFACE_ROLES = ("background", "surface", "muted", "text")

#: The state roles: the roles whose colour names
#: a state, so each must also be named in text or
#: shape - colour is never the only signal.
STATE_ROLES = ("success", "warning", "error")

#: The modes one theme may stand in.
MODES = ("full_colour", "high_contrast", "no_colour")

_MODE_ALIASES = {
    "full_colour": "full_colour",
    "full-colour": "full_colour",
    "full_color": "full_colour",
    "colour": "full_colour", "color": "full_colour",
    "high_contrast": "high_contrast",
    "high-contrast": "high_contrast",
    "contrast": "high_contrast",
    "no_colour": "no_colour",
    "no-colour": "no_colour",
    "no_color": "no_colour",
    "monochrome": "no_colour",
    "grayscale": "no_colour", "grey": "no_colour",
    "gray": "no_colour"}

#: The Lawbook's ladder floor: at least four
#: distinct surface values.
MIN_LADDER_RUNGS = 4

#: The Lawbook's accent budget: accents stand at
#: 5-12% of area, ambient ornament at 1-5%.
ACCENT_MIN_PERCENT = 5
ACCENT_MAX_PERCENT = 12
ORNAMENT_MIN_PERCENT = 1
ORNAMENT_MAX_PERCENT = 5

#: The smallest value gap at which two roles
#: still read apart when colour falls away: two
#: roles closer than this in value share one
#: value in grayscale, unless a cue told apart
#: names them both.
MIN_VALUE_GAP = 0.005

#: The words a theme's budget standing may carry:
#: within the Lawbook budgets, outside them, or
#: unknown while a share stands unmeasured.
BUDGET_WORDS = ("within", "outside", "unknown")

#: The words a whole book's verdict under one view
#: may carry: disciplined while every shown theme
#: stands disciplined, strained while some do,
#: bare while none does.
VERDICT_WORDS = ("disciplined", "strained", "bare")

_THEME_KEYS = frozenset({
    "theme_id", "id", "name", "title",
    "mode", "kind", "type_of",
    "colours", "colors", "roles", "palette",
    "signals", "cues",
    "accent_percent", "accent",
    "ornament_percent", "ornament",
    "detail", "note", "description",
    "recorded_on", "day", "date",
    "actor", "by", "who", "source",
    "origin_session", "session"})

_DERIVED_THEME_KEYS = frozenset({
    "ladder", "ladder_count", "budget", "verdict",
    "segment", "summary", "loses_nothing", "passes",
    "grayscale", "luminance", "value"})

_ROW_KEYS = frozenset({
    "theme_id", "id", "name", "mode",
    "segment", "recorded_on"})

_MODE_COUNT_KEYS = frozenset({"mode", "themes", "count"})

_PANEL_KEYS = frozenset({
    "panel_id", "id", "view_id", "view",
    "mode_filter", "filter", "mode",
    "rows", "shown",
    "total_themes", "themes",
    "total_shown", "matched",
    "mode_counts", "modes",
    "as_of", "day", "account", "statements"})

_VIEW_KEYS = frozenset({
    "view_id", "id", "seq", "sequence", "order",
    "mode_filter", "filter", "mode",
    "detail", "reason",
    "recorded_on", "day", "date",
    "actor", "by", "who", "source",
    "origin_session", "session"})

_VERDICT_KEYS = frozenset({
    "total_themes", "themes",
    "total_shown", "matched",
    "passing_shown", "passing",
    "distinct_modes", "modes",
    "earliest_on", "earliest", "latest_on", "latest",
    "verdict"})

_BOOK_KEYS = frozenset({"title", "name"})

_THEMES_GROWN_UP_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "canon_note", "guide", "themes", "views",
    "panels"})

_EXAMPLE_TITLE = "Themes at the M-178 slice boundary"

_EXAMPLE_THEME_IDS = (
    "theme-tokyo-night", "theme-viking-dark",
    "theme-light", "theme-high-contrast",
    "theme-no-colour")

_EXAMPLE_FIRST_THEME_ID = "theme-tokyo-night"

_EXAMPLE_FIRST_THEME_NAME = "tokyo_night"

_EXAMPLE_PANEL_ID = "panel-m178-boundary"

_EXAMPLE_AS_OF = "2026-11-09"

_EXAMPLE_VIEW_IDS = ("view-all", "view-nocolour")

PLAIN_EXPLANATION = (
    "Themes Grown Up: the theme system judged "
    "under the Design Lawbook's discipline - "
    "darkness ladders of at least four distinct "
    "surface values, accents held to 5-12% of "
    "area and ambient ornament to 1-5%, and "
    "colour never the only signal, every state a "
    "colour names also named in text or shape. A "
    "theme is held whole - its name, its mode "
    "(full colour, high contrast or no colour), "
    "its colours role by role, the cue each state "
    "carries, and its declared shares, with its "
    "provenance whole. Every judgement - the "
    "ladder count, the budget word, whether "
    "colour stands alone, and whether the theme "
    "loses anything when colour falls away - is "
    "derived from the theme's own colours, cues "
    "and shares, never stored, never written by "
    "hand. The book holds the three shipped "
    "themes judged as data beside a high-contrast "
    "theme and a no-colour theme, each derived to "
    "lose nothing: every role and state of the "
    "full-colour themes stands present in them "
    "and distinguishable by value, text or shape, "
    "not by hue. A share that is not measured "
    "stands honestly unknown - no area is invented "
    "here. This layer holds themes and views as "
    "data only: it repaints no live UI, applies "
    "no theme live, renders no live screen and "
    "measures no running screen - a theme held "
    "here is a finding, never the live face of "
    "the app."
)

USAGE = (
    "Usage: /themesgrownup, /themesgrownup show, "
    "/themesgrownup theme <theme-id>, "
    "/themesgrownup view <view-id>, "
    "/themesgrownup mode <mode>, "
    "/themesgrownup panel, /themesgrownup verdict"
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


def _check_percent(value: Any, what: str) -> Optional[int]:
    if value is None:
        return None
    percent = _check_count(value, what)
    if percent > 100:
        raise ValueError(
            f"{what} is a share of area, at most 100, "
            f"got {value!r}")
    return percent


def _check_hex(value: Any, what: str = "a colour") -> str:
    text = _clean_text(value, what)
    if len(text) != 7 or not text.startswith("#"):
        raise ValueError(
            f"{what} must be a hex colour like "
            f"'#1a1b26', got {value!r}")
    try:
        int(text[1:], 16)
    except ValueError:
        raise ValueError(
            f"{what} must be a hex colour like "
            f"'#1a1b26', got {value!r}") from None
    return text.lower()


def colour_value(colour: Any) -> float:
    """The value (relative luminance) of one colour.

    Read off the colour's own channels by the
    sRGB luminance weights - the value the colour
    keeps when colour itself falls away. Derived
    at call time; stored nowhere.
    """
    text = _check_hex(colour)
    channels = []
    for index in (1, 3, 5):
        part = int(text[index:index + 2], 16) / 255.0
        channels.append(
            part / 12.92 if part <= 0.03928
            else ((part + 0.055) / 1.055) ** 2.4)
    return (0.2126 * channels[0] + 0.7152 * channels[1]
            + 0.0722 * channels[2])


def normalize_role(value: Any) -> str:
    """One role word, read onto the closed role set."""
    if not isinstance(value, str):
        raise ValueError(f"a role must be a word, got {value!r}")
    role = _ROLE_ALIASES.get(value.strip().lower())
    if role is None:
        raise ValueError(
            "a role is one of %s, got %r"
            % ("/".join(ROLES), value))
    return role


def normalize_mode(value: Any) -> str:
    """One mode word, read onto the closed mode set."""
    if not isinstance(value, str):
        raise ValueError(f"a mode must be a word, got {value!r}")
    mode = _MODE_ALIASES.get(value.strip().lower())
    if mode is None:
        raise ValueError(
            "a mode is one of %s, got %r"
            % ("/".join(MODES), value))
    return mode


def normalize_mode_filter(value: Any) -> str:
    """One mode-filter word: every mode, or one named mode."""
    if not isinstance(value, str):
        raise ValueError(
            f"a mode filter must be a word, got {value!r}")
    if value.strip().lower() == "all":
        return "all"
    return normalize_mode(value)


def _check_colours(value: Any) -> Tuple[Tuple[str, str], ...]:
    """One theme's colours, in the shipped role order.

    Read from a role-to-colour mapping, or from a
    list of pairs (or of small mappings naming a
    role and its colour). Roles stand in the
    shipped role order whatever order they arrive
    in, one colour per role.
    """
    pairs: List[Tuple[Any, Any]] = []
    if isinstance(value, dict):
        pairs = list(value.items())
    elif isinstance(value, (list, tuple)):
        for entry in value:
            if isinstance(entry, dict):
                role = _pick_any(
                    entry, ("role", "name"), "role")
                colour = _pick_any(
                    entry, ("colour", "color", "hex"), "colour")
                unknown = set(entry) - {
                    "role", "name", "colour", "color", "hex"}
                if unknown:
                    raise ValueError(
                        f"a colour entry carries unknown "
                        f"keys: {sorted(unknown)}")
                if role is None or colour is None:
                    raise ValueError(
                        "a colour entry names its role and "
                        "its colour")
                pairs.append((role, colour))
            elif isinstance(entry, (list, tuple)) and len(entry) == 2:
                pairs.append((entry[0], entry[1]))
            else:
                raise ValueError(
                    f"a colour entry must be a role and a "
                    f"colour, got {entry!r}")
    else:
        raise ValueError(
            f"a theme's colours must be a mapping or a "
            f"list of pairs, got {value!r}")
    if not pairs:
        raise ValueError("a theme names at least one colour")
    held: Dict[str, str] = {}
    for role_in, colour_in in pairs:
        role = normalize_role(role_in)
        if role in held:
            raise ValueError(
                f"a theme names the {role!r} role twice - "
                f"one colour stands per role")
        held[role] = _check_hex(colour_in, f"the {role} colour")
    return tuple(
        (role, held[role]) for role in ROLES if role in held)


def _check_signals(value: Any) -> Tuple[Tuple[str, str], ...]:
    """One theme's non-colour state cues, in state order.

    Read from a role-to-cue mapping, or from a list
    of pairs (or of small mappings naming a state
    role and its cue). Only state roles carry cues;
    one cue stands per state, and no two states
    share one cue - a shared cue tells nothing
    apart.
    """
    if value is None:
        return ()
    pairs: List[Tuple[Any, Any]] = []
    if isinstance(value, dict):
        pairs = list(value.items())
    elif isinstance(value, (list, tuple)):
        for entry in value:
            if isinstance(entry, dict):
                role = _pick_any(
                    entry, ("role", "name"), "role")
                cue = _pick_any(
                    entry, ("cue", "signal", "label"), "cue")
                unknown = set(entry) - {
                    "role", "name", "cue", "signal", "label"}
                if unknown:
                    raise ValueError(
                        f"a cue entry carries unknown "
                        f"keys: {sorted(unknown)}")
                if role is None or cue is None:
                    raise ValueError(
                        "a cue entry names its state role "
                        "and its cue")
                pairs.append((role, cue))
            elif isinstance(entry, (list, tuple)) and len(entry) == 2:
                pairs.append((entry[0], entry[1]))
            else:
                raise ValueError(
                    f"a cue entry must be a state role and "
                    f"a cue, got {entry!r}")
    else:
        raise ValueError(
            f"a theme's cues must be a mapping or a list "
            f"of pairs, got {value!r}")
    held: Dict[str, str] = {}
    for role_in, cue_in in pairs:
        role = normalize_role(role_in)
        if role not in STATE_ROLES:
            raise ValueError(
                f"only a state role carries a cue - "
                f"{role!r} names no state")
        if role in held:
            raise ValueError(
                f"a theme names the {role!r} cue twice - "
                f"one cue stands per state")
        held[role] = _check_title(cue_in, f"the {role} cue")
    cues = list(held.values())
    if len(set(cues)) != len(cues):
        raise ValueError(
            "no two states share one cue - a shared cue "
            "tells nothing apart")
    return tuple(
        (role, held[role]) for role in STATE_ROLES if role in held)


# ---------------------------------------------------------------------
# The theme: one theme, held and judged whole.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class ThemeProfile:
    """One theme: one named theme, held whole.

    ``name`` is the theme's shipped name; ``mode``
    is the mode it stands in (full colour, high
    contrast or no colour); ``colours`` are its
    colours role by role in the shipped role
    order; ``signals`` are the non-colour cues its
    states carry, one per state role it cues.
    ``accent_percent`` and ``ornament_percent``
    are its declared shares of area, or None while
    a share stands unmeasured - honestly unknown,
    never invented. ``detail`` is the theme's own
    words. The theme carries NO ladder count, NO
    budget word, NO verdict and NO summary - those
    are derived from the theme at call time, never
    fields. The provenance - the day it was
    recorded, who recorded it, its source and the
    session it was recorded in - rides whole.
    """

    theme_id: str
    name: str
    mode: str
    colours: Tuple[Tuple[str, str], ...]
    signals: Tuple[Tuple[str, str], ...]
    accent_percent: Optional[int]
    ornament_percent: Optional[int]
    detail: str
    recorded_on: str
    actor: str
    source: str
    origin_session: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "theme_id",
            _check_word(self.theme_id, "a theme id"))
        object.__setattr__(
            self, "name", _check_word(self.name, "a theme name"))
        object.__setattr__(self, "mode", normalize_mode(self.mode))
        object.__setattr__(
            self, "colours", _check_colours(self.colours))
        object.__setattr__(
            self, "signals", _check_signals(self.signals))
        object.__setattr__(
            self, "accent_percent", _check_percent(
                self.accent_percent, "an accent share"))
        object.__setattr__(
            self, "ornament_percent", _check_percent(
                self.ornament_percent, "an ornament share"))
        object.__setattr__(
            self, "detail",
            _check_long_text(self.detail, "the theme's words"))
        object.__setattr__(
            self, "recorded_on", _check_day(self.recorded_on))
        object.__setattr__(
            self, "actor", _check_title(self.actor, "an actor"))
        object.__setattr__(
            self, "source", _check_title(self.source, "a source"))
        object.__setattr__(
            self, "origin_session",
            _check_word(self.origin_session, "an origin session"))

    def colour_of(self, role: Any) -> Optional[str]:
        """The colour one role carries here, or None."""
        wanted = normalize_role(role)
        for held_role, colour in self.colours:
            if held_role == wanted:
                return colour
        return None

    def cue_of(self, role: Any) -> Optional[str]:
        """The non-colour cue one state carries, or None."""
        wanted = normalize_role(role)
        for held_role, cue in self.signals:
            if held_role == wanted:
                return cue
        return None

    @property
    def segment(self) -> str:
        """The derived segment of this theme in a panel."""
        return segment_of(self)

    @property
    def passes(self) -> bool:
        """True when this theme stands disciplined whole."""
        return theme_passes(self)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "themes_grown_up_theme",
            "slice": THEMES_GROWN_UP_SLICE,
            "theme_id": self.theme_id,
            "name": self.name,
            "mode": self.mode,
            "colours": [
                {"role": role, "colour": colour}
                for role, colour in self.colours],
            "signals": [
                {"role": role, "cue": cue}
                for role, cue in self.signals],
            "accent_percent": self.accent_percent,
            "ornament_percent": self.ornament_percent,
            "ladder_count": ladder_count(self),
            "budget": budget_word(self),
            "colour_not_only_signal": colour_not_only_signal(self),
            "missing_roles": list(missing_roles(self)),
            "colliding_pairs": [
                list(pair) for pair in colliding_pairs(self)],
            "loses_nothing": loses_nothing(self),
            "passes": self.passes,
            "segment": self.segment,
            "detail": self.detail,
            "recorded_on": self.recorded_on,
            "actor": self.actor,
            "source": self.source,
            "origin_session": self.origin_session,
        }


def _check_theme_ref(value: Any) -> "ThemeProfile":
    if isinstance(value, ThemeProfile):
        return value
    return validate_theme(value)


# ---------------------------------------------------------------------
# The derived judgements: read off the theme, never stored on it.
# ---------------------------------------------------------------------


def ladder_count(theme: Any) -> int:
    """How many distinct surface values the ladder holds.

    The distinct values among the surface rungs
    (background, surface, muted, text) the theme
    names, read off their colours' own values.
    The Lawbook holds a theme to at least four.
    """
    current = _check_theme_ref(theme)
    values = set()
    for role in SURFACE_ROLES:
        colour = current.colour_of(role)
        if colour is not None:
            values.add(round(colour_value(colour), 4))
    return len(values)


def ladder_holds(theme: Any) -> bool:
    """True when the ladder holds its four distinct values."""
    return ladder_count(theme) >= MIN_LADDER_RUNGS


def budget_word(theme: Any) -> str:
    """The theme's budget standing, derived from its shares.

    ``within`` while the accent share stands at
    5-12% and the ornament share at 1-5%;
    ``outside`` while a measured share stands
    beyond its budget; ``unknown`` while either
    share stands unmeasured - honestly unknown,
    never invented.
    """
    current = _check_theme_ref(theme)
    if (current.accent_percent is None
            or current.ornament_percent is None):
        return "unknown"
    if not (ACCENT_MIN_PERCENT <= current.accent_percent
            <= ACCENT_MAX_PERCENT):
        return "outside"
    if not (ORNAMENT_MIN_PERCENT <= current.ornament_percent
            <= ORNAMENT_MAX_PERCENT):
        return "outside"
    return "within"


def cued_states(theme: Any) -> Tuple[str, ...]:
    """The state roles carrying a non-colour cue, in order."""
    current = _check_theme_ref(theme)
    return tuple(role for role, _cue in current.signals)


def colour_not_only_signal(theme: Any) -> bool:
    """True when no state is named by colour alone.

    Every state role the theme colours also
    carries its own non-colour cue - the word or
    shape that names the state when colour falls
    away.
    """
    current = _check_theme_ref(theme)
    for role in STATE_ROLES:
        if current.colour_of(role) is not None and (
                current.cue_of(role) is None):
            return False
    return True


def missing_roles(theme: Any) -> Tuple[str, ...]:
    """The roles of the full set this theme does not name."""
    current = _check_theme_ref(theme)
    held = {role for role, _colour in current.colours}
    return tuple(role for role in ROLES if role not in held)


def colliding_pairs(theme: Any) -> Tuple[Tuple[str, str], ...]:
    """The role pairs that share one value in grayscale.

    Two named roles collide when their values
    stand closer than the smallest telling gap
    and no pair of told-apart cues names them
    both: in grayscale they are one value, and
    nothing else tells them apart.
    """
    current = _check_theme_ref(theme)
    held = [(role, colour_value(colour))
            for role, colour in current.colours]
    pairs = []
    for index, (first, first_value) in enumerate(held):
        for second, second_value in held[index + 1:]:
            if abs(first_value - second_value) >= MIN_VALUE_GAP:
                continue
            first_cue = current.cue_of(first)
            second_cue = current.cue_of(second)
            if (first_cue is not None and second_cue is not None
                    and first_cue != second_cue):
                continue
            pairs.append((first, second))
    return tuple(pairs)


def lost_labels(theme: Any) -> Tuple[str, ...]:
    """What the theme loses when colour falls away, in words."""
    current = _check_theme_ref(theme)
    labels = [f"no {role} role" for role in missing_roles(current)]
    labels += [
        f"{first} and {second} share one value"
        for first, second in colliding_pairs(current)]
    return tuple(labels)


def loses_nothing(theme: Any) -> bool:
    """True when the theme loses nothing without colour.

    Every role of the full set stands present,
    and every pair of roles still reads apart by
    value or by cue - distinguishable without
    hue, exactly as the roadmap words hold the
    high-contrast and no-colour themes to.
    """
    current = _check_theme_ref(theme)
    return not missing_roles(current) and not colliding_pairs(current)


def theme_passes(theme: Any) -> bool:
    """True when the theme stands disciplined whole.

    The ladder holds its four distinct surface
    values, the budget stands within the Lawbook
    budgets, colour is never the only signal, and
    the theme loses nothing when colour falls
    away - all derived, none stored.
    """
    current = _check_theme_ref(theme)
    return (ladder_holds(current)
            and budget_word(current) == "within"
            and colour_not_only_signal(current)
            and loses_nothing(current))


def segment_of(theme: Any) -> str:
    """The segment one theme derives in a panel.

    Read off the theme's own colours, cues and
    shares: its ladder count, its budget word and
    what it loses without colour. The segment is
    derived at call time - it is never a field of
    the theme.
    """
    current = _check_theme_ref(theme)
    lost = lost_labels(current)
    tail = "loses nothing" if not lost else (
        "loses " + "; ".join(lost))
    if colour_not_only_signal(current):
        signal = "colour never alone"
    else:
        uncued = [role for role in STATE_ROLES
                  if current.colour_of(role) is not None
                  and current.cue_of(role) is None]
        signal = "colour alone for " + ", ".join(uncued)
    return (f"{current.name}: ladder {ladder_count(current)} "
            f"rungs, budget {budget_word(current)}, "
            f"{signal}, {tail}")


def validate_theme(theme: Any) -> ThemeProfile:
    """Judge one theme whole and return it.

    A mapping is read through its spellings: a
    derived key (``ladder``, ``budget``, ``verdict``
    and their kin) refuses - those are derived,
    never stored - as does any key the theme does
    not carry, and two spellings naming two
    different values.
    """
    if isinstance(theme, ThemeProfile):
        return theme
    if not isinstance(theme, dict):
        raise ValueError(
            f"a theme must be a mapping, got {theme!r}")
    derived = set(theme) & _DERIVED_THEME_KEYS
    if derived:
        raise ValueError(
            f"a theme carries no derived keys: "
            f"{sorted(derived)} - the ladder, the "
            f"budget and what a theme loses are "
            f"derived from the theme, never stored "
            f"on one")
    unknown = set(theme) - _THEME_KEYS
    if unknown:
        raise ValueError(
            f"a theme carries unknown keys: "
            f"{sorted(unknown)}")
    if "type" in theme:
        raise ValueError(
            "a theme is judged without its news keys")

    def _needed(spellings: Tuple[str, ...], what: str) -> Any:
        value = _pick_any(theme, spellings, what)
        if value is None:
            raise ValueError(f"a theme names no {what}")
        return value

    return ThemeProfile(
        theme_id=_needed(("theme_id", "id"), "theme id"),
        name=_needed(("name", "title"), "theme name"),
        mode=_needed(("mode", "kind", "type_of"), "mode"),
        colours=_check_colours(_needed(
            ("colours", "colors", "roles", "palette"), "colours")),
        signals=_check_signals(_pick_any(
            theme, ("signals", "cues"), "cues")),
        accent_percent=_check_percent(
            _pick_any(theme, ("accent_percent", "accent"),
                      "accent share"), "an accent share"),
        ornament_percent=_check_percent(
            _pick_any(theme, ("ornament_percent", "ornament"),
                      "ornament share"), "an ornament share"),
        detail=_needed(
            ("detail", "note", "description"), "the theme's words"),
        recorded_on=_needed(
            ("recorded_on", "day", "date"), "day it was recorded"),
        actor=_needed(("actor", "by", "who"), "actor"),
        source=_needed(("source",), "source"),
        origin_session=_needed(
            ("origin_session", "session"), "origin session"),
    )


def build_theme(theme: Any = None, **kwargs: Any) -> ThemeProfile:
    """Build one theme from a mapping, a theme, or fields."""
    if kwargs:
        if theme is not None:
            raise ValueError("a theme is built one way at a time")
        theme = kwargs
    return validate_theme(theme)


# ---------------------------------------------------------------------
# Composition: themes raised from their own palettes, honestly.
# ---------------------------------------------------------------------


def measured_theme(
        name: Any, mode: Any, colours: Any, *,
        theme_id: Any, accent_percent: Any,
        ornament_percent: Any, detail: Any,
        signals: Any = None,
        recorded_on: Any = "2026-11-09",
        actor: Any = "the coordinator",
        source: Any = "themes grown up",
        origin_session: Any = "session-m179") -> ThemeProfile:
    """Raise one theme over measured shares.

    The shares are the caller's own declared
    standing, held whole - this layer measures no
    screen itself, so a caller with no measurement
    names none here: an unmeasured share refuses
    on this road, because a theme with no measured
    share is raised by :func:`unmeasured_theme`,
    never dressed as measured.
    """
    if accent_percent is None or ornament_percent is None:
        raise ValueError(
            "a theme with an unmeasured share is not "
            "raised as measured - raise it by the "
            "unmeasured-theme road, honestly")
    return ThemeProfile(
        theme_id=theme_id, name=name, mode=mode,
        colours=_check_colours(colours),
        signals=_check_signals(signals),
        accent_percent=accent_percent,
        ornament_percent=ornament_percent,
        detail=detail, recorded_on=recorded_on,
        actor=actor, source=source,
        origin_session=origin_session)


def unmeasured_theme(
        name: Any, mode: Any, colours: Any, *,
        theme_id: Any,
        detail: Any = None,
        signals: Any = None,
        recorded_on: Any = "2026-11-09",
        actor: Any = "the coordinator",
        source: Any = "themes grown up",
        origin_session: Any = "session-m179") -> ThemeProfile:
    """Raise one theme over no measured share.

    The theme stands with both shares unmeasured:
    its budget word derives ``unknown`` - this
    layer invents no area it cannot measure, and
    an unmeasured budget is named unknown in plain
    words, never filled in.
    """
    return ThemeProfile(
        theme_id=theme_id, name=name, mode=mode,
        colours=_check_colours(colours),
        signals=_check_signals(signals),
        accent_percent=None, ornament_percent=None,
        detail=detail if detail is not None else (
            "No area share stands measured for this "
            "theme - its budget stands honestly "
            "unknown, not invented."),
        recorded_on=recorded_on, actor=actor,
        source=source, origin_session=origin_session)


def inspect_theme_source(piece: Any) -> Dict[str, Any]:
    """Judge one raw theme piece and name what it is.

    A piece shaped like a theme - a mapping
    carrying a ``name`` and ``colours`` - is read
    onto its closed mode without holding a theme.
    Anything else is named not-a-theme.
    """
    if not isinstance(piece, dict):
        return {"mode": None,
                "reason": "not a mapping - no theme stands here"}
    name = _pick_any(piece, ("name", "title"), "theme name")
    colours = _pick_any(
        piece, ("colours", "colors", "roles", "palette"), "colours")
    mode_in = _pick_any(piece, ("mode", "kind", "type_of"), "mode")
    if name is None or colours is None or mode_in is None:
        return {"mode": None,
                "reason": "no name, no colours or no mode "
                          "named - no theme stands here"}
    try:
        mode = normalize_mode(mode_in)
    except ValueError as exc:
        return {"mode": None, "name": name, "reason": str(exc)}
    return {
        "mode": mode, "name": name,
        "reason": "a theme piece in the closed mode set"}


# ---------------------------------------------------------------------
# The view record: the one mode a panel looks at, held whole.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class ThemeView:
    """One view, held as its own record.

    ``mode_filter`` is the one mode the view looks
    at, or ``all`` for every mode at once - it
    narrows which themes stand in the view's
    panel, never how they are judged; ``detail``
    is the view's own words. ``seq`` is the view's
    place in the book's recorded order, from 1.
    The provenance rides whole. A view carries no
    results of its own: its panel and the book's
    verdict under it are derived.
    """

    seq: int
    mode_filter: str
    detail: str
    recorded_on: str
    actor: str
    source: str
    origin_session: str
    view_id: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "mode_filter",
            normalize_mode_filter(self.mode_filter))
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

    def shows(self, theme: Any) -> bool:
        """True when this view shows the theme."""
        current = _check_theme_ref(theme)
        return (self.mode_filter == "all"
                or current.mode == self.mode_filter)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "themes_grown_up_view",
            "slice": THEMES_GROWN_UP_SLICE,
            "view_id": self.view_id,
            "seq": self.seq,
            "mode_filter": self.mode_filter,
            "detail": self.detail,
            "recorded_on": self.recorded_on,
            "actor": self.actor,
            "source": self.source,
            "origin_session": self.origin_session,
        }


def _check_view_ref(value: Any) -> ThemeView:
    if isinstance(value, ThemeView):
        return value
    return validate_view(value)


def validate_view(view: Any) -> ThemeView:
    """Judge one view record whole and return it."""
    if isinstance(view, ThemeView):
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

    return ThemeView(
        view_id=_pick_any(view, ("view_id", "id"), "view id"),
        seq=_needed(("seq", "sequence", "order"), "sequence"),
        mode_filter=_needed(
            ("mode_filter", "filter", "mode"), "mode filter"),
        detail=_needed(("detail", "reason"), "the view's words"),
        recorded_on=_needed(
            ("recorded_on", "day", "date"), "day it was recorded"),
        actor=_needed(("actor", "by", "who"), "actor"),
        source=_needed(("source",), "source"),
        origin_session=_needed(
            ("origin_session", "session"), "origin session"),
    )


def build_view(view: Any = None, **kwargs: Any) -> ThemeView:
    """Build one view record from a mapping, a record, or fields."""
    if kwargs:
        if view is not None:
            raise ValueError("a view record is built one way at a time")
        view = kwargs
    return validate_view(view)


def shown_themes(themes: Any, view: Any) -> Tuple[ThemeProfile, ...]:
    """The themes one view shows, in held order."""
    held_view = _check_view_ref(view)
    return tuple(
        current for current in (
            _check_theme_ref(theme) for theme in themes)
        if held_view.shows(current))


# ---------------------------------------------------------------------
# The panel row: one shown theme as the panel carries it.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class ThemePanelRow:
    """One shown theme as the panel carries it.

    The row carries the theme's id, its name, its
    mode, its DERIVED segment and its recorded
    day. The theme's detail never stands in a row -
    the panel is the book at a glance.
    """

    theme_id: str
    name: str
    mode: str
    segment: str
    recorded_on: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "theme_id",
            _check_word(self.theme_id, "a theme id"))
        object.__setattr__(
            self, "name", _check_word(self.name, "a theme name"))
        object.__setattr__(self, "mode", normalize_mode(self.mode))
        object.__setattr__(
            self, "segment",
            _check_long_text(self.segment, "a theme segment"))
        object.__setattr__(
            self, "recorded_on", _check_day(self.recorded_on))

    @property
    def passes(self) -> bool:
        """True when this row's segment ends in discipline.

        Read off the segment alone: a passing theme's
        segment names a within budget and nothing
        lost, on a ladder that holds - the row is
        the theme at a glance, and its standing is
        the segment's own.
        """
        ladder = self.segment.split("ladder ", 1)
        rungs = 0
        if len(ladder) == 2:
            try:
                rungs = int(ladder[1].split(" ", 1)[0])
            except ValueError:
                rungs = 0
        return (rungs >= MIN_LADDER_RUNGS
                and "budget within" in self.segment
                and "colour never alone" in self.segment
                and self.segment.endswith("loses nothing"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "theme_id": self.theme_id,
            "name": self.name,
            "mode": self.mode,
            "segment": self.segment,
            "recorded_on": self.recorded_on,
        }


def _row_for_theme(theme: ThemeProfile) -> ThemePanelRow:
    return ThemePanelRow(
        theme_id=theme.theme_id, name=theme.name,
        mode=theme.mode, segment=segment_of(theme),
        recorded_on=theme.recorded_on)


def _check_row_ref(value: Any) -> ThemePanelRow:
    if isinstance(value, ThemePanelRow):
        return value
    return validate_row(value)


def validate_row(row: Any, theme: Any = None) -> ThemePanelRow:
    """Judge one panel row, against its theme when named."""
    if isinstance(row, ThemePanelRow):
        current = row
    elif isinstance(row, dict):
        unknown = set(row) - _ROW_KEYS
        if unknown:
            raise ValueError(
                f"a themes panel row carries unknown keys: "
                f"{sorted(unknown)}")

        def _needed(spellings: Tuple[str, ...], what: str) -> Any:
            value = _pick_any(row, spellings, what)
            if value is None:
                raise ValueError(f"a themes panel row names no {what}")
            return value

        current = ThemePanelRow(
            theme_id=_needed(("theme_id", "id"), "theme id"),
            name=_needed(("name",), "theme name"),
            mode=_needed(("mode",), "mode"),
            segment=_needed(("segment",), "segment"),
            recorded_on=_needed(("recorded_on",), "day it was recorded"))
    else:
        raise ValueError(
            f"a themes panel row must be a mapping, got {row!r}")
    if theme is not None:
        held = _check_theme_ref(theme)
        wanted = _row_for_theme(held)
        if current != wanted:
            raise ValueError(
                "a themes panel row must be its theme's own "
                "row - the segment is derived from the theme, "
                "never written beside it")
    return current


def build_row(row: Any = None, theme: Any = None,
              **kwargs: Any) -> ThemePanelRow:
    """Build one panel row from a mapping, a row, or its theme."""
    if theme is not None:
        if row is not None or kwargs:
            return validate_row(
                row if row is not None else kwargs, theme)
        return _row_for_theme(_check_theme_ref(theme))
    if kwargs:
        if row is not None:
            raise ValueError("a row is built one way at a time")
        row = kwargs
    return validate_row(row)


@dataclass(frozen=True)
class ThemeModeCount:
    """How many shown themes of one mode a panel holds."""

    mode: str
    themes: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "mode", normalize_mode(self.mode))
        object.__setattr__(
            self, "themes", _check_count(self.themes, "a mode's themes"))

    def to_record(self) -> Dict[str, Any]:
        return {"mode": self.mode, "themes": self.themes}


def _check_mode_count_ref(value: Any) -> ThemeModeCount:
    if isinstance(value, ThemeModeCount):
        return value
    if isinstance(value, dict):
        unknown = set(value) - _MODE_COUNT_KEYS
        if unknown:
            raise ValueError(
                f"a mode count carries unknown keys: "
                f"{sorted(unknown)}")
        mode = _pick_any(value, ("mode",), "mode")
        themes = _pick_any(value, ("themes", "count"), "themes")
        if mode is None or themes is None:
            raise ValueError("a mode count names its mode and its themes")
        return ThemeModeCount(mode=mode, themes=themes)
    raise ValueError(f"a mode count must be a mapping, got {value!r}")


def _mode_counts(
        rows: Tuple[ThemePanelRow, ...]) -> Tuple[ThemeModeCount, ...]:
    counts: Dict[str, int] = {}
    for row in rows:
        counts[row.mode] = counts.get(row.mode, 0) + 1
    return tuple(
        ThemeModeCount(mode=mode, themes=counts[mode])
        for mode in MODES if mode in counts)


def _panel_account(total_themes: int, total_shown: int,
                   mode_counts: Tuple[ThemeModeCount, ...],
                   mode_filter: str,
                   as_of: str,
                   passing_shown: int) -> Tuple[str, ...]:
    modes = ", ".join(
        f"{count.mode} {count.themes}" for count in mode_counts) or "none"
    return (
        f"The theme book holds {total_themes} themes as of "
        f"{as_of}: the view {mode_filter!r} shows "
        f"{total_shown} of them: {modes}; {passing_shown} "
        f"of the shown themes stand disciplined whole.",
        "Rows stand in held order, the order the book "
        "itself stands in, so two panels of one view "
        "diff cleanly, segment by segment.",
        "Every segment is derived from its theme's own "
        "colours, cues and shares - the ladder counted "
        "from the surface values, the budget read off "
        "the declared shares, what falls away read off "
        "the values and cues - and no judgement is "
        "stored on any theme.",
        "The book is judged as data only: it repaints "
        "no live UI, applies no theme live and measures "
        "no running screen - an unmeasured share stands "
        "honestly unknown.",
    )


@dataclass(frozen=True)
class ThemePanel:
    """The derived panel of one book under one view.

    Rows stand in held order - the order the book
    itself stands in; the totals are the rows' own
    counts and the mode counts stand in the closed
    mode order. A stored panel is judged whole in
    ``__post_init__``: its totals, its mode counts
    and its account must all be the rows' own
    derived shape - a panel may not soften its
    view.
    """

    panel_id: Optional[str]
    view_id: Optional[str]
    mode_filter: str
    rows: Tuple[ThemePanelRow, ...]
    total_themes: int
    total_shown: int
    mode_counts: Tuple[ThemeModeCount, ...]
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
            self, "mode_filter",
            normalize_mode_filter(self.mode_filter))
        rows = tuple(_check_row_ref(r) for r in self.rows)
        object.__setattr__(self, "rows", rows)
        ids = [r.theme_id for r in rows]
        if len(set(ids)) != len(ids):
            raise ValueError("panel rows stand one row per theme")
        for row in rows:
            if self.mode_filter != "all" and (
                    row.mode != self.mode_filter):
                raise ValueError(
                    "a panel row stands outside its view's "
                    "mode - the view narrows the panel, "
                    "never widens it")
        for field in ("total_themes", "total_shown"):
            object.__setattr__(
                self, field,
                _check_count(getattr(self, field), f"a panel's {field}"))
        counts = tuple(
            _check_mode_count_ref(c) for c in self.mode_counts)
        object.__setattr__(self, "mode_counts", counts)
        object.__setattr__(self, "as_of", _check_day(self.as_of, "an as-of day"))
        object.__setattr__(self, "account", _check_account(self.account))
        if self.total_shown != len(rows):
            raise ValueError("a panel's shown total is its rows' own count")
        if self.total_themes < self.total_shown:
            raise ValueError(
                "a panel's theme total cannot stand below "
                "its shown total")
        if counts != _mode_counts(rows):
            raise ValueError("a panel's mode counts are its rows' own counts")
        if rows and self.as_of < max(r.recorded_on for r in rows):
            raise ValueError(
                "a panel's as-of day precedes one of its rows")
        passing = sum(1 for r in rows if r.passes)
        if self.account != _panel_account(
                self.total_themes, self.total_shown, counts,
                self.mode_filter, self.as_of, passing):
            raise ValueError(
                "a panel's account is its rows' own account, "
                "derived, never written loose")

    def row_for(self, theme_id: Any) -> ThemePanelRow:
        """The row one theme id names (KeyError if absent)."""
        wanted = _check_word(theme_id, "a theme id")
        for row in self.rows:
            if row.theme_id == wanted:
                return row
        raise KeyError(f"no row named {wanted!r} stands on the panel")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "themes_grown_up_panel",
            "slice": THEMES_GROWN_UP_SLICE,
            "panel_id": self.panel_id,
            "view_id": self.view_id,
            "mode_filter": self.mode_filter,
            "rows": [r.to_record() for r in self.rows],
            "total_themes": self.total_themes,
            "total_shown": self.total_shown,
            "mode_counts": [c.to_record() for c in self.mode_counts],
            "as_of": self.as_of,
            "account": list(self.account),
        }


def _held_themes(source: Any) -> Tuple[ThemeProfile, ...]:
    if isinstance(source, ThemeBook):
        return source.themes
    if isinstance(source, ThemeRegistry):
        return source.list_themes()
    if isinstance(source, ThemeProfile):
        return (source,)
    raise ValueError(f"a themes source is needed, got {source!r}")


def _held_views(source: Any) -> Tuple[ThemeView, ...]:
    if isinstance(source, ThemeBook):
        return source.views
    if isinstance(source, ThemeRegistry):
        return source.list_views()
    return ()


def _resolve_view(source: Any, view: Any) -> ThemeView:
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


def _default_view(source: Any) -> ThemeView:
    """The view a book's own panel stands under, or its first."""
    if isinstance(source, (ThemeBook, ThemeRegistry)):
        book = source if isinstance(source, ThemeBook) else source.book()
        for panel in book.panels:
            if panel.view_id is not None:
                for held in book.views:
                    if held.view_id == panel.view_id:
                        return held
        if book.views:
            return book.views[0]
    raise ValueError("no view stands in the source to derive under")


def derive_panel(source: Any, view: Any = None) -> ThemePanel:
    """Derive the panel of a book under one view."""
    held_view = _resolve_view(source, view)
    themes = _held_themes(source)
    shown = shown_themes(themes, held_view)
    rows = tuple(_row_for_theme(theme) for theme in shown)
    counts = _mode_counts(rows)
    as_of = max((t.recorded_on for t in themes), default=_EXAMPLE_AS_OF)
    passing = sum(1 for r in rows if r.passes)
    return ThemePanel(
        panel_id=None, view_id=held_view.view_id,
        mode_filter=held_view.mode_filter,
        rows=rows, total_themes=len(themes),
        total_shown=len(rows), mode_counts=counts, as_of=as_of,
        account=_panel_account(
            len(themes), len(rows), counts,
            held_view.mode_filter, as_of, passing))


def validate_panel(panel: Any, source: Any = None) -> ThemePanel:
    """Judge one panel whole, against its source when named."""
    if isinstance(panel, ThemePanel):
        current = panel
    elif isinstance(panel, dict):
        data = dict(panel)
        data.pop("type", None)
        data.pop("slice", None)
        unknown = set(data) - _PANEL_KEYS
        if unknown:
            raise ValueError(
                f"a themes panel carries unknown keys: "
                f"{sorted(unknown)}")

        def _needed(spellings: Tuple[str, ...], what: str) -> Any:
            value = _pick_any(data, spellings, what)
            if value is None:
                raise ValueError(f"a themes panel names no {what}")
            return value

        rows_in = _needed(("rows", "shown"), "rows")
        counts_in = _needed(("mode_counts", "modes"), "mode counts")
        current = ThemePanel(
            panel_id=_pick_any(data, ("panel_id", "id"), "panel id"),
            view_id=_pick_any(data, ("view_id", "view"), "view id"),
            mode_filter=_needed(
                ("mode_filter", "filter", "mode"), "mode filter"),
            rows=tuple(validate_row(r) for r in rows_in),
            total_themes=_needed(
                ("total_themes", "themes"), "theme total"),
            total_shown=_needed(("total_shown", "matched"), "shown total"),
            mode_counts=tuple(
                _check_mode_count_ref(c) for c in counts_in),
            as_of=_needed(("as_of", "day"), "as-of day"),
            account=tuple(_needed(("account", "statements"), "account")))
    else:
        raise ValueError(f"a themes panel must be a mapping, got {panel!r}")
    if source is not None:
        held_view = _resolve_view(source, current.view_id)
        derived = derive_panel(source, held_view)
        if (current.view_id != derived.view_id
                or current.mode_filter != derived.mode_filter
                or current.rows != derived.rows
                or current.total_themes != derived.total_themes
                or current.total_shown != derived.total_shown
                or current.mode_counts != derived.mode_counts
                or current.as_of != derived.as_of
                or current.account != derived.account):
            raise ValueError(
                "a stored panel must equal the panel its book "
                "derives under its view - the panel is "
                "derived, never stored loose")
    return current


def build_panel(panel: Any = None, source: Any = None,
                view: Any = None, **kwargs: Any) -> ThemePanel:
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


def _verdict_word(total_shown: int, passing_shown: int) -> str:
    if passing_shown == 0:
        return "bare"
    if passing_shown == total_shown:
        return "disciplined"
    return "strained"


@dataclass(frozen=True)
class ThemeVerdict:
    """The derived verdict of one whole book under one view.

    The word is read off the shown themes alone:
    bare while no shown theme stands disciplined,
    disciplined while every shown theme does,
    strained otherwise. A stored verdict is judged
    against those tallies in ``__post_init__``.
    """

    total_themes: int
    total_shown: int
    passing_shown: int
    distinct_modes: int
    earliest_on: str
    latest_on: str
    verdict: str

    def __post_init__(self) -> None:
        for field in ("total_themes", "total_shown",
                      "passing_shown", "distinct_modes"):
            object.__setattr__(
                self, field,
                _check_count(getattr(self, field), f"a verdict's {field}"))
        object.__setattr__(
            self, "earliest_on", _check_day(self.earliest_on, "an earliest day"))
        object.__setattr__(
            self, "latest_on", _check_day(self.latest_on, "a latest day"))
        if self.latest_on < self.earliest_on:
            raise ValueError("a verdict's latest day precedes its earliest")
        if self.total_shown > self.total_themes:
            raise ValueError(
                "a verdict's shown tally cannot exceed its "
                "theme total")
        if self.passing_shown > self.total_shown:
            raise ValueError(
                "a verdict's passing tally cannot exceed "
                "its shown tally")
        if self.total_shown == 0 and (
                self.distinct_modes != 0 or self.passing_shown != 0):
            raise ValueError(
                "an empty showing names no mode and no "
                "passing theme among its shown")
        if self.distinct_modes > self.total_shown:
            raise ValueError(
                "a verdict's modes cannot exceed its shown themes")
        word = _clean_text(self.verdict, "a verdict")
        if word not in VERDICT_WORDS:
            raise ValueError(
                f"a verdict is one of {VERDICT_WORDS}, got {word!r}")
        object.__setattr__(self, "verdict", word)
        if word != _verdict_word(self.total_shown, self.passing_shown):
            raise ValueError(
                "a verdict's word is derived from its tallies, "
                "never chosen")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "themes_grown_up_verdict",
            "slice": THEMES_GROWN_UP_SLICE,
            "total_themes": self.total_themes,
            "total_shown": self.total_shown,
            "passing_shown": self.passing_shown,
            "distinct_modes": self.distinct_modes,
            "earliest_on": self.earliest_on,
            "latest_on": self.latest_on,
            "verdict": self.verdict,
        }


def derive_verdict(source: Any, view: Any = None) -> ThemeVerdict:
    """Derive the verdict of a book under one view."""
    held_view = _resolve_view(source, view)
    themes = _held_themes(source)
    shown = shown_themes(themes, held_view)
    passing = sum(1 for theme in shown if theme_passes(theme))
    distinct = len({theme.mode for theme in shown})
    days = [theme.recorded_on for theme in themes]
    return ThemeVerdict(
        total_themes=len(themes), total_shown=len(shown),
        passing_shown=passing, distinct_modes=distinct,
        earliest_on=min(days) if days else _EXAMPLE_AS_OF,
        latest_on=max(days) if days else _EXAMPLE_AS_OF,
        verdict=_verdict_word(len(shown), passing))


def _check_verdict_ref(value: Any) -> ThemeVerdict:
    if isinstance(value, ThemeVerdict):
        return value
    return validate_verdict(value)


def validate_verdict(verdict: Any, source: Any = None,
                     view: Any = None) -> ThemeVerdict:
    """Judge one verdict whole, against its source when named."""
    if isinstance(verdict, ThemeVerdict):
        current = verdict
    elif isinstance(verdict, dict):
        data = dict(verdict)
        data.pop("type", None)
        data.pop("slice", None)
        unknown = set(data) - _VERDICT_KEYS
        if unknown:
            raise ValueError(
                f"a themes verdict carries unknown keys: "
                f"{sorted(unknown)}")

        def _needed(spellings: Tuple[str, ...], what: str) -> Any:
            value = _pick_any(data, spellings, what)
            if value is None:
                raise ValueError(f"a themes verdict names no {what}")
            return value

        current = ThemeVerdict(
            total_themes=_needed(
                ("total_themes", "themes"), "theme total"),
            total_shown=_needed(("total_shown", "matched"), "shown total"),
            passing_shown=_needed(
                ("passing_shown", "passing"), "passing total"),
            distinct_modes=_needed(
                ("distinct_modes", "modes"), "distinct modes"),
            earliest_on=_needed(("earliest_on", "earliest"), "earliest day"),
            latest_on=_needed(("latest_on", "latest"), "latest day"),
            verdict=_needed(("verdict",), "verdict"))
    else:
        raise ValueError(f"a themes verdict must be a mapping, got {verdict!r}")
    if source is not None:
        derived = derive_verdict(source, view)
        if current != derived:
            raise ValueError(
                "a stored verdict must equal the verdict its "
                "book derives under its view - the verdict "
                "is derived, never stored loose")
    return current


def build_verdict(verdict: Any = None, source: Any = None,
                  view: Any = None, **kwargs: Any) -> ThemeVerdict:
    """Build one verdict from a mapping, a verdict, or its source."""
    if kwargs:
        if verdict is not None:
            raise ValueError("a verdict is built one way at a time")
        verdict = kwargs
    if verdict is None and source is not None:
        return derive_verdict(source, view)
    return validate_verdict(verdict, source, view)


# ---------------------------------------------------------------------
# The book: one set of themes and views, held whole.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class ThemeBook:
    """One set of themes and views, held whole.

    Themes stand in held order - one theme per
    theme id and one per name - views stand in
    recorded order, one view per sequence and per
    id, and every stored panel is judged against
    the book and the view it stands under. The
    book carries no verdict: verdicts are derived
    from its themes at call time.
    """

    title: str
    themes: Tuple[ThemeProfile, ...] = ()
    views: Tuple[ThemeView, ...] = ()
    panels: Tuple[ThemePanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_title(self.title, "a book title"))
        themes = tuple(_check_theme_ref(t) for t in self.themes)
        object.__setattr__(self, "themes", themes)
        ids = [t.theme_id for t in themes]
        if len(set(ids)) != len(ids):
            raise ValueError("a book holds one theme per theme id")
        names = [t.name for t in themes]
        if len(set(names)) != len(names):
            raise ValueError("a book holds one theme per theme name")
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

    def theme_for(self, theme_id: Any) -> ThemeProfile:
        """The theme one id names (KeyError if absent)."""
        wanted = _check_word(theme_id, "a theme id")
        for theme in self.themes:
            if theme.theme_id == wanted:
                return theme
        raise KeyError(f"no theme named {wanted!r} stands in the book")

    def view_for(self, view_id: Any) -> ThemeView:
        """The view one id names (KeyError if absent)."""
        wanted = _check_word(view_id, "a view id")
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no view named {wanted!r} stands in the book")

    def panel_for(self, panel_id: Any) -> ThemePanel:
        """The panel one id names (KeyError if absent)."""
        wanted = _check_word(panel_id, "a panel id")
        for panel in self.panels:
            if panel.panel_id == wanted:
                return panel
        raise KeyError(f"no panel named {wanted!r} stands in the book")

    def theme_ids(self) -> Tuple[str, ...]:
        """The book's theme ids, in held order."""
        return tuple(t.theme_id for t in self.themes)

    def view_ids(self) -> Tuple[Optional[str], ...]:
        """The book's view ids, in recorded order."""
        return tuple(v.view_id for v in self.views)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "themes_grown_up_book",
            "slice": THEMES_GROWN_UP_SLICE,
            "title": self.title,
            "themes": [t.to_record() for t in self.themes],
            "views": [v.to_record() for v in self.views],
            "panels": [p.to_record() for p in self.panels],
            "theme_count": len(self.themes),
            "view_count": len(self.views),
        }


def _judge_book_panels(book: ThemeBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def validate_book(data: Any, *, require_example: bool = False) -> ThemeBook:
    """Judge one theme file's data whole and return its book."""
    if isinstance(data, ThemeBook):
        book = data
        _judge_book_panels(book)
        if require_example:
            _check_example(book)
        return book
    if not isinstance(data, dict):
        raise ValueError(f"a theme book must be a mapping, got {data!r}")
    if "verdict" in data or "segment" in data:
        raise ValueError(
            "a theme book carries no stored verdict or "
            "segment - judgements are derived from its "
            "themes, never stored")
    unknown = set(data) - _THEMES_GROWN_UP_KEYS
    if unknown:
        raise ValueError(
            f"a theme book carries unknown keys: {sorted(unknown)}")
    if data.get("schema") != THEMES_GROWN_UP_SCHEMA:
        raise ValueError(
            f"a theme book's schema must be "
            f"{THEMES_GROWN_UP_SCHEMA!r}, got {data.get('schema')!r}")
    if data.get("slice") != THEMES_GROWN_UP_SLICE:
        raise ValueError(
            f"a theme book's slice must be "
            f"{THEMES_GROWN_UP_SLICE!r}, got {data.get('slice')!r}")
    guide = data.get("guide") or {}
    title = _pick_any(guide, ("title", "name"), "title")
    if title is None:
        title = _pick_any(data, ("title", "name"), "title")
    themes_in = _pick_any(data, ("themes",), "themes")
    if themes_in is None:
        raise ValueError("a theme book names no themes")
    views_in = data.get("views") or []
    panels_in = data.get("panels") or []
    themes = []
    for raw in themes_in:
        stored = dict(raw)
        stored.pop("type", None)
        stored.pop("slice", None)
        for derived_key in (
                "ladder_count", "budget",
                "colour_not_only_signal", "missing_roles",
                "colliding_pairs", "loses_nothing",
                "passes", "segment"):
            stored.pop(derived_key, None)
        themes.append(validate_theme(stored))
    views = []
    for raw in views_in:
        stored = dict(raw)
        stored.pop("type", None)
        stored.pop("slice", None)
        views.append(validate_view(stored))
    book = ThemeBook(
        title=title,
        themes=tuple(themes),
        views=tuple(views),
        panels=tuple(validate_panel(p) for p in panels_in))
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def _check_example(book: ThemeBook) -> None:
    if book.title != _EXAMPLE_TITLE:
        raise ValueError(
            f"the shipped example book is {_EXAMPLE_TITLE!r}, "
            f"got {book.title!r}")
    if book.theme_ids() != _EXAMPLE_THEME_IDS:
        raise ValueError("the shipped example book's themes differ")
    first = book.themes[0]
    if first.theme_id != _EXAMPLE_FIRST_THEME_ID or (
            first.name != _EXAMPLE_FIRST_THEME_NAME):
        raise ValueError("the shipped example book's first theme differs")
    if book.view_ids() != _EXAMPLE_VIEW_IDS:
        raise ValueError("the shipped example book's views differ")
    if len(book.panels) != 1 or (
            book.panels[0].panel_id != _EXAMPLE_PANEL_ID):
        raise ValueError("the shipped example book's panel differs")
    if book.panels[0].as_of != _EXAMPLE_AS_OF:
        raise ValueError("the shipped example book's as-of day differs")
    derived = derive_panel(book, book.panels[0].view_id)
    if tuple(r.theme_id for r in book.panels[0].rows) != tuple(
            r.theme_id for r in derived.rows):
        raise ValueError("the shipped example book's panel rows differ")


def build_book(book: Any = None, **kwargs: Any) -> ThemeBook:
    """Build one book from a mapping, a book, or fields."""
    if isinstance(book, ThemeBook) and not kwargs:
        return validate_book(book)
    if kwargs:
        if book is not None:
            raise ValueError("a book is built one way at a time")
        fields = dict(kwargs)
    elif isinstance(book, dict) and (
            "themes" in book) and (
            "schema" not in book and "guide" not in book
            and "canon_note" not in book):
        fields = dict(book)
    else:
        return _book_from(book, require_example=False)
    unknown = set(fields) - _BOOK_KEYS - {
        "themes", "views", "panels"}
    if unknown:
        raise ValueError(
            f"a theme book carries unknown keys: "
            f"{sorted(unknown)}")
    title = _pick_any(fields, ("title", "name"), "title")
    if title is None:
        raise ValueError("a theme book names no title")
    themes_in = _pick_any(fields, ("themes",), "themes") or ()
    return ThemeBook(
        title=title,
        themes=tuple(_check_theme_ref(t) for t in themes_in),
        views=tuple(
            _check_view_ref(v) for v in fields.get("views") or ()),
        panels=tuple(
            validate_panel(p) for p in fields.get("panels") or ()))


def _book_from(data: Any, *, require_example: bool) -> ThemeBook:
    if isinstance(data, ThemeBook):
        return validate_book(data, require_example=require_example)
    if isinstance(data, dict):
        return validate_book(data, require_example=require_example)
    raise ValueError(f"a theme book must be a mapping, got {data!r}")


def load_themes_grown_up(
        data: Optional[Dict[str, Any]] = None) -> ThemeBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(THEMES_GROWN_UP_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_themes_grown_up_file(path: Any) -> ThemeBook:
    """Load one theme file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: themes and views held one by one.
# ---------------------------------------------------------------------


class ThemeRegistry:
    """An in-memory holding of themes and views.

    The registry is the pure layer's model of a
    session's theme book: themes are held under
    their theme ids, one theme per id and per
    name, in held order, and views are held in
    recorded order, one view per sequence and per
    id. Holding is data only - no theme held here
    is applied live, and no screen is repainted.
    """

    def __init__(self, book: Any = None) -> None:
        self._themes: List[ThemeProfile] = []
        self._views: List[ThemeView] = []
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

    def _check_theme_free(self, theme: ThemeProfile) -> None:
        for held in self._themes:
            if held.theme_id == theme.theme_id:
                raise ValueError(
                    f"a theme already stands under id "
                    f"{theme.theme_id!r}")
            if held.name == theme.name:
                raise ValueError(
                    f"a theme already stands under name "
                    f"{theme.name!r} - the book holds one "
                    f"theme per name")

    def register_theme(self, theme: Any) -> ThemeProfile:
        """Hold one theme, judged whole before it is held."""
        validated = _check_theme_ref(theme)
        self._check_theme_free(validated)
        self._themes.append(validated)
        return validated

    def _check_view_free(self, view: ThemeView) -> None:
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

    def register_view(self, view: Any) -> ThemeView:
        """Hold one view record, judged whole first.

        A view id or a sequence already standing here
        refuses and holds nothing new. A held view
        only ever looks: standing it derives its
        panel, applies nothing and repaints nothing.
        """
        validated = _check_view_ref(view)
        self._check_view_free(validated)
        if validated.view_id is None:
            validated = ThemeView(
                view_id=self._fresh_view_id(
                    {v.view_id for v in self._views}),
                seq=validated.seq,
                mode_filter=validated.mode_filter,
                detail=validated.detail,
                recorded_on=validated.recorded_on,
                actor=validated.actor, source=validated.source,
                origin_session=validated.origin_session)
        self._views.append(validated)
        self._views.sort(key=lambda v: v.seq)
        return validated

    def register_book(self, book: Any) -> ThemeBook:
        """Hold a whole book, judged whole first."""
        validated = build_book(book)
        for theme in validated.themes:
            self._check_theme_free(theme)
        if self._title is None:
            self._title = validated.title
        elif validated.title != self._title:
            raise ValueError(
                "a second book under a different title refuses - "
                "one book stands in one registry")
        for theme in validated.themes:
            self._themes.append(theme)
        for view in validated.views:
            self.register_view(view)
        return self.book()

    def get_theme(self, theme_id: Any) -> ThemeProfile:
        """The theme one id names (KeyError if absent)."""
        wanted = _check_word(theme_id, "a theme id")
        for theme in self._themes:
            if theme.theme_id == wanted:
                return theme
        raise KeyError(f"no theme named {wanted!r} stands held")

    def get_view(self, view_id: Any) -> ThemeView:
        """The view record one id names (KeyError if absent)."""
        wanted = _check_word(view_id, "a view id")
        for view in self._views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no view named {wanted!r} stands held")

    def latest_view(self) -> ThemeView:
        """The last view recorded (KeyError if none)."""
        if not self._views:
            raise KeyError("no view stands held")
        return self._views[-1]

    def list_themes(self) -> Tuple[ThemeProfile, ...]:
        return tuple(self._themes)

    def list_views(self) -> Tuple[ThemeView, ...]:
        return tuple(self._views)

    def book(self) -> ThemeBook:
        return ThemeBook(
            title=self._title or "Themes Grown Up",
            themes=tuple(self._themes),
            views=tuple(self._views))

    def panel(self, view: Any = None) -> ThemePanel:
        return derive_panel(self.book(), view)

    def verdict(self, view: Any = None) -> ThemeVerdict:
        return derive_verdict(self.book(), view)


def themes_for_mode(source: Any, mode: Any) -> Tuple[ThemeProfile, ...]:
    """The themes of one mode, in held order."""
    wanted = normalize_mode(mode)
    return tuple(
        t for t in _held_themes(source) if t.mode == wanted)


def passing_themes(source: Any) -> Tuple[ThemeProfile, ...]:
    """The themes standing disciplined whole, in held order."""
    return tuple(t for t in _held_themes(source) if theme_passes(t))


def total_themes(source: Any) -> int:
    """How many themes a source holds."""
    return len(_held_themes(source))


# ---------------------------------------------------------------------
# Session news, plain words, and the screens.
# ---------------------------------------------------------------------


def theme_record(theme: Any) -> Dict[str, Any]:
    """The session-news record of one theme."""
    current = _check_theme_ref(theme)
    record_out = current.to_record()
    record_out["news"] = True
    record_out["headline"] = (
        f"Themes grown up theme {current.theme_id}: "
        f"{segment_of(current)}.")
    return record_out


def view_record(view: Any) -> Dict[str, Any]:
    """The session-news record of one view record."""
    current = _check_view_ref(view)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Themes grown up view {current.view_id or current.seq}: "
        f"mode {current.mode_filter!r} - "
        f"{current.detail}")
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of one derived panel."""
    current = validate_panel(panel, source)
    record = current.to_record()
    record["news"] = True
    modes = ", ".join(
        f"{c.mode} {c.themes}" for c in current.mode_counts)
    record["headline"] = (
        f"Themes grown up panel as of {current.as_of}: "
        f"{current.total_shown} of {current.total_themes} "
        f"themes show for mode {current.mode_filter!r} "
        f"({modes}).")
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    """The session-news record of one derived verdict."""
    current = validate_verdict(verdict, source, view)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Themes grown up verdict: {current.verdict} - "
        f"{current.passing_shown} of {current.total_shown} "
        f"shown themes disciplined across "
        f"{current.distinct_modes} modes, from "
        f"{current.earliest_on} to {current.latest_on}.")
    return record


def book_record(book: Any) -> Dict[str, Any]:
    """The session-news record of one theme book."""
    current = book if isinstance(book, ThemeBook) else build_book(book)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Themes grown up {current.title}: "
        f"{record['theme_count']} themes named, "
        f"{record['view_count']} views held - "
        f"{len(passing_themes(current))} of "
        f"{len(current.themes)} themes stand disciplined.")
    return record


def plain_words(theme: Any) -> str:
    """One theme, in one plain sentence."""
    current = _check_theme_ref(theme)
    return (
        f"{segment_of(current)} - one theme on "
        f"theme {current.theme_id}, standing in "
        f"{current.mode} mode. Holding it here "
        f"repaints nothing and applies no theme live.")


def view_plain_words(view: Any) -> str:
    """One view record, in one plain sentence."""
    current = _check_view_ref(view)
    return (
        f"View {current.view_id or current.seq} looks at "
        f"mode {current.mode_filter!r}, recorded on "
        f"{current.recorded_on} by {current.actor}: "
        f"{current.detail} A view only ever looks - it "
        f"applies no theme and repaints nothing.")


def panel_plain_words(source: Any, view: Any = None) -> str:
    """The panel in plain words, in full."""
    if isinstance(source, ThemePanel):
        panel = validate_panel(source)
        title = None
    elif isinstance(source, (ThemeBook, ThemeRegistry)):
        book = source if isinstance(
            source, ThemeBook) else source.book()
        panel = derive_panel(
            book, view if view is not None
            else _default_view(book))
        title = book.title
    else:
        raise ValueError(f"a themes source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    lines.append("Shown, in held order:")
    for row in panel.rows:
        lines.append(
            f"{row.theme_id}: {row.segment} "
            f"({row.recorded_on})")
    lines.extend(panel.account)
    return "\n".join(lines)


def verdict_plain_words(source: Any, view: Any = None) -> str:
    """The book verdict in plain words, in full."""
    if isinstance(source, ThemeVerdict):
        verdict = validate_verdict(source)
    elif isinstance(source, (ThemeBook, ThemeRegistry)):
        book = source if isinstance(
            source, ThemeBook) else source.book()
        verdict = derive_verdict(
            book, view if view is not None
            else _default_view(book))
    else:
        raise ValueError(f"a themes source is needed, got {source!r}")
    return (
        f"Themes grown up verdict: {verdict.verdict} - "
        f"{verdict.passing_shown} of {verdict.total_shown} "
        f"shown themes disciplined, across "
        f"{verdict.distinct_modes} modes, from "
        f"{verdict.earliest_on} to {verdict.latest_on} - "
        f"every judgement is derived from the themes' "
        f"own colours, cues and shares.")


def _source_book(source: Any) -> ThemeBook:
    if source is None:
        return load_themes_grown_up()
    if isinstance(source, ThemeRegistry):
        return source.book()
    if isinstance(source, ThemeBook):
        return source
    if isinstance(source, ThemeProfile):
        return ThemeBook(title="One theme", themes=(source,))
    raise ValueError(f"a theme book is needed, got {source!r}")


def format_theme(theme: Any) -> str:
    """One theme as a screen block.

    The theme's mode and words stand as their own
    lines, its colours stand role by role with
    their derived values, its cues and shares
    stand named - an unmeasured share standing
    honestly unknown - and its derived judgements
    and provenance stand whole: a theme held here
    is a finding, never the live face of the app.
    """
    current = _check_theme_ref(theme)
    lines = [
        f"{current.theme_id}: {segment_of(current)}",
        f"Name: {current.name}",
        f"Mode: {current.mode}",
    ]
    for role, colour in current.colours:
        lines.append(
            f"Colour {role}: {colour} "
            f"(value {colour_value(colour):.4f})")
    for role in STATE_ROLES:
        cue = current.cue_of(role)
        lines.append(
            f"Cue {role}: {cue if cue is not None else 'none recorded'}")
    lines.append(
        f"Accent share: "
        f"{current.accent_percent if current.accent_percent is not None else 'unknown'} "
        f"- Ornament share: "
        f"{current.ornament_percent if current.ornament_percent is not None else 'unknown'} "
        f"(shares are declared as data - no screen is "
        f"measured here).")
    lines.append(f"Words: {current.detail}")
    lines.append(
        f"Recorded: on {current.recorded_on} by {current.actor} "
        f"from {current.source} in {current.origin_session}.")
    return "\n".join(lines)


def format_view(view: Any) -> str:
    """One view record as a screen block."""
    current = _check_view_ref(view)
    lines = [
        f"{current.view_id or '-'}: mode "
        f"{current.mode_filter!r}",
        f"Words: {current.detail}",
        f"Recorded: on {current.recorded_on} by {current.actor} "
        f"from {current.source} in {current.origin_session}.",
    ]
    return "\n".join(lines)


def format_book(source: Any = None, mode: Any = None) -> str:
    """The book as derived segments, in held order.

    By default the lines are every theme's derived
    segment. With ``mode`` only that mode's themes
    stand in the list.
    """
    book = _source_book(source)
    wanted = normalize_mode(mode) if mode is not None else None
    lines = []
    for theme in book.themes:
        if wanted is not None and theme.mode != wanted:
            continue
        lines.append(f"{theme.theme_id}: {segment_of(theme)}")
    if not lines:
        lines.append("No themes stand in the book on that reading.")
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    """The panel as a screen block: every row and the account."""
    if isinstance(source, ThemePanel):
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
            f"{row.theme_id}: {row.segment} ({row.recorded_on})")
    lines.extend(panel.account)
    return "\n".join(lines)


def format_verdict(source: Any = None, view: Any = None) -> str:
    """The verdict as a screen block."""
    if isinstance(source, ThemeVerdict):
        verdict = validate_verdict(source)
        title = "the book"
    else:
        book = _source_book(source)
        verdict = derive_verdict(
            book, view if view is not None
            else _default_view(book))
        title = book.title
    return (
        f"Verdict in Themes Grown Up over {title}: "
        f"{verdict.verdict} - {verdict.passing_shown} of "
        f"{verdict.total_shown} shown themes disciplined, "
        f"across {verdict.distinct_modes} modes, from "
        f"{verdict.earliest_on} to {verdict.latest_on}.")


def format_themes_grown_up_screen(source: Any = None) -> str:
    """The whole themes-grown-up screen for one book."""
    book = _source_book(source)
    view = _default_view(book)
    panel = derive_panel(book, view)
    verdict = derive_verdict(book, view)
    lines = [
        f"Themes Grown Up (M-179) - {book.title}",
        format_book(book),
        f"Panel: {panel.total_shown} of "
        f"{panel.total_themes} themes show "
        f"for mode {panel.mode_filter!r}.",
        f"Verdict: {verdict.verdict}.",
        "This layer holds themes as data only - it "
        "repaints no live UI, applies no theme live, "
        "renders no live screen and measures no "
        "running screen.",
    ]
    return "\n".join(lines)


def parse_themes_grown_up_args(args: Any) -> Tuple[str, Any]:
    """Parse the /themesgrownup grammar into (action, target).

    ``""``/``show``/``list`` show the book;
    ``theme <theme-id>`` shows one theme whole;
    ``view <view-id>`` shows one held view record;
    ``mode <mode>`` shows one mode's themes;
    ``panel`` and ``verdict`` show the derived
    panel and verdict under the book's own view.
    Anything else raises ValueError carrying the
    usage line.
    """
    if args is None:
        return ("show", None)
    if not isinstance(args, str):
        raise ValueError(USAGE)
    parts = args.split()
    if not parts or parts == ["show"] or parts == ["list"]:
        return ("show", None)
    if parts[0] == "theme" and len(parts) == 2:
        return ("theme", _check_word(parts[1], "a theme id"))
    if parts[0] == "view" and len(parts) == 2:
        return ("view", _check_word(parts[1], "a view id"))
    if parts[0] == "mode" and len(parts) == 2:
        try:
            return ("mode", normalize_mode(parts[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if parts == ["panel"]:
        return ("panel", None)
    if parts == ["verdict"]:
        return ("verdict", None)
    raise ValueError(USAGE)
