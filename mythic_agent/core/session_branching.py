"""Session branching (All-Features roadmap slice M-076).

Part IV. The roadmap's words: fork a session at any
message ("try the other road from here") — branches share
history, diverge honestly, and can be compared.

What already shipped, and what this slice adds:

* M-010 (``core/session_catalog.py``) froze the session
  formats at v1: the SQLite session store, the session
  record dict, and the session export. A session's context
  is its ordered message list; its metadata is a plain
  dict on the record. Branching therefore needs NO format
  change: a branch is an ordinary new v1 session whose
  context is a copy of the parent's context up to the fork
  message, and whose lineage rides in the metadata's
  ``branch`` entry — a key v1 readers simply carry, under
  the catalogue's own compat rule (required keys never
  shrink; the record is a superset road, never a
  reshaping). The golden v1 artefacts are untouched.
* ``SessionStore.create`` / ``checkpoint`` / ``resume``
  already give a new session its own row, its own lease,
  and its own journaled life. A branch is created through
  that same road (``SessionStore.branch``), checkpointed
  once with a ``session_branched`` event naming its parent
  and fork point, and then released — it is nobody's live
  session until someone resumes it, exactly like any
  other stored session.
* This module is the pure layer: where a fork may land,
  what the shared and divergent parts of two contexts
  are, and how lineage is recorded and read back. It
  writes nothing itself; the store and the agent layer
  do the writing, through the roads above.

Honesty rules, enforced here and pinned by the slice's
tests:

* **Branches share history — literally.** A branch's
  context up to and including the fork message is a deep
  copy of the parent's messages at those positions: the
  same messages, in the same order. Nothing is summarised,
  rewritten, or quietly dropped on the way over.
* **Branches diverge honestly.** After the fork the two
  sessions are independent rows: a checkpoint on one
  never touches the other, and a comparison reports the
  true shared prefix and each side's own messages after
  it — the first position where the two contexts differ
  is named, never smoothed over, and a side that is
  simply the other's prefix is reported as exactly that
  (no divergence yet), never as a difference.
* **A fork lands on a message, whole.** The fork index
  names one message in the parent (0-based, the system
  message is 0); the branch keeps every message up to
  and including it and none after it. An index outside
  the conversation refuses, and a prefix that would not
  itself be a valid session context refuses — a branch
  never starts from a broken history.
* **Lineage is recorded, never implied.** Every branch
  carries its parent session id, its fork index, the
  fork message's role, its root session (the ancestor
  that is not itself a branch), and its depth. A session
  that is not a branch says so plainly (no lineage),
  and malformed lineage raises, never guesses.
* **The setting is a gate, not a guess.** With
  ``session_branching`` off, forking through the agent
  layer refuses and says so; comparing and listing
  branches — pure reads of what already exists — stay
  available, and the pure maths stays available. A
  malformed stored setting raises, never defaults
  silently.
"""

from __future__ import annotations

__all__ = [
    "SESSION_BRANCHING_SLICE",
    "PLAIN_EXPLANATION",
    "SETTING_KEY",
    "USAGE",
    "Any",
    "BoolChange",
    "BranchComparison",
    "Dict",
    "List",
    "Optional",
    "Tuple",
    "branch_info",
    "branch_metadata",
    "children_of",
    "compare_contexts",
    "enabled_from_config",
    "fork_context",
    "format_branch_list",
    "format_branching",
    "format_comparison",
    "format_fork",
    "format_setting_change",
    "parse_branch_args",
    "set_enabled",
    "shared_prefix_length",
]

import copy
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .sessions import validate_messages, validate_session_id

#: The slice that owns this module.
SESSION_BRANCHING_SLICE = "M-076"

#: The config key the session-branching gate lives under.
SETTING_KEY = "session_branching"

