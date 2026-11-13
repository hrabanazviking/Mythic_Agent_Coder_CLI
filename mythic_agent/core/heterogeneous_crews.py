"""Heterogeneous crews (All-Features roadmap slice M-129).

Part VI - Agents as files - continues here. The
roadmap's words: ``members on different
models/providers (a Claude Architect, a local-LLM
Forge Worker) - routing from Part II, budgets from
Part V.``

What already shipped, and what this slice adds:

* The crew itself is already data
  (``core/crew_members.py``, M-121: every member
  holds one office and may name a model route),
  the offices are formalised (M-122, M-123), the
  worktrees, dealing, comms, deadlock watch and
  merge discipline are already data (M-124 to
  M-128). What nothing held is the crew's
  heterogeneity itself: which member rides which
  provider on which model, whether that route is
  one the shipped registry actually lists, and
  whether the member's spending stays inside the
  budget its assignment names. Today every member
  silently rides the session default, a route
  naming a model its provider does not list looks
  the same as a real one, and no budget guards a
  member's own line.
* This slice is that heterogeneity, as a pure
  layer: the evidence validated as data (an
  assignment - a member, a provider, a model and
  the budget it rides under; a Part V budget,
  composed from ``core/budgets.py`` (M-107) by
  import and never re-invented; and a usage
  reading - what one member has actually spent),
  the shipped data file
  (``mythic_agent/data/heterogeneous_crews.yaml``)
  holding one example crew plan in exactly the
  shape a real crew plan's file takes, a loader
  for a plan file anywhere on disk, the verdicts
  and the state of every member's route derived
  mechanically from the evidence alone and from
  the shipped Part II truth, a verdict record and
  a report record shaped as session news, and a
  small in-memory registry model. This module
  spawns no crew, calls no provider, performs no
  routing and imports no agent / UI code; the
  agent layer owns holding the plan for a session
  and handing the verdicts to the coordinator.

Honesty rules, enforced here and pinned by tests:

* **Verdicts are derived, never stored.** A
  report is computed from the assignments,
  budgets and readings it is judged under, so it
  can never disagree with them; the same evidence
  always yields the same verdicts and the same
  routes (deterministic order, deterministic
  wording).
* **Routing truth is Part II's, composed.** A
  provider word resolves through the M-019
  registry (``core/provider_registry.py``),
  aliases included - an unknown provider refuses.
  A route is known only when that registry lists
  the model under the provider. A model's known
  context is the M-027 capability truth
  (``core/model_capabilities.py``): unknown stays
  unknown (None), never guessed. A route's
  switchability is the M-028 rule
  (``core/model_switch.py`` SWITCHABLE_DIALECTS):
  only the dialects the live session can speak
  count as switchable.
* **Budgets are Part V's, composed.** A budget
  is an M-107 Budget (``core/budgets.py``),
  validated and judged by that layer's own roads
  (``judge_budget``) - this slice invents no
  second budget and no second judge. A usage
  reading is an M-107 BudgetUsage.
* **The verdicts are the roadmap's three.** A
  verdict is ``unknown_route`` (the provider does
  not list the model the assignment names),
  ``missing_budget`` (the assignment names no
  budget this plan holds) or ``over_budget`` (the
  member's reading is judged exceeded by the
  M-107 judge against the budget its assignment
  names) - no other kind is read, and an unknown
  kind refuses. Each assignment earns at most one
  verdict, in that precedence: route, then
  budget, then spending.
* **Members are the shipped layer's.** A member
  id reads exactly as the M-121 layer reads one
  and a budget id exactly as the M-107 layer
  reads one - composed by import, never re-read
  here.
* **Heterogeneity is data only; no crew is
  spawned.** No live crew is spawned, no real
  provider is called, no routing or billing
  actually happens in this slice: a verdict here
  is a validated record derived from given
  evidence, not an action taken, and the
  coordinator acts on the verdicts through later
  roads. The roadmap names the board (Part VIII)
  as where crew state will be visible; that board
  does not exist yet, so the verdicts are visible
  through this slice's own /hetero screen, and
  nothing here claims a board exists.
* **Malformed refuses.** An unknown kind or
  provider, a malformed member, model or budget
  id, a member assigned twice, a budget id held
  twice, two readings for one member, and unknown
  keys in an assignment, a reading, a verdict or
  a plan mapping all raise instead of being
  skipped or guessed at.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..resources import load_resource
from .budgets import (
    Budget,
    BudgetUsage,
    build_budget,
    build_usage,
    judge_budget,
    normalize_budget_id,
)
from .crew_members import normalize_member_id
from .model_capabilities import load_capabilities
from .model_switch import SWITCHABLE_DIALECTS
from .provider_registry import load_registry
from .validation import ValidationError

__all__ = [
    "HETERO_RESOURCE",
    "HETERO_SCHEMA",
    "HETERO_SLICE",
    "PLAIN_EXPLANATION",
    "USAGE",
    "VERDICT_KINDS",
    "HeteroAssignment",
    "HeteroReading",
    "HeteroReport",
    "HeteroVerdict",
    "HeterogeneousCrew",
    "HeterogeneousCrewRegistry",
    "RouteState",
    "assignment_record",
    "build_assignment",
    "build_reading",
    "build_verdict",
    "format_kinds",
    "format_routes",
    "format_verdict",
    "format_verdicts",
    "format_hetero_screen",
    "judge_hetero",
    "load_heterogeneous_crew",
    "load_heterogeneous_crew_file",
    "normalize_model",
    "normalize_provider",
    "normalize_verdict_kind",
    "parse_hetero_args",
    "plain_words",
    "reading_record",
    "report_plain_words",
    "report_record",
    "validate_assignment",
    "validate_plan",
    "validate_reading",
    "validate_report",
    "validate_verdict",
    "verdict_record",
]

HETERO_SLICE = "M-129"

#: The packaged data resource holding the example crew plan.
HETERO_RESOURCE = "heterogeneous_crews.yaml"

#: The schema word a crew plan file must carry.
HETERO_SCHEMA = "mythic.heterogeneous_crews/1"

#: The verdict kinds, in roadmap order: the route,
#: the budget, the spending.
VERDICT_KINDS = (
    "unknown_route", "missing_budget", "over_budget")

_KIND_READINGS = {
    "route": "unknown_route",
    "unknown": "unknown_route",
    "unknown_route": "unknown_route",
    "unlisted": "unknown_route",
    "budget": "missing_budget",
    "missing_budget": "missing_budget",
    "unbudgeted": "missing_budget",
    "over": "over_budget",
    "over_budget": "over_budget",
    "exceeded": "over_budget",
    "overspent": "over_budget",
}

#: The budget standings a route state may carry.
_BUDGET_STATUSES = (
    "within", "warning", "exceeded",
    "no_reading", "unbudgeted")

PLAIN_EXPLANATION = (
    "Heterogeneous crews: members ride different "
    "models on different providers - a Claude "
    "Architect, a local-LLM Forge Worker - with "
    "routing truth from Part II and budgets from "
    "Part V. Every verdict is derived from the "
    "given assignments, budgets and readings "
    "alone. There is no Part VIII board yet, so "
    "the verdicts are visible on this slice's own "
    "screen, not on a board. This layer holds the "
    "crew as data only; it spawns no live crew, "
    "calls no real provider and performs no "
    "routing or billing itself - the coordinator "
    "acts on the verdicts through later roads."
)

USAGE = (
    "Usage: /hetero, /hetero show, "
    "/hetero show <member>, /hetero routes, "
    "/hetero kinds"
)

_ASSIGNMENT_KEYS = frozenset({
    "id", "assignment_id", "member", "member_id",
    "provider", "provider_name", "model",
    "model_name", "budget", "budget_id",
})

_READING_KEYS = frozenset({
    "id", "reading_id", "member", "member_id", "usage",
    "tokens_used", "tokens", "token_count",
    "cost_used", "cost", "cost_usd", "spend", "spent_usd",
    "time_used_seconds", "elapsed_seconds", "time_seconds",
    "time_used", "elapsed", "time_used_minutes",
    "elapsed_minutes", "time_minutes", "minutes_used",
    "commands_used", "commands", "command_count",
})

_VERDICT_KEYS = frozenset({
    "kind", "verdict_kind", "member", "member_id",
    "provider", "provider_name", "model", "model_name",
    "title", "detail",
})

_PLAN_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "plan_note", "keeper", "assignments", "budgets",
    "readings",
})

#: The shipped example plan's assignments, in file
#: order: (member, provider, model, budget_id).
#: The shipped data file is held to exactly this
#: list by the loader's example check: the Claude
#: Architect and the local-LLM Forge Worker clean,
#: scribe under a budget the plan does not hold,
#: cartographer on a model ollama does not list.
_EXAMPLE_ASSIGNMENTS = (
    ("architect", "anthropic", "claude-sonnet-4-5",
     "arch-budget"),
    ("forge_worker", "ollama", "llama3.1",
     "forge-budget"),
    ("scribe", "openai", "gpt-5", "scribe-budget"),
    ("cartographer", "ollama", "llama9.9", None),
)

#: The shipped example plan's budgets, in file
#: order: (budget_id, scope, token_limit,
#: cost_limit, command_limit), composed M-107
#: budgets - the architect's session budget and
#: the forge worker's task budget.
_EXAMPLE_BUDGETS = (
    ("arch-budget", "session", 200000, 20.0, None),
    ("forge-budget", "task", 40000, None, 100),
)

#: The shipped example plan's readings, in file
#: order: (member, tokens_used, cost_used,
#: commands_used). The architect's reading is
#: within its budget; the forge worker's reading
#: is past its budget's token limit.
_EXAMPLE_READINGS = (
    ("architect", 1000, 0.5, 0),
    ("forge_worker", 45000, 0.0, 10),
)


def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_title(value: Any) -> str:
    title = _clean_text(value, "a verdict's title")
    if len(title) > 200 or "\x00" in title:
        raise ValueError(
            f"a verdict's title must be plain text of at most "
            f"200 characters, got {len(title)} characters")
    return title


def _check_detail(value: Any) -> str:
    detail = _clean_text(value, "a verdict's detail")
    if len(detail) > 2000 or "\x00" in detail:
        raise ValueError(
            f"a verdict's detail must be plain text of at most "
            f"2000 characters, got {len(detail)} characters")
    return detail


def normalize_provider(value: Any) -> str:
    """The canonical provider name a word names.

    Provider words read through the M-019 registry
    (``core/provider_registry.py``): case is
    folded and the registry's aliases resolve
    (``claude`` reads as anthropic, ``local`` as
    ollama). A name the registry does not hold
    raises - an unknown door is unknown, never
    guessed.
    """
    if isinstance(value, str) and value.strip():
        try:
            return load_registry().provider(value).name
        except KeyError:
            pass
    raise ValueError(
        f"a provider must be one the M-019 registry holds, "
        f"got {value!r}")


def normalize_model(value: Any) -> str:
    """The canonical model name a word names.

    A model name is plain text of at most 200
    characters, read with its case kept: model
    names are the providers' own words. Whether
    the named provider lists the model is the
    judge's concern (the unknown-route verdict),
    not this reading's.
    """
    model = _clean_text(value, "a model name")
    if len(model) > 200 or "\x00" in model:
        raise ValueError(
            f"a model name must be plain text of at most 200 "
            f"characters, got {len(model)} characters")
    return model


def normalize_verdict_kind(value: Any) -> str:
    """The canonical verdict kind a word names.

    Kind words read case-insensitively, with dashes
    read as underscores; the plain words ``route``,
    ``budget`` and ``over`` read as the one
    canonical kind each names. Anything else
    raises.
    """
    if isinstance(value, str):
        wanted = value.strip().lower().replace("-", "_")
        if wanted in _KIND_READINGS:
            return _KIND_READINGS[wanted]
    raise ValueError(
        "a verdict kind must be one of %s, got %r"
        % ("/".join(VERDICT_KINDS), value))


def _pick(mapping: Dict[str, Any], first: str, second: str,
          what: str) -> Any:
    """One field from its two spellings, or a refusal."""
    if first in mapping and second in mapping:
        if mapping[first] != mapping[second]:
            raise ValueError(f"a record names two different {what}")
        return mapping[first]
    if first in mapping:
        return mapping[first]
    return mapping.get(second)


def _provider_entry(provider: str):
    """The M-019 registry entry one canonical provider name holds."""
    return load_registry().provider(provider)


def _known_context(model: str) -> Optional[int]:
    """The M-027 known context for *model*, or None (unknown)."""
    return load_capabilities().for_model(model).context_tokens


# ---------------------------------------------------------------------
# The assignment: one member's route and budget, as evidence.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class HeteroAssignment:
    """One member's heterogeneous assignment, as data.

    ``member`` is the M-121 member the assignment
    routes; ``provider`` is the canonical M-019
    provider name it rides; ``model`` is the model
    it rides on that provider; ``budget_id`` is the
    id of the Part V budget guarding the member, or
    None when the assignment names none.
    Constructing one validates its shape only:
    whether the provider lists the model and
    whether the budget is held are the judge's
    concerns, not the validator's.
    """

    assignment_id: Optional[str] = None
    member: str = ""
    provider: str = ""
    model: str = ""
    budget_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.assignment_id is not None:
            object.__setattr__(
                self, "assignment_id",
                normalize_member_id(self.assignment_id))
        object.__setattr__(
            self, "member", normalize_member_id(self.member))
        object.__setattr__(
            self, "provider", normalize_provider(self.provider))
        object.__setattr__(
            self, "model", normalize_model(self.model))
        if self.budget_id is not None:
            object.__setattr__(
                self, "budget_id",
                normalize_budget_id(self.budget_id))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "hetero_assignment",
            "slice": HETERO_SLICE,
            "assignment_id": self.assignment_id,
            "member": self.member,
            "provider": self.provider,
            "model": self.model,
            "budget_id": self.budget_id,
        }


def validate_assignment(assignment: Any) -> HeteroAssignment:
    """Validate one assignment into a HeteroAssignment.

    Accepts a HeteroAssignment or a mapping naming
    a ``member`` (or ``member_id``), a ``provider``
    (or ``provider_name``), a ``model`` (or
    ``model_name``), an optional ``budget_id`` (or
    ``budget``) and an optional ``assignment_id``
    (or ``id``). Naming both spellings of one field
    with different values refuses, and unknown keys
    refuse.
    """
    if isinstance(assignment, HeteroAssignment):
        return assignment
    if not isinstance(assignment, dict):
        raise ValueError(
            f"an assignment must be a mapping, got {assignment!r}")
    unknown = set(assignment) - _ASSIGNMENT_KEYS
    if unknown:
        raise ValueError(
            "unknown assignment keys: %s"
            % ", ".join(sorted(unknown)))
    member = _pick(assignment, "member", "member_id", "members")
    if member is None:
        raise ValueError("an assignment is missing its member")
    provider = _pick(
        assignment, "provider", "provider_name", "providers")
    if provider is None:
        raise ValueError("an assignment is missing its provider")
    model = _pick(assignment, "model", "model_name", "models")
    if model is None:
        raise ValueError("an assignment is missing its model")
    kwargs: Dict[str, Any] = {
        "member": member, "provider": provider, "model": model,
    }
    budget_id = _pick(
        assignment, "budget_id", "budget", "budgets")
    if budget_id is not None:
        kwargs["budget_id"] = budget_id
    assignment_id = _pick(
        assignment, "assignment_id", "id", "assignment ids")
    if assignment_id is not None:
        kwargs["assignment_id"] = assignment_id
    return HeteroAssignment(**kwargs)


def build_assignment(
        assignment: Any = None, **kwargs: Any) -> HeteroAssignment:
    """Build one validated assignment.

    From a HeteroAssignment, from a mapping (the
    spellings :func:`validate_assignment` reads), or
    from field words given as keyword arguments.
    """
    if isinstance(assignment, HeteroAssignment) and not kwargs:
        return assignment
    if isinstance(assignment, dict) or assignment is None:
        merged: Dict[str, Any] = {}
        if isinstance(assignment, dict):
            merged.update(assignment)
        merged.update(kwargs)
        return validate_assignment(merged)
    raise ValueError(
        f"an assignment must be a mapping, got {assignment!r}")


# ---------------------------------------------------------------------
# The usage reading: what one member has spent, as evidence.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class HeteroReading:
    """One member's usage reading, as data.

    ``member`` is the member the reading belongs
    to; ``usage`` is the M-107 BudgetUsage it has
    spent (tokens, cost, time, commands), validated
    and judged by the budgets layer's own roads,
    never re-read here. Constructing one validates
    its shape only: judging the reading against a
    budget is the judge's job.
    """

    reading_id: Optional[str] = None
    member: str = ""
    usage: BudgetUsage = BudgetUsage()

    def __post_init__(self) -> None:
        if self.reading_id is not None:
            object.__setattr__(
                self, "reading_id",
                normalize_member_id(self.reading_id))
        object.__setattr__(
            self, "member", normalize_member_id(self.member))
        object.__setattr__(
            self, "usage", build_usage(self.usage))

    def to_record(self) -> Dict[str, Any]:
        usage = self.usage.to_record()
        return {
            "type": "hetero_reading",
            "slice": HETERO_SLICE,
            "reading_id": self.reading_id,
            "member": self.member,
            "tokens_used": usage["tokens_used"],
            "cost_used": usage["cost_used"],
            "time_used_seconds": usage["time_used_seconds"],
            "commands_used": usage["commands_used"],
        }


def validate_reading(reading: Any) -> HeteroReading:
    """Validate one usage reading into a HeteroReading.

    Accepts a HeteroReading or a mapping naming a
    ``member`` (or ``member_id``), an optional
    ``reading_id`` (or ``id``), and any of the
    M-107 usage spellings ``build_usage`` reads
    (``tokens_used``, ``cost_used``, ``time_used_seconds``,
    ``commands_used`` and their aliases), or one
    ``usage`` record on its own. Naming
    both spellings of the member or the id with
    different values refuses, and unknown keys
    refuse; the usage words themselves are read by
    the budgets layer, whose two-spellings refusal
    rides along.
    """
    if isinstance(reading, HeteroReading):
        return reading
    if not isinstance(reading, dict):
        raise ValueError(
            f"a usage reading must be a mapping, got {reading!r}")
    unknown = set(reading) - _READING_KEYS
    if unknown:
        raise ValueError(
            "unknown reading keys: %s" % ", ".join(sorted(unknown)))
    member = _pick(reading, "member", "member_id", "members")
    if member is None:
        raise ValueError("a usage reading is missing its member")
    usage_words = {
        key: value for key, value in reading.items()
        if key not in ("member", "member_id", "id", "reading_id",
                       "usage")}
    if "usage" in reading and usage_words:
        raise ValueError(
            "a usage reading names its usage twice: as a "
            "usage record and as flat usage words")
    usage = build_usage(reading["usage"]) if "usage" in reading         else build_usage(usage_words)
    kwargs: Dict[str, Any] = {
        "member": member, "usage": usage,
    }
    reading_id = _pick(reading, "reading_id", "id", "reading ids")
    if reading_id is not None:
        kwargs["reading_id"] = reading_id
    return HeteroReading(**kwargs)


def build_reading(reading: Any = None, **kwargs: Any) -> HeteroReading:
    """Build one validated usage reading.

    From a HeteroReading, from a mapping (the
    spellings :func:`validate_reading` reads), or
    from field words given as keyword arguments.
    """
    if isinstance(reading, HeteroReading) and not kwargs:
        return reading
    if isinstance(reading, dict) or reading is None:
        merged: Dict[str, Any] = {}
        if isinstance(reading, dict):
            merged.update(reading)
        merged.update(kwargs)
        return validate_reading(merged)
    raise ValueError(
        f"a usage reading must be a mapping, got {reading!r}")


# ---------------------------------------------------------------------
# The verdict and the route state: the judgements, as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class HeteroVerdict:
    """One judgement on one assignment, as data.

    ``kind`` is one of the roadmap's three kinds;
    ``member`` is the member the assignment routes;
    ``provider`` and ``model`` are the route the
    assignment names; ``title`` names the judgement
    in plain words and ``detail`` states the whole
    evidence for it. A verdict is derived from
    evidence by the judge - it is a record for the
    coordinator, never an action.
    """

    kind: str = ""
    member: str = ""
    provider: str = ""
    model: str = ""
    title: str = ""
    detail: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "kind", normalize_verdict_kind(self.kind))
        object.__setattr__(
            self, "member", normalize_member_id(self.member))
        object.__setattr__(
            self, "provider", normalize_provider(self.provider))
        object.__setattr__(
            self, "model", normalize_model(self.model))
        object.__setattr__(self, "title", _check_title(self.title))
        object.__setattr__(
            self, "detail", _check_detail(self.detail))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "hetero_verdict",
            "slice": HETERO_SLICE,
            "kind": self.kind,
            "member": self.member,
            "provider": self.provider,
            "model": self.model,
            "title": self.title,
            "detail": self.detail,
        }


def validate_verdict(verdict: Any) -> HeteroVerdict:
    """Validate one verdict into a HeteroVerdict.

    Accepts a HeteroVerdict or a mapping naming a
    ``kind`` (or ``verdict_kind``), a ``member``
    (or ``member_id``), a ``provider`` (or
    ``provider_name``), a ``model`` (or
    ``model_name``), a ``title`` and a ``detail``.
    Unknown keys refuse.
    """
    if isinstance(verdict, HeteroVerdict):
        return verdict
    if not isinstance(verdict, dict):
        raise ValueError(
            f"a verdict must be a mapping, got {verdict!r}")
    unknown = set(verdict) - _VERDICT_KEYS
    if unknown:
        raise ValueError(
            "unknown verdict keys: %s" % ", ".join(sorted(unknown)))
    kind = _pick(verdict, "kind", "verdict_kind", "kinds")
    if kind is None:
        raise ValueError("a verdict is missing its kind")
    member = _pick(verdict, "member", "member_id", "members")
    if member is None:
        raise ValueError("a verdict is missing its member")
    provider = _pick(
        verdict, "provider", "provider_name", "providers")
    if provider is None:
        raise ValueError("a verdict is missing its provider")
    model = _pick(verdict, "model", "model_name", "models")
    if model is None:
        raise ValueError("a verdict is missing its model")
    for field in ("title", "detail"):
        if field not in verdict:
            raise ValueError(f"a verdict is missing its {field}")
    return HeteroVerdict(
        kind=kind, member=member, provider=provider, model=model,
        title=verdict["title"], detail=verdict["detail"])


def build_verdict(verdict: Any = None, **kwargs: Any) -> HeteroVerdict:
    """Build one validated verdict.

    From a HeteroVerdict, from a mapping (the
    spellings :func:`validate_verdict` reads), or
    from field words given as keyword arguments.
    """
    if isinstance(verdict, HeteroVerdict) and not kwargs:
        return verdict
    if isinstance(verdict, dict) or verdict is None:
        merged: Dict[str, Any] = {}
        if isinstance(verdict, dict):
            merged.update(verdict)
        merged.update(kwargs)
        return validate_verdict(merged)
    raise ValueError(
        f"a verdict must be a mapping, got {verdict!r}")


@dataclass(frozen=True)
class RouteState:
    """One member's route, as the evidence and Part II leave it.

    ``member``, ``provider`` and ``model`` are the
    assignment's own words; ``locality`` and
    ``dialect`` are the M-019 registry's truth
    about the provider; ``switchable`` is the
    M-028 rule (the provider's dialect is one the
    live session can speak); ``context_tokens`` is
    the M-027 known context for the model, or None
    when that truth is unknown - unknown is never
    guessed; ``budget_id`` is the assignment's
    named budget (None when it names none) and
    ``budget_status`` is the M-107 standing of the
    member's reading against that budget (within /
    warning / exceeded), ``no_reading`` when no
    reading is held, or ``unbudgeted`` when the
    plan holds no budget under the named id. A
    route state is derived from evidence by the
    judge - it is never stored.
    """

    member: str = ""
    provider: str = ""
    model: str = ""
    locality: str = ""
    dialect: str = ""
    switchable: bool = False
    context_tokens: Optional[int] = None
    budget_id: Optional[str] = None
    budget_status: str = "unbudgeted"

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "member", normalize_member_id(self.member))
        object.__setattr__(
            self, "provider", normalize_provider(self.provider))
        object.__setattr__(
            self, "model", normalize_model(self.model))
        entry = _provider_entry(self.provider)
        if self.locality != entry.locality:
            raise ValueError(
                f"a route's locality must be the registry's "
                f"{entry.locality!r} for {self.provider}, "
                f"got {self.locality!r}")
        if self.dialect != entry.dialect:
            raise ValueError(
                f"a route's dialect must be the registry's "
                f"{entry.dialect!r} for {self.provider}, "
                f"got {self.dialect!r}")
        if bool(self.switchable) != (
                entry.dialect in SWITCHABLE_DIALECTS):
            raise ValueError(
                "a route is switchable exactly when its "
                "provider's dialect is one the M-028 resolver "
                "can switch to")
        if self.context_tokens is not None:
            if isinstance(self.context_tokens, bool) \
                    or not isinstance(self.context_tokens, int) \
                    or self.context_tokens <= 0:
                raise ValueError(
                    "a route's known context must be a whole "
                    f"number over zero or None, got "
                    f"{self.context_tokens!r}")
        if self.budget_id is not None:
            object.__setattr__(
                self, "budget_id",
                normalize_budget_id(self.budget_id))
        if self.budget_status not in _BUDGET_STATUSES:
            raise ValueError(
                "a route's budget status must be one of %s, "
                "got %r" % ("/".join(_BUDGET_STATUSES),
                            self.budget_status))

    @property
    def is_local(self) -> bool:
        """True when the member's models live locally (M-019)."""
        return self.locality == "local"

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "hetero_route",
            "slice": HETERO_SLICE,
            "member": self.member,
            "provider": self.provider,
            "model": self.model,
            "locality": self.locality,
            "dialect": self.dialect,
            "switchable": bool(self.switchable),
            "context_tokens": self.context_tokens,
            "budget_id": self.budget_id,
            "budget_status": self.budget_status,
        }


