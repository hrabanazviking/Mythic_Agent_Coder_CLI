"""M-022: Google/Gemini-native adapter — dialect, long context, grounding.

TIER: unit

The real ``google-generativeai`` SDK is never imported and never
installed here: every test either stubs ``google`` /
``google.generativeai`` in ``sys.modules`` (the R-030 pattern) or
exercises a validation path that must fail before any client is
built. No network traffic, no real keys.
"""

import sys
import types

import pytest

from mythic_agent.providers.base import ToolCall
from mythic_agent.providers.context_windows import resolve as resolve_window
from mythic_agent.providers.google import (
    GoogleChatResult,
    GoogleProvider,
    ProviderError,
    _gemini_contents,
    _grounding_tool,
    _tool_config_param,
    _tools_param,
)

FAKE_KEY = "AIza-test-key-000"

TOOLS = [{
    "name": "get_weather",
    "description": "Get the current weather for a city.",
    "parameters": {"type": "object",
                   "properties": {"city": {"type": "string"}},
                   "required": ["city"]},
}]


def _install_genai_stub(monkeypatch, captured, response=None):
    """Install stub ``google`` + ``google.generativeai`` modules with spies."""
    child = types.ModuleType("google.generativeai")
    parent = types.ModuleType("google")
    parent.__path__ = []  # mark as a package
    parent.generativeai = child

    def configure(**kwargs):
        captured.setdefault("configure_calls", []).append(dict(kwargs))

    class GenerativeModel:
        def __init__(self, model_name, **kwargs):
            captured["model_name"] = model_name
            captured["model_kwargs"] = dict(kwargs)

        def generate_content(self, contents, **kwargs):
            captured["contents"] = contents
            captured["gen_kwargs"] = dict(kwargs)
            assert response is not None, "stub needs a response"
            return response() if callable(response) else response

    child.configure = configure
    child.GenerativeModel = GenerativeModel
    monkeypatch.setitem(sys.modules, "google", parent)
    monkeypatch.setitem(sys.modules, "google.generativeai", child)
    return child


def _provider(monkeypatch, captured, response):
    _install_genai_stub(monkeypatch, captured, response=response)
    return GoogleProvider(api_key=FAKE_KEY)


def _candidate_response(text=None, calls=(), finish="STOP", usage=None,
                        grounding=None):
    parts = []
    if text is not None:
        parts.append(types.SimpleNamespace(text=text))
    for name, args in calls:
        parts.append(types.SimpleNamespace(
            function_call=types.SimpleNamespace(name=name, args=args)))
    candidate = types.SimpleNamespace(
        content=types.SimpleNamespace(parts=parts),
        finish_reason=finish, grounding_metadata=grounding)
    return types.SimpleNamespace(candidates=[candidate],
                                 usage_metadata=usage)


# ----------------------------------------------------------------------
# capabilities: the registry's claim is now true in fact
# ----------------------------------------------------------------------

def test_capabilities_unchanged_and_true():
    caps = GoogleProvider(api_key=FAKE_KEY).capabilities()
    assert caps == {"streaming": True, "tool_calling": True,
                    "vision": True, "json_mode": True}


# ----------------------------------------------------------------------
# function declarations + tool_config dialect
# ----------------------------------------------------------------------

def test_tools_param_gemini_dialect():
    payload = _tools_param(TOOLS)
    assert payload == [{"function_declarations": [{
        "name": "get_weather",
        "description": "Get the current weather for a city.",
        "parameters": {"type": "object",
                       "properties": {"city": {"type": "string"}},
                       "required": ["city"]},
    }]}]


def test_tools_param_accepts_input_schema_spelling():
    tools = [{"name": "t", "description": "d",
              "input_schema": {"type": "object"}}]
    assert _tools_param(tools)[0]["function_declarations"][0][
        "parameters"] == {"type": "object"}


def test_tools_param_rejects_bad_specs():
    with pytest.raises(ProviderError):
        _tools_param([])
    with pytest.raises(ProviderError):
        _tools_param([{"description": "no name"}])
    with pytest.raises(ProviderError):
        _tools_param(["not-a-dict"])


def test_tools_reach_sdk_in_native_shape(monkeypatch):
    captured = {}
    provider = _provider(monkeypatch, captured,
                         _candidate_response(text="ok"))
    assert provider.chat([{"role": "user", "content": "weather?"}],
                         tools=TOOLS) == "ok"
    tools = captured["gen_kwargs"]["tools"]
    assert tools[0]["function_declarations"][0]["name"] == "get_weather"
    assert "function" not in tools[0]  # not the OpenAI shim shape


