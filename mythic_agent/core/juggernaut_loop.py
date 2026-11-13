"""The Juggernaut loop as runtime (roadmap slice M-204).

Part IX - The Mythic Method Engine. The roadmap
words: *inspect, build, test, repair, continue,
per slice, without asking file/framework questions
the code can answer; the loop's state machine is
explicit and visible.*

What already ships, and what this slice adds:

* The M-005 method charter holds the Juggernaut
  plug as doctrine - the working loop is inspect,
  build, test, repair, continue; the forge takes
  initiative on every technical detail and asks
  the human only about product meaning, desired
  behaviour, values, or creative direction. The
  M-203 slicing book holds the drafts the loop
  walks, and the M-201 campaigns book holds a
  campaign as data. What nothing held is *the
  loop itself as a book*: one run of the loop per
  slice, its walked phases held as data against
  an explicit state machine, and the questions
  it asked held beside them. This slice is that
  book, in its own module, standing in the M-195
  copy-and-share book shape the M-203 book stands
  in. The shipped roads stand untouched behind
  their seams: this layer holds loop runs as
  data over the slicing book's slices and
  rewrites none of them.

* No charter row names this slice: the M-171 TUI
  redesign charter binds Part VIII alone (M-172
  to M-200) and names M-204 on no row, and the
  slice tests pin that absence live. The M-005
  method charter names no slice row either: its
  own words name the whole of Part IX as the
  part that executes the charter, and this slice
  is built to the roadmap words and that
  execution note together - its Juggernaut plug
  (F-04) is the doctrine this runtime holds.

* A loop run is held whole: the slice it runs,
  named by its slice id; its title; the phases
  it walked, held as data in walk order; and
  the questions it asked the human, held as
  data by kind. The state machine is EXPLICIT:
  its phases and its legal steps stand as data
  (:data:`PHASES`, :data:`TRANSITIONS`), and a
  run's standing is DERIVED at call time from
  its held phases and questions alone: a run
  that opens anywhere but inspect, steps where
  the machine does not allow, asks a question
  the code can answer, or has not yet reached
  continue stands unsound, named in its gaps.
* The questions are a closed vocabulary in two
  halves: the human questions - meaning,
  behaviour, values, direction, the only
  questions the loop may ask - and the code
  questions - file, framework, table, function,
  which the code answers itself and the loop
  must never ask. A run holding a code question
  stands unsound, named in its gaps.
* A run stands only for an ACTIVE slice. The
  book holds each slice it runs for as a
  reference record - its id, its title and its
  standing, active or queued, held as data
  copied from the roadmap's own telling. A run
  naming a slice that stands nowhere in the
  book refuses BY NAME, and a run for a slice
  that is not active refuses BY NAME beside
  it: the loop runs the slice in hand, never a
  queued one.
* The loop's trace is visible. A trace record
  holds one run's walked phases as one trace
  line, exactly as walked, beside the run. The
  derived trace is computed at call time from
  the run's held phases; a held trace that no
  longer agrees with it stands stale, named in
  the board - the trace is the walk itself,
  never a retelling of it.
* The juggernaut index is DERIVED at call time
  from the held runs - one entry per sound run,
  under the phase it stands at - never a second
  stored copy that could drift. A stored index,
  soundness verdict, panel, trace, order or
  current-run claim on any record refuses by
  name.
* The current run is DERIVED at call time - the
  first held run, in held order, that does not
  yet stand sound - never stored where it could
  go stale: that is where the loop must look
  next.
* The notes are held as data: a note record
  naming its run, its stance - note, concern,
  praise, question, a closed vocabulary - and
  what it feeds back toward, one record per run
  stance; holding a note posts none of it, the
  rule stands as data (:data:`JUGGERNAUT_RULE`),
  and a record claiming a loop was actually
  run live, a slice actually built, banked or
  pushed refuses BY NAME.
* The shipped data file holds one example book
  in exactly the shape a real juggernaut file
  takes, a loader reads a juggernaut file
  anywhere on disk, runs and views are shaped
  as session news, and a small in-memory
  registry holds records one by one. The agent
  layer owns holding a juggernaut book for a
  session and telling from it. This layer
  reaches no live road: it runs no loop, builds
  no slice, executes nothing, banks nothing,
  pushes nothing and opens no network - it
  holds loop runs as data and tells them.

Honesty rules, enforced here and pinned by tests:

* **The state machine is explicit.** A run is
  judged against the held phases and legal
  steps alone; an illegal step stands named in
  its gaps, never silently reordered.
* **The code answers its own questions.** A run
  that asked a file, framework, table or
  function question stands unsound, named in
  its gaps; the human is asked only meaning,
  behaviour, values and direction.
* **Active slices only.** A run for a missing
  or queued slice refuses by name; no run is
  invented for a slice the loop is not on.
* **Unknown stays unknown.** A run whose phases
  are not yet held stands with its phases
  empty - no phase is invented.
* **The index, panel, verdict, trace, order
  and current run are derived, never stored.**
  Each is derived from the held runs at call
  time; a stored one refuses by name, so it
  can never drift.
* **One run per run.** Two runs standing for
  one run id refuse by name, and one note
  record stands per run stance.
* **The notes are data alone.** The records
  hold the feedback; holding, viewing or
  telling them runs nothing and posts nothing.
"""


from __future__ import annotations

__all__ = [
    "PHASE_FIELDS",
    "PHASES",
    "QUESTION_KINDS",
    "HUMAN_QUESTIONS",
    "CODE_QUESTIONS",
    "TRANSITIONS",
    "EXAMPLE_PHASE",
    "STANCES",
    "INDEX_ACTION",
    "JUGGERNAUT_RESOURCE",
    "JUGGERNAUT_SCHEMA",
    "JUGGERNAUT_SLICE",
    "JUGGERNAUT_RULE",
    "PLAIN_EXPLANATION",
    "THE_JUGGERNAUT_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "VIEW_FILTERS",
    "SOUND_WORDS",
    "SLICE_STATES",
    "Any",
    "Dict",
    "List",
    "Optional",
    "TraceRecord",
    "RunRecord",
    "IndexEntry",
    "SliceRef",
    "NoteRecord",
    "JuggernautBook",
    "JuggernautIndex",
    "JuggernautPanel",
    "JuggernautPanelRow",
    "JuggernautRegistry",
    "JuggernautVerdict",
    "JuggernautView",
    "TargetCount",
    "trace_for_run",
    "trace_record",
    "board_record",
    "book_record",
    "build_trace",
    "build_book",
    "build_run",
    "build_slice_ref",
    "build_note",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "current_run",
    "transition_breaks",
    "derive_index",
    "derive_panel",
    "derive_verdict",
    "run_for_phase",
    "run_order",
    "run_record",
    "first_note",
    "format_book",
    "format_run",
    "format_index",
    "format_note",
    "format_phase",
    "format_panel",
    "format_juggernaut_screen",
    "format_verdict",
    "format_view",
    "index_plain_words",
    "index_record",
    "slice_record",
    "load_juggernaut",
    "load_juggernaut_file",
    "normalize_slice_state",
    "normalize_phase",
    "normalize_question_kind",
    "legal_step",
    "next_phase",
    "normalize_stance",
    "normalize_view_filter",
    "note_for_run",
    "note_plain_words",
    "note_record",
    "panel_plain_words",
    "panel_record",
    "parse_juggernaut_args",
    "passing_runs",
    "plain_lines",
    "plain_words",
    "roadmap_record",
    "segment_of",
    "trace_of",
    "trace_current",
    "shown_runs",
    "validate_trace",
    "validate_book",
    "validate_run",
    "validate_slice_ref",
    "validate_note",
    "validate_panel",
    "validate_row",
    "validate_verdict",
    "validate_view",
    "verdict_plain_words",
    "verdict_record",
    "view_plain_words",
    "view_record",
    "run_gaps",
    "run_sound",
    "runs_for_slice",
]

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource

