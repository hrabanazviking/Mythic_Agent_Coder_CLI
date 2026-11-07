"""Background tasks - managed background jobs (M-103).

Part V - Autonomy & Safety. The roadmap's words:
``long commands (builds, suites, servers) run as
managed background jobs with live output tails,
kill, and completion events into the session.``

What already shipped, and what this slice adds:

* The gap audit names ``mythic_agent/agents/tasks.py``
  as this slice's basis: a typed task lifecycle with
  budgets and cancellation - a thread-safe registry
  recording state transitions for agent tasks, with
  the states queued / running / completed / failed /
  cancelled. It executes nothing and knows nothing
  about a long command's output, its live tail, or a
  job's completion announced into the session. The
  feature census says it plainly: ``managed
  background jobs with live tails are owed.``
* This slice is that missing job layer, as a pure
  layer: a job spec (a command as data - an argv
  list, never a shell string - an optional cwd and
  label) validated as data, a job lifecycle carrying
  the tasks layer's own state words with legal
  transitions only, a bounded live output tail that
  counts the lines it drops, a kill request held as
  data, a completion record shaped as session news,
  and a small in-memory registry model with
  deterministic ids. This module runs no process,
  signals nothing, writes no file and changes no
  setting; the agent layer owns spawning the real
  subprocess for a job's argv, feeding its output
  lines into the tail, asking for a kill to be
  carried out, and publishing a completion record
  into the session.

Honesty rules, enforced here and pinned by tests:

* **A command is data, never a shell string.** A
  job's command is an argv list of non-empty text
  parts. A single string - the shape a shell would
  eval - refuses, so no job spec can smuggle in a
  command line to be interpreted later.
* **Transitions are legal or refused.** A job moves
  queued -> running -> completed / failed /
  cancelled, or queued -> cancelled. Every other
  move - finishing a job that never started,
  starting one twice, any move out of a terminal
  state - raises instead of being guessed at.
* **The tail is bounded and says what it dropped.**
  The tail keeps the newest lines within a line
  bound and a byte bound; lines pushed out are
  counted in ``dropped_lines`` and the count is
  shown wherever the tail is shown. A single line
  is never cut in the middle: a line longer than
  the byte bound is kept whole and the bound is
  applied between lines.
* **A kill is a request until it lands.** Asking
  for a kill records the request and its reason on
  the job and changes no state; the job reaches
  cancelled only when the kill is applied. This
  layer signals no process - carrying the request
  out is the agent layer's work.
* **Completion is news.** A job in a terminal state
  yields a completion record shaped as session
  news - job id, label, exit status and a one-line
  plain headline. A job that has not finished
  yields no record at all, never a premature one.
* **Malformed refuses.** An unknown state, an
  empty argv, a non-text part, an out-of-range
  tail bound, a duplicate job id and unknown keys
  in a spec mapping all raise instead of being
  skipped or guessed at.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Dict, Optional, Sequence, Tuple

__all__ = [
    "BACKGROUND_TASKS_SLICE",
    "DEFAULT_TAIL_MAX_BYTES",
    "DEFAULT_TAIL_MAX_LINES",
    "JOB_STATES",
    "LEGAL_TRANSITIONS",
    "PLAIN_EXPLANATION",
    "TERMINAL_STATES",
    "USAGE",
    "BackgroundJobRegistry",
    "Job",
    "JobSpec",
    "KillRequest",
    "append_output",
    "append_output_text",
    "apply_kill",
    "build_job",
    "build_job_spec",
    "completion_record",
    "display_label",
    "finish_job",
    "format_background",
    "format_command",
    "format_completion",
    "format_job",
    "format_jobs",
    "format_kill_request",
    "format_tail",
    "job_tail",
    "kill_job",
    "new_job",
    "normalize_job_id",
    "normalize_state",
    "parse_background_args",
    "request_kill",
    "start_job",
    "transition_job",
    "validate_job_spec",
]

BACKGROUND_TASKS_SLICE = "M-103"

#: The lifecycle states, in lifecycle order - the
#: same words ``agents/tasks.py`` uses for its typed
#: task lifecycle (its TaskState values), so a job
#: and a task are never described in two dialects.
JOB_STATES = (
    "queued",
    "running",
    "completed",
    "failed",
    "cancelled",
)

#: States a job never leaves.
TERMINAL_STATES = ("completed", "failed", "cancelled")

#: The legal moves, by state. A move not listed
#: here refuses.
LEGAL_TRANSITIONS = {
    "queued": ("running", "cancelled"),
    "running": ("completed", "failed", "cancelled"),
    "completed": (),
    "failed": (),
    "cancelled": (),
}

#: The tail bounds a job is created with when its
#: spec names none: the newest 200 lines, within
#: 64 KiB of output.
DEFAULT_TAIL_MAX_LINES = 200
DEFAULT_TAIL_MAX_BYTES = 65536

PLAIN_EXPLANATION = (
    "Background tasks are long commands - builds, "
    "test suites, servers - run as managed jobs. "
    "A job is a command given as a list of words "
    "(never a shell string), with a lifecycle in "
    "the task layer's own words: queued, running, "
    "then completed, failed or cancelled, with "
    "legal moves only. While it runs, its newest "
    "output is kept in a bounded live tail that "
    "counts the lines it drops. A kill is first a "
    "request recorded on the job, with its reason; "
    "the job is cancelled when the kill lands. "
    "When a job finishes, its completion is news "
    "for the session: the job, its label and its "
    "exit status in one plain line. This layer "
    "holds the jobs as data only; it runs no "
    "process itself."
)

USAGE = (
    "Usage: /background, /background list, "
    "/background show [<job>], /background tail [<job>], "
    "/background kill <job>, "
    "/background start <command...>"
)

_SPEC_KEYS = frozenset({"argv", "command", "cwd", "label", "name"})

_JOB_ID_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789-_.")


def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def normalize_job_id(value: Any) -> str:
    """The canonical job id a word names, or a refusal.

    A job id is one word of letters, digits, dashes,
    underscores and dots, read with its case kept
    (ids are pinned by callers and tests, so no
    reading may rename one). Anything else raises.
    """
    if isinstance(value, str):
        wanted = value.strip()
        if wanted and all(ch in _JOB_ID_CHARS for ch in wanted):
            return wanted
    raise ValueError(
        f"a job id must be a non-empty word of letters, digits, "
        f"dashes, underscores and dots, got {value!r}")


def normalize_state(value: Any) -> str:
    """The canonical lifecycle state a word names.

    State words read case-insensitively, with dashes
    read as underscores - the reading the hooks
    layer gives its event words. An unknown state
    raises.
    """
    if isinstance(value, str):
        wanted = value.strip().lower().replace("-", "_")
        if wanted in JOB_STATES:
            return wanted
    raise ValueError(
        "a job state must be one of %s, got %r"
        % ("/".join(JOB_STATES), value))


def _check_tail_bound(value: Any, what: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{what} must be a whole number, got {value!r}")
    if value < 1:
        raise ValueError(f"{what} must be at least 1, got {value!r}")
    return value


def _check_argv(value: Any) -> Tuple[str, ...]:
    """A job's command words, validated whole.

    A single string refuses outright - that is the
    shape a shell would eval, and a job's command is
    data. Every part must be non-empty text.
    """
    if isinstance(value, (str, bytes)):
        raise ValueError(
            "a job command must be an argv list of words, "
            "not a shell string")
    if not isinstance(value, (list, tuple)):
        raise ValueError(
            f"a job command must be an argv list, got {value!r}")
    parts = tuple(value)
    if not parts:
        raise ValueError("a job command needs at least one word")
    cleaned = []
    for part in parts:
        if not isinstance(part, str) or not part.strip():
            raise ValueError(
                f"a job command word must be non-empty text, "
                f"got {part!r}")
        cleaned.append(part.strip())
    return tuple(cleaned)


# ---------------------------------------------------------------------
# The job spec: one command, as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class JobSpec:
    """One background job's command, as data.

    ``argv`` is the command as a list of words -
    never a shell string. ``cwd`` is the directory
    the agent layer will run it in, or None for the
    session's own directory. ``label`` is the short
    human name reports use; when it is empty the
    command itself is the label.

    Constructing one validates it, so a JobSpec that
    exists is a command the agent layer could run.
    """

    argv: Tuple[str, ...]
    cwd: Optional[str] = None
    label: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "argv", _check_argv(self.argv))
        if self.cwd is not None:
            object.__setattr__(
                self, "cwd", _clean_text(self.cwd, "a job cwd"))
        if not isinstance(self.label, str):
            raise ValueError(
                f"a job label must be text, got {self.label!r}")
        object.__setattr__(self, "label", self.label.strip())

    @property
    def command_text(self) -> str:
        """The command as one display line (display only)."""
        return " ".join(self.argv)

    @property
    def display_label(self) -> str:
        return self.label or self.command_text

    def to_record(self) -> Dict[str, Any]:
        return {
            "argv": list(self.argv),
            "cwd": self.cwd,
            "label": self.label,
        }


def display_label(spec: Any) -> str:
    """The name reports use for one spec: label or command."""
    return _coerce_spec(spec).display_label


def format_command(spec: Any) -> str:
    """One spec's command as a display line."""
    return _coerce_spec(spec).command_text


