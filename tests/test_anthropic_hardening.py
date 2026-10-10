"""R-029: Anthropic adapter hardening tests.

TIER: unit

The real ``anthropic`` SDK is never imported and never installed here:
every test either hides it from ``sys.modules`` (SDK-absent path) or
installs a stub module. No network traffic, no real keys.
"""

import sys
import types

import pytest

from mythic_agent.providers.anthropic import (
    AnthropicAuthError,
    AnthropicProvider,
    AnthropicRateLimitError,
    ProviderError,
    ProviderNotConfigured,
    _anthropic_messages,
    _map_sdk_error,
)

FAKE_KEY = "sk-ant-test-key-000"


def _boom(exc):
    """Build a _send replacement that raises ``exc``."""
    def raiser(*args, **kwargs):
        raise exc
    return raiser


def _text_response(*texts, block_type="text"):
    return types.SimpleNamespace(
        content=[types.SimpleNamespace(type=block_type, text=t)
                 for t in texts])


def _install_sdk_stub(monkeypatch, captured, response=None, error=None):
    """Install a stub ``anthropic`` module; prove the real SDK is untouched."""
    mod = types.ModuleType("anthropic")

    class _Messages:
        def create(self, **params):
            captured["create_params"] = dict(params)
            if error is not None:
                raise error
            assert response is not None, "stub needs a response or an error"
            return response() if callable(response) else response

    class Anthropic:
        def __init__(self, api_key=None):
            captured["client_api_key"] = api_key
            self.messages = _Messages()

    class RateLimitError(Exception):
        status_code = 429

    class AuthenticationError(Exception):
        status_code = 401

    class APIError(Exception):
        """Generic SDK failure; str() may echo request details."""

    mod.Anthropic = Anthropic
    mod.RateLimitError = RateLimitError
    mod.AuthenticationError = AuthenticationError
    mod.APIError = APIError
    monkeypatch.setitem(sys.modules, "anthropic", mod)
    return mod


def _hide_sdk(monkeypatch):
    monkeypatch.setitem(sys.modules, "anthropic", None)


# ----------------------------------------------------------------------
# (a) SDK stubbed in sys.modules; absent SDK / missing key paths
# ----------------------------------------------------------------------

def test_sdk_absent_raises_provider_not_configured(monkeypatch):
    _hide_sdk(monkeypatch)
    provider = AnthropicProvider(api_key=FAKE_KEY)
    with pytest.raises(ProviderNotConfigured) as exc:
        provider._client()
    assert "anthropic" in str(exc.value).lower()


def test_chat_with_absent_sdk_raises_before_network(monkeypatch):
    _hide_sdk(monkeypatch)
    provider = AnthropicProvider(api_key=FAKE_KEY)
    with pytest.raises(ProviderNotConfigured):
        provider.chat([{"role": "user", "content": "Hi"}])


def test_key_missing_raises_provider_not_configured(monkeypatch):
    captured = {}
    _install_sdk_stub(monkeypatch, captured,
                      response=_text_response("hi"))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    provider = AnthropicProvider(api_key=None)
    with pytest.raises(ProviderNotConfigured) as exc:
        provider._client()
    assert "ANTHROPIC_API_KEY" in str(exc.value)


def test_stub_sdk_is_used_and_key_is_wired(monkeypatch):
    captured = {}
    stub = _install_sdk_stub(monkeypatch, captured,
                             response=_text_response("hi"))
    assert sys.modules["anthropic"] is stub  # the stub, never a real SDK
    provider = AnthropicProvider(api_key=FAKE_KEY)
    provider.chat([{"role": "user", "content": "Hi"}])
    assert captured["client_api_key"] == FAKE_KEY


# ----------------------------------------------------------------------
# (b) system-message merging across multiple system blocks
# ----------------------------------------------------------------------

def test_multiple_system_blocks_merge():
    system, converted = _anthropic_messages([
        {"role": "system", "content": "be terse"},
        {"role": "system", "content": "be kind"},
        {"role": "user", "content": "hi"},
    ])
    assert system == "be terse\n\nbe kind"
    assert converted == [{"role": "user", "content": "hi"}]


def test_merged_system_reaches_sdk_call(monkeypatch):
    captured = {}
    _install_sdk_stub(monkeypatch, captured,
                      response=_text_response("ok"))
    provider = AnthropicProvider(api_key=FAKE_KEY)
    provider.chat([
        {"role": "system", "content": "one"},
        {"role": "system", "content": "two"},
        {"role": "user", "content": "hi"},
    ])
    assert captured["create_params"]["system"] == "one\n\ntwo"


