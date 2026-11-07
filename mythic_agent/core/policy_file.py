"""Policy as code: a checked-in project policy file (M-119).

Part V - Autonomy & Safety. The roadmap's words:
``project policies in a checked-in file (postures,
jails, hooks) so a team's rules travel with the
repo.``

What already shipped, and what this slice adds:

* Three Part V roads each hold one piece of a
  team's rules as validated config data: the
  permission profiles (M-095, ``core/
  permission_profiles.py``) bind a session's
  posture under the ``permission_profile`` setting
  (a shipped profile name, or a custom posture
  mapping held to the shipped vocabulary); the
  path jail (M-099, ``core/path_jail.py``) confines
  file tools under the ``path_jail`` gate and the
  ``path_grants`` list of absolute directory
  grants; and hooks (M-101, ``core/hooks.py``)
  hold user scripts riding lifecycle events under
  the ``hooks`` setting. Each road reads its piece
  from the session config - but nothing held the
  three pieces together in ONE file a project
  checks in, so a team's rules lived in each
  developer's local config instead of travelling
  with the repo.
* This slice is that one file, as a pure layer: a
  YAML policy file (``mythic-policy.yaml`` at the
  repo root) naming, in one place, the posture
  (by shipped profile name, or a custom posture in
  the exact M-095 shape), the jail posture and its
  grants (the exact M-099 shapes), and the hooks
  (the exact M-101 hook records as data). The
  layer validates the whole file against the
  shipped roads' own validators - it imports and
  reuses them, never a second drifting copy of
  their rules - and derives, mechanically, the
  application plan: the exact settings keys and
  values the agent layer would set, as data only.
  This module applies nothing, writes nothing
  into a live session, runs no hook and opens no
  session; the agent layer owns loading the file
  at session start and applying the plan through
  the existing journal-first setting roads.

Honesty rules, enforced here and pinned by tests:

* **No file means no policy, never an invented
  one.** A missing policy file loads as ``None``
  and yields no plan. An empty policy yields an
  empty plan. This layer invents no default
  posture, grant or hook of its own.
* **Unknown keys refuse.** A policy file may not
  silently invent settings: an unknown top-level
  key, an unknown jail key, or any key the
  composed roads themselves refuse, refuses the
  whole file.
* **A checked-in policy never loosens safety
  past the shipped roads.** The exact rule: the
  jail section may not turn the path jail off
  (``enabled: false`` refuses - the interactive
  ``/pathjail off`` road stays available to a
  person at the terminal, but a file that travels
  with the repo may not silently unconfine every
  checkout), and a grant may not name the
  filesystem root (a root grant nullifies the
  jail the file claims to set). When in doubt,
  this layer refuses rather than loosens.
* **The plan is data only, and complete.** Every
  section present in the file appears in the
  plan under the exact settings key its road
  consumes, and nothing absent appears. Applying
  the plan is the agent layer's work, not this
  layer's.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import yaml

from ..resources import load_resource
from .hooks import Hook, validate_hooks
from .hooks import SETTING_KEY as HOOKS_SETTING_KEY
from .path_jail import GRANTS_KEY, build_grants
from .path_jail import SETTING_KEY as JAIL_SETTING_KEY
from .permission_profiles import (
    SETTING_KEY as POSTURE_SETTING_KEY,
)
from .permission_profiles import Profile, profile_named, validate_profile
from .validation import ValidationError

__all__ = [
    "EXAMPLE_RESOURCE",
    "JAIL_KEYS",
    "PLAIN_EXPLANATION",
    "POLICY_FILENAME",
    "POLICY_FILE_SLICE",
    "POLICY_SCHEMA",
    "POLICY_SLICE",
    "TOP_LEVEL_KEYS",
    "USAGE",
    "Policy",
    "PolicyPlan",
    "PolicyRegistry",
    "application_plan",
    "build_plan",
    "default_policy_path",
    "format_plan",
    "format_policy",
    "format_policy_sections",
    "format_policy_screen",
    "load_example_policy",
    "load_policy_file",
    "parse_policy_args",
    "plain_words",
    "policy_record",
    "validate_policy",
]

POLICY_FILE_SLICE = "M-119"

#: The shorter name other layers cite for this slice.
POLICY_SLICE = POLICY_FILE_SLICE

#: The only schema this loader accepts.
POLICY_SCHEMA = "mythic.policy_file/1"

#: The checked-in policy file's name, at the repo root.
POLICY_FILENAME = "mythic-policy.yaml"

#: Resource name of the shipped example policy.
EXAMPLE_RESOURCE = "policy_example.yaml"

#: The top-level keys a policy file may name - no others.
TOP_LEVEL_KEYS = frozenset({"schema", "name", "posture", "jail", "hooks"})

#: The keys the jail section may name - no others.
JAIL_KEYS = frozenset({"enabled", "grants"})

_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")

PLAIN_EXPLANATION = (
    "Policy as code: one checked-in file "
    "(mythic-policy.yaml at the repo root) carries "
    "a team's rules - the permission posture, the "
    "path jail and its grants, and the hooks - in "
    "the exact shapes the shipped roads already "
    "consume, so the rules travel with the repo. "
    "This layer validates the file whole and "
    "derives the settings plan as data only; it "
    "applies nothing itself. No file means no "
    "policy and no plan - never an invented "
    "default."
)

USAGE = (
    "Usage: /policy, /policy show, /policy plan, "
    "/policy sections, /policy apply"
)


def _refuse(message: str) -> ValidationError:
    return ValidationError(message)


def _as_validation(exc: ValueError, what: str) -> ValidationError:
    """Re-raise a composed road's refusal as ValidationError."""
    if isinstance(exc, ValidationError):
        return exc
    return ValidationError(f"{what}: {exc}")


