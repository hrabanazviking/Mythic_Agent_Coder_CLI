"""Scheduled work - cron-style jobs as data (M-105).

Part V - Autonomy & Safety. The roadmap's words:
``cron-style jobs ("run the suite at dawn",
"check the upstream repo weekly") as data, with
the same approval lines as live work.``

What already shipped, and what this slice adds:

* The M-103 background tasks layer holds a long
  command as a managed job: an argv list, never a
  shell string, with a lifecycle and completion
  news. The M-104 keeper layer judges whether
  work has gone quiet and says what is owed when
  it has. Nothing in the tree says when a piece
  of work is *owed* in the first place - a job
  that should run every dawn, or every week, as
  a standing piece of data a session can hold,
  judge, and surface when its moment comes.
* This slice is that missing schedule, as a pure
  layer: a scheduled job (what to run - an argv
  list, never a shell string - when to run it,
  whether it is enabled, and its approval
  posture) validated as data, a schedule as data
  (daily at a named time, weekly on a named
  weekday at a named time, or every N minutes or
  hours from an anchor), the next due moment
  computed deterministically from any given
  moment, a mechanical due judgement at a moment
  (not due, due, overdue, waiting for approval,
  or disabled), a due record shaped as session
  news, and a small in-memory registry model
  with deterministic ids. This module starts no
  timer, runs no process, writes no file and
  changes no setting; the agent layer owns
  holding the registry for a session, feeding it
  real run moments, carrying a due job out in
  the world, and publishing a due record into
  the session.

Honesty rules, enforced here and pinned by tests:

* **A command is data, never a shell string.**
  A job's command is an argv list of non-empty
  text parts. A single string - the shape a
  shell would eval - refuses, exactly as M-103
  refuses it, so no scheduled job can smuggle
  in a command line to be interpreted later.
* **A schedule is data, and malformed refuses.**
  A daily job names a time of day as HH:MM, a
  weekly job names a weekday and a time, an
  interval job names a whole number of minutes
  (hours read as minutes). A bad time, an
  unknown weekday, a zero or negative interval
  and unknown keys all raise plainly instead of
  being skipped or guessed at.
* **The approval lines are the live-work lines.**
  A job's approval posture is data: ``unattended``
  jobs name work live work could run without
  asking, and only those are ever judged owed a
  run. A ``needs_approval`` job that comes due
  is judged waiting for approval - recorded as
  due and waiting, never silently run.
* **Due is mechanical.** A job is due from its
  schedule alone: the latest schedule moment at
  or before the judged moment, when no run has
  been recorded at or after that moment. Exactly
  at the due moment is due; past it is overdue.
  No other signal moves the verdict.
* **A due record is news only when a run or an
  approval is owed.** A job that is not due, or
  is disabled, yields no due record at all,
  exactly as a job that has not finished yields
  no completion record. A due job yields one
  record with a one-line plain headline.
* **Status is never carried by colour or symbol
  alone.** Every formatter states the due state
  in words, and a due or waiting job's line
  states its due moment and the action owed.

Times are timezone-naive local datetimes, the
reading the roadmap's own examples use ("at
dawn", "weekly"): a moment with tzinfo refuses,
so no reading can quietly shift a due moment.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, time, timedelta
from typing import Any, Dict, Optional, Tuple

__all__ = [
    "APPROVAL_POSTURES",
    "DUE_ACTIONS",
    "DUE_STATUSES",
    "PLAIN_EXPLANATION",
    "SCHEDULED_WORK_SLICE",
    "SCHEDULE_KINDS",
    "USAGE",
    "WEEKDAYS",
    "DueVerdict",
    "Schedule",
    "ScheduledJob",
    "ScheduledWorkRegistry",
    "build_schedule",
    "build_scheduled_job",
    "due_at_or_before",
    "due_record",
    "format_due_record",
    "format_schedule",
    "format_scheduled_job",
    "format_scheduled_jobs",
    "format_scheduled_work",
    "format_verdict",
    "judge_job",
    "next_due",
    "normalize_approval",
    "normalize_job_id",
    "normalize_schedule_kind",
    "normalize_time_of_day",
    "normalize_weekday",
    "parse_schedule_args",
    "validate_schedule",
    "validate_scheduled_job",
]

SCHEDULED_WORK_SLICE = "M-105"

#: The schedule kinds, in house order.
SCHEDULE_KINDS = ("daily", "weekly", "interval")

#: Weekday words, Monday first - the order
#: ``datetime.weekday()`` numbers them.
WEEKDAYS = (
    "monday", "tuesday", "wednesday", "thursday",
    "friday", "saturday", "sunday",
)

#: The approval postures a job can carry. An
#: unattended job names work live work could run
#: without asking; a needs_approval job waits.
APPROVAL_POSTURES = ("unattended", "needs_approval")

#: The due statuses a verdict carries.
DUE_STATUSES = (
    "not_due", "due", "overdue",
    "waiting_for_approval", "disabled",
)

#: The actions a verdict can owe.
DUE_ACTIONS = ("none", "run", "await_approval")

PLAIN_EXPLANATION = (
    "Scheduled work is cron-style jobs held as "
    "data: what to run (a command as a list of "
    "words, never a shell string), when to run "
    "it (daily at a named time, weekly on a named "
    "weekday, or every so many minutes or hours), "
    "whether it is enabled, and its approval "
    "posture. Scheduled work keeps the same "
    "approval lines as live work: a job may run "
    "unattended only what live work could run "
    "without asking, and a job that needs "
    "approval, when its moment comes, is recorded "
    "as due and waiting for approval - never "
    "silently run. When a job comes due, that is "
    "news for the session: the job, its due "
    "moment and the action owed in one plain "
    "line. This layer holds the jobs and the due "
    "verdicts as data only; it starts no timer "
    "and runs nothing itself."
)

USAGE = (
    "Usage: /schedule, /schedule show, "
    "/schedule show <job>, /schedule check"
)

_JOB_KEYS = frozenset({
    "job_id", "id", "label", "name", "argv", "command",
    "cwd", "schedule", "enabled", "approval",
    "requires_approval",
})

_SCHEDULE_KEYS = frozenset({
    "kind", "type", "time", "at", "time_of_day",
    "weekday", "day", "every_minutes", "every_hours",
    "interval_minutes", "anchor", "anchor_at",
})

_JOB_ID_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789-_.")


def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_moment(value: Any, what: str) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError(
            f"{what} must be a datetime, got {value!r}")
    if value.tzinfo is not None:
        raise ValueError(
            f"{what} must be timezone-naive local time, "
            f"got {value!r}")
    return value


def _parse_moment(value: Any, what: str) -> datetime:
    if isinstance(value, datetime):
        return _check_moment(value, what)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.strip())
        except ValueError:
            raise ValueError(
                f"{what} must be an ISO datetime, "
                f"got {value!r}") from None
        return _check_moment(parsed, what)
    raise ValueError(
        f"{what} must be a datetime, got {value!r}")


def normalize_job_id(value: Any) -> str:
    """The canonical scheduled job id a word names.

    A job id is one word of letters, digits,
    dashes, underscores and dots, read with its
    case kept. Anything else raises.
    """
    if isinstance(value, str):
        wanted = value.strip()
        if wanted and all(ch in _JOB_ID_CHARS for ch in wanted):
            return wanted
    raise ValueError(
        f"a scheduled job id must be a non-empty word of letters, "
        f"digits, dashes, underscores and dots, got {value!r}")


def normalize_schedule_kind(value: Any) -> str:
    """The canonical schedule kind a word names."""
    if isinstance(value, str):
        wanted = value.strip().lower().replace("-", "_")
        if wanted in SCHEDULE_KINDS:
            return wanted
    raise ValueError(
        "a schedule kind must be one of %s, got %r"
        % ("/".join(SCHEDULE_KINDS), value))


def normalize_time_of_day(value: Any) -> str:
    """The canonical HH:MM time of day a word names.

    Accepts a ``datetime.time`` or text in HH:MM
    form (a one-digit hour reads the same). A
    word like ``dawn``, an hour past 23, a minute
    past 59 and seconds all refuse plainly.
    """
    if isinstance(value, time):
        if value.second or value.microsecond or value.tzinfo is not None:
            raise ValueError(
                f"a time of day must be a plain HH:MM, got {value!r}")
        return "%02d:%02d" % (value.hour, value.minute)
    if isinstance(value, str):
        parts = value.strip().split(":")
        if len(parts) == 2 and all(p.isdigit() for p in parts):
            hour, minute = int(parts[0]), int(parts[1])
            if hour <= 23 and minute <= 59:
                return "%02d:%02d" % (hour, minute)
    raise ValueError(
        f"a time of day must be HH:MM (00:00 to 23:59), "
        f"got {value!r}")


def normalize_weekday(value: Any) -> str:
    """The canonical weekday a word names.

    Full names and three-letter abbreviations
    read case-insensitively; a weekday number
    (Monday 0 to Sunday 6, the ``datetime``
    numbering) reads too. Anything else raises.
    """
    if isinstance(value, bool):
        raise ValueError(f"a weekday is not a boolean, got {value!r}")
    if isinstance(value, int):
        if 0 <= value <= 6:
            return WEEKDAYS[value]
        raise ValueError(
            f"a weekday number must be 0 to 6, got {value!r}")
    if isinstance(value, str):
        wanted = value.strip().lower()
        for name in WEEKDAYS:
            if wanted == name or wanted == name[:3]:
                return name
    raise ValueError(
        "a weekday must be one of %s, got %r"
        % ("/".join(WEEKDAYS), value))


def normalize_approval(value: Any) -> str:
    """The canonical approval posture a word names.

    ``unattended`` and ``needs_approval`` read
    case-insensitively with dashes as underscores;
    a boolean reads as the posture it means
    (True - approval is required - is
    needs_approval). Anything else raises.
    """
    if isinstance(value, bool):
        return "needs_approval" if value else "unattended"
    if isinstance(value, str):
        wanted = value.strip().lower().replace("-", "_")
        if wanted in APPROVAL_POSTURES:
            return wanted
        if wanted in ("approved", "auto", "automatic"):
            return "unattended"
    raise ValueError(
        "an approval posture must be one of %s, got %r"
        % ("/".join(APPROVAL_POSTURES), value))


def _check_argv(value: Any) -> Tuple[str, ...]:
    """A job's command words, validated whole (M-103's rule)."""
    if isinstance(value, (str, bytes)):
        raise ValueError(
            "a scheduled job command must be an argv list of "
            "words, not a shell string")
    if not isinstance(value, (list, tuple)):
        raise ValueError(
            f"a scheduled job command must be an argv list, "
            f"got {value!r}")
    parts = tuple(value)
    if not parts:
        raise ValueError("a scheduled job command needs at least one word")
    cleaned = []
    for part in parts:
        if not isinstance(part, str) or not part.strip():
            raise ValueError(
                f"a scheduled job command word must be non-empty "
                f"text, got {part!r}")
        cleaned.append(part.strip())
    return tuple(cleaned)


def _check_interval_minutes(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(
            f"an interval must be a whole number of minutes, "
            f"got {value!r}")
    if value < 1 or value > 10080:
        raise ValueError(
            f"an interval must be between 1 and 10080 minutes, "
            f"got {value!r}")
    return value


# ---------------------------------------------------------------------
# The schedule: when a job runs, as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class Schedule:
    """When one scheduled job runs, as data.

    ``kind`` is daily, weekly or interval. A daily
    schedule names a ``time_of_day``; a weekly
    schedule names a ``weekday`` and a
    ``time_of_day``; an interval schedule names
    ``interval_minutes`` and an ``anchor`` moment
    its ticks are counted from. Fields a kind
    does not use refuse when named, so a schedule
    is never half one kind and half another.

    Constructing one validates it, so a Schedule
    that exists is a schedule a job could run by.
    """

    kind: str = "daily"
    time_of_day: Optional[str] = None
    weekday: Optional[str] = None
    interval_minutes: Optional[int] = None
    anchor: Optional[datetime] = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "kind", normalize_schedule_kind(self.kind))
        if self.kind == "daily":
            if self.weekday is not None or self.interval_minutes is not None \
                    or self.anchor is not None:
                raise ValueError(
                    "a daily schedule names only a time of day")
            object.__setattr__(
                self, "time_of_day",
                normalize_time_of_day(self.time_of_day))
        elif self.kind == "weekly":
            if self.interval_minutes is not None or self.anchor is not None:
                raise ValueError(
                    "a weekly schedule names only a weekday and a time")
            object.__setattr__(
                self, "time_of_day",
                normalize_time_of_day(self.time_of_day))
            object.__setattr__(
                self, "weekday", normalize_weekday(self.weekday))
        else:
            if self.time_of_day is not None or self.weekday is not None:
                raise ValueError(
                    "an interval schedule names only an interval "
                    "and its anchor")
            object.__setattr__(
                self, "interval_minutes",
                _check_interval_minutes(self.interval_minutes))
            if self.anchor is not None:
                object.__setattr__(
                    self, "anchor", _check_moment(self.anchor, "an anchor"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "time_of_day": self.time_of_day,
            "weekday": self.weekday,
            "interval_minutes": self.interval_minutes,
            "anchor": self.anchor.isoformat() if self.anchor else None,
        }


def _pick(mapping: Dict[str, Any], names: Tuple[str, ...],
          what: str) -> Any:
    """One field from its spellings, or a refusal on conflict."""
    found = [name for name in names if name in mapping]
    if not found:
        return None
    first = mapping[found[0]]
    for name in found[1:]:
        if mapping[name] != first:
            raise ValueError(f"a schedule names two different {what}")
    return first


def validate_schedule(schedule: Any) -> Schedule:
    """Validate one schedule into a Schedule.

    Accepts a Schedule or a mapping naming a
    ``kind`` (or ``type``), a ``time`` (or ``at``
    / ``time_of_day``), a ``weekday`` (or
    ``day``), an ``every_minutes`` (or
    ``interval_minutes``; ``every_hours`` reads
    as minutes), and an ``anchor`` (or
    ``anchor_at``) as a datetime or ISO text.
    Naming two spellings of one field with
    different values refuses, and unknown keys
    refuse.
    """
    if isinstance(schedule, Schedule):
        return schedule
    if not isinstance(schedule, dict):
        raise ValueError(
            f"a schedule must be a mapping, got {schedule!r}")
    unknown = set(schedule) - _SCHEDULE_KEYS
    if unknown:
        raise ValueError(
            "unknown schedule keys: %s" % ", ".join(sorted(unknown)))
    kind = _pick(schedule, ("kind", "type"), "kinds")
    if kind is None:
        raise ValueError("a schedule is missing its kind")
    kind = normalize_schedule_kind(kind)
    kwargs: Dict[str, Any] = {"kind": kind}
    moment = _pick(schedule, ("time", "at", "time_of_day"), "times")
    if moment is not None:
        kwargs["time_of_day"] = moment
    weekday = _pick(schedule, ("weekday", "day"), "weekdays")
    if weekday is not None:
        kwargs["weekday"] = weekday
    minutes = _pick(
        schedule, ("every_minutes", "interval_minutes"), "intervals")
    hours = schedule.get("every_hours")
    if hours is not None:
        if isinstance(hours, bool) or not isinstance(hours, int):
            raise ValueError(
                f"an interval in hours must be a whole number, "
                f"got {hours!r}")
        if minutes is not None and minutes != hours * 60:
            raise ValueError("a schedule names two different intervals")
        minutes = hours * 60
    if minutes is not None:
        kwargs["interval_minutes"] = minutes
    anchor = _pick(schedule, ("anchor", "anchor_at"), "anchors")
    if anchor is not None:
        kwargs["anchor"] = _parse_moment(anchor, "an anchor")
    return Schedule(**kwargs)


def build_schedule(schedule: Any = None, **kwargs: Any) -> Schedule:
    """Build one validated schedule from a mapping or field words."""
    if isinstance(schedule, Schedule) and not kwargs:
        return schedule
    if isinstance(schedule, dict) or schedule is None:
        merged: Dict[str, Any] = {}
        if isinstance(schedule, dict):
            merged.update(schedule)
        merged.update(kwargs)
        return validate_schedule(merged)
    if kwargs:
        merged = dict(kwargs)
        merged.setdefault("kind", schedule)
        return validate_schedule(merged)
    raise ValueError(f"a schedule must be a mapping, got {schedule!r}")


# ---------------------------------------------------------------------
# The scheduled job: what runs, when, and under which approval line.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class ScheduledJob:
    """One cron-style job, as data.

    ``argv`` is the command as a list of words -
    never a shell string. ``schedule`` is when it
    runs. ``enabled`` says the job is live at all.
    ``approval`` is its approval posture: an
    unattended job names work live work could run
    without asking; a needs_approval job, when
    due, waits for approval and is never run by
    this layer's judgement. ``label`` is the
    short human name reports use; when empty the
    command itself is the label.

    Constructing one validates it, so a
    ScheduledJob that exists is a job the agent
    layer could hold and judge.
    """

    label: str = ""
    argv: Tuple[str, ...] = ()
    schedule: Schedule = Schedule(kind="daily", time_of_day="00:00")
    job_id: Optional[str] = None
    cwd: Optional[str] = None
    enabled: bool = True
    approval: str = "unattended"

    def __post_init__(self) -> None:
        object.__setattr__(self, "argv", _check_argv(self.argv))
        if not isinstance(self.label, str):
            raise ValueError(
                f"a scheduled job label must be text, got {self.label!r}")
        object.__setattr__(self, "label", self.label.strip())
        if not isinstance(self.schedule, Schedule):
            object.__setattr__(
                self, "schedule", validate_schedule(self.schedule))
        if self.job_id is not None:
            object.__setattr__(
                self, "job_id", normalize_job_id(self.job_id))
        if self.cwd is not None:
            object.__setattr__(
                self, "cwd", _clean_text(self.cwd, "a job cwd"))
        if not isinstance(self.enabled, bool):
            raise ValueError(
                f"a scheduled job enabled flag must be true or "
                f"false, got {self.enabled!r}")
        object.__setattr__(
            self, "approval", normalize_approval(self.approval))

    @property
    def requires_approval(self) -> bool:
        return self.approval == "needs_approval"

    @property
    def command_text(self) -> str:
        """The command as one display line (display only)."""
        return " ".join(self.argv)

    @property
    def display_label(self) -> str:
        return self.label or self.command_text

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "scheduled_job",
            "slice": SCHEDULED_WORK_SLICE,
            "job_id": self.job_id,
            "label": self.label,
            "argv": list(self.argv),
            "cwd": self.cwd,
            "schedule": self.schedule.to_record(),
            "enabled": self.enabled,
            "approval": self.approval,
            "requires_approval": self.requires_approval,
        }


def validate_scheduled_job(job: Any) -> ScheduledJob:
    """Validate one scheduled job into a ScheduledJob.

    Accepts a ScheduledJob or a mapping naming an
    ``argv`` (or ``command``) list, a
    ``schedule``, an optional ``label`` (or
    ``name``), ``job_id`` (or ``id``), ``cwd``,
    ``enabled``, and an approval posture as
    ``approval`` or ``requires_approval``. Naming
    both spellings of one field with different
    values refuses, and unknown keys refuse.
    """
    if isinstance(job, ScheduledJob):
        return job
    if not isinstance(job, dict):
        raise ValueError(
            f"a scheduled job must be a mapping, got {job!r}")
    unknown = set(job) - _JOB_KEYS
    if unknown:
        raise ValueError(
            "unknown scheduled job keys: %s"
            % ", ".join(sorted(unknown)))
    if "argv" in job and "command" in job \
            and job["argv"] != job["command"]:
        raise ValueError("a scheduled job names two different commands")
    if "argv" not in job and "command" not in job:
        raise ValueError("a scheduled job is missing its argv command")
    argv = job["argv"] if "argv" in job else job["command"]
    if "label" in job and "name" in job and job["label"] != job["name"]:
        raise ValueError("a scheduled job names two different labels")
    label = job.get("label", job.get("name", ""))
    if "schedule" not in job:
        raise ValueError("a scheduled job is missing its schedule")
    approval: Any = "unattended"
    if "approval" in job:
        approval = job["approval"]
    if "requires_approval" in job:
        wanted = normalize_approval(job["requires_approval"])
        if "approval" in job and normalize_approval(approval) != wanted:
            raise ValueError(
                "a scheduled job names two different approval postures")
        approval = wanted
    kwargs: Dict[str, Any] = {
        "label": label, "argv": argv,
        "schedule": validate_schedule(job["schedule"]),
        "approval": approval,
    }
    job_id = job.get("job_id", job.get("id"))
    if "job_id" in job and "id" in job and job["job_id"] != job["id"]:
        raise ValueError("a scheduled job names two different job ids")
    if job_id is not None:
        kwargs["job_id"] = job_id
    if "cwd" in job:
        kwargs["cwd"] = job["cwd"]
    if "enabled" in job:
        kwargs["enabled"] = job["enabled"]
    return ScheduledJob(**kwargs)


def build_scheduled_job(job: Any = None, **kwargs: Any) -> ScheduledJob:
    """Build one validated scheduled job."""
    if isinstance(job, ScheduledJob) and not kwargs:
        return job
    if isinstance(job, dict) or job is None:
        merged: Dict[str, Any] = {}
        if isinstance(job, dict):
            merged.update(job)
        merged.update(kwargs)
        return validate_scheduled_job(merged)
    raise ValueError(
        f"a scheduled job must be a mapping, got {job!r}")


def _require_job(job: Any) -> ScheduledJob:
    if isinstance(job, ScheduledJob):
        return job
    return validate_scheduled_job(job)


# ---------------------------------------------------------------------
# Due moments and the mechanical verdict.
# ---------------------------------------------------------------------


def _time_of(schedule: Schedule) -> time:
    hour, minute = schedule.time_of_day.split(":")
    return time(int(hour), int(minute))


def _interval_anchor(schedule: Schedule, moment: datetime) -> datetime:
    if schedule.anchor is not None:
        return schedule.anchor
    return moment.replace(hour=0, minute=0, second=0, microsecond=0)


def next_due(job: Any, after: Any) -> datetime:
    """The earliest schedule moment at or after ``after``.

    Deterministic and purely from the schedule:
    a daily job's next moment is today at its
    time, or tomorrow's when that has passed; a
    weekly job's is the named weekday at its
    time, this week or next; an interval job's
    is the anchor plus a whole number of
    intervals (an unanchored interval counts
    from the start of ``after``'s day). Exactly
    at a schedule moment, that moment is the
    next due - it is due then, not a cycle later.
    """
    current = _require_job(job)
    moment = _check_moment(after, "a next-due moment")
    schedule = current.schedule
    if schedule.kind == "daily":
        candidate = datetime.combine(moment.date(), _time_of(schedule))
        if candidate < moment:
            candidate += timedelta(days=1)
        return candidate
    if schedule.kind == "weekly":
        wanted = WEEKDAYS.index(schedule.weekday)
        ahead = (wanted - moment.weekday()) % 7
        candidate = datetime.combine(
            moment.date() + timedelta(days=ahead), _time_of(schedule))
        if candidate < moment:
            candidate += timedelta(days=7)
        return candidate
    anchor = _interval_anchor(schedule, moment)
    step = timedelta(minutes=schedule.interval_minutes)
    if moment <= anchor:
        return anchor
    elapsed = moment - anchor
    ticks = elapsed // step
    candidate = anchor + ticks * step
    if candidate < moment:
        candidate += step
    return candidate


def due_at_or_before(job: Any, now: Any) -> Optional[datetime]:
    """The latest schedule moment at or before ``now``, or None.

    None only for an interval job judged before
    its anchor - no tick has happened yet.
    """
    current = _require_job(job)
    moment = _check_moment(now, "a due moment")
    schedule = current.schedule
    if schedule.kind == "daily":
        candidate = datetime.combine(moment.date(), _time_of(schedule))
        if candidate > moment:
            candidate -= timedelta(days=1)
        return candidate
    if schedule.kind == "weekly":
        wanted = WEEKDAYS.index(schedule.weekday)
        back = (moment.weekday() - wanted) % 7
        candidate = datetime.combine(
            moment.date() - timedelta(days=back), _time_of(schedule))
        if candidate > moment:
            candidate -= timedelta(days=7)
        return candidate
    anchor = _interval_anchor(schedule, moment)
    if moment < anchor:
        return None
    step = timedelta(minutes=schedule.interval_minutes)
    ticks = (moment - anchor) // step
    return anchor + ticks * step


@dataclass(frozen=True)
class DueVerdict:
    """One scheduled job judged at one moment.

    ``status`` is the mechanical reading of the
    job at that moment: disabled, not_due, due
    (exactly at its moment), overdue (past it),
    or waiting_for_approval (due, but its posture
    is needs_approval). ``action`` is what is
    owed: none, run, or await_approval - a
    needs_approval job is never owed a run.
    ``due_at`` is the pending schedule moment, or
    None when none is pending; ``next_due_at``
    is the next schedule moment after the judged
    moment's pending slot.
    """

    job_id: Optional[str] = None
    label: str = ""
    status: str = "not_due"
    action: str = "none"
    due_at: Optional[datetime] = None
    next_due_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if self.job_id is not None:
            object.__setattr__(
                self, "job_id", normalize_job_id(self.job_id))
        if not isinstance(self.label, str):
            raise ValueError(
                f"a verdict label must be text, got {self.label!r}")
        if self.status not in DUE_STATUSES:
            raise ValueError(
                "a due status must be one of %s, got %r"
                % ("/".join(DUE_STATUSES), self.status))
        if self.action not in DUE_ACTIONS:
            raise ValueError(
                "a due action must be one of %s, got %r"
                % ("/".join(DUE_ACTIONS), self.action))
        if self.due_at is not None:
            object.__setattr__(
                self, "due_at", _check_moment(self.due_at, "a due time"))
        if self.next_due_at is not None:
            object.__setattr__(
                self, "next_due_at",
                _check_moment(self.next_due_at, "a next due time"))
        if self.status in ("not_due", "disabled") and self.action != "none":
            raise ValueError(
                f"a {self.status} verdict owes no action, "
                f"got {self.action!r}")
        if self.status in ("due", "overdue") and self.action != "run":
            raise ValueError(
                f"a {self.status} verdict owes a run, "
                f"got {self.action!r}")
        if self.status == "waiting_for_approval" \
                and self.action != "await_approval":
            raise ValueError(
                "a waiting_for_approval verdict owes an approval "
                f"wait, got {self.action!r}")
        if self.status in ("due", "overdue", "waiting_for_approval") \
                and self.due_at is None:
            raise ValueError(f"a {self.status} verdict names its due time")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "scheduled_job_verdict",
            "slice": SCHEDULED_WORK_SLICE,
            "job_id": self.job_id,
            "label": self.label,
            "status": self.status,
            "action": self.action,
            "due_at": self.due_at.isoformat() if self.due_at else None,
            "next_due_at": (
                self.next_due_at.isoformat() if self.next_due_at else None),
        }


def judge_job(job: Any, now: Any,
              last_run_at: Any = None) -> DueVerdict:
    """Judge one job at ``now``, mechanically.

    The pending moment is the latest schedule
    moment at or before ``now`` that no recorded
    run covers: a ``last_run_at`` at or after
    that moment means the slot already ran, and
    the job is not due. A disabled job is judged
    disabled before anything else. Of a pending
    job, a needs_approval posture is judged
    waiting_for_approval - due and waiting,
    never owed a run; an unattended job is due
    exactly at its moment and overdue past it,
    owed a run either way. A ``last_run_at``
    after ``now`` raises - time never runs
    backwards.
    """
    current = _require_job(job)
    moment = _check_moment(now, "a judgement time")
    last_run: Optional[datetime] = None
    if last_run_at is not None:
        last_run = _check_moment(last_run_at, "a last run time")
        if last_run > moment:
            raise ValueError(
                f"a last run at {last_run} is after the judgement "
                f"moment {moment}; time never runs backwards")
    upcoming = next_due(current, moment)
    if not current.enabled:
        return DueVerdict(
            job_id=current.job_id, label=current.display_label,
            status="disabled", action="none", next_due_at=upcoming)
    pending = due_at_or_before(current, moment)
    if pending is None or (last_run is not None and pending <= last_run):
        following = upcoming
        if last_run is not None and following <= last_run:
            following = _next_after(current, last_run)
        return DueVerdict(
            job_id=current.job_id, label=current.display_label,
            status="not_due", action="none", next_due_at=following)
    if current.requires_approval:
        status, action = "waiting_for_approval", "await_approval"
    elif moment == pending:
        status, action = "due", "run"
    else:
        status, action = "overdue", "run"
    return DueVerdict(
        job_id=current.job_id, label=current.display_label,
        status=status, action=action, due_at=pending,
        next_due_at=_next_after(current, pending))


def _next_after(job: ScheduledJob, moment: datetime) -> datetime:
    """The first schedule moment strictly after ``moment``."""
    candidate = next_due(job, moment)
    if candidate > moment:
        return candidate
    return next_due(job, moment + _smallest_step(job))


def _smallest_step(job: ScheduledJob) -> timedelta:
    schedule = job.schedule
    if schedule.kind == "interval":
        return timedelta(minutes=schedule.interval_minutes)
    if schedule.kind == "weekly":
        return timedelta(days=7)
    return timedelta(days=1)


# ---------------------------------------------------------------------
# Due, shaped as session news.
# ---------------------------------------------------------------------


def _due_headline(verdict: DueVerdict, job: ScheduledJob) -> str:
    name = verdict.job_id or verdict.label
    due_text = verdict.due_at.strftime("%Y-%m-%d %H:%M")
    if verdict.action == "await_approval":
        return (
            f"Scheduled: {verdict.label} ({name}) came due at "
            f"{due_text} and is waiting for approval - scheduled "
            "work keeps the approval lines of live work, so it "
            "does not run unattended.")
    lateness = "overdue" if verdict.status == "overdue" else "due"
    return (
        f"Scheduled: {verdict.label} ({name}) is {lateness} "
        f"(due at {due_text}) - running it is owed.")


def due_record(verdict: Any, job: Any) -> Optional[Dict[str, Any]]:
    """The session-news record of one owed due moment, or None.

    A verdict whose action is ``none`` returns
    None - the agent layer publishes this record
    as a session event when it is not None, so a
    due moment can never be lost as a mere log
    line, and never announced when none is owed.
    """
    current = _require_job(job)
    if not isinstance(verdict, DueVerdict):
        raise ValueError(f"a due verdict is needed, got {verdict!r}")
    if verdict.action == "none":
        return None
    return {
        "type": "scheduled_job_due",
        "news": True,
        "job_id": verdict.job_id,
        "label": verdict.label,
        "status": verdict.status,
        "action": verdict.action,
        "approval": current.approval,
        "due_at": verdict.due_at.isoformat() if verdict.due_at else None,
        "headline": _due_headline(verdict, current),
    }


def format_due_record(record: Any) -> str:
    """One due record as its plain headline."""
    if isinstance(record, dict) \
            and record.get("type") == "scheduled_job_due":
        return str(record["headline"])
    raise ValueError("format_due_record needs a scheduled job due record")


# ---------------------------------------------------------------------
# The registry model: jobs held in registration order, ids
# deterministic; run moments held alongside.
# ---------------------------------------------------------------------


class ScheduledWorkRegistry:
    """An in-memory registry of scheduled jobs.

    Jobs are held in registration order and
    replaced, never mutated, as they change. Ids
    are deterministic: a caller-supplied id is
    used as given (a duplicate refuses), and an
    unsupplied id is the next ``schedule-N`` in
    sequence, skipping any number a supplied id
    already took - no randomness a test cannot
    pin. Run moments are held as data alongside
    the jobs (``record_run``), so a check judges
    each job against its own last run. Storage
    beyond memory (a session's journal, a file)
    is the agent layer's concern; this model is
    neutral.
    """

    def __init__(self) -> None:
        self._jobs: Dict[str, ScheduledJob] = {}
        self._last_runs: Dict[str, datetime] = {}
        self._next = 1

    def _fresh_id(self) -> str:
        while f"schedule-{self._next}" in self._jobs:
            self._next += 1
        job_id = f"schedule-{self._next}"
        self._next += 1
        return job_id

    def register(self, job: Any) -> ScheduledJob:
        """Register one job and hold it; duplicate ids refuse."""
        validated = _require_job(job)
        if validated.job_id is None:
            validated = replace(validated, job_id=self._fresh_id())
        elif validated.job_id in self._jobs:
            raise ValueError(
                f"a scheduled job named {validated.job_id!r} "
                "already exists")
        self._jobs[validated.job_id] = validated
        return validated

    def get(self, job_id: Any) -> ScheduledJob:
        """The job one id names; an unknown id raises KeyError."""
        wanted = normalize_job_id(job_id)
        if wanted not in self._jobs:
            raise KeyError(f"unknown scheduled job: {wanted!r}")
        return self._jobs[wanted]

    def list_jobs(self, enabled: Any = None) -> Tuple[ScheduledJob, ...]:
        """Every held job, in registration order, optionally by enabled."""
        jobs = tuple(self._jobs.values())
        if enabled is None:
            return jobs
        if not isinstance(enabled, bool):
            raise ValueError(
                f"an enabled filter must be true or false, "
                f"got {enabled!r}")
        return tuple(j for j in jobs if j.enabled == enabled)

    def record_run(self, job_id: Any, at: Any) -> ScheduledJob:
        """Record one run moment for a held job; backwards refuses."""
        job = self.get(job_id)
        moment = _check_moment(at, "a run time")
        previous = self._last_runs.get(job.job_id)
        if previous is not None and moment < previous:
            raise ValueError(
                f"a run at {moment} is earlier than the job's last "
                f"run at {previous}; time never runs backwards")
        self._last_runs[job.job_id] = moment
        return job

    def last_run(self, job_id: Any) -> Optional[datetime]:
        """The last recorded run moment for one job, or None."""
        job = self.get(job_id)
        return self._last_runs.get(job.job_id)

    def check(self, now: Any) -> Tuple[DueVerdict, ...]:
        """Every held job judged at ``now``, in registration order."""
        moment = _check_moment(now, "a judgement time")
        return tuple(
            judge_job(job, moment, self._last_runs.get(job.job_id))
            for job in self._jobs.values())

    def due_records(self, now: Any) -> Tuple[Dict[str, Any], ...]:
        """The owed due records at ``now``, in registration order."""
        moment = _check_moment(now, "a judgement time")
        records = []
        for job in self._jobs.values():
            record = due_record(
                judge_job(job, moment, self._last_runs.get(job.job_id)),
                job)
            if record is not None:
                records.append(record)
        return tuple(records)


# ---------------------------------------------------------------------
# The /schedule surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------


def format_schedule(schedule: Any) -> str:
    """One schedule, in plain words."""
    current = validate_schedule(schedule) \
        if not isinstance(schedule, Schedule) else schedule
    if current.kind == "daily":
        return f"daily at {current.time_of_day}"
    if current.kind == "weekly":
        return f"weekly on {current.weekday} at {current.time_of_day}"
    if current.interval_minutes % 60 == 0:
        hours = current.interval_minutes // 60
        return f"every {hours} hour" + ("s" if hours != 1 else "")
    return f"every {current.interval_minutes} minutes"


def format_verdict(verdict: Any) -> str:
    """One verdict, in plain words."""
    if not isinstance(verdict, DueVerdict):
        raise ValueError(f"a due verdict is needed, got {verdict!r}")
    name = verdict.job_id or verdict.label
    if verdict.status == "disabled":
        following = verdict.next_due_at.strftime("%Y-%m-%d %H:%M") \
            if verdict.next_due_at else "none"
        return (
            f"{name}: {verdict.label} [disabled] - it does not "
            f"run; its next schedule moment would be {following}.")
    if verdict.status == "not_due":
        following = verdict.next_due_at.strftime("%Y-%m-%d %H:%M") \
            if verdict.next_due_at else "none"
        return (
            f"{name}: {verdict.label} [not due] - next due "
            f"{following}; no action owed.")
    due_text = verdict.due_at.strftime("%Y-%m-%d %H:%M")
    if verdict.status == "waiting_for_approval":
        return (
            f"{name}: {verdict.label} [waiting for approval] - "
            f"due at {due_text}; action owed: wait for approval, "
            "never run unattended.")
    return (
        f"{name}: {verdict.label} [{verdict.status}] - due at "
        f"{due_text}; action owed: run it.")


def format_scheduled_job(job: Any, now: Any = None) -> str:
    """One job, in plain words, judged at ``now`` when given."""
    current = _require_job(job)
    if now is not None:
        return format_verdict(judge_job(current, now))
    name = current.job_id or current.display_label
    enabled_word = "enabled" if current.enabled else "disabled"
    return (
        f"{name}: {current.display_label} [{enabled_word}, "
        f"{current.approval}] - {format_schedule(current.schedule)}; "
        f"runs: {current.command_text}")


def format_scheduled_jobs(jobs: Any = None, now: Any = None) -> str:
    """The jobs, in plain words, in the order given.

    With no jobs at all the text starts with the
    plain statement of that fact. Every line
    states its due or enabled state in words; a
    due or waiting job's line states its due
    moment and its owed action.
    """
    if jobs is None:
        selected: Tuple[ScheduledJob, ...] = ()
    elif isinstance(jobs, ScheduledWorkRegistry):
        selected = jobs.list_jobs()
    else:
        if isinstance(jobs, (str, bytes)) \
                or not isinstance(jobs, (list, tuple)):
            raise ValueError("scheduled jobs must be a list of jobs")
        selected = tuple(_require_job(j) for j in jobs)
    if not selected:
        return (
            "Scheduled jobs: none. No work is "
            "scheduled to run on a schedule.")
    lines = [f"Scheduled jobs: {len(selected)} held."]
    for job in selected:
        lines.append(f"  {format_scheduled_job(job, now)}")
    return "\n".join(lines)


def format_scheduled_work(registry: Any = None, now: Any = None) -> str:
    """The whole slice, in plain words, for /schedule."""
    lines = ["Scheduled work (M-105) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_scheduled_jobs(registry, now))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_schedule_args(args: Any) -> Tuple[str, Optional[str]]:
    """Parse the /schedule grammar both surfaces share.

    No words (or ``show``) shows the jobs;
    ``show <job>`` and a bare job id show one
    job; ``check`` asks for every job to be
    judged now. Anything else is a usage error
    naming the grammar. Returns
    ``(action, job-id-or-None)``.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None \
        else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() == "show":
        return ("show", None)
    words = text.split()
    head = words[0].lower()
    if head == "check" and len(words) == 1:
        return ("check", None)
    if head == "show" and len(words) == 2:
        try:
            return ("show", normalize_job_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head in ("show", "check"):
        raise ValueError(USAGE)
    if len(words) == 1:
        try:
            return ("show", normalize_job_id(words[0]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
