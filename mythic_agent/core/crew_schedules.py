"""Crew on schedule (All-Features roadmap slice M-145).

Part VI continues here. The roadmap's words:
``formations can be attached to Part V's scheduled
jobs (a dawn Auditor sweep over yesterday's
commits).``

What already shipped, and what this slice adds:

* Part V's scheduled jobs are already data
  (``core/scheduled_work.py``, M-105): a job -
  what to run (an argv list, never a shell
  string), when it runs (a schedule: daily at a
  named time, weekly on a named weekday, or
  every N minutes or hours), whether it is
  enabled, and its approval posture - validated
  as data, judged due mechanically, and carried
  out by the agent layer's scheduled check when
  a run is owed. That job record is composed
  here BY IMPORT, whole: an attachment's job is
  an M-105 ``ScheduledJob``, read by that layer's
  own builders, so an attached job answers to
  exactly the validators a live scheduled job
  answers to.
* The crew's formations are already data too
  (``core/crew_templates.py``, M-143): a saved
  formation summonable by name, its name read by
  the M-121 casting layer's
  ``normalize_member_id`` - the reading composed
  here by import for an attachment's formation
  name and template id, so a formation is named
  exactly as the template book names one. The
  template record itself is NOT composed: an
  attachment names a formation by its word and
  its template id; it does not restate the
  formation's seats, which stay the template
  book's own record.
* What nothing holds is the attachment itself,
  as data: a named joining of one formation to
  one scheduled job, from which alone the
  attachment's standing is judged.
* This slice is that attachment book, as a pure
  layer: an attachment record validated as data
  (one formation attached to one scheduled job,
  named in plain words), an attachment report
  per attachment whose checks, standing, action
  and account are DERIVED from the attachment's
  job, an attachment index whose rows, totals
  and account are DERIVED from the whole book,
  the shipped data file
  (``mythic_agent/data/crew_schedules.yaml``)
  holding one example attachment book in exactly
  the shape a real crew schedules file takes, a
  loader for a crew schedules file anywhere on
  disk, records shaped as session news, and a
  small in-memory registry model. This module
  starts no timer, runs no job, summons no crew,
  spawns no agent and imports no agent / UI code;
  the agent layer owns holding an attachment
  book for a session.

Honesty rules, enforced here and pinned by tests:

* **Standing is derived, never stored loose.**
  An attachment record names its job - enabled
  or disabled, unattended or needs approval -
  and no standing and no action of its own:
  whether the attached formation runs when the
  job's moment comes (armed), waits for approval
  (waiting_for_approval) or is owed nothing
  because its job is disabled (disabled) is read
  off the job at call time, so a stored
  ``standing`` / ``status`` / ``action`` key on
  a record refuses as an unknown key, and no
  attachment can claim a readiness its job does
  not give it.
* **The job is Part V's own record.** A job
  reads exactly as the M-105 layer reads one,
  composed by import - its argv a list of words,
  never a shell string; its schedule daily,
  weekly or interval; its approval posture the
  live-work lines - so every attached job
  answers to exactly the validator the live
  scheduled jobs answer to. An attachment names
  its job whole, job id and all: an unnamed job
  cannot be attached, because there would be no
  job to name.
* **One job, one formation.** A book or registry
  holding two attachments on one job id, or two
  attachments under one attachment id, refuses:
  a job with two formations attached would run
  neither honestly. One formation may stand on
  many jobs.
* **A report is derived, never stored loose.**
  An attachment report's checks, standing,
  action and account are read off its
  attachment's job, in held order, so a stored
  report that disagrees with the report derived
  from its attachment refuses. A report naming
  no account of its own refuses too.
* **The index is derived, never stored loose.**
  The index's rows are the book's reports, in
  held order; its totals are read off the
  records (every attachment held, those armed,
  those waiting, those on disabled jobs, and
  every distinct formation standing on a job)
  and its account is read off the rows and
  totals, so a stored index whose rows, totals
  or account disagree with the derived index
  refuses.
* **Data only - no live road is claimed.** An
  attachment here is a validated record held as
  data: no timer is started, no job is run, no
  crew is summoned or spawned and nothing is
  persisted. The M-105 agent road still carries
  due jobs out as plain background jobs exactly
  as before - attaching a formation changes no
  execution; it names the crew that stands on
  the job when its moment comes. The attachments
  are visible through this slice's own
  /crewschedules screen.
* **Malformed refuses.** A duplicate attachment
  id or job id in one book, a report or index
  naming an attachment the book holds no record
  for, and unknown keys in a record, a report,
  an index or an attachment mapping all raise
  instead of being skipped or guessed at.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..resources import load_resource
from .crew_members import normalize_member_id
from .scheduled_work import (
    ScheduledJob,
    format_schedule,
    normalize_job_id,
    validate_scheduled_job,
)
from .validation import ValidationError

__all__ = [
    "PLAIN_EXPLANATION",
    "CREW_SCHEDULES_RESOURCE",
    "CREW_SCHEDULES_SCHEMA",
    "CREW_SCHEDULES_SLICE",
    "STANDINGS",
    "USAGE",
    "AttachmentIndex",
    "AttachmentReport",
    "CrewAttachment",
    "CrewScheduleBook",
    "CrewScheduleRegistry",
    "attachment_record",
    "book_record",
    "build_attachment",
    "build_book",
    "build_index",
    "build_report",
    "derive_index",
    "derive_report",
    "format_attachment",
    "format_attachments",
    "format_crew_schedules_screen",
    "format_index",
    "format_report",
    "index_plain_words",
    "index_record",
    "load_crew_schedules",
    "load_crew_schedules_file",
    "normalize_standing",
    "parse_crew_schedules_args",
    "plain_words",
    "report_plain_words",
    "report_record",
    "validate_attachment",
    "validate_book",
    "validate_index",
    "validate_report",
]

CREW_SCHEDULES_SLICE = "M-145"

#: The packaged data resource holding the example book.
CREW_SCHEDULES_RESOURCE = "crew_schedules.yaml"

#: The schema word a crew schedules file must carry.
CREW_SCHEDULES_SCHEMA = "mythic.crew_schedules/1"

#: The standings an attachment may derive, in
#: roadmap order: armed to run when its job's
#: moment comes, waiting for approval at that
#: moment, or disabled with its job.
STANDINGS = ("armed", "waiting_for_approval", "disabled")

#: The actions an attachment owes when its job's
#: moment comes, one per standing.
ATTACHMENT_ACTIONS = ("run", "await_approval", "none")

_ATTACHMENT_KEYS = frozenset({
    "attachment_id", "id", "title", "headline",
    "detail", "description", "purpose",
    "template", "formation", "template_id",
    "job", "scheduled_job",
})

_REPORT_KEYS = frozenset({
    "report_id", "id", "attachment_id",
    "template", "formation", "template_id",
    "job_id", "job", "schedule_text", "schedule",
    "checks", "findings", "standing", "status",
    "action", "account", "statements",
})

_INDEX_KEYS = frozenset({
    "index_id", "id", "rows", "reports",
    "total_attachments", "attachments",
    "total_armed", "armed",
    "total_waiting", "waiting",
    "total_disabled", "disabled",
    "total_templates", "templates",
    "account", "statements",
})

_BOOK_KEYS = frozenset({"title", "name"})

_CREW_SCHEDULES_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "schedules_note", "guide", "entries", "indexes",
})

#: The shipped example book's title, held to this
#: by the loader's example check.
_EXAMPLE_TITLE = "Crew schedule book at the M-144 slice boundary"

#: The shipped example's attachment ids, in held
#: order, pinned by the loader.
_EXAMPLE_ATTACHMENT_IDS = (
    "att-dawn-auditor-sweep", "att-weekly-full-six",
    "att-research-swarm-watch", "att-weekend-duo-paused")

#: The shipped example's formations, in held
#: order, pinned by the loader: the roadmap's
#: dawn Auditor sweep first.
_EXAMPLE_TEMPLATES = (
    "review_panel", "full_six", "research_swarm", "duo")

#: The shipped example's job ids, in held order,
#: pinned by the loader - one job per attachment.
_EXAMPLE_JOB_IDS = (
    "dawn-auditor-sweep", "weekly-full-six",
    "research-swarm-watch", "weekend-duo-sweep")

#: The shipped example's derived standings, in
#: held order, pinned by the loader: two armed,
#: one waiting for approval, one disabled.
_EXAMPLE_STANDINGS = (
    "armed", "waiting_for_approval", "armed", "disabled")

#: The shipped example's one index: its rows are
#: the attachments in held order and its totals
#: are pinned by the loader.
_EXAMPLE_INDEX_ID = "index-m144-boundary"

_EXAMPLE_INDEX_ROWS = (
    "review_panel", "full_six", "research_swarm", "duo")

_EXAMPLE_INDEX_TOTALS = (4, 2, 1, 1, 4)

_EXAMPLE_INDEX_ACCOUNT = (
    "The book holds 4 crew schedule attachment(s): "
    "2 armed to run when due, 1 waiting for "
    "approval, 1 on disabled jobs.",
    "Every standing word here is derived from the "
    "held records' jobs - enabled and approval "
    "read off the Part V job each attachment "
    "names - never stored loose.",
    "An attachment here joins a formation to a "
    "scheduled job as data; nothing in this book "
    "runs a job or summons a crew.",
)

#: The shipped example's pinned first report: the
#: dawn Auditor sweep's checks read off its job,
#: its account pinned word-for-word by the loader.
_EXAMPLE_FIRST_REPORT_CHECKS = (
    "formation review_panel: attached by name",
    "schedule daily at 06:00: stated",
    "approval unattended: runs when its moment comes",
)

_EXAMPLE_FIRST_REPORT_ACCOUNT = (
    "Formation review_panel is attached to "
    "scheduled job dawn-auditor-sweep: daily at "
    "06:00, running when its moment comes.",
    "The attachment keeps the scheduled job's own "
    "approval line: unattended work runs when "
    "due, exactly as live work would.",
    "This record runs nothing: it is data only, "
    "and no crew is summoned by this layer.",
)

PLAIN_EXPLANATION = (
    "Crew on schedule: formations can be attached "
    "to Part V's scheduled jobs - a dawn Auditor "
    "sweep over yesterday's commits. An attachment "
    "record names one formation, by the name the "
    "crew template book summons it by, joined to "
    "one scheduled job held whole as Part V data: "
    "what it runs, when it runs, whether it is "
    "enabled and its approval posture. Whether the "
    "formation runs when the job's moment comes, "
    "waits for approval, or is owed nothing because "
    "its job is disabled is derived from the job, "
    "never stored loose, and the attachment reports "
    "and the attachment index are read off the held "
    "records, so a stored form that disagrees "
    "refuses. This layer holds attachments as data "
    "only; it starts no timer, runs no job, summons "
    "no crew, spawns no agent and persists nothing "
    "itself."
)

USAGE = (
    "Usage: /crewschedules, /crewschedules show, "
    "/crewschedules attachment <attachment-id>, "
    "/crewschedules template <template>, "
    "/crewschedules job <job-id>, "
    "/crewschedules report <attachment-id>, "
    "/crewschedules index"
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


def _check_bool(value: Any, what: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{what} must be true or false, got {value!r}")
    return value


def normalize_standing(value: Any) -> str:
    """The canonical attachment standing a word names.

    A standing is ``armed`` (the job is enabled
    and unattended), ``waiting_for_approval``
    (enabled, but its posture is needs approval)
    or ``disabled`` (its job is disabled), read
    case-insensitively with dashes read as
    underscores. Anything else raises.
    """
    if isinstance(value, str):
        wanted = value.strip().lower().replace("-", "_")
        if wanted in STANDINGS:
            return wanted
    raise ValueError(
        "an attachment standing must be one of %s, got %r"
        % ("/".join(STANDINGS), value))


def _standing_of(job: ScheduledJob) -> str:
    """An attachment's standing, derived from its job."""
    if not job.enabled:
        return "disabled"
    if job.requires_approval:
        return "waiting_for_approval"
    return "armed"