def validate_job_spec(spec: Any) -> JobSpec:
    """Validate one job spec into a JobSpec.

    Accepts a JobSpec or a mapping naming an ``argv``
    (or ``command``) list, an optional ``cwd``, and
    an optional ``label`` (or ``name``). Naming both
    spellings of one field with different values
    refuses, and unknown keys refuse - a spec is
    never repaired by guessing.
    """
    if isinstance(spec, JobSpec):
        return spec
    if not isinstance(spec, dict):
        raise ValueError(f"a job spec must be a mapping, got {spec!r}")
    unknown = set(spec) - _SPEC_KEYS
    if unknown:
        raise ValueError(
            "unknown job spec keys: %s" % ", ".join(sorted(unknown)))
    if "argv" in spec and "command" in spec \
            and spec["argv"] != spec["command"]:
        raise ValueError("a job spec names two different commands")
    if "argv" not in spec and "command" not in spec:
        raise ValueError("a job spec is missing its argv command")
    argv = spec["argv"] if "argv" in spec else spec["command"]
    if "label" in spec and "name" in spec \
            and spec["label"] != spec["name"]:
        raise ValueError("a job spec names two different labels")
    label = ""
    if "label" in spec:
        label = spec["label"]
    elif "name" in spec:
        label = spec["name"]
    return JobSpec(argv=argv, cwd=spec.get("cwd"), label=label)


