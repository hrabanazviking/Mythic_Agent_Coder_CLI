"""Deterministic startup and machine-output ordering guarantees (R-011).

What this module promises:

* User-facing listings (providers, themes, tools, slash commands, doctor
  checks, cost summaries) are emitted in sorted or otherwise stable order.
* Machine output (``--json``) contains no wall-clock timestamps or other
  volatile values, except for fields explicitly documented in
  :data:`VOLATILE_JSON_FIELDS`.
* Any randomness that reaches user-visible output is either seeded or
  documented in :data:`RANDOMNESS_NOTES`.
"""

from __future__ import annotations

__all__ = [
    "RANDOMNESS_NOTES",
    "VOLATILE_JSON_FIELDS",
    "StartupSequence",
    "sorted_listing",
    "startup_sequence",
]

#: Machine (``--json``) fields that are intentionally volatile, keyed by
#: command name. Every other field in machine output must be byte-identical
#: across runs given identical inputs. An empty tuple means the command's
#: machine output is fully deterministic.
VOLATILE_JSON_FIELDS: dict[str, tuple[str, ...]] = {
    # Stored record metadata, not wall-clock readings taken at emit time.
    "sessions": ("created_at", "updated_at"),
    "run": (),
    "cache": (),
    "costs": (),
    "metrics": (),
    # Opt-in --live checks embed round-trip timings in the message text;
    # offline checks are fully deterministic.
    "doctor": ("message",),
    "review": (),
    # bench.py emits a run timestamp; it is a benchmarking tool, not a
    # machine interface, so its output is volatile by design.
    "bench": ("timestamp",),
}

#: Known user-visible randomness that is intentionally *not* seeded,
#: with the reason. Decorative-only; never part of machine output.
RANDOMNESS_NOTES: dict[str, str] = {
    "ui.screens.chat_screen:agent-image":
        "random.choice over local image files for the TUI agent portrait; "
        "decorative only, never emitted in machine output.",
}


def sorted_listing(items, *, key=None):
    """Return *items* as a list in stable sorted order for user-facing output.

    ``key`` defaults to the identity; callers that need a custom order pass
    an explicit key function instead of relying on container iteration order.
    """
    return sorted(items, key=key)


class StartupSequence:
    """Recorder for the deterministic startup order of an entry point.

    Entry points (``engine.initialize``, the MCP server, …) record each
    initialization step in order. Tests assert the recorded order is stable;
    operators can inspect ``report()`` to see exactly what startup did.
    """

    def __init__(self) -> None:
        self._steps: list[tuple[str, str]] = []

    def record(self, name: str, detail: str = "") -> None:
        """Record one startup step, in call order."""
        self._steps.append((name, detail))

    def step_names(self) -> list[str]:
        """Step names in the order they were recorded."""
        return [name for name, _ in self._steps]

    def report(self) -> list[dict[str, str]]:
        """Full ordered record as a list of ``{"step", "detail"}`` dicts."""
        return [{"step": name, "detail": detail} for name, detail in self._steps]


def startup_sequence() -> StartupSequence:
    """Create a fresh :class:`StartupSequence` recorder."""
    return StartupSequence()