def _action_of(standing: str) -> str:
    """The action owed at the due moment, per standing."""
    if standing == "armed":
        return "run"
    if standing == "waiting_for_approval":
        return "await_approval"
    return "none"


def _formation_check(template: str) -> str:
    return f"formation {template}: attached by name"


def _schedule_check(schedule_text: str) -> str:
    return f"schedule {schedule_text}: stated"


def _action_check(standing: str) -> str:
    if standing == "armed":
        return "approval unattended: runs when its moment comes"
    if standing == "waiting_for_approval":
        return "approval needs approval: waits when its moment comes"
    return "job disabled: does not run"


#: Every action check a report may carry, one per
#: standing, in STANDINGS order.
_ACTION_CHECKS = tuple(_action_check(s) for s in STANDINGS)


def _check_checks(value: Any, template: str,
                  schedule_text: str) -> Tuple[str, ...]:
    if isinstance(value, (str, bytes)) \
            or not isinstance(value, (list, tuple)):
        raise ValueError(f"a report's checks must be a list, got {value!r}")
    checks = tuple(
        _check_long_text(c, "a report check") for c in value)
    if len(checks) != 3:
        raise ValueError(
            "an attachment report carries exactly three "
            "checks: formation, schedule and action")
    if checks[0] != _formation_check(template):
        raise ValueError(
            f"a report's formation check names its own "
            f"formation, got {checks[0]!r}")
    if checks[1] != _schedule_check(schedule_text):
        raise ValueError(
            f"a report's schedule check names its own "
            f"schedule, got {checks[1]!r}")
    if checks[2] not in _ACTION_CHECKS:
        raise ValueError(
            f"a report check names no known action: {checks[2]!r}")
    return checks


def _standing_phrase(standing: str) -> str:
    if standing == "armed":
        return "armed to run when due"
    if standing == "waiting_for_approval":
        return "waiting for approval when due"
    return "disabled, so nothing is owed"


