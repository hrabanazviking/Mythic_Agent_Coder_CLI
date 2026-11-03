"""Apply-failure repair loop (All-Features roadmap slice M-073).

Part IV — The Editor's Hand. M-071's appliers and M-072's
anchored appliers refuse a stale target cleanly and change
nothing — but a refusal alone left the coder guessing what
the file holds now, and re-trying blind. This slice is the
bounded, visible loop the roadmap names: a failed apply
returns the true current text to the coder for one honest
retry.

What already shipped, and what this slice adds:

* M-071 (``core/edit_formats.py``): strict appliers — a
  unified diff whose context no longer matches, a search
  block matching zero or several times — refuse, change
  nothing, and carry the refusal's reason. There is no
  fuzz there, ever.
* M-072 (``core/hash_anchored.py``): anchored appliers
  refuse a moved target naming the expected and current
  anchors — but the coder still had to re-read the file
  itself to learn the true text behind the new anchor.
* This module turns either refusal into a *repair packet*:
  the road that refused, the refusal's own reason, and the
  true current text of the refused target — a bounded
  window of the file as it stands now — and lets exactly
  one retry ride on that packet, judged by the same strict
  appliers. This module writes no file; repaired applies
  ride the EditJournal road through the agent layer.

Honesty rules, enforced here and pinned by the slice's tests:

* **One honest retry, never two.** A packet carries a
  budget of ``MAX_RETRIES`` = 1. The retry is spent by
  being attempted — succeed or refuse, the packet is
  spent; a second refusal raises the exhaustion error,
  which names the budget spent, and a spent packet refuses
  any further retry outright. There is no silent re-apply
  and no loop.
* **No fuzz, ever.** The retry payload is judged by the
  exact M-071/M-072 appliers, unchanged. The loop hands
  the coder the truth; it never loosens the judgement.
* **The true text is bounded, and the bound is named.**
  The window is the refused target's lines plus
  ``CONTEXT_LINES`` of context on each side, capped at
  ``MAX_WINDOW_LINES``; whenever the window is not the
  whole file the packet says so (``truncated``) and names
  the file's true line count — a partial window is never
  presented as the whole file.
* **The setting is a gate, not a guess.** With
  ``apply_repair_loop`` off, applies through the agent
  layer keep the plain M-071/M-072 refusal and no packet
  is made; the pure packet maths stays available. A
  malformed stored setting raises, never defaults silently.
"""

from __future__ import annotations

__all__ = [
    "APPLY_REPAIR_SLICE",
    "CONTEXT_LINES",
    "MAX_RETRIES",
    "MAX_WINDOW_LINES",
    "PLAIN_EXPLANATION",
    "ROADS",
    "SETTING_KEY",
    "USAGE",
    "Any",
    "BoolChange",
    "Dict",
    "List",
    "Optional",
    "RepairPacket",
    "Sequence",
    "TrueTextWindow",
    "Tuple",
    "build_packet",
    "enabled_from_config",
    "format_apply_repair",
    "format_packet",
    "format_setting_change",
    "parse_repairloop_args",
    "retry_anchored_range",
    "retry_anchored_search",
    "retry_edit_format",
    "set_enabled",
    "target_range_for_format",
    "true_text_window",
]

import re
from dataclasses import dataclass, replace
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .edit_formats import apply_edit
from .hash_anchored import (
    apply_anchored_range,
    apply_anchored_search,
    range_hash,
)

#: The slice that owns this module.
APPLY_REPAIR_SLICE = "M-073"

#: The config key the repair-loop gate lives under.
SETTING_KEY = "apply_repair_loop"

#: The refusal roads a repair packet can be made from.
ROADS = ("edit_format", "anchored_range", "anchored_search")

#: The whole budget: one honest retry per refused apply.
MAX_RETRIES = 1

#: Lines of context shown on each side of a refused target.
CONTEXT_LINES = 5

#: The most lines of true current text a packet may carry.
MAX_WINDOW_LINES = 40

#: The setting explained in plain words — the sentence every
#: surface shows.
PLAIN_EXPLANATION = (
    "Apply-failure repair loop: when an edit refuses — a "
    "diff whose context no longer matches, a search block "
    "that does not match exactly once, an anchored target "
    "that moved — Mythic hands the coder the true current "
    "text of the refused target, a bounded window of the "
    "file as it stands now, and allows exactly one honest "
    "retry built on that truth. The retry is judged by the "
    "same strict rules — no fuzz, ever — and if it refuses "
    "too, the loop stops and says so. Every refusal, packet, "
    "retry, and outcome is recorded on the session journal, "
    "never silent."
)

