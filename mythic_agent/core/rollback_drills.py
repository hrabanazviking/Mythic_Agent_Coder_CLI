"""Rollback drills (All-Features roadmap slice M-112).

Part V - Autonomy & Safety. The roadmap's words:
``scripted disasters (bad mass edit, wrong branch
push attempt, corrupted session) recovered in
tests.``

What already shipped, and what this slice adds:

* The tree already holds every recovery road a
  drill exercises: named checkpoints capture the
  whole working tree plus session state and
  restore in one command
  (``mythic_agent/core/checkpoints.py``, M-075,
  ``CheckpointStore``), the undo timeline walks
  edits, commands and checkpoints as one timeline
  and undoes a command by its recorded footprint,
  all-or-nothing (``undo_timeline.py``, M-077),
  the mass-edit guard reports a mass edit's risks
  before it lands and gates it on approval
  (``mass_edit_guard.py``, M-093,
  ``build_report`` / ``require_approval``),
  change sets are reviewed whole and applied or
  rejected as one (``change_sets.py``), the
  destructive-command doctrine judges a push
  before it runs - a plain push is costly, a
  force push irreversible (``destructive_doctrine.py``,
  M-111, ``judge_command``), sessions are kept in
  a write-ahead journal so a dead process loses
  nothing (``sessions.py``, ``SessionStore`` with
  ``check_recovery`` / ``recover_pending``), and
  startup crash recovery replays journaled
  checkpoints left by a dead process
  (``recovery.py``, ``recover_crashed_sessions``).
  Nothing in the tree holds the *drills*
  themselves as data - the scripted disasters,
  the recovery road each one exercises, and a
  judged record of whether the recovery held.
* This slice is that missing drill book, as a
  pure layer in the exact sibling shape: the
  drill catalogue held as validated data (the
  roadmap's three named disasters, each a frozen
  definition carrying its scripted setup and the
  recovery road it exercises, step by step), a
  drill result held as validated data whose
  outcome is derived from its step counts, a
  mechanical judge that reads step counts alone,
  a drill record shaped as session news, and a
  small in-memory registry model with
  deterministic ids. This module scripts no
  disaster, restores nothing, writes no file,
  changes no setting and imports no agent / UI
  code; the agent layer owns holding the
  registry for a session and running the real
  drills against the real recovery roads in
  tests.

Honesty rules, enforced here and pinned by tests:

* **The catalogue is exactly three drills.**
  Bad mass edit, wrong-branch push attempt,
  corrupted session - the roadmap's own three
  disasters, in the roadmap's order. Each drill
  names the recovery road it exercises as held
  steps, naming the shipped machinery it walks;
  a definition built naming any other disaster
  refuses.
* **A result never disagrees with itself.**
  A result's step total is its drill's own held
  step count, its passed count never exceeds
  that total, and its outcome is derived from
  the two counts: recovered only when every
  step passed, partially recovered when some
  passed, not recovered when none did. A result
  built naming any other outcome refuses.
* **Recovery is claimed only whole.** A drill
  is ``recovered`` only when every step of its
  recovery road passed; a partial walk is stated
  as partially recovered, in words, wherever it
  is shown - never rounded up to a recovery.
* **A drill here is data, not a deed.** Holding
  or judging a drill runs no disaster and
  restores nothing; the record says what a test
  run reported, and this layer never presents a
  held definition as a recovery that happened.
* **Status is never carried by colour or symbol
  alone.** Every formatter states a result's
  outcome in words.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Dict, Optional, Tuple

__all__ = [
    "DRILL_CATALOGUE",
    "DRILL_DISASTERS",
    "DRILL_OUTCOMES",
    "OUTCOME_PHRASES",
    "PLAIN_EXPLANATION",
    "ROLLBACK_DRILLS_SLICE",
    "USAGE",
    "Definition",
    "DrillDefinition",
    "DrillRegistry",
    "DrillResult",
    "Result",
    "build_definition",
    "build_result",
    "drill_for",
    "drill_for_disaster",
    "drill_record",
    "format_drill",
    "format_drills",
    "format_result",
    "format_results",
    "format_record",
    "format_rollback_record",
    "format_rollback_screen",
    "judge_result",
    "normalize_disaster",
    "normalize_drill_id",
    "normalize_outcome",
    "normalize_run_id",
    "outcome_for_counts",
    "parse_rollback_args",
    "plain_words",
    "validate_definition",
    "validate_result",
]

ROLLBACK_DRILLS_SLICE = "M-112"

#: The roadmap's three named disasters, in the
#: roadmap's order: the drills this book holds.
DRILL_DISASTERS = (
    "bad_mass_edit", "wrong_branch_push",
    "corrupted_session")

#: What a drill run can honestly conclude, in
#: worsening order of wholeness: every recovery
#: step passed, some passed, or none did.
DRILL_OUTCOMES = (
    "recovered", "partially_recovered",
    "not_recovered")

#: Each outcome, said in plain words.
OUTCOME_PHRASES = {
    "recovered": "recovered in full",
    "partially_recovered": "only partially recovered",
    "not_recovered": "not recovered",
}

_DISASTER_LABELS = {
    "bad_mass_edit": "bad mass edit",
    "wrong_branch_push": "wrong branch push attempt",
    "corrupted_session": "corrupted session",
}

_DISASTER_WORDS = {
    "bad_mass_edit": "bad_mass_edit",
    "mass_edit": "bad_mass_edit",
    "bad_edit": "bad_mass_edit",
    "wrong_branch_push": "wrong_branch_push",
    "wrong_branch": "wrong_branch_push",
    "wrong_push": "wrong_branch_push",
    "corrupted_session": "corrupted_session",
    "corrupt_session": "corrupted_session",
    "corrupted": "corrupted_session",
}

_OUTCOME_WORDS = {
    "recovered": "recovered", "full": "recovered",
    "whole": "recovered",
    "partially_recovered": "partially_recovered",
    "partial": "partially_recovered",
    "partly": "partially_recovered",
    "not_recovered": "not_recovered",
    "failed": "not_recovered",
    "unrecovered": "not_recovered",
}

PLAIN_EXPLANATION = (
    "Rollback drills are scripted disasters, "
    "recovered in tests. The drill book holds "
    "exactly three drills - a bad mass edit, a "
    "wrong branch push attempt and a corrupted "
    "session - each as data: the disaster setup "
    "and the recovery road it exercises, step by "
    "step, over machinery the tree already "
    "ships (checkpoints, the undo timeline, the "
    "mass-edit guard, the destructive-command "
    "doctrine and the session journal's crash "
    "recovery). A drill result counts the steps "
    "that passed, and its outcome is derived "
    "from that count: recovered only when every "
    "step passed, never rounded up. This layer "
    "holds the drills and their results as data "
    "only; it scripts no disaster and restores "
    "nothing itself - the agent layer runs the "
    "real drills against the real recovery "
    "roads and holds the results for a session."
)

USAGE = (
    "Usage: /rollback, /rollback show, "
    "/rollback show <run>, "
    "/rollback drills, "
    "/rollback run <drill>"
)

_ID_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789-_.")

_DRILL_ID_CHARS = frozenset(
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
                f"a drill record names two different {what}")
    return first


def _clean_steps(values: Any, what: str) -> Tuple[str, ...]:
    """Recovery steps as a validated, ordered tuple of texts."""
    if isinstance(values, (str, bytes)) \
            or not isinstance(values, (list, tuple)):
        raise ValueError(
            f"{what} must be a list of step texts, got {values!r}")
    cleaned = []
    for value in values:
        cleaned.append(_clean_text(value, "a recovery step"))
    if not cleaned:
        raise ValueError(f"{what} must name at least one step")
    return tuple(cleaned)


def _clean_count(value: Any, what: str) -> int:
    """A step count as data: a non-negative whole number."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{what} must be a whole number, got {value!r}")
    if value < 0:
        raise ValueError(f"{what} must not be negative, got {value!r}")
    return value


