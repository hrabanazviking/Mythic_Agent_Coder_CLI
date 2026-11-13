"""Crew replay (All-Features roadmap slice M-138).

Part VI continues here. The roadmap's words:
``a crew run's hand-offs replayable from the
journal - how a decision happened is auditable.``

What already shipped, and what this slice adds:

* The traffic of a run is already data
  (``core/crew_comms.py``, M-126): a hand-off is
  a sender member, a recipient member - or the
  human - a kind, the slice it belongs to, a
  title and a body, validated by that layer
  itself. The members are the shipped crew
  (``core/crew_members.py``, M-121). And a run's
  checkpoints are already journaled by the
  session layer as they happen. What nothing
  holds is the reading-back: the hand-offs of
  one finished run, in journal order, as one
  replay a reader can walk - and, for any
  decision in the run, the trace of the
  hand-offs that led to it.
* This slice is that reading-back, as a pure
  layer: a replay book validated as data - one
  journal step per hand-off of the run (the
  hand-off itself, composed by import from
  ``core/crew_comms.py`` - validate_handoff /
  Handoff, never re-implemented - and its
  journal position), under a title, plus
  decision traces whose account is DERIVED
  from the steps that led to the decision -
  the shipped data file
  (``mythic_agent/data/crew_replay.yaml``)
  holding one example replay book in exactly
  the shape a real replay file takes, a loader
  for a replay file anywhere on disk, records
  shaped as session news, and a small in-memory
  registry model. This module reads no live
  journal, re-runs nothing, spawns nothing,
  calls no model, persists nothing and imports
  no agent / UI code; the agent layer owns
  holding a replay for a session.

Honesty rules, enforced here and pinned by tests:

* **The replay is derived from the journal, in
  order, never stored loose.** A book's steps
  stand at journal positions 1..N in the order
  held: a step naming a position other than
  its place in the book refuses, exactly as a
  stored stand-up digest that disagrees with
  its entries does. There is no second,
  re-ordered copy of a run to drift from the
  journal.
* **A decision trace is derived, never stored
  loose.** A trace's account is read off the
  steps that led to its decision - every
  hand-off of the decision's slice, in journal
  order, up to and including the decision
  itself - so a stored trace whose steps,
  member, slice or account disagree with the
  derived trace refuses, exactly as a stored
  M-137 check does. A trace naming no account
  of its own and judged against no steps
  refuses for the same reason.
* **Hand-offs are the comms layer's own.** A
  step's hand-off is read by
  ``core/crew_comms.py`` itself, so the sender,
  recipient, kind, slice, title and body a
  replay walks answer to exactly the
  validators a live hand-off answers to - a
  sender naming the human, an unknown kind and
  unknown hand-off keys all refuse through
  that layer. Member ids read exactly as the
  M-121 layer reads them, composed by import.
* **Data only - no live road is claimed.** A
  replay here is a validated record of a
  finished run's hand-offs, held as data: it
  reads no running crew's journal, re-executes
  no step, delivers no message and claims no
  run is live. The roadmap names the board
  (Part VIII) as where crew state will be
  visible; that board does not exist yet, so
  the replay is visible through this slice's
  own /replay screen, and nothing here claims
  a board exists.
* **Malformed refuses.** A position that is
  not the step's place in the book, a duplicate
  step id or trace id anywhere in the book, a
  trace naming a step the book holds no step
  for, and unknown keys in a step, a trace or
  a replay mapping all raise instead of being
  skipped or guessed at.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..resources import load_resource
from .crew_comms import Handoff, build_handoff, validate_handoff
from .crew_members import normalize_member_id
from .validation import ValidationError
from .worktrees import normalize_slice_id

__all__ = [
    "CREW_REPLAY_RESOURCE",
    "CREW_REPLAY_SCHEMA",
    "CREW_REPLAY_SLICE",
    "PLAIN_EXPLANATION",
    "USAGE",
    "DecisionTrace",
    "ReplayBook",
    "ReplayRegistry",
    "ReplayStep",
    "book_record",
    "build_book",
    "build_step",
    "build_trace",
    "derive_trace",
    "format_replay_screen",
    "format_step",
    "format_steps",
    "format_trace",
    "load_crew_replay",
    "load_crew_replay_file",
    "parse_replay_args",
    "plain_words",
    "step_record",
    "trace_plain_words",
    "trace_record",
    "validate_book",
    "validate_step",
    "validate_trace",
]

CREW_REPLAY_SLICE = "M-138"

#: The packaged data resource holding the example replay book.
CREW_REPLAY_RESOURCE = "crew_replay.yaml"

#: The schema word a replay file must carry.
CREW_REPLAY_SCHEMA = "mythic.crew_replay/1"

_STEP_KEYS = frozenset({
    "step_id", "id", "position", "seq", "journal_position",
    "handoff", "hand_off", "entry",
})

_TRACE_KEYS = frozenset({
    "trace_id", "id", "decision_step", "step_id", "step",
    "member", "decider", "slice", "slice_id", "steps",
    "positions", "account", "statements",
})

_BOOK_KEYS = frozenset({"title", "name"})

_REPLAY_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "replay_note", "guide", "steps", "traces",
})

#: The shipped example book's title, held to this
#: by the loader's example check.
_EXAMPLE_TITLE = "Crew replay at the M-137 slice boundary"

#: The shipped example's step ids, in journal
#: order, pinned by the loader.
_EXAMPLE_STEP_IDS = (
    "step-map", "step-diff", "step-ask",
    "step-decision", "step-note")

#: The shipped example's one trace: the replay
#: decision at step 4, its steps and its account
#: pinned word-for-word by the loader.
_EXAMPLE_TRACE_ID = "trace-replay-decision"

_EXAMPLE_TRACE_STEPS = (1, 2, 3, 4)

_EXAMPLE_TRACE_ACCOUNT = (
    "Step 1: cartographer handed findings "
    "'Run traffic mapped' to architect (M-138).",
    "Step 2: architect handed diff "
    "'Replay shape diff' to forge_worker (M-138).",
    "Step 3: forge_worker handed question "
    "'Replay kept whole' to human (M-138).",
    "Step 4: auditor handed findings "
    "'Decision - replay derived, never stored' "
    "to scribe (M-138).",
    "The decision 'Decision - replay derived, "
    "never stored' was handed by auditor at "
    "step 4; it rests on 4 hand-offs in "
    "journal order.",
)

PLAIN_EXPLANATION = (
    "Crew replay: a crew run's hand-offs, held "
    "in journal order as one replay a reader "
    "can walk, step by step - each step naming "
    "the member who handed, the member (or the "
    "human) it was handed to, the kind, the "
    "slice, the title and the body, validated "
    "by the crew comms layer itself. The replay "
    "is derived from the journal in order, "
    "never stored loose, and a decision's trace "
    "is derived from the hand-offs that led to "
    "it, so how a decision happened stays "
    "auditable. This layer holds replays and "
    "traces as data only; it reads no live "
    "journal, re-runs no step, spawns no agent "
    "and calls no model itself."
)

USAGE = (
    "Usage: /replay, /replay show, "
    "/replay step <step-id>, "
    "/replay trace <step-id>"
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


def _check_position(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) \
            or value < 1:
        raise ValueError(
            f"a journal position must be a whole number "
            f"from 1, got {value!r}")
    return value


def _check_positions(value: Any) -> Tuple[int, ...]:
    if isinstance(value, (str, bytes)) \
            or not isinstance(value, (list, tuple)):
        raise ValueError(
            f"a trace's steps must be a list of journal "
            f"positions, got {value!r}")
    positions = tuple(_check_position(p) for p in value)
    if not positions:
        raise ValueError("a trace names at least one step")
    if tuple(sorted(positions)) != positions \
            or len(set(positions)) != len(positions):
        raise ValueError(
            "a trace's steps stand in journal order, "
            "each once")
    return positions


def _check_account(value: Any) -> Tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(
            f"a trace's account must be a list of "
            f"statements, got {value!r}")
    account = tuple(
        _check_long_text(a, "an account statement")
        for a in value)
    if not account:
        raise ValueError("a trace carries at least one statement")
    if len(account) > 16:
        raise ValueError(
            f"a trace carries at most 16 statements, "
            f"got {len(account)}")
    if len(set(account)) != len(account):
        raise ValueError("a trace states one statement twice")
    return account


def _pick_any(mapping: Dict[str, Any], spellings: Tuple[str, ...],
              what: str) -> Any:
    values = [mapping[s] for s in spellings if s in mapping]
    if not values:
        return None
    if any(value != values[0] for value in values[1:]):
        raise ValueError(f"a record names two different {what}")
    return values[0]


def _check_handoff(value: Any) -> Handoff:
    """One step's hand-off: the comms layer's own reading.

    A Handoff stands as it is; a mapping is read
    by ``core/crew_comms.py`` itself, so the
    hand-off a replay walks is validated by
    exactly the validators a live hand-off
    answers to.
    """
    if isinstance(value, Handoff):
        return value
    if isinstance(value, dict):
        return validate_handoff(value)
    raise ValueError(
        f"a step's hand-off must be a hand-off record, "
        f"got {value!r}")


# ---------------------------------------------------------------------
# The step: one hand-off of the run, at its journal position.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class ReplayStep:
    """One step of a replay: a hand-off at its journal position.

    ``handoff`` is the M-126 hand-off itself -
    its sender, recipient, kind, slice, title
    and body are the decision or task handed;
    ``position`` is the step's place in the
    journal, from 1. Constructing one validates
    its shape only: whether its position is its
    place in its book is the book's concern.
    """

    step_id: Optional[str] = None
    position: int = 0
    handoff: Any = None

    def __post_init__(self) -> None:
        if self.step_id is not None:
            object.__setattr__(
                self, "step_id", normalize_member_id(self.step_id))
        object.__setattr__(
            self, "position", _check_position(self.position))
        if self.handoff is None:
            raise ValueError("a step is missing its hand-off")
        object.__setattr__(
            self, "handoff", _check_handoff(self.handoff))

    @property
    def sender(self) -> str:
        """The member who handed this step's hand-off."""
        return self.handoff.sender

    @property
    def recipient(self) -> str:
        """The member (or human) this hand-off was handed to."""
        return self.handoff.recipient

    @property
    def kind(self) -> str:
        """The kind of this step's hand-off."""
        return self.handoff.kind

    @property
    def slice_id(self) -> str:
        """The slice this step's hand-off belongs to."""
        return self.handoff.slice_id

    @property
    def title(self) -> str:
        """The title of this step's hand-off."""
        return self.handoff.title

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "crew_replay_step",
            "slice": CREW_REPLAY_SLICE,
            "step_id": self.step_id,
            "position": self.position,
            "handoff": self.handoff.to_record(),
        }


