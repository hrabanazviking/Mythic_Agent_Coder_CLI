"""TIER: unit

Unit tests for slice R-040 (tool-call negotiation).

No network, no sockets, no real keys: negotiation and parsing operate
on in-memory shapes only; the OpenAI provider is constructed with a
fake transport that must never be called.
"""

import pytest

from mythic_agent.providers.anthropic import AnthropicProvider
from mythic_agent.providers.base import Provider, ProviderError, ToolCall
from mythic_agent.providers.ollama import OllamaProvider
from mythic_agent.providers.openai_compat import OpenAICompatProvider
from mythic_agent.providers import tool_negotiation


# ----------------------------------------------------------------------
# Fakes
# ----------------------------------------------------------------------

class _AnthropicStyleProvider(Provider):
    """Anthropic-named provider WITH tool calling (native adapter lacks it)."""

    name = "anthropic"

    def capabilities(self):
        return {"streaming": True, "tool_calling": True,
                "vision": True, "json_mode": False}

    def chat(self, messages, **kwargs):
        raise ProviderError("stub")


def _boom_transport(path, payload, headers):
    raise AssertionError("negotiation must never touch the network")


def _openai_provider():
    return OpenAICompatProvider(api_key="fake-key", transport=_boom_transport)


def _tools():
    return [{
        "name": "get_weather",
        "description": "Get the current weather for a city.",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    }]


# ----------------------------------------------------------------------
# negotiate(): payload shapes
# ----------------------------------------------------------------------

def test_negotiate_openai_family_shape():
    payload = tool_negotiation.negotiate(_openai_provider(), _tools())
    assert payload == {"tools": [{
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a city.",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
            },
        },
    }]}


def test_negotiate_anthropic_shape():
    payload = tool_negotiation.negotiate(_AnthropicStyleProvider(), _tools())
    assert payload == {"tools": [{
        "name": "get_weather",
        "description": "Get the current weather for a city.",
        "input_schema": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    }]}


def test_negotiate_falls_back_to_openai_style_for_other_names():
    payload = tool_negotiation.negotiate(OllamaProvider(), _tools())
    assert payload["tools"][0]["type"] == "function"
    assert payload["tools"][0]["function"]["name"] == "get_weather"


def test_negotiate_unsupported_provider_raises():
    # The native Anthropic adapter reports tool_calling=False.
    with pytest.raises(ProviderError):
        tool_negotiation.negotiate(AnthropicProvider(api_key="x"), _tools())


def test_negotiate_rejects_empty_tools():
    with pytest.raises(ProviderError):
        tool_negotiation.negotiate(_openai_provider(), [])


def test_negotiate_rejects_tool_without_name():
    with pytest.raises(ProviderError):
        tool_negotiation.negotiate(_openai_provider(), [{"description": "x"}])


def test_negotiate_defaults_missing_description_and_parameters():
    payload = tool_negotiation.negotiate(_openai_provider(),
                                         [{"name": "ping"}])
    function = payload["tools"][0]["function"]
    assert function["description"] == ""
    assert function["parameters"] == {"type": "object"}


# ----------------------------------------------------------------------
# parse_tool_calls(): OpenAI shape
# ----------------------------------------------------------------------

def _openai_raw(arguments='{"city": "Oslo"}'):
    return {"choices": [{
        "message": {"tool_calls": [{
            "id": "call_1",
            "type": "function",
            "function": {"name": "get_weather", "arguments": arguments},
        }]},
    }]}


def test_parse_openai_tool_calls():
    calls = tool_negotiation.parse_tool_calls(_openai_provider(),
                                              _openai_raw())
    assert calls == [ToolCall(id="call_1", name="get_weather",
                              arguments={"city": "Oslo"})]


def test_parse_openai_empty_tool_calls():
    raw = {"choices": [{"message": {}}]}
    assert tool_negotiation.parse_tool_calls(_openai_provider(), raw) == []


def test_parse_openai_bad_arguments_json_raises():
    with pytest.raises(ProviderError):
        tool_negotiation.parse_tool_calls(_openai_provider(),
                                          _openai_raw("not-json{{{"))


def test_parse_openai_missing_choices_raises():
    with pytest.raises(ProviderError):
        tool_negotiation.parse_tool_calls(_openai_provider(), {"nope": 1})


def test_parse_openai_empty_name_raises():
    raw = {"choices": [{"message": {"tool_calls": [
        {"id": "c", "function": {"name": "", "arguments": "{}"}}]}}]}
    with pytest.raises(ProviderError):
        tool_negotiation.parse_tool_calls(_openai_provider(), raw)


# ----------------------------------------------------------------------
# parse_tool_calls(): Anthropic shape
# ----------------------------------------------------------------------

def _anthropic_raw():
    return {"content": [
        {"type": "text", "text": "Let me check."},
        {"type": "tool_use", "id": "toolu_1",
         "name": "get_weather", "input": {"city": "Oslo"}},
    ]}


def test_parse_anthropic_tool_use_blocks():
    calls = tool_negotiation.parse_tool_calls(_AnthropicStyleProvider(),
                                              _anthropic_raw())
    assert calls == [ToolCall(id="toolu_1", name="get_weather",
                              arguments={"city": "Oslo"})]


def test_parse_anthropic_no_tool_use_blocks():
    raw = {"content": [{"type": "text", "text": "no tools here"}]}
    assert tool_negotiation.parse_tool_calls(_AnthropicStyleProvider(),
                                             raw) == []


def test_parse_anthropic_non_dict_input_raises():
    raw = {"content": [{"type": "tool_use", "id": "t", "name": "n",
                        "input": [1, 2]}]}
    with pytest.raises(ProviderError):
        tool_negotiation.parse_tool_calls(_AnthropicStyleProvider(), raw)


def test_parse_rejects_non_dict_raw():
    with pytest.raises(ProviderError):
        tool_negotiation.parse_tool_calls(_openai_provider(), "garbage")
