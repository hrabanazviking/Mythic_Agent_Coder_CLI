"""Entrys (roadmap slice M-221).

Part IX - The Mythic Method Engine. The roadmap
words: **the campaign's diary in the user's words (their domain terms preserved, per the Plain-Language Protocol) — readable by the human it was built for.*

What already ships, and what this slice adds:

* The entries book already ships as data
  (M-201, ``core/milestones.py``): a roadmap/entry
  file (parts, slices, acceptance checks, state) the
  app reads. This slice WIRES the book that book's
  book invites - several entries held across
  days with one diary over them - as data, in its
  own module, standing in the M-195 copy-and-share
  book book the M-221 book stands in: one logkeeper
  per book, and the logkeeper's charge over one
  entry across its day held as a book - a
  entry. The shipped entries stand untouched behind
  their seams: this layer holds entries as data
  over the book's days and rewrites none of them,
  and the entries book keeps its own standing.
  Entrys stand on the diary AS DATA alone: a
  entry carries a diary ref, a reference held in
  this book; holding, viewing or telling a entry
  runs no entry live, moves no keeper and files
  nothing.
* No charter row names this slice: the M-171 TUI
  redesign charter binds Part VIII alone (M-172
  to M-200) and names M-221 on no row, and the
  slice tests pin that absence live. The M-005
  method charter names no slice row either: its
  own words name the whole of Part IX as the
  part that executes the charter, and this slice
  is built to the roadmap words and that
  execution note together.

* A entry is held whole: the slice it
  answers for, named by its slice id; its title;
  the entry steps it walked, held as data in
  walk order; and the evidence it carries, held
  as data by day. The entry walk is EXPLICIT:
  its sequence stands as data
  (:data:`CHECKS`, :data:`TRANSITIONS`) -
  noted, worded, checked, read, kept -
  and a entry's standing is DERIVED at
  call time from its held steps and evidence
  alone: a entry that opens anywhere but
  noted, steps where the sequence does not
  allow, carries a bare claim in place of held
  evidence, or has not yet noted kept stands
  open, named in its gaps.
* The evidence is a closed vocabulary in two
  halves: the held evidence - day_ref,
  words_ref, keeper_record, entry_ref, evidence
  a logkeeper can point to - and the bare claims -
  feeling, memory, assertion, summary, which
  stand as no evidence at all. A entry is
  read from held evidence alone, never
  from a feeling: a entry holding a
  bare claim stands open, named in its gaps.
* A entry stands only for an ACTIVE
  slice. The book holds each slice it answers
  for as a reference record - its id, its title
  and its standing, active or queued, held as
  data copied from the roadmap's own telling. A
  entry naming a slice that stands
  nowhere in the book refuses BY NAME, and a
  entry for a slice that is not active
  refuses BY NAME beside it: the logkeeper deals with
  the slice in hand, in roadmap order, never a
  queued one, and a slice whose entry already
  stands complete is never checked twice - the
  current entry is derived, so a
  completed slice is never the current entry
  twice.
* The entry's trace is visible. A trace
  record holds one entry's walked steps
  as one trace line, exactly as walked, beside
  the entry. The derived trace is
  computed at call time from the entry's
  held steps; a held trace that no longer agrees
  with it stands stale, named in the diary - the
  trace is the walk itself, never a retelling
  of it.
* The entry index is DERIVED at call
  time from the held entries - one entry
  per complete entry, under the step it
  stands at - never a second stored copy that
  could drift. A stored index, standing verdict,
  panel, trace, order or current-entry
  claim on any record refuses by name.
* The current entry is DERIVED at call
  time - the first held entry, in held
  order, that does not yet stand complete - never
  stored where it could go stale.
* The notes are held as data: a note record
  naming its entry, its stance - note,
  concern, praise, question, a closed
  vocabulary - and what it feeds back toward,
  one record per entry stance; holding
  a note posts none of it, the rule stands as
  data (:data:`ENTRY_RULE`), and a record
  claiming a entry was actually kept,
  captured or promoted live refuses BY NAME.
  The logkeeper entries - and those entries, too,
  are held as data here, never sent.
* The shipped data file holds one example book
  in exactly the book a real entry
  file takes, a loader reads a file anywhere on
  disk, entries and views are worded as
  session news, and a small in-memory registry
  holds records one by one. The agent layer owns
  holding a entry book for a session and
  telling from it. This layer reaches no live
  entry: it writes no entry live, files nothing
  to the ledger, captures no candidate, promotes
  nothing, spawns no logkeeper, destroys nothing,
  publishes nothing, sends nothing as the user,
  exposes no secret, weakens no security and
  opens no network - it holds entries
  as data and tells them.

Honesty rules, enforced here and pinned by tests:

* **The entry walk is explicit.** A
  entry is read against the held
  steps and legal steps alone; an illegal step
  stands named in its gaps, never silently
  reordered.
* **Complete stands on held evidence alone.** A
  entry that carries a feeling, a
  memory, an assertion or a summary in place of
  held evidence stands open, named in its gaps:
  a entry is read from evidence, not
  vibes.
* **Active slices only, in roadmap order.** A
  entry for a missing or queued slice
  refuses by name; no entry is invented
  for a slice the logkeeper has not dealt with.
* **Unknown stays unknown.** A entry
  whose steps are not yet held stands with its
  steps empty - no step is invented.
* **The index, panel, verdict, trace, order
  and current entry are derived, never
  stored.** Each is derived from the held
  entries at call time; a stored one
  refuses by name, so it can never drift.
* **One entry per entry.** Two
  entries standing for one entry id
  refuse by name, and one note record stands per
  entry stance.
* **The notes are data alone.** The records
  hold the feedback; holding, viewing or telling
  them writes nothing, files nothing and posts
  nothing.
"""


from __future__ import annotations

__all__ = [
    "CHECK_FIELDS",
    "CHECKS",
    "CLAIM_DAYS",
    "HELD_EVIDENCE",
    "BARE_CLAIMS",
    "TRANSITIONS",
    "EXAMPLE_CHECK",
    "STANCES",
    "INDEX_ACTION",
    "ENTRY_RESOURCE",
    "ENTRY_SCHEMA",
    "ENTRY_SLICE",
    "ENTRY_RULE",
    "PLAIN_EXPLANATION",
    "THE_ENTRY_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "VIEW_FILTERS",
    "COMPLETE_WORDS",
    "DAY_STATES",
    "Any",
    "Dict",
    "List",
    "Optional",
    "TraceRecord",
    "EntryRecord",
    "IndexEntry",
    "DayRef",
    "NoteRecord",
    "EntryBook",
    "EntryIndex",
    "EntryPanel",
    "EntryPanelRow",
    "EntryRegistry",
    "EntryVerdict",
    "EntryView",
    "TargetCount",
    "trace_for_entry",
    "trace_record",
    "diary_record",
    "book_record",
    "build_trace",
    "build_book",
    "build_entry",
    "build_day_ref",
    "build_note",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "current_entry",
    "transition_breaks",
    "derive_index",
    "derive_panel",
    "derive_verdict",
    "entry_for_check",
    "entry_order",
    "entry_record",
    "first_note",
    "format_book",
    "format_entry",
    "format_index",
    "format_note",
    "format_check",
    "format_panel",
    "format_entry_screen",
    "format_verdict",
    "format_view",
    "index_plain_words",
    "index_record",
    "day_record",
    "load_entry",
    "load_entry_file",
    "normalize_day_state",
    "normalize_check",
    "normalize_claim_day",
    "legal_step",
    "next_check",
    "normalize_stance",
    "normalize_view_filter",
    "note_for_entry",
    "note_plain_words",
    "note_record",
    "panel_plain_words",
    "panel_record",
    "parse_entry_args",
    "green_entrys",
    "plain_lines",
    "plain_words",
    "roadmap_record",
    "segment_of",
    "trace_of",
    "trace_current",
    "shown_entrys",
    "validate_trace",
    "validate_book",
    "validate_entry",
    "validate_day_ref",
    "validate_note",
    "validate_panel",
    "validate_row",
    "validate_verdict",
    "validate_view",
    "verdict_plain_words",
    "verdict_record",
    "view_plain_words",
    "view_record",
    "entry_gaps",
    "entry_green",
    "entries_for_day",
]

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource

