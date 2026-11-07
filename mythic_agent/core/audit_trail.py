"""Audit trail - every act in the journal, append-only (M-109).

Part V - Autonomy & Safety. The roadmap's words:
``every tool call, approval, edit, and command in
the journal with actor (human/coder/crew/hook) -
exportable for review; the trail is append-only.``

What already shipped, and what this slice adds:

* The tree already keeps an append-only JSONL
  audit file (``mythic_agent/core/audit.py``: an
  ``AuditLog`` writing one JSON object per line
  under the workspace) and a write-ahead journal
  for session checkpoints
  (``mythic_agent/core/journal.py``). Neither
  holds the trail as validated session data: no
  closed vocabulary of what kind of act was
  recorded, no closed vocabulary of who acted,
  no registry a session can hold and read back,
  and no export shaped for review.
* This slice is that missing trail, as a pure
  layer in the exact sibling shape: an audit
  entry (its kind - a tool call, an approval, an
  edit or a command - its actor - a human, the
  coder, the crew or a hook - what happened, in
  words, and optionally the target it touched
  and a detail) validated as data, a record of
  one entry shaped as session news, an export
  that renders the whole trail for review as
  plain data, and a small in-memory registry
  model with deterministic ids. This module
  writes no file, appends to no journal and
  changes no setting; the agent layer owns
  holding the registry for a session, feeding it
  entries from the real roads as acts happen,
  and carrying the export out to a reviewer.

Honesty rules, enforced here and pinned by tests:

* **The vocabularies are closed.** An entry's
  kind is one of the four roadmap kinds and its
  actor one of the four roadmap actors. Any
  other word refuses plainly instead of being
  guessed at, so the trail never describes an
  act in a dialect review cannot read.
* **The trail is append-only.** An entry, once
  recorded, is never changed: entries are frozen
  data, the registry offers no edit, removal,
  clearing or reordering road at all, and
  recording an entry under an id the trail
  already holds refuses - a rewrite of history
  is an error, never a silent success. The
  order entries are read back in is the order
  they were appended, forever.
* **The export is complete.** An export names
  every held entry, in append order, with the
  counts by kind and by actor counted from the
  entries themselves - nothing held is left out
  and nothing is summarised away.
* **A recorded entry is news.** Every entry
  yields one record shaped as session news,
  stating its kind and actor in plain words, so
  a recorded act can never be lost as a mere
  log line.
* **Status is never carried by colour or symbol
  alone.** Every formatter states an entry's
  kind and actor in words.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Dict, Optional, Tuple

__all__ = [
    "AUDIT_ACTORS",
    "AUDIT_KINDS",
    "AUDIT_TRAIL_SLICE",
    "PLAIN_EXPLANATION",
    "USAGE",
    "AuditEntry",
    "AuditRegistry",
    "Entry",
    "audit_record",
    "build_entry",
    "export_trail",
    "format_audit_record",
    "format_audit_screen",
    "format_entries",
    "format_entry",
    "format_export",
    "format_record",
    "normalize_audit_actor",
    "normalize_audit_id",
    "normalize_audit_kind",
    "parse_audit_args",
    "validate_entry",
]

AUDIT_TRAIL_SLICE = "M-109"

#: The audit entry kinds, in roadmap order: every
#: tool call, approval, edit and command.
AUDIT_KINDS = ("tool_call", "approval", "edit", "command")

#: The actors an entry may be stamped with, in
#: roadmap order: the human, the coder itself,
#: its crew, and a hook.
AUDIT_ACTORS = ("human", "coder", "crew", "hook")

PLAIN_EXPLANATION = (
    "The audit trail records every tool call, "
    "approval, edit and command in the journal, "
    "each stamped with its actor - the human, "
    "the coder, the crew or a hook. The trail is "
    "append-only: an entry, once recorded, is "
    "never changed or removed, and the export "
    "for review names every recorded entry in "
    "the order it was appended. This layer holds "
    "entries as data only; it writes no file and "
    "appends to no journal itself - the agent "
    "layer feeds it entries from the real roads "
    "and carries the export out to a reviewer."
)

USAGE = (
    "Usage: /audit, /audit show, "
    "/audit show <entry>, /audit export"
)

_ENTRY_KEYS = frozenset({
    "entry_id", "id", "kind", "type", "category",
    "actor", "by", "who",
    "summary", "what", "description",
    "detail", "details", "target", "subject",
})

_KIND_WORDS = {
    "tool_call": "tool_call", "toolcall": "tool_call",
    "tool": "tool_call",
    "approval": "approval", "approve": "approval",
    "edit": "edit", "edits": "edit", "file_edit": "edit",
    "command": "command", "cmd": "command", "shell": "command",
}

_ACTOR_WORDS = {
    "human": "human", "user": "human", "person": "human",
    "coder": "coder", "agent": "coder",
    "crew": "crew", "fleet": "crew",
    "hook": "hook", "hooks": "hook",
}

_KIND_LABELS = {
    "tool_call": "tool call",
    "approval": "approval",
    "edit": "edit",
    "command": "command",
}

_ENTRY_ID_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789-_.")


def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _loose_text(value: Any, what: str) -> str:
    """An optional text field: text, stripped; anything else refuses."""
    if not isinstance(value, str):
        raise ValueError(f"{what} must be text, got {value!r}")
    return value.strip()


def normalize_audit_id(value: Any) -> str:
    """The canonical audit entry id a word names.

    An entry id is one word of letters, digits,
    dashes, underscores and dots, read with its
    case kept. Anything else raises.
    """
    if isinstance(value, str):
        wanted = value.strip()
        if wanted and all(ch in _ENTRY_ID_CHARS for ch in wanted):
            return wanted
    raise ValueError(
        f"an audit entry id must be a non-empty word of letters, "
        f"digits, dashes, underscores and dots, got {value!r}")


def normalize_audit_kind(value: Any) -> str:
    """The canonical audit kind a word names.

    Reads ``tool_call`` (or ``tool``), ``approval``
    (or ``approve``), ``edit`` and ``command``
    (or ``cmd`` / ``shell``), case-insensitively,
    with dashes and spaces read as underscores.
    Any other word refuses: the kinds are a
    closed vocabulary.
    """
    if isinstance(value, str):
        wanted = value.strip().lower().replace("-", "_").replace(" ", "_")
        if wanted in _KIND_WORDS:
            return _KIND_WORDS[wanted]
    raise ValueError(
        "an audit kind must be one of %s, got %r"
        % ("/".join(AUDIT_KINDS), value))


def normalize_audit_actor(value: Any) -> str:
    """The canonical audit actor a word names.

    Reads ``human`` (or ``user``), ``coder`` (or
    ``agent``), ``crew`` (or ``fleet``) and
    ``hook``, case-insensitively, with dashes
    and spaces read as underscores. Any other
    word refuses: the actors are a closed
    vocabulary.
    """
    if isinstance(value, str):
        wanted = value.strip().lower().replace("-", "_").replace(" ", "_")
        if wanted in _ACTOR_WORDS:
            return _ACTOR_WORDS[wanted]
    raise ValueError(
        "an audit actor must be one of %s, got %r"
        % ("/".join(AUDIT_ACTORS), value))


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
                f"an audit record names two different {what}")
    return first


# ---------------------------------------------------------------------
# The entry: one recorded act, as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class AuditEntry:
    """One audit entry: one act, its actor, as data.

    ``kind`` names what kind of act it was - a
    tool call, an approval, an edit or a command;
    ``actor`` names who acted - the human, the
    coder, the crew or a hook. ``summary`` says
    what happened, in words; it is never empty,
    because an entry that says nothing audits
    nothing. ``target`` names what the act
    touched (a tool, a file, a command line) and
    ``detail`` carries any further words; either
    may be empty when nothing more is known. An
    entry is frozen: once recorded it is never
    changed - the trail is append-only, and a
    correction is a new entry, never a rewrite.

    Constructing one validates it, so an
    AuditEntry that exists is an entry the agent
    layer could record.
    """

    kind: str
    actor: str
    summary: str
    detail: str = ""
    target: str = ""
    entry_id: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "kind", normalize_audit_kind(self.kind))
        object.__setattr__(
            self, "actor", normalize_audit_actor(self.actor))
        object.__setattr__(
            self, "summary", _clean_text(self.summary, "a summary"))
        object.__setattr__(
            self, "detail", _loose_text(self.detail, "a detail"))
        object.__setattr__(
            self, "target", _loose_text(self.target, "a target"))
        if self.entry_id is not None:
            object.__setattr__(
                self, "entry_id", normalize_audit_id(self.entry_id))

    @property
    def display_label(self) -> str:
        name = self.entry_id or "entry"
        return f"{name} ({_KIND_LABELS[self.kind]} by {self.actor})"

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "audit_entry",
            "slice": AUDIT_TRAIL_SLICE,
            "entry_id": self.entry_id,
            "kind": self.kind,
            "actor": self.actor,
            "summary": self.summary,
            "detail": self.detail,
            "target": self.target,
        }


#: The shorter word for an audit entry.
Entry = AuditEntry


def validate_entry(entry: Any) -> AuditEntry:
    """Validate one audit entry into an AuditEntry.

    Accepts an AuditEntry or a mapping naming a
    ``kind`` (or ``type`` / ``category``), an
    ``actor`` (or ``by`` / ``who``) and a
    ``summary`` (or ``what`` / ``description``) -
    all three are required - and optionally an
    ``entry_id`` (or ``id``), a ``detail`` (or
    ``details``) and a ``target`` (or
    ``subject``). Naming two spellings of one
    field with different values refuses, and
    unknown keys refuse.
    """
    if isinstance(entry, AuditEntry):
        return entry
    if not isinstance(entry, dict):
        raise ValueError(f"an audit entry must be a mapping, got {entry!r}")
    unknown = set(entry) - _ENTRY_KEYS
    if unknown:
        raise ValueError(
            "unknown audit entry keys: %s" % ", ".join(sorted(unknown)))
    kind = _pick(entry, ("kind", "type", "category"), "kinds")
    if kind is None:
        raise ValueError("an audit entry must name its kind")
    actor = _pick(entry, ("actor", "by", "who"), "actors")
    if actor is None:
        raise ValueError("an audit entry must name its actor")
    summary = _pick(
        entry, ("summary", "what", "description"), "summaries")
    if summary is None:
        raise ValueError("an audit entry must say what happened")
    kwargs: Dict[str, Any] = {
        "kind": kind, "actor": actor, "summary": summary}
    entry_id = _pick(entry, ("entry_id", "id"), "entry ids")
    if entry_id is not None:
        kwargs["entry_id"] = entry_id
    detail = _pick(entry, ("detail", "details"), "details")
    if detail is not None:
        kwargs["detail"] = detail
    target = _pick(entry, ("target", "subject"), "targets")
    if target is not None:
        kwargs["target"] = target
    return AuditEntry(**kwargs)


def build_entry(entry: Any = None, **kwargs: Any) -> AuditEntry:
    """Build one validated audit entry from a mapping or field words."""
    if isinstance(entry, AuditEntry) and not kwargs:
        return entry
    if isinstance(entry, dict) or entry is None:
        merged: Dict[str, Any] = {}
        if isinstance(entry, dict):
            merged.update(entry)
        merged.update(kwargs)
        return validate_entry(merged)
    raise ValueError(f"an audit entry must be a mapping, got {entry!r}")


def _require_entry(entry: Any) -> AuditEntry:
    if isinstance(entry, AuditEntry):
        return entry
    return validate_entry(entry)


# ---------------------------------------------------------------------
# Reading a trail whole: its entries, its counts, its export.
# ---------------------------------------------------------------------


def _trail_entries(source: Any) -> Tuple[AuditEntry, ...]:
    """The entries a trail source holds, in append order.

    A source is an AuditRegistry, a list of
    entries (or entry mappings), one entry, or
    nothing at all - an empty trail.
    """
    if source is None:
        return ()
    if isinstance(source, AuditRegistry):
        return source.list_entries()
    if isinstance(source, (AuditEntry, dict)):
        return (_require_entry(source),)
    if isinstance(source, (list, tuple)):
        return tuple(_require_entry(entry) for entry in source)
    raise ValueError(
        "an audit trail must be a registry or a list of entries")


def _trail_counts(entries: Tuple[AuditEntry, ...]) -> Dict[str, Any]:
    """Entry counts by kind and by actor, counted from the entries.

    Every word of both vocabularies is named,
    with a count of zero when no entry carries
    it, so a review reading never has to guess
    whether a missing word means none or uncounted.
    """
    by_kind = {kind: 0 for kind in AUDIT_KINDS}
    by_actor = {actor: 0 for actor in AUDIT_ACTORS}
    for entry in entries:
        by_kind[entry.kind] += 1
        by_actor[entry.actor] += 1
    return {"by_kind": by_kind, "by_actor": by_actor}


def export_trail(source: Any = None) -> Dict[str, Any]:
    """The whole trail, as plain data, for review.

    Every held entry is named, in append order,
    with the counts by kind and by actor counted
    from those entries. Nothing held is left out
    and nothing is summarised away: the export
    is the trail, readable by a reviewer who
    holds nothing else.
    """
    entries = _trail_entries(source)
    counts = _trail_counts(entries)
    return {
        "type": "audit_export",
        "slice": AUDIT_TRAIL_SLICE,
        "append_only": True,
        "count": len(entries),
        "entries": [entry.to_record() for entry in entries],
        "by_kind": counts["by_kind"],
        "by_actor": counts["by_actor"],
    }


# ---------------------------------------------------------------------
# The news record: one recorded entry, shaped as session news.
# ---------------------------------------------------------------------


def _entry_headline(entry: AuditEntry) -> str:
    name = entry.entry_id or "entry"
    headline = (
        f"Audit recorded ({name}): {_KIND_LABELS[entry.kind]} "
        f"by {entry.actor} - {entry.summary}.")
    if entry.target:
        headline += f" Target: {entry.target}."
    if entry.detail:
        headline += f" Detail: {entry.detail}."
    return headline


def audit_record(entry: Any) -> Dict[str, Any]:
    """The session-news record of one recorded entry.

    Every recorded entry yields a record - the
    agent layer publishes this record as a
    session event, so a recorded act is always
    news and can never be lost as a mere log
    line. The headline states the entry's kind
    and actor in plain words.
    """
    checked = _require_entry(entry)
    return {
        "type": "audit_recorded",
        "news": True,
        "slice": AUDIT_TRAIL_SLICE,
        "entry_id": checked.entry_id,
        "kind": checked.kind,
        "actor": checked.actor,
        "summary": checked.summary,
        "detail": checked.detail,
        "target": checked.target,
        "headline": _entry_headline(checked),
    }


# ---------------------------------------------------------------------
# The registry model: entries held in append order, ids
# deterministic; append-only - there is no other road in or out.
# ---------------------------------------------------------------------


class AuditRegistry:
    """An in-memory, append-only registry of audit entries.

    Entries are held in the order appended, and
    that order is the trail's order forever: this
    registry offers no edit, removal, clearing or
    reordering road, entries themselves are
    frozen, and appending an entry under an id
    the trail already holds refuses - history is
    never rewritten here. Ids are deterministic:
    a caller-supplied id is used as given (a
    duplicate refuses), and an unsupplied id is
    the next ``audit-N`` in sequence, skipping
    any number a supplied id already took - no
    randomness a test cannot pin. Storage beyond
    memory (a session's journal, a file) is the
    agent layer's concern; this model is neutral.
    """

    def __init__(self) -> None:
        self._entries: Dict[str, AuditEntry] = {}
        self._next = 1

    def _fresh_id(self) -> str:
        while f"audit-{self._next}" in self._entries:
            self._next += 1
        entry_id = f"audit-{self._next}"
        self._next += 1
        return entry_id

    def append(self, entry: Any = None, **kwargs: Any) -> AuditEntry:
        """Append one entry to the trail and hold it.

        This is the registry's only road in: the
        entry goes last, after every entry already
        held, and an id the trail already holds
        refuses rather than rewriting that entry.
        Accepts an AuditEntry, an entry mapping, or
        entry field words.
        """
        if kwargs and isinstance(entry, (AuditEntry, dict)):
            validated = build_entry(entry, **kwargs)
        elif kwargs and entry is None:
            validated = build_entry(**kwargs)
        else:
            if kwargs:
                raise ValueError(
                    "an audit entry is named twice: as a record "
                    "and as field words")
            validated = _require_entry(entry)
        if validated.entry_id is None:
            validated = replace(validated, entry_id=self._fresh_id())
        elif validated.entry_id in self._entries:
            raise ValueError(
                f"an audit entry named {validated.entry_id!r} "
                f"already exists - the trail is append-only and "
                f"its entries are never rewritten")
        self._entries[validated.entry_id] = validated
        return validated

    def register(self, entry: Any = None, **kwargs: Any) -> AuditEntry:
        """Append one entry - the sibling registries' word for append."""
        return self.append(entry, **kwargs)

    def get(self, entry_id: Any) -> AuditEntry:
        """The entry one id names; an unknown id raises KeyError."""
        wanted = normalize_audit_id(entry_id)
        if wanted not in self._entries:
            raise KeyError(f"unknown audit entry: {wanted!r}")
        return self._entries[wanted]

    def list_entries(self) -> Tuple[AuditEntry, ...]:
        """Every held entry, in append order, as an immutable tuple."""
        return tuple(self._entries.values())

    def __len__(self) -> int:
        return len(self._entries)

    def record(self, entry_id: Any) -> Dict[str, Any]:
        """One held entry's news record."""
        return audit_record(self.get(entry_id))

    def export(self) -> Dict[str, Any]:
        """The whole held trail, as plain data, for review."""
        return export_trail(self)


# ---------------------------------------------------------------------
# The /audit surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------


def format_entry(entry: Any) -> str:
    """One audit entry, in plain words: kind and actor always stated."""
    current = _require_entry(entry)
    name = current.entry_id or "entry"
    line = (
        f"{name}: audit entry - {_KIND_LABELS[current.kind]} "
        f"by {current.actor}: {current.summary}.")
    if current.target:
        line += f" Target: {current.target}."
    if current.detail:
        line += f" Detail: {current.detail}."
    return line


def format_entries(source: Any = None) -> str:
    """The trail's entries, in plain words, in append order.

    With no entries at all the text starts with
    the plain statement of that fact. Every line
    states its entry's kind and actor in words.
    """
    entries = _trail_entries(source)
    if not entries:
        return "Audit trail: none recorded. No audit entry is held."
    lines = [f"Audit trail: {len(entries)} recorded."]
    for entry in entries:
        lines.append(f"  {format_entry(entry)}")
    return "\n".join(lines)


def format_export(source: Any = None) -> str:
    """The whole trail as a text export for review.

    The header states the count and the counts
    by kind and by actor; every held entry then
    follows, in append order - an export that
    left an entry out would not be an export.
    """
    entries = _trail_entries(source)
    counts = _trail_counts(entries)
    by_kind = ", ".join(
        f"{_KIND_LABELS[kind]} {counts['by_kind'][kind]}"
        for kind in AUDIT_KINDS)
    by_actor = ", ".join(
        f"{actor} {counts['by_actor'][actor]}"
        for actor in AUDIT_ACTORS)
    lines = [
        f"Audit trail export (M-109) - {len(entries)} "
        f"entries, append-only.",
        f"By kind: {by_kind}.",
        f"By actor: {by_actor}.",
    ]
    if not entries:
        lines.append("No audit entry is held.")
    for entry in entries:
        lines.append(f"  {format_entry(entry)}")
    return "\n".join(lines)


def format_audit_record(record: Any) -> str:
    """One audit news record as its plain headline."""
    if isinstance(record, dict) \
            and record.get("type") == "audit_recorded":
        return str(record["headline"])
    raise ValueError("format_audit_record needs an audit record")


#: The audit record's formatter under its own name.
format_record = format_audit_record


def format_audit_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /audit."""
    lines = ["Audit trail (M-109) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_entries(source))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


_GRAMMAR_WORDS = ("show", "export")


def parse_audit_args(args: Any) -> Tuple[str, Optional[str]]:
    """Parse the /audit grammar both surfaces share.

    No words (or ``show``) shows the trail;
    ``show <entry>`` and a bare entry id show one
    entry; ``export`` exports the whole trail for
    review. A grammar word in the wrong shape -
    a bare kind or actor word, a doubled word -
    is a usage error naming the grammar, never
    an entry id. Returns ``(action,
    entry-id-or-None)``: for ``show`` the second
    word is an entry id, for ``export`` it is
    always None.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None \
        else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() == "show":
        return ("show", None)
    words = text.split()
    head = words[0].lower()
    if head == "export":
        if len(words) == 1:
            return ("export", None)
        raise ValueError(USAGE)
    if head == "show" and len(words) == 2:
        if words[1].lower() in _GRAMMAR_WORDS:
            raise ValueError(USAGE)
        try:
            return ("show", normalize_audit_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head in _GRAMMAR_WORDS or len(words) != 1:
        raise ValueError(USAGE)
    lowered = words[0].lower().replace("-", "_")
    if lowered in _KIND_WORDS or lowered in _ACTOR_WORDS:
        raise ValueError(USAGE)
    try:
        return ("show", normalize_audit_id(words[0]))
    except ValueError:
        raise ValueError(USAGE) from None