USAGE = ("Usage: /repairloop, /repairloop on, "
         "or /repairloop off")


def _split(text: str) -> List[str]:
    if text == "":
        return []
    return (text[:-1] if text.endswith("\n") else text).split("\n")


@dataclass(frozen=True)
class TrueTextWindow:
    """A bounded window of a file's true current text."""

    start: int
    end: int
    lines: Tuple[str, ...]
    total_lines: int
    truncated: bool

    def text(self) -> str:
        return "\n".join(self.lines)

    def numbered(self) -> str:
        return "\n".join(
            f"{n}: {line}"
            for n, line in zip(
                range(self.start, self.end + 1), self.lines))


def true_text_window(current: str, start: Optional[int] = None,
                     end: Optional[int] = None) -> TrueTextWindow:
    """The true current text around lines *start*..*end*.

    The window is the target's lines plus ``CONTEXT_LINES``
    on each side, capped at ``MAX_WINDOW_LINES``. With no
    target given it starts at the file's head. ``truncated``
    is True whenever the window is not the whole file — the
    bound is named, never silent.
    """
    if not isinstance(current, str):
        raise ValueError("a repair window is made from a file's text")
    lines = _split(current)
    total = len(lines)
    if total == 0:
        return TrueTextWindow(start=0, end=0, lines=(), total_lines=0,
                              truncated=False)
    if start is None:
        lo, hi = 1, total
    else:
        if not isinstance(start, int) or not isinstance(end, int):
            raise ValueError("repair window line numbers must be "
                             "whole numbers")
        lo = min(max(start, 1), total)
        hi = min(max(end, lo), total)
    lo = max(1, lo - CONTEXT_LINES)
    hi = min(total, hi + CONTEXT_LINES)
    if hi - lo + 1 > MAX_WINDOW_LINES:
        hi = lo + MAX_WINDOW_LINES - 1
    truncated = lo > 1 or hi < total
    return TrueTextWindow(start=lo, end=hi,
                          lines=tuple(lines[lo - 1:hi]),
                          total_lines=total, truncated=truncated)


_HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def target_range_for_format(format_id: str, current: str,
                            payload: str) -> Optional[Tuple[int, int]]:
    """Where a refused format payload's target sits, if known.

    A unified diff names its first hunk's position outright.
    A search-and-replace payload's first block is located in
    the file when it appears there at all (once or several
    times — the first hit is the refused target's ground);
    when it appears nowhere, the target is honestly unknown
    and the window falls back to the file's head. Any other
    format carries no locatable target.
    """
    if not isinstance(current, str) or not isinstance(payload, str):
        raise ValueError("a repair target is located in text")
    lines = _split(current)
    if format_id == "unified-diff":
        for raw in payload.split("\n"):
            match = _HUNK_RE.match(raw)
            if match:
                start = int(match.group(1))
                count = int(match.group(2)) if match.group(2) else 1
                return start, max(start, start + count - 1)
        return None
    if format_id == "search-replace":
        raw = payload.split("\n")
        try:
            at = raw.index("<<<<<<< SEARCH")
            stop = raw.index("=======", at + 1)
        except ValueError:
            return None
        needle = raw[at + 1:stop]
        if not needle:
            return None
        for i in range(0, len(lines) - len(needle) + 1):
            if lines[i:i + len(needle)] == needle:
                return i + 1, i + len(needle)
        return None
    return None


@dataclass(frozen=True)
class RepairPacket:
    """One refused apply, handed back with the true text."""

    road: str
    reason: str
    window: TrueTextWindow
    attempts_used: int = 0

    @property
    def attempts_left(self) -> int:
        return MAX_RETRIES - self.attempts_used

    def event(self) -> Dict[str, Any]:
        return {"type": "apply_repair_offered", "road": self.road,
                "reason": self.reason, "start": self.window.start,
                "end": self.window.end,
                "total_lines": self.window.total_lines,
                "truncated": self.window.truncated,
                "attempts_used": self.attempts_used}

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        return {"type": "apply_repair_offered", "road": self.road,
                "reason": self.reason, "start": self.window.start,
                "end": self.window.end,
                "total_lines": self.window.total_lines,
                "truncated": self.window.truncated,
                "attempts_used": self.attempts_used,
                "true_text": self.window.text(),
                "session_id": session_id, "journaled": journaled}

    def spend(self) -> "RepairPacket":
        """The packet with its one retry spent — or a refusal.

        A packet whose budget is already spent refuses any
        further retry outright: the loop is bounded by
        construction, not by a caller's good behaviour.
        """
        if self.attempts_used >= MAX_RETRIES:
            raise ValueError(
                "the repair loop's one honest retry is already "
                "spent for this refused apply — there is no "
                "second retry; nothing was changed")
        return replace(self, attempts_used=self.attempts_used + 1)


