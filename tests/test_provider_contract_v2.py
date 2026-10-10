"""R-026 / roadmap 026 — Provider Contract V2.

Hardens ``mythic_agent/providers/base.py``:

* ``validate_messages`` rejects malformed chat input with ProviderError,
* ``ChatUsage`` / ``ToolCall`` dataclasses round-trip,
* ``__init_subclass__`` kills bad capability-flag subclasses at
  definition time,
* ``iter_chunks`` default raises ProviderError ("streaming unsupported"),
* ``timeout`` / ``max_retries`` knobs are stored on the instance.

Zero network: no transport is touched anywhere in this module.
"""

from __future__ import annotations

import dataclasses

import pytest

from mythic_agent.providers.base import (
    ChatUsage,
    Provider,
    ProviderError,
    ToolCall,
)


class _EchoProvider(Provider):
    """Minimal concrete provider: validates, then echoes the last text."""

    name = "echo-test"
    default_model = "echo-1"

    def chat(self, messages, **kwargs):
        messages = self.validate_messages(messages)
        return str(messages[-1]["content"])

    def capabilities(self):
        return {"streaming": False, "tool_calling": False,
                "vision": False, "json_mode": True}


# ----------------------------------------------------------------------
# message validation
# ----------------------------------------------------------------------

@pytest.mark.parametrize("bad", [
    None,
    "not-a-list",
    {"role": "user", "content": "hi"},
    [],
    [{"content": "missing role"}],
    [{"role": "superuser", "content": "bad role"}],
    [{"role": "user"}],                       # missing content key
    [{"role": "user", "content": None}],      # None content
    [{"role": "user", "content": 42}],        # non-str/list content
    [{"role": "user", "content": {"x": 1}}],  # dict content
    ["just a string"],
    [None],
])
def test_malformed_messages_rejected(bad):
    with pytest.raises(ProviderError):
        Provider.validate_messages(bad)


def test_malformed_messages_rejected_via_chat():
    provider = _EchoProvider()
    with pytest.raises(ProviderError):
        provider.chat([{"role": "hacker", "content": "x"}])
    with pytest.raises(ProviderError):
        provider.chat("nope")


@pytest.mark.parametrize("good", [
    [{"role": "user", "content": "hi"}],
    [{"role": "system", "content": "be nice"},
     {"role": "user", "content": "hi"},
     {"role": "assistant", "content": "hello"}],
    [{"role": "tool", "content": "result"}],
    [{"role": "developer", "content": "rules"}],
    [{"role": "user", "content": [{"type": "text", "text": "see"}]}],
    [{"role": "user", "content": ""}],  # empty string is allowed, not malformed
])
def test_wellformed_messages_accepted(good):
    assert Provider.validate_messages(good) is good
    assert _EchoProvider().chat(good) == str(good[-1]["content"])


# ----------------------------------------------------------------------
# ChatUsage / ToolCall round-trip
# ----------------------------------------------------------------------

def test_chatusage_round_trip():
    usage = ChatUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
    restored = ChatUsage(**dataclasses.asdict(usage))
    assert restored == usage
    assert restored.total_tokens == 15


def test_chatusage_total_derived_when_omitted():
    usage = ChatUsage(prompt_tokens=10, completion_tokens=5)
    assert usage.total_tokens == 15


def test_chatusage_defaults_zero():
    usage = ChatUsage()
    assert (usage.prompt_tokens, usage.completion_tokens,
            usage.total_tokens) == (0, 0, 0)


def test_toolcall_round_trip():
    call = ToolCall(id="call_1", name="read_file",
                    arguments={"path": "/tmp/x", "n": 3})
    restored = ToolCall(**dataclasses.asdict(call))
    assert restored == call
    assert restored.name == "read_file"
    assert restored.arguments == {"path": "/tmp/x", "n": 3}
    assert isinstance(restored.arguments, dict)


def test_toolcall_defaults():
    call = ToolCall()
    assert call.id == "" and call.name == "" and call.arguments == {}


# ----------------------------------------------------------------------
# __init_subclass__ capability-flag validation
# ----------------------------------------------------------------------

def test_bad_subclass_missing_flag_killed_at_definition():
    with pytest.raises(TypeError, match="capabilities"):
        class _BadFlags(Provider):
            name = "bad-flags"

            def chat(self, messages, **kwargs):
                return "x"

            def capabilities(self):
                return {"streaming": True}  # missing three flags


def test_bad_subclass_extra_flag_killed_at_definition():
    with pytest.raises(TypeError, match="capabilities"):
        class _ExtraFlag(Provider):
            name = "extra-flag"

            def chat(self, messages, **kwargs):
                return "x"

            def capabilities(self):
                return {"streaming": False, "tool_calling": False,
                        "vision": False, "json_mode": False,
                        "teleportation": True}


def test_bad_subclass_non_bool_killed_at_definition():
    with pytest.raises(TypeError, match="capabilities"):
        class _NonBool(Provider):
            name = "non-bool"

            def chat(self, messages, **kwargs):
                return "x"

            def capabilities(self):
                return {"streaming": "yes", "tool_calling": False,
                        "vision": False, "json_mode": False}


def test_good_subclass_survives_definition():
    # _EchoProvider defined at module import already proves this, and its
    # flags are exactly CAPABILITY_FLAGS with bool values.
    assert set(_EchoProvider().capabilities()) == set(Provider.CAPABILITY_FLAGS)


# ----------------------------------------------------------------------
# iter_chunks seam
# ----------------------------------------------------------------------

def test_iter_chunks_default_raises():
    provider = _EchoProvider()
    with pytest.raises(ProviderError, match="streaming unsupported"):
        provider.iter_chunks([{"role": "user", "content": "hi"}])


def test_iter_chunks_overridable():
    class _Streaming(Provider):
        name = "stream-test"

        def chat(self, messages, **kwargs):
            return "full"

        def capabilities(self):
            return {"streaming": True, "tool_calling": False,
                    "vision": False, "json_mode": False}

        def iter_chunks(self, messages, **kwargs):
            yield "par"
            yield "tial"

    assert list(_Streaming().iter_chunks([])) == ["par", "tial"]


# ----------------------------------------------------------------------
# timeout / retry knobs
# ----------------------------------------------------------------------

def test_timeout_retry_defaults_stored():
    provider = _EchoProvider()
    assert provider.timeout == 60.0
    assert provider.max_retries == 2


def test_timeout_retry_custom_stored():
    provider = _EchoProvider(timeout=5.5, max_retries=7)
    assert provider.timeout == 5.5
    assert provider.max_retries == 7


def test_timeout_retry_invalid_rejected():
    with pytest.raises(ValueError):
        _EchoProvider(timeout=0)
    with pytest.raises(ValueError):
        _EchoProvider(timeout=-1)
    with pytest.raises(ValueError):
        _EchoProvider(max_retries=-1)


def test_require_capability_still_works():
    provider = _EchoProvider()
    provider.require_capability("json_mode")  # advertised True -> no raise
    with pytest.raises(ProviderError):
        provider.require_capability("streaming")  # advertised False
    with pytest.raises(ValueError, match="Unknown capability flag"):
        provider.require_capability("teleportation")
