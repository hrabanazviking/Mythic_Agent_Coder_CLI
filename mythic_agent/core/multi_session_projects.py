"""Multi-session per project (All-Features roadmap slice M-162).

Part VII continues. The roadmap's words:
``parallel sessions on one repo (different
branches) with shared memory map and no journal
crosstalk.``

What already ships, and what this slice adds:

* Work on one project already ships as data on
  shipped roads: the session store
  (``core/sessions.py``) keeps workspace
  transcripts with a write-ahead journal, session
  memory across days (``core/session_memory.py``,
  M-153) holds a session's situation - its carried
  memory counted, never carried whole - the
  project memory map (``core/project_memory_map.py``,
  M-150) holds the project's living map as entries,
  cross-project memory
  (``core/cross_project_memory.py``, M-154) holds
  lessons one project offers another, and
  long-session endurance
  (``core/long_session_endurance.py``, M-161)
  holds a long session's measured budgets. What
  none of those layers holds is the parallel
  session itself: the declaration, as data, that
  several sessions stand on ONE project at once,
  each on its own branch, each with its own
  journal, all reading the one shared memory map.
* This slice is that declaration, as a pure layer:
  a parallel session is one session standing on
  one project, validated as data WITH ITS
  PROVENANCE WHOLE - the project it stands on, the
  branch it works, the session and journal it
  stands under, its state, the journal entries
  that are its own, how many shared memory-map
  entries it has read, who recorded it, the day,
  and where it was read from - composed BY IMPORT
  from the shipped holdings it stands beside (a
  session-memory situation, a project memory-map
  entry, a cross-project shared lesson, a
  long-session endurance record), each judged by
  its own layer's validation. The shipped data
  file (``mythic_agent/data/multi_session_projects.yaml``)
  holds one example book in exactly the shape a
  real book file takes, a loader reads a book file
  anywhere on disk, the multi-session panel is
  DERIVED from the whole book (every session
  carried whole, in a settled order), an ISOLATION
  verdict is derived for the whole book, sessions
  are shaped as session news, and a small in-memory
  registry model holds sessions one by one. The
  agent layer owns holding a book for a session
  and reading the session's memory onto parallel
  sessions.

Honesty rules, enforced here and pinned by tests:

* **Different branches.** Two sessions of one book
  never stand on the same branch: a second session
  naming a held branch refuses, in a book and in
  the registry alike.
* **No journal crosstalk.** Every session stands
  under its own journal, and a journal entry named
  by one session never appears in another's: a
  book or registry where one entry stands in two
  sessions refuses - crosstalk is named, never
  merged or hidden.
* **One shared memory map.** The sessions of one
  book stand on one project and read the one
  shared map: a session's shared reads are counted
  against that map, and the map's facts themselves
  stay in the map layer - only counts cross.
* **Composed, never duplicated.** A session that
  stands beside a shipped holding is that holding
  read onto this layer by import and judged by its
  own layer's validation, by reference and count
  alone: its own words never cross.
* **Data only.** This layer holds parallel
  sessions as data: it reads no file itself beyond
  its own book files, spawns no live session,
  appends to no live journal, calls no model and
  persists nothing. A session standing in a book
  is a recorded standing, never a claim that a
  live session is running here.
"""

from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..resources import load_resource
from .crew_members import normalize_member_id
from .cross_project_memory import SharedLesson
from .cross_project_memory import validate_lesson as _validate_lesson
from .long_session_endurance import EnduranceRecord
from .long_session_endurance import validate_record as _validate_endurance
from .project_memory_map import MemoryMapEntry
from .project_memory_map import validate_entry as _validate_entry
from .session_memory import SessionSituation
from .session_memory import validate_situation as _validate_situation
from .validation import ValidationError

__all__ = [
    "MULTI_SESSION_PROJECTS_RESOURCE",
    "MULTI_SESSION_PROJECTS_SCHEMA",
    "MULTI_SESSION_PROJECTS_SLICE",
    "PLAIN_EXPLANATION",
    "SESSION_STATES",
    "USAGE",
    "IsolationVerdict",
    "MultiSessionBook",
    "MultiSessionPanel",
    "MultiSessionPanelRow",
    "MultiSessionRegistry",
    "ParallelSession",
    "SessionStateCount",
    "book_record",
    "build_book",
    "build_isolation",
    "build_panel",
    "build_row",
    "build_session",
    "derive_isolation",
    "derive_panel",
    "format_isolation",
    "format_multi_session_projects_screen",
    "format_panel",
    "format_parallel_session",
    "format_parallel_sessions",
    "inspect_parallel_source",
    "isolation_plain_words",
    "isolation_record",
    "load_multi_session_projects",
    "load_multi_session_projects_file",
    "multi_session_refs",
    "normalize_session_state",
    "panel_plain_words",
    "panel_record",
    "parallel_from_endurance_record",
    "parallel_from_map_entry",
    "parallel_from_session_situation",
    "parallel_from_shared_lesson",
    "parallel_record",
    "parallel_sessions_from_session_memory",
    "parse_multisession_args",
    "plain_words",
    "total_journal_entries",
    "validate_book",
    "validate_isolation",
    "validate_panel",
    "validate_row",
    "validate_session",
]

MULTI_SESSION_PROJECTS_SLICE = "M-162"

MULTI_SESSION_PROJECTS_RESOURCE = "multi_session_projects.yaml"

MULTI_SESSION_PROJECTS_SCHEMA = "mythic.multi_session_projects/1"

SESSION_STATES = ("active", "paused", "done")

_STATE_RANK = {state: rank for rank, state in enumerate(SESSION_STATES)}

_STATE_ALIASES = {
    "active": "active", "running": "active",
    "live": "active", "working": "active",
    "paused": "paused", "held": "paused",
    "waiting": "paused", "parked": "paused",
    "done": "done", "finished": "done",
    "closed": "done", "complete": "done",
}

_RECORD_KEYS = frozenset({
    "session_id", "id", "title", "name", "subject",
    "project", "branch", "session_ref", "session",
    "journal_ref", "journal", "state", "status",
    "journal_entries", "entries",
    "shared_reads", "reads",
    "recorded_by", "by", "who",
    "recorded_on", "day", "date", "source",
})

_ROW_KEYS = frozenset({
    "session_id", "id", "title", "project", "branch",
    "session_ref", "journal_ref", "state",
    "journal_count", "shared_reads",
    "recorded_by", "recorded_on",
})

_STATE_COUNT_KEYS = frozenset({"state", "sessions", "count"})

_PANEL_KEYS = frozenset({
    "panel_id", "id", "rows", "sessions",
    "total_sessions", "total",
    "total_journal_entries", "journal_entries",
    "total_shared_reads", "shared_reads",
    "state_counts", "states", "account", "statements",
})

_ISOLATION_KEYS = frozenset({
    "total_sessions", "total",
    "total_journal_entries", "journal_entries",
    "distinct_journals", "journals",
    "distinct_branches", "branches",
    "shared_reads", "verdict",
})

_BOOK_KEYS = frozenset({"title", "name"})

_MULTI_SESSION_BOOK_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "canon_note", "guide", "sessions", "records", "panels",
})

_EXAMPLE_TITLE = "Multi-session per project at the M-161 slice boundary"

_EXAMPLE_SESSION_IDS = (
    "multisession-main", "multisession-memory",
    "multisession-graph", "multisession-thrift")

_EXAMPLE_FIRST_SESSION_ID = "multisession-main"

_EXAMPLE_FIRST_SESSION_TITLE = (
    "the endurance session, carried forward on the main line")

_EXAMPLE_PANEL_ID = "panel-m161-boundary"

_EXAMPLE_PANEL_ROW_IDS = (
    "multisession-main", "multisession-memory",
    "multisession-graph", "multisession-thrift")

_EXAMPLE_PANEL_ACCOUNT = (
    "The multi-session panel holds 4 sessions: "
    "8 journal entries in all, 19 shared memory-map "
    "reads: active 2, done 1, paused 1.",
    "Sessions stand by state - active first, then "
    "paused, then done - then by branch, then title, "
    "then session id, so two panels of one book diff "
    "cleanly, line by line.",
    "Every session stands on its own branch with "
    "its own journal: a journal entry named by one "
    "session never appears in another - no "
    "crosstalk.",
    "The panel is read off the book at call time - "
    "it is derived, never stored loose.",
)

PLAIN_EXPLANATION = (
    "Multi-session per project: parallel sessions "
    "on one repo, on different branches, with a "
    "shared memory map and no journal crosstalk. A "
    "parallel session is one session standing on "
    "one project, carried with its provenance "
    "whole: the project, the branch it works, the "
    "session and journal it stands under, its "
    "state, the journal entries that are its own, "
    "how many shared memory-map entries it has "
    "read, who recorded it, the day, and where it "
    "was read from. Two sessions never stand on "
    "the same branch, and a journal entry named by "
    "one session never appears in another's. The "
    "multi-session panel is derived from the book "
    "at call time: every session standing whole, "
    "by state, then branch, then title, then "
    "session id, and the isolation verdict is "
    "derived for the whole book. This layer holds "
    "parallel sessions as data only: it spawns no "
    "live session, appends to no live journal, "
    "calls no model and persists nothing."
)

