"""Diff theatre in the TUI (roadmap slice M-091).

Part IV - The Editor's Hand. The roadmap's words:
``side-by-side and unified views, word-level
highlighting, whitespace toggle - colour never the
only signal.``

What already shipped, and what this slice adds:

* Diffs already reach the user in several places -
  hunk review (M-074) shows a unified diff hunk by
  hunk, commit craft (M-080) previews a commit's
  diff, the context compiler carries git diff hunks.
  Every one of those roads renders the same single
  form: a unified list, plus/minus colour doing most
  of the talking, whole lines as the smallest unit,
  and whitespace-only churn indistinguishable from
  real change.
* This slice is the theatre those diffs deserve, as
  a pure layer. One change, computed once from the
  true before/after texts, can be staged two ways:
  unified (one column, in order) or side-by-side
  (before and after paired on one row, a replacement
  facing itself). Inside a changed line, the words
  that actually changed are picked out, so a one-word
  fix in a long line reads as a one-word fix. A
  whitespace toggle judges lines that differ only in
  whitespace as unchanged - and says so on the line,
  never silently. This module renders nothing and
  writes nothing; the agent/TUI layer owns the screen.

Honesty rules, enforced here and pinned by tests:

* **Colour is never the only signal.** Every staged
  line carries a written sign (``+`` added, ``-``
  removed, blank for unchanged) and every rendered
  view carries a counted header (added / removed /
  unchanged), so the change reads in plain text, in
  grayscale, and through a screen reader.
* **Words, not impressions.** Word-level segments
  come from a real token diff of the two lines; a
  word is marked changed only when the token diff
  says so, and the removed/added word lists are
  counted from those same segments.
* **Whitespace honesty.** With the toggle on, a line
  that differs only in whitespace is staged as
  unchanged and flagged ``whitespace_only`` - shown,
  named, never hidden and never counted as a change.
  With the toggle off, the same lines stage as a
  removal plus an addition, exactly as they are.
* **No change is no change.** Identical texts stage
  as all-unchanged with zero added/removed, and the
  render says so; an empty before is all additions
  and an empty after is all removals - nothing is
  invented to fill the stage.
* **The setting is a gate, not a guess.** With
  ``diff_theatre`` off, staging through the agent
  layer refuses and says so; the pure maths stays
  available. A malformed stored setting raises,
  never defaults silently.
"""

from __future__ import annotations

__all__ = [
    "DIFF_THEATRE_SLICE",
    "PLAIN_EXPLANATION",
    "SETTING_KEY",
    "USAGE",
    "VIEWS",
    "Any",
    "BoolChange",
    "Dict",
    "DiffLine",
    "List",
    "Optional",
    "SideRow",
    "Theatre",
    "Tuple",
    "build_theatre",
    "enabled_from_config",
    "format_diff_theatre",
    "format_setting_change",
    "format_word_change",
    "line_diff",
    "parse_diff_args",
    "render",
    "render_side_by_side",
    "render_unified",
    "set_enabled",
    "whitespace_only_change",
    "word_changes",
    "word_segments",
]

import difflib
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

#: The slice that owns this module.
DIFF_THEATRE_SLICE = "M-091"

#: The config key the diff-theatre gate lives under.
SETTING_KEY = "diff_theatre"

#: The staged views this slice knows.
VIEWS = ("unified", "side_by_side")

#: The setting explained in plain words.
PLAIN_EXPLANATION = (
    "Diff theatre: a change can be read two ways - "
    "unified, one column in order, or side-by-side, "
    "with the before and after facing each other on "
    "one row so a replacement meets itself. Inside a "
    "changed line the words that actually changed are "
    "picked out, so a one-word fix in a long line "
    "reads as a one-word fix. A whitespace toggle "
    "judges lines that differ only in whitespace as "
    "unchanged - and flags them as whitespace-only on "
    "the line, never hiding them and never counting "
    "them as change. Colour is never the only signal: "
    "every line carries its written sign (+ added, "
    "- removed, blank for unchanged) and every view "
    "opens with the counted header, so the change "
    "reads in plain text, in grayscale, and through "
    "a screen reader."
)

USAGE = ("Usage: /diff, /diff on, /diff off, "
         "/diff unified, /diff side-by-side, "
         "/diff whitespace, or /diff whitespace off")


