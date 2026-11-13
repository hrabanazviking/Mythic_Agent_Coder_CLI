"""Stand-ups (All-Features roadmap slice M-134).

Part VI continues here. The roadmap's words:
``the coordinator's progress digest in plain
words (done, doing, blocked, needs-you) on
demand and at slice boundaries.``

What already shipped, and what this slice adds:

* The crew itself is already data
  (``core/crew_members.py``, M-121), the crew's
  work is dealt as data (M-125), research swarms
  digest their findings (M-131), review panels
  derive their outcome from two verdicts (M-132)
  and the crew's hard-won facts are held as data
  (M-133). What nothing held is the coordinator's
  own account of where the work stands: progress
  lived in chat and in ledgers, so a human asking
  ``where do we stand?`` got prose, not a digest
  that could be checked against the work itself.
* This slice is that account, as a pure layer: a
  stand-up report validated as data - progress
  entries (one item of work per entry: a title,
  the item in plain words, the member who holds
  it, and the state the item stands in) under a
  title and a boundary (the slice boundary the
  stand-up stands at, or an on-demand asking) -
  the shipped data file
  (``mythic_agent/data/stand_ups.yaml``) holding
  one example stand-up in exactly the shape a
  real stand-up file takes, a loader for a
  stand-up file anywhere on disk, the digest
  derived mechanically from the entries alone, a
  record shaped as session news, and a small
  in-memory registry model. This module schedules
  nothing, sends nothing, posts nothing, persists
  nothing, calls no model and imports no agent /
  UI code; the agent layer owns holding the
  report for a session and showing the digest on
  demand and at slice boundaries.

Honesty rules, enforced here and pinned by tests:

* **The digest is derived, never stored.** A
  digest's four sections - done, doing, blocked
  and needs-you - group the report's entries by
  the state each entry stands in, in report
  order, computed from the entries held at that
  moment, so the same report always yields the
  same digest and the digest can never disagree
  with the entries. A stored digest that
  disagrees with the derived one refuses.
* **Four states, plainly named.** An entry stands
  in exactly one of the roadmap's four states:
  done, doing, blocked, or needs-you - an item
  waiting on the human's word is its own section,
  never folded into blocked, so what needs
  Volmarr is always visible at a glance. An
  unknown state raises; there is no fifth state
  and no score.
* **Members are the shipped casting.** An entry
  names its holder as an M-121 member id read
  exactly as the M-121 layer reads one
  (``core/crew_members.py``) - composed by
  import, never re-read here.
* **Data only.** No scheduling, no sending, no
  posting, no persistence and no model call is
  claimed or attempted here: a stand-up here is a
  validated record of where the work stands, not
  the standing itself. The roadmap names the
  board (Part VIII) as where crew state will be
  visible; that board does not exist yet, so the
  digest is visible through this slice's own
  /standup screen, and nothing here claims a
  board exists.
* **Malformed refuses.** An unknown state, an
  empty title or detail, a malformed member, a
  duplicate entry id anywhere in the report, and
  unknown keys in an entry, a digest, or a
  stand-up mapping all raise instead of being
  skipped or guessed at.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..resources import load_resource
from .crew_members import normalize_member_id
from .validation import ValidationError

__all__ = [
    "PLAIN_EXPLANATION",
    "STAND_UP_RESOURCE",
    "STAND_UP_SCHEMA",
    "STAND_UP_SLICE",
    "STATUS_KINDS",
    "USAGE",
    "ProgressEntry",
    "StandUpDigest",
    "StandUpRegistry",
    "StandUpReport",
    "build_digest",
    "build_entry",
    "build_report",
    "digest_plain_words",
    "digest_record",
    "digest_stand_up",
    "entry_record",
    "format_digest",
    "format_entries",
    "format_entry",
    "format_stand_up_screen",
    "format_status_kinds",
    "load_stand_up",
    "load_stand_up_file",
    "normalize_status",
    "parse_stand_up_args",
    "plain_words",
    "report_record",
    "validate_digest",
    "validate_entry",
    "validate_report",
]

STAND_UP_SLICE = "M-134"

#: The packaged data resource holding the example stand-up.
STAND_UP_RESOURCE = "stand_ups.yaml"

#: The schema word a stand-up file must carry.
STAND_UP_SCHEMA = "mythic.stand_ups/1"

#: The four states an item of work stands in, in
#: digest order: finished, under way, held, and
#: waiting on the human's word.
STATUS_KINDS = ("done", "doing", "blocked", "needs_you")

_STATUS_READINGS = {
    "done": "done",
    "finished": "done",
    "complete": "done",
    "completed": "done",
    "shipped": "done",
    "banked": "done",
    "doing": "doing",
    "in_progress": "doing",
    "active": "doing",
    "working": "doing",
    "underway": "doing",
    "blocked": "blocked",
    "stuck": "blocked",
    "waiting": "blocked",
    "held": "blocked",
    "needs_you": "needs_you",
    "needs_human": "needs_you",
    "needs_decision": "needs_you",
    "decision": "needs_you",
    "awaiting_you": "needs_you",
}

_ENTRY_KEYS = frozenset({
    "id", "entry_id", "member", "member_id", "owner",
    "title", "name", "detail", "body", "text", "notes",
    "status", "state", "kind",
})

_DIGEST_KEYS = frozenset({
    "title", "boundary", "done", "doing", "blocked",
    "needs_you", "needs-you", "needs",
})

_REPORT_KEYS = frozenset({"title", "name", "boundary"})

_STAND_UP_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "standup_note", "report", "entries", "digest",
})

#: The shipped example stand-up's boundary: the
#: M-133 slice boundary it stands at, held to this
#: by the loader's example check.
_EXAMPLE_BOUNDARY = "M-133"

#: The shipped example's entry ids in each digest
#: section, in report order, pinned by the loader.
_EXAMPLE_SECTIONS = {
    "done": ("m-133-memory-banked", "m-132-panels-banked"),
    "doing": ("m-134-stand-ups-building",),
    "blocked": ("full-suite-portaudio-held",),
    "needs_you": ("hall-posting-needs-word",),
}

PLAIN_EXPLANATION = (
    "Stand-ups: the coordinator's progress "
    "digest in plain words. A stand-up report "
    "holds progress entries - one item of work "
    "per entry, with the member who holds it "
    "and the state it stands in - and the digest "
    "is derived from the entries alone, in four "
    "sections: done, doing, blocked and "
    "needs-you, so what needs the human's word "
    "is always its own section, never folded "
    "into blocked. This layer holds the stand-up "
    "as data only; it schedules nothing, sends "
    "nothing, posts nothing, persists nothing "
    "and calls no model itself."
)

USAGE = (
    "Usage: /standup, /standup show, "
    "/standup digest, /standup done, "
    "/standup doing, /standup blocked, "
    "/standup needs-you, /standup entry <entry-id>, "
    "/standup kinds"
)


def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_short_text(value: Any, what: str) -> str:
    text = _clean_text(value, what)
    if len(text) > 200 or "\x00" in text:
        raise ValueError(
            f"{what} must be plain text of at most "
            f"200 characters, got {len(text)} characters")
    return text


def _check_long_text(value: Any, what: str) -> str:
    text = _clean_text(value, what)
    if len(text) > 2000 or "\x00" in text:
        raise ValueError(
            f"{what} must be plain text of at most "
            f"2000 characters, got {len(text)} characters")
    return text


def normalize_status(value: Any) -> str:
    """The canonical state a word names.

    State words read case-insensitively, with
    dashes read as underscores: ``finished``,
    ``complete`` and ``banked`` read as done,
    ``in-progress`` and ``working`` as doing,
    ``stuck`` and ``held`` as blocked, and
    ``needs-you``, ``needs-human`` and
    ``decision`` as needs_you. Anything else
    raises - a state is one of the four, never a
    maybe.
    """
    if isinstance(value, str):
        wanted = value.strip().lower().replace("-", "_")
        if wanted in _STATUS_READINGS:
            return _STATUS_READINGS[wanted]
    raise ValueError(
        "a status must be one of %s, got %r"
        % ("/".join(STATUS_KINDS), value))


def _status_words(status: str) -> str:
    """One state's plain display words."""
    return "needs-you" if status == "needs_you" else status


