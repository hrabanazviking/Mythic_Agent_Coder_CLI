"""R-027 / roadmap 027 — OpenAI Adapter + R-028 — Local Adapter.

TIER: unit

Tests ``mythic_agent/providers/openai_compat.py`` with a fake transport
seam — zero network traffic, zero real API keys.

Covers:
* request URL / method / payload shape and Authorization header,
* HTTP 401 -> ProviderError auth mapping,
* 429 retried with backoff+jitter then succeeding,
* exhausted retries raise ProviderError,
* no key material leaks into any raised error text,
* empty / malformed choices raise ProviderError,
* (028) local base_url shaping, no Authorization header without a key,
  per-instance model override, malformed-JSON error mapping.
"""

from __future__ import annotations

import socket

import pytest

from mythic_agent.providers import openai_compat
from mythic_agent.providers.base import ProviderError
from mythic_agent.providers.openai_compat import (
    GenericLocalCompatProvider,
    OpenAICompatProvider,
)

FAKE_KEY = "sk-test-fake-key-not-a-real-secret"
MESSAGES = [{"role": "user", "content": "hello"}]


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    """Hard fail if any test in this module opens a real socket."""

    def _blocked(*args, **kwargs):
        raise AssertionError("network socket creation is forbidden here")

    monkeypatch.setattr(socket, "socket", _blocked)


def _ok_body(text="hi there"):
    return {"choices": [{"message": {"role": "assistant", "content": text}}],
            "usage": {"prompt_tokens": 3, "completion_tokens": 2,
                      "total_tokens": 5}}


class _FakeTransport:
    """Injectable transport: scripted (status, body) script, records calls."""

    def __init__(self, script):
        self.script = list(script)
        self.calls = []

    def __call__(self, path, payload, headers):
        self.calls.append({"path": path, "payload": payload,
                           "headers": headers})
        status, body = self.script.pop(0) if self.script else self.script[-1]
        return status, body


def _provider(script, **kwargs):
    kwargs.setdefault("api_key", FAKE_KEY)
    transport = _FakeTransport(script)
    provider = OpenAICompatProvider(transport=transport, **kwargs)
    return provider, transport


# ----------------------------------------------------------------------
# R-027: request shape
# ----------------------------------------------------------------------

def test_request_url_method_shape_and_auth():
    provider, transport = _provider([ (200, _ok_body()) ],
                                    model="gpt-5-test")
    text = provider.chat(MESSAGES)
    assert text == "hi there"
    assert len(transport.calls) == 1
    call = transport.calls[0]
    # URL shaping: base_url + path, POST implied by the seam contract.
    assert provider.base_url == "https://api.openai.com/v1"
    assert call["path"] == "/chat/completions"
    assert provider.base_url + call["path"] == \
        "https://api.openai.com/v1/chat/completions"
    payload = call["payload"]
    assert payload["model"] == "gpt-5-test"
    assert payload["messages"] == [{"role": "user", "content": "hello"}]
    assert call["headers"]["Content-Type"] == "application/json"
    assert call["headers"]["Authorization"] == f"Bearer {FAKE_KEY}"


def test_capabilities_and_defaults():
    provider = OpenAICompatProvider(api_key=FAKE_KEY)
    assert provider.name == "openai"
    assert provider.default_model == "gpt-5"
    assert provider.capabilities() == {"streaming": True,
                                       "tool_calling": True,
                                       "vision": True, "json_mode": True}
    assert provider.timeout == 60.0
    assert provider.max_retries == 2


def test_malformed_messages_rejected_before_transport():
    provider, transport = _provider([(200, _ok_body())])
    with pytest.raises(ProviderError):
        provider.chat([{"role": "nope", "content": "x"}])
    assert transport.calls == []


def test_no_model_configured_raises():
    provider = OpenAICompatProvider(api_key=FAKE_KEY, model="")
    provider.model = ""
    provider.default_model = ""
    with pytest.raises(ProviderError, match="No model"):
        provider.chat(MESSAGES)


