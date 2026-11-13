"""Decision records (All-Features roadmap slice M-156).

Part VII continues. The roadmap's words:
``choices made in session (library picked, road
not taken, why) written as small ADRs into the
project docs by the Scribe.``

What already shipped, and what this slice adds:

* A project's facts already ship as data: the
  project memory map (``core/project_memory_map.py``,
  M-150) holds the project's decisions among its
  facts, in its closed ``decision`` section, and
  session memory across days
  (``core/session_memory.py``, M-153) carries those
  decision entries onward as standing decisions.
  The Scribe - the office of memory & docs - keeps
  that map under the method charter's
  Project Memory Map tenet (``PROJECT_MEMORY_MAP``),
  whose directives name decisions among the things
  kept current. What no shipped layer holds is the
  choice itself as a record: what was chosen, the
  roads not taken, and why - the small ADR the
  Scribe writes into the project docs. (The search
  was made: no Scribe ADR machinery, no decision-
  record module and no ADR formatter ships in the
  tree; the Scribe stands in the tree as an office
  and as the cost court's ledger keeper, never as
  an ADR road.)
* This slice is that holding, as a pure layer: a
  decision record is one choice made in session,
  validated as data WITH ITS PROVENANCE WHOLE -
  the session it was decided in, the day it was
  decided on, and where it was read from - standing
  in a closed set of states (proposed, accepted,
  superseded), a superseded record naming the
  record that superseded it. Records render as
  small ADRs in a deterministic markdown form: the
  exact text that would land in the project docs.
  The shipped data file
  (``mythic_agent/data/decision_records.yaml``)
  holds one example book in exactly the shape a
  real book file takes, a loader reads a book file
  anywhere on disk, the composition roads read the
  shipped project memory map's decision entries
  and the shipped session memory's standing
  decisions onto records BY IMPORT, the scribe
  road reads the Project Memory Map tenet's
  directives BY IMPORT, the decision panel is
  DERIVED from the whole book (every record
  standing whole, in a settled order), records are
  shaped as session news, and a small in-memory
  registry model holds records one by one. The
  agent layer owns holding a book for a session
  and drafting records from the session's standing
  decisions.

Honesty rules, enforced here and pinned by tests:

* **Provenance, always.** A record carries the
  session it was decided in, the day it was
  decided on and where it was read from. A record
  with no provenance refuses - choices are never
  recorded anonymously, and a bare memory-map
  entry or standing decision becomes a record
  only when the frame words are named with it.
* **Supersession is explicit, never silent.** A
  record stands proposed until it is accepted. A
  superseded record names the record that
  superseded it - a record the same book holds -
  and a record in any other state names no
  superseder. There is no road here that accepts
  or supersedes by capture, by age or by count.
* **Composed, never duplicated.** Records are the
  shipped project memory map's decision-section
  entries and the shipped session memory's
  standing decisions, read onto this layer by
  import, and the Scribe's keeping doctrine is
  the shipped method charter's own Project Memory
  Map tenet, read by import. No second taxonomy
  of decisions is invented here.
* **The panel is derived, never stored loose.**
  Its rows are the book's records carried whole,
  in settled order (accepted first, then
  proposed, then superseded; within a state, by
  session, then record title), and its totals are
  the records' own counts; a stored panel or book
  whose rows, totals, counts or account disagree
  with the derived shape refuses.
* **Rendering only - data only.** A record here
  is validated data and its ADR is rendered text:
  no model is called, no project docs are
  written, no workspace file is touched, and
  nothing persists beyond the session journal
  news the agent layer publishes. Writing the
  rendered ADR into a project's docs is a live
  act no shipped road performs, so this layer
  does not perform it either: the formatter is
  the whole road.
* **Malformed refuses.** A duplicate record id
  in one book, the same choice named twice by
  one session, a superseded record naming a
  record the book does not hold (or itself), and
  unknown keys in a record, a panel or a book
  mapping all raise instead of being skipped or
  guessed at.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..resources import load_resource
from .crew_members import normalize_member_id
from .method_charter import load_charter
from .project_memory_map import MemoryMapEntry
from .project_memory_map import validate_entry as _validate_map_entry
from .session_memory import StandingDecision
from .session_memory import validate_decision as _validate_standing
from .validation import ValidationError

__all__ = [
    "DECISION_RECORDS_RESOURCE",
    "DECISION_RECORDS_SCHEMA",
    "DECISION_RECORDS_SLICE",
    "DECISION_SCRIBE_TENET",
    "DECISION_STATUSES",
    "PLAIN_EXPLANATION",
    "USAGE",
    "DecisionBook",
    "DecisionPanel",
    "DecisionPanelRow",
    "DecisionRecord",
    "DecisionRegistry",
    "DecisionStatusCount",
    "accepted_records",
    "book_record",
    "build_book",
    "build_panel",
    "build_record",
    "build_row",
    "derive_panel",
    "format_accepted",
    "format_adr",
    "format_adrs",
    "format_decision_records_screen",
    "format_panel",
    "format_record",
    "format_records",
    "load_decision_records",
    "load_decision_records_file",
    "normalize_decision_status",
    "panel_plain_words",
    "panel_record",
    "parse_decision_records_args",
    "plain_words",
    "record_from_map_entry",
    "record_from_standing_decision",
    "record_record",
    "records_from_memory_map",
    "records_from_session_memory",
    "scribe_directives",
    "validate_book",
    "validate_panel",
    "validate_record",
    "validate_row",
]

DECISION_RECORDS_SLICE = "M-156"

#: The packaged data resource holding the example book.
DECISION_RECORDS_RESOURCE = "decision_records.yaml"

#: The schema word a decision-records file must carry.
DECISION_RECORDS_SCHEMA = "mythic.decision_records/1"

#: The method charter's Project Memory Map tenet
#: key: the plug whose directives are the Scribe's
#: keeping doctrine for decisions, read by import.
DECISION_SCRIBE_TENET = "project-memory-map"

#: The states one decision record may stand in: a
#: choice drafted and awaiting its word
#: (``proposed``), a choice standing as the
#: project's road (``accepted``), or a choice an
#: accepted record has replaced (``superseded``) -
#: the ADR states, in the repo's own plain words.
DECISION_STATUSES = ("proposed", "accepted", "superseded")

_STATUS_ALIASES = {
    "proposed": "proposed",
    "draft": "proposed",
    "pending": "proposed",
    "accepted": "accepted",
    "decided": "accepted",
    "agreed": "accepted",
    "superseded": "superseded",
    "replaced": "superseded",
}

#: The order records stand in on the decision
#: panel: what stands as the road first, then what
#: awaits its word, then what was replaced.
_PANEL_STATUS_ORDER = ("accepted", "proposed", "superseded")

_RECORD_KEYS = frozenset({
    "record_id", "id", "status", "state",
    "title", "name", "decision", "choice",
    "alternatives", "roads_not_taken", "not_taken",
    "rationale", "why", "reason",
    "context", "consequences", "effects",
    "session_ref", "session",
    "decided_on", "day", "date",
    "source", "superseded_by", "superseded",
    "replaced_by",
})

_ROW_KEYS = frozenset({
    "status", "record_id", "id", "title",
    "decision", "session_ref",
})

_STATUS_COUNT_KEYS = frozenset({"status", "items", "count"})

_PANEL_KEYS = frozenset({
    "panel_id", "id", "rows", "records",
    "total_items", "total", "total_accepted",
    "total_proposed", "total_superseded",
    "status_counts", "states",
    "account", "statements",
})

_BOOK_KEYS = frozenset({"title", "name"})

_DECISION_BOOK_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "canon_note", "guide", "records", "panels",
})

#: The shipped example book's title, held to this
#: by the loader's example check.
_EXAMPLE_TITLE = "Decision records at the M-155 slice boundary"

#: The shipped example's record ids, in held
#: order, pinned by the loader.
_EXAMPLE_RECORD_IDS = (
    "record-stdlib-http", "record-httpx-client",
    "record-rune-index")

#: The shipped example's first record and the
#: session it was decided in, pinned by the loader.
_EXAMPLE_FIRST_RECORD_ID = "record-stdlib-http"

_EXAMPLE_FIRST_RECORD_SESSION = "session-provider-ocean"

#: The shipped example's one panel id, and its rows
#: in panel order, pinned by the loader.
_EXAMPLE_PANEL_ID = "panel-m155-boundary"

_EXAMPLE_PANEL_ROW_IDS = (
    "record-httpx-client", "record-rune-index",
    "record-stdlib-http")

_EXAMPLE_PANEL_ACCOUNT = (
    "The decision panel holds 3 records: accepted 1, "
    "proposed 1, superseded 1.",
    "Records stand accepted first, then proposed, "
    "then superseded; within a state, by session, "
    "then record title - so two panels of one book "
    "diff cleanly, line by line.",
    "A superseded record names the record that "
    "superseded it, and it stands in the panel with "
    "its provenance whole - the session it was "
    "decided in, the day, and where it was read from.",
    "The panel is read off the book at call time - "
    "it is derived, never stored loose.",
)

PLAIN_EXPLANATION = (
    "Decision records: the choices made in session "
    "- what was chosen, the roads not taken, and "
    "why - held as small ADRs by the Scribe, with "
    "provenance whole. A decision record is one "
    "choice carried with the session it was decided "
    "in, the day it was decided on and where it was "
    "read from, standing proposed, accepted or "
    "superseded; a superseded record names the "
    "record that superseded it. Each record renders "
    "as a small ADR in a deterministic markdown "
    "form - the exact text that would land in the "
    "project docs. The decision panel is derived "
    "from the book at call time: every record "
    "standing whole, accepted first, then proposed "
    "and superseded. This layer holds and renders "
    "records as data only: it calls no model, "
    "writes no project docs and persists nothing."
)

USAGE = (
    "Usage: /decisions, /decisions show, "
    "/decisions record <record-id>, "
    "/decisions adr <record-id>, "
    "/decisions accepted, "
    "/decisions panel"
)


def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_title(value: Any, what: str = "a title") -> str:
    text = _clean_text(value, what)
    if len(text) > 120 or "\x00" in text:
        raise ValueError(
            f"{what} must be plain text of at most "
            f"120 characters, got {len(text)} characters")
    return text


def _check_long_text(value: Any, what: str) -> str:
    text = _clean_text(value, what)
    if len(text) > 2000 or "\x00" in text:
        raise ValueError(
            f"{what} must be plain text of at most "
            f"2000 characters, got {len(text)} characters")
    return text


def _check_account(value: Any) -> Tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(
            f"an account must be a list of statements, "
            f"got {value!r}")
    account = tuple(
        _check_long_text(a, "an account statement")
        for a in value)
    if not account:
        raise ValueError("an account carries at least one statement")
    if len(account) > 16:
        raise ValueError(
            f"an account carries at most 16 statements, "
            f"got {len(account)}")
    if len(set(account)) != len(account):
        raise ValueError("an account states one statement twice")
    return account


def _pick_any(mapping: Dict[str, Any], spellings: Tuple[str, ...],
              what: str) -> Any:
    values = [mapping[s] for s in spellings if s in mapping]
    if not values:
        return None
    if any(value != values[0] for value in values[1:]):
        raise ValueError(f"a record names two different {what}")
    return values[0]


def _check_count(value: Any, what: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{what} must be a count, got {value!r}")
    if value < 0:
        raise ValueError(f"{what} must not be negative, got {value!r}")
    return value


def _check_session(value: Any, what: str = "a session") -> str:
    """One session name, judged as one plain word.

    Session names on this layer are the shipped id
    shape (letters, digits, dashes, underscores and
    dots, case kept) - the same word a registry id
    takes - so the session a choice was decided in
    can be compared exactly.
    """
    try:
        return normalize_member_id(value)
    except ValueError:
        raise ValueError(
            f"{what} must be one plain session word, "
            f"got {value!r}") from None


def _check_day(value: Any) -> str:
    text = _clean_text(value, "a record's decided-on day")
    try:
        parsed = date.fromisoformat(text)
    except ValueError:
        raise ValueError(
            f"a record's decided-on day must be an ISO "
            f"date (YYYY-MM-DD), got {text!r}") from None
    if parsed.isoformat() != text:
        raise ValueError(
            f"a record's decided-on day must be an ISO "
            f"date (YYYY-MM-DD), got {text!r}")
    return text


def _check_alternatives(value: Any) -> Tuple[str, ...]:
    if isinstance(value, (str, bytes)) \
            or not isinstance(value, (list, tuple)):
        raise ValueError(
            f"a record's roads not taken must be a list, "
            f"got {value!r}")
    roads = tuple(
        _check_long_text(item, "a road not taken")
        for item in value)
    if not roads:
        raise ValueError(
            "a record names at least one road not taken - "
            "a choice with no alternative was no choice")
    if len(roads) > 8:
        raise ValueError(
            f"a record names at most 8 roads not taken, "
            f"got {len(roads)}")
    if len(set(roads)) != len(roads):
        raise ValueError("a record names one road not taken twice")
    return roads


def normalize_decision_status(value: Any) -> str:
    """The canonical decision status a word names.

    A status is one of :data:`DECISION_STATUSES` -
    ``proposed`` (drafted, awaiting its word),
    ``accepted`` (standing as the project's road)
    or ``superseded`` (replaced by a named record)
    - read case-insensitively, with ``draft`` and
    ``pending`` read onto ``proposed``, ``decided``
    and ``agreed`` onto ``accepted`` and
    ``replaced`` onto ``superseded``. Anything else
    raises, plainly naming the three.
    """
    if isinstance(value, str):
        wanted = _STATUS_ALIASES.get(value.strip().lower())
        if wanted is not None:
            return wanted
    raise ValueError(
        "a record's status must be one of %s, got %r"
        % ("/".join(DECISION_STATUSES), value))


# ---------------------------------------------------------------------
# The decision record: one choice made in session, provenance whole.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class DecisionRecord:
    """One choice made in session, as a small ADR record.

    ``status`` is the record's standing in the
    closed set - ``proposed``, ``accepted`` or
    ``superseded``; ``title`` names the choice;
    ``decision`` is what was chosen, in plain
    words; ``alternatives`` are the roads not
    taken, each named; ``rationale`` says why;
    ``context`` is the situation the choice was
    made in; ``consequences`` say what follows
    from it. The provenance stands whole beside
    it: ``session_ref`` is the session it was
    decided in, ``decided_on`` the day, and
    ``source`` names where it was read from. A
    superseded record names its superseder in
    ``superseded_by`` - a record the same book
    holds, judged by the book - and a record in
    any other state names none: supersession is
    explicit, never silent. A record with any
    provenance word missing is no record at all.
    """

    status: str
    title: str
    decision: str
    alternatives: Tuple[str, ...]
    rationale: str
    context: str
    consequences: str
    session_ref: str
    decided_on: str
    source: str
    record_id: Optional[str] = None
    superseded_by: Optional[str] = None

    def __post_init__(self) -> None:
        if self.record_id is not None:
            object.__setattr__(
                self, "record_id",
                normalize_member_id(self.record_id))
        object.__setattr__(
            self, "status", normalize_decision_status(self.status))
        object.__setattr__(
            self, "title", _check_title(self.title, "a record's title"))
        object.__setattr__(
            self, "decision",
            _check_long_text(self.decision, "a record's decision"))
        object.__setattr__(
            self, "alternatives",
            _check_alternatives(self.alternatives))
        object.__setattr__(
            self, "rationale",
            _check_long_text(self.rationale, "a record's rationale"))
        object.__setattr__(
            self, "context",
            _check_long_text(self.context, "a record's context"))
        object.__setattr__(
            self, "consequences",
            _check_long_text(
                self.consequences, "a record's consequences"))
        object.__setattr__(
            self, "session_ref",
            _check_session(
                self.session_ref, "a record's session"))
        object.__setattr__(
            self, "decided_on", _check_day(self.decided_on))
        object.__setattr__(
            self, "source",
            _check_title(self.source, "a record's source"))
        if self.status == "superseded":
            if self.superseded_by is None or (
                    isinstance(self.superseded_by, str)
                    and not self.superseded_by.strip()):
                raise ValueError(
                    "a superseded record names the record that "
                    "superseded it; supersession is explicit, "
                    "never silent")
            object.__setattr__(
                self, "superseded_by",
                normalize_member_id(self.superseded_by))
            if self.record_id is not None \
                    and self.superseded_by == self.record_id:
                raise ValueError(
                    "a record cannot supersede itself")
        else:
            if self.superseded_by not in (None, ""):
                raise ValueError(
                    "only a superseded record names a superseder - "
                    "this record stands in the %s state" % self.status)
            object.__setattr__(self, "superseded_by", None)

    @property
    def status_index(self) -> int:
        """This record's status's place in panel order (derived)."""
        return _PANEL_STATUS_ORDER.index(self.status)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "decision_record",
            "slice": DECISION_RECORDS_SLICE,
            "record_id": self.record_id,
            "status": self.status,
            "title": self.title,
            "decision": self.decision,
            "alternatives": list(self.alternatives),
            "rationale": self.rationale,
            "context": self.context,
            "consequences": self.consequences,
            "session_ref": self.session_ref,
            "decided_on": self.decided_on,
            "source": self.source,
            "superseded_by": self.superseded_by,
        }


def _frame_words(session_ref: Any, decided_on: Any,
                 alternatives: Any, rationale: Any,
                 context: Any, consequences: Any
                 ) -> Tuple[str, str, Tuple[str, ...], str, str, str]:
    """The words a composed record must carry, or a refusal.

    A memory-map decision entry or a standing
    session decision becomes a record only when
    the words are named with it: the session it
    was decided in, the day, the roads not taken,
    why, the context and the consequences. A
    missing word refuses plainly - never a guessed
    or empty provenance, and never an invented
    road not taken.
    """
    if session_ref is None or decided_on is None \
            or alternatives is None or rationale is None \
            or context is None or consequences is None:
        raise ValueError(
            "a decision record must carry its frame: the "
            "session it was decided in, the day it was "
            "decided on, the roads not taken, why, the "
            "context it was decided in and what follows "
            "from it")
    return (
        _check_session(session_ref, "a record's session"),
        _check_day(decided_on),
        _check_alternatives(alternatives),
        _check_long_text(rationale, "a record's rationale"),
        _check_long_text(context, "a record's context"),
        _check_long_text(consequences, "a record's consequences"))


def validate_record(record: Any, *, session_ref: Any = None,
                    decided_on: Any = None,
                    alternatives: Any = None, rationale: Any = None,
                    context: Any = None, consequences: Any = None,
                    status: Any = None, superseded_by: Any = None
                    ) -> DecisionRecord:
    """Validate one decision record into a DecisionRecord.

    Accepts a record; a shipped memory-map entry
    standing in the map's decision section or a
    shipped session-memory standing decision (whose
    title, decision and source are read onto the
    record - the shipped memory layers composed by
    import - with the frame words named beside it:
    *session_ref*, *decided_on*, *alternatives*,
    *rationale*, *context* and *consequences*, and
    an optional *status* - a drafted record stands
    ``proposed`` unless a state is named - and
    *superseded_by* where a superseded state is
    named); or a mapping naming a ``status`` (or
    ``state``), a ``title`` (or ``name``), a
    ``decision`` (or ``choice``), ``alternatives``
    (or ``roads_not_taken`` / ``not_taken``), a
    ``rationale`` (or ``why`` / ``reason``), a
    ``context``, ``consequences`` (or ``effects``),
    a ``session_ref`` (or ``session``), a
    ``decided_on`` (or ``day`` / ``date``), a
    ``source``, an optional ``superseded_by`` (or
    ``superseded`` / ``replaced_by``) and an
    optional ``record_id`` (or ``id``). A map entry
    of any other section refuses, plainly. Naming
    two spellings of one field with different
    values refuses, and unknown keys refuse.
    """
    if isinstance(record, DecisionRecord):
        return record
    if isinstance(record, MemoryMapEntry):
        if record.section != "decision":
            raise ValueError(
                "only a memory map entry in the decision "
                "section stands as a decision record, got "
                f"a {record.section} entry")
        session, day, roads, why, situation, follows = _frame_words(
            session_ref, decided_on, alternatives, rationale,
            context, consequences)
        return DecisionRecord(
            status="proposed" if status is None else status,
            title=record.title, decision=record.detail,
            alternatives=roads, rationale=why, context=situation,
            consequences=follows, session_ref=session,
            decided_on=day, source=record.source,
            record_id=record.entry_id,
            superseded_by=superseded_by)
    if isinstance(record, StandingDecision):
        session, day, roads, why, situation, follows = _frame_words(
            session_ref, decided_on, alternatives, rationale,
            context, consequences)
        return DecisionRecord(
            status="proposed" if status is None else status,
            title=record.title, decision=record.decision,
            alternatives=roads, rationale=why, context=situation,
            consequences=follows, session_ref=session,
            decided_on=day, source=record.source,
            record_id=record.decision_id,
            superseded_by=superseded_by)
    if not isinstance(record, dict):
        raise ValueError(
            f"a decision record must be a mapping, "
            f"got {record!r}")
    unknown = set(record) - _RECORD_KEYS
    if unknown:
        raise ValueError(
            "unknown record keys: %s"
            % ", ".join(sorted(unknown)))

    def _needed(spellings: Tuple[str, ...], what: str) -> Any:
        value = _pick_any(record, spellings, what)
        if value is None:
            raise ValueError(f"a decision record is missing its {what}")
        return value

    kwargs: Dict[str, Any] = {
        "status": _needed(("status", "state"), "status"),
        "title": _needed(("title", "name"), "title"),
        "decision": _needed(("decision", "choice"), "decision"),
        "alternatives": _needed(
            ("alternatives", "roads_not_taken", "not_taken"),
            "roads not taken"),
        "rationale": _needed(
            ("rationale", "why", "reason"), "rationale"),
        "context": _needed(("context",), "context"),
        "consequences": _needed(
            ("consequences", "effects"), "consequences"),
        "session_ref": _needed(
            ("session_ref", "session"), "session"),
        "decided_on": _needed(
            ("decided_on", "day", "date"), "decided-on day"),
        "source": _needed(("source",), "source"),
    }
    superseder = _pick_any(
        record, ("superseded_by", "superseded", "replaced_by"),
        "superseders")
    if superseder is not None:
        kwargs["superseded_by"] = superseder
    named_id = _pick_any(record, ("record_id", "id"), "record ids")
    if named_id is not None:
        kwargs["record_id"] = named_id
    return DecisionRecord(**kwargs)


_FRAME_KEYS = (
    "session_ref", "decided_on", "alternatives", "rationale",
    "context", "consequences", "status", "superseded_by")


def build_record(record: Any = None, **kwargs: Any) -> DecisionRecord:
    """Build one validated record, from a mapping or field words.

    Frame words for a composed entry or standing
    decision (``session_ref``, ``decided_on``,
    ``alternatives``, ``rationale``, ``context``,
    ``consequences``, and an optional ``status`` /
    ``superseded_by``) may ride in the field words;
    in a mapping they are the record's own fields.
    """
    frame = {
        key: kwargs.pop(key) for key in _FRAME_KEYS if key in kwargs}
    if isinstance(record, DecisionRecord) and not kwargs and not frame:
        return record
    if isinstance(record, (MemoryMapEntry, StandingDecision)):
        if kwargs:
            raise ValueError(
                "a composed record takes only its frame words")
        return validate_record(record, **frame)
    if isinstance(record, dict) or record is None:
        merged: Dict[str, Any] = {}
        if isinstance(record, dict):
            merged.update(record)
        merged.update(frame)
        merged.update(kwargs)
        return validate_record(merged)
    raise ValueError(
        f"a decision record must be a mapping, got {record!r}")


def _check_record_ref(value: Any) -> DecisionRecord:
    if isinstance(value, DecisionRecord):
        return value
    if isinstance(value, dict):
        return validate_record(value)
    raise ValueError(f"a decision record is needed, got {value!r}")


# ---------------------------------------------------------------------
# The decision panel: every record carried whole, derived.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class DecisionPanelRow:
    """One record carried whole into the panel, with its standing.

    ``status`` is the record's own standing;
    ``record_id`` names the record; ``title`` and
    ``decision`` are the record's own words;
    ``session_ref`` is the record's provenance
    head - the session it was decided in.
    :func:`validate_row` judged against its record
    refuses a row whose fields disagree with the
    row they derive - a panel row can never
    re-home a choice or soften its standing.
    """

    status: str
    record_id: str
    title: str
    decision: str
    session_ref: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "status", normalize_decision_status(self.status))
        object.__setattr__(
            self, "record_id",
            normalize_member_id(self.record_id))
        object.__setattr__(
            self, "title", _check_title(self.title, "a row's title"))
        object.__setattr__(
            self, "decision",
            _check_long_text(self.decision, "a row's decision"))
        object.__setattr__(
            self, "session_ref",
            _check_session(self.session_ref, "a row's session"))

    @property
    def sort_key(self) -> Tuple[int, str, str]:
        """This row's place in panel order (derived).

        Rows stand status first (accepted, proposed,
        superseded, in that settled order); within a
        state, by session, then record title.
        """
        return (
            _PANEL_STATUS_ORDER.index(self.status),
            self.session_ref, self.title)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "decision_panel_row",
            "slice": DECISION_RECORDS_SLICE,
            "status": self.status,
            "record_id": self.record_id,
            "title": self.title,
            "decision": self.decision,
            "session_ref": self.session_ref,
        }


def _row_for_record(record: DecisionRecord) -> DecisionPanelRow:
    return DecisionPanelRow(
        status=record.status,
        record_id=record.record_id,
        title=record.title, decision=record.decision,
        session_ref=record.session_ref)


def _check_row_ref(value: Any) -> DecisionPanelRow:
    if isinstance(value, DecisionPanelRow):
        return value
    if isinstance(value, dict):
        unknown = set(value) - _ROW_KEYS
        if unknown:
            raise ValueError(
                "unknown row keys: %s" % ", ".join(sorted(unknown)))

        def _needed(spellings: Tuple[str, ...], what: str) -> Any:
            picked = _pick_any(value, spellings, what)
            if picked is None:
                raise ValueError(f"a row is missing its {what}")
            return picked

        return DecisionPanelRow(
            status=_needed(("status",), "status"),
            record_id=_needed(("record_id", "id"), "record id"),
            title=_needed(("title",), "title"),
            decision=_needed(("decision",), "decision"),
            session_ref=_needed(("session_ref",), "session"))
    raise ValueError(f"a panel row is needed, got {value!r}")


def validate_row(row: Any, record: Any = None) -> DecisionPanelRow:
    """Validate one panel row into a DecisionPanelRow.

    Accepts a row or a mapping naming a ``status``,
    a ``record_id`` (or ``id``), a ``title``, a
    ``decision`` and a ``session_ref``. With
    *record* given, the row is judged against the
    row derived from that record: a stored row
    whose fields disagree with the derived row
    refuses.
    """
    current = _check_row_ref(row)
    if record is not None:
        checked_record = _check_record_ref(record)
        derived = _row_for_record(checked_record)
        if current != derived:
            raise ValueError(
                "a stored row disagrees with the row "
                "derived from its record")
    return current


def build_row(row: Any = None, record: Any = None,
              **kwargs: Any) -> DecisionPanelRow:
    """Build one validated row, from a mapping or field words."""
    if isinstance(row, DecisionPanelRow) and not kwargs:
        return validate_row(row, record)
    if isinstance(row, dict) or row is None:
        merged: Dict[str, Any] = {}
        if isinstance(row, dict):
            merged.update(row)
        merged.update(kwargs)
        return validate_row(merged, record)
    return validate_row(row, record)


@dataclass(frozen=True)
class DecisionStatusCount:
    """One status's count in a panel: its records tallied."""

    status: str
    items: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "status", normalize_decision_status(self.status))
        object.__setattr__(
            self, "items",
            _check_count(self.items, "a status count's items"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "items": self.items,
        }


def _check_status_count_ref(value: Any) -> DecisionStatusCount:
    if isinstance(value, DecisionStatusCount):
        return value
    if isinstance(value, dict):
        unknown = set(value) - _STATUS_COUNT_KEYS
        if unknown:
            raise ValueError(
                "unknown status-count keys: %s"
                % ", ".join(sorted(unknown)))
        status = _pick_any(value, ("status",), "statuses")
        if status is None:
            raise ValueError("a status count is missing its status")
        items = _pick_any(value, ("items", "count"), "counts")
        if items is None:
            raise ValueError("a status count is missing its items")
        return DecisionStatusCount(status=status, items=items)
    raise ValueError(f"a status count is needed, got {value!r}")


def _panel_account(total_items: int, total_accepted: int,
                   total_proposed: int, total_superseded: int
                   ) -> Tuple[str, ...]:
    return (
        f"The decision panel holds {total_items} records: "
        f"accepted {total_accepted}, proposed {total_proposed}, "
        f"superseded {total_superseded}.",
        "Records stand accepted first, then proposed, "
        "then superseded; within a state, by session, "
        "then record title - so two panels of one book "
        "diff cleanly, line by line.",
        "A superseded record names the record that "
        "superseded it, and it stands in the panel with "
        "its provenance whole - the session it was "
        "decided in, the day, and where it was read from.",
        "The panel is read off the book at call time - "
        "it is derived, never stored loose.",
    )


@dataclass(frozen=True)
class DecisionPanel:
    """The decision panel of one book, derived from the whole book.

    ``rows`` are the book's records carried whole,
    in panel order (accepted first, then proposed,
    then superseded; within a state, by session,
    then record title, so two panels of one book
    diff cleanly); ``total_items`` is the record
    count and the three status totals are the rows'
    own counts; ``status_counts`` are the per-status
    tallies in the order their statuses first appear
    in the panel; ``account`` is read off those
    numbers. A panel whose rows stand out of panel
    order, or whose totals are not its own rows'
    counts, refuses at construction;
    :func:`validate_panel` judged against a book
    refuses a stored panel that disagrees with the
    derived one.
    """

    rows: Tuple[DecisionPanelRow, ...] = ()
    total_items: int = 0
    total_accepted: int = 0
    total_proposed: int = 0
    total_superseded: int = 0
    status_counts: Tuple[DecisionStatusCount, ...] = ()
    account: Tuple[str, ...] = ()
    panel_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.panel_id is not None:
            object.__setattr__(
                self, "panel_id",
                normalize_member_id(self.panel_id))
        if isinstance(self.rows, (str, bytes)) \
                or not isinstance(self.rows, (list, tuple)):
            raise ValueError(
                f"a panel's rows must be a list of rows, "
                f"got {self.rows!r}")
        rows = tuple(_check_row_ref(r) for r in self.rows)
        seen = set()
        for row in rows:
            if row.record_id in seen:
                raise ValueError(
                    f"a panel row for record "
                    f"{row.record_id!r} already exists")
            seen.add(row.record_id)
        order = [_PANEL_STATUS_ORDER.index(r.status) for r in rows]
        if order != sorted(order):
            raise ValueError(
                "a panel's rows must stand in panel order "
                "(accepted, then proposed, then superseded)")
        object.__setattr__(self, "rows", rows)
        for field_name, state, what in (
                ("total_accepted", "accepted", "accepted total"),
                ("total_proposed", "proposed", "proposed total"),
                ("total_superseded", "superseded",
                 "superseded total")):
            checked = _check_count(
                getattr(self, field_name), f"a panel's {what}")
            if checked != sum(1 for r in rows if r.status == state):
                raise ValueError(
                    f"a panel's {what} must be its own rows' count")
            object.__setattr__(self, field_name, checked)
        object.__setattr__(
            self, "total_items",
            _check_count(self.total_items, "a panel's total"))
        if self.total_items != len(rows):
            raise ValueError(
                "a panel's total must be its own rows' count")
        if isinstance(self.status_counts, (str, bytes)) \
                or not isinstance(self.status_counts, (list, tuple)):
            raise ValueError(
                f"a panel's status counts must be a list, "
                f"got {self.status_counts!r}")
        status_counts = tuple(
            _check_status_count_ref(c) for c in self.status_counts)
        seen_statuses = set()
        for count in status_counts:
            if count.status in seen_statuses:
                raise ValueError(
                    f"a status count named {count.status!r} "
                    f"already exists")
            seen_statuses.add(count.status)
        object.__setattr__(self, "status_counts", status_counts)
        if sum(c.items for c in status_counts) != self.total_items:
            raise ValueError(
                "a panel's status counts must sum to its own total")
        for count in status_counts:
            if count.items != sum(
                    1 for r in rows if r.status == count.status):
                raise ValueError(
                    "a panel's status counts must be its own "
                    "rows' counts")
        object.__setattr__(self, "account", _check_account(self.account))

    def row_for(self, record_id: Any) -> DecisionPanelRow:
        """The panel row one record names in this panel."""
        wanted = normalize_member_id(record_id)
        for row in self.rows:
            if row.record_id == wanted:
                return row
        raise KeyError(f"no row in the panel: record {wanted!r}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "decision_panel",
            "slice": DECISION_RECORDS_SLICE,
            "panel_id": self.panel_id,
            "rows": [row.to_record() for row in self.rows],
            "total_items": self.total_items,
            "total_accepted": self.total_accepted,
            "total_proposed": self.total_proposed,
            "total_superseded": self.total_superseded,
            "status_counts": [c.to_record() for c in self.status_counts],
            "account": list(self.account),
        }


def _held_records(source: Any) -> Tuple[DecisionRecord, ...]:
    """The records one source holds, in held order."""
    if isinstance(source, DecisionBook):
        return source.records
    if isinstance(source, DecisionRegistry):
        return source.list_records()
    if isinstance(source, (list, tuple)):
        return tuple(_check_record_ref(item) for item in source)
    raise ValueError(f"decision records are needed, got {source!r}")


def derive_panel(source: Any) -> DecisionPanel:
    """Derive the decision panel from one book.

    The rows are the book's records carried whole,
    in panel order: accepted first, then proposed,
    then superseded; within a state, by the
    record's session, then its title. *source* is
    a book or a registry. A source holding no
    record refuses - a panel of nothing is no
    panel.
    """
    records = _held_records(source)
    if not records:
        raise ValueError("a panel needs at least one record")
    rows = []
    for record in records:
        if record.record_id is None:
            raise ValueError(
                "a panel row must name its record - a "
                "record with no id refuses derivation")
        rows.append(_row_for_record(record))
    rows = tuple(sorted(rows, key=lambda r: r.sort_key))
    order: list = []
    tally: Dict[str, int] = {}
    for row in rows:
        if row.status not in tally:
            tally[row.status] = 0
            order.append(row.status)
        tally[row.status] += 1
    status_counts = tuple(
        DecisionStatusCount(status=status, items=tally[status])
        for status in order)
    totals = {
        state: tally.get(state, 0) for state in DECISION_STATUSES}
    return DecisionPanel(
        rows=rows,
        total_items=len(rows),
        total_accepted=totals["accepted"],
        total_proposed=totals["proposed"],
        total_superseded=totals["superseded"],
        status_counts=status_counts,
        account=_panel_account(
            len(rows), totals["accepted"], totals["proposed"],
            totals["superseded"]))


def validate_panel(panel: Any, source: Any = None) -> DecisionPanel:
    """Validate one panel into a DecisionPanel.

    Accepts a panel or a mapping naming ``rows``
    (or ``records``), a ``total_items`` (or
    ``total``), the three status totals,
    ``status_counts`` (or ``states``), an
    ``account`` (or ``statements``) and an optional
    ``panel_id`` (or ``id``). With *source* given
    (a book), the panel is judged against the
    panel derived from that book: a stored panel
    whose rows, totals, status counts or account
    disagree with the derived panel refuses. A
    panel naming no account refuses too.
    """
    if isinstance(panel, DecisionPanel):
        current = panel
    elif isinstance(panel, dict):
        unknown = set(panel) - _PANEL_KEYS
        if unknown:
            raise ValueError(
                "unknown panel keys: %s" % ", ".join(sorted(unknown)))
        rows = _pick_any(panel, ("rows", "records"), "rows")
        if rows is None:
            raise ValueError("a panel is missing its rows")
        total = _pick_any(
            panel, ("total_items", "total"), "totals")
        if total is None:
            raise ValueError("a panel is missing its total items")
        status_counts = _pick_any(
            panel, ("status_counts", "states"), "status counts")
        if status_counts is None:
            raise ValueError("a panel is missing its status counts")
        account = _pick_any(panel, ("account", "statements"), "accounts")
        if account is None:
            raise ValueError("a panel names no account of its own")
        kwargs: Dict[str, Any] = {
            "rows": rows, "total_items": total,
            "status_counts": status_counts, "account": account}
        for field_name in (
                "total_accepted", "total_proposed",
                "total_superseded"):
            value = _pick_any(panel, (field_name,), field_name)
            if value is None:
                raise ValueError(f"a panel is missing its {field_name}")
            kwargs[field_name] = value
        panel_id = _pick_any(panel, ("panel_id", "id"), "panel ids")
        if panel_id is not None:
            kwargs["panel_id"] = panel_id
        current = DecisionPanel(**kwargs)
    else:
        raise ValueError(f"a panel must be a mapping, got {panel!r}")
    if source is not None:
        derived = derive_panel(source)
        if (current.rows != derived.rows
                or current.total_items != derived.total_items
                or current.total_accepted != derived.total_accepted
                or current.total_proposed != derived.total_proposed
                or current.total_superseded != derived.total_superseded
                or current.status_counts != derived.status_counts
                or current.account != derived.account):
            raise ValueError(
                "a stored panel disagrees with the panel "
                "derived from its book")
    return current


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> DecisionPanel:
    """Build one validated panel, from a mapping or field words."""
    if isinstance(panel, DecisionPanel) and not kwargs:
        return validate_panel(panel, source)
    if isinstance(panel, dict) or panel is None:
        merged: Dict[str, Any] = {}
        if isinstance(panel, dict):
            merged.update(panel)
        merged.update(kwargs)
        return validate_panel(merged, source)
    return validate_panel(panel, source)


# ---------------------------------------------------------------------
# The composition roads: the shipped memory layers and charter, by import.
# ---------------------------------------------------------------------


def scribe_directives() -> Tuple[str, ...]:
    """The Scribe's keeping directives for decisions, by import.

    The doctrine this slice executes is the shipped
    method charter's own: its ``project-memory-map``
    tenet (the ``PROJECT_MEMORY_MAP`` plug) is read
    through the charter layer BY IMPORT and its
    directives are returned whole - keep the map
    current, decisions named among its contents,
    updated in the same session as the change it
    records. No second statement of the doctrine is
    kept here.
    """
    return load_charter().tenet(DECISION_SCRIBE_TENET).directives


def record_from_map_entry(entry: Any, *, session_ref: Any,
                          decided_on: Any, alternatives: Any,
                          rationale: Any, context: Any,
                          consequences: Any, status: Any = None,
                          superseded_by: Any = None
                          ) -> DecisionRecord:
    """Build one record from a shipped memory-map decision entry.

    The entry - the project memory map's own record
    in its decision section, judged by the map's
    own validation, then by this layer's standing
    law (an entry of any other section refuses) -
    is read onto a record BY IMPORT: its title, its
    detail standing as the decision itself, and its
    source stand exactly as the map holds them. The
    frame words are named beside it: the session
    the choice was decided in, the day, the roads
    not taken, why, the context and what follows.
    Without all of them, the entry stays a fact of
    its own project - it is not recorded. A drafted
    record stands ``proposed`` unless a state is
    named.
    """
    validated = _validate_map_entry(entry)
    return validate_record(
        validated, session_ref=session_ref,
        decided_on=decided_on, alternatives=alternatives,
        rationale=rationale, context=context,
        consequences=consequences, status=status,
        superseded_by=superseded_by)


def record_from_standing_decision(decision: Any, *,
                                  session_ref: Any,
                                  decided_on: Any,
                                  alternatives: Any,
                                  rationale: Any, context: Any,
                                  consequences: Any,
                                  status: Any = None,
                                  superseded_by: Any = None
                                  ) -> DecisionRecord:
    """Build one record from a shipped standing decision.

    The decision - session memory's own record,
    judged by that layer's own validation - is read
    onto a record BY IMPORT: its title, its
    decision words and its source stand exactly as
    the situation holds them, and its id stands as
    the record's id. The frame words are named
    beside it, exactly as for a map entry. A
    drafted record stands ``proposed`` unless a
    state is named.
    """
    validated = _validate_standing(decision)
    return validate_record(
        validated, session_ref=session_ref,
        decided_on=decided_on, alternatives=alternatives,
        rationale=rationale, context=context,
        consequences=consequences, status=status,
        superseded_by=superseded_by)


def _map_entries(source: Any) -> Tuple[MemoryMapEntry, ...]:
    """The shipped map entries one source holds, judged by the map."""
    from .project_memory_map import MemoryMapBook, MemoryMapRegistry
    if isinstance(source, MemoryMapBook):
        return source.entries
    if isinstance(source, MemoryMapRegistry):
        return source.list_entries()
    if isinstance(source, (list, tuple)):
        return tuple(_validate_map_entry(e) for e in source)
    if isinstance(source, (MemoryMapEntry, dict)):
        return (_validate_map_entry(source),)
    raise ValueError(f"memory map entries are needed, got {source!r}")


def records_from_memory_map(source: Any, *, session_ref: Any,
                            decided_on: Any, alternatives: Any,
                            rationale: Any, context: Any,
                            consequences: Any, status: Any = None,
                            superseded_by: Any = None
                            ) -> Tuple[DecisionRecord, ...]:
    """Records read off the shipped project memory map.

    The map's entries standing in its decision
    section - and only those - are read onto
    records BY IMPORT, judged by the map's own
    validation on the way, under one frame: the
    session the choices were decided in, the day,
    the roads not taken, why, the context and what
    follows, all named. Entries of other sections
    are the map's other facts, never silently
    promoted to choices. Every drafted record
    stands as its named state - ``proposed`` by
    default: drafting accepts nothing.
    """
    return tuple(
        validate_record(
            entry, session_ref=session_ref,
            decided_on=decided_on, alternatives=alternatives,
            rationale=rationale, context=context,
            consequences=consequences, status=status,
            superseded_by=superseded_by)
        for entry in _map_entries(source)
        if entry.section == "decision")


def _standing_decisions(source: Any) -> Tuple[StandingDecision, ...]:
    """The standing decisions one session-memory source holds."""
    from .session_memory import (
        SessionMemoryBook, SessionMemoryRegistry, SessionSituation)
    if isinstance(source, SessionSituation):
        return source.decisions
    if isinstance(source, SessionMemoryBook):
        decisions: list = []
        for situation in source.situations:
            decisions.extend(situation.decisions)
        return tuple(decisions)
    if isinstance(source, SessionMemoryRegistry):
        decisions = []
        for situation in source.list_situations():
            decisions.extend(situation.decisions)
        return tuple(decisions)
    if isinstance(source, (list, tuple)):
        return tuple(
            item if isinstance(item, StandingDecision)
            else _validate_standing(item)
            for item in source)
    raise ValueError(f"standing decisions are needed, got {source!r}")


def records_from_session_memory(source: Any, *, session_ref: Any,
                                decided_on: Any,
                                alternatives: Any,
                                rationale: Any, context: Any,
                                consequences: Any,
                                status: Any = None,
                                superseded_by: Any = None
                                ) -> Tuple[DecisionRecord, ...]:
    """Records read off the shipped session memory.

    The standing decisions of a session situation -
    or of a whole session-memory book or registry -
    are read onto records BY IMPORT: a choice a
    session settled can be drafted as a record for
    the project docs, under one frame (the session,
    the day, the roads not taken, why, the context
    and what follows, all named). The decision's
    own title, words and source stand exactly as
    the situation holds them. Every drafted record
    stands as its named state - ``proposed`` by
    default: drafting accepts nothing.
    """
    return tuple(
        validate_record(
            decision, session_ref=session_ref,
            decided_on=decided_on, alternatives=alternatives,
            rationale=rationale, context=context,
            consequences=consequences, status=status,
            superseded_by=superseded_by)
        for decision in _standing_decisions(source))


def accepted_records(source: Any) -> Tuple[DecisionRecord, ...]:
    """The records standing accepted in one source.

    This derivation is the ONLY road by which a
    record stands as the project's road on this
    layer: the records of *source* (a book or a
    registry) whose status stands accepted, read
    in panel order, each record carried whole -
    its provenance standing beside it exactly as
    it was decided. A proposed record and a
    superseded record stand nowhere here: not yet,
    or no longer. Nothing is written into any
    project's docs - the standing is derived at
    call time, and the ADR is rendered text.
    """
    records = _held_records(source)
    accepted = [item for item in records if item.status == "accepted"]
    return tuple(sorted(
        accepted,
        key=lambda item: (item.session_ref, item.title)))


# ---------------------------------------------------------------------
# The book: records in held order, panels judged.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class DecisionBook:
    """One decision book: its records, in held order.

    ``records`` are the decision records, in held
    order, each with its provenance whole; a
    superseded record is judged against the book
    at construction: its superseder names a record
    the book holds, and no record supersedes
    itself. ``panels`` are the book's derivations -
    decision panels of the whole book, each judged
    against the book by :func:`validate_book`;
    ``canon_note`` is the book's own note. The
    total is the records' own count, judged at
    construction. This book is the book file's
    shape: the shipped example is one book, and a
    real book file is a new file in this shape.
    """

    title: str = ""
    records: Tuple[DecisionRecord, ...] = ()
    panels: Tuple[DecisionPanel, ...] = ()
    canon_note: str = ""
    total_records: Optional[int] = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_title(self.title, "a book's title"))
        if isinstance(self.records, (str, bytes)) \
                or not isinstance(self.records, (list, tuple)):
            raise ValueError(
                f"a book's records must be a list of "
                f"decision records, got {self.records!r}")
        records = tuple(
            _check_record_ref(item) for item in self.records)
        if not records:
            raise ValueError(
                "a decision book holds at least one record")
        seen_ids = set()
        seen_choices = set()
        for record in records:
            if record.record_id is not None:
                if record.record_id in seen_ids:
                    raise ValueError(
                        f"a record named "
                        f"{record.record_id!r} already exists")
                seen_ids.add(record.record_id)
            key = (record.session_ref, record.title)
            if key in seen_choices:
                raise ValueError(
                    f"the choice {record.title!r} already "
                    f"stands in this book from {record.session_ref}")
            seen_choices.add(key)
        for record in records:
            if record.status == "superseded":
                if record.superseded_by not in seen_ids:
                    raise ValueError(
                        f"a superseded record names a record the "
                        f"book does not hold: "
                        f"{record.superseded_by!r}")
        object.__setattr__(self, "records", records)
        if isinstance(self.panels, (str, bytes)) \
                or not isinstance(self.panels, (list, tuple)):
            raise ValueError(
                f"a book's panels must be a list of panels, "
                f"got {self.panels!r}")
        panels = tuple(
            p if isinstance(p, DecisionPanel) else validate_panel(p)
            for p in self.panels)
        seen_panels = set()
        for panel in panels:
            if panel.panel_id is not None:
                if panel.panel_id in seen_panels:
                    raise ValueError(
                        f"a panel named {panel.panel_id!r} "
                        f"already exists")
                seen_panels.add(panel.panel_id)
        object.__setattr__(self, "panels", panels)
        if not isinstance(self.canon_note, str):
            raise ValueError("a book's note must be text")
        object.__setattr__(
            self, "canon_note", self.canon_note.strip())
        given = self.total_records
        if given is None:
            object.__setattr__(self, "total_records", len(records))
        else:
            checked = _check_count(
                given, "a book's total records")
            if checked != len(records):
                raise ValueError(
                    "a book's total records must be its "
                    "own records' count")
            object.__setattr__(self, "total_records", checked)

    def record_for(self, record_id: Any) -> DecisionRecord:
        """The record one id names in this book."""
        wanted = normalize_member_id(record_id)
        for record in self.records:
            if record.record_id == wanted:
                return record
        raise KeyError(f"no record in the book: {wanted!r}")

    def panel_for(self, panel_id: Any) -> DecisionPanel:
        """The stored panel one id names in this book."""
        wanted = normalize_member_id(panel_id)
        for panel in self.panels:
            if panel.panel_id == wanted:
                return panel
        raise KeyError(f"no panel in the book: {wanted!r}")

    def record_ids(self) -> Tuple[str, ...]:
        """Every held record id, in held order."""
        return tuple(
            item.record_id for item in self.records
            if item.record_id)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "decision_book",
            "slice": DECISION_RECORDS_SLICE,
            "title": self.title,
            "record_ids": list(self.record_ids()),
            "record_count": len(self.records),
            "panel_count": len(self.panels),
        }