def build_job_spec(argv: Any, cwd: Any = None,
                   label: Any = "") -> JobSpec:
    """Build one validated job spec from its pieces."""
    return JobSpec(argv=argv, cwd=cwd, label=label)


def _coerce_spec(spec: Any) -> JobSpec:
    """A spec from a JobSpec, a mapping, or a bare argv list.

    The bare-list form is the command itself, with
    no cwd and no label. Anything else goes through
    :func:`validate_job_spec`, which refuses it.
    """
    if isinstance(spec, JobSpec):
        return spec
    if isinstance(spec, (list, tuple)):
        return build_job_spec(spec)
    return validate_job_spec(spec)


# ---------------------------------------------------------------------
# The kill request: a request, as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class KillRequest:
    """A kill asked for, as data.

    ``requested`` says a kill was asked for at all;
    ``reason`` is the asker's own words, possibly
    empty. Recording a request changes no state -
    the job is cancelled only when the kill lands
    (:func:`apply_kill`), and the agent layer owns
    signalling the real process in between.
    """

    requested: bool = False
    reason: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.requested, bool):
            raise ValueError(
                f"a kill request flag must be true or false, "
                f"got {self.requested!r}")
        if not isinstance(self.reason, str):
            raise ValueError(
                f"a kill reason must be text, got {self.reason!r}")
        object.__setattr__(self, "reason", self.reason.strip())
        if self.reason and not self.requested:
            raise ValueError(
                "a kill reason with no kill requested is not a request")

    @property
    def active(self) -> bool:
        return self.requested

    def to_record(self) -> Dict[str, Any]:
        return {"requested": self.requested, "reason": self.reason}