def default_policy_path(root: Any) -> Path:
    """The policy file path inside a repo *root*."""
    return Path(root) / POLICY_FILENAME


@dataclass(frozen=True)
class Policy:
    """One validated project policy, as data.

    Only the sections the file named are present:
    ``posture`` is the M-095 Profile the file
    resolved to (or None), ``jail_enabled`` /
    ``grants`` carry the M-099 section (both None
    when the file named no jail section; grants is
    the empty tuple when the section named none),
    and ``hooks`` is the M-101 hook tuple (or
    None). ``sections`` names the sections the
    file carried, in file order.
    """

    name: str
    posture: Optional[Profile]
    jail_enabled: Optional[bool]
    grants: Optional[Tuple[str, ...]]
    hooks: Optional[Tuple[Hook, ...]]
    sections: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "project_policy",
            "slice": POLICY_FILE_SLICE,
            "name": self.name,
            "sections": list(self.sections),
            "posture": (
                self.posture.to_record()
                if self.posture is not None else None),
            "jail_enabled": self.jail_enabled,
            "grants": (
                list(self.grants)
                if self.grants is not None else None),
            "hooks": (
                [hook.to_record() for hook in self.hooks]
                if self.hooks is not None else None),
        }


def _validate_posture(spec: Any) -> Profile:
    """The posture one file section names, via M-095 itself.

    A string names a shipped posture (profile_named);
    a mapping is a custom posture (validate_profile).
    Both are the shipped road's own validators - this
    layer adds no posture rule of its own.
    """
    try:
        if isinstance(spec, str):
            return profile_named(spec)
        if isinstance(spec, dict):
            return validate_profile(spec)
    except ValueError as exc:
        raise _as_validation(exc, "policy posture") from exc
    raise _refuse(
        "policy posture must be a shipped profile name or a "
        f"custom posture mapping, got {spec!r}")


