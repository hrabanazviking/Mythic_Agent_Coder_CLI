"""The keeper pattern - watching for stalled work (M-104).

Part V - Autonomy & Safety. The roadmap's words:
``a watcher that notices stalled work (a dead
background job, a crew member gone quiet) and
restarts or reports per the user's standing keeper
law - timers that *work*, not timers that watch.``

What already shipped, and what this slice adds:

* The keeper law itself is Volmarr's standing
  design, worked by hand in this campaign: a
  ten-minute minder checks whether guarded work
  has stopped, and if it has, it continues the
  work itself - the tick exists to catch stalls
  and restart work, never merely to report. The
  M-103 background tasks layer holds long commands
  as managed jobs with live tails and completion
  news, but nothing in the tree judges whether a
  piece of work has gone quiet for too long, or
  says what is owed when it has.
* This slice is that missing judgement, as a pure
  layer: a watch target (what is watched - a
  background job, a crew member, any tracked task -
  how long it may stay quiet, when it was last
  seen active, and how many restarts it has left)
  validated as data, a mechanical verdict on one
  target at one moment (active, quiet, or stalled,
  from the age of its last activity alone), the
  action the keeper law owes for a stalled target
  (restart it while restarts remain; report it
  when they run out), an intervention record
  shaped as session news, and a small in-memory
  registry model with deterministic ids. This
  module starts no timer, runs no process, writes
  no file and changes no setting; the agent layer
  owns holding the registry for a session, feeding
  it heartbeats from real work, carrying a restart
  out in the world, and publishing an intervention
  record into the session.

Honesty rules, enforced here and pinned by tests:

* **A verdict is mechanical.** A target's status
  comes only from the age of its last activity
  against its own stall bound: younger than half
  the bound is active, older is quiet, at or past
  the bound is stalled. No other signal - no
  vibes about the work - moves the verdict.
* **Time never runs backwards.** Recording
  activity, or a restart, at a moment earlier
  than the target's last activity raises, and
  judging a target at a moment before its last
  activity raises: a clock that runs backwards
  is malformed data, never a younger target.
* **Restart is bounded, report is the backstop.**
  A stalled target is restarted only while its
  restarts remain; when they run out the owed
  action is report - the stall is surfaced to a
  person, never silently watched forever, and a
  target is never restarted past its bound.
* **An intervention is news only when one is
  owed.** A target whose action is ``none``
  yields no intervention record at all, exactly
  as a job that has not finished yields no
  completion record. An owed restart or report
  yields one record with a one-line plain
  headline.
* **Status is never carried by colour or symbol
  alone.** Every formatter states the stall state
  in words, and a stalled target's line states
  its age and the action owed (restart or
  report).
* **Malformed refuses.** An unknown watch kind,
  an empty label, a boolean or out-of-range
  stall bound, a negative activity time, a
  duplicate watch id and unknown keys in a
  target mapping all raise instead of being
  skipped or guessed at.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Dict, Optional, Tuple

__all__ = [
    "ACTIONS",
    "KEEPER_SLICE",
    "PLAIN_EXPLANATION",
    "USAGE",
    "WATCH_KINDS",
    "WATCH_STATUSES",
    "KeeperRegistry",
    "WatchTarget",
    "WatchVerdict",
    "build_watch_target",
    "format_intervention",
    "format_keeper",
    "format_verdict",
    "format_watch_target",
    "format_watch_targets",
    "intervention_record",
    "judge_watch",
    "normalize_action",
    "normalize_target_id",
    "normalize_watch_kind",
    "normalize_watch_status",
    "parse_keeper_args",
    "record_activity",
    "record_restart",
    "validate_watch_target",
]

KEEPER_SLICE = "M-104"

#: What a watch watches, in house order. A kind
#: names the sort of work whose quiet matters: a
#: background job from M-103, a crew member's
#: task, or any tracked task.
WATCH_KINDS = ("background_job", "crew_member", "task")

#: The status words a verdict carries, in the
#: order work falls into them as it goes quiet.
WATCH_STATUSES = ("active", "quiet", "stalled")

#: The actions a verdict can owe, in keeper-law
#: order: nothing, a restart, or a report.
ACTIONS = ("none", "restart", "report")

#: The stall bound a target is watched with when
#: it names none: ten minutes - the keeper
#: cadence of Volmarr's standing law.
DEFAULT_STALL_AFTER_SECONDS = 600

#: The restarts a target is given when it names
#: none.
DEFAULT_MAX_RESTARTS = 3

PLAIN_EXPLANATION = (
    "The keeper watches work the way Volmarr's "
    "standing keeper law works: it notices work "
    "that has gone quiet - a background job that "
    "stopped, a crew member gone silent, a task "
    "with no sign of life - judges it stalled "
    "when it has been quiet past its bound, and "
    "acts instead of just watching. While "
    "restarts remain, the owed action is to "
    "restart the work; when the restarts run "
    "out, the owed action is to report the stall "
    "to a person, in plain words, so it is never "
    "silently watched forever. A watch is a "
    "timer that works, not a timer that watches. "
    "This layer holds the watches and the "
    "verdicts as data only; it starts no timer "
    "and restarts nothing itself."
)

USAGE = (
    "Usage: /keeper, /keeper show, "
    "/keeper show <target>, /keeper check, "
    "/keeper heartbeat <target>"
)

_TARGET_KEYS = frozenset({
    "target_id", "id", "kind", "type", "label", "name",
    "stall_after_seconds", "stall_after",
    "last_activity_at", "last_seen_at",
    "restarts", "max_restarts",
})

_TARGET_ID_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789-_.")


def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def normalize_target_id(value: Any) -> str:
    """The canonical watch target id a word names.

    A target id is one word of letters, digits,
    dashes, underscores and dots, read with its
    case kept (ids are pinned by callers and
    tests, so no reading may rename one). Anything
    else raises.
    """
    if isinstance(value, str):
        wanted = value.strip()
        if wanted and all(ch in _TARGET_ID_CHARS for ch in wanted):
            return wanted
    raise ValueError(
        f"a watch target id must be a non-empty word of letters, "
        f"digits, dashes, underscores and dots, got {value!r}")


def normalize_watch_kind(value: Any) -> str:
    """The canonical watch kind a word names.

    Kind words read case-insensitively, with
    dashes read as underscores - the reading the
    background tasks layer gives its state words.
    An unknown kind raises.
    """
    if isinstance(value, str):
        wanted = value.strip().lower().replace("-", "_")
        if wanted in WATCH_KINDS:
            return wanted
    raise ValueError(
        "a watch kind must be one of %s, got %r"
        % ("/".join(WATCH_KINDS), value))


def normalize_watch_status(value: Any) -> str:
    """The canonical watch status a word names."""
    if isinstance(value, str):
        wanted = value.strip().lower().replace("-", "_")
        if wanted in WATCH_STATUSES:
            return wanted
    raise ValueError(
        "a watch status must be one of %s, got %r"
        % ("/".join(WATCH_STATUSES), value))


def normalize_action(value: Any) -> str:
    """The canonical keeper action a word names."""
    if isinstance(value, str):
        wanted = value.strip().lower().replace("-", "_")
        if wanted in ACTIONS:
            return wanted
    raise ValueError(
        "a keeper action must be one of %s, got %r"
        % ("/".join(ACTIONS), value))


def _check_stall_after(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(
            f"a stall bound must be a whole number of seconds, "
            f"got {value!r}")
    if value < 60 or value > 86400:
        raise ValueError(
            f"a stall bound must be between 60 and 86400 seconds, "
            f"got {value!r}")
    return value


def _check_epoch(value: Any, what: str) -> float:
    if isinstance(value, bool) \
            or not isinstance(value, (int, float)):
        raise ValueError(
            f"{what} must be a number of seconds, got {value!r}")
    moment = float(value)
    if moment != moment or moment in (float("inf"), float("-inf")):
        raise ValueError(f"{what} must be a finite time, got {value!r}")
    if moment < 0:
        raise ValueError(f"{what} must be 0 or later, got {value!r}")
    return moment


def _check_count(value: Any, what: str,
                 minimum: int, maximum: Optional[int]) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(
            f"{what} must be a whole number, got {value!r}")
    if value < minimum or (maximum is not None and value > maximum):
        if maximum is None:
            raise ValueError(
                f"{what} must be {minimum} or more, got {value!r}")
        raise ValueError(
            f"{what} must be between {minimum} and {maximum}, "
            f"got {value!r}")
    return value


def _format_age(age_seconds: float) -> str:
    """One age of quiet, in plain seconds."""
    age = float(age_seconds)
    if age == int(age):
        return f"{int(age)} seconds"
    return f"{age:.1f} seconds"


# ---------------------------------------------------------------------
# The watch target: one piece of work being watched, as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class WatchTarget:
    """One piece of work the keeper watches, as data.

    ``kind`` names what is watched (a background
    job, a crew member, any tracked task);
    ``label`` is the short human name reports use.
    ``stall_after_seconds`` is how long the work
    may stay quiet before it is judged stalled.
    ``last_activity_at`` is the last moment the
    work showed life, as an epoch float.
    ``restarts`` counts the restarts already
    spent; ``max_restarts`` bounds them - past
    the bound, a stall is reported, not restarted.

    Constructing one validates it, so a
    WatchTarget that exists is a watch the keeper
    could judge.
    """

    target_id: Optional[str] = None
    kind: str = "task"
    label: str = ""
    stall_after_seconds: int = DEFAULT_STALL_AFTER_SECONDS
    last_activity_at: float = 0.0
    restarts: int = 0
    max_restarts: int = DEFAULT_MAX_RESTARTS

    def __post_init__(self) -> None:
        if self.target_id is not None:
            object.__setattr__(
                self, "target_id", normalize_target_id(self.target_id))
        object.__setattr__(
            self, "kind", normalize_watch_kind(self.kind))
        object.__setattr__(
            self, "label", _clean_text(self.label, "a watch label"))
        object.__setattr__(
            self, "stall_after_seconds",
            _check_stall_after(self.stall_after_seconds))
        object.__setattr__(
            self, "last_activity_at",
            _check_epoch(self.last_activity_at, "a last activity time"))
        object.__setattr__(
            self, "restarts",
            _check_count(self.restarts, "a restart count", 0, None))
        object.__setattr__(
            self, "max_restarts",
            _check_count(self.max_restarts, "a max restarts bound",
                         0, 100))

    @property
    def restarts_remaining(self) -> int:
        return max(0, self.max_restarts - self.restarts)

    @property
    def restarts_exhausted(self) -> bool:
        return self.restarts >= self.max_restarts

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "keeper_watch",
            "slice": KEEPER_SLICE,
            "target_id": self.target_id,
            "kind": self.kind,
            "label": self.label,
            "stall_after_seconds": self.stall_after_seconds,
            "last_activity_at": self.last_activity_at,
            "restarts": self.restarts,
            "max_restarts": self.max_restarts,
        }


def _pick(mapping: Dict[str, Any], first: str, second: str,
          what: str) -> Any:
    """One field from its two spellings, or a refusal.

    Naming both spellings with different values
    refuses - a target is never repaired by
    guessing which spelling the caller meant.
    """
    if first in mapping and second in mapping:
        if mapping[first] != mapping[second]:
            raise ValueError(f"a watch target names two different {what}")
        return mapping[first]
    if first in mapping:
        return mapping[first]
    return mapping.get(second)


def validate_watch_target(target: Any) -> WatchTarget:
    """Validate one watch target into a WatchTarget.

    Accepts a WatchTarget or a mapping naming a
    ``kind`` (or ``type``), a ``label`` (or
    ``name``), an optional ``target_id`` (or
    ``id``), a ``stall_after_seconds`` (or
    ``stall_after``), a ``last_activity_at`` (or
    ``last_seen_at``), ``restarts`` and
    ``max_restarts``. Naming both spellings of
    one field with different values refuses, and
    unknown keys refuse.
    """
    if isinstance(target, WatchTarget):
        return target
    if not isinstance(target, dict):
        raise ValueError(
            f"a watch target must be a mapping, got {target!r}")
    unknown = set(target) - _TARGET_KEYS
    if unknown:
        raise ValueError(
            "unknown watch target keys: %s"
            % ", ".join(sorted(unknown)))
    kind = _pick(target, "kind", "type", "kinds")
    if kind is None:
        raise ValueError("a watch target is missing its kind")
    label = _pick(target, "label", "name", "labels")
    if label is None:
        raise ValueError("a watch target is missing its label")
    kwargs: Dict[str, Any] = {"kind": kind, "label": label}
    target_id = _pick(target, "target_id", "id", "target ids")
    if target_id is not None:
        kwargs["target_id"] = target_id
    stall = _pick(target, "stall_after_seconds", "stall_after",
                  "stall bounds")
    if stall is not None:
        kwargs["stall_after_seconds"] = stall
    seen = _pick(target, "last_activity_at", "last_seen_at",
                 "last activity times")
    if seen is not None:
        kwargs["last_activity_at"] = seen
    if "restarts" in target:
        kwargs["restarts"] = target["restarts"]
    if "max_restarts" in target:
        kwargs["max_restarts"] = target["max_restarts"]
    return WatchTarget(**kwargs)


def build_watch_target(target: Any = None, **kwargs: Any) -> WatchTarget:
    """Build one validated watch target.

    From a WatchTarget, from a mapping (the
    spellings :func:`validate_watch_target`
    reads), or from field words given as keyword
    arguments.
    """
    if isinstance(target, WatchTarget) and not kwargs:
        return target
    if isinstance(target, dict) or target is None:
        merged: Dict[str, Any] = {}
        if isinstance(target, dict):
            merged.update(target)
        merged.update(kwargs)
        return validate_watch_target(merged)
    if kwargs:
        merged = dict(kwargs)
        merged.setdefault("kind", target)
        return validate_watch_target(merged)
    raise ValueError(
        f"a watch target must be a mapping, got {target!r}")


def _require_target(target: Any) -> WatchTarget:
    if not isinstance(target, WatchTarget):
        raise ValueError(f"a watch target is needed, got {target!r}")
    return target


def record_activity(target: Any, at: Any) -> WatchTarget:
    """Record one sign of life: a copy last active at ``at``.

    Time never runs backwards - an ``at`` earlier
    than the target's stored last activity raises
    instead of making the target look younger
    than it honestly is.
    """
    current = _require_target(target)
    moment = _check_epoch(at, "an activity time")
    if moment < current.last_activity_at:
        raise ValueError(
            f"activity at {moment} is earlier than the target's "
            f"last activity at {current.last_activity_at}; "
            "time never runs backwards")
    return replace(current, last_activity_at=moment)


def record_restart(target: Any, at: Any) -> WatchTarget:
    """Record one restart spent: a copy, its clock reset to ``at``.

    A restart is spent only while restarts
    remain - a target whose restarts already
    equal its bound refuses, because an exhausted
    target is reported, not restarted past its
    bound. The restart moment obeys the same
    no-backwards-time rule as any activity.
    """
    current = _require_target(target)
    if current.restarts >= current.max_restarts:
        raise ValueError(
            f"target {current.label!r} has spent all "
            f"{current.max_restarts} restart(s); it is reported, "
            "not restarted past its bound")
    moment = _check_epoch(at, "a restart time")
    if moment < current.last_activity_at:
        raise ValueError(
            f"a restart at {moment} is earlier than the target's "
            f"last activity at {current.last_activity_at}; "
            "time never runs backwards")
    return replace(current, restarts=current.restarts + 1,
                   last_activity_at=moment)


# ---------------------------------------------------------------------
# The verdict: one target judged at one moment, mechanically.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class WatchVerdict:
    """One watch target judged at one moment.

    ``status`` is the mechanical reading of the
    target's quiet: active, quiet, or stalled.
    ``age_seconds`` is how long the target has
    been quiet - the moment judged minus its last
    activity. ``action`` is what the keeper law
    owes for that status: none, restart, or
    report.
    """

    target_id: Optional[str] = None
    kind: str = "task"
    label: str = ""
    status: str = "active"
    age_seconds: float = 0.0
    action: str = "none"

    def __post_init__(self) -> None:
        if self.target_id is not None:
            object.__setattr__(
                self, "target_id", normalize_target_id(self.target_id))
        object.__setattr__(
            self, "kind", normalize_watch_kind(self.kind))
        object.__setattr__(
            self, "label", _clean_text(self.label, "a watch label"))
        object.__setattr__(
            self, "status", normalize_watch_status(self.status))
        object.__setattr__(
            self, "action", normalize_action(self.action))
        object.__setattr__(
            self, "age_seconds",
            _check_epoch(self.age_seconds, "an age of quiet"))
        if self.status in ("active", "quiet") and self.action != "none":
            raise ValueError(
                f"a {self.status} verdict owes no action, "
                f"got {self.action!r}")
        if self.status == "stalled" and self.action == "none":
            raise ValueError(
                "a stalled verdict owes a restart or a report, "
                "never nothing")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "keeper_verdict",
            "slice": KEEPER_SLICE,
            "target_id": self.target_id,
            "kind": self.kind,
            "label": self.label,
            "status": self.status,
            "age_seconds": self.age_seconds,
            "action": self.action,
        }


def judge_watch(target: Any, now: Any) -> WatchVerdict:
    """Judge one target at ``now``, mechanically.

    The age of the target's quiet is ``now``
    minus its last activity; a negative age - a
    judgement moment before the last activity -
    is malformed and raises. Younger than half
    the stall bound is active; at or past half,
    but younger than the bound, is quiet; at or
    past the bound is stalled. A stalled target
    is owed a restart while its restarts remain,
    and a report when they are exhausted.
    """
    current = _require_target(target)
    moment = _check_epoch(now, "a judgement time")
    age = moment - current.last_activity_at
    if age < 0:
        raise ValueError(
            f"judging at {moment} is earlier than the target's "
            f"last activity at {current.last_activity_at}; "
            "time never runs backwards")
    bound = current.stall_after_seconds
    if age < bound / 2:
        status, action = "active", "none"
    elif age < bound:
        status, action = "quiet", "none"
    else:
        status = "stalled"
        action = "report" if current.restarts_exhausted else "restart"
    return WatchVerdict(
        target_id=current.target_id, kind=current.kind,
        label=current.label, status=status, age_seconds=age,
        action=action)


# ---------------------------------------------------------------------
# Intervention, shaped as session news.
# ---------------------------------------------------------------------


def _intervention_headline(verdict: WatchVerdict,
                           target: WatchTarget) -> str:
    name = verdict.target_id or verdict.label
    if verdict.action == "restart":
        return (
            f"Keeper: {verdict.label} ({name}) has been quiet for "
            f"{_format_age(verdict.age_seconds)} and is stalled - "
            f"restarting it (restart {target.restarts + 1} of "
            f"{target.max_restarts}).")
    return (
        f"Keeper: {verdict.label} ({name}) has been quiet for "
        f"{_format_age(verdict.age_seconds)} and is stalled, and "
        f"its {target.max_restarts} restart(s) are spent - "
        "reporting the stall instead of watching it forever.")


def intervention_record(verdict: Any,
                        target: Any) -> Optional[Dict[str, Any]]:
    """The session-news record of one owed intervention, or None.

    A verdict whose action is ``none`` returns
    None - the agent layer publishes this record
    as a session event when it is not None, so an
    intervention can never be lost as a mere log
    line, and never announced when none is owed.
    """
    current = _require_target(target)
    if not isinstance(verdict, WatchVerdict):
        raise ValueError(f"a watch verdict is needed, got {verdict!r}")
    if verdict.action == "none":
        return None
    return {
        "type": "keeper_intervention",
        "news": True,
        "target_id": verdict.target_id,
        "kind": verdict.kind,
        "label": verdict.label,
        "status": verdict.status,
        "action": verdict.action,
        "age_seconds": verdict.age_seconds,
        "restarts": current.restarts,
        "headline": _intervention_headline(verdict, current),
    }


def format_intervention(record: Any) -> str:
    """One intervention record as its plain headline."""
    if isinstance(record, dict) \
            and record.get("type") == "keeper_intervention":
        return str(record["headline"])
    raise ValueError(
        "format_intervention needs a keeper intervention record")


# ---------------------------------------------------------------------
# The registry model: watches held in registration order, ids
# deterministic.
# ---------------------------------------------------------------------


class KeeperRegistry:
    """An in-memory registry of watch targets.

    Targets are held in registration order and
    replaced, never mutated, as they change. Ids
    are deterministic: a caller-supplied id is
    used as given (a duplicate refuses), and an
    unsupplied id is the next ``watch-N`` in
    sequence, skipping any number a supplied id
    already took - no randomness a test cannot
    pin. Storage beyond memory (a session's
    journal, a file) is the agent layer's
    concern; this model is neutral.
    """

    def __init__(self) -> None:
        self._targets: Dict[str, WatchTarget] = {}
        self._next = 1

    def _fresh_id(self) -> str:
        while f"watch-{self._next}" in self._targets:
            self._next += 1
        target_id = f"watch-{self._next}"
        self._next += 1
        return target_id

    def register(self, target: Any) -> WatchTarget:
        """Register one target and hold it; duplicate ids refuse."""
        validated = build_watch_target(target)
        if validated.target_id is None:
            validated = replace(validated, target_id=self._fresh_id())
        elif validated.target_id in self._targets:
            raise ValueError(
                f"a watch target named {validated.target_id!r} "
                "already exists")
        self._targets[validated.target_id] = validated
        return validated

    def get(self, target_id: Any) -> WatchTarget:
        """The target one id names; an unknown id raises KeyError."""
        wanted = normalize_target_id(target_id)
        if wanted not in self._targets:
            raise KeyError(f"unknown watch target: {wanted!r}")
        return self._targets[wanted]

    def list_targets(self, kind: Any = None) -> Tuple[WatchTarget, ...]:
        """Every held target, in registration order, optionally by kind."""
        targets = tuple(self._targets.values())
        if kind is None:
            return targets
        wanted = normalize_watch_kind(kind)
        return tuple(t for t in targets if t.kind == wanted)

    def _store(self, target: WatchTarget) -> WatchTarget:
        self._targets[target.target_id] = target
        return target

    def heartbeat(self, target_id: Any, at: Any) -> WatchTarget:
        """Record one sign of life on a held target."""
        return self._store(record_activity(self.get(target_id), at))

    def restart(self, target_id: Any, at: Any) -> WatchTarget:
        """Record one restart spent on a held target."""
        return self._store(record_restart(self.get(target_id), at))

    def check(self, now: Any) -> Tuple[WatchVerdict, ...]:
        """Every held target judged at ``now``, in registration order."""
        return tuple(
            judge_watch(target, now) for target in self._targets.values())

    def interventions(self, now: Any) -> Tuple[Dict[str, Any], ...]:
        """The owed intervention records at ``now``, in order.

        Only targets whose verdict owes an action
        appear - a registry at peace yields an
        empty tuple, never a list of non-events.
        """
        records = []
        for target in self._targets.values():
            record = intervention_record(judge_watch(target, now), target)
            if record is not None:
                records.append(record)
        return tuple(records)


# ---------------------------------------------------------------------
# The /keeper surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------


def format_verdict(verdict: Any) -> str:
    """One verdict, in plain words."""
    if not isinstance(verdict, WatchVerdict):
        raise ValueError(f"a watch verdict is needed, got {verdict!r}")
    name = verdict.target_id or verdict.label
    base = (
        f"{name}: {verdict.label} [{verdict.status}] - quiet for "
        f"{_format_age(verdict.age_seconds)}")
    if verdict.status == "stalled":
        if verdict.action == "restart":
            return base + "; action owed: restart the stalled work."
        return base + "; action owed: report the stall."
    return base + "; no action owed."


def format_watch_target(target: Any, now: Any) -> str:
    """One target, in plain words, judged at ``now``."""
    return format_verdict(judge_watch(_require_target(target), now))


def format_watch_targets(targets: Any = None, now: Any = 0.0) -> str:
    """The targets, in plain words, in the order given.

    With no targets at all the text starts with
    the plain statement of that fact. Every line
    states its stall state in words; a stalled
    target's line states its age and its owed
    action.
    """
    if targets is None:
        selected: Tuple[WatchTarget, ...] = ()
    elif isinstance(targets, KeeperRegistry):
        selected = targets.list_targets()
    else:
        if isinstance(targets, (str, bytes)) \
                or not isinstance(targets, (list, tuple)):
            raise ValueError("watch targets must be a list of targets")
        selected = tuple(_require_target(t) for t in targets)
    if not selected:
        return (
            "Keeper watches: none. No work is being "
            "watched for stalls.")
    lines = [f"Keeper watches: {len(selected)} held."]
    for target in selected:
        lines.append(f"  {format_watch_target(target, now)}")
    return "\n".join(lines)


def format_keeper(registry: Any = None, now: Any = 0.0) -> str:
    """The whole slice, in plain words, for /keeper."""
    lines = ["Keeper (M-104) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_watch_targets(registry, now))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_keeper_args(args: Any) -> Tuple[str, Optional[str]]:
    """Parse the /keeper grammar both surfaces share.

    No words (or ``show``) shows the watches;
    ``show <target>`` and a bare target id show
    one watch; ``check`` asks for every target to
    be judged now; ``heartbeat <target>`` records
    a sign of life on one target. Anything else
    is a usage error naming the grammar. Returns
    ``(action, target-id-or-None)``.
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
            return ("show", normalize_target_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "heartbeat" and len(words) == 2:
        try:
            return ("heartbeat", normalize_target_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head in ("show", "check", "heartbeat"):
        # A grammar word in the wrong shape is a usage
        # error, never a target id that happens to spell one.
        raise ValueError(USAGE)
    if len(words) == 1:
        try:
            return ("show", normalize_target_id(words[0]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
