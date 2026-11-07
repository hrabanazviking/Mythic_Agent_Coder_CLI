"""Network gates: per-tool, per-domain allowlists (M-098).

Part V - Autonomy & Safety. The roadmap's words:
``outbound network per-tool and per-domain
allowlists; a sandboxed command that reaches for
the net is refused and the refusal is news, not a
log line.``

What already shipped, and what this slice adds:

* The elder ``core/sandbox.py`` runner marks a
  no-network run with an environment marker, the
  M-097 OS sandbox plan carries an explicit
  ``deny`` / ``allow`` network stance, and the
  M-095 permission profiles bind one network
  answer (``deny`` / ``ask`` / ``allow``) for the
  whole session. None of them answers the finer
  question this slice owns: may *this tool* reach
  *this domain*? A posture that allows the network
  still needs a gate that names which tools may
  go where, and a session-wide deny says nothing
  about which reach was refused, or why.
* This slice is that gate, as a pure layer: an
  allowlist of (tool, domain) entries, a mechanical
  check that decides allow or deny for one tool
  reaching for one host, and a refusal record
  shaped so the agent layer can surface a refusal
  as a session event - news the user sees - rather
  than a line buried in a log. This module writes
  no file, changes no setting, opens no socket and
  runs nothing itself; the agent layer owns
  holding the live allowlist, asking this gate
  before a reach, and publishing the refusal.

The matching rules, plainly:

* An entry names one tool and one domain. The
  tool ``*`` names every tool. Any other tool name
  matches only itself (case-insensitively).
* A plain domain (``example.com``) matches that
  host exactly - not its subdomains, not a longer
  name that merely ends with it.
* A wildcard domain (``*.example.com``) matches
  any subdomain of the base, at any depth, but
  never the base host itself.
* A reach is allowed only when some entry matches
  BOTH the tool and the host. Everything else is
  refused: the default posture is deny, fail-closed.

Honesty rules, enforced here and pinned by tests:

* **Default deny.** No matching entry means
  refusal - an empty allowlist refuses every
  outbound reach. Silence is never consent.
* **Malformed refuses.** A malformed allowlist
  entry raises instead of being skipped or
  guessed at; a target whose host cannot be read
  is refused, never waved through.
* **A refusal is news, not a log line.** Every
  denial can be rendered as a structured refusal
  record (``type: network_refusal``, ``news``
  true, surfaced as a session event) and as one
  plain headline naming the tool, the host and
  the reason. The pure layer builds that record;
  publishing it is the agent layer's duty.
* **Decisions are mechanical.** The check reads
  the allowlist and nothing else - no vibes, no
  reputation scores, no silent third state
  between allow and deny.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple
from urllib.parse import urlparse

__all__ = [
    "ALLOWLIST_KEY",
    "DECISIONS",
    "DEFAULT_DECISION",
    "ENTRY_KEYS",
    "NETWORK_GATES_SLICE",
    "PLAIN_EXPLANATION",
    "SETTING_KEY",
    "USAGE",
    "WILDCARD_TOOL",
    "AllowlistEntry",
    "GateChange",
    "NetworkDecision",
    "NetworkGates",
    "NetworkRefusal",
    "build_allowlist",
    "build_refusal",
    "check_network",
    "decide_network",
    "enabled_from_config",
    "entry_matches",
    "extract_host",
    "format_allowlist",
    "format_gate_change",
    "format_network_decision",
    "format_network_gates",
    "format_refusal",
    "gates_from_config",
    "normalize_domain_pattern",
    "normalize_host",
    "normalize_tool",
    "parse_network_args",
    "refusal_record",
    "set_enabled",
    "validate_entry",
]

NETWORK_GATES_SLICE = "M-098"

SETTING_KEY = "network_gates"

ALLOWLIST_KEY = "network_allowlist"

DECISIONS = ("allow", "deny")

#: The posture when no allowlist entry matches: refuse.
DEFAULT_DECISION = "deny"

WILDCARD_TOOL = "*"

ENTRY_KEYS = frozenset({"tool", "domain"})

_TOOL_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
_LABEL_RE = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$")
_IPV4_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")

PLAIN_EXPLANATION = (
    "Outbound network is gated per tool and per domain: "
    "a tool may reach only the domains its allowlist "
    "entries name, everything else is refused by "
    "default, and every refusal is surfaced as news - "
    "a session event naming the tool, the host and "
    "the reason - never just a log line. This layer "
    "holds the allowlist and decides; it opens no "
    "socket itself."
)

USAGE = (
    "Usage: /network, /network on, /network off, "
    "/network list, /network check <tool> <host-or-url>, "
    "/network allow <tool> <domain>"
)


def normalize_tool(name: Any) -> str:
    """One canonical tool name, or a plain refusal.

    ``*`` is the wildcard that names every tool.
    Anything else must be a plain tool slug -
    letters, digits, ``-`` and ``_`` - lowercased.
    """
    if not isinstance(name, str) or not name.strip():
        raise ValueError("an allowlist tool must be a non-empty string")
    wanted = name.strip().lower()
    if wanted == WILDCARD_TOOL:
        return wanted
    if not _TOOL_RE.match(wanted):
        raise ValueError(
            f"malformed allowlist tool {name!r}: a tool is a plain "
            "name of letters, digits, - and _, or * for every tool")
    return wanted


def _validate_host(host: str, what: str) -> str:
    if _IPV4_RE.match(host):
        if all(int(part) <= 255 for part in host.split(".")):
            return host
        raise ValueError(f"malformed {what} {host!r}: bad IPv4 address")
    labels = host.split(".")
    if len(labels) > 253 or any(
            not label or len(label) > 63 or not _LABEL_RE.match(label)
            for label in labels):
        raise ValueError(
            f"malformed {what} {host!r}: a host is dot-separated "
            "labels of letters, digits and hyphens")
    return host


def normalize_host(name: Any) -> str:
    """One canonical host name, or a plain refusal.

    Lowercased, trailing dot stripped. ``localhost``
    and IPv4 addresses are hosts too. No scheme, no
    port, no path - use ``extract_host`` for targets
    that carry those.
    """
    if not isinstance(name, str) or not name.strip():
        raise ValueError("a host must be a non-empty string")
    host = name.strip().lower().rstrip(".")
    if not host or "://" in host or "/" in host or ":" in host \
            or any(ch.isspace() for ch in host):
        raise ValueError(
            f"malformed host {name!r}: expected a bare host name")
    return _validate_host(host, "host")


def normalize_domain_pattern(name: Any) -> str:
    """One canonical allowlist domain, or a refusal.

    Either a plain host (exact match only) or
    ``*.`` in front of a host (any subdomain of
    that base, never the base itself). A bare ``*``,
    a doubled wildcard, or a malformed host refuses.
    """
    if not isinstance(name, str) or not name.strip():
        raise ValueError("an allowlist domain must be a non-empty string")
    wanted = name.strip().lower().rstrip(".")
    if wanted.startswith("*."):
        base = wanted[2:]
        if not base or "*" in base:
            raise ValueError(
                f"malformed allowlist domain {name!r}: a wildcard "
                "is *. followed by one plain domain")
        return "*." + _validate_host(base, "allowlist domain")
    if "*" in wanted:
        raise ValueError(
            f"malformed allowlist domain {name!r}: the only "
            "wildcard is a leading *.")
    return _validate_host(wanted, "allowlist domain")


def extract_host(target: Any) -> str:
    """The host a reach is headed for, or a refusal.

    Accepts a bare host, a ``host:port``, or a full
    URL with a scheme; userinfo, port, path, query
    and fragment are not the destination and are
    set aside. A target with no readable host
    refuses - the gate never guesses a destination.
    """
    if not isinstance(target, str) or not target.strip():
        raise ValueError("a network target must be a non-empty string")
    text = target.strip()
    if "://" in text:
        host = urlparse(text).hostname
        if not host:
            raise ValueError(
                f"could not read a host from the target {target!r}")
        return normalize_host(host)
    bare = text.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0]
    bare = bare.rsplit("@", 1)[-1]
    if bare.startswith("["):
        raise ValueError(
            f"could not read a host from the target {target!r}: "
            "IPv6 targets are not gated by this layer yet")
    if ":" in bare:
        bare = bare.split(":", 1)[0]
    return normalize_host(bare)


@dataclass(frozen=True)
class AllowlistEntry:
    """One allowlist grant: this tool may reach this domain."""

    tool: str
    domain: str

    def to_record(self) -> Dict[str, Any]:
        return {"tool": self.tool, "domain": self.domain}


def validate_entry(spec: Any) -> AllowlistEntry:
    """Validate one allowlist entry, or refuse it plainly.

    An entry is an ``AllowlistEntry``, a mapping with
    exactly the keys ``tool`` and ``domain``, or the
    text form ``<tool>:<domain>``. Unknown keys,
    missing keys, a malformed tool and a malformed
    domain all refuse - a bad entry is never skipped
    or repaired by guessing.
    """
    if isinstance(spec, AllowlistEntry):
        return AllowlistEntry(
            tool=normalize_tool(spec.tool),
            domain=normalize_domain_pattern(spec.domain))
    if isinstance(spec, str):
        tool, sep, domain = spec.partition(":")
        if not sep or not tool.strip() or not domain.strip():
            raise ValueError(
                f"malformed allowlist entry {spec!r}: the text "
                "form is <tool>:<domain>")
        return AllowlistEntry(
            tool=normalize_tool(tool),
            domain=normalize_domain_pattern(domain))
    if isinstance(spec, dict):
        unknown = set(spec) - ENTRY_KEYS
        if unknown:
            raise ValueError(
                "an allowlist entry names unknown keys: "
                + ", ".join(sorted(unknown)))
        missing = ENTRY_KEYS - set(spec)
        if missing:
            raise ValueError(
                "an allowlist entry is missing keys: "
                + ", ".join(sorted(missing)))
        return AllowlistEntry(
            tool=normalize_tool(spec["tool"]),
            domain=normalize_domain_pattern(spec["domain"]))
    raise ValueError(
        f"an allowlist entry must be a mapping or text, got {spec!r}")


def build_allowlist(specs: Any) -> Tuple[AllowlistEntry, ...]:
    """Validate a whole allowlist, in order, duplicates dropped.

    Every entry must validate; one malformed entry
    refuses the whole list rather than silently
    narrowing what the user wrote.
    """
    if specs is None:
        return ()
    if not isinstance(specs, (list, tuple)):
        raise ValueError("an allowlist must be a list of entries")
    entries: List[AllowlistEntry] = []
    for spec in specs:
        entry = validate_entry(spec)
        if entry not in entries:
            entries.append(entry)
    return tuple(entries)


def _domain_matches(pattern: str, host: str) -> bool:
    if pattern.startswith("*."):
        base = pattern[2:]
        return host != base and host.endswith("." + base)
    return host == pattern


def entry_matches(entry: AllowlistEntry, tool: Any, host: Any) -> bool:
    """Whether one entry grants *tool* a reach to *host*.

    Both halves must match: the tool exactly (or the
    entry is the wildcard tool) and the domain by
    the plain / wildcard rules in the module docstring.
    Bad inputs raise - matching is never guessed.
    """
    wanted_tool = normalize_tool(tool)
    wanted_host = normalize_host(host)
    if entry.tool != WILDCARD_TOOL and entry.tool != wanted_tool:
        return False
    return _domain_matches(entry.domain, wanted_host)


@dataclass(frozen=True)
class NetworkDecision:
    """The gate's mechanical answer for one reach."""

    decision: str
    tool: str
    host: Optional[str]
    target: str
    reason: str
    matched_entry: Optional[AllowlistEntry]

    @property
    def allowed(self) -> bool:
        return self.decision == "allow"

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "network_decision",
            "slice": NETWORK_GATES_SLICE,
            "decision": self.decision,
            "tool": self.tool,
            "host": self.host,
            "target": self.target,
            "reason": self.reason,
            "matched_entry": (
                self.matched_entry.to_record()
                if self.matched_entry is not None else None),
        }