JUGGERNAUT_SCHEMA = "mythic.juggernaut_loop/1"
JUGGERNAUT_SLICE = "M-204"
THE_JUGGERNAUT_SLICE = JUGGERNAUT_SLICE
JUGGERNAUT_RESOURCE = "juggernaut_loop.yaml"
INDEX_ACTION = "index"
EXAMPLE_PHASE = "continue"
PHASE_FIELDS = ("phases", "questions")
SOUND_WORDS = ("sound", "unsound")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "sound", "unsound")
VERDICT_WORDS = ("open", "strained", "shut")
SLICE_STATES = ("active", "queued")
JUGGERNAUT_RULE = (
    "loop runs are held as data alone: each run "
    "walks the state machine - inspect, build, "
    "test, repair, continue - in the open, per "
    "slice, and asks the human only what the code "
    "cannot answer - meaning, behaviour, values, "
    "direction - never a file, framework, table "
    "or function question; holding, viewing and "
    "reading a run runs no loop, builds no slice, "
    "banks nothing and opens no network - a run "
    "is judged from its held phases and its held "
    "questions alone, never claimed live, and "
    "its state machine is explicit and visible")
PLAIN_EXPLANATION = (
    "The Juggernaut loop as runtime (M-204): "
    "inspect, build, test, repair, continue, per "
    "slice, without asking file or framework "
    "questions the code can answer; the loop's "
    "state machine is explicit and visible.")
USAGE = (
    "Usage: /juggernaut | /juggernaut run <run-id> | "
    "/juggernaut phase <phase> | /juggernaut slice <slice-id> | "
    "/juggernaut view <view-id> | /juggernaut note <note-id> | "
    "/juggernaut index | /juggernaut panel | /juggernaut verdict")

PHASES = ("inspect", "build", "test", "repair", "continue")
HUMAN_QUESTIONS = ("meaning", "behaviour", "values", "direction")
CODE_QUESTIONS = ("file", "framework", "table", "function")
QUESTION_KINDS = HUMAN_QUESTIONS + CODE_QUESTIONS
TRANSITIONS = {
    "inspect": ("build",),
    "build": ("test",),
    "test": ("repair", "continue"),
    "repair": ("build", "test"),
    "continue": (),
}


def legal_step(before: Any, after: Any) -> bool:
    """Whether the state machine allows one step, DERIVED.

    The machine stands as data in TRANSITIONS:
    inspect steps only to build, build only to
    test, test to repair on a failure or to
    continue on a pass, repair back to build or
    test for the rerun, and continue steps
    nowhere - it is where a run stands complete.
    A phase outside the machine allows nothing.
    """
    return after in TRANSITIONS.get(before, ())


def next_phase(phase: Any, failed: Any = False) -> Optional[str]:
    """The phase the loop takes next, DERIVED from the machine.

    Inspect leads to build and build to test;
    at test a failure steps to repair and a pass
    steps to continue; repair steps back to test
    for the rerun; continue is the end of the
    walk and steps nowhere. A phase outside the
    machine refuses by name.
    """
    checked = normalize_phase(phase)
    if checked == "inspect":
        return "build"
    if checked == "build":
        return "test"
    if checked == "test":
        return "repair" if failed else "continue"
    if checked == "repair":
        return "test"
    return None

_PROVENANCE = ("recorded_on", "actor", "source", "origin_session")
_RUN_KEYS = frozenset({
    "run_id", "seq", "slice_id", "title", "phases",
    "questions", "detail",
} | set(_PROVENANCE))
_SLICE_REF_KEYS = frozenset({
    "slice_id", "seq", "title", "state", "detail",
} | set(_PROVENANCE))
_TRACE_KEYS = frozenset({
    "trace_id", "seq", "run_id", "trace", "detail",
} | set(_PROVENANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_PROVENANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "run_id", "stance", "target", "title",
    "detail",
} | set(_PROVENANCE))
_DERIVED_KEYS = frozenset({
    "standing", "sound", "sounds", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "entries", "coverage", "covered", "uncovered",
    "current_run", "next_run", "progress", "board",
    "current", "order", "breaks", "active"})
_LIVE_KEYS = (
    "live_run", "runs_live", "live_loop",
    "runs_loop", "ran_loop", "runs_slice",
    "ran_slice", "builds_slice", "built_slice",
    "builds_live", "executes_slice", "executed_slice",
    "executes_live", "live_execution",
    "banks_slice", "banked_live", "banking_live",
    "pushes_slice", "pushed_live", "merges_live",
    "merged_live", "opens_network", "writes_file",
    "write_file", "sends_run", "sent_run",
    "posts_note", "posted_note", "traces_live",
    "traced_live")


# ---------------------------------------------------------------------
# Small judges, in the sibling trace.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_phases(value: Any) -> Tuple[str, ...]:
    """A run's walked phases, held as data.

    The phases stand as a list of phase names in
    walk order, each one a phase of the explicit
    state machine; a walk not yet held stands
    honestly empty - no phase is invented - and
    a name outside the machine refuses.
    """
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError("phases must be a list of state machine phases")
    return tuple(normalize_phase(v) for v in value)

def _check_questions(value: Any) -> Tuple[str, ...]:
    """A run's asked questions: question kinds named as data.

    Each question names one kind from the closed
    vocabulary - the human kinds the loop may ask
    and the code kinds it must never ask, both
    held honestly as data - and a kind outside
    the vocabulary refuses.
    """
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError("questions must be a list of question kinds")
    return tuple(normalize_question_kind(v) for v in value)

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
                f"{what} claims a live loop run or slice build "
                f"execution ({key!r} is named on it): "
                f"{JUGGERNAUT_RULE}")
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