# ---------------------------------------------------------------------
# The job: one managed background job, as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class Job:
    """One background job and everything known about it.

    A Job is an immutable snapshot: every change -
    a transition, an output line, a kill request -
    is a pure function returning the new Job, so a
    registry (or a test) holds exactly the history
    it kept. ``tail_lines`` is the live tail's kept
    lines, newest last; ``dropped_lines`` counts
    the lines the bounded tail pushed out.
    """

    job_id: str
    spec: JobSpec
    state: str = "queued"
    exit_code: Optional[int] = None
    kill: KillRequest = field(default_factory=KillRequest)
    tail_lines: Tuple[str, ...] = ()
    dropped_lines: int = 0
    tail_max_lines: int = DEFAULT_TAIL_MAX_LINES
    tail_max_bytes: int = DEFAULT_TAIL_MAX_BYTES

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "job_id", normalize_job_id(self.job_id))
        if not isinstance(self.spec, JobSpec):
            object.__setattr__(self, "spec", _coerce_spec(self.spec))
        object.__setattr__(self, "state", normalize_state(self.state))
        if self.exit_code is not None:
            if isinstance(self.exit_code, bool) \
                    or not isinstance(self.exit_code, int):
                raise ValueError(
                    f"a job exit code must be a whole number, "
                    f"got {self.exit_code!r}")
            if self.state in ("queued", "running"):
                raise ValueError(
                    f"a {self.state} job has no exit code yet")
            if self.state == "completed" and self.exit_code != 0:
                raise ValueError(
                    "a completed job's exit code is 0, "
                    f"got {self.exit_code!r}")
            if self.state == "failed" and self.exit_code == 0:
                raise ValueError(
                    "a failed job's exit code is not 0")
            if self.state == "cancelled":
                raise ValueError("a cancelled job has no exit code")
        if not isinstance(self.kill, KillRequest):
            raise ValueError(
                f"a job's kill must be a KillRequest, got {self.kill!r}")
        if isinstance(self.tail_lines, (str, bytes)) \
                or not isinstance(self.tail_lines, (list, tuple)):
            raise ValueError("a job's tail lines must be a list of lines")
        lines = []
        for line in self.tail_lines:
            if not isinstance(line, str):
                raise ValueError(
                    f"a tail line must be text, got {line!r}")
            lines.append(line)
        object.__setattr__(self, "tail_lines", tuple(lines))
        if isinstance(self.dropped_lines, bool) \
                or not isinstance(self.dropped_lines, int) \
                or self.dropped_lines < 0:
            raise ValueError(
                f"a dropped-line count must be a whole number "
                f"of 0 or more, got {self.dropped_lines!r}")
        object.__setattr__(
            self, "tail_max_lines",
            _check_tail_bound(self.tail_max_lines, "a tail line bound"))
        object.__setattr__(
            self, "tail_max_bytes",
            _check_tail_bound(self.tail_max_bytes, "a tail byte bound"))
        if len(self.tail_lines) > self.tail_max_lines:
            raise ValueError(
                "a job's tail holds more lines than its bound allows")

    @property
    def label(self) -> str:
        """The name reports use: the spec's label or its command."""
        return self.spec.display_label

    @property
    def is_terminal(self) -> bool:
        return self.state in TERMINAL_STATES

    @property
    def kill_requested(self) -> bool:
        return self.kill.requested

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "background_job",
            "slice": BACKGROUND_TASKS_SLICE,
            "job_id": self.job_id,
            "argv": list(self.spec.argv),
            "cwd": self.spec.cwd,
            "label": self.spec.label,
            "state": self.state,
            "exit_code": self.exit_code,
            "kill": self.kill.to_record(),
            "tail": list(self.tail_lines),
            "dropped_lines": self.dropped_lines,
        }


