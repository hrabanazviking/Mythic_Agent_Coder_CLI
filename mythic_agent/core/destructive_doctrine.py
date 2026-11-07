"""Destructive-command doctrine (All-Features roadmap slice M-111).

Part V - Autonomy & Safety. The roadmap's words:
``a written ladder (reversible -> costly ->
irreversible) with the approval each rung needs;
`rm -rf` class acts always name their targets in
plain words first.``

What already shipped, and what this slice adds:

* The tree already refuses a denylist of
  destructive shell invocations outright on the
  execution road (``mythic_agent/core/sandbox.py``:
  ``_DENYLIST_PATTERNS`` - rm -rf, mkfs, dd
  of=/dev/..., shred and kin, judged by
  ``Sandbox.check_denied``), already answers
  command permission with ``ask`` / ``allow`` /
  ``deny`` in its postures
  (``permission_profiles.py``, M-095: the command
  answers are deny / ask / allow, and Trusted
  Forge's command answer is ``ask``), already
  asks afresh through the ``ask`` mode of the
  elder ToolPolicy (``policy.py``), and already
  knows that a remembered approval is only ever
  created with the caller's explicit answer
  (``remembered_approvals.py``, M-096:
  ``explicit=True``). Nothing in the tree holds
  the *ladder* itself as data - which acts are
  reversible, which are costly, which can never
  be undone, and what approval each kind needs
  before it runs - and no road names an
  irreversible act's targets in plain words
  before judging it.
* This slice is that missing doctrine, as a pure
  layer in the exact sibling shape: the ladder
  held as validated data (three rungs, each
  carrying the one approval it needs), the
  command patterns that place an act on a rung
  held as validated data (their regex shapes
  widen the shipped sandbox denylist's shapes;
  this layer classifies, it does not refuse or
  run anything), a mechanical judge that reads a
  command against those patterns alone, a
  plain-words naming of an irreversible act's
  targets, a judgement record shaped as session
  news, and a small in-memory registry model
  with deterministic ids. This module runs no
  command, deletes nothing, writes no file,
  changes no setting and imports no agent / UI
  code; the agent layer owns holding the
  registry for a session, judging real commands
  on the real roads, and asking the approvals
  the ladder names.

Honesty rules, enforced here and pinned by tests:

* **The ladder is exactly three rungs.**
  Reversible, costly, irreversible - the
  roadmap's own words, in the roadmap's order.
  Each rung carries exactly one approval:
  reversible needs none, costly asks once (the
  tree's own ``ask`` answer), irreversible needs
  explicit approval naming every target first
  (the M-096 explicit-answer rule, with the
  roadmap's plain-words rule added). A rung
  built naming any other approval refuses.
* **Classification is mechanical, never
  guessed.** An act sits on a rung only because
  one of the held patterns - explicit data -
  matches it. Patterns are read most-severe
  first after the dry-run reading, so an act
  matching two rungs earns the worse one.
* **Unknown commands are never claimed safe.**
  A command no pattern knows is judged
  ``unclassified``: it carries no rung, and it
  needs approval (ask once) precisely because
  this layer cannot say what it costs. Nothing
  in this layer ever calls an unknown command
  reversible.
* **An irreversible act names its targets
  first.** A judgement on the irreversible rung
  refuses to exist without at least one named
  target - read from the command's own operands,
  or, for acts whose target is implicit (a force
  push, a hard reset, a fork bomb), named by the
  pattern's own held words. The session-news
  headline states those targets in plain words
  before anything else about the act.
* **A judgement never disagrees with itself.**
  The rung, the classification, the pattern and
  the approval are validated against each other
  on construction: a classified judgement names
  a held pattern of its own rung and carries
  that rung's one approval; an unclassified
  judgement names no pattern and no rung.
* **Status is never carried by colour or symbol
  alone.** Every formatter states a judgement's
  rung and approval in words.
"""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass, replace
from typing import Any, Dict, Optional, Tuple

__all__ = [
    "APPROVAL_PHRASES",
    "APPROVAL_REQUIREMENTS",
    "CLASSIFICATIONS",
    "COMMAND_PATTERNS",
    "DESTRUCTIVE_DOCTRINE_SLICE",
    "DOCTRINE_LADDER",
    "DOCTRINE_RUNGS",
    "PLAIN_EXPLANATION",
    "USAGE",
    "DestructiveJudgement",
    "DestructivePattern",
    "DoctrineRegistry",
    "DoctrineRung",
    "Judgement",
    "Rung",
    "approval_for_rung",
    "build_judgement",
    "build_pattern",
    "build_rung",
    "doctrine_record",
    "format_doctrine_record",
    "format_doctrine_screen",
    "format_judgement",
    "format_judgements",
    "format_ladder",
    "format_pattern",
    "format_patterns",
    "format_record",
    "format_rung",
    "judge_command",
    "normalize_approval",
    "normalize_classification",
    "normalize_judgement_id",
    "normalize_pattern_id",
    "normalize_rung",
    "pattern_for_id",
    "plain_words",
    "parse_doctrine_args",
    "rung_for",
    "validate_judgement",
    "validate_pattern",
    "validate_rung",
]

DESTRUCTIVE_DOCTRINE_SLICE = "M-111"

#: The ladder's rungs, in the roadmap's order:
#: what can be undone, what can be undone only
#: at a price, and what can never be undone.
DOCTRINE_RUNGS = ("reversible", "costly", "irreversible")

#: The approval each rung needs, in rung order:
#: none at all; the tree's own ``ask`` answer,
#: asked once; and an explicit approval that
#: names every target first (see M-096).
APPROVAL_REQUIREMENTS = (
    "none", "ask_once", "explicit_named_targets")

#: The one approval each rung carries. A rung or
#: a judgement naming any other pairing refuses.
_RUNG_APPROVALS = {
    "reversible": "none",
    "costly": "ask_once",
    "irreversible": "explicit_named_targets",
}

#: Each approval, said in plain words.
APPROVAL_PHRASES = {
    "none": "no approval needed",
    "ask_once": "ask once before it runs",
    "explicit_named_targets": (
        "explicit approval naming every target first"),
}

#: How a judgement was classified: a held pattern
#: placed it on a rung, or no pattern knows it.
CLASSIFICATIONS = ("classified", "unclassified")