USAGE = (
    "Usage: /multisession, /multisession show, "
    "/multisession session <session-id>, "
    "/multisession branch <branch>, "
    "/multisession panel, /multisession isolation"
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


def _check_word(value: Any, what: str) -> str:
    try:
        return normalize_member_id(value)
    except ValueError:
        raise ValueError(
            f"{what} must be one plain word, "
            f"got {value!r}") from None


_BRANCH_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789-_./")


def _check_branch(value: Any) -> str:
    text = _clean_text(value, "a session's branch")
    if len(text) > 120 or any(ch not in _BRANCH_CHARS for ch in text):
        raise ValueError(
            f"a session's branch must be a plain branch "
            f"name, got {text!r}")
    if text.startswith(("/", ".", "-")) or text.endswith(("/", ".")) \
            or "//" in text or ".." in text:
        raise ValueError(
            f"a session's branch must be a plain branch "
            f"name, got {text!r}")
    return text


def _check_day(value: Any) -> str:
    text = _clean_text(value, "a record's recorded-on day")
    try:
        parsed = date.fromisoformat(text)
    except ValueError:
        raise ValueError(
            f"a record's recorded-on day must be an ISO "
            f"date (YYYY-MM-DD), got {text!r}") from None
    if parsed.isoformat() != text:
        raise ValueError(
            f"a record's recorded-on day must be an ISO "
            f"date (YYYY-MM-DD), got {text!r}")
    return text


def normalize_session_state(value: Any) -> str:
    """The canonical session state a word names.

    A state is one of :data:`SESSION_STATES` - a
    parallel session is ``active``, ``paused`` or
    ``done`` - read case-insensitively, with their
    plain faces (``running`` / ``live``, ``held`` /
    ``waiting``, ``finished`` / ``closed``) read onto
    them. Anything else raises, plainly naming the
    three.
    """
    if isinstance(value, str):
        wanted = _STATE_ALIASES.get(value.strip().lower())
        if wanted is not None:
            return wanted
    raise ValueError(
        "a session state must be one of %s, got %r"
        % ("/".join(SESSION_STATES), value))


# ---------------------------------------------------------------------
# The parallel session: one session on one project, whole.
# ---------------------------------------------------------------------


def _check_entries(value: Any) -> Tuple[str, ...]:
    if isinstance(value, (str, bytes)) \
            or not isinstance(value, (list, tuple)):
        raise ValueError(
            f"a session's journal entries must be a list "
            f"of entry ids, got {value!r}")
    entries = tuple(
        _check_word(item, "a journal entry id") for item in value)
    if not entries:
        raise ValueError(
            "a parallel session names at least one journal "
            "entry of its own - a session with no journal "
            "entries stands nowhere")
    if len(entries) > 512:
        raise ValueError(
            f"a session names at most 512 journal entries, "
            f"got {len(entries)}")
    if len(set(entries)) != len(entries):
        raise ValueError(
            "a session names one journal entry twice")
    return entries


@dataclass(frozen=True)
class ParallelSession:
    """One session standing on one project, as data.

    ``title`` names the session's work in plain
    words; ``project`` is the one project (repo) it
    stands on; ``branch`` is the branch it works -
    its own, shared with no other session of its
    book; ``session_ref`` names the stored session
    it stands under and ``journal_ref`` the journal
    that is its own alone; ``state`` is its standing
    in the closed set; ``journal_entries`` are the
    entry ids of its own journal, in held order - an
    entry named here stands in no other session;
    ``shared_reads`` counts the shared memory-map
    entries this session has read off the project's
    one shared map. The provenance stands whole
    beside the session: ``recorded_by`` names who
    recorded it, ``recorded_on`` is the day, and
    ``source`` names where it was read from.
    """

    title: str
    project: str
    branch: str
    session_ref: str
    journal_ref: str
    state: str
    journal_entries: Tuple[str, ...]
    shared_reads: int
    recorded_by: str
    recorded_on: str
    source: str
    session_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.session_id is not None:
            object.__setattr__(
                self, "session_id", normalize_member_id(self.session_id))
        object.__setattr__(
            self, "title", _check_title(self.title, "a session's title"))
        object.__setattr__(
            self, "project",
            _check_title(self.project, "a session's project"))
        object.__setattr__(self, "branch", _check_branch(self.branch))
        object.__setattr__(
            self, "session_ref",
            _check_word(self.session_ref, "a session's session reference"))
        object.__setattr__(
            self, "journal_ref",
            _check_word(self.journal_ref, "a session's journal reference"))
        object.__setattr__(
            self, "state", normalize_session_state(self.state))
        object.__setattr__(
            self, "journal_entries", _check_entries(self.journal_entries))
        object.__setattr__(
            self, "shared_reads",
            _check_count(self.shared_reads, "a session's shared reads"))
        object.__setattr__(
            self, "recorded_by",
            _check_title(self.recorded_by, "a session's recorder"))
        object.__setattr__(
            self, "recorded_on", _check_day(self.recorded_on))
        object.__setattr__(
            self, "source",
            _check_title(self.source, "a session's source"))

    @property
    def journal_count(self) -> int:
        """How many journal entries are this session's own."""
        return len(self.journal_entries)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "multi_session_projects_session",
            "slice": MULTI_SESSION_PROJECTS_SLICE,
            "session_id": self.session_id,
            "title": self.title,
            "project": self.project,
            "branch": self.branch,
            "session_ref": self.session_ref,
            "journal_ref": self.journal_ref,
            "state": self.state,
            "journal_entries": list(self.journal_entries),
            "journal_count": self.journal_count,
            "shared_reads": self.shared_reads,
            "recorded_by": self.recorded_by,
            "recorded_on": self.recorded_on,
            "source": self.source,
        }


def _check_session_ref(value: Any) -> ParallelSession:
    if isinstance(value, ParallelSession):
        return value
    if isinstance(value, dict):
        return validate_session(value)
    raise ValueError(f"a parallel session is needed, got {value!r}")


def validate_session(session: Any) -> ParallelSession:
    """Validate one parallel session into a ParallelSession.

    Accepts a session or a mapping naming a ``title``
    (or ``name`` / ``subject``), a ``project``, a
    ``branch``, a ``session_ref`` (or ``session``), a
    ``journal_ref`` (or ``journal``), a ``state`` (or
    ``status``), ``journal_entries`` (or ``entries``),
    ``shared_reads`` (or ``reads``), a ``recorded_by``
    (or ``by`` / ``who``), a ``recorded_on`` (or
    ``day`` / ``date``), a ``source`` and an optional
    ``session_id`` (or ``id``). Naming two spellings
    of one field with different values refuses, and
    unknown keys refuse.
    """
    if isinstance(session, ParallelSession):
        return session
    if not isinstance(session, dict):
        raise ValueError(
            f"a parallel session must be a mapping, got {session!r}")
    unknown = set(session) - _RECORD_KEYS
    if unknown:
        raise ValueError(
            "unknown parallel-session keys: %s"
            % ", ".join(sorted(unknown)))

    def _needed(spellings: Tuple[str, ...], what: str) -> Any:
        value = _pick_any(session, spellings, what)
        if value is None:
            raise ValueError(f"a parallel session is missing its {what}")
        return value

    kwargs: Dict[str, Any] = {
        "title": _needed(("title", "name", "subject"), "title"),
        "project": _needed(("project",), "project"),
        "branch": _needed(("branch",), "branch"),
        "session_ref": _needed(("session_ref", "session"), "session reference"),
        "journal_ref": _needed(("journal_ref", "journal"), "journal reference"),
        "state": _needed(("state", "status"), "state"),
        "journal_entries": _needed(
            ("journal_entries", "entries"), "journal entries"),
        "shared_reads": _needed(("shared_reads", "reads"), "shared reads"),
        "recorded_by": _needed(("recorded_by", "by", "who"), "recorder"),
        "recorded_on": _needed(
            ("recorded_on", "day", "date"), "recorded-on day"),
        "source": _needed(("source",), "source"),
    }
    named_id = _pick_any(session, ("session_id", "id"), "session ids")
    if named_id is not None:
        kwargs["session_id"] = named_id
    return ParallelSession(**kwargs)


def build_session(session: Any = None, **kwargs: Any) -> ParallelSession:
    """Build one validated parallel session, from a mapping or words."""
    if isinstance(session, ParallelSession) and not kwargs:
        return session
    if isinstance(session, dict) or session is None:
        merged: Dict[str, Any] = {}
        if isinstance(session, dict):
            merged.update(session)
        merged.update(kwargs)
        return validate_session(merged)
    raise ValueError(
        f"a parallel session must be a mapping, got {session!r}")


