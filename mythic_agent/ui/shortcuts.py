"""Central keyboard-shortcut registry for the TUI and terminal loop.

The defaults live in :data:`SHORTCUTS` (action name -> key binding). Users can
override any binding through config at ``ui.shortcuts.<action>``; the override
takes effect everywhere the registry is consulted. ``docs/SHORTCUTS.md``
documents the same table for humans.
"""


from __future__ import annotations

__all__ = [
    "Any",
    "Mapping",
    "SHORTCUTS",
    "effective_shortcuts",
    "get_shortcut",
    "list_actions",
]

from typing import Any, Mapping

#: action name -> default binding. Bindings use Textual-style key notation
#: ("ctrl+c", "f1", "escape"); terminal fallbacks are listed in SHORTCUTS.md.
SHORTCUTS: dict[str, str] = {
    # TUI actions
    "quit": "ctrl+q",
    "help": "f1",
    "clear": "ctrl+l",
    "focus_input": "ctrl+i",
    "scroll_up": "shift+up",
    "scroll_down": "shift+down",
    "new_tab": "ctrl+t",
    "next_tab": "ctrl+tab",
    "prev_tab": "ctrl+shift+tab",
    "close_tab": "ctrl+w",
    "command_palette": "ctrl+k",
    "toggle_sidebar": "ctrl+b",
    # Terminal loop actions
    "interrupt": "ctrl+c",
    "suspend": "ctrl+z",
    "send": "enter",
    "send_multiline": "shift+enter",
    "history_prev": "up",
    "history_next": "down",
    "clear_line": "ctrl+u",
}


def get_shortcut(action: str, config: Mapping[str, Any] | None = None) -> str:
    """Return the binding for ``action``.

    Args:
        action: The action name from :data:`SHORTCUTS`.
        config: Optional loaded config dict; a custom binding at
            ``config["ui"]["shortcuts"][action]`` overrides the default.

    Raises:
        KeyError: If ``action`` is not a known action.
    """
    if action not in SHORTCUTS:
        raise KeyError(f"Unknown shortcut action: {action!r}")
    if config:
        try:
            override = config["ui"]["shortcuts"][action]
        except (KeyError, TypeError):
            override = None
        if override:
            return str(override)
    return SHORTCUTS[action]


def list_actions() -> list[str]:
    """Return the known shortcut action names, sorted for stable output."""
    return sorted(SHORTCUTS)


def effective_shortcuts(config: Mapping[str, Any] | None = None) -> dict[str, str]:
    """Return ``{action: binding}`` with config overrides applied."""
    return {action: get_shortcut(action, config) for action in list_actions()}