def normalize_disaster(value: Any) -> str:
    """The canonical disaster a word names.

    Reads the roadmap's three disasters (and
    their short spellings), case-insensitively,
    with dashes and spaces read as underscores.
    Any other word refuses: the catalogue's
    disasters are a closed vocabulary of three.
    """
    if isinstance(value, str):
        wanted = value.strip().lower().replace(
            "-", "_").replace(" ", "_")
        if wanted in _DISASTER_WORDS:
            return _DISASTER_WORDS[wanted]
    raise ValueError(
        "a drill disaster must be one of %s, got %r"
        % ("/".join(DRILL_DISASTERS), value))


def normalize_outcome(value: Any) -> str:
    """The canonical drill outcome a word names.

    Reads ``recovered``, ``partially_recovered``
    (or ``partial``) and ``not_recovered`` (or
    ``failed``), case-insensitively. Any other
    word refuses: the outcomes are a closed
    vocabulary.
    """
    if isinstance(value, str):
        wanted = value.strip().lower().replace(
            "-", "_").replace(" ", "_")
        if wanted in _OUTCOME_WORDS:
            return _OUTCOME_WORDS[wanted]
    raise ValueError(
        "a drill outcome must be one of %s, got %r"
        % ("/".join(DRILL_OUTCOMES), value))


