"""Fallback chains (All-Features roadmap slice M-030).

Part II — The Provider Ocean — continues here. When a provider
fails or rate-limits, the session does not have to die with it: a
*fallback chain* walks to the next door, in the order the user
configured, **with the user's standing permission** and with
**every walk announced, never silent**.

What already shipped, and what this slice adds:

* The elder road already ships a provider-level failover machinery
  (``mythic_agent.providers.failover.FailoverRouter`` — health-aware
  ordering, circuit breakers, per-attempt attribution over scripted
  provider factories). That machinery answers "which candidate
  first" for code that builds its own providers; it is *not* a
  user-facing chain: nothing in config names it, no permission
  governs it, and the live session never walks it.
* This slice is the user-facing chain over that ground: the chain
  and its standing permission are **config settings**
  (``fallback_chain`` — a list of doors, in walk order — and
  ``fallback_permission`` — a bool, off by default), every entry is
  validated through the M-019 registry + the M-028 switch resolver
  (so a chain entry can only name a door the live session can
  actually speak — a native-SDK or Ollama-native provider is
  refused plainly, exactly as a switch is), the agent layer walks
  the chain in the live chat path when a provider request fails,
  and every walk is announced on the chat surface **and** journaled
  as a ``fallback_walked`` session event before the new door is
  tried.

This module is the pure layer: it validates and describes chains,
parses the ``/fallback`` grammar shared by both surfaces, and
formats the announcements. It performs no I/O: the agent layer
owns the config save, the session journal, and the walk itself.

Honesty rules, enforced here and pinned by the slice's tests:

* No permission, no walk. ``fallback_permission`` defaults to
  False; with it off (or with an empty chain) a provider failure
  is simply the failure — the chain never stirs uninvited.
* A stored chain that is malformed (not a list, an entry that is
  not a mapping, a missing or blank model or door, a duplicate
  door) raises instead of being silently ignored — a broken chain
  the user wrote must surface, not vanish.
* An entry that names the session's own current door is refused
  at set time (walking to the door that just failed is no walk),
  and a duplicate entry is refused: the chain is a walk through
  *different* doors, in the user's order — never reordered by
  health scores or anything else. (Health ordering is the elder
  router's job, for its own callers; the user's chain order is
  the user's.)
* A provider is never stored in an entry: it is inferred from the
  door by exact endpoint equality (M-028's rule), so an entry can
  never claim a provider its door is not.
"""

from __future__ import annotations

__all__ = [
    "CHAIN_KEY",
    "FALLBACK_SLICE",
    "PERMISSION_KEY",
    "Any",
    "ChainEntry",
    "Dict",
    "FallbackChange",
    "List",
    "Optional",
    "Tuple",
    "chain_from_config",
    "clear_chain",
    "format_chain",
    "format_fallback_change",
    "format_walk",
    "parse_fallback_args",
    "permission_from_config",
    "resolve_entry",
    "set_chain_entry",
    "set_permission",
    "walk_entries",
]

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .model_switch import infer_provider, parse_switch_args, resolve_switch

#: The slice that owns this module.
FALLBACK_SLICE = "M-030"

#: The config key the chain lives under.
CHAIN_KEY = "fallback_chain"

#: The config key the standing permission lives under.
PERMISSION_KEY = "fallback_permission"


@dataclass(frozen=True)
class ChainEntry:
    """One door in the chain: a model at a base URL.

    ``provider`` is inferred from the door by exact endpoint
    equality, or ``None`` for a custom door — never stored.
    """

    model: str
    base_url: str
    provider: Optional[str]

    def selection(self) -> Dict[str, Any]:
        """This entry as a plain selection mapping."""
        return {"model": self.model, "base_url": self.base_url,
                "provider": self.provider}

    def describe(self) -> str:
        """One plain phrase: model, provider when known, door."""
        label = self.model
        if self.provider:
            label += f" via {self.provider}"
        return f"{label} ({self.base_url})"


