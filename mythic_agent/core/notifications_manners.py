"""Notifications with manners (All-Features roadmap slice M-181).

Part VIII - The Beautiful Face - builds here. The
roadmap's words: *long jobs announce completion
(terminal bell/OS notification, once), failures
announce once with the one action that matters;
silence is the default posture.*

What already ships, and what this slice adds:

* The shipped tree already carries a raw
  notification road: ``mythic_agent/core/
  notifications.py`` (Slice 37) sends desktop
  notifications and webhooks when configured.
  What nothing held is the *manners* of
  announcing, as checkable data: which finished
  jobs may announce at all, through which
  channel, exactly once, and what a failure must
  carry when it speaks. This slice is that
  manners book, in its own module; the shipped
  road is reused behind a seam, never reinvented,
  and its behaviour is untouched.
* This slice is the manners room, as a pure
  layer: a finished (or still running) job held
  whole (its outcome, how long it ran, the bell
  and OS backends it names, and the one failure
  action a failure carries); a notification
  channel held whole (its name - terminal bell
  or OS notification - and the backend road it
  names); and a manners rule held whole (the
  standing law itself, as data: silence by
  default, announce once, a failure names one
  action). Whether a job announces is DERIVED
  from its outcome and duration at call time: a
  running job and a short completed job announce
  nothing - silence is the default posture - a
  long completed job announces, and a failure
  announces whatever its length. Which channel
  carries an announcement, and whether that
  channel stands available, unavailable by a
  named reason, or honestly unknown, is DERIVED
  from the backends a record names, never stored
  and never faked. An announcement is derived
  from a job under an announced-key ledger: its
  key is the job's own identity (job id and
  outcome), so a job polled twice announces at
  most once - the once-only ledger is derived
  from event identity, never a stored counter
  that could double-announce. The panel is
  DERIVED for one held view and a verdict is
  DERIVED for the whole book under one view. The
  shipped data file (``mythic_agent/data/
  notifications_manners.yaml``) holds one
  example book in exactly the shape a real
  manners file takes, a loader reads a manners
  file anywhere on disk, items and views are
  shaped as session news, and a small in-memory
  registry holds items and views one by one.
  The agent layer owns holding manners for a
  session and polling its jobs for the
  announcements that stand due. Live roads stand
  behind seams: a caller may hand
  ``deliver_announcement`` a bell callable and a
  notifier callable; the defaults reach for a
  terminal bell and the shipped ``notifications.
  py`` road lazily, by import inside the call, so
  this module imports cleanly where no desktop,
  no notify-send and no terminal stand.

Honesty rules, enforced here and pinned by tests:

* **Silence is the default posture.** A job
  announces only when the derivation says so: a
  running job announces nothing, a completed job
  shorter than the long-job threshold announces
  nothing, and a job already announced announces
  nothing again. Quiet is not an absence of a
  rule - it is the headline rule, held as data
  and derived as logic.
* **Once, and only once.** An announcement's
  key is derived from the job's identity alone,
  so the same job under the same outcome can
  never announce twice, however often it is
  polled. No record stores an announced flag: a
  mapping naming one refuses.
* **A failure carries the one action that
  matters.** A failed job names exactly one
  failure action - the single next step its
  announcement speaks - held as data. A failure
  naming none, or naming several, refuses by
  name; a job that did not fail names none.
* **Availability is derived, never faked.** A
  channel naming a working backend stands
  available; one naming no backend stands
  unavailable, with the missing piece named as
  the reason; one naming the unknown backend
  stands honestly unknown. A delivery through an
  unavailable or unknown channel renders
  nothing and names its outcome - no bell is
  rung and no notification is posted by
  invention.
"""

from __future__ import annotations

__all__ = [
    "AVAILABILITY_WORDS",
    "BACKEND_UNKNOWN",
    "CHANNEL_NAMES",
    "DECISION_WORDS",
    "ITEM_KINDS",
    "LONG_JOB_THRESHOLD_SECONDS",
    "NOTIFICATIONS_MANNERS_RESOURCE",
    "NOTIFICATIONS_MANNERS_SCHEMA",
    "NOTIFICATIONS_MANNERS_SLICE",
    "OUTCOMES",
    "PLAIN_EXPLANATION",
    "RULE_NAMES",
    "SILENCE_IS_THE_DEFAULT_POSTURE",
    "THE_NOTIFICATIONS_MANNERS_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "VIEW_KINDS",
    "Announcement",
    "Any",
    "ChannelNotice",
    "Dict",
    "JobNotice",
    "List",
    "MannersRule",
    "NoticeBook",
    "NoticeDelivery",
    "NoticeKindCount",
    "NoticePanel",
    "NoticePanelRow",
    "NoticeRegistry",
    "NoticeVerdict",
    "NoticeView",
    "Optional",
    "Tuple",
    "announcement_decision",
    "announcement_for",
    "announcement_key",
    "announcement_plain_words",
    "availability_of",
    "book_record",
    "build_book",
    "build_channel",
    "build_job",
    "build_panel",
    "build_row",
    "build_rule",
    "build_verdict",
    "build_view",
    "channel_availability",
    "channel_of",
    "channel_plain_words",
    "channel_record",
    "complete_job",
    "decision_of",
    "default_bell",
    "default_notifier",
    "deliver_announcement",
    "derive_panel",
    "derive_verdict",
    "due_announcements",
    "fail_job",
    "format_book",
    "format_channel",
    "format_job",
    "format_notifications_manners_screen",
    "format_panel",
    "format_rule",
    "format_verdict",
    "format_view",
    "inspect_item_source",
    "is_long_job",
    "item_passes",
    "item_record",
    "items_for_kind",
    "job_availability",
    "job_passes",
    "job_plain_words",
    "job_record",
    "load_notifications_manners",
    "load_notifications_manners_file",
    "normalize_channel_name",
    "normalize_kind",
    "normalize_kind_filter",
    "normalize_outcome",
    "normalize_rule_name",
    "panel_plain_words",
    "panel_record",
    "parse_notifications_manners_args",
    "passing_items",
    "plain_words",
    "rule_plain_words",
    "rule_record",
    "segment_of",
    "shown_items",
    "total_items",
    "validate_book",
    "validate_channel",
    "validate_job",
    "validate_panel",
    "validate_row",
    "validate_rule",
    "validate_verdict",
    "validate_view",
    "verdict_plain_words",
    "verdict_record",
    "view_plain_words",
    "view_record",
]

from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource
from .crew_members import normalize_member_id

NOTIFICATIONS_MANNERS_SLICE = "M-181"

#: The longer name other layers cite for this slice.
THE_NOTIFICATIONS_MANNERS_SLICE = NOTIFICATIONS_MANNERS_SLICE

NOTIFICATIONS_MANNERS_RESOURCE = "notifications_manners.yaml"

NOTIFICATIONS_MANNERS_SCHEMA = "mythic.notifications_manners/1"

#: The kinds of item one manners book holds, in
#: held order: the jobs judged for announcing, the
#: channels an announcement may travel, and the
#: rules of the standing law itself.
ITEM_KINDS = ("job", "channel", "rule")

_KIND_ALIASES = {
    "job": "job", "jobs": "job", "task": "job",
    "channel": "channel", "channels": "channel",
    "road": "channel",
    "rule": "rule", "rules": "rule", "law": "rule"}

#: The views a panel may stand under: every kind
#: at once, or one kind alone.
VIEW_KINDS = ("all",) + ITEM_KINDS

#: A job's outcomes, in the order a job walks
#: them: still running, completed, or failed.
OUTCOMES = ("running", "completed", "failed")

_OUTCOME_ALIASES = {
    "running": "running", "live": "running",
    "in-progress": "running", "in_progress": "running",
    "completed": "completed", "complete": "completed",
    "done": "completed", "finished": "completed",
    "succeeded": "completed",
    "failed": "failed", "failure": "failed",
    "error": "failed", "errored": "failed"}

#: The channels an announcement may travel, in
#: preference order reversed: the OS notification
#: is preferred where it stands available, and
#: the terminal bell is the road that always
#: stands closest to hand.
CHANNEL_NAMES = ("terminal_bell", "os_notification")

_CHANNEL_ALIASES = {
    "terminal_bell": "terminal_bell", "bell": "terminal_bell",
    "terminal-bell": "terminal_bell",
    "os_notification": "os_notification",
    "os": "os_notification", "desktop": "os_notification",
    "notify": "os_notification",
    "os-notification": "os_notification"}

#: The names of the standing manners rules, the
#: closed set the law is held in.
RULE_NAMES = (
    "silence_by_default", "announce_once",
    "failure_names_one_action")

_RULE_ALIASES = {
    "silence_by_default": "silence_by_default",
    "silence": "silence_by_default",
    "quiet_by_default": "silence_by_default",
    "announce_once": "announce_once", "once": "announce_once",
    "announce-once": "announce_once",
    "failure_names_one_action": "failure_names_one_action",
    "one_action": "failure_names_one_action",
    "failure-names-one-action": "failure_names_one_action"}

#: The words an announcement decision may stand
#: at, always derived from a job's own fields.
DECISION_WORDS = ("announce", "silence")

#: The words availability may stand at, always
#: derived from what a record names.
AVAILABILITY_WORDS = ("available", "unavailable", "unknown")

#: The backend name that stands honestly unknown:
#: a record naming it claims no working road.
BACKEND_UNKNOWN = "unknown"

#: How long a job must run, in seconds, before
#: its completion may announce at all. A job
#: shorter than this stands under the default
#: posture: silence.
LONG_JOB_THRESHOLD_SECONDS = 60

#: The standing law, as data: silence is the
#: default posture of this layer.
SILENCE_IS_THE_DEFAULT_POSTURE = True

VERDICT_WORDS = ("open", "strained", "shut")

_JOB_KEYS = frozenset({
    "job_id", "id", "seq", "sequence", "order",
    "outcome", "state", "status",
    "duration_seconds", "duration", "seconds",
    "bell_backend", "bell", "os_backend", "os",
    "failure_action", "action",
    "failure_actions", "actions",
    "detail", "reason",
    "recorded_on", "day", "date",
    "actor", "by", "who", "source",
    "origin_session", "session"})

_JOB_DERIVED = frozenset({
    "availability", "availability_reason", "decision",
    "decision_reason", "channel", "announced",
    "announcement_key", "passes", "segment"})

_CHANNEL_KEYS = frozenset({
    "channel_id", "id", "seq", "sequence", "order",
    "name", "channel", "backend", "road",
    "detail", "reason",
    "recorded_on", "day", "date",
    "actor", "by", "who", "source",
    "origin_session", "session"})

_CHANNEL_DERIVED = frozenset({
    "availability", "availability_reason", "passes", "segment"})

_RULE_KEYS = frozenset({
    "rule_id", "id", "seq", "sequence", "order",
    "name", "rule", "statement", "text", "words",
    "detail", "reason",
    "recorded_on", "day", "date",
    "actor", "by", "who", "source",
    "origin_session", "session"})

_RULE_DERIVED = frozenset({"passes", "segment"})

_VIEW_KEYS = frozenset({
    "view_id", "id", "seq", "sequence", "order",
    "kind_filter", "filter", "kind",
    "detail", "reason",
    "recorded_on", "day", "date",
    "actor", "by", "who", "source",
    "origin_session", "session"})

_ROW_KEYS = frozenset({
    "item_id", "id", "kind", "label", "name",
    "segment", "recorded_on", "day", "date"})

_PANEL_KEYS = frozenset({
    "panel_id", "id", "view_id", "view",
    "kind_filter", "filter", "kind", "rows", "shown",
    "total_items", "items", "total_shown", "matched",
    "kind_counts", "kinds", "as_of", "day",
    "account", "statements"})

_VERDICT_KEYS = frozenset({
    "total_items", "items", "total_shown", "matched",
    "passing_shown", "passing", "distinct_kinds", "kinds",
    "earliest_on", "earliest", "latest_on", "latest",
    "verdict"})

_BOOK_KEYS = frozenset({"title", "name"})

_NOTIFICATIONS_MANNERS_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "canon_note", "guide", "jobs", "channels",
    "rules", "views", "panels"})

_EXAMPLE_TITLE = "Notifications at the M-180 slice boundary"

_EXAMPLE_JOB_IDS = (
    "job-morning-build", "job-quick-check",
    "job-night-export")

_EXAMPLE_CHANNEL_IDS = (
    "channel-terminal-bell", "channel-os-notification")

_EXAMPLE_RULE_IDS = (
    "rule-silence-by-default",
    "rule-failure-names-one-action")

_EXAMPLE_FIRST_JOB_ID = "job-morning-build"

_EXAMPLE_PANEL_ID = "panel-m180-boundary"

_EXAMPLE_AS_OF = "2026-11-09"

_EXAMPLE_VIEW_IDS = ("view-all", "view-job")