# ---------------------------------------------------------------------
# The attachment record: one formation on one job, as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class CrewAttachment:
    """One formation attached to one scheduled job.

    ``template`` is the formation's own word - the
    name the crew template book summons it by -
    and ``template_id`` its template id when the
    attachment names one. ``title`` names the
    attachment in plain words and ``detail`` says
    what the formation stands on the job to do.
    ``job`` is the scheduled job whole, a Part V
    (M-105) ``ScheduledJob``: what it runs, when
    it runs, whether it is enabled and its
    approval posture, and it always names its job
    id. The record names NO standing and NO action
    of its own: both are read off the job, so an
    attachment can never claim a readiness its job
    does not give it.
    """

    template: str
    title: str
    detail: str
    job: ScheduledJob
    template_id: Optional[str] = None
    attachment_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.attachment_id is not None:
            object.__setattr__(
                self, "attachment_id",
                normalize_member_id(self.attachment_id))
        object.__setattr__(
            self, "template", normalize_member_id(self.template))
        object.__setattr__(
            self, "title",
            _check_title(self.title, "an attachment's title"))
        object.__setattr__(
            self, "detail",
            _check_long_text(self.detail, "an attachment's detail"))
        if self.template_id is not None:
            object.__setattr__(
                self, "template_id",
                normalize_member_id(self.template_id))
        job = self.job
        if not isinstance(job, ScheduledJob):
            job = validate_scheduled_job(job)
            object.__setattr__(self, "job", job)
        if job.job_id is None:
            raise ValueError(
                "an attachment's job names its job id: "
                "an unnamed job cannot be attached")

    @property
    def job_id(self) -> str:
        """The attached job's id, read off the job."""
        return self.job.job_id or ""

    @property
    def schedule_text(self) -> str:
        """The attached job's schedule, in plain words."""
        return format_schedule(self.job.schedule)

    @property
    def standing(self) -> str:
        """The attachment's standing, derived from its job."""
        return _standing_of(self.job)

    @property
    def action(self) -> str:
        """The action owed when due, derived from its job."""
        return _action_of(self.standing)

    @property
    def checks(self) -> Tuple[str, ...]:
        """The report checks, derived from the attachment."""
        return (
            _formation_check(self.template),
            _schedule_check(self.schedule_text),
            _action_check(self.standing))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "crew_schedule_attachment",
            "slice": CREW_SCHEDULES_SLICE,
            "attachment_id": self.attachment_id,
            "template": self.template,
            "template_id": self.template_id,
            "title": self.title,
            "detail": self.detail,
            "job": self.job.to_record(),
            "job_id": self.job_id,
            "schedule_text": self.schedule_text,
            "standing": self.standing,
            "action": self.action,
        }


def validate_attachment(attachment: Any) -> CrewAttachment:
    """Validate one attachment record into a CrewAttachment.

    Accepts a CrewAttachment or a mapping naming a
    ``template`` (or ``formation``), a ``title``
    (or ``headline``), a ``detail`` (or
    ``description`` / ``purpose``), a ``job`` (or
    ``scheduled_job``) - one Part V scheduled job
    mapping, read by the M-105 layer's own
    builder - an optional ``attachment_id`` (or
    ``id``) and an optional ``template_id``.
    Naming two spellings of one field with
    different values refuses, and unknown keys
    refuse - a stored standing or action key among
    them, because standing and action are derived
    from the job, never stored on a record.
    """
    if isinstance(attachment, CrewAttachment):
        return attachment
    if not isinstance(attachment, dict):
        raise ValueError(
            f"an attachment record must be a mapping, "
            f"got {attachment!r}")
    unknown = set(attachment) - _ATTACHMENT_KEYS
    if unknown:
        raise ValueError(
            "unknown attachment-record keys: %s"
            % ", ".join(sorted(unknown)))
    template = _pick_any(
        attachment, ("template", "formation"), "templates")
    if template is None:
        raise ValueError("an attachment record is missing its template")
    title = _pick_any(attachment, ("title", "headline"), "titles")
    if title is None:
        raise ValueError("an attachment record is missing its title")
    detail = _pick_any(
        attachment, ("detail", "description", "purpose"), "details")
    if detail is None:
        raise ValueError("an attachment record is missing its detail")
    job = _pick_any(attachment, ("job", "scheduled_job"), "jobs")
    if job is None:
        raise ValueError("an attachment record is missing its job")
    kwargs: Dict[str, Any] = {
        "template": template, "title": title, "detail": detail,
        "job": job}
    attachment_id = _pick_any(
        attachment, ("attachment_id", "id"), "attachment ids")
    if attachment_id is not None:
        kwargs["attachment_id"] = attachment_id
    template_id = _pick_any(
        attachment, ("template_id",), "template ids")
    if template_id is not None:
        kwargs["template_id"] = template_id
    return CrewAttachment(**kwargs)


def build_attachment(attachment: Any = None, **kwargs: Any) -> CrewAttachment:
    """Build one validated attachment record, from a mapping or field words."""
    if isinstance(attachment, CrewAttachment) and not kwargs:
        return attachment
    if isinstance(attachment, dict) or attachment is None:
        merged: Dict[str, Any] = {}
        if isinstance(attachment, dict):
            merged.update(attachment)
        merged.update(kwargs)
        return validate_attachment(merged)
    raise ValueError(
        f"an attachment record must be a mapping, got {attachment!r}")


def _check_attachment_ref(value: Any) -> CrewAttachment:
    if isinstance(value, CrewAttachment):
        return value
    if isinstance(value, dict):
        return validate_attachment(value)
    raise ValueError(f"an attachment record is needed, got {value!r}")


def _held_attachments(source: Any) -> Tuple[CrewAttachment, ...]:
    """The attachment records one source holds, in held order."""
    if isinstance(source, CrewScheduleBook):
        return source.entries
    if isinstance(source, CrewScheduleRegistry):
        return source.list_attachments()
    if isinstance(source, (list, tuple)):
        return tuple(_check_attachment_ref(e) for e in source)
    raise ValueError(f"attachment records are needed, got {source!r}")


# ---------------------------------------------------------------------
# The attachment report: one attachment judged, derived.
# ---------------------------------------------------------------------


def _report_account(template: str, job_id: str,
                    schedule_text: str,
                    standing: str) -> Tuple[str, ...]:
    if standing == "armed":
        return (
            f"Formation {template} is attached to "
            f"scheduled job {job_id}: {schedule_text}, "
            f"running when its moment comes.",
            "The attachment keeps the scheduled job's own "
            "approval line: unattended work runs when "
            "due, exactly as live work would.",
            "This record runs nothing: it is data only, "
            "and no crew is summoned by this layer.",
        )
    if standing == "waiting_for_approval":
        return (
            f"Formation {template} is attached to "
            f"scheduled job {job_id}: {schedule_text}, "
            f"waiting for approval when its moment comes.",
            "The attachment keeps the scheduled job's own "
            "approval line: a job that needs approval is "
            "recorded as due and waiting, never run "
            "unattended.",
            "This record runs nothing: it is data only, "
            "and no crew is summoned by this layer.",
        )
    return (
        f"Formation {template} is attached to "
        f"scheduled job {job_id}: {schedule_text}, "
        f"and the job is disabled, so nothing is owed.",
        "A disabled job does not run; the attachment "
        "stands as data until the job is enabled.",
        "This record runs nothing: it is data only, "
        "and no crew is summoned by this layer.",
    )