def _pick_any(mapping: Dict[str, Any], spellings: Tuple[str, ...],
              what: str) -> Any:
    values = [mapping[s] for s in spellings if s in mapping]
    if not values:
        return None
    if any(value != values[0] for value in values[1:]):
        raise ValueError(f"a record names two different {what}")
    return values[0]


# ---------------------------------------------------------------------
# The entry: one item of work, and the state it stands in.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class ProgressEntry:
    """One item of work in a stand-up report, as data.

    ``member`` is the M-121 member who holds the
    item; ``title`` names it; ``detail`` is the
    item in plain words (for a blocked item, what
    holds it; for a needs-you item, what the human
    is asked); ``status`` is the one state the
    item stands in. Constructing one validates its
    shape only: whether its id already stands in
    its report is the report's concern.
    """

    entry_id: Optional[str] = None
    member: str = ""
    title: str = ""
    detail: str = ""
    status: str = ""

    def __post_init__(self) -> None:
        if self.entry_id is not None:
            object.__setattr__(
                self, "entry_id", normalize_member_id(self.entry_id))
        object.__setattr__(
            self, "member", normalize_member_id(self.member))
        object.__setattr__(
            self, "title", _check_short_text(self.title, "a title"))
        object.__setattr__(
            self, "detail", _check_long_text(self.detail, "a detail"))
        object.__setattr__(self, "status", normalize_status(self.status))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "stand_up_entry",
            "slice": STAND_UP_SLICE,
            "entry_id": self.entry_id,
            "member": self.member,
            "title": self.title,
            "detail": self.detail,
            "status": self.status,
        }