def build_job(job_id: Any, spec: Any, **kwargs: Any) -> Job:
    """Build one validated queued job from its pieces."""
    return Job(job_id=job_id, spec=_coerce_spec(spec), **kwargs)


#: The creating name alongside build_job.
new_job = build_job


# ---------------------------------------------------------------------
# Lifecycle: legal moves only, each a new Job.
# ---------------------------------------------------------------------


def _require_job(job: Any) -> Job:
    if not isinstance(job, Job):
        raise ValueError(f"a background job is needed, got {job!r}")
    return job


def transition_job(job: Any, state: Any,
                   exit_code: Any = None) -> Job:
    """Move one job to a new state, or refuse.

    The move must be listed in ``LEGAL_TRANSITIONS``
    for the job's current state; anything else
    raises, naming both states. An exit code rides
    only a completing or failing move and must
    agree with it (0 completes, non-zero fails).
    """
    current = _require_job(job)
    wanted = normalize_state(state)
    if wanted not in LEGAL_TRANSITIONS[current.state]:
        raise ValueError(
            f"a {current.state} job cannot become {wanted}")
    if wanted in ("completed", "failed"):
        if isinstance(exit_code, bool) \
                or not isinstance(exit_code, int):
            raise ValueError(
                f"finishing a job needs its exit code, got {exit_code!r}")
        if wanted == "completed" and exit_code != 0:
            raise ValueError(
                f"exit code {exit_code!r} does not complete a job")
        if wanted == "failed" and exit_code == 0:
            raise ValueError("exit code 0 does not fail a job")
        return replace(current, state=wanted, exit_code=exit_code)
    if exit_code is not None:
        raise ValueError(
            f"a move to {wanted} carries no exit code")
    return replace(current, state=wanted)


def start_job(job: Any) -> Job:
    """Move a queued job to running."""
    return transition_job(job, "running")


def finish_job(job: Any, exit_code: Any) -> Job:
    """Finish a running job from its exit code, mechanically.

    Exit 0 completes the job; any other exit code
    fails it - the same mechanical reading the hooks
    layer gives a finished run. A non-integer exit
    code raises: a run with no readable exit code is
    never judged by guessing.
    """
    current = _require_job(job)
    if isinstance(exit_code, bool) or not isinstance(exit_code, int):
        raise ValueError(
            f"a job exit code must be a whole number, got {exit_code!r}")
    wanted = "completed" if exit_code == 0 else "failed"
    return transition_job(current, wanted, exit_code=exit_code)


def request_kill(job: Any, reason: Any = "") -> Job:
    """Record a kill request on a live job; no state changes.

    Only a queued or running job can be asked to
    die - a finished job refuses - and a second
    request refuses rather than rewriting the first
    request's reason.
    """
    current = _require_job(job)
    if current.is_terminal:
        raise ValueError(
            f"a {current.state} job cannot be killed; it already ended")
    if current.kill.requested:
        raise ValueError(
            f"a kill was already requested for job {current.job_id}")
    if not isinstance(reason, str):
        raise ValueError(f"a kill reason must be text, got {reason!r}")
    return replace(
        current, kill=KillRequest(requested=True, reason=reason.strip()))