def validate_step(step: Any) -> ReplayStep:
    """Validate one step into a ReplayStep.

    Accepts a ReplayStep or a mapping naming a
    ``position`` (or ``seq`` /
    ``journal_position``), a ``handoff`` (or
    ``hand_off`` / ``entry``) - itself an M-126
    hand-off mapping, read by the comms layer -
    and an optional ``step_id`` (or ``id``).
    Naming two spellings of one field with
    different values refuses, and unknown keys
    refuse.
    """
    if isinstance(step, ReplayStep):
        return step
    if not isinstance(step, dict):
        raise ValueError(f"a step must be a mapping, got {step!r}")
    unknown = set(step) - _STEP_KEYS
    if unknown:
        raise ValueError(
            "unknown step keys: %s" % ", ".join(sorted(unknown)))
    position = _pick_any(
        step, ("position", "seq", "journal_position"), "positions")
    if position is None:
        raise ValueError("a step is missing its journal position")
    handoff = _pick_any(
        step, ("handoff", "hand_off", "entry"), "hand-offs")
    if handoff is None:
        raise ValueError("a step is missing its hand-off")
    kwargs: Dict[str, Any] = {
        "position": position, "handoff": handoff}
    step_id = _pick_any(step, ("step_id", "id"), "step ids")
    if step_id is not None:
        kwargs["step_id"] = step_id
    return ReplayStep(**kwargs)