def normalize_drill_id(value: Any) -> str:
    """The canonical drill id a word names.

    A drill id is lowercase letters, digits and
    underscores, read case-insensitively with
    dashes and spaces as underscores. Anything
    else raises.
    """
    if isinstance(value, str):
        wanted = value.strip().lower().replace(
            "-", "_").replace(" ", "_")
        if wanted and all(
                ch in _DRILL_ID_CHARS for ch in wanted):
            return wanted
    raise ValueError(
        f"a drill id must be a word of lowercase letters, "
        f"digits and underscores, got {value!r}")


def normalize_run_id(value: Any) -> str:
    """The canonical drill-run id a word names.

    A run id is one word of letters, digits,
    dashes, underscores and dots, read with its
    case kept. Anything else raises.
    """
    if isinstance(value, str):
        wanted = value.strip()
        if wanted and all(ch in _ID_CHARS for ch in wanted):
            return wanted
    raise ValueError(
        f"a run id must be a non-empty word of letters, "
        f"digits, dashes, underscores and dots, got {value!r}")


def outcome_for_counts(steps_passed: Any,
                       steps_total: Any) -> str:
    """The one outcome two step counts honestly earn.

    Every step passed is ``recovered``; some
    passed is ``partially_recovered``; none is
    ``not_recovered``. A total of zero steps, or
    more passed than the total holds, refuses -
    no outcome can be derived from counts that
    cannot be.
    """
    passed = _clean_count(steps_passed, "steps passed")
    total = _clean_count(steps_total, "steps total")
    if total < 1:
        raise ValueError("a drill must hold at least one step")
    if passed > total:
        raise ValueError(
            f"steps passed ({passed}) cannot exceed "
            f"steps total ({total})")
    if passed == total:
        return "recovered"
    if passed == 0:
        return "not_recovered"
    return "partially_recovered"