def validate_entry(entry: Any) -> ProgressEntry:
    """Validate one entry into a ProgressEntry.

    Accepts a ProgressEntry or a mapping naming a
    ``member`` (or ``member_id`` / ``owner``), a
    ``title`` (or ``name``), a ``detail`` (or
    ``body`` / ``text`` / ``notes``), a ``status``
    (or ``state`` / ``kind``) and an optional
    ``entry_id`` (or ``id``). Naming two spellings
    of one field with different values refuses,
    and unknown keys refuse.
    """
    if isinstance(entry, ProgressEntry):
        return entry
    if not isinstance(entry, dict):
        raise ValueError(f"an entry must be a mapping, got {entry!r}")
    unknown = set(entry) - _ENTRY_KEYS
    if unknown:
        raise ValueError(
            "unknown entry keys: %s" % ", ".join(sorted(unknown)))
    member = _pick_any(entry, ("member", "member_id", "owner"), "members")
    if member is None:
        raise ValueError("an entry is missing its member")
    title = _pick_any(entry, ("title", "name"), "titles")
    if title is None:
        raise ValueError("an entry is missing its title")
    detail = _pick_any(
        entry, ("detail", "body", "text", "notes"), "details")
    if detail is None:
        raise ValueError("an entry is missing its detail")
    status = _pick_any(entry, ("status", "state", "kind"), "statuses")
    if status is None:
        raise ValueError("an entry is missing its status")
    kwargs: Dict[str, Any] = {
        "member": member, "title": title, "detail": detail,
        "status": status}
    entry_id = _pick_any(entry, ("entry_id", "id"), "entry ids")
    if entry_id is not None:
        kwargs["entry_id"] = entry_id
    return ProgressEntry(**kwargs)


def build_entry(entry: Any = None, **kwargs: Any) -> ProgressEntry:
    """Build one validated entry, from a mapping or field words."""
    if isinstance(entry, ProgressEntry) and not kwargs:
        return entry
    if isinstance(entry, dict) or entry is None:
        merged: Dict[str, Any] = {}
        if isinstance(entry, dict):
            merged.update(entry)
        merged.update(kwargs)
        return validate_entry(merged)
    raise ValueError(f"an entry must be a mapping, got {entry!r}")


