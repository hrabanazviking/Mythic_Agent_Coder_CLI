"""TIER: unit

Unit tests for slices R-037 (capability discovery), R-038 (model
capability registry), and R-039 (context-window discovery).

No network, no sockets, no real keys: R-037's live probe is driven
through the OpenAICompatProvider fake ``transport=`` seam, so the
mapping / TTL / degradation logic is tested without any invented
live results.
"""

import pytest

from mythic_agent.providers import capabilities, context_windows, model_registry
from mythic_agent.providers.base import (
    Provider, ProviderError, ProviderNotConfigured, ToolCall)
from mythic_agent.providers.openai_compat import OpenAICompatProvider


# ----------------------------------------------------------------------
# Shared fakes
# ----------------------------------------------------------------------

class _FakeTransport:
    """Records (path, payload, headers); returns scripted (status, body)."""

    def __init__(self, script):
        self.script = list(script)
        self.calls = []

    def __call__(self, path, payload, headers):
        self.calls.append({"path": path, "payload": payload,
                           "headers": headers})
        if not self.script:
            raise AssertionError("fake transport called with empty script")
        action = self.script.pop(0)
        if isinstance(action, Exception):
            raise action
        return action


class _NoBaseUrlProvider(Provider):
    """Provider without a base_url: live discovery must refuse it."""

    name = "nourl"

    def capabilities(self):
        return {flag: False for flag in Provider.CAPABILITY_FLAGS}

    def chat(self, messages, **kwargs):
        raise ProviderError("stub")


def _probed_provider(script, **kwargs):
    kwargs.setdefault("api_key", "fake-key")
    transport = _FakeTransport(script)
    return OpenAICompatProvider(transport=transport, **kwargs), transport


@pytest.fixture(autouse=True)
def _clear_probe_cache():
    capabilities._CACHE.clear()
    yield
    capabilities._CACHE.clear()


# ----------------------------------------------------------------------
# R-037: capability discovery
# ----------------------------------------------------------------------

def test_probe_maps_model_id_substrings_to_flags():
    provider, transport = _probed_provider(
        [(200, {"data": [{"id": "gpt-4o-mini"}, {"id": "gpt-3.5-turbo"}]})])
    flags = capabilities.probe_capabilities(provider)
    assert flags == {"streaming": True, "tool_calling": True,
                     "vision": True, "json_mode": True}
    assert transport.calls[0]["path"] == "/models"


def test_probe_unknown_model_ids_yield_blank_flags():
    provider, _ = _probed_provider(
        [(200, {"data": [{"id": "some-custom-model"}]})])
    assert capabilities.probe_capabilities(provider) == {
        "streaming": False, "tool_calling": False,
        "vision": False, "json_mode": False}


def test_probe_result_cached_within_ttl():
    now = [1000.0]
    provider, transport = _probed_provider(
        [(200, {"data": [{"id": "gpt-4o"}]})] * 3)
    first = capabilities.probe_capabilities(provider, clock=lambda: now[0])
    second = capabilities.probe_capabilities(provider, clock=lambda: now[0])
    assert first == second
    assert len(transport.calls) == 1  # second hit the cache


def test_probe_cache_expires_after_ttl():
    now = [1000.0]
    provider, transport = _probed_provider(
        [(200, {"data": [{"id": "gpt-4o"}]})] * 3)
    capabilities.probe_capabilities(provider, ttl=300.0,
                                    clock=lambda: now[0])
    now[0] += 301.0
    capabilities.probe_capabilities(provider, ttl=300.0,
                                    clock=lambda: now[0])
    assert len(transport.calls) == 2


def test_probe_failure_degrades_to_static_capabilities():
    provider, _ = _probed_provider([ProviderError("boom")])
    assert capabilities.probe_capabilities(provider) == provider.capabilities()


def test_probe_non_200_degrades_gracefully():
    provider, _ = _probed_provider([(503, {"error": "down"})])
    assert capabilities.probe_capabilities(provider) == provider.capabilities()


def test_probe_malformed_body_degrades_gracefully():
    provider, _ = _probed_provider([(200, {"nope": []})])
    assert capabilities.probe_capabilities(provider) == provider.capabilities()


def test_probe_requires_base_url():
    with pytest.raises(ProviderError):
        capabilities.probe_capabilities(_NoBaseUrlProvider(api_key="x"))


def test_invalidate_drops_cached_probe():
    provider, transport = _probed_provider(
        [(200, {"data": [{"id": "gpt-4o"}]})] * 2)
    capabilities.probe_capabilities(provider)
    capabilities.invalidate(provider)
    capabilities.probe_capabilities(provider)
    assert len(transport.calls) == 2


# ----------------------------------------------------------------------
# R-038: model capability registry
# ----------------------------------------------------------------------

def test_validate_table_passes():
    model_registry.validate_table()