def test_tool_config_shapes():
    assert _tool_config_param("auto") == {
        "function_calling_config": {"mode": "AUTO"}}
    assert _tool_config_param("any") == {
        "function_calling_config": {"mode": "ANY"}}
    assert _tool_config_param({"type": "tool", "name": "get_weather"}) == {
        "function_calling_config": {"mode": "ANY",
                                    "allowed_function_names": ["get_weather"]}}
    assert _tool_config_param({"mode": "none"}) == {
        "function_calling_config": {"mode": "NONE"}}
    assert _tool_config_param(
        {"function_calling_config": {"mode": "AUTO"}}) == {
        "function_calling_config": {"mode": "AUTO"}}
    with pytest.raises(ProviderError):
        _tool_config_param("sometimes")
    with pytest.raises(ProviderError):
        _tool_config_param({"function_calling_config": {"mode": "LOUD"}})


def test_tool_choice_reaches_sdk_as_tool_config(monkeypatch):
    captured = {}
    provider = _provider(monkeypatch, captured,
                         _candidate_response(text="ok"))
    provider.chat([{"role": "user", "content": "hi"}], tools=TOOLS,
                  tool_choice="any")
    assert captured["gen_kwargs"]["tool_config"] == {
        "function_calling_config": {"mode": "ANY"}}
    with pytest.raises(ProviderError):
        provider.chat([{"role": "user", "content": "hi"}],
                      tool_choice="any", tool_config="auto")


# ----------------------------------------------------------------------
# message dialect: function_call / function_response parts
# ----------------------------------------------------------------------

def test_assistant_tool_calls_become_function_call_parts():
    _system, contents = _gemini_contents([
        {"role": "user", "content": "weather in Oslo?"},
        {"role": "assistant", "content": "",
         "tool_calls": [{"id": "c1", "name": "get_weather",
                         "arguments": {"city": "Oslo"}}]},
    ])
    assert contents[1] == {"role": "model", "parts": [
        {"function_call": {"name": "get_weather",
                           "args": {"city": "Oslo"}}}]}


def test_assistant_tool_call_dataclass_and_json_string_args():
    _system, contents = _gemini_contents([
        {"role": "assistant", "content": "checking",
         "tool_calls": [ToolCall(id="t1", name="get_weather",
                                 arguments={"city": "Oslo"}),
                        {"id": "t2", "name": "get_weather",
                         "arguments": '{"city": "Bergen"}'}]},
    ])
    parts = contents[0]["parts"]
    assert parts[0] == "checking"
    assert parts[1]["function_call"]["args"] == {"city": "Oslo"}
    assert parts[2]["function_call"]["args"] == {"city": "Bergen"}


def test_tool_role_named_becomes_function_response():
    _system, contents = _gemini_contents([
        {"role": "tool", "name": "get_weather", "content": "sunny"},
    ])
    assert contents == [{"role": "user", "parts": [
        {"function_response": {"name": "get_weather",
                               "response": {"result": "sunny"}}}]}]


def test_tool_role_json_object_content_parsed():
    _system, contents = _gemini_contents([
        {"role": "tool", "tool_name": "get_weather",
         "content": '{"temp_c": 4}'},
    ])
    assert contents[0]["parts"][0]["function_response"]["response"] == {
        "temp_c": 4}


def test_tool_role_resolves_name_from_earlier_call_id():
    _system, contents = _gemini_contents([
        {"role": "assistant", "content": "",
         "tool_calls": [{"id": "call-9", "name": "get_weather",
                         "arguments": {"city": "Oslo"}}]},
        {"role": "tool", "tool_call_id": "call-9", "content": "sunny"},
    ])
    assert contents[1]["parts"][0]["function_response"]["name"] == \
        "get_weather"


def test_tool_role_resolves_name_as_id_pairing():
    # Gemini issues no call ids: this adapter's parsed calls carry the
    # function name as id, and a generic loop's tool_call_id=<name>
    # must pair back to that function.
    _system, contents = _gemini_contents([
        {"role": "assistant", "content": "",
         "tool_calls": [{"id": "get_weather", "name": "get_weather",
                         "arguments": {}}]},
        {"role": "tool", "tool_call_id": "get_weather", "content": "sunny"},
    ])
    assert contents[1]["parts"][0]["function_response"]["name"] == \
        "get_weather"


def test_vision_list_parts_become_inline_data():
    _system, contents = _gemini_contents([
        {"role": "user", "content": [
            {"type": "text", "text": "what is this?"},
            {"type": "image", "mime_type": "image/png", "data": "AAAA"},
        ]},
    ])
    assert contents == [{"role": "user", "parts": [
        "what is this?", {"mime_type": "image/png", "data": "AAAA"}]}]


# ----------------------------------------------------------------------
# response parsing: function calls surface, text stays text
# ----------------------------------------------------------------------