#: The setting explained in plain words — the sentence
#: every surface shows.
PLAIN_EXPLANATION = (
    "Session branching: fork a session at any message — "
    "try the other road from here. The branch is a new "
    "session whose history is the parent's history up to "
    "and including the fork message, copied exactly; "
    "from there the two sessions are independent, and "
    "neither one's later messages ever touch the other. "
    "Every branch records its lineage — its parent, the "
    "fork message, and its root session — in its "
    "metadata, inside the frozen v1 session format, so "
    "any v1 reader still reads it. Two sessions can be "
    "compared: the comparison names the messages they "
    "share, the first message where they diverge, and "
    "each side's own messages after that point."
)

USAGE = (
    "Usage: /branch, /branch on, /branch off, "
    "/branch fork <message-index> [name], /branch list, "
    "or /branch compare <session-id> <session-id>"
)


def fork_context(messages: List[Dict[str, Any]],
                 at_index: Any) -> List[Dict[str, Any]]:
    """The branch's starting history: a copy up to a fork.

    *at_index* is the 0-based position of the fork
    message in *messages*; the returned context holds
    every message up to and including it, deep-copied so
    the branch and the parent can never alias each
    other's history. The prefix must itself validate as
    a session context — the same judgement the store
    applies to any session it creates.
    """
    if not isinstance(messages, list) or not messages:
        raise ValueError(
            "a branch forks a session with at least one "
            "message; this one has none")
    if isinstance(at_index, bool) or not isinstance(at_index, int):
        raise ValueError(
            f"a fork names a message by its index (a whole "
            f"number); got {at_index!r}")
    if not 0 <= at_index < len(messages):
        raise ValueError(
            f"there is no message {at_index} in this "
            f"session; it holds {len(messages)} message(s), "
            f"numbered 0 to {len(messages) - 1}")
    prefix = copy.deepcopy(messages[:at_index + 1])
    try:
        validate_messages(prefix)
    except ValueError as exc:
        raise ValueError(
            f"forking at message {at_index} would start "
            f"the branch on a broken history: {exc}") from exc
    return prefix


def shared_prefix_length(first: List[Dict[str, Any]],
                         second: List[Dict[str, Any]]) -> int:
    """How many opening messages two contexts share.

    Messages are compared as whole values — role,
    content, and any tool calls together — so a message
    that merely looks similar does not count as shared.
    """
    shared = 0
    for left, right in zip(first, second):
        if left != right:
            break
        shared += 1
    return shared


@dataclass(frozen=True)
class BranchComparison:
    """Two contexts compared, in counted plain data.

    ``diverged_at`` is the first index where the two
    contexts hold different messages, or None when one
    context is a prefix of the other (identical, or one
    side simply continued the shared road further).
    ``first_only`` / ``second_only`` are the messages
    after the shared prefix on each side — what each
    road did after the fork.
    """

    shared: int
    diverged_at: Optional[int]
    first_total: int
    second_total: int
    first_only: Tuple[Dict[str, Any], ...]
    second_only: Tuple[Dict[str, Any], ...]

    @property
    def identical(self) -> bool:
        return (self.diverged_at is None
                and self.first_total == self.second_total)

    def record(self, first_id: Optional[str],
               second_id: Optional[str]) -> Dict[str, Any]:
        return {
            "type": "session_branch_compared",
            "first_session_id": first_id,
            "second_session_id": second_id,
            "shared_messages": self.shared,
            "diverged_at": self.diverged_at,
            "identical": self.identical,
            "first_total": self.first_total,
            "second_total": self.second_total,
            "first_only": len(self.first_only),
            "second_only": len(self.second_only),
        }


def compare_contexts(first: List[Dict[str, Any]],
                     second: List[Dict[str, Any]]
                     ) -> BranchComparison:
    """Compare two session contexts, honestly.

    The shared prefix is counted exactly; what follows
    it on each side is carried in the comparison, so a
    caller can show the divergence itself, not just its
    position.
    """
    if not isinstance(first, list) or not isinstance(second, list):
        raise ValueError("a comparison works on two message lists")
    shared = shared_prefix_length(first, second)
    diverged_at = None
    if shared < min(len(first), len(second)):
        diverged_at = shared
    return BranchComparison(
        shared=shared, diverged_at=diverged_at,
        first_total=len(first), second_total=len(second),
        first_only=tuple(copy.deepcopy(first[shared:])),
        second_only=tuple(copy.deepcopy(second[shared:])))