def _ws_key(line: str) -> str:
    """A line reduced to its words, for whitespace judging."""
    return " ".join(line.split())


def whitespace_only_change(old: str, new: str) -> bool:
    """True when *old* and *new* differ only in whitespace."""
    return old != new and _ws_key(old) == _ws_key(new)


@dataclass(frozen=True)
class DiffLine:
    """One staged line of a change.

    ``kind`` is ``context`` (unchanged), ``add`` or
    ``remove``. ``sign`` is the written signal that
    rides with the line whatever the colour does.
    ``whitespace_only`` marks a line judged unchanged
    under the whitespace toggle whose raw text did
    differ - named, never hidden.
    """

    kind: str
    text: str
    old_no: Optional[int]
    new_no: Optional[int]
    whitespace_only: bool = False

    @property
    def sign(self) -> str:
        return {"add": "+", "remove": "-"}.get(self.kind, " ")

    def record(self) -> Dict[str, Any]:
        return {"kind": self.kind, "text": self.text,
                "old_no": self.old_no, "new_no": self.new_no,
                "whitespace_only": self.whitespace_only}


def line_diff(before: str, after: str,
              ignore_whitespace: bool = False,
              ) -> List[DiffLine]:
    """Stage *before* -> *after* as a list of DiffLines.

    The diff is a real line diff (difflib) over the
    split lines. With *ignore_whitespace*, lines are
    judged by their words alone: a whitespace-only
    difference stages as context, flagged as such.
    """
    a = before.splitlines()
    b = after.splitlines()
    keys_a = [_ws_key(x) for x in a] if ignore_whitespace else a
    keys_b = [_ws_key(x) for x in b] if ignore_whitespace else b
    matcher = difflib.SequenceMatcher(None, keys_a, keys_b,
                                      autojunk=False)
    lines: List[DiffLine] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                old, new = a[i1 + k], b[j1 + k]
                lines.append(DiffLine(
                    kind="context", text=new,
                    old_no=i1 + k + 1, new_no=j1 + k + 1,
                    whitespace_only=(old != new)))
        if tag in ("replace", "delete"):
            for i in range(i1, i2):
                lines.append(DiffLine(
                    kind="remove", text=a[i],
                    old_no=i + 1, new_no=None))
        if tag in ("replace", "insert"):
            for j in range(j1, j2):
                lines.append(DiffLine(
                    kind="add", text=b[j],
                    old_no=None, new_no=j + 1))
    return lines


@dataclass(frozen=True)
class SideRow:
    """One side-by-side row: before facing after.

    ``kind`` is ``equal``, ``replace``, ``add`` (no
    left side) or ``remove`` (no right side).
    """

    kind: str
    left: Optional[DiffLine]
    right: Optional[DiffLine]


@dataclass(frozen=True)
class Theatre:
    """One staged change, ready to render either way."""

    view: str
    ignore_whitespace: bool
    lines: Tuple[DiffLine, ...]
    before_label: str
    after_label: str

    @property
    def added(self) -> int:
        return sum(1 for x in self.lines if x.kind == "add")

    @property
    def removed(self) -> int:
        return sum(1 for x in self.lines if x.kind == "remove")

    @property
    def unchanged(self) -> int:
        return sum(1 for x in self.lines if x.kind == "context")

    @property
    def changed(self) -> bool:
        return self.added > 0 or self.removed > 0

    def pairs(self) -> List[SideRow]:
        """Pair the staged lines into side-by-side rows.

        A removal block immediately followed by an
        addition block pairs in order as replacements
        (the longer side's tail pairs against nothing);
        everything else stands on its own side.
        """
        rows: List[SideRow] = []
        i = 0
        while i < len(self.lines):
            line = self.lines[i]
            if line.kind == "context":
                rows.append(SideRow("equal", line, line))
                i += 1
                continue
            removes: List[DiffLine] = []
            while i < len(self.lines) and self.lines[i].kind == "remove":
                removes.append(self.lines[i])
                i += 1
            adds: List[DiffLine] = []
            while i < len(self.lines) and self.lines[i].kind == "add":
                adds.append(self.lines[i])
                i += 1
            for k in range(max(len(removes), len(adds))):
                left = removes[k] if k < len(removes) else None
                right = adds[k] if k < len(adds) else None
                kind = ("replace" if left is not None
                        and right is not None
                        else "remove" if left is not None
                        else "add")
                rows.append(SideRow(kind, left, right))
        return rows

    def record(self) -> Dict[str, Any]:
        return {"type": "diff_theatre", "view": self.view,
                "ignore_whitespace": self.ignore_whitespace,
                "before": self.before_label,
                "after": self.after_label,
                "added": self.added, "removed": self.removed,
                "unchanged": self.unchanged,
                "lines": [x.record() for x in self.lines]}


