"""Path jail: file tools confined to the workspace + grants (M-099).

Part V - Autonomy & Safety. The roadmap's words:
``file tools confined to the workspace + named
grants; escapes by symlink are checked, not
assumed away.``

What already shipped, and what this slice adds:

* The elder ``core/workspace.py`` already resolves
  one file path against one workspace root:
  ``resolve_file`` (and ``assert_within_workspace``
  / ``canonical_workspace_root`` beside it) resolves
  symlinks with ``Path.resolve`` and raises a
  ``SecurityError`` when the result escapes the
  root. The live file tools ride that road today -
  ``agents/tools.py`` resolves each read and write
  through it, and ``core/validation.py`` checks
  file-tool arguments against the workspace the
  same way. That road knows exactly one root,
  answers by raising, and carries extra
  write-specific refusals of its own (the workspace
  root itself and ``.git`` on writes). It has no
  named grants beyond the workspace, no allow /
  deny decision a surface can show, no stored gate,
  and no shared ``/pathjail`` grammar.
* The M-095 permission profiles bind ``paths`` as
  one coarse posture word (``read`` / ``write``) for
  the whole session, and the elder ``core/policy.py``
  ``ToolPolicy`` authorizes tools by name and mode
  only. Neither judges a single candidate path
  against named places. ``core/sandbox.py`` guards
  commands and the M-097 OS sandbox plans command
  confinement; neither confines file-tool paths.
* This slice is that missing judge, as a pure
  layer: one mechanical decision for one candidate
  path against the workspace root plus the named
  grant roots, with symlinks RESOLVED before
  judging. The decision is data (allow / deny, the
  resolved path, which root granted it, or the
  refusal reason), the grants and the gate are
  validated config readers, and the ``/pathjail``
  parser and formatters are shared by both roads.
  This module writes no file, changes no setting,
  opens nothing and runs nothing itself; the agent
  layer owns holding the live workspace root,
  asking this jail before a file tool touches a
  path, and storing grants and the gate. The elder
  ``resolve_file`` road keeps its own write rules;
  the jail is the confinement judge, not a
  replacement for them.

The judging rules, plainly:

* A relative candidate is resolved against the
  workspace root; an absolute candidate stands as
  given. Either way the candidate is then resolved
  with ``os.path.realpath`` BEFORE judging, so a
  symlinked directory inside the workspace that
  points outside is judged by where it truly
  leads - the escape is caught by resolution,
  never assumed away - and ``..`` traversal is
  judged on the resolved path for the same reason.
* Allow requires the resolved path to be the
  workspace root itself or inside it, or a grant
  root itself or inside it. Inside is judged on
  path components (a separator boundary, via
  ``os.path.commonpath``): a sibling directory
  that merely shares a name prefix - ``/ws2``
  beside ``/ws`` - is NOT inside ``/ws``.
* A grant is one absolute directory path. Grants
  are directory prefixes: a grant names a
  directory and allows exactly its subtree.
  Whether a named path is a file or a directory
  on disk is data the layer does not check - the
  prefix is what is judged.

Honesty rules, enforced here and pinned by tests:

* **Default deny, fail-closed.** A resolved path
  inside neither the workspace nor any grant is
  refused. Silence is never consent.
* **Symlinks are resolved, never assumed.** For a
  candidate that does not exist yet, ``realpath``
  resolves the deepest existing ancestor and
  judges the remaining tail lexically beneath it.
  That is stated, not hidden: a tail that does
  not exist cannot itself be a symlink, so the
  resolved prefix is the whole of the escape
  question - and the moment any part of it exists
  as a link, resolution follows it.
* **Malformed candidates are denied, malformed
  stored data raises.** An empty, non-text or
  NUL-bearing candidate is refused as a decision
  - a file tool naming no readable path is exactly
  what a fail-closed jail must stop. A malformed
  workspace root or grant (relative grant, empty,
  wrong type) raises instead of being skipped or
  guessed at: stored data is never silently
  narrowed.
* **Decisions are mechanical.** The check reads
  the resolved path, the workspace root and the
  grant roots - nothing else. No reputation, no
  vibes, no silent third state between allow
  and deny.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional, Sequence, Tuple

__all__ = [
    "DECISIONS",
    "DEFAULT_DECISION",
    "GRANTS_KEY",
    "PATH_JAIL_SLICE",
    "PLAIN_EXPLANATION",
    "SETTING_KEY",
    "USAGE",
    "GateChange",
    "JailDecision",
    "JailRefusal",
    "PathJail",
    "build_grants",
    "build_refusal",
    "check_path",
    "decide_path",
    "enabled_from_config",
    "format_gate_change",
    "format_grants",
    "format_jail_decision",
    "format_path_jail",
    "format_refusal",
    "grants_from_config",
    "is_within",
    "jail_from_config",
    "normalize_grant",
    "parse_pathjail_args",
    "refusal_record",
    "resolve_workspace_root",
    "set_enabled",
    "validate_grant",
]

PATH_JAIL_SLICE = "M-099"

SETTING_KEY = "path_jail"

GRANTS_KEY = "path_grants"

DECISIONS = ("allow", "deny")

#: The posture when no root grants a path: refuse.
DEFAULT_DECISION = "deny"

PLAIN_EXPLANATION = (
    "File tools are jailed to the workspace plus named "
    "grants: a path is allowed only when, after every "
    "symlink on it is resolved, it lands inside the "
    "workspace or inside a granted directory; "
    "everything else is refused by default, and an "
    "escape hidden behind a symlink is caught by "
    "resolving it, never assumed away. This layer "
    "judges paths; it opens no file itself."
)

USAGE = (
    "Usage: /pathjail, /pathjail on, /pathjail off, "
    "/pathjail grants, /pathjail check <path>, "
    "/pathjail grant <abs-path>"
)


def _path_text(value: Any, what: str) -> str:
    """The text of a path-like *value*, or a plain refusal."""
    if isinstance(value, str):
        return value
    if isinstance(value, os.PathLike):
        text = os.fspath(value)
        if isinstance(text, str):
            return text
    raise ValueError(f"{what} must be a path string, got {value!r}")


def resolve_workspace_root(root: Any) -> str:
    """The canonical workspace root, or a plain refusal.

    The root is expanded, made absolute and resolved
    with ``os.path.realpath`` - symlinks in the root
    itself are followed, so every judgement is made
    against the one true directory. An empty,
    NUL-bearing or non-path root raises: the jail
    never guesses where the workspace is.
    """
    text = _path_text(root, "a workspace root")
    if not text.strip() or "\x00" in text:
        raise ValueError("a workspace root must be a non-empty path")
    absolute = os.path.abspath(os.path.expanduser(text))
    return os.path.realpath(absolute)


def normalize_grant(value: Any) -> str:
    """One canonical grant root, or a plain refusal.

    A grant is one ABSOLUTE directory path: expanded
    and resolved with ``os.path.realpath`` (so a
    grant that itself rides a symlink names the true
    directory it grants). A relative grant refuses -
    a grant is never quietly anchored to whatever
    directory the process happens to sit in - and so
    do an empty, NUL-bearing or non-path grant.
    """
    text = _path_text(value, "a path grant")
    if not text.strip() or "\x00" in text:
        raise ValueError("a path grant must be a non-empty path")
    expanded = os.path.expanduser(text.strip())
    if not os.path.isabs(expanded):
        raise ValueError(
            f"malformed path grant {value!r}: a grant is one "
            "absolute directory path")
    return os.path.realpath(expanded)


def validate_grant(spec: Any) -> str:
    """Validate one grant, or refuse it plainly.

    A grant is a path string (or path-like), or a
    mapping with exactly the key ``path``. Anything
    else refuses - a bad grant is never skipped or
    repaired by guessing.
    """
    if isinstance(spec, dict):
        unknown = set(spec) - {"path"}
        if unknown:
            raise ValueError(
                "a path grant names unknown keys: "
                + ", ".join(sorted(unknown)))
        if "path" not in spec:
            raise ValueError("a path grant is missing its path")
        return normalize_grant(spec["path"])
    return normalize_grant(spec)


def build_grants(specs: Any) -> Tuple[str, ...]:
    """Validate a whole grant list, in order, duplicates dropped.

    Every grant must validate; one malformed grant
    refuses the whole list rather than silently
    narrowing what the user wrote.
    """
    if specs is None:
        return ()
    if not isinstance(specs, (list, tuple)):
        raise ValueError("path grants must be a list of absolute paths")
    grants: list = []
    for spec in specs:
        grant = validate_grant(spec)
        if grant not in grants:
            grants.append(grant)
    return tuple(grants)


def is_within(resolved: str, root: str) -> bool:
    """Whether *resolved* is *root* itself or inside it.

    Both are resolved absolute paths. Inside is a
    component question, answered with
    ``os.path.commonpath``: the common path must be
    the root itself, so a sibling sharing a name
    prefix (``/ws2`` beside ``/ws``) never counts.
    """
    try:
        return os.path.commonpath([resolved, root]) == root
    except ValueError:
        return False


@dataclass(frozen=True)
class JailDecision:
    """The jail's mechanical answer for one candidate path."""

    decision: str
    candidate: str
    resolved: Optional[str]
    workspace: str
    granted_by: Optional[str]
    reason: str

    @property
    def allowed(self) -> bool:
        return self.decision == "allow"

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "path_jail_decision",
            "slice": PATH_JAIL_SLICE,
            "decision": self.decision,
            "candidate": self.candidate,
            "resolved": self.resolved,
            "workspace": self.workspace,
            "granted_by": self.granted_by,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class PathJail:
    """The whole jail as data: the grant roots, nothing else.

    The workspace root is NOT held here - it is the
    session's project root, supplied per check by
    the agent layer. The default posture is deny
    and is not a field: a path no root grants is
    refused, always.
    """

    grants: Tuple[str, ...] = ()

    def check(self, path: Any, workspace_root: Any) -> JailDecision:
        return check_path(path, workspace_root, self.grants)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "path_jail",
            "slice": PATH_JAIL_SLICE,
            "default": DEFAULT_DECISION,
            "grants": list(self.grants),
        }


