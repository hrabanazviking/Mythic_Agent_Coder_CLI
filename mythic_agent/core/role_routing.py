"""Role routing (All-Features roadmap slice M-029).

Part II — The Provider Ocean — continues here. Different offices of
the crew can sit on different models: a deep thinker for the
Architect, a fast hand for the Forge Worker's grunt edits, a cheap
scout for the Cartographer's searches. A route is *set per crew
role, visible, and changeable* — the three properties this module
exists to keep true.

Where routes live and how they take effect:

* Routes are user configuration, stored in the config mapping under
  ``role_routes`` (a top-level key in ``config_defaults.yaml``,
  catalogued by M-009's contract): ``{office: {"model": ...,
  "base_url": ...}}``. Only offices with an explicit route appear;
  every other office truthfully uses the session default.
* This module is the pure layer: it validates and resolves routes
  against the session selection, reusing the M-028 resolver
  (:mod:`mythic_agent.core.model_switch`) so a route can only name
  doors the live session can actually speak — a native-SDK or
  Ollama-native provider is refused plainly here too, and nothing
  is mutated on a refusal. It performs no I/O: the agent layer owns
  the config save, the session journal, and applying a route to a
  crew member when it is spawned (or re-routed while idle).
* The offices are the crew's real offices, taken from the shipped
  sub-agent definitions (``DEFAULT_SUBAGENTS``): every shipped
  sub-agent name maps to exactly one office through
  :func:`office_for_agent_name`, and the slice's tests pin that
  mapping against the live constants so a new crew member cannot
  arrive unrouted. ``primary`` is the lead session itself.

Honesty bounds, enforced here and pinned by tests:

* An office with no explicit route resolves to the session default
  (the config's own ``model`` / ``base_url``) with source
  ``session_default`` — the fallback is shown, never hidden.
* The Primary office has no route of its own: its selection *is*
  the session default, changed by M-028's switch, so setting or
  clearing a ``primary`` route is refused plainly.
* A stored route that is malformed (unknown office, missing or
  blank model / door) raises instead of being silently ignored —
  a broken route the user wrote must surface, not vanish.
* A provider is never stored in a route: it is inferred from the
  door by exact endpoint equality (M-028's rule), so a route can
  never claim a provider its door is not.
"""

from __future__ import annotations

__all__ = [
    "OFFICES",
    "ROUTES_KEY",
    "ROUTING_SLICE",
    "Any",
    "Dict",
    "Office",
    "Optional",
    "Route",
    "RouteChange",
    "Tuple",
    "clear_route",
    "effective_routes",
    "format_route_change",
    "format_routes",
    "get_office",
    "office_for_agent_name",
    "office_ids",
    "parse_route_args",
    "resolve_route",
    "routes_from_config",
    "set_route",
]

import shlex
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from .model_switch import infer_provider, resolve_switch

#: The slice that owns this module.
ROUTING_SLICE = "M-029"

#: The config key routes live under.
ROUTES_KEY = "role_routes"


@dataclass(frozen=True)
class Office:
    """One crew office: its id, its title, and what it is for."""

    id: str
    title: str
    purpose: str


#: The crew's offices, in crew order. Titles and purposes are the
#: shipped sub-agent definitions' own focus lines (constants.py),
#: compressed — never invented offices the crew does not hold.
OFFICES: Tuple[Office, ...] = (
    Office("primary", "Primary",
           "The lead session itself; its selection is the session "
           "default every other office falls back to."),
    Office("polymath", "Polymath",
           "Bleeding-edge logic, architecture, deep technical "
           "polymathy and full-stack integrations (Alfhild)."),
    Office("architect", "Architect",
           "Boundaries, domain ownership, overall structure and "
           "refactoring strategy — the deep thinker."),
    Office("auditor", "Auditor",
           "Finding bugs, checking invariants, running tests and "
           "exposing contradictions with reality."),
    Office("cartographer", "Cartographer",
           "Mapping relationships, data flows and dependencies; "
           "the crew's scout for searches and overviews."),
    Office("forge_worker", "Forge Worker",
           "Writing clean working code, tests, boilerplate and "
           "mechanical implementation — the fast hand for edits."),
    Office("scribe", "Scribe",
           "Writing and maintaining documentation, changelogs and "
           "task summaries; preserving continuity."),
    Office("skald", "Skald",
           "High-level vision, philosophy, elegant naming and "
           "framing concepts."),
    Office("guardian", "Guardian",
           "Security and stability: rock-solid, bug-free, safe "
           "handling of dangerous operations (Thor)."),
)

