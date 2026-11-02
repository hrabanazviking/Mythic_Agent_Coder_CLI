"""Cost-aware routing (All-Features roadmap slice M-031).

Part II — The Provider Ocean — continues here. With ``mythic
costs`` data, the router can prefer the cheaper *adequate* model
for a task class — a setting, off by default, explained in plain
words.

What already shipped, and what this slice adds:

* ``mythic costs`` (``mythic_agent.core.costs``) already prices
  models against its PRICING table and keeps the per-workspace
  ledger; M-027 already stores capability truth per model
  (context, tool use, vision, reasoning — known, or honestly
  unknown). M-028 switches the session's model with journal +
  reason; M-029 routes per crew office; M-030 chains fallback
  doors with standing permission.
* This slice is the router that reads those three truths
  together: for a named *task class* it looks at the doors the
  user has already configured — the current selection, the
  M-030 fallback chain, and the M-029 role routes, never a door
  the user did not choose — keeps only the doors that are
  *adequate* for the class (capability truth says so) and the
  live session can actually speak, prices each with the costs
  table, and prefers the cheapest adequate door cheaper than
  the current one. The pure decision lives here; the agent
  layer owns applying it (through M-028's journaled switch).

Honesty rules, enforced here and pinned by the slice's tests:

* **Off by default.** ``cost_routing`` defaults to False; with
  it off the router changes nothing — it only explains itself.
* **Unknown price is never "cheaper".** A model the costs table
  does not price has no provable cost, so it can never be
  preferred on price; and when the *current* model is adequate
  but its price is unknown, no saving over it can be proven, so
  the current door stays. (A current door that is not known to
  be adequate at all yields on adequacy alone — cost was never
  the question there.)
* **Unknown capability is never "adequate".** Where a task
  class requires a capability (tool use, vision, reasoning, a
  known context size), only a known-true record counts — a
  null (unknown) record is not adequate, per M-027's law.
* **A tie keeps the current door.** Equal price is no saving.
* **Every decision carries its plain-words reason** — why this
  door, or why the current door stays — so a routed switch is
  explained, never silent. The applied switch itself rides
  M-028's ``model_switched`` journal event with that reason.
* A malformed stored setting (non-bool) raises instead of
  being guessed at, exactly like M-030's permission.
"""

from __future__ import annotations

__all__ = [
    "PLAIN_EXPLANATION",
    "ROUTING_SLICE",
    "SETTING_KEY",
    "TASK_CLASSES",
    "Any",
    "CostDecision",
    "CostRoutingChange",
    "Dict",
    "Door",
    "List",
    "Optional",
    "TASK_CLASS_IDS",
    "TaskClass",
    "Tuple",
    "candidate_doors",
    "choose_route",
    "door_adequate",
    "enabled_from_config",
    "format_cost_change",
    "format_cost_routing",
    "format_decision",
    "get_task_class",
    "parse_cost_args",
    "set_enabled",
    "unit_cost",
]

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .costs import price as _cost_price
from .fallback_chain import chain_from_config
from .model_capabilities import ModelCapability, load_capabilities
from .model_switch import SWITCHABLE_DIALECTS, infer_provider
from .provider_registry import load_registry
from .role_routing import routes_from_config

#: The slice that owns this module.
ROUTING_SLICE = "M-031"

#: The config key the setting lives under.
SETTING_KEY = "cost_routing"

#: The setting explained in plain words — the sentence every
#: surface shows. Cost-aware routing never stirs uninvited, and
#: it never claims a saving it cannot prove from the costs data.
PLAIN_EXPLANATION = (
    "Cost-aware routing: when this setting is on, Mythic may "
    "prefer a cheaper model that is still good enough for the "
    "kind of work at hand — for example a cheaper model that "
    "can still use tools for coding work. It only ever chooses "
    "between doors you have already set up (your current door, "
    "your fallback chain, and your role routes), only when the "
    "cheaper model's price is known from the costs data and "
    "its abilities are known to fit the work, and it always "
    "says why. It is off by default: turn it on with "
    "/costroute on."
)


