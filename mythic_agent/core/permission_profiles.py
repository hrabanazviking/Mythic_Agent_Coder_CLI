"""Permission profiles (roadmap slice M-095).

Part V - Autonomy & Safety. The roadmap's words:
``named postures (Read-Only Scout, Trusted Forge,
Full Autonomy, and custom) binding tools, paths,
network, and commands; the posture is always
visible in the status line.``

What already shipped, and what this slice adds:

* The elder ``core/policy.py`` ToolPolicy knows
  three modes (read-only, ask, trusted) and one
  read-only tool list, but a mode is an answer to
  one question - may this tool run - while a user
  thinks in postures: what may this session touch,
  where may it write, may it reach the network,
  may it run commands. Nothing named a posture,
  nothing bound the four answers together, and
  nothing promised the posture a permanent place
  on the status line.
* This slice is that naming, as a pure layer. A
  profile binds four things - tools, paths,
  network, commands - each from a small fixed
  vocabulary. Three postures ship by name; a
  custom posture is a plain mapping held to the
  same vocabulary and the same validation. The
  layer decides mechanically (allow, ask, deny)
  and formats the one status-line sentence every
  surface shows. This module writes no file,
  changes no setting and runs nothing itself;
  the agent layer owns applying a chosen profile
  to the live ToolPolicy road.

Honesty rules, enforced here and pinned by tests:

* **A posture binds exactly four things.** Tools,
  paths, network, commands - no fifth binding is
  smuggled in, and a custom spec naming an
  unknown key refuses instead of ignoring it.
* **Decisions are mechanical, never vibes.** Each
  binding answers from its vocabulary alone: a
  read-only posture denies a writing tool because
  the tool is not a read tool, never because the
  layer dislikes the call.
* **Ask is a real answer, kept as one.** A binding
  set to ``ask`` decides ``ask`` - it is not
  quietly rounded up to allow or down to deny.
* **The default is named, not hidden.** With no
  stored profile, the posture is Trusted Forge -
  the posture whose answers match the elder
  road's standing ``ask`` default. A malformed
  stored profile raises, never defaults silently.
* **A custom name cannot impersonate a shipped
  one.** A custom id colliding with a built-in
  id refuses; the shipped postures keep their
  own meanings.
* **The posture is always sayable in one line.**
  ``format_permission_profile`` renders the one
  sentence the status line carries, from the
  profile itself - never from a second source
  that could drift away from the bindings.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

__all__ = [
    "BUILTIN_PROFILE_IDS",
    "CUSTOM_PROFILE_KEYS",
    "DEFAULT_PROFILE_ID",
    "NETWORK_ANSWERS",
    "PATH_ANSWERS",
    "PERMISSION_PROFILES_SLICE",
    "PLAIN_EXPLANATION",
    "Profile",
    "SETTING_KEY",
    "TOOL_ANSWERS",
    "USAGE",
    "builtin_profile",
    "decide",
    "format_permission_profile",
    "format_permission_profiles",
    "format_profile_change",
    "parse_posture_args",
    "policy_mode_for",
    "profile_change_record",
    "profile_named",
    "stored_profile",
    "validate_profile",
]

PERMISSION_PROFILES_SLICE = "M-095"

SETTING_KEY = "permission_profile"

DEFAULT_PROFILE_ID = "trusted-forge"

TOOL_ANSWERS = ("read_only", "all")
PATH_ANSWERS = ("read", "write")
NETWORK_ANSWERS = ("deny", "ask", "allow")
COMMAND_ANSWERS = ("deny", "ask", "allow")

CUSTOM_PROFILE_KEYS = frozenset(
    {"name", "title", "tools", "paths", "network", "commands"}
)

_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")

PLAIN_EXPLANATION = (
    "A permission profile is the session's posture: one named "
    "answer to what it may do - which tools, whether it may "
    "write, whether it may reach the network, and whether it "
    "may run commands. The posture rides the status line so "
    "it is never a surprise."
)


@dataclass(frozen=True)
class Profile:
    """One named posture: four bindings, nothing else."""

    id: str
    title: str
    tools: str
    paths: str
    network: str
    commands: str
    custom: bool = False

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "permission_profile",
            "id": self.id,
            "title": self.title,
            "tools": self.tools,
            "paths": self.paths,
            "network": self.network,
            "commands": self.commands,
            "custom": self.custom,
        }


_BUILTINS: Tuple[Profile, ...] = (
    Profile(
        id="read-only-scout",
        title="Read-Only Scout",
        tools="read_only",
        paths="read",
        network="deny",
        commands="deny",
    ),
    Profile(
        id="trusted-forge",
        title="Trusted Forge",
        tools="all",
        paths="write",
        network="ask",
        commands="ask",
    ),
    Profile(
        id="full-autonomy",
        title="Full Autonomy",
        tools="all",
        paths="write",
        network="allow",
        commands="allow",
    ),
)

BUILTIN_PROFILE_IDS = tuple(p.id for p in _BUILTINS)


def builtin_profile(profile_id: str) -> Profile:
    """The shipped posture with this exact id (raises if none)."""
    for profile in _BUILTINS:
        if profile.id == profile_id:
            return profile
    raise ValueError(
        "unknown built-in permission profile: %r (known: %s)"
        % (profile_id, ", ".join(BUILTIN_PROFILE_IDS))
    )


def profile_named(name: Any) -> Profile:
    """Resolve a shipped posture by id or title, case-insensitively."""
    if not isinstance(name, str) or not name.strip():
        raise ValueError("permission profile name must be a non-empty string")
    wanted = name.strip().lower()
    for profile in _BUILTINS:
        if wanted in (profile.id, profile.title.lower()):
            return profile
    raise ValueError(
        "unknown permission profile: %r (known: %s)"
        % (name, ", ".join(BUILTIN_PROFILE_IDS))
    )


def _check_answer(field: str, value: Any, answers: Tuple[str, ...]) -> str:
    if value not in answers:
        raise ValueError(
            "permission profile %s must be one of %s, got %r"
            % (field, "/".join(answers), value)
        )
    return value


def validate_profile(spec: Any) -> Profile:
    """Validate a custom posture mapping into a Profile.

    Every binding is required, every value must come from its
    binding's vocabulary, unknown keys refuse, and the custom
    id may not reuse a shipped posture's id.
    """
    if not isinstance(spec, dict):
        raise ValueError("a custom permission profile must be a mapping")
    unknown = set(spec) - CUSTOM_PROFILE_KEYS
    if unknown:
        raise ValueError(
            "unknown permission profile keys: %s" % ", ".join(sorted(unknown))
        )
    missing = CUSTOM_PROFILE_KEYS - set(spec)
    if missing:
        raise ValueError(
            "custom permission profile is missing: %s"
            % ", ".join(sorted(missing))
        )
    name = spec["name"]
    if (
        not isinstance(name, str)
        or len(name) > 40
        or not _NAME_RE.match(name)
    ):
        raise ValueError(
            "custom permission profile name must be a lowercase slug "
            "of at most 40 characters, got %r" % (name,)
        )
    if name in BUILTIN_PROFILE_IDS:
        raise ValueError(
            "custom permission profile may not reuse the shipped "
            "posture id %r" % (name,)
        )
    title = spec["title"]
    if not isinstance(title, str) or not title.strip() or len(title) > 80:
        raise ValueError(
            "custom permission profile title must be a non-empty "
            "string of at most 80 characters"
        )
    return Profile(
        id=name,
        title=title.strip(),
        tools=_check_answer("tools", spec["tools"], TOOL_ANSWERS),
        paths=_check_answer("paths", spec["paths"], PATH_ANSWERS),
        network=_check_answer("network", spec["network"], NETWORK_ANSWERS),
        commands=_check_answer("commands", spec["commands"], COMMAND_ANSWERS),
        custom=True,
    )


def stored_profile(config: Dict[str, Any]) -> Profile:
    """The posture *config* holds: named, custom, or the default.

    Absent setting -> Trusted Forge (named in the module
    docstring, never a silent invention). A stored string must
    name a shipped posture; a stored mapping must validate as
    a custom posture; anything else raises.
    """
    value = config.get(SETTING_KEY)
    if value is None:
        return builtin_profile(DEFAULT_PROFILE_ID)
    if isinstance(value, str):
        return profile_named(value)
    if isinstance(value, dict):
        return validate_profile(value)
    raise ValueError(
        "stored %s must be a profile name or a custom profile "
        "mapping, got %r" % (SETTING_KEY, value)
    )


def decide(
    profile: Profile, kind: str, *, read_only_tool: bool = False
) -> str:
    """One mechanical answer: ``allow``, ``ask`` or ``deny``.

    Kinds: ``tool`` (a tool call; *read_only_tool* says whether
    the tool only reads), ``path_read``, ``path_write``,
    ``network``, ``command``. An unknown kind raises - a
    question the posture does not cover is never guessed at.
    """
    if kind == "tool":
        if profile.tools == "all" or read_only_tool:
            return "allow"
        return "deny"
    if kind == "path_read":
        return "allow"
    if kind == "path_write":
        return "allow" if profile.paths == "write" else "deny"
    if kind == "network":
        return profile.network
    if kind == "command":
        return profile.commands
    raise ValueError("unknown permission decision kind: %r" % (kind,))


def policy_mode_for(profile: Profile) -> str:
    """The elder ToolPolicy mode this posture rides as.

    Mechanical: a read-only-tools posture is ``read-only``; a
    posture that allows tools, network and commands outright
    is ``trusted``; everything between asks.
    """
    if profile.tools == "read_only":
        return "read-only"
    if profile.network == "allow" and profile.commands == "allow":
        return "trusted"
    return "ask"


def profile_change_record(
    previous: Optional[Profile], current: Profile
) -> Dict[str, Any]:
    """The journal-shaped record of a posture change."""
    return {
        "type": "permission_profile_changed",
        "from": previous.id if previous is not None else None,
        "to": current.id,
        "record": current.to_record(),
    }


def _tools_word(profile: Profile) -> str:
    return "read-only" if profile.tools == "read_only" else "all"


def _paths_word(profile: Profile) -> str:
    return "read-only" if profile.paths == "read" else "read-write"


def format_permission_profile(config: Dict[str, Any]) -> str:
    """The status line's one sentence for the stored posture."""
    profile = stored_profile(config)
    return (
        "Posture: %s (tools: %s · paths: %s · network: %s · "
        "commands: %s)"
        % (
            profile.title,
            _tools_word(profile),
            _paths_word(profile),
            profile.network,
            profile.commands,
        )
    )