def build_step(step: Any = None, **kwargs: Any) -> ReplayStep:
    """Build one validated step, from a mapping or field words."""
    if isinstance(step, ReplayStep) and not kwargs:
        return step
    if isinstance(step, dict) or step is None:
        merged: Dict[str, Any] = {}
        if isinstance(step, dict):
            merged.update(step)
        merged.update(kwargs)
        return validate_step(merged)
    raise ValueError(f"a step must be a mapping, got {step!r}")


# ---------------------------------------------------------------------
# The trace: how one decision happened, derived from its steps.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class DecisionTrace:
    """One decision trace: how a decision happened, as data.

    ``decision_step`` is the step id of the step
    carrying the decision; ``member`` is the
    member who handed that decision;
    ``slice_id`` is the decision's slice;
    ``steps`` are the journal positions that led
    to it, in journal order, the decision's own
    position last; ``account`` is the plain
    statements the trace rests on, read off
    those steps. A trace is normally derived
    from its steps (see :func:`derive_trace`);
    constructing one directly validates its
    shape only.
    """

    trace_id: Optional[str] = None
    decision_step: str = ""
    member: str = ""
    slice_id: str = ""
    steps: Tuple[int, ...] = ()
    account: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.trace_id is not None:
            object.__setattr__(
                self, "trace_id", normalize_member_id(self.trace_id))
        object.__setattr__(
            self, "decision_step",
            normalize_member_id(self.decision_step))
        object.__setattr__(
            self, "member", normalize_member_id(self.member))
        object.__setattr__(
            self, "slice_id", normalize_slice_id(self.slice_id))
        object.__setattr__(
            self, "steps", _check_positions(self.steps))
        object.__setattr__(
            self, "account", _check_account(self.account))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "crew_replay_trace",
            "slice": CREW_REPLAY_SLICE,
            "trace_id": self.trace_id,
            "decision_step": self.decision_step,
            "member": self.member,
            "slice_id": self.slice_id,
            "steps": list(self.steps),
            "account": list(self.account),
        }


