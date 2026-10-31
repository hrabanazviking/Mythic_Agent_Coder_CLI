"""M-021: Anthropic-native adapter v2 — caching, thinking, tool use.

TIER: unit

The real ``anthropic`` SDK is never imported: every chat goes through
the provider's ``_send`` / ``_client`` seams with fakes, exactly like
the R-029 hardening tests. No network, no real keys.
"""

import types

import pytest

from mythic_agent.providers.anthropic import (
    AnthropicChatResult,
    AnthropicProvider,
    ProviderError,
    _anthropic_messages,
    _thinking_param,
    _tools_param,
)
from mythic_agent.providers.base import ToolCall
from mythic_agent.providers.reasoning import ReasoningConfig

FAKE_KEY = "sk-ant-test-key-000"


def _block(kind, **kw):
    return types.SimpleNamespace(type=kind, **kw)


def _provider(captured, response):
    """An AnthropicProvider whose _send captures params, returns response."""
    provider = AnthropicProvider(api_key=FAKE_KEY)

    def fake_send(client, **params):
        captured.update(params)
        return response

    provider._send = fake_send  # type: ignore[method-assign]
    provider._client = lambda: object()  # type: ignore[method-assign]
    return provider


def _text_response(*texts):
    return types.SimpleNamespace(
        content=[_block("text", text=t) for t in texts],
        stop_reason="end_turn", usage=None)


TOOLS = [{
    "name": "get_weather",
    "description": "Get the current weather for a city.",
    "parameters": {"type": "object",
                   "properties": {"city": {"type": "string"}},
                   "required": ["city"]},
}]


# ----------------------------------------------------------------------
# capabilities: v2 truth
# ----------------------------------------------------------------------

def test_capabilities_v2():
    caps = AnthropicProvider(api_key=FAKE_KEY).capabilities()
    assert caps == {"streaming": True, "tool_calling": True,
                    "vision": True, "json_mode": False}


# ----------------------------------------------------------------------
# tool-use dialect: definitions, tool_use blocks, tool_result blocks
# ----------------------------------------------------------------------

def test_tools_param_anthropic_dialect():
    payload = _tools_param(TOOLS, prompt_cache=False)
    assert payload == [{
        "name": "get_weather",
        "description": "Get the current weather for a city.",
        "input_schema": {"type": "object",
                         "properties": {"city": {"type": "string"}},
                         "required": ["city"]},
    }]


def test_tools_param_accepts_input_schema_spelling():
    tools = [{"name": "t", "description": "d",
              "input_schema": {"type": "object"}}]
    assert _tools_param(tools, prompt_cache=False)[0]["input_schema"] == {
        "type": "object"}


def test_tools_param_rejects_bad_specs():
    with pytest.raises(ProviderError):
        _tools_param([], prompt_cache=False)
    with pytest.raises(ProviderError):
        _tools_param([{"description": "no name"}], prompt_cache=False)
    with pytest.raises(ProviderError):
        _tools_param(["not-a-dict"], prompt_cache=False)


def test_tools_reach_the_sdk_call_in_native_shape():
    captured = {}
    provider = _provider(captured, _text_response("ok"))
    assert provider.chat([{"role": "user", "content": "weather?"}],
                         tools=TOOLS) == "ok"
    assert captured["tools"][0]["input_schema"]["type"] == "object"
    assert "function" not in captured["tools"][0]  # not the OpenAI shim


def test_tool_choice_string_and_dict():
    captured = {}
    provider = _provider(captured, _text_response("ok"))
    provider.chat([{"role": "user", "content": "hi"}], tools=TOOLS,
                  tool_choice="any")
    assert captured["tool_choice"] == {"type": "any"}
    captured2 = {}
    provider2 = _provider(captured2, _text_response("ok"))
    provider2.chat([{"role": "user", "content": "hi"}], tools=TOOLS,
                   tool_choice={"type": "tool", "name": "get_weather"})
    assert captured2["tool_choice"] == {"type": "tool",
                                        "name": "get_weather"}
    with pytest.raises(ProviderError):
        _provider({}, _text_response("ok")).chat(
            [{"role": "user", "content": "hi"}], tool_choice="sometimes")


def test_tool_role_with_id_becomes_tool_result_block():
    _system, converted = _anthropic_messages([
        {"role": "user", "content": "weather in Oslo?"},
        {"role": "assistant", "content": "",
         "tool_calls": [{"id": "toolu_1", "name": "get_weather",
                         "arguments": {"city": "Oslo"}}]},
        {"role": "tool", "tool_use_id": "toolu_1", "content": "sunny"},
    ])
    assert converted[1] == {"role": "assistant", "content": [
        {"type": "tool_use", "id": "toolu_1", "name": "get_weather",
         "input": {"city": "Oslo"}}]}
    assert converted[2] == {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": "toolu_1",
         "content": "sunny"}]}