def chain_from_config(config: Dict[str, Any]) -> Tuple[ChainEntry, ...]:
    """The validated chain stored in *config*, in walk order.

    A stored chain that is malformed — not a list, an entry that
    is not a mapping, a missing or blank model or door, or the
    same door named twice — raises :class:`ValueError`: a broken
    chain surfaces, it is never silently dropped.
    """
    raw = config.get(CHAIN_KEY) or []
    if not isinstance(raw, list):
        raise ValueError(
            f"{CHAIN_KEY} must be a list of doors, "
            f"got {type(raw).__name__}")
    entries: List[ChainEntry] = []
    seen: set = set()
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(
                f"Fallback chain entry {index + 1} must be a mapping "
                f"with model and base_url, got {type(item).__name__}")
        model, base_url = item.get("model"), item.get("base_url")
        if not isinstance(model, str) or not model.strip():
            raise ValueError(
                f"Fallback chain entry {index + 1} has no model name")
        if not isinstance(base_url, str) or not base_url.strip():
            raise ValueError(
                f"Fallback chain entry {index + 1} has no door URL")
        model, base_url = model.strip(), base_url.strip()
        key = (model, base_url)
        if key in seen:
            raise ValueError(
                f"Fallback chain names {model} at {base_url} twice; "
                "each door may appear once")
        seen.add(key)
        entries.append(ChainEntry(model=model, base_url=base_url,
                                  provider=infer_provider(base_url)))
    return tuple(entries)


def permission_from_config(config: Dict[str, Any]) -> bool:
    """The standing fallback permission stored in *config*.

    Absent means False (no permission was ever given). A stored
    value that is not a bool raises — a permission the user cannot
    read back truthfully must surface, not be guessed at.
    """
    raw = config.get(PERMISSION_KEY, False)
    if not isinstance(raw, bool):
        raise ValueError(
            f"{PERMISSION_KEY} must be true or false, "
            f"got {type(raw).__name__}")
    return raw


def resolve_entry(config: Dict[str, Any], *, model: Any = None,
                  provider: Any = None,
                  base_url: Any = None) -> ChainEntry:
    """Validate one proposed chain entry against the session.

    Resolved by the M-028 switch resolver against the session's
    current selection, so a provider name takes that provider's
    endpoint and default model, an explicit model is taken as
    given, and a door the live session cannot speak is refused
    plainly before anything changes. An entry that *is* the
    session's current door is refused: it could never be walked
    to, because it is the door whose failure starts the walk.
    """
    target = resolve_switch(
        {"model": config.get("model") or "",
         "base_url": config.get("base_url") or ""},
        model=model, provider=provider, base_url=base_url)
    if (target.to_model == (config.get("model") or "")
            and target.to_base_url == (config.get("base_url") or "")):
        raise ValueError(
            "That door is the session's current door; a fallback "
            "entry must be a different door to walk to when this "
            "one fails.")
    return ChainEntry(model=target.to_model,
                      base_url=target.to_base_url,
                      provider=target.to_provider)


@dataclass(frozen=True)
class FallbackChange:
    """One validated chain/permission change: before and after.

    ``kind`` is ``"chain"`` (``after`` is the new chain, a tuple of
    entries — empty when the change clears the chain) or
    ``"permission"`` (``after`` is the new bool).
    """

    kind: str
    before: Any
    after: Any

    def event(self) -> Dict[str, Any]:
        """The session-event payload for this change."""
        if self.kind == "permission":
            return {"type": "fallback_permission_changed",
                    "from": self.before, "to": self.after}
        return {"type": "fallback_chain_changed",
                "from": [e.selection() for e in self.before],
                "to": [e.selection() for e in self.after]}

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        """The change record the agent returns to its callers."""
        if self.kind == "permission":
            return {"kind": self.kind, "from": self.before,
                    "to": self.after, "session_id": session_id,
                    "journaled": journaled}
        return {"kind": self.kind,
                "from": [e.selection() for e in self.before],
                "to": [e.selection() for e in self.after],
                "session_id": session_id, "journaled": journaled}


