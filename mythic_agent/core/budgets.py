"""Budgets as guardrails - token, cost, time and command budgets as data (M-107).

Part V - Autonomy & Safety. The roadmap's words:
``per-task and per-session token, cost, time, and
command budgets; hitting a budget is a graceful
pause with a report, never a mid-edit death.``

What already shipped, and what this slice adds:

* The M-103 background tasks layer holds one long
  command as a managed job, the M-105 scheduled
  work layer holds a cron-style job as data, and
  the M-106 fleet layer holds many headless runs
  as data with verdicts judged mechanically.
  ``mythic_agent/core/costs.py`` already counts
  tokens and prices them honestly - a model not
  in its pricing table is billed as ``unknown``
  at zero cost, never at an invented price.
  Nothing in the tree says how much work is
  *allowed* before a guardrail is reached: a
  budget a task or a whole session may spend,
  judged the same mechanical way.
* This slice is that missing budget layer, as a
  pure layer in the exact sibling shape: a budget
  (its scope - per-task or per-session - and an
  optional limit on each of tokens, cost, time
  and commands) validated as data, a usage
  reading (what has actually been spent, in the
  ``costs.py`` vocabulary: token counts and a
  cost in US dollars) validated as data, a
  mechanical judge that reads a budget against a
  usage and returns a verdict - within, warning
  or exceeded - naming the dimensions concerned
  with their used and limit amounts, a pause
  report shaped as session news for a budget that
  has been reached, and a small in-memory
  registry model with deterministic ids. This
  module starts no process, runs no command,
  writes no file and changes no setting; the
  agent layer owns holding the registry for a
  session, feeding it real usage from the real
  roads, and carrying a graceful pause out in
  the world when a verdict says exceeded.

Honesty rules, enforced here and pinned by tests:

* **No limit named means unlimited.** A budget
  with no limit on a dimension is unlimited on
  that dimension: it can warn about nothing and
  exceed nothing, however large the usage. This
  layer invents no default limit of its own.
* **Limits and usage agree with themselves.**
  A limit is a whole number of tokens or
  commands, a cost in dollars, or a time in
  seconds (minutes read as seconds); a zero or
  negative limit, a negative usage, and a
  boolean where a number belongs all refuse
  plainly instead of being guessed at. A
  verdict whose status disagrees with its own
  used and limit amounts refuses on
  construction - the three readings can never
  be made to disagree.
* **The judge is mechanical.** A dimension is
  exceeded when its usage is at or past its
  limit, and approaching - warning - when its
  usage is at or past 80% of its limit. The
  verdict is exceeded when any dimension is
  exceeded, warning when none is exceeded and
  any is approaching, and within otherwise.
  No other signal moves the verdict.
* **Hitting a budget is a graceful pause.**
  An exceeded verdict yields one pause record
  shaped as session news, stating in plain
  words that the pause is graceful - a report
  at a resting point, never a mid-edit death.
  A budget that is only within or approaching
  yields no pause record at all, exactly as a
  job that has not finished yields no
  completion record.
* **Status is never carried by colour or symbol
  alone.** Every formatter states a budget's
  scope, limits and verdict in words, and a
  verdict's line always names the dimensions
  concerned with their used and limit amounts.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Any, Dict, Optional, Tuple

__all__ = [
    "BUDGETS_SLICE",
    "BUDGET_DIMENSIONS",
    "BUDGET_SCOPES",
    "BUDGET_VERDICT_STATUSES",
    "PLAIN_EXPLANATION",
    "USAGE",
    "WARNING_FRACTION",
    "Budget",
    "BudgetRegistry",
    "BudgetUsage",
    "BudgetVerdict",
    "Usage",
    "budget_paused_record",
    "budget_report_record",
    "build_budget",
    "build_usage",
    "format_budget",
    "format_budget_report",
    "format_report",
    "format_budgets",
    "format_budgets_screen",
    "format_verdict",
    "judge_budget",
    "normalize_budget_id",
    "normalize_budget_scope",
    "parse_budgets_args",
    "validate_budget",
    "validate_usage",
    "validate_verdict",
]

BUDGETS_SLICE = "M-107"

#: The budget scopes, in roadmap order: a budget
#: guards one task, or a whole session.
BUDGET_SCOPES = ("task", "session")

#: The dimensions a budget can limit, in the
#: order verdicts name them.
BUDGET_DIMENSIONS = ("tokens", "cost", "time", "commands")

#: The verdict status words.
BUDGET_VERDICT_STATUSES = ("within", "warning", "exceeded")

#: A limited dimension is approaching its limit
#: - the warning reading - at or past this
#: fraction of it.
WARNING_FRACTION = 0.8

PLAIN_EXPLANATION = (
    "Budgets are guardrails: a per-task or "
    "per-session budget may name a limit on "
    "tokens, on cost, on time and on commands, "
    "and a usage reading says what has actually "
    "been spent. A dimension with no limit named "
    "is unlimited on that dimension - no default "
    "limit is invented. The judge is mechanical: "
    "a verdict is exceeded when usage is at or "
    "past any limit, warning when usage reaches "
    "80% of any limit, and within otherwise. "
    "Hitting a budget is a graceful pause with "
    "a report, never a mid-edit death. This layer "
    "holds budgets, usage readings and verdicts "
    "as data only; it starts no process, runs no "
    "command and spends nothing itself."
)

USAGE = (
    "Usage: /budgets, /budgets show, "
    "/budgets show <budget>, /budgets check, "
    "/budgets check <budget>"
)

_BUDGET_KEYS = frozenset({
    "budget_id", "id", "label", "name", "scope", "kind", "type",
    "token_limit", "max_tokens", "tokens",
    "cost_limit", "max_cost", "cost", "cost_usd", "cost_limit_usd",
    "time_limit_seconds", "time_seconds", "time_limit", "time",
    "seconds", "time_limit_minutes", "time_minutes", "minutes",
    "command_limit", "max_commands", "commands",
})

_USAGE_KEYS = frozenset({
    "tokens_used", "tokens", "token_count",
    "cost_used", "cost", "cost_usd", "spend", "spent_usd",
    "time_used_seconds", "elapsed_seconds", "time_seconds",
    "time_used", "elapsed", "time_used_minutes",
    "elapsed_minutes", "time_minutes", "minutes_used",
    "commands_used", "commands", "command_count",
})

_SCOPE_WORDS = {
    "task": "task", "per_task": "task",
    "session": "session", "per_session": "session",
}

_BUDGET_ID_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789-_.")


def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def normalize_budget_id(value: Any) -> str:
    """The canonical budget id a word names.

    A budget id is one word of letters, digits,
    dashes, underscores and dots, read with its
    case kept. Anything else raises.
    """
    if isinstance(value, str):
        wanted = value.strip()
        if wanted and all(ch in _BUDGET_ID_CHARS for ch in wanted):
            return wanted
    raise ValueError(
        f"a budget id must be a non-empty word of letters, "
        f"digits, dashes, underscores and dots, got {value!r}")


def normalize_budget_scope(value: Any) -> str:
    """The canonical budget scope a word names.

    Reads ``task`` / ``per-task`` / ``per_task``
    as the per-task scope and ``session`` /
    ``per-session`` / ``per_session`` as the
    per-session scope, case-insensitively.
    """
    if isinstance(value, str):
        wanted = value.strip().lower().replace("-", "_").replace(" ", "_")
        if wanted in _SCOPE_WORDS:
            return _SCOPE_WORDS[wanted]
    raise ValueError(
        "a budget scope must be one of %s, got %r"
        % ("/".join(BUDGET_SCOPES), value))


def _pick(mapping: Dict[str, Any], names: Tuple[str, ...],
          what: str) -> Any:
    """One field from its spellings, or a refusal on conflict."""
    found = [name for name in names if name in mapping]
    if not found:
        return None
    first = mapping[found[0]]
    for name in found[1:]:
        if mapping[name] != first:
            raise ValueError(f"a budget record names two different {what}")
    return first


def _check_count_limit(value: Any, what: str) -> Optional[int]:
    """A token / command limit: a whole number over 0, or None."""
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(
            f"a budget {what} limit must be a whole number, "
            f"got {value!r}")
    if value <= 0:
        raise ValueError(
            f"a budget {what} limit must be more than zero, "
            f"got {value!r}")
    return value


def _check_amount_limit(value: Any, what: str) -> Optional[float]:
    """A cost / time limit: a finite number over 0, or None."""
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(
            f"a budget {what} limit must be a number, got {value!r}")
    amount = float(value)
    if not math.isfinite(amount) or amount <= 0:
        raise ValueError(
            f"a budget {what} limit must be more than zero, "
            f"got {value!r}")
    return amount


def _check_count_used(value: Any, what: str) -> int:
    """Tokens / commands actually used: a whole number of 0 or more."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(
            f"{what} used must be a whole number, got {value!r}")
    if value < 0:
        raise ValueError(f"{what} used must not be negative, got {value!r}")
    return value