def apply_kill(job: Any) -> Job:
    """Land a requested kill: the job becomes cancelled.

    Without a recorded request this refuses - a job
    is never cancelled in this layer by anything
    but a kill that was asked for, or a transition
    the caller names outright.
    """
    current = _require_job(job)
    if not current.kill.requested:
        raise ValueError(
            f"no kill was requested for job {current.job_id}")
    return transition_job(current, "cancelled")


def kill_job(job: Any, reason: Any = "") -> Job:
    """Ask for a kill and land it in one move: request + cancelled."""
    return apply_kill(request_kill(job, reason))


# ---------------------------------------------------------------------
# The live tail: bounded, and honest about what it dropped.
# ---------------------------------------------------------------------


def _tail_size(lines: Sequence[str]) -> int:
    return sum(len(line.encode("utf-8")) + 1 for line in lines)


def append_output(job: Any, line: Any) -> Job:
    """Append one output line to a running job's tail.

    The line is stored without its trailing newline.
    Lines beyond the line bound, or beyond the byte
    bound, are pushed out oldest-first and counted
    in ``dropped_lines``; a single line is never cut
    (a line longer than the byte bound is kept whole
    and the bound applies between lines). Only a
    running job produces output - appending to a
    queued or finished job raises.
    """
    current = _require_job(job)
    if current.state != "running":
        raise ValueError(
            f"a {current.state} job produces no output; "
            "only a running job's tail grows")
    if not isinstance(line, str):
        raise ValueError(f"a tail line must be text, got {line!r}")
    lines = list(current.tail_lines)
    lines.append(line.rstrip("\n"))
    dropped = current.dropped_lines
    while len(lines) > 1 and (
            len(lines) > current.tail_max_lines
            or _tail_size(lines) > current.tail_max_bytes):
        lines.pop(0)
        dropped += 1
    if len(lines) > current.tail_max_lines:
        overflow = len(lines) - current.tail_max_lines
        lines = lines[overflow:]
        dropped += overflow
    return replace(
        current, tail_lines=tuple(lines), dropped_lines=dropped)


def append_output_text(job: Any, text: Any) -> Job:
    """Append a block of output text, line by line."""
    current = _require_job(job)
    if not isinstance(text, str):
        raise ValueError(f"job output must be text, got {text!r}")
    for line in text.splitlines():
        current = append_output(current, line)
    return current


def job_tail(job: Any, count: Any = None) -> Tuple[str, ...]:
    """The newest ``count`` kept lines (all kept lines by default)."""
    current = _require_job(job)
    if count is None:
        return current.tail_lines
    if isinstance(count, bool) or not isinstance(count, int) or count < 1:
        raise ValueError(
            f"a tail count must be a whole number of 1 or more, "
            f"got {count!r}")
    return current.tail_lines[-count:]


# ---------------------------------------------------------------------
# Completion, shaped as session news.
# ---------------------------------------------------------------------


def format_completion(job: Any) -> str:
    """One finished job's headline, in plain words.

    A job that has not reached a terminal state has
    no completion headline and raises, exactly as a
    verdict that does not block has no block headline.
    """
    current = _require_job(job)
    if not current.is_terminal:
        raise ValueError(
            f"job {current.job_id} is {current.state}; "
            "it has not finished, so there is no completion")
    label = current.label
    if current.state == "completed":
        return (
            f"Background job {current.job_id} ({label}) "
            f"finished: completed (exit {current.exit_code}).")
    if current.state == "failed":
        return (
            f"Background job {current.job_id} ({label}) "
            f"finished: failed (exit {current.exit_code}).")
    if current.kill.requested:
        reason = f" - {current.kill.reason}" if current.kill.reason else ""
        return (
            f"Background job {current.job_id} ({label}) "
            f"was killed{reason}.")
    return f"Background job {current.job_id} ({label}) was cancelled."