# ---------------------------------------------------------------------
# The judge: verdicts and routes derived from the evidence alone.
# ---------------------------------------------------------------------


def _judge(assignments: Tuple[HeteroAssignment, ...],
           budgets: Tuple[Budget, ...],
           readings: Tuple[HeteroReading, ...]) -> Tuple[
               Tuple[HeteroVerdict, ...], Tuple[RouteState, ...],
               bool]:
    budgets_by_id = {
        b.budget_id: b for b in budgets if b.budget_id is not None}
    readings_by_member = {r.member: r.usage for r in readings}
    by_kind: Dict[str, list] = {kind: [] for kind in VERDICT_KINDS}
    routes = []
    for assignment in assignments:
        entry = _provider_entry(assignment.provider)
        known = assignment.model in entry.models
        budget = budgets_by_id.get(assignment.budget_id) \
            if assignment.budget_id is not None else None
        usage = readings_by_member.get(assignment.member)
        if budget is None:
            budget_status = "unbudgeted"
        elif usage is None:
            budget_status = "no_reading"
        else:
            budget_status = judge_budget(budget, usage).status
        routes.append(RouteState(
            member=assignment.member,
            provider=assignment.provider,
            model=assignment.model,
            locality=entry.locality,
            dialect=entry.dialect,
            switchable=entry.dialect in SWITCHABLE_DIALECTS,
            context_tokens=_known_context(assignment.model),
            budget_id=assignment.budget_id,
            budget_status=budget_status))
        if not known:
            by_kind["unknown_route"].append(HeteroVerdict(
                kind="unknown_route",
                member=assignment.member,
                provider=assignment.provider,
                model=assignment.model,
                title=(
                    f"Unknown route: {assignment.member} rides "
                    f"{assignment.model} on "
                    f"{assignment.provider}"),
                detail=(
                    f"The M-019 provider registry lists "
                    f"{assignment.provider}'s models as "
                    f"{', '.join(entry.models)}, and "
                    f"{assignment.model} is not among them, "
                    f"so the route {assignment.member} is "
                    f"assigned is not a route that provider "
                    f"is known to serve, caught for the "
                    f"coordinator to name a listed model or "
                    f"a provider that lists it.")))
            continue
        if budget is None:
            named = (
                f"budget {assignment.budget_id}"
                if assignment.budget_id is not None
                else "no budget")
            by_kind["missing_budget"].append(HeteroVerdict(
                kind="missing_budget",
                member=assignment.member,
                provider=assignment.provider,
                model=assignment.model,
                title=(
                    f"Missing budget: {assignment.member} "
                    f"rides unguarded"),
                detail=(
                    f"{assignment.member}'s assignment names "
                    f"{named}, and this plan holds no budget "
                    f"under that id, so no Part V budget "
                    f"guards the member's spending on "
                    f"{assignment.provider}, caught for the "
                    f"coordinator to hold the budget the "
                    f"assignment names or name one the "
                    f"plan holds.")))
            continue
        if usage is not None \
                and judge_budget(budget, usage).status == "exceeded":
            verdict = judge_budget(budget, usage)
            exceeded = ", ".join(verdict.exceeded_dimensions)
            by_kind["over_budget"].append(HeteroVerdict(
                kind="over_budget",
                member=assignment.member,
                provider=assignment.provider,
                model=assignment.model,
                title=(
                    f"Over budget: {assignment.member} past "
                    f"{assignment.budget_id}"),
                detail=(
                    f"The M-107 judge reads "
                    f"{assignment.member}'s usage against "
                    f"budget {assignment.budget_id} as "
                    f"exceeded on {exceeded}, so the "
                    f"member's line on "
                    f"{assignment.provider} has spent past "
                    f"the budget its assignment names, "
                    f"caught for the coordinator to pause "
                    f"the line or raise the budget - this "
                    f"slice bills nothing itself.")))
    verdicts: list = []
    for kind in VERDICT_KINDS:
        verdicts.extend(by_kind[kind])
    pairs = {(a.provider, a.model) for a in assignments}
    return tuple(verdicts), tuple(routes), len(pairs) >= 2


