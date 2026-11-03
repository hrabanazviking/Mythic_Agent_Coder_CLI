"""Hunk-level review (All-Features roadmap slice M-074).

Part IV — The Editor's Hand. The roadmap's words: the
approval UI shows diffs per hunk with accept / reject /
edit per hunk; rejecting one hunk never kills the rest.

What already shipped, and what this slice adds:

* M-071 (``core/edit_formats.py``): a unified diff applies
  strictly, hunk by hunk — every hunk's context and removed
  lines must match the file exactly at the stated position
  (shifted by earlier hunks), no fuzz, ever — but the diff
  was all-or-nothing: accept the whole payload or refuse
  the whole payload. There was no way to review it a hunk
  at a time, and no way to keep the good hunks when one
  hunk was wrong.
* This slice is the review layer over that applier: a
  unified diff is split into its hunks as data, each hunk
  carries its own decision (pending, accepted, rejected,
  or edited), an edited hunk is re-judged before it may
  apply, and the accepted subset is applied through the
  unchanged M-071 applier. This module writes no file;
  accepted edits ride the EditJournal road through the
  agent layer, and the whole review is recorded there.

Honesty rules, enforced here and pinned by the slice's
tests:

* **Rejecting one hunk never kills the rest.** A rejected
  hunk is simply left out of the applied payload; every
  other accepted hunk is judged and applied on its own
  merits, against the file as it stands — the rejected
  hunk's change is never smuggled in, and its absence is
  counted in the outcome, never hidden.
* **Every hunk must be decided.** Applying a review with
  a pending hunk in it refuses and names the undecided
  hunks — a hunk is never silently accepted by default,
  and never silently dropped by default either.
* **An edit edits what a hunk becomes, never what it
  matches.** An edited hunk's old side — its context and
  removed lines, the evidence the strict applier judges
  against — must stay byte-for-byte the original hunk's
  old side; only its new side may change. The edited hunk
  is then re-judged by exactly the same strict applier as
  any other hunk: a stale edited hunk refuses like any
  stale hunk, and a refusal changes nothing at all.
* **No fuzz, ever.** The applied subset rides M-071's
  ``apply_unified_diff`` unchanged — the review layer
  never loosens the judgement, it only chooses which
  hunks stand in front of it.
* **Rejecting everything is an honest outcome.** A review
  whose hunks are all rejected applies nothing, changes
  nothing, and is recorded as exactly that — it is not an
  error and it is not presented as an apply.
* **The setting is a gate, not a guess.** With
  ``hunk_review`` off, reviewed applies through the agent
  layer refuse and say so; the pure review maths stays
  available. A malformed stored setting raises, never
  defaults silently.
"""

from __future__ import annotations

__all__ = [
    "DECISIONS",
    "HUNK_REVIEW_SLICE",
    "PLAIN_EXPLANATION",
    "SETTING_KEY",
    "USAGE",
    "Any",
    "BoolChange",
    "Dict",
    "Hunk",
    "HunkReview",
    "List",
    "Optional",
    "ReviewOutcome",
    "Sequence",
    "Tuple",
    "apply_review",
    "decide",
    "edit_hunk",
    "enabled_from_config",
    "format_hunk_review",
    "format_review",
    "format_setting_change",
    "parse_hunkreview_args",
    "set_enabled",
    "split_diff",
    "start_review",
]

import re
from dataclasses import dataclass, replace
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .edit_formats import apply_unified_diff

#: The slice that owns this module.
HUNK_REVIEW_SLICE = "M-074"

#: The config key the hunk-review gate lives under.
SETTING_KEY = "hunk_review"

#: Every decision a hunk may carry. ``pending`` is where
#: every hunk starts; it is never a valid state to apply in.
DECISIONS: Tuple[str, ...] = ("pending", "accept", "reject", "edit")

#: The setting explained in plain words — the sentence
#: every surface shows.
PLAIN_EXPLANATION = (
    "Hunk-level review: a unified diff is shown one hunk "
    "at a time, and each hunk is accepted, rejected, or "
    "edited on its own. Rejecting one hunk never kills "
    "the rest — the accepted hunks are applied through "
    "the same strict applier as any diff (every hunk's "
    "context must match the file exactly; no fuzz, ever), "
    "and the rejected hunks are simply left out. An edit "
    "may change what a hunk becomes, never what it "
    "matches: its context and removed lines stay exactly "
    "as proposed, and the edited hunk is re-judged by the "
    "same strict rules before it applies. Every hunk must "
    "be decided before anything applies — nothing is "
    "accepted or dropped by default — and the whole "
    "review, with each hunk's decision, is recorded on "
    "the session journal."
)

USAGE = "Usage: /hunkreview, /hunkreview on, or /hunkreview off"