def _check_amount_used(value: Any, what: str) -> float:
    """Cost / time actually used: a finite number of 0 or more."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{what} used must be a number, got {value!r}")
    amount = float(value)
    if not math.isfinite(amount) or amount < 0:
        raise ValueError(
            f"{what} used must not be negative, got {value!r}")
    return amount


def _pick_time(mapping: Dict[str, Any], second_names: Tuple[str, ...],
               minute_names: Tuple[str, ...], what: str,
               check: Any) -> Any:
    """A time named in seconds and/or minutes, read as seconds.

    Spellings in one unit must agree (``_pick``'s
    rule); when both units are named, the two
    readings must name the same time after
    conversion, or the record refuses.
    """
    seconds = _pick(mapping, second_names, what)
    minutes = _pick(mapping, minute_names, what)
    if seconds is None and minutes is None:
        return None
    if minutes is None:
        return check(seconds)
    if seconds is None:
        return check(minutes) * 60.0
    if check(seconds) != check(minutes) * 60.0:
        raise ValueError(f"a budget record names two different {what}")
    return check(seconds)


# ---------------------------------------------------------------------
# The budget: how much work is allowed, as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class Budget:
    """One budget: a scope and its limits, as data.

    ``scope`` is ``task`` (per-task) or ``session``
    (per-session). Each limit is optional: a limit
    of None means that dimension is unlimited - no
    default is invented. ``token_limit`` and
    ``command_limit`` are whole numbers;
    ``cost_limit`` is a cost in US dollars, the
    ``costs.py`` vocabulary; ``time_limit_seconds``
    is a time in seconds (a limit named in minutes
    is stored as seconds). ``label`` is the short
    human name reports use; when empty the scope
    itself is the label.

    Constructing one validates it, so a Budget
    that exists is a budget the agent layer could
    guard with.
    """

    label: str = ""
    scope: str = "task"
    budget_id: Optional[str] = None
    token_limit: Optional[int] = None
    cost_limit: Optional[float] = None
    time_limit_seconds: Optional[float] = None
    command_limit: Optional[int] = None

    def __post_init__(self) -> None:
        if not isinstance(self.label, str):
            raise ValueError(
                f"a budget label must be text, got {self.label!r}")
        object.__setattr__(self, "label", self.label.strip())
        object.__setattr__(
            self, "scope", normalize_budget_scope(self.scope))
        if self.budget_id is not None:
            object.__setattr__(
                self, "budget_id", normalize_budget_id(self.budget_id))
        object.__setattr__(
            self, "token_limit",
            _check_count_limit(self.token_limit, "token"))
        object.__setattr__(
            self, "cost_limit",
            _check_amount_limit(self.cost_limit, "cost"))
        object.__setattr__(
            self, "time_limit_seconds",
            _check_amount_limit(self.time_limit_seconds, "time"))
        object.__setattr__(
            self, "command_limit",
            _check_count_limit(self.command_limit, "command"))

    @property
    def display_label(self) -> str:
        return self.label or f"per-{self.scope} budget"

    @property
    def limits(self) -> Dict[str, Any]:
        """The named limits by dimension; None is unlimited."""
        return {
            "tokens": self.token_limit,
            "cost": self.cost_limit,
            "time": self.time_limit_seconds,
            "commands": self.command_limit,
        }

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "budget",
            "slice": BUDGETS_SLICE,
            "budget_id": self.budget_id,
            "label": self.label,
            "scope": self.scope,
            "token_limit": self.token_limit,
            "cost_limit": self.cost_limit,
            "time_limit_seconds": self.time_limit_seconds,
            "command_limit": self.command_limit,
        }


def validate_budget(budget: Any) -> Budget:
    """Validate one budget into a Budget.

    Accepts a Budget or a mapping naming a
    ``scope`` (or ``kind`` / ``type``), an
    optional ``budget_id`` (or ``id``) and
    ``label`` (or ``name``), and any of the
    limits: tokens as ``token_limit`` (or
    ``max_tokens`` / ``tokens``), cost in dollars
    as ``cost_limit`` (or ``max_cost`` / ``cost``
    / ``cost_usd`` / ``cost_limit_usd``), time as
    seconds (``time_limit_seconds`` /
    ``time_seconds`` / ``time_limit`` / ``time`` /
    ``seconds``) or minutes (``time_limit_minutes``
    / ``time_minutes`` / ``minutes``, read as
    seconds), and commands as ``command_limit``
    (or ``max_commands`` / ``commands``). Naming
    two spellings of one field with different
    values refuses, and unknown keys refuse.
    """
    if isinstance(budget, Budget):
        return budget
    if not isinstance(budget, dict):
        raise ValueError(f"a budget must be a mapping, got {budget!r}")
    unknown = set(budget) - _BUDGET_KEYS
    if unknown:
        raise ValueError(
            "unknown budget keys: %s" % ", ".join(sorted(unknown)))
    label = _pick(budget, ("label", "name"), "labels")
    scope = _pick(budget, ("scope", "kind", "type"), "scopes")
    budget_id = _pick(budget, ("budget_id", "id"), "budget ids")
    kwargs: Dict[str, Any] = {}
    if label is not None:
        kwargs["label"] = label
    if scope is not None:
        kwargs["scope"] = scope
    if budget_id is not None:
        kwargs["budget_id"] = budget_id
    token_limit = _pick(
        budget, ("token_limit", "max_tokens", "tokens"), "token limits")
    if token_limit is not None:
        kwargs["token_limit"] = token_limit
    cost_limit = _pick(
        budget,
        ("cost_limit", "max_cost", "cost", "cost_usd",
         "cost_limit_usd"),
        "cost limits")
    if cost_limit is not None:
        kwargs["cost_limit"] = cost_limit
    time_limit = _pick_time(
        budget,
        ("time_limit_seconds", "time_seconds", "time_limit", "time",
         "seconds"),
        ("time_limit_minutes", "time_minutes", "minutes"),
        "time limits", lambda v: _check_amount_limit(v, "time"))
    if time_limit is not None:
        kwargs["time_limit_seconds"] = time_limit
    command_limit = _pick(
        budget, ("command_limit", "max_commands", "commands"),
        "command limits")
    if command_limit is not None:
        kwargs["command_limit"] = command_limit
    return Budget(**kwargs)


def build_budget(budget: Any = None, **kwargs: Any) -> Budget:
    """Build one validated budget from a mapping or field words."""
    if isinstance(budget, Budget) and not kwargs:
        return budget
    if isinstance(budget, dict) or budget is None:
        merged: Dict[str, Any] = {}
        if isinstance(budget, dict):
            merged.update(budget)
        merged.update(kwargs)
        return validate_budget(merged)
    raise ValueError(f"a budget must be a mapping, got {budget!r}")


def _require_budget(budget: Any) -> Budget:
    if isinstance(budget, Budget):
        return budget
    return validate_budget(budget)


# ---------------------------------------------------------------------
# The usage reading: what has actually been spent, as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class BudgetUsage:
    """What has actually been spent, as data.

    ``tokens_used`` counts tokens and
    ``commands_used`` counts commands, both whole
    numbers of 0 or more; ``cost_used`` is a cost
    in US dollars, the ``costs.py`` vocabulary (a
    model its table does not price is unknown at
    zero cost there, so a reading here never
    invents a price either); ``time_used_seconds``
    is elapsed time in seconds. A reading of all
    zeros is a fresh start, not an error.

    Constructing one validates it, so a reading
    that exists never runs backwards or below
    zero.
    """

    tokens_used: int = 0
    cost_used: float = 0.0
    time_used_seconds: float = 0.0
    commands_used: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "tokens_used",
            _check_count_used(self.tokens_used, "tokens"))
        object.__setattr__(
            self, "cost_used",
            _check_amount_used(self.cost_used, "cost"))
        object.__setattr__(
            self, "time_used_seconds",
            _check_amount_used(self.time_used_seconds, "time"))
        object.__setattr__(
            self, "commands_used",
            _check_count_used(self.commands_used, "commands"))

    @property
    def amounts(self) -> Dict[str, Any]:
        """The spent amounts by dimension."""
        return {
            "tokens": self.tokens_used,
            "cost": self.cost_used,
            "time": self.time_used_seconds,
            "commands": self.commands_used,
        }

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "budget_usage",
            "slice": BUDGETS_SLICE,
            "tokens_used": self.tokens_used,
            "cost_used": self.cost_used,
            "time_used_seconds": self.time_used_seconds,
            "commands_used": self.commands_used,
        }


#: The roadmap's own word for a usage reading.
Usage = BudgetUsage


def validate_usage(usage: Any) -> BudgetUsage:
    """Validate one usage reading into a BudgetUsage.

    Accepts a BudgetUsage or a mapping naming any
    of: tokens as ``tokens_used`` (or ``tokens`` /
    ``token_count``), cost in dollars as
    ``cost_used`` (or ``cost`` / ``cost_usd`` /
    ``spend`` / ``spent_usd``), time as seconds
    (``time_used_seconds`` / ``elapsed_seconds`` /
    ``time_seconds`` / ``time_used`` / ``elapsed``)
    or minutes (``time_used_minutes`` /
    ``elapsed_minutes`` / ``time_minutes`` /
    ``minutes_used``, read as seconds), and
    commands as ``commands_used`` (or ``commands``
    / ``command_count``). Unnamed dimensions read
    as zero spent. Naming two spellings of one
    field with different values refuses, and
    unknown keys refuse.
    """
    if isinstance(usage, BudgetUsage):
        return usage
    if not isinstance(usage, dict):
        raise ValueError(
            f"a budget usage reading must be a mapping, got {usage!r}")
    unknown = set(usage) - _USAGE_KEYS
    if unknown:
        raise ValueError(
            "unknown budget usage keys: %s" % ", ".join(sorted(unknown)))
    kwargs: Dict[str, Any] = {}
    tokens = _pick(
        usage, ("tokens_used", "tokens", "token_count"), "tokens used")
    if tokens is not None:
        kwargs["tokens_used"] = tokens
    cost = _pick(
        usage, ("cost_used", "cost", "cost_usd", "spend", "spent_usd"),
        "costs used")
    if cost is not None:
        kwargs["cost_used"] = cost
    elapsed = _pick_time(
        usage,
        ("time_used_seconds", "elapsed_seconds", "time_seconds",
         "time_used", "elapsed"),
        ("time_used_minutes", "elapsed_minutes", "time_minutes",
         "minutes_used"),
        "times used", lambda v: _check_amount_used(v, "time"))
    if elapsed is not None:
        kwargs["time_used_seconds"] = elapsed
    commands = _pick(
        usage, ("commands_used", "commands", "command_count"),
        "commands used")
    if commands is not None:
        kwargs["commands_used"] = commands
    return BudgetUsage(**kwargs)


def build_usage(usage: Any = None, **kwargs: Any) -> BudgetUsage:
    """Build one validated usage reading."""
    if isinstance(usage, BudgetUsage) and not kwargs:
        return usage
    if isinstance(usage, dict) or usage is None:
        merged: Dict[str, Any] = {}
        if isinstance(usage, dict):
            merged.update(usage)
        merged.update(kwargs)
        return validate_usage(merged)
    raise ValueError(
        f"a budget usage reading must be a mapping, got {usage!r}")


def _require_usage(usage: Any) -> BudgetUsage:
    if isinstance(usage, BudgetUsage):
        return usage
    if usage is None:
        return BudgetUsage()
    return validate_usage(usage)


# ---------------------------------------------------------------------
# The verdict: one budget judged against one usage, mechanically.
# ---------------------------------------------------------------------


def _dimension_readings(budget: Budget, usage: BudgetUsage):
    """(dimension, used, limit) triples, in canonical order."""
    limits = budget.limits
    amounts = usage.amounts
    return tuple(
        (dimension, amounts[dimension], limits[dimension])
        for dimension in BUDGET_DIMENSIONS)


def _classify(budget: Budget, usage: BudgetUsage):
    """The (exceeded, warning) dimension tuples a reading earns."""
    exceeded, warning = [], []
    for dimension, used, limit in _dimension_readings(budget, usage):
        if limit is None:
            continue
        if used >= limit:
            exceeded.append(dimension)
        elif used >= WARNING_FRACTION * limit:
            warning.append(dimension)
    return tuple(exceeded), tuple(warning)


def _status_for(exceeded: Tuple[str, ...],
                warning: Tuple[str, ...]) -> str:
    if exceeded:
        return "exceeded"
    if warning:
        return "warning"
    return "within"


@dataclass(frozen=True)
class BudgetVerdict:
    """One budget judged against one usage, as data.

    ``status`` is within, warning (a limited
    dimension at or past 80% of its limit) or
    exceeded (a limited dimension at or past its
    limit). ``exceeded_dimensions`` and
    ``warning_dimensions`` name the dimensions in
    canonical order, and the used and limit
    amounts for every dimension are carried
    alongside. The status and the two dimension
    lists are validated against those amounts on
    construction, so a verdict that exists never
    disagrees with itself.
    """

    budget_id: Optional[str] = None
    label: str = ""
    scope: str = "task"
    status: str = "within"
    exceeded_dimensions: Tuple[str, ...] = ()
    warning_dimensions: Tuple[str, ...] = ()
    tokens_used: int = 0
    token_limit: Optional[int] = None
    cost_used: float = 0.0
    cost_limit: Optional[float] = None
    time_used_seconds: float = 0.0
    time_limit_seconds: Optional[float] = None
    commands_used: int = 0
    command_limit: Optional[int] = None

    def __post_init__(self) -> None:
        if self.budget_id is not None:
            object.__setattr__(
                self, "budget_id", normalize_budget_id(self.budget_id))
        if not isinstance(self.label, str):
            raise ValueError(
                f"a budget verdict label must be text, got {self.label!r}")
        object.__setattr__(self, "label", self.label.strip())
        object.__setattr__(
            self, "scope", normalize_budget_scope(self.scope))
        if not isinstance(self.status, str) \
                or self.status.strip().lower().replace("-", "_") \
                not in BUDGET_VERDICT_STATUSES:
            raise ValueError(
                "a budget verdict status must be one of %s, got %r"
                % ("/".join(BUDGET_VERDICT_STATUSES), self.status))
        object.__setattr__(
            self, "status",
            self.status.strip().lower().replace("-", "_"))
        object.__setattr__(
            self, "tokens_used",
            _check_count_used(self.tokens_used, "tokens"))
        object.__setattr__(
            self, "token_limit",
            _check_count_limit(self.token_limit, "token"))
        object.__setattr__(
            self, "cost_used",
            _check_amount_used(self.cost_used, "cost"))
        object.__setattr__(
            self, "cost_limit",
            _check_amount_limit(self.cost_limit, "cost"))
        object.__setattr__(
            self, "time_used_seconds",
            _check_amount_used(self.time_used_seconds, "time"))
        object.__setattr__(
            self, "time_limit_seconds",
            _check_amount_limit(self.time_limit_seconds, "time"))
        object.__setattr__(
            self, "commands_used",
            _check_count_used(self.commands_used, "commands"))
        object.__setattr__(
            self, "command_limit",
            _check_count_limit(self.command_limit, "command"))
        for field_name in ("exceeded_dimensions", "warning_dimensions"):
            value = getattr(self, field_name)
            if isinstance(value, (str, bytes)) \
                    or not isinstance(value, (list, tuple)):
                raise ValueError(
                    f"a budget verdict's {field_name} must be a list "
                    f"of dimension words")
            cleaned = []
            for word in value:
                if not isinstance(word, str) \
                        or word.strip().lower() not in BUDGET_DIMENSIONS:
                    raise ValueError(
                        f"a budget dimension must be one of %s, "
                        f"got {word!r}" % "/".join(BUDGET_DIMENSIONS))
                cleaned.append(word.strip().lower())
            object.__setattr__(self, field_name, tuple(cleaned))
        budget = Budget(
            label=self.label, scope=self.scope,
            budget_id=self.budget_id, token_limit=self.token_limit,
            cost_limit=self.cost_limit,
            time_limit_seconds=self.time_limit_seconds,
            command_limit=self.command_limit)
        usage = BudgetUsage(
            tokens_used=self.tokens_used, cost_used=self.cost_used,
            time_used_seconds=self.time_used_seconds,
            commands_used=self.commands_used)
        exceeded, warning = _classify(budget, usage)
        if tuple(self.exceeded_dimensions) != exceeded \
                or tuple(self.warning_dimensions) != warning:
            raise ValueError(
                "a budget verdict's dimensions disagree with its "
                "used and limit amounts")
        wanted = _status_for(exceeded, warning)
        if self.status != wanted:
            raise ValueError(
                f"a budget verdict with these amounts is {wanted}, "
                f"got {self.status!r}")

    @property
    def display_label(self) -> str:
        return self.label or f"per-{self.scope} budget"

    @property
    def readings(self) -> Dict[str, Dict[str, Any]]:
        """Used / limit / fraction by dimension; limit None is unlimited."""
        raw = {
            "tokens": (self.tokens_used, self.token_limit),
            "cost": (self.cost_used, self.cost_limit),
            "time": (self.time_used_seconds, self.time_limit_seconds),
            "commands": (self.commands_used, self.command_limit),
        }
        result: Dict[str, Dict[str, Any]] = {}
        for dimension in BUDGET_DIMENSIONS:
            used, limit = raw[dimension]
            result[dimension] = {
                "used": used, "limit": limit,
                "fraction": (used / limit) if limit is not None else None,
            }
        return result

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "budget_verdict",
            "slice": BUDGETS_SLICE,
            "budget_id": self.budget_id,
            "label": self.label,
            "scope": self.scope,
            "status": self.status,
            "exceeded": list(self.exceeded_dimensions),
            "warning": list(self.warning_dimensions),
            "readings": {
                dimension: {
                    "used": reading["used"], "limit": reading["limit"]}
                for dimension, reading in self.readings.items()},
        }


def validate_verdict(verdict: Any) -> BudgetVerdict:
    """Validate one verdict into a BudgetVerdict.

    A verdict is normally made by ``judge_budget``;
    this accepts a BudgetVerdict unchanged, so a
    caller holding one needs no second road.
    """
    if isinstance(verdict, BudgetVerdict):
        return verdict
    raise ValueError(f"a budget verdict is needed, got {verdict!r}")


def _require_verdict(verdict: Any) -> BudgetVerdict:
    return validate_verdict(verdict)


def judge_budget(budget: Any, usage: Any = None) -> BudgetVerdict:
    """Judge one budget against one usage reading, mechanically.

    ``budget`` is a Budget (or budget mapping) and
    ``usage`` a BudgetUsage (or usage mapping);
    with no usage named, nothing has been spent
    and the verdict is within. A dimension at or
    past its limit is exceeded; at or past 80% of
    its limit it is approaching (warning); a
    dimension with no limit is unlimited and can
    earn neither reading.
    """
    checked_budget = _require_budget(budget)
    checked_usage = _require_usage(usage)
    exceeded, warning = _classify(checked_budget, checked_usage)
    return BudgetVerdict(
        budget_id=checked_budget.budget_id,
        label=checked_budget.label, scope=checked_budget.scope,
        status=_status_for(exceeded, warning),
        exceeded_dimensions=exceeded, warning_dimensions=warning,
        tokens_used=checked_usage.tokens_used,
        token_limit=checked_budget.token_limit,
        cost_used=checked_usage.cost_used,
        cost_limit=checked_budget.cost_limit,
        time_used_seconds=checked_usage.time_used_seconds,
        time_limit_seconds=checked_budget.time_limit_seconds,
        commands_used=checked_usage.commands_used,
        command_limit=checked_budget.command_limit)


def _format_amount(dimension: str, value: Any) -> str:
    """One used / limit amount, in the dimension's own words."""
    if dimension == "tokens":
        return f"{value} tokens"
    if dimension == "cost":
        return f"${float(value):.2f}"
    if dimension == "time":
        amount = float(value)
        if amount == int(amount):
            return f"{int(amount)} seconds"
        return f"{amount} seconds"
    return f"{value} commands"