@dataclass(frozen=True)
class TaskClass:
    """One kind of work the router can price-choose for.

    ``required_flag`` names a capability flag that must be
    known-true (M-027 tri-state) for a model to be adequate, or
    ``None``; ``min_context`` names a known context size a model
    must reach, or ``None``. A class with neither requires only
    that the model exists — any priced door is adequate.
    """

    id: str
    title: str
    plain: str
    required_flag: Optional[str] = None
    min_context: Optional[int] = None


#: The task classes, in router order. Each requirement is a
#: capability M-027 records per model — nothing is required
#: that the capability truth cannot answer honestly.
TASK_CLASSES: Tuple[TaskClass, ...] = (
    TaskClass(
        "general", "General work",
        "Ordinary work with no special ability required; the "
        "cheapest priced door is adequate."),
    TaskClass(
        "coding", "Coding work",
        "Writing and editing code with tools; the model must "
        "be known to support tool use.",
        required_flag="tool_calling"),
    TaskClass(
        "reasoning", "Deep reasoning",
        "Hard thinking — architecture, proofs, tricky bugs; "
        "the model must be known to reason.",
        required_flag="reasoning"),
    TaskClass(
        "vision", "Vision work",
        "Work that looks at images; the model must be known "
        "to see.",
        required_flag="vision"),
    TaskClass(
        "long_context", "Long-context work",
        "Work over very large inputs; the model's known "
        "context must reach at least 200,000 tokens.",
        min_context=200_000),
)

#: The task class ids, in router order.
TASK_CLASS_IDS: Tuple[str, ...] = tuple(t.id for t in TASK_CLASSES)


def get_task_class(task_class: Any) -> TaskClass:
    """The task class named *task_class* (ValueError if unknown)."""
    if not isinstance(task_class, str) or not task_class.strip():
        raise ValueError(
            "Name a task class: " + ", ".join(TASK_CLASS_IDS) + ".")
    key = task_class.strip().lower()
    for entry in TASK_CLASSES:
        if entry.id == key:
            return entry
    raise ValueError(
        f"Unknown task class {task_class!r}; the classes are: "
        + ", ".join(TASK_CLASS_IDS) + ".")


@dataclass(frozen=True)
class Door:
    """One configured door the router may consider.

    ``provider`` is inferred from the door by exact endpoint
    equality, or ``None`` for a custom door — never stored.
    ``source`` says where the user configured this door: the
    current selection, the fallback chain, or a role route.
    """

    model: str
    base_url: str
    provider: Optional[str]
    source: str

    def selection(self) -> Dict[str, Any]:
        """This door as a plain selection mapping."""
        return {"model": self.model, "base_url": self.base_url,
                "provider": self.provider, "source": self.source}

    def describe(self) -> str:
        """One plain phrase: model, provider when known, door."""
        label = self.model
        if self.provider:
            label += f" via {self.provider}"
        return f"{label} ({self.base_url}, {self.source})"


def _door_switchable(base_url: str) -> bool:
    """Whether the live session can speak this door (M-028's bound).

    A custom door (no registry provider owns its endpoint) is
    speakable, exactly as a switch to it is; a registry door is
    speakable only when its dialect is one the live session
    speaks — a native-SDK or Ollama-native door is not a
    candidate, however cheap.
    """
    provider = infer_provider(base_url)
    if provider is None:
        return True
    return load_registry().provider(provider).dialect in SWITCHABLE_DIALECTS