def branch_metadata(parent_id: str, fork_index: int,
                    fork_message: Dict[str, Any],
                    name: Optional[str] = None,
                    parent_branch: Optional[Dict[str, Any]] = None
                    ) -> Dict[str, Any]:
    """The lineage a branch records in its metadata.

    ``root_session_id`` is the ancestor that is not
    itself a branch — the session every road in this
    family ultimately forks from — and ``depth`` counts
    the forks between the root and this branch. A branch
    of a branch keeps the same root and adds one depth.
    """
    try:
        validate_session_id(parent_id)
    except ValueError as exc:
        raise ValueError(f"branch lineage: {exc}") from exc
    if isinstance(fork_index, bool) or not isinstance(fork_index, int) \
            or fork_index < 0:
        raise ValueError(
            f"branch lineage: the fork index must be a "
            f"non-negative whole number; got {fork_index!r}")
    if not isinstance(fork_message, dict) \
            or not isinstance(fork_message.get("role"), str):
        raise ValueError(
            "branch lineage: the fork message must be a "
            "message with a role")
    if name is not None:
        if not isinstance(name, str) or not name.strip():
            raise ValueError(
                "branch lineage: a branch name, when "
                "given, must be words")
        name = name.strip()
    if parent_branch is not None:
        root = parent_branch["root_session_id"]
        depth = parent_branch["depth"] + 1
    else:
        root, depth = parent_id, 1
    return {
        "parent_session_id": parent_id,
        "fork_index": fork_index,
        "fork_role": fork_message["role"],
        "branch_name": name,
        "root_session_id": root,
        "depth": depth,
    }


_BRANCH_KEYS = ("parent_session_id", "fork_index", "fork_role",
                "branch_name", "root_session_id", "depth")


def branch_info(metadata: Any) -> Optional[Dict[str, Any]]:
    """A session metadata's lineage, or None.

    None is the honest answer for a session that is not
    a branch. A ``branch`` entry that is present but
    malformed raises — lineage is never guessed at.
    """
    if not isinstance(metadata, dict):
        raise ValueError(
            "branch lineage: session metadata must be an object")
    raw = metadata.get("branch")
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError(
            "branch lineage: the branch entry must be an object")
    for key in _BRANCH_KEYS:
        if key not in raw:
            raise ValueError(
                f"branch lineage: the branch entry is "
                f"missing '{key}'")
    for key in ("parent_session_id", "root_session_id"):
        try:
            validate_session_id(raw[key])
        except ValueError as exc:
            raise ValueError(
                f"branch lineage field '{key}': {exc}") from exc
    if isinstance(raw["fork_index"], bool) \
            or not isinstance(raw["fork_index"], int) \
            or raw["fork_index"] < 0:
        raise ValueError(
            "branch lineage field 'fork_index': must be a "
            "non-negative whole number")
    if isinstance(raw["depth"], bool) \
            or not isinstance(raw["depth"], int) or raw["depth"] < 1:
        raise ValueError(
            "branch lineage field 'depth': must be a "
            "positive whole number")
    if not isinstance(raw["fork_role"], str) or not raw["fork_role"]:
        raise ValueError(
            "branch lineage field 'fork_role': must name a role")
    if raw["branch_name"] is not None \
            and not isinstance(raw["branch_name"], str):
        raise ValueError(
            "branch lineage field 'branch_name': must be "
            "words or null")
    return dict(raw)