def _held_steps(source: Any) -> Tuple[ReplayStep, ...]:
    """The steps one source holds, in journal order."""
    if isinstance(source, ReplayBook):
        return source.steps
    if isinstance(source, ReplayRegistry):
        return source.list_steps()
    if isinstance(source, (list, tuple)):
        steps = tuple(
            s if isinstance(s, ReplayStep) else validate_step(s)
            for s in source)
        return tuple(sorted(steps, key=lambda s: s.position))
    raise ValueError(f"replay steps are needed, got {source!r}")


def _decision_step(steps: Tuple[ReplayStep, ...],
                   decision: Any) -> ReplayStep:
    if isinstance(decision, ReplayStep):
        for step in steps:
            if step.position == decision.position:
                return step
        raise KeyError(
            f"no step in the replay at position: "
            f"{decision.position!r}")
    if isinstance(decision, bool):
        raise ValueError(f"a decision step is needed, got {decision!r}")
    if isinstance(decision, int):
        for step in steps:
            if step.position == decision:
                return step
        raise KeyError(
            f"no step in the replay at position: {decision!r}")
    if isinstance(decision, str):
        wanted = normalize_member_id(decision)
        for step in steps:
            if step.step_id == wanted:
                return step
        raise KeyError(f"no step in the replay: {wanted!r}")
    raise ValueError(f"a decision step is needed, got {decision!r}")


def derive_trace(source: Any, decision: Any) -> DecisionTrace:
    """Derive one decision trace from the steps that led to it.

    *source* is a ReplayBook, a ReplayRegistry
    or a list of steps; *decision* names the
    decision step, by step id, by journal
    position or as the step itself. The trace
    holds every step of the decision's slice at
    or before the decision's position, in
    journal order - the hand-offs that led to
    the decision, the decision itself last -
    and its account is read off those steps:
    one statement per step, in order, and a
    closing statement naming the decision.
    Deriving is deterministic: the same steps
    derive the same trace, every time.
    """
    steps = _held_steps(source)
    target = _decision_step(steps, decision)
    if target.step_id is None:
        raise ValueError(
            "a decision step must name a step id - "
            "a trace is addressed by its step")
    chain = tuple(
        s for s in steps
        if s.position <= target.position
        and s.slice_id == target.slice_id)
    account = tuple(
        f"Step {s.position}: {s.sender} handed {s.kind} "
        f"'{s.title}' to {s.recipient} ({s.slice_id})."
        for s in chain) + (
        f"The decision '{target.title}' was handed by "
        f"{target.sender} at step {target.position}; "
        f"it rests on {len(chain)} hand-offs in "
        f"journal order.",)
    return DecisionTrace(
        decision_step=target.step_id, member=target.sender,
        slice_id=target.slice_id,
        steps=tuple(s.position for s in chain), account=account)


def validate_trace(trace: Any, source: Any = None) -> DecisionTrace:
    """Validate one trace into a DecisionTrace.

    Accepts a DecisionTrace or a mapping naming
    a ``decision_step`` (or ``step_id`` /
    ``step``), a ``member`` (or ``decider``), a
    ``slice_id`` (or ``slice``), ``steps`` (or
    ``positions``), an ``account`` (or
    ``statements``) and an optional ``trace_id``
    (or ``id``). When *source* is given (a book,
    a registry or a list of steps), the trace is
    judged against the trace derived from those
    steps: the decision step, member, slice,
    steps and any stored account must equal the
    derived ones (a missing account is read off
    the steps). A stored trace naming no account
    of its own and judged against no steps
    refuses, because an account is derived off
    the steps, never stored loose.
    """
    derived = None
    if source is not None:
        ref = None
        if isinstance(trace, DecisionTrace):
            ref = trace.decision_step
        elif isinstance(trace, dict):
            ref = _pick_any(
                trace, ("decision_step", "step_id", "step"),
                "decision steps")
        if ref is None:
            raise ValueError("a trace is missing its decision step")
        derived = derive_trace(source, ref)
    if isinstance(trace, DecisionTrace):
        current = trace
    elif isinstance(trace, dict):
        unknown = set(trace) - _TRACE_KEYS
        if unknown:
            raise ValueError(
                "unknown trace keys: %s" % ", ".join(sorted(unknown)))
        decision_step = _pick_any(
            trace, ("decision_step", "step_id", "step"),
            "decision steps")
        if decision_step is None:
            if derived is None:
                raise ValueError("a trace is missing its decision step")
            decision_step = derived.decision_step
        member = _pick_any(trace, ("member", "decider"), "members")
        if member is None:
            if derived is None:
                raise ValueError("a trace is missing its member")
            member = derived.member
        slice_id = _pick_any(trace, ("slice_id", "slice"), "slices")
        if slice_id is None:
            if derived is None:
                raise ValueError("a trace is missing its slice")
            slice_id = derived.slice_id
        steps = _pick_any(trace, ("steps", "positions"), "steps")
        if steps is None:
            if derived is None:
                raise ValueError("a trace is missing its steps")
            steps = derived.steps
        account = _pick_any(
            trace, ("account", "statements"), "accounts")
        if account is None:
            if derived is None:
                raise ValueError(
                    "a stored trace names no account of its own - "
                    "derive it from its steps")
            account = derived.account
        trace_id = _pick_any(trace, ("trace_id", "id"), "trace ids")
        current = DecisionTrace(
            trace_id=trace_id, decision_step=decision_step,
            member=member, slice_id=slice_id, steps=steps,
            account=account)
    else:
        raise ValueError(f"a trace must be a mapping, got {trace!r}")
    if derived is not None:
        if current.decision_step != derived.decision_step:
            raise ValueError(
                "a trace's decision step disagrees with its steps")
        if current.member != derived.member:
            raise ValueError(
                "a trace's member disagrees with its decision "
                "step - a trace judges its own decision")
        if current.slice_id != derived.slice_id:
            raise ValueError(
                "a trace's slice disagrees with its decision step")
        if current.steps != derived.steps:
            raise ValueError(
                "a stored trace's steps disagree with the steps "
                "derived from the journal - a trace is derived "
                "off the steps, never stored loose")
        if current.account != derived.account:
            raise ValueError(
                "a stored trace's account disagrees with the "
                "account derived from its steps - an account "
                "is derived off the steps, never stored loose")
    return current