@dataclass(frozen=True)
class AttachmentReport:
    """One attachment's report, derived from its job.

    ``checks`` are the three readings judged, in
    formation / schedule / action order;
    ``standing`` is the attachment's standing and
    ``action`` the action owed when its job's
    moment comes; ``account`` is the report's own
    account. Every field is a derivation:
    :func:`validate_report` judged against an
    attachment refuses a report whose fields
    disagree with the report that attachment
    derives. A report's standing, action and
    action check must agree with each other at
    construction.
    """

    template: str
    job_id: str
    schedule_text: str
    checks: Tuple[str, ...] = ()
    standing: str = "armed"
    action: str = "run"
    account: Tuple[str, ...] = ()
    template_id: Optional[str] = None
    attachment_id: Optional[str] = None
    report_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.report_id is not None:
            object.__setattr__(
                self, "report_id", normalize_member_id(self.report_id))
        if self.attachment_id is not None:
            object.__setattr__(
                self, "attachment_id",
                normalize_member_id(self.attachment_id))
        object.__setattr__(
            self, "template", normalize_member_id(self.template))
        if self.template_id is not None:
            object.__setattr__(
                self, "template_id",
                normalize_member_id(self.template_id))
        object.__setattr__(
            self, "job_id", normalize_job_id(self.job_id))
        object.__setattr__(
            self, "schedule_text",
            _check_title(self.schedule_text, "a report's schedule text"))
        object.__setattr__(
            self, "standing", normalize_standing(self.standing))
        if self.action not in ATTACHMENT_ACTIONS:
            raise ValueError(
                "an attachment action must be one of %s, got %r"
                % ("/".join(ATTACHMENT_ACTIONS), self.action))
        if self.action != _action_of(self.standing):
            raise ValueError(
                "a report's action must be its own "
                "standing's action")
        checks = _check_checks(
            self.checks, self.template, self.schedule_text)
        object.__setattr__(self, "checks", checks)
        if checks[2] != _action_check(self.standing):
            raise ValueError(
                "a report's action check must be its own "
                "standing's check")
        object.__setattr__(self, "account", _check_account(self.account))

    @property
    def armed(self) -> bool:
        """Whether the attachment runs when due, derived."""
        return self.standing == "armed"

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "crew_schedule_report",
            "slice": CREW_SCHEDULES_SLICE,
            "report_id": self.report_id,
            "attachment_id": self.attachment_id,
            "template": self.template,
            "template_id": self.template_id,
            "job_id": self.job_id,
            "schedule_text": self.schedule_text,
            "checks": list(self.checks),
            "standing": self.standing,
            "action": self.action,
            "account": list(self.account),
        }


def derive_report(attachment: Any) -> AttachmentReport:
    """Derive one attachment's report from its record.

    The report's checks, standing, action and
    account are read off the attachment's job
    alone: its formation name, its schedule in
    plain words, and the standing its job's
    enabled flag and approval posture give it.
    """
    current = _check_attachment_ref(attachment)
    return AttachmentReport(
        template=current.template,
        job_id=current.job_id,
        schedule_text=current.schedule_text,
        checks=current.checks,
        standing=current.standing,
        action=current.action,
        account=_report_account(
            current.template, current.job_id,
            current.schedule_text, current.standing),
        template_id=current.template_id,
        attachment_id=current.attachment_id)


def validate_report(report: Any, source: Any = None) -> AttachmentReport:
    """Validate one attachment report into an AttachmentReport.

    Accepts an AttachmentReport or a mapping
    naming a ``template`` (or ``formation``), a
    ``job_id`` (or ``job``), a ``schedule_text``
    (or ``schedule``), ``checks`` (or
    ``findings``), a ``standing`` (or ``status``),
    an ``action``, an ``account`` (or
    ``statements``) and optional ``template_id``,
    ``attachment_id`` and ``report_id`` (or
    ``id``) spellings. With *source* given (one
    attachment record), the report is judged
    against the report derived from that
    attachment: a stored report whose template,
    job, schedule, checks, standing, action or
    account disagree with the derived report
    refuses. A report naming no account refuses
    too.
    """
    if isinstance(report, AttachmentReport):
        current = report
    elif isinstance(report, dict):
        unknown = set(report) - _REPORT_KEYS
        if unknown:
            raise ValueError(
                "unknown report keys: %s" % ", ".join(sorted(unknown)))
        template = _pick_any(report, ("template", "formation"), "templates")
        if template is None:
            raise ValueError("a report is missing its template")
        job_id = _pick_any(report, ("job_id", "job"), "job ids")
        if job_id is None:
            raise ValueError("a report is missing its job id")
        schedule_text = _pick_any(
            report, ("schedule_text", "schedule"), "schedule texts")
        if schedule_text is None:
            raise ValueError("a report is missing its schedule text")
        checks = _pick_any(report, ("checks", "findings"), "checks")
        if checks is None:
            raise ValueError("a report is missing its checks")
        standing = _pick_any(report, ("standing", "status"), "standings")
        if standing is None:
            raise ValueError("a report is missing its standing")
        action = _pick_any(report, ("action",), "actions")
        if action is None:
            raise ValueError("a report is missing its action")
        account = _pick_any(report, ("account", "statements"), "accounts")
        if account is None:
            raise ValueError("a report names no account of its own")
        kwargs: Dict[str, Any] = {
            "template": template, "job_id": job_id,
            "schedule_text": schedule_text, "checks": checks,
            "standing": standing, "action": action,
            "account": account}
        template_id = _pick_any(report, ("template_id",), "template ids")
        if template_id is not None:
            kwargs["template_id"] = template_id
        attachment_id = _pick_any(
            report, ("attachment_id",), "attachment ids")
        if attachment_id is not None:
            kwargs["attachment_id"] = attachment_id
        report_id = _pick_any(report, ("report_id", "id"), "report ids")
        if report_id is not None:
            kwargs["report_id"] = report_id
        current = AttachmentReport(**kwargs)
    else:
        raise ValueError(f"a report must be a mapping, got {report!r}")
    if source is not None:
        derived = derive_report(source)
        if (current.template != derived.template
                or current.template_id != derived.template_id
                or current.job_id != derived.job_id
                or current.schedule_text != derived.schedule_text
                or current.checks != derived.checks
                or current.standing != derived.standing
                or current.action != derived.action
                or current.account != derived.account):
            raise ValueError(
                "a stored report disagrees with the report "
                "derived from its attachment")
    return current


def build_report(report: Any = None, source: Any = None,
                 **kwargs: Any) -> AttachmentReport:
    """Build one validated report, from a mapping or field words."""
    if isinstance(report, AttachmentReport) and not kwargs:
        return validate_report(report, source)
    if isinstance(report, dict) or report is None:
        merged: Dict[str, Any] = {}
        if isinstance(report, dict):
            merged.update(report)
        merged.update(kwargs)
        return validate_report(merged, source)
    return validate_report(report, source)


# ---------------------------------------------------------------------
# The attachment index: the whole book, derived.
# ---------------------------------------------------------------------


def _index_account(rows: Tuple[AttachmentReport, ...],
                   total_attachments: int, total_armed: int,
                   total_waiting: int, total_disabled: int,
                   total_templates: int) -> Tuple[str, ...]:
    return (
        f"The book holds {total_attachments} crew "
        f"schedule attachment(s): {total_armed} armed "
        f"to run when due, {total_waiting} waiting for "
        f"approval, {total_disabled} on disabled jobs.",
        "Every standing word here is derived from the "
        "held records' jobs - enabled and approval "
        "read off the Part V job each attachment "
        "names - never stored loose.",
        "An attachment here joins a formation to a "
        "scheduled job as data; nothing in this book "
        "runs a job or summons a crew.",
    )


def _check_report_ref(value: Any) -> AttachmentReport:
    if isinstance(value, AttachmentReport):
        return value
    if isinstance(value, dict):
        return validate_report(value)
    raise ValueError(f"a report is needed, got {value!r}")