def _parallel_for(*, title: Any, project: Any, branch: Any,
                  session_ref: Any, journal_ref: Any, state: Any,
                  journal_entries: Any, shared_reads: Any,
                  recorded_by: Any, recorded_on: Any,
                  source: Any) -> ParallelSession:
    """One parallel session for one shipped piece, by ref and count.

    The piece's own words are never read here: only
    the references and counts named beside it cross.
    A session naming no branch, no journal of its
    own, no journal entries or no recorder refuses -
    a parallel session stands on a branch, with a
    journal, or it does not stand at all.
    """
    if branch is None or (isinstance(branch, str) and not branch.strip()):
        raise ValueError(
            "a parallel session must name the branch it "
            "stands on - parallel sessions stand on "
            "different branches")
    if journal_ref is None or (
            isinstance(journal_ref, str) and not journal_ref.strip()):
        raise ValueError(
            "a parallel session must name the journal "
            "that is its own - a session with no journal "
            "of its own cannot stand apart")
    if journal_entries is None:
        raise ValueError(
            "a parallel session must name its own "
            "journal entries - a session's journal is "
            "its own, entry by entry")
    if recorded_by is None:
        raise ValueError(
            "a parallel session must name who recorded "
            "it - a session recorded by no one is no "
            "record")
    if session_ref is None or (
            isinstance(session_ref, str) and not session_ref.strip()):
        raise ValueError(
            "a parallel session names the session it "
            "stands under - a standing with no session "
            "cannot be held")
    return ParallelSession(
        title=title, project=project, branch=branch,
        session_ref=session_ref, journal_ref=journal_ref,
        state=state, journal_entries=journal_entries,
        shared_reads=shared_reads, recorded_by=recorded_by,
        recorded_on=recorded_on, source=source)


def inspect_parallel_source(piece: Any) -> Dict[str, Any]:
    """Inspect one shipped piece: its references and counts only.

    The piece is judged by the layer that owns its
    type, never by whichever validator happens to
    accept its shape first. A session-memory
    situation reports its session reference and its
    carried-memory count (the shared-map facts it
    carries); a project memory-map entry reports
    the reference where its fact lives and one
    shared read; a long-session endurance record
    reports the reference it stands under and no
    journal count of its own (``None`` - its entries
    are named beside the reference at the
    composition seam); a parallel session reports
    itself whole. A piece no shipped layer owns
    refuses.
    """
    if isinstance(piece, ParallelSession):
        return {"session_ref": piece.session_ref,
                "journal_count": piece.journal_count,
                "shared_reads": piece.shared_reads}
    if isinstance(piece, SessionSituation):
        validated = _validate_situation(piece)
        return {"session_ref": validated.session_ref,
                "journal_count": None,
                "shared_reads": validated.total_memory}
    if isinstance(piece, MemoryMapEntry):
        validated = _validate_entry(piece)
        return {"entry_ref": validated.ref, "shared_reads": 1}
    if isinstance(piece, SharedLesson):
        validated = _validate_lesson(piece)
        return {"project": validated.source_project,
                "shared_reads": 1}
    if isinstance(piece, EnduranceRecord):
        validated = _validate_endurance(piece)
        return {"session_ref": validated.ref,
                "journal_count": None, "shared_reads": 0}
    if isinstance(piece, dict):
        if "branch" in piece and "journal_ref" in piece:
            checked = validate_session(piece)
            return {"session_ref": checked.session_ref,
                    "journal_count": checked.journal_count,
                    "shared_reads": checked.shared_reads}
        for validator in (_validate_situation, _validate_entry,
                          _validate_lesson, _validate_endurance):
            try:
                validated = validator(piece)
            except Exception:
                continue
            return inspect_parallel_source(validated)
    raise ValueError(
        f"no shipped layer owns this piece, got {piece!r}")


def parallel_from_session_situation(
        situation: Any, *, project: Any, branch: Any,
        journal_ref: Any, journal_entries: Any,
        recorded_by: Any, recorded_on: Any,
        state: Any = "active", source: Any = "session memory",
        title: Any = None) -> ParallelSession:
    """Build one parallel session from a session-memory situation.

    The situation - session memory's own record
    (M-153), judged by that layer's own validation -
    is read onto a parallel session BY IMPORT by its
    reference and count alone: its session reference
    stands as the session's reference and its
    carried-memory count - the shared memory-map
    facts the situation carries - is the session's
    shared reads. The project, branch, journal and
    journal entries are named beside it. The
    situation's title, workspace and carried memory
    words are never read here.
    """
    validated = _validate_situation(situation)
    return _parallel_for(
        title=title if title is not None else (
            f"session {validated.session_ref}"),
        project=project, branch=branch,
        session_ref=validated.session_ref,
        journal_ref=journal_ref, state=state,
        journal_entries=journal_entries,
        shared_reads=validated.total_memory,
        recorded_by=recorded_by, recorded_on=recorded_on,
        source=source)


def parallel_from_map_entry(
        entry: Any, *, project: Any, branch: Any,
        session_ref: Any, journal_ref: Any,
        journal_entries: Any, recorded_by: Any,
        recorded_on: Any, state: Any = "active",
        source: Any = "project memory map",
        title: Any = None) -> ParallelSession:
    """Build one parallel session that has read the shared map.

    The entry - the project memory map's own record
    (M-150), judged by that layer's own validation -
    is read onto a parallel session BY IMPORT as one
    shared read: a session standing beside the map
    has read the shared map, and its shared reads
    stand at one for this entry. The project,
    branch, session and journal are named beside
    it. The entry's title, detail and source are
    never read here.
    """
    _validate_entry(entry)
    return _parallel_for(
        title=title if title is not None else (
            f"session {session_ref}"),
        project=project, branch=branch,
        session_ref=session_ref, journal_ref=journal_ref,
        state=state, journal_entries=journal_entries,
        shared_reads=1, recorded_by=recorded_by,
        recorded_on=recorded_on, source=source)


def parallel_from_shared_lesson(
        lesson: Any, *, branch: Any, session_ref: Any,
        journal_ref: Any, journal_entries: Any,
        recorded_by: Any, recorded_on: Any,
        state: Any = "active", source: Any = "cross-project memory",
        title: Any = None) -> ParallelSession:
    """Build one parallel session from a cross-project lesson.

    The lesson - cross-project memory's own record
    (M-154), judged by that layer's own validation -
    is read onto a parallel session BY IMPORT by its
    project alone: the project the lesson was
    learned in stands as the session's project, and
    the lesson counts as one shared read - a lesson
    carried across projects is shared memory read.
    The branch, session and journal are named
    beside it. The lesson's title, detail, context
    and evidence are never read here.
    """
    validated = _validate_lesson(lesson)
    return _parallel_for(
        title=title if title is not None else (
            f"session {session_ref}"),
        project=validated.source_project, branch=branch,
        session_ref=session_ref, journal_ref=journal_ref,
        state=state, journal_entries=journal_entries,
        shared_reads=1, recorded_by=recorded_by,
        recorded_on=recorded_on, source=source)


def parallel_from_endurance_record(
        record: Any, *, project: Any, branch: Any,
        journal_ref: Any, journal_entries: Any,
        recorded_by: Any = None, recorded_on: Any = None,
        state: Any = "active", source: Any = "long-session endurance",
        title: Any = None) -> ParallelSession:
    """Build one parallel session from an endurance record.

    The record - long-session endurance's own record
    (M-161), judged by that layer's own validation -
    is read onto a parallel session BY IMPORT by its
    reference alone: the reference it stands under
    stands as the session's reference. The project,
    branch, journal and journal entries are named
    beside it; the recorder and day default to the
    endurance record's own provenance. Its subject
    and figures are never read here.
    """
    validated = _validate_endurance(record)
    return _parallel_for(
        title=title if title is not None else (
            f"session {validated.ref}"),
        project=project, branch=branch,
        session_ref=validated.ref, journal_ref=journal_ref,
        state=state, journal_entries=journal_entries,
        shared_reads=0,
        recorded_by=recorded_by if recorded_by is not None
        else validated.recorded_by,
        recorded_on=recorded_on if recorded_on is not None
        else validated.recorded_on,
        source=source)


def _situations(source: Any) -> Tuple[SessionSituation, ...]:
    """The situations one source holds, judged by session memory."""
    from .session_memory import SessionMemoryBook, SessionMemoryRegistry
    if isinstance(source, SessionMemoryBook):
        return source.situations
    if isinstance(source, SessionMemoryRegistry):
        return source.list_situations()
    if isinstance(source, (list, tuple)):
        return tuple(_validate_situation(item) for item in source)
    if isinstance(source, (SessionSituation, dict)):
        return (_validate_situation(source),)
    raise ValueError(f"session situations are needed, got {source!r}")


def parallel_sessions_from_session_memory(
        source: Any, *, project: Any, recorded_by: Any,
        recorded_on: Any) -> Tuple[ParallelSession, ...]:
    """Parallel sessions read off the shipped session memory.

    The situations of a session-memory book - or of
    a whole session-memory registry - are read onto
    parallel sessions BY IMPORT, judged by session
    memory's own validation on the way, one session
    per situation, all standing on the one named
    *project* (no project named refuses the whole
    road before anything is built, because parallel
    sessions stand on one project). Each session's
    branch, journal and opening journal entry are
    named deterministically from its session
    reference - ``work/<session-ref>``,
    ``journal-<session-ref>`` and
    ``entry-<session-ref>-opening`` - so two
    situations never collide, and each session's
    shared reads are its situation's carried-memory
    count. Every situation's title, workspace and
    carried memory words stay in session memory:
    only references and counts cross.
    """
    if project is None or (isinstance(project, str) and not project.strip()):
        raise ValueError(
            "a project must be named for the parallel "
            "sessions - parallel sessions stand on one "
            "project")
    situations = _situations(source)
    return tuple(
        parallel_from_session_situation(
            situation, project=project,
            branch=f"work/{situation.session_ref}",
            journal_ref=f"journal-{situation.session_ref}",
            journal_entries=(
                f"entry-{situation.session_ref}-opening",),
            recorded_by=recorded_by, recorded_on=recorded_on)
        for situation in situations)