def build_trace(trace: Any = None, source: Any = None,
                **kwargs: Any) -> DecisionTrace:
    """Build one validated trace, from a mapping or field words."""
    if isinstance(trace, DecisionTrace) and not kwargs \
            and source is None:
        return trace
    if isinstance(trace, dict) or trace is None:
        merged: Dict[str, Any] = {}
        if isinstance(trace, dict):
            merged.update(trace)
        merged.update(kwargs)
        return validate_trace(merged, source)
    return validate_trace(trace, source)


# ---------------------------------------------------------------------
# The book: one run's replay whole, under a title.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class ReplayBook:
    """One replay book, whole, as data.

    ``title`` names the book; ``steps`` are the
    run's steps in journal order, standing at
    positions 1..N in the order held - a step
    naming any other position refuses, because
    the replay is the journal in order, never a
    re-ordered copy; ``traces`` are example
    traces, each judged against this book's
    steps as the book is built, so a held
    trace's account is always its steps'
    derived account.
    """

    title: str = ""
    steps: Tuple[ReplayStep, ...] = ()
    traces: Tuple[DecisionTrace, ...] = ()
    replay_note: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_short_text(self.title, "a title"))
        steps = tuple(
            s if isinstance(s, ReplayStep) else validate_step(s)
            for s in self.steps)
        if not steps:
            raise ValueError("a replay book holds at least one step")
        for place, step in enumerate(steps, start=1):
            if step.position != place:
                raise ValueError(
                    f"a replay's steps stand in journal order: "
                    f"the step at place {place} names position "
                    f"{step.position} - a replay is derived "
                    f"from the journal in order, never stored "
                    f"loose")
        ids = [s.step_id for s in steps if s.step_id is not None]
        if len(set(ids)) != len(ids):
            raise ValueError("a book holds one step id twice")
        object.__setattr__(self, "steps", steps)
        held = []
        for raw in self.traces:
            ref = raw.decision_step if isinstance(raw, DecisionTrace) \
                else _pick_any(
                    raw, ("decision_step", "step_id", "step"),
                    "decision steps")
            if ref is None or normalize_member_id(ref) not in ids:
                raise ValueError(
                    "a trace names a step the book holds "
                    "no step for")
            held.append(validate_trace(raw, source=steps))
        trace_ids = [t.trace_id for t in held if t.trace_id is not None]
        if len(set(trace_ids)) != len(trace_ids):
            raise ValueError("a book holds one trace id twice")
        object.__setattr__(self, "traces", tuple(held))
        if not isinstance(self.replay_note, str):
            raise ValueError("a replay book's note must be text")
        object.__setattr__(
            self, "replay_note", self.replay_note.strip())

    def step_for(self, step_id: Any) -> ReplayStep:
        """The step one id names in this book; unknown raises."""
        wanted = normalize_member_id(step_id)
        for step in self.steps:
            if step.step_id == wanted:
                return step
        raise KeyError(f"no step in the book: {wanted!r}")

    def step_at(self, position: Any) -> ReplayStep:
        """The step at one journal position; unknown raises."""
        wanted = _check_position(position)
        for step in self.steps:
            if step.position == wanted:
                return step
        raise KeyError(f"no step in the book at position: {wanted!r}")

    def steps_for(self, member: Any) -> Tuple[ReplayStep, ...]:
        """Every step one member sent or received, in order."""
        from .crew_comms import normalize_recipient
        wanted = normalize_recipient(member)
        return tuple(
            s for s in self.steps
            if s.sender == wanted or s.recipient == wanted)

    def step_ids(self) -> Tuple[str, ...]:
        """Every held step id, in journal order (id-less skipped)."""
        return tuple(s.step_id for s in self.steps if s.step_id)

    def trace_for(self, trace_id: Any) -> DecisionTrace:
        """The trace one id names in this book; unknown raises."""
        wanted = normalize_member_id(trace_id)
        for trace in self.traces:
            if trace.trace_id == wanted:
                return trace
        raise KeyError(f"no trace in the replay book: {wanted!r}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "crew_replay_book",
            "slice": CREW_REPLAY_SLICE,
            "title": self.title,
            "step_ids": list(self.step_ids()),
            "step_count": len(self.steps),
            "trace_count": len(self.traces),
        }


