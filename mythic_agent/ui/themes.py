"""Named color themes for the Mythic Agent TUI and terminal output.

Themes are plain dicts mapping semantic color roles to hex color strings so
callers can adapt them to any frontend (Textual ``Theme``, Rich console
styles, plain ANSI).  The user's choice is persisted in the config under
the ``ui.theme`` key by the ``mythic theme --set NAME`` command.
"""


from __future__ import annotations

__all__ = [
    "Any",
    "DEFAULT_THEME",
    "THEMES",
    "get_theme",
    "is_valid_theme",
    "list_themes",
    "to_textual_kwargs",
]

import copy
from typing import Any

#: Theme name -> semantic role -> hex color.
THEMES: dict[str, dict[str, str]] = {
    "tokyo_night": {
        "background": "#1a1b26",
        "surface": "#24283b",
        "primary": "#7aa2f7",
        "secondary": "#bb9af7",
        "accent": "#7dcfff",
        "text": "#c0caf5",
        "muted": "#565f89",
        "success": "#9ece6a",
        "warning": "#e0af68",
        "error": "#f7768e",
    },
    "viking_dark": {
        "background": "#14120e",
        "surface": "#1f1b14",
        "primary": "#c98f2e",
        "secondary": "#7a9b4a",
        "accent": "#4a8b9b",
        "text": "#d8cfae",
        "muted": "#5c5646",
        "success": "#7a9b4a",
        "warning": "#d19a2e",
        "error": "#a33b2e",
    },
    "light": {
        "background": "#f5f3ee",
        "surface": "#ffffff",
        "primary": "#2f5fa3",
        "secondary": "#6a4fa3",
        "accent": "#1f7a8c",
        "text": "#1f1f24",
        "muted": "#7d7a72",
        "success": "#3d7a34",
        "warning": "#a06a1c",
        "error": "#a3231d",
    },
}

DEFAULT_THEME = "tokyo_night"


def list_themes() -> list[str]:
    """Return the available theme names, sorted for stable output."""
    return sorted(THEMES)


def get_theme(name: str) -> dict[str, str]:
    """Return a deep copy of the named theme's color roles.

    Raises:
        KeyError: If ``name`` is not a known theme.
    """
    return copy.deepcopy(THEMES[name])


def is_valid_theme(name: str) -> bool:
    """Return True when ``name`` is a known theme."""
    return name in THEMES


def to_textual_kwargs(name: str) -> dict[str, Any]:
    """Convert a theme into keyword args suitable for Textual's ``Theme``.

    Raises:
        KeyError: If ``name`` is not a known theme.
    """
    return get_theme(name)