def _evidence_from(source: Any) -> Tuple[
        Tuple[HeteroAssignment, ...], Tuple[Budget, ...],
        Tuple[HeteroReading, ...]]:
    if isinstance(source, HeterogeneousCrew):
        return source.assignments, source.budgets, source.readings
    if isinstance(source, HeterogeneousCrewRegistry):
        return (source.list_assignments(), source.list_budgets(),
                source.list_readings())
    if isinstance(source, dict):
        unknown = set(source) - {
            "assignments", "budgets", "readings"}
        if unknown:
            raise ValueError(
                "unknown evidence keys: %s"
                % ", ".join(sorted(unknown)))
        raw_assignments = source.get("assignments") or ()
        raw_budgets = source.get("budgets") or ()
        raw_readings = source.get("readings") or ()
        for what, raw in (("assignments", raw_assignments),
                          ("budgets", raw_budgets),
                          ("readings", raw_readings)):
            if isinstance(raw, (str, bytes)) \
                    or not isinstance(raw, (list, tuple)):
                raise ValueError(
                    f"evidence {what} must be a list")
        return (
            tuple(build_assignment(a) for a in raw_assignments),
            tuple(build_budget(b) for b in raw_budgets),
            tuple(build_reading(r) for r in raw_readings))
    raise ValueError(f"crew evidence is needed, got {source!r}")