#: The approval an unclassified command needs:
#: it is not claimed safe, so it is asked about.
_UNCLASSIFIED_APPROVAL = "ask_once"

_RUNG_LABELS = {
    "reversible": "can be undone",
    "costly": "can be undone only at a price",
    "irreversible": "can never be undone",
}

_RUNG_WORDS = {
    "reversible": "reversible", "undoable": "reversible",
    "revertible": "reversible",
    "costly": "costly", "expensive": "costly",
    "irreversible": "irreversible",
    "permanent": "irreversible",
    "unrecoverable": "irreversible",
}

_APPROVAL_WORDS = {
    "none": "none", "no": "none", "free": "none",
    "ask_once": "ask_once", "ask": "ask_once",
    "ask_once_before": "ask_once", "once": "ask_once",
    "explicit_named_targets": "explicit_named_targets",
    "explicit": "explicit_named_targets",
    "named_targets": "explicit_named_targets",
    "explicit_named": "explicit_named_targets",
}

_CLASS_WORDS = {
    "classified": "classified", "known": "classified",
    "unclassified": "unclassified",
    "unknown": "unclassified",
}

PLAIN_EXPLANATION = (
    "The destructive-command doctrine is a "
    "written ladder of three rungs. A reversible "
    "act can be undone and needs no approval; a "
    "costly act can be undone only at a price and "
    "asks once before it runs; an irreversible "
    "act can never be undone and needs explicit "
    "approval naming every target in plain words "
    "first. Commands are placed on a rung by "
    "held patterns only, never by guessing, and "
    "a command no pattern knows is unclassified "
    "- never claimed safe, and asked about. This "
    "layer holds the ladder, the patterns and "
    "the judgements as data only; it runs no "
    "command and deletes nothing itself - the "
    "agent layer judges real commands through it "
    "and asks the approvals it names."
)

USAGE = (
    "Usage: /doctrine, /doctrine show, "
    "/doctrine show <judgement>, "
    "/doctrine ladder, "
    "/doctrine check <command>"
)

_ID_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789-_.")

_PATTERN_ID_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyz0123456789_")


def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _pick(mapping: Dict[str, Any], names: Tuple[str, ...],
          what: str) -> Any:
    """One field from its spellings, or a refusal on conflict."""
    found = [name for name in names if name in mapping]
    if not found:
        return None
    first = mapping[found[0]]
    for name in found[1:]:
        if mapping[name] != first:
            raise ValueError(
                f"a doctrine record names two different {what}")
    return first


def normalize_rung(value: Any) -> str:
    """The canonical ladder rung a word names.

    Reads ``reversible`` (or ``undoable``),
    ``costly`` and ``irreversible`` (or
    ``permanent``), case-insensitively, with
    dashes and spaces read as underscores. Any
    other word refuses: the rungs are a closed
    vocabulary of exactly three.
    """
    if isinstance(value, str):
        wanted = value.strip().lower().replace(
            "-", "_").replace(" ", "_")
        if wanted in _RUNG_WORDS:
            return _RUNG_WORDS[wanted]
    raise ValueError(
        "a doctrine rung must be one of %s, got %r"
        % ("/".join(DOCTRINE_RUNGS), value))


def normalize_approval(value: Any) -> str:
    """The canonical approval a word names.

    Reads ``none``, ``ask_once`` (or ``ask``) and
    ``explicit_named_targets`` (or ``explicit``),
    case-insensitively. Any other word refuses:
    the approvals are a closed vocabulary.
    """
    if isinstance(value, str):
        wanted = value.strip().lower().replace(
            "-", "_").replace(" ", "_")
        if wanted in _APPROVAL_WORDS:
            return _APPROVAL_WORDS[wanted]
    raise ValueError(
        "an approval must be one of %s, got %r"
        % ("/".join(APPROVAL_REQUIREMENTS), value))


def normalize_classification(value: Any) -> str:
    """The canonical classification a word names."""
    if isinstance(value, str):
        wanted = value.strip().lower().replace(
            "-", "_").replace(" ", "_")
        if wanted in _CLASS_WORDS:
            return _CLASS_WORDS[wanted]
    raise ValueError(
        "a classification must be one of %s, got %r"
        % ("/".join(CLASSIFICATIONS), value))


def normalize_judgement_id(value: Any) -> str:
    """The canonical judgement id a word names.

    A judgement id is one word of letters,
    digits, dashes, underscores and dots, read
    with its case kept. Anything else raises.
    """
    if isinstance(value, str):
        wanted = value.strip()
        if wanted and all(ch in _ID_CHARS for ch in wanted):
            return wanted
    raise ValueError(
        f"a judgement id must be a non-empty word of letters, "
        f"digits, dashes, underscores and dots, got {value!r}")


def normalize_pattern_id(value: Any) -> str:
    """The canonical command-pattern id a word names.

    A pattern id is lowercase letters, digits
    and underscores, read case-insensitively with
    dashes and spaces as underscores. Anything
    else raises.
    """
    if isinstance(value, str):
        wanted = value.strip().lower().replace(
            "-", "_").replace(" ", "_")
        if wanted and all(
                ch in _PATTERN_ID_CHARS for ch in wanted):
            return wanted
    raise ValueError(
        f"a pattern id must be a word of lowercase letters, "
        f"digits and underscores, got {value!r}")


# ---------------------------------------------------------------------
# The ladder: the three rungs, each with the approval it needs,
# held as validated data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class DoctrineRung:
    """One rung of the ladder, as data.

    ``rung`` names the rung in the closed
    vocabulary, ``label`` says it in plain words,
    and ``approval`` is the one approval that
    rung needs. The approval is derived from the
    rung when unnamed, and a rung built naming
    any other approval refuses on construction -
    so a rung that exists never promises less
    (or more) than the doctrine asks.
    Constructing one validates it.
    """

    rung: str
    label: str = ""
    approval: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "rung", normalize_rung(self.rung))
        label = self.label
        if not isinstance(label, str):
            raise ValueError(f"a rung label must be text, got {label!r}")
        label = label.strip() or _RUNG_LABELS[self.rung]
        object.__setattr__(self, "label", label)
        wanted = _RUNG_APPROVALS[self.rung]
        if self.approval is None:
            object.__setattr__(self, "approval", wanted)
        else:
            named = normalize_approval(self.approval)
            if named != wanted:
                raise ValueError(
                    f"the {self.rung} rung needs approval "
                    f"{wanted}, not {named}")
            object.__setattr__(self, "approval", named)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "doctrine_rung",
            "slice": DESTRUCTIVE_DOCTRINE_SLICE,
            "rung": self.rung,
            "label": self.label,
            "approval": self.approval,
        }


