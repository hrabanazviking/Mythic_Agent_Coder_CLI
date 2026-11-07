"""Headless fleet mode - ``mythic run`` grown for CI, as data (M-106).

Part V - Autonomy & Safety. The roadmap's words:
``'`mythic run` grown for CI - parallel tasks
across repos, machine-readable verdicts, artefact
bundles, honest exit codes; a fleet run is
resumable.'``

What already shipped, and what this slice adds:

* The ``mythic run`` road already exists for one
  task: ``mythic_agent/cli.py`` gives it a single
  prompt (a positional word, read from stdin when
  omitted), a ``--workspace`` project directory, a
  ``--model`` / ``--base-url`` override, a
  ``--resume`` session id, a ``--permission``
  posture and a ``--format`` of plain, json or
  jsonl; ``mythic_agent/terminal.py``'s
  ``run_once`` carries one such task out and
  ``_render_result`` judges it with the house exit
  codes - completed 0, failed 1, invalid input 2,
  approval required 3, cancelled 130. Nothing in
  the tree holds *many* such tasks at once: a
  fleet of headless runs across repos, with one
  machine-readable verdict for the whole fleet,
  the artefacts each task produced named as data,
  and a record of what a resumed run still owes.
* The M-103 background tasks layer holds one long
  command as a managed job - an argv list, never
  a shell string - and the M-105 scheduled work
  layer holds a cron-style job the same way. This
  slice is the missing fleet layer, as a pure
  layer in their exact shape: a fleet task (what
  to run - an argv list, never a shell string -
  in which repo, with the prompt the ``mythic
  run`` road itself names) validated as data, a
  per-task verdict as data, a fleet verdict that
  aggregates the per-task verdicts mechanically,
  honest exit codes as a pure function of those
  verdicts, an artefact bundle as data (names
  only - this module writes nothing), a resume
  plan as data, and a small in-memory registry
  model with deterministic ids. This module
  starts no process, writes no file and changes
  no setting; the agent layer owns spawning the
  real headless runs in parallel, feeding real
  verdicts and artefact names in, carrying the
  fleet's exit code out to the process exit, and
  carrying a resume plan out in the world.

Honesty rules, enforced here and pinned by tests:

* **A task is data, never a shell string.** A
  task's argv is a list of non-empty text words.
  A single string - the shape a shell would eval
  - bytes, an empty list, a blank word and a
  non-text word all refuse outright, exactly as
  M-103 and M-105 refuse them, so no fleet task
  can smuggle in a command line to be interpreted
  later.
* **Verdicts are data, and they agree with
  themselves.** A per-task verdict names one of
  the status words queued / running / passed /
  failed / error / skipped. A queued, running or
  skipped task carries no exit code; a passed
  task's exit code, when one is named, is 0; a
  failed task's is never 0. A verdict that
  contradicts itself refuses instead of being
  guessed at.
* **The exit code is mechanical and honest.** It
  is a pure function of the verdicts, in the
  ``mythic run`` road's own mapping
  (``terminal._render_result``: completed 0,
  failed 1, invalid input 2): 0 only when every
  task in the fleet passed - and a fleet with no
  tasks never earns a 0; 1 when a task ran and
  failed and none errored; 2 when a task errored
  or the fleet is unfinished (a task queued,
  running, skipped or missing its verdict, or no
  tasks at all). A failed task can therefore
  never yield 0, and an unfinished fleet can
  never claim success.
* **An artefact bundle names names only.** A
  bundle lists artefact names for one task, as
  data. A name that is absolute, or that carries
  a ``..`` path segment, refuses plainly - a
  bundle can never point outside the place its
  artefacts belong. This layer writes nothing.
* **A passed task is never re-run.** A resume
  plan is computed from the recorded verdicts
  alone: passed tasks are listed as passed and
  never as remaining; queued, running, skipped
  and verdictless tasks remain; failed and error
  tasks remain only when the caller explicitly
  asks to retry failures, and are otherwise held
  back and named as held back.
* **Status is never carried by colour or symbol
  alone.** Every formatter states a task's and
  the fleet's state in words, and the fleet
  verdict's line always states its exit code.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Dict, Optional, Tuple

__all__ = [
    "EXIT_ERROR",
    "EXIT_FAILED",
    "EXIT_OK",
    "FLEET_MODE_SLICE",
    "FLEET_STATUSES",
    "PLAIN_EXPLANATION",
    "TASK_STATUSES",
    "USAGE",
    "ArtefactBundle",
    "FleetRegistry",
    "FleetRun",
    "FleetTask",
    "FleetVerdict",
    "ResumePlan",
    "TaskVerdict",
    "build_artefact_bundle",
    "build_fleet_run",
    "build_fleet_task",
    "build_task_verdict",
    "fleet_exit_code",
    "format_artefact_bundle",
    "format_fleet_mode",
    "format_fleet_run",
    "format_fleet_task",
    "format_fleet_tasks",
    "format_fleet_verdict",
    "format_resume_plan",
    "format_resume_record",
    "judge_fleet",
    "normalize_artefact_name",
    "normalize_task_id",
    "normalize_verdict_status",
    "parse_fleet_args",
    "plan_resume",
    "resume_record",
    "validate_artefact_bundle",
    "validate_fleet_run",
    "validate_fleet_task",
    "validate_task_verdict",
]

FLEET_MODE_SLICE = "M-106"

#: The per-task verdict status words, in lifecycle
#: order. Passed / failed / error are the finished
#: readings a headless run can earn; queued and
#: running are unfinished; skipped was not run.
TASK_STATUSES = (
    "queued", "running", "passed", "failed", "error", "skipped",
)

#: The fleet verdict status words.
FLEET_STATUSES = ("passed", "failed", "error", "incomplete")

#: Honest exit codes, in the ``mythic run`` road's
#: own mapping (``terminal._render_result``:
#: completed 0, failed 1, invalid input 2). The
#: fleet reading: 0 only when every task passed,
#: 1 when a task failed, 2 when a task errored or
#: the fleet is unfinished.
EXIT_OK = 0
EXIT_FAILED = 1
EXIT_ERROR = 2

_EXIT_FOR_STATUS = {
    "passed": EXIT_OK,
    "failed": EXIT_FAILED,
    "error": EXIT_ERROR,
    "incomplete": EXIT_ERROR,
}

PLAIN_EXPLANATION = (
    "Fleet mode is the headless 'mythic run' road "
    "grown for CI: many tasks held as data - what "
    "to run (a command as a list of words, never a "
    "shell string), in which repo, with the prompt "
    "the run names - run in parallel across repos, "
    "each earning a verdict as data (queued, "
    "running, passed, failed, error or skipped). "
    "The fleet verdict is mechanical, and its exit "
    "code honest, in the mythic run road's own "
    "mapping: 0 only when every task passed, 1 when "
    "a task ran and failed, 2 when a task errored "
    "or the fleet is unfinished - a failed task "
    "can never yield 0. Each task's artefacts are "
    "named in a bundle, as data only. A fleet run "
    "is resumable: the resume plan lists what "
    "remains from the recorded verdicts, and a "
    "passed task is never run again. This layer "
    "holds the tasks, verdicts, bundles and resume "
    "plans as data only; it starts no process and "
    "runs nothing itself."
)

USAGE = (
    "Usage: /fleet, /fleet show, "
    "/fleet show <task>, /fleet verdict, "
    "/fleet resume"
)

_TASK_KEYS = frozenset({
    "task_id", "id", "label", "name", "argv", "command",
    "cwd", "repo", "workspace", "prompt",
})

_VERDICT_KEYS = frozenset({
    "task_id", "id", "label", "name", "status", "state",
    "exit_code", "detail", "message",
})

_BUNDLE_KEYS = frozenset({
    "task_id", "id", "artefacts", "artifacts",
    "artefact_names", "names",
})

_RUN_KEYS = frozenset({"label", "name", "tasks"})

_TASK_ID_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789-_.")


def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def normalize_task_id(value: Any) -> str:
    """The canonical fleet task id a word names.

    A task id is one word of letters, digits,
    dashes, underscores and dots, read with its
    case kept. Anything else raises.
    """
    if isinstance(value, str):
        wanted = value.strip()
        if wanted and all(ch in _TASK_ID_CHARS for ch in wanted):
            return wanted
    raise ValueError(
        f"a fleet task id must be a non-empty word of letters, "
        f"digits, dashes, underscores and dots, got {value!r}")


def normalize_verdict_status(value: Any) -> str:
    """The canonical per-task verdict status a word names."""
    if isinstance(value, str):
        wanted = value.strip().lower().replace("-", "_")
        if wanted in TASK_STATUSES:
            return wanted
    raise ValueError(
        "a fleet task status must be one of %s, got %r"
        % ("/".join(TASK_STATUSES), value))


def _check_argv(value: Any) -> Tuple[str, ...]:
    """A task's command words, validated whole (M-103's rule)."""
    if isinstance(value, (str, bytes)):
        raise ValueError(
            "a fleet task command must be an argv list of "
            "words, not a shell string")
    if not isinstance(value, (list, tuple)):
        raise ValueError(
            f"a fleet task command must be an argv list, "
            f"got {value!r}")
    parts = tuple(value)
    if not parts:
        raise ValueError("a fleet task command needs at least one word")
    cleaned = []
    for part in parts:
        if not isinstance(part, str) or not part.strip():
            raise ValueError(
                f"a fleet task command word must be non-empty "
                f"text, got {part!r}")
        cleaned.append(part.strip())
    return tuple(cleaned)


def _check_exit_code(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(
            f"a fleet task exit code must be a whole number, "
            f"got {value!r}")
    return value


def _pick(mapping: Dict[str, Any], names: Tuple[str, ...],
          what: str) -> Any:
    """One field from its spellings, or a refusal on conflict."""
    found = [name for name in names if name in mapping]
    if not found:
        return None
    first = mapping[found[0]]
    for name in found[1:]:
        if mapping[name] != first:
            raise ValueError(f"a fleet record names two different {what}")
    return first


# ---------------------------------------------------------------------
# The fleet task: one headless run, as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class FleetTask:
    """One headless task in a fleet, as data.

    ``argv`` is what to run, as a list of words -
    never a shell string. ``cwd`` is the repo the
    task runs in (the ``mythic run`` road's
    ``--workspace``), or None for the caller's own
    directory. ``prompt`` is the task prompt the
    ``mythic run`` road itself names - its single
    positional prompt word - or None when the argv
    alone is the task. ``label`` is the short human
    name reports use; when empty the command itself
    is the label.

    Constructing one validates it, so a FleetTask
    that exists is a task the agent layer could run.
    """

    label: str = ""
    argv: Tuple[str, ...] = ()
    task_id: Optional[str] = None
    cwd: Optional[str] = None
    prompt: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "argv", _check_argv(self.argv))
        if not isinstance(self.label, str):
            raise ValueError(
                f"a fleet task label must be text, got {self.label!r}")
        object.__setattr__(self, "label", self.label.strip())
        if self.task_id is not None:
            object.__setattr__(
                self, "task_id", normalize_task_id(self.task_id))
        if self.cwd is not None:
            object.__setattr__(
                self, "cwd", _clean_text(self.cwd, "a fleet task repo"))
        if self.prompt is not None:
            object.__setattr__(
                self, "prompt",
                _clean_text(self.prompt, "a fleet task prompt"))

    @property
    def command_text(self) -> str:
        """The command as one display line (display only)."""
        return " ".join(self.argv)

    @property
    def display_label(self) -> str:
        return self.label or self.command_text

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "fleet_task",
            "slice": FLEET_MODE_SLICE,
            "task_id": self.task_id,
            "label": self.label,
            "argv": list(self.argv),
            "cwd": self.cwd,
            "prompt": self.prompt,
        }


def validate_fleet_task(task: Any) -> FleetTask:
    """Validate one fleet task into a FleetTask.

    Accepts a FleetTask or a mapping naming an
    ``argv`` (or ``command``) list, an optional
    ``label`` (or ``name``), ``task_id`` (or
    ``id``), a repo as ``cwd`` (or ``repo`` /
    ``workspace`` - the ``mythic run`` road's own
    word), and an optional ``prompt``. Naming two
    spellings of one field with different values
    refuses, and unknown keys refuse.
    """
    if isinstance(task, FleetTask):
        return task
    if not isinstance(task, dict):
        raise ValueError(
            f"a fleet task must be a mapping, got {task!r}")
    unknown = set(task) - _TASK_KEYS
    if unknown:
        raise ValueError(
            "unknown fleet task keys: %s"
            % ", ".join(sorted(unknown)))
    if "argv" not in task and "command" not in task:
        raise ValueError("a fleet task is missing its argv command")
    argv = _pick(task, ("argv", "command"), "commands")
    label = _pick(task, ("label", "name"), "labels")
    task_id = _pick(task, ("task_id", "id"), "task ids")
    cwd = _pick(task, ("cwd", "repo", "workspace"), "repos")
    kwargs: Dict[str, Any] = {
        "label": label if label is not None else "", "argv": argv,
    }
    if task_id is not None:
        kwargs["task_id"] = task_id
    if cwd is not None:
        kwargs["cwd"] = cwd
    if "prompt" in task:
        kwargs["prompt"] = task["prompt"]
    return FleetTask(**kwargs)


def build_fleet_task(task: Any = None, **kwargs: Any) -> FleetTask:
    """Build one validated fleet task from a mapping or field words."""
    if isinstance(task, FleetTask) and not kwargs:
        return task
    if isinstance(task, dict) or task is None:
        merged: Dict[str, Any] = {}
        if isinstance(task, dict):
            merged.update(task)
        merged.update(kwargs)
        return validate_fleet_task(merged)
    raise ValueError(
        f"a fleet task must be a mapping, got {task!r}")


def _require_task(task: Any) -> FleetTask:
    if isinstance(task, FleetTask):
        return task
    return validate_fleet_task(task)


# ---------------------------------------------------------------------
# The per-task verdict: one task judged, as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class TaskVerdict:
    """One fleet task's verdict, as data.

    ``status`` is one of the TASK_STATUSES words.
    ``exit_code`` is the headless run's own exit
    code when the task finished: a queued, running
    or skipped task carries none, a passed task's
    is 0 when named, and a failed task's is never
    0. ``detail`` is the run's own plain words
    about the outcome, possibly empty.

    Constructing one validates it, so a verdict
    that exists never contradicts itself.
    """

    task_id: Optional[str] = None
    label: str = ""
    status: str = "queued"
    exit_code: Optional[int] = None
    detail: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "task_id", normalize_task_id(self.task_id))
        if not isinstance(self.label, str):
            raise ValueError(
                f"a verdict label must be text, got {self.label!r}")
        object.__setattr__(self, "label", self.label.strip())
        object.__setattr__(
            self, "status", normalize_verdict_status(self.status))
        object.__setattr__(
            self, "exit_code", _check_exit_code(self.exit_code))
        if self.status in ("queued", "running", "skipped") \
                and self.exit_code is not None:
            raise ValueError(
                f"a {self.status} task has no exit code yet, "
                f"got {self.exit_code!r}")
        if self.status == "passed" and self.exit_code not in (None, 0):
            raise ValueError(
                f"a passed task's exit code is 0, "
                f"got {self.exit_code!r}")
        if self.status == "failed" and self.exit_code == 0:
            raise ValueError("a failed task's exit code is not 0")
        if not isinstance(self.detail, str):
            raise ValueError(
                f"a verdict detail must be text, got {self.detail!r}")
        object.__setattr__(self, "detail", self.detail.strip())

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "fleet_task_verdict",
            "slice": FLEET_MODE_SLICE,
            "task_id": self.task_id,
            "label": self.label,
            "status": self.status,
            "exit_code": self.exit_code,
            "detail": self.detail,
        }


def validate_task_verdict(verdict: Any) -> TaskVerdict:
    """Validate one per-task verdict into a TaskVerdict.

    Accepts a TaskVerdict or a mapping naming a
    ``task_id`` (or ``id``), an optional ``label``
    (or ``name``), a ``status`` (or ``state``), an
    optional ``exit_code``, and an optional
    ``detail`` (or ``message``). Conflicting
    spellings and unknown keys refuse.
    """
    if isinstance(verdict, TaskVerdict):
        return verdict
    if not isinstance(verdict, dict):
        raise ValueError(
            f"a fleet task verdict must be a mapping, got {verdict!r}")
    unknown = set(verdict) - _VERDICT_KEYS
    if unknown:
        raise ValueError(
            "unknown fleet task verdict keys: %s"
            % ", ".join(sorted(unknown)))
    task_id = _pick(verdict, ("task_id", "id"), "task ids")
    if task_id is None:
        raise ValueError("a fleet task verdict is missing its task id")
    label = _pick(verdict, ("label", "name"), "labels")
    status = _pick(verdict, ("status", "state"), "statuses")
    detail = _pick(verdict, ("detail", "message"), "details")
    kwargs: Dict[str, Any] = {"task_id": task_id}
    if label is not None:
        kwargs["label"] = label
    if status is not None:
        kwargs["status"] = status
    if "exit_code" in verdict:
        kwargs["exit_code"] = verdict["exit_code"]
    if detail is not None:
        kwargs["detail"] = detail
    return TaskVerdict(**kwargs)


def build_task_verdict(verdict: Any = None, **kwargs: Any) -> TaskVerdict:
    """Build one validated per-task verdict."""
    if isinstance(verdict, TaskVerdict) and not kwargs:
        return verdict
    if isinstance(verdict, dict) or verdict is None:
        merged: Dict[str, Any] = {}
        if isinstance(verdict, dict):
            merged.update(verdict)
        merged.update(kwargs)
        return validate_task_verdict(merged)
    raise ValueError(
        f"a fleet task verdict must be a mapping, got {verdict!r}")


def _require_verdict(verdict: Any) -> TaskVerdict:
    if isinstance(verdict, TaskVerdict):
        return verdict
    return validate_task_verdict(verdict)


# ---------------------------------------------------------------------
# The fleet verdict: the per-task verdicts, aggregated mechanically.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class FleetVerdict:
    """A whole fleet judged, as data.

    ``status`` is passed only when every task
    passed (and the fleet is not empty); failed
    when a task failed and none errored; error
    when a task errored; incomplete when a task
    is unfinished or the fleet is empty.
    ``exit_code`` is the status's honest code in
    the ``mythic run`` road's mapping, and a
    FleetVerdict whose exit code does not match
    its status refuses on construction - the two
    can never be made to disagree. The counts are
    the per-status tallies, and they must sum to
    ``total``.
    """

    status: str = "incomplete"
    exit_code: int = EXIT_ERROR
    total: int = 0
    queued_count: int = 0
    running_count: int = 0
    passed_count: int = 0
    failed_count: int = 0
    error_count: int = 0
    skipped_count: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.status, str) \
                or self.status.strip().lower().replace("-", "_") \
                not in FLEET_STATUSES:
            raise ValueError(
                "a fleet status must be one of %s, got %r"
                % ("/".join(FLEET_STATUSES), self.status))
        object.__setattr__(
            self, "status",
            self.status.strip().lower().replace("-", "_"))
        if isinstance(self.exit_code, bool) \
                or not isinstance(self.exit_code, int):
            raise ValueError(
                f"a fleet exit code must be a whole number, "
                f"got {self.exit_code!r}")
        wanted = _EXIT_FOR_STATUS[self.status]
        if self.exit_code != wanted:
            raise ValueError(
                f"a {self.status} fleet's exit code is {wanted}, "
                f"got {self.exit_code!r}")
        counts = (
            self.total, self.queued_count, self.running_count,
            self.passed_count, self.failed_count, self.error_count,
            self.skipped_count)
        for count in counts:
            if isinstance(count, bool) or not isinstance(count, int) \
                    or count < 0:
                raise ValueError(
                    f"a fleet verdict count must be a whole number "
                    f"of 0 or more, got {count!r}")
        tallied = (
            self.queued_count + self.running_count + self.passed_count
            + self.failed_count + self.error_count + self.skipped_count)
        if tallied != self.total:
            raise ValueError(
                f"a fleet verdict's counts tally {tallied}, "
                f"not its total {self.total}")

    @property
    def counts(self) -> Dict[str, int]:
        return {
            "queued": self.queued_count,
            "running": self.running_count,
            "passed": self.passed_count,
            "failed": self.failed_count,
            "error": self.error_count,
            "skipped": self.skipped_count,
        }

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "fleet_verdict",
            "slice": FLEET_MODE_SLICE,
            "status": self.status,
            "exit_code": self.exit_code,
            "total": self.total,
            "counts": self.counts,
        }


def _verdict_list(verdicts: Any) -> Tuple[TaskVerdict, ...]:
    if verdicts is None:
        return ()
    if isinstance(verdicts, (str, bytes)) \
            or not isinstance(verdicts, (list, tuple)):
        raise ValueError("fleet task verdicts must be a list of verdicts")
    checked = tuple(_require_verdict(v) for v in verdicts)
    seen = set()
    for verdict in checked:
        if verdict.task_id in seen:
            raise ValueError(
                f"two verdicts name the same fleet task "
                f"{verdict.task_id!r}")
        seen.add(verdict.task_id)
    return checked


def judge_fleet(verdicts: Any = None, tasks: Any = None) -> FleetVerdict:
    """Judge a whole fleet from its per-task verdicts, mechanically.

    ``tasks``, when given, is the fleet itself (a
    list of FleetTask, a FleetRun or a
    FleetRegistry): a task with no recorded
    verdict counts as queued, so an unfinished
    fleet can never judge as passed, and a verdict
    naming a task the fleet does not hold refuses.
    Without ``tasks``, the verdicts alone are
    judged. Error outranks failure, failure
    outranks incompleteness only in the exit code
    it earns (both are non-zero); the status word
    always names the worst reading present.
    """
    if isinstance(tasks, FleetRegistry):
        registry = tasks
        tasks = registry.list_tasks()
        if verdicts is None:
            verdicts = registry.list_verdicts()
    if isinstance(tasks, FleetRun):
        tasks = tasks.tasks
    checked_tasks: Tuple[FleetTask, ...] = ()
    if tasks is not None:
        if isinstance(tasks, (str, bytes)) \
                or not isinstance(tasks, (list, tuple)):
            raise ValueError("fleet tasks must be a list of tasks")
        checked_tasks = tuple(_require_task(t) for t in tasks)
    checked = _verdict_list(verdicts)
    if tasks is not None:
        known = set()
        for task in checked_tasks:
            if task.task_id is None:
                raise ValueError(
                    "judging a fleet by its tasks needs every "
                    "task to carry an id; register the task first")
            known.add(task.task_id)
        for verdict in checked:
            if verdict.task_id not in known:
                raise ValueError(
                    f"a verdict names fleet task {verdict.task_id!r}, "
                    "which the fleet does not hold")
    counts = {status: 0 for status in TASK_STATUSES}
    if tasks is not None:
        by_id = {v.task_id: v for v in checked}
        for task in checked_tasks:
            verdict = by_id.get(task.task_id)
            counts[verdict.status if verdict else "queued"] += 1
        total = len(checked_tasks)
    else:
        for verdict in checked:
            counts[verdict.status] += 1
        total = len(checked)
    if total == 0:
        status = "incomplete"
    elif counts["error"]:
        status = "error"
    elif counts["failed"]:
        status = "failed"
    elif counts["passed"] == total:
        status = "passed"
    else:
        status = "incomplete"
    return FleetVerdict(
        status=status, exit_code=_EXIT_FOR_STATUS[status], total=total,
        queued_count=counts["queued"], running_count=counts["running"],
        passed_count=counts["passed"], failed_count=counts["failed"],
        error_count=counts["error"], skipped_count=counts["skipped"])


def fleet_exit_code(source: Any = None, tasks: Any = None) -> int:
    """The honest exit code of a fleet, as a pure function.

    ``source`` is a FleetVerdict, a FleetRegistry,
    or a list of per-task verdicts (judged against
    ``tasks`` when given). 0 only when every task
    passed; 1 when a task failed; 2 when a task
    errored or the fleet is unfinished.
    """
    if isinstance(source, FleetVerdict):
        return source.exit_code
    if isinstance(source, FleetRegistry):
        return source.fleet_verdict().exit_code
    return judge_fleet(source, tasks).exit_code


# ---------------------------------------------------------------------
# The artefact bundle: artefact names for one task, as data only.
# ---------------------------------------------------------------------


def normalize_artefact_name(value: Any) -> str:
    """The canonical artefact name a word names.

    A name is a relative path of one or more
    segments. An absolute name, an empty segment
    and a ``..`` segment all refuse plainly, so a
    bundle can never point outside the place its
    artefacts belong.
    """
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"an artefact name must be non-empty text, got {value!r}")
    name = value.strip()
    if name.startswith(("/", "\\")) \
            or (len(name) > 1 and name[1] == ":"):
        raise ValueError(
            f"an artefact name must be relative, got {value!r}")
    segments = name.replace("\\", "/").split("/")
    if any(not segment for segment in segments):
        raise ValueError(
            f"an artefact name has an empty path segment, "
            f"got {value!r}")
    if any(segment == ".." for segment in segments):
        raise ValueError(
            f"an artefact name must not carry a '..' path "
            f"segment, got {value!r}")
    return name


@dataclass(frozen=True)
class ArtefactBundle:
    """The artefacts one fleet task produced, named as data.

    ``artefacts`` is the bundle's list of artefact
    names for the task - names only; this layer
    writes nothing and checks no file. Duplicate
    names refuse: a bundle names each artefact
    once.
    """

    task_id: Optional[str] = None
    artefacts: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "task_id", normalize_task_id(self.task_id))
        if isinstance(self.artefacts, (str, bytes)) \
                or not isinstance(self.artefacts, (list, tuple)):
            raise ValueError(
                f"a bundle's artefacts must be a list of names, "
                f"got {self.artefacts!r}")
        cleaned = tuple(
            normalize_artefact_name(name) for name in self.artefacts)
        if len(set(cleaned)) != len(cleaned):
            raise ValueError("a bundle names the same artefact twice")
        object.__setattr__(self, "artefacts", cleaned)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "fleet_artefact_bundle",
            "slice": FLEET_MODE_SLICE,
            "task_id": self.task_id,
            "artefacts": list(self.artefacts),
        }


def validate_artefact_bundle(bundle: Any) -> ArtefactBundle:
    """Validate one artefact bundle into an ArtefactBundle.

    Accepts an ArtefactBundle or a mapping naming
    a ``task_id`` (or ``id``) and its ``artefacts``
    (or ``artifacts`` / ``artefact_names`` /
    ``names``). Conflicting spellings and unknown
    keys refuse.
    """
    if isinstance(bundle, ArtefactBundle):
        return bundle
    if not isinstance(bundle, dict):
        raise ValueError(
            f"an artefact bundle must be a mapping, got {bundle!r}")
    unknown = set(bundle) - _BUNDLE_KEYS
    if unknown:
        raise ValueError(
            "unknown artefact bundle keys: %s"
            % ", ".join(sorted(unknown)))
    task_id = _pick(bundle, ("task_id", "id"), "task ids")
    if task_id is None:
        raise ValueError("an artefact bundle is missing its task id")
    names = _pick(
        bundle, ("artefacts", "artifacts", "artefact_names", "names"),
        "artefact lists")
    return ArtefactBundle(
        task_id=task_id, artefacts=names if names is not None else ())


def build_artefact_bundle(bundle: Any = None,
                          **kwargs: Any) -> ArtefactBundle:
    """Build one validated artefact bundle."""
    if isinstance(bundle, ArtefactBundle) and not kwargs:
        return bundle
    if isinstance(bundle, dict) or bundle is None:
        merged: Dict[str, Any] = {}
        if isinstance(bundle, dict):
            merged.update(bundle)
        merged.update(kwargs)
        return validate_artefact_bundle(merged)
    raise ValueError(
        f"an artefact bundle must be a mapping, got {bundle!r}")


def _require_bundle(bundle: Any) -> ArtefactBundle:
    if isinstance(bundle, ArtefactBundle):
        return bundle
    return validate_artefact_bundle(bundle)


# ---------------------------------------------------------------------
# The fleet run: a named fleet of tasks, as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class FleetRun:
    """One fleet run: a label and its tasks, as data.

    The tasks are held in the order given. Two
    tasks carrying the same supplied id refuse -
    a run never holds two tasks under one name.
    """

    label: str = ""
    tasks: Tuple[FleetTask, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.label, str):
            raise ValueError(
                f"a fleet run label must be text, got {self.label!r}")
        object.__setattr__(self, "label", self.label.strip())
        if isinstance(self.tasks, (str, bytes)) \
                or not isinstance(self.tasks, (list, tuple)):
            raise ValueError("a fleet run's tasks must be a list of tasks")
        checked = tuple(_require_task(t) for t in self.tasks)
        seen = set()
        for task in checked:
            if task.task_id is not None:
                if task.task_id in seen:
                    raise ValueError(
                        f"a fleet run holds two tasks named "
                        f"{task.task_id!r}")
                seen.add(task.task_id)
        object.__setattr__(self, "tasks", checked)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "fleet_run",
            "slice": FLEET_MODE_SLICE,
            "label": self.label,
            "tasks": [task.to_record() for task in self.tasks],
            "task_count": len(self.tasks),
        }


def validate_fleet_run(run: Any) -> FleetRun:
    """Validate one fleet run into a FleetRun.

    Accepts a FleetRun or a mapping naming an
    optional ``label`` (or ``name``) and its
    ``tasks``. Unknown keys refuse.
    """
    if isinstance(run, FleetRun):
        return run
    if not isinstance(run, dict):
        raise ValueError(f"a fleet run must be a mapping, got {run!r}")
    unknown = set(run) - _RUN_KEYS
    if unknown:
        raise ValueError(
            "unknown fleet run keys: %s" % ", ".join(sorted(unknown)))
    if "tasks" not in run:
        raise ValueError("a fleet run is missing its tasks")
    label = _pick(run, ("label", "name"), "labels")
    return FleetRun(
        label=label if label is not None else "", tasks=run["tasks"])


def build_fleet_run(run: Any = None, **kwargs: Any) -> FleetRun:
    """Build one validated fleet run."""
    if isinstance(run, FleetRun) and not kwargs:
        return run
    if isinstance(run, dict) or run is None:
        merged: Dict[str, Any] = {}
        if isinstance(run, dict):
            merged.update(run)
        merged.update(kwargs)
        return validate_fleet_run(merged)
    raise ValueError(f"a fleet run must be a mapping, got {run!r}")


# ---------------------------------------------------------------------
# Resumability: what a resumed fleet still owes, as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class ResumePlan:
    """What a resumed fleet run still owes, as data.

    ``remaining_ids`` are the tasks a resume must
    run, in fleet order; ``passed_ids`` are the
    tasks already passed, which a resume never
    runs again; ``held_back_ids`` are the failed
    and error tasks a resume leaves alone because
    the caller did not ask to retry failures. The
    three lists never overlap and name no task
    twice. ``retry_failures`` records the caller's
    explicit choice.
    """

    remaining_ids: Tuple[str, ...] = ()
    passed_ids: Tuple[str, ...] = ()
    held_back_ids: Tuple[str, ...] = ()
    retry_failures: bool = False

    def __post_init__(self) -> None:
        cleaned = {}
        for field_name in (
                "remaining_ids", "passed_ids", "held_back_ids"):
            value = getattr(self, field_name)
            if isinstance(value, (str, bytes)) \
                    or not isinstance(value, (list, tuple)):
                raise ValueError(
                    f"a resume plan's {field_name} must be a list "
                    f"of task ids")
            ids = tuple(normalize_task_id(v) for v in value)
            if len(set(ids)) != len(ids):
                raise ValueError(
                    f"a resume plan names a task twice in "
                    f"{field_name}")
            cleaned[field_name] = ids
            object.__setattr__(self, field_name, ids)
        named = (
            list(cleaned["remaining_ids"]) + list(cleaned["passed_ids"])
            + list(cleaned["held_back_ids"]))
        if len(set(named)) != len(named):
            raise ValueError(
                "a resume plan names the same task as both "
                "remaining and settled")
        if not isinstance(self.retry_failures, bool):
            raise ValueError(
                f"a resume plan's retry choice must be true or "
                f"false, got {self.retry_failures!r}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "fleet_resume_plan",
            "slice": FLEET_MODE_SLICE,
            "remaining": list(self.remaining_ids),
            "passed": list(self.passed_ids),
            "held_back": list(self.held_back_ids),
            "retry_failures": self.retry_failures,
        }


def _plan_inputs(tasks: Any, verdicts: Any):
    """The (tasks, verdicts) a resume plan reads, registry-aware."""
    if isinstance(tasks, FleetRegistry):
        registry = tasks
        if verdicts is None:
            verdicts = registry.list_verdicts()
        tasks = registry.list_tasks()
    if isinstance(tasks, FleetRun):
        tasks = tasks.tasks
    if isinstance(tasks, (str, bytes)) \
            or not isinstance(tasks, (list, tuple)):
        raise ValueError("a resume plan needs a list of fleet tasks")
    checked_tasks = tuple(_require_task(t) for t in tasks)
    checked_verdicts = _verdict_list(verdicts)
    return checked_tasks, checked_verdicts


def plan_resume(tasks: Any, verdicts: Any = None,
                retry_failures: Any = False) -> ResumePlan:
    """Plan a fleet resume from recorded verdicts, mechanically.

    A passed task is never remaining - it is
    listed as passed. A queued, running, skipped
    or verdictless task is remaining. A failed or
    error task is remaining only when
    ``retry_failures`` is exactly True, and is
    otherwise held back. Every task must carry an
    id (a resume names tasks by id), a verdict
    naming a task the fleet does not hold refuses,
    and a non-boolean retry choice refuses.
    """
    if not isinstance(retry_failures, bool):
        raise ValueError(
            f"a resume retry choice must be true or false, "
            f"got {retry_failures!r}")
    checked_tasks, checked = _plan_inputs(tasks, verdicts)
    by_id = {v.task_id: v for v in checked}
    known = set()
    remaining, passed, held_back = [], [], []
    for task in checked_tasks:
        if task.task_id is None:
            raise ValueError(
                "a resume plan names tasks by id; register "
                "the task first")
        known.add(task.task_id)
        verdict = by_id.get(task.task_id)
        if verdict is not None and verdict.status == "passed":
            passed.append(task.task_id)
        elif verdict is not None \
                and verdict.status in ("failed", "error") \
                and not retry_failures:
            held_back.append(task.task_id)
        else:
            remaining.append(task.task_id)
    for verdict in checked:
        if verdict.task_id not in known:
            raise ValueError(
                f"a verdict names fleet task {verdict.task_id!r}, "
                "which the fleet does not hold")
    return ResumePlan(
        remaining_ids=tuple(remaining), passed_ids=tuple(passed),
        held_back_ids=tuple(held_back), retry_failures=retry_failures)


def _resume_headline(plan: ResumePlan) -> str:
    remaining = ", ".join(plan.remaining_ids)
    headline = (
        f"Fleet resume: {len(plan.remaining_ids)} task(s) remain "
        f"to run ({remaining}); {len(plan.passed_ids)} passed "
        "task(s) will not be run again.")
    if plan.held_back_ids:
        headline += (
            f" {len(plan.held_back_ids)} failed or error task(s) "
            "are held back - retrying failures was not asked for.")
    return headline


def resume_record(tasks: Any, verdicts: Any = None,
                  retry_failures: Any = False) -> Optional[Dict[str, Any]]:
    """The session-news record of one owed resume, or None.

    A fleet with nothing remaining returns None -
    the agent layer publishes this record as a
    session event when it is not None, so a resume
    can never be lost as a mere log line, and
    never announced when none is owed.
    """
    plan = plan_resume(tasks, verdicts, retry_failures)
    if not plan.remaining_ids:
        return None
    return {
        "type": "fleet_resume",
        "news": True,
        "slice": FLEET_MODE_SLICE,
        "remaining": list(plan.remaining_ids),
        "passed": list(plan.passed_ids),
        "held_back": list(plan.held_back_ids),
        "retry_failures": plan.retry_failures,
        "headline": _resume_headline(plan),
    }


def format_resume_record(record: Any) -> str:
    """One resume record as its plain headline."""
    if isinstance(record, dict) and record.get("type") == "fleet_resume":
        return str(record["headline"])
    raise ValueError("format_resume_record needs a fleet resume record")


# ---------------------------------------------------------------------
# The registry model: tasks held in registration order, ids
# deterministic; verdicts and bundles held alongside.
# ---------------------------------------------------------------------


class FleetRegistry:
    """An in-memory registry of fleet tasks.

    Tasks are held in registration order. Ids are
    deterministic: a caller-supplied id is used as
    given (a duplicate refuses), and an unsupplied
    id is the next ``fleet-N`` in sequence,
    skipping any number a supplied id already took
    - no randomness a test cannot pin. Verdicts
    and artefact bundles are held as data
    alongside the tasks, one per task, replaced
    when a newer one is recorded. Storage beyond
    memory (a session's journal, a file) is the
    agent layer's concern; this model is neutral.
    """

    def __init__(self) -> None:
        self._tasks: Dict[str, FleetTask] = {}
        self._verdicts: Dict[str, TaskVerdict] = {}
        self._bundles: Dict[str, ArtefactBundle] = {}
        self._next = 1

    def _fresh_id(self) -> str:
        while f"fleet-{self._next}" in self._tasks:
            self._next += 1
        task_id = f"fleet-{self._next}"
        self._next += 1
        return task_id

    def register(self, task: Any) -> FleetTask:
        """Register one task and hold it; duplicate ids refuse."""
        validated = _require_task(task)
        if validated.task_id is None:
            validated = replace(validated, task_id=self._fresh_id())
        elif validated.task_id in self._tasks:
            raise ValueError(
                f"a fleet task named {validated.task_id!r} "
                "already exists")
        self._tasks[validated.task_id] = validated
        return validated

    def get(self, task_id: Any) -> FleetTask:
        """The task one id names; an unknown id raises KeyError."""
        wanted = normalize_task_id(task_id)
        if wanted not in self._tasks:
            raise KeyError(f"unknown fleet task: {wanted!r}")
        return self._tasks[wanted]

    def list_tasks(self) -> Tuple[FleetTask, ...]:
        """Every held task, in registration order."""
        return tuple(self._tasks.values())

    def record_verdict(self, verdict: Any = None,
                       **kwargs: Any) -> TaskVerdict:
        """Record one task's verdict, replacing any older one.

        Accepts a TaskVerdict, a verdict mapping, or
        a task id plus verdict field words. A task
        the registry does not hold raises KeyError.
        """
        if kwargs and isinstance(verdict, (TaskVerdict, dict)):
            raise ValueError(
                "a verdict is named twice: as a record and as "
                "field words")
        if isinstance(verdict, (TaskVerdict, dict)) or verdict is None:
            checked = build_task_verdict(verdict, **kwargs)
        else:
            checked = build_task_verdict(
                {"task_id": verdict, **kwargs})
        task = self.get(checked.task_id)
        if not checked.label:
            checked = replace(checked, label=task.display_label)
        self._verdicts[checked.task_id] = checked
        return checked

    def get_verdict(self, task_id: Any) -> Optional[TaskVerdict]:
        """One task's recorded verdict, or None when none is held."""
        task = self.get(task_id)
        return self._verdicts.get(task.task_id)

    def list_verdicts(self) -> Tuple[TaskVerdict, ...]:
        """Every recorded verdict, in task registration order."""
        return tuple(
            self._verdicts[task.task_id]
            for task in self._tasks.values()
            if task.task_id in self._verdicts)

    def fleet_verdict(self) -> FleetVerdict:
        """The whole held fleet judged from its recorded verdicts."""
        return judge_fleet(self.list_verdicts(), self.list_tasks())

    def exit_code(self) -> int:
        """The held fleet's honest exit code."""
        return self.fleet_verdict().exit_code

    def record_bundle(self, bundle: Any = None,
                      **kwargs: Any) -> ArtefactBundle:
        """Record one task's artefact bundle, replacing any older one.

        Accepts an ArtefactBundle, a bundle mapping,
        or a task id plus an ``artefacts`` list. A
        task the registry does not hold raises
        KeyError.
        """
        if kwargs and isinstance(bundle, (ArtefactBundle, dict)):
            raise ValueError(
                "a bundle is named twice: as a record and as "
                "field words")
        if isinstance(bundle, (ArtefactBundle, dict)) or bundle is None:
            checked = build_artefact_bundle(bundle, **kwargs)
        else:
            checked = build_artefact_bundle(
                {"task_id": bundle, **kwargs})
        self.get(checked.task_id)
        self._bundles[checked.task_id] = checked
        return checked

    def get_bundle(self, task_id: Any) -> Optional[ArtefactBundle]:
        """One task's recorded bundle, or None when none is held."""
        task = self.get(task_id)
        return self._bundles.get(task.task_id)

    def list_bundles(self) -> Tuple[ArtefactBundle, ...]:
        """Every recorded bundle, in task registration order."""
        return tuple(
            self._bundles[task.task_id]
            for task in self._tasks.values()
            if task.task_id in self._bundles)

    def resume_plan(self, retry_failures: Any = False) -> ResumePlan:
        """The held fleet's resume plan from its recorded verdicts."""
        return plan_resume(
            self.list_tasks(), self.list_verdicts(), retry_failures)

    def resume_record(self,
                      retry_failures: Any = False) -> Optional[Dict[str, Any]]:
        """The held fleet's resume news record, or None."""
        return resume_record(
            self.list_tasks(), self.list_verdicts(), retry_failures)


# ---------------------------------------------------------------------
# The /fleet surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------


def _verdict_map(tasks: Any, verdicts: Any) -> Dict[str, TaskVerdict]:
    """Verdicts by task id, from a registry or an explicit list."""
    if isinstance(tasks, FleetRegistry):
        return {v.task_id: v for v in tasks.list_verdicts()}
    return {v.task_id: v for v in _verdict_list(verdicts)}


def format_fleet_task(task: Any, verdict: Any = None) -> str:
    """One task, in plain words, with its verdict when one is given."""
    current = _require_task(task)
    checked = _require_verdict(verdict) if verdict is not None else None
    if checked is not None and current.task_id is not None \
            and checked.task_id != current.task_id:
        raise ValueError(
            f"a verdict for task {checked.task_id!r} does not "
            f"judge task {current.task_id!r}")
    name = current.task_id or current.display_label
    status = checked.status if checked else "queued"
    line = (
        f"{name}: {current.display_label} [{status}] - "
        f"{current.command_text}")
    if current.cwd:
        line += f"; repo: {current.cwd}"
    if current.prompt:
        line += f"; prompt: {current.prompt}"
    if checked is not None and checked.exit_code is not None:
        line += f"; exit {checked.exit_code}"
    if checked is not None and checked.detail:
        line += f"; {checked.detail}"
    return line


def format_fleet_tasks(tasks: Any = None, verdicts: Any = None) -> str:
    """The tasks, in plain words, in the order given.

    With no tasks at all the text starts with the
    plain statement of that fact. Every line states
    its task's status in words.
    """
    if tasks is None:
        selected: Tuple[FleetTask, ...] = ()
    elif isinstance(tasks, FleetRegistry):
        selected = tasks.list_tasks()
    elif isinstance(tasks, FleetRun):
        selected = tasks.tasks
    else:
        if isinstance(tasks, (str, bytes)) \
                or not isinstance(tasks, (list, tuple)):
            raise ValueError("fleet tasks must be a list of tasks")
        selected = tuple(_require_task(t) for t in tasks)
    if not selected:
        return (
            "Fleet tasks: none. No headless fleet run is held.")
    by_id = _verdict_map(tasks, verdicts)
    lines = [f"Fleet tasks: {len(selected)} held."]
    for task in selected:
        verdict = by_id.get(task.task_id) \
            if task.task_id is not None else None
        lines.append(f"  {format_fleet_task(task, verdict)}")
    return "\n".join(lines)


def format_fleet_verdict(verdict: Any = None, tasks: Any = None) -> str:
    """One fleet verdict, in plain words, exit code always stated."""
    if isinstance(verdict, FleetVerdict):
        judged = verdict
    elif isinstance(verdict, FleetRegistry):
        judged = verdict.fleet_verdict()
    else:
        judged = judge_fleet(verdict, tasks)
    counts = judged.counts
    unfinished = (
        counts["queued"] + counts["running"] + counts["skipped"])
    return (
        f"Fleet verdict: {judged.status} - {counts['passed']} of "
        f"{judged.total} task(s) passed, {counts['failed']} failed, "
        f"{counts['error']} error, {unfinished} not finished; "
        f"exit code {judged.exit_code}.")


def format_fleet_run(source: Any = None, verdicts: Any = None) -> str:
    """A fleet run, in plain words: its tasks and its verdict."""
    lines = [format_fleet_tasks(source, verdicts)]
    if isinstance(source, FleetRegistry):
        tasks = source.list_tasks()
    elif isinstance(source, FleetRun):
        tasks = source.tasks
    elif isinstance(source, (list, tuple)):
        tasks = source
    else:
        tasks = ()
    if tasks:
        lines.append(format_fleet_verdict(
            source if isinstance(source, FleetRegistry) else verdicts,
            None if isinstance(source, FleetRegistry) else tasks))
    return "\n".join(lines)


def format_artefact_bundle(bundle: Any) -> str:
    """One artefact bundle, in plain words."""
    current = _require_bundle(bundle)
    if not current.artefacts:
        return (
            f"{current.task_id}: artefact bundle - no artefacts "
            "recorded.")
    return (
        f"{current.task_id}: artefact bundle - "
        + ", ".join(current.artefacts))


def format_resume_plan(plan: Any) -> str:
    """One resume plan, in plain words."""
    if not isinstance(plan, ResumePlan):
        raise ValueError(f"a resume plan is needed, got {plan!r}")
    if not plan.remaining_ids:
        return (
            "Fleet resume: nothing remains to run - every task "
            "is passed or held back.")
    lines = [
        f"Fleet resume: {len(plan.remaining_ids)} task(s) remain "
        "to run: " + ", ".join(plan.remaining_ids) + "."]
    if plan.passed_ids:
        lines.append(
            "  Passed, never run again: "
            + ", ".join(plan.passed_ids) + ".")
    if plan.held_back_ids:
        lines.append(
            "  Held back (failed or error, retry not asked for): "
            + ", ".join(plan.held_back_ids) + ".")
    return "\n".join(lines)


def format_fleet_mode(source: Any = None, verdicts: Any = None) -> str:
    """The whole slice, in plain words, for /fleet."""
    lines = ["Fleet mode (M-106) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_fleet_run(source, verdicts))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_fleet_args(args: Any) -> Tuple[str, Optional[str]]:
    """Parse the /fleet grammar both surfaces share.

    No words (or ``show``) shows the fleet;
    ``show <task>`` and a bare task id show one
    task; ``verdict`` asks for the fleet verdict;
    ``resume`` asks for the resume plan. Anything
    else is a usage error naming the grammar.
    Returns ``(action, task-id-or-None)``.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None \
        else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() == "show":
        return ("show", None)
    words = text.split()
    head = words[0].lower()
    if head in ("verdict", "resume") and len(words) == 1:
        return (head, None)
    if head == "show" and len(words) == 2:
        try:
            return ("show", normalize_task_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head in ("show", "verdict", "resume"):
        raise ValueError(USAGE)
    if len(words) == 1:
        try:
            return ("show", normalize_task_id(words[0]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