def _reading_phrase(dimension: str, used: Any, limit: Any) -> str:
    """``800 of 1000 tokens`` - one dimension's reading, in words."""
    if dimension == "tokens":
        return f"{used} of {limit} tokens"
    if dimension == "cost":
        return f"${float(used):.2f} of ${float(limit):.2f}"
    if dimension == "time":
        return (
            f"{_format_amount(dimension, used)} of "
            f"{_format_amount(dimension, limit)}")
    return f"{used} of {limit} commands"


def _verdict_readings(verdict: BudgetVerdict, dimensions) -> str:
    readings = verdict.readings
    return "; ".join(
        _reading_phrase(
            dimension, readings[dimension]["used"],
            readings[dimension]["limit"])
        for dimension in dimensions)


def _paused_headline(verdict: BudgetVerdict) -> str:
    names = ", ".join(verdict.exceeded_dimensions)
    return (
        f"Budget paused: {verdict.display_label} (per-{verdict.scope} "
        f"budget) reached its limit on {names} - "
        f"{_verdict_readings(verdict, verdict.exceeded_dimensions)}. "
        "This is a graceful pause with a report, never a "
        "mid-edit death: work rests here until the budget is "
        "raised or a new budget begins.")


def _report_headline(verdict: BudgetVerdict) -> str:
    names = ", ".join(verdict.warning_dimensions)
    return (
        f"Budget warning: {verdict.display_label} (per-{verdict.scope} "
        f"budget) is approaching its limit on {names} - "
        f"{_verdict_readings(verdict, verdict.warning_dimensions)}. "
        "No pause yet; a budget that reaches its limit pauses "
        "gracefully, never mid-edit.")