_OFFICE_BY_ID = {office.id: office for office in OFFICES}

#: Name fragments (matched against a sub-agent's *name* only) that
#: place it in an office, checked in order. Guardian precedes Scribe
#: because the Guardian's own description calls it a scribe too —
#: its name, "Thor Guardian", is the truth that routes it.
_NAME_MATCHERS: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("architect", ("Architect",)),
    ("auditor", ("Auditor",)),
    ("cartographer", ("Cartographer",)),
    ("forge_worker", ("Forge Worker",)),
    ("guardian", ("Guardian", "Thor")),
    ("skald", ("Skald",)),
    ("scribe", ("Scribe",)),
    ("polymath", ("Alfhild",)),
)


def office_ids() -> Tuple[str, ...]:
    """Every office id, in crew order."""
    return tuple(office.id for office in OFFICES)


def get_office(office_id: Any) -> Office:
    """The office named *office_id* (KeyError naming all offices)."""
    if isinstance(office_id, str) and office_id in _OFFICE_BY_ID:
        return _OFFICE_BY_ID[office_id]
    raise KeyError(
        f"Unknown office {office_id!r}. Offices: "
        f"{', '.join(office_ids())}")


def office_for_agent_name(name: Any) -> Optional[str]:
    """The office a sub-agent *name* belongs to, or None.

    ``"Primary"`` is the primary office. Any other name is matched
    against the shipped crew's office titles; a name no office
    claims returns ``None`` — unrouted, never guessed into one.
    """
    if not isinstance(name, str) or not name.strip():
        return None
    if name.strip() == "Primary":
        return "primary"
    for office_id, fragments in _NAME_MATCHERS:
        if any(fragment in name for fragment in fragments):
            return office_id
    return None


@dataclass(frozen=True)
class Route:
    """One office's effective selection.

    ``source`` is ``"route"`` for an explicit per-office route and
    ``"session_default"`` when the office falls back to the
    session's own selection. ``provider`` is inferred from the door
    by exact endpoint equality, or ``None`` for a custom door.
    """

    office: str
    model: str
    base_url: str
    provider: Optional[str]
    source: str

    def selection(self) -> Dict[str, Any]:
        """This route as a plain selection mapping."""
        return {"model": self.model, "base_url": self.base_url,
                "provider": self.provider}

    def describe(self) -> str:
        """One plain phrase: model, provider when known, and source."""
        label = self.model
        if self.provider:
            label += f" via {self.provider}"
        origin = ("role route" if self.source == "route"
                  else "session default")
        return f"{label} ({self.base_url}) [{origin}]"