PLAIN_EXPLANATION = (
    "Notifications with Manners: long jobs announce "
    "completion (terminal bell/OS notification, "
    "once), failures announce once with the one "
    "action that matters; silence is the default "
    "posture. A job is held whole - its outcome "
    "(running, completed or failed), how long it "
    "ran, the bell and OS backends it names, and "
    "the one failure action a failure carries. "
    "Whether a job announces is derived from its "
    "outcome and duration: a running job and a "
    "short completed job announce nothing, a long "
    "completed job announces, and a failure "
    "announces whatever its length - each at most "
    "once, under a key derived from the job's own "
    "identity. A failure names exactly one action: "
    "a failure naming none, or several, refuses by "
    "name. Availability - available, unavailable by "
    "a named reason, or honestly unknown - is "
    "derived from the backends a record names, "
    "never stored and never faked. This layer holds "
    "manners as data and reaches live roads only "
    "through seams: it rings no bell and posts no "
    "notification in tests."
)

USAGE = (
    "Usage: /manners, /manners show, "
    "/manners job <job-id>, "
    "/manners channel <channel-id>, "
    "/manners rule <rule-id>, "
    "/manners view <view-id>, "
    "/manners kind <kind>, "
    "/manners panel, /manners verdict"
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


def _check_seq(value: Any, what: str = "a sequence") -> int:
    seq = _check_count(value, what)
    if seq < 1:
        raise ValueError(f"{what} stands from 1, got {value!r}")
    return seq


def _check_seconds(value: Any, what: str = "a duration") -> int:
    return _check_count(value, what)


def _check_word(value: Any, what: str) -> str:
    try:
        return normalize_member_id(value)
    except ValueError:
        raise ValueError(
            f"{what} must be one plain word, "
            f"got {value!r}") from None


def _check_day(value: Any, what: str = "a day") -> str:
    text = _clean_text(value, what)
    try:
        parsed = date.fromisoformat(text)
    except ValueError:
        raise ValueError(
            f"{what} must be an ISO date "
            f"(YYYY-MM-DD), got {text!r}") from None
    if parsed.isoformat() != text:
        raise ValueError(
            f"{what} must be an ISO date "
            f"(YYYY-MM-DD), got {text!r}")
    return text


def _check_backend(value: Any, what: str) -> Optional[str]:
    if value is None:
        return None
    text = _clean_text(value, what)
    if len(text) > 80 or "\x00" in text:
        raise ValueError(
            f"{what} must be a plain backend name of at "
            f"most 80 characters, got {value!r}")
    return text


def normalize_kind(value: Any) -> str:
    """One item kind, read onto the closed kind set."""
    text = _clean_text(value, "a kind").lower()
    kind = _KIND_ALIASES.get(text)
    if kind is None:
        raise ValueError(
            f"a kind is one of {ITEM_KINDS}, got {value!r}")
    return kind


def normalize_kind_filter(value: Any) -> str:
    """One view's kind filter: every kind, or one."""
    text = _clean_text(value, "a kind filter").lower()
    if text == "all":
        return "all"
    return normalize_kind(text)


def normalize_outcome(value: Any) -> str:
    """One job outcome, read onto the closed set."""
    text = _clean_text(value, "a job outcome").lower()
    outcome = _OUTCOME_ALIASES.get(text)
    if outcome is None:
        raise ValueError(
            f"a job outcome is one of {OUTCOMES}, "
            f"got {value!r}")
    return outcome


def normalize_channel_name(value: Any) -> str:
    """One channel name, read onto the closed set."""
    text = _clean_text(value, "a channel name").lower()
    name = _CHANNEL_ALIASES.get(text)
    if name is None:
        raise ValueError(
            f"a channel name is one of {CHANNEL_NAMES}, "
            f"got {value!r}")
    return name


def normalize_rule_name(value: Any) -> str:
    """One manners rule name, read onto the closed set."""
    text = _clean_text(value, "a rule name").lower()
    name = _RULE_ALIASES.get(text)
    if name is None:
        raise ValueError(
            f"a rule name is one of {RULE_NAMES}, "
            f"got {value!r}")
    return name


def _needed(mapping: Dict[str, Any],
            spellings: Tuple[str, ...], what: str) -> Any:
    value = _pick_any(mapping, spellings, what)
    if value is None:
        raise ValueError(f"a record names no {what}")
    return value


def _provenance(mapping: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "detail": _check_long_text(
            _needed(mapping, ("detail", "reason"), "detail"),
            "a detail"),
        "recorded_on": _check_day(
            _needed(mapping, ("recorded_on", "day", "date"),
                    "recorded day")),
        "actor": _check_long_text(
            _needed(mapping, ("actor", "by", "who"), "actor"),
            "an actor"),
        "source": _check_long_text(
            _needed(mapping, ("source",), "source"), "a source"),
        "origin_session": _check_word(
            _needed(mapping, ("origin_session", "session"),
                    "origin session"), "an origin session"),
    }


# ---------------------------------------------------------------------
# The job: a finished (or running) job, held whole.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class JobNotice:
    """One job, held whole under the manners law.

    The job stands in one outcome - running while
    it still runs, completed, or failed - and
    names how long it ran, the terminal-bell and
    OS backends an announcement for it would
    travel, and, when it failed, the one action
    that matters: the single next step its
    announcement speaks. Its decision (announce
    or silence), its channel and its availability
    are derived from those fields at call time,
    never stored, and it carries no announced
    flag: once-only is derived from its identity,
    never counted here.
    """

    job_id: str
    seq: int
    outcome: str
    duration_seconds: int
    bell_backend: Optional[str]
    os_backend: Optional[str]
    failure_action: Optional[str]
    detail: str
    recorded_on: str
    actor: str
    source: str
    origin_session: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "job_id", _check_word(self.job_id, "a job id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "outcome", normalize_outcome(self.outcome))
        object.__setattr__(
            self, "duration_seconds",
            _check_seconds(self.duration_seconds))
        object.__setattr__(
            self, "bell_backend",
            _check_backend(self.bell_backend, "a bell backend"))
        object.__setattr__(
            self, "os_backend",
            _check_backend(self.os_backend, "an OS backend"))
        action = self.failure_action
        if self.outcome == "failed":
            if not isinstance(action, str) or not action.strip():
                raise ValueError(
                    f"failed job {self.job_id!r} names no "
                    f"failure action - a failure announces "
                    f"once with the one action that "
                    f"matters, and a failure naming none "
                    f"refuses by name")
            object.__setattr__(
                self, "failure_action",
                _check_long_text(action, "a failure action"))
        elif action is not None:
            raise ValueError(
                f"job {self.job_id!r} stands "
                f"{self.outcome} and names a failure "
                f"action - the one action that matters "
                f"stands on a failure alone")
        object.__setattr__(
            self, "detail", _check_long_text(self.detail, "a detail"))
        object.__setattr__(
            self, "recorded_on", _check_day(self.recorded_on))
        object.__setattr__(
            self, "actor", _check_long_text(self.actor, "an actor"))
        object.__setattr__(
            self, "source", _check_long_text(self.source, "a source"))
        object.__setattr__(
            self, "origin_session",
            _check_word(self.origin_session, "an origin session"))

    @property
    def kind(self) -> str:
        return "job"

    @property
    def item_id(self) -> str:
        return self.job_id

    @property
    def label(self) -> str:
        return self.job_id

    @property
    def is_long(self) -> bool:
        return is_long_job(self)

    @property
    def decision(self) -> str:
        return announcement_decision(self)[0]

    @property
    def decision_reason(self) -> str:
        return announcement_decision(self)[1]

    @property
    def channel(self) -> Optional[str]:
        return channel_of(self)[0]

    @property
    def availability(self) -> str:
        return job_availability(self)[0]

    @property
    def availability_reason(self) -> str:
        return job_availability(self)[1]

    @property
    def announcement_key(self) -> str:
        return announcement_key(self)

    @property
    def passes(self) -> bool:
        return job_passes(self)

    @property
    def segment(self) -> str:
        return segment_of(self)

    def to_record(self) -> Dict[str, Any]:
        word, reason = announcement_decision(self)
        channel, aword, areason = channel_of(self)
        return {
            "type": "notifications_manners_job",
            "slice": NOTIFICATIONS_MANNERS_SLICE,
            "job_id": self.job_id,
            "seq": self.seq,
            "outcome": self.outcome,
            "duration_seconds": self.duration_seconds,
            "bell_backend": self.bell_backend,
            "os_backend": self.os_backend,
            "failure_action": self.failure_action,
            "decision": word,
            "decision_reason": reason,
            "channel": channel,
            "availability": aword,
            "availability_reason": areason,
            "announcement_key": self.announcement_key,
            "passes": self.passes,
            "segment": self.segment,
            "detail": self.detail,
            "recorded_on": self.recorded_on,
            "actor": self.actor,
            "source": self.source,
            "origin_session": self.origin_session,
        }


def _check_job_ref(value: Any) -> JobNotice:
    if isinstance(value, JobNotice):
        return value
    if isinstance(value, dict):
        return validate_job(value)
    raise ValueError(f"a job notice is needed, got {value!r}")


def is_long_job(job: Any,
                threshold: int = LONG_JOB_THRESHOLD_SECONDS) -> bool:
    """Whether a job ran long, against the threshold.

    The threshold is data at call time: a job is
    long while its duration stands at or past it.
    """
    current = _check_job_ref(job)
    limit = _check_seconds(threshold, "a long-job threshold")
    return current.duration_seconds >= limit


def announcement_decision(
        job: Any,
        threshold: int = LONG_JOB_THRESHOLD_SECONDS) -> Tuple[str, str]:
    """Whether a job announces, derived whole.

    Silence is the default posture: a running job
    announces nothing, and a completed job shorter
    than the long-job threshold announces nothing.
    A long completed job announces its completion,
    and a failure announces whatever its length -
    once, with the one action that matters.
    """
    current = _check_job_ref(job)
    if current.outcome == "running":
        return ("silence",
                "the job still runs - nothing stands "
                "finished to announce, and silence is "
                "the default posture")
    if current.outcome == "failed":
        return ("announce",
                "a failure announces once, with the one "
                "action that matters, whatever its length")
    if is_long_job(current, threshold):
        return ("announce",
                f"a long job announces its completion "
                f"once - it ran {current.duration_seconds} "
                f"seconds, at or past the "
                f"{LONG_JOB_THRESHOLD_SECONDS}-second "
                f"long-job threshold" if threshold == LONG_JOB_THRESHOLD_SECONDS else
                f"a long job announces its completion "
                f"once - it ran {current.duration_seconds} "
                f"seconds, at or past the named "
                f"{threshold}-second threshold")
    return ("silence",
            f"a short job announces nothing - it ran "
            f"{current.duration_seconds} seconds, under "
            f"the long-job threshold, and silence is "
            f"the default posture")


def decision_of(job: Any,
                threshold: int = LONG_JOB_THRESHOLD_SECONDS) -> Tuple[str, str]:
    """One job's announcement decision, derived whole."""
    return announcement_decision(job, threshold)


def channel_of(job: Any) -> Tuple[Optional[str], str, str]:
    """The channel a job's announcement travels, derived.

    Returns (channel name or None, availability
    word, reason). The OS notification is
    preferred while its backend stands named and
    known; the terminal bell stands next; a job
    naming only the unknown backend stands
    honestly unknown; a job naming no backend
    stands unavailable, with the missing road
    named as the reason.
    """
    current = _check_job_ref(job)
    if current.os_backend is not None and (
            current.os_backend != BACKEND_UNKNOWN):
        return ("os_notification", "available",
                f"OS backend {current.os_backend!r} stands "
                f"named - the announcement travels as an "
                f"OS notification")
    if current.bell_backend is not None and (
            current.bell_backend != BACKEND_UNKNOWN):
        return ("terminal_bell", "available",
                f"bell backend {current.bell_backend!r} "
                f"stands named - the announcement travels "
                f"as a terminal bell")
    if BACKEND_UNKNOWN in (current.os_backend, current.bell_backend):
        return (None, "unknown",
                "a named backend stands unknown - whether "
                "either road travels is not proven, and no "
                "channel is chosen by invention")
    return (None, "unavailable",
            "no bell backend and no OS backend is named "
            "- no road stands recorded for this "
            "announcement")


def job_availability(job: Any) -> Tuple[str, str]:
    """A job's announcement availability, derived whole."""
    _channel, word, reason = channel_of(job)
    return (word, reason)


def announcement_key(job: Any) -> str:
    """One job's once-only announcement key, derived.

    The key is the job's own identity - its job id
    and its outcome - and nothing else: the same
    job under the same outcome always derives the
    same key, so an announced-key ledger built
    from these keys can never let it announce
    twice, and no counter is ever stored.
    """
    current = _check_job_ref(job)
    return f"{current.job_id}:{current.outcome}"


def job_passes(job: Any) -> bool:
    """Whether a job's manners stand settled and whole.

    Whole while the job stands finished and its
    derived decision stands travel-ready: a job
    whose decision is silence stands whole under
    the default posture, and a job whose decision
    is announce stands whole only while a channel
    stands available for it. A running job's
    manners stand unsettled - nothing has
    finished, so nothing stands judged.
    """
    current = _check_job_ref(job)
    if current.outcome == "running":
        return False
    word, _reason = announcement_decision(current)
    if word == "silence":
        return True
    return current.availability == "available"


def validate_job(job: Any) -> JobNotice:
    """Judge one job mapping whole.

    The one-action law is enforced here, by name:
    a failure naming several actions in a list
    refuses, a failure naming none refuses at the
    dataclass gate, and a mapping carrying a
    stored decision, channel, availability or
    announced flag refuses - every judgement is
    derived from the job's own fields.
    """
    if isinstance(job, JobNotice):
        return job
    if not isinstance(job, dict):
        raise ValueError(f"a job notice must be a mapping, got {job!r}")
    derived = set(job) & _JOB_DERIVED
    if derived:
        raise ValueError(
            f"a job notice carries no stored "
            f"{sorted(derived)} - decision, channel, "
            f"availability and segment are derived "
            f"from its own fields, and no job here is "
            f"stored as already announced")
    unknown = set(job) - _JOB_KEYS - {"type", "slice"}
    if unknown:
        raise ValueError(
            f"a job notice carries unknown keys: {sorted(unknown)}")
    job_id = _pick_any(job, ("job_id", "id"), "job id")
    action = _pick_any(
        job, ("failure_action", "action"), "failure action")
    actions = _pick_any(
        job, ("failure_actions", "actions"), "failure actions")
    if actions is not None:
        if not isinstance(actions, (list, tuple)):
            raise ValueError(
                f"job {job_id!r} names its failure actions "
                f"as no list - a failure names the one "
                f"action that matters, as one action")
        if len(actions) != 1:
            raise ValueError(
                f"job {job_id!r} names {len(actions)} "
                f"failure actions - a failure announces "
                f"once with the one action that matters, "
                f"never {len(actions)} of them")
        if action is not None and action != actions[0]:
            raise ValueError(
                f"job {job_id!r} names two different "
                f"failure actions - the one action that "
                f"matters stands alone")
        action = actions[0]
    fields = _provenance(job)
    return JobNotice(
        job_id=_needed(job, ("job_id", "id"), "job id"),
        seq=_needed(job, ("seq", "sequence", "order"), "sequence"),
        outcome=_needed(
            job, ("outcome", "state", "status"), "outcome"),
        duration_seconds=_needed(
            job, ("duration_seconds", "duration", "seconds"),
            "duration"),
        bell_backend=_pick_any(
            job, ("bell_backend", "bell"), "bell backend"),
        os_backend=_pick_any(job, ("os_backend", "os"), "OS backend"),
        failure_action=action,
        **fields)


def build_job(job: Any = None, **kwargs: Any) -> JobNotice:
    """Build one job notice from a mapping or fields."""
    if isinstance(job, JobNotice) and not kwargs:
        return job
    if kwargs:
        if job is not None:
            raise ValueError("a job is built one way at a time")
        return validate_job(dict(kwargs))
    return validate_job(job)


def complete_job(job: Any, duration_seconds: Any = None) -> JobNotice:
    """Stand a running job completed, at a named length.

    The finished job is a new record: outcome
    completed, at the named duration or the
    duration the job already carries. A job that
    already stands finished refuses - a job
    finishes once, as it announces once.
    """
    current = _check_job_ref(job)
    if current.outcome != "running":
        raise ValueError(
            f"job {current.job_id!r} already stands "
            f"{current.outcome} - a job finishes once")
    seconds = current.duration_seconds if (
        duration_seconds is None) else _check_seconds(
            duration_seconds)
    return replace(current, outcome="completed",
                   duration_seconds=seconds)


def fail_job(job: Any, failure_action: Any,
             duration_seconds: Any = None) -> JobNotice:
    """Stand a running job failed, naming its one action.

    The failed job is a new record carrying the
    one action that matters, named whole. A job
    that already stands finished refuses.
    """
    current = _check_job_ref(job)
    if current.outcome != "running":
        raise ValueError(
            f"job {current.job_id!r} already stands "
            f"{current.outcome} - a job finishes once")
    seconds = current.duration_seconds if (
        duration_seconds is None) else _check_seconds(
            duration_seconds)
    return replace(current, outcome="failed",
                   duration_seconds=seconds,
                   failure_action=_check_long_text(
                       failure_action, "a failure action"))


# ---------------------------------------------------------------------
# The announcement: derived from a job, at most once.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class Announcement:
    """One job's announcement, derived whole.

    The announcement carries the job's identity,
    its channel (None while no channel stands
    available - the announcement is still derived
    and its delivery is named unavailable or
    unknown, never faked), its message, and, for
    a failure, the one action that matters. Its
    key is derived from the job's identity alone.
    """

    job_id: str
    outcome: str
    channel: Optional[str]
    availability: str
    message: str
    action: Optional[str]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "job_id", _check_word(self.job_id, "a job id"))
        object.__setattr__(
            self, "outcome", normalize_outcome(self.outcome))
        if self.outcome == "running":
            raise ValueError(
                "a running job carries no announcement - "
                "silence is the default posture")
        if self.channel is not None:
            object.__setattr__(
                self, "channel",
                normalize_channel_name(self.channel))
        word = _clean_text(self.availability, "an availability")
        if word not in AVAILABILITY_WORDS:
            raise ValueError(
                f"an availability is one of "
                f"{AVAILABILITY_WORDS}, got {word!r}")
        object.__setattr__(self, "availability", word)
        if word == "available" and self.channel is None:
            raise ValueError(
                "an available announcement names its channel")
        if word != "available" and self.channel is not None:
            raise ValueError(
                "an announcement whose channel stands "
                f"{word} names no channel - no road is "
                "chosen by invention")
        object.__setattr__(
            self, "message",
            _check_long_text(self.message, "a message"))
        if self.outcome == "failed":
            if not isinstance(self.action, str) or not self.action.strip():
                raise ValueError(
                    f"announcement for failed job "
                    f"{self.job_id!r} names no action - a "
                    f"failure announces with the one action "
                    f"that matters")
            object.__setattr__(
                self, "action",
                _check_long_text(self.action, "a failure action"))
        elif self.action is not None:
            raise ValueError(
                "a completion announcement names no failure "
                "action - the one action stands on a "
                "failure alone")

    @property
    def key(self) -> str:
        return f"{self.job_id}:{self.outcome}"

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "notifications_manners_announcement",
            "slice": NOTIFICATIONS_MANNERS_SLICE,
            "announcement_key": self.key,
            "job_id": self.job_id,
            "outcome": self.outcome,
            "channel": self.channel,
            "availability": self.availability,
            "message": self.message,
            "action": self.action,
        }