def budget_paused_record(budget: Any, usage: Any = None,
                         verdict: Any = None) -> Optional[Dict[str, Any]]:
    """The session-news record of one reached budget, or None.

    Only an exceeded verdict yields a record -
    the agent layer publishes this record as a
    session event when it is not None, so a
    graceful pause can never be lost as a mere
    log line, and never announced when no budget
    has been reached. ``verdict``, when given, is
    the reading judged instead of a fresh one.
    """
    judged = _require_verdict(verdict) if verdict is not None \
        else judge_budget(budget, usage)
    if judged.status != "exceeded":
        return None
    return {
        "type": "budget_paused",
        "news": True,
        "slice": BUDGETS_SLICE,
        "budget_id": judged.budget_id,
        "label": judged.label,
        "scope": judged.scope,
        "status": judged.status,
        "exceeded": list(judged.exceeded_dimensions),
        "warning": list(judged.warning_dimensions),
        "readings": judged.to_record()["readings"],
        "graceful": True,
        "headline": _paused_headline(judged),
    }


def budget_report_record(budget: Any, usage: Any = None,
                         verdict: Any = None) -> Optional[Dict[str, Any]]:
    """The session-news budget report, or None when within.

    A warning verdict yields a ``budget_report``
    record; an exceeded verdict yields the
    ``budget_paused`` record itself, so the pause
    is reported by the same shape whichever road
    a caller takes. A within verdict yields no
    record at all.
    """
    judged = _require_verdict(verdict) if verdict is not None \
        else judge_budget(budget, usage)
    if judged.status == "exceeded":
        return budget_paused_record(budget, usage, judged)
    if judged.status != "warning":
        return None
    return {
        "type": "budget_report",
        "news": True,
        "slice": BUDGETS_SLICE,
        "budget_id": judged.budget_id,
        "label": judged.label,
        "scope": judged.scope,
        "status": judged.status,
        "exceeded": list(judged.exceeded_dimensions),
        "warning": list(judged.warning_dimensions),
        "readings": judged.to_record()["readings"],
        "graceful": True,
        "headline": _report_headline(judged),
    }


