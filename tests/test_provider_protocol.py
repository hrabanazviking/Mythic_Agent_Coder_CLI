"""R-017 / roadmap 017 — Protocol Invariants (Provider Protocol).

Proves, with ZERO network traffic, that every registered provider
adapter honors the ``Provider`` protocol in
``mythic_agent/providers/base.py``:

* exposes ``chat`` / ``capabilities`` with protocol-compatible
  signatures (checked with ``inspect.signature`` against the base),
* raises ``ProviderError`` (or a subclass) on bad input — empty model
  name, malformed host, malformed response body — never a raw
  ``ValueError`` / ``Exception``,
* is resolvable through the registry, which rejects unknown names with
  ``ProviderNotFound`` and resolves duplicate registrations
  deterministically,
* normalizes synthetic responses through its extraction / conversion
  helpers into the documented shapes (the closest thing adapters have
  to a streaming-chunk normalizer; the protocol itself defines no
  ``stream`` method),
* and that a deliberately non-conformant fake adapter FAILS the
  protocol check (negative control — proves the check is real).

Network policy: an autouse fixture forbids socket creation for the
whole module. Adapters are constructed with fake credentials /
endpoints, and the one transport seam (``urllib.request.urlopen``) is
stubbed wherever a failure path must be exercised.
"""

from __future__ import annotations

import inspect
import socket
import urllib.request
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from mythic_agent.core.exceptions import MythicError, MythicProviderError
from mythic_agent.providers import registry
from mythic_agent.providers.anthropic import AnthropicProvider, _anthropic_messages
from mythic_agent.providers.base import (
    Provider,
    ProviderError,
    ProviderNotConfigured,
    ProviderNotFound,
)
from mythic_agent.providers.google import GoogleProvider, _gemini_contents
from mythic_agent.providers.ollama import OllamaProvider

ADAPTERS: list[type[Provider]] = [AnthropicProvider, GoogleProvider, OllamaProvider]
NAME_TO_CLS: dict[str, type[Provider]] = {cls.name: cls for cls in ADAPTERS}
FAKE_KEY = "fake-test-key-not-a-secret"


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    """Hard fail if any test in this module opens a real socket."""

    def _blocked(*args, **kwargs):
        raise AssertionError("network socket creation is forbidden in protocol tests")

    monkeypatch.setattr(socket, "socket", _blocked)


# ----------------------------------------------------------------------
# The protocol check itself (also exercised by the negative controls)
# ----------------------------------------------------------------------

def check_provider_protocol(adapter_cls: type[Provider]) -> None:
    """Raise AssertionError unless ``adapter_cls`` honors the Provider protocol.

    Checks, against ``mythic_agent.providers.base.Provider``:
      * subclassing and full implementation of abstract methods,
      * ``chat`` parameter names/kinds and return annotation,
      * ``capabilities`` parameter names/kinds and return annotation,
      * presence of the required class attributes (``name``,
        ``default_model``, ``api_key_env``),
      * that ``capabilities()`` returns booleans for known flags only.
    """
    label = getattr(adapter_cls, "__name__", repr(adapter_cls))
    assert isinstance(adapter_cls, type) and issubclass(adapter_cls, Provider), (
        f"{label} is not a Provider subclass")
    abstract = getattr(adapter_cls, "__abstractmethods__", frozenset())
    assert not abstract, (
        f"{label} leaves abstract methods unimplemented: {sorted(abstract)}")

    base_chat = inspect.signature(Provider.chat)
    chat = inspect.signature(adapter_cls.chat)
    base_params = list(base_chat.parameters.values())
    params = list(chat.parameters.values())
    assert [p.name for p in params] == [p.name for p in base_params], (
        f"{label}.chat parameter names { [p.name for p in params] } "
        f"do not match protocol {[p.name for p in base_params]}")
    assert [p.kind for p in params] == [p.kind for p in base_params], (
        f"{label}.chat parameter kinds do not match the protocol")
    assert params[1].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD, (
        f"{label}.chat must accept 'messages' positionally")
    assert params[2].kind is inspect.Parameter.VAR_KEYWORD, (
        f"{label}.chat must accept **kwargs")
    assert chat.return_annotation == base_chat.return_annotation, (
        f"{label}.chat return annotation {chat.return_annotation!r} != "
        f"protocol {base_chat.return_annotation!r}")

    base_caps = inspect.signature(Provider.capabilities)
    caps = inspect.signature(adapter_cls.capabilities)
    assert [p.name for p in caps.parameters.values()] == ["self"], (
        f"{label}.capabilities signature does not match the protocol")
    assert caps.return_annotation == base_caps.return_annotation, (
        f"{label}.capabilities return annotation {caps.return_annotation!r} != "
        f"protocol {base_caps.return_annotation!r}")

    assert isinstance(adapter_cls.name, str) and adapter_cls.name != "unknown", (
        f"{label} must set a canonical registry name")
    assert hasattr(adapter_cls, "default_model"), f"{label} must define default_model"
    assert hasattr(adapter_cls, "api_key_env"), f"{label} must define api_key_env"

    instance = adapter_cls(api_key=FAKE_KEY) if adapter_cls is not OllamaProvider \
        else adapter_cls()
    flags = instance.capabilities()
    assert set(flags) <= set(Provider.CAPABILITY_FLAGS), (
        f"{label}.capabilities() returned unknown flags: "
        f"{sorted(set(flags) - set(Provider.CAPABILITY_FLAGS))}")
    assert all(isinstance(v, bool) for v in flags.values()), (
        f"{label}.capabilities() values must be booleans")