def validate_book(data: Any, *, require_example: bool = False) -> ReplayBook:
    """Validate one replay mapping into a ReplayBook.

    The mapping names a ``schema`` (the replay
    schema word), a ``guide`` mapping (its
    ``title``), a ``steps`` list and an optional
    ``traces`` list. Every step is validated -
    its hand-off by the comms layer - then the
    whole is judged: the steps stand at
    positions 1..N in the order held, step ids
    are unique, and every trace is judged
    against the book's steps. With
    ``require_example`` the shipped example is
    held to its pinned shape: the pinned title,
    the pinned steps in order, and the pinned
    example trace carrying its pinned account
    word-for-word. Problems raise
    :class:`ValidationError` or ``ValueError``
    naming the problem.
    """
    if isinstance(data, ReplayBook):
        return data
    if not isinstance(data, dict):
        raise ValidationError(
            f"a replay book must be a mapping, got {data!r}")
    unknown = set(data) - _REPLAY_KEYS
    if unknown:
        raise ValidationError(
            "unknown replay keys: %s" % ", ".join(sorted(unknown)))
    if data.get("schema") != CREW_REPLAY_SCHEMA:
        raise ValidationError(
            f"a replay book must carry schema "
            f"{CREW_REPLAY_SCHEMA!r}, got {data.get('schema')!r}")
    if "steps" not in data:
        raise ValidationError("a replay book is missing its steps")
    raw = data["steps"]
    if not isinstance(raw, (list, tuple)):
        raise ValidationError("a replay book's steps must be a list")
    raw_traces = data.get("traces") or []
    if not isinstance(raw_traces, (list, tuple)):
        raise ValidationError("a replay book's traces must be a list")
    head = data.get("guide") or {}
    if not isinstance(head, dict):
        raise ValidationError("a replay book's guide must be a mapping")
    unknown_head = set(head) - _BOOK_KEYS
    if unknown_head:
        raise ValidationError(
            "unknown guide keys: %s" % ", ".join(sorted(unknown_head)))
    try:
        title = _pick_any(head, ("title", "name"), "titles")
        if title is None:
            raise ValidationError("a replay book is missing its title")
        steps = tuple(validate_step(s) for s in raw)
        note = data.get("replay_note") or ""
        if not isinstance(note, str):
            raise ValidationError("a replay book's note must be text")
        book = ReplayBook(
            title=title, steps=steps, traces=tuple(raw_traces),
            replay_note=note)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    if require_example:
        if book.title != _EXAMPLE_TITLE:
            raise ValidationError(
                "the shipped example replay book's title is not "
                "the pinned title")
        if book.step_ids() != _EXAMPLE_STEP_IDS:
            raise ValidationError(
                "the shipped example replay book's steps are not "
                "the pinned steps")
        trace = book.trace_for(_EXAMPLE_TRACE_ID)
        if trace.steps != _EXAMPLE_TRACE_STEPS:
            raise ValidationError(
                "the shipped example trace does not name its "
                "pinned steps")
        if trace.account != _EXAMPLE_TRACE_ACCOUNT:
            raise ValidationError(
                "the shipped example trace does not carry its "
                "pinned account word-for-word")
        derived = derive_trace(book, trace.decision_step)
        if (derived.member, derived.slice_id, derived.steps,
                derived.account) != (trace.member, trace.slice_id,
                                     trace.steps, trace.account):
            raise ValidationError(
                "the shipped example trace is not the trace "
                "derived from its steps")
    return book


def build_book(book: Any = None, **kwargs: Any) -> ReplayBook:
    """Build one validated book, from a mapping or field words."""
    if isinstance(book, ReplayBook) and not kwargs:
        return book
    if isinstance(book, (list, tuple)) and not kwargs:
        raise ValueError("a book needs its title")
    if isinstance(book, dict):
        if "steps" in book or "schema" in book:
            return validate_book(book)
        merged: Dict[str, Any] = dict(book)
        merged.update(kwargs)
        return ReplayBook(**merged)
    if book is None:
        return ReplayBook(**kwargs)
    raise ValueError(f"a replay book is needed, got {book!r}")