def validate_book(data: Any, *, require_example: bool = False
                  ) -> DecisionBook:
    """Validate one decision-records mapping into a book.

    The mapping names a ``schema`` (the decision-
    records schema word), a ``guide`` mapping (its
    ``title``), a ``records`` list and an optional
    ``panels`` list. Every record stands on its own
    validation, then the whole is judged: record
    ids unique, every superseded record judged
    against the book's records (a real superseder,
    never itself), and every stored panel judged
    against the book (a panel the book does not
    derive refuses). With ``require_example`` the
    shipped example is held to its pinned shape:
    the pinned title, records and panel, and the
    panel's pinned rows and account word-for-word.
    Problems raise :class:`ValidationError` or
    ``ValueError``.
    """
    if isinstance(data, DecisionBook):
        return data
    if not isinstance(data, dict):
        raise ValidationError(
            f"a decision book must be a mapping, got {data!r}")
    unknown = set(data) - _DECISION_BOOK_KEYS
    if unknown:
        raise ValidationError(
            "unknown decision-book keys: %s"
            % ", ".join(sorted(unknown)))
    if data.get("schema") != DECISION_RECORDS_SCHEMA:
        raise ValidationError(
            f"a decision book must carry schema "
            f"{DECISION_RECORDS_SCHEMA!r}, got {data.get('schema')!r}")
    records = _pick_any(data, ("records",), "records")
    if records is None:
        raise ValidationError(
            "a decision book is missing its records")
    if not isinstance(records, (list, tuple)):
        raise ValidationError(
            "a decision book's records must be a list")
    if data.get("panels") is not None \
            and not isinstance(data["panels"], (list, tuple)):
        raise ValidationError(
            "a decision book's panels must be a list")
    head = data.get("guide") or {}
    if not isinstance(head, dict):
        raise ValidationError(
            "a decision book's guide must be a mapping")
    unknown_head = set(head) - _BOOK_KEYS
    if unknown_head:
        raise ValidationError(
            "unknown guide keys: %s" % ", ".join(sorted(unknown_head)))
    try:
        title = _pick_any(head, ("title", "name"), "titles")
        if title is None:
            raise ValidationError(
                "a decision book is missing its title")
        note = data.get("canon_note") or ""
        if not isinstance(note, str):
            raise ValidationError(
                "a decision book's note must be text")
        book = DecisionBook(
            title=title, records=tuple(records),
            panels=tuple(data.get("panels") or ()),
            canon_note=note)
        for panel in book.panels:
            validate_panel(panel, book)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    if require_example:
        if book.title != _EXAMPLE_TITLE:
            raise ValidationError(
                "the shipped example decision book's title "
                "is not the pinned title")
        if book.record_ids() != _EXAMPLE_RECORD_IDS:
            raise ValidationError(
                "the shipped example's records are not "
                "the pinned records")
        panel = book.panel_for(_EXAMPLE_PANEL_ID)
        if tuple(r.record_id for r in panel.rows) \
                != _EXAMPLE_PANEL_ROW_IDS:
            raise ValidationError(
                "the shipped example panel does not name "
                "its pinned rows in panel order")
        if panel.account != _EXAMPLE_PANEL_ACCOUNT:
            raise ValidationError(
                "the shipped example panel does not carry "
                "its pinned account word-for-word")
        first = book.records[0]
        if first.record_id != _EXAMPLE_FIRST_RECORD_ID \
                or first.session_ref != _EXAMPLE_FIRST_RECORD_SESSION:
            raise ValidationError(
                "the shipped example's first record is not "
                "its pinned record from its pinned session")
    return book


