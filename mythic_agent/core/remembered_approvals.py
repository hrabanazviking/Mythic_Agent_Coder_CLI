"""Remembered approvals with scope (roadmap slice M-096).

Part V - Autonomy & Safety. The roadmap's words:
``"always allow *this* command in *this* project" -
scopes are exact (command + args pattern + path),
listed, and revocable in one screen; nothing is
remembered silently.``

What already shipped, and what this slice adds:

* The elder approval road (``core/policy.py``
  ToolPolicy in ``ask`` mode, the TUI/terminal
  approval prompts in ``agents/tools.py``) asks
  afresh every time. A user who approves the same
  command in the same project every day has no way
  to say "always allow this one" - and, just as
  importantly, no screen where such a standing
  answer could be listed and taken back.
* This slice is that standing answer, as a pure
  layer. A remembered approval is one exact scope:
  a command, an args pattern, and a project path.
  This module validates scopes, matches a proposed
  call against them, lists them, and revokes them.
  It writes no file, changes no setting and runs
  nothing itself; the agent layer owns storing the
  list and consulting it on the live approval road.

Honesty rules, enforced here and pinned by tests:

* **A scope is exact in all three parts.** The
  command must equal the scope's command exactly,
  the project path must equal the scope's path
  exactly (after plain normalisation), and every
  argument must match the args pattern - each
  pattern element is either the argument itself or
  ``*``, which stands for exactly one argument.
  A call with more or fewer arguments than the
  pattern never matches. No prefix matching, no
  substring matching, no silent broadening.
* **Nothing is remembered silently.** Creating a
  remembered approval requires the caller's
  explicit ``explicit=True`` - the recorded answer
  to a question the user was actually asked. Any
  other value refuses and remembers nothing.
* **The command itself carries no pattern.** A
  ``*`` (or any wildcard) in the command position
  refuses at validation: the pattern lives in the
  args, never in which command may run.
* **Duplicates refuse.** Remembering a scope that
  is already remembered raises instead of stacking
  a second identical entry; the list stays the one
  true list the screen shows.
* **Malformed stored data raises.** A stored list
  that is not a list, a record that is not a
  mapping, a record with unknown or missing keys,
  or two records for one scope all raise - a
  corrupt memory is named, never quietly trusted
  or quietly dropped.
* **Revocation is by the id the screen shows.**
  Every record carries a fingerprint id derived
  from its exact scope; revoking names that id
  (or a unique prefix of it) and removes exactly
  that entry. An unknown or ambiguous id refuses
  and removes nothing.
* **Listing is the whole truth in one screen.**
  ``format_remembered_approvals`` renders every
  remembered scope - command, args pattern, path
  and id - from the validated list itself, never
  from a second source that could drift.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

__all__ = [
    "PLAIN_EXPLANATION",
    "RECORD_KEYS",
    "REMEMBERED_APPROVALS_SLICE",
    "SETTING_KEY",
    "USAGE",
    "RememberedApproval",
    "Scope",
    "approval_change_record",
    "args_match",
    "find_match",
    "format_remembered_approval",
    "format_remembered_approvals",
    "matches",
    "normalize_path",
    "parse_remember_args",
    "remember_approval",
    "revoke_approval",
    "scope_fingerprint",
    "stored_approvals",
    "validate_record",
    "validate_scope",
]

REMEMBERED_APPROVALS_SLICE = "M-096"

SETTING_KEY = "remembered_approvals"

RECORD_KEYS = frozenset({"command", "args_pattern", "path"})

_PLAIN_PARTS_RE = re.compile(r"\s+")

PLAIN_EXPLANATION = (
    "A remembered approval is a standing answer with an exact "
    "scope: this command, with these arguments, in this project. "
    "It is only ever created when you say so out loud, it is "
    "listed in one screen, and it can be revoked from that same "
    "screen. Anything outside the exact scope is asked afresh."
)

USAGE = (
    "Usage: /remember, /remember list, "
    "/remember forget <id>, /remember clear"
)


def normalize_path(path: Any) -> str:
    """One canonical spelling of a project path.

    Backslashes become slashes, a leading ``./`` is
    dropped, and a trailing slash is dropped (except
    for the root itself). Nothing is resolved against
    the filesystem - this is spelling, not lookup.
    """
    if not isinstance(path, str):
        raise ValueError("a scope path must be a string")
    text = path.strip().replace("\\", "/")
    while text.startswith("./"):
        text = text[2:]
    if len(text) > 1:
        text = text.rstrip("/")
    if not text:
        raise ValueError("a scope path must not be empty")
    return text


def _check_command(command: Any) -> str:
    if not isinstance(command, str):
        raise ValueError("a scope command must be a string")
    text = command.strip()
    if not text:
        raise ValueError("a scope command must not be empty")
    if any(ch in text for ch in "*?[]"):
        raise ValueError(
            "a scope command carries no pattern: "
            "wildcards live in the args pattern only"
        )
    if _PLAIN_PARTS_RE.search(text):
        raise ValueError(
            "a scope command is one command name; "
            "its arguments belong in the args pattern"
        )
    return text


def _check_args_pattern(pattern: Any) -> Tuple[str, ...]:
    if isinstance(pattern, str) or not isinstance(pattern, (list, tuple)):
        raise ValueError("an args pattern must be a list of strings")
    checked: List[str] = []
    for element in pattern:
        if not isinstance(element, str):
            raise ValueError("every args pattern element must be a string")
        if element == "":
            raise ValueError("an args pattern element must not be empty")
        checked.append(element)
    return tuple(checked)


@dataclass(frozen=True)
class Scope:
    """One exact scope: command + args pattern + path."""

    command: str
    args_pattern: Tuple[str, ...]
    path: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "command": self.command,
            "args_pattern": list(self.args_pattern),
            "path": self.path,
        }


def validate_scope(spec: Any) -> Scope:
    """Validate a scope spec (a Scope or its record mapping)."""
    if isinstance(spec, Scope):
        spec = spec.to_record()
    if not isinstance(spec, dict):
        raise ValueError("a scope must be a mapping")
    unknown = set(spec) - RECORD_KEYS
    if unknown:
        raise ValueError(
            "a scope names unknown keys: " + ", ".join(sorted(unknown))
        )
    missing = RECORD_KEYS - set(spec)
    if missing:
        raise ValueError(
            "a scope is missing keys: " + ", ".join(sorted(missing))
        )
    return Scope(
        command=_check_command(spec["command"]),
        args_pattern=_check_args_pattern(spec["args_pattern"]),
        path=normalize_path(spec["path"]),
    )


def scope_fingerprint(scope: Scope) -> str:
    """The id of one exact scope, derived from the scope itself."""
    canonical = json.dumps(
        scope.to_record(), sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class RememberedApproval:
    """One remembered approval: an exact scope plus its id."""

    scope: Scope

    @property
    def id(self) -> str:
        return scope_fingerprint(self.scope)

    @property
    def command(self) -> str:
        return self.scope.command

    @property
    def args_pattern(self) -> Tuple[str, ...]:
        return self.scope.args_pattern

    @property
    def path(self) -> str:
        return self.scope.path

    def to_record(self) -> Dict[str, Any]:
        record = self.scope.to_record()
        record["type"] = "remembered_approval"
        record["id"] = self.id
        return record


def validate_record(record: Any) -> RememberedApproval:
    """Validate one stored record (id, when present, must agree)."""
    if not isinstance(record, dict):
        raise ValueError("a remembered approval must be a mapping")
    keys = set(record) - {"type", "id"}
    unknown = keys - RECORD_KEYS
    if unknown:
        raise ValueError(
            "a remembered approval names unknown keys: "
            + ", ".join(sorted(unknown))
        )
    missing = RECORD_KEYS - keys
    if missing:
        raise ValueError(
            "a remembered approval is missing keys: "
            + ", ".join(sorted(missing))
        )
    if "type" in record and record["type"] != "remembered_approval":
        raise ValueError("a remembered approval has the wrong type")
    scope_spec = {key: record[key] for key in RECORD_KEYS}
    approval = RememberedApproval(scope=validate_scope(scope_spec))
    if "id" in record and record["id"] != approval.id:
        raise ValueError(
            "a remembered approval's id does not match its scope"
        )
    return approval


def stored_approvals(config: Dict[str, Any]) -> List[RememberedApproval]:
    """The validated remembered approvals held in *config*.

    Absent setting = an empty list (nothing remembered
    yet). Anything malformed raises, never defaults.
    """
    raw = config.get(SETTING_KEY)
    if raw is None:
        return []
    if isinstance(raw, (str, bytes)) or not isinstance(raw, (list, tuple)):
        raise ValueError("remembered approvals must be stored as a list")
    approvals: List[RememberedApproval] = []
    seen: set = set()
    for record in raw:
        approval = validate_record(record)
        if approval.id in seen:
            raise ValueError(
                "two remembered approvals cover one exact scope: "
                + approval.id[:12]
            )
        seen.add(approval.id)
        approvals.append(approval)
    return approvals


def args_match(pattern: Sequence[str], args: Sequence[str]) -> bool:
    """Exact args matching: ``*`` stands for exactly one argument."""
    if len(pattern) != len(args):
        return False
    return all(p == "*" or p == a for p, a in zip(pattern, args))


def matches(
    approval: RememberedApproval,
    command: Any,
    args: Sequence[str],
    path: Any,
) -> bool:
    """True only when the call sits inside the exact scope."""
    if not isinstance(command, str) or command.strip() != approval.command:
        return False
    try:
        here = normalize_path(path)
    except ValueError:
        return False
    if here != approval.path:
        return False
    return args_match(approval.args_pattern, list(args))


def find_match(
    approvals: Sequence[RememberedApproval],
    command: Any,
    args: Sequence[str],
    path: Any,
) -> Optional[RememberedApproval]:
    """The most specific remembered approval covering a call, or None.

    Specificity is mechanical: fewer ``*`` elements wins;
    ties break by fingerprint so the answer never depends
    on list order alone.
    """
    found = [a for a in approvals if matches(a, command, args, path)]
    if not found:
        return None
    found.sort(key=lambda a: (a.args_pattern.count("*"), a.id))
    return found[0]


def remember_approval(
    approvals: Sequence[RememberedApproval],
    spec: Any,
    *,
    explicit: Any = False,
) -> List[RememberedApproval]:
    """A new list with *spec* remembered - only when explicit.

    ``explicit`` must be exactly True: the recorded answer
    to a question the user was actually asked. Anything
    else refuses and remembers nothing.
    """
    if explicit is not True:
        raise ValueError(
            "nothing is remembered silently: remembering an "
            "approval requires an explicit yes from the user"
        )
    approval = RememberedApproval(scope=validate_scope(spec))
    if any(a.id == approval.id for a in approvals):
        raise ValueError(
            "that exact scope is already remembered: "
            + approval.id[:12]
        )
    return list(approvals) + [approval]


def revoke_approval(
    approvals: Sequence[RememberedApproval],
    id_text: Any,
) -> List[RememberedApproval]:
    """A new list with exactly the named approval removed.

    The name is the id the listing shows, or a unique
    prefix of it (at least 6 characters). Unknown or
    ambiguous names refuse and remove nothing.
    """
    if not isinstance(id_text, str) or len(id_text.strip()) < 6:
        raise ValueError("revoke by the id the listing shows")
    wanted = id_text.strip().lower()
    hits = [a for a in approvals if a.id.lower().startswith(wanted)]
    if not hits:
        raise ValueError("no remembered approval carries that id")
    if len(hits) > 1:
        raise ValueError("that id is ambiguous; name more of it")
    return [a for a in approvals if a.id != hits[0].id]


def approval_change_record(
    action: str,
    approval: RememberedApproval,
    *,
    total: int,
) -> Dict[str, Any]:
    """The journal-shaped record of a remember/revoke change."""
    if action not in ("remembered", "revoked"):
        raise ValueError("a change action is remembered or revoked")
    record = approval.to_record()
    record["action"] = action
    record["total"] = total
    return record


def format_remembered_approval(approval: RememberedApproval) -> str:
    """One listing line: command, args pattern, path, id."""
    args = " ".join(approval.args_pattern) if approval.args_pattern else "(no args)"
    return (
        f"{approval.command} {args} in {approval.path} "
        f"[{approval.id[:12]}]"
    )


def format_remembered_approvals(
    approvals: Sequence[RememberedApproval],
) -> str:
    """The one screen: every remembered approval, or the plain none."""
    if not approvals:
        return (
            "No remembered approvals. Every command is asked "
            "afresh; nothing is remembered silently."
        )
    lines = [f"Remembered approvals ({len(approvals)}):"]
    for approval in approvals:
        lines.append("  " + format_remembered_approval(approval))
    lines.append("Revoke one with /remember forget <id>.")
    return "\n".join(lines)


def parse_remember_args(args: str) -> Dict[str, Any]:
    """The one /remember grammar for both surfaces.

    ``\"\"`` / ``list`` / ``show`` -> list; ``forget <id>``
    -> revoke that id; ``clear`` -> revoke all. Anything
    else is a usage error naming the grammar.
    """
    text = (args or "").strip()
    if text in ("", "list", "show"):
        return {"action": "list"}
    if text == "clear":
        return {"action": "clear"}
    parts = text.split()
    if len(parts) == 2 and parts[0] == "forget":
        return {"action": "forget", "id": parts[1]}
    raise ValueError(USAGE)