def test_httpx2_first_declared_fallback_pattern():
    """Repo rule: httpx2 tried first, plain httpx only as ImportError fallback."""
    import ast
    import pathlib
    tree = ast.parse(pathlib.Path(openai_compat.__file__).read_text())
    found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Try):
            tried = [a.name for n in node.body
                     if isinstance(n, ast.Import) for a in n.names]
            caught = [a.name for h in node.handlers
                      for n in h.body if isinstance(n, ast.Import)
                      for a in n.names]
            if "httpx2" in tried and "httpx" in caught:
                found = True
    assert found, "missing the declared try: httpx2 / except: httpx pattern"


# ----------------------------------------------------------------------
# R-027: error mapping + retries + redaction
# ----------------------------------------------------------------------

def test_auth_error_mapping_401():
    provider, _ = _provider([(401, {"error": {"message": "bad key"}})])
    with pytest.raises(ProviderError, match="authentication failed") as exc:
        provider.chat(MESSAGES)
    assert FAKE_KEY not in str(exc.value)


def test_auth_error_mapping_403():
    provider, _ = _provider([(403, {})])
    with pytest.raises(ProviderError, match="authentication failed"):
        provider.chat(MESSAGES)


def test_429_retry_then_success(monkeypatch):
    sleeps = []
    monkeypatch.setattr(openai_compat.time, "sleep", sleeps.append)
    provider, transport = _provider(
        [(429, {"error": "slow down"}), (200, _ok_body("recovered"))],
        max_retries=2)
    assert provider.chat(MESSAGES) == "recovered"
    assert len(transport.calls) == 2
    assert len(sleeps) == 1 and sleeps[0] > 0  # backoff+jitter applied


def test_5xx_retry_then_success(monkeypatch):
    monkeypatch.setattr(openai_compat.time, "sleep", lambda s: None)
    provider, transport = _provider(
        [(503, {}), (500, {}), (200, _ok_body("third time"))],
        max_retries=3)
    assert provider.chat(MESSAGES) == "third time"
    assert len(transport.calls) == 3


def test_exhausted_retries_raise(monkeypatch):
    monkeypatch.setattr(openai_compat.time, "sleep", lambda s: None)
    provider, transport = _provider([(503, {"oops": 1})] * 5, max_retries=2)
    with pytest.raises(ProviderError, match="HTTP 503"):
        provider.chat(MESSAGES)
    assert len(transport.calls) == 3  # 1 initial + 2 retries


def test_no_retry_on_plain_400():
    provider, transport = _provider([(400, {"error": "bad request"})])
    with pytest.raises(ProviderError, match="HTTP 400"):
        provider.chat(MESSAGES)
    assert len(transport.calls) == 1


def test_no_key_material_in_any_error_text():
    key = "sk-test-super-secret-key-000"
    # Body echoes the key back: it must never surface in raised text.
    evil_body = {"error": {"message": f"invalid key {key} rejected"}}
    for status in (400, 401, 429, 500):
        provider, _ = _provider([(status, evil_body)], api_key=key,
                                max_retries=0)
        with pytest.raises(ProviderError) as exc:
            provider.chat(MESSAGES)
        assert key not in str(exc.value), f"key leaked on HTTP {status}"


def test_redact_helper():
    provider = OpenAICompatProvider(api_key=FAKE_KEY)
    scrubbed = provider._redact(f"boom {FAKE_KEY} boom")
    assert FAKE_KEY not in scrubbed
    assert "***REDACTED***" in scrubbed


# ----------------------------------------------------------------------
# R-027: response extraction
# ----------------------------------------------------------------------

