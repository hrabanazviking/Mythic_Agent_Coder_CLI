"""Tests for smart token-budget-aware context assembly (Slice 15)."""

import pytest

from mythic_agent.agents.context import (
    ContextBuilder,
    Priority,
    Turn,
    default_summarizer,
    estimate_tokens,
)


def _builder(budget=500):
    b = ContextBuilder(max_tokens=budget)
    b.add_system("You are a helpful coding agent.")
    return b


def test_system_prompt_always_included_even_when_over_budget():
    b = ContextBuilder(max_tokens=1)
    b.add_system("System prompt that alone exceeds the budget.")
    b.add_turn("user", "hello", Priority.HIGH)
    messages = b.build()
    assert len(messages) == 1
    assert messages[0]["role"] == "system"
    assert "exceeds the budget" in messages[0]["content"]


def test_recent_turns_preferred_over_older_ones():
    b = _builder(budget=40)
    for i in range(6):
        b.add_turn("user", f"question number {i}", Priority.HIGH)
    messages = b.build()
    contents = [m["content"] for m in messages]
    assert any("question number 5" in c for c in contents)
    assert not any("question number 0" in c for c in contents)


def test_tool_call_result_pair_never_split():
    b = _builder(budget=500)
    call = {"id": "c1", "name": "read_file", "arguments": "{}"}
    b.add_tool_pair(call, "file contents here")
    b.add_turn("user", "x" * 2000, Priority.HIGH)  # crowd the budget
    messages = b.build()
    roles = [m["role"] for m in messages]
    # Pair is atomic: both messages present or neither is.
    assert ("assistant" in roles) == ("tool" in roles)


def test_pair_fully_dropped_when_it_does_not_fit():
    b = _builder(budget=80)
    call = {"id": "c1", "name": "read_file", "arguments": "{}"}
    b.add_tool_pair(call, "some tool result content that is fairly long " * 20)
    messages = b.build()
    roles = [m["role"] for m in messages]
    assert "assistant" not in roles
    assert "tool" not in roles


def test_low_priority_turns_summarized_when_dropped():
    b = _builder(budget=500)
    for i in range(3):
        b.add_turn("user", f"old detail {i} " * 60, Priority.LOW)
    messages = b.build()
    contents = " ".join(m["content"] for m in messages)
    assert "Summary of earlier context" in contents
    assert "old detail 0" in contents


def test_messages_returned_in_chronological_order():
    b = _builder(budget=5000)
    b.add_turn("user", "first", Priority.HIGH)
    b.add_turn("assistant", "second", Priority.HIGH)
    b.add_turn("user", "third", Priority.HIGH)
    messages = b.build()
    assert [m["content"] for m in messages][1:] == ["first", "second", "third"]


def test_output_preserves_chronology_across_priorities():
    b = _builder(budget=5000)
    b.add_turn("user", "low note", Priority.LOW)
    b.add_turn("user", "medium note", Priority.MEDIUM)
    b.add_turn("user", "high note", Priority.HIGH)
    messages = b.build()
    # System prompt first; everything else in chronological order.
    assert messages[0]["role"] == "system"
    assert [m["content"] for m in messages][1:] == ["low note", "medium note", "high note"]


def test_custom_summarizer_is_used():
    b = ContextBuilder(max_tokens=120, summarize_fn=lambda turns: "CUSTOM SUMMARY")
    for i in range(3):
        b.add_turn("user", f"old detail {i} " * 30, Priority.LOW)
    contents = " ".join(m["content"] for m in b.build())
    assert "CUSTOM SUMMARY" in contents


def test_invalid_budget_rejected():
    with pytest.raises(ValueError):
        ContextBuilder(max_tokens=0)
    with pytest.raises(ValueError):
        ContextBuilder(max_tokens=-10)


def test_default_summarizer_truncates_long_content():
    turn = Turn(role="user", content="x" * 500, priority=Priority.LOW)
    summary = default_summarizer([turn])
    assert len(summary) < 500
    assert "user" in summary


def test_estimate_tokens_scales_with_length():
    assert estimate_tokens("ab") < estimate_tokens("ab" * 1000)