#: The plainer word for a ladder rung.
Rung = DoctrineRung

#: The ladder itself, held as data, in roadmap
#: order: reversible, then costly, then
#: irreversible, each with its one approval.
DOCTRINE_LADDER: Tuple[DoctrineRung, ...] = tuple(
    DoctrineRung(rung=rung) for rung in DOCTRINE_RUNGS)


def rung_for(rung: Any) -> DoctrineRung:
    """The one held rung a rung word names."""
    wanted = normalize_rung(rung)
    for held in DOCTRINE_LADDER:
        if held.rung == wanted:
            return held
    raise ValueError(f"unknown doctrine rung: {wanted!r}")


def approval_for_rung(rung: Any) -> str:
    """The one approval a rung needs, in the closed vocabulary."""
    return rung_for(rung).approval


def validate_rung(rung: Any) -> DoctrineRung:
    """Validate one rung into a DoctrineRung.

    Accepts a DoctrineRung or a mapping naming a
    ``rung`` (or ``level`` / ``name``) and
    optionally a ``label`` and an ``approval``
    that must be the rung's own. Unknown keys
    refuse.
    """
    if isinstance(rung, DoctrineRung):
        return rung
    if not isinstance(rung, dict):
        raise ValueError(f"a rung must be a mapping, got {rung!r}")
    unknown = set(rung) - {"rung", "level", "name", "label", "approval"}
    if unknown:
        raise ValueError(
            "unknown rung keys: %s" % ", ".join(sorted(unknown)))
    named = _pick(rung, ("rung", "level", "name"), "rungs")
    if named is None:
        raise ValueError("a rung must name its rung")
    kwargs: Dict[str, Any] = {"rung": named}
    if "label" in rung:
        kwargs["label"] = rung["label"]
    if "approval" in rung:
        kwargs["approval"] = rung["approval"]
    return DoctrineRung(**kwargs)


def build_rung(rung: Any = None, **kwargs: Any) -> DoctrineRung:
    """Build one validated rung from a mapping or field words."""
    if isinstance(rung, DoctrineRung) and not kwargs:
        return rung
    if isinstance(rung, dict) or rung is None:
        merged: Dict[str, Any] = {}
        if isinstance(rung, dict):
            merged.update(rung)
        merged.update(kwargs)
        return validate_rung(merged)
    raise ValueError(f"a rung must be a mapping, got {rung!r}")


# ---------------------------------------------------------------------
# The patterns: what places an act on a rung, held as validated
# data, read in the order listed (the judge's precedence).
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class DestructivePattern:
    """One command shape that places an act on a rung, as data.

    ``pattern_id`` names the shape, ``rung`` is
    the rung a match earns, ``label`` says the
    shape in plain words, and ``regex`` is the
    shape itself, matched against the command
    text. ``anchor`` names the command word an
    act's targets are read after (for ``git``
    shapes the subcommand word, e.g. ``push``);
    ``implicit_target`` names, in plain words,
    the target of an act whose command names
    none - held here so an irreversible act
    always names a target from data, never from
    a guess at judge time. Constructing one
    validates it, the regex included.
    """

    pattern_id: str
    rung: str
    label: str
    regex: str
    anchor: str = ""
    implicit_target: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "pattern_id", normalize_pattern_id(self.pattern_id))
        object.__setattr__(self, "rung", normalize_rung(self.rung))
        object.__setattr__(
            self, "label", _clean_text(self.label, "a label"))
        shape = _clean_text(self.regex, "a pattern")
        try:
            re.compile(shape, re.IGNORECASE)
        except re.error as exc:
            raise ValueError(
                f"a pattern must be a valid regex: {exc}") from None
        object.__setattr__(self, "regex", shape)
        for field_name in ("anchor", "implicit_target"):
            value = getattr(self, field_name)
            if not isinstance(value, str):
                raise ValueError(
                    f"a pattern {field_name} must be text, "
                    f"got {value!r}")
            object.__setattr__(self, field_name, value.strip())

    def matches(self, command_text: str) -> Optional[re.Match]:
        """This shape's match in a command text, or None."""
        return re.search(self.regex, command_text, re.IGNORECASE)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "destructive_pattern",
            "slice": DESTRUCTIVE_DOCTRINE_SLICE,
            "pattern_id": self.pattern_id,
            "rung": self.rung,
            "label": self.label,
            "anchor": self.anchor,
            "implicit_target": self.implicit_target,
        }


_PATTERN_KEYS = frozenset({
    "pattern_id", "id", "name", "rung", "level",
    "label", "regex", "pattern", "anchor", "implicit_target",
})


def validate_pattern(pattern: Any) -> DestructivePattern:
    """Validate one command pattern into a DestructivePattern.

    Accepts a DestructivePattern or a mapping
    naming a ``pattern_id`` (or ``id`` / ``name``),
    a ``rung`` (or ``level``), a ``label`` and a
    ``regex`` (or ``pattern``), and optionally an
    ``anchor`` and an ``implicit_target``. Naming
    two spellings of one field with different
    values refuses, and unknown keys refuse.
    """
    if isinstance(pattern, DestructivePattern):
        return pattern
    if not isinstance(pattern, dict):
        raise ValueError(
            f"a command pattern must be a mapping, got {pattern!r}")
    unknown = set(pattern) - _PATTERN_KEYS
    if unknown:
        raise ValueError(
            "unknown pattern keys: %s" % ", ".join(sorted(unknown)))
    pattern_id = _pick(pattern, ("pattern_id", "id", "name"), "pattern ids")
    rung = _pick(pattern, ("rung", "level"), "rungs")
    regex = _pick(pattern, ("regex", "pattern"), "patterns")
    if pattern_id is None or rung is None \
            or "label" not in pattern or regex is None:
        raise ValueError(
            "a command pattern must name its pattern_id, rung, "
            "label and regex")
    kwargs: Dict[str, Any] = {
        "pattern_id": pattern_id, "rung": rung,
        "label": pattern["label"], "regex": regex}
    for field_name in ("anchor", "implicit_target"):
        if field_name in pattern:
            kwargs[field_name] = pattern[field_name]
    return DestructivePattern(**kwargs)