def _book_from(data: Any, *, require_example: bool) -> ReplayBook:
    try:
        return validate_book(data, require_example=require_example)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def load_crew_replay(data: Optional[Dict[str, Any]] = None) -> ReplayBook:
    """Load and validate the shipped example replay book (or *data*).

    The shipped file is held to the example check:
    the pinned title, the pinned steps in journal
    order, and the pinned example trace - the
    replay decision at step 4, its account derived
    from its steps - so the shipped book covers
    the boundary this slice exists to hold.
    """
    raw = data if data is not None else load_resource(
        CREW_REPLAY_RESOURCE)
    return _book_from(raw, require_example=True)


def load_crew_replay_file(path: Any) -> ReplayBook:
    """Load and validate a replay book from a file at *path*.

    Any file in the replay shape, anywhere on
    disk, validated whole - a malformed file
    raises :class:`ValidationError` naming the
    problem, and a missing file raises
    ``FileNotFoundError``. The example check is
    not held: a real replay book stands on its
    own steps.
    """
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _book_from(raw, require_example=False)


# ---------------------------------------------------------------------
# The registry model: one book held step by step, in journal order.
# ---------------------------------------------------------------------


class ReplayRegistry:
    """One session's replay book, held step by step.

    The registry holds steps, never traces: a
    trace is a derivation, read off held steps
    at call time, so nothing here can hold an
    account stale. A step joins only at the
    next journal position - the held order IS
    the journal order.
    """

    def __init__(self, book: Any = None) -> None:
        self._title: Optional[str] = None
        self._steps: Dict[str, ReplayStep] = {}
        self._order: list = []
        self._next_step = 1
        if book is not None:
            self.register_book(book)

    def _fresh_step_id(self, held_ids: Any) -> str:
        while f"replay-{self._next_step}" in held_ids:
            self._next_step += 1
        fresh = f"replay-{self._next_step}"
        self._next_step += 1
        return fresh

    def register_step(self, step: Any) -> ReplayStep:
        """Register one step into the held book.

        The step must stand at the next journal
        position - a step naming any other
        position refuses, because the held order
        is the journal order. A step with no id
        is given a deterministic ``replay-N`` id.
        A step id already standing here refuses.
        """
        validated = build_step(step)
        expected = len(self._order) + 1
        if validated.position != expected:
            raise ValueError(
                f"a step joins the replay at the next journal "
                f"position {expected}, got position "
                f"{validated.position} - the held order is "
                f"the journal order")
        held_ids = set(self._steps)
        if validated.step_id is not None \
                and validated.step_id in held_ids:
            raise ValueError(
                f"a step named {validated.step_id!r} already exists")
        if validated.step_id is None:
            validated = replace(
                validated, step_id=self._fresh_step_id(held_ids))
        self._steps[validated.step_id] = validated
        self._order.append(validated.step_id)
        return validated

    def register_book(self, book: Any) -> ReplayBook:
        """Register every step of one book, in order.

        The first book held sets the title; a
        later book under a different title
        refuses, as does a book whose steps do
        not continue the held journal order. The
        book's traces are derivations, not
        holdings, and are not held.
        """
        validated = build_book(book)
        if self._title is not None and validated.title != self._title:
            raise ValueError(
                "this registry already holds a replay book under "
                "a different title")
        for step in validated.steps:
            if step.step_id is not None and step.step_id in self._steps:
                raise ValueError(
                    f"a step named {step.step_id!r} already exists")
        self._title = validated.title
        for step in validated.steps:
            self.register_step(step)
        return self.book()

    def get_step(self, step_id: Any) -> ReplayStep:
        """The step one id names among the held steps."""
        wanted = normalize_member_id(step_id)
        if wanted not in self._steps:
            raise KeyError(f"unknown step: {wanted!r}")
        return self._steps[wanted]

    def step_at(self, position: Any) -> ReplayStep:
        """The held step at one journal position."""
        wanted = _check_position(position)
        for step_id in self._order:
            step = self._steps[step_id]
            if step.position == wanted:
                return step
        raise KeyError(f"no held step at position: {wanted!r}")

    def list_steps(self) -> Tuple[ReplayStep, ...]:
        """Every held step, in the order they were held."""
        return tuple(self._steps[s] for s in self._order)

    def book(self) -> ReplayBook:
        """The held steps as one validated replay book."""
        if self._title is None:
            raise ValueError("no replay book is held yet")
        return ReplayBook(title=self._title, steps=self.list_steps())

    def trace_for(self, decision: Any) -> DecisionTrace:
        """Derive the trace for one held decision, at call time.

        The account is the held steps' own
        hand-offs, read at call time - the
        registry holds steps, and this trace is
        derived from them.
        """
        return derive_trace(self.list_steps(), decision)