# ---------------------------------------------------------------------
# The catalogue: the roadmap's three scripted disasters, each with
# the recovery road it exercises, held as validated data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class DrillDefinition:
    """One scripted disaster and its recovery road, as data.

    ``drill_id`` names the drill, ``disaster``
    is one of the roadmap's three named
    disasters, ``label`` says the drill in plain
    words, ``setup`` states the scripted disaster
    a test run stages, and ``recovery_steps`` is
    the recovery road the drill exercises, step
    by step, in order - each step naming the
    shipped machinery it walks. Constructing one
    validates it.
    """

    drill_id: str
    disaster: str
    label: str
    setup: str
    recovery_steps: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "drill_id", normalize_drill_id(self.drill_id))
        object.__setattr__(
            self, "disaster", normalize_disaster(self.disaster))
        object.__setattr__(
            self, "label", _clean_text(self.label, "a label"))
        object.__setattr__(
            self, "setup", _clean_text(self.setup, "a setup"))
        object.__setattr__(
            self, "recovery_steps",
            _clean_steps(self.recovery_steps, "recovery steps"))

    @property
    def step_count(self) -> int:
        return len(self.recovery_steps)

    @property
    def display_label(self) -> str:
        return f"{self.drill_id} ({self.label})"

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "rollback_drill",
            "slice": ROLLBACK_DRILLS_SLICE,
            "drill_id": self.drill_id,
            "disaster": self.disaster,
            "label": self.label,
            "setup": self.setup,
            "recovery_steps": list(self.recovery_steps),
            "step_count": self.step_count,
        }


#: The plainer word for a drill definition.
Definition = DrillDefinition

_DEFINITION_KEYS = frozenset({
    "drill_id", "id", "name", "disaster", "kind",
    "label", "setup", "recovery_steps", "steps", "road",
})


def validate_definition(definition: Any) -> DrillDefinition:
    """Validate one drill definition into a DrillDefinition.

    Accepts a DrillDefinition or a mapping naming
    a ``drill_id`` (or ``id`` / ``name``), a
    ``disaster`` (or ``kind``), a ``label``, a
    ``setup`` and ``recovery_steps`` (or ``steps``
    / ``road``). Naming two spellings of one
    field with different values refuses, and
    unknown keys refuse.
    """
    if isinstance(definition, DrillDefinition):
        return definition
    if not isinstance(definition, dict):
        raise ValueError(
            f"a drill definition must be a mapping, got {definition!r}")
    unknown = set(definition) - _DEFINITION_KEYS
    if unknown:
        raise ValueError(
            "unknown definition keys: %s" % ", ".join(sorted(unknown)))
    drill_id = _pick(definition, ("drill_id", "id", "name"), "drill ids")
    disaster = _pick(definition, ("disaster", "kind"), "disasters")
    steps = _pick(
        definition, ("recovery_steps", "steps", "road"),
        "recovery steps")
    if drill_id is None or disaster is None \
            or "label" not in definition \
            or "setup" not in definition or steps is None:
        raise ValueError(
            "a drill definition must name its drill_id, "
            "disaster, label, setup and recovery_steps")
    return DrillDefinition(
        drill_id=drill_id, disaster=disaster,
        label=definition["label"], setup=definition["setup"],
        recovery_steps=steps)


def build_definition(definition: Any = None,
                     **kwargs: Any) -> DrillDefinition:
    """Build one validated definition from a mapping or field words."""
    if isinstance(definition, DrillDefinition) and not kwargs:
        return definition
    if isinstance(definition, dict) or definition is None:
        merged: Dict[str, Any] = {}
        if isinstance(definition, dict):
            merged.update(definition)
        merged.update(kwargs)
        return validate_definition(merged)
    raise ValueError(
        f"a drill definition must be a mapping, got {definition!r}")