_HUNK_RE = re.compile(
    r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(?:\s.*)?$")


@dataclass(frozen=True)
class Hunk:
    """One reviewable hunk of a unified diff.

    ``body`` is the hunk's lines exactly as proposed, each
    keeping its one-character prefix (' ' context, '-'
    removed, '+' added, '\\' no-newline marker). The old
    side (context + removed) is what the strict applier
    judges against the file; the new side (context +
    added) is what the file becomes where the hunk lands.
    """

    index: int
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    body: Tuple[str, ...]

    @property
    def old_side(self) -> List[str]:
        return [line[1:] for line in self.body
                if line[:1] in (" ", "-")]

    @property
    def new_side(self) -> List[str]:
        return [line[1:] for line in self.body
                if line[:1] in (" ", "+")]

    def header(self) -> str:
        return (f"@@ -{self.old_start},{self.old_count} "
                f"+{self.new_start},{self.new_count} @@")

    def to_diff(self) -> str:
        """This hunk alone, as a one-hunk unified diff."""
        return "\n".join([self.header(), *self.body])


def _judge_body(index: int, old_start: int, old_count: int,
                new_start: int, new_count: int,
                body: Sequence[str]) -> Hunk:
    """Build a Hunk, proving its body's counts are honest."""
    old_seen = sum(1 for line in body if line[:1] in (" ", "-"))
    new_seen = sum(1 for line in body if line[:1] in (" ", "+"))
    for line in body:
        if line[:1] not in (" ", "-", "+", "\\"):
            raise ValueError(
                f"hunk {index} carries a line that is not a "
                f"diff body line: {line!r}; nothing was changed")
    if old_seen != old_count or new_seen != new_count:
        raise ValueError(
            f"hunk {index}'s line counts do not match its "
            "header — the diff is malformed; nothing was changed")
    return Hunk(index=index, old_start=old_start,
                old_count=old_count, new_start=new_start,
                new_count=new_count, body=tuple(body))


def split_diff(payload: str) -> Tuple[Hunk, ...]:
    """Split a unified diff into its reviewable hunks.

    File headers (``---`` / ``+++``) and blank lines are
    skipped, exactly as the M-071 applier skips them; every
    hunk's stated counts are proven against its body here,
    so a malformed diff refuses at review time, before any
    decision is made on it — never halfway through an
    apply.
    """
    if not isinstance(payload, str):
        raise ValueError("a unified diff works on text")
    raw = payload.split("\n")
    hunks: List[Hunk] = []
    i = 0
    while i < len(raw):
        line = raw[i]
        if line.startswith("--- ") or line.startswith("+++ "):
            i += 1
            continue
        match = _HUNK_RE.match(line)
        if match is None:
            if line.strip() == "":
                i += 1
                continue
            raise ValueError(f"not a unified diff: line {line!r}")
        old_start = int(match.group(1))
        old_count = int(match.group(2)) if match.group(2) else 1
        new_start = int(match.group(3))
        new_count = int(match.group(4)) if match.group(4) else 1
        i += 1
        body: List[str] = []
        while i < len(raw) and not raw[i].startswith("@@ "):
            body_line = raw[i]
            if body_line == "" and (
                    sum(1 for b in body if b[:1] in (" ", "-"))
                    >= old_count
                    and sum(1 for b in body if b[:1] in (" ", "+"))
                    >= new_count):
                break
            body.append(body_line if body_line else " ")
            i += 1
            if (sum(1 for b in body if b[:1] in (" ", "-"))
                    >= old_count
                    and sum(1 for b in body if b[:1] in (" ", "+"))
                    >= new_count):
                break
        hunks.append(_judge_body(len(hunks), old_start, old_count,
                                 new_start, new_count, body))
    if not hunks:
        raise ValueError("the payload carries no diff hunk")
    return tuple(hunks)


@dataclass(frozen=True)
class HunkReview:
    """A whole review: the hunks, and each hunk's decision.

    ``decisions`` runs parallel to ``hunks``; an edited
    hunk's replacement body is carried in ``edited`` by
    hunk index. Reviews are values: deciding or editing
    returns a new review and changes nothing in the old
    one, so a review can be shown, recorded, and only then
    applied.
    """

    hunks: Tuple[Hunk, ...]
    decisions: Tuple[str, ...]
    edited: Tuple[Tuple[int, Tuple[str, ...]], ...] = ()

    def decision(self, index: int) -> str:
        return self.decisions[index]

    def hunk(self, index: int) -> Hunk:
        """Hunk *index* as it would apply (edited body in)."""
        base = self.hunks[index]
        for edited_index, body in self.edited:
            if edited_index == index:
                old_count = sum(
                    1 for line in body if line[:1] in (" ", "-"))
                new_count = sum(
                    1 for line in body if line[:1] in (" ", "+"))
                return replace(base, old_count=old_count,
                               new_count=new_count, body=tuple(body))
        return base

    def undecided(self) -> List[int]:
        return [i for i, d in enumerate(self.decisions)
                if d == "pending"]

    def counts(self) -> Dict[str, int]:
        result = {"accepted": 0, "rejected": 0, "edited": 0,
                  "pending": 0}
        for decision in self.decisions:
            if decision == "accept":
                result["accepted"] += 1
            elif decision == "reject":
                result["rejected"] += 1
            elif decision == "edit":
                result["edited"] += 1
            else:
                result["pending"] += 1
        return result

    def event(self) -> Dict[str, Any]:
        return {"type": "hunk_review_applied",
                "hunks": len(self.hunks),
                "decisions": list(self.decisions),
                **self.counts()}

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        return {**self.event(), "session_id": session_id,
                "journaled": journaled}


def start_review(payload: str) -> HunkReview:
    """Open a review over *payload*: every hunk pending."""
    hunks = split_diff(payload)
    return HunkReview(hunks=hunks,
                      decisions=tuple("pending" for _ in hunks))


def _check_index(review: HunkReview, index: int) -> None:
    if not isinstance(index, int) or not 0 <= index < len(review.hunks):
        raise ValueError(
            f"there is no hunk {index!r} in this review; it "
            f"holds {len(review.hunks)} hunk(s)")


def decide(review: HunkReview, index: int,
           decision: str) -> HunkReview:
    """Record an accept / reject decision for one hunk.

    ``edit`` is not a decision this road takes — an edit
    must carry its edited body, through :func:`edit_hunk`,
    so it can be judged. Re-deciding a hunk replaces its
    decision (and clears any edited body), never stacks.
    """
    _check_index(review, index)
    if decision == "edit":
        raise ValueError(
            "an edit must carry its edited body — use the "
            "edit road, so the new hunk can be judged")
    if decision not in DECISIONS or decision == "pending":
        raise ValueError(
            f"a hunk is decided accept or reject; got {decision!r}")
    decisions = list(review.decisions)
    decisions[index] = decision
    edited = tuple((i, b) for i, b in review.edited if i != index)
    return replace(review, decisions=tuple(decisions), edited=edited)


def edit_hunk(review: HunkReview, index: int,
              body: Sequence[str]) -> HunkReview:
    """Record an edited body for one hunk, re-judged here.

    The edited body's old side must equal the original
    hunk's old side exactly — an edit changes what the
    hunk becomes, never what it matches. Its counts are
    recomputed from the body itself (the header is
    rebuilt at apply time), so a body whose lines do not
    parse as a hunk refuses here, at edit time, instead of
    at apply time.
    """
    _check_index(review, index)
    if isinstance(body, str):
        lines = body.split("\n")
        while lines and lines[-1] == "":
            lines.pop()
    else:
        lines = list(body)
    if not lines:
        raise ValueError("an edited hunk needs at least one line")
    original = review.hunks[index]
    candidate = _judge_body(
        index, original.old_start,
        sum(1 for line in lines if line[:1] in (" ", "-")),
        original.new_start,
        sum(1 for line in lines if line[:1] in (" ", "+")), lines)
    if candidate.old_side != original.old_side:
        raise ValueError(
            "an edit may change what a hunk becomes, never "
            "what it matches: the edited hunk's context and "
            "removed lines differ from the proposed hunk's; "
            "nothing was changed")
    decisions = list(review.decisions)
    decisions[index] = "edit"
    edited = tuple((i, b) for i, b in review.edited if i != index)
    edited = edited + ((index, tuple(lines)),)
    return replace(review, decisions=tuple(decisions), edited=edited)


@dataclass(frozen=True)
class ReviewOutcome:
    """What an applied review did, in counted plain data."""

    applied: int
    rejected: int
    edited: int
    changed: bool

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        return {"type": "hunk_review_applied",
                "applied": self.applied, "rejected": self.rejected,
                "edited": self.edited, "changed": self.changed,
                "session_id": session_id, "journaled": journaled}


def apply_review(current: str, review: HunkReview
                 ) -> Tuple[str, ReviewOutcome]:
    """Apply a fully-decided review to *current*.

    Returns (new_text, outcome). The accepted and edited
    hunks — and only those — are rebuilt into a diff and
    judged by M-071's strict applier, unchanged: any one
    of them gone stale refuses the whole apply and changes
    nothing. Rejected hunks are left out entirely: their
    changes never land, and their absence never shifts an
    accepted hunk's judgement (the applier's offset follows
    the applied hunks only, which is exactly the file the
    accepted hunks were proposed against once the rejected
    changes are not made). A review with every hunk
    rejected is an honest no-change outcome, not an error.
    """
    if not isinstance(current, str):
        raise ValueError("hunk review works on text")
    pending = review.undecided()
    if pending:
        raise ValueError(
            "hunk(s) " + ", ".join(str(i) for i in pending)
            + " are not decided yet — every hunk must be "
            "accepted, rejected, or edited before anything "
            "applies; nothing was changed")
    counts = review.counts()
    chosen = [review.hunk(i) for i, d in enumerate(review.decisions)
              if d in ("accept", "edit")]
    if not chosen:
        return current, ReviewOutcome(
            applied=0, rejected=counts["rejected"], edited=0,
            changed=False)
    payload = "\n".join(hunk.to_diff() for hunk in chosen)
    new_text, units = apply_unified_diff(current, payload)
    return new_text, ReviewOutcome(
        applied=units, rejected=counts["rejected"],
        edited=counts["edited"], changed=new_text != current)


def enabled_from_config(config: Dict[str, Any]) -> bool:
    """The hunk-review setting stored in *config*.

    Absent means True (the setting ships on). A stored
    value that is not a bool raises — never guessed at.
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
        return {"type": "hunk_review_setting_changed",
                "from": self.before, "to": self.after}

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        return {"type": "hunk_review_setting_changed",
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
            f"hunk review is already "
            f"{'on' if before else 'off'}")
    return enabled, BoolChange(before=before, after=enabled)


# ---------------------------------------------------------------------
# The /hunkreview surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------

def parse_hunkreview_args(args: str) -> Dict[str, Any]:
    """Parse ``/hunkreview`` arguments.

    /hunkreview       -> show
    /hunkreview on    -> turn the gate on
    /hunkreview off   -> turn the gate off
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
    return (f"Hunk review: {word[record['from']]} -> "
            f"{word[record['to']]}.")


def format_review(review: HunkReview) -> str:
    """A review, hunk by hunk, in plain words."""
    lines = [f"Hunk review — {len(review.hunks)} hunk(s):"]
    for hunk in review.hunks:
        decision = review.decision(hunk.index)
        shown = review.hunk(hunk.index)
        lines.append(
            f"  hunk {hunk.index}: {hunk.header()} "
            f"(-{shown.old_count} +{shown.new_count}) "
            f"[{decision}]")
        for body_line in shown.body:
            lines.append(f"    {body_line}")
    counts = review.counts()
    lines.append(
        f"Decisions: {counts['accepted']} accepted, "
        f"{counts['edited']} edited, {counts['rejected']} "
        f"rejected, {counts['pending']} undecided.")
    return "\n".join(lines)


_SAMPLE = (
    "alpha = 1\nbeta = 2\ngamma = 3\ndelta = 4\nepsilon = 5\n")

_SAMPLE_DIFF = (
    "@@ -1,2 +1,2 @@\n alpha = 1\n-beta = 2\n+beta = 20\n"
    "@@ -4,2 +4,2 @@\n delta = 4\n-epsilon = 5\n+epsilon = 50")


def format_hunk_review(config: Dict[str, Any]) -> str:
    """The whole slice, in plain words, for /hunkreview.

    Built from split_diff() / start_review() / decide() /
    edit_hunk() / apply_review() / format_review(), so
    every public road this module offers is exercised by
    its own show surface: a two-hunk diff where the first
    hunk is accepted, the second is rejected — and the
    rejected change honestly never lands — then the same
    diff with the second hunk edited instead.
    """
    enabled = enabled_from_config(config)
    lines = ["Hunk-level review (M-074) — " + PLAIN_EXPLANATION, ""]
    lines.append(f"Setting: {'on' if enabled else 'off'} "
                 f"({SETTING_KEY}).")
    lines.append("")
    review = start_review(_SAMPLE_DIFF)
    lines.append(f"The sample diff splits into "
                 f"{len(review.hunks)} reviewable hunks:")
    lines.append(format_review(review))
    decided = decide(decide(review, 0, "accept"), 1, "reject")
    new_text, outcome = apply_review(_SAMPLE, decided)
    lines.append("")
    lines.append(
        f"Accept hunk 0, reject hunk 1: {outcome.applied} "
        f"hunk applied, {outcome.rejected} rejected — "
        f"line 2 is now {new_text.splitlines()[1]!r} and "
        f"line 5 is still {new_text.splitlines()[4]!r}: "
        "rejecting one hunk never kills the rest, and a "
        "rejected change never lands.")
    edited = edit_hunk(
        decide(review, 0, "accept"), 1,
        [" delta = 4", "-epsilon = 5", "+epsilon = 55"])
    new_text, outcome = apply_review(_SAMPLE, edited)
    lines.append(
        f"Edit hunk 1 instead (its new side only): "
        f"{outcome.applied} hunks applied, {outcome.edited} "
        f"of them edited — line 5 is now "
        f"{new_text.splitlines()[4]!r}.")
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)