def announcement_for(job: Any, announced: Any = (),
                     threshold: int = LONG_JOB_THRESHOLD_SECONDS
                     ) -> Optional[Announcement]:
    """The announcement one job stands due, or None.

    None stands while the job's derived decision
    is silence - a running job, a short completed
    job - and None stands while the job's key
    already stands in *announced*, the announced-
    key ledger a caller holds: the job has
    announced, once, and announces no more. The
    ledger is a plain collection of derived keys;
    nothing here stores a counter on the job.
    """
    current = _check_job_ref(job)
    word, _reason = announcement_decision(current, threshold)
    if word == "silence":
        return None
    if announcement_key(current) in set(announced or ()):
        return None
    channel, aword, _areason = channel_of(current)
    if current.outcome == "failed":
        message = (
            f"Job {current.job_id} failed after "
            f"{current.duration_seconds} seconds - "
            f"{current.failure_action}.")
        action = current.failure_action
    else:
        message = (
            f"Job {current.job_id} finished after "
            f"{current.duration_seconds} seconds.")
        action = None
    return Announcement(
        job_id=current.job_id, outcome=current.outcome,
        channel=channel, availability=aword,
        message=message, action=action)


def due_announcements(source: Any, announced: Any = (),
                      threshold: int = LONG_JOB_THRESHOLD_SECONDS
                      ) -> Tuple[Announcement, ...]:
    """Every announcement a source stands due, in held order.

    One announcement per job whose decision is
    announce and whose key stands outside the
    announced-key ledger - each job at most once,
    however often the source is polled with the
    same ledger.
    """
    seen = set(announced or ())
    due = []
    for item in _held_items(source):
        if not isinstance(item, JobNotice):
            continue
        found = announcement_for(item, seen, threshold)
        if found is not None:
            due.append(found)
            seen.add(found.key)
    return tuple(due)


@dataclass(frozen=True)
class NoticeDelivery:
    """One announcement's delivery outcome, as data.

    The outcome is the word the delivery stood at
    - delivered only while the announcement's
    channel stood available and a seam stood on
    it - with the reason named whole. A delivery
    is a finding about one call through the
    seams, never a stored claim on the job itself.
    """

    announcement_key: str
    job_id: str
    channel: Optional[str]
    outcome: str
    reason: str

    def __post_init__(self) -> None:
        text = _clean_text(
            self.announcement_key, "an announcement key")
        if ":" not in text or len(text) > 200 or "\x00" in text:
            raise ValueError(
                f"an announcement key is a job id and an "
                f"outcome joined by ':', got {text!r}")
        object.__setattr__(self, "announcement_key", text)
        object.__setattr__(
            self, "job_id", _check_word(self.job_id, "a job id"))
        if self.channel is not None:
            object.__setattr__(
                self, "channel",
                normalize_channel_name(self.channel))
        outcome = _clean_text(self.outcome, "an outcome")
        if outcome not in ("delivered",) + AVAILABILITY_WORDS:
            raise ValueError(
                f"a delivery outcome is 'delivered' or one "
                f"of {AVAILABILITY_WORDS}, got {outcome!r}")
        object.__setattr__(self, "outcome", outcome)
        object.__setattr__(
            self, "reason",
            _check_long_text(self.reason, "a reason"))

    @property
    def delivered(self) -> bool:
        return self.outcome == "delivered"

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "notifications_manners_delivery",
            "slice": NOTIFICATIONS_MANNERS_SLICE,
            "announcement_key": self.announcement_key,
            "job_id": self.job_id,
            "channel": self.channel,
            "outcome": self.outcome,
            "reason": self.reason,
            "delivered": self.delivered,
        }


def default_bell() -> Any:
    """The terminal bell seam, lazily.

    Returns a callable that rings the terminal
    bell - the BEL character written to the
    terminal's error stream - and reports True,
    or None where no terminal stream stands. The
    callable takes one announcement.
    """
    import sys
    stream = getattr(sys, "stderr", None)
    if stream is None:
        return None

    def _ring(announcement: Announcement) -> bool:
        try:
            stream.write("\a")
            stream.flush()
        except Exception:
            return False
        return True

    return _ring


def default_notifier() -> Any:
    """The shipped notifications road, lazily.

    Reaches for ``core/notifications.py``'s
    ``notify`` only when called, and returns None
    where that road does not stand. The returned
    callable takes a title and a message, as the
    shipped road does.
    """
    try:
        from .notifications import notify as _notify
    except Exception:
        return None

    def _send(title: str, message: str) -> bool:
        try:
            _notify(title, message)
        except Exception:
            return False
        return True

    return _send


def deliver_announcement(announcement: Any, bell: Any = None,
                         notify: Any = None) -> NoticeDelivery:
    """Deliver one announcement through the channel seams.

    The bell seam is a callable taking the
    announcement; the notifier seam is a callable
    taking a title and a message - the shipped
    roads by default, reached lazily. A seam is
    called only while the announcement's derived
    availability stands available: an unavailable
    or unknown channel is not travelled, and its
    outcome is named, never faked as delivered. A
    seam returning False, or no seam at all,
    likewise delivers nothing and says so.
    """
    if not isinstance(announcement, Announcement):
        raise ValueError(
            f"an announcement is needed, got {announcement!r}")
    current = announcement
    if current.availability != "available":
        return NoticeDelivery(
            announcement_key=current.key, job_id=current.job_id,
            channel=current.channel, outcome=current.availability,
            reason="the announcement's channel stands "
                   f"{current.availability} - no road is "
                   "travelled and nothing is delivered by "
                   "invention")
    if current.channel == "terminal_bell":
        seam = bell if bell is not None else default_bell()
        if seam is None:
            return NoticeDelivery(
                announcement_key=current.key,
                job_id=current.job_id, channel=current.channel,
                outcome="unavailable",
                reason="no bell stands on the terminal seam "
                       "- no terminal stands here, and no "
                       "bell is rung by invention")
        rung = seam(current)
        if rung is False:
            return NoticeDelivery(
                announcement_key=current.key,
                job_id=current.job_id, channel=current.channel,
                outcome="unavailable",
                reason="the bell seam rang nothing - the "
                       "terminal took no bell, and nothing "
                       "was delivered")
        return NoticeDelivery(
            announcement_key=current.key, job_id=current.job_id,
            channel=current.channel, outcome="delivered",
            reason="rung through the terminal bell seam, "
                   "once")
    seam = notify if notify is not None else default_notifier()
    if seam is None:
        return NoticeDelivery(
            announcement_key=current.key, job_id=current.job_id,
            channel=current.channel, outcome="unavailable",
            reason="no notifier stands on the OS seam - the "
                   "shipped notifications road is unavailable "
                   "here, and no notification is posted by "
                   "invention")
    sent = seam(f"Mythic: {current.job_id}", current.message)
    if sent is False:
        return NoticeDelivery(
            announcement_key=current.key, job_id=current.job_id,
            channel=current.channel, outcome="unavailable",
            reason="the OS seam posted nothing - the "
                   "notifications road took no message, and "
                   "nothing was delivered")
    return NoticeDelivery(
        announcement_key=current.key, job_id=current.job_id,
        channel=current.channel, outcome="delivered",
        reason="posted through the shipped notifications "
               "seam, once")