USAGE = ("Usage: /posture, /posture show, "
         "/posture <profile name>, or /posture custom "
         "<name> | <title> | <tools> | <paths> | "
         "<network> | <commands>")

_CUSTOM_FIELDS = ("name", "title", "tools", "paths",
                  "network", "commands")


def parse_posture_args(args: str) -> Dict[str, Any]:
    """Parse the /posture grammar both surfaces share.

    No words (or ``show``) shows the current posture;
    ``custom`` followed by six pipe-separated fields
    builds a custom posture through validate_profile;
    anything else names a shipped posture, resolved by
    profile_named - an unknown name refuses with the
    shipped names listed, never a guess.
    """
    text = (args or "").strip()
    if not text or text.lower() == "show":
        return {"action": "show"}
    lowered = text.lower()
    if lowered == "custom" or lowered.startswith("custom "):
        rest = text[len("custom"):].strip()
        fields = [part.strip() for part in rest.split("|")]
        if len(fields) != len(_CUSTOM_FIELDS) or not all(fields):
            raise ValueError(f"usage: {USAGE}")
        spec = dict(zip(_CUSTOM_FIELDS, fields))
        return {"action": "set", "profile": validate_profile(spec)}
    return {"action": "set", "profile": profile_named(text)}


def format_profile_change(record: Dict[str, Any]) -> str:
    """The one sentence a posture change answers with."""
    profile = record.get("record") or {}
    title = profile.get("title") or record.get("to")
    return f"Posture is now {title} ({record.get('to')})."


def format_permission_profiles(config: Dict[str, Any]) -> str:
    """The whole slice, in plain words, for /posture.

    The current posture's line and every shipped
    posture's line are rendered by
    format_permission_profile itself, so the show
    surface can never drift from the status line.
    """
    current = stored_profile(config)
    lines = ["Permission profiles (M-095) - "
             + PLAIN_EXPLANATION, ""]
    lines.append(format_permission_profile(config))
    lines.append(
        f"Tool policy mode: {policy_mode_for(current)} "
        f"({SETTING_KEY}).")
    lines.append("")
    lines.append("Shipped postures:")
    for profile_id in BUILTIN_PROFILE_IDS:
        lines.append("  " + format_permission_profile(
            {SETTING_KEY: profile_id}))
    if current.custom:
        lines.append(
            "The current posture is custom; it is stored "
            "whole under permission_profile.")
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)