# ---------------------------------------------------------------------
# The registry model: budgets held in registration order, ids
# deterministic; the latest usage reading held alongside each.
# ---------------------------------------------------------------------


class BudgetRegistry:
    """An in-memory registry of budgets.

    Budgets are held in registration order. Ids
    are deterministic: a caller-supplied id is
    used as given (a duplicate refuses), and an
    unsupplied id is the next ``budget-N`` in
    sequence, skipping any number a supplied id
    already took - no randomness a test cannot
    pin. The latest usage reading for a budget is
    held alongside it, as data, replaced when a
    newer one is recorded. Storage beyond memory
    (a session's journal, a file) is the agent
    layer's concern; this model is neutral.
    """

    def __init__(self) -> None:
        self._budgets: Dict[str, Budget] = {}
        self._usage: Dict[str, BudgetUsage] = {}
        self._next = 1

    def _fresh_id(self) -> str:
        while f"budget-{self._next}" in self._budgets:
            self._next += 1
        budget_id = f"budget-{self._next}"
        self._next += 1
        return budget_id

    def register(self, budget: Any = None, **kwargs: Any) -> Budget:
        """Register one budget and hold it; duplicate ids refuse."""
        if kwargs and isinstance(budget, (Budget, dict)):
            validated = build_budget(budget, **kwargs)
        elif kwargs and budget is None:
            validated = build_budget(**kwargs)
        else:
            if kwargs:
                raise ValueError(
                    "a budget is named twice: as a record and as "
                    "field words")
            validated = _require_budget(budget)
        if validated.budget_id is None:
            validated = replace(validated, budget_id=self._fresh_id())
        elif validated.budget_id in self._budgets:
            raise ValueError(
                f"a budget named {validated.budget_id!r} already exists")
        self._budgets[validated.budget_id] = validated
        return validated

    def get(self, budget_id: Any) -> Budget:
        """The budget one id names; an unknown id raises KeyError."""
        wanted = normalize_budget_id(budget_id)
        if wanted not in self._budgets:
            raise KeyError(f"unknown budget: {wanted!r}")
        return self._budgets[wanted]

    def list_budgets(self) -> Tuple[Budget, ...]:
        """Every held budget, in registration order."""
        return tuple(self._budgets.values())

    def record_usage(self, budget_id: Any, usage: Any = None,
                     **kwargs: Any) -> BudgetUsage:
        """Record one budget's latest usage reading, replacing any older.

        Accepts a BudgetUsage, a usage mapping, or
        usage field words. A budget the registry
        does not hold raises KeyError.
        """
        budget = self.get(budget_id)
        if kwargs and isinstance(usage, (BudgetUsage, dict)):
            raise ValueError(
                "a usage reading is named twice: as a record and "
                "as field words")
        if isinstance(usage, (BudgetUsage, dict)) or usage is None:
            checked = build_usage(usage, **kwargs)
        else:
            raise ValueError(
                f"a budget usage reading must be a mapping, "
                f"got {usage!r}")
        self._usage[budget.budget_id] = checked
        return checked

    def get_usage(self, budget_id: Any) -> Optional[BudgetUsage]:
        """One budget's recorded usage, or None when none is held."""
        budget = self.get(budget_id)
        return self._usage.get(budget.budget_id)

    def check(self, budget_id: Any, usage: Any = None) -> BudgetVerdict:
        """Judge one held budget, mechanically.

        ``usage``, when given, is the reading
        judged; otherwise the budget's recorded
        reading is judged, and a budget with no
        recorded reading has spent nothing.
        Checking records nothing.
        """
        budget = self.get(budget_id)
        reading = _require_usage(usage) if usage is not None \
            else self._usage.get(budget.budget_id)
        return judge_budget(budget, reading)

    def list_verdicts(self) -> Tuple[BudgetVerdict, ...]:
        """Every held budget judged on its recorded reading, in order."""
        return tuple(self.check(b.budget_id) for b in self.list_budgets())

    def paused_record(self, budget_id: Any,
                      usage: Any = None) -> Optional[Dict[str, Any]]:
        """One held budget's pause news record, or None."""
        return budget_paused_record(None, None, self.check(budget_id, usage))

    def report_record(self, budget_id: Any,
                      usage: Any = None) -> Optional[Dict[str, Any]]:
        """One held budget's report news record, or None when within."""
        return budget_report_record(None, None, self.check(budget_id, usage))