def _validate_jail(spec: Any) -> Tuple[bool, Tuple[str, ...]]:
    """The jail section, via M-099's own grant validator.

    ``enabled`` defaults to True when the section
    omits it, and ``enabled: false`` REFUSES (the
    never-loosen rule in the module docstring).
    Grants validate through path_jail.build_grants
    itself; a grant naming the filesystem root
    refuses for the same reason.
    """
    if not isinstance(spec, dict):
        raise _refuse(f"policy jail must be a mapping, got {spec!r}")
    unknown = set(spec) - JAIL_KEYS
    if unknown:
        raise _refuse(
            "unknown policy jail keys: %s" % ", ".join(sorted(unknown)))
    enabled = spec.get("enabled", True)
    if not isinstance(enabled, bool):
        raise _refuse(
            f"policy jail enabled must be true or false, got {enabled!r}")
    if enabled is False:
        raise _refuse(
            "policy jail may not be turned off by a checked-in "
            "policy file: a travelling policy never unconfines "
            "the checkout (use /pathjail off interactively instead)")
    try:
        grants = build_grants(spec.get("grants"))
    except ValueError as exc:
        raise _as_validation(exc, "policy jail grants") from exc
    root = os.path.realpath(os.sep)
    for grant in grants:
        if grant == root:
            raise _refuse(
                "policy jail grant may not name the filesystem "
                "root: a root grant nullifies the jail")
    return enabled, grants


def _validate_hooks(spec: Any) -> Tuple[Hook, ...]:
    """The hooks section, via M-101's own validator."""
    try:
        return validate_hooks(spec)
    except ValueError as exc:
        raise _as_validation(exc, "policy hooks") from exc


def validate_policy(data: Any) -> Policy:
    """Validate one parsed policy mapping into a Policy.

    The mapping must carry the policy schema; every
    section present validates through its shipped
    road's own validator; unknown top-level keys
    refuse. An empty mapping is an empty policy
    (no sections, no plan) - stated plainly, never
    an invented default.
    """
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise _refuse(
            f"a policy file must be a mapping, got {type(data).__name__}")
    unknown = set(data) - TOP_LEVEL_KEYS
    if unknown:
        raise _refuse(
            "unknown policy keys: %s" % ", ".join(sorted(unknown)))
    if "schema" in data and data["schema"] != POLICY_SCHEMA:
        raise _refuse(
            f"policy schema must be {POLICY_SCHEMA!r}, "
            f"got {data['schema']!r}")
    name = data.get("name", "")
    if not isinstance(name, str):
        raise _refuse(f"policy name must be text, got {name!r}")
    name = name.strip()
    if name and (len(name) > 40 or not _NAME_RE.match(name)):
        raise _refuse(
            "policy name must be a lowercase slug of at most "
            f"40 characters, got {name!r}")
    sections = tuple(
        key for key in data if key in ("posture", "jail", "hooks"))
    posture = (
        _validate_posture(data["posture"]) if "posture" in data else None)
    jail_enabled: Optional[bool] = None
    grants: Optional[Tuple[str, ...]] = None
    if "jail" in data:
        jail_enabled, grants = _validate_jail(data["jail"])
    hooks = _validate_hooks(data["hooks"]) if "hooks" in data else None
    return Policy(
        name=name, posture=posture, jail_enabled=jail_enabled,
        grants=grants, hooks=hooks, sections=sections)


@dataclass(frozen=True)
class PolicyPlan:
    """The application plan: settings keys to values, as data.

    ``entries`` holds (settings key, value) pairs in
    the file's section order, under the exact keys
    the shipped roads consume: ``permission_profile``
    (a shipped profile id, or the custom posture
    mapping in the exact M-095 stored shape),
    ``path_jail`` + ``path_grants`` (M-099), and
    ``hooks`` (M-101 hook records). Nothing here is
    applied by this layer.
    """

    entries: Tuple[Tuple[str, Any], ...]

    def settings(self) -> Dict[str, Any]:
        """The plan as one config-shaped mapping."""
        return dict(self.entries)

    def keys(self) -> Tuple[str, ...]:
        return tuple(key for key, _ in self.entries)

    @property
    def empty(self) -> bool:
        return not self.entries

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "policy_application_plan",
            "slice": POLICY_FILE_SLICE,
            "settings": self.settings(),
            "keys": list(self.keys()),
        }