# ---------------------------------------------------------------------
# The report: the entries whole, under a title and a boundary.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class StandUpReport:
    """One stand-up report, whole, as data.

    ``title`` names the stand-up; ``boundary``
    names where it stands (a slice boundary such
    as ``M-133``, or an on-demand asking);
    ``entries`` are the progress entries, in file
    order, their ids unique across the report.
    The digest is derived from the entries held,
    never stored on the report.
    """

    title: str = ""
    boundary: str = ""
    entries: Tuple[ProgressEntry, ...] = ()
    standup_note: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_short_text(self.title, "a title"))
        object.__setattr__(
            self, "boundary",
            _check_short_text(self.boundary, "a boundary"))
        entries = tuple(
            e if isinstance(e, ProgressEntry) else validate_entry(e)
            for e in self.entries)
        ids = [e.entry_id for e in entries if e.entry_id is not None]
        if len(set(ids)) != len(ids):
            raise ValueError("a report holds one entry id twice")
        object.__setattr__(self, "entries", entries)
        if not isinstance(self.standup_note, str):
            raise ValueError("a stand-up's note must be text")
        object.__setattr__(self, "standup_note", self.standup_note.strip())

    def entry_for(self, entry_id: Any) -> ProgressEntry:
        """The entry one id names in this report; unknown raises."""
        wanted = normalize_member_id(entry_id)
        for entry in self.entries:
            if entry.entry_id == wanted:
                return entry
        raise KeyError(f"no entry in the stand-up: {wanted!r}")

    def entries_for(self, status: Any) -> Tuple[ProgressEntry, ...]:
        """Every entry standing in one state, in report order."""
        wanted = normalize_status(status)
        return tuple(e for e in self.entries if e.status == wanted)

    def entry_ids(self) -> Tuple[str, ...]:
        """Every held entry id, in report order (id-less skipped)."""
        return tuple(e.entry_id for e in self.entries if e.entry_id)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "stand_up_report",
            "slice": STAND_UP_SLICE,
            "title": self.title,
            "boundary": self.boundary,
            "entry_ids": list(self.entry_ids()),
            "entry_count": len(self.entries),
        }


def validate_report(data: Any, *, require_example: bool = False) -> StandUpReport:
    """Validate one stand-up mapping into a StandUpReport.

    The mapping names a ``schema`` (the stand-up
    schema word), a ``report`` mapping (its
    ``title`` and ``boundary``) and an ``entries``
    list. Every entry is validated, then the whole
    is judged: entry ids unique across the report.
    A ``digest`` named in the mapping is judged
    against the digest the entries derive: any
    disagreement refuses, because a digest is
    derived, never stored. With
    ``require_example`` the shipped example is
    held to its pinned shape: the M-133 boundary
    and the pinned entry ids in each of the four
    digest sections. Problems raise
    :class:`ValidationError` or ``ValueError``
    naming the problem.
    """
    if isinstance(data, StandUpReport):
        return data
    if not isinstance(data, dict):
        raise ValidationError(f"a stand-up must be a mapping, got {data!r}")
    unknown = set(data) - _STAND_UP_KEYS
    if unknown:
        raise ValidationError(
            "unknown stand-up keys: %s" % ", ".join(sorted(unknown)))
    if data.get("schema") != STAND_UP_SCHEMA:
        raise ValidationError(
            f"a stand-up must carry schema {STAND_UP_SCHEMA!r}, "
            f"got {data.get('schema')!r}")
    if "entries" not in data:
        raise ValidationError("a stand-up is missing its entries")
    raw = data["entries"]
    if not isinstance(raw, (list, tuple)):
        raise ValidationError("a stand-up's entries must be a list")
    head = data.get("report") or {}
    if not isinstance(head, dict):
        raise ValidationError("a stand-up's report must be a mapping")
    unknown_head = set(head) - _REPORT_KEYS
    if unknown_head:
        raise ValidationError(
            "unknown report keys: %s" % ", ".join(sorted(unknown_head)))
    try:
        title = _pick_any(head, ("title", "name"), "titles")
        if title is None:
            raise ValidationError("a stand-up is missing its title")
        if "boundary" not in head:
            raise ValidationError("a stand-up is missing its boundary")
        entries = tuple(validate_entry(e) for e in raw)
        note = data.get("standup_note") or ""
        if not isinstance(note, str):
            raise ValidationError("a stand-up's note must be text")
        report = StandUpReport(
            title=title, boundary=head["boundary"], entries=entries,
            standup_note=note)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    if data.get("digest") is not None:
        try:
            validate_digest(data["digest"], report)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
    if require_example:
        if report.boundary != _EXAMPLE_BOUNDARY:
            raise ValidationError(
                "the shipped example stand-up's boundary is not "
                "the pinned M-133 boundary")
        derived = digest_stand_up(report)
        for status in STATUS_KINDS:
            if derived.section(status) != _EXAMPLE_SECTIONS[status]:
                raise ValidationError(
                    f"the shipped example stand-up's {status} section "
                    "is not the pinned shape")
    return report


