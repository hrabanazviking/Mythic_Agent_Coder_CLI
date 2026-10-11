"""TIER: unit

Unit tests for slice 043 (reasoning-mode negotiation).

No network, no sockets, no real keys: negotiation maps a
ReasoningConfig to in-memory wire fragments only.
"""

import pytest

from mythic_agent.providers import reasoning
from mythic_agent.providers.base import Provider, ProviderError
from mythic_agent.providers.reasoning import ReasoningConfig


# ----------------------------------------------------------------------
# Fakes
# ----------------------------------------------------------------------

def _make_provider(name, model=""):
    flags = {"streaming": True, "tool_calling": False,
             "vision": False, "json_mode": False}

    def capabilities(self):
        return dict(flags)

    def chat(self, messages, **kwargs):
        raise ProviderError("fake: chat not implemented")

    cls = type(f"_Provider_{name}", (Provider,), {
        "name": name,
        "capabilities": capabilities,
        "chat": chat,
    })
    instance = cls()
    instance.model = model
    return instance


# ----------------------------------------------------------------------
# ReasoningConfig validation
# ----------------------------------------------------------------------

def test_config_defaults_off():
    config = ReasoningConfig()
    assert config.mode == "off"
    assert config.budget_tokens is None


def test_config_rejects_bad_mode():
    with pytest.raises(ValueError):
        ReasoningConfig(mode="turbo")


def test_config_rejects_bad_budget():
    for bad in (0, -100, "many", 1.5):
        with pytest.raises(ValueError):
            ReasoningConfig(mode="on", budget_tokens=bad)


# ----------------------------------------------------------------------
# mode="off" -> {} everywhere
# ----------------------------------------------------------------------

def test_off_returns_empty_for_all_providers():
    config = ReasoningConfig(mode="off")
    for name in ("openai", "openrouter", "anthropic", "deepseek",
                 "google", "ollama", "mystery"):
        assert reasoning.negotiate(_make_provider(name), config) == {}


# ----------------------------------------------------------------------
# OpenAI / OpenRouter effort mapping
# ----------------------------------------------------------------------

def test_openai_reasoning_effort_explicit():
    for effort in ("low", "medium", "high"):
        fragment = reasoning.negotiate(
            _make_provider("openai"), ReasoningConfig(mode=effort))
        assert fragment == {"reasoning_effort": effort}


def test_openai_effort_derived_from_budget():
    provider = _make_provider("openai")
    assert reasoning.negotiate(
        provider, ReasoningConfig(mode="on",
                                  budget_tokens=1000)) == {
        "reasoning_effort": "low"}
    assert reasoning.negotiate(
        provider, ReasoningConfig(mode="on",
                                  budget_tokens=8000)) == {
        "reasoning_effort": "medium"}
    assert reasoning.negotiate(
        provider, ReasoningConfig(mode="on",
                                  budget_tokens=100_000)) == {
        "reasoning_effort": "high"}
    assert reasoning.negotiate(
        provider, ReasoningConfig(mode="on")) == {
        "reasoning_effort": "medium"}


def test_openrouter_reasoning_shape():
    fragment = reasoning.negotiate(
        _make_provider("openrouter"), ReasoningConfig(mode="high"))
    assert fragment == {"reasoning": {"effort": "high"}}


# ----------------------------------------------------------------------
# Anthropic thinking shape
# ----------------------------------------------------------------------

def test_anthropic_thinking_shape():
    fragment = reasoning.negotiate(
        _make_provider("anthropic"),
        ReasoningConfig(mode="on", budget_tokens=2048))
    assert fragment == {"thinking": {"type": "enabled",
                                     "budget_tokens": 2048}}


def test_anthropic_default_budget():
    fragment = reasoning.negotiate(
        _make_provider("anthropic"), ReasoningConfig(mode="on"))
    assert fragment["thinking"]["budget_tokens"] == \
        reasoning.DEFAULT_THINKING_BUDGET


# ----------------------------------------------------------------------
# DeepSeek: reasoning is model-inherent
# ----------------------------------------------------------------------

def test_deepseek_reasoner_model_on_returns_empty():
    provider = _make_provider("deepseek", model="deepseek-reasoner")
    assert reasoning.negotiate(
        provider, ReasoningConfig(mode="on")) == {}


def test_deepseek_non_reasoner_model_raises():
    provider = _make_provider("deepseek", model="deepseek-chat")
    with pytest.raises(ProviderError):
        reasoning.negotiate(provider, ReasoningConfig(mode="on"))


def test_deepseek_explicit_effort_raises():
    provider = _make_provider("deepseek", model="deepseek-reasoner")
    with pytest.raises(ProviderError):
        reasoning.negotiate(provider, ReasoningConfig(mode="high"))
    with pytest.raises(ProviderError):
        reasoning.negotiate(provider, ReasoningConfig(
            mode="on", budget_tokens=1024))


# ----------------------------------------------------------------------
# Unsupported providers
# ----------------------------------------------------------------------

def test_unsupported_provider_raises():
    for name in ("google", "ollama", "llama.cpp", "vllm", "mystery"):
        with pytest.raises(ProviderError) as excinfo:
            reasoning.negotiate(_make_provider(name),
                                ReasoningConfig(mode="on"))
        assert name in str(excinfo.value)


def test_negotiate_rejects_non_config():
    with pytest.raises(ProviderError):
        reasoning.negotiate(_make_provider("openai"),
                            {"mode": "on"})  # type: ignore[arg-type]