def test_function_call_response_surfaces_calls(monkeypatch):
    captured = {}
    provider = _provider(monkeypatch, captured, _candidate_response(
        text="Let me check.",
        calls=[("get_weather", {"city": "Oslo"})]))
    result = provider.chat_with_tools(
        [{"role": "user", "content": "hi"}], tools=TOOLS)
    assert isinstance(result, GoogleChatResult)
    assert result.text == "Let me check."
    # Gemini issues no call ids: id is the function name (documented).
    assert result.tool_calls == [ToolCall(
        id="get_weather", name="get_weather", arguments={"city": "Oslo"})]
    assert result.finish_reason == "STOP"
    assert provider.last_tool_calls == result.tool_calls


def test_dict_shaped_candidate_parts_parse():
    response = {"candidates": [{
        "content": {"parts": [
            {"text": "hi "},
            {"function_call": {"name": "f", "args": {"x": 1}}}]},
        "finish_reason": "STOP"}]}
    provider = GoogleProvider(api_key=FAKE_KEY)
    provider._client = lambda: types.SimpleNamespace(  # _send is stubbed
        configure=lambda **kw: None,
        GenerativeModel=lambda name, **kw: object())

    def fake_send(model, contents, **kwargs):
        return response

    provider._send = fake_send
    result = provider.chat_with_tools([{"role": "user", "content": "hi"}])
    assert result.text == "hi "
    assert result.tool_calls[0].name == "f"
    assert result.tool_calls[0].arguments == {"x": 1}


def test_function_call_only_chat_returns_empty_and_records(monkeypatch):
    captured = {}
    provider = _provider(monkeypatch, captured, _candidate_response(
        calls=[("get_weather", {"city": "Oslo"})]))
    assert provider.chat([{"role": "user", "content": "hi"}],
                         tools=TOOLS) == ""
    assert [c.name for c in provider.last_tool_calls] == ["get_weather"]


def test_extract_text_ignores_function_calls_and_raises_on_call_only(
        monkeypatch):
    response = _candidate_response(calls=[("get_weather", {"city": "Oslo"})])
    with pytest.raises(ProviderError):
        GoogleProvider._extract_text(response)
    mixed = _candidate_response(
        text="a", calls=[("get_weather", {"city": "Oslo"})])
    assert GoogleProvider._extract_text(mixed) == "a"


def test_full_tool_round_trip_through_stub_sdk(monkeypatch):
    captured = {}
    provider = _provider(monkeypatch, captured, _candidate_response(
        calls=[("get_weather", {"city": "Oslo"})]))
    result = provider.chat_with_tools(
        [{"role": "user", "content": "weather in Oslo?"}], tools=TOOLS)
    call = result.tool_calls[0]
    captured2 = {}
    provider2 = _provider(monkeypatch, captured2,
                          _candidate_response(text="It is sunny in Oslo."))
    text = provider2.chat([
        {"role": "user", "content": "weather in Oslo?"},
        {"role": "assistant", "content": "",
         "tool_calls": [{"id": call.id, "name": call.name,
                         "arguments": call.arguments}]},
        {"role": "tool", "tool_call_id": call.id, "content": "sunny"},
    ], tools=TOOLS)
    assert text == "It is sunny in Oslo."
    roles = [c["role"] for c in captured2["contents"]]
    assert roles == ["user", "model", "user"]
    assert captured2["contents"][2]["parts"][0][
        "function_response"]["name"] == "get_weather"


def test_safety_finish_with_no_parts_raises_safety(monkeypatch):
    response = types.SimpleNamespace(candidates=[types.SimpleNamespace(
        content=types.SimpleNamespace(parts=[]), finish_reason="SAFETY",
        grounding_metadata=None)], usage_metadata=None)
    provider = _provider(monkeypatch, {}, response)
    with pytest.raises(ProviderError) as exc:
        provider.chat([{"role": "user", "content": "hi"}])
    assert "safety" in str(exc.value).lower()


# ----------------------------------------------------------------------
# long-context handling: real windows, refuse-never-truncate, caching
# ----------------------------------------------------------------------

def test_probe_context_window_gemini_models_are_1m():
    provider = GoogleProvider(api_key=FAKE_KEY)
    assert provider.probe_context_window("gemini-2.5-pro") == 1_048_576
    assert provider.probe_context_window("gemini-2.0-flash") == 1_048_576
    assert provider.probe_context_window("gemini-1.5-pro") == 1_048_576
    assert provider.context_window() == 1_048_576  # its own default model
    assert resolve_window("gemini-2.5-pro", provider) == 1_048_576


def test_probe_context_window_unknown_model_is_generic_fallback():
    provider = GoogleProvider(api_key=FAKE_KEY)
    assert provider.probe_context_window("no-such-model") == 128_000