def build_book(book: Any = None, **kwargs: Any) -> DecisionBook:
    """Build one validated book, from a mapping or field words."""
    if isinstance(book, DecisionBook) and not kwargs:
        return book
    if isinstance(book, dict):
        if "schema" in book:
            return validate_book(book)
        merged: Dict[str, Any] = dict(book)
        merged.update(kwargs)
        return DecisionBook(**merged)
    if book is None:
        return DecisionBook(**kwargs)
    raise ValueError(f"a decision book is needed, got {book!r}")


def _book_from(data: Any, *, require_example: bool) -> DecisionBook:
    try:
        return validate_book(data, require_example=require_example)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def load_decision_records(
        data: Optional[Dict[str, Any]] = None) -> DecisionBook:
    """Load and validate the shipped example book (or *data*).

    The shipped file is held to the example check:
    the pinned title, record records and panel -
    the M-155 slice boundary book - so the shipped
    book covers the canon this slice exists to hold.
    """
    raw = data if data is not None else load_resource(
        DECISION_RECORDS_RESOURCE)
    return _book_from(raw, require_example=True)


def load_decision_records_file(path: Any) -> DecisionBook:
    """Load and validate a decision book from a file at *path*.

    Any file in the decision-records shape, anywhere
    on disk, validated whole - a malformed file
    raises :class:`ValidationError` naming the
    problem, and a missing file raises
    ``FileNotFoundError``. The example check is not
    held: a real book stands on its own records.
    """
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _book_from(raw, require_example=False)


