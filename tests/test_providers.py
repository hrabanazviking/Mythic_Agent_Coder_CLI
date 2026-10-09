"""Slice 35 provider tests: registry, capabilities, adapters.

All provider adapters are exercised with stubs; no real provider is
ever contacted.
"""

import pytest

from mythic_agent.providers import registry
from mythic_agent.providers.anthropic import AnthropicProvider, _anthropic_messages
from mythic_agent.providers.base import (
    Provider, ProviderError, ProviderNotConfigured, ProviderNotFound)
from mythic_agent.providers.google import GoogleProvider, _gemini_contents
from mythic_agent.providers.ollama import OllamaProvider


def test_provider_base_is_abstract():
    with pytest.raises(TypeError):
        Provider()


def test_registry_lists_all_providers():
    names = registry.list_providers()
    assert names == ["anthropic", "google", "ollama"]


def test_registry_resolves_each_provider():
    assert isinstance(registry.get_provider("anthropic"), AnthropicProvider)
    assert isinstance(registry.get_provider("google"), GoogleProvider)
    assert isinstance(registry.get_provider("ollama"), OllamaProvider)


def test_registry_accepts_aliases_and_case():
    assert isinstance(registry.get_provider("Claude"), AnthropicProvider)
    assert isinstance(registry.get_provider("gemini"), GoogleProvider)
    assert isinstance(registry.get_provider("local"), OllamaProvider)


def test_registry_rejects_unknown_provider():
    with pytest.raises(ProviderNotFound):
        registry.get_provider("deepseek")


def test_capability_flags_are_boolean_and_stable():
    for name in registry.list_providers():
        caps = registry.get_provider(name).capabilities()
        assert set(caps) == set(Provider.CAPABILITY_FLAGS)
        assert all(isinstance(v, bool) for v in caps.values())


def test_require_capability_raises_for_missing_flag():
    anthropic = registry.get_provider("anthropic")
    with pytest.raises(ProviderError):
        anthropic.require_capability("json_mode")  # anthropic has no strict JSON mode


def test_anthropic_chat_uses_native_messages_shape(monkeypatch):
    provider = AnthropicProvider(api_key="test-key")
    seen = {}

    class FakeBlock:
        type = "text"
        text = "hello from claude"

    class FakeResponse:
        content = [FakeBlock()]

    def fake_send(client, **params):
        seen.update(params)
        return FakeResponse()

    monkeypatch.setattr(provider, "_send", fake_send)
    monkeypatch.setattr(provider, "_client", lambda: object())
    text = provider.chat([
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "Hi"}])
    assert text == "hello from claude"
    assert seen["system"] == "You are helpful."
    assert seen["messages"] == [{"role": "user", "content": "Hi"}]


def _hide_module(monkeypatch, module_name):
    """Make one import fail while every other import keeps working."""
    import builtins
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == module_name or name.startswith(module_name + "."):
            raise ImportError(f"No module named {module_name!r}")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)


def test_anthropic_missing_sdk_raises_before_network(monkeypatch):
    provider = AnthropicProvider(api_key="test-key")
    _hide_module(monkeypatch, "anthropic")
    with pytest.raises(ProviderNotConfigured) as exc:
        provider.chat([{"role": "user", "content": "Hi"}])
    assert "anthropic" in str(exc.value).lower()


def test_anthropic_missing_key_raises_with_remedy(monkeypatch):
    import sys
    import types
    # Stub the SDK so _client() reaches the key check instead of the SDK check.
    stub = types.ModuleType("anthropic")
    stub.Anthropic = lambda **kwargs: object()
    monkeypatch.setitem(sys.modules, "anthropic", stub)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    provider = AnthropicProvider(api_key=None)
    with pytest.raises(ProviderNotConfigured) as exc:
        provider._client()
    assert "ANTHROPIC_API_KEY" in str(exc.value)


def test_google_chat_extracts_text(monkeypatch):
    provider = GoogleProvider(api_key="test-key")

    class FakeResponse:
        text = "hello from gemini"

    seen = {}

    def fake_send(model, contents, **kwargs):
        seen["contents"] = contents
        return FakeResponse()

    monkeypatch.setattr(provider, "_send", fake_send)
    monkeypatch.setattr(provider, "_client", lambda: _FakeGenAI(seen))
    text = provider.chat([
        {"role": "system", "content": "sys"},
        {"role": "assistant", "content": "prev"},
        {"role": "user", "content": "Hi"}])
    assert text == "hello from gemini"
    assert seen["model"] == "gemini-2.0-flash"
    assert seen["system_instruction"] == "sys"
    # assistant turns map to gemini "model" role
    assert seen["contents"][0]["role"] == "model"


class _FakeGenAI:
    def __init__(self, seen):
        self._seen = seen

    def GenerativeModel(self, model, **kwargs):
        self._seen["model"] = model
        self._seen.update(kwargs)
        return object()


def test_google_missing_sdk_raises_provider_not_configured(monkeypatch):
    provider = GoogleProvider(api_key="test-key")
    _hide_module(monkeypatch, "google")
    with pytest.raises(ProviderNotConfigured):
        provider._client()


def test_ollama_chat_posts_native_payload(monkeypatch):
    provider = OllamaProvider(model="llama3.1")
    seen = {}

    def fake_post(path, payload):
        seen["path"] = path
        seen["payload"] = payload
        return {"message": {"role": "assistant", "content": " local reply "}}

    monkeypatch.setattr(provider, "_post", fake_post)
    assert provider.chat([{"role": "user", "content": "Hi"}]) == "local reply"
    assert seen["path"] == "/api/chat"
    assert seen["payload"]["model"] == "llama3.1"
    assert seen["payload"]["stream"] is False


def test_ollama_needs_no_key_and_points_at_loopback():
    provider = OllamaProvider()
    assert provider.api_key is None
    assert provider.host == "http://localhost:11434"


def test_gemini_contents_conversion_helper():
    system, contents = _gemini_contents([
        {"role": "system", "content": "s"},
        {"role": "user", "content": "u"}])
    assert system == "s"
    assert contents == [{"role": "user", "parts": ["u"]}]


def test_anthropic_message_conversion_helper():
    system, messages = _anthropic_messages([
        {"role": "system", "content": "s"},
        {"role": "user", "content": "u"}])
    assert system == "s"
    assert messages == [{"role": "user", "content": "u"}]
