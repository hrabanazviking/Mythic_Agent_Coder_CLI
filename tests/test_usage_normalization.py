"""TIER: unit

Unit tests for slice 045 (usage normalization).

No network, no sockets, no real keys: mapping operates on in-memory
response bodies only.
"""

import pytest

from mythic_agent.providers import usage
from mythic_agent.providers.base import ChatUsage, Provider, ProviderError


# ----------------------------------------------------------------------
# Fakes
# ----------------------------------------------------------------------

def _make_provider(name):
    flags = {"streaming": True, "tool_calling": False,
             "vision": False, "json_mode": False}

    def capabilities(self):
        return dict(flags)

    def chat(self, messages, **kwargs):
        raise ProviderError("fake: chat not implemented")

    return type(f"_Provider_{name}", (Provider,), {
        "name": name,
        "capabilities": capabilities,
        "chat": chat,
    })()


# ----------------------------------------------------------------------
# estimate_tokens()
# ----------------------------------------------------------------------

def test_estimate_tokens_heuristic():
    assert usage.estimate_tokens("") == 0
    assert usage.estimate_tokens("a") == 1
    assert usage.estimate_tokens("x" * 400) == 100
    assert usage.estimate_tokens("x" * 401) == 100


# ----------------------------------------------------------------------
# normalize(): per-family shapes
# ----------------------------------------------------------------------

def test_normalize_openai_shape():
    provider = _make_provider("openai")
    record = usage.normalize(
        provider, {"usage": {"prompt_tokens": 10, "completion_tokens": 4,
                             "total_tokens": 14}})
    assert record == ChatUsage(prompt_tokens=10, completion_tokens=4,
                               total_tokens=14)
    assert record.estimated is False


def test_normalize_openai_derives_total():
    provider = _make_provider("openai")
    record = usage.normalize(
        provider, {"usage": {"prompt_tokens": 10, "completion_tokens": 4}})
    assert record.total_tokens == 14


def test_normalize_anthropic_shape_with_cache():
    provider = _make_provider("anthropic")
    record = usage.normalize(provider, {
        "input_tokens": 100, "output_tokens": 20,
        "cache_creation_input_tokens": 30,
        "cache_read_input_tokens": 10})
    assert record.prompt_tokens == 100
    assert record.completion_tokens == 20
    assert record.cached_tokens == 40
    assert record.total_tokens == 120


def test_normalize_google_shape():
    provider = _make_provider("google")
    record = usage.normalize(provider, {
        "usageMetadata": {"promptTokenCount": 50,
                          "candidatesTokenCount": 10,
                          "totalTokenCount": 60,
                          "cachedContentTokenCount": 5}})
    assert record.prompt_tokens == 50
    assert record.completion_tokens == 10
    assert record.total_tokens == 60
    assert record.cached_tokens == 5


def test_normalize_ollama_shape():
    provider = _make_provider("ollama")
    record = usage.normalize(
        provider, {"prompt_eval_count": 33, "eval_count": 7})
    assert record.prompt_tokens == 33
    assert record.completion_tokens == 7
    assert record.total_tokens == 40


def test_normalize_google_missing_metadata_falls_back():
    provider = _make_provider("google")
    record = usage.normalize(provider, {}, fallback_text="x" * 80)
    assert record.estimated is True
    assert record.completion_tokens == 20


# ----------------------------------------------------------------------
# Estimation fallback
# ----------------------------------------------------------------------

def test_normalize_none_raw_estimates():
    provider = _make_provider("openai")
    record = usage.normalize(provider, None, fallback_text="x" * 400)
    assert record.estimated is True
    assert record.prompt_tokens == 0
    assert record.completion_tokens == 100
    assert record.total_tokens == 100


def test_normalize_empty_text_estimates_zero():
    provider = _make_provider("openai")
    record = usage.normalize(provider, None, fallback_text="")
    assert record.estimated is True
    assert record.total_tokens == 0


def test_normalize_missing_usage_key_estimates():
    provider = _make_provider("openai")
    record = usage.normalize(provider, {"choices": []},
                             fallback_text="hello world")
    assert record.estimated is True
    assert record.completion_tokens == 2  # 11 chars // 4


# ----------------------------------------------------------------------
# Failure behavior
# ----------------------------------------------------------------------

def test_normalize_rejects_non_dict_raw():
    provider = _make_provider("openai")
    with pytest.raises(ProviderError):
        usage.normalize(provider, "nope")


def test_normalize_rejects_negative_counts():
    provider = _make_provider("openai")
    with pytest.raises(ProviderError):
        usage.normalize(provider, {"usage": {"prompt_tokens": -1,
                                             "completion_tokens": 0}})


def test_normalize_rejects_non_int_counts():
    provider = _make_provider("anthropic")
    with pytest.raises(ProviderError):
        usage.normalize(provider, {"input_tokens": "lots",
                                   "output_tokens": 0})
    # Bool is not a valid count either.
    with pytest.raises(ProviderError):
        usage.normalize(provider, {"input_tokens": True,
                                   "output_tokens": 0})


# ----------------------------------------------------------------------
# ChatUsage additions (slice 045 contract)
# ----------------------------------------------------------------------

def test_chat_usage_new_fields_default_absent():
    record = ChatUsage(prompt_tokens=1, completion_tokens=2)
    assert record.cached_tokens == 0
    assert record.estimated is False