@dataclass(frozen=True)
class AttachmentIndex:
    """The attachment index of one crew schedule book.

    ``rows`` are the book's attachment reports, in
    held order; ``total_attachments`` is every
    attachment the book holds, ``total_armed``
    those running when due, ``total_waiting``
    those waiting for approval, ``total_disabled``
    those on disabled jobs and ``total_templates``
    every distinct formation standing on a job,
    and ``account`` is read off the rows and
    totals. An index whose totals are not its own
    rows' counts refuses at construction.
    """

    rows: Tuple[AttachmentReport, ...] = ()
    total_attachments: int = 0
    total_armed: int = 0
    total_waiting: int = 0
    total_disabled: int = 0
    total_templates: int = 0
    account: Tuple[str, ...] = ()
    index_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.index_id is not None:
            object.__setattr__(
                self, "index_id", normalize_member_id(self.index_id))
        if isinstance(self.rows, (str, bytes)) \
                or not isinstance(self.rows, (list, tuple)):
            raise ValueError(
                f"an index's rows must be a list of reports, "
                f"got {self.rows!r}")
        rows = tuple(_check_report_ref(r) for r in self.rows)
        object.__setattr__(self, "rows", rows)
        object.__setattr__(
            self, "total_attachments",
            _check_count(
                self.total_attachments, "an index's total attachments"))
        object.__setattr__(
            self, "total_armed",
            _check_count(self.total_armed, "an index's total armed"))
        object.__setattr__(
            self, "total_waiting",
            _check_count(self.total_waiting, "an index's total waiting"))
        object.__setattr__(
            self, "total_disabled",
            _check_count(self.total_disabled, "an index's total disabled"))
        object.__setattr__(
            self, "total_templates",
            _check_count(
                self.total_templates, "an index's total templates"))
        if self.total_attachments != len(rows):
            raise ValueError(
                "an index's attachment total must be its "
                "own rows' count")
        armed = sum(1 for row in rows if row.standing == "armed")
        if self.total_armed != armed:
            raise ValueError(
                "an index's armed total must be its "
                "rows' armed count")
        waiting = sum(
            1 for row in rows if row.standing == "waiting_for_approval")
        if self.total_waiting != waiting:
            raise ValueError(
                "an index's waiting total must be its "
                "rows' waiting count")
        if self.total_disabled != len(rows) - armed - waiting:
            raise ValueError(
                "an index's disabled total must be its "
                "rows' remaining count")
        templates = len({row.template for row in rows})
        if self.total_templates != templates:
            raise ValueError(
                "an index's template total must be its "
                "rows' distinct formation count")
        object.__setattr__(self, "account", _check_account(self.account))

    def row_for(self, attachment_id: Any) -> AttachmentReport:
        """The row one attachment id names in this index."""
        wanted = normalize_member_id(attachment_id)
        for row in self.rows:
            if row.attachment_id == wanted:
                return row
        raise KeyError(f"no row in the index: attachment {wanted!r}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "crew_schedule_index",
            "slice": CREW_SCHEDULES_SLICE,
            "index_id": self.index_id,
            "rows": [row.to_record() for row in self.rows],
            "total_attachments": self.total_attachments,
            "total_armed": self.total_armed,
            "total_waiting": self.total_waiting,
            "total_disabled": self.total_disabled,
            "total_templates": self.total_templates,
            "account": list(self.account),
        }


def derive_index(source: Any) -> AttachmentIndex:
    """Derive the attachment index from attachment records.

    The rows are the attachments' reports, in held
    order; the totals are the records' own derived
    counts and the account is read off the rows
    and totals. An empty source refuses - an index
    of nothing is no index.
    """
    entries = _held_attachments(source)
    if not entries:
        raise ValueError("an index needs at least one attachment record")
    rows = tuple(derive_report(entry) for entry in entries)
    total_armed = sum(1 for entry in entries if entry.standing == "armed")
    total_waiting = sum(
        1 for entry in entries
        if entry.standing == "waiting_for_approval")
    total_disabled = len(entries) - total_armed - total_waiting
    total_templates = len({entry.template for entry in entries})
    return AttachmentIndex(
        rows=rows,
        total_attachments=len(entries),
        total_armed=total_armed,
        total_waiting=total_waiting,
        total_disabled=total_disabled,
        total_templates=total_templates,
        account=_index_account(
            rows, len(entries), total_armed, total_waiting,
            total_disabled, total_templates))


def validate_index(index: Any, source: Any = None) -> AttachmentIndex:
    """Validate one attachment index into an AttachmentIndex.

    Accepts an AttachmentIndex or a mapping naming
    ``rows`` (or ``reports``),
    ``total_attachments`` (or ``attachments``),
    ``total_armed`` (or ``armed``),
    ``total_waiting`` (or ``waiting``),
    ``total_disabled`` (or ``disabled``),
    ``total_templates`` (or ``templates``), an
    ``account`` (or ``statements``) and an optional
    ``index_id`` (or ``id``). With *source* given,
    the index is judged against the index derived
    from those records: a stored index whose rows,
    totals or account disagree with the derived
    index refuses.
    """
    if isinstance(index, AttachmentIndex):
        current = index
    elif isinstance(index, dict):
        unknown = set(index) - _INDEX_KEYS
        if unknown:
            raise ValueError(
                "unknown index keys: %s" % ", ".join(sorted(unknown)))
        rows = _pick_any(index, ("rows", "reports"), "rows")
        if rows is None:
            raise ValueError("an index is missing its rows")
        total_attachments = _pick_any(
            index, ("total_attachments", "attachments"),
            "total attachments")
        if total_attachments is None:
            raise ValueError("an index is missing its total attachments")
        total_armed = _pick_any(
            index, ("total_armed", "armed"), "total armed")
        if total_armed is None:
            raise ValueError("an index is missing its total armed")
        total_waiting = _pick_any(
            index, ("total_waiting", "waiting"), "total waiting")
        if total_waiting is None:
            raise ValueError("an index is missing its total waiting")
        total_disabled = _pick_any(
            index, ("total_disabled", "disabled"), "total disabled")
        if total_disabled is None:
            raise ValueError("an index is missing its total disabled")
        total_templates = _pick_any(
            index, ("total_templates", "templates"), "total templates")
        if total_templates is None:
            raise ValueError("an index is missing its total templates")
        account = _pick_any(index, ("account", "statements"), "accounts")
        if account is None:
            raise ValueError("an index names no account of its own")
        kwargs: Dict[str, Any] = {
            "rows": rows, "total_attachments": total_attachments,
            "total_armed": total_armed, "total_waiting": total_waiting,
            "total_disabled": total_disabled,
            "total_templates": total_templates, "account": account}
        index_id = _pick_any(index, ("index_id", "id"), "index ids")
        if index_id is not None:
            kwargs["index_id"] = index_id
        current = AttachmentIndex(**kwargs)
    else:
        raise ValueError(f"an index must be a mapping, got {index!r}")
    if source is not None:
        derived = derive_index(source)
        if (current.rows != derived.rows
                or current.total_attachments != derived.total_attachments
                or current.total_armed != derived.total_armed
                or current.total_waiting != derived.total_waiting
                or current.total_disabled != derived.total_disabled
                or current.total_templates != derived.total_templates
                or current.account != derived.account):
            raise ValueError(
                "a stored index disagrees with the index "
                "derived from its records")
    return current


def build_index(index: Any = None, source: Any = None,
                **kwargs: Any) -> AttachmentIndex:
    """Build one validated index, from a mapping or field words."""
    if isinstance(index, AttachmentIndex) and not kwargs:
        return validate_index(index, source)
    if isinstance(index, dict) or index is None:
        merged: Dict[str, Any] = {}
        if isinstance(index, dict):
            merged.update(index)
        merged.update(kwargs)
        return validate_index(merged, source)
    return validate_index(index, source)