# ---------------------------------------------------------------------
# The registry model: one book held record by record.
# ---------------------------------------------------------------------


class DecisionRegistry:
    """One session's decision records, held one by one.

    The registry holds record records, never
    panels: the panel is a derivation, read off the
    whole held book at call time, so nothing here
    can hold a figure stale. A superseded record
    held one by one names a superseder already
    standing here; a whole book is judged as a
    book judges it, against the whole book, before
    its records are held in book order. Drafting accepts
    nothing: a record held here stands in the
    state it was held in.
    """

    def __init__(self, book: Any = None) -> None:
        self._title: Optional[str] = None
        self._records: Dict[str, DecisionRecord] = {}
        self._record_order: list = []
        self._next_record = 1
        if book is not None:
            self.register_book(book)

    def _fresh_record_id(self, held_ids: Any) -> str:
        while f"record-{self._next_record}" in held_ids:
            self._next_record += 1
        fresh = f"record-{self._next_record}"
        self._next_record += 1
        return fresh

    def register_record(self, record: Any) -> DecisionRecord:
        """Register one record into the held book.

        A record with no id is given a deterministic
        ``record-N`` id. A record id already standing
        here refuses, as does a choice one session
        already stands in this book, and a superseded
        record naming a superseder not yet held.
        """
        validated = _check_record_ref(record)
        held_ids = set(self._records)
        if validated.record_id is not None \
                and validated.record_id in held_ids:
            raise ValueError(
                f"a record named "
                f"{validated.record_id!r} already exists")
        for held in self._records.values():
            if (held.session_ref, held.title) == (
                    validated.session_ref, validated.title):
                raise ValueError(
                    f"the choice {validated.title!r} already "
                    f"stands in this book from "
                    f"{validated.session_ref}")
        if validated.status == "superseded" \
                and validated.superseded_by not in held_ids:
            raise ValueError(
                f"a superseded record names a record the book "
                f"does not hold: {validated.superseded_by!r}")
        return self._hold_record(validated)

    def _hold_record(self, validated: DecisionRecord) -> DecisionRecord:
        """Hold one judged record, in held order.

        The caller has already judged the record
        against the held book (its id, its choice and
        its supersession); this is the holding alone,
        with a deterministic ``record-N`` id given to
        a record carrying none.
        """
        if validated.record_id is None:
            validated = replace(
                validated,
                record_id=self._fresh_record_id(set(self._records)))
        self._records[validated.record_id] = validated
        self._record_order.append(validated.record_id)
        return validated

    def register_book(self, book: Any) -> DecisionBook:
        """Register every record of one book, in order.

        The first book held sets the title; a later
        book under a different title refuses, as does
        a book naming a held record id or a choice a
        held session already stands here. The book is
        judged whole before anything is held - as a
        book judges supersession against the whole
        book, a superseded record may name a
        superseder the same book holds later in held
        order - and the records are then held in the
        book's own order. The book's panels are
        derivations, not holdings, and are not held.
        """
        validated = build_book(book)
        if self._title is not None and validated.title != self._title:
            raise ValueError(
                "this registry already holds a decision "
                "book under a different title")
        for record in validated.records:
            if record.record_id in self._records:
                raise ValueError(
                    f"a record named "
                    f"{record.record_id!r} already exists")
            for held in self._records.values():
                if (held.session_ref, held.title) == (
                        record.session_ref, record.title):
                    raise ValueError(
                        f"the choice {record.title!r} already "
                        f"stands in this book from "
                        f"{record.session_ref}")
        known = set(self._records) | {
            item.record_id for item in validated.records}
        for record in validated.records:
            if record.status == "superseded" \
                    and record.superseded_by not in known:
                raise ValueError(
                    f"a superseded record names a record the "
                    f"book does not hold: "
                    f"{record.superseded_by!r}")
        self._title = validated.title
        for record in validated.records:
            self._hold_record(record)
        return self.book()

    def get_record(self, record_id: Any) -> DecisionRecord:
        """The record one id names among the held records."""
        wanted = normalize_member_id(record_id)
        if wanted not in self._records:
            raise KeyError(f"unknown record: {wanted!r}")
        return self._records[wanted]

    def latest_record(self) -> DecisionRecord:
        """The most recently held record."""
        if not self._record_order:
            raise ValueError("no record is held yet")
        return self._records[self._record_order[-1]]

    def list_records(self) -> Tuple[DecisionRecord, ...]:
        """Every held record, in the order they were held."""
        return tuple(
            self._records[item] for item in self._record_order)

    def book(self) -> DecisionBook:
        """The held records as one validated book."""
        if self._title is None:
            raise ValueError("no decision book is held yet")
        return DecisionBook(
            title=self._title, records=self.list_records())

    def panel(self) -> DecisionPanel:
        """Derive the decision panel of the whole held book."""
        return derive_panel(self)

    def accepted_records(self) -> Tuple[DecisionRecord, ...]:
        """The held records standing accepted."""
        return accepted_records(self)