# ---------------------------------------------------------------------
# The channel: one road an announcement may travel.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class ChannelNotice:
    """One notification channel, held whole.

    A channel names its road - terminal bell or
    OS notification - and the backend that road
    travels, with its provenance whole. Its
    availability is derived at call time, never
    stored: a channel is a claim about a road,
    judged from the backend it names.
    """

    channel_id: str
    seq: int
    name: str
    backend: Optional[str]
    detail: str
    recorded_on: str
    actor: str
    source: str
    origin_session: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "channel_id",
            _check_word(self.channel_id, "a channel id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "name", normalize_channel_name(self.name))
        object.__setattr__(
            self, "backend",
            _check_backend(self.backend, "a channel backend"))
        object.__setattr__(
            self, "detail", _check_long_text(self.detail, "a detail"))
        object.__setattr__(
            self, "recorded_on", _check_day(self.recorded_on))
        object.__setattr__(
            self, "actor", _check_long_text(self.actor, "an actor"))
        object.__setattr__(
            self, "source", _check_long_text(self.source, "a source"))
        object.__setattr__(
            self, "origin_session",
            _check_word(self.origin_session, "an origin session"))

    @property
    def kind(self) -> str:
        return "channel"

    @property
    def item_id(self) -> str:
        return self.channel_id

    @property
    def label(self) -> str:
        return self.channel_id

    @property
    def availability(self) -> str:
        return channel_availability(self)[0]

    @property
    def availability_reason(self) -> str:
        return channel_availability(self)[1]

    @property
    def passes(self) -> bool:
        return self.availability == "available"

    @property
    def segment(self) -> str:
        return segment_of(self)

    def to_record(self) -> Dict[str, Any]:
        word, reason = channel_availability(self)
        return {
            "type": "notifications_manners_channel",
            "slice": NOTIFICATIONS_MANNERS_SLICE,
            "channel_id": self.channel_id,
            "seq": self.seq,
            "name": self.name,
            "backend": self.backend,
            "availability": word,
            "availability_reason": reason,
            "passes": self.passes,
            "segment": self.segment,
            "detail": self.detail,
            "recorded_on": self.recorded_on,
            "actor": self.actor,
            "source": self.source,
            "origin_session": self.origin_session,
        }


def _check_channel_ref(value: Any) -> ChannelNotice:
    if isinstance(value, ChannelNotice):
        return value
    if isinstance(value, dict):
        return validate_channel(value)
    raise ValueError(f"a channel notice is needed, got {value!r}")


def channel_availability(channel: Any) -> Tuple[str, str]:
    """A channel's availability, derived whole.

    Available while it names a backend that is not
    the unknown backend; unavailable with the
    missing road named while it names none;
    honestly unknown while the backend it names
    stands unknown.
    """
    current = _check_channel_ref(channel)
    if current.backend is None:
        return ("unavailable",
                f"no backend is named for the "
                f"{current.name} channel - no road stands "
                f"recorded for it here")
    if current.backend == BACKEND_UNKNOWN:
        return ("unknown",
                "the backend this channel names stands "
                "unknown - whether its road travels is "
                "not proven")
    return ("available",
            f"backend {current.backend!r} stands named "
            f"for the {current.name} channel")


def validate_channel(channel: Any) -> ChannelNotice:
    """Judge one channel mapping whole."""
    if isinstance(channel, ChannelNotice):
        return channel
    if not isinstance(channel, dict):
        raise ValueError(
            f"a channel notice must be a mapping, got {channel!r}")
    derived = set(channel) & _CHANNEL_DERIVED
    if derived:
        raise ValueError(
            f"a channel notice carries no stored "
            f"{sorted(derived)} - availability and "
            f"segment are derived from its own fields")
    unknown = set(channel) - _CHANNEL_KEYS - {"type", "slice"}
    if unknown:
        raise ValueError(
            f"a channel notice carries unknown keys: "
            f"{sorted(unknown)}")
    fields = _provenance(channel)
    return ChannelNotice(
        channel_id=_needed(channel, ("channel_id", "id"), "channel id"),
        seq=_needed(channel, ("seq", "sequence", "order"), "sequence"),
        name=_needed(channel, ("name", "channel"), "channel name"),
        backend=_pick_any(channel, ("backend", "road"), "backend"),
        **fields)


def build_channel(channel: Any = None, **kwargs: Any) -> ChannelNotice:
    """Build one channel notice from a mapping or fields."""
    if isinstance(channel, ChannelNotice) and not kwargs:
        return channel
    if kwargs:
        if channel is not None:
            raise ValueError("a channel is built one way at a time")
        return validate_channel(dict(kwargs))
    return validate_channel(channel)


# ---------------------------------------------------------------------
# The rule: the standing law itself, held as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class MannersRule:
    """One rule of the manners law, held whole.

    A rule names itself in the closed rule set and
    states itself in plain words, with its
    provenance whole. The rule is not decoration:
    the layer's derivations are these rules,
    executed - silence by default in the decision,
    announce once in the derived key, and the one
    action in the failure gate.
    """

    rule_id: str
    seq: int
    name: str
    statement: str
    detail: str
    recorded_on: str
    actor: str
    source: str
    origin_session: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "rule_id", _check_word(self.rule_id, "a rule id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "name", normalize_rule_name(self.name))
        object.__setattr__(
            self, "statement",
            _check_long_text(self.statement, "a rule statement"))
        object.__setattr__(
            self, "detail", _check_long_text(self.detail, "a detail"))
        object.__setattr__(
            self, "recorded_on", _check_day(self.recorded_on))
        object.__setattr__(
            self, "actor", _check_long_text(self.actor, "an actor"))
        object.__setattr__(
            self, "source", _check_long_text(self.source, "a source"))
        object.__setattr__(
            self, "origin_session",
            _check_word(self.origin_session, "an origin session"))

    @property
    def kind(self) -> str:
        return "rule"

    @property
    def item_id(self) -> str:
        return self.rule_id

    @property
    def label(self) -> str:
        return self.name

    @property
    def passes(self) -> bool:
        return True

    @property
    def segment(self) -> str:
        return segment_of(self)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "notifications_manners_rule",
            "slice": NOTIFICATIONS_MANNERS_SLICE,
            "rule_id": self.rule_id,
            "seq": self.seq,
            "name": self.name,
            "statement": self.statement,
            "passes": True,
            "segment": self.segment,
            "detail": self.detail,
            "recorded_on": self.recorded_on,
            "actor": self.actor,
            "source": self.source,
            "origin_session": self.origin_session,
        }


def _check_rule_ref(value: Any) -> MannersRule:
    if isinstance(value, MannersRule):
        return value
    if isinstance(value, dict):
        return validate_rule(value)
    raise ValueError(f"a manners rule is needed, got {value!r}")


def validate_rule(rule: Any) -> MannersRule:
    """Judge one manners rule mapping whole."""
    if isinstance(rule, MannersRule):
        return rule
    if not isinstance(rule, dict):
        raise ValueError(
            f"a manners rule must be a mapping, got {rule!r}")
    derived = set(rule) & _RULE_DERIVED
    if derived:
        raise ValueError(
            f"a manners rule carries no stored "
            f"{sorted(derived)} - its segment is derived "
            f"from its own fields")
    unknown = set(rule) - _RULE_KEYS - {"type", "slice"}
    if unknown:
        raise ValueError(
            f"a manners rule carries unknown keys: "
            f"{sorted(unknown)}")
    fields = _provenance(rule)
    return MannersRule(
        rule_id=_needed(rule, ("rule_id", "id"), "rule id"),
        seq=_needed(rule, ("seq", "sequence", "order"), "sequence"),
        name=_needed(rule, ("name", "rule"), "rule name"),
        statement=_needed(
            rule, ("statement", "text", "words"), "rule statement"),
        **fields)


def build_rule(rule: Any = None, **kwargs: Any) -> MannersRule:
    """Build one manners rule from a mapping or fields."""
    if isinstance(rule, MannersRule) and not kwargs:
        return rule
    if kwargs:
        if rule is not None:
            raise ValueError("a rule is built one way at a time")
        return validate_rule(dict(kwargs))
    return validate_rule(rule)


# ---------------------------------------------------------------------
# Derived judgements shared by every item kind.
# ---------------------------------------------------------------------


def segment_of(item: Any) -> str:
    """One item's derived segment, from its own fields."""
    if isinstance(item, JobNotice):
        word, _reason = announcement_decision(item)
        channel, _aword, _areason = channel_of(item)
        road = channel if channel is not None else "no channel"
        return (
            f"{item.job_id}: job {item.outcome} after "
            f"{item.duration_seconds}s, decision {word}, "
            f"channel {road}")
    if isinstance(item, ChannelNotice):
        word, _reason = channel_availability(item)
        backend = item.backend if item.backend is not None \
            else "no backend named"
        return (
            f"{item.channel_id}: channel {item.name}, "
            f"availability {word}, backend {backend}")
    if isinstance(item, MannersRule):
        return (
            f"{item.name}: manners rule stands - "
            f"{item.statement}")
    raise ValueError(f"a manners item is needed, got {item!r}")


def availability_of(item: Any) -> Tuple[str, str]:
    """One item's availability, derived whole.

    Jobs and channels derive theirs from the
    backends they name. A rule's road stands
    available by the law itself: it travels as
    text wherever the book is read.
    """
    if isinstance(item, JobNotice):
        return job_availability(item)
    if isinstance(item, ChannelNotice):
        return channel_availability(item)
    if isinstance(item, MannersRule):
        return ("available",
                "the rule stands in the book's own text - "
                "it travels wherever the book is read")
    raise ValueError(f"a manners item is needed, got {item!r}")


def item_passes(item: Any) -> bool:
    """Whether one item of any kind stands whole."""
    if isinstance(item, JobNotice):
        return job_passes(item)
    if isinstance(item, ChannelNotice):
        return item.availability == "available"
    if isinstance(item, MannersRule):
        return True
    raise ValueError(f"a manners item is needed, got {item!r}")


def _check_item_ref(value: Any) -> Any:
    if isinstance(value, (JobNotice, ChannelNotice, MannersRule)):
        return value
    raise ValueError(f"a manners item is needed, got {value!r}")


def inspect_item_source(piece: Any) -> Dict[str, Any]:
    """Judge one raw manners piece and name what it is.

    A mapping carrying an outcome or a duration is
    read as a job piece, one carrying a channel
    name as a channel piece, and one carrying a
    rule name or a statement as a rule piece.
    Anything else is named not-a-manners-item.
    """
    if not isinstance(piece, dict):
        return {"kind": None,
                "reason": "not a mapping - no manners item stands here"}
    if "outcome" in piece or "duration_seconds" in piece \
            or "job_id" in piece:
        if "announced" in piece:
            return {"kind": None,
                    "reason": "a job piece carrying a stored "
                              "announced flag - once-only is "
                              "derived from identity, and the "
                              "piece refuses by name"}
        return {"kind": "job",
                "reason": "a job piece in the closed kind set"}
    if "channel_id" in piece or (
            "name" in piece and "backend" in piece):
        return {"kind": "channel",
                "reason": "a channel piece in the closed kind set"}
    if "rule_id" in piece or "statement" in piece:
        return {"kind": "rule",
                "reason": "a rule piece in the closed kind set"}
    return {"kind": None,
            "reason": "no outcome, no channel and no "
                      "statement named - no manners "
                      "item stands here"}


# ---------------------------------------------------------------------
# The view record: the one kind a panel looks at, held whole.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class NoticeView:
    """One view, held as its own record.

    A view looks at every kind at once, or at one
    kind alone. A view only ever looks: standing
    one derives its panel, announces nothing and
    delivers nothing.
    """

    view_id: Optional[str]
    seq: int
    kind_filter: str
    detail: str
    recorded_on: str
    actor: str
    source: str
    origin_session: str

    def __post_init__(self) -> None:
        if self.view_id is not None:
            object.__setattr__(
                self, "view_id",
                _check_word(self.view_id, "a view id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "kind_filter",
            normalize_kind_filter(self.kind_filter))
        object.__setattr__(
            self, "detail", _check_long_text(self.detail, "a detail"))
        object.__setattr__(
            self, "recorded_on", _check_day(self.recorded_on))
        object.__setattr__(
            self, "actor", _check_long_text(self.actor, "an actor"))
        object.__setattr__(
            self, "source", _check_long_text(self.source, "a source"))
        object.__setattr__(
            self, "origin_session",
            _check_word(self.origin_session, "an origin session"))

    def shows(self, item: Any) -> bool:
        current = _check_item_ref(item)
        return self.kind_filter == "all" \
            or current.kind == self.kind_filter

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "notifications_manners_view",
            "slice": NOTIFICATIONS_MANNERS_SLICE,
            "view_id": self.view_id,
            "seq": self.seq,
            "kind_filter": self.kind_filter,
            "detail": self.detail,
            "recorded_on": self.recorded_on,
            "actor": self.actor,
            "source": self.source,
            "origin_session": self.origin_session,
        }


def _check_view_ref(value: Any) -> NoticeView:
    if isinstance(value, NoticeView):
        return value
    if isinstance(value, dict):
        return validate_view(value)
    raise ValueError(f"a manners view is needed, got {value!r}")


def validate_view(view: Any) -> NoticeView:
    """Judge one view mapping whole."""
    if isinstance(view, NoticeView):
        return view
    if not isinstance(view, dict):
        raise ValueError(f"a manners view must be a mapping, got {view!r}")
    unknown = set(view) - _VIEW_KEYS - {"type", "slice"}
    if unknown:
        raise ValueError(
            f"a manners view carries unknown keys: {sorted(unknown)}")
    fields = _provenance(view)
    return NoticeView(
        view_id=_pick_any(view, ("view_id", "id"), "view id"),
        seq=_needed(view, ("seq", "sequence", "order"), "sequence"),
        kind_filter=_needed(
            view, ("kind_filter", "filter", "kind"), "kind filter"),
        **fields)


def build_view(view: Any = None, **kwargs: Any) -> NoticeView:
    """Build one view from a mapping, a view, or fields."""
    if isinstance(view, NoticeView) and not kwargs:
        return view
    if kwargs:
        if view is not None:
            raise ValueError("a view is built one way at a time")
        return validate_view(dict(kwargs))
    return validate_view(view)


# ---------------------------------------------------------------------
# The panel: derived for one held view.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class NoticePanelRow:
    """One shown item's row on a derived panel."""

    item_id: str
    kind: str
    label: str
    segment: str
    recorded_on: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "item_id", _check_word(self.item_id, "an item id"))
        object.__setattr__(
            self, "kind", normalize_kind(self.kind))
        object.__setattr__(
            self, "label", _check_long_text(self.label, "a label"))
        object.__setattr__(
            self, "segment",
            _check_long_text(self.segment, "a segment"))
        object.__setattr__(
            self, "recorded_on", _check_day(self.recorded_on))

    def to_record(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "kind": self.kind,
            "label": self.label,
            "segment": self.segment,
            "recorded_on": self.recorded_on,
        }