def candidate_doors(config: Dict[str, Any]) -> Tuple[Door, ...]:
    """Every door the user has configured, current door first.

    The candidate pool is exactly: the session's current
    selection, the M-030 fallback chain in its order, and the
    M-029 role routes in office order — deduplicated by
    (model, door), first source winning. A malformed stored
    chain or route raises here, as it does on its own surface:
    a broken configuration surfaces, it is never routed around.
    """
    doors: List[Door] = []
    seen: set = set()

    def _add(model: Any, base_url: Any, source: str) -> None:
        if not isinstance(model, str) or not model.strip():
            return
        if not isinstance(base_url, str) or not base_url.strip():
            return
        model, base_url = model.strip(), base_url.strip()
        key = (model, base_url)
        if key in seen:
            return
        seen.add(key)
        doors.append(Door(model=model, base_url=base_url,
                          provider=infer_provider(base_url),
                          source=source))

    _add(config.get("model"), config.get("base_url"), "current door")
    for entry in chain_from_config(config):
        _add(entry.model, entry.base_url, "fallback chain")
    for office, route in routes_from_config(config).items():
        _add(route["model"], route["base_url"], f"route for {office}")
    return tuple(doors)


def unit_cost(model: str) -> Optional[float]:
    """The comparable cost of *model*, or None when unpriced.

    The ``mythic costs`` price of one million input tokens plus
    one million output tokens — one fixed yardstick every door
    is measured with. A model the costs table does not price
    returns None: its cost is unknown, and unknown is never
    cheaper.
    """
    cost, known = _cost_price(model, 1_000_000, 1_000_000)
    return cost if known else None


def door_adequate(record: ModelCapability, task: TaskClass) -> bool:
    """Whether capability truth *record* is adequate for *task*.

    Only known truth counts: a required flag must be exactly
    True (False fails, None — unknown — fails), and a context
    requirement must be met by a known context size.
    """
    if task.required_flag is not None:
        if record.capability(task.required_flag) is not True:
            return False
    if task.min_context is not None:
        if record.context_tokens is None:
            return False
        if record.context_tokens < task.min_context:
            return False
    return True


@dataclass(frozen=True)
class CostRoutingChange:
    """One validated setting change: before and after."""

    before: bool
    after: bool

    def event(self) -> Dict[str, Any]:
        """The session-event payload for this change."""
        return {"type": "cost_routing_changed",
                "from": self.before, "to": self.after}

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        """The change record the agent returns to its callers."""
        return {"kind": "setting", "from": self.before,
                "to": self.after, "session_id": session_id,
                "journaled": journaled}


def enabled_from_config(config: Dict[str, Any]) -> bool:
    """The cost-routing setting stored in *config*.

    Absent means False (the setting was never turned on). A
    stored value that is not a bool raises — a setting the user
    cannot read back truthfully must surface, not be guessed at.
    """
    raw = config.get(SETTING_KEY, False)
    if not isinstance(raw, bool):
        raise ValueError(
            f"{SETTING_KEY} must be true or false, "
            f"got {type(raw).__name__}")
    return raw


def set_enabled(config: Dict[str, Any], enabled: Any
                ) -> Tuple[bool, CostRoutingChange]:
    """Validate a setting change; return (new value, change).

    Pure: *config* is not mutated. A non-bool request is
    refused, and setting the value it already holds is refused
    plainly — no change happened, so none is recorded.
    """
    if not isinstance(enabled, bool):
        raise ValueError(
            f"Cost routing must be true or false, "
            f"got {type(enabled).__name__}")
    before = enabled_from_config(config)
    if enabled == before:
        raise ValueError(
            "Cost-aware routing is already "
            f"{'on' if before else 'off'}; nothing changes.")
    return enabled, CostRoutingChange(before=before, after=enabled)


@dataclass(frozen=True)
class CostDecision:
    """The router's decision for one task class, with its reason.

    ``chosen`` is the door to use, ``current`` the door in
    place; ``changed`` is True only when the router prefers a
    different door. Costs are the :func:`unit_cost` yardstick
    (None = unpriced, never guessed). ``reason`` is the
    plain-words explanation every surface shows.
    """

    task_class: str
    enabled: bool
    current: Door
    chosen: Door
    changed: bool
    current_cost: Optional[float]
    chosen_cost: Optional[float]
    reason: str

    def record(self) -> Dict[str, Any]:
        """This decision as a plain mapping."""
        return {
            "task_class": self.task_class,
            "enabled": self.enabled,
            "changed": self.changed,
            "current": self.current.selection(),
            "chosen": self.chosen.selection(),
            "current_cost": self.current_cost,
            "chosen_cost": self.chosen_cost,
            "reason": self.reason,
        }