def build_packet(road: str, reason: str, current: str,
                 start: Optional[int] = None,
                 end: Optional[int] = None) -> RepairPacket:
    """Make the repair packet for one refused apply."""
    if road not in ROADS:
        raise ValueError(
            f"a repair packet's road is one of {', '.join(ROADS)}; "
            f"got {road!r}")
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("a repair packet carries the refusal's reason")
    return RepairPacket(
        road=road, reason=reason,
        window=true_text_window(current, start, end))


def _spend(packet: RepairPacket, road: str) -> RepairPacket:
    if not isinstance(packet, RepairPacket):
        raise ValueError("a repair retry rides on a repair packet")
    if packet.road != road:
        raise ValueError(
            f"this packet came from the {packet.road} road; it "
            f"cannot be retried on the {road} road")
    return packet.spend()


def _exhausted(exc: ValueError) -> ValueError:
    return ValueError(
        f"the one honest retry also refused: {exc} The repair "
        f"budget is spent ({MAX_RETRIES} of {MAX_RETRIES} used) "
        "— nothing was changed, and there is no second retry")


def retry_edit_format(current: str, packet: RepairPacket,
                      format_id: str, payload: str
                      ) -> Tuple[str, int, RepairPacket]:
    """Retry a refused format apply once, on its packet.

    Judged by M-071's appliers exactly as the first attempt
    was — no fuzz. Returns (new text, units, spent packet).
    A second refusal raises the exhaustion error.
    """
    spent = _spend(packet, "edit_format")
    try:
        new_text, units = apply_edit(format_id, current, payload)
    except ValueError as exc:
        raise _exhausted(exc) from exc
    return new_text, units, spent


def retry_anchored_range(current: str, packet: RepairPacket,
                         start: int, end: int, expected: str,
                         replacement: str
                         ) -> Tuple[str, Any, RepairPacket]:
    """Retry a refused anchored range edit once, on its packet.

    The coder names the target again from the packet's true
    text — its new anchor — and M-072's applier judges it
    exactly as before. A second refusal exhausts the loop.
    """
    spent = _spend(packet, "anchored_range")
    try:
        new_text, applied = apply_anchored_range(
            current, start, end, expected, replacement)
    except ValueError as exc:
        raise _exhausted(exc) from exc
    return new_text, applied, spent


def retry_anchored_search(current: str, packet: RepairPacket,
                          search: str, expected: str,
                          replacement: str
                          ) -> Tuple[str, Any, RepairPacket]:
    """Retry a refused anchored search edit once, on its packet."""
    spent = _spend(packet, "anchored_search")
    try:
        new_text, applied = apply_anchored_search(
            current, search, expected, replacement)
    except ValueError as exc:
        raise _exhausted(exc) from exc
    return new_text, applied, spent


# ---------------------------------------------------------------------
# The gate setting — on by default, validated, never guessed.
# ---------------------------------------------------------------------

def enabled_from_config(config: Dict[str, Any]) -> bool:
    """The apply-repair-loop setting stored in *config*.

    Absent means True (the setting ships on). A stored value
    that is not a bool raises — never guessed at.
    """
    raw = config.get(SETTING_KEY, True)
    if not isinstance(raw, bool):
        raise ValueError(
            f"{SETTING_KEY} must be true or false, "
            f"got {type(raw).__name__}")
    return raw


@dataclass(frozen=True)
class BoolChange:
    """A recorded change of the gate setting."""

    before: bool
    after: bool

    def event(self) -> Dict[str, Any]:
        return {"type": "apply_repair_setting_changed",
                "from": self.before, "to": self.after}

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        return {"type": "apply_repair_setting_changed",
                "from": self.before, "to": self.after,
                "session_id": session_id, "journaled": journaled}


def set_enabled(config: Dict[str, Any],
                enabled: Any) -> Tuple[bool, BoolChange]:
    """Validate a gate change against *config*, purely."""
    if not isinstance(enabled, bool):
        raise ValueError(
            f"{SETTING_KEY} is turned on or off; got {enabled!r}")
    before = enabled_from_config(config)
    if enabled == before:
        raise ValueError(
            f"the apply-failure repair loop is already "
            f"{'on' if before else 'off'}")
    return enabled, BoolChange(before=before, after=enabled)