def judge_hetero(source: Any) -> Tuple[HeteroVerdict, ...]:
    """Every verdict in *source*'s evidence, in fixed order.

    Accepts a HeterogeneousCrew, a
    HeterogeneousCrewRegistry or a mapping with
    ``assignments``, ``budgets`` and ``readings``
    lists. The mechanical judge of the slice, as
    data only: unknown-route verdicts first (in
    assignment order), then missing-budget
    verdicts, then over-budget verdicts - the same
    evidence always yields the same verdicts.
    """
    assignments, budgets, readings = _evidence_from(source)
    verdicts, _routes, _hetero = _judge(
        assignments, budgets, readings)
    return verdicts


@dataclass(frozen=True)
class HeteroReport:
    """One report of verdicts and routes, derived from evidence.

    ``verdicts`` are the judgements the judge
    derived, in judgement order; ``routes`` are the
    state of every assigned member's route, in
    assignment order; ``heterogeneous`` is True
    when the assignments hold at least two distinct
    provider/model pairs; ``providers``, ``models``
    and ``localities`` are the distinct words the
    routes ride, in first-seen order. Constructing
    one validates it: every verdict is a verdict
    and every route a route state.
    """

    verdicts: Tuple[HeteroVerdict, ...] = ()
    routes: Tuple[RouteState, ...] = ()
    heterogeneous: bool = False
    providers: Tuple[str, ...] = ()
    models: Tuple[str, ...] = ()
    localities: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field in ("verdicts", "routes", "providers",
                      "models", "localities"):
            value = getattr(self, field)
            if isinstance(value, (str, bytes)) \
                    or not isinstance(value, (list, tuple)):
                raise ValueError(
                    f"a report's {field} must be a list, "
                    f"got {value!r}")
        object.__setattr__(self, "verdicts", tuple(
            v if isinstance(v, HeteroVerdict)
            else validate_verdict(v) for v in self.verdicts))
        routes = []
        for route in self.routes:
            if not isinstance(route, RouteState):
                raise ValueError(
                    f"a report's routes must be route states, "
                    f"got {route!r}")
            routes.append(route)
        object.__setattr__(self, "routes", tuple(routes))
        object.__setattr__(self, "providers", tuple(
            normalize_provider(p) for p in self.providers))
        object.__setattr__(self, "models", tuple(
            normalize_model(m) for m in self.models))
        for locality in self.localities:
            if locality not in ("local", "remote"):
                raise ValueError(
                    f"a report's localities must be local or "
                    f"remote, got {locality!r}")
        object.__setattr__(
            self, "localities", tuple(self.localities))
        pairs = {(r.provider, r.model) for r in self.routes}
        if bool(self.heterogeneous) != (len(pairs) >= 2):
            raise ValueError(
                "a report is heterogeneous exactly when its "
                "routes hold at least two distinct "
                "provider/model pairs")

    @property
    def is_clean(self) -> bool:
        """True when the evidence holds no verdict."""
        return not self.verdicts

    def by_kind(self, kind: Any) -> Tuple[HeteroVerdict, ...]:
        """Every verdict of one kind, in report order."""
        wanted = normalize_verdict_kind(kind)
        return tuple(v for v in self.verdicts if v.kind == wanted)

    def for_member(self, member: Any) -> Tuple[HeteroVerdict, ...]:
        """Every verdict on one member's route, in order."""
        wanted = normalize_member_id(member)
        return tuple(v for v in self.verdicts if v.member == wanted)

    def route_for(self, member: Any) -> RouteState:
        """The one route one member rides; unknown raises."""
        wanted = normalize_member_id(member)
        for route in self.routes:
            if route.member == wanted:
                return route
        raise KeyError(f"no route for the member: {wanted!r}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "hetero_report",
            "slice": HETERO_SLICE,
            "count": len(self.verdicts),
            "clean": self.is_clean,
            "heterogeneous": bool(self.heterogeneous),
            "providers": list(self.providers),
            "models": list(self.models),
            "localities": list(self.localities),
            "unknown_route": len(self.by_kind("unknown_route")),
            "missing_budget": len(self.by_kind("missing_budget")),
            "over_budget": len(self.by_kind("over_budget")),
            "verdicts": [v.to_record() for v in self.verdicts],
            "routes": [r.to_record() for r in self.routes],
        }


