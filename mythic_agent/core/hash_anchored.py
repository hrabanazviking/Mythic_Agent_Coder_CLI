"""Hash-anchored edits (All-Features roadmap slice M-072).

Part IV — The Editor's Hand. An edit no longer has to carry
the full text it touches, or trust that the file still holds
it: every line — and every range of lines — carries a content
hash, its anchor. The coder names a target by line range plus
the anchor it saw; the applier recomputes the anchor from the
file's true current text and applies only on an exact match.

What already shipped, and what this slice adds:

* M-071's appliers refuse a stale target (a unified diff whose
  context no longer matches, a search block that does not
  match exactly once) — but the coder still had to re-send the
  context or the search text on every attempt, and a refusal
  could not say *which* of the lines it touched had moved.
* M-069's intelligence cache already keys its entries by a
  file's SHA-256 content hash. This slice is the per-line /
  per-range version of that same road for edits: SHA-256 over
  the exact lines touched, nothing else.
* This module writes no file. Anchored applies ride the
  existing EditJournal road through the agent layer, exactly
  like M-071's formats.

Honesty rules, enforced here and pinned by the slice's tests:

* **A moved target refuses cleanly, and changes nothing.**
  When the recomputed anchor differs from the anchor the
  edit carries, the refusal names the range, the expected
  anchor, and the anchor the file actually holds now — that
  is the whole report. The bounded retry that hands the
  coder the true current text is M-073's road, not a silent
  fuzz here; there is no fuzz, ever (the M-071 law).
* **An anchor is the hash of the exact lines only.** No line
  numbers, no file name, no surrounding context ride in it —
  the same lines hash the same everywhere, and lines that
  merely moved keep their anchor while the range that names
  them is judged at its stated position.
* **Anchors are shown short, checked whole.** Surfaces show
  the first 12 hex digits; verification accepts a full hash
  or that short form, and refuses anything that is not hex
  of at least the short length instead of guessing.
* **The setting is a gate, not a guess.** With
  ``hash_anchored_edits`` off, anchored applies through the
  agent layer refuse and say so; the pure anchor maths stays
  available — knowing a file's anchors is not an edit. A
  malformed stored setting raises, never defaults silently.
"""

from __future__ import annotations

__all__ = [
    "HASH_ANCHORED_SLICE",
    "PLAIN_EXPLANATION",
    "SETTING_KEY",
    "SHORT_HASH_LEN",
    "USAGE",
    "Any",
    "AnchoredApply",
    "BoolChange",
    "Dict",
    "LineAnchor",
    "List",
    "Optional",
    "RangeAnchor",
    "RefusalReport",
    "Sequence",
    "Tuple",
    "anchor_lines",
    "annotate",
    "apply_anchored_range",
    "apply_anchored_search",
    "enabled_from_config",
    "format_hash_anchored",
    "format_refusal",
    "format_setting_change",
    "line_hash",
    "parse_hashanchor_args",
    "range_anchor",
    "range_hash",
    "set_enabled",
    "verify_range",
]

import hashlib
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

#: The slice that owns this module.
HASH_ANCHORED_SLICE = "M-072"

#: The config key the anchored-edits gate lives under.
SETTING_KEY = "hash_anchored_edits"

#: How many hex digits of an anchor a surface shows.
SHORT_HASH_LEN = 12

#: The setting explained in plain words — the sentence every
#: surface shows.
PLAIN_EXPLANATION = (
    "Hash-anchored edits: every line of a file carries a "
    "short content hash — its anchor — made from the line's "
    "exact text. The coder can name the lines it wants to "
    "change by their line numbers and the anchor it saw, "
    "instead of re-sending the whole text. Mythic checks the "
    "anchor against the file as it stands now: if the lines "
    "are unchanged, the edit applies; if they moved or "
    "changed, the edit refuses cleanly, names the anchor it "
    "expected and the anchor the file holds now, and changes "
    "nothing — no guesswork, no mangled file."
)