ENTRY_SCHEMA = "mythic.build_log/1"
ENTRY_SLICE = "M-221"
THE_ENTRY_SLICE = ENTRY_SLICE
ENTRY_RESOURCE = "build_log.yaml"
INDEX_ACTION = "index"
EXAMPLE_CHECK = "kept"
CHECK_FIELDS = ("checks", "claims")
COMPLETE_WORDS = ("complete", "open")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "complete", "open")
VERDICT_WORDS = ("kept", "held", "blocked")
DAY_STATES = ("live", "dormant")
ENTRY_RULE = 'entries are held as data alone: several entries across days stand with one diary, keepers per entry, and the human sees the whole forge at a run - a run stands as data, held by reference (a run ref), never taken live - the entry walk stands as an explicit entry sequence - noted, worded, checked, read, kept - and a entry completes only complete, complete being a state with evidence held - day ref, diary ref, keeper record, run ref - never a feeling, a memory, an assertion or a summary; holding, viewing and reading a entry runs no entry live, approves nothing, spawns no process and opens no network'
PLAIN_EXPLANATION = "The plain-language build log (M-221): the campaign's diary in the user's words (their domain terms preserved, per the Plain-Language Protocol) — readable by the human it was built for."
USAGE = 'Usage: /log | /log entry <entry-id> | /log check <check> | /log day <day-id> | /log view <view-id> | /log note <note-id> | /log index | /log panel | /log verdict'