def _row_for_item(item: Any) -> NoticePanelRow:
    current = _check_item_ref(item)
    return NoticePanelRow(
        item_id=current.item_id, kind=current.kind,
        label=current.label, segment=segment_of(current),
        recorded_on=current.recorded_on)


def _check_row_ref(value: Any) -> NoticePanelRow:
    if isinstance(value, NoticePanelRow):
        return value
    raise ValueError(f"a panel row is needed, got {value!r}")


def validate_row(row: Any, item: Any = None) -> NoticePanelRow:
    """Judge one panel row, against its item when one is named."""
    if isinstance(row, NoticePanelRow):
        current = row
    elif isinstance(row, dict):
        unknown = set(row) - _ROW_KEYS
        if unknown:
            raise ValueError(
                f"a panel row carries unknown keys: "
                f"{sorted(unknown)}")
        current = NoticePanelRow(
            item_id=_needed(row, ("item_id", "id"), "item id"),
            kind=_needed(row, ("kind",), "kind"),
            label=_needed(row, ("label", "name"), "label"),
            segment=_needed(row, ("segment",), "segment"),
            recorded_on=_needed(
                row, ("recorded_on", "day", "date"), "recorded day"))
    else:
        raise ValueError(f"a panel row must be a mapping, got {row!r}")
    if item is not None:
        expected = _row_for_item(item)
        if current != expected:
            raise ValueError(
                "a panel row is its item's own derived row - "
                "a stored row disagreeing with its item refuses")
    return current


def build_row(row: Any = None, item: Any = None,
              **kwargs: Any) -> NoticePanelRow:
    """Build one panel row from a mapping, a row, or an item."""
    if item is not None:
        if kwargs:
            raise ValueError("a row is built one way at a time")
        if row is not None:
            return validate_row(row, item)
        return _row_for_item(item)
    if isinstance(row, NoticePanelRow) and not kwargs:
        return row
    if kwargs:
        if row is not None:
            raise ValueError("a row is built one way at a time")
        return validate_row(dict(kwargs))
    return validate_row(row)


@dataclass(frozen=True)
class NoticeKindCount:
    """How many shown items stand of one kind."""

    kind: str
    items: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "kind", normalize_kind(self.kind))
        object.__setattr__(
            self, "items", _check_count(self.items, "a kind count"))

    def to_record(self) -> Dict[str, Any]:
        return {"kind": self.kind, "items": self.items}


def _check_kind_count_ref(value: Any) -> NoticeKindCount:
    if isinstance(value, NoticeKindCount):
        return value
    if isinstance(value, dict):
        return NoticeKindCount(
            kind=_needed(value, ("kind",), "kind"),
            items=_needed(value, ("items",), "items"))
    raise ValueError(f"a kind count is needed, got {value!r}")


def _kind_counts(rows: Tuple[NoticePanelRow, ...]) -> Tuple[NoticeKindCount, ...]:
    counts = []
    for kind in ITEM_KINDS:
        n = sum(1 for row in rows if row.kind == kind)
        if n:
            counts.append(NoticeKindCount(kind=kind, items=n))
    return tuple(counts)


def _panel_account(total_items: int, total_shown: int,
                   kind_counts: Tuple[NoticeKindCount, ...],
                   kind_filter: str, as_of: Optional[str],
                   passing: int) -> Tuple[str, ...]:
    kinds = ", ".join(f"{c.kind} {c.items}" for c in kind_counts)
    if not kinds:
        kinds = "no kinds"
    return (
        f"The notifications book holds {total_items} items as of "
        f"{as_of}: the view {kind_filter!r} shows "
        f"{total_shown} of them: {kinds}; {passing} of "
        f"the shown items stand whole.",
        "Rows stand in held order, the order the book "
        "itself stands in, so two panels of one view "
        "diff cleanly, segment by segment.",
        "Every segment is derived from its item's own "
        "fields - a decision from its outcome and "
        "duration, a channel from the backends it "
        "names - and no judgement is stored on any item.",
        "Silence is the default posture: running jobs "
        "and short jobs announce nothing, a long job "
        "announces once, and a failure announces once "
        "with the one action that matters.",
    )


@dataclass(frozen=True)
class NoticePanel:
    """The derived panel of one book under one view.

    Rows stand in held order; the totals are the
    rows' own counts and the kind counts stand in
    the closed kind order. A stored panel is
    judged whole: its totals, counts and account
    must all be the rows' own derived shape.
    """

    panel_id: Optional[str]
    view_id: Optional[str]
    kind_filter: str
    rows: Tuple[NoticePanelRow, ...]
    total_items: int
    total_shown: int
    kind_counts: Tuple[NoticeKindCount, ...]
    as_of: Optional[str]
    account: Tuple[str, ...]

    def __post_init__(self) -> None:
        if self.panel_id is not None:
            object.__setattr__(
                self, "panel_id",
                _check_word(self.panel_id, "a panel id"))
        if self.view_id is not None:
            object.__setattr__(
                self, "view_id",
                _check_word(self.view_id, "a view id"))
        object.__setattr__(
            self, "kind_filter",
            normalize_kind_filter(self.kind_filter))
        rows = tuple(_check_row_ref(r) for r in self.rows)
        object.__setattr__(self, "rows", rows)
        ids = [r.item_id for r in rows]
        if len(set(ids)) != len(ids):
            raise ValueError("panel rows stand one row per item")
        for row in rows:
            if self.kind_filter != "all" and (
                    row.kind != self.kind_filter):
                raise ValueError(
                    "a panel row stands outside its view's "
                    "kind - the view narrows the panel, "
                    "never widens it")
        for field in ("total_items", "total_shown"):
            object.__setattr__(
                self, field,
                _check_count(getattr(self, field), f"a panel's {field}"))
        counts = tuple(
            _check_kind_count_ref(c) for c in self.kind_counts)
        object.__setattr__(self, "kind_counts", counts)
        if self.as_of is not None:
            object.__setattr__(
                self, "as_of", _check_day(self.as_of, "an as-of day"))
        object.__setattr__(self, "account", _check_account(self.account))
        if self.total_shown != len(rows):
            raise ValueError("a panel's shown total is its rows' own count")
        if self.total_items < self.total_shown:
            raise ValueError(
                "a panel's item total cannot stand below "
                "its shown total")
        if counts != _kind_counts(rows):
            raise ValueError("a panel's kind counts are its rows' own counts")
        if rows and self.as_of is not None and (
                self.as_of < max(r.recorded_on for r in rows)):
            raise ValueError("a panel's as-of day precedes one of its rows")

    def row_for(self, item_id: Any) -> NoticePanelRow:
        """The row one item id names (KeyError if absent)."""
        wanted = _check_word(item_id, "an item id")
        for row in self.rows:
            if row.item_id == wanted:
                return row
        raise KeyError(f"no row named {wanted!r} stands on the panel")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "notifications_manners_panel",
            "slice": NOTIFICATIONS_MANNERS_SLICE,
            "panel_id": self.panel_id,
            "view_id": self.view_id,
            "kind_filter": self.kind_filter,
            "rows": [r.to_record() for r in self.rows],
            "total_items": self.total_items,
            "total_shown": self.total_shown,
            "kind_counts": [c.to_record() for c in self.kind_counts],
            "as_of": self.as_of,
            "account": list(self.account),
        }


def _held_items(source: Any) -> Tuple[Any, ...]:
    if isinstance(source, NoticeBook):
        return source.items()
    if isinstance(source, NoticeRegistry):
        return source.book().items()
    if isinstance(source, (JobNotice, ChannelNotice, MannersRule)):
        return (source,)
    if isinstance(source, (list, tuple)):
        return tuple(_check_item_ref(i) for i in source)
    raise ValueError(f"a manners source is needed, got {source!r}")


def _held_views(source: Any) -> Tuple[NoticeView, ...]:
    if isinstance(source, NoticeBook):
        return source.views
    if isinstance(source, NoticeRegistry):
        return source.book().views
    return ()


def _resolve_view(source: Any, view: Any) -> NoticeView:
    if isinstance(view, NoticeView):
        return view
    if isinstance(view, str):
        wanted = _check_word(view, "a view id")
        for held in _held_views(source):
            if held.view_id == wanted:
                return held
        raise KeyError(f"no view named {wanted!r} stands in the book")
    if view is None:
        return _default_view(source)
    raise ValueError(f"a manners view is needed, got {view!r}")


def _default_view(source: Any) -> NoticeView:
    views = _held_views(source)
    if isinstance(source, NoticeBook) and source.panels:
        for panel in source.panels:
            if panel.view_id is not None:
                for held in views:
                    if held.view_id == panel.view_id:
                        return held
    if views:
        return views[0]
    return NoticeView(
        view_id=None, seq=1, kind_filter="all",
        detail="See the whole notifications book, every kind at once.",
        recorded_on="2026-11-09", actor="the coordinator",
        source="notifications with manners", origin_session="session-m181")


def shown_items(source: Any, view: Any = None) -> Tuple[Any, ...]:
    """The items one view shows, in held order."""
    held_view = _resolve_view(source, view)
    return tuple(i for i in _held_items(source) if held_view.shows(i))


def items_for_kind(source: Any, kind: Any) -> Tuple[Any, ...]:
    """The items of one kind, in held order."""
    wanted = normalize_kind(kind)
    return tuple(i for i in _held_items(source) if i.kind == wanted)


def passing_items(source: Any) -> Tuple[Any, ...]:
    """The items standing whole, in held order."""
    return tuple(i for i in _held_items(source) if item_passes(i))


def total_items(source: Any) -> int:
    """How many items a source holds."""
    return len(_held_items(source))