# ----------------------------------------------------------------------
# Protocol conformance of every registered adapter
# ----------------------------------------------------------------------

def test_registry_lists_exactly_the_known_adapters():
    assert set(registry.list_providers()) == set(NAME_TO_CLS)
    assert registry.list_providers() == sorted(registry.list_providers())


@pytest.mark.parametrize("adapter_cls", ADAPTERS, ids=[c.__name__ for c in ADAPTERS])
def test_adapter_passes_protocol_check(adapter_cls):
    check_provider_protocol(adapter_cls)


def test_protocol_requires_exactly_chat_and_capabilities():
    # The protocol's abstract surface is fixed; streaming is a capability
    # flag, not a method, so no chunk-normalizer method is required.
    assert set(Provider.__abstractmethods__) == {"chat", "capabilities"}
    for adapter_cls in ADAPTERS:
        assert "stream_chat" not in adapter_cls.__dict__
        assert "_normalize_chunk" not in adapter_cls.__dict__


# ----------------------------------------------------------------------
# ProviderError hierarchy (recently migrated to the MythicError taxonomy)
# ----------------------------------------------------------------------

def test_provider_error_hierarchy_is_preserved():
    assert issubclass(ProviderError, MythicProviderError)
    assert issubclass(ProviderError, MythicError)
    assert issubclass(ProviderError, RuntimeError)
    assert not issubclass(ProviderError, ValueError)
    assert issubclass(ProviderNotConfigured, ProviderError)
    assert issubclass(ProviderNotFound, ProviderError)


# ----------------------------------------------------------------------
# Bad input -> ProviderError, never a raw ValueError/Exception
# ----------------------------------------------------------------------

@pytest.mark.parametrize("adapter_cls", [AnthropicProvider, GoogleProvider],
                         ids=["AnthropicProvider", "GoogleProvider"])
def test_empty_model_name_raises_provider_error(adapter_cls):
    provider = adapter_cls(api_key=FAKE_KEY)
    with pytest.raises(ProviderError) as excinfo:
        provider.chat([{"role": "user", "content": "hello"}], model="")
    assert not isinstance(excinfo.value, ValueError)
    assert isinstance(excinfo.value, MythicError)


def test_ollama_empty_model_name_raises_provider_error():
    # OllamaProvider falls back to default_model on falsy constructor args,
    # so the true empty-model state is an empty self.model.
    provider = OllamaProvider()
    provider.model = ""
    with pytest.raises(ProviderError, match="No model configured") as excinfo:
        provider.chat([{"role": "user", "content": "hello"}])
    assert not isinstance(excinfo.value, ValueError)


@pytest.mark.parametrize("adapter_cls", [AnthropicProvider, GoogleProvider],
                         ids=["AnthropicProvider", "GoogleProvider"])
def test_empty_message_list_raises_provider_error(adapter_cls):
    provider = adapter_cls(api_key=FAKE_KEY)
    with pytest.raises(ProviderError):
        provider.chat([], model="some-model")


class _FakeReply:
    """Minimal context-manager stand-in for an HTTP response object."""

    def __init__(self, body: bytes):
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "_FakeReply":
        return self

    def __exit__(self, *args) -> bool:
        return False