def test_no_system_blocks_means_none_system(monkeypatch):
    captured = {}
    _install_sdk_stub(monkeypatch, captured,
                      response=_text_response("ok"))
    provider = AnthropicProvider(api_key=FAKE_KEY)
    provider.chat([{"role": "user", "content": "hi"}])
    assert captured["create_params"]["system"] is None


# ----------------------------------------------------------------------
# (c) tool-block content is explicit, never silently dropped
# ----------------------------------------------------------------------

def test_tool_role_is_rejected_not_dropped():
    with pytest.raises(ProviderError) as exc:
        _anthropic_messages([
            {"role": "user", "content": "hi"},
            {"role": "tool", "content": "tool output"},
        ])
    assert "tool" in str(exc.value).lower()
    assert "capabilities" in str(exc.value).lower()


def test_chat_rejects_tool_transcripts(monkeypatch):
    captured = {}
    _install_sdk_stub(monkeypatch, captured,
                      response=_text_response("ok"))
    provider = AnthropicProvider(api_key=FAKE_KEY)
    with pytest.raises(ProviderError):
        provider.chat([
            {"role": "user", "content": "hi"},
            {"role": "tool", "content": "tool output"},
        ])
    assert "create_params" not in captured  # rejected before any SDK call


def test_tool_calling_capability_is_honest():
    provider = AnthropicProvider(api_key=FAKE_KEY)
    assert provider.capabilities()["tool_calling"] is False
    with pytest.raises(ProviderError):
        provider.require_capability("tool_calling")


# ----------------------------------------------------------------------
# (d) malformed responses -> ProviderError, never raw AttributeError
# ----------------------------------------------------------------------

def test_empty_content_blocks_raise_provider_error():
    with pytest.raises(ProviderError):
        AnthropicProvider._extract_text(types.SimpleNamespace(content=[]))


def test_non_text_blocks_only_raise_provider_error():
    with pytest.raises(ProviderError):
        AnthropicProvider._extract_text(_text_response("x", block_type="tool_use"))


def test_missing_content_attribute_raises_provider_error():
    with pytest.raises(ProviderError):
        AnthropicProvider._extract_text(types.SimpleNamespace())


def test_none_content_raises_provider_error():
    with pytest.raises(ProviderError):
        AnthropicProvider._extract_text(types.SimpleNamespace(content=None))


def test_non_iterable_content_raises_provider_error_not_type_error():
    with pytest.raises(ProviderError):
        AnthropicProvider._extract_text(types.SimpleNamespace(content=42))


def test_malformed_response_end_to_end(monkeypatch):
    captured = {}
    _install_sdk_stub(monkeypatch, captured,
                      response=types.SimpleNamespace())  # no content at all
    provider = AnthropicProvider(api_key=FAKE_KEY)
    with pytest.raises(ProviderError):
        provider.chat([{"role": "user", "content": "hi"}])


# ----------------------------------------------------------------------
# (e) SDK exception mapping, with no key material in error text
# ----------------------------------------------------------------------

def test_rate_limit_maps_to_rate_limit_subclass(monkeypatch):
    captured = {}
    stub = _install_sdk_stub(monkeypatch, captured,
                             response=_text_response("ok"))
    provider = AnthropicProvider(api_key=FAKE_KEY)
    monkeypatch.setattr(
        provider, "_send", _boom(stub.RateLimitError("slow down")))
    with pytest.raises(AnthropicRateLimitError) as exc:
        provider.chat([{"role": "user", "content": "hi"}])
    assert isinstance(exc.value, ProviderError)
    assert FAKE_KEY not in str(exc.value)


def test_auth_error_maps_to_auth_subclass_without_key_material(monkeypatch):
    captured = {}
    stub = _install_sdk_stub(monkeypatch, captured,
                             response=_text_response("ok"))
    # The SDK's own message echoes the key; our mapping must not repeat it.
    sdk_error = stub.AuthenticationError(f"invalid x-api-key: {FAKE_KEY}")
    provider = AnthropicProvider(api_key=FAKE_KEY)
    monkeypatch.setattr(provider, "_send", _boom(sdk_error))
    with pytest.raises(AnthropicAuthError) as exc:
        provider.chat([{"role": "user", "content": "hi"}])
    assert isinstance(exc.value, ProviderError)
    assert FAKE_KEY not in str(exc.value)