def build_pattern(pattern: Any = None, **kwargs: Any) -> DestructivePattern:
    """Build one validated pattern from a mapping or field words."""
    if isinstance(pattern, DestructivePattern) and not kwargs:
        return pattern
    if isinstance(pattern, dict) or pattern is None:
        merged: Dict[str, Any] = {}
        if isinstance(pattern, dict):
            merged.update(pattern)
        merged.update(kwargs)
        return validate_pattern(merged)
    raise ValueError(
        f"a command pattern must be a mapping, got {pattern!r}")


def pattern_for_id(pattern_id: Any) -> DestructivePattern:
    """The one held pattern a pattern id names."""
    wanted = normalize_pattern_id(pattern_id)
    for pattern in COMMAND_PATTERNS:
        if pattern.pattern_id == wanted:
            return pattern
    raise ValueError(f"unknown command pattern: {wanted!r}")


#: Every held command shape, as data, in the
#: order the judge reads them: the dry-run
#: reading first (a command that declares it
#: will change nothing), then the irreversible
#: shapes, then the costly shapes, then the
#: reversible readings - so an act matching two
#: rungs earns the worse one. The irreversible
#: and costly shapes widen the shipped sandbox
#: denylist's shapes; this layer classifies
#: where that road refuses.
COMMAND_PATTERNS: Tuple[DestructivePattern, ...] = (
    DestructivePattern(
        pattern_id="dry_run", rung="reversible",
        label="dry run (the command declares it changes nothing)",
        regex=r"--dry-run\b|\bgit\b[^;&|]*\b(clean|push)\b[^;&|]*\s-n\b"),
    DestructivePattern(
        pattern_id="rm_force_recursive", rung="irreversible",
        label="recursive force deletion (the rm -rf class)",
        regex=(r"\brm\b[^;&|]*(-[a-z]*r[a-z]*f|-[a-z]*f[a-z]*r"
               r"|--recursive\b[^;&|]*--force\b"
               r"|--force\b[^;&|]*--recursive\b"
               r"|-[a-z]*r\b[^;&|]*-[a-z]*f\b"
               r"|-[a-z]*r\b[^;&|]*--force\b"
               r"|--recursive\b[^;&|]*-[a-z]*f\b)"),
        anchor="rm"),
    DestructivePattern(
        pattern_id="disk_format", rung="irreversible",
        label="filesystem creation (mkfs)",
        regex=r"\b(mkfs(\.[a-z0-9]+)?|mke2fs|mkswap)\b",
        anchor="mkfs", implicit_target="the named device"),
    DestructivePattern(
        pattern_id="disk_wipe", rung="irreversible",
        label="disk-wiping utility (shred / wipefs / blkdiscard)",
        regex=r"\b(shred|wipefs|blkdiscard)\b",
        implicit_target="the named file or device"),
    DestructivePattern(
        pattern_id="dd_device_write", rung="irreversible",
        label="raw device write (dd of=/dev/...)",
        regex=r"\bdd\b[^;&|]*\bof\s*=\s*/dev/\S+",
        anchor="dd"),
    DestructivePattern(
        pattern_id="device_overwrite", rung="irreversible",
        label="raw block-device overwrite by redirection",
        regex=r">>?\s*/dev/(sd[a-z]|hd[a-z]|nvme\d|mmcblk\d)\S*"),
    DestructivePattern(
        pattern_id="sql_drop", rung="irreversible",
        label="dropping or truncating a database object",
        regex=(r"\b(drop\s+(table|database|schema)"
               r"|truncate\s+table)\b"),
        implicit_target="the named database object"),
    DestructivePattern(
        pattern_id="git_force_push", rung="irreversible",
        label="force push (rewrites shared remote history)",
        regex=(r"\bgit\b[^;&|]*\bpush\b[^;&|]*"
               r"(--force-with-lease|--force|\s-[a-z]*f\b)"),
        anchor="push",
        implicit_target="the current branch on its remote"),
    DestructivePattern(
        pattern_id="git_hard_reset", rung="irreversible",
        label="hard reset (discards uncommitted work)",
        regex=r"\bgit\b[^;&|]*\breset\b[^;&|]*--hard\b",
        anchor="reset",
        implicit_target="uncommitted work in the working tree"),
    DestructivePattern(
        pattern_id="git_clean_force", rung="irreversible",
        label="forced clean (deletes untracked files)",
        regex=r"\bgit\b[^;&|]*\bclean\b[^;&|]*-[a-z]*f",
        anchor="clean",
        implicit_target="untracked files in the working tree"),
    DestructivePattern(
        pattern_id="fork_bomb", rung="irreversible",
        label="fork bomb",
        regex=r":\s*\(\s*\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;",
        implicit_target="every process on this machine"),
    DestructivePattern(
        pattern_id="rm_delete", rung="costly",
        label="file deletion (rm)",
        regex=r"\brm\b", anchor="rm"),
    DestructivePattern(
        pattern_id="redirect_overwrite", rung="costly",
        label="overwriting a file by redirection",
        regex=r"(?<!>)>(?!>)\s*(?!/dev/null\b)(\S+)"),
    DestructivePattern(
        pattern_id="git_push", rung="costly",
        label="push (publishes history to a remote)",
        regex=r"\bgit\b[^;&|]*\bpush\b", anchor="push"),
    DestructivePattern(
        pattern_id="git_reset", rung="costly",
        label="reset (moves committed history)",
        regex=r"\bgit\b[^;&|]*\breset\b", anchor="reset"),
    DestructivePattern(
        pattern_id="git_checkout_discard", rung="costly",
        label="checkout or restore discarding file changes",
        regex=(r"\bgit\b[^;&|]*\brestore\b"
               r"|\bgit\b[^;&|]*\bcheckout\b[^;&|]*\s--(\s|$)"),
        anchor="checkout"),
    DestructivePattern(
        pattern_id="git_branch_delete", rung="costly",
        label="branch deletion",
        regex=(r"\bgit\b[^;&|]*\bbranch\b[^;&|]*"
               r"(-d\b|-D\b|--delete\b)"),
        anchor="branch"),
    DestructivePattern(
        pattern_id="mv_overwrite", rung="costly",
        label="move or rename (may overwrite the destination)",
        regex=r"\bmv\b", anchor="mv"),
    DestructivePattern(
        pattern_id="recursive_chmod_chown", rung="costly",
        label="recursive permission or ownership change",
        regex=r"\b(chmod|chown)\b[^;&|]*(-R\b|--recursive\b)",
        anchor="chmod"),
    DestructivePattern(
        pattern_id="kill_process", rung="costly",
        label="stopping a running process",
        regex=r"\b(kill|killall|pkill)\b", anchor="kill"),
    DestructivePattern(
        pattern_id="pipe_to_shell", rung="costly",
        label="piping into a shell (runs what it is fed)",
        regex=r"\|\s*(sudo\s+)?(sh|bash|zsh)\b",
        implicit_target="this machine (whatever the pipe feeds it)"),
    DestructivePattern(
        pattern_id="shutdown_reboot", rung="costly",
        label="system shutdown or reboot",
        regex=r"\b(shutdown|reboot|poweroff)\b",
        implicit_target="the whole machine"),
    DestructivePattern(
        pattern_id="truncate_file", rung="costly",
        label="truncating a file",
        regex=r"\btruncate\b", anchor="truncate"),
    DestructivePattern(
        pattern_id="find_delete", rung="costly",
        label="find with -delete (deletes what it finds)",
        regex=r"\bfind\b[^;&|]*-delete\b", anchor="find"),
    DestructivePattern(
        pattern_id="read_only_command", rung="reversible",
        label="read-only command (looks, changes nothing)",
        regex=(r"^\s*(ls|pwd|cat|head|tail|grep|egrep|fgrep|rg"
               r"|echo|printf|wc|which|type|printenv|date|whoami"
               r"|hostname|df|du|stat|file)\b")),
    DestructivePattern(
        pattern_id="find_read", rung="reversible",
        label="find (searching only)",
        regex=r"^\s*find\b", anchor="find"),
    DestructivePattern(
        pattern_id="git_read_only", rung="reversible",
        label="git reading (status, log, diff, show and kin)",
        regex=(r"^\s*git\b[^;&|]*\b(status|log|diff|show|blame"
               r"|rev-parse|ls-files)\b")),
    DestructivePattern(
        pattern_id="git_switch", rung="reversible",
        label="switching branches (the old branch stays)",
        regex=r"^\s*git\b[^;&|]*\b(switch|checkout)\b",
        anchor="switch"),
    DestructivePattern(
        pattern_id="create_path", rung="reversible",
        label="creating an empty file or directory",
        regex=r"^\s*(mkdir|touch)\b"),
)