def _posture_setting(profile: Profile) -> Any:
    """The stored permission_profile value for one posture.

    A shipped posture stores as its id (the string
    stored_profile resolves by name); a custom
    posture stores whole, in the exact mapping shape
    validate_profile consumes, so the plan round-
    trips through the M-095 stored road unchanged.
    """
    if not profile.custom:
        return profile.id
    return {
        "name": profile.id,
        "title": profile.title,
        "tools": profile.tools,
        "paths": profile.paths,
        "network": profile.network,
        "commands": profile.commands,
    }


def application_plan(policy: Policy) -> PolicyPlan:
    """Derive the settings plan from one policy, mechanically.

    Every section the policy carries appears, in
    section order, and nothing else does: posture
    yields ``permission_profile``; jail yields
    ``path_jail`` and ``path_grants``; hooks yields
    ``hooks`` as M-101 hook records. An empty policy
    yields an empty plan. Data only - this judge
    applies nothing, writes nothing, runs no hook.
    """
    if not isinstance(policy, Policy):
        raise _refuse(f"a policy is needed, got {policy!r}")
    entries: list = []
    for section in policy.sections:
        if section == "posture":
            entries.append(
                (POSTURE_SETTING_KEY, _posture_setting(policy.posture)))
        elif section == "jail":
            entries.append((JAIL_SETTING_KEY, policy.jail_enabled))
            entries.append((GRANTS_KEY, list(policy.grants or ())))
        elif section == "hooks":
            entries.append(
                (HOOKS_SETTING_KEY,
                 [hook.to_record() for hook in (policy.hooks or ())]))
    return PolicyPlan(entries=tuple(entries))


#: The plan under its building name.
build_plan = application_plan