USAGE = ("Usage: /hashanchor, /hashanchor on, "
         "or /hashanchor off")


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def line_hash(line: str) -> str:
    """The full SHA-256 anchor of one line's exact text."""
    if not isinstance(line, str):
        raise ValueError("a line anchor is made from text")
    return _hash_text(line)


def range_hash(lines: Sequence[str]) -> str:
    """The full SHA-256 anchor of a range of lines, in order.

    The lines are joined with a single newline and no
    trailing newline — the anchor is over the lines only.
    An empty range has no anchor and raises.
    """
    if not lines:
        raise ValueError("an empty range has no anchor")
    for line in lines:
        if not isinstance(line, str):
            raise ValueError("a range anchor is made from text lines")
    return _hash_text("\n".join(lines))


def _short(full: str) -> str:
    return full[:SHORT_HASH_LEN]


def _split(text: str) -> Tuple[List[str], bool]:
    if text == "":
        return [], False
    ending = text.endswith("\n")
    return (text[:-1] if ending else text).split("\n"), ending


def _join(lines: List[str], ending: bool) -> str:
    text = "\n".join(lines)
    return text + "\n" if ending and lines else text


def _check_range(lines: List[str], start: int, end: int) -> None:
    if not isinstance(start, int) or not isinstance(end, int):
        raise ValueError("anchor line numbers must be whole numbers")
    if start < 1 or end < start or end > len(lines):
        raise ValueError(
            f"anchor range {start}-{end} is outside the file "
            f"(it holds {len(lines)} line(s)) — the target has "
            "moved or gone; nothing was changed")


@dataclass(frozen=True)
class LineAnchor:
    """One line, its number (1-based), and its anchor."""

    number: int
    hash: str
    text: str

    @property
    def short(self) -> str:
        return _short(self.hash)

    def ref(self) -> str:
        return f"{self.number}:{self.short}"


@dataclass(frozen=True)
class RangeAnchor:
    """A range of lines (1-based, inclusive) and its anchor."""

    start: int
    end: int
    hash: str

    @property
    def short(self) -> str:
        return _short(self.hash)

    @property
    def line_count(self) -> int:
        return self.end - self.start + 1

    def ref(self) -> str:
        return f"{self.start}-{self.end}:{self.short}"


def anchor_lines(current: str, start: Optional[int] = None,
                 end: Optional[int] = None) -> Tuple[LineAnchor, ...]:
    """Every line's anchor, or one range's (1-based, inclusive)."""
    if not isinstance(current, str):
        raise ValueError("anchors are made from a file's text")
    lines, _ending = _split(current)
    lo = 1 if start is None else start
    hi = len(lines) if end is None else end
    if lines:
        _check_range(lines, lo, hi)
    elif lo != 1 or (end is not None and end != 0):
        raise ValueError("an empty file holds no line anchors")
    return tuple(
        LineAnchor(number=n, hash=line_hash(lines[n - 1]),
                   text=lines[n - 1])
        for n in range(lo, hi + 1))


def range_anchor(current: str, start: int, end: int) -> RangeAnchor:
    """The anchor of lines *start*..*end* of *current*."""
    if not isinstance(current, str):
        raise ValueError("anchors are made from a file's text")
    lines, _ending = _split(current)
    _check_range(lines, start, end)
    return RangeAnchor(start=start, end=end,
                       hash=range_hash(lines[start - 1:end]))


def annotate(current: str, start: Optional[int] = None,
             end: Optional[int] = None) -> str:
    """A file's lines in anchored form: ``number:short| text``.

    This is the presentation the coder reads a target from:
    the anchor names the line's exact text in 12 hex digits,
    so a later edit can carry the anchor instead of the text.
    """
    anchors = anchor_lines(current, start, end)
    return "\n".join(f"{a.ref()}| {a.text}" for a in anchors)