def derive_panel(source: Any, view: Any = None) -> NoticePanel:
    """Derive the panel of a book under one view."""
    held_view = _resolve_view(source, view)
    items = _held_items(source)
    shown = tuple(i for i in items if held_view.shows(i))
    rows = tuple(_row_for_item(i) for i in shown)
    counts = _kind_counts(rows)
    days = [i.recorded_on for i in shown] or \
        [i.recorded_on for i in items]
    as_of = max(days) if days else None
    passing = sum(1 for i in shown if item_passes(i))
    return NoticePanel(
        panel_id=None, view_id=held_view.view_id,
        kind_filter=held_view.kind_filter, rows=rows,
        total_items=len(items), total_shown=len(shown),
        kind_counts=counts, as_of=as_of,
        account=_panel_account(
            len(items), len(shown), counts,
            held_view.kind_filter, as_of, passing))


def validate_panel(panel: Any, source: Any = None) -> NoticePanel:
    """Judge one panel whole, against its source when named."""
    if isinstance(panel, NoticePanel):
        current = panel
    elif isinstance(panel, dict):
        unknown = set(panel) - _PANEL_KEYS - {"type", "slice"}
        if unknown:
            raise ValueError(
                f"a panel carries unknown keys: {sorted(unknown)}")
        rows_in = _needed(panel, ("rows", "shown"), "rows")
        counts_in = _pick_any(
            panel, ("kind_counts", "kinds"), "kind counts") or ()
        current = NoticePanel(
            panel_id=_pick_any(panel, ("panel_id", "id"), "panel id"),
            view_id=_pick_any(panel, ("view_id", "view"), "view id"),
            kind_filter=_needed(
                panel, ("kind_filter", "filter", "kind"),
                "kind filter"),
            rows=tuple(validate_row(r) for r in rows_in),
            total_items=_needed(
                panel, ("total_items", "items"), "total items"),
            total_shown=_needed(
                panel, ("total_shown", "matched"), "total shown"),
            kind_counts=tuple(
                _check_kind_count_ref(c) for c in counts_in),
            as_of=_pick_any(panel, ("as_of", "day"), "as-of day"),
            account=_needed(
                panel, ("account", "statements"), "account"))
    else:
        raise ValueError(f"a panel must be a mapping, got {panel!r}")
    if source is not None:
        derived = derive_panel(source, current.view_id)
        if (current.kind_filter != derived.kind_filter
                or current.rows != derived.rows
                or current.total_items != derived.total_items
                or current.total_shown != derived.total_shown
                or current.kind_counts != derived.kind_counts
                or current.as_of != derived.as_of
                or current.account != derived.account):
            raise ValueError(
                "a stored panel disagreeing with its derived "
                "panel refuses - panels are derived, never "
                "written by hand")
    return current


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> NoticePanel:
    """Build one panel from a mapping, a panel, or a source."""
    if kwargs:
        if panel is not None:
            raise ValueError("a panel is built one way at a time")
        return validate_panel(dict(kwargs), source)
    if isinstance(panel, NoticePanel):
        return validate_panel(panel, source)
    if isinstance(panel, dict):
        return validate_panel(panel, source)
    if panel is None and source is not None:
        return derive_panel(source)
    return validate_panel(panel, source)


# ---------------------------------------------------------------------
# The verdict: derived for the whole book under one view.
# ---------------------------------------------------------------------


def _verdict_word(total_shown: int, passing_shown: int) -> str:
    if total_shown == 0 or passing_shown == 0:
        return "shut"
    if passing_shown == total_shown:
        return "open"
    return "strained"


@dataclass(frozen=True)
class NoticeVerdict:
    """The derived verdict of one whole book under one view.

    The word is read off the shown items alone:
    shut while no shown item stands whole, open
    while every shown item does, strained
    otherwise. A stored verdict is judged against
    those tallies in ``__post_init__``.
    """

    total_items: int
    total_shown: int
    passing_shown: int
    distinct_kinds: int
    earliest_on: Optional[str]
    latest_on: Optional[str]
    verdict: str

    def __post_init__(self) -> None:
        for field in ("total_items", "total_shown",
                      "passing_shown", "distinct_kinds"):
            object.__setattr__(
                self, field,
                _check_count(getattr(self, field), f"a verdict's {field}"))
        if self.earliest_on is not None:
            object.__setattr__(
                self, "earliest_on",
                _check_day(self.earliest_on, "an earliest day"))
        if self.latest_on is not None:
            object.__setattr__(
                self, "latest_on",
                _check_day(self.latest_on, "a latest day"))
        if self.earliest_on is not None and self.latest_on is not None \
                and self.latest_on < self.earliest_on:
            raise ValueError("a verdict's latest day precedes its earliest")
        if self.total_shown > self.total_items:
            raise ValueError(
                "a verdict's shown tally cannot exceed its item total")
        if self.passing_shown > self.total_shown:
            raise ValueError(
                "a verdict's passing tally cannot exceed its shown tally")
        if self.total_shown == 0 and (
                self.distinct_kinds != 0 or self.passing_shown != 0):
            raise ValueError(
                "an empty showing names no kind and no passing item")
        if self.distinct_kinds > self.total_shown:
            raise ValueError(
                "a verdict's kinds cannot exceed its shown items")
        word = _clean_text(self.verdict, "a verdict")
        if word not in VERDICT_WORDS:
            raise ValueError(
                f"a verdict is one of {VERDICT_WORDS}, got {word!r}")
        object.__setattr__(self, "verdict", word)
        if word != _verdict_word(self.total_shown, self.passing_shown):
            raise ValueError(
                "a verdict's word is derived from its tallies, "
                "never chosen")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "notifications_manners_verdict",
            "slice": NOTIFICATIONS_MANNERS_SLICE,
            "total_items": self.total_items,
            "total_shown": self.total_shown,
            "passing_shown": self.passing_shown,
            "distinct_kinds": self.distinct_kinds,
            "earliest_on": self.earliest_on,
            "latest_on": self.latest_on,
            "verdict": self.verdict,
        }


def derive_verdict(source: Any, view: Any = None) -> NoticeVerdict:
    """Derive the verdict of a book under one view."""
    held_view = _resolve_view(source, view)
    items = _held_items(source)
    shown = tuple(i for i in items if held_view.shows(i))
    passing = sum(1 for i in shown if item_passes(i))
    days = [i.recorded_on for i in shown]
    return NoticeVerdict(
        total_items=len(items), total_shown=len(shown),
        passing_shown=passing,
        distinct_kinds=len({i.kind for i in shown}),
        earliest_on=min(days) if days else None,
        latest_on=max(days) if days else None,
        verdict=_verdict_word(len(shown), passing))


def _check_verdict_ref(value: Any) -> NoticeVerdict:
    if isinstance(value, NoticeVerdict):
        return value
    raise ValueError(f"a manners verdict is needed, got {value!r}")


def validate_verdict(verdict: Any, source: Any = None,
                     view: Any = None) -> NoticeVerdict:
    """Judge one verdict whole, against its source when named."""
    if isinstance(verdict, NoticeVerdict):
        current = verdict
    elif isinstance(verdict, dict):
        unknown = set(verdict) - _VERDICT_KEYS - {"type", "slice"}
        if unknown:
            raise ValueError(
                f"a verdict carries unknown keys: {sorted(unknown)}")
        current = NoticeVerdict(
            total_items=_needed(
                verdict, ("total_items", "items"), "total items"),
            total_shown=_needed(
                verdict, ("total_shown", "matched"), "total shown"),
            passing_shown=_needed(
                verdict, ("passing_shown", "passing"), "passing shown"),
            distinct_kinds=_needed(
                verdict, ("distinct_kinds", "kinds"), "distinct kinds"),
            earliest_on=_pick_any(
                verdict, ("earliest_on", "earliest"), "earliest day"),
            latest_on=_pick_any(
                verdict, ("latest_on", "latest"), "latest day"),
            verdict=_needed(verdict, ("verdict",), "verdict"))
    else:
        raise ValueError(f"a verdict must be a mapping, got {verdict!r}")
    if source is not None:
        derived = derive_verdict(source, view)
        if current != derived:
            raise ValueError(
                "a stored verdict disagreeing with its derived "
                "verdict refuses - verdicts are derived, "
                "never written by hand")
    return current


def build_verdict(verdict: Any = None, source: Any = None,
                  **kwargs: Any) -> NoticeVerdict:
    """Build one verdict from a mapping, a verdict, or a source."""
    if kwargs:
        if verdict is not None:
            raise ValueError("a verdict is built one way at a time")
        return validate_verdict(dict(kwargs), source)
    if isinstance(verdict, NoticeVerdict):
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        return validate_verdict(verdict, source)
    if verdict is None and source is not None:
        return derive_verdict(source)
    return validate_verdict(verdict, source)


# ---------------------------------------------------------------------
# The book: notifications with manners, held whole under a title.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class NoticeBook:
    """One set of manners items and views, held whole.

    Jobs, channels and rules stand in held order -
    one item per id within its kind, one sequence
    per kind, one rule per name - views stand in
    recorded order, one view per sequence and per
    id, and every stored panel is judged against
    the book and the view it stands under. The
    book carries no verdict: verdicts are derived
    from its items at call time.
    """

    title: str
    jobs: Tuple[JobNotice, ...] = ()
    channels: Tuple[ChannelNotice, ...] = ()
    rules: Tuple[MannersRule, ...] = ()
    views: Tuple[NoticeView, ...] = ()
    panels: Tuple[NoticePanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_title(self.title, "a book title"))
        jobs = tuple(_check_job_ref(d) for d in self.jobs)
        object.__setattr__(self, "jobs", jobs)
        ids = [d.job_id for d in jobs]
        if len(set(ids)) != len(ids):
            raise ValueError("a book holds one job per job id")
        seqs = [d.seq for d in jobs]
        if len(set(seqs)) != len(seqs):
            raise ValueError("a book holds one job per sequence")
        channels = tuple(_check_channel_ref(s) for s in self.channels)
        object.__setattr__(self, "channels", channels)
        ids = [s.channel_id for s in channels]
        if len(set(ids)) != len(ids):
            raise ValueError("a book holds one channel per channel id")
        seqs = [s.seq for s in channels]
        if len(set(seqs)) != len(seqs):
            raise ValueError("a book holds one channel per sequence")
        rules = tuple(_check_rule_ref(a) for a in self.rules)
        object.__setattr__(self, "rules", rules)
        ids = [a.rule_id for a in rules]
        if len(set(ids)) != len(ids):
            raise ValueError("a book holds one rule per rule id")
        names = [a.name for a in rules]
        if len(set(names)) != len(names):
            raise ValueError("a book holds one rule per rule name")
        seqs = [a.seq for a in rules]
        if len(set(seqs)) != len(seqs):
            raise ValueError("a book holds one rule per sequence")
        views = tuple(_check_view_ref(v) for v in self.views)
        object.__setattr__(self, "views", views)
        seqs = [v.seq for v in views]
        if seqs != sorted(seqs) or len(set(seqs)) != len(seqs):
            raise ValueError(
                "a book's views stand in recorded order, "
                "one view per sequence")
        view_ids = [v.view_id for v in views if v.view_id is not None]
        if len(set(view_ids)) != len(view_ids):
            raise ValueError("a book holds one view per view id")
        panels = tuple(validate_panel(p, self) for p in self.panels)
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        """Every item in held order: jobs, channels, rules."""
        return tuple(self.jobs) + tuple(self.channels) \
            + tuple(self.rules)

    def job_for(self, job_id: Any) -> JobNotice:
        """The job one id names (KeyError if absent)."""
        wanted = _check_word(job_id, "a job id")
        for item in self.jobs:
            if item.job_id == wanted:
                return item
        raise KeyError(f"no job named {wanted!r} stands in the book")

    def channel_for(self, channel_id: Any) -> ChannelNotice:
        """The channel one id names (KeyError if absent)."""
        wanted = _check_word(channel_id, "a channel id")
        for item in self.channels:
            if item.channel_id == wanted:
                return item
        raise KeyError(
            f"no channel named {wanted!r} stands in the book")

    def rule_for(self, rule_id: Any) -> MannersRule:
        """The rule one id names (KeyError if absent)."""
        wanted = _check_word(rule_id, "a rule id")
        for item in self.rules:
            if item.rule_id == wanted:
                return item
        raise KeyError(f"no rule named {wanted!r} stands in the book")

    def view_for(self, view_id: Any) -> NoticeView:
        """The view one id names (KeyError if absent)."""
        wanted = _check_word(view_id, "a view id")
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no view named {wanted!r} stands in the book")

    def panel_for(self, panel_id: Any) -> NoticePanel:
        """The panel one id names (KeyError if absent)."""
        wanted = _check_word(panel_id, "a panel id")
        for panel in self.panels:
            if panel.panel_id == wanted:
                return panel
        raise KeyError(f"no panel named {wanted!r} stands in the book")

    def job_ids(self) -> Tuple[str, ...]:
        return tuple(d.job_id for d in self.jobs)

    def channel_ids(self) -> Tuple[str, ...]:
        return tuple(s.channel_id for s in self.channels)

    def rule_ids(self) -> Tuple[str, ...]:
        return tuple(a.rule_id for a in self.rules)

    def view_ids(self) -> Tuple[Optional[str], ...]:
        return tuple(v.view_id for v in self.views)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "notifications_manners_book",
            "slice": NOTIFICATIONS_MANNERS_SLICE,
            "title": self.title,
            "jobs": [d.to_record() for d in self.jobs],
            "channels": [s.to_record() for s in self.channels],
            "rules": [a.to_record() for a in self.rules],
            "views": [v.to_record() for v in self.views],
            "panels": [p.to_record() for p in self.panels],
            "job_count": len(self.jobs),
            "channel_count": len(self.channels),
            "rule_count": len(self.rules),
            "view_count": len(self.views),
            "item_count": len(self.items()),
        }