# ---------------------------------------------------------------------
# The multi-session panel: every session carried whole, derived.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class MultiSessionPanelRow:
    """One parallel session carried whole into the panel.

    Every field is the session's own head: its id,
    title, project, branch, session and journal
    references, state, its own journal's entry count,
    its shared reads, and its provenance head.
    :func:`validate_row` judged against its session
    refuses a row whose fields disagree with the row
    they derive.
    """

    session_id: str
    title: str
    project: str
    branch: str
    session_ref: str
    journal_ref: str
    state: str
    journal_count: int
    shared_reads: int
    recorded_by: str
    recorded_on: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "session_id", normalize_member_id(self.session_id))
        object.__setattr__(
            self, "title", _check_title(self.title, "a row's title"))
        object.__setattr__(
            self, "project", _check_title(self.project, "a row's project"))
        object.__setattr__(self, "branch", _check_branch(self.branch))
        object.__setattr__(
            self, "session_ref",
            _check_word(self.session_ref, "a row's session reference"))
        object.__setattr__(
            self, "journal_ref",
            _check_word(self.journal_ref, "a row's journal reference"))
        object.__setattr__(
            self, "state", normalize_session_state(self.state))
        object.__setattr__(
            self, "journal_count",
            _check_count(self.journal_count, "a row's journal count"))
        if self.journal_count < 1:
            raise ValueError(
                "a row's journal count must name at least "
                "one entry of its own")
        object.__setattr__(
            self, "shared_reads",
            _check_count(self.shared_reads, "a row's shared reads"))
        object.__setattr__(
            self, "recorded_by",
            _check_title(self.recorded_by, "a row's recorder"))
        object.__setattr__(
            self, "recorded_on", _check_day(self.recorded_on))

    @property
    def sort_key(self) -> Tuple[int, str, str, str]:
        """This row's place in panel order (derived).

        Rows stand by state - active first, then
        paused, then done - then by branch, then
        title, then session id.
        """
        return (_STATE_RANK[self.state], self.branch.lower(),
                self.title.lower(), self.session_id)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "multi_session_projects_panel_row",
            "slice": MULTI_SESSION_PROJECTS_SLICE,
            "session_id": self.session_id,
            "title": self.title,
            "project": self.project,
            "branch": self.branch,
            "session_ref": self.session_ref,
            "journal_ref": self.journal_ref,
            "state": self.state,
            "journal_count": self.journal_count,
            "shared_reads": self.shared_reads,
            "recorded_by": self.recorded_by,
            "recorded_on": self.recorded_on,
        }


def _row_for_session(session: ParallelSession) -> MultiSessionPanelRow:
    return MultiSessionPanelRow(
        session_id=session.session_id, title=session.title,
        project=session.project, branch=session.branch,
        session_ref=session.session_ref,
        journal_ref=session.journal_ref, state=session.state,
        journal_count=session.journal_count,
        shared_reads=session.shared_reads,
        recorded_by=session.recorded_by,
        recorded_on=session.recorded_on)


def _check_row_ref(value: Any) -> MultiSessionPanelRow:
    if isinstance(value, MultiSessionPanelRow):
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

        return MultiSessionPanelRow(
            session_id=_needed(("session_id", "id"), "session id"),
            title=_needed(("title",), "title"),
            project=_needed(("project",), "project"),
            branch=_needed(("branch",), "branch"),
            session_ref=_needed(("session_ref",), "session reference"),
            journal_ref=_needed(("journal_ref",), "journal reference"),
            state=_needed(("state",), "state"),
            journal_count=_needed(("journal_count",), "journal count"),
            shared_reads=_needed(("shared_reads",), "shared reads"),
            recorded_by=_needed(("recorded_by",), "recorder"),
            recorded_on=_needed(("recorded_on",), "recorded-on day"))
    raise ValueError(f"a panel row is needed, got {value!r}")


def validate_row(row: Any, session: Any = None) -> MultiSessionPanelRow:
    """Validate one panel row into a MultiSessionPanelRow.

    With *session* given, the row is judged against
    the row derived from that session: a stored row
    whose fields disagree with the derived row
    refuses.
    """
    current = _check_row_ref(row)
    if session is not None:
        checked = _check_session_ref(session)
        derived = _row_for_session(checked)
        if current != derived:
            raise ValueError(
                "a stored row disagrees with the row "
                "derived from its session")
    return current


def build_row(row: Any = None, session: Any = None,
              **kwargs: Any) -> MultiSessionPanelRow:
    """Build one validated row, from a mapping or field words."""
    if isinstance(row, MultiSessionPanelRow) and not kwargs:
        return validate_row(row, session)
    if isinstance(row, dict) or row is None:
        merged: Dict[str, Any] = {}
        if isinstance(row, dict):
            merged.update(row)
        merged.update(kwargs)
        return validate_row(merged, session)
    return validate_row(row, session)


@dataclass(frozen=True)
class SessionStateCount:
    """One state's count in a panel: its sessions tallied."""

    state: str
    sessions: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "state", normalize_session_state(self.state))
        object.__setattr__(
            self, "sessions",
            _check_count(self.sessions, "a state count's sessions"))

    def to_record(self) -> Dict[str, Any]:
        return {"state": self.state, "sessions": self.sessions}


def _check_state_count_ref(value: Any) -> SessionStateCount:
    if isinstance(value, SessionStateCount):
        return value
    if isinstance(value, dict):
        unknown = set(value) - _STATE_COUNT_KEYS
        if unknown:
            raise ValueError(
                "unknown state-count keys: %s"
                % ", ".join(sorted(unknown)))
        state = _pick_any(value, ("state",), "states")
        if state is None:
            raise ValueError("a state count is missing its state")
        sessions = _pick_any(value, ("sessions", "count"), "sessions")
        if sessions is None:
            raise ValueError("a state count is missing its sessions")
        return SessionStateCount(state=state, sessions=sessions)
    raise ValueError(f"a state count is needed, got {value!r}")


def _panel_account(total_sessions: int, total_journal: int,
                   total_shared: int,
                   state_counts: Tuple[SessionStateCount, ...]
                   ) -> Tuple[str, ...]:
    tallies = ", ".join(
        f"{count.state} {count.sessions}"
        for count in sorted(
            state_counts, key=lambda count: count.state))
    return (
        f"The multi-session panel holds {total_sessions} sessions: "
        f"{total_journal} journal entries in all, {total_shared} "
        f"shared memory-map reads: {tallies}.",
        "Sessions stand by state - active first, then "
        "paused, then done - then by branch, then title, "
        "then session id, so two panels of one book diff "
        "cleanly, line by line.",
        "Every session stands on its own branch with "
        "its own journal: a journal entry named by one "
        "session never appears in another - no "
        "crosstalk.",
        "The panel is read off the book at call time - "
        "it is derived, never stored loose.",
    )