def _denied(candidate: str, resolved: Optional[str], workspace: str,
            reason: str) -> JailDecision:
    return JailDecision(
        decision="deny", candidate=candidate, resolved=resolved,
        workspace=workspace, granted_by=None, reason=reason)


def check_path(
    path: Any,
    workspace_root: Any,
    grants: Sequence[str] = (),
) -> JailDecision:
    """Decide one candidate path, mechanically.

    The candidate is resolved against the workspace
    when relative, then resolved whole with
    ``os.path.realpath`` - symlinks followed, ``..``
    collapsed - and allowed only when the RESOLVED
    path is the workspace root itself or inside it,
    or a grant root itself or inside it. A malformed
    workspace root or grant raises (stored and
    session data is never guessed at); a malformed
    candidate - empty, non-text, NUL-bearing - is
    *denied* as a decision, never waved through and
    never an exception the caller must catch.
    Nothing is opened, written or read here.
    """
    workspace = resolve_workspace_root(workspace_root)
    if isinstance(grants, (str, bytes, dict)) or isinstance(grants, os.PathLike):
        raise ValueError("path grants must be a list of absolute paths")
    grant_roots = build_grants(list(grants) if grants is not None else None)
    if isinstance(path, bytes) or (
            not isinstance(path, str)
            and not isinstance(path, os.PathLike)):
        return _denied(
            repr(path), None, workspace,
            f"refused: a candidate path must be text, got {path!r}; "
            "the path jail denies by default")
    candidate = _path_text(path, "a candidate path")
    if not candidate.strip() or "\x00" in candidate:
        return _denied(
            candidate, None, workspace,
            "refused: a candidate path must be a non-empty path "
            "without NUL characters; the path jail denies by default")
    expanded = os.path.expanduser(candidate.strip())
    joined = expanded if os.path.isabs(expanded) else os.path.join(
        workspace, expanded)
    resolved = os.path.realpath(joined)
    if is_within(resolved, workspace):
        return JailDecision(
            decision="allow", candidate=candidate, resolved=resolved,
            workspace=workspace, granted_by="workspace",
            reason=(
                f"allowed: {resolved!r} is inside the workspace "
                f"{workspace!r}"))
    for grant in grant_roots:
        if is_within(resolved, grant):
            return JailDecision(
                decision="allow", candidate=candidate, resolved=resolved,
                workspace=workspace, granted_by=grant,
                reason=(
                    f"allowed: {resolved!r} is inside the path "
                    f"grant {grant!r}"))
    return _denied(
        candidate, resolved, workspace,
        f"refused: {resolved!r} is outside the workspace "
        f"{workspace!r} and no path grant names it; the path "
        "jail denies by default")