def test_ollama_empty_message_list_raises_provider_error():
    # Ollama forwards the empty list; the server's error-shaped body must
    # still surface as ProviderError, never as a raw transport/decode error.
    provider = OllamaProvider(model="llama3.1")
    reply = _FakeReply(b'{"error": "messages required"}')
    with patch.object(urllib.request, "urlopen", return_value=reply):
        with pytest.raises(ProviderError) as excinfo:
            provider.chat([])
    assert not isinstance(excinfo.value, ValueError)


def test_malformed_ollama_host_raises_provider_error_not_valueerror():
    # 'not a url' makes urllib.request.Request raise ValueError("unknown url
    # type") before any socket exists; the adapter must wrap it.
    provider = OllamaProvider(model="llama3.1", host="not a url")
    with pytest.raises(ProviderError) as excinfo:
        provider.chat([{"role": "user", "content": "hello"}])
    assert not isinstance(excinfo.value, ValueError)
    assert "malformed" in str(excinfo.value).lower()


def test_ollama_transport_failure_is_wrapped_as_provider_error():
    provider = OllamaProvider(model="llama3.1", host="http://127.0.0.1:1")
    with patch.object(urllib.request, "urlopen", side_effect=OSError("refused")):
        with pytest.raises(ProviderError) as excinfo:
            provider.chat([{"role": "user", "content": "hello"}])
    assert not isinstance(excinfo.value, OSError)
    assert "unreachable" in str(excinfo.value).lower()


def test_ollama_malformed_response_body_is_wrapped_as_provider_error():
    # A non-JSON body must surface as ProviderError (malformed response),
    # not as a raw json.JSONDecodeError (a ValueError subclass).
    provider = OllamaProvider(model="llama3.1")
    reply = _FakeReply(b"this is not json{{")
    with patch.object(urllib.request, "urlopen", return_value=reply):
        with pytest.raises(ProviderError) as excinfo:
            provider.chat([{"role": "user", "content": "hello"}])
    assert type(excinfo.value) is ProviderError
    assert not isinstance(excinfo.value, ValueError)


# ----------------------------------------------------------------------
# Registry behavior
# ----------------------------------------------------------------------

def test_registry_rejects_unknown_provider_with_clear_error():
    with pytest.raises(ProviderNotFound) as excinfo:
        registry.get_provider("definitely-not-a-provider")
    message = str(excinfo.value)
    assert "Unknown provider" in message
    for name in registry.list_providers():
        assert name in message  # the remedy lists what IS available
    assert isinstance(excinfo.value, ProviderError)  # taxonomy preserved


def test_registry_is_case_insensitive_and_honors_aliases():
    assert isinstance(registry.get_provider("ANTHROPIC", api_key=FAKE_KEY),
                      AnthropicProvider)
    assert isinstance(registry.get_provider("claude", api_key=FAKE_KEY),
                      AnthropicProvider)
    assert isinstance(registry.get_provider("gemini", api_key=FAKE_KEY),
                      GoogleProvider)
    assert isinstance(registry.get_provider("local"), OllamaProvider)


def test_registry_forwards_constructor_kwargs():
    provider = registry.get_provider("ollama", model="test-model",
                                     host="http://example.invalid:11434")
    assert isinstance(provider, OllamaProvider)
    assert provider.model == "test-model"
    assert provider.host == "http://example.invalid:11434"


def test_registry_duplicate_registration_is_deterministic_last_write_wins(monkeypatch):
    """There is no public register() API; ``_REGISTRY`` is a plain dict, so
    registering the same name twice overwrites deterministically — the
    last write wins, and no error is raised."""

    class First(AnthropicProvider):
        name = "dupe-probe"

    class Second(AnthropicProvider):
        name = "dupe-probe"

    monkeypatch.setitem(registry._REGISTRY, "dupe-probe", First)
    assert isinstance(registry.get_provider("dupe-probe", api_key=FAKE_KEY), First)
    monkeypatch.setitem(registry._REGISTRY, "dupe-probe", Second)
    assert isinstance(registry.get_provider("dupe-probe", api_key=FAKE_KEY), Second)


# ----------------------------------------------------------------------
# Response / message normalization shape (synthetic chunks, no network)
# ----------------------------------------------------------------------

def _anthropic_text_response(*texts: str, block_type: str = "text"):
    return SimpleNamespace(
        content=[SimpleNamespace(type=block_type, text=t) for t in texts])