#: The drill book itself, held as data, in the
#: roadmap's order: the bad mass edit, the wrong
#: branch push attempt, the corrupted session.
#: Each recovery road walks only machinery the
#: tree already ships - this book composes those
#: roads into drills, it invents no new one.
DRILL_CATALOGUE: Tuple[DrillDefinition, ...] = (
    DrillDefinition(
        drill_id="bad_mass_edit_drill",
        disaster="bad_mass_edit",
        label="bad mass edit, rolled back to the checkpoint",
        setup=(
            "a scripted mass edit rewrites many files "
            "wrongly at once - the change the mass-edit "
            "guard exists to catch"),
        recovery_steps=(
            "take a named checkpoint of the clean tree "
            "(checkpoints, M-075)",
            "stage the bad mass edit and read its "
            "mass-edit guard report (M-093)",
            "restore the checkpoint in one command, "
            "discarding the bad edit whole",
            "verify the working tree matches the "
            "checkpoint exactly - no bad edit remains",
        )),
    DrillDefinition(
        drill_id="wrong_branch_push_drill",
        disaster="wrong_branch_push",
        label="wrong branch push attempt, stopped before the remote",
        setup=(
            "a scripted push aims the session's commits "
            "at the wrong branch - the push the "
            "destructive-command doctrine exists to "
            "judge before it runs"),
        recovery_steps=(
            "judge the push against the doctrine "
            "before it runs (M-111)",
            "stop the attempt: the wrong branch on "
            "the remote is never written",
            "verify the remote still names the "
            "pre-drill state - nothing was published",
            "retarget the push at the session's own "
            "branch and judge it again",
        )),
    DrillDefinition(
        drill_id="corrupted_session_drill",
        disaster="corrupted_session",
        label="corrupted session, recovered from its journal",
        setup=(
            "a scripted corruption breaks the live "
            "session's state - the crash the session "
            "journal and startup recovery exist to "
            "survive"),
        recovery_steps=(
            "detect the uncommitted checkpoint the "
            "dead session left (session journal)",
            "replay it through startup crash recovery "
            "(recovery, recover_crashed_sessions)",
            "verify the recovered session carries "
            "its full transcript - nothing was lost",
            "walk the undo timeline back over the "
            "corrupting command's footprint (M-077)",
        )),
)


def drill_for(drill_id: Any) -> DrillDefinition:
    """The one held drill a drill id names."""
    wanted = normalize_drill_id(drill_id)
    for drill in DRILL_CATALOGUE:
        if drill.drill_id == wanted:
            return drill
    raise ValueError(f"unknown rollback drill: {wanted!r}")


def drill_for_disaster(disaster: Any) -> DrillDefinition:
    """The one held drill a disaster word names."""
    wanted = normalize_disaster(disaster)
    for drill in DRILL_CATALOGUE:
        if drill.disaster == wanted:
            return drill
    raise ValueError(f"unknown drill disaster: {wanted!r}")


# ---------------------------------------------------------------------
# The result: one drill run reported, the verdict as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class DrillResult:
    """One drill run's reported outcome, as data.

    ``drill_id`` names a held drill, and the
    result's ``disaster`` is that drill's own.
    ``steps_total`` is the drill's held step
    count - a result naming any other total
    refuses - and ``steps_passed`` counts the
    recovery steps a test run reported passing.
    ``outcome`` is derived from the two counts
    when unnamed, and a result built naming any
    other outcome refuses, so a result that
    exists never disagrees with itself.
    Constructing one validates it.
    """

    drill_id: str
    steps_passed: int = 0
    steps_total: Optional[int] = None
    outcome: Optional[str] = None
    run_id: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "drill_id", normalize_drill_id(self.drill_id))
        held = drill_for(self.drill_id)
        passed = _clean_count(self.steps_passed, "steps passed")
        object.__setattr__(self, "steps_passed", passed)
        if self.steps_total is None:
            total = held.step_count
        else:
            total = _clean_count(self.steps_total, "steps total")
            if total != held.step_count:
                raise ValueError(
                    f"drill {held.drill_id} holds {held.step_count} "
                    f"recovery steps, not {total}")
        object.__setattr__(self, "steps_total", total)
        derived = outcome_for_counts(passed, total)
        if self.outcome is None:
            object.__setattr__(self, "outcome", derived)
        else:
            named = normalize_outcome(self.outcome)
            if named != derived:
                raise ValueError(
                    f"{passed} of {total} steps passed earns "
                    f"outcome {derived}, not {named}")
            object.__setattr__(self, "outcome", named)
        if self.run_id is not None:
            object.__setattr__(
                self, "run_id", normalize_run_id(self.run_id))

    @property
    def disaster(self) -> str:
        return drill_for(self.drill_id).disaster

    @property
    def recovered(self) -> bool:
        return self.outcome == "recovered"

    @property
    def display_label(self) -> str:
        name = self.run_id or "run"
        return f"{name} ({self.drill_id}: {self.outcome})"

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "drill_result",
            "slice": ROLLBACK_DRILLS_SLICE,
            "run_id": self.run_id,
            "drill_id": self.drill_id,
            "disaster": self.disaster,
            "steps_passed": self.steps_passed,
            "steps_total": self.steps_total,
            "outcome": self.outcome,
        }