# ---------------------------------------------------------------------
# The judgement: one command judged, the verdict as data.
# ---------------------------------------------------------------------

_SEPARATORS = frozenset({";", "&", "|", "&&", "||"})


def _tokens(text: str) -> Tuple[str, ...]:
    """A command text as argv words (shlex; whitespace fallback)."""
    try:
        return tuple(shlex.split(text))
    except ValueError:
        return tuple(text.split())


def _clean_targets(values: Any) -> Tuple[str, ...]:
    """Named targets as a validated, deduplicated tuple."""
    if values is None:
        return ()
    if isinstance(values, str):
        values = (values,)
    if isinstance(values, (str, bytes)) \
            or not isinstance(values, (list, tuple)):
        raise ValueError(
            f"named targets must be a list of target words, "
            f"got {values!r}")
    cleaned = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"a named target must be non-empty text, "
                f"got {value!r}")
        word = value.strip()
        if word not in cleaned:
            cleaned.append(word)
    return tuple(cleaned)


def _clean_argv(values: Any, command: str) -> Tuple[str, ...]:
    """Argv words as data: validated, or read from the command."""
    if values is None:
        return _tokens(command)
    if isinstance(values, (str, bytes)) \
            or not isinstance(values, (list, tuple)):
        raise ValueError(f"argv must be a list of words, got {values!r}")
    cleaned = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"an argv word must be non-empty text, got {value!r}")
        cleaned.append(value.strip())
    return tuple(cleaned)


def _operands_after(argv: Tuple[str, ...], start: int) -> Tuple[str, ...]:
    """Operand words after an index: no flags, no separators.

    Reading stops at the first shell separator,
    skips flag words and the word a ``>`` / ``>>``
    / ``<`` operator names (a redirection is
    judged by its own shape), and skips a flag's
    separate value only where the flag is one
    this layer does not model - it does not:
    every non-flag word rides as a named target,
    which for a plain-words naming is the safe
    direction.
    """
    operands = []
    index = start
    while index < len(argv):
        word = argv[index]
        if word in _SEPARATORS:
            break
        if word in (">", ">>", "<"):
            index += 2
            continue
        if word.startswith(">") or word.startswith("<"):
            index += 1
            continue
        if not word.startswith("-") or word == "-":
            operands.append(word)
        index += 1
    return tuple(operands)


def _extract_targets(pattern: DestructivePattern,
                     match: re.Match, text: str,
                     argv: Tuple[str, ...]) -> Tuple[str, ...]:
    """The targets one matched act names, in plain words.

    Read mechanically per shape: a redirection
    names its file; a ``dd`` names its ``of=``
    device; a drop names its database object;
    every other shape names the operands after
    its anchor word (for ``git`` shapes, after
    the subcommand). When no operand is named
    and the pattern holds an implicit target,
    that held phrase is the name.
    """
    if pattern.pattern_id == "redirect_overwrite" \
            or pattern.pattern_id == "device_overwrite":
        named = match.group(match.lastindex) if match.lastindex else None
        if named:
            return (named.strip(),)
        return ()
    if pattern.pattern_id == "dd_device_write":
        found = re.search(r"\bof\s*=\s*(\S+)", text, re.IGNORECASE)
        return (found.group(1),) if found else ()
    if pattern.pattern_id == "sql_drop":
        found = re.search(
            r"\b(?:drop\s+(?:table|database|schema)"
            r"|truncate\s+table)\s+(?:if\s+exists\s+)?"
            r"([A-Za-z0-9_.$`\"']+)", text, re.IGNORECASE)
        if found:
            return (found.group(1).strip("`\"'"),)
        return (pattern.implicit_target,) if pattern.implicit_target else ()
    start = None
    if pattern.anchor:
        for index, word in enumerate(argv):
            if word == pattern.anchor \
                    or word.rsplit("/", 1)[-1] == pattern.anchor:
                start = index + 1
                break
    if start is None:
        start = 1
        if len(argv) > 1 and argv[0].rsplit("/", 1)[-1] == "git":
            start = 2
    operands = _operands_after(argv, start)
    if operands:
        return operands
    if pattern.implicit_target:
        return (pattern.implicit_target,)
    return ()