@dataclass(frozen=True)
class NetworkGates:
    """The whole gate as data: the entries, nothing else.

    The default posture is deny and is not a field:
    a reach no entry grants is refused, always.
    """

    entries: Tuple[AllowlistEntry, ...] = ()

    def check(self, tool: Any, target: Any) -> NetworkDecision:
        return check_network(tool, target, self.entries)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "network_gates",
            "slice": NETWORK_GATES_SLICE,
            "default": DEFAULT_DECISION,
            "entries": [e.to_record() for e in self.entries],
        }


def check_network(
    tool: Any,
    target: Any,
    entries: Sequence[AllowlistEntry] = (),
) -> NetworkDecision:
    """Decide one outbound reach, mechanically.

    Allow requires an entry matching both the tool
    and the target's host. A malformed tool raises
    (the caller named no real tool); a target whose
    host cannot be read is *refused*, not raised -
    an unreadable destination is exactly what a
    fail-closed gate must stop. Nothing is opened,
    written or sent here.
    """
    wanted_tool = normalize_tool(tool)
    target_text = target if isinstance(target, str) else repr(target)
    try:
        host = extract_host(target)
    except ValueError as exc:
        return NetworkDecision(
            decision="deny", tool=wanted_tool, host=None,
            target=target_text,
            reason=f"refused: {exc}", matched_entry=None)
    for entry in entries:
        if entry_matches(entry, wanted_tool, host):
            return NetworkDecision(
                decision="allow", tool=wanted_tool, host=host,
                target=target_text,
                reason=(
                    f"allowed: the allowlist entry "
                    f"{entry.tool}:{entry.domain} grants tool "
                    f"{wanted_tool!r} a reach to {host!r}"),
                matched_entry=entry)
    return NetworkDecision(
        decision="deny", tool=wanted_tool, host=host,
        target=target_text,
        reason=(
            f"refused: no allowlist entry grants tool "
            f"{wanted_tool!r} a reach to {host!r}; network "
            "gates deny by default"),
        matched_entry=None)