@dataclass(frozen=True)
class MultiSessionPanel:
    """The multi-session panel of one book, derived whole.

    ``rows`` are the book's sessions carried whole,
    in panel order (by state, then branch, then
    title, then session id); ``total_sessions`` is
    the rows' own count, ``total_journal_entries``
    the sum of their own journals' counts and
    ``total_shared_reads`` the sum of their shared
    reads; ``state_counts`` are the per-state
    tallies of every session in the book, in the
    order their states first appear in the panel;
    ``account`` is read off those numbers. A panel
    whose rows stand out of panel order, or whose
    tallies are not its own rows' tallies, refuses
    at construction; :func:`validate_panel` judged
    against a book refuses a stored panel that
    disagrees with the derived one.
    """

    rows: Tuple[MultiSessionPanelRow, ...] = ()
    total_sessions: int = 0
    total_journal_entries: int = 0
    total_shared_reads: int = 0
    state_counts: Tuple[SessionStateCount, ...] = ()
    account: Tuple[str, ...] = ()
    panel_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.panel_id is not None:
            object.__setattr__(
                self, "panel_id", normalize_member_id(self.panel_id))
        if isinstance(self.rows, (str, bytes)) \
                or not isinstance(self.rows, (list, tuple)):
            raise ValueError(
                f"a panel's rows must be a list of rows, "
                f"got {self.rows!r}")
        rows = tuple(_check_row_ref(r) for r in self.rows)
        seen = set()
        for row in rows:
            if row.session_id in seen:
                raise ValueError(
                    f"a panel row for session {row.session_id!r} "
                    f"already exists")
            seen.add(row.session_id)
        keys = [row.sort_key for row in rows]
        if keys != sorted(keys):
            raise ValueError(
                "a panel's rows must stand in panel order "
                "(by state, then branch, then title, then "
                "session id)")
        object.__setattr__(self, "rows", rows)
        object.__setattr__(
            self, "total_sessions",
            _check_count(self.total_sessions, "a panel's total sessions"))
        if self.total_sessions != len(rows):
            raise ValueError(
                "a panel's total sessions must be its own "
                "rows' count")
        object.__setattr__(
            self, "total_journal_entries",
            _check_count(
                self.total_journal_entries,
                "a panel's total journal entries"))
        if self.total_journal_entries != sum(
                r.journal_count for r in rows):
            raise ValueError(
                "a panel's total journal entries must be "
                "its own rows' sum")
        object.__setattr__(
            self, "total_shared_reads",
            _check_count(
                self.total_shared_reads, "a panel's total shared reads"))
        if self.total_shared_reads != sum(r.shared_reads for r in rows):
            raise ValueError(
                "a panel's total shared reads must be its "
                "own rows' sum")
        if isinstance(self.state_counts, (str, bytes)) \
                or not isinstance(self.state_counts, (list, tuple)):
            raise ValueError(
                f"a panel's state counts must be a list, "
                f"got {self.state_counts!r}")
        state_counts = tuple(
            _check_state_count_ref(c) for c in self.state_counts)
        seen_states = set()
        for count in state_counts:
            if count.state in seen_states:
                raise ValueError(
                    f"a state count named {count.state!r} "
                    f"already exists")
            seen_states.add(count.state)
        object.__setattr__(self, "state_counts", state_counts)
        if sum(c.sessions for c in state_counts) != self.total_sessions:
            raise ValueError(
                "a panel's state counts must sum to its "
                "own total sessions")
        tallies: Dict[str, int] = {}
        for row in rows:
            tallies[row.state] = tallies.get(row.state, 0) + 1
        for count in state_counts:
            if count.sessions != tallies.get(count.state, 0):
                raise ValueError(
                    "a panel's state counts must be its "
                    "own rows' counts")
        if set(tallies) != {c.state for c in state_counts}:
            raise ValueError(
                "a panel's state counts must name every "
                "state its rows carry")
        object.__setattr__(self, "account", _check_account(self.account))

    def row_for(self, session_id: Any) -> MultiSessionPanelRow:
        """The panel row one session names in this panel."""
        wanted = normalize_member_id(session_id)
        for row in self.rows:
            if row.session_id == wanted:
                return row
        raise KeyError(f"no row in the panel: session {wanted!r}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "multi_session_projects_panel",
            "slice": MULTI_SESSION_PROJECTS_SLICE,
            "panel_id": self.panel_id,
            "rows": [row.to_record() for row in self.rows],
            "total_sessions": self.total_sessions,
            "total_journal_entries": self.total_journal_entries,
            "total_shared_reads": self.total_shared_reads,
            "state_counts": [c.to_record() for c in self.state_counts],
            "account": list(self.account),
        }


def _held_sessions(source: Any) -> Tuple[ParallelSession, ...]:
    if isinstance(source, MultiSessionBook):
        return source.sessions
    if isinstance(source, MultiSessionRegistry):
        return source.list_sessions()
    if isinstance(source, (list, tuple)):
        return tuple(_check_session_ref(item) for item in source)
    raise ValueError(f"parallel sessions are needed, got {source!r}")


def derive_panel(source: Any) -> MultiSessionPanel:
    """Derive the multi-session panel from one book.

    The rows are the book's sessions carried whole,
    in panel order: by state, then branch, then
    title, then session id. *source* is a book or a
    registry. A source holding no session refuses -
    a panel of nothing is no panel.
    """
    sessions = _held_sessions(source)
    if not sessions:
        raise ValueError("a panel needs at least one parallel session")
    rows = []
    for session in sessions:
        if session.session_id is None:
            raise ValueError(
                "a panel row must name its session - a "
                "session with no id refuses derivation")
        rows.append(_row_for_session(session))
    rows = tuple(sorted(rows, key=lambda r: r.sort_key))
    order: list = []
    tally: Dict[str, int] = {}
    for row in rows:
        if row.state not in tally:
            tally[row.state] = 0
            order.append(row.state)
        tally[row.state] += 1
    state_counts = tuple(
        SessionStateCount(state=state, sessions=tally[state])
        for state in order)
    total_journal = sum(r.journal_count for r in rows)
    total_shared = sum(r.shared_reads for r in rows)
    return MultiSessionPanel(
        rows=rows, total_sessions=len(rows),
        total_journal_entries=total_journal,
        total_shared_reads=total_shared,
        state_counts=state_counts,
        account=_panel_account(
            len(rows), total_journal, total_shared, state_counts))


def validate_panel(panel: Any, source: Any = None
                   ) -> MultiSessionPanel:
    """Validate one panel into a MultiSessionPanel.

    Accepts a panel or a mapping naming ``rows`` (or
    ``sessions``), a ``total_sessions`` (or
    ``total``), ``total_journal_entries``,
    ``total_shared_reads``, ``state_counts`` (or
    ``states``), an ``account`` (or ``statements``)
    and an optional ``panel_id`` (or ``id``). With
    *source* given (a book), the panel is judged
    against the panel derived from that book.
    """
    if isinstance(panel, MultiSessionPanel):
        current = panel
    elif isinstance(panel, dict):
        unknown = set(panel) - _PANEL_KEYS
        if unknown:
            raise ValueError(
                "unknown panel keys: %s" % ", ".join(sorted(unknown)))
        rows = _pick_any(panel, ("rows", "sessions"), "rows")
        if rows is None:
            raise ValueError("a panel is missing its rows")
        total = _pick_any(panel, ("total_sessions", "total"), "totals")
        if total is None:
            raise ValueError("a panel is missing its total sessions")
        journal = _pick_any(
            panel, ("total_journal_entries", "journal_entries"),
            "journal totals")
        if journal is None:
            raise ValueError("a panel is missing its total journal entries")
        shared = _pick_any(
            panel, ("total_shared_reads", "shared_reads"), "shared totals")
        if shared is None:
            raise ValueError("a panel is missing its total shared reads")
        state_counts = _pick_any(
            panel, ("state_counts", "states"), "state counts")
        if state_counts is None:
            raise ValueError("a panel is missing its state counts")
        account = _pick_any(panel, ("account", "statements"), "accounts")
        if account is None:
            raise ValueError("a panel names no account of its own")
        kwargs: Dict[str, Any] = {
            "rows": rows, "total_sessions": total,
            "total_journal_entries": journal,
            "total_shared_reads": shared,
            "state_counts": state_counts, "account": account}
        panel_id = _pick_any(panel, ("panel_id", "id"), "panel ids")
        if panel_id is not None:
            kwargs["panel_id"] = panel_id
        current = MultiSessionPanel(**kwargs)
    else:
        raise ValueError(f"a panel must be a mapping, got {panel!r}")
    if source is not None:
        derived = derive_panel(source)
        if (current.rows != derived.rows
                or current.total_sessions != derived.total_sessions
                or current.total_journal_entries
                != derived.total_journal_entries
                or current.total_shared_reads != derived.total_shared_reads
                or current.state_counts != derived.state_counts
                or current.account != derived.account):
            raise ValueError(
                "a stored panel disagrees with the panel "
                "derived from its book")
    return current


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> MultiSessionPanel:
    """Build one validated panel, from a mapping or field words."""
    if isinstance(panel, MultiSessionPanel) and not kwargs:
        return validate_panel(panel, source)
    if isinstance(panel, dict) or panel is None:
        merged: Dict[str, Any] = {}
        if isinstance(panel, dict):
            merged.update(panel)
        merged.update(kwargs)
        return validate_panel(merged, source)
    return validate_panel(panel, source)


# ---------------------------------------------------------------------
# The isolation verdict: the whole book judged, derived.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class IsolationVerdict:
    """One isolation verdict: a whole book judged, as data.

    ``total_sessions`` counts the book's sessions and
    ``total_journal_entries`` their own journals'
    entries in all; ``distinct_journals`` and
    ``distinct_branches`` count how many journals
    and branches those sessions actually stand
    under - isolation holds exactly when both equal
    the session count; ``shared_reads`` is the
    sessions' shared memory-map reads in all;
    ``verdict`` is the book's word -
    ``parallel-isolated`` when two or more sessions
    stand apart, ``single-session`` when one stands
    alone. :func:`validate_isolation` judged against
    a book refuses a stored verdict that disagrees
    with the verdict derived from that book, and a
    verdict claiming isolation its distinct counts
    do not prove refuses at construction - crosstalk
    is never certified away.
    """

    total_sessions: int
    total_journal_entries: int
    distinct_journals: int
    distinct_branches: int
    shared_reads: int
    verdict: str

    def __post_init__(self) -> None:
        for field, what in (
                ("total_sessions", "total sessions"),
                ("total_journal_entries", "total journal entries"),
                ("distinct_journals", "distinct journals"),
                ("distinct_branches", "distinct branches"),
                ("shared_reads", "shared reads")):
            object.__setattr__(
                self, field,
                _check_count(getattr(self, field), f"a verdict's {what}"))
        if self.total_sessions < 1:
            raise ValueError("a verdict judges at least one session")
        if self.distinct_journals > self.total_sessions \
                or self.distinct_branches > self.total_sessions:
            raise ValueError(
                "a verdict's distinct counts must not "
                "exceed its own total sessions")
        verdict = _clean_text(self.verdict, "a verdict's word")
        if self.distinct_journals != self.total_sessions \
                or self.distinct_branches != self.total_sessions:
            raise ValueError(
                "a verdict whose sessions share a journal "
                "or a branch certifies no isolation - "
                "crosstalk is reported, never certified away")
        expected = "parallel-isolated" if self.total_sessions >= 2 \
            else "single-session"
        if verdict != expected:
            raise ValueError(
                "a verdict's word must be its own counts' "
                "word - a verdict is derived, never stored "
                "loose")
        object.__setattr__(self, "verdict", verdict)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "multi_session_projects_isolation",
            "slice": MULTI_SESSION_PROJECTS_SLICE,
            "total_sessions": self.total_sessions,
            "total_journal_entries": self.total_journal_entries,
            "distinct_journals": self.distinct_journals,
            "distinct_branches": self.distinct_branches,
            "shared_reads": self.shared_reads,
            "verdict": self.verdict,
        }


