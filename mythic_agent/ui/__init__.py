"""Thread-safety helpers and terminal-size guards for the Textual TUI.

This module is intentionally free of Textual imports so it can be used
(and unit-tested) without a running application. ``MythicTUI.on_mount``
calls :func:`register_app` so the wrappers below know which thread owns
the app's message loop.
"""

from __future__ import annotations

import functools
import logging
import shutil
import threading
from typing import Any, Callable

logger = logging.getLogger(__name__)

MIN_TERMINAL_COLS = 80
MIN_TERMINAL_ROWS = 24

_app_threads: dict[int, int] = {}  # id(app) -> thread ident running its message loop
_app_lock = threading.RLock()


def register_app(app: Any) -> None:
    """Record which thread runs ``app``'s message loop.

    Call from the app's ``on_mount`` (which executes on the app thread).
    """
    with _app_lock:
        _app_threads[id(app)] = threading.get_ident()
    logger.debug("Registered UI app thread: %s", threading.get_ident())


def unregister_app(app: Any) -> None:
    """Forget a previously registered app (cleanup / tests)."""
    with _app_lock:
        _app_threads.pop(id(app), None)


def _resolve_app(explicit: Any, args: tuple) -> Any | None:
    if explicit is not None:
        return explicit
    if args:
        # Screen/Widget convention: the bound self carries .app
        return getattr(args[0], "app", None)
    return None


def _app_thread_ident(app: Any) -> int | None:
    with _app_lock:
        return _app_threads.get(id(app))


def call_from_thread(app: Any, callback: Callable, *args: Any, **kwargs: Any) -> Any:
    """Route ``callback`` onto the Textual app thread, safely.

    If the caller is already on the app thread — or ``app`` was never
    registered (app not running, tests) — the callback runs inline so the
    work is never silently dropped.
    """
    if app is None:
        return callback(*args, **kwargs)
    loop_thread = _app_thread_ident(app)
    if loop_thread is not None and threading.get_ident() != loop_thread:
        return app.call_from_thread(callback, *args, **kwargs)
    return callback(*args, **kwargs)


def ui_thread(app: Any = None):
    """Decorator ensuring the wrapped callable runs on the Textual app thread.

    The app is resolved from the ``app=`` argument, otherwise from
    ``self.app`` (the Screen/Widget convention). Off-thread calls are
    marshalled with ``app.call_from_thread``; on-thread calls run inline.

    Usage::

        @ui_thread()
        def _update_label(self, text: str): ...
    """

    def decorate(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            target = _resolve_app(app, args)
            return call_from_thread(target, func, *args, **kwargs)

        return wrapper

    return decorate


def terminal_size(fallback: tuple[int, int] = (80, 24)) -> tuple[int, int]:
    """Current terminal size as (columns, rows)."""
    size = shutil.get_terminal_size(fallback=fallback)
    return (size.columns, size.lines)


def terminal_too_small(
    min_cols: int = MIN_TERMINAL_COLS, min_rows: int = MIN_TERMINAL_ROWS
) -> tuple[bool, tuple[int, int]]:
    """Return (is_too_small, (cols, rows)) for the current terminal."""
    cols, rows = terminal_size()
    return (cols < min_cols or rows < min_rows), (cols, rows)


def small_terminal_warning(cols: int, rows: int) -> str:
    """Warning banner shown when the terminal is below the minimum size."""
    return (
        f"[bold yellow]⚠ Small terminal detected ({cols}x{rows}; "
        f"minimum {MIN_TERMINAL_COLS}x{MIN_TERMINAL_ROWS}).[/bold yellow]\n"
        "[dim]Sidebar hidden and layout simplified for readability.[/dim]"
    )