# ---------------------------------------------------------------------
# The schedule book: attachment records in held order, indexes judged.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class CrewScheduleBook:
    """One crew schedule book: formations on jobs, held whole.

    ``entries`` are the attachment records, in held
    order; ``indexes`` are attachment indexes of
    the book - derivations, judged against the
    book's records by :func:`validate_book`;
    ``schedules_note`` is the book's own note.
    """

    title: str = ""
    entries: Tuple[CrewAttachment, ...] = ()
    indexes: Tuple[AttachmentIndex, ...] = ()
    schedules_note: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_title(self.title, "a book's title"))
        if isinstance(self.entries, (str, bytes)) \
                or not isinstance(self.entries, (list, tuple)):
            raise ValueError(
                f"a book's entries must be a list of attachment "
                f"records, got {self.entries!r}")
        entries = tuple(_check_attachment_ref(e) for e in self.entries)
        if not entries:
            raise ValueError(
                "a crew schedule book holds at least one "
                "attachment record")
        seen_ids = set()
        seen_jobs = set()
        for entry in entries:
            if entry.attachment_id is not None:
                if entry.attachment_id in seen_ids:
                    raise ValueError(
                        f"an attachment record named "
                        f"{entry.attachment_id!r} already exists")
                seen_ids.add(entry.attachment_id)
            if entry.job_id in seen_jobs:
                raise ValueError(
                    f"a scheduled job named {entry.job_id!r} "
                    f"already stands attached in this book: "
                    f"one job, one formation")
            seen_jobs.add(entry.job_id)
        object.__setattr__(self, "entries", entries)
        if isinstance(self.indexes, (str, bytes)) \
                or not isinstance(self.indexes, (list, tuple)):
            raise ValueError(
                f"a book's indexes must be a list of indexes, "
                f"got {self.indexes!r}")
        indexes = tuple(
            idx if isinstance(idx, AttachmentIndex)
            else validate_index(idx)
            for idx in self.indexes)
        seen_indexes = set()
        for index in indexes:
            if index.index_id is not None:
                if index.index_id in seen_indexes:
                    raise ValueError(
                        f"an index named {index.index_id!r} "
                        f"already exists")
                seen_indexes.add(index.index_id)
        object.__setattr__(self, "indexes", indexes)
        if not isinstance(self.schedules_note, str):
            raise ValueError("a book's note must be text")
        object.__setattr__(
            self, "schedules_note", self.schedules_note.strip())

    def attachment_for(self, attachment_id: Any) -> CrewAttachment:
        """The attachment record one id names in this book."""
        wanted = normalize_member_id(attachment_id)
        for entry in self.entries:
            if entry.attachment_id == wanted:
                return entry
        raise KeyError(f"no attachment record in the book: {wanted!r}")

    def attachment_for_job(self, job_id: Any) -> CrewAttachment:
        """The attachment record one job id names in this book."""
        wanted = normalize_job_id(job_id)
        for entry in self.entries:
            if entry.job_id == wanted:
                return entry
        raise KeyError(f"no attachment record for job: {wanted!r}")

    def attachments_for_template(
            self, template: Any) -> Tuple[CrewAttachment, ...]:
        """Every attachment naming one formation, in held order."""
        wanted = normalize_member_id(template)
        return tuple(
            e for e in self.entries if e.template == wanted)

    def attachments_with_standing(
            self, standing: Any) -> Tuple[CrewAttachment, ...]:
        """Every attachment of one standing, in held order."""
        wanted = normalize_standing(standing)
        return tuple(e for e in self.entries if e.standing == wanted)

    def index_for(self, index_id: Any) -> AttachmentIndex:
        """The index one id names in this book."""
        wanted = normalize_member_id(index_id)
        for index in self.indexes:
            if index.index_id == wanted:
                return index
        raise KeyError(f"no index in the book: {wanted!r}")

    def attachment_ids(self) -> Tuple[str, ...]:
        """Every held attachment id, in held order."""
        return tuple(e.attachment_id for e in self.entries if e.attachment_id)

    def template_words(self) -> Tuple[str, ...]:
        """Every held attachment's formation, in held order."""
        return tuple(e.template for e in self.entries)

    def job_ids(self) -> Tuple[str, ...]:
        """Every held attachment's job id, in held order."""
        return tuple(e.job_id for e in self.entries)

    def standings(self) -> Tuple[str, ...]:
        """Every held attachment's standing, in held order."""
        return tuple(e.standing for e in self.entries)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "crew_schedule_book",
            "slice": CREW_SCHEDULES_SLICE,
            "title": self.title,
            "attachment_ids": list(self.attachment_ids()),
            "attachment_count": len(self.entries),
            "index_count": len(self.indexes),
        }


def validate_book(data: Any, *, require_example: bool = False) -> CrewScheduleBook:
    """Validate one crew schedules mapping into a CrewScheduleBook.

    The mapping names a ``schema`` (the crew
    schedules schema word), a ``guide`` mapping
    (its ``title``), an ``entries`` list and an
    optional ``indexes`` list. Every record stands
    on its own validation, then the whole is
    judged: attachment ids unique, job ids unique
    (one job, one formation), and every index
    judged against the book's own attachment
    records. With ``require_example`` the shipped
    example is held to its pinned shape: the
    pinned title, records and index, the index's
    pinned rows, totals and account word-for-word,
    and the first report's pinned checks and
    account. Problems raise
    :class:`ValidationError` or ``ValueError``.
    """
    if isinstance(data, CrewScheduleBook):
        return data
    if not isinstance(data, dict):
        raise ValidationError(
            f"a crew schedule book must be a mapping, got {data!r}")
    unknown = set(data) - _CREW_SCHEDULES_KEYS
    if unknown:
        raise ValidationError(
            "unknown crew schedules keys: %s" % ", ".join(sorted(unknown)))
    if data.get("schema") != CREW_SCHEDULES_SCHEMA:
        raise ValidationError(
            f"a crew schedule book must carry schema "
            f"{CREW_SCHEDULES_SCHEMA!r}, got {data.get('schema')!r}")
    if "entries" not in data:
        raise ValidationError("a crew schedule book is missing its entries")
    if not isinstance(data["entries"], (list, tuple)):
        raise ValidationError("a crew schedule book's entries must be a list")
    if data.get("indexes") is not None \
            and not isinstance(data["indexes"], (list, tuple)):
        raise ValidationError("a crew schedule book's indexes must be a list")
    head = data.get("guide") or {}
    if not isinstance(head, dict):
        raise ValidationError("a crew schedule book's guide must be a mapping")
    unknown_head = set(head) - _BOOK_KEYS
    if unknown_head:
        raise ValidationError(
            "unknown guide keys: %s" % ", ".join(sorted(unknown_head)))
    try:
        title = _pick_any(head, ("title", "name"), "titles")
        if title is None:
            raise ValidationError("a crew schedule book is missing its title")
        note = data.get("schedules_note") or ""
        if not isinstance(note, str):
            raise ValidationError("a crew schedule book's note must be text")
        book = CrewScheduleBook(
            title=title, entries=tuple(data["entries"]),
            indexes=tuple(data.get("indexes") or ()),
            schedules_note=note)
        for index in book.indexes:
            validate_index(index, book.entries)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    if require_example:
        if book.title != _EXAMPLE_TITLE:
            raise ValidationError(
                "the shipped example crew schedule book's title is "
                "not the pinned title")
        if book.attachment_ids() != _EXAMPLE_ATTACHMENT_IDS:
            raise ValidationError(
                "the shipped example's attachment records are not "
                "the pinned records")
        if book.template_words() != _EXAMPLE_TEMPLATES:
            raise ValidationError(
                "the shipped example's formations are not "
                "the pinned formations")
        if book.job_ids() != _EXAMPLE_JOB_IDS:
            raise ValidationError(
                "the shipped example's jobs are not "
                "the pinned jobs")
        if book.standings() != _EXAMPLE_STANDINGS:
            raise ValidationError(
                "the shipped example's attachments do not derive "
                "their pinned standings")
        index = book.index_for(_EXAMPLE_INDEX_ID)
        if tuple(r.template for r in index.rows) != _EXAMPLE_INDEX_ROWS:
            raise ValidationError(
                "the shipped example index does not name "
                "its pinned rows")
        totals = (
            index.total_attachments, index.total_armed,
            index.total_waiting, index.total_disabled,
            index.total_templates)
        if totals != _EXAMPLE_INDEX_TOTALS:
            raise ValidationError(
                "the shipped example index does not carry "
                "its pinned totals")
        if index.account != _EXAMPLE_INDEX_ACCOUNT:
            raise ValidationError(
                "the shipped example index does not carry "
                "its pinned account word-for-word")
        first = derive_report(book.entries[0])
        if first.checks != _EXAMPLE_FIRST_REPORT_CHECKS:
            raise ValidationError(
                "the shipped example's first report does not "
                "carry its pinned checks")
        if first.account != _EXAMPLE_FIRST_REPORT_ACCOUNT:
            raise ValidationError(
                "the shipped example's first report does not "
                "carry its pinned account word-for-word")
    return book