def derive_isolation(source: Any) -> IsolationVerdict:
    """Derive the isolation verdict of one book.

    The verdict's tallies are the derived panel's
    own, its distinct counts are read off the
    sessions' actual journals and branches, and its
    word is read off those counts. *source* is a
    book or a registry.
    """
    sessions = _held_sessions(source)
    panel = derive_panel(source)
    return IsolationVerdict(
        total_sessions=panel.total_sessions,
        total_journal_entries=panel.total_journal_entries,
        distinct_journals=len({s.journal_ref for s in sessions}),
        distinct_branches=len({s.branch for s in sessions}),
        shared_reads=panel.total_shared_reads,
        verdict="parallel-isolated" if panel.total_sessions >= 2
        else "single-session")


def _check_isolation_ref(value: Any) -> IsolationVerdict:
    if isinstance(value, IsolationVerdict):
        return value
    if isinstance(value, dict):
        unknown = set(value) - _ISOLATION_KEYS
        if unknown:
            raise ValueError(
                "unknown verdict keys: %s" % ", ".join(sorted(unknown)))

        def _needed(spellings: Tuple[str, ...], what: str) -> Any:
            picked = _pick_any(value, spellings, what)
            if picked is None:
                raise ValueError(f"a verdict is missing its {what}")
            return picked

        return IsolationVerdict(
            total_sessions=_needed(
                ("total_sessions", "total"), "total sessions"),
            total_journal_entries=_needed(
                ("total_journal_entries", "journal_entries"),
                "total journal entries"),
            distinct_journals=_needed(
                ("distinct_journals", "journals"), "distinct journals"),
            distinct_branches=_needed(
                ("distinct_branches", "branches"), "distinct branches"),
            shared_reads=_needed(("shared_reads",), "shared reads"),
            verdict=_needed(("verdict",), "verdict word"))
    raise ValueError(f"an isolation verdict is needed, got {value!r}")


def validate_isolation(verdict: Any, source: Any = None) -> IsolationVerdict:
    """Validate one verdict into an IsolationVerdict.

    With *source* given (a book), the verdict is
    judged against the verdict derived from that
    book: a stored verdict whose tallies, distinct
    counts or word disagree with the derived verdict
    refuses.
    """
    current = _check_isolation_ref(verdict)
    if source is not None:
        derived = derive_isolation(source)
        if current != derived:
            raise ValueError(
                "a stored verdict disagrees with the "
                "verdict derived from its book")
    return current


def build_isolation(verdict: Any = None, source: Any = None,
                    **kwargs: Any) -> IsolationVerdict:
    """Build one validated verdict, from a mapping or field words."""
    if isinstance(verdict, IsolationVerdict) and not kwargs:
        return validate_isolation(verdict, source)
    if isinstance(verdict, dict) or verdict is None:
        merged: Dict[str, Any] = {}
        if isinstance(verdict, dict):
            merged.update(verdict)
        merged.update(kwargs)
        return validate_isolation(merged, source)
    return validate_isolation(verdict, source)


# ---------------------------------------------------------------------
# The book: parallel sessions in held order, panels judged.
# ---------------------------------------------------------------------


def _judge_standings(sessions: Tuple[ParallelSession, ...],
                     held: Tuple[ParallelSession, ...] = ()) -> None:
    """Judge sessions against held standings: the book's laws.

    One project, one session per session reference,
    one session per branch, one journal per session,
    and no journal entry standing in two sessions -
    no crosstalk. *held* names sessions already
    standing (a registry's), judged alongside.
    """
    all_sessions = tuple(held) + tuple(sessions)
    projects = {s.project for s in all_sessions}
    if len(projects) > 1:
        raise ValueError(
            "parallel sessions stand on one project - "
            "this book names more than one")
    seen_refs = set()
    seen_branches = set()
    seen_journals = set()
    owners: Dict[str, str] = {}
    for session in all_sessions:
        if session.session_ref in seen_refs:
            raise ValueError(
                f"the session standing as "
                f"{session.session_ref!r} already stands - "
                f"one session stands once")
        seen_refs.add(session.session_ref)
        if session.branch in seen_branches:
            raise ValueError(
                f"the branch {session.branch!r} already "
                f"stands in this book - parallel sessions "
                f"stand on different branches")
        seen_branches.add(session.branch)
        if session.journal_ref in seen_journals:
            raise ValueError(
                f"the journal {session.journal_ref!r} "
                f"already stands in this book - every "
                f"session stands under its own journal")
        seen_journals.add(session.journal_ref)
        for entry in session.journal_entries:
            if entry in owners:
                raise ValueError(
                    f"journal crosstalk: entry {entry!r} "
                    f"stands in two sessions "
                    f"({owners[entry]!r} and "
                    f"{session.session_ref!r}) - a journal "
                    f"entry named by one session never "
                    f"appears in another")
            owners[entry] = session.session_ref


@dataclass(frozen=True)
class MultiSessionBook:
    """One multi-session book: its sessions, in held order.

    ``sessions`` are the parallel sessions, in held
    order, each with its provenance whole, all
    standing on one project, each on its own branch,
    each under its own journal, no journal entry
    standing in two sessions. ``panels`` are the
    book's derivations - multi-session panels of the
    whole book, each judged against the book by
    :func:`validate_book`; ``canon_note`` is the
    book's own note. The total is the sessions' own
    count, judged at construction.
    """

    title: str = ""
    sessions: Tuple[ParallelSession, ...] = ()
    panels: Tuple[MultiSessionPanel, ...] = ()
    canon_note: str = ""
    total_sessions: Optional[int] = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_title(self.title, "a book's title"))
        if isinstance(self.sessions, (str, bytes)) \
                or not isinstance(self.sessions, (list, tuple)):
            raise ValueError(
                f"a book's sessions must be a list of "
                f"sessions, got {self.sessions!r}")
        sessions = tuple(_check_session_ref(item) for item in self.sessions)
        if not sessions:
            raise ValueError("a multi-session book holds at least one session")
        seen_ids = set()
        for session in sessions:
            if session.session_id is not None:
                if session.session_id in seen_ids:
                    raise ValueError(
                        f"a parallel session named "
                        f"{session.session_id!r} already exists")
                seen_ids.add(session.session_id)
        _judge_standings(sessions)
        object.__setattr__(self, "sessions", sessions)
        if isinstance(self.panels, (str, bytes)) \
                or not isinstance(self.panels, (list, tuple)):
            raise ValueError(
                f"a book's panels must be a list of panels, "
                f"got {self.panels!r}")
        panels = tuple(
            p if isinstance(p, MultiSessionPanel)
            else validate_panel(p)
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
        object.__setattr__(self, "canon_note", self.canon_note.strip())
        given = self.total_sessions
        if given is None:
            object.__setattr__(self, "total_sessions", len(sessions))
        else:
            checked = _check_count(given, "a book's total sessions")
            if checked != len(sessions):
                raise ValueError(
                    "a book's total sessions must be its "
                    "own sessions' count")
            object.__setattr__(self, "total_sessions", checked)

    @property
    def project(self) -> str:
        """The one project every session of this book stands on."""
        return self.sessions[0].project

    def session_for(self, session_id: Any) -> ParallelSession:
        """The parallel session one id names in this book."""
        wanted = normalize_member_id(session_id)
        for session in self.sessions:
            if session.session_id == wanted:
                return session
        raise KeyError(f"no parallel session in the book: {wanted!r}")

    def session_for_branch(self, branch: Any) -> ParallelSession:
        """The session standing on one branch in this book."""
        wanted = _check_branch(branch)
        for session in self.sessions:
            if session.branch == wanted:
                return session
        raise KeyError(f"no session in the book stands on {wanted!r}")

    def panel_for(self, panel_id: Any) -> MultiSessionPanel:
        """The stored panel one id names in this book."""
        wanted = normalize_member_id(panel_id)
        for panel in self.panels:
            if panel.panel_id == wanted:
                return panel
        raise KeyError(f"no panel in the book: {wanted!r}")

    def session_ids(self) -> Tuple[str, ...]:
        """Every held session id, in held order."""
        return tuple(
            item.session_id for item in self.sessions if item.session_id)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "multi_session_projects_book",
            "slice": MULTI_SESSION_PROJECTS_SLICE,
            "title": self.title,
            "project": self.project,
            "session_ids": list(self.session_ids()),
            "session_count": len(self.sessions),
            "panel_count": len(self.panels),
        }