@dataclass(frozen=True)
class DestructiveJudgement:
    """One command judged against the ladder, as data.

    ``command`` is the command text and ``argv``
    its words as data. A classified judgement
    names its ``rung`` and the held ``pattern_id``
    that placed it there, and carries that rung's
    one ``approval``; an unclassified judgement
    names no rung and no pattern, and carries the
    ask-once approval - it is never claimed safe.
    ``targets`` names, in plain words, what the
    act acts on; a judgement on the irreversible
    rung refuses to exist without at least one
    named target. The rung, classification,
    pattern and approval are validated against
    each other on construction, so a judgement
    that exists never disagrees with itself.
    Constructing one validates it.
    """

    command: str
    argv: Tuple[str, ...] = ()
    rung: Optional[str] = None
    approval: Optional[str] = None
    classification: Optional[str] = None
    pattern_id: Optional[str] = None
    targets: Tuple[str, ...] = ()
    judgement_id: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "command",
            _clean_text(self.command, "a command"))
        object.__setattr__(
            self, "argv", _clean_argv(self.argv or None, self.command))
        object.__setattr__(self, "targets", _clean_targets(self.targets))
        if self.rung is None:
            rung = None
        else:
            rung = normalize_rung(self.rung)
        object.__setattr__(self, "rung", rung)
        if self.pattern_id is None:
            pattern_id = None
        else:
            pattern_id = normalize_pattern_id(self.pattern_id)
        object.__setattr__(self, "pattern_id", pattern_id)
        if rung is None and pattern_id is not None:
            raise ValueError(
                "an unclassified judgement names no pattern")
        if rung is not None:
            if pattern_id is None:
                raise ValueError(
                    "a classified judgement must name the pattern "
                    "that placed it")
            held = pattern_for_id(pattern_id)
            if held.rung != rung:
                raise ValueError(
                    f"pattern {pattern_id} places an act on the "
                    f"{held.rung} rung, not {rung}")
        derived_class = "unclassified" if rung is None else "classified"
        if self.classification is None:
            object.__setattr__(self, "classification", derived_class)
        else:
            named_class = normalize_classification(self.classification)
            if named_class != derived_class:
                raise ValueError(
                    f"a judgement with rung {rung!r} is "
                    f"{derived_class}, not {named_class}")
            object.__setattr__(self, "classification", named_class)
        wanted_approval = _RUNG_APPROVALS[rung] if rung is not None \
            else _UNCLASSIFIED_APPROVAL
        if self.approval is None:
            object.__setattr__(self, "approval", wanted_approval)
        else:
            named_approval = normalize_approval(self.approval)
            if named_approval != wanted_approval:
                raise ValueError(
                    f"a judgement on rung {rung!r} needs approval "
                    f"{wanted_approval}, not {named_approval}")
            object.__setattr__(self, "approval", named_approval)
        if rung == "irreversible" and not self.targets:
            raise ValueError(
                "an irreversible act must name its targets in "
                "plain words first: a judgement on the "
                "irreversible rung refuses to exist without at "
                "least one named target")
        if self.judgement_id is not None:
            object.__setattr__(
                self, "judgement_id",
                normalize_judgement_id(self.judgement_id))

    @property
    def classified(self) -> bool:
        return self.classification == "classified"

    @property
    def needs_approval(self) -> bool:
        return self.approval != "none"

    @property
    def targets_phrase(self) -> str:
        """The named targets, as one plain-words phrase."""
        if not self.targets:
            return "no named target"
        return ", ".join(self.targets)

    @property
    def display_label(self) -> str:
        name = self.judgement_id or "judgement"
        rung = self.rung or "unclassified"
        return f"{name} ({self.command}: {rung})"

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "destructive_judgement",
            "slice": DESTRUCTIVE_DOCTRINE_SLICE,
            "judgement_id": self.judgement_id,
            "command": self.command,
            "argv": list(self.argv),
            "rung": self.rung,
            "classification": self.classification,
            "pattern_id": self.pattern_id,
            "approval": self.approval,
            "targets": list(self.targets),
        }


#: The shorter word for a destructive judgement.
Judgement = DestructiveJudgement

_JUDGEMENT_KEYS = frozenset({
    "judgement_id", "id", "command", "cmd", "argv", "args",
    "rung", "level", "approval", "classification", "class",
    "pattern_id", "pattern", "targets", "target",
})


def validate_judgement(judgement: Any) -> DestructiveJudgement:
    """Validate one judgement into a DestructiveJudgement.

    Accepts a DestructiveJudgement or a mapping
    naming a ``command`` (or ``cmd``) - required -
    and optionally ``argv`` (or ``args``), a
    ``rung`` (or ``level``), an ``approval``, a
    ``classification`` (or ``class``), a
    ``pattern_id`` (or ``pattern``), ``targets``
    (or ``target``) and a ``judgement_id`` (or
    ``id``). Naming two spellings of one field
    with different values refuses, and unknown
    keys refuse.
    """
    if isinstance(judgement, DestructiveJudgement):
        return judgement
    if not isinstance(judgement, dict):
        raise ValueError(
            f"a judgement must be a mapping, got {judgement!r}")
    unknown = set(judgement) - _JUDGEMENT_KEYS
    if unknown:
        raise ValueError(
            "unknown judgement keys: %s" % ", ".join(sorted(unknown)))
    command = _pick(judgement, ("command", "cmd"), "commands")
    if command is None:
        raise ValueError("a judgement must name its command")
    kwargs: Dict[str, Any] = {"command": command}
    for field_name, spellings in (
            ("argv", ("argv", "args")),
            ("rung", ("rung", "level")),
            ("approval", ("approval",)),
            ("classification", ("classification", "class")),
            ("pattern_id", ("pattern_id", "pattern")),
            ("targets", ("targets", "target")),
            ("judgement_id", ("judgement_id", "id"))):
        value = _pick(judgement, spellings, field_name)
        if value is not None:
            kwargs[field_name] = value
    return DestructiveJudgement(**kwargs)