#: The shorter word for a drill result.
Result = DrillResult

_RESULT_KEYS = frozenset({
    "run_id", "id", "drill_id", "drill", "steps_passed",
    "passed", "steps_total", "total", "outcome", "verdict",
})


def validate_result(result: Any) -> DrillResult:
    """Validate one drill result into a DrillResult.

    Accepts a DrillResult or a mapping naming a
    ``drill_id`` (or ``drill``) - required - and
    optionally ``steps_passed`` (or ``passed``),
    ``steps_total`` (or ``total``), an ``outcome``
    (or ``verdict``) that must be the counts' own,
    and a ``run_id`` (or ``id``). Naming two
    spellings of one field with different values
    refuses, and unknown keys refuse.
    """
    if isinstance(result, DrillResult):
        return result
    if not isinstance(result, dict):
        raise ValueError(f"a drill result must be a mapping, got {result!r}")
    unknown = set(result) - _RESULT_KEYS
    if unknown:
        raise ValueError(
            "unknown result keys: %s" % ", ".join(sorted(unknown)))
    drill_id = _pick(result, ("drill_id", "drill"), "drill ids")
    if drill_id is None:
        raise ValueError("a drill result must name its drill")
    kwargs: Dict[str, Any] = {"drill_id": drill_id}
    for field_name, spellings in (
            ("steps_passed", ("steps_passed", "passed")),
            ("steps_total", ("steps_total", "total")),
            ("outcome", ("outcome", "verdict")),
            ("run_id", ("run_id", "id"))):
        value = _pick(result, spellings, field_name)
        if value is not None:
            kwargs[field_name] = value
    return DrillResult(**kwargs)


def build_result(result: Any = None, **kwargs: Any) -> DrillResult:
    """Build one validated result from a mapping or field words."""
    if isinstance(result, DrillResult) and not kwargs:
        return result
    if isinstance(result, dict) or result is None:
        merged: Dict[str, Any] = {}
        if isinstance(result, dict):
            merged.update(result)
        merged.update(kwargs)
        return validate_result(merged)
    raise ValueError(f"a drill result must be a mapping, got {result!r}")


def _require_result(result: Any) -> DrillResult:
    if isinstance(result, DrillResult):
        return result
    return validate_result(result)


# ---------------------------------------------------------------------
# The judge: step counts read against the held catalogue alone.
# ---------------------------------------------------------------------


def judge_result(drill_id: Any, steps_passed: Any) -> DrillResult:
    """Judge one drill run from its passed-step count alone.

    ``drill_id`` names a held drill (an unknown
    drill refuses) and ``steps_passed`` is the
    count a test run reported. The result's total
    is the drill's own held step count and its
    outcome is derived from the two counts -
    recovered only when every step passed. This
    judge runs no drill: it reads counts, as data.
    """
    held = drill_for(drill_id)
    return DrillResult(
        drill_id=held.drill_id, steps_passed=steps_passed)


def plain_words(result: Any) -> str:
    """One drill run, in plain words - its outcome stated whole.

    A recovered drill is stated as recovered in
    full; a partial walk is stated as only
    partially recovered, with its counts; a
    failed recovery is stated as not recovered.
    The outcome is never rounded up.
    """
    checked = _require_result(result)
    drill = drill_for(checked.drill_id)
    counts = f"{checked.steps_passed} of {checked.steps_total} steps passed"
    if checked.outcome == "recovered":
        return (
            f"Recovered in full: the {drill.label} drill "
            f"passed every recovery step ({counts}).")
    if checked.outcome == "partially_recovered":
        return (
            f"Only partially recovered: the {drill.label} "
            f"drill: {counts} - the recovery did "
            f"not hold whole.")
    return (
        f"Not recovered: the {drill.label} drill "
        f"{counts} - the recovery did not hold.")