def build_report(report: Any = None, **kwargs: Any) -> StandUpReport:
    """Build one validated report, from a mapping or field words."""
    if isinstance(report, StandUpReport) and not kwargs:
        return report
    if isinstance(report, (list, tuple)) and not kwargs:
        raise ValueError("a report needs its title and boundary")
    if isinstance(report, dict):
        if "entries" in report or "schema" in report:
            return validate_report(report)
        merged: Dict[str, Any] = dict(report)
        merged.update(kwargs)
        return StandUpReport(**merged)
    if report is None:
        return StandUpReport(**kwargs)
    raise ValueError(f"a stand-up report is needed, got {report!r}")


def _report_from(data: Any, *, require_example: bool) -> StandUpReport:
    try:
        return validate_report(data, require_example=require_example)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def load_stand_up(data: Optional[Dict[str, Any]] = None) -> StandUpReport:
    """Load and validate the shipped example stand-up (or *data*).

    The shipped file is held to the example check:
    the M-133 boundary and the pinned entry ids in
    each of the four digest sections, so the
    shipped digest covers done, doing, blocked and
    needs-you.
    """
    raw = data if data is not None else load_resource(STAND_UP_RESOURCE)
    return _report_from(raw, require_example=True)


def load_stand_up_file(path: Any) -> StandUpReport:
    """Load and validate a stand-up from a file at *path*.

    Any file in the stand-up shape, anywhere on
    disk, validated whole - a malformed file
    raises :class:`ValidationError` naming the
    problem, and a missing file raises
    ``FileNotFoundError``. The example check is
    not held: a real stand-up stands at its own
    boundary.
    """
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _report_from(raw, require_example=False)


# ---------------------------------------------------------------------
# The digest: the four sections, derived from the entries alone.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class StandUpDigest:
    """The coordinator's digest, derived from one report.

    ``title`` and ``boundary`` are the report's own;
    ``done``, ``doing``, ``blocked`` and
    ``needs_you`` hold the entry ids standing in
    each state, each in report order. No entry id
    stands in two sections. The counts are read
    off the sections, never stored apart from
    them.
    """

    title: str = ""
    boundary: str = ""
    done: Tuple[str, ...] = ()
    doing: Tuple[str, ...] = ()
    blocked: Tuple[str, ...] = ()
    needs_you: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_short_text(self.title, "a title"))
        object.__setattr__(
            self, "boundary",
            _check_short_text(self.boundary, "a boundary"))
        seen = []
        for status in STATUS_KINDS:
            ids = tuple(
                normalize_member_id(entry_id)
                for entry_id in getattr(self, status))
            object.__setattr__(self, status, ids)
            seen.extend(ids)
        if len(set(seen)) != len(seen):
            raise ValueError("a digest names one entry in two sections")

    def section(self, status: Any) -> Tuple[str, ...]:
        """One section's entry ids, by its state word."""
        return getattr(self, normalize_status(status))

    def counts(self) -> Dict[str, int]:
        """Each section's size, read off the sections held."""
        return {status: len(self.section(status)) for status in STATUS_KINDS}

    def total(self) -> int:
        """Every entry the digest names, across all sections."""
        return sum(self.counts().values())

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "stand_up_digest",
            "slice": STAND_UP_SLICE,
            "title": self.title,
            "boundary": self.boundary,
            "done": list(self.done),
            "doing": list(self.doing),
            "blocked": list(self.blocked),
            "needs_you": list(self.needs_you),
            "counts": self.counts(),
            "entry_count": self.total(),
        }