def choose_route(config: Dict[str, Any], task_class: Any,
                 capabilities: Any = None) -> CostDecision:
    """Decide the door for *task_class* under the user's config.

    The decision procedure, in order: the setting governs
    (off → the current door, explained); the candidate pool is
    the user's configured doors the live session can speak;
    adequacy is M-027 capability truth; preference is the
    costs table's price, cheapest adequate first, ties and
    unprovable savings keeping the current door. When the
    current door is itself not known to be adequate, the
    cheapest priced adequate door wins on adequacy alone —
    cost comparison against a door that cannot do the work
    proves nothing.
    """
    task = get_task_class(task_class)
    doors = candidate_doors(config)
    if not doors:
        raise ValueError(
            "No door is configured: set a model and base URL "
            "before cost routing can choose.")
    current = doors[0]
    enabled = enabled_from_config(config)
    current_cost = unit_cost(current.model)
    if not enabled:
        return CostDecision(
            task_class=task.id, enabled=False, current=current,
            chosen=current, changed=False,
            current_cost=current_cost, chosen_cost=current_cost,
            reason=(
                "Cost-aware routing is off, so the current door "
                "stays. " + PLAIN_EXPLANATION))
    caps = capabilities if capabilities is not None else load_capabilities()
    speakable = [d for d in doors if _door_switchable(d.base_url)]
    adequate = [d for d in speakable
                if door_adequate(caps.for_model(d.model), task)]
    priced = [(unit_cost(d.model), index, d)
              for index, d in enumerate(adequate)
              if unit_cost(d.model) is not None]
    current_adequate = any(
        d.model == current.model and d.base_url == current.base_url
        for d in adequate)
    if not priced:
        return CostDecision(
            task_class=task.id, enabled=True, current=current,
            chosen=current, changed=False,
            current_cost=current_cost, chosen_cost=current_cost,
            reason=(
                f"No configured door is both known to be adequate "
                f"for {task.id} work and priced in the costs data, "
                "so no cheaper adequate door can be proven; the "
                "current door stays."))
    priced.sort(key=lambda item: (item[0], item[1]))
    best_cost, _, best = priced[0]
    if best.model == current.model and best.base_url == current.base_url:
        return CostDecision(
            task_class=task.id, enabled=True, current=current,
            chosen=current, changed=False,
            current_cost=current_cost, chosen_cost=current_cost,
            reason=(
                f"The current door is already the cheapest "
                f"adequate door for {task.id} work "
                f"(${best_cost:.2f} on the costs yardstick); "
                "nothing changes."))
    if current_adequate and current_cost is None:
        return CostDecision(
            task_class=task.id, enabled=True, current=current,
            chosen=current, changed=False,
            current_cost=None, chosen_cost=best_cost,
            reason=(
                "The current door's price is not in the costs "
                "data, so no saving over it can be proven; the "
                "current door stays."))
    if current_adequate and best_cost >= current_cost:
        return CostDecision(
            task_class=task.id, enabled=True, current=current,
            chosen=current, changed=False,
            current_cost=current_cost, chosen_cost=current_cost,
            reason=(
                f"No adequate door is cheaper than the current "
                f"door for {task.id} work (${current_cost:.2f} on "
                "the costs yardstick); the current door stays."))
    if current_adequate:
        reason = (
            f"For {task.id} work, {best.describe()} is adequate "
            f"and cheaper: ${best_cost:.2f} against "
            f"${current_cost:.2f} on the costs yardstick "
            "(one million input plus one million output tokens, "
            "priced by the mythic costs data).")
    else:
        reason = (
            f"For {task.id} work, the current door is not known "
            f"to be adequate, and {best.describe()} is the "
            f"cheapest adequate priced door (${best_cost:.2f} on "
            "the costs yardstick).")
    return CostDecision(
        task_class=task.id, enabled=True, current=current,
        chosen=best, changed=True,
        current_cost=current_cost, chosen_cost=best_cost,
        reason=reason)