def test_prompt_over_known_window_refused_before_client():
    # No SDK stub installed: if the guard did not fire first, the chat
    # would fail with ProviderNotConfigured instead of the window error.
    provider = GoogleProvider(api_key=FAKE_KEY)
    huge = "x" * (4 * 1_048_576 + 400)
    with pytest.raises(ProviderError) as exc:
        provider.chat([{"role": "user", "content": huge}])
    assert "context window" in str(exc.value)
    assert "truncated" in str(exc.value)


def test_prompt_under_window_passes_the_guard(monkeypatch):
    captured = {}
    provider = _provider(monkeypatch, captured,
                         _candidate_response(text="ok"))
    assert provider.chat([{"role": "user", "content": "x" * 4000}]) == "ok"


def test_cached_content_passes_through(monkeypatch):
    captured = {}
    provider = _provider(monkeypatch, captured,
                         _candidate_response(text="ok"))
    provider.chat([{"role": "user", "content": "hi"}],
                  cached_content="cachedContents/abc123")
    assert captured["gen_kwargs"]["cached_content"] == \
        "cachedContents/abc123"


def test_cached_content_validated_before_client():
    provider = GoogleProvider(api_key=FAKE_KEY)
    with pytest.raises(ProviderError):
        provider.chat([{"role": "user", "content": "hi"}], cached_content="")
    with pytest.raises(ProviderError):
        provider.chat([{"role": "user", "content": "hi"}], cached_content=7)


def test_usage_parses_cached_content_tokens(monkeypatch):
    usage = types.SimpleNamespace(
        prompt_token_count=1000, candidates_token_count=50,
        total_token_count=1050, cached_content_token_count=800)
    captured = {}
    provider = _provider(monkeypatch, captured,
                         _candidate_response(text="ok", usage=usage))
    result = provider.chat_with_tools([{"role": "user", "content": "hi"}],
                                      cached_content="cachedContents/x")
    assert result.usage is not None
    assert result.usage.prompt_tokens == 1000
    assert result.usage.completion_tokens == 50
    assert result.usage.total_tokens == 1050
    assert result.usage.cached_tokens == 800
    assert provider.last_usage == result.usage


# ----------------------------------------------------------------------
# grounding toggles, where offered
# ----------------------------------------------------------------------

def test_grounding_tool_shapes():
    assert _grounding_tool(True) == {"google_search_retrieval": {}}
    assert _grounding_tool({"dynamic_retrieval_config": {"mode": "auto"}}) == {
        "google_search_retrieval": {
            "dynamic_retrieval_config": {"mode": "auto"}}}
    assert _grounding_tool(None) is None
    assert _grounding_tool(False) is None
    with pytest.raises(ProviderError):
        _grounding_tool("yes")


def test_grounding_reaches_sdk_alongside_function_tools(monkeypatch):
    captured = {}
    provider = _provider(monkeypatch, captured,
                         _candidate_response(text="ok"))
    provider.chat([{"role": "user", "content": "news?"}], tools=TOOLS,
                  grounding=True)
    tools = captured["gen_kwargs"]["tools"]
    assert tools[0]["function_declarations"][0]["name"] == "get_weather"
    assert tools[1] == {"google_search_retrieval": {}}


def test_grounding_off_by_default_and_alias(monkeypatch):
    captured = {}
    provider = _provider(monkeypatch, captured,
                         _candidate_response(text="ok"))
    provider.chat([{"role": "user", "content": "hi"}])
    assert "tools" not in captured["gen_kwargs"]
    captured2 = {}
    provider2 = _provider(monkeypatch, captured2,
                          _candidate_response(text="ok"))
    provider2.chat([{"role": "user", "content": "hi"}], google_search=True)
    assert captured2["gen_kwargs"]["tools"] == [
        {"google_search_retrieval": {}}]
    with pytest.raises(ProviderError):
        provider2.chat([{"role": "user", "content": "hi"}],
                       grounding=True, google_search=True)


def test_grounding_metadata_surfaced(monkeypatch):
    grounding = types.SimpleNamespace(
        web_search_queries=["weather Oslo today"])
    captured = {}
    provider = _provider(monkeypatch, captured, _candidate_response(
        text="sunny", grounding=grounding))
    result = provider.chat_with_tools(
        [{"role": "user", "content": "weather?"}], grounding=True)
    assert result.grounding_metadata == {
        "web_search_queries": ["weather Oslo today"]}
    assert provider.last_grounding_metadata == result.grounding_metadata


def test_no_grounding_metadata_is_none(monkeypatch):
    captured = {}
    provider = _provider(monkeypatch, captured,
                         _candidate_response(text="ok"))
    result = provider.chat_with_tools([{"role": "user", "content": "hi"}])
    assert result.grounding_metadata is None