def test_every_table_entry_has_all_four_bool_flags_and_positive_window():
    for pattern, flags, window in model_registry.MODEL_TABLE:
        assert set(flags) == set(Provider.CAPABILITY_FLAGS)
        assert all(isinstance(v, bool) for v in flags.values())
        assert isinstance(window, int) and window > 0


@pytest.mark.parametrize("model,window", [
    ("gpt-5", 400_000),
    ("gpt-5-mini", 400_000),
    ("gpt-4o", 128_000),
    ("gpt-4o-2024-08-06", 128_000),
    ("claude-sonnet-4-5", 200_000),
    ("claude-sonnet-4-5-20250929", 200_000),
    ("claude-opus-4-1", 200_000),
    ("gemini-2.0-flash", 1_048_576),
    ("gemini-2.5-pro", 1_048_576),
    ("deepseek-chat", 128_000),
    ("deepseek-reasoner", 128_000),
    ("llama3.1:8b", 131_072),
    ("qwen3:14b", 32_768),
    ("mistral-large-2411", 128_000),
])
def test_lookup_known_models(model, window):
    flags, found = model_registry.lookup(model)
    assert found == window
    assert set(flags) == set(Provider.CAPABILITY_FLAGS)


def test_lookup_first_match_wins():
    # gpt-4o matches the gpt-4o row before any broader row could claim it.
    flags, window = model_registry.lookup("gpt-4o")
    assert window == 128_000
    assert flags["vision"] is True


def test_lookup_known_returns_blank_for_unknown():
    flags, window = model_registry.lookup("mystery-model-xyz")
    assert window == 8_192
    assert flags == {"streaming": False, "tool_calling": False,
                     "vision": False, "json_mode": False}


def test_lookup_rejects_non_string_and_empty():
    for bad in ("", None, 123, ["gpt-4o"]):
        flags, window = model_registry.lookup(bad)
        assert window == 8_192
        assert all(v is False for v in flags.values())


def test_known_helper():
    assert model_registry.known("gpt-5") is True
    assert model_registry.known("mystery-model-xyz") is False


# ----------------------------------------------------------------------
# R-039: context-window discovery
# ----------------------------------------------------------------------

def test_resolve_prefers_registry():
    assert context_windows.resolve("gpt-4o") == 128_000
    assert context_windows.resolve("claude-opus-4") == 200_000


def test_resolve_falls_back_to_documented_default():
    assert (context_windows.resolve("mystery-model-xyz")
            == context_windows.DEFAULT_CONTEXT_WINDOW == 128_000)


def test_resolve_uses_provider_probe_hook():
    class Hooked(Provider):
        name = "hooked"

        def capabilities(self):
            return {flag: True for flag in Provider.CAPABILITY_FLAGS}

        def chat(self, messages, **kwargs):
            raise ProviderError("stub")

        def probe_context_window(self, model):
            assert model == "mystery-model-xyz"
            return 64_000

    assert context_windows.resolve("mystery-model-xyz",
                                   Hooked(api_key="x")) == 64_000


def test_resolve_rejects_bad_probe_hook_value():
    class BadHook(Provider):
        name = "badhook"

        def capabilities(self):
            return {flag: True for flag in Provider.CAPABILITY_FLAGS}

        def chat(self, messages, **kwargs):
            raise ProviderError("stub")

        def probe_context_window(self, model):
            return "huge"

    with pytest.raises(ProviderError):
        context_windows.resolve("mystery-model-xyz", BadHook(api_key="x"))


def _msgs():
    return [
        {"role": "system", "content": "sys!"},
        {"role": "user", "content": "aaaa"},
        {"role": "user", "content": "bbbb"},
        {"role": "user", "content": "cccc"},
    ]


def test_truncate_exact_fit_keeps_everything():
    messages = _msgs()  # 4 tokens total with the default len//4 heuristic
    assert context_windows.truncate_messages(messages, 4) == messages


def test_truncate_one_over_drops_oldest_non_system():
    result = context_windows.truncate_messages(_msgs(), 3)
    assert [m["content"] for m in result] == ["sys!", "bbbb", "cccc"]


def test_truncate_empty_list():
    assert context_windows.truncate_messages([], 100) == []


def test_truncate_keeps_single_oversized_message():
    messages = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "x" * 100},  # 25 tokens > max
    ]
    result = context_windows.truncate_messages(messages, 4)
    assert result == messages  # kept as-is, never dropped


def test_truncate_never_drops_system_messages():
    messages = _msgs()
    result = context_windows.truncate_messages(messages, 1)
    assert result[0]["role"] == "system"
    assert result[0]["content"] == "sys!"


def test_truncate_preserves_order_and_accepts_custom_estimator():
    messages = _msgs()
    result = context_windows.truncate_messages(
        messages, 2, estimate=lambda text: 1)
    assert [m["content"] for m in result] == ["sys!", "cccc"]