def validate_report(source: Any, report: Any) -> list:
    """Every problem in a claimed report of *source*, as strings.

    An empty list means the report answers the
    source exactly: every verdict and every route
    the evidence yields, in judgement order, and
    nothing else - a report missing a verdict, or
    holding one the evidence does not hold, is
    named.
    """
    if not isinstance(report, HeteroReport):
        return [f"a hetero report is needed, got {report!r}"]
    try:
        assignments, budgets, readings = _evidence_from(source)
    except ValueError as exc:
        return [str(exc)]
    wanted_verdicts, wanted_routes, _hetero = _judge(
        assignments, budgets, readings)
    problems = []
    if tuple(report.verdicts) != wanted_verdicts \
            or tuple(report.routes) != wanted_routes:
        problems.append(
            "the report does not hold exactly the evidence's "
            "verdicts and routes, in judgement order: the "
            "report must catch every verdict the evidence "
            "holds, and no other verdict")
    return problems


def _report_from(assignments, budgets, readings) -> HeteroReport:
    verdicts, routes, heterogeneous = _judge(
        assignments, budgets, readings)
    providers, models, localities = [], [], []
    for route in routes:
        if route.provider not in providers:
            providers.append(route.provider)
        if route.model not in models:
            models.append(route.model)
        if route.locality not in localities:
            localities.append(route.locality)
    return HeteroReport(
        verdicts=verdicts, routes=routes,
        heterogeneous=heterogeneous,
        providers=tuple(providers), models=tuple(models),
        localities=tuple(localities))