CHECKS = ("noted", "worded", "checked", "read", "kept")
HELD_EVIDENCE = ("day_ref", "words_ref", "keeper_record", "entry_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
CLAIM_DAYS = HELD_EVIDENCE + BARE_CLAIMS
TRANSITIONS = {
    "noted": ("worded",),
    "worded": ("checked",),
    "checked": ("read",),
    "read": ("noted", "kept"),
    "kept": (),
}


def legal_step(before: Any, after: Any) -> bool:
    """Whether the gate sequence allows one step, DERIVED.

    The machine stands as data in TRANSITIONS:
    inspect steps only to build, build only to
    test, test to repair on a failure or to
    continue on a pass, repair back to build or
    test for the rerun, and continue steps
    nowhere - it is where a entry stands complete.
    A check outside the machine allows nothing.
    """
    return after in TRANSITIONS.get(before, ())


def next_check(check: Any, failed: Any = False) -> Optional[str]:
    """The step the logkeeper takes next, DERIVED from the sequence.

    Banked leads to worded and worded to
    checked; checked leads to read; at
    read a follow-up banking steps back to noted and a finished entry steps to kept;
    kept is the end of the walk and steps
    nowhere. A step outside the sequence refuses
    by name.
    """
    read = normalize_check(check)
    if read == "noted":
        return "worded"
    if read == "worded":
        return "checked"
    if read == "checked":
        return "read"
    if read == "read":
        return "noted" if failed else "kept"
    return None


_PROVENANCE = ("recorded_on", "actor", "source", "origin_session")
_RUN_KEYS = frozenset({
    "entry_id", "seq", "day_id", "title", "checks",
    "claims", "detail",
} | set(_PROVENANCE))
_SLICE_REF_KEYS = frozenset({
    "day_id", "seq", "title", "state", "detail",
} | set(_PROVENANCE))
_TRACE_KEYS = frozenset({
    "trace_id", "seq", "entry_id", "trace", "detail",
} | set(_PROVENANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_PROVENANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "entry_id", "stance", "target", "title",
    "detail",
} | set(_PROVENANCE))
_DERIVED_KEYS = frozenset({
    "standing", "complete", "greens", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "entries", "coverage", "covered", "uncovered",
    "current_entry", "next_entry", "progress", "diary",
    "current", "order", "breaks", "live"})
_LIVE_KEYS = (
    "live_entry", "entries_live", "live_question",
    "entries_raise", "raises_slice", "raised_live",
    "answers_live", "answers_question", "answered_live",
    "delivers_live", "delivered_live", "entries_live",
    "resumed_live", "days_entry", "paused_live",
    "runs_entry", "ran_entry", "spawns_process",
    "spawned_process", "builds_slice", "built_slice",
    "builds_live", "executes_slice", "executed_slice",
    "executes_live", "live_execution",
    "banks_slice", "banked_live", "entry_live",
    "pushes_slice", "pushed_live", "merges_live",
    "merged_live", "opens_network", "writes_file",
    "write_file", "sends_entry", "sent_entry",
    "posts_note", "posted_note", "traces_live",
    "traced_live", "writes_ledger", "wrote_ledger", "files_entry", "filed_live", "spawns_logkeeper", "spawned_logkeeper", "sends_entry", "sent_entry", "writes_entry", "wrote_entry")


# ---------------------------------------------------------------------
# Small judges, in the sibling trace.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_checks(value: Any) -> Tuple[str, ...]:
    """A entry's walked checks, held as data.

    The checks stand as a list of check names in
    walk order, each one a check of the explicit
    gate sequence; a walk not yet held stands
    honestly empty - no check is invented - and
    a name outside the machine refuses.
    """
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError("checks must be a list of gate sequence checks")
    return tuple(normalize_check(v) for v in value)

def _check_claims(value: Any) -> Tuple[str, ...]:
    """A entry's asked claims: claim days named as data.

    Each claim names one day from the kept
    vocabulary - the human days the gate may ask
    and the code days it must never ask, both
    held honestly as data - and a day outside
    the vocabulary refuses.
    """
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError("claims must be a list of claim days")
    return tuple(normalize_claim_day(v) for v in value)

def _check_count(value: Any, what: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{what} must be a whole number")
    if value < 0:
        raise ValueError(f"{what} must not be negative")
    return value


def _check_seq(value: Any, what: str = "a sequence") -> int:
    number = _check_count(value, what)
    if number < 1:
        raise ValueError(f"{what} must stand at 1 or later")
    return number


def _provenance(mapping: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key in _PROVENANCE:
        if key == "recorded_on":
            out[key] = _clean_text(mapping.get(key), "a recorded_on day")
        else:
            out[key] = _clean_text(mapping.get(key), f"a {key}")
    return out


def _needed(mapping: Dict[str, Any], allowed: frozenset,
            what: str) -> None:
    if not isinstance(mapping, dict):
        raise ValueError(f"{what} must be a mapping")
    for key in _LIVE_KEYS:
        if key in mapping:
            raise ValueError(
                f"{what} claims a live gate entry or slice build "
                f"execution ({key!r} is named on it): "
                f"{ENTRY_RULE}")
    for key in mapping:
        if key in _DERIVED_KEYS:
            raise ValueError(
                f"{what} carries {key!r}, which is derived from its "
                f"own fields and never stored")
        if key not in allowed:
            raise ValueError(f"{what} carries unknown field {key!r}")


def normalize_stance(value: Any) -> str:
    stance = _clean_text(value, "a stance").lower()
    if stance not in STANCES:
        raise ValueError(
            f"stance {stance!r} is not one of the held "
            f"notes: " + ", ".join(STANCES))
    return stance


def normalize_day_state(value: Any) -> str:
    state = _clean_text(value, "an slice state").lower()
    if state not in DAY_STATES:
        raise ValueError(
            f"slice state {state!r} is not one of the held "
            f"states: " + ", ".join(DAY_STATES))
    return state


def normalize_view_filter(value: Any) -> str:
    view_filter = _clean_text(value, "a view filter").lower()
    if view_filter not in VIEW_FILTERS:
        raise ValueError(
            f"view filter {view_filter!r} is not one of the held "
            f"filters: " + ", ".join(VIEW_FILTERS))
    return view_filter


def normalize_check(value: Any) -> str:
    check = _clean_text(value, "a check").lower()
    if check not in CHECKS:
        raise ValueError(
            f"check {check!r} is not one of the held "
            f"checks: " + ", ".join(CHECKS))
    return check


def normalize_claim_day(value: Any) -> str:
    day = _clean_text(value, "a claim day").lower()
    if day not in CLAIM_DAYS:
        raise ValueError(
            f"claim day {day!r} is not one of the held "
            f"days: " + ", ".join(CLAIM_DAYS))
    return day

# ---------------------------------------------------------------------
# The held entry: one slice cut from an active slice.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class EntryRecord:
    """One entry slice, held as data.

    The entry names the active slice it was
    held from, by slice id, its title, its
    verifiable checks, held as data, and its
    claims, named by entry id. The grain is
    derived, never stored: exactly one verifiable
    walk is checked against the machine. A entry whose
    checks are not yet held stands with its
    checks empty: it stands open, named in
    its gaps, and no check is invented for it.
    The entry is local data alone - no live build
    stands behind it: holding it builds nothing.
    """

    entry_id: str
    seq: int
    day_id: str
    title: str
    checks: Tuple[str, ...] = ()
    claims: Tuple[str, ...] = ()
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "entry_id", _clean_text(self.entry_id, "a entry id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "day_id", _clean_text(self.day_id, "an slice id"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a entry title"))
        object.__setattr__(
            self, "checks", _check_checks(self.checks))
        object.__setattr__(
            self, "claims", _check_claims(self.claims))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a entry detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.entry_id

    @property
    def check(self) -> str:
        """The check the entry stands at: its last walked check."""
        return self.checks[-1] if self.checks else ""

    def to_record(self) -> Dict[str, Any]:
        record = {
            "entry_id": self.entry_id, "seq": self.seq,
            "day_id": self.day_id, "title": self.title,
            "checks": list(self.checks),
            "claims": list(self.claims),
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_entry_ref(value: Any) -> EntryRecord:
    if not isinstance(value, EntryRecord):
        raise ValueError("a entry must be a EntryRecord")
    return value


def validate_entry(entry: Any) -> EntryRecord:
    return _check_entry_ref(entry)


def build_entry(record: Any = None, **kwargs: Any) -> EntryRecord:
    """Build one held entry from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, EntryRecord):
        if kwargs:
            raise ValueError("a entry stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a entry must be a mapping or a EntryRecord")
    _needed(data, _RUN_KEYS, "a entry")
    return EntryRecord(
        entry_id=data.get("entry_id"), seq=data.get("seq"),
        day_id=data.get("day_id"), title=data.get("title"),
        checks=data.get("checks"),
        claims=data.get("claims"),
        detail=data.get("detail"),
        **_provenance(data))


def _breaks_map(book: Any) -> Dict[str, Tuple[str, ...]]:
    """Map each entry to the steps it took outside the machine.

    Derived from the held entries alone: a break is
    one consecutive pair of walked checks the
    explicit gate sequence does not allow, told
    in walk order as before, then after.
    """
    found: Dict[str, Tuple[str, ...]] = {}
    for entry in book.entries:
        breaks = tuple(
            f"{before} > {after}"
            for before, after in zip(entry.checks, entry.checks[1:])
            if not legal_step(before, after))
        if breaks:
            found[entry.entry_id] = breaks
    return found

def entry_gaps(entry: Any, source: Any = None) -> Tuple[str, ...]:
    """The gaps that keep a entry from standing complete.

    Checked from the entry's own held fields alone -
    its walked steps against the explicit question
    sequence, and its carried evidence against the
    kept vocabulary: the entry opens at
    named, steps only where the sequence
    allows, carries held evidence and no bare claim,
    and a entry stands complete only when it has
    noted kept. The source names nothing
    further: no gap is borrowed from another
    entry.
    """
    read = _check_entry_ref(entry)
    gaps: List[str] = []
    if not read.checks:
        gaps.append(
            "has passed through no step: the entry has not started")
        return tuple(gaps)
    if read.checks[0] != "noted":
        gaps.append(
            f"opens at {read.checks[0]}, not at noted: "
            f"the entry opens with the reflection")
    for before, after in zip(read.checks, read.checks[1:]):
        if not legal_step(before, after):
            gaps.append(
                f"steps from {before} to {after}, which the "
                f"entry sequence does not allow")
    for day in read.claims:
        if day in BARE_CLAIMS:
            gaps.append(
                f"carries a {day} claim, a bare claim with no "
                f"held proof: complete stands on held proof alone")
    if read.checks[-1] != "kept":
        gaps.append(
            f"has not noted kept: the entry stands "
            f"at {read.checks[-1]}")
    return tuple(gaps)

def entry_green(entry: Any, source: Any = None) -> bool:
    return not entry_gaps(entry, source)


def plain_lines(entry: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the entry's own fields."""
    read = _check_entry_ref(entry)
    return (
        f"Entry: {read.title}",
        f"Day: {read.day_id}",
        f"Check: {read.check if read.check else 'none'}",
        f"Claims: "
        f"{', '.join(read.claims) if read.claims else 'none'}",
    )


def segment_of(entry: Any, source: Any = None) -> str:
    read = _check_entry_ref(entry)
    gaps = entry_gaps(read, source)
    return (
        f"{read.entry_id}: {read.title} - slice: "
        f"'{read.day_id}' - check: "
        f"'{read.check if read.check else 'none'}' - "
        f"checks: {len(read.checks)} - claims: "
        f"'{', '.join(read.claims) if read.claims else 'none'}' - "
        f"detail: '{read.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held slice reference: the active slice a book entries from.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class DayRef:
    """One slice a entry book entries from, held as a reference.

    The record names the slice, the title it
    opens and its standing - active or
    queued - held as data copied from the
    M-203 slice book's own telling. A entry
    stands only from an active reference: the
    book refuses a entry naming no held reference,
    and a entry from an queued one, BY NAME.
    """

    day_id: str
    seq: int
    title: str
    state: str
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "day_id", _clean_text(self.day_id, "an slice id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a title"))
        object.__setattr__(
            self, "state", normalize_day_state(self.state))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "an slice detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.day_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "day_id": self.day_id, "seq": self.seq,
            "title": self.title, "state": self.state,
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_day_ref(value: Any) -> DayRef:
    if not isinstance(value, DayRef):
        raise ValueError("a slice reference must be an DayRef")
    return value


def validate_day_ref(ref: Any) -> DayRef:
    return _check_day_ref(ref)


def build_day_ref(record: Any = None, **kwargs: Any) -> DayRef:
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, DayRef):
        if kwargs:
            raise ValueError(
                "a slice reference stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError(
            "a slice reference must be a mapping or an DayRef")
    _needed(data, _SLICE_REF_KEYS, "a slice reference")
    return DayRef(
        day_id=data.get("day_id"), seq=data.get("seq"),
        title=data.get("title"), state=data.get("state"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held trace trace: the human approves the trace, as data.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class TraceRecord:
    """One trace trace, held as data.

    The record names its slice and the trace the
    human active - the slice's entry ids in
    derived claim order, held exactly as
    active. The trace is of the set and its
    order, never of a step: when the derived
    trace moves, this record stands stale, named
    in the diary, until a new trace is active.
    """

    trace_id: str
    seq: int
    entry_id: str
    trace: str
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "trace_id",
            _clean_text(self.trace_id, "an trace id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "entry_id", _clean_text(self.entry_id, "an slice id"))
        object.__setattr__(
            self, "trace", _clean_text(self.trace, "an active trace"))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "an trace detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.trace_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "trace_id": self.trace_id, "seq": self.seq,
            "entry_id": self.entry_id, "trace": self.trace,
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_trace_ref(value: Any) -> TraceRecord:
    if not isinstance(value, TraceRecord):
        raise ValueError("an trace must be an TraceRecord")
    return value


def validate_trace(trace: Any) -> TraceRecord:
    return _check_trace_ref(trace)


def build_trace(record: Any = None, **kwargs: Any) -> TraceRecord:
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, TraceRecord):
        if kwargs:
            raise ValueError(
                "an trace stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError(
            "an trace must be a mapping or an TraceRecord")
    _needed(data, _TRACE_KEYS, "an trace")
    return TraceRecord(
        trace_id=data.get("trace_id"), seq=data.get("seq"),
        entry_id=data.get("entry_id"), trace=data.get("trace"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held stance: a note on a entry, held as data beside the book.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class NoteRecord:
    """One entry stance, held as data.

    The record names its entry, its stance and
    what it feeds back toward, with its title and
    its detail. One record stands per entry stance
    in a book. The record is data alone: holding
    it builds nothing and posts nothing, ever.
    """

    note_id: str
    seq: int
    entry_id: str
    stance: str
    target: str
    title: str
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "note_id", _clean_text(self.note_id, "a stance id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "entry_id", _clean_text(self.entry_id, "a entry id"))
        object.__setattr__(self, "stance", normalize_stance(self.stance))
        object.__setattr__(
            self, "target", _clean_text(self.target, "a stance target"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a stance title"))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a stance detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.note_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "note_id": self.note_id, "seq": self.seq,
            "entry_id": self.entry_id, "stance": self.stance,
            "target": self.target, "title": self.title,
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_note_ref(value: Any) -> NoteRecord:
    if not isinstance(value, NoteRecord):
        raise ValueError("a stance must be a NoteRecord")
    return value


def validate_note(stance: Any) -> NoteRecord:
    return _check_note_ref(stance)


def build_note(stance: Any = None, **kwargs: Any) -> NoteRecord:
    if stance is None:
        data = dict(kwargs)
    elif isinstance(stance, NoteRecord):
        if kwargs:
            raise ValueError("a stance stands whole or by fields, not both")
        return stance
    elif isinstance(stance, dict):
        data = dict(stance)
        data.update(kwargs)
    else:
        raise ValueError("a stance must be a mapping or a NoteRecord")
    _needed(data, _ACTION_KEYS, "a stance")
    return NoteRecord(
        note_id=data.get("note_id"), seq=data.get("seq"),
        entry_id=data.get("entry_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held view: which slices a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class EntryView:
    """A view over the book: every entry, the green, the rest."""

    view_id: str
    seq: int
    view_filter: str
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "view_id", _clean_text(self.view_id, "a view id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "view_filter", normalize_view_filter(self.view_filter))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a view detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.view_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "view_id": self.view_id, "seq": self.seq,
            "view_filter": self.view_filter, "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_view_ref(value: Any) -> EntryView:
    if not isinstance(value, EntryView):
        raise ValueError("a view must be an EntryView")
    return value


def validate_view(view: Any) -> EntryView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> EntryView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, EntryView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or an EntryView")
    _needed(data, _VIEW_KEYS, "a view")
    return EntryView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class EntryPanelRow:
    item_id: str
    standing: str
    label: str
    segment: str
    recorded_on: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id, "standing": self.standing,
            "label": self.label, "segment": self.segment,
            "recorded_on": self.recorded_on,
        }


def _row_for_entry(entry: EntryRecord,
                     source: Any = None) -> EntryPanelRow:
    return EntryPanelRow(
        item_id=entry.entry_id,
        standing="complete" if entry_green(entry, source) else "open",
        label=entry.title, segment=segment_of(entry, source),
        recorded_on=entry.recorded_on)


def _check_row_ref(value: Any) -> EntryPanelRow:
    if not isinstance(value, EntryPanelRow):
        raise ValueError("a panel row must be an EntryPanelRow")
    return value


def validate_row(row: Any, entry: Any = None,
                 source: Any = None) -> EntryPanelRow:
    read = _check_row_ref(row)
    if entry is not None:
        derived = _row_for_entry(_check_entry_ref(entry), source)
        if read != derived:
            raise ValueError(
                f"panel row {read.item_id!r} does not agree with "
                f"the row derived from its entry")
    return read


def build_row(row: Any = None, entry: Any = None,
              source: Any = None,
              **kwargs: Any) -> EntryPanelRow:
    if entry is not None:
        derived = _row_for_entry(_check_entry_ref(entry), source)
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            EntryPanelRow(**kwargs))
        return validate_row(built, entry, source)
    if isinstance(row, EntryPanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in COMPLETE_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return EntryPanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on day"))
    if row is None and kwargs:
        return EntryPanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or an EntryPanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[EntryPanelRow, ...]
                 ) -> Tuple[TargetCount, ...]:
    counts: List[TargetCount] = []
    for standing in COMPLETE_WORDS:
        number = sum(1 for row in rows if row.standing == standing)
        if number:
            counts.append(TargetCount(standing=standing, items=number))
    return tuple(counts)


def _panel_account(total_items: int, total_shown: int,
                   green_shown: int,
                   target_counts: Tuple[TargetCount, ...],
                   view_filter: str, as_of: str) -> Tuple[str, ...]:
    standing_words = ", ".join(
        f"{count.standing} {count.items}"
        for count in target_counts) or "none"
    return (
        f"The entry book holds {total_items} entries as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {green_shown} of the shown entries "
        f"stand complete.",
        "Rows stand in held order, the order the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its entry's own fields "
        "- the slice it answers for, the steps it walked in the "
        "open and the evidence it honestly carries - and no "
        "judgement is stored on any entry.",
        "Completeness is checked from the held records alone: "
        "a entry that steps outside the entry sequence, "
        "carries a bare claim in place of held evidence, or has "
        "not noted kept stands open, named in its "
        "gaps, and the entry index is derived from the "
        "held entries, never stored where it could drift.",
    )

@dataclass(frozen=True)
class EntryPanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[EntryPanelRow, ...]
    total_items: int
    total_shown: int
    target_counts: Tuple[TargetCount, ...]
    as_of: str
    account: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "panel_id": self.panel_id, "view_id": self.view_id,
            "view_filter": self.view_filter,
            "rows": [row.to_record() for row in self.rows],
            "total_items": self.total_items,
            "total_shown": self.total_shown,
            "target_counts": [c.to_record() for c in self.target_counts],
            "as_of": self.as_of, "account": list(self.account),
        }


def _resolve_view(source: Any, view: Any) -> EntryView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, EntryView):
        return view
    return book.view_for(view)


def shown_entrys(source: Any, view: Any = None
                   ) -> Tuple[EntryRecord, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.entries
    if resolved.view_filter == "complete":
        return tuple(g for g in book.entries if entry_green(g, book))
    return tuple(g for g in book.entries if not entry_green(g, book))


def entries_for_day(source: Any, day_id: Any
                      ) -> Tuple[EntryRecord, ...]:
    wanted = _clean_text(day_id, "an slice id")
    return tuple(
        g for g in _source_book(source).entries if g.day_id == wanted)


def green_entrys(source: Any) -> Tuple[EntryRecord, ...]:
    book = _source_book(source)
    return tuple(g for g in book.entries if entry_green(g, book))


def current_entry(source: Any) -> Optional[EntryRecord]:
    """The book's current entry, DERIVED at call time.

    The first held entry, in held order, that does
    not yet stand complete - where the Architect must
    look next. Nothing here is stored: the telling
    is derived from the held entries alone, so it can
    never go stale against them. A book whose every
    entry stands complete has no current entry.
    """
    book = _source_book(source)
    for entry in book.entries:
        if not entry_green(entry, book):
            return entry
    return None


def derive_panel(source: Any, view: Any = None) -> EntryPanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_entrys(book, resolved)
    rows = tuple(_row_for_entry(entry, book) for entry in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.entries), default="")
    green = sum(1 for g in shown if entry_green(g, book))
    return EntryPanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.entries), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.entries), len(shown), green, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> EntryPanel:
    if not isinstance(value, EntryPanel):
        raise ValueError("a panel must be an EntryPanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> EntryPanel:
    """Judge a stored panel against the panel derived from its book.

    Every derived field must agree; the stored
    panel's own name is its identity, not derived
    content (the M-182 entry).
    """
    read = _check_panel_ref(panel)
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(read.view_id)
                if read.view_id is not None else None)
        derived = derive_panel(book, view)
        for attr in ("view_id", "view_filter", "rows", "total_items",
                     "total_shown", "target_counts", "as_of", "account"):
            if getattr(read, attr) != getattr(derived, attr):
                raise ValueError(
                    f"panel {read.panel_id!r} disagrees with the "
                    f"panel derived from its book on {attr}")
    return read


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> EntryPanel:
    if isinstance(panel, EntryPanel):
        if kwargs:
            raise ValueError("a panel stands whole or by fields, not both")
        return validate_panel(panel, source)
    if isinstance(panel, dict):
        data = dict(panel)
        data.update(kwargs)
        rows = tuple(build_row(row) for row in data.get("rows") or ())
        counts = tuple(
            TargetCount(
                standing=_clean_text(
                    c.get("standing"), "a standing count word").lower(),
                items=_check_count(c.get("items"), "a standing count"))
            for c in data.get("target_counts") or ()
            if isinstance(c, dict))
        built = EntryPanel(
            panel_id=_clean_text(data.get("panel_id"), "a panel id"),
            view_id=data.get("view_id"),
            view_filter=normalize_view_filter(data.get("view_filter")),
            rows=rows,
            total_items=_check_count(
                data.get("total_items"), "a total_items count"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            target_counts=counts,
            as_of=_clean_text(data.get("as_of"), "an as_of day"),
            account=_check_lines(data.get("account"), "the account"))
        return validate_panel(built, source)
    if panel is None and source is not None:
        return derive_panel(source, kwargs.get("view"))
    raise ValueError("a panel must be a mapping, an EntryPanel, or derived")


def _check_lines(value: Any, what: str) -> Tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError(f"{what} must be a list of lines")
    lines = []
    for line in value:
        lines.append(_clean_text(line, f"a line of {what}"))
    return tuple(lines)


def _verdict_word(total_shown: int, green_shown: int) -> str:
    if total_shown > 0 and green_shown == total_shown:
        return "kept"
    if green_shown == 0:
        return "blocked"
    return "held"


@dataclass(frozen=True)
class EntryVerdict:
    verdict: str
    view_id: Optional[str]
    total_shown: int
    green_shown: int
    latest_on: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict, "view_id": self.view_id,
            "total_shown": self.total_shown,
            "green_shown": self.green_shown,
            "latest_on": self.latest_on,
        }


def derive_verdict(source: Any, view: Any = None) -> EntryVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_entrys(book, resolved)
    green = sum(1 for g in shown if entry_green(g, book))
    latest = max((g.recorded_on for g in shown), default="")
    return EntryVerdict(
        verdict=_verdict_word(len(shown), green),
        view_id=resolved.view_id, total_shown=len(shown),
        green_shown=green, latest_on=latest)


def _check_verdict_ref(value: Any) -> EntryVerdict:
    if not isinstance(value, EntryVerdict):
        raise ValueError("a verdict must be an EntryVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> EntryVerdict:
    read = _check_verdict_ref(verdict)
    if read.verdict not in VERDICT_WORDS:
        raise ValueError(f"verdict {read.verdict!r} is not a held word")
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(read.view_id)
                if read.view_id is not None else None)
        derived = derive_verdict(book, view)
        if read != derived:
            raise ValueError(
                "the stored verdict disagrees with the verdict "
                "derived from its book")
    return read


def build_verdict(verdict: Any = None, source: Any = None,
                  **kwargs: Any) -> EntryVerdict:
    if isinstance(verdict, EntryVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = EntryVerdict(
            verdict=_clean_text(data.get("verdict"), "a verdict"),
            view_id=data.get("view_id"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            green_shown=_check_count(
                data.get("green_shown"), "a green_shown count"),
            latest_on=_clean_text(data.get("latest_on"), "a latest day"))
        return validate_verdict(built, source)
    if verdict is None and source is not None:
        return derive_verdict(source, kwargs.get("view"))
    raise ValueError(
        "a verdict must be a mapping, an EntryVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held slices' citations at call time.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexEntry:
    check: str
    entry_id: str
    title: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "check": self.check, "entry_id": self.entry_id,
            "title": self.title,
        }


@dataclass(frozen=True)
class EntryIndex:
    """The entry index, derived from the held entries.

    The index names one entry per green entry, in
    held order - the entry's own one verifiable
    check, its entry id and its title - and the
    entries that do not stand complete, named in its
    gaps. Nothing here is stored on any entry: the
    index is derived at call time from the held
    records alone, so it can never drift from them.
    """

    entries: Tuple[IndexEntry, ...]
    gaps: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "entries": [e.to_record() for e in self.entries],
            "gaps": list(self.gaps),
        }


def derive_index(source: Any) -> EntryIndex:
    """Derive the entry index from the book's held entries."""
    book = _source_book(source)
    entries = tuple(
        IndexEntry(check=g.check, entry_id=g.entry_id,
                   title=g.title)
        for g in book.entries if entry_green(g, book))
    gaps = tuple(
        g.entry_id for g in book.entries if not entry_green(g, book))
    return EntryIndex(entries=entries, gaps=gaps)


def entry_for_check(source: Any, check: Any) -> Optional[EntryRecord]:
    """The first held entry one check reaches, or none - honestly."""
    if check is None:
        return None
    if not isinstance(check, str):
        raise ValueError("an check must be a string naming the check")
    wanted = check.strip()
    if not wanted:
        return None
    for entry in _source_book(source).entries:
        if entry.check == wanted:
            return entry
    return None


def transition_breaks(source: Any) -> Tuple[str, ...]:
    """Every step outside the gate sequence, DERIVED.

    One telling per break, in held order: the entry
    that took it and the step it took, before,
    then after. A book whose entries all walk inside
    the machine tells none.
    """
    book = _source_book(source)
    return tuple(
        f"{entry_id}: {step}"
        for entry_id, steps in _breaks_map(book).items()
        for step in steps)

def entry_order(source: Any,
              day_id: Any = None) -> Tuple[EntryRecord, ...]:
    """The held entries in their held order, DERIVED at call time.

    Entrys stand in the order the book holds them -
    the order their slices were taken - optionally
    for one slice alone. Nothing here is stored:
    the order is the book's own held order, told.
    """
    book = _source_book(source)
    entries = list(book.entries)
    if day_id is not None:
        wanted = _clean_text(day_id, "a slice id")
        entries = [r for r in entries if r.day_id == wanted]
    return tuple(entries)

def trace_of(source: Any, entry_id: Any) -> str:
    """One entry's trace, DERIVED at call time.

    The entry's walked checks joined as one trace
    line, in walk order. A entry that has walked
    nowhere traces empty: the trace tells only
    what stands walked, and the walk is named
    elsewhere.
    """
    entry = _source_book(source).entry_for(entry_id)
    return " > ".join(entry.checks)

def trace_for_entry(source: Any,
                  entry_id: Any) -> Optional[TraceRecord]:
    """The held trace for one entry, or none - honestly."""
    wanted = _clean_text(entry_id, "a entry id")
    for record in _source_book(source).traces:
        if record.entry_id == wanted:
            return record
    return None

def trace_current(source: Any, entry_id: Any) -> bool:
    """Whether the held trace agrees with the derived trace.

    The trace stands current only while the trace
    it holds is the trace the book derives now; a
    moved walk leaves it stale, and no trace at
    all traces nothing.
    """
    trace = trace_for_entry(source, entry_id)
    if trace is None:
        return False
    return trace.trace == trace_of(source, entry_id)

def note_for_entry(source: Any, entry_id: Any,
                   stance: Any = None) -> Optional[NoteRecord]:
    """The held stance target for one entry (and stance, when named)."""
    wanted = _clean_text(entry_id, "a entry id")
    for record in _source_book(source).notes:
        if record.entry_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_note(source: Any) -> Optional[NoteRecord]:
    """The first held stance target, standing for the slice targets, or none."""
    notes = _source_book(source).notes
    return notes[0] if notes else None


def diary_record(source: Any = None) -> Dict[str, Any]:
    """The entry diary, DERIVED here from the held entries alone.

    The diary counts the held entries by their
    derived completeness - green and red - names
    the current entry, the first that does not yet
    stand complete, tells each held entry's trace
    standing - current while its held trace
    agrees with its derived trace, stale when it
    has moved, unheld while no trace stands for
    it - and names every step the held entries took
    outside the gate sequence. Nothing here is
    stored: the telling is derived at call time.
    """
    book = _source_book(source)
    standings = []
    for standing in COMPLETE_WORDS:
        number = sum(
            1 for g in book.entries
            if ("complete" if entry_green(g, book) else "open") == standing)
        standings.append({"standing": standing, "entry_records": number})
    current = current_entry(book)
    traces = []
    for entry in book.entries:
        trace = trace_for_entry(book, entry.entry_id)
        if trace is None:
            standing = "unheld"
        elif trace_current(book, entry.entry_id):
            standing = "current"
        else:
            standing = "stale"
        traces.append({"entry_id": entry.entry_id, "trace": standing})
    return {
        "type": "entry_well",
        "slice": ENTRY_SLICE,
        "standings": standings,
        "total": len(book.entries),
        "current_entry": current.entry_id if current is not None else None,
        "traces": traces,
        "breaks": list(transition_breaks(book)),
    }

def roadmap_record() -> Dict[str, Any]:
    """This slice's own roadmap standing, proved from the roadmap itself.

    The record loads this day's own roadmap through
    the shipped M-017 layer for real and tells its
    counts as they stand: 272 slices in 11 parts,
    the noted prefix, the next slice where the
    entry entries, and M-221's own ledger
    standing in Part IX.
    """
    from .roadmap_slices import load_roadmap
    roadmap = load_roadmap()
    own = roadmap.slice(ENTRY_SLICE)
    next_slice = roadmap.next_slice()
    return {
        "type": "entry_roadmap",
        "slice": ENTRY_SLICE,
        "roadmap_file": "roadmap_slices.yaml",
        "roadmap": roadmap.roadmap,
        "parts": len(roadmap.parts),
        "slices": len(roadmap.slices),
        "done": len(roadmap.done()),
        "next_slice": next_slice.id if next_slice is not None else None,
        "m221_title": own.title,
        "m221_part": own.part,
        "m221_status": own.status,
    }


# ---------------------------------------------------------------------
# The book: slices, entries, views, notes and trace traces held
# together, one pinned panel at most per telling, and no verdict,
# index, trace or order ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class EntryBook:
    title: str
    slices: Tuple[DayRef, ...] = ()
    entries: Tuple[EntryRecord, ...] = ()
    views: Tuple[EntryView, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    traces: Tuple[TraceRecord, ...] = ()
    panels: Tuple[EntryPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        slices = tuple(_check_day_ref(g) for g in self.slices)
        entries = tuple(_check_entry_ref(g) for g in self.entries)
        views = tuple(_check_view_ref(v) for v in self.views)
        notes = tuple(_check_note_ref(m) for m in self.notes)
        traces = tuple(_check_trace_ref(a) for a in self.traces)
        panels = tuple(_check_panel_ref(pn) for pn in self.panels)
        seen_ids = set()
        seen_seqs = set()
        for ref in slices:
            if ref.day_id in seen_ids:
                raise ValueError(
                    f"two slice references stand under id {ref.day_id!r}")
            if ref.seq in seen_seqs:
                raise ValueError(
                    f"two slice references stand at sequence {ref.seq}")
            seen_ids.add(ref.day_id)
            seen_seqs.add(ref.seq)
        entry_ids = set()
        entry_seqs = set()
        for entry in entries:
            if entry.entry_id in entry_ids:
                raise ValueError(
                    f"two entries stand under id {entry.entry_id!r}")
            if entry.seq in entry_seqs:
                raise ValueError(
                    f"two entries stand at sequence {entry.seq}")
            entry_ids.add(entry.entry_id)
            entry_seqs.add(entry.seq)
        by_slice = {ref.day_id: ref for ref in slices}
        for entry in (entries if slices else ()):

            ref = by_slice.get(entry.day_id)
            if ref is None:
                raise ValueError(
                    f"entry {entry.entry_id!r} is held from slice "
                    f"{entry.day_id!r}, which stands nowhere in "
                    f"this book")
            if ref.state != "live":
                raise ValueError(
                    f"entry {entry.entry_id!r} is held from slice "
                    f"{entry.day_id!r}, which is not active: "
                    f"no slice is held from an queued slice")
        view_ids = set()
        view_seqs = set()
        for view in views:
            if view.view_id in view_ids:
                raise ValueError(
                    f"two views stand under id {view.view_id!r}")
            if view.seq in view_seqs:
                raise ValueError(
                    f"two views stand at sequence {view.seq}")
            view_ids.add(view.view_id)
            view_seqs.add(view.seq)
        note_ids = set()
        note_seqs = set()
        note_targets = set()
        for record in notes:
            if record.note_id in note_ids:
                raise ValueError(
                    f"two notes stand under id {record.note_id!r}")
            if record.seq in note_seqs:
                raise ValueError(
                    f"two notes stand at sequence {record.seq}")
            target = (record.entry_id, record.stance)
            if target in note_targets:
                raise ValueError(
                    f"two stance records stand for entry "
                    f"{record.entry_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per entry target")
            note_ids.add(record.note_id)
            note_seqs.add(record.seq)
            note_targets.add(target)
        trace_ids = set()
        trace_seqs = set()
        trace_entrys = set()
        entry_ids = {entry.entry_id for entry in entries}
        for record in traces:
            if record.trace_id in trace_ids:
                raise ValueError(
                    f"two traces stand under id {record.trace_id!r}")
            if record.seq in trace_seqs:
                raise ValueError(
                    f"two traces stand at sequence {record.seq}")
            if record.entry_id in trace_entrys:
                raise ValueError(
                    f"two traces stand for entry "
                    f"{record.entry_id!r}: one trace stands "
                    f"per entry walk")
            if entries and record.entry_id not in entry_ids:
                raise ValueError(
                    f"trace {record.trace_id!r} traces entry "
                    f"{record.entry_id!r}, which stands nowhere in "
                    f"this book")
            trace_ids.add(record.trace_id)
            trace_seqs.add(record.seq)
            trace_entrys.add(record.entry_id)
        object.__setattr__(
            self, "days", tuple(sorted(slices, key=lambda g: g.seq)))
        object.__setattr__(
            self, "entry_records", tuple(sorted(entries, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "notes", tuple(sorted(notes, key=lambda m: m.seq)))
        object.__setattr__(
            self, "traces",
            tuple(sorted(traces, key=lambda a: a.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.entries + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.entry_id for g in self.entries) + tuple(
            v.view_id for v in self.views)

    def entry_ids(self) -> Tuple[str, ...]:
        return tuple(g.entry_id for g in self.entries)

    def day_ids(self) -> Tuple[str, ...]:
        return tuple(g.day_id for g in self.slices)

    def entry_for(self, entry_id: Any) -> EntryRecord:
        wanted = _clean_text(entry_id, "a entry id")
        for entry in self.entries:
            if entry.entry_id == wanted:
                return entry
        raise KeyError(f"no entry named {wanted!r} stands in this book")

    def slice_for(self, day_id: Any) -> DayRef:
        wanted = _clean_text(day_id, "an slice id")
        for ref in self.slices:
            if ref.day_id == wanted:
                return ref
        raise KeyError(f"no slice named {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> EntryView:
        wanted = _clean_text(view_id, "a view id")
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no view named {wanted!r} stands in this book")

    def note_for(self, note_id: Any) -> NoteRecord:
        wanted = _clean_text(note_id, "a stance id")
        for record in self.notes:
            if record.note_id == wanted:
                return record
        raise KeyError(f"no stance named {wanted!r} stands in this book")

    def trace_for(self, trace_id: Any) -> TraceRecord:
        wanted = _clean_text(trace_id, "an trace id")
        for record in self.traces:
            if record.trace_id == wanted:
                return record
        raise KeyError(f"no trace named {wanted!r} stands in this book")

    def item_for(self, item_id: Any) -> Any:
        wanted = _clean_text(item_id, "an item id")
        for entry in self.entries:
            if entry.entry_id == wanted:
                return entry
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "days": [g.to_record() for g in self.slices],
            "entry_records": [g.to_record() for g in self.entries],
            "views": [v.to_record() for v in self.views],
            "notes": [m.to_record() for m in self.notes],
            "traces": [a.to_record() for a in self.traces],
            "panels": [pn.to_record() for pn in self.panels],
        }


def _judge_book_panels(book: EntryBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: EntryBook) -> None:
    if book.title != "The plain-language build log at the M-221 slice day":
        raise ValueError("the shipped example book carries another title")
    if len(book.slices) != 3 or len(book.entries) != 5 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold three slice references, five entries and two views")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.traces) != 1:
        raise ValueError("the shipped example book must hold one trace record")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-m220-day":
        raise ValueError("the pinned panel is panel-m220-day")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "held" or verdict.green_shown != 3:
        raise ValueError("the shipped example book verdict must stand held at three complete of five")
    index = derive_index(book)
    if [e.check for e in index.entries] != ["kept", "kept", "kept"]:
        raise ValueError("the shipped example book index must derive the three held complete entries in held order")
    if index.gaps != ("entry-bare-entry", "entry-leaping-entry"):
        raise ValueError("the shipped example book must leave the bare and leaping entries honestly open, named in its gaps")
    found = entry_for_check(book, EXAMPLE_CHECK)
    if found is None or found.entry_id != "entry-held-entry":
        raise ValueError("the shipped example book must reach its opening entry under the example check")
    if trace_of(book, "entry-held-entry") != "noted > worded > checked > read > kept":
        raise ValueError("the shipped example book must derive the opening entry's trace from its walked steps")
    if not trace_current(book, "entry-held-entry"):
        raise ValueError("the shipped example book must hold the opening entry's trace current")
    first = first_note(book)
    if first is None or first.note_id != "note-note-first":
        raise ValueError("the shipped example book must hold the opening note as its first note entry")

def validate_book(data: Any, *, require_example: bool = False) -> EntryBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, EntryBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a entry book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live slice build or execution "
                f"({key!r} is named on it): {ENTRY_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its entries under a view")
    if "entry_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held entries at call time")
    if "diary" in data or "current_entry" in data:
        raise ValueError(
            "a book stores no diary and no current entry: both are "
            "derived from its held entries at call time")
    if "trace" in data or "order" in data:
        raise ValueError(
            "a book stores no trace and no order: both are derived "
            "from its held entries at call time; an trace record "
            "holds the trace the human active")
    if data.get("schema") is not None and (
            data["schema"] != ENTRY_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{ENTRY_SCHEMA!r}")
    if data.get("slice") is not None and (
            data["slice"] != ENTRY_SLICE):
        raise ValueError(
            f"a book's slice must be {ENTRY_SLICE!r}")
    head = data.get("entry_head") or data.get("build_log") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's entry head must be a mapping")
    title = head.get("title") or data.get("title")
    slices = tuple(build_day_ref(g) for g in data.get("days") or ())
    entries = tuple(build_entry(g) for g in data.get("entry_records") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    traces = tuple(build_trace(a) for a in data.get("traces") or ())
    book = EntryBook(
        title=title, slices=slices, entries=entries, views=views,
        notes=notes, traces=traces, panels=())
    panels = tuple(
        build_panel(pn, book) for pn in data.get("panels") or ())
    book = EntryBook(
        title=book.title, slices=book.slices, entries=book.entries,
        views=book.views, notes=book.notes,
        traces=book.traces, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> EntryBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (EntryBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or an EntryBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> EntryBook:
    return validate_book(data, require_example=require_example)


def load_entry(
        data: Optional[Dict[str, Any]] = None) -> EntryBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(ENTRY_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_entry_file(path: Any) -> EntryBook:
    """Load one entry file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: slice references, entries and views held one by one.
# ---------------------------------------------------------------------

class EntryRegistry:
    """An in-memory holding of slice references, entries and views.

    The registry is the pure layer's model of a
    session's entry book: slice references are
    held under their ids, entries are held under
    their ids, one entry per id and per sequence,
    and views are held in worded order, one view
    per sequence and per id. Holding is data only -
    nothing held here builds anything, executes
    anything, or opens a network.
    """

    def __init__(self, book: Any = None) -> None:
        self._slices: List[DayRef] = []
        self._entrys: List[EntryRecord] = []
        self._views: List[EntryView] = []
        self._title: Optional[str] = None
        if book is not None:
            self.register_book(book)

    def title(self) -> Optional[str]:
        return self._title

    def _fresh_view_id(self, held_ids: Any) -> str:
        n = 1
        while f"view-{n}" in held_ids:
            n += 1
        return f"view-{n}"

    def _register(self, held: List[Any], item: Any,
                  id_attr: str, what: str) -> Any:
        for other in held:
            if getattr(other, id_attr) == getattr(item, id_attr):
                raise ValueError(
                    f"a {what} already stands under id "
                    f"{getattr(item, id_attr)!r}")
            if other.seq == item.seq:
                raise ValueError(
                    f"a {what} already stands at sequence {item.seq}")
        held.append(item)
        held.sort(key=lambda held_item: held_item.seq)
        return item

    def register_day_ref(self, item: Any) -> DayRef:
        """Hold one slice reference, checked whole before held."""
        read = _check_day_ref(item)
        return self._register(
            self._slices, read, "day_id", "slice reference")

    def register_entry(self, item: Any) -> EntryRecord:
        """Hold one entry, checked whole before held."""
        read = _check_entry_ref(item)
        return self._register(
            self._entrys, read, "entry_id", "entry")

    def register_view(self, view: Any) -> EntryView:
        """Hold one view; a view naming no id takes a fresh one."""
        read = _check_view_ref(view)
        if not read.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            read = build_view({**read.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, read, "view_id", "view")

    def register_book(self, book: Any) -> EntryBook:
        """Hold a whole book's records, under its title."""
        read = build_book(book)
        if self._title is not None and read.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {read.title!r}")
        for ref in read.slices:
            self.register_day_ref(ref)
        for entry in read.entries:
            self.register_entry(entry)
        for view in read.views:
            self.register_view(view)
        self._title = read.title
        return self.book()

    def book(self) -> EntryBook:
        return EntryBook(
            title=self._title or "An unheld entry book",
            slices=tuple(self._slices), entries=tuple(self._entrys),
            views=tuple(self._views), notes=(), traces=(), panels=())

    def list_slices(self) -> Tuple[DayRef, ...]:
        return tuple(self._slices)

    def list_entrys(self) -> Tuple[EntryRecord, ...]:
        return tuple(self._entrys)

    def list_views(self) -> Tuple[EntryView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._entrys) + tuple(self._views)

    def get_slice(self, day_id: Any) -> DayRef:
        return self.book().slice_for(day_id)

    def get_entry(self, entry_id: Any) -> EntryRecord:
        return self.book().entry_for(entry_id)

    def get_view(self, view_id: Any) -> EntryView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records traced for the diary target.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> EntryBook:
    if source is None:
        return load_entry()
    if isinstance(source, EntryBook):
        return source
    if isinstance(source, EntryRegistry):
        return source.book()
    return build_book(source)


def _provenance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _PROVENANCE}


def entry_record(entry: Any, source: Any = None) -> Dict[str, Any]:
    read = _check_entry_ref(entry)
    book = _source_book(source) if source is not None else None
    record = {
        "type": "entry_entry",
        "slice": ENTRY_SLICE,
        "entry_id": read.entry_id,
        "day_id": read.day_id,
        "title": read.title,
        "segment": segment_of(read, book),
        "complete": entry_green(read, book),
        "gaps": list(entry_gaps(read, book)),
    }
    record.update(_provenance_record(read))
    return record


def day_record(ref: Any) -> Dict[str, Any]:
    read = _check_day_ref(ref)
    record = {
        "type": "entry_slice",
        "slice": ENTRY_SLICE,
        "day_id": read.day_id,
        "title": read.title,
        "state": read.state,
    }
    record.update(_provenance_record(read))
    return record


def trace_record(record_in: Any) -> Dict[str, Any]:
    read = _check_trace_ref(record_in)
    record = {
        "type": "entry_trace",
        "slice": ENTRY_SLICE,
        "trace_id": read.trace_id,
        "entry_id": read.entry_id,
        "trace": read.trace,
    }
    record.update(_provenance_record(read))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    read = _check_view_ref(view)
    record = {
        "type": "entry_view",
        "slice": ENTRY_SLICE,
        "view_id": read.view_id, "seq": read.seq,
        "view_filter": read.view_filter,
    }
    record.update(_provenance_record(read))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    read = _check_note_ref(record_in)
    record = {
        "type": "entry_note",
        "slice": ENTRY_SLICE,
        "note_id": read.note_id,
        "entry_id": read.entry_id,
        "stance": read.stance,
    }
    record.update(_provenance_record(read))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    read = validate_panel(panel, source)
    record = {"type": "entry_panel",
              "slice": ENTRY_SLICE}
    record.update(read.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, EntryVerdict):
        read = validate_verdict(verdict, source)
    else:
        read = derive_verdict(_source_book(verdict), view)
    record = {"type": "entry_verdict",
              "slice": ENTRY_SLICE}
    record.update(read.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, EntryIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "entry_index",
              "slice": ENTRY_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    read = _source_book(book)
    record = {"type": "entry_book",
              "slice": ENTRY_SLICE,
              "title": read.title}
    record.update(read.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(entry: Any, source: Any = None) -> str:
    read = _check_entry_ref(entry)
    return (
        f"{read.title} - from {read.day_id}: "
        f"check {read.check if read.check else 'none'}, "
        f"claims "
        f"{', '.join(read.claims) if read.claims else 'none'}. "
        f"{read.detail}")


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The entries stand {verdict.verdict}: "
        f"{verdict.green_shown} of {verdict.total_shown} shown "
        f"entries stand complete.")


def view_plain_words(view: Any) -> str:
    read = _check_view_ref(view)
    return f"View {read.view_id}: shows {read.view_filter} entries."


def note_plain_words(record_in: Any) -> str:
    read = _check_note_ref(record_in)
    return (
        f"Note {read.note_id}: {read.stance} "
        f"{read.entry_id}, toward {read.target}. "
        f"{read.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, EntryIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.entries)} green entries; "
        f"red, named in its gaps: {gaps}.")

def format_entry(entry: Any, source: Any = None) -> str:
    read = _check_entry_ref(entry)
    book = _source_book(source) if source is not None else None
    lines = [f"{read.title} ({read.entry_id})"]
    lines.extend(plain_lines(read))
    lines.append(read.detail)
    if entry_green(read, book):
        lines.append(
            "This entry stands complete - it walked the question "
            "sequence in the open from noted to kept, "
            "and it carries held evidence alone.")
    else:
        lines.append(
            "This entry stands open - it stands named in "
            f"its gaps: {', '.join(entry_gaps(read, book))}, and "
            "nothing is invented for it.")
    return "\n".join(lines)

def format_view(view: Any) -> str:
    read = _check_view_ref(view)
    return (
        f"View {read.view_id}: filter {read.view_filter} - "
        f"{read.detail}")


def format_note(record_in: Any) -> str:
    read = _check_note_ref(record_in)
    lines = [
        f"Entry note {read.stance} {read.entry_id} "
        f"({read.note_id}): {read.title}. {read.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or reading it builds nothing, executes nothing "
        "and posts no note.")
    return "\n".join(lines)


def format_check(source: Any, check: Any) -> str:
    entry = entry_for_check(source, check)
    if entry is not None:
        return format_entry(entry, source)
    wanted = check.strip() if isinstance(check, str) else check
    return (
        f"No held entry stands under check {wanted!r} yet - the "
        f"check reaches nothing in this book, and no entry is "
        f"invented for it.")


def format_book(source: Any = None, day_id: Any = None) -> str:
    book = _source_book(source)
    entries = (entries_for_day(book, day_id)
              if day_id is not None else book.entries)
    lines = [f"The Entry Gate (M-221) - {book.title}"]
    lines.extend(segment_of(entry, book) for entry in entries)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Entry panel under view {panel.view_id}:"]
    lines.extend(row.segment for row in panel.rows)
    lines.extend(panel.account)
    return "\n".join(lines)


def format_verdict(source: Any = None, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return verdict_plain_words(source, view) + (
        f" (view {verdict.view_id}, as of {verdict.latest_on})")


def format_index(source: Any = None) -> str:
    book = _source_book(source)
    index = derive_index(book)
    lines = ["Entry index, derived from the held entries:"]
    for entry in index.entries:
        lines.append(f"{entry.check} - {entry.title} ({entry.entry_id})")
    if index.gaps:
        lines.append(
            "Red, named honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "builds nothing, executes nothing and opens no network.")
    return "\n".join(lines)


def format_entry_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "The Entry Gate (M-221)",
        f"{book.title}: {len(book.entries)} entries held, "
        f"{len(green_entrys(book))} entries standing green, "
        f"{len(book.notes)} notes held.",
    ]
    if book.views:
        panel = derive_panel(book, book.views[0])
        lines.append(
            f"{panel.total_shown} of {panel.total_items} items show "
            f"under the first view.")
        lines.extend(row.segment for row in panel.rows)
    lines.append(index_plain_words(book))
    lines.append(PLAIN_EXPLANATION)
    return "\n".join(lines)


def parse_entry_args(args: Any) -> Tuple[str, Any]:
    """Parse the /entry grammar into (stance, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("entry", "view", "note"):
        if len(parts) != 2:
            raise ValueError(USAGE)
        return (head, parts[1])
    if head in ("check", "day"):
        if len(parts) < 2:
            raise ValueError(USAGE)
        return (head, " ".join(parts[1:]))
    if head in ("index", "panel", "verdict") and len(parts) == 1:
        return (head, None)
    raise ValueError(USAGE)
