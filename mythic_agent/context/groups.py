"""Protocol-group preservation (Slice 053).

Messages travel in atomic groups that must never be split mid-group when
the context is truncated to a budget:

* ``system`` / ``developer`` messages -- standalone atomic groups, always
  kept (they define the protocol itself).
* ``user`` messages (including multipart user+attachment payloads) --
  one atomic group per message.
* tool-call rounds -- an ``assistant`` message carrying ``tool_calls``
  together with the ``tool`` result messages that answer it; the group is
  included whole or not at all.

:func:`group_protocol_messages` segments a message list and
:func:`truncate_groups` selects whole groups inside a token budget,
restoring chronological order afterwards.
"""

from __future__ import annotations

__all__ = [
    "MessageGroup",
    "group_protocol_messages",
    "truncate_groups",
]

from dataclasses import dataclass, field
from typing import Any

from .budget import TokenEstimator


@dataclass
class MessageGroup:
    """An atomic unit of messages; selected whole or dropped whole."""

    name: str
    messages: list[dict[str, Any]]
    priority: int = 3  # lower == more important; 0 == system (always kept)
    provenance: dict[str, Any] = field(default_factory=dict)


def group_protocol_messages(messages: list[dict[str, Any]]) -> list[MessageGroup]:
    """Segment *messages* into atomic protocol groups."""
    groups: list[MessageGroup] = []
    i = 0
    n = len(messages)
    while i < n:
        message = messages[i]
        role = message.get("role")
        if role in ("system", "developer"):
            groups.append(MessageGroup(
                name=f"system-{i}", messages=[message], priority=0,
                provenance={"kind": "system"}))
            i += 1
        elif role == "assistant" and message.get("tool_calls"):
            pending = {call.get("id") for call in message.get("tool_calls", [])}
            collected = [message]
            j = i + 1
            while j < n:
                nxt = messages[j]
                if nxt.get("role") == "tool" and nxt.get("tool_call_id") in pending:
                    pending.discard(nxt.get("tool_call_id"))
                    collected.append(nxt)
                    j += 1
                else:
                    break
            groups.append(MessageGroup(
                name=f"tool-round-{len(groups)}", messages=collected, priority=2,
                provenance={"kind": "tool-round",
                            "calls": len(message.get("tool_calls", [])),
                            "results": len(collected) - 1,
                            "pending": sorted(c for c in pending if c)}))
            i = j
        elif role == "user":
            content = message.get("content")
            groups.append(MessageGroup(
                name=f"user-{i}", messages=[message], priority=1,
                provenance={"kind": "user+attachments"
                            if isinstance(content, list) else "user"}))
            i += 1
        else:
            groups.append(MessageGroup(
                name=f"solo-{i}", messages=[message], priority=3,
                provenance={"kind": "solo", "role": role}))
            i += 1
    return groups


def _group_tokens(group: MessageGroup, estimator: TokenEstimator) -> int:
    return sum(
        estimator.count_message(str(m.get("role", "")), _content_text(m))
        for m in group.messages
    )


def _content_text(message: dict[str, Any]) -> str:
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict):
                text = part.get("text")
                parts.append(text if isinstance(text, str)
                             else f"<{part.get('type', 'part')}>")
            else:
                parts.append(str(part))
        return " ".join(parts)
    return "" if content is None else str(content)


def truncate_groups(
    groups: list[MessageGroup],
    budget: int,
    estimator: TokenEstimator | None = None,
) -> list[dict[str, Any]]:
    """Select whole groups inside *budget*, preserving chronology.

    System groups (priority 0) are always kept, even over budget --
    dropping them would change the protocol itself.  Remaining groups
    compete atomically: most important and most recent first.  A group
    is either fully included or fully excluded; the returned messages
    are in their original chronological order.
    """
    estimator = estimator or TokenEstimator()
    if budget < 0:
        raise ValueError("budget must be non-negative")
    systems = [g for g in groups if g.priority == 0]
    rest = [g for g in groups if g.priority != 0]
    # Most important first; within equal priority, most recent first.
    order = sorted(enumerate(rest),
                   key=lambda pair: (pair[1].priority, -pair[0]))
    selected: list[MessageGroup] = list(systems)
    remaining = budget - sum(_group_tokens(g, estimator) for g in systems)
    for _, group in order:
        cost = _group_tokens(group, estimator)
        if cost <= remaining:
            selected.append(group)
            remaining -= cost
    # Restore chronological order by original position.
    position = {id(g): idx for idx, g in enumerate(groups)}
    selected.sort(key=lambda g: position[id(g)])
    return [message for group in selected for message in group.messages]