# ---------------------------------------------------------------------
# The crew plan: the evidence one file holds, under one keeper.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class HeterogeneousCrew:
    """A whole crew plan: the evidence one file holds.

    ``keeper`` is the member id of the one who
    keeps the plan - in the shipped example the
    architect, the roadmap's Claude Architect.
    Constructing one holds the plan law: at least
    one assignment, no member assigned twice, no
    budget id held twice (and every budget names
    its id, so an assignment can name it), and no
    two readings for one member.
    """

    assignments: Tuple[HeteroAssignment, ...] = ()
    budgets: Tuple[Budget, ...] = ()
    readings: Tuple[HeteroReading, ...] = ()
    keeper: str = ""
    plan_note: str = ""

    def __post_init__(self) -> None:
        for field in ("assignments", "budgets", "readings"):
            value = getattr(self, field)
            if isinstance(value, (str, bytes)) \
                    or not isinstance(value, (list, tuple)):
                raise ValueError(
                    f"a crew plan's {field} must be a list, "
                    f"got {value!r}")
        assignments = tuple(
            a if isinstance(a, HeteroAssignment)
            else validate_assignment(a)
            for a in self.assignments)
        budgets = tuple(
            b if isinstance(b, Budget) else build_budget(b)
            for b in self.budgets)
        readings = tuple(
            r if isinstance(r, HeteroReading)
            else validate_reading(r) for r in self.readings)
        if not assignments:
            raise ValueError(
                "a crew plan must hold at least one assignment")
        seen_members = set()
        for assignment in assignments:
            if assignment.member in seen_members:
                raise ValueError(
                    f"a member is assigned twice: "
                    f"{assignment.member} holds two assignments")
            seen_members.add(assignment.member)
        seen_budgets = set()
        for budget in budgets:
            if budget.budget_id is None:
                raise ValueError(
                    "a crew plan's budgets must name their "
                    "budget id, so an assignment can name them")
            if budget.budget_id in seen_budgets:
                raise ValueError(
                    f"a budget id is held twice: "
                    f"{budget.budget_id}")
            seen_budgets.add(budget.budget_id)
        seen_readings = set()
        for reading in readings:
            if reading.member in seen_readings:
                raise ValueError(
                    f"a member holds two readings: "
                    f"{reading.member}")
            seen_readings.add(reading.member)
        object.__setattr__(self, "assignments", assignments)
        object.__setattr__(self, "budgets", budgets)
        object.__setattr__(self, "readings", readings)
        object.__setattr__(
            self, "keeper", normalize_member_id(self.keeper))
        object.__setattr__(
            self, "plan_note", str(self.plan_note or ""))

    def report(self) -> HeteroReport:
        """The report this crew plan's evidence yields."""
        return _report_from(
            self.assignments, self.budgets, self.readings)

    def assignments_for(self, member: Any) -> Tuple[
            HeteroAssignment, ...]:
        """Every assignment one member holds (at most one)."""
        wanted = normalize_member_id(member)
        return tuple(
            a for a in self.assignments if a.member == wanted)

    def budget_for(self, budget_id: Any) -> Budget:
        """The one budget one id names; unknown raises."""
        wanted = normalize_budget_id(budget_id)
        for budget in self.budgets:
            if budget.budget_id == wanted:
                return budget
        raise KeyError(f"no budget held under the id: {wanted!r}")

    def readings_for(self, member: Any) -> Tuple[HeteroReading, ...]:
        """Every reading one member holds (at most one)."""
        wanted = normalize_member_id(member)
        return tuple(
            r for r in self.readings if r.member == wanted)


def _example_problems(parsed_assignments, parsed_budgets,
                      parsed_readings, keeper) -> list:
    problems = []
    held_assignments = tuple(
        (a.member, a.provider, a.model, a.budget_id)
        for a in parsed_assignments)
    if held_assignments != _EXAMPLE_ASSIGNMENTS:
        problems.append(
            "the shipped example plan must hold exactly "
            "the four assignments in file order, with "
            "their members, providers, models and budgets")
    held_budgets = tuple(
        (b.budget_id, b.scope, b.token_limit, b.cost_limit,
         b.command_limit) for b in parsed_budgets)
    if held_budgets != _EXAMPLE_BUDGETS:
        problems.append(
            "the shipped example plan must hold exactly "
            "the two budgets in file order, with their "
            "ids, scopes and limits")
    held_readings = tuple(
        (r.member, r.usage.tokens_used, r.usage.cost_used,
         r.usage.commands_used) for r in parsed_readings)
    if held_readings != _EXAMPLE_READINGS:
        problems.append(
            "the shipped example plan must hold exactly "
            "the two readings in file order, with their "
            "members and amounts")
    if keeper is not None and keeper != "architect":
        problems.append(
            "the shipped example plan is kept by the "
            "architect")
    if held_assignments == _EXAMPLE_ASSIGNMENTS \
            and held_budgets == _EXAMPLE_BUDGETS \
            and held_readings == _EXAMPLE_READINGS:
        report = _report_from(
            tuple(parsed_assignments), tuple(parsed_budgets),
            tuple(parsed_readings))
        kinds = [v.kind for v in report.verdicts]
        if kinds != ["unknown_route", "missing_budget",
                     "over_budget"]:
            problems.append(
                "the shipped example plan must yield "
                "exactly three verdicts, one of each "
                "kind, in judgement order")
        if not report.heterogeneous \
                or set(report.localities) != {"local", "remote"}:
            problems.append(
                "the shipped example plan must be "
                "heterogeneous across local and remote "
                "providers")
        architect = report.route_for("architect")
        if architect.provider != "anthropic" \
                or architect.locality != "remote" \
                or architect.context_tokens != 200000 \
                or architect.budget_status != "within":
            problems.append(
                "the shipped example plan must leave the "
                "architect on anthropic, remote, with a "
                "known context of 200000 and its budget "
                "within")
        forge = report.route_for("forge_worker")
        if forge.provider != "ollama" \
                or forge.locality != "local" \
                or forge.context_tokens != 131072 \
                or forge.budget_status != "exceeded":
            problems.append(
                "the shipped example plan must leave the "
                "forge_worker on ollama, local, with a "
                "known context of 131072 and its budget "
                "exceeded")
    return problems


def validate_plan(data: Any, *,
                  require_example: bool = False) -> list:
    """Every problem in a crew plan mapping, as plain strings.

    An empty list means the crew plan is
    well-formed. With ``require_example`` the file
    must be exactly the shipped example: the four
    assignments, two budgets and two readings in
    file order, kept by the architect - and the
    report derived from it must hold exactly its
    three verdicts, one of each kind, heterogeneous
    across local and remote providers, with the
    architect's route within budget and the forge
    worker's exceeded (the check the shipped file
    is held to; a real plan's file is read without
    it).
    """
    if not isinstance(data, dict):
        return [f"a crew plan must be a mapping, got {data!r}"]
    problems = []
    unknown = set(data) - _PLAN_KEYS
    if unknown:
        problems.append(
            "unknown crew plan keys: %s"
            % ", ".join(sorted(unknown)))
    if data.get("schema") != HETERO_SCHEMA:
        problems.append(
            f"a crew plan's schema must be "
            f"{HETERO_SCHEMA!r}, got {data.get('schema')!r}")
    if data.get("slice") != HETERO_SLICE:
        problems.append(
            f"a crew plan's slice must be "
            f"{HETERO_SLICE!r}, got {data.get('slice')!r}")
    keeper = None
    if data.get("keeper") is None:
        problems.append("a crew plan is missing its keeper")
    else:
        try:
            keeper = normalize_member_id(data["keeper"])
        except ValueError as exc:
            problems.append(f"keeper: {exc}")
    raw_assignments = data.get("assignments")
    raw_budgets = data.get("budgets")
    raw_readings = data.get("readings")
    if not isinstance(raw_assignments, list):
        problems.append(
            "a crew plan must hold an assignments list")
        raw_assignments = []
    if raw_budgets is None:
        raw_budgets = []
    if not isinstance(raw_budgets, list):
        problems.append("a crew plan must hold a budgets list")
        raw_budgets = []
    if raw_readings is None:
        raw_readings = []
    if not isinstance(raw_readings, list):
        problems.append("a crew plan must hold a readings list")
        raw_readings = []
    if isinstance(raw_assignments, list) and not raw_assignments:
        problems.append(
            "a crew plan must hold at least one assignment")
    parsed_assignments = []
    for index, entry in enumerate(raw_assignments):
        try:
            parsed_assignments.append(validate_assignment(entry))
        except ValueError as exc:
            problems.append(f"assignment {index + 1}: {exc}")
    parsed_budgets = []
    for index, entry in enumerate(raw_budgets):
        try:
            parsed_budgets.append(build_budget(entry))
        except ValueError as exc:
            problems.append(f"budget {index + 1}: {exc}")
    parsed_readings = []
    for index, entry in enumerate(raw_readings):
        try:
            parsed_readings.append(validate_reading(entry))
        except ValueError as exc:
            problems.append(f"reading {index + 1}: {exc}")
    if len(parsed_assignments) == len(raw_assignments):
        seen = set()
        for assignment in parsed_assignments:
            if assignment.member in seen:
                problems.append(
                    f"a member is assigned twice: "
                    f"{assignment.member} holds two assignments")
            seen.add(assignment.member)
    if len(parsed_budgets) == len(raw_budgets):
        seen = set()
        for budget in parsed_budgets:
            if budget.budget_id is None:
                problems.append(
                    "a crew plan's budgets must name their "
                    "budget id, so an assignment can name them")
            elif budget.budget_id in seen:
                problems.append(
                    f"a budget id is held twice: "
                    f"{budget.budget_id}")
            seen.add(budget.budget_id)
    if len(parsed_readings) == len(raw_readings):
        seen = set()
        for reading in parsed_readings:
            if reading.member in seen:
                problems.append(
                    f"a member holds two readings: "
                    f"{reading.member}")
            seen.add(reading.member)
    if require_example \
            and len(parsed_assignments) == len(raw_assignments) \
            and len(parsed_budgets) == len(raw_budgets) \
            and len(parsed_readings) == len(raw_readings):
        problems.extend(_example_problems(
            parsed_assignments, parsed_budgets,
            parsed_readings, keeper))
    return problems