#: The decision under its decision-shaped name.
decide_network = check_network


@dataclass(frozen=True)
class NetworkRefusal:
    """One refusal, shaped as news for the session.

    The agent layer publishes this record as a
    session event; ``news`` is true and ``surface``
    names that road so no surface can mistake a
    refusal for an ordinary log line.
    """

    tool: str
    host: Optional[str]
    target: str
    command: Optional[str]
    reason: str

    @property
    def headline(self) -> str:
        where = self.host if self.host is not None else self.target
        return (
            f"Network refusal: tool {self.tool!r} was refused "
            f"a reach to {where!r} - {self.reason}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "network_refusal",
            "slice": NETWORK_GATES_SLICE,
            "news": True,
            "surface": "session_event",
            "tool": self.tool,
            "host": self.host,
            "target": self.target,
            "command": self.command,
            "reason": self.reason,
            "headline": self.headline,
        }


def build_refusal(
    decision: NetworkDecision,
    *,
    command: Any = None,
) -> NetworkRefusal:
    """The refusal record for a denied decision.

    An allowed decision has no refusal; asking for
    one raises instead of dressing an allow up as
    news it is not.
    """
    if decision.allowed:
        raise ValueError("an allowed reach has no refusal")
    if command is not None and not isinstance(command, str):
        raise ValueError("a refusal command must be text or None")
    return NetworkRefusal(
        tool=decision.tool, host=decision.host,
        target=decision.target, command=command,
        reason=decision.reason)