def set_chain_entry(config: Dict[str, Any], *, model: Any = None,
                    provider: Any = None,
                    base_url: Any = None
                    ) -> Tuple[List[Dict[str, str]], FallbackChange]:
    """Append one validated entry; return (stored chain, change).

    Pure: *config* is not mutated. The entry is resolved through
    :func:`resolve_entry`, and an entry already in the chain is
    refused — the walk visits each door once.
    """
    before = chain_from_config(config)
    entry = resolve_entry(config, model=model, provider=provider,
                          base_url=base_url)
    if any(e.model == entry.model and e.base_url == entry.base_url
           for e in before):
        raise ValueError(
            f"{entry.model} at {entry.base_url} is already in the "
            "fallback chain; each door may appear once")
    after = before + (entry,)
    stored = [{"model": e.model, "base_url": e.base_url} for e in after]
    return stored, FallbackChange(kind="chain", before=before, after=after)


def clear_chain(config: Dict[str, Any]
                ) -> Tuple[List[Dict[str, str]], FallbackChange]:
    """Remove every chain entry; return (stored chain, change).

    Pure: *config* is not mutated. Clearing an already-empty chain
    is refused plainly — it already walks nowhere, and claiming a
    change would be a lie.
    """
    before = chain_from_config(config)
    if not before:
        raise ValueError(
            "The fallback chain is already empty; there is nothing "
            "to clear.")
    return [], FallbackChange(kind="chain", before=before, after=())


def set_permission(config: Dict[str, Any], enabled: Any
                   ) -> Tuple[bool, FallbackChange]:
    """Validate a permission change; return (new value, change).

    Pure: *config* is not mutated. A non-bool request is refused,
    and setting the permission to the value it already holds is
    refused plainly — no change happened, so none is recorded.
    """
    if not isinstance(enabled, bool):
        raise ValueError(
            f"Fallback permission must be true or false, "
            f"got {type(enabled).__name__}")
    before = permission_from_config(config)
    if enabled == before:
        raise ValueError(
            "Standing fallback permission is already "
            f"{'on' if before else 'off'}; nothing changes.")
    return enabled, FallbackChange(kind="permission", before=before,
                                   after=enabled)


def walk_entries(config: Dict[str, Any]) -> Tuple[ChainEntry, ...]:
    """The doors a walk may visit, in the user's order.

    The chain exactly as configured, minus any entry that is the
    session's *current* selection at walk time (that door is the
    one that just failed; "walking" to it would be a silent retry
    wearing a walk's clothes). Permission is *not* folded in here:
    the caller checks :func:`permission_from_config` itself, so a
    caller can always say honestly whether the chain was silent
    because no permission was given or because it is empty.
    """
    current = (config.get("model") or "", config.get("base_url") or "")
    return tuple(
        entry for entry in chain_from_config(config)
        if (entry.model, entry.base_url) != current)