def test_anthropic_extract_text_shape_on_synthetic_response():
    assert AnthropicProvider._extract_text(_anthropic_text_response("he", "llo")) == "hello"
    # non-text blocks are ignored, not concatenated
    mixed = SimpleNamespace(content=[
        SimpleNamespace(type="text", text="a"),
        SimpleNamespace(type="tool_use", text="IGNORED"),
    ])
    assert AnthropicProvider._extract_text(mixed) == "a"
    # malformed chunk shape (no text blocks) -> ProviderError, not a raw error
    with pytest.raises(ProviderError):
        AnthropicProvider._extract_text(SimpleNamespace(content=[]))


def test_google_extract_text_shape_on_synthetic_response():
    assert GoogleProvider._extract_text(SimpleNamespace(text="hello")) == "hello"
    with pytest.raises(ProviderError):
        GoogleProvider._extract_text(SimpleNamespace(text=None))
    with pytest.raises(ProviderError):
        GoogleProvider._extract_text(SimpleNamespace(text=""))


def test_anthropic_message_converter_output_shape():
    system, converted = _anthropic_messages([
        {"role": "system", "content": "be terse"},
        {"role": "system", "content": "be kind"},
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ])
    assert system == "be terse\n\nbe kind"
    assert converted == [{"role": "user", "content": "hi"},
                         {"role": "assistant", "content": "hello"}]
    assert all(set(m) == {"role", "content"} for m in converted)


def test_gemini_contents_converter_output_shape():
    system, contents = _gemini_contents([
        {"role": "system", "content": "sys"},
        {"role": "assistant", "content": "a"},
        {"role": "user", "content": "u"},
    ])
    assert system == "sys"
    assert [c["role"] for c in contents] == ["model", "user"]
    assert all(set(c) == {"role", "parts"} for c in contents)


def test_ollama_message_normalization_keeps_role_and_content():
    provider = OllamaProvider(model="llama3.1")
    captured: dict = {}

    def fake_post(self, path, payload):
        captured.update(payload)
        return {"message": {"content": "ok"}}

    with patch.object(OllamaProvider, "_post", fake_post):
        assert provider.chat([{"role": "user", "content": "hi"}]) == "ok"
    assert captured["model"] == "llama3.1"
    assert captured["stream"] is False
    assert captured["messages"] == [{"role": "user", "content": "hi"}]
    with patch.object(OllamaProvider, "_post",
                      lambda self, path, payload: {"message": {"content": "  "}}):
        with pytest.raises(ProviderError):
            provider.chat([{"role": "user", "content": "hi"}])


# ----------------------------------------------------------------------
# require_capability contract (inherited from the base)
# ----------------------------------------------------------------------

def test_require_capability_contract():
    provider = AnthropicProvider(api_key=FAKE_KEY)
    provider.require_capability("streaming")  # advertised -> no raise
    with pytest.raises(ValueError, match="Unknown capability flag"):
        provider.require_capability("teleportation")  # base-specified behavior
    with pytest.raises(ProviderError):
        provider.require_capability("json_mode")  # advertised False


# ----------------------------------------------------------------------
# Negative controls: deliberately non-conformant fakes MUST fail
# ----------------------------------------------------------------------

class _MissingChat(Provider):
    """Implements capabilities but forgets chat entirely."""
    name = "broken-missing-chat"

    def capabilities(self) -> dict[str, bool]:
        return {"streaming": False, "tool_calling": False,
                "vision": False, "json_mode": False}


class _WrongChatSignature(Provider):
    """chat() with an incompatible signature (no messages, no kwargs)."""
    name = "broken-chat-signature"

    def chat(self):  # type: ignore[override]
        return "x"

    def capabilities(self) -> dict[str, bool]:
        return {"streaming": False, "tool_calling": False,
                "vision": False, "json_mode": False}


class _RawValueErrorProvider(Provider):
    """Raises a raw ValueError on bad input instead of ProviderError."""
    name = "broken-raw-exception"

    def chat(self, messages, **kwargs):
        raise ValueError("raw boom")

    def capabilities(self) -> dict[str, bool]:
        return {"streaming": False, "tool_calling": False,
                "vision": False, "json_mode": False}


def test_nonconformant_fakes_fail_the_protocol_check():
    with pytest.raises(AssertionError):
        check_provider_protocol(_MissingChat)
    with pytest.raises(AssertionError):
        check_provider_protocol(_WrongChatSignature)


def test_raw_value_error_is_detected_as_non_provider_error():
    provider = _RawValueErrorProvider()
    with pytest.raises(ValueError) as excinfo:
        provider.chat([{"role": "user", "content": "hi"}], model="")
    # This is exactly what the bad-input tests forbid in real adapters:
    assert not isinstance(excinfo.value, ProviderError)
    assert not isinstance(excinfo.value, MythicError)