def _normalise_expected(expected: str) -> str:
    if not isinstance(expected, str):
        raise ValueError("an anchor must be given as hex text")
    value = expected.strip().lower()
    if len(value) < SHORT_HASH_LEN or len(value) > 64:
        raise ValueError(
            f"an anchor is {SHORT_HASH_LEN} to 64 hex digits; "
            f"got {expected!r}")
    if any(c not in "0123456789abcdef" for c in value):
        raise ValueError(f"an anchor is hex digits; got {expected!r}")
    return value


def _matches(expected: str, full: str) -> bool:
    return full.startswith(_normalise_expected(expected))


def verify_range(current: str, start: int, end: int,
                 expected: str) -> bool:
    """True when lines *start*..*end* still hold *expected*."""
    return _matches(expected, range_anchor(current, start, end).hash)


@dataclass(frozen=True)
class RefusalReport:
    """A moved target, named: what was expected, what stands."""

    start: int
    end: int
    expected: str
    current: str
    reason: str

    def event(self) -> Dict[str, Any]:
        return {"type": "hash_anchored_refused",
                "start": self.start, "end": self.end,
                "expected": self.expected, "current": self.current,
                "reason": self.reason}


def _refuse(anchor: RangeAnchor, expected: str) -> RefusalReport:
    return RefusalReport(
        start=anchor.start, end=anchor.end,
        expected=_normalise_expected(expected), current=anchor.hash,
        reason=(f"lines {anchor.start}-{anchor.end} no longer hold "
                f"the anchor the edit carries "
                f"({_short(_normalise_expected(expected))}); the "
                f"file now holds {_short(anchor.hash)} there — "
                "the target moved, so the edit refuses and "
                "changes nothing"))


def format_refusal(report: RefusalReport) -> str:
    """A refusal report, in plain words."""
    return ("Hash-anchored edit refused: " + report.reason + ".")


@dataclass(frozen=True)
class AnchoredApply:
    """One applied anchored edit: before/after range anchors."""

    start: int
    end: int
    before: RangeAnchor
    after_hash: str
    units: int

    def event(self, path: str) -> Dict[str, Any]:
        return {"type": "hash_anchored_applied", "path": path,
                "start": self.start, "end": self.end,
                "before": self.before.hash, "after": self.after_hash,
                "units": self.units}

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        return {"type": "hash_anchored_applied",
                "start": self.start, "end": self.end,
                "before": self.before.hash, "after": self.after_hash,
                "units": self.units, "session_id": session_id,
                "journaled": journaled}


def apply_anchored_range(current: str, start: int, end: int,
                         expected: str, replacement: str
                         ) -> Tuple[str, AnchoredApply]:
    """Replace lines *start*..*end* — only under their anchor.

    The range's current anchor must match *expected* (full or
    short form). A mismatch raises ValueError carrying the
    refusal report's words, and the text is unchanged — this
    function is pure, so a refusal writes nothing anywhere.
    The replacement may hold any number of lines (including
    none — an anchored deletion).
    """
    if not isinstance(current, str) or not isinstance(replacement, str):
        raise ValueError("an anchored edit works on text")
    lines, ending = _split(current)
    _check_range(lines, start, end)
    before = range_anchor(current, start, end)
    if not _matches(expected, before.hash):
        raise ValueError(format_refusal(_refuse(before, expected)))
    new_lines = (lines[:start - 1]
                 + (replacement.split("\n") if replacement else [])
                 + lines[end:])
    new_text = _join(new_lines, ending)
    after = _hash_text(replacement) if replacement else _hash_text("")
    return new_text, AnchoredApply(
        start=start, end=end, before=before, after_hash=after, units=1)