# ---------------------------------------------------------------------
# The news record: one drill run, shaped as session news.
# ---------------------------------------------------------------------


def drill_record(result: Any) -> Dict[str, Any]:
    """The session-news record of one drill run.

    Every judged drill run yields a record - the
    agent layer publishes this record as a session
    event, so a drill's outcome is announced in
    plain words in its headline, never lost as a
    mere log line. The record names the drill, its
    disaster, its step counts and its outcome.
    """
    checked = _require_result(result)
    return {
        "type": "rollback_drill_run",
        "news": True,
        "slice": ROLLBACK_DRILLS_SLICE,
        "run_id": checked.run_id,
        "drill_id": checked.drill_id,
        "disaster": checked.disaster,
        "steps_passed": checked.steps_passed,
        "steps_total": checked.steps_total,
        "outcome": checked.outcome,
        "headline": plain_words(checked),
    }


# ---------------------------------------------------------------------
# The registry model: drill results held for a session, ids
# deterministic.
# ---------------------------------------------------------------------


class DrillRegistry:
    """An in-memory, storage-neutral registry of drill results.

    Results are held in the order reported. Ids
    are deterministic: a caller-supplied id is
    used as given (a duplicate refuses), and an
    unsupplied id is the next ``run-N`` in
    sequence, skipping any number a supplied id
    already took - no randomness a test cannot
    pin. Storage beyond memory is the agent
    layer's concern; this model is neutral.
    """

    def __init__(self) -> None:
        self._results: Dict[str, DrillResult] = {}
        self._next = 1

    def _fresh_id(self) -> str:
        while f"run-{self._next}" in self._results:
            self._next += 1
        run_id = f"run-{self._next}"
        self._next += 1
        return run_id

    def register(self, result: Any = None,
                 **kwargs: Any) -> DrillResult:
        """Hold one drill result, under its id or a fresh one."""
        if kwargs and isinstance(result, (DrillResult, dict)):
            validated = build_result(result, **kwargs)
        elif kwargs and result is None:
            validated = build_result(**kwargs)
        else:
            if kwargs:
                raise ValueError(
                    "a drill result is named twice: as a record "
                    "and as field words")
            validated = _require_result(result)
        if validated.run_id is None:
            validated = replace(validated, run_id=self._fresh_id())
        elif validated.run_id in self._results:
            raise ValueError(
                f"a drill run named {validated.run_id!r} "
                f"already exists")
        self._results[validated.run_id] = validated
        return validated

    def judge(self, drill_id: Any, steps_passed: Any) -> DrillResult:
        """Judge one drill run and hold its result."""
        return self.register(judge_result(drill_id, steps_passed))

    def get(self, run_id: Any) -> DrillResult:
        """The result one id names; an unknown id raises KeyError."""
        wanted = normalize_run_id(run_id)
        if wanted not in self._results:
            raise KeyError(f"unknown drill run: {wanted!r}")
        return self._results[wanted]

    def list_results(self) -> Tuple[DrillResult, ...]:
        """Every held result, in the order reported, as a tuple."""
        return tuple(self._results.values())

    def __len__(self) -> int:
        return len(self._results)

    def record(self, run_id: Any) -> Dict[str, Any]:
        """One held result's session-news record."""
        return drill_record(self.get(run_id))


# ---------------------------------------------------------------------
# The /rollback surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------


def format_drill(drill: Any) -> str:
    """One held drill, in plain words: disaster and its road."""
    current = drill if isinstance(drill, DrillDefinition) \
        else drill_for(drill)
    return (
        f"{current.drill_id}: {current.label} "
        f"({_DISASTER_LABELS[current.disaster]}; "
        f"{current.step_count} recovery steps).")