def _judge_book_panels(book: NoticeBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _strip_derived(raw: Dict[str, Any],
                     derived: frozenset) -> Dict[str, Any]:
    stored = dict(raw)
    stored.pop("type", None)
    stored.pop("slice", None)
    for key in derived:
        stored.pop(key, None)
    return stored


def validate_book(data: Any, *, require_example: bool = False) -> NoticeBook:
    """Judge one manners file's data whole and return its book."""
    if isinstance(data, NoticeBook):
        book = data
        _judge_book_panels(book)
        if require_example:
            _check_example(book)
        return book
    if not isinstance(data, dict):
        raise ValueError(f"a manners book must be a mapping, got {data!r}")
    if "verdict" in data or "segment" in data:
        raise ValueError(
            "a manners book carries no stored verdict or "
            "segment - judgements are derived from its "
            "items, never stored")
    unknown = set(data) - _NOTIFICATIONS_MANNERS_KEYS
    if unknown:
        raise ValueError(
            f"a manners book carries unknown keys: {sorted(unknown)}")
    if data.get("schema") != NOTIFICATIONS_MANNERS_SCHEMA:
        raise ValueError(
            f"a manners book's schema must be "
            f"{NOTIFICATIONS_MANNERS_SCHEMA!r}, got {data.get('schema')!r}")
    if data.get("slice") != NOTIFICATIONS_MANNERS_SLICE:
        raise ValueError(
            f"a manners book's slice must be "
            f"{NOTIFICATIONS_MANNERS_SLICE!r}, got {data.get('slice')!r}")
    guide = data.get("guide") or {}
    title = _pick_any(guide, ("title", "name"), "title")
    if title is None:
        title = _pick_any(data, ("title", "name"), "title")
    if title is None:
        raise ValueError("a manners book names no title")
    jobs = [
        validate_job(_strip_derived(raw, _JOB_DERIVED))
        for raw in data.get("jobs") or []]
    channels = [
        validate_channel(_strip_derived(raw, _CHANNEL_DERIVED))
        for raw in data.get("channels") or []]
    rules = [
        validate_rule(_strip_derived(raw, _RULE_DERIVED))
        for raw in data.get("rules") or []]
    views = []
    for raw in data.get("views") or []:
        stored = dict(raw)
        stored.pop("type", None)
        stored.pop("slice", None)
        views.append(validate_view(stored))
    book = NoticeBook(
        title=title,
        jobs=tuple(jobs),
        channels=tuple(channels),
        rules=tuple(rules),
        views=tuple(views),
        panels=tuple(
            validate_panel(p) for p in data.get("panels") or []))
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def _check_example(book: NoticeBook) -> None:
    if book.title != _EXAMPLE_TITLE:
        raise ValueError(
            f"the shipped example book is {_EXAMPLE_TITLE!r}, "
            f"got {book.title!r}")
    if book.job_ids() != _EXAMPLE_JOB_IDS:
        raise ValueError("the shipped example book's jobs differ")
    if book.channel_ids() != _EXAMPLE_CHANNEL_IDS:
        raise ValueError("the shipped example book's channels differ")
    if book.rule_ids() != _EXAMPLE_RULE_IDS:
        raise ValueError("the shipped example book's rules differ")
    first = book.jobs[0]
    if first.job_id != _EXAMPLE_FIRST_JOB_ID:
        raise ValueError("the shipped example book's first job differs")
    if book.view_ids() != _EXAMPLE_VIEW_IDS:
        raise ValueError("the shipped example book's views differ")
    if len(book.panels) != 1 or (
            book.panels[0].panel_id != _EXAMPLE_PANEL_ID):
        raise ValueError("the shipped example book's panel differs")
    if book.panels[0].as_of != _EXAMPLE_AS_OF:
        raise ValueError("the shipped example book's as-of day differs")
    derived = derive_panel(book, book.panels[0].view_id)
    if tuple(r.item_id for r in book.panels[0].rows) != tuple(
            r.item_id for r in derived.rows):
        raise ValueError("the shipped example book's panel rows differ")


def build_book(book: Any = None, **kwargs: Any) -> NoticeBook:
    """Build one book from a mapping, a book, or fields."""
    if isinstance(book, NoticeBook) and not kwargs:
        return validate_book(book)
    if kwargs:
        if book is not None:
            raise ValueError("a book is built one way at a time")
        fields = dict(kwargs)
    elif isinstance(book, dict) and (
            "jobs" in book or "channels" in book
            or "rules" in book) and (
            "schema" not in book and "guide" not in book
            and "canon_note" not in book):
        fields = dict(book)
    else:
        return _book_from(book, require_example=False)
    unknown = set(fields) - _BOOK_KEYS - {
        "jobs", "channels", "rules", "views", "panels"}
    if unknown:
        raise ValueError(
            f"a manners book carries unknown keys: {sorted(unknown)}")
    title = _pick_any(fields, ("title", "name"), "title")
    if title is None:
        raise ValueError("a manners book names no title")
    return NoticeBook(
        title=title,
        jobs=tuple(
            _check_job_ref(d) for d in fields.get("jobs") or ()),
        channels=tuple(
            _check_channel_ref(s)
            for s in fields.get("channels") or ()),
        rules=tuple(
            _check_rule_ref(a) for a in fields.get("rules") or ()),
        views=tuple(
            _check_view_ref(v) for v in fields.get("views") or ()),
        panels=tuple(
            validate_panel(p) for p in fields.get("panels") or ()))


def _book_from(data: Any, *, require_example: bool) -> NoticeBook:
    if isinstance(data, NoticeBook):
        return validate_book(data, require_example=require_example)
    if isinstance(data, dict):
        return validate_book(data, require_example=require_example)
    raise ValueError(f"a manners book must be a mapping, got {data!r}")


def load_notifications_manners(
        data: Optional[Dict[str, Any]] = None) -> NoticeBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(NOTIFICATIONS_MANNERS_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_notifications_manners_file(path: Any) -> NoticeBook:
    """Load one manners file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: manners items and views held one by one.
# ---------------------------------------------------------------------


class NoticeRegistry:
    """An in-memory holding of manners items and views.

    The registry is the pure layer's model of a
    session's manners book: jobs, channels and
    rules are held under their ids, one item per
    id within its kind and one rule per name, in
    held order, and views are held in recorded
    order, one view per sequence and per id.
    Holding is data only - nothing held here rings
    a bell, posts a notification, or announces.
    """

    def __init__(self, book: Any = None) -> None:
        self._jobs: List[JobNotice] = []
        self._channels: List[ChannelNotice] = []
        self._rules: List[MannersRule] = []
        self._views: List[NoticeView] = []
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

    def _check_job_free(self, item: JobNotice) -> None:
        for held in self._jobs:
            if held.job_id == item.job_id:
                raise ValueError(
                    f"a job already stands under id "
                    f"{item.job_id!r}")
            if held.seq == item.seq:
                raise ValueError(
                    f"a job already stands at sequence "
                    f"{item.seq}")

    def register_job(self, item: Any) -> JobNotice:
        """Hold one job, judged whole before it is held."""
        validated = _check_job_ref(item)
        self._check_job_free(validated)
        self._jobs.append(validated)
        return validated

    def _check_channel_free(self, item: ChannelNotice) -> None:
        for held in self._channels:
            if held.channel_id == item.channel_id:
                raise ValueError(
                    f"a channel already stands under id "
                    f"{item.channel_id!r}")
            if held.seq == item.seq:
                raise ValueError(
                    f"a channel already stands at sequence "
                    f"{item.seq}")

    def register_channel(self, item: Any) -> ChannelNotice:
        """Hold one channel, judged whole before it is held."""
        validated = _check_channel_ref(item)
        self._check_channel_free(validated)
        self._channels.append(validated)
        return validated

    def _check_rule_free(self, item: MannersRule) -> None:
        for held in self._rules:
            if held.rule_id == item.rule_id:
                raise ValueError(
                    f"a rule already stands under id "
                    f"{item.rule_id!r}")
            if held.name == item.name:
                raise ValueError(
                    f"a rule already stands under name "
                    f"{item.name!r} - the book holds one "
                    f"rule per name")
            if held.seq == item.seq:
                raise ValueError(
                    f"a rule already stands at sequence "
                    f"{item.seq}")

    def register_rule(self, item: Any) -> MannersRule:
        """Hold one rule, judged whole before it is held."""
        validated = _check_rule_ref(item)
        self._check_rule_free(validated)
        self._rules.append(validated)
        return validated

    def _check_view_free(self, view: NoticeView) -> None:
        for held in self._views:
            if view.view_id is not None and (
                    held.view_id == view.view_id):
                raise ValueError(
                    f"a view already stands under id "
                    f"{view.view_id!r}")
            if held.seq == view.seq:
                raise ValueError(
                    f"a view already stands at sequence "
                    f"{view.seq} - the book holds one "
                    f"view per place")

    def register_view(self, view: Any) -> NoticeView:
        """Hold one view record, judged whole first."""
        validated = _check_view_ref(view)
        self._check_view_free(validated)
        if validated.view_id is None:
            validated = NoticeView(
                view_id=self._fresh_view_id(
                    {v.view_id for v in self._views}),
                seq=validated.seq,
                kind_filter=validated.kind_filter,
                detail=validated.detail,
                recorded_on=validated.recorded_on,
                actor=validated.actor, source=validated.source,
                origin_session=validated.origin_session)
        self._views.append(validated)
        self._views.sort(key=lambda v: v.seq)
        return validated

    def register_book(self, book: Any) -> NoticeBook:
        """Hold a whole book, judged whole first."""
        validated = build_book(book)
        for item in validated.jobs:
            self._check_job_free(item)
        for item in validated.channels:
            self._check_channel_free(item)
        for item in validated.rules:
            self._check_rule_free(item)
        if self._title is None:
            self._title = validated.title
        elif validated.title != self._title:
            raise ValueError(
                "a second book under a different title refuses - "
                "one book stands in one registry")
        for item in validated.jobs:
            self._jobs.append(item)
        for item in validated.channels:
            self._channels.append(item)
        for item in validated.rules:
            self._rules.append(item)
        for view in validated.views:
            self.register_view(view)
        return self.book()

    def get_job(self, job_id: Any) -> JobNotice:
        wanted = _check_word(job_id, "a job id")
        for item in self._jobs:
            if item.job_id == wanted:
                return item
        raise KeyError(f"no job named {wanted!r} stands held")

    def get_channel(self, channel_id: Any) -> ChannelNotice:
        wanted = _check_word(channel_id, "a channel id")
        for item in self._channels:
            if item.channel_id == wanted:
                return item
        raise KeyError(f"no channel named {wanted!r} stands held")

    def get_rule(self, rule_id: Any) -> MannersRule:
        wanted = _check_word(rule_id, "a rule id")
        for item in self._rules:
            if item.rule_id == wanted:
                return item
        raise KeyError(f"no rule named {wanted!r} stands held")

    def get_view(self, view_id: Any) -> NoticeView:
        wanted = _check_word(view_id, "a view id")
        for view in self._views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no view named {wanted!r} stands held")

    def latest_view(self) -> NoticeView:
        if not self._views:
            raise KeyError("no view stands held")
        return self._views[-1]

    def list_jobs(self) -> Tuple[JobNotice, ...]:
        return tuple(self._jobs)

    def list_channels(self) -> Tuple[ChannelNotice, ...]:
        return tuple(self._channels)

    def list_rules(self) -> Tuple[MannersRule, ...]:
        return tuple(self._rules)

    def list_views(self) -> Tuple[NoticeView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._jobs) + tuple(self._channels) \
            + tuple(self._rules)

    def book(self) -> NoticeBook:
        return NoticeBook(
            title=self._title or "Notifications with Manners",
            jobs=tuple(self._jobs),
            channels=tuple(self._channels),
            rules=tuple(self._rules),
            views=tuple(self._views))

    def panel(self, view: Any = None) -> NoticePanel:
        return derive_panel(self.book(), view)

    def verdict(self, view: Any = None) -> NoticeVerdict:
        return derive_verdict(self.book(), view)


# ---------------------------------------------------------------------
# Session news, plain words, and the screens.
# ---------------------------------------------------------------------


def job_record(job: Any) -> Dict[str, Any]:
    """The session-news record of one job."""
    current = _check_job_ref(job)
    record_out = current.to_record()
    record_out["news"] = True
    record_out["headline"] = (
        f"Notifications manners job {current.job_id}: "
        f"{segment_of(current)}.")
    return record_out


def channel_record(channel: Any) -> Dict[str, Any]:
    """The session-news record of one channel."""
    current = _check_channel_ref(channel)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Notifications manners channel {current.channel_id}: "
        f"{segment_of(current)}.")
    return record


def rule_record(rule: Any) -> Dict[str, Any]:
    """The session-news record of one manners rule."""
    current = _check_rule_ref(rule)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Notifications manners rule {current.rule_id}: "
        f"{segment_of(current)}.")
    return record


def item_record(item: Any) -> Dict[str, Any]:
    """The session-news record of one item of any kind."""
    if isinstance(item, JobNotice):
        return job_record(item)
    if isinstance(item, ChannelNotice):
        return channel_record(item)
    if isinstance(item, MannersRule):
        return rule_record(item)
    raise ValueError(f"a manners item is needed, got {item!r}")


def view_record(view: Any) -> Dict[str, Any]:
    """The session-news record of one view record."""
    current = _check_view_ref(view)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Notifications manners view {current.view_id or current.seq}: "
        f"kind {current.kind_filter!r} - {current.detail}")
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of one derived panel."""
    current = validate_panel(panel, source)
    record = current.to_record()
    record["news"] = True
    kinds = ", ".join(
        f"{c.kind} {c.items}" for c in current.kind_counts)
    record["headline"] = (
        f"Notifications manners panel as of {current.as_of}: "
        f"{current.total_shown} of {current.total_items} "
        f"items show for kind {current.kind_filter!r} "
        f"({kinds}).")
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    """The session-news record of one derived verdict."""
    current = validate_verdict(verdict, source, view)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Notifications manners verdict: {current.verdict} - "
        f"{current.passing_shown} of {current.total_shown} "
        f"shown items stand whole across "
        f"{current.distinct_kinds} kinds, from "
        f"{current.earliest_on} to {current.latest_on}.")
    return record


def book_record(book: Any) -> Dict[str, Any]:
    """The session-news record of one manners book."""
    current = book if isinstance(book, NoticeBook) else build_book(book)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Notifications with manners {current.title}: "
        f"{record['item_count']} items named, "
        f"{record['view_count']} views held - "
        f"{len(passing_items(current))} of "
        f"{record['item_count']} items stand whole.")
    return record