def test_tool_result_accepts_tool_call_id_and_error_flag():
    _system, converted = _anthropic_messages([
        {"role": "tool", "tool_call_id": "toolu_9", "content": "boom",
         "is_error": True},
    ])
    block = converted[0]["content"][0]
    assert block["tool_use_id"] == "toolu_9"
    assert block["is_error"] is True


def test_assistant_tool_call_dataclass_and_json_string_args():
    _system, converted = _anthropic_messages([
        {"role": "assistant", "content": "checking",
         "tool_calls": [ToolCall(id="t1", name="get_weather",
                                 arguments={"city": "Oslo"}),
                        {"id": "t2", "name": "get_weather",
                         "arguments": '{"city": "Bergen"}'}]},
    ])
    blocks = converted[0]["content"]
    assert blocks[0] == {"type": "text", "text": "checking"}
    assert blocks[1]["input"] == {"city": "Oslo"}
    assert blocks[2]["input"] == {"city": "Bergen"}


def test_tool_use_response_surfaces_calls():
    response = types.SimpleNamespace(content=[
        _block("text", text="Let me check."),
        _block("tool_use", id="toolu_1", name="get_weather",
               input={"city": "Oslo"}),
    ], stop_reason="tool_use", usage=None)
    captured = {}
    provider = _provider(captured, response)
    result = provider.chat_with_tools([{"role": "user", "content": "hi"}],
                                      tools=TOOLS)
    assert isinstance(result, AnthropicChatResult)
    assert result.text == "Let me check."
    assert result.tool_calls == [ToolCall(id="toolu_1", name="get_weather",
                                          arguments={"city": "Oslo"})]
    assert result.stop_reason == "tool_use"
    assert provider.last_tool_calls == result.tool_calls


def test_tool_use_only_response_chat_returns_empty_and_records_calls():
    response = types.SimpleNamespace(content=[
        _block("tool_use", id="toolu_2", name="get_weather",
               input={"city": "Oslo"}),
    ], stop_reason="tool_use", usage=None)
    provider = _provider({}, response)
    assert provider.chat([{"role": "user", "content": "hi"}],
                         tools=TOOLS) == ""
    assert [c.name for c in provider.last_tool_calls] == ["get_weather"]


def test_empty_response_still_raises_through_chat():
    provider = _provider({}, types.SimpleNamespace(
        content=[], stop_reason="end_turn", usage=None))
    with pytest.raises(ProviderError):
        provider.chat([{"role": "user", "content": "hi"}])


def test_full_tool_round_trip_through_fake_sdk():
    """user -> tool_use answer -> tool_result -> final text, all native."""
    first = types.SimpleNamespace(content=[
        _block("tool_use", id="toolu_1", name="get_weather",
               input={"city": "Oslo"})], stop_reason="tool_use", usage=None)
    captured = {}
    provider = _provider(captured, first)
    result = provider.chat_with_tools(
        [{"role": "user", "content": "weather in Oslo?"}], tools=TOOLS)
    assert result.tool_calls[0].id == "toolu_1"
    second = _provider(captured, _text_response("It is sunny in Oslo."))
    text = second.chat([
        {"role": "user", "content": "weather in Oslo?"},
        {"role": "assistant", "content": "",
         "tool_calls": [{"id": "toolu_1", "name": "get_weather",
                         "arguments": {"city": "Oslo"}}]},
        {"role": "tool", "tool_use_id": "toolu_1", "content": "sunny"},
    ], tools=TOOLS)
    assert text == "It is sunny in Oslo."
    roles = [m["role"] for m in captured["messages"]]
    assert roles == ["user", "assistant", "user"]


# ----------------------------------------------------------------------
# prompt caching
# ----------------------------------------------------------------------

def test_prompt_cache_marks_system_block():
    system, _converted = _anthropic_messages(
        [{"role": "system", "content": "be terse"},
         {"role": "user", "content": "hi"}], prompt_cache=True)
    assert system == [{"type": "text", "text": "be terse",
                       "cache_control": {"type": "ephemeral"}}]


def test_no_cache_keeps_plain_string_system():
    system, _converted = _anthropic_messages(
        [{"role": "system", "content": "be terse"},
         {"role": "user", "content": "hi"}])
    assert system == "be terse"