def format_drills() -> str:
    """Every held drill, in plain words, in roadmap order."""
    lines = [f"Rollback drills: {len(DRILL_CATALOGUE)} scripted."]
    for drill in DRILL_CATALOGUE:
        lines.append(f"  {format_drill(drill)}")
    return "\n".join(lines)


def format_result(result: Any) -> str:
    """One drill result, in plain words: outcome always stated."""
    current = _require_result(result)
    name = current.run_id or "run"
    return (
        f"{name}: {current.drill_id} - "
        f"{OUTCOME_PHRASES[current.outcome]} "
        f"({current.steps_passed} of {current.steps_total} "
        f"steps passed).")


def _results_from(source: Any) -> Tuple[DrillResult, ...]:
    """The results a source holds, in the order reported.

    A source is a DrillRegistry, a list of results
    (or result mappings), one result, or nothing
    at all.
    """
    if source is None:
        return ()
    if isinstance(source, DrillRegistry):
        return source.list_results()
    if isinstance(source, (DrillResult, dict)):
        return (_require_result(source),)
    if isinstance(source, (list, tuple)):
        return tuple(_require_result(item) for item in source)
    raise ValueError(
        "rollback results must be a registry or a list of results")


def format_results(source: Any = None) -> str:
    """The held drill results, in plain words, in report order.

    With no results at all the text starts with
    the plain statement of that fact. Every line
    states its result's outcome in words.
    """
    results = _results_from(source)
    if not results:
        return (
            "Rollback drills: no drill runs reported. "
            "No result is held.")
    lines = [f"Rollback drills: {len(results)} runs reported."]
    for result in results:
        lines.append(f"  {format_result(result)}")
    return "\n".join(lines)


def format_rollback_record(record: Any) -> str:
    """One drill-run news record as its plain headline."""
    if isinstance(record, dict) \
            and record.get("type") == "rollback_drill_run":
        return str(record["headline"])
    raise ValueError("format_rollback_record needs a drill record")


#: The drill record's formatter under its own name.
format_record = format_rollback_record


def format_rollback_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /rollback."""
    lines = [
        "Rollback drills (M-112) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_drills())
    lines.append("")
    lines.append(format_results(source))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


_GRAMMAR_WORDS = ("show", "drills", "run")


def parse_rollback_args(args: Any) -> Tuple[str, Optional[str]]:
    """Parse the /rollback grammar both surfaces share.

    No words (or ``show``) shows the results;
    ``show <run>`` and a bare run id show one
    result; ``drills`` shows the catalogue alone;
    ``run <drill>`` names the one held drill a
    run would exercise - a drill word that names
    no held drill is a usage error, never a run
    id. A grammar word in the wrong shape - a
    bare disaster word, a bare drill id,
    ``run`` with no drill - is a usage error
    naming the grammar, never a run id. Returns
    ``(action, target-or-None)``: for ``show``
    the target is a run id, for ``run`` it is a
    drill id.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None \
        else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() == "show":
        return ("show", None)
    if text.lower() == "drills":
        return ("drills", None)
    words = text.split()
    head = words[0].lower()
    if head == "run":
        if len(words) == 2:
            try:
                return ("run", drill_for(words[1]).drill_id)
            except ValueError:
                raise ValueError(USAGE) from None
        raise ValueError(USAGE)
    if head == "show" and len(words) == 2:
        if words[1].lower() in _GRAMMAR_WORDS:
            raise ValueError(USAGE)
        try:
            return ("show", normalize_run_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head in _GRAMMAR_WORDS or len(words) != 1:
        raise ValueError(USAGE)
    lowered = words[0].lower().replace("-", "_")
    if lowered in _DISASTER_WORDS or lowered in {
            drill.drill_id for drill in DRILL_CATALOGUE}:
        raise ValueError(USAGE)
    try:
        return ("show", normalize_run_id(words[0]))
    except ValueError:
        raise ValueError(USAGE) from None
