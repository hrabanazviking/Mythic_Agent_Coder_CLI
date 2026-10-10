"""Progress indicators for long operations (Slice 29).

Simple, dependency-free progress display:
- ``ProgressBar``: determinate bar for known totals
- ``Spinner``: indeterminate spinner for unknown durations
- Both write to stderr and respect NO_COLOR / non-TTY.
"""

from __future__ import annotations

import os
import sys
import threading
import time
from typing import Optional, TextIO


class ProgressBar:
    """Determinate progress bar.

    Usage:
        with ProgressBar(total=100, label="Indexing") as bar:
            for i in range(100):
                ...
                bar.update(1)
    """

    BAR_WIDTH = 30

    def __init__(
        self,
        total: int,
        label: str = "",
        stream: Optional[TextIO] = None,
        enabled: Optional[bool] = None,
    ) -> None:
        self.total = max(1, total)
        self.label = label
        self.stream = stream or sys.stderr
        self.enabled = self.stream.isatty() if enabled is None else enabled
        self._done = 0
        self._start = time.monotonic()
        self._lock = threading.Lock()

    def update(self, n: int = 1) -> None:
        with self._lock:
            self._done = min(self.total, self._done + n)
            self._render()

    def set(self, n: int) -> None:
        with self._lock:
            self._done = min(self.total, max(0, n))
            self._render()

    @property
    def fraction(self) -> float:
        return self._done / self.total

    def _render(self) -> None:
        if not self.enabled:
            return
        filled = int(self.BAR_WIDTH * self.fraction)
        bar = "█" * filled + "░" * (self.BAR_WIDTH - filled)
        pct = self.fraction * 100
        elapsed = time.monotonic() - self._start
        line = f"\r{self.label} [{bar}] {pct:5.1f}% ({self._done}/{self.total}) {elapsed:.1f}s"
        self.stream.write(line)
        self.stream.flush()

    def finish(self) -> None:
        with self._lock:
            self._done = self.total
            self._render()
            if self.enabled:
                self.stream.write("\n")
                self.stream.flush()

    def __enter__(self) -> "ProgressBar":
        return self

    def __exit__(self, *args: object) -> None:
        self.finish()


class Spinner:
    """Indeterminate spinner for operations of unknown duration.

    Usage:
        with Spinner("Loading model"):
            do_slow_thing()
    """

    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(
        self,
        label: str = "",
        stream: Optional[TextIO] = None,
        interval: float = 0.1,
        enabled: Optional[bool] = None,
    ) -> None:
        self.label = label
        self.stream = stream or sys.stderr
        self.interval = interval
        self.enabled = self.stream.isatty() if enabled is None else enabled
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def _spin(self) -> None:
        i = 0
        while not self._stop.wait(self.interval):
            frame = self.FRAMES[i % len(self.FRAMES)]
            self.stream.write(f"\r{frame} {self.label}")
            self.stream.flush()
            i += 1

    def start(self) -> None:
        if not self.enabled or self._thread:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._thread:
            self._stop.set()
            self._thread.join(timeout=1.0)
            self._thread = None
            if self.enabled:
                # Clear the spinner line
                self.stream.write("\r" + " " * (len(self.label) + 4) + "\r")
                self.stream.flush()

    def __enter__(self) -> "Spinner":
        self.start()
        return self

    def __exit__(self, *args: object) -> None:
        self.stop()