def test_generic_sdk_error_maps_to_provider_error_without_key_material(monkeypatch):
    captured = {}
    stub = _install_sdk_stub(monkeypatch, captured,
                             response=_text_response("ok"))
    sdk_error = stub.APIError(f"request failed with key {FAKE_KEY}")
    provider = AnthropicProvider(api_key=FAKE_KEY)
    monkeypatch.setattr(provider, "_send", _boom(sdk_error))
    with pytest.raises(ProviderError) as exc:
        provider.chat([{"role": "user", "content": "hi"}])
    assert not isinstance(exc.value, (AnthropicAuthError, AnthropicRateLimitError))
    assert FAKE_KEY not in str(exc.value)


def test_name_based_mapping_without_status_code():
    class WeirdPermissionDenied(Exception):
        pass

    mapped = _map_sdk_error(WeirdPermissionDenied("nope"))
    assert isinstance(mapped, AnthropicAuthError)

    class OddThrottleBlast(Exception):
        pass

    # "throttle" is not a known token -> generic ProviderError, still safe
    mapped = _map_sdk_error(OddThrottleBlast("nope"))
    assert type(mapped) is ProviderError


def test_status_code_on_nested_response_object_maps():
    class NestedAuth(Exception):
        response = types.SimpleNamespace(status_code=403)

    assert isinstance(_map_sdk_error(NestedAuth()), AnthropicAuthError)


# ----------------------------------------------------------------------
# (f) capabilities honesty: json_mode False must hold
# ----------------------------------------------------------------------

def test_json_mode_capability_is_false():
    assert AnthropicProvider(api_key=FAKE_KEY).capabilities()["json_mode"] is False


def test_chat_rejects_response_format_kwarg(monkeypatch):
    captured = {}
    _install_sdk_stub(monkeypatch, captured,
                      response=_text_response("ok"))
    provider = AnthropicProvider(api_key=FAKE_KEY)
    with pytest.raises(ProviderError) as exc:
        provider.chat([{"role": "user", "content": "hi"}],
                      response_format={"type": "json_object"})
    assert "json" in str(exc.value).lower()
    assert "create_params" not in captured  # rejected before any SDK call


def test_chat_never_emits_json_mode_params(monkeypatch):
    captured = {}
    _install_sdk_stub(monkeypatch, captured,
                      response=_text_response("ok"))
    provider = AnthropicProvider(api_key=FAKE_KEY)
    provider.chat([{"role": "user", "content": "hi"}])
    params = captured["create_params"]
    assert "response_format" not in params
    assert "json_mode" not in params


# ----------------------------------------------------------------------
# (g) model override via kwargs; empty model raises
# ----------------------------------------------------------------------

def test_model_override_via_kwargs(monkeypatch):
    captured = {}
    _install_sdk_stub(monkeypatch, captured,
                      response=_text_response("ok"))
    provider = AnthropicProvider(api_key=FAKE_KEY)
    provider.chat([{"role": "user", "content": "hi"}], model="claude-custom-1")
    assert captured["create_params"]["model"] == "claude-custom-1"


def test_default_model_used_without_override(monkeypatch):
    captured = {}
    _install_sdk_stub(monkeypatch, captured,
                      response=_text_response("ok"))
    provider = AnthropicProvider(api_key=FAKE_KEY)
    provider.chat([{"role": "user", "content": "hi"}])
    assert captured["create_params"]["model"] == "claude-sonnet-4-5"


def test_empty_model_raises_provider_error(monkeypatch):
    captured = {}
    _install_sdk_stub(monkeypatch, captured,
                      response=_text_response("ok"))
    provider = AnthropicProvider(api_key=FAKE_KEY)
    provider.model = ""
    with pytest.raises(ProviderError) as exc:
        provider.chat([{"role": "user", "content": "hi"}])
    assert "model" in str(exc.value).lower()


def test_send_seam_defaults_max_tokens(monkeypatch):
    captured = {}
    _install_sdk_stub(monkeypatch, captured,
                      response=_text_response("ok"))
    provider = AnthropicProvider(api_key=FAKE_KEY)
    provider.chat([{"role": "user", "content": "hi"}])
    assert captured["create_params"]["max_tokens"] == 1024