def parse_fallback_args(text: Any) -> Dict[str, Any]:
    """Parse the ``/fallback`` slash-command argument string.

    Grammar::

        /fallback                       -> show chain + permission
        /fallback on                    -> give standing permission
        /fallback off                   -> withdraw it
        /fallback add <model> [url]     -> append a door (legacy form)
        /fallback add --provider <name> [--model <model>]
               [--base-url <url>]       -> append a door
        /fallback clear                 -> empty the chain

    Returns a dict with keys ``action`` (``show`` / ``permission``
    / ``add`` / ``clear``), ``enabled``, ``model``, ``provider``
    and ``base_url``. Raises :class:`ValueError` on a usage error.
    """
    if text is None:
        text = ""
    if not isinstance(text, str):
        raise ValueError(
            f"Fallback arguments must be text, "
            f"got {type(text).__name__}")
    parsed: Dict[str, Any] = {"action": "show", "enabled": None,
                              "model": None, "provider": None,
                              "base_url": None}
    stripped = text.strip()
    if not stripped:
        return parsed
    head, _, rest = stripped.partition(" ")
    head = head.lower()
    if head in ("on", "off"):
        if rest.strip():
            raise ValueError(f"Usage: /fallback {head}")
        parsed["action"] = "permission"
        parsed["enabled"] = head == "on"
        return parsed
    if head == "clear":
        if rest.strip():
            raise ValueError("Usage: /fallback clear")
        parsed["action"] = "clear"
        return parsed
    if head == "add":
        if not rest.strip():
            raise ValueError(
                "Usage: /fallback add <model> [url] or "
                "/fallback add --provider <name>")
        request = parse_switch_args(rest)
        if request["reason"] is not None:
            raise ValueError(
                "A fallback door takes no --reason; name the door "
                "with <model> [url] or --provider/--model/--base-url")
        parsed["action"] = "add"
        parsed["model"] = request["model"]
        parsed["provider"] = request["provider"]
        parsed["base_url"] = request["base_url"]
        return parsed
    if head == "show":
        if rest.strip():
            raise ValueError("Usage: /fallback")
        return parsed
    raise ValueError(
        f"Unknown fallback command {head!r}; use /fallback, "
        "/fallback on, /fallback off, /fallback add <model> [url] "
        "or /fallback clear")


def format_chain(config: Dict[str, Any]) -> str:
    """The visible chain: permission, current door, ordered doors."""
    permission = permission_from_config(config)
    entries = chain_from_config(config)
    current_model = config.get("model") or ""
    current_url = config.get("base_url") or ""
    current_provider = infer_provider(current_url)
    label = current_model
    if current_provider:
        label += f" via {current_provider}"
    lines = [
        "Fallback chain: standing permission "
        + ("ON — a failed provider request walks this chain, "
           "and every walk is announced."
           if permission else
           "OFF — provider failures are reported, never walked. "
           "Give standing permission with /fallback on."),
        f"  Current door: {label} ({current_url})",
    ]
    if not entries:
        lines.append(
            "  Chain: empty — add a door with "
            "/fallback add <model> [url] or "
            "/fallback add --provider <name>.")
    else:
        for index, entry in enumerate(entries, start=1):
            lines.append(f"  {index}. {entry.describe()}")
    return "\n".join(lines)


def format_walk(record: Dict[str, Any]) -> str:
    """The announcement of one walk — the sentence every surface shows.

    Names the door that failed and its error, the door being
    walked to and its place in the chain, so a walk can never
    pass unnoticed in the transcript.
    """
    before, after = record["from"], record["to"]
    def _describe(side: Dict[str, Any]) -> str:
        label = f"{side['model']}"
        if side.get("provider"):
            label += f" via {side['provider']}"
        return f"{label} ({side['base_url']})"
    return (f"Fallback walk {record['position']}: "
            f"{_describe(before)} failed — {record['error']} "
            f"Walking to {_describe(after)}. "
            "This walk is announced and journaled, never silent.")


def format_fallback_change(record: Dict[str, Any]) -> str:
    """One plain sentence describing a completed chain change."""
    if record["kind"] == "permission":
        if record["to"]:
            text = ("Standing fallback permission is now ON: when a "
                    "provider fails or rate-limits, the session "
                    "walks the configured chain, announcing every "
                    "walk.")
        else:
            text = ("Standing fallback permission is now OFF: "
                    "provider failures are reported and the chain "
                    "is never walked.")
    elif not record["to"]:
        text = "Fallback chain cleared: no doors remain to walk to."
    else:
        added = record["to"][-1]
        label = added["model"]
        if added.get("provider"):
            label += f" via {added['provider']}"
        text = (f"Fallback door added: {label} "
                f"({added['base_url']}) is now door "
                f"{len(record['to'])} in the chain.")
    if record.get("session_id"):
        text += f" Recorded on session {record['session_id']}."
    return text