def plain_words(job: Any) -> str:
    """One job, in one plain sentence."""
    current = _check_job_ref(job)
    return job_plain_words(current)


def job_plain_words(job: Any) -> str:
    """One job, in one plain sentence."""
    current = _check_job_ref(job)
    word, _reason = announcement_decision(current)
    if word == "silence":
        return (
            f"{segment_of(current)} - one job on "
            f"{current.job_id}, standing silent: silence "
            f"is the default posture, and nothing "
            f"announces for it.")
    return (
        f"{segment_of(current)} - one job on "
        f"{current.job_id}, announcing once under key "
        f"{announcement_key(current)!r}.")


def channel_plain_words(channel: Any) -> str:
    """One channel, in one plain sentence."""
    current = _check_channel_ref(channel)
    return (
        f"{segment_of(current)} - one channel named "
        f"{current.name}, judged from the backend it "
        f"names and never from a stored claim.")


def rule_plain_words(rule: Any) -> str:
    """One manners rule, in one plain sentence."""
    current = _check_rule_ref(rule)
    return (
        f"{segment_of(current)} - the rule "
        f"{current.name!r} stands as data, and the "
        f"layer's derivations are this rule, executed.")


def announcement_plain_words(announcement: Any) -> str:
    """One announcement, in one plain sentence."""
    if not isinstance(announcement, Announcement):
        raise ValueError(
            f"an announcement is needed, got {announcement!r}")
    current = announcement
    if current.action is not None:
        return (
            f"Announcement {current.key}: {current.message} "
            f"The one action that matters: {current.action}. "
            f"It announces once, through "
            f"{current.channel or 'no channel'}.")
    return (
        f"Announcement {current.key}: {current.message} "
        f"It announces once, through "
        f"{current.channel or 'no channel'}.")


def panel_plain_words(source: Any, view: Any = None) -> str:
    """The panel in plain words, in full."""
    if isinstance(source, NoticePanel):
        panel = validate_panel(source)
        title = None
    elif isinstance(source, (NoticeBook, NoticeRegistry)):
        book = source if isinstance(
            source, NoticeBook) else source.book()
        panel = derive_panel(
            book, view if view is not None
            else _default_view(book))
        title = book.title
    else:
        raise ValueError(f"a manners source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    lines.append("Shown, in held order:")
    for row in panel.rows:
        lines.append(
            f"{row.item_id}: {row.segment} "
            f"({row.recorded_on})")
    lines.extend(panel.account)
    return "\n".join(lines)


def verdict_plain_words(source: Any, view: Any = None) -> str:
    """The book verdict in plain words, in full."""
    if isinstance(source, NoticeVerdict):
        verdict = validate_verdict(source)
    elif isinstance(source, (NoticeBook, NoticeRegistry)):
        book = source if isinstance(
            source, NoticeBook) else source.book()
        verdict = derive_verdict(
            book, view if view is not None
            else _default_view(book))
    else:
        raise ValueError(f"a manners source is needed, got {source!r}")
    return (
        f"Notifications manners verdict: {verdict.verdict} - "
        f"{verdict.passing_shown} of {verdict.total_shown} "
        f"shown items stand whole, across "
        f"{verdict.distinct_kinds} kinds, from "
        f"{verdict.earliest_on} to {verdict.latest_on} - "
        f"every judgement is derived from the items' "
        f"own fields.")


def view_plain_words(view: Any) -> str:
    """One view record, in one plain sentence."""
    current = _check_view_ref(view)
    return (
        f"View {current.view_id or current.seq} looks at "
        f"kind {current.kind_filter!r}, recorded on "
        f"{current.recorded_on} by {current.actor}: "
        f"{current.detail} A view only ever looks - it "
        f"announces nothing and delivers nothing.")


def _source_book(source: Any) -> NoticeBook:
    if source is None:
        return load_notifications_manners()
    if isinstance(source, NoticeRegistry):
        return source.book()
    if isinstance(source, NoticeBook):
        return source
    raise ValueError(f"a manners book is needed, got {source!r}")


def format_job(job: Any) -> str:
    """One job as a screen block."""
    current = _check_job_ref(job)
    word, reason = announcement_decision(current)
    channel, aword, areason = channel_of(current)
    lines = [
        f"{current.job_id}: {segment_of(current)}",
        f"Outcome: {current.outcome}",
        f"Duration: {current.duration_seconds} seconds "
        f"(long-job threshold {LONG_JOB_THRESHOLD_SECONDS} seconds)",
        f"Decision: {word} - {reason}",
        f"Channel: {channel if channel is not None else 'none chosen'}",
        f"Availability: {aword} - {areason}",
        f"Bell backend: {current.bell_backend if current.bell_backend is not None else 'none named'}",
        f"OS backend: {current.os_backend if current.os_backend is not None else 'none named'}",
        f"Failure action: {current.failure_action if current.failure_action is not None else 'none - the job did not fail'}",
        f"Announcement key: {announcement_key(current)} (announced at most once)",
        f"Words: {current.detail}",
        f"Recorded: on {current.recorded_on} by {current.actor} "
        f"from {current.source} in {current.origin_session}.",
    ]
    return "\n".join(lines)


def format_channel(channel: Any) -> str:
    """One channel as a screen block."""
    current = _check_channel_ref(channel)
    word, reason = channel_availability(current)
    lines = [
        f"{current.channel_id}: {segment_of(current)}",
        f"Name: {current.name}",
        f"Backend: {current.backend if current.backend is not None else 'none named'}",
        f"Availability: {word} - {reason}",
        f"Words: {current.detail}",
        f"Recorded: on {current.recorded_on} by {current.actor} "
        f"from {current.source} in {current.origin_session}.",
    ]
    return "\n".join(lines)


def format_rule(rule: Any) -> str:
    """One manners rule as a screen block."""
    current = _check_rule_ref(rule)
    lines = [
        f"{current.rule_id}: {segment_of(current)}",
        f"Name: {current.name}",
        f"Statement: {current.statement}",
        f"Words: {current.detail}",
        f"Recorded: on {current.recorded_on} by {current.actor} "
        f"from {current.source} in {current.origin_session}.",
    ]
    return "\n".join(lines)


def format_view(view: Any) -> str:
    """One view record as a screen block."""
    current = _check_view_ref(view)
    lines = [
        f"{current.view_id or '-'}: kind "
        f"{current.kind_filter!r}",
        f"Words: {current.detail}",
        f"Recorded: on {current.recorded_on} by {current.actor} "
        f"from {current.source} in {current.origin_session}.",
    ]
    return "\n".join(lines)


def format_book(source: Any = None, kind: Any = None) -> str:
    """The book as derived segments, in held order.

    By default the lines are every item's derived
    segment. With ``kind`` only that kind's items
    stand in the list.
    """
    book = _source_book(source)
    wanted = normalize_kind(kind) if kind is not None else None
    lines = []
    for item in book.items():
        if wanted is not None and item.kind != wanted:
            continue
        lines.append(f"{item.item_id}: {segment_of(item)}")
    if not lines:
        lines.append("No items stand in the book on that reading.")
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    """The panel as a screen block: every row and the account."""
    if isinstance(source, NoticePanel):
        panel = validate_panel(source)
        lines: list = []
    else:
        book = _source_book(source)
        panel = derive_panel(
            book, view if view is not None
            else _default_view(book))
        lines = [f"Panel in {book.title}:"]
    lines.append("Shown, in held order:")
    for row in panel.rows:
        lines.append(
            f"{row.item_id}: {row.segment} ({row.recorded_on})")
    lines.extend(panel.account)
    return "\n".join(lines)


def format_verdict(source: Any = None, view: Any = None) -> str:
    """The verdict as a screen block."""
    if isinstance(source, NoticeVerdict):
        verdict = validate_verdict(source)
        title = "the book"
    else:
        book = _source_book(source)
        verdict = derive_verdict(
            book, view if view is not None
            else _default_view(book))
        title = book.title
    return (
        f"Verdict in Notifications with Manners over {title}: "
        f"{verdict.verdict} - {verdict.passing_shown} of "
        f"{verdict.total_shown} shown items stand whole, "
        f"across {verdict.distinct_kinds} kinds, from "
        f"{verdict.earliest_on} to {verdict.latest_on}.")


def format_notifications_manners_screen(source: Any = None) -> str:
    """The whole notifications-manners screen for one book."""
    book = _source_book(source)
    view = _default_view(book)
    panel = derive_panel(book, view)
    verdict = derive_verdict(book, view)
    due = due_announcements(book)
    lines = [
        f"Notifications with Manners (M-181) - {book.title}",
        format_book(book),
        f"Panel: {panel.total_shown} of "
        f"{panel.total_items} items show "
        f"for kind {panel.kind_filter!r}.",
        f"Verdict: {verdict.verdict}.",
        f"Due announcements: {len(due)} stand due, each "
        f"at most once.",
        "This layer holds manners as data only - it "
        "rings no bell and posts no notification in "
        "tests: silence is the default posture, a "
        "long job announces once, and a failure "
        "announces once with the one action that "
        "matters.",
    ]
    return "\n".join(lines)


def parse_notifications_manners_args(args: Any) -> Tuple[str, Any]:
    """Parse the /manners grammar into (action, target).

    ``""``/``show``/``list`` show the book;
    ``job <job-id>`` shows one job whole;
    ``channel <channel-id>`` shows one channel;
    ``rule <rule-id>`` shows one manners rule;
    ``view <view-id>`` shows one held view record;
    ``kind <kind>`` shows one kind's items;
    ``panel`` and ``verdict`` show the derived
    panel and verdict under the book's own view.
    Anything else raises ValueError carrying the
    usage line.
    """
    if args is None:
        return ("show", None)
    if not isinstance(args, str):
        raise ValueError(USAGE)
    parts = args.split()
    if not parts or parts == ["show"] or parts == ["list"]:
        return ("show", None)
    if parts[0] == "job" and len(parts) == 2:
        return ("job", _check_word(parts[1], "a job id"))
    if parts[0] == "channel" and len(parts) == 2:
        return ("channel", _check_word(parts[1], "a channel id"))
    if parts[0] == "rule" and len(parts) == 2:
        return ("rule", _check_word(parts[1], "a rule id"))
    if parts[0] == "view" and len(parts) == 2:
        return ("view", _check_word(parts[1], "a view id"))
    if parts[0] == "kind" and len(parts) == 2:
        try:
            return ("kind", normalize_kind(parts[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if parts == ["panel"]:
        return ("panel", None)
    if parts == ["verdict"]:
        return ("verdict", None)
    raise ValueError(USAGE)