def build_book(book: Any = None, **kwargs: Any) -> CrewScheduleBook:
    """Build one validated book, from a mapping or field words."""
    if isinstance(book, CrewScheduleBook) and not kwargs:
        return book
    if isinstance(book, dict):
        if "entries" in book or "schema" in book:
            return validate_book(book)
        merged: Dict[str, Any] = dict(book)
        merged.update(kwargs)
        return CrewScheduleBook(**merged)
    if book is None:
        return CrewScheduleBook(**kwargs)
    raise ValueError(f"a crew schedule book is needed, got {book!r}")


def _book_from(data: Any, *, require_example: bool) -> CrewScheduleBook:
    try:
        return validate_book(data, require_example=require_example)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def load_crew_schedules(
        data: Optional[Dict[str, Any]] = None) -> CrewScheduleBook:
    """Load and validate the shipped example book (or *data*).

    The shipped file is held to the example check:
    the pinned title, attachment records and index -
    the M-144 boundary book, the roadmap's dawn
    Auditor sweep first - so the shipped book
    covers the attachment this slice exists to hold.
    """
    raw = data if data is not None else load_resource(CREW_SCHEDULES_RESOURCE)
    return _book_from(raw, require_example=True)


def load_crew_schedules_file(path: Any) -> CrewScheduleBook:
    """Load and validate a crew schedule book from a file at *path*.

    Any file in the crew schedules shape, anywhere
    on disk, validated whole - a malformed file
    raises :class:`ValidationError` naming the
    problem, and a missing file raises
    ``FileNotFoundError``. The example check is
    not held: a real schedule book stands on its
    own records.
    """
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _book_from(raw, require_example=False)


# ---------------------------------------------------------------------
# The registry model: one book held record by record, in held order.
# ---------------------------------------------------------------------


class CrewScheduleRegistry:
    """One session's crew schedule book, held record by record.

    The registry holds attachment records, never
    reports or indexes: both are derivations, read
    off held records at call time, so nothing here
    can hold a standing stale.
    """

    def __init__(self, book: Any = None) -> None:
        self._title: Optional[str] = None
        self._entries: Dict[str, CrewAttachment] = {}
        self._order: list = []
        self._next_entry = 1
        if book is not None:
            self.register_book(book)

    def _fresh_attachment_id(self, held_ids: Any) -> str:
        while f"attachment-{self._next_entry}" in held_ids:
            self._next_entry += 1
        fresh = f"attachment-{self._next_entry}"
        self._next_entry += 1
        return fresh

    def register_attachment(self, attachment: Any) -> CrewAttachment:
        """Register one attachment record into the held book.

        A record with no id is given a deterministic
        ``attachment-N`` id. A record id already
        standing here refuses, and a job already
        standing attached here refuses too - one
        job, one formation.
        """
        validated = build_attachment(attachment)
        held_ids = set(self._entries)
        if validated.attachment_id is not None \
                and validated.attachment_id in held_ids:
            raise ValueError(
                f"an attachment record named "
                f"{validated.attachment_id!r} already exists")
        for held in self._entries.values():
            if held.job_id == validated.job_id:
                raise ValueError(
                    f"a scheduled job named {validated.job_id!r} "
                    f"already stands attached here: "
                    f"one job, one formation")
        if validated.attachment_id is None:
            validated = replace(
                validated,
                attachment_id=self._fresh_attachment_id(held_ids))
        self._entries[validated.attachment_id] = validated
        self._order.append(validated.attachment_id)
        return validated

    def register_book(self, book: Any) -> CrewScheduleBook:
        """Register every attachment record of one book, in order.

        The first book held sets the title; a later
        book under a different title refuses, as does
        a book naming a held record id or a held job
        id. The book's indexes are derivations, not
        holdings, and are not held.
        """
        validated = build_book(book)
        if self._title is not None and validated.title != self._title:
            raise ValueError(
                "this registry already holds a crew schedule book "
                "under a different title")
        for entry in validated.entries:
            if entry.attachment_id in self._entries:
                raise ValueError(
                    f"an attachment record named "
                    f"{entry.attachment_id!r} already exists")
        self._title = validated.title
        for entry in validated.entries:
            self.register_attachment(entry)
        return self.book()

    def get_attachment(self, attachment_id: Any) -> CrewAttachment:
        """The attachment record one id names among the held records."""
        wanted = normalize_member_id(attachment_id)
        if wanted not in self._entries:
            raise KeyError(f"unknown attachment record: {wanted!r}")
        return self._entries[wanted]

    def get_for_job(self, job_id: Any) -> CrewAttachment:
        """The attachment record one job id names among the held records."""
        wanted = normalize_job_id(job_id)
        for entry in self._entries.values():
            if entry.job_id == wanted:
                return entry
        raise KeyError(f"unknown attachment for job: {wanted!r}")

    def list_attachments(self) -> Tuple[CrewAttachment, ...]:
        """Every held attachment record, in the order they were held."""
        return tuple(self._entries[e] for e in self._order)

    def book(self) -> CrewScheduleBook:
        """The held attachment records as one validated book."""
        if self._title is None:
            raise ValueError("no crew schedule book is held yet")
        return CrewScheduleBook(
            title=self._title, entries=self.list_attachments())

    def report_for(self, attachment_id: Any) -> AttachmentReport:
        """Derive one attachment's report, at call time.

        The report is derived from the held record
        the id names, read at call time - the
        registry holds records, and this report is
        derived from them.
        """
        return derive_report(self.get_attachment(attachment_id))

    def index(self) -> AttachmentIndex:
        """Derive the attachment index of the held book.

        The rows, totals and account are the held
        records' own derived counts, read at call
        time.
        """
        return derive_index(self.list_attachments())


# ---------------------------------------------------------------------
# Crew schedule news, shaped as session records.
# ---------------------------------------------------------------------


def attachment_record(attachment: Any) -> Dict[str, Any]:
    """The session-news record of one attachment record."""
    current = attachment if isinstance(attachment, CrewAttachment) \
        else build_attachment(attachment)
    record = current.to_record()
    record["news"] = True
    if current.standing == "armed":
        record["headline"] = (
            f"Formation {current.template} is attached to "
            f"scheduled job {current.job_id} "
            f"({current.schedule_text}) and runs when "
            f"its moment comes.")
    elif current.standing == "waiting_for_approval":
        record["headline"] = (
            f"Formation {current.template} is attached to "
            f"scheduled job {current.job_id} "
            f"({current.schedule_text}) and waits for "
            f"approval when its moment comes.")
    else:
        record["headline"] = (
            f"Formation {current.template} is attached to "
            f"scheduled job {current.job_id} "
            f"({current.schedule_text}) on a disabled "
            f"job, so nothing is owed.")
    return record