def build_judgement(judgement: Any = None,
                    **kwargs: Any) -> DestructiveJudgement:
    """Build one validated judgement from a mapping or field words."""
    if isinstance(judgement, DestructiveJudgement) and not kwargs:
        return judgement
    if isinstance(judgement, dict) or judgement is None:
        merged: Dict[str, Any] = {}
        if isinstance(judgement, dict):
            merged.update(judgement)
        merged.update(kwargs)
        return validate_judgement(merged)
    raise ValueError(
        f"a judgement must be a mapping, got {judgement!r}")


def _require_judgement(judgement: Any) -> DestructiveJudgement:
    if isinstance(judgement, DestructiveJudgement):
        return judgement
    return validate_judgement(judgement)


# ---------------------------------------------------------------------
# The judge: one command read against the held patterns alone.
# ---------------------------------------------------------------------


def judge_command(command: Any, argv: Any = None) -> DestructiveJudgement:
    """Judge one command against the ladder, mechanically.

    ``command`` is the command text, or its argv
    words as a list (then the text is the words
    joined); ``argv``, when named, is the argv as
    data the reading is taken from. The held
    patterns are read in their held order -
    dry-run first, then irreversible, costly,
    reversible - and the first match places the
    act. A command no pattern matches is judged
    unclassified: no rung, no pattern, and the
    ask-once approval, because this layer will
    not claim an unknown command safe. An empty
    command refuses.
    """
    if isinstance(command, (list, tuple)):
        words = _clean_argv(command, "")
        if not words:
            raise ValueError("a command must be a non-empty string")
        text = " ".join(words)
        argv_words = words
    elif isinstance(command, str):
        text = _clean_text(command, "a command")
        argv_words = _clean_argv(argv, text) if argv is not None \
            else _tokens(text)
    else:
        raise ValueError(
            f"a command must be text or argv words, got {command!r}")
    for pattern in COMMAND_PATTERNS:
        match = pattern.matches(text)
        if match is None:
            continue
        return DestructiveJudgement(
            command=text, argv=argv_words, rung=pattern.rung,
            pattern_id=pattern.pattern_id,
            targets=_extract_targets(pattern, match, text, argv_words))
    return DestructiveJudgement(
        command=text, argv=argv_words,
        targets=_operands_after(argv_words, 1))


def plain_words(judgement: Any) -> str:
    """One judged act, in plain words - its targets named first.

    For an irreversible act the sentence names
    every target and says the act cannot be
    undone, before it names anything else: that
    naming is the roadmap's rule, as code. An
    unclassified act is stated plainly as not
    classified and not claimed safe.
    """
    checked = _require_judgement(judgement)
    if checked.rung == "irreversible":
        return (
            f"This cannot be undone: {checked.command} "
            f"permanently affects {checked.targets_phrase}. "
            f"It needs explicit approval naming every "
            f"target first.")
    if checked.rung == "costly":
        return (
            f"This has a cost: {checked.command} affects "
            f"{checked.targets_phrase}; undoing it takes "
            f"work or a restore. It asks once before "
            f"it runs.")
    if checked.rung == "reversible":
        return (
            f"This can be undone: {checked.command}. "
            f"No approval is needed.")
    return (
        f"This command is not classified: {checked.command}. "
        f"It is not claimed safe, and it needs approval "
        f"(ask once) before it runs.")


# ---------------------------------------------------------------------
# The news record: one judged act, shaped as session news.
# ---------------------------------------------------------------------


def doctrine_record(judgement: Any) -> Dict[str, Any]:
    """The session-news record of one judged act.

    Every judged act yields a record - the agent
    layer publishes this record as a session
    event, so a destructive act is announced
    with its targets named in plain words in its
    headline, never lost as a mere log line. The
    record names the command, its rung (None
    when unclassified), the approval it needs
    and its named targets - and the command text
    itself, which is the act being announced,
    never a secret it may carry.
    """
    checked = _require_judgement(judgement)
    return {
        "type": "destructive_act",
        "news": True,
        "slice": DESTRUCTIVE_DOCTRINE_SLICE,
        "judgement_id": checked.judgement_id,
        "command": checked.command,
        "argv": list(checked.argv),
        "rung": checked.rung,
        "classification": checked.classification,
        "pattern_id": checked.pattern_id,
        "approval": checked.approval,
        "targets": list(checked.targets),
        "headline": plain_words(checked),
    }


# ---------------------------------------------------------------------
# The registry model: judgements held for a session, ids
# deterministic.
# ---------------------------------------------------------------------


class DoctrineRegistry:
    """An in-memory, storage-neutral registry of judgements.

    Judgements are held in the order judged. Ids
    are deterministic: a caller-supplied id is
    used as given (a duplicate refuses), and an
    unsupplied id is the next ``judgement-N`` in
    sequence, skipping any number a supplied id
    already took - no randomness a test cannot
    pin. Storage beyond memory is the agent
    layer's concern; this model is neutral.
    """

    def __init__(self) -> None:
        self._judgements: Dict[str, DestructiveJudgement] = {}
        self._next = 1

    def _fresh_id(self) -> str:
        while f"judgement-{self._next}" in self._judgements:
            self._next += 1
        judgement_id = f"judgement-{self._next}"
        self._next += 1
        return judgement_id

    def register(self, judgement: Any = None,
                 **kwargs: Any) -> DestructiveJudgement:
        """Hold one judgement, under its id or a fresh one."""
        if kwargs and isinstance(
                judgement, (DestructiveJudgement, dict)):
            validated = build_judgement(judgement, **kwargs)
        elif kwargs and judgement is None:
            validated = build_judgement(**kwargs)
        else:
            if kwargs:
                raise ValueError(
                    "a judgement is named twice: as a record "
                    "and as field words")
            validated = _require_judgement(judgement)
        if validated.judgement_id is None:
            validated = replace(
                validated, judgement_id=self._fresh_id())
        elif validated.judgement_id in self._judgements:
            raise ValueError(
                f"a judgement named {validated.judgement_id!r} "
                f"already exists")
        self._judgements[validated.judgement_id] = validated
        return validated

    def judge(self, command: Any, argv: Any = None) -> DestructiveJudgement:
        """Judge one command and hold its judgement."""
        return self.register(judge_command(command, argv))

    def get(self, judgement_id: Any) -> DestructiveJudgement:
        """The judgement one id names; an unknown id raises KeyError."""
        wanted = normalize_judgement_id(judgement_id)
        if wanted not in self._judgements:
            raise KeyError(f"unknown judgement: {wanted!r}")
        return self._judgements[wanted]

    def list_judgements(self) -> Tuple[DestructiveJudgement, ...]:
        """Every held judgement, in the order judged, as a tuple."""
        return tuple(self._judgements.values())

    def __len__(self) -> int:
        return len(self._judgements)

    def record(self, judgement_id: Any) -> Dict[str, Any]:
        """One held judgement's session-news record."""
        return doctrine_record(self.get(judgement_id))


