"""TIER: unit

Unit tests for slice 041 (structured-output negotiation).

No network, no sockets, no real keys: negotiation and parsing operate
on in-memory shapes only; providers are fakes or constructed with a
transport that must never be called.
"""

import pytest

from mythic_agent.providers import structured_output
from mythic_agent.providers.base import Provider, ProviderError
from mythic_agent.providers.openai_compat import OpenAICompatProvider


# ----------------------------------------------------------------------
# Fakes
# ----------------------------------------------------------------------

def _make_provider(name, flags):
    def capabilities(self):
        return dict(flags)

    def chat(self, messages, **kwargs):
        raise ProviderError("fake: chat not implemented")

    return type(f"_Provider_{name}", (Provider,), {
        "name": name,
        "capabilities": capabilities,
        "chat": chat,
    })


_NATIVE_FLAGS = {"streaming": True, "tool_calling": True,
                 "vision": True, "json_mode": True}
_NOJSON_FLAGS = {"streaming": True, "tool_calling": False,
                 "vision": True, "json_mode": False}

_SCHEMA = {
    "type": "object",
    "properties": {"answer": {"type": "string"}},
    "required": ["answer"],
}


def _boom_transport(path, payload, headers):
    raise AssertionError("negotiation must never touch the network")


def _openai_provider():
    return OpenAICompatProvider(api_key="fake-key", transport=_boom_transport)


# ----------------------------------------------------------------------
# negotiate(): payload shapes
# ----------------------------------------------------------------------

def test_negotiate_openai_family_shape():
    fragment = structured_output.negotiate(_openai_provider(), _SCHEMA,
                                          name="answer")
    assert fragment == {"response_format": {
        "type": "json_schema",
        "json_schema": {"name": "answer", "schema": _SCHEMA,
                        "strict": False},
    }}


def test_negotiate_strict_passthrough():
    fragment = structured_output.negotiate(
        _openai_provider(), _SCHEMA, strict=True)
    assert fragment["response_format"]["json_schema"]["strict"] is True


def test_negotiate_ollama_format_shape():
    provider = _make_provider("ollama", _NATIVE_FLAGS)()
    fragment = structured_output.negotiate(provider, _SCHEMA)
    assert fragment == {"format": _SCHEMA}


def test_negotiate_google_generation_config_shape():
    provider = _make_provider("google", _NATIVE_FLAGS)()
    fragment = structured_output.negotiate(provider, _SCHEMA)
    assert fragment == {"generation_config": {
        "response_mime_type": "application/json",
        "response_schema": _SCHEMA,
    }}


def test_negotiate_google_chat_passthrough(monkeypatch):
    """negotiate() fragment flows through GoogleProvider.chat() to the SDK."""
    import sys
    import types

    from mythic_agent.providers.google import GoogleProvider

    captured = {}
    child = types.ModuleType("google.generativeai")
    parent = types.ModuleType("google")
    parent.__path__ = []
    parent.generativeai = child

    class GenerativeModel:
        def __init__(self, model_name, **kwargs):
            captured["model_kwargs"] = dict(kwargs)

        def generate_content(self, contents, **kwargs):
            captured["gen_kwargs"] = dict(kwargs)
            return types.SimpleNamespace(text='{"answer": "yes"}')

    child.configure = lambda **kwargs: None
    child.GenerativeModel = GenerativeModel
    monkeypatch.setitem(sys.modules, "google", parent)
    monkeypatch.setitem(sys.modules, "google.generativeai", child)

    provider = GoogleProvider(api_key="fake-key")
    fragment = structured_output.negotiate(provider, _SCHEMA)
    text = provider.chat([{"role": "user", "content": "hi"}], **fragment)
    assert text == '{"answer": "yes"}'
    assert captured["gen_kwargs"]["generation_config"] == {
        "response_mime_type": "application/json",
        "response_schema": _SCHEMA,
    }


def test_google_chat_rejects_non_dict_generation_config(monkeypatch):
    import sys
    import types

    from mythic_agent.providers.google import GoogleProvider

    monkeypatch.setitem(sys.modules, "google", None)
    monkeypatch.setitem(sys.modules, "google.generativeai", None)
    provider = GoogleProvider(api_key="fake-key")
    with pytest.raises(ProviderError):
        provider.chat([{"role": "user", "content": "hi"}],
                      generation_config="not-a-dict")