def completion_record(job: Any) -> Optional[Dict[str, Any]]:
    """The session-news record of one finished job, or None.

    A job that has not finished returns None - the
    agent layer publishes this record as a session
    event when it is not None, so a completion can
    never be lost as a mere log line, and never
    announced before it happens.
    """
    current = _require_job(job)
    if not current.is_terminal:
        return None
    return {
        "type": "background_job_completed",
        "news": True,
        "surface": "session_event",
        "slice": BACKGROUND_TASKS_SLICE,
        "job_id": current.job_id,
        "label": current.label,
        "state": current.state,
        "exit_code": current.exit_code,
        "headline": format_completion(current),
    }


def format_kill_request(job: Any) -> str:
    """One job's kill request, in plain words."""
    current = _require_job(job)
    if not current.kill.requested:
        return f"No kill has been requested for job {current.job_id}."
    reason = f" - {current.kill.reason}" if current.kill.reason else ""
    return f"Kill requested for job {current.job_id} ({current.label}){reason}."


# ---------------------------------------------------------------------
# The registry model: jobs held in creation order, ids deterministic.
# ---------------------------------------------------------------------


class BackgroundJobRegistry:
    """An in-memory registry of background jobs.

    Jobs are held in creation order and replaced,
    never mutated, as they change. Ids are
    deterministic: a caller-supplied id is used as
    given (a duplicate refuses), and an unsupplied
    id is the next ``job-N`` in sequence, skipping
    any number a supplied id already took - no
    randomness a test cannot pin. Storage beyond
    memory (a session's journal, a file) is the
    agent layer's concern; this model is neutral.
    """

    def __init__(self) -> None:
        self._jobs: Dict[str, Job] = {}
        self._next = 1

    def _fresh_id(self) -> str:
        while f"job-{self._next}" in self._jobs:
            self._next += 1
        job_id = f"job-{self._next}"
        self._next += 1
        return job_id

    def create(self, spec: Any, job_id: Any = None, **kwargs: Any) -> Job:
        """Create a queued job and hold it; duplicate ids refuse."""
        validated = _coerce_spec(spec)
        if job_id is None:
            job_id = self._fresh_id()
        else:
            job_id = normalize_job_id(job_id)
            if job_id in self._jobs:
                raise ValueError(f"a job named {job_id!r} already exists")
        job = Job(job_id=job_id, spec=validated, **kwargs)
        self._jobs[job.job_id] = job
        return job

    def get(self, job_id: Any) -> Job:
        """The job one id names; an unknown id raises KeyError."""
        wanted = normalize_job_id(job_id)
        if wanted not in self._jobs:
            raise KeyError(f"unknown background job: {wanted!r}")
        return self._jobs[wanted]

    def list_jobs(self, state: Any = None) -> Tuple[Job, ...]:
        """Every held job, in creation order, optionally by state."""
        jobs = tuple(self._jobs.values())
        if state is None:
            return jobs
        wanted = normalize_state(state)
        return tuple(job for job in jobs if job.state == wanted)

    def _store(self, job: Job) -> Job:
        self._jobs[job.job_id] = job
        return job

    def start(self, job_id: Any) -> Job:
        return self._store(start_job(self.get(job_id)))

    def append_output(self, job_id: Any, line: Any) -> Job:
        return self._store(append_output(self.get(job_id), line))

    def append_output_text(self, job_id: Any, text: Any) -> Job:
        return self._store(append_output_text(self.get(job_id), text))

    def request_kill(self, job_id: Any, reason: Any = "") -> Job:
        return self._store(request_kill(self.get(job_id), reason))

    def apply_kill(self, job_id: Any) -> Job:
        return self._store(apply_kill(self.get(job_id)))

    def kill(self, job_id: Any, reason: Any = "") -> Job:
        return self._store(kill_job(self.get(job_id), reason))

    def finish(self, job_id: Any, exit_code: Any) -> Job:
        return self._store(finish_job(self.get(job_id), exit_code))

    def completion_record(self, job_id: Any) -> Optional[Dict[str, Any]]:
        return completion_record(self.get(job_id))