def digest_stand_up(source: Any) -> StandUpDigest:
    """The digest one report yields, derived from its entries alone.

    Accepts a StandUpReport or a StandUpRegistry.
    Each section holds the ids of the entries
    standing in that state, in report order - the
    order the entries stand in the report, not the
    order any section fills. An entry with no id
    refuses: a digest names every item it digests,
    so an unnamed item cannot be digested.
    """
    if isinstance(source, StandUpRegistry):
        report = source.report()
    elif isinstance(source, StandUpReport):
        report = source
    else:
        raise ValueError(f"a stand-up report is needed, got {source!r}")
    sections: Dict[str, list] = {status: [] for status in STATUS_KINDS}
    for entry in report.entries:
        if entry.entry_id is None:
            raise ValueError(
                "a digest names every entry by id; an entry "
                "without an id cannot be digested")
        sections[entry.status].append(entry.entry_id)
    return StandUpDigest(
        title=report.title, boundary=report.boundary,
        done=tuple(sections["done"]), doing=tuple(sections["doing"]),
        blocked=tuple(sections["blocked"]),
        needs_you=tuple(sections["needs_you"]))


def validate_digest(digest: Any, report: Any = None) -> StandUpDigest:
    """Validate one digest into a StandUpDigest.

    Accepts a StandUpDigest or a mapping naming a
    ``title``, a ``boundary`` and the four
    sections (``needs-you`` / ``needs`` also read
    for the needs_you section). When *report* is
    given, the digest is also judged against the
    digest that report derives: any disagreement
    refuses, because a digest is derived, never
    stored.
    """
    if isinstance(digest, StandUpDigest):
        current = digest
    elif isinstance(digest, dict):
        unknown = set(digest) - _DIGEST_KEYS
        if unknown:
            raise ValueError(
                "unknown digest keys: %s" % ", ".join(sorted(unknown)))
        if "title" not in digest or "boundary" not in digest:
            raise ValueError("a digest is missing its title or boundary")
        needs = _pick_any(
            digest, ("needs_you", "needs-you", "needs"), "needs-you sections")
        current = StandUpDigest(
            title=digest["title"], boundary=digest["boundary"],
            done=tuple(digest.get("done") or ()),
            doing=tuple(digest.get("doing") or ()),
            blocked=tuple(digest.get("blocked") or ()),
            needs_you=tuple(needs or ()))
    else:
        raise ValueError(f"a digest must be a mapping, got {digest!r}")
    if report is not None:
        derived = digest_stand_up(report)
        if current != derived:
            raise ValueError(
                "a stored digest disagrees with the digest its "
                "report derives - a digest is derived, never stored")
    return current


def build_digest(digest: Any = None, **kwargs: Any) -> StandUpDigest:
    """Build one validated digest, from a mapping or field words."""
    if isinstance(digest, StandUpDigest) and not kwargs:
        return digest
    if isinstance(digest, dict) or digest is None:
        merged: Dict[str, Any] = {}
        if isinstance(digest, dict):
            merged.update(digest)
        merged.update(kwargs)
        return validate_digest(merged)
    raise ValueError(f"a digest must be a mapping, got {digest!r}")


# ---------------------------------------------------------------------
# The registry model: one report held entry by entry, in order.
# ---------------------------------------------------------------------