# ---------------------------------------------------------------------
# The /doctrine surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------


def format_rung(rung: Any) -> str:
    """One ladder rung, in plain words: rung, label and approval."""
    current = rung if isinstance(rung, DoctrineRung) else rung_for(rung)
    return (
        f"{current.rung}: {current.label} - approval: "
        f"{APPROVAL_PHRASES[current.approval]}.")


def format_ladder() -> str:
    """The whole ladder, in plain words, in roadmap order."""
    lines = [f"Destructive-command ladder: {len(DOCTRINE_LADDER)} rungs."]
    for rung in DOCTRINE_LADDER:
        lines.append(f"  {format_rung(rung)}")
    return "\n".join(lines)


def format_pattern(pattern: Any) -> str:
    """One command pattern, in plain words: shape and its rung."""
    current = pattern if isinstance(pattern, DestructivePattern) \
        else pattern_for_id(pattern)
    return f"{current.pattern_id}: {current.label} ({current.rung})."


def format_patterns() -> str:
    """Every held command shape, in plain words, in held order."""
    lines = [f"Command patterns: {len(COMMAND_PATTERNS)} known."]
    for pattern in COMMAND_PATTERNS:
        lines.append(f"  {format_pattern(pattern)}")
    return "\n".join(lines)


def format_judgement(judgement: Any) -> str:
    """One judgement, in plain words: rung and approval stated."""
    current = _require_judgement(judgement)
    name = current.judgement_id or "judgement"
    if not current.classified:
        return (
            f"{name}: {current.command} - not classified; "
            f"not claimed safe; approval: "
            f"{APPROVAL_PHRASES[current.approval]}; targets: "
            f"{current.targets_phrase}.")
    return (
        f"{name}: {current.command} - {current.rung}; "
        f"approval: {APPROVAL_PHRASES[current.approval]}; "
        f"targets: {current.targets_phrase}.")


def _judgements_from(source: Any) -> Tuple[DestructiveJudgement, ...]:
    """The judgements a source holds, in the order judged.

    A source is a DoctrineRegistry, a list of
    judgements (or judgement mappings), one
    judgement, or nothing at all.
    """
    if source is None:
        return ()
    if isinstance(source, DoctrineRegistry):
        return source.list_judgements()
    if isinstance(source, (DestructiveJudgement, dict)):
        return (_require_judgement(source),)
    if isinstance(source, (list, tuple)):
        return tuple(_require_judgement(item) for item in source)
    raise ValueError(
        "doctrine judgements must be a registry or a list "
        "of judgements")


def format_judgements(source: Any = None) -> str:
    """The held judgements, in plain words, in the order judged.

    With no judgements at all the text starts
    with the plain statement of that fact. Every
    line states its judgement's rung and approval
    in words.
    """
    judgements = _judgements_from(source)
    if not judgements:
        return (
            "Destructive-command doctrine: no commands "
            "judged. No judgement is held.")
    lines = [
        f"Destructive-command doctrine: {len(judgements)} judged."]
    for judgement in judgements:
        lines.append(f"  {format_judgement(judgement)}")
    return "\n".join(lines)


def format_doctrine_record(record: Any) -> str:
    """One destructive-act news record as its plain headline."""
    if isinstance(record, dict) \
            and record.get("type") == "destructive_act":
        return str(record["headline"])
    raise ValueError("format_doctrine_record needs a doctrine record")


#: The doctrine record's formatter under its own name.
format_record = format_doctrine_record


def format_doctrine_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /doctrine."""
    lines = [
        "Destructive-command doctrine (M-111) - "
        + PLAIN_EXPLANATION, ""]
    lines.append(format_ladder())
    lines.append("")
    lines.append(format_patterns())
    lines.append("")
    lines.append(format_judgements(source))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


_GRAMMAR_WORDS = ("show", "check", "ladder")


def parse_doctrine_args(args: Any) -> Tuple[str, Optional[str]]:
    """Parse the /doctrine grammar both surfaces share.

    No words (or ``show``) shows the judgements;
    ``show <judgement>`` and a bare judgement id
    show one judgement; ``ladder`` shows the
    ladder alone; ``check <command>`` judges one
    command - everything after ``check`` is the
    command, however many words it takes. A
    grammar word in the wrong shape - a bare rung
    word, a bare pattern id, ``check`` with no
    command - is a usage error naming the
    grammar, never a judgement id. Returns
    ``(action, target-or-None)``: for ``show``
    the target is a judgement id, for ``check``
    it is the command text to judge.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None \
        else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() == "show":
        return ("show", None)
    if text.lower() == "ladder":
        return ("ladder", None)
    words = text.split()
    head = words[0].lower()
    if head == "check":
        rest = text.split(None, 1)
        if len(rest) == 2 and rest[1].strip():
            return ("check", rest[1].strip())
        raise ValueError(USAGE)
    if head == "show" and len(words) == 2:
        if words[1].lower() in _GRAMMAR_WORDS:
            raise ValueError(USAGE)
        try:
            return ("show", normalize_judgement_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head in _GRAMMAR_WORDS or len(words) != 1:
        raise ValueError(USAGE)
    lowered = words[0].lower().replace("-", "_")
    if lowered in _RUNG_WORDS or lowered in {
            pattern.pattern_id for pattern in COMMAND_PATTERNS}:
        raise ValueError(USAGE)
    try:
        return ("show", normalize_judgement_id(words[0]))
    except ValueError:
        raise ValueError(USAGE) from None
