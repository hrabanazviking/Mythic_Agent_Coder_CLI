"""Smart token-budget-aware context assembly (Slice 15).

:class:`ContextBuilder` assembles the message list sent to the language
model so the most important context always survives a fixed token budget:

1. **System prompt** -- always included, never truncated.
2. **Recent turns** (``Priority.HIGH``) -- most recent first.
3. **Tool results** (``Priority.MEDIUM``) -- after recent turns.
4. **Old turns** (``Priority.LOW``) -- summarized when they no longer fit.

A tool call and its result form an atomic group: the builder never splits
a pair across the budget boundary -- a group is either fully included or
fully excluded.

Token estimation uses a character heuristic (``~4`` chars per token) plus a
small per-message framing overhead so this module has no optional
dependencies. Pass a real tokenizer as ``token_fn`` when one is available.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any


class Priority(IntEnum):
    """Importance of a turn when competing for the token budget.

    Lower value == more important. ``SYSTEM`` is always included.
    """

    SYSTEM = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3


def estimate_tokens(text: str) -> int:
    """Heuristic token count: ~4 characters per token plus framing."""
    return max(1, len(text) // 4) + 3


def default_summarizer(turns: Sequence["Turn"]) -> str:
    """Condense low-priority turns into a compact recap message."""
    parts = []
    for turn in turns:
        snippet = turn.content.replace("\n", " ")
        if len(snippet) > 160:
            snippet = snippet[:157] + "..."
        parts.append(f"- {turn.role}: {snippet}")
    return "[Summary of earlier context]\n" + "\n".join(parts)


@dataclass
class Turn:
    """One stored turn with its budget priority and optional pair group."""

    role: str
    content: str
    priority: Priority = Priority.HIGH
    group: str | None = None
    index: int = 0  # insertion order; used to restore chronology


@dataclass
class ContextBuilder:
    """Assemble a token-budget-aware message list for the model."""

    max_tokens: int
    token_fn: Callable[[str], int] = field(default=estimate_tokens)
    summarize_fn: Callable[[Sequence[Turn]], str] = field(default=default_summarizer)
    summary_budget_fraction: float = 0.15

    def __post_init__(self) -> None:
        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        if not 0 <= self.summary_budget_fraction < 1:
            raise ValueError("summary_budget_fraction must be in [0, 1)")
        self._turns: list[Turn] = []
        self._counter = 0
        self._pair_counter = 0

    # -- recording ------------------------------------------------------
    def add_turn(
        self,
        role: str,
        content: str,
        priority: Priority = Priority.HIGH,
        group: str | None = None,
    ) -> Turn:
        """Record a turn; returns the stored :class:`Turn` for grouping."""
        turn = Turn(role=role, content=str(content), priority=priority,
                    group=group, index=self._counter)
        self._counter += 1
        self._turns.append(turn)
        return turn

    def add_system(self, content: str) -> Turn:
        """Record a system prompt turn (always included by :meth:`build`)."""
        return self.add_turn("system", content, Priority.SYSTEM)

    def add_tool_pair(self, tool_call: dict[str, Any], tool_result: str) -> tuple[Turn, Turn]:
        """Record an assistant tool-call message and its tool result as one atomic group.

        The pair is never split across the budget boundary: both messages are
        included or neither is.
        """
        self._pair_counter += 1
        group = f"tool-pair-{self._pair_counter}"
        call_turn = self.add_turn(
            "assistant",
            json.dumps({"tool_calls": [tool_call]}),
            Priority.MEDIUM,
            group=group,
        )
        result_turn = self.add_turn(
            "tool",
            tool_result,
            Priority.MEDIUM,
            group=group,
        )
        return call_turn, result_turn

    # -- building -------------------------------------------------------
    def build(self) -> list[dict[str, Any]]:
        """Return the message list that fits inside ``max_tokens``.

        System messages always come first (in order), followed by the
        selected turns in chronological order. Oversized low-priority turns
        are replaced by a summary message when it fits.
        """
        selected, low_leftovers = self._select()
        messages = [
            {"role": t.role, "content": t.content}
            for t in sorted(selected, key=lambda t: (t.priority != Priority.SYSTEM, t.index))
        ]
        if low_leftovers:
            summary = Turn("system", self.summarize_fn(low_leftovers),
                           Priority.LOW, index=-1)
            used = sum(self._message_tokens(t) for t in selected)
            if self._message_tokens(summary) <= self.max_tokens - used:
                # Place the summary right after the system prompt.
                insert_at = sum(1 for m in messages if m["role"] == "system")
                messages.insert(insert_at, {"role": "system", "content": summary.content})
        return messages

    # -- internals ------------------------------------------------------
    def _message_tokens(self, turn: Turn) -> int:
        return self.token_fn(f"{turn.role}: {turn.content}")

    def _select(self) -> tuple[list[Turn], list[Turn]]:
        """Pick atomic groups greedily; return (selected, leftover_low)."""
        systems = [t for t in self._turns if t.priority == Priority.SYSTEM]
        rest = [t for t in self._turns if t.priority != Priority.SYSTEM]

        groups: dict[str, list[Turn]] = {}
        order: list[str] = []
        for t in rest:
            key = t.group if t.group is not None else f"solo-{t.index}"
            if key not in groups:
                groups[key] = []
                order.append(key)
            groups[key].append(t)

        # Most important and most recent first: priority asc, index desc.
        order.sort(key=lambda k: (min(t.priority for t in groups[k]),
                                  -max(t.index for t in groups[k])))

        budget = self.max_tokens
        selected: list[Turn] = []
        leftover_low: list[Turn] = []

        system_cost = sum(self._message_tokens(t) for t in systems)
        remaining = budget - system_cost
        if remaining < 0:
            # Even the system prompt overflows: keep it anyway (it is mandatory)
            # and drop everything else.
            return systems, [t for t in rest if t.priority == Priority.LOW]

        selected.extend(systems)
        for key in order:
            group = groups[key]
            cost = sum(self._message_tokens(t) for t in group)
            if cost <= remaining:
                selected.extend(group)
                remaining -= cost
            elif all(t.priority == Priority.LOW for t in group):
                leftover_low.extend(sorted(group, key=lambda t: t.index))
        return selected, leftover_low