# ---------------------------------------------------------------------
# Decision news, shaped as session records.
# ---------------------------------------------------------------------


def record_record(record: Any) -> Dict[str, Any]:
    """The session-news record of one decision record."""
    current = record if isinstance(record, DecisionRecord) \
        else build_record(record)
    record_out = current.to_record()
    record_out["news"] = True
    record_out["headline"] = (
        f"{current.title} ({current.status}) decided in "
        f"{current.session_ref} on {current.decided_on}: "
        f"{current.decision}")
    return record_out


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of one derived panel.

    With *source* given, the panel is first judged
    against the panel that source derives.
    """
    current = validate_panel(panel, source)
    record_out = current.to_record()
    record_out["news"] = True
    record_out["headline"] = (
        f"Decision panel: {current.total_items} "
        f"records - accepted {current.total_accepted}, "
        f"proposed {current.total_proposed}, superseded "
        f"{current.total_superseded}.")
    return record_out


def book_record(book: Any) -> Dict[str, Any]:
    """The session-news record of one decision book."""
    current = book if isinstance(book, DecisionBook) \
        else build_book(book)
    record_out = current.to_record()
    record_out["news"] = True
    record_out["headline"] = (
        f"Decision records {current.title}: "
        f"{record_out['record_count']} records named.")
    return record_out


def plain_words(record: Any) -> str:
    """One decision record, in one plain sentence."""
    current = record if isinstance(record, DecisionRecord) \
        else build_record(record)
    return (
        f"{current.title} - a {current.status} decision "
        f"from {current.session_ref} on {current.decided_on}: "
        f"chose {current.decision} Not taken: "
        f"{'; '.join(current.alternatives)}. Why: "
        f"{current.rationale} (read from {current.source}).")


def panel_plain_words(source: Any) -> str:
    """The decision panel in plain words, in full.

    Accepts a DecisionPanel or a DecisionBook
    (whose derived panel is told). The panel is told
    whole - its rows in panel order and its account.
    """
    if isinstance(source, DecisionPanel):
        panel = validate_panel(source)
        title = None
    elif isinstance(source, DecisionBook):
        panel = derive_panel(source)
        title = source.title
    else:
        raise ValueError(
            f"a decision-records source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    lines.append("Records, in panel order:")
    for row in panel.rows:
        lines.append(
            f"{row.record_id}: {row.status} - {row.title} "
            f"(from {row.session_ref}): "
            f"{row.decision}")
    lines.extend(panel.account)
    return "\n".join(lines)


# ---------------------------------------------------------------------
# Screens: the ADR renderer, the formatters, the /decisions grammar.
# ---------------------------------------------------------------------


def _source_book(source: Any) -> DecisionBook:
    if source is None:
        return load_decision_records()
    if isinstance(source, DecisionRegistry):
        return source.book()
    if isinstance(source, DecisionBook):
        return source
    raise ValueError(
        f"a decision book is needed, got {source!r}")


def format_record(record: Any) -> str:
    """One decision record as a screen block, provenance whole."""
    current = record if isinstance(record, DecisionRecord) \
        else build_record(record)
    lines = [
        f"{current.record_id or '-'}: {current.title} - "
        f"{current.status}, decided in {current.session_ref} "
        f"on {current.decided_on}",
        f"Chose: {current.decision}",
        "Not taken: " + "; ".join(current.alternatives),
        f"Why: {current.rationale}",
        f"In this context: {current.context}",
        f"Follows: {current.consequences}",
        f"(from {current.source})",
    ]
    if current.superseded_by is not None:
        lines.append(f"Superseded by: {current.superseded_by}")
    return "\n".join(lines)


def format_records(source: Any = None) -> str:
    """Decision records of one book, in held order."""
    book = _source_book(source)
    lines = [
        f"{item.record_id or '-'}: {item.title} - "
        f"{item.status} (decided in "
        f"{item.session_ref}): {item.decision}"
        for item in book.records]
    if not lines:
        lines.append("No records are held.")
    return "\n".join(lines)


def format_adr(record: Any) -> str:
    """One decision record rendered as a small ADR, exactly.

    This markdown is the exact text that would
    land in the project docs for this choice -
    rendered here as data. No file is written:
    rendering is the whole road this layer walks.
    """
    current = record if isinstance(record, DecisionRecord) \
        else build_record(record)
    lines = [
        f"# ADR {current.record_id or '-'}: {current.title}",
        "",
        f"- Status: {current.status}",
        f"- Session: {current.session_ref}",
        f"- Date: {current.decided_on}",
        f"- Source: {current.source}",
    ]
    if current.superseded_by is not None:
        lines.append(f"- Superseded by: {current.superseded_by}")
    lines.extend([
        "",
        "## Context",
        "",
        current.context,
        "",
        "## Decision",
        "",
        current.decision,
        "",
        "## Alternatives considered",
        "",
    ])
    lines.extend(f"- {road}" for road in current.alternatives)
    lines.extend([
        "",
        "## Rationale",
        "",
        current.rationale,
        "",
        "## Consequences",
        "",
        current.consequences,
    ])
    return "\n".join(lines)


def format_adrs(source: Any = None) -> str:
    """Every record of one book rendered as ADRs, in held order."""
    book = _source_book(source)
    return "\n\n".join(format_adr(item) for item in book.records)


def format_accepted(source: Any = None) -> str:
    """The records standing accepted in one book."""
    standing = accepted_records(_source_book(source))
    lines = [
        f"{item.record_id or '-'}: {item.title} - "
        f"decided in {item.session_ref} "
        f"({item.context}), follows: "
        f"{item.consequences}: {item.decision}"
        for item in standing]
    if not lines:
        lines.append("No decisions stand accepted yet.")
    return "\n".join(lines)


def format_panel(source: Any = None) -> str:
    """The decision panel as a screen block: every row and the account.

    Accepts a DecisionPanel or a DecisionBook; a
    book shows the panel it derives.
    """
    if isinstance(source, DecisionPanel):
        panel = validate_panel(source)
        lines: list = []
    else:
        book = _source_book(source)
        if not book.records:
            return (f"Decision panel in {book.title}:\n"
                    f"No records are held.")
        panel = derive_panel(book)
        lines = [f"Decision panel in {book.title}:"]
    lines.append("Records, in panel order:")
    for row in panel.rows:
        lines.append(
            f"{row.record_id}: {row.status} - {row.title} "
            f"(from {row.session_ref}): "
            f"{row.decision}")
    lines.extend(panel.account)
    return "\n".join(lines)


def format_decision_records_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /decisions.

    With nothing named, the shipped example
    decision book is shown - the example this
    slice ships - so the screen is never empty.
    """
    book = _source_book(source)
    lines = ["Decision Records (M-156) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_records(book))
    lines.append("")
    lines.append(format_panel(book))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_decision_records_args(args: Any) -> Tuple[str, Any]:
    """Parse the /decisions grammar both surfaces share.

    No words (or ``show`` / ``list``) shows the
    decision book; ``record <record-id>`` shows one
    decision record with its provenance whole;
    ``adr <record-id>`` renders one record as the
    small ADR that would land in the project docs;
    ``accepted`` shows the records standing
    accepted; ``panel`` shows the decision panel
    derived from the whole book. Anything else is
    a usage error naming the grammar. Returns
    ``(action, value-or-None)``.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() in ("show", "list"):
        return ("show", None)
    words = text.split()
    head = words[0].lower()
    if head == "accepted" and len(words) == 1:
        return (head, None)
    if head == "panel" and len(words) == 1:
        return (head, None)
    if head in ("record", "adr") and len(words) == 2:
        try:
            return (head, normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