def routes_from_config(config: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    """The validated explicit routes stored in *config*.

    Returns ``{office: {"model": ..., "base_url": ...}}``. A stored
    route that is malformed — not a mapping, an unknown office, a
    missing or blank model or door — raises :class:`ValueError`:
    a broken route surfaces, it is never silently dropped.
    """
    raw = config.get(ROUTES_KEY) or {}
    if not isinstance(raw, dict):
        raise ValueError(
            f"{ROUTES_KEY} must be a mapping of office to route, "
            f"got {type(raw).__name__}")
    routes: Dict[str, Dict[str, str]] = {}
    for office_id, entry in raw.items():
        if office_id not in _OFFICE_BY_ID:
            raise ValueError(
                f"Route stored for unknown office {office_id!r}. "
                f"Offices: {', '.join(office_ids())}")
        if not isinstance(entry, dict):
            raise ValueError(
                f"Route for office {office_id!r} must be a mapping "
                f"with model and base_url, got {type(entry).__name__}")
        model, base_url = entry.get("model"), entry.get("base_url")
        if not isinstance(model, str) or not model.strip():
            raise ValueError(
                f"Route for office {office_id!r} has no model name")
        if not isinstance(base_url, str) or not base_url.strip():
            raise ValueError(
                f"Route for office {office_id!r} has no door URL")
        routes[office_id] = {"model": model.strip(),
                             "base_url": base_url.strip()}
    return routes


def resolve_route(config: Dict[str, Any], office_id: str) -> Route:
    """The effective route for *office_id* under *config*.

    The office's explicit route when one is stored; otherwise the
    session default — the config's own model and door — with
    source ``session_default``. Raises KeyError for an unknown
    office and ValueError for a malformed stored route.
    """
    office = get_office(office_id)
    stored = routes_from_config(config)
    if office.id in stored:
        entry = stored[office.id]
        return Route(office=office.id, model=entry["model"],
                     base_url=entry["base_url"],
                     provider=infer_provider(entry["base_url"]),
                     source="route")
    model = config.get("model") or ""
    base_url = config.get("base_url") or ""
    return Route(office=office.id, model=model, base_url=base_url,
                 provider=infer_provider(base_url),
                 source="session_default")


def effective_routes(config: Dict[str, Any]) -> Tuple[Route, ...]:
    """Every office's effective route, in crew order (visibility)."""
    return tuple(resolve_route(config, office.id) for office in OFFICES)


@dataclass(frozen=True)
class RouteChange:
    """One validated route change: an office's before and after.

    ``after`` is ``None`` when the change clears the office's route
    (the office returns to the session default).
    """

    office: str
    before: Route
    after: Optional[Route]

    def event(self) -> Dict[str, Any]:
        """The ``role_route_changed`` session-event payload."""
        return {
            "type": "role_route_changed",
            "office": self.office,
            "from": self.before.selection(),
            "from_source": self.before.source,
            "to": (self.after.selection() if self.after else None),
        }

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        """The change record the agent returns to its callers."""
        return {
            "office": self.office,
            "from": self.before.selection(),
            "from_source": self.before.source,
            "to": (self.after.selection() if self.after else None),
            "session_id": session_id,
            "journaled": journaled,
        }


def set_route(config: Dict[str, Any], office_id: str, *,
              model: Any = None, provider: Any = None,
              base_url: Any = None) -> Tuple[Dict[str, Dict[str, str]], RouteChange]:
    """Validate a new route for *office_id*; return (routes, change).

    Pure: *config* is not mutated. The requested change is resolved
    by the M-028 switch resolver against the office's *current
    effective* selection, so a provider name takes that provider's
    endpoint and default model, an explicit model is taken as
    given, and a door the live session cannot speak is refused
    plainly before anything changes. The Primary office is refused:
    its selection is the session default itself (M-028's road).
    """
    office = get_office(office_id)
    if office.id == "primary":
        raise ValueError(
            "The Primary office has no route of its own: its "
            "selection is the session default. Change it with the "
            "model switch (M-028) and every unrouted office "
            "follows.")
    before = resolve_route(config, office.id)
    target = resolve_switch(
        {"model": before.model, "base_url": before.base_url},
        model=model, provider=provider, base_url=base_url)
    routes = routes_from_config(config)
    routes[office.id] = {"model": target.to_model,
                         "base_url": target.to_base_url}
    after = Route(office=office.id, model=target.to_model,
                  base_url=target.to_base_url,
                  provider=target.to_provider, source="route")
    return routes, RouteChange(office=office.id, before=before, after=after)


def clear_route(config: Dict[str, Any],
                office_id: str) -> Tuple[Dict[str, Dict[str, str]], RouteChange]:
    """Remove *office_id*'s explicit route; return (routes, change).

    Pure: *config* is not mutated. Clearing an office that has no
    explicit route is refused plainly — it already rides the
    session default, and claiming a change would be a lie.
    """
    office = get_office(office_id)
    if office.id == "primary":
        raise ValueError(
            "The Primary office has no route to clear: its "
            "selection is the session default itself.")
    routes = routes_from_config(config)
    if office.id not in routes:
        raise ValueError(
            f"Office {office.id!r} has no role route to clear; it "
            "already uses the session default.")
    before = resolve_route(config, office.id)
    del routes[office.id]
    return routes, RouteChange(office=office.id, before=before, after=None)


def parse_route_args(text: Any) -> Dict[str, Any]:
    """Parse the ``/route`` slash-command argument string.

    Grammar::

        /route                                   -> list all offices
        /route <office>                          -> show one office
        /route <office> <model> [url]            -> set (legacy form)
        /route <office> --provider <name> [--model <model>]
               [--base-url <url>]                -> set
        /route clear <office>                    -> clear the route

    Returns a dict with keys ``action`` (``list`` / ``show`` /
    ``set`` / ``clear``), ``office``, ``model``, ``provider`` and
    ``base_url``. Raises :class:`ValueError` on a usage error
    (unknown office, unknown flag, a field given twice).
    """
    if text is None:
        text = ""
    if not isinstance(text, str):
        raise ValueError(
            f"Route arguments must be text, got {type(text).__name__}")
    try:
        tokens = shlex.split(text)
    except ValueError as exc:
        raise ValueError(f"Could not parse route arguments: {exc}") from exc
    parsed: Dict[str, Any] = {"action": "list", "office": None,
                              "model": None, "provider": None,
                              "base_url": None}
    if not tokens:
        return parsed
    if tokens[0] == "clear":
        if len(tokens) != 2:
            raise ValueError("Usage: /route clear <office>")
        parsed["action"] = "clear"
        parsed["office"] = get_office(tokens[1]).id
        return parsed
    office = get_office(tokens[0])  # KeyError -> caller shows it plainly
    parsed["office"] = office.id
    rest = tokens[1:]
    if not rest:
        parsed["action"] = "show"
        return parsed
    parsed["action"] = "set"
    positionals: list = []
    index = 0
    while index < len(rest):
        token = rest[index]
        if token in ("--provider", "--model", "--base-url"):
            if index + 1 >= len(rest):
                raise ValueError(f"{token} needs a value after it")
            key = {"--provider": "provider", "--model": "model",
                   "--base-url": "base_url"}[token]
            if parsed[key] is not None:
                raise ValueError(f"{token} was given twice")
            parsed[key] = rest[index + 1]
            index += 2
        elif token.startswith("--"):
            raise ValueError(
                f"Unknown route flag {token!r}; use --provider, "
                "--model or --base-url")
        else:
            positionals.append(token)
            index += 1
    if len(positionals) > 2:
        raise ValueError(
            "Usage: /route <office> <model> [url] — too many bare words")
    if positionals:
        if parsed["model"] is not None:
            raise ValueError(
                "Model given both as a bare word and with --model; "
                "give it once")
        parsed["model"] = positionals[0]
    if len(positionals) == 2:
        if parsed["base_url"] is not None:
            raise ValueError(
                "Door URL given both as a bare word and with "
                "--base-url; give it once")
        parsed["base_url"] = positionals[1]
    return parsed


def format_routes(config: Dict[str, Any]) -> str:
    """The visible route table: every office, its model, its source."""
    lines = ["Role routes:"]
    for route in effective_routes(config):
        office = get_office(route.office)
        lines.append(f"  {office.title}: {route.describe()}")
    return "\n".join(lines)


def format_route_change(record: Dict[str, Any]) -> str:
    """One plain sentence describing a completed route change."""
    office = get_office(record["office"])
    before = record["from"]
    before_label = before["model"]
    if before.get("provider"):
        before_label += f" via {before['provider']}"
    if record["to"] is None:
        return (f"{office.title} route cleared: it used "
                f"{before_label} ({before['base_url']}) and now "
                "uses the session default.")
    after = record["to"]
    after_label = after["model"]
    if after.get("provider"):
        after_label += f" via {after['provider']}"
    text = (f"{office.title} route changed from {before_label} "
            f"({before['base_url']}) to {after_label} "
            f"({after['base_url']}).")
    if record.get("session_id"):
        text += (f" Recorded on session {record['session_id']}; "
                 "crew members take the route when they are "
                 "spawned or next re-routed while idle.")
    return text