def parse_cost_args(text: Any) -> Dict[str, Any]:
    """Parse the ``/costroute`` slash-command argument string.

    Grammar::

        /costroute                  -> show setting + explanation
        /costroute on               -> turn the setting on
        /costroute off              -> turn the setting off
        /costroute <task-class>     -> the decision for that class

    Returns a dict with keys ``action`` (``show`` / ``setting``
    / ``decide``), ``enabled`` and ``task_class``. Raises
    :class:`ValueError` on a usage error.
    """
    if text is None:
        text = ""
    if not isinstance(text, str):
        raise ValueError(
            f"Cost routing arguments must be text, "
            f"got {type(text).__name__}")
    parsed: Dict[str, Any] = {"action": "show", "enabled": None,
                              "task_class": None}
    stripped = text.strip()
    if not stripped:
        return parsed
    head, _, rest = stripped.partition(" ")
    head = head.lower()
    if rest.strip():
        raise ValueError(
            "Usage: /costroute, /costroute on, /costroute off, "
            "or /costroute <task-class> (one of: "
            + ", ".join(TASK_CLASS_IDS) + ")")
    if head in ("on", "off"):
        parsed["action"] = "setting"
        parsed["enabled"] = head == "on"
        return parsed
    if head == "show":
        return parsed
    task = get_task_class(head)
    parsed["action"] = "decide"
    parsed["task_class"] = task.id
    return parsed


def _cost_phrase(cost: Optional[float]) -> str:
    if cost is None:
        return "price unknown in the costs data"
    return f"${cost:.2f} on the costs yardstick"


def format_cost_routing(config: Dict[str, Any]) -> str:
    """The visible setting: state, explanation, doors, classes."""
    enabled = enabled_from_config(config)
    lines = [
        "Cost-aware routing: "
        + ("ON — the router may prefer a cheaper adequate door "
           "for a task class, and always says why."
           if enabled else
           "OFF (the default) — the router changes nothing. "
           "Turn it on with /costroute on."),
        PLAIN_EXPLANATION,
        "  Doors the router may choose between (yours only):",
    ]
    for door in candidate_doors(config):
        lines.append(
            f"    {door.describe()} — {_cost_phrase(unit_cost(door.model))}")
    lines.append("  Task classes:")
    for task in TASK_CLASSES:
        lines.append(f"    {task.id} — {task.plain}")
    lines.append(
        "  Ask for a decision with /costroute <task-class>; "
        "the decision is applied through the journaled model "
        "switch and explained in the transcript.")
    return "\n".join(lines)


def format_decision(decision: CostDecision) -> str:
    """One plain paragraph: the decision and its reason."""
    if decision.changed:
        head = (f"Cost routing for {decision.task_class} work: "
                f"switch to {decision.chosen.describe()}. ")
    else:
        head = (f"Cost routing for {decision.task_class} work: "
                f"stay on {decision.current.describe()}. ")
    return head + decision.reason


def format_cost_change(record: Dict[str, Any]) -> str:
    """One plain sentence describing a completed setting change."""
    if record["to"]:
        text = ("Cost-aware routing is now ON: for a task class, "
                "Mythic may prefer a cheaper adequate door among "
                "the doors you configured, and will say why.")
    else:
        text = ("Cost-aware routing is now OFF: the router "
                "changes nothing; your current door is used as "
                "set.")
    if record.get("session_id"):
        text += f" Recorded on session {record['session_id']}."
    return text