def refusal_record(
    decision: NetworkDecision,
    *,
    command: Any = None,
) -> Dict[str, Any]:
    """The journal-shaped record of one refusal."""
    return build_refusal(decision, command=command).to_record()


def enabled_from_config(config: Dict[str, Any]) -> bool:
    """The network_gates gate stored in *config*.

    Absent means True (the gate ships on). A stored
    value that is not a bool raises - never guessed
    at. With the gate off the agent layer says so
    plainly; the allowlist and the check stay
    readable either way.
    """
    raw = config.get(SETTING_KEY, True)
    if not isinstance(raw, bool):
        raise ValueError(
            f"{SETTING_KEY} must be true or false, "
            f"got {type(raw).__name__}")
    return raw


def gates_from_config(config: Dict[str, Any]) -> NetworkGates:
    """The gate *config* holds, validated whole.

    The allowlist rides under ``network_allowlist``
    as a list of entries; absent means empty, and
    an empty allowlist refuses every reach. A
    malformed stored entry raises - the stored
    gate is never silently narrowed.
    """
    return NetworkGates(entries=build_allowlist(config.get(ALLOWLIST_KEY)))


@dataclass(frozen=True)
class GateChange:
    """A recorded change of the network_gates gate."""

    before: bool
    after: bool

    def event(self) -> Dict[str, Any]:
        return {"type": "network_gates_setting_changed",
                "from": self.before, "to": self.after}

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        return {"type": "network_gates_setting_changed",
                "from": self.before, "to": self.after,
                "session_id": session_id, "journaled": journaled}