class StandUpRegistry:
    """One session's stand-up report, held entry by entry."""

    def __init__(self, report: Any = None) -> None:
        self._title: Optional[str] = None
        self._boundary: Optional[str] = None
        self._entries: Dict[str, ProgressEntry] = {}
        self._order: list = []
        self._next_entry = 1
        if report is not None:
            self.register_report(report)

    def _fresh_entry_id(self, held_ids: Any) -> str:
        while f"entry-{self._next_entry}" in held_ids:
            self._next_entry += 1
        fresh = f"entry-{self._next_entry}"
        self._next_entry += 1
        return fresh

    def register_entry(self, entry: Any) -> ProgressEntry:
        """Register one entry into the held report.

        An entry with no id is given a deterministic
        ``entry-N`` id. A duplicate entry id refuses.
        The held report's title and boundary must
        already stand (register a report first, or
        hold entries under a report registered
        whole).
        """
        validated = build_entry(entry)
        if validated.entry_id is not None \
                and validated.entry_id in self._entries:
            raise ValueError(
                f"an entry named {validated.entry_id!r} already exists")
        if validated.entry_id is None:
            validated = replace(
                validated,
                entry_id=self._fresh_entry_id(set(self._entries)))
        self._entries[validated.entry_id] = validated
        self._order.append(validated.entry_id)
        return validated

    def register_report(self, report: Any) -> StandUpReport:
        """Register every entry of one report, in order.

        The first report held sets the title and
        boundary; a later report under a different
        title or boundary refuses, as does a report
        whose entry ids already stand here.
        """
        validated = build_report(report)
        if self._title is not None and (
                validated.title != self._title
                or validated.boundary != self._boundary):
            raise ValueError(
                "this registry already holds a stand-up under a "
                "different title or boundary")
        for entry in validated.entries:
            if entry.entry_id is not None \
                    and entry.entry_id in self._entries:
                raise ValueError(
                    f"an entry named {entry.entry_id!r} already exists")
        self._title = validated.title
        self._boundary = validated.boundary
        for entry in validated.entries:
            self.register_entry(entry)
        return self.report()

    def get_entry(self, entry_id: Any) -> ProgressEntry:
        """The entry one id names among the held entries."""
        wanted = normalize_member_id(entry_id)
        if wanted not in self._entries:
            raise KeyError(f"unknown entry: {wanted!r}")
        return self._entries[wanted]

    def list_entries(self) -> Tuple[ProgressEntry, ...]:
        """Every held entry, in the order they were held."""
        return tuple(self._entries[i] for i in self._order)

    def entries_for(self, status: Any) -> Tuple[ProgressEntry, ...]:
        """Every held entry standing in one state, in held order."""
        wanted = normalize_status(status)
        return tuple(e for e in self.list_entries() if e.status == wanted)

    def report(self) -> StandUpReport:
        """The held entries as one validated stand-up report."""
        if self._title is None or self._boundary is None:
            raise ValueError("no stand-up report is held yet")
        return StandUpReport(
            title=self._title, boundary=self._boundary,
            entries=self.list_entries())

    def digest(self) -> StandUpDigest:
        """The held report's digest, derived at call time."""
        return digest_stand_up(self.report())


# ---------------------------------------------------------------------
# Stand-up news, shaped as session records.
# ---------------------------------------------------------------------


def entry_record(entry: Any) -> Dict[str, Any]:
    """The session-news record of one entry."""
    current = entry if isinstance(entry, ProgressEntry) else build_entry(entry)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"{current.member} reports {current.title}: "
        f"{_status_words(current.status)}.")
    return record


def report_record(report: Any) -> Dict[str, Any]:
    """The session-news record of one report."""
    current = report if isinstance(report, StandUpReport) else build_report(report)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Stand-up at {current.boundary}: {record['entry_count']} "
        f"item(s) of work stand reported.")
    return record


def digest_record(digest: Any, report: Any = None) -> Dict[str, Any]:
    """The session-news record of one digest.

    With *report* given, the digest is first
    judged against the digest that report derives.
    """
    current = validate_digest(digest, report)
    record = current.to_record()
    record["news"] = True
    counts = current.counts()
    record["headline"] = (
        f"Stand-up at {current.boundary}: {counts['done']} done, "
        f"{counts['doing']} doing, {counts['blocked']} blocked, "
        f"{counts['needs_you']} needs-you.")
    return record


def plain_words(entry: Any) -> str:
    """One entry, in one plain sentence."""
    current = entry if isinstance(entry, ProgressEntry) else build_entry(entry)
    return (
        f"{current.member} - {current.title} "
        f"({_status_words(current.status)}): {current.detail}")