# ---------------------------------------------------------------------
# The /budgets surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------


def format_budget(budget: Any, verdict: Any = None) -> str:
    """One budget, in plain words, with its verdict when one is given."""
    current = _require_budget(budget)
    checked = _require_verdict(verdict) if verdict is not None else None
    if checked is not None and current.budget_id is not None \
            and checked.budget_id != current.budget_id:
        raise ValueError(
            f"a verdict for budget {checked.budget_id!r} does not "
            f"judge budget {current.budget_id!r}")
    name = current.budget_id or current.display_label
    limits = current.limits
    parts = []
    for dimension in BUDGET_DIMENSIONS:
        limit = limits[dimension]
        if limit is None:
            parts.append(f"{dimension}: unlimited")
        else:
            parts.append(
                f"{dimension}: limit {_format_amount(dimension, limit)}")
    line = (
        f"{name}: {current.display_label} [per-{current.scope} budget] - "
        + "; ".join(parts) + ".")
    if checked is not None:
        line += f" Verdict: {checked.status}."
    return line


def format_budgets(source: Any = None, verdicts: Any = None) -> str:
    """The budgets, in plain words, in the order given.

    With no budgets at all the text starts with
    the plain statement of that fact. Every line
    states its budget's scope and limits in words.
    """
    if source is None:
        selected: Tuple[Budget, ...] = ()
        by_id: Dict[str, BudgetVerdict] = {}
    elif isinstance(source, BudgetRegistry):
        selected = source.list_budgets()
        by_id = {v.budget_id: v for v in source.list_verdicts()}
    elif isinstance(source, (list, tuple)):
        selected = tuple(_require_budget(b) for b in source)
        by_id = {}
        if verdicts is not None:
            if isinstance(verdicts, (str, bytes)) \
                    or not isinstance(verdicts, (list, tuple)):
                raise ValueError("budget verdicts must be a list of verdicts")
            by_id = {
                v.budget_id: _require_verdict(v) for v in verdicts}
    else:
        raise ValueError("budgets must be a registry or a list of budgets")
    if verdicts is not None and not isinstance(source, BudgetRegistry) \
            and not isinstance(source, (list, tuple)):
        by_id = {}
    if not selected:
        return "Budgets: none. No budget guardrails are held."
    lines = [f"Budgets: {len(selected)} held."]
    for budget in selected:
        verdict = by_id.get(budget.budget_id) \
            if budget.budget_id is not None else None
        lines.append(f"  {format_budget(budget, verdict)}")
    return "\n".join(lines)