def set_enabled(config: Dict[str, Any],
                enabled: Any) -> Tuple[bool, GateChange]:
    """Validate a gate change against *config*, purely."""
    if not isinstance(enabled, bool):
        raise ValueError(
            f"{SETTING_KEY} is turned on or off; got {enabled!r}")
    before = enabled_from_config(config)
    if enabled == before:
        raise ValueError(
            f"the network gates are already {'on' if before else 'off'}")
    return enabled, GateChange(before=before, after=enabled)


# ---------------------------------------------------------------------
# The /network surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------

def parse_network_args(args: str) -> Dict[str, Any]:
    """Parse the /network grammar both surfaces share.

    No words (or ``show``) shows the slice; ``on`` /
    ``off`` steer the gate; ``list`` asks for the
    allowlist; ``check <tool> <target>`` decides one
    reach; ``allow <tool> <domain>`` names one entry
    (validated here, stored by the agent layer).
    Anything else is a usage error naming the grammar.
    """
    text = (args or "").strip()
    if not text or text == "show":
        return {"action": "show"}
    if text == "on":
        return {"action": "on"}
    if text == "off":
        return {"action": "off"}
    if text == "list":
        return {"action": "list"}
    words = text.split()
    if words[0] == "check":
        if len(words) != 3:
            raise ValueError(USAGE)
        return {"action": "check", "tool": normalize_tool(words[1]),
                "target": words[2]}
    if words[0] == "allow":
        if len(words) != 3:
            raise ValueError(USAGE)
        entry = validate_entry({"tool": words[1], "domain": words[2]})
        return {"action": "allow", "entry": entry.to_record()}
    raise ValueError(USAGE)


def format_gate_change(record: Dict[str, Any]) -> str:
    state = "on" if record.get("to") else "off"
    return f"The network gates are now {state}."


def format_allowlist(entries: Sequence[AllowlistEntry]) -> str:
    """The allowlist, in plain words, from the entries."""
    if not entries:
        return (
            "Network allowlist: empty - every outbound "
            "reach is refused by default.")
    lines = ["Network allowlist:"]
    for entry in entries:
        lines.append(f"  {entry.tool}: {entry.domain}")
    return "\n".join(lines)


def format_network_decision(decision: NetworkDecision) -> str:
    """One decision, in plain words, from the decision."""
    if decision.allowed:
        return f"Network allowed: {decision.reason}."
    return build_refusal(decision).headline + "."


def format_refusal(refusal: Any) -> str:
    """One refusal as the headline the session shows.

    Accepts a ``NetworkRefusal`` or its record; the
    headline names the tool, the host and the reason
    - the refusal is news, stated like news.
    """
    if isinstance(refusal, NetworkRefusal):
        return refusal.headline
    if isinstance(refusal, dict) and refusal.get("type") == "network_refusal":
        return str(refusal["headline"])
    raise ValueError("format_refusal needs a network refusal")


def format_network_gates(config: Dict[str, Any]) -> str:
    """The whole slice, in plain words, for /network.

    Built from the stored gate and allowlist plus a
    sample refused reach, so the show surface
    exercises the refusal road it names and can
    never drift from the gate itself.
    """
    enabled = enabled_from_config(config)
    gates = gates_from_config(config)
    lines = ["Network gates (M-098) - " + PLAIN_EXPLANATION, ""]
    lines.append(
        f"Setting: {'on' if enabled else 'off'} ({SETTING_KEY}).")
    lines.append("Default posture: deny (fail-closed).")
    lines.append("")
    lines.append(format_allowlist(gates.entries))
    lines.append("")
    sample = check_network("curl", "https://example.com", gates.entries)
    lines.append("Sample check (curl -> example.com): "
                 + format_network_decision(sample))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)