def normalize_slice_state(value: Any) -> str:
    state = _clean_text(value, "an slice state").lower()
    if state not in SLICE_STATES:
        raise ValueError(
            f"slice state {state!r} is not one of the held "
            f"states: " + ", ".join(SLICE_STATES))
    return state


def normalize_view_filter(value: Any) -> str:
    view_filter = _clean_text(value, "a view filter").lower()
    if view_filter not in VIEW_FILTERS:
        raise ValueError(
            f"view filter {view_filter!r} is not one of the held "
            f"filters: " + ", ".join(VIEW_FILTERS))
    return view_filter


def normalize_phase(value: Any) -> str:
    phase = _clean_text(value, "a phase").lower()
    if phase not in PHASES:
        raise ValueError(
            f"phase {phase!r} is not one of the held "
            f"phases: " + ", ".join(PHASES))
    return phase


def normalize_question_kind(value: Any) -> str:
    kind = _clean_text(value, "a question kind").lower()
    if kind not in QUESTION_KINDS:
        raise ValueError(
            f"question kind {kind!r} is not one of the held "
            f"kinds: " + ", ".join(QUESTION_KINDS))
    return kind

# ---------------------------------------------------------------------
# The held run: one slice cut from an active slice.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class RunRecord:
    """One run slice, held as data.

    The run names the active slice it was
    runed from, by slice id, its title, its
    verifiable phases, held as data, and its
    questions, named by run id. The grain is
    derived, never stored: exactly one verifiable
    walk is judged against the machine. A run whose
    phases are not yet held stands with its
    phases empty: it stands unsound, named in
    its gaps, and no phase is invented for it.
    The run is local data alone - no live build
    stands behind it: holding it builds nothing.
    """

    run_id: str
    seq: int
    slice_id: str
    title: str
    phases: Tuple[str, ...] = ()
    questions: Tuple[str, ...] = ()
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "run_id", _clean_text(self.run_id, "a run id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "slice_id", _clean_text(self.slice_id, "an slice id"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a run title"))
        object.__setattr__(
            self, "phases", _check_phases(self.phases))
        object.__setattr__(
            self, "questions", _check_questions(self.questions))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a run detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.run_id

    @property
    def phase(self) -> str:
        """The phase the run stands at: its last walked phase."""
        return self.phases[-1] if self.phases else ""

    def to_record(self) -> Dict[str, Any]:
        record = {
            "run_id": self.run_id, "seq": self.seq,
            "slice_id": self.slice_id, "title": self.title,
            "phases": list(self.phases),
            "questions": list(self.questions),
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_run_ref(value: Any) -> RunRecord:
    if not isinstance(value, RunRecord):
        raise ValueError("a run must be a RunRecord")
    return value


def validate_run(run: Any) -> RunRecord:
    return _check_run_ref(run)


def build_run(record: Any = None, **kwargs: Any) -> RunRecord:
    """Build one held run from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, RunRecord):
        if kwargs:
            raise ValueError("a run stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a run must be a mapping or a RunRecord")
    _needed(data, _RUN_KEYS, "a run")
    return RunRecord(
        run_id=data.get("run_id"), seq=data.get("seq"),
        slice_id=data.get("slice_id"), title=data.get("title"),
        phases=data.get("phases"),
        questions=data.get("questions"),
        detail=data.get("detail"),
        **_provenance(data))


def _breaks_map(book: Any) -> Dict[str, Tuple[str, ...]]:
    """Map each run to the steps it took outside the machine.

    Derived from the held runs alone: a break is
    one consecutive pair of walked phases the
    explicit state machine does not allow, told
    in walk order as before, then after.
    """
    found: Dict[str, Tuple[str, ...]] = {}
    for run in book.runs:
        breaks = tuple(
            f"{before} > {after}"
            for before, after in zip(run.phases, run.phases[1:])
            if not legal_step(before, after))
        if breaks:
            found[run.run_id] = breaks
    return found

def run_gaps(run: Any, source: Any = None) -> Tuple[str, ...]:
    """The gaps that keep a run from standing sound.

    Judged from the run's own held fields alone -
    its walked phases against the explicit state
    machine, and its asked questions against the
    closed vocabulary: the loop opens at inspect,
    steps only where the machine allows, asks the
    human nothing the code can answer, and a run
    stands sound only when it has reached
    continue. The source names nothing further:
    no gap is borrowed from another run.
    """
    checked = _check_run_ref(run)
    gaps: List[str] = []
    if not checked.phases:
        gaps.append(
            "has passed through no phase: the loop has not started")
        return tuple(gaps)
    if checked.phases[0] != "inspect":
        gaps.append(
            f"opens at {checked.phases[0]}, not at inspect: "
            f"the loop opens by inspecting")
    for before, after in zip(checked.phases, checked.phases[1:]):
        if not legal_step(before, after):
            gaps.append(
                f"steps from {before} to {after}, which the "
                f"state machine does not allow")
    for kind in checked.questions:
        if kind in CODE_QUESTIONS:
            gaps.append(
                f"asked a {kind} question the code can answer")
    if checked.phases[-1] != "continue":
        gaps.append(
            f"has not reached continue: the loop stands "
            f"at {checked.phases[-1]}")
    return tuple(gaps)

def run_sound(run: Any, source: Any = None) -> bool:
    return not run_gaps(run, source)


def plain_lines(run: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the run's own fields."""
    checked = _check_run_ref(run)
    return (
        f"Run: {checked.title}",
        f"Slice: {checked.slice_id}",
        f"Phase: {checked.phase if checked.phase else 'none'}",
        f"Questions: "
        f"{', '.join(checked.questions) if checked.questions else 'none'}",
    )


def segment_of(run: Any, source: Any = None) -> str:
    checked = _check_run_ref(run)
    gaps = run_gaps(checked, source)
    return (
        f"{checked.run_id}: {checked.title} - slice: "
        f"'{checked.slice_id}' - phase: "
        f"'{checked.phase if checked.phase else 'none'}' - "
        f"phases: {len(checked.phases)} - questions: "
        f"'{', '.join(checked.questions) if checked.questions else 'none'}' - "
        f"detail: '{checked.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held slice reference: the active slice a book runs from.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class SliceRef:
    """One slice a juggernaut book runs from, held as a reference.

    The record names the slice, the title it
    opens and its standing - active or
    queued - held as data copied from the
    M-202 slice book's own telling. A run
    stands only from an active reference: the
    book refuses a run naming no held reference,
    and a run from an queued one, BY NAME.
    """

    slice_id: str
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
            self, "slice_id", _clean_text(self.slice_id, "an slice id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a title"))
        object.__setattr__(
            self, "state", normalize_slice_state(self.state))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "an slice detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.slice_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "slice_id": self.slice_id, "seq": self.seq,
            "title": self.title, "state": self.state,
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_slice_ref(value: Any) -> SliceRef:
    if not isinstance(value, SliceRef):
        raise ValueError("a slice reference must be an SliceRef")
    return value


def validate_slice_ref(ref: Any) -> SliceRef:
    return _check_slice_ref(ref)


def build_slice_ref(record: Any = None, **kwargs: Any) -> SliceRef:
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, SliceRef):
        if kwargs:
            raise ValueError(
                "a slice reference stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError(
            "a slice reference must be a mapping or an SliceRef")
    _needed(data, _SLICE_REF_KEYS, "a slice reference")
    return SliceRef(
        slice_id=data.get("slice_id"), seq=data.get("seq"),
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
    human active - the slice's run ids in
    derived question order, held exactly as
    active. The trace is of the set and its
    order, never of a step: when the derived
    trace moves, this record stands stale, named
    in the board, until a new trace is active.
    """

    trace_id: str
    seq: int
    run_id: str
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
            self, "run_id", _clean_text(self.run_id, "an slice id"))
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
            "run_id": self.run_id, "trace": self.trace,
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
        run_id=data.get("run_id"), trace=data.get("trace"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held stance: a note on a run, held as data beside the book.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class NoteRecord:
    """One run stance, held as data.

    The record names its run, its stance and
    what it feeds back toward, with its title and
    its detail. One record stands per run stance
    in a book. The record is data alone: holding
    it builds nothing and posts nothing, ever.
    """

    note_id: str
    seq: int
    run_id: str
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
            self, "run_id", _clean_text(self.run_id, "a run id"))
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
            "run_id": self.run_id, "stance": self.stance,
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
        run_id=data.get("run_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held view: which slices a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class JuggernautView:
    """A view over the book: every run, the sound, the rest."""

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


def _check_view_ref(value: Any) -> JuggernautView:
    if not isinstance(value, JuggernautView):
        raise ValueError("a view must be an JuggernautView")
    return value


def validate_view(view: Any) -> JuggernautView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> JuggernautView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, JuggernautView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or an JuggernautView")
    _needed(data, _VIEW_KEYS, "a view")
    return JuggernautView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class JuggernautPanelRow:
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


def _row_for_run(run: RunRecord,
                     source: Any = None) -> JuggernautPanelRow:
    return JuggernautPanelRow(
        item_id=run.run_id,
        standing="sound" if run_sound(run, source) else "unsound",
        label=run.title, segment=segment_of(run, source),
        recorded_on=run.recorded_on)


def _check_row_ref(value: Any) -> JuggernautPanelRow:
    if not isinstance(value, JuggernautPanelRow):
        raise ValueError("a panel row must be an JuggernautPanelRow")
    return value


def validate_row(row: Any, run: Any = None,
                 source: Any = None) -> JuggernautPanelRow:
    checked = _check_row_ref(row)
    if run is not None:
        derived = _row_for_run(_check_run_ref(run), source)
        if checked != derived:
            raise ValueError(
                f"panel row {checked.item_id!r} does not agree with "
                f"the row derived from its run")
    return checked


def build_row(row: Any = None, run: Any = None,
              source: Any = None,
              **kwargs: Any) -> JuggernautPanelRow:
    if run is not None:
        derived = _row_for_run(_check_run_ref(run), source)
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            JuggernautPanelRow(**kwargs))
        return validate_row(built, run, source)
    if isinstance(row, JuggernautPanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in SOUND_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return JuggernautPanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on day"))
    if row is None and kwargs:
        return JuggernautPanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or an JuggernautPanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[JuggernautPanelRow, ...]
                 ) -> Tuple[TargetCount, ...]:
    counts: List[TargetCount] = []
    for standing in SOUND_WORDS:
        number = sum(1 for row in rows if row.standing == standing)
        if number:
            counts.append(TargetCount(standing=standing, items=number))
    return tuple(counts)


def _panel_account(total_items: int, total_shown: int,
                   passing_shown: int,
                   target_counts: Tuple[TargetCount, ...],
                   view_filter: str, as_of: str) -> Tuple[str, ...]:
    standing_words = ", ".join(
        f"{count.standing} {count.items}"
        for count in target_counts) or "none"
    return (
        f"The juggernaut book holds {total_items} runs as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {passing_shown} of the shown runs "
        f"stand sound.",
        "Rows stand in held order, the order the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its run's own fields "
        "- the slice it runs, the phases it walked in the "
        "open and the questions it honestly carries - and no "
        "judgement is stored on any run.",
        "Soundness is judged from the held records alone: "
        "a run that steps outside the state machine, asks a "
        "question the code can answer, or has not reached "
        "continue stands unsound, named in its gaps, and the "
        "juggernaut index is derived from the held runs, "
        "never stored where it could drift.",
    )

@dataclass(frozen=True)
class JuggernautPanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[JuggernautPanelRow, ...]
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


def _resolve_view(source: Any, view: Any) -> JuggernautView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, JuggernautView):
        return view
    return book.view_for(view)


def shown_runs(source: Any, view: Any = None
                   ) -> Tuple[RunRecord, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.runs
    if resolved.view_filter == "sound":
        return tuple(g for g in book.runs if run_sound(g, book))
    return tuple(g for g in book.runs if not run_sound(g, book))


def runs_for_slice(source: Any, slice_id: Any
                      ) -> Tuple[RunRecord, ...]:
    wanted = _clean_text(slice_id, "an slice id")
    return tuple(
        g for g in _source_book(source).runs if g.slice_id == wanted)


def passing_runs(source: Any) -> Tuple[RunRecord, ...]:
    book = _source_book(source)
    return tuple(g for g in book.runs if run_sound(g, book))


def current_run(source: Any) -> Optional[RunRecord]:
    """The book's current run, DERIVED at call time.

    The first held run, in held order, that does
    not yet stand sound - where the Architect must
    look next. Nothing here is stored: the telling
    is derived from the held runs alone, so it can
    never go stale against them. A book whose every
    run stands sound has no current run.
    """
    book = _source_book(source)
    for run in book.runs:
        if not run_sound(run, book):
            return run
    return None


def derive_panel(source: Any, view: Any = None) -> JuggernautPanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_runs(book, resolved)
    rows = tuple(_row_for_run(run, book) for run in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.runs), default="")
    passing = sum(1 for g in shown if run_sound(g, book))
    return JuggernautPanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.runs), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.runs), len(shown), passing, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> JuggernautPanel:
    if not isinstance(value, JuggernautPanel):
        raise ValueError("a panel must be an JuggernautPanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> JuggernautPanel:
    """Judge a stored panel against the panel derived from its book.

    Every derived field must agree; the stored
    panel's own name is its identity, not derived
    content (the M-182 lesson).
    """
    checked = _check_panel_ref(panel)
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(checked.view_id)
                if checked.view_id is not None else None)
        derived = derive_panel(book, view)
        for attr in ("view_id", "view_filter", "rows", "total_items",
                     "total_shown", "target_counts", "as_of", "account"):
            if getattr(checked, attr) != getattr(derived, attr):
                raise ValueError(
                    f"panel {checked.panel_id!r} disagrees with the "
                    f"panel derived from its book on {attr}")
    return checked


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> JuggernautPanel:
    if isinstance(panel, JuggernautPanel):
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
        built = JuggernautPanel(
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
    raise ValueError("a panel must be a mapping, an JuggernautPanel, or derived")


def _check_lines(value: Any, what: str) -> Tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError(f"{what} must be a list of lines")
    lines = []
    for line in value:
        lines.append(_clean_text(line, f"a line of {what}"))
    return tuple(lines)


def _verdict_word(total_shown: int, passing_shown: int) -> str:
    if total_shown > 0 and passing_shown == total_shown:
        return "open"
    if passing_shown == 0:
        return "shut"
    return "strained"


@dataclass(frozen=True)
class JuggernautVerdict:
    verdict: str
    view_id: Optional[str]
    total_shown: int
    passing_shown: int
    latest_on: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict, "view_id": self.view_id,
            "total_shown": self.total_shown,
            "passing_shown": self.passing_shown,
            "latest_on": self.latest_on,
        }


def derive_verdict(source: Any, view: Any = None) -> JuggernautVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_runs(book, resolved)
    passing = sum(1 for g in shown if run_sound(g, book))
    latest = max((g.recorded_on for g in shown), default="")
    return JuggernautVerdict(
        verdict=_verdict_word(len(shown), passing),
        view_id=resolved.view_id, total_shown=len(shown),
        passing_shown=passing, latest_on=latest)


def _check_verdict_ref(value: Any) -> JuggernautVerdict:
    if not isinstance(value, JuggernautVerdict):
        raise ValueError("a verdict must be an JuggernautVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> JuggernautVerdict:
    checked = _check_verdict_ref(verdict)
    if checked.verdict not in VERDICT_WORDS:
        raise ValueError(f"verdict {checked.verdict!r} is not a held word")
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(checked.view_id)
                if checked.view_id is not None else None)
        derived = derive_verdict(book, view)
        if checked != derived:
            raise ValueError(
                "the stored verdict disagrees with the verdict "
                "derived from its book")
    return checked


def build_verdict(verdict: Any = None, source: Any = None,
                  **kwargs: Any) -> JuggernautVerdict:
    if isinstance(verdict, JuggernautVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = JuggernautVerdict(
            verdict=_clean_text(data.get("verdict"), "a verdict"),
            view_id=data.get("view_id"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            passing_shown=_check_count(
                data.get("passing_shown"), "a passing_shown count"),
            latest_on=_clean_text(data.get("latest_on"), "a latest day"))
        return validate_verdict(built, source)
    if verdict is None and source is not None:
        return derive_verdict(source, kwargs.get("view"))
    raise ValueError(
        "a verdict must be a mapping, an JuggernautVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held slices' citations at call time.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexEntry:
    phase: str
    run_id: str
    title: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "phase": self.phase, "run_id": self.run_id,
            "title": self.title,
        }


@dataclass(frozen=True)
class JuggernautIndex:
    """The juggernaut index, derived from the held runs.

    The index names one entry per sound run, in
    held order - the run's own one verifiable
    phase, its run id and its title - and the
    runs that do not stand sound, named in its
    gaps. Nothing here is stored on any run: the
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


def derive_index(source: Any) -> JuggernautIndex:
    """Derive the juggernaut index from the book's held runs."""
    book = _source_book(source)
    entries = tuple(
        IndexEntry(phase=g.phase, run_id=g.run_id,
                   title=g.title)
        for g in book.runs if run_sound(g, book))
    gaps = tuple(
        g.run_id for g in book.runs if not run_sound(g, book))
    return JuggernautIndex(entries=entries, gaps=gaps)


def run_for_phase(source: Any, phase: Any) -> Optional[RunRecord]:
    """The first held run one phase reaches, or none - honestly."""
    if phase is None:
        return None
    if not isinstance(phase, str):
        raise ValueError("an phase must be a string naming the phase")
    wanted = phase.strip()
    if not wanted:
        return None
    for run in _source_book(source).runs:
        if run.phase == wanted:
            return run
    return None


def transition_breaks(source: Any) -> Tuple[str, ...]:
    """Every step outside the state machine, DERIVED.

    One telling per break, in held order: the run
    that took it and the step it took, before,
    then after. A book whose runs all walk inside
    the machine tells none.
    """
    book = _source_book(source)
    return tuple(
        f"{run_id}: {step}"
        for run_id, steps in _breaks_map(book).items()
        for step in steps)

def run_order(source: Any,
              slice_id: Any = None) -> Tuple[RunRecord, ...]:
    """The held runs in their held order, DERIVED at call time.

    Runs stand in the order the book holds them -
    the order their slices were taken - optionally
    for one slice alone. Nothing here is stored:
    the order is the book's own held order, told.
    """
    book = _source_book(source)
    runs = list(book.runs)
    if slice_id is not None:
        wanted = _clean_text(slice_id, "a slice id")
        runs = [r for r in runs if r.slice_id == wanted]
    return tuple(runs)

def trace_of(source: Any, run_id: Any) -> str:
    """One run's trace, DERIVED at call time.

    The run's walked phases joined as one trace
    line, in walk order. A run that has walked
    nowhere traces empty: the trace tells only
    what stands walked, and the walk is named
    elsewhere.
    """
    run = _source_book(source).run_for(run_id)
    return " > ".join(run.phases)

def trace_for_run(source: Any,
                  run_id: Any) -> Optional[TraceRecord]:
    """The held trace for one run, or none - honestly."""
    wanted = _clean_text(run_id, "a run id")
    for record in _source_book(source).traces:
        if record.run_id == wanted:
            return record
    return None

def trace_current(source: Any, run_id: Any) -> bool:
    """Whether the held trace agrees with the derived trace.

    The trace stands current only while the trace
    it holds is the trace the book derives now; a
    moved walk leaves it stale, and no trace at
    all traces nothing.
    """
    trace = trace_for_run(source, run_id)
    if trace is None:
        return False
    return trace.trace == trace_of(source, run_id)

def note_for_run(source: Any, run_id: Any,
                   stance: Any = None) -> Optional[NoteRecord]:
    """The held stance target for one run (and stance, when named)."""
    wanted = _clean_text(run_id, "a run id")
    for record in _source_book(source).notes:
        if record.run_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_note(source: Any) -> Optional[NoteRecord]:
    """The first held stance target, standing for the slice targets, or none."""
    notes = _source_book(source).notes
    return notes[0] if notes else None


def board_record(source: Any = None) -> Dict[str, Any]:
    """The juggernaut board, DERIVED here from the held runs alone.

    The board counts the held runs by their
    derived soundness - sound and unsound - names
    the current run, the first that does not yet
    stand sound, tells each held run's trace
    standing - current while its held trace
    agrees with its derived trace, stale when it
    has moved, unheld while no trace stands for
    it - and names every step the held runs took
    outside the state machine. Nothing here is
    stored: the telling is derived at call time.
    """
    book = _source_book(source)
    standings = []
    for standing in SOUND_WORDS:
        number = sum(
            1 for g in book.runs
            if ("sound" if run_sound(g, book) else "unsound") == standing)
        standings.append({"standing": standing, "runs": number})
    current = current_run(book)
    traces = []
    for run in book.runs:
        trace = trace_for_run(book, run.run_id)
        if trace is None:
            standing = "unheld"
        elif trace_current(book, run.run_id):
            standing = "current"
        else:
            standing = "stale"
        traces.append({"run_id": run.run_id, "trace": standing})
    return {
        "type": "juggernaut_board",
        "slice": JUGGERNAUT_SLICE,
        "standings": standings,
        "total": len(book.runs),
        "current_run": current.run_id if current is not None else None,
        "traces": traces,
        "breaks": list(transition_breaks(book)),
    }

def roadmap_record() -> Dict[str, Any]:
    """This slice's own roadmap standing, proved from the roadmap itself.

    The record loads this repo's own roadmap through
    the shipped M-017 layer for real and tells its
    counts as they stand: 272 slices in 11 parts,
    the banked prefix, the next slice where the
    campaign resumes, and M-204's own ledger
    standing in Part IX.
    """
    from .roadmap_slices import load_roadmap
    roadmap = load_roadmap()
    own = roadmap.slice(JUGGERNAUT_SLICE)
    next_slice = roadmap.next_slice()
    return {
        "type": "juggernaut_roadmap",
        "slice": JUGGERNAUT_SLICE,
        "roadmap_file": "roadmap_slices.yaml",
        "roadmap": roadmap.roadmap,
        "parts": len(roadmap.parts),
        "slices": len(roadmap.slices),
        "done": len(roadmap.done()),
        "next_slice": next_slice.id if next_slice is not None else None,
        "m204_title": own.title,
        "m204_part": own.part,
        "m204_status": own.status,
    }


# ---------------------------------------------------------------------
# The book: slices, runs, views, notes and trace traces held
# together, one pinned panel at most per telling, and no verdict,
# index, trace or order ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class JuggernautBook:
    title: str
    slices: Tuple[SliceRef, ...] = ()
    runs: Tuple[RunRecord, ...] = ()
    views: Tuple[JuggernautView, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    traces: Tuple[TraceRecord, ...] = ()
    panels: Tuple[JuggernautPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        slices = tuple(_check_slice_ref(g) for g in self.slices)
        runs = tuple(_check_run_ref(g) for g in self.runs)
        views = tuple(_check_view_ref(v) for v in self.views)
        notes = tuple(_check_note_ref(m) for m in self.notes)
        traces = tuple(_check_trace_ref(a) for a in self.traces)
        panels = tuple(_check_panel_ref(pn) for pn in self.panels)
        seen_ids = set()
        seen_seqs = set()
        for ref in slices:
            if ref.slice_id in seen_ids:
                raise ValueError(
                    f"two slice references stand under id {ref.slice_id!r}")
            if ref.seq in seen_seqs:
                raise ValueError(
                    f"two slice references stand at sequence {ref.seq}")
            seen_ids.add(ref.slice_id)
            seen_seqs.add(ref.seq)
        run_ids = set()
        run_seqs = set()
        for run in runs:
            if run.run_id in run_ids:
                raise ValueError(
                    f"two runs stand under id {run.run_id!r}")
            if run.seq in run_seqs:
                raise ValueError(
                    f"two runs stand at sequence {run.seq}")
            run_ids.add(run.run_id)
            run_seqs.add(run.seq)
        by_slice = {ref.slice_id: ref for ref in slices}
        for run in (runs if slices else ()):

            ref = by_slice.get(run.slice_id)
            if ref is None:
                raise ValueError(
                    f"run {run.run_id!r} is runed from slice "
                    f"{run.slice_id!r}, which stands nowhere in "
                    f"this book")
            if ref.state != "active":
                raise ValueError(
                    f"run {run.run_id!r} is runed from slice "
                    f"{run.slice_id!r}, which is not active: "
                    f"no slice is runed from an queued slice")
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
            target = (record.run_id, record.stance)
            if target in note_targets:
                raise ValueError(
                    f"two stance records stand for run "
                    f"{record.run_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per run target")
            note_ids.add(record.note_id)
            note_seqs.add(record.seq)
            note_targets.add(target)
        trace_ids = set()
        trace_seqs = set()
        trace_runs = set()
        run_ids = {run.run_id for run in runs}
        for record in traces:
            if record.trace_id in trace_ids:
                raise ValueError(
                    f"two traces stand under id {record.trace_id!r}")
            if record.seq in trace_seqs:
                raise ValueError(
                    f"two traces stand at sequence {record.seq}")
            if record.run_id in trace_runs:
                raise ValueError(
                    f"two traces stand for run "
                    f"{record.run_id!r}: one trace stands "
                    f"per run walk")
            if runs and record.run_id not in run_ids:
                raise ValueError(
                    f"trace {record.trace_id!r} traces run "
                    f"{record.run_id!r}, which stands nowhere in "
                    f"this book")
            trace_ids.add(record.trace_id)
            trace_seqs.add(record.seq)
            trace_runs.add(record.run_id)
        object.__setattr__(
            self, "slices", tuple(sorted(slices, key=lambda g: g.seq)))
        object.__setattr__(
            self, "runs", tuple(sorted(runs, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "notes", tuple(sorted(notes, key=lambda m: m.seq)))
        object.__setattr__(
            self, "traces",
            tuple(sorted(traces, key=lambda a: a.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.runs + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.run_id for g in self.runs) + tuple(
            v.view_id for v in self.views)

    def run_ids(self) -> Tuple[str, ...]:
        return tuple(g.run_id for g in self.runs)

    def slice_ids(self) -> Tuple[str, ...]:
        return tuple(g.slice_id for g in self.slices)

    def run_for(self, run_id: Any) -> RunRecord:
        wanted = _clean_text(run_id, "a run id")
        for run in self.runs:
            if run.run_id == wanted:
                return run
        raise KeyError(f"no run named {wanted!r} stands in this book")

    def slice_for(self, slice_id: Any) -> SliceRef:
        wanted = _clean_text(slice_id, "an slice id")
        for ref in self.slices:
            if ref.slice_id == wanted:
                return ref
        raise KeyError(f"no slice named {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> JuggernautView:
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
        for run in self.runs:
            if run.run_id == wanted:
                return run
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "slices": [g.to_record() for g in self.slices],
            "runs": [g.to_record() for g in self.runs],
            "views": [v.to_record() for v in self.views],
            "notes": [m.to_record() for m in self.notes],
            "traces": [a.to_record() for a in self.traces],
            "panels": [pn.to_record() for pn in self.panels],
        }


def _judge_book_panels(book: JuggernautBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: JuggernautBook) -> None:
    if book.title != "The Juggernaut loop at the M-203 slice boundary":
        raise ValueError("the shipped example book carries another title")
    if len(book.slices) != 3 or len(book.runs) != 5 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold three slice references, five runs and two views")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.traces) != 1:
        raise ValueError("the shipped example book must hold one trace record")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-m203-boundary":
        raise ValueError("the pinned panel is panel-m203-boundary")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "strained" or verdict.passing_shown != 3:
        raise ValueError("the shipped example book verdict must stand strained at three sound of five")
    index = derive_index(book)
    if [e.phase for e in index.entries] != ["continue", "continue", "continue"]:
        raise ValueError("the shipped example book index must derive the three held sound runs in held order")
    if index.gaps != ("run-asking-loop", "run-skipping-loop"):
        raise ValueError("the shipped example book must leave the asking and skipping runs honestly unsound, named in its gaps")
    found = run_for_phase(book, EXAMPLE_PHASE)
    if found is None or found.run_id != "run-slicing-loop":
        raise ValueError("the shipped example book must reach its opening run under the example phase")
    if trace_of(book, "run-slicing-loop") != "inspect > build > test > continue":
        raise ValueError("the shipped example book must derive the opening run's trace from its walked phases")
    if not trace_current(book, "run-slicing-loop"):
        raise ValueError("the shipped example book must hold the opening run's trace current")
    first = first_note(book)
    if first is None or first.note_id != "note-note-open":
        raise ValueError("the shipped example book must hold the opening note as its first note road")

def validate_book(data: Any, *, require_example: bool = False) -> JuggernautBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, JuggernautBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a juggernaut book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live slice build or execution "
                f"({key!r} is named on it): {JUGGERNAUT_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its runs under a view")
    if "juggernaut_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held runs at call time")
    if "board" in data or "current_run" in data:
        raise ValueError(
            "a book stores no board and no current run: both are "
            "derived from its held runs at call time")
    if "trace" in data or "order" in data:
        raise ValueError(
            "a book stores no trace and no order: both are derived "
            "from its held runs at call time; an trace record "
            "holds the trace the human active")
    if data.get("schema") is not None and (
            data["schema"] != JUGGERNAUT_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{JUGGERNAUT_SCHEMA!r}")
    if data.get("slice") is not None and (
            data["slice"] != JUGGERNAUT_SLICE):
        raise ValueError(
            f"a book's slice must be {JUGGERNAUT_SLICE!r}")
    head = data.get("juggernaut_head") or data.get("juggernaut_loop") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's juggernaut head must be a mapping")
    title = head.get("title") or data.get("title")
    slices = tuple(build_slice_ref(g) for g in data.get("slices") or ())
    runs = tuple(build_run(g) for g in data.get("runs") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    traces = tuple(build_trace(a) for a in data.get("traces") or ())
    book = JuggernautBook(
        title=title, slices=slices, runs=runs, views=views,
        notes=notes, traces=traces, panels=())
    panels = tuple(
        build_panel(pn, book) for pn in data.get("panels") or ())
    book = JuggernautBook(
        title=book.title, slices=book.slices, runs=book.runs,
        views=book.views, notes=book.notes,
        traces=book.traces, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> JuggernautBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (JuggernautBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or an JuggernautBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> JuggernautBook:
    return validate_book(data, require_example=require_example)


def load_juggernaut(
        data: Optional[Dict[str, Any]] = None) -> JuggernautBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(JUGGERNAUT_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_juggernaut_file(path: Any) -> JuggernautBook:
    """Load one juggernaut file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: slice references, runs and views held one by one.
# ---------------------------------------------------------------------

class JuggernautRegistry:
    """An in-memory holding of slice references, runs and views.

    The registry is the pure layer's model of a
    session's juggernaut book: slice references are
    held under their ids, runs are held under
    their ids, one run per id and per sequence,
    and views are held in recorded order, one view
    per sequence and per id. Holding is data only -
    nothing held here builds anything, executes
    anything, or opens a network.
    """

    def __init__(self, book: Any = None) -> None:
        self._slices: List[SliceRef] = []
        self._runs: List[RunRecord] = []
        self._views: List[JuggernautView] = []
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

    def register_slice_ref(self, item: Any) -> SliceRef:
        """Hold one slice reference, judged whole before held."""
        checked = _check_slice_ref(item)
        return self._register(
            self._slices, checked, "slice_id", "slice reference")

    def register_run(self, item: Any) -> RunRecord:
        """Hold one run, judged whole before held."""
        checked = _check_run_ref(item)
        return self._register(
            self._runs, checked, "run_id", "run")

    def register_view(self, view: Any) -> JuggernautView:
        """Hold one view; a view naming no id takes a fresh one."""
        checked = _check_view_ref(view)
        if not checked.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            checked = build_view({**checked.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, checked, "view_id", "view")

    def register_book(self, book: Any) -> JuggernautBook:
        """Hold a whole book's records, under its title."""
        checked = build_book(book)
        if self._title is not None and checked.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {checked.title!r}")
        for ref in checked.slices:
            self.register_slice_ref(ref)
        for run in checked.runs:
            self.register_run(run)
        for view in checked.views:
            self.register_view(view)
        self._title = checked.title
        return self.book()

    def book(self) -> JuggernautBook:
        return JuggernautBook(
            title=self._title or "An unheld juggernaut book",
            slices=tuple(self._slices), runs=tuple(self._runs),
            views=tuple(self._views), notes=(), traces=(), panels=())

    def list_slices(self) -> Tuple[SliceRef, ...]:
        return tuple(self._slices)

    def list_runs(self) -> Tuple[RunRecord, ...]:
        return tuple(self._runs)

    def list_views(self) -> Tuple[JuggernautView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._runs) + tuple(self._views)

    def get_slice(self, slice_id: Any) -> SliceRef:
        return self.book().slice_for(slice_id)

    def get_run(self, run_id: Any) -> RunRecord:
        return self.book().run_for(run_id)

    def get_view(self, view_id: Any) -> JuggernautView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records traced for the journal target.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> JuggernautBook:
    if source is None:
        return load_juggernaut()
    if isinstance(source, JuggernautBook):
        return source
    if isinstance(source, JuggernautRegistry):
        return source.book()
    return build_book(source)


def _provenance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _PROVENANCE}


def run_record(run: Any, source: Any = None) -> Dict[str, Any]:
    checked = _check_run_ref(run)
    book = _source_book(source) if source is not None else None
    record = {
        "type": "juggernaut_run",
        "slice": JUGGERNAUT_SLICE,
        "run_id": checked.run_id,
        "slice_id": checked.slice_id,
        "title": checked.title,
        "segment": segment_of(checked, book),
        "sound": run_sound(checked, book),
        "gaps": list(run_gaps(checked, book)),
    }
    record.update(_provenance_record(checked))
    return record


def slice_record(ref: Any) -> Dict[str, Any]:
    checked = _check_slice_ref(ref)
    record = {
        "type": "juggernaut_slice",
        "slice": JUGGERNAUT_SLICE,
        "slice_id": checked.slice_id,
        "title": checked.title,
        "state": checked.state,
    }
    record.update(_provenance_record(checked))
    return record


def trace_record(record_in: Any) -> Dict[str, Any]:
    checked = _check_trace_ref(record_in)
    record = {
        "type": "juggernaut_trace",
        "slice": JUGGERNAUT_SLICE,
        "trace_id": checked.trace_id,
        "run_id": checked.run_id,
        "trace": checked.trace,
    }
    record.update(_provenance_record(checked))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    checked = _check_view_ref(view)
    record = {
        "type": "juggernaut_view",
        "slice": JUGGERNAUT_SLICE,
        "view_id": checked.view_id, "seq": checked.seq,
        "view_filter": checked.view_filter,
    }
    record.update(_provenance_record(checked))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    checked = _check_note_ref(record_in)
    record = {
        "type": "juggernaut_note",
        "slice": JUGGERNAUT_SLICE,
        "note_id": checked.note_id,
        "run_id": checked.run_id,
        "stance": checked.stance,
    }
    record.update(_provenance_record(checked))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    checked = validate_panel(panel, source)
    record = {"type": "juggernaut_panel",
              "slice": JUGGERNAUT_SLICE}
    record.update(checked.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, JuggernautVerdict):
        checked = validate_verdict(verdict, source)
    else:
        checked = derive_verdict(_source_book(verdict), view)
    record = {"type": "juggernaut_verdict",
              "slice": JUGGERNAUT_SLICE}
    record.update(checked.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, JuggernautIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "juggernaut_index",
              "slice": JUGGERNAUT_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    checked = _source_book(book)
    record = {"type": "juggernaut_book",
              "slice": JUGGERNAUT_SLICE,
              "title": checked.title}
    record.update(checked.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(run: Any, source: Any = None) -> str:
    checked = _check_run_ref(run)
    return (
        f"{checked.title} - from {checked.slice_id}: "
        f"phase {checked.phase if checked.phase else 'none'}, "
        f"questions "
        f"{', '.join(checked.questions) if checked.questions else 'none'}. "
        f"{checked.detail}")


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The runs stand {verdict.verdict}: "
        f"{verdict.passing_shown} of {verdict.total_shown} shown "
        f"runs stand sound.")


def view_plain_words(view: Any) -> str:
    checked = _check_view_ref(view)
    return f"View {checked.view_id}: shows {checked.view_filter} runs."


def note_plain_words(record_in: Any) -> str:
    checked = _check_note_ref(record_in)
    return (
        f"Note {checked.note_id}: {checked.stance} "
        f"{checked.run_id}, toward {checked.target}. "
        f"{checked.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, JuggernautIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.entries)} sound runs; "
        f"unsound, named in its gaps: {gaps}.")

def format_run(run: Any, source: Any = None) -> str:
    checked = _check_run_ref(run)
    book = _source_book(source) if source is not None else None
    lines = [f"{checked.title} ({checked.run_id})"]
    lines.extend(plain_lines(checked))
    lines.append(checked.detail)
    if run_sound(checked, book):
        lines.append(
            "This run stands sound - it walked the state "
            "machine in the open from inspect to continue, "
            "and it asked the human nothing the code can "
            "answer.")
    else:
        lines.append(
            "This run stands unsound - it stands named in "
            f"its gaps: {', '.join(run_gaps(checked, book))}, and "
            "nothing is invented for it.")
    return "\n".join(lines)

def format_view(view: Any) -> str:
    checked = _check_view_ref(view)
    return (
        f"View {checked.view_id}: filter {checked.view_filter} - "
        f"{checked.detail}")


def format_note(record_in: Any) -> str:
    checked = _check_note_ref(record_in)
    lines = [
        f"Juggernaut note {checked.stance} {checked.run_id} "
        f"({checked.note_id}): {checked.title}. {checked.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or reading it builds nothing, executes nothing "
        "and posts no note.")
    return "\n".join(lines)


def format_phase(source: Any, phase: Any) -> str:
    run = run_for_phase(source, phase)
    if run is not None:
        return format_run(run, source)
    wanted = phase.strip() if isinstance(phase, str) else phase
    return (
        f"No held run stands under phase {wanted!r} yet - the "
        f"phase reaches nothing in this book, and no run is "
        f"invented for it.")


def format_book(source: Any = None, slice_id: Any = None) -> str:
    book = _source_book(source)
    runs = (runs_for_slice(book, slice_id)
              if slice_id is not None else book.runs)
    lines = [f"The Juggernaut Loop (M-204) - {book.title}"]
    lines.extend(segment_of(run, book) for run in runs)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Juggernaut panel under view {panel.view_id}:"]
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
    lines = ["Juggernaut index, derived from the held runs:"]
    for entry in index.entries:
        lines.append(f"{entry.phase} - {entry.title} ({entry.run_id})")
    if index.gaps:
        lines.append(
            "Unsound, named honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "builds nothing, executes nothing and opens no network.")
    return "\n".join(lines)


def format_juggernaut_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "The Juggernaut Loop (M-204)",
        f"{book.title}: {len(book.runs)} runs held, "
        f"{len(passing_runs(book))} runs standing sound, "
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


def parse_juggernaut_args(args: Any) -> Tuple[str, Any]:
    """Parse the /juggernaut grammar into (stance, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("run", "view", "note"):
        if len(parts) != 2:
            raise ValueError(USAGE)
        return (head, parts[1])
    if head in ("phase", "slice"):
        if len(parts) < 2:
            raise ValueError(USAGE)
        return (head, " ".join(parts[1:]))
    if head in ("index", "panel", "verdict") and len(parts) == 1:
        return (head, None)
    raise ValueError(USAGE)