# ---------------------------------------------------------------------
# The /background surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------


def format_job(job: Any) -> str:
    """One job, in plain words, from the job."""
    current = _require_job(job)
    exit_part = f", exit {current.exit_code}" \
        if current.exit_code is not None else ""
    kill_part = ", kill requested" if current.kill.requested else ""
    return (
        f"{current.job_id}: {current.label} [{current.state}"
        f"{exit_part}{kill_part}] - {current.spec.command_text}")


def format_jobs(jobs: Any = None) -> str:
    """The jobs, in plain words, in the order given.

    With no jobs at all the text starts with the
    plain statement of that fact.
    """
    if jobs is None:
        selected: Tuple[Job, ...] = ()
    elif isinstance(jobs, BackgroundJobRegistry):
        selected = jobs.list_jobs()
    else:
        if isinstance(jobs, (str, bytes)) \
                or not isinstance(jobs, (list, tuple)):
            raise ValueError("background jobs must be a list of jobs")
        selected = tuple(_require_job(job) for job in jobs)
    if not selected:
        return (
            "Background jobs: none. No long command is "
            "running as a managed job.")
    lines = [f"Background jobs: {len(selected)} held."]
    for job in selected:
        lines.append(f"  {format_job(job)}")
    return "\n".join(lines)


def format_tail(job: Any, count: Any = 10) -> str:
    """One job's live tail, in plain words.

    The kept lines, newest last, with the dropped
    count stated whenever lines were pushed out -
    the tail never pretends to be the whole output.
    """
    current = _require_job(job)
    lines = job_tail(current, count)
    header = (
        f"Tail of job {current.job_id} ({current.label}) "
        f"[{current.state}]:")
    notes = []
    if current.dropped_lines:
        notes.append(
            f"{current.dropped_lines} earlier line(s) dropped "
            "by the bounded tail")
    if len(lines) < len(current.tail_lines):
        notes.append(
            f"showing the newest {len(lines)} of "
            f"{len(current.tail_lines)} kept lines")
    out = [header]
    if notes:
        out.append("  (" + "; ".join(notes) + ")")
    if lines:
        out.extend(f"  {line}" for line in lines)
    else:
        out.append("  (no output yet)")
    return "\n".join(out)


def format_background(jobs: Any = None) -> str:
    """The whole slice, in plain words, for /background."""
    lines = ["Background tasks (M-103) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_jobs(jobs))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_background_args(args: Any) -> Tuple[str, Optional[str]]:
    """Parse the /background grammar both surfaces share.

    No words (or ``list`` / ``show``) shows the jobs;
    ``show <job>`` and a bare job id show one job;
    ``tail [<job>]`` asks for one job's tail (no id
    means the newest job, which the agent layer
    resolves); ``kill <job>`` asks for a kill;
    ``start <command...>`` carries the command words
    as one string for the agent layer to split into
    argv - never to run through a shell. Anything
    else is a usage error naming the grammar.
    Returns ``(action, job-id-or-text-or-None)``.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None \
        else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() in ("list", "show"):
        return ("show", None)
    words = text.split()
    head = words[0].lower()
    if head == "start":
        if len(words) < 2:
            raise ValueError(USAGE)
        return ("start", text.split(None, 1)[1])
    if head == "show" and len(words) == 2:
        try:
            return ("show", normalize_job_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "tail" and len(words) == 1:
        return ("tail", None)
    if head == "tail" and len(words) == 2:
        try:
            return ("tail", normalize_job_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "kill" and len(words) == 2:
        try:
            return ("kill", normalize_job_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head in ("show", "list", "tail", "kill", "start"):
        # A grammar word in the wrong shape is a usage
        # error, never a job id that happens to spell one.
        raise ValueError(USAGE)
    if len(words) == 1:
        try:
            return ("show", normalize_job_id(words[0]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