def _plan_from(data: Any, *, require_example: bool) -> HeterogeneousCrew:
    problems = validate_plan(data, require_example=require_example)
    if problems:
        raise ValidationError(
            "invalid crew plan: " + "; ".join(problems))
    assert isinstance(data, dict)
    return HeterogeneousCrew(
        assignments=tuple(
            validate_assignment(entry)
            for entry in data["assignments"]),
        budgets=tuple(
            build_budget(entry)
            for entry in data.get("budgets") or []),
        readings=tuple(
            validate_reading(entry)
            for entry in data.get("readings") or []),
        keeper=data["keeper"],
        plan_note=str(data.get("plan_note") or ""))


def load_heterogeneous_crew(
        data: Optional[Dict[str, Any]] = None) -> HeterogeneousCrew:
    """Load and validate the shipped example plan (or *data*).

    The shipped file is held to the example check:
    exactly the four assignments, two budgets and
    two readings, kept by the architect, yielding
    exactly its three verdicts, one of each kind.
    Raises :class:`ValidationError` listing every
    problem when the record is not a well-formed
    crew plan.
    """
    raw = data if data is not None else load_resource(
        HETERO_RESOURCE)
    return _plan_from(raw, require_example=True)


def load_heterogeneous_crew_file(path: Any) -> HeterogeneousCrew:
    """Load and validate a crew plan from a file at *path*.

    This is the road a real crew plan arrives by:
    any file in the plan shape, anywhere on disk,
    validated whole - a malformed file raises
    :class:`ValidationError` naming the problem,
    and a missing file raises ``FileNotFoundError``.
    The example check is not held: a plan may hold
    a single assignment and no budgets or readings
    yet.
    """
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _plan_from(raw, require_example=False)


# ---------------------------------------------------------------------
# The registry model: evidence held in registration order, ids
# deterministic. A registry refuses a supplied id already held, a
# member assigned twice, a budget id held twice and two readings for
# one member: repetition here is a second route for one member, not
# two pieces of evidence, so it is refused, never hidden.
# ---------------------------------------------------------------------


class HeterogeneousCrewRegistry:
    """An in-memory registry of heterogeneous crew evidence.

    Assignments, budgets and readings are held in
    registration order. Ids are deterministic: a
    caller-supplied id is used as given, and an
    unsupplied id is the next ``assignment-N`` /
    ``reading-N`` in sequence, skipping any number
    a supplied id already took (budgets carry their
    own M-107 ids). A supplied id already held
    refuses. A plan registered whole refuses a
    duplicated member, budget id or reading exactly
    as the plan does. Storage beyond memory (a
    session's journal, a file) is the agent layer's
    concern; this model is neutral.
    """

    def __init__(self) -> None:
        self._assignments: Dict[str, HeteroAssignment] = {}
        self._budgets: Dict[str, Budget] = {}
        self._readings: Dict[str, HeteroReading] = {}
        self._next_assignment = 1
        self._next_reading = 1

    def _fresh_assignment_id(self) -> str:
        while f"assignment-{self._next_assignment}" in self._assignments:
            self._next_assignment += 1
        assignment_id = f"assignment-{self._next_assignment}"
        self._next_assignment += 1
        return assignment_id

    def _fresh_reading_id(self) -> str:
        while f"reading-{self._next_reading}" in self._readings:
            self._next_reading += 1
        reading_id = f"reading-{self._next_reading}"
        self._next_reading += 1
        return reading_id

    def register_assignment(self, assignment: Any) -> HeteroAssignment:
        """Register one assignment and hold it."""
        validated = build_assignment(assignment)
        for held in self._assignments.values():
            if held.member == validated.member:
                raise ValueError(
                    f"a member is assigned twice: "
                    f"{validated.member} holds two assignments")
        if validated.assignment_id is not None \
                and validated.assignment_id in self._assignments:
            raise ValueError(
                f"an assignment named "
                f"{validated.assignment_id!r} already exists")
        if validated.assignment_id is None:
            validated = replace(
                validated,
                assignment_id=self._fresh_assignment_id())
        self._assignments[validated.assignment_id] = validated
        return validated

    def register_budget(self, budget: Any) -> Budget:
        """Register one Part V budget and hold it."""
        validated = build_budget(budget)
        if validated.budget_id is None:
            raise ValueError(
                "a held budget must name its budget id, so "
                "an assignment can name it")
        if validated.budget_id in self._budgets:
            raise ValueError(
                f"a budget id is held twice: "
                f"{validated.budget_id}")
        self._budgets[validated.budget_id] = validated
        return validated

    def register_reading(self, reading: Any) -> HeteroReading:
        """Register one usage reading and hold it."""
        validated = build_reading(reading)
        for held in self._readings.values():
            if held.member == validated.member:
                raise ValueError(
                    f"a member holds two readings: "
                    f"{validated.member}")
        if validated.reading_id is not None \
                and validated.reading_id in self._readings:
            raise ValueError(
                f"a reading named {validated.reading_id!r} "
                f"already exists")
        if validated.reading_id is None:
            validated = replace(
                validated, reading_id=self._fresh_reading_id())
        self._readings[validated.reading_id] = validated
        return validated

    def register_plan(self, plan: Any) -> Tuple[
            Tuple[HeteroAssignment, ...], Tuple[Budget, ...],
            Tuple[HeteroReading, ...]]:
        """Register every piece of one plan's evidence, in order."""
        if not isinstance(plan, HeterogeneousCrew):
            raise ValueError(f"a crew plan is needed, got {plan!r}")
        budgets = tuple(
            self.register_budget(b) for b in plan.budgets)
        assignments = tuple(
            self.register_assignment(a) for a in plan.assignments)
        readings = tuple(
            self.register_reading(r) for r in plan.readings)
        return assignments, budgets, readings

    def get_assignment(self, assignment_id: Any) -> HeteroAssignment:
        """The assignment one id names; an unknown id raises."""
        wanted = normalize_member_id(assignment_id)
        if wanted not in self._assignments:
            raise KeyError(f"unknown assignment: {wanted!r}")
        return self._assignments[wanted]

    def get_budget(self, budget_id: Any) -> Budget:
        """The budget one id names; an unknown id raises."""
        wanted = normalize_budget_id(budget_id)
        if wanted not in self._budgets:
            raise KeyError(f"unknown budget: {wanted!r}")
        return self._budgets[wanted]

    def get_reading(self, reading_id: Any) -> HeteroReading:
        """The reading one id names; an unknown id raises."""
        wanted = normalize_member_id(reading_id)
        if wanted not in self._readings:
            raise KeyError(f"unknown reading: {wanted!r}")
        return self._readings[wanted]

    def list_assignments(self) -> Tuple[HeteroAssignment, ...]:
        """Every held assignment, in registration order."""
        return tuple(self._assignments.values())

    def list_budgets(self) -> Tuple[Budget, ...]:
        """Every held budget, in registration order."""
        return tuple(self._budgets.values())

    def list_readings(self) -> Tuple[HeteroReading, ...]:
        """Every held reading, in registration order."""
        return tuple(self._readings.values())

    def verdicts(self) -> Tuple[HeteroVerdict, ...]:
        """Every verdict in the held evidence, in judgement order."""
        return judge_hetero(self)

    def report(self) -> HeteroReport:
        """The report the held evidence yields."""
        return _report_from(
            self.list_assignments(), self.list_budgets(),
            self.list_readings())

    def for_member(self, member: Any) -> Tuple[HeteroVerdict, ...]:
        """Every held verdict on one member's route, in order."""
        return self.report().for_member(member)