def test_negotiate_requires_json_mode_capability():
    provider = _make_provider("novel", _NOJSON_FLAGS)()
    with pytest.raises(ProviderError):
        structured_output.negotiate(provider, _SCHEMA)


def test_negotiate_rejects_bad_schema():
    provider = _openai_provider()
    for bad in (None, {}, [], "nope", {"properties": {}}):
        with pytest.raises(ProviderError):
            structured_output.negotiate(provider, bad)


def test_negotiate_rejects_empty_name():
    with pytest.raises(ProviderError):
        structured_output.negotiate(_openai_provider(), _SCHEMA, name="")


def test_negotiate_unknown_family_with_json_mode_raises():
    provider = _make_provider("mysterybox", _NATIVE_FLAGS)()
    with pytest.raises(ProviderError):
        structured_output.negotiate(provider, _SCHEMA)


# ----------------------------------------------------------------------
# prepare(): native vs fallback
# ----------------------------------------------------------------------

def test_prepare_native_returns_fragment():
    provider = _openai_provider()
    messages = [{"role": "user", "content": "hi"}]
    out_messages, fragment = structured_output.prepare(
        provider, messages, _SCHEMA)
    assert out_messages == messages
    assert "response_format" in fragment


def test_prepare_fallback_appends_system_instruction():
    provider = _make_provider("novel", _NOJSON_FLAGS)()
    messages = [{"role": "user", "content": "hi"}]
    out_messages, fragment = structured_output.prepare(
        provider, messages, _SCHEMA)
    assert fragment == {}
    assert len(out_messages) == 2
    assert out_messages[0] == messages[0]  # caller's list untouched
    assert out_messages[1]["role"] == "system"
    assert "JSON Schema" in out_messages[1]["content"]
    assert messages == [{"role": "user", "content": "hi"}]


def test_prepare_validates_messages():
    provider = _openai_provider()
    with pytest.raises(ProviderError):
        structured_output.prepare(provider, [], _SCHEMA)


# ----------------------------------------------------------------------
# parse_json(): native and fallback paths
# ----------------------------------------------------------------------

def test_parse_json_native_strict():
    provider = _openai_provider()
    assert structured_output.parse_json(
        provider, '{"answer": "yes"}') == {"answer": "yes"}
    with pytest.raises(ProviderError):
        structured_output.parse_json(
            provider, '```json\n{"answer": "yes"}\n```')


def test_parse_json_fallback_strips_fences():
    provider = _make_provider("novel", _NOJSON_FLAGS)()
    assert structured_output.parse_json(
        provider, '```json\n{"answer": "yes"}\n```') == {"answer": "yes"}
    assert structured_output.parse_json(
        provider, '```\n{"answer": "yes"}\n```') == {"answer": "yes"}


def test_parse_json_fallback_finds_object_in_prose():
    provider = _make_provider("novel", _NOJSON_FLAGS)()
    text = 'Here you go: {"answer": "yes"} hope that helps.'
    assert structured_output.parse_json(provider, text) == {"answer": "yes"}


def test_parse_json_fallback_ignores_braces_in_strings():
    provider = _make_provider("novel", _NOJSON_FLAGS)()
    text = '{"answer": "a } tricky { string"} trailing'
    assert structured_output.parse_json(provider, text) == {
        "answer": "a } tricky { string"}


def test_parse_json_rejects_garbage():
    provider = _make_provider("novel", _NOJSON_FLAGS)()
    for bad in ("", "   ", "no json here", '{"unclosed": true',
                "[1, 2, 3]", '"just a string"'):
        with pytest.raises(ProviderError):
            structured_output.parse_json(provider, bad)


def test_parse_json_forced_paths():
    provider = _openai_provider()
    # Force fallback on a native provider.
    assert structured_output.parse_json(
        provider, 'x {"a": 1} y', native=False) == {"a": 1}
    # Force native on a non-native provider.
    other = _make_provider("novel", _NOJSON_FLAGS)()
    assert structured_output.parse_json(
        other, '{"a": 1}', native=True) == {"a": 1}


# ----------------------------------------------------------------------
# system_prompt_fallback()
# ----------------------------------------------------------------------

def test_system_prompt_fallback_embeds_schema():
    text = structured_output.system_prompt_fallback(_SCHEMA)
    assert '"answer"' in text
    assert "exactly one JSON object" in text
    with pytest.raises(ProviderError):
        structured_output.system_prompt_fallback({})