def validate_book(data: Any, *, require_example: bool = False
                  ) -> MultiSessionBook:
    """Validate one multi-session mapping into a book.

    The mapping names a ``schema``, a ``guide``
    mapping (its ``title``), a ``sessions`` list (or
    ``records``) and an optional ``panels`` list.
    Every session stands on its own validation, then
    the whole is judged: session ids unique, one
    project, different branches, own journals, no
    crosstalk, and every stored panel judged against
    the book. With ``require_example`` the shipped
    example is held to its pinned shape.
    """
    if isinstance(data, MultiSessionBook):
        return data
    if not isinstance(data, dict):
        raise ValidationError(
            f"a multi-session book must be a mapping, got {data!r}")
    unknown = set(data) - _MULTI_SESSION_BOOK_KEYS
    if unknown:
        raise ValidationError(
            "unknown multi-session-book keys: %s"
            % ", ".join(sorted(unknown)))
    if data.get("schema") != MULTI_SESSION_PROJECTS_SCHEMA:
        raise ValidationError(
            f"a multi-session book must carry schema "
            f"{MULTI_SESSION_PROJECTS_SCHEMA!r}, "
            f"got {data.get('schema')!r}")
    sessions = _pick_any(data, ("sessions", "records"), "sessions")
    if sessions is None:
        raise ValidationError("a multi-session book is missing its sessions")
    if not isinstance(sessions, (list, tuple)):
        raise ValidationError("a multi-session book's sessions must be a list")
    if data.get("panels") is not None \
            and not isinstance(data["panels"], (list, tuple)):
        raise ValidationError("a multi-session book's panels must be a list")
    head = data.get("guide") or {}
    if not isinstance(head, dict):
        raise ValidationError("a multi-session book's guide must be a mapping")
    unknown_head = set(head) - _BOOK_KEYS
    if unknown_head:
        raise ValidationError(
            "unknown guide keys: %s" % ", ".join(sorted(unknown_head)))
    try:
        title = _pick_any(head, ("title", "name"), "titles")
        if title is None:
            raise ValidationError("a multi-session book is missing its title")
        note = data.get("canon_note") or ""
        if not isinstance(note, str):
            raise ValidationError("a multi-session book's note must be text")
        book = MultiSessionBook(
            title=title, sessions=tuple(sessions),
            panels=tuple(data.get("panels") or ()), canon_note=note)
        for panel in book.panels:
            validate_panel(panel, book)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    if require_example:
        if book.title != _EXAMPLE_TITLE:
            raise ValidationError(
                "the shipped example multi-session book's "
                "title is not the pinned title")
        if book.session_ids() != _EXAMPLE_SESSION_IDS:
            raise ValidationError(
                "the shipped example's sessions are not "
                "the pinned sessions")
        panel = book.panel_for(_EXAMPLE_PANEL_ID)
        if tuple(r.session_id for r in panel.rows) != _EXAMPLE_PANEL_ROW_IDS:
            raise ValidationError(
                "the shipped example panel does not name "
                "its pinned rows in panel order")
        if panel.account != _EXAMPLE_PANEL_ACCOUNT:
            raise ValidationError(
                "the shipped example panel does not carry "
                "its pinned account word-for-word")
        first = book.sessions[0]
        if first.session_id != _EXAMPLE_FIRST_SESSION_ID \
                or first.title != _EXAMPLE_FIRST_SESSION_TITLE:
            raise ValidationError(
                "the shipped example's first session is "
                "not its pinned session of its pinned title")
    return book


def build_book(book: Any = None, **kwargs: Any) -> MultiSessionBook:
    """Build one validated book, from a mapping or field words."""
    if isinstance(book, MultiSessionBook) and not kwargs:
        return book
    if isinstance(book, dict):
        if "schema" in book:
            return validate_book(book)
        merged: Dict[str, Any] = dict(book)
        merged.update(kwargs)
        return MultiSessionBook(**merged)
    if book is None:
        return MultiSessionBook(**kwargs)
    raise ValueError(f"a multi-session book is needed, got {book!r}")


def _book_from(data: Any, *, require_example: bool) -> MultiSessionBook:
    try:
        return validate_book(data, require_example=require_example)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def load_multi_session_projects(
        data: Optional[Dict[str, Any]] = None) -> MultiSessionBook:
    """Load and validate the shipped example book (or *data*)."""
    raw = data if data is not None else load_resource(
        MULTI_SESSION_PROJECTS_RESOURCE)
    return _book_from(raw, require_example=True)


def load_multi_session_projects_file(path: Any) -> MultiSessionBook:
    """Load and validate a multi-session book from a file at *path*."""
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _book_from(raw, require_example=False)


# ---------------------------------------------------------------------
# The registry model: one book held session by session.
# ---------------------------------------------------------------------


class MultiSessionRegistry:
    """One project's parallel sessions, held one by one.

    The registry holds sessions, never panels or
    verdicts: the panel and the isolation verdict
    are derivations, read off the whole held book at
    call time. A whole book is judged as a book
    judges it before its sessions are held in book
    order. A session held here stands apart: a
    second session on a held branch, under a held
    journal, or naming a held journal entry refuses
    - no crosstalk, ever.
    """

    def __init__(self, book: Any = None) -> None:
        self._title: Optional[str] = None
        self._project: Optional[str] = None
        self._sessions: Dict[str, ParallelSession] = {}
        self._session_order: list = []
        self._next_session = 1
        if book is not None:
            self.register_book(book)

    def _fresh_session_id(self, held_ids: Any) -> str:
        while f"multisession-{self._next_session}" in held_ids:
            self._next_session += 1
        fresh = f"multisession-{self._next_session}"
        self._next_session += 1
        return fresh

    def _check_standing_free(self, session: ParallelSession) -> None:
        _judge_standings((session,), held=self.list_sessions())
        if self._project is not None \
                and session.project != self._project:
            raise ValueError(
                "this registry already holds sessions of "
                "a different project - parallel sessions "
                "stand on one project")

    def register_session(self, session: Any) -> ParallelSession:
        """Register one parallel session into the held book."""
        validated = _check_session_ref(session)
        if validated.session_id is not None \
                and validated.session_id in self._sessions:
            raise ValueError(
                f"a parallel session named "
                f"{validated.session_id!r} already exists")
        self._check_standing_free(validated)
        return self._hold_session(validated)

    def _hold_session(self, validated: ParallelSession) -> ParallelSession:
        if validated.session_id is None:
            validated = replace(
                validated,
                session_id=self._fresh_session_id(set(self._sessions)))
        if self._project is None:
            self._project = validated.project
        self._sessions[validated.session_id] = validated
        self._session_order.append(validated.session_id)
        return validated

    def register_book(self, book: Any) -> MultiSessionBook:
        """Register every session of one book, in order."""
        validated = build_book(book)
        if self._title is not None and validated.title != self._title:
            raise ValueError(
                "this registry already holds a multi-session "
                "book under a different title")
        if self._project is not None \
                and validated.project != self._project:
            raise ValueError(
                "this registry already holds sessions of "
                "a different project")
        for session in validated.sessions:
            if session.session_id in self._sessions:
                raise ValueError(
                    f"a parallel session named "
                    f"{session.session_id!r} already exists")
        _judge_standings(validated.sessions, held=self.list_sessions())
        self._title = validated.title
        self._project = validated.project
        for session in validated.sessions:
            self._hold_session(session)
        return self.book()

    def get_session(self, session_id: Any) -> ParallelSession:
        """The parallel session one id names among the held sessions."""
        wanted = normalize_member_id(session_id)
        if wanted not in self._sessions:
            raise KeyError(f"unknown parallel session: {wanted!r}")
        return self._sessions[wanted]

    def session_for_branch(self, branch: Any) -> ParallelSession:
        """The held session standing on one branch."""
        wanted = _check_branch(branch)
        for session_id in self._session_order:
            session = self._sessions[session_id]
            if session.branch == wanted:
                return session
        raise KeyError(f"no session held stands on {wanted!r}")

    def latest_session(self) -> ParallelSession:
        """The most recently held parallel session."""
        if not self._session_order:
            raise ValueError("no parallel session is held yet")
        return self._sessions[self._session_order[-1]]

    def list_sessions(self) -> Tuple[ParallelSession, ...]:
        """Every held parallel session, in the order they were held."""
        return tuple(self._sessions[item] for item in self._session_order)

    def book(self) -> MultiSessionBook:
        """The held sessions as one validated book."""
        if self._title is None:
            raise ValueError("no multi-session book is held yet")
        return MultiSessionBook(
            title=self._title, sessions=self.list_sessions())

    def panel(self) -> MultiSessionPanel:
        """Derive the multi-session panel of the whole held book."""
        return derive_panel(self)

    def isolation(self) -> IsolationVerdict:
        """Derive the isolation verdict of the whole held book."""
        return derive_isolation(self)