def apply_anchored_search(current: str, search: str, expected: str,
                          replacement: str) -> Tuple[str, AnchoredApply]:
    """Replace the one block matching *search* — under its anchor.

    The search text must match exactly once (the EditJournal
    / M-071 law) AND the matched lines' anchor must match
    *expected*: a block whose text is right but whose anchor
    was made from different lines refuses, exactly as a moved
    target does. Zero matches and several matches both refuse.
    """
    if not isinstance(current, str) or not isinstance(search, str) \
            or not isinstance(replacement, str):
        raise ValueError("an anchored edit works on text")
    if not search:
        raise ValueError("an anchored search needs the text it touches")
    lines, ending = _split(current)
    needle = search.split("\n")
    hits = [i for i in range(0, len(lines) - len(needle) + 1)
            if lines[i:i + len(needle)] == needle]
    if not hits:
        raise ValueError(
            "an anchored search matched nothing — the file does "
            "not hold that text, so its anchor cannot be checked; "
            "nothing was changed")
    if len(hits) > 1:
        raise ValueError(
            f"an anchored search matched {len(hits)} places — it "
            "must match exactly once; nothing was changed")
    start = hits[0] + 1
    end = hits[0] + len(needle)
    before = range_anchor(current, start, end)
    if not _matches(expected, before.hash):
        raise ValueError(format_refusal(_refuse(before, expected)))
    new_text, applied = apply_anchored_range(
        current, start, end, before.hash, replacement)
    return new_text, applied


# ---------------------------------------------------------------------
# The gate setting — on by default, validated, never guessed.
# ---------------------------------------------------------------------

def enabled_from_config(config: Dict[str, Any]) -> bool:
    """The hash-anchored-edits setting stored in *config*.

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
        return {"type": "hash_anchored_setting_changed",
                "from": self.before, "to": self.after}

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        return {"type": "hash_anchored_setting_changed",
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
            f"hash-anchored edits are already "
            f"{'on' if before else 'off'}")
    return enabled, BoolChange(before=before, after=enabled)


# ---------------------------------------------------------------------
# The /hashanchor surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------

def parse_hashanchor_args(args: str) -> Dict[str, Any]:
    """Parse ``/hashanchor`` arguments.

    /hashanchor       -> show
    /hashanchor on    -> turn the gate on
    /hashanchor off   -> turn the gate off
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
    return (f"Hash-anchored edits: {word[record['from']]} -> "
            f"{word[record['to']]}.")


def format_hash_anchored(config: Dict[str, Any]) -> str:
    """The whole slice, in plain words, for /hashanchor.

    Built from enabled_from_config() / anchor_lines() /
    range_anchor() / annotate() / verify_range(), so every
    public road this module offers is exercised by its own
    show surface.
    """
    enabled = enabled_from_config(config)
    sample = "alpha = 1\nbeta = 2\nalpha = 1"
    lines = ["Hash-anchored edits (M-072) — " + PLAIN_EXPLANATION, ""]
    lines.append(f"Setting: {'on' if enabled else 'off'} "
                 f"({SETTING_KEY}).")
    lines.append("")
    lines.append("A small file, in anchored form:")
    lines.append(annotate(sample))
    lines.append("")
    whole = range_anchor(sample, 1, 2)
    lines.append(f"Lines 1-2 together anchor as {whole.ref()} "
                 f"({whole.line_count} lines); line 1 alone is "
                 f"{anchor_lines(sample, 1, 1)[0].ref()}.")
    changed = "alpha = 1\nbeta = 99\nalpha = 1"
    lines.append(f"Checking lines 1-2 against that anchor: "
                 f"unchanged file {verify_range(sample, 1, 2, whole.hash)}; "
                 f"after line 2 changed "
                 f"{verify_range(changed, 1, 2, whole.hash)} — "
                 f"a changed line ({line_hash('beta = 2')[:SHORT_HASH_LEN]} "
                 f"became {line_hash('beta = 99')[:SHORT_HASH_LEN]}) "
                 f"moves the range anchor, and the edit refuses.")
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)