def build_theatre(before: str, after: str,
                  view: str = "unified",
                  ignore_whitespace: bool = False,
                  before_label: str = "before",
                  after_label: str = "after") -> Theatre:
    """Stage one change for the theatre.

    *view* must name a known view - an unknown view
    raises rather than silently staging unified.
    """
    if view not in VIEWS:
        raise ValueError(
            f"unknown diff view {view!r}: "
            f"use one of {', '.join(VIEWS)}")
    return Theatre(
        view=view, ignore_whitespace=ignore_whitespace,
        lines=tuple(line_diff(before, after, ignore_whitespace)),
        before_label=before_label, after_label=after_label)


_TOKEN_RE = re.compile(r"\S+|\s+")


def _merge_segments(segments: List[Tuple[str, str]],
                    ) -> List[Tuple[str, str]]:
    merged: List[Tuple[str, str]] = []
    for status, text in segments:
        if not text:
            continue
        if merged and merged[-1][0] == status:
            merged[-1] = (status, merged[-1][1] + text)
        else:
            merged.append((status, text))
    return merged


def word_segments(old: str, new: str,
                  ) -> Tuple[List[Tuple[str, str]],
                             List[Tuple[str, str]]]:
    """Word-level segments for one changed line pair.

    Returns ``(old_segments, new_segments)``; each
    segment is ``(status, text)`` with status
    ``equal`` or ``changed``, the segments joining
    back to the exact original line on each side.
    """
    old_tokens = _TOKEN_RE.findall(old)
    new_tokens = _TOKEN_RE.findall(new)
    matcher = difflib.SequenceMatcher(None, old_tokens, new_tokens,
                                      autojunk=False)
    old_segments: List[Tuple[str, str]] = []
    new_segments: List[Tuple[str, str]] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            text = "".join(old_tokens[i1:i2])
            old_segments.append(("equal", text))
            new_segments.append(("equal", text))
        if tag in ("replace", "delete"):
            old_segments.append(
                ("changed", "".join(old_tokens[i1:i2])))
        if tag in ("replace", "insert"):
            new_segments.append(
                ("changed", "".join(new_tokens[j1:j2])))
    return _merge_segments(old_segments), _merge_segments(new_segments)


def word_changes(old: str, new: str) -> Tuple[List[str], List[str]]:
    """The (removed_words, added_words) of one line pair."""
    old_segments, new_segments = word_segments(old, new)
    removed = [word for status, text in old_segments
               if status == "changed" for word in text.split()]
    added = [word for status, text in new_segments
             if status == "changed" for word in text.split()]
    return removed, added


def format_word_change(old: str, new: str) -> str:
    """One line pair's word change, in written signs."""
    removed, added = word_changes(old, new)
    parts = []
    if removed:
        parts.append("words removed: " + ", ".join(
            f"-{word}" for word in removed))
    if added:
        parts.append("words added: " + ", ".join(
            f"+{word}" for word in added))
    return "; ".join(parts) if parts else "no word changes"


def _header(theatre: Theatre) -> str:
    if not theatre.changed:
        return (f"Diff theatre ({theatre.view}) "
                f"{theatre.before_label} -> {theatre.after_label}: "
                f"no changes "
                f"({theatre.unchanged} unchanged)")
    return (f"Diff theatre ({theatre.view}) "
            f"{theatre.before_label} -> {theatre.after_label}: "
            f"{theatre.added} added, {theatre.removed} removed, "
            f"{theatre.unchanged} unchanged")


def render_unified(theatre: Theatre) -> str:
    """Render the staged change as a unified view.

    Every line opens with its written sign; a replaced
    pair is followed by its word-level change, in
    words, so the highlighting never rides on colour
    alone.
    """
    lines = [_header(theatre)]
    for row in theatre.pairs():
        if row.kind == "equal":
            assert row.left is not None
            note = (" [whitespace only]"
                    if row.left.whitespace_only else "")
            lines.append(f"  {row.left.text}{note}")
        if row.left is not None and row.kind != "equal":
            lines.append(f"- {row.left.text}")
        if row.right is not None and row.kind != "equal":
            lines.append(f"+ {row.right.text}")
        if row.kind == "replace":
            assert row.left is not None and row.right is not None
            lines.append("  " + format_word_change(
                row.left.text, row.right.text))
    return "\n".join(lines)