def children_of(parent_id: str,
                sessions: List[Dict[str, Any]]
                ) -> List[Dict[str, Any]]:
    """The branches forked directly from *parent_id*.

    *sessions* is a ``SessionStore.list_sessions()``-shaped
    list (id + metadata per row). Children come back in
    the order the list carries them; a row whose lineage
    is malformed raises through :func:`branch_info`,
    never silently passes or silently vanishes.
    """
    validate_session_id(parent_id)
    children = []
    for row in sessions:
        info = branch_info(row.get("metadata") or {})
        if info is not None and info["parent_session_id"] == parent_id:
            children.append({
                "session_id": row["id"],
                "created_at": row.get("created_at"),
                "status": row.get("status"),
                **info,
            })
    return children


def enabled_from_config(config: Dict[str, Any]) -> bool:
    """The session-branching setting stored in *config*.

    Absent means True (the setting ships on). A stored
    value that is not a bool raises — never guessed at.
    """
    raw = config.get(SETTING_KEY, True)
    if not isinstance(raw, bool):
        raise ValueError(
            f"{SETTING_KEY} must be true or false, "
            f"got {type(raw).__name__}")
    return raw


@dataclass(frozen=True)
class BoolChange:
    """A recorded change of the gate setting."""

    before: bool
    after: bool

    def event(self) -> Dict[str, Any]:
        return {"type": "session_branching_setting_changed",
                "from": self.before, "to": self.after}

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        return {"type": "session_branching_setting_changed",
                "from": self.before, "to": self.after,
                "session_id": session_id, "journaled": journaled}


def set_enabled(config: Dict[str, Any],
                enabled: Any) -> Tuple[bool, BoolChange]:
    """Validate a gate change against *config*, purely."""
    if not isinstance(enabled, bool):
        raise ValueError(
            f"{SETTING_KEY} is turned on or off; got {enabled!r}")
    before = enabled_from_config(config)
    if enabled == before:
        raise ValueError(
            f"session branching is already "
            f"{'on' if before else 'off'}")
    return enabled, BoolChange(before=before, after=enabled)


# ---------------------------------------------------------------------
# The /branch surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------

def parse_branch_args(args: str) -> Dict[str, Any]:
    """Parse ``/branch`` arguments.

    /branch                              -> show
    /branch on / off                     -> the gate
    /branch fork <index> [name words]    -> fork here
    /branch list                         -> this session's branches
    /branch compare <id> <id>            -> compare two sessions
    """
    text = (args or "").strip()
    if not text:
        return {"action": "show"}
    if text == "on":
        return {"action": "setting", "enabled": True}
    if text == "off":
        return {"action": "setting", "enabled": False}
    if text == "list":
        return {"action": "list"}
    parts = text.split()
    if parts[0] == "fork":
        if len(parts) < 2:
            raise ValueError(USAGE)
        try:
            index = int(parts[1])
        except ValueError:
            raise ValueError(
                f"a fork names a message by its index (a "
                f"whole number); got {parts[1]!r}") from None
        name = " ".join(parts[2:]) or None
        return {"action": "fork", "at_index": index, "name": name}
    if parts[0] == "compare":
        if len(parts) != 3:
            raise ValueError(USAGE)
        for value in parts[1:]:
            try:
                validate_session_id(value)
            except ValueError as exc:
                raise ValueError(str(exc)) from exc
        return {"action": "compare", "first_id": parts[1],
                "second_id": parts[2]}
    raise ValueError(USAGE)


def format_setting_change(record: Dict[str, Any]) -> str:
    """A setting change record, in plain words."""
    word = {True: "on", False: "off"}
    return (f"Session branching: {word[record['from']]} -> "
            f"{word[record['to']]}.")


def format_fork(record: Dict[str, Any]) -> str:
    """A fork record, in plain words."""
    name = record.get("branch_name")
    label = f" '{name}'" if name else ""
    return (
        f"Branched session {record['parent_session_id']} at "
        f"message {record['fork_index']}: new session "
        f"{record['branch_session_id']}{label} shares the "
        f"first {record['shared_messages']} message(s) and "
        f"diverges from here. Resume it with --resume "
        f"{record['branch_session_id']}.")