def format_verdict(verdict: Any = None, usage: Any = None) -> str:
    """One budget verdict, in plain words, amounts always stated.

    Accepts a BudgetVerdict, or a Budget (or
    budget mapping) judged against ``usage``.
    """
    if isinstance(verdict, BudgetVerdict):
        judged = verdict
    elif verdict is not None:
        judged = judge_budget(verdict, usage)
    else:
        raise ValueError("format_verdict needs a verdict or a budget")
    readings = judged.readings
    if judged.status == "exceeded":
        return (
            f"Budget verdict: exceeded - "
            f"{_verdict_readings(judged, judged.exceeded_dimensions)} "
            "reached the limit. This is a graceful pause with a "
            "report, never a mid-edit death.")
    if judged.status == "warning":
        detail = _verdict_readings(judged, judged.warning_dimensions)
        return (
            f"Budget verdict: warning - {detail} is approaching "
            "the limit (at or past 80%); no dimension has reached "
            "its limit yet.")
    spent = "; ".join(
        _reading_phrase(dimension, readings[dimension]["used"],
                        readings[dimension]["limit"])
        for dimension in BUDGET_DIMENSIONS
        if readings[dimension]["limit"] is not None)
    if spent:
        return (
            f"Budget verdict: within - {spent}; every limited "
            "dimension is below 80% of its limit, and unlimited "
            "dimensions never pause.")
    return (
        "Budget verdict: within - this budget names no limits, "
        "so every dimension is unlimited and nothing can pause.")


def format_budget_report(record: Any) -> str:
    """One budget pause / report record as its plain headline."""
    if isinstance(record, dict) \
            and record.get("type") in ("budget_paused", "budget_report"):
        return str(record["headline"])
    raise ValueError(
        "format_budget_report needs a budget pause or report record")


#: The pause record's formatter under its own name.
format_report = format_budget_report


def format_budgets_screen(source: Any = None, verdicts: Any = None) -> str:
    """The whole slice, in plain words, for /budgets."""
    lines = ["Budgets (M-107) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_budgets(source, verdicts))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_budgets_args(args: Any) -> Tuple[str, Optional[str]]:
    """Parse the /budgets grammar both surfaces share.

    No words (or ``show``) shows the budgets;
    ``show <budget>`` and a bare budget id show
    one budget; ``check`` checks every held
    budget and ``check <budget>`` checks one.
    Anything else is a usage error naming the
    grammar. Returns ``(action, budget-id-or-None)``.
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
    if head in ("show", "check") and len(words) == 2:
        try:
            return (head, normalize_budget_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head in ("show", "check"):
        raise ValueError(USAGE)
    if len(words) == 1:
        try:
            return ("show", normalize_budget_id(words[0]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