def report_record(report: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of one attachment report.

    With *source* given, the report is first judged
    against the attachment it belongs to.
    """
    current = validate_report(report, source)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Formation {current.template} attached to job "
        f"{current.job_id} - {_standing_phrase(current.standing)}: "
        f"{'; '.join(current.checks)}.")
    return record


def index_record(index: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of the attachment index.

    With *source* given, the index is first judged
    against the records it belongs to.
    """
    current = validate_index(index, source)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Crew on schedule: {current.total_attachments} "
        f"attachment(s), {current.total_armed} armed "
        f"to run when due.")
    return record


def book_record(book: Any) -> Dict[str, Any]:
    """The session-news record of one crew schedule book."""
    current = book if isinstance(book, CrewScheduleBook) else build_book(book)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Crew schedule book {current.title}: "
        f"{record['attachment_count']} attachment "
        f"record(s), {record['index_count']} index(es).")
    return record


def plain_words(attachment: Any) -> str:
    """One attachment record, in one plain sentence."""
    current = attachment if isinstance(attachment, CrewAttachment) \
        else build_attachment(attachment)
    enabled_word = "enabled" if current.job.enabled else "disabled"
    return (
        f"{current.title} - formation {current.template} "
        f"on scheduled job {current.job_id}: "
        f"{current.detail} The job runs "
        f"{current.job.command_text} ({current.schedule_text}); "
        f"it is {enabled_word} under "
        f"{current.job.approval} approval: this attachment "
        f"is {_standing_phrase(current.standing)}.")


def report_plain_words(source: Any) -> str:
    """Attachment reports in plain words: every report, in full.

    Accepts an AttachmentReport or a
    CrewScheduleBook. Each report is told whole -
    its attachment and its account.
    """
    if isinstance(source, AttachmentReport):
        reports = (validate_report(source),)
        title = None
    elif isinstance(source, CrewScheduleBook):
        reports = tuple(
            derive_report(entry) for entry in source.entries)
        title = source.title
    else:
        raise ValueError(f"a crew schedule source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    for report in reports:
        lines.append(
            f"Formation {report.template} on job {report.job_id} - "
            f"{_standing_phrase(report.standing)}")
        lines.extend(report.account)
    return "\n".join(lines)


def index_plain_words(source: Any) -> str:
    """The attachment index in plain words, in full.

    Accepts an AttachmentIndex or a CrewScheduleBook.
    The index is told whole - its rows and its
    account.
    """
    if isinstance(source, AttachmentIndex):
        index = validate_index(source)
        title = None
    elif isinstance(source, CrewScheduleBook):
        index = derive_index(source.entries)
        title = source.title
    else:
        raise ValueError(f"a crew schedule source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    lines.append("Attachment index:")
    for row in index.rows:
        lines.append(
            f"Formation {row.template} on job {row.job_id} - "
            f"{_standing_phrase(row.standing)}")
    lines.extend(index.account)
    return "\n".join(lines)


# ---------------------------------------------------------------------
# Screens: the formatters and the shared /crewschedules grammar.
# ---------------------------------------------------------------------


def _source_book(source: Any) -> CrewScheduleBook:
    if source is None:
        return load_crew_schedules()
    if isinstance(source, CrewScheduleRegistry):
        return source.book()
    if isinstance(source, CrewScheduleBook):
        return source
    raise ValueError(f"a crew schedule book is needed, got {source!r}")


def format_attachment(attachment: Any) -> str:
    """One attachment record as a screen line."""
    current = attachment if isinstance(attachment, CrewAttachment) \
        else build_attachment(attachment)
    return (
        f"{current.attachment_id or '-'}: {current.template} - "
        f"{current.title} (on job {current.job_id}: "
        f"{_standing_phrase(current.standing)})")


def format_attachments(source: Any = None, template: Any = None,
                       standing: Any = None) -> str:
    """Attachment records of one book, in held order.

    With *template* given, only the attachments
    naming that formation are shown; with
    *standing* given, only the attachments of
    that standing.
    """
    book = _source_book(source)
    entries = book.entries
    if template is not None:
        wanted = normalize_member_id(template)
        entries = tuple(e for e in entries if e.template == wanted)
    if standing is not None:
        wanted_standing = normalize_standing(standing)
        entries = tuple(e for e in entries if e.standing == wanted_standing)
    lines = [format_attachment(entry) for entry in entries]
    if not lines:
        lines.append("No attachment records are held.")
    return "\n".join(lines)


def format_report(source: Any = None) -> str:
    """Attachment reports as screen blocks: attachment over account.

    Accepts an AttachmentReport or a
    CrewScheduleBook; a book shows every report
    it derives, in book order.
    """
    if isinstance(source, AttachmentReport):
        reports = (validate_report(source),)
        lines: list = []
    else:
        book = _source_book(source)
        reports = tuple(
            derive_report(entry) for entry in book.entries)
        lines = [f"Attachment reports in {book.title}:"]
    for report in reports:
        lines.append(
            f"Formation {report.template} on job {report.job_id} - "
            f"{_standing_phrase(report.standing)}")
        lines.extend(report.account)
    if isinstance(source, AttachmentReport):
        return "\n".join(lines)
    if len(lines) == 1:
        lines.append("Nothing here.")
    return "\n".join(lines)


def format_index(source: Any = None) -> str:
    """The attachment index as a screen block.

    Accepts an AttachmentIndex or a CrewScheduleBook;
    a book shows the index it derives, its rows
    over its derived account.
    """
    if isinstance(source, AttachmentIndex):
        index = validate_index(source)
        lines: list = []
    else:
        book = _source_book(source)
        index = derive_index(book.entries)
        lines = [f"Index in {book.title}:"]
    lines.append("Attachment index:")
    for row in index.rows:
        lines.append(
            f"Formation {row.template} on job {row.job_id} - "
            f"{_standing_phrase(row.standing)}")
    lines.extend(index.account)
    return "\n".join(lines)


def format_crew_schedules_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /crewschedules.

    With nothing named, the shipped example crew
    schedule book is shown - the example this
    slice ships - so the screen is never empty.
    """
    book = _source_book(source)
    lines = ["Crew on schedule (M-145) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_attachments(book))
    lines.append("")
    lines.append(format_report(book))
    lines.append("")
    lines.append(format_index(book))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_crew_schedules_args(args: Any) -> Tuple[str, Any]:
    """Parse the /crewschedules grammar both surfaces share.

    No words (or ``show`` / ``list``) shows the
    crew schedule book; ``attachment
    <attachment-id>`` shows one attachment record;
    ``template <template>`` shows the attachments
    naming one formation; ``job <job-id>`` shows
    the attachment naming one job; ``report
    <attachment-id>`` shows one attachment's
    report; ``index`` shows the attachment index.
    Anything else is a usage error naming the
    grammar. Returns ``(action, value-or-None)``.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() in ("show", "list"):
        return ("show", None)
    words = text.split()
    head = words[0].lower()
    if head == "index" and len(words) == 1:
        return ("index", None)
    if head in ("attachment", "template", "report") and len(words) == 2:
        try:
            return (head, normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "job" and len(words) == 2:
        try:
            return (head, normalize_job_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