def test_prompt_cache_reaches_sdk_and_marks_last_tool():
    captured = {}
    provider = _provider(captured, _text_response("ok"))
    provider.chat([{"role": "system", "content": "sys"},
                   {"role": "user", "content": "hi"}],
                  tools=TOOLS, prompt_cache=True)
    assert captured["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert captured["tools"][-1]["cache_control"] == {"type": "ephemeral"}


def test_cache_system_alias():
    captured = {}
    provider = _provider(captured, _text_response("ok"))
    provider.chat([{"role": "system", "content": "sys"},
                   {"role": "user", "content": "hi"}], cache_system=True)
    assert isinstance(captured["system"], list)


def test_per_message_cache_marker_attaches_to_last_block():
    _system, converted = _anthropic_messages([
        {"role": "user", "content": "long context", "cache": True},
        {"role": "user", "content": "question"},
    ])
    assert converted[0]["content"] == [
        {"type": "text", "text": "long context",
         "cache_control": {"type": "ephemeral"}}]
    assert converted[1] == {"role": "user", "content": "question"}


def test_bad_cache_marker_rejected():
    with pytest.raises(ProviderError):
        _anthropic_messages([
            {"role": "user", "content": "hi",
             "cache_control": {"type": "permanent"}}])


def test_usage_parses_cache_token_counts():
    usage = types.SimpleNamespace(
        input_tokens=100, output_tokens=20,
        cache_creation_input_tokens=80, cache_read_input_tokens=50)
    response = types.SimpleNamespace(
        content=[_block("text", text="ok")], stop_reason="end_turn",
        usage=usage)
    result = _provider({}, response).chat_with_tools(
        [{"role": "user", "content": "hi"}], prompt_cache=True)
    assert result.usage is not None
    assert result.usage.prompt_tokens == 100
    assert result.usage.completion_tokens == 20
    assert result.usage.cached_tokens == 130
    assert result.usage.total_tokens == 120


# ----------------------------------------------------------------------
# extended thinking controls
# ----------------------------------------------------------------------

def test_thinking_param_shapes():
    assert _thinking_param(True, 4096) == {
        "type": "enabled", "budget_tokens": 1024}
    assert _thinking_param(2048, 4096) == {
        "type": "enabled", "budget_tokens": 2048}
    assert _thinking_param({"type": "disabled"}, 4096) == {
        "type": "disabled"}
    assert _thinking_param(None, 4096) is None
    assert _thinking_param(
        ReasoningConfig(mode="on", budget_tokens=3000), 4096) == {
        "type": "enabled", "budget_tokens": 3000}
    assert _thinking_param(ReasoningConfig(mode="off"), 4096) is None


def test_thinking_param_rejects_bad_budgets():
    with pytest.raises(ProviderError):
        _thinking_param(0, 4096)
    with pytest.raises(ProviderError):
        _thinking_param({"type": "enabled", "budget_tokens": -5}, 4096)
    with pytest.raises(ProviderError):
        _thinking_param({"type": "enabled", "budget_tokens": 4096}, 4096)
    with pytest.raises(ProviderError):
        _thinking_param({"type": "disabled", "budget_tokens": 10}, 4096)
    with pytest.raises(ProviderError):
        _thinking_param("lots", 4096)


def test_thinking_reaches_sdk_and_thinking_blocks_stay_out_of_text():
    response = types.SimpleNamespace(content=[
        _block("thinking", thinking="weighing the options"),
        _block("text", text="the answer"),
    ], stop_reason="end_turn", usage=None)
    captured = {}
    provider = _provider(captured, response)
    result = provider.chat_with_tools(
        [{"role": "user", "content": "hi"}],
        thinking=True, max_tokens=4096)
    assert captured["thinking"] == {"type": "enabled",
                                    "budget_tokens": 1024}
    assert result.text == "the answer"
    assert result.thinking == "weighing the options"
    # chat() likewise returns only the text blocks.
    provider2 = _provider({}, response)
    assert provider2.chat([{"role": "user", "content": "hi"}],
                          thinking=True, max_tokens=4096) == "the answer"


def test_thinking_budget_must_fit_under_max_tokens_before_client():
    provider = _provider({}, _text_response("ok"))
    with pytest.raises(ProviderError):
        provider.chat([{"role": "user", "content": "hi"}],
                      thinking=2048)  # default max_tokens is 1024


def test_reasoning_alias_and_conflict():
    captured = {}
    provider = _provider(captured, _text_response("ok"))
    provider.chat([{"role": "user", "content": "hi"}],
                  reasoning=ReasoningConfig(mode="on", budget_tokens=512),
                  max_tokens=4096)
    assert captured["thinking"] == {"type": "enabled", "budget_tokens": 512}
    with pytest.raises(ProviderError):
        _provider({}, _text_response("ok")).chat(
            [{"role": "user", "content": "hi"}],
            thinking=True, reasoning=ReasoningConfig(mode="on"),
            max_tokens=4096)


def test_no_thinking_kwarg_sends_no_thinking_param():
    captured = {}
    provider = _provider(captured, _text_response("ok"))
    provider.chat([{"role": "user", "content": "hi"}])
    assert "thinking" not in captured
    assert "tools" not in captured