# ---------------------------------------------------------------------
# The visible surface: how the book stands, read off any book.
# ---------------------------------------------------------------------


def multi_session_refs(source: Any) -> Tuple[Tuple[str, str], ...]:
    """Every standing one source holds, in panel order.

    Each held session's branch and the session
    reference it stands under, in the order the
    derived panel shows them. *source* is a book or
    a registry.
    """
    panel = derive_panel(source)
    return tuple((row.branch, row.session_ref) for row in panel.rows)


def total_journal_entries(source: Any) -> int:
    """The journal entries one source holds, in all."""
    return derive_panel(source).total_journal_entries


# ---------------------------------------------------------------------
# Multi-session news, shaped as session records.
# ---------------------------------------------------------------------


def parallel_record(session: Any) -> Dict[str, Any]:
    """The session-news record of one parallel session."""
    current = session if isinstance(session, ParallelSession) \
        else build_session(session)
    record_out = current.to_record()
    record_out["news"] = True
    record_out["headline"] = (
        f"Parallel session ({current.state}) on "
        f"{current.branch}: \"{current.title}\" - journal "
        f"{current.journal_ref} holds {current.journal_count} "
        f"entries of its own, {current.shared_reads} shared "
        f"memory-map reads, recorded by {current.recorded_by} "
        f"on {current.recorded_on}.")
    return record_out


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of one derived panel."""
    current = validate_panel(panel, source)
    record_out = current.to_record()
    record_out["news"] = True
    record_out["headline"] = (
        f"Multi-session panel: {current.total_sessions} sessions - "
        f"{current.total_journal_entries} journal entries, "
        f"{current.total_shared_reads} shared memory-map reads.")
    return record_out


def isolation_record(verdict: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of one derived verdict."""
    current = validate_isolation(verdict, source)
    record_out = current.to_record()
    record_out["news"] = True
    record_out["headline"] = (
        f"Multi-session isolation: {current.verdict} - "
        f"{current.distinct_journals} journals and "
        f"{current.distinct_branches} branches for "
        f"{current.total_sessions} sessions.")
    return record_out


def book_record(book: Any) -> Dict[str, Any]:
    """The session-news record of one multi-session book."""
    current = book if isinstance(book, MultiSessionBook) \
        else build_book(book)
    record_out = current.to_record()
    record_out["news"] = True
    record_out["headline"] = (
        f"Multi-session per project {current.title}: "
        f"{record_out['session_count']} sessions held on "
        f"{current.project}.")
    return record_out


def plain_words(session: Any) -> str:
    """One parallel session, in one plain sentence."""
    current = session if isinstance(session, ParallelSession) \
        else build_session(session)
    return (
        f"\"{current.title}\" stands on {current.project} "
        f"on branch {current.branch} ({current.session_ref}), "
        f"{current.state}, under journal {current.journal_ref} "
        f"with {current.journal_count} entries of its own and "
        f"{current.shared_reads} shared memory-map reads. It "
        f"was recorded by {current.recorded_by} on "
        f"{current.recorded_on} (read from {current.source}).")


def panel_plain_words(source: Any) -> str:
    """The multi-session panel in plain words, in full."""
    if isinstance(source, MultiSessionPanel):
        panel = validate_panel(source)
        title = None
    elif isinstance(source, MultiSessionBook):
        panel = derive_panel(source)
        title = source.title
    else:
        raise ValueError(
            f"a multi-session source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    lines.append("Parallel sessions, in panel order:")
    for row in panel.rows:
        lines.append(
            f"{row.session_id}: \"{row.title}\" - "
            f"branch {row.branch} ({row.session_ref}), "
            f"{row.state}, journal {row.journal_ref} with "
            f"{row.journal_count} entries, {row.shared_reads} "
            f"shared reads, recorded by {row.recorded_by} "
            f"on {row.recorded_on}")
    lines.extend(panel.account)
    return "\n".join(lines)


def isolation_plain_words(source: Any) -> str:
    """The isolation verdict in plain words."""
    if isinstance(source, IsolationVerdict):
        verdict = validate_isolation(source)
    elif isinstance(source, (MultiSessionBook, MultiSessionRegistry)):
        verdict = derive_isolation(source)
    else:
        raise ValueError(
            f"a multi-session source is needed, got {source!r}")
    return (
        f"Isolation verdict: {verdict.verdict} - "
        f"{verdict.total_sessions} sessions stand under "
        f"{verdict.distinct_journals} journals on "
        f"{verdict.distinct_branches} branches, with "
        f"{verdict.total_journal_entries} journal entries "
        f"in all and no crosstalk.")


# ---------------------------------------------------------------------
# Screens: the formatters and the /multisession grammar.
# ---------------------------------------------------------------------


def _source_book(source: Any) -> MultiSessionBook:
    if source is None:
        return load_multi_session_projects()
    if isinstance(source, MultiSessionRegistry):
        return source.book()
    if isinstance(source, MultiSessionBook):
        return source
    raise ValueError(f"a multi-session book is needed, got {source!r}")


def format_parallel_session(session: Any) -> str:
    """One parallel session as a screen block, provenance whole."""
    current = session if isinstance(session, ParallelSession) \
        else build_session(session)
    lines = [
        f"{current.session_id or '-'}: \"{current.title}\" - "
        f"{current.project} on branch {current.branch} "
        f"({current.session_ref}), {current.state}, recorded "
        f"by {current.recorded_by} on {current.recorded_on}",
        f"Journal {current.journal_ref}: "
        f"{current.journal_count} entries of its own - "
        f"{', '.join(current.journal_entries)}.",
        f"Shared memory map: {current.shared_reads} reads. "
        f"(read from {current.source})",
        "This record holds a parallel session as data - "
        "it spawns no live session itself.",
    ]
    return "\n".join(lines)


def format_parallel_sessions(source: Any = None,
                             branch: Any = None) -> str:
    """Parallel sessions of one book, in held order.

    With *branch* named, only the session standing
    on that branch stands.
    """
    book = _source_book(source)
    wanted = _check_branch(branch) if branch is not None else None
    lines = [
        f"{item.session_id or '-'}: \"{item.title}\" - "
        f"branch {item.branch} ({item.session_ref}), "
        f"{item.state}, journal {item.journal_ref} with "
        f"{item.journal_count} entries, {item.shared_reads} "
        f"shared reads, recorded by {item.recorded_by}"
        for item in book.sessions
        if wanted is None or item.branch == wanted]
    if not lines:
        lines.append("No parallel sessions are held.")
    return "\n".join(lines)


def format_panel(source: Any = None) -> str:
    """The multi-session panel as a screen block."""
    if isinstance(source, MultiSessionPanel):
        panel = validate_panel(source)
        lines: list = []
    else:
        book = _source_book(source)
        if not book.sessions:
            return (f"Multi-session panel in {book.title}:\n"
                    f"No parallel sessions are held.")
        panel = derive_panel(book)
        lines = [f"Multi-session panel in {book.title}:"]
    lines.append("Parallel sessions, in panel order:")
    for row in panel.rows:
        lines.append(
            f"{row.session_id}: \"{row.title}\" - "
            f"branch {row.branch} ({row.session_ref}), "
            f"{row.state}, journal {row.journal_ref} with "
            f"{row.journal_count} entries, {row.shared_reads} "
            f"shared reads, recorded by {row.recorded_by} "
            f"on {row.recorded_on}")
    lines.extend(panel.account)
    return "\n".join(lines)


def format_isolation(source: Any = None) -> str:
    """The isolation verdict as a screen block, for the whole book."""
    if isinstance(source, IsolationVerdict):
        verdict = validate_isolation(source)
        lines = [isolation_plain_words(verdict)]
    else:
        book = _source_book(source)
        verdict = derive_isolation(book)
        lines = [f"Isolation verdict in {book.title}:",
                 isolation_plain_words(verdict)]
    lines.append(
        "This verdict is a derivation for reporting - "
        "it changes nothing any live session does.")
    return "\n".join(lines)


def format_multi_session_projects_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /multisession."""
    book = _source_book(source)
    lines = ["Multi-Session Per Project (M-162) - "
             + PLAIN_EXPLANATION, ""]
    lines.append(format_parallel_sessions(book))
    lines.append("")
    lines.append(format_panel(book))
    lines.append("")
    lines.append(format_isolation(book))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_multisession_args(args: Any) -> Tuple[str, Any]:
    """Parse the /multisession grammar both surfaces share.

    No words (or ``show`` / ``list``) shows the
    multi-session book; ``session <session-id>``
    shows one session with its provenance whole;
    ``branch <branch>`` shows the session standing
    on one branch; ``panel`` shows the multi-session
    panel derived from the whole book; ``isolation``
    shows the isolation verdict derived for the
    whole book. Anything else is a usage error
    naming the grammar. Returns
    ``(action, value-or-None)``.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() in ("show", "list"):
        return ("show", None)
    words = text.split()
    head = words[0].lower()
    if head in ("panel", "isolation") and len(words) == 1:
        return (head, None)
    if head == "session" and len(words) == 2:
        try:
            return (head, normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "branch" and len(words) == 2:
        try:
            return (head, _check_branch(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