def digest_plain_words(source: Any) -> str:
    """One digest in plain words: every section, in full.

    Accepts a StandUpDigest, a StandUpReport or a
    StandUpRegistry. Each section names its items
    by title in report order, and an empty section
    says so plainly - nothing is hidden by an
    empty section and nothing is invented for one.
    """
    if isinstance(source, StandUpDigest):
        digest = source
        titles: Optional[Dict[str, str]] = None
    elif isinstance(source, (StandUpReport, StandUpRegistry)):
        report = source.report() if isinstance(
            source, StandUpRegistry) else source
        digest = digest_stand_up(report)
        titles = {e.entry_id: e.title for e in report.entries}
    else:
        raise ValueError(f"a stand-up digest is needed, got {source!r}")
    lines = [f"{digest.title} (boundary: {digest.boundary})"]
    for status in STATUS_KINDS:
        ids = digest.section(status)
        words = _status_words(status)
        if not ids:
            lines.append(f"{words}: nothing.")
            continue
        named = ", ".join(
            (titles or {}).get(entry_id, entry_id) for entry_id in ids)
        lines.append(f"{words}: {named}.")
    return "\n".join(lines)


# ---------------------------------------------------------------------
# Screens: the formatters and the shared /standup grammar.
# ---------------------------------------------------------------------


def _source_report(source: Any) -> StandUpReport:
    if source is None:
        return load_stand_up()
    if isinstance(source, StandUpRegistry):
        return source.report()
    if isinstance(source, StandUpReport):
        return source
    raise ValueError(f"a stand-up report is needed, got {source!r}")


def format_entry(entry: Any) -> str:
    """One entry as a screen line, with its state."""
    current = entry if isinstance(entry, ProgressEntry) else build_entry(entry)
    return (
        f"{current.member} / {current.entry_id or '-'} "
        f"[{_status_words(current.status)}]: {current.title} - "
        f"{current.detail}")


def format_entries(source: Any = None, status: Any = None) -> str:
    """Entries of one report, in report order.

    With *status* given, only the entries standing
    in that state are shown.
    """
    report = _source_report(source)
    entries = report.entries if status is None else report.entries_for(status)
    lines = [format_entry(entry) for entry in entries]
    if not lines:
        lines.append("No items stand reported.")
    return "\n".join(lines)


def format_digest(source: Any = None) -> str:
    """The digest of one report as screen lines, section by section."""
    report = _source_report(source)
    digest = digest_stand_up(report)
    lines = [
        f"Digest at {digest.boundary}: {digest.total()} item(s) - "
        + ", ".join(
            f"{digest.counts()[s]} {_status_words(s)}" for s in STATUS_KINDS)
        + "."]
    for status in STATUS_KINDS:
        entries = report.entries_for(status)
        lines.append(f"{_status_words(status)} ({len(entries)}):")
        if entries:
            lines.extend(format_entry(entry) for entry in entries)
        else:
            lines.append("Nothing here.")
    return "\n".join(lines)


def format_status_kinds() -> str:
    """The four states, in digest order, as one line."""
    return "Status kinds: " + ", ".join(
        _status_words(status) for status in STATUS_KINDS)


def format_stand_up_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /standup.

    With nothing named, the shipped example
    stand-up is shown - the example this slice
    ships - so the screen is never empty.
    """
    report = _source_report(source)
    lines = ["Stand-ups (M-134) - " + PLAIN_EXPLANATION, ""]
    lines.append(digest_plain_words(report))
    lines.append("")
    lines.append(format_digest(report))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_stand_up_args(args: Any) -> Tuple[str, Optional[str]]:
    """Parse the /standup grammar both surfaces share.

    No words (or ``show`` / ``list``) shows the
    stand-up; ``digest`` shows the derived digest;
    a state word (``done`` / ``doing`` / ``blocked``
    / ``needs-you``) shows that section;
    ``entry <entry-id>`` shows one entry; ``kinds``
    lists the four states. Anything else is a
    usage error naming the grammar. Returns
    ``(action, value-or-None)``.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() in ("show", "list"):
        return ("show", None)
    words = text.split()
    head = words[0].lower()
    if head == "digest" and len(words) == 1:
        return ("digest", None)
    if head == "kinds" and len(words) == 1:
        return ("kinds", None)
    if head == "entry" and len(words) == 2:
        try:
            return ("entry", normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if len(words) == 1:
        try:
            return ("section", normalize_status(words[0]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