# ---------------------------------------------------------------------
# The /repairloop surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------

def parse_repairloop_args(args: str) -> Dict[str, Any]:
    """Parse ``/repairloop`` arguments.

    /repairloop       -> show
    /repairloop on    -> turn the gate on
    /repairloop off   -> turn the gate off
    """
    text = (args or "").strip()
    if not text:
        return {"action": "show"}
    if text == "on":
        return {"action": "setting", "enabled": True}
    if text == "off":
        return {"action": "setting", "enabled": False}
    raise ValueError(USAGE)


def format_setting_change(record: Dict[str, Any]) -> str:
    """A setting change record, in plain words."""
    word = {True: "on", False: "off"}
    return (f"Apply-failure repair loop: {word[record['from']]} -> "
            f"{word[record['to']]}.")


def format_packet(packet: RepairPacket) -> str:
    """A repair packet, in plain words, with its true text."""
    window = packet.window
    lines = [
        f"Apply refused ({packet.road}): {packet.reason}",
        f"True current text — lines {window.start}-{window.end} "
        f"of {window.total_lines}"
        + (" (a bounded window, not the whole file)"
           if window.truncated else "") + ":",
        window.numbered() if window.lines else "(the file is empty)",
        f"One honest retry is available on this packet "
        f"({packet.attempts_left} of {MAX_RETRIES} left); "
        "it is judged by the same strict rules — no fuzz, "
        "and there is no second retry.",
    ]
    return "\n".join(lines)


def format_apply_repair(config: Dict[str, Any]) -> str:
    """The whole slice, in plain words, for /repairloop.

    Built from enabled_from_config() / build_packet() /
    true_text_window() / target_range_for_format() /
    retry_edit_format() / retry_anchored_range() /
    retry_anchored_search(), so every public road this
    module offers is exercised by its own show surface.
    """
    enabled = enabled_from_config(config)
    sample = "alpha = 1\nbeta = 2\ngamma = 3"
    stale = "@@ -2,1 +2,1 @@\n-beta = 99\n+beta = 20"
    lines = ["Apply-failure repair loop (M-073) — "
             + PLAIN_EXPLANATION, ""]
    lines.append(f"Setting: {'on' if enabled else 'off'} "
                 f"({SETTING_KEY}).")
    lines.append("")
    try:
        apply_edit("unified-diff", sample, stale)
        verdict = "applied (unexpected)"
        packet = None
    except ValueError as exc:
        verdict = f"refused: {exc}"
        target = target_range_for_format("unified-diff", sample, stale)
        packet = build_packet(
            "edit_format", str(exc), sample,
            *(target if target else (None, None)))
    lines.append(f"A stale diff against a small file is {verdict}")
    if packet is not None:
        lines.append("")
        lines.append(format_packet(packet))
        good = "@@ -2,1 +2,1 @@\n-beta = 2\n+beta = 20"
        new_text, units, spent = retry_edit_format(
            sample, packet, "unified-diff", good)
        lines.append("")
        lines.append(
            f"The one honest retry, rebuilt on the true text, "
            f"applies ({units} hunk): line 2 is now "
            f"{new_text.splitlines()[1]!r}; the packet is spent "
            f"({spent.attempts_used} of {MAX_RETRIES} used).")
        try:
            retry_edit_format(sample, spent, "unified-diff", good)
            lines.append("A second retry was allowed (unexpected).")
        except ValueError as exc:
            lines.append(f"A second retry refuses: {exc}")
        anchor = range_hash(["beta = 2"])
        ranged = build_packet("anchored_range", "sample refusal",
                              sample, 2, 2)
        new_text, applied, _spent = retry_anchored_range(
            sample, ranged, 2, 2, anchor, "beta = 20")
        lines.append(
            f"An anchored retry on its packet applies too "
            f"(lines {applied.start}-{applied.end} of the sample "
            f"now hold {new_text.splitlines()[1]!r}).")
        searched = build_packet("anchored_search", "sample refusal",
                                sample, 2, 2)
        new_text, applied, _spent = retry_anchored_search(
            sample, searched, "beta = 2", anchor, "beta = 20")
        lines.append(
            f"And an anchored search retry applies "
            f"({applied.units} edit) from its packet's truth.")
        head = true_text_window(sample)
        lines.append(
            f"A window with no target named covers lines "
            f"{head.start}-{head.end} of {head.total_lines} "
            f"(truncated: {head.truncated}).")
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)