# ---------------------------------------------------------------------
# Crew news, shaped as session records.
# ---------------------------------------------------------------------


def assignment_record(assignment: Any) -> Dict[str, Any]:
    """The session-news record of one assignment."""
    current = assignment if isinstance(
        assignment, HeteroAssignment) else build_assignment(assignment)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"{current.member} rides {current.model} on "
        f"{current.provider}.")
    return record


def reading_record(reading: Any) -> Dict[str, Any]:
    """The session-news record of one usage reading."""
    current = reading if isinstance(
        reading, HeteroReading) else build_reading(reading)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"{current.member} reading held: "
        f"{record['tokens_used']} tokens, "
        f"{record['commands_used']} commands spent.")
    return record


def plain_words(verdict: Any) -> str:
    """One verdict, in one plain sentence."""
    current = verdict if isinstance(verdict, HeteroVerdict) \
        else build_verdict(verdict)
    return f"{current.title} - {current.detail}"


def verdict_record(verdict: Any) -> Dict[str, Any]:
    """The session-news record of one verdict.

    Carries the verdict's whole record plus a
    one-line plain headline, so a judgement made in
    a session is news with its shape attached, never
    a bare log line.
    """
    current = verdict if isinstance(verdict, HeteroVerdict) \
        else build_verdict(verdict)
    record = current.to_record()
    record["news"] = True
    record["headline"] = plain_words(current)
    return record


def report_plain_words(report: Any) -> str:
    """One hetero report, in one plain sentence."""
    current = report if isinstance(report, HeteroReport) \
        else HeteroReport(verdicts=report)
    if current.is_clean:
        return (
            "The crew plan is clean: every route is "
            "listed and every member rides within "
            "budget.")
    caught = "; ".join(v.title for v in current.verdicts)
    return (
        f"{len(current.verdicts)} verdicts stand for the "
        f"coordinator: {caught}.")


def report_record(report: Any) -> Dict[str, Any]:
    """The session-news record of one hetero report.

    ONE record holding every verdict and every
    route with its full evidence - the report
    itself, as news for the coordinator.
    """
    current = report if isinstance(report, HeteroReport) \
        else HeteroReport(verdicts=report)
    record = current.to_record()
    record["news"] = True
    record["headline"] = report_plain_words(current)
    return record


# ---------------------------------------------------------------------
# The /hetero surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------


def format_verdict(verdict: Any) -> str:
    """One verdict, in plain words."""
    current = verdict if isinstance(verdict, HeteroVerdict) \
        else build_verdict(verdict)
    return f"  {current.kind}: {plain_words(current)}"


def _selected_verdicts(source: Any) -> Tuple[HeteroVerdict, ...]:
    if source is None:
        return load_heterogeneous_crew().report().verdicts
    if isinstance(source, HeteroReport):
        return source.verdicts
    if isinstance(source, (HeterogeneousCrew,
                           HeterogeneousCrewRegistry, dict)):
        return judge_hetero(source)
    if isinstance(source, (str, bytes)) \
            or not isinstance(source, (list, tuple)):
        raise ValueError("verdicts must be a list of verdicts")
    return tuple(
        v if isinstance(v, HeteroVerdict) else build_verdict(v)
        for v in source)


def format_verdicts(source: Any = None) -> str:
    """The verdicts, in plain words, in judgement order.

    Accepts a list of verdicts, a HeteroReport, a
    HeterogeneousCrew or a HeterogeneousCrewRegistry.
    With no source the shipped example plan's
    verdicts are shown. With no verdicts at all the
    text states the crew plan is clean, plainly.
    """
    selected = _selected_verdicts(source)
    if not selected:
        return ("Heterogeneous crews: clean. No unknown "
                "route, missing budget or over-budget "
                "member stands.")
    lines = [
        f"Heterogeneous crews: {len(selected)} verdicts "
        f"stand for the coordinator."]
    for verdict in selected:
        lines.append(format_verdict(verdict))
    return "\n".join(lines)


def _selected_routes(source: Any) -> Tuple[RouteState, ...]:
    if source is None:
        return load_heterogeneous_crew().report().routes
    if isinstance(source, HeteroReport):
        return source.routes
    if isinstance(source, HeterogeneousCrew):
        return source.report().routes
    if isinstance(source, HeterogeneousCrewRegistry):
        return source.report().routes
    raise ValueError(f"crew routes are needed, got {source!r}")


def format_routes(source: Any = None) -> str:
    """Every route's state, in plain words, in assignment order.

    Accepts a HeteroReport, a HeterogeneousCrew or a
    HeterogeneousCrewRegistry. With no source the
    shipped example plan's routes are shown.
    """
    selected = _selected_routes(source)
    if not selected:
        return "Crew routes: no assignment is held yet."
    rendered = ["Crew routes:"]
    for route in selected:
        where = "local" if route.is_local else "remote"
        context = (
            f"context {route.context_tokens}"
            if route.context_tokens is not None
            else "context unknown")
        rendered.append(
            f"  {route.member}: {route.model} on "
            f"{route.provider} ({where}, {context}); "
            f"budget {route.budget_status}.")
    return "\n".join(rendered)


def format_kinds() -> str:
    """The verdict kinds, in plain words."""
    return (
        "Verdict kinds: unknown_route (the provider "
        "does not list the model the assignment "
        "names, per the M-019 registry), "
        "missing_budget (the assignment names no "
        "budget this plan holds), over_budget (the "
        "member's usage reading is judged exceeded "
        "by the M-107 budget judge against the "
        "budget its assignment names).")


def format_hetero_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /hetero.

    With nothing named, the shipped example plan's
    verdicts and routes are shown - the example this
    slice ships - so the screen is never empty.
    There is no Part VIII board yet; this screen is
    where the verdicts are visible.
    """
    lines = ["Heterogeneous crews (M-129) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_verdicts(source))
    lines.append("")
    lines.append(format_routes(source))
    lines.append("")
    lines.append(format_kinds())
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_hetero_args(args: Any) -> Tuple[str, Optional[str]]:
    """Parse the /hetero grammar both surfaces share.

    No words (or ``show`` / ``list`` / ``verdicts``)
    shows the verdicts; ``show <member>`` and a bare
    member id show one member's verdicts; ``routes``
    shows every route's state; ``kinds`` asks for
    the kinds. Anything else is a usage error naming
    the grammar. Returns ``(action, value-or-None)``.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None \
        else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() in ("show", "list", "verdicts"):
        return ("show", None)
    words = text.split()
    head = words[0].lower()
    if head == "show" and len(words) == 2:
        try:
            return ("show", normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "routes" and len(words) == 1:
        return ("routes", None)
    if head == "kinds" and len(words) == 1:
        return ("kinds", None)
    if head in ("show", "kinds", "routes", "list", "verdicts"):
        raise ValueError(USAGE)
    if len(words) == 1:
        try:
            return ("show", normalize_member_id(words[0]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