# ---------------------------------------------------------------------
# Replay news, shaped as session records.
# ---------------------------------------------------------------------


def step_record(step: Any) -> Dict[str, Any]:
    """The session-news record of one step."""
    current = step if isinstance(step, ReplayStep) \
        else build_step(step)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Step {current.position}: {current.sender} handed "
        f"{current.kind} '{current.title}' to "
        f"{current.recipient} ({current.slice_id}).")
    return record


def book_record(book: Any) -> Dict[str, Any]:
    """The session-news record of one replay book."""
    current = book if isinstance(book, ReplayBook) else build_book(book)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Replay book {current.title}: {record['step_count']} "
        f"step(s) in journal order.")
    return record


def trace_record(trace: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of one trace.

    With *source* given, the trace is first
    judged against the steps it belongs to.
    """
    current = validate_trace(trace, source)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"How '{current.decision_step}' happened: "
        f"{len(current.steps)} step(s) led to the "
        f"decision by {current.member}.")
    return record


def plain_words(step: Any) -> str:
    """One step, in one plain sentence."""
    current = step if isinstance(step, ReplayStep) \
        else build_step(step)
    return (
        f"{current.sender} handed {current.kind} "
        f"'{current.title}' to {current.recipient} "
        f"at journal step {current.position} "
        f"({current.slice_id})")


def trace_plain_words(source: Any) -> str:
    """Traces in plain words: every trace, in full.

    Accepts a DecisionTrace or a ReplayBook.
    Each trace is told whole - its decision, its
    member and its account - so nothing is
    hidden and nothing is invented.
    """
    if isinstance(source, DecisionTrace):
        traces = (source,)
        title = None
    elif isinstance(source, ReplayBook):
        traces = source.traces
        title = source.title
    else:
        raise ValueError(f"a replay source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    for trace in traces:
        lines.append(
            f"{trace.decision_step} - decision by {trace.member}")
        lines.extend(trace.account)
    return "\n".join(lines)


# ---------------------------------------------------------------------
# Screens: the formatters and the shared /replay grammar.
# ---------------------------------------------------------------------


def _source_book(source: Any) -> ReplayBook:
    if source is None:
        return load_crew_replay()
    if isinstance(source, ReplayRegistry):
        return source.book()
    if isinstance(source, ReplayBook):
        return source
    raise ValueError(f"a replay book is needed, got {source!r}")


def format_step(step: Any) -> str:
    """One step as a screen line, at its journal position."""
    current = step if isinstance(step, ReplayStep) \
        else build_step(step)
    return (
        f"{current.position}. {current.step_id or '-'}: "
        f"{current.sender} -> {current.recipient} "
        f"[{current.kind}] '{current.title}' ({current.slice_id})")


def format_steps(source: Any = None, member: Any = None) -> str:
    """Steps of one book, in journal order.

    With *member* given, only the steps that
    member sent or received are shown.
    """
    book = _source_book(source)
    steps = book.steps if member is None else book.steps_for(member)
    lines = [format_step(step) for step in steps]
    if not lines:
        lines.append("No replay steps are held.")
    return "\n".join(lines)


def format_trace(source: Any = None) -> str:
    """Traces as screen blocks: decision over derived account.

    Accepts a DecisionTrace or a ReplayBook; a
    book shows every trace it holds, in book
    order.
    """
    if isinstance(source, DecisionTrace):
        traces = (source,)
        lines: list = []
    else:
        book = _source_book(source)
        traces = book.traces
        lines = [f"Traces in {book.title}:"]
    for trace in traces:
        lines.append(
            f"{trace.decision_step} - decision by {trace.member}")
        lines.extend(trace.account)
    if isinstance(source, DecisionTrace):
        return "\n".join(lines)
    if len(lines) == 1:
        lines.append("Nothing here.")
    return "\n".join(lines)


def format_replay_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /replay.

    With nothing named, the shipped example
    replay book is shown - the example this
    slice ships - so the screen is never empty.
    """
    book = _source_book(source)
    lines = ["Crew replay (M-138) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_steps(book))
    lines.append("")
    lines.append(format_trace(book))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_replay_args(args: Any) -> Tuple[str, Optional[str]]:
    """Parse the /replay grammar both surfaces share.

    No words (or ``show`` / ``list``) shows the
    replay book; ``step <step-id>`` shows one
    step; ``trace <step-id>`` derives the trace
    of the decision that step carries. Anything
    else is a usage error naming the grammar.
    Returns ``(action, value-or-None)``.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() in ("show", "list"):
        return ("show", None)
    words = text.split()
    head = words[0].lower()
    if head in ("step", "trace") and len(words) == 2:
        try:
            return (head, normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