#: The decision under its decision-shaped name.
decide_path = check_path


@dataclass(frozen=True)
class JailRefusal:
    """One refusal, shaped as news for the session.

    A file tool reaching outside the jail is an
    escape attempt, not an ordinary log line: the
    agent layer publishes this record as a session
    event, and ``news`` is true with ``surface``
    naming that road, mirroring the network gates.
    """

    candidate: str
    resolved: Optional[str]
    workspace: str
    reason: str

    @property
    def headline(self) -> str:
        where = self.resolved if self.resolved is not None else self.candidate
        return (
            f"Path jail refusal: {where!r} was refused - "
            f"{self.reason}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "path_jail_refusal",
            "slice": PATH_JAIL_SLICE,
            "news": True,
            "surface": "session_event",
            "candidate": self.candidate,
            "resolved": self.resolved,
            "workspace": self.workspace,
            "reason": self.reason,
            "headline": self.headline,
        }


def build_refusal(decision: JailDecision) -> JailRefusal:
    """The refusal record for a denied decision.

    An allowed decision has no refusal; asking for
    one raises instead of dressing an allow up as
    news it is not.
    """
    if decision.allowed:
        raise ValueError("an allowed path has no refusal")
    return JailRefusal(
        candidate=decision.candidate, resolved=decision.resolved,
        workspace=decision.workspace, reason=decision.reason)