def load_policy_file(path: Any) -> Optional[Policy]:
    """Load the policy file at *path*, or None when absent.

    No file means no policy - stated plainly, never
    an invented default. A present file must parse
    as YAML and validate whole; malformed YAML and
    every validation refusal raise ValidationError
    naming the file. An empty file is an empty
    policy (no sections, no plan).
    """
    target = Path(path)
    if not target.exists():
        return None
    if not target.is_file():
        raise _refuse(f"policy path is not a file: {target}")
    try:
        raw = yaml.safe_load(target.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValidationError(
            f"malformed YAML in policy file {target}: {exc}") from exc
    try:
        return validate_policy(raw)
    except ValidationError as exc:
        raise ValidationError(
            f"invalid policy file {target}: {exc}") from exc


def load_example_policy() -> Policy:
    """The shipped example policy, loaded and validated."""
    return validate_policy(load_resource(EXAMPLE_RESOURCE))


def plain_words(policy: Policy) -> str:
    """One policy stated in one plain sentence."""
    if not policy.sections:
        return (
            "Project policy: no sections named - the file "
            "sets nothing.")
    parts = []
    if policy.posture is not None:
        parts.append(f"posture {policy.posture.title}")
    if policy.jail_enabled is not None:
        parts.append(
            f"path jail on with {len(policy.grants or ())} grant(s)")
    if policy.hooks is not None:
        parts.append(f"{len(policy.hooks)} hook(s)")
    label = policy.name or "unnamed"
    return f"Project policy {label}: " + "; ".join(parts) + "."


def policy_record(policy: Policy) -> Dict[str, Any]:
    """The policy shaped as a session-news record."""
    plan = application_plan(policy)
    return {
        "type": "project_policy",
        "session_event": "project_policy",
        "news": True,
        "slice": POLICY_FILE_SLICE,
        "name": policy.name,
        "sections": list(policy.sections),
        "plan_keys": list(plan.keys()),
        "headline": plain_words(policy),
    }


class PolicyRegistry:
    """An in-memory registry of policies, ids deterministic.

    Policies are held in registration order. Ids
    are deterministic: a caller-supplied id is used
    as given (a duplicate refuses), and an
    unsupplied id is the next ``policy-N`` in
    sequence, skipping any number a supplied id
    already took. Storage beyond memory is the
    agent layer's concern; this model is neutral.
    """

    def __init__(self) -> None:
        self._policies: Dict[str, Policy] = {}
        self._next = 1

    def _fresh_id(self) -> str:
        while f"policy-{self._next}" in self._policies:
            self._next += 1
        policy_id = f"policy-{self._next}"
        self._next += 1
        return policy_id

    def register(self, policy: Policy,
                 policy_id: Optional[str] = None) -> str:
        """Register one policy and hold it; duplicate ids refuse."""
        if not isinstance(policy, Policy):
            raise _refuse(f"a policy is needed, got {policy!r}")
        chosen = policy_id if policy_id is not None else self._fresh_id()
        if not isinstance(chosen, str) or not chosen.strip():
            raise _refuse(f"a policy id must be text, got {chosen!r}")
        chosen = chosen.strip()
        if chosen in self._policies:
            raise _refuse(f"a policy named {chosen!r} already exists")
        self._policies[chosen] = policy
        return chosen

    def get(self, policy_id: str) -> Policy:
        """The policy one id names; an unknown id raises KeyError."""
        if policy_id not in self._policies:
            raise KeyError(f"unknown policy: {policy_id!r}")
        return self._policies[policy_id]

    def policy_ids(self) -> Tuple[str, ...]:
        return tuple(self._policies)

    def list_policies(self) -> Tuple[Policy, ...]:
        """Every held policy, in registration order."""
        return tuple(self._policies.values())


# ---------------------------------------------------------------------
# The /policy surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------


def parse_policy_args(args: Any) -> Dict[str, Any]:
    """Parse the /policy grammar both surfaces share.

    No words (or ``show``) shows the policy;
    ``plan`` asks for the application plan;
    ``sections`` asks for the section list;
    ``apply`` (or ``load``) asks the agent layer
    to load the file on disk and apply its plan.
    Anything else is a usage error naming the
    grammar.
    """
    text = (args or "").strip().lower() if isinstance(args, str) else ""
    if not isinstance(args, str) and args is not None:
        raise _refuse(USAGE)
    if not text or text == "show":
        return {"action": "show"}
    if text == "plan":
        return {"action": "plan"}
    if text == "sections":
        return {"action": "sections"}
    if text in ("apply", "load"):
        return {"action": "apply"}
    raise _refuse(USAGE)


def format_policy(policy: Optional[Policy]) -> str:
    """One policy (or its absence), in plain words."""
    if policy is None:
        return (
            f"No project policy: no {POLICY_FILENAME} file - "
            "no policy, no plan, nothing invented.")
    lines = [plain_words(policy)]
    if policy.posture is not None:
        profile = policy.posture
        lines.append(
            f"  posture: {profile.title} ({profile.id}) - tools "
            f"{profile.tools}, paths {profile.paths}, network "
            f"{profile.network}, commands {profile.commands}")
    if policy.jail_enabled is not None:
        lines.append("  jail: on")
        for grant in policy.grants or ():
            lines.append(f"  grant: {grant}")
    if policy.hooks is not None:
        for hook in policy.hooks:
            state = "on" if hook.enabled else "off"
            lines.append(
                f"  hook: {hook.event} - {hook.label} ({state}, "
                f"{hook.timeout_seconds}s)")
    return "\n".join(lines)


def format_policy_sections(policy: Optional[Policy]) -> str:
    """The sections one policy names, in plain words."""
    if policy is None:
        return (
            f"No project policy: no {POLICY_FILENAME} file - "
            "no sections.")
    if not policy.sections:
        return (
            "Policy sections: none - the policy names no "
            "sections and sets nothing.")
    return "Policy sections: " + ", ".join(policy.sections) + "."


def format_plan(policy: Optional[Policy]) -> str:
    """The application plan, in plain words, keys and values."""
    if policy is None:
        return "No project policy: no plan."
    plan = application_plan(policy)
    if plan.empty:
        return "Policy plan: the policy names no sections; nothing to set."
    lines = ["Policy plan (data only - nothing applied):"]
    for key, value in plan.entries:
        lines.append(f"  {key} = {value!r}")
    return "\n".join(lines)


def format_policy_screen(policy: Optional[Policy]) -> str:
    """The whole slice, in plain words, for /policy."""
    lines = [
        "Policy as code (M-119) - " + PLAIN_EXPLANATION, "",
        format_policy(policy), "", format_plan(policy), "", USAGE]
    return "\n".join(lines)