def format_comparison(record: Dict[str, Any]) -> str:
    """A comparison record, in plain words."""
    lines = [
        f"Comparing {record['first_session_id']} and "
        f"{record['second_session_id']}:",
        f"  shared history: {record['shared_messages']} "
        f"message(s)",
    ]
    if record["identical"]:
        lines.append("  the two sessions are identical — "
                     "neither road has diverged.")
    elif record["diverged_at"] is None:
        lines.append("  no divergence yet: one session is "
                     "the other's history, continued.")
    else:
        lines.append(
            f"  they diverge at message "
            f"{record['diverged_at']}.")
    lines.append(
        f"  after the shared history: "
        f"{record['first_only']} message(s) on the first "
        f"road ({record['first_total']} in all), "
        f"{record['second_only']} on the second "
        f"({record['second_total']} in all).")
    return "\n".join(lines)


def format_branch_list(record: Dict[str, Any]) -> str:
    """A branch list record, in plain words."""
    branches = record["branches"]
    lines = [f"Branches of {record['parent_session_id']}: "
             f"{len(branches)}"]
    for branch in branches:
        name = branch.get("branch_name")
        label = f" '{name}'" if name else ""
        lines.append(
            f"  {branch['session_id']}{label} — forked at "
            f"message {branch['fork_index']} "
            f"({branch['fork_role']}), depth "
            f"{branch['depth']}, status {branch['status']}")
    if not branches:
        lines.append("  none yet — fork one with "
                     "/branch fork <message-index>")
    return "\n".join(lines)


_SAMPLE_MESSAGES = [
    {"role": "system", "content": "You are Mythic."},
    {"role": "user", "content": "Rework the auth module."},
    {"role": "assistant", "content": "Road A: patch it in place."},
    {"role": "user", "content": "Go on."},
]


def format_branching(config: Dict[str, Any]) -> str:
    """The whole slice, in plain words, for /branch.

    Built from fork_context() / branch_metadata() /
    branch_info() / children_of() / compare_contexts(),
    so every public road this module offers is exercised
    by its own show surface: a session forked at its
    third message, both roads continued differently,
    and the two compared.
    """
    enabled = enabled_from_config(config)
    lines = ["Session branching (M-076) — " + PLAIN_EXPLANATION, ""]
    lines.append(f"Setting: {'on' if enabled else 'off'} "
                 f"({SETTING_KEY}).")
    lines.append("")
    parent_id = "a" * 32
    branch_id = "b" * 32
    forked = fork_context(_SAMPLE_MESSAGES, 2)
    lines.append(
        f"The sample session holds "
        f"{len(_SAMPLE_MESSAGES)} messages; forking at "
        f"message 2 gives the branch {len(forked)} "
        f"messages — every message up to and including "
        f"the fork message, and none after it.")
    lineage = branch_metadata(parent_id, 2, forked[2],
                              name="the other road")
    assert branch_info({"branch": lineage}) == lineage
    children = children_of(parent_id, [{
        "id": branch_id, "created_at": "2026-01-01T00:00:00+00:00",
        "status": "idle", "metadata": {"branch": lineage}}])
    lines.append(
        f"Its lineage is recorded in its metadata: parent "
        f"{parent_id[:8]}…, fork at message "
        f"{lineage['fork_index']} (a {lineage['fork_role']} "
        f"message), root {lineage['root_session_id'][:8]}…, "
        f"depth {lineage['depth']} — and it is found as a "
        f"child of its parent ({len(children)} child "
        f"listed).")
    parent_road = _SAMPLE_MESSAGES + [
        {"role": "assistant", "content": "Road A continues."}]
    branch_road = forked + [
        {"role": "user", "content": "Try the other road."},
        {"role": "assistant", "content": "Road B: rewrite it."}]
    comparison = compare_contexts(parent_road, branch_road)
    record = comparison.record(parent_id, branch_id)
    lines.append("")
    lines.append(format_comparison(record))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)