def refusal_record(decision: JailDecision) -> Dict[str, Any]:
    """The journal-shaped record of one refusal."""
    return build_refusal(decision).to_record()


def enabled_from_config(config: Dict[str, Any]) -> bool:
    """The path_jail gate stored in *config*.

    Absent means True (the jail ships on). A stored
    value that is not a bool raises - never guessed
    at. With the gate off the agent layer says so
    plainly; the grants and the check stay readable
    either way.
    """
    raw = config.get(SETTING_KEY, True)
    if not isinstance(raw, bool):
        raise ValueError(
            f"{SETTING_KEY} must be true or false, "
            f"got {type(raw).__name__}")
    return raw


def grants_from_config(config: Dict[str, Any]) -> Tuple[str, ...]:
    """The grant roots *config* holds, validated whole.

    The grants ride under ``path_grants`` as a list
    of absolute directory paths; absent means no
    grants - the workspace alone is allowed. A
    malformed stored grant raises - the stored
    jail is never silently narrowed.
    """
    return build_grants(config.get(GRANTS_KEY))


def jail_from_config(config: Dict[str, Any]) -> PathJail:
    """The jail *config* holds, validated whole."""
    return PathJail(grants=grants_from_config(config))


@dataclass(frozen=True)
class GateChange:
    """A recorded change of the path_jail gate."""

    before: bool
    after: bool

    def event(self) -> Dict[str, Any]:
        return {"type": "path_jail_setting_changed",
                "from": self.before, "to": self.after}

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        return {"type": "path_jail_setting_changed",
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
            f"the path jail is already {'on' if before else 'off'}")
    return enabled, GateChange(before=before, after=enabled)


# ---------------------------------------------------------------------
# The /pathjail surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------

def parse_pathjail_args(args: str) -> Dict[str, Any]:
    """Parse the /pathjail grammar both surfaces share.

    No words (or ``show``) shows the slice; ``on`` /
    ``off`` steer the gate; ``grants`` asks for the
    grant list; ``check <path>`` decides one path
    (the path is the rest of the line, spaces and
    all); ``grant <abs-path>`` names one grant root
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
    if text == "grants":
        return {"action": "grants"}
    words = text.split(None, 1)
    if words[0] == "check":
        if len(words) != 2 or not words[1].strip():
            raise ValueError(USAGE)
        return {"action": "check", "path": words[1].strip()}
    if words[0] == "grant":
        if len(words) != 2 or not words[1].strip():
            raise ValueError(USAGE)
        return {"action": "grant",
                "grant": validate_grant(words[1].strip())}
    raise ValueError(USAGE)


def format_gate_change(record: Dict[str, Any]) -> str:
    state = "on" if record.get("to") else "off"
    return f"The path jail is now {state}."


def format_grants(grants: Sequence[str]) -> str:
    """The grant list, in plain words, from the grants."""
    if not grants:
        return (
            "Path grants: none - only the workspace itself "
            "is allowed.")
    lines = ["Path grants:"]
    for grant in grants:
        lines.append(f"  {grant}")
    return "\n".join(lines)


def format_jail_decision(decision: JailDecision) -> str:
    """One decision, in plain words, from the decision."""
    if decision.allowed:
        return f"Path allowed: {decision.reason}."
    return build_refusal(decision).headline + "."


def format_refusal(refusal: Any) -> str:
    """One refusal as the headline the session shows.

    Accepts a ``JailRefusal`` or its record; the
    headline names the resolved path and the reason
    - the refusal is news, stated like news.
    """
    if isinstance(refusal, JailRefusal):
        return refusal.headline
    if isinstance(refusal, dict) and refusal.get("type") == "path_jail_refusal":
        return str(refusal["headline"])
    raise ValueError("format_refusal needs a path jail refusal")


def format_path_jail(config: Dict[str, Any], workspace: Any) -> str:
    """The whole slice, in plain words, for /pathjail.

    Built from the stored gate and grants plus a
    sample allowed check, so the show surface
    exercises the judging road it names and can
    never drift from the jail itself. The workspace
    is the session's project root, supplied by the
    caller and shown resolved.
    """
    enabled = enabled_from_config(config)
    jail = jail_from_config(config)
    root = resolve_workspace_root(workspace)
    lines = ["Path jail (M-099) - " + PLAIN_EXPLANATION, ""]
    lines.append(
        f"Setting: {'on' if enabled else 'off'} ({SETTING_KEY}).")
    lines.append(f"Workspace: {root}")
    lines.append("Default posture: deny (fail-closed).")
    lines.append("")
    lines.append(format_grants(jail.grants))
    lines.append("")
    sample = jail.check("notes.txt", root)
    lines.append("Sample check (notes.txt inside the workspace): "
                 + format_jail_decision(sample))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)