def render_side_by_side(theatre: Theatre, width: int = 40) -> str:
    """Render the staged change side-by-side.

    Each row is ``<sign> <before> | <sign> <after>``;
    the signs and the header carry the meaning, the
    pairing carries the reading.
    """
    lines = [_header(theatre)]
    for row in theatre.pairs():
        left_text = row.left.text if row.left is not None else ""
        right_text = row.right.text if row.right is not None else ""
        left_sign = row.left.sign if row.left is not None else " "
        right_sign = row.right.sign if row.right is not None else " "
        note = ""
        if (row.kind == "equal" and row.left is not None
                and row.left.whitespace_only):
            note = " [whitespace only]"
        lines.append(
            f"{left_sign} {left_text:<{width}} | "
            f"{right_sign} {right_text}{note}")
    return "\n".join(lines)


def render(theatre: Theatre) -> str:
    """Render *theatre* in its own staged view."""
    if theatre.view == "side_by_side":
        return render_side_by_side(theatre)
    return render_unified(theatre)


def enabled_from_config(config: Dict[str, Any]) -> bool:
    """The diff_theatre setting stored in *config*.

    Absent means True (the setting ships on). A stored
    value that is not a bool raises - never guessed at.
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
        return {"type": "diff_theatre_setting_changed",
                "from": self.before, "to": self.after}

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        return {**self.event(), "session_id": session_id,
                "journaled": journaled}


def set_enabled(config: Dict[str, Any],
                enabled: Any) -> Tuple[bool, BoolChange]:
    """Validate a gate change against *config*, purely."""
    if not isinstance(enabled, bool):
        raise ValueError(
            f"{SETTING_KEY} is turned on or off; got {enabled!r}")
    before = enabled_from_config(config)
    if enabled == before:
        raise ValueError(
            f"diff theatre is already "
            f"{'on' if before else 'off'}")
    return enabled, BoolChange(before=before, after=enabled)


def parse_diff_args(args: str) -> Dict[str, Any]:
    """Parse the /diff grammar both surfaces share.

    ``show`` / ``on`` / ``off`` stand alone; ``unified``
    and ``side-by-side`` choose the staged view;
    ``whitespace`` turns the whitespace toggle on
    (whitespace-only differences judged unchanged,
    and flagged) and ``whitespace off`` turns it off.
    """
    text = (args or "").strip()
    if not text or text == "show":
        return {"action": "show"}
    if text == "on":
        return {"action": "on"}
    if text == "off":
        return {"action": "off"}
    if text == "unified":
        return {"action": "view", "view": "unified"}
    if text in ("side-by-side", "side", "sbs"):
        return {"action": "view", "view": "side_by_side"}
    if text in ("whitespace", "whitespace on"):
        return {"action": "whitespace", "ignore_whitespace": True}
    if text == "whitespace off":
        return {"action": "whitespace", "ignore_whitespace": False}
    raise ValueError(f"usage: {USAGE}")


def format_setting_change(record: Dict[str, Any]) -> str:
    state = "on" if record.get("to") else "off"
    return f"Diff theatre is now {state}."


def format_diff_theatre(config: Dict[str, Any]) -> str:
    """The whole slice, in plain words, for /diff.

    Built from build_theatre() / render_*(), so the
    show surface exercises the road it names: one demo
    change staged both ways, with its word change.
    """
    enabled = enabled_from_config(config)
    lines = ["Diff theatre in the TUI (M-091) - "
             + PLAIN_EXPLANATION, ""]
    lines.append(f"Setting: {'on' if enabled else 'off'} "
                 f"({SETTING_KEY}).")
    lines.append("")
    before = "alpha\nbeta old gamma\ndelta\n"
    after = "alpha\nbeta new gamma\ndelta\n"
    lines.append(render_unified(build_theatre(before, after)))
    lines.append("")
    lines.append(render_side_by_side(
        build_theatre(before, after, view="side_by_side")))
    return "\n".join(lines)