@pytest.mark.parametrize("body", [
    {},
    {"choices": []},
    {"choices": [{"message": {"content": ""}}]},
    {"choices": [{"message": {"content": "   "}}]},
    {"choices": [{"message": {}}]},
    {"choices": [{}]},
    {"choices": "not-a-list"},
    {"nope": True},
])
def test_empty_or_malformed_choices_raise(body):
    provider, _ = _provider([(200, body)])
    with pytest.raises(ProviderError, match="(no choices|empty assistant)"):
        provider.chat(MESSAGES)


def test_extract_text_returns_first_choice():
    body = {"choices": [
        {"message": {"role": "assistant", "content": "first"}},
        {"message": {"role": "assistant", "content": "second"}}]}
    provider, _ = _provider([(200, body)])
    assert provider.chat(MESSAGES) == "first"


# ----------------------------------------------------------------------
# R-028: local adapter generalization
# ----------------------------------------------------------------------

def test_local_base_url_shaping():
    transport = _FakeTransport([(200, _ok_body("local hi"))])
    provider = GenericLocalCompatProvider(transport=transport)
    assert provider.base_url == "http://localhost:1234/v1"
    assert provider.chat(MESSAGES) == "local hi"
    call = transport.calls[0]
    assert provider.base_url + call["path"] == \
        "http://localhost:1234/v1/chat/completions"


def test_local_custom_base_url_trailing_slash_stripped():
    transport = _FakeTransport([(200, _ok_body())])
    provider = GenericLocalCompatProvider(
        base_url="http://localhost:8080/v1/", transport=transport)
    assert provider.base_url == "http://localhost:8080/v1"
    provider.chat(MESSAGES)
    assert provider.base_url + transport.calls[0]["path"] == \
        "http://localhost:8080/v1/chat/completions"


def test_no_authorization_header_when_key_is_none():
    transport = _FakeTransport([(200, _ok_body())])
    provider = GenericLocalCompatProvider(transport=transport)
    assert provider.api_key is None
    provider.chat(MESSAGES)
    assert "Authorization" not in transport.calls[0]["headers"]


def test_authorization_header_sent_when_key_given():
    transport = _FakeTransport([(200, _ok_body())])
    provider = GenericLocalCompatProvider(api_key="local-key",
                                          transport=transport)
    provider.chat(MESSAGES)
    assert transport.calls[0]["headers"]["Authorization"] == "Bearer local-key"


def test_per_instance_model_override():
    transport = _FakeTransport([(200, _ok_body())])
    provider = GenericLocalCompatProvider(model="my-local-model",
                                          transport=transport)
    provider.chat(MESSAGES)
    assert transport.calls[0]["payload"]["model"] == "my-local-model"
    assert GenericLocalCompatProvider.default_model == "local-model"


def test_for_endpoint_classmethod():
    transport = _FakeTransport([(200, _ok_body())])
    provider = OpenAICompatProvider.for_endpoint(
        "http://pi:11434/v1", model="qwen", transport=transport)
    assert provider.base_url == "http://pi:11434/v1"
    provider.chat(MESSAGES)
    assert transport.calls[0]["payload"]["model"] == "qwen"


def test_local_provider_flag_validation_and_caps():
    provider = GenericLocalCompatProvider()
    assert set(provider.capabilities()) == \
        {"streaming", "tool_calling", "vision", "json_mode"}
    assert provider.name == "local-openai"


def test_malformed_json_error_mapping(monkeypatch):
    """_real_post maps a JSON decode failure to ProviderError, no network."""

    class _BadJSON:
        status_code = 200

        def json(self):
            raise ValueError("No JSON could be decoded")

    class _StubResponse:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def post(self, url, headers=None, json=None):
            assert url == "http://localhost:1234/v1/chat/completions"
            return _BadJSON()

    class _StubClient:
        def __init__(self, timeout=None):
            pass

        def __enter__(self):
            return _StubResponse()

        def __exit__(self, *exc):
            return False

    monkeypatch.setattr(openai_compat.httpx2, "Client", _StubClient)
    provider = GenericLocalCompatProvider()
    with pytest.raises(ProviderError, match="malformed JSON"):
        provider.chat(MESSAGES)
