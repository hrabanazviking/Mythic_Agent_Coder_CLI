"""Tests for coding prompt optimization assets (Slice 22)."""

import pytest

from mythic_agent.agents import prompts
from mythic_agent.agents.prompts import (
    CODING_SYSTEM_PROMPT,
    FEW_SHOT_EXAMPLES,
    for_provider,
)

# Real tool names declared in mythic_agent.agents.tools.get_agent_tools().
from mythic_agent.agents.tools import get_agent_tools


def _tool_names() -> set[str]:
    return {t["function"]["name"] for t in get_agent_tools()}


def test_system_prompt_is_clear_and_tool_focused():
    assert isinstance(CODING_SYSTEM_PROMPT, str)
    assert len(CODING_SYSTEM_PROMPT) > 500
    for token in ("read_file", "replace_file_content", "run_command", "grep_search"):
        assert token in CODING_SYSTEM_PROMPT


def test_system_prompt_bans_pseudocode_and_invention():
    lowered = CODING_SYSTEM_PROMPT.lower()
    assert "pseudocode" in lowered
    assert "verify" in lowered


def test_few_shot_examples_count_and_shape():
    assert len(FEW_SHOT_EXAMPLES) == 3
    for example in FEW_SHOT_EXAMPLES:
        assert example["task"]
        assert len(example["steps"]) >= 3
        for step in example["steps"]:
            assert step["tool"]
            assert isinstance(step["arguments"], dict)
            assert step["note"]


def test_few_shot_examples_follow_read_edit_test_pattern():
    tool_names = _tool_names()
    read_tools = {"read_file", "grep_search", "list_dir"}
    edit_tools = {"write_file", "replace_file_content"}
    for example in FEW_SHOT_EXAMPLES:
        tools = [s["tool"] for s in example["steps"]]
        # Every example must read before it edits and test at the end.
        first_edit = min(
            i for i, t in enumerate(tools) if t in edit_tools
        )
        assert any(t in read_tools for t in tools[:first_edit]), (
            f"example '{example['task']}' edits before reading"
        )
        assert tools[-1] == "run_command", (
            f"example '{example['task']}' does not end with verification"
        )


def test_few_shot_tools_are_real():
    tool_names = _tool_names()
    for example in FEW_SHOT_EXAMPLES:
        for step in example["steps"]:
            assert step["tool"] in tool_names, (
                f"unknown tool '{step['tool']}' in example '{example['task']}'"
            )


def test_for_provider_anthropic():
    text = for_provider("anthropic")
    assert text.startswith(CODING_SYSTEM_PROMPT)
    assert "Anthropic" in text or "Claude" in text
    assert for_provider("Claude") == for_provider("ANTHROPIC")


def test_for_provider_openai():
    text = for_provider("openai")
    assert text.startswith(CODING_SYSTEM_PROMPT)
    assert "OpenAI" in text or "GPT" in text
    assert "anthropic" not in text.lower()


def test_for_provider_unknown_returns_base():
    assert for_provider("definitely-not-a-provider") == CODING_SYSTEM_PROMPT
    assert for_provider("") == CODING_SYSTEM_PROMPT


def test_provider_prompts_differ():
    assert for_provider("anthropic") != for_provider("openai")
