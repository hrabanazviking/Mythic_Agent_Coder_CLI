"""R-031..R-036 — local & third-party OpenAI-compatible provider adapters.

TIER: unit

Tests the six dusk-forge provider slices with fake transports and stubbed
seams only — no network, no real API keys, no sockets:

* R-031 openrouter.py — URL shaping, HTTP-Referer/X-Title headers,
  inherited auth mapping.
* R-032 deepseek.py — reasoning_content fallback incl. reasoning-only.
* R-033 ollama.py — malformed host, connection-refused remedy, malformed
  JSON, honored timeout, list_models() via stubbed _get.
* R-034 llamacpp.py — attrs, no auth header, health() via stubbed _http_get.
* R-035 vllm.py — "token-abc123" placeholder convention, OpenAI-shape parity.
* R-036 lmstudio.py — attrs, no auth header, chat via fake transport.
"""

from __future__ import annotations

import socket
import urllib.request
from unittest.mock import patch

import pytest

from mythic_agent.providers import registry
from mythic_agent.providers.base import Provider, ProviderError
from mythic_agent.providers.deepseek import DeepSeekProvider
from mythic_agent.providers.llamacpp import LlamaCppProvider
from mythic_agent.providers.lmstudio import LMStudioProvider
from mythic_agent.providers.ollama import OllamaProvider
from mythic_agent.providers.openai_compat import OpenAICompatProvider
from mythic_agent.providers.openrouter import (
    DEFAULT_HTTP_REFERER,
    DEFAULT_X_TITLE,
    OpenRouterProvider,
)
from mythic_agent.providers.vllm import PLACEHOLDER_API_KEY, VLLMProvider

FAKE_KEY = "fake-test-key-not-real"
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


def _capabilities_honest(provider):
    caps = provider.capabilities()
    assert set(caps) == set(Provider.CAPABILITY_FLAGS)
    assert all(isinstance(v, bool) for v in caps.values())


# ----------------------------------------------------------------------
# R-031: OpenRouter
# ----------------------------------------------------------------------

class TestOpenRouter:
    def test_attrs(self):
        provider = OpenRouterProvider(api_key=FAKE_KEY)
        assert provider.name == "openrouter"
        assert provider.api_key_env == "OPENROUTER_API_KEY"
        assert provider.default_model == "openrouter/auto"
        assert provider.model == "openrouter/auto"
        assert provider.base_url == "https://openrouter.ai/api/v1"
        _capabilities_honest(provider)

    def test_url_shaping_and_required_headers(self):
        transport = _FakeTransport([(200, _ok_body())])
        provider = OpenRouterProvider(api_key=FAKE_KEY, transport=transport)
        assert provider.chat(MESSAGES) == "hi there"
        call = transport.calls[0]
        assert call["path"] == "/chat/completions"
        assert call["payload"]["model"] == "openrouter/auto"
        headers = call["headers"]
        # Both identification headers are ALWAYS sent.
        assert headers["HTTP-Referer"] == DEFAULT_HTTP_REFERER
        assert headers["X-Title"] == DEFAULT_X_TITLE
        assert headers["Authorization"] == f"Bearer {FAKE_KEY}"

    def test_headers_overridable_via_kwargs(self):
        transport = _FakeTransport([(200, _ok_body())])
        provider = OpenRouterProvider(
            api_key=FAKE_KEY, transport=transport,
            http_referer="https://example.test/app",
            x_title="Example Test App")
        provider.chat(MESSAGES)
        headers = transport.calls[0]["headers"]
        assert headers["HTTP-Referer"] == "https://example.test/app"
        assert headers["X-Title"] == "Example Test App"

    def test_auth_mapping_inherited(self):
        transport = _FakeTransport([(401, {"error": "bad key"})])
        provider = OpenRouterProvider(api_key="wrong", transport=transport,
                                      max_retries=0)
        with pytest.raises(ProviderError, match="authentication failed"):
            provider.chat(MESSAGES)

    def test_no_key_means_no_authorization_but_headers_still_sent(self):
        transport = _FakeTransport([(200, _ok_body())])
        provider = OpenRouterProvider(transport=transport)
        provider.chat(MESSAGES)
        headers = transport.calls[0]["headers"]
        assert "Authorization" not in headers
        assert headers["HTTP-Referer"] == DEFAULT_HTTP_REFERER
        assert headers["X-Title"] == DEFAULT_X_TITLE


# ----------------------------------------------------------------------
# R-032: DeepSeek
# ----------------------------------------------------------------------

class TestDeepSeek:
    def test_attrs(self):
        provider = DeepSeekProvider(api_key=FAKE_KEY)
        assert provider.name == "deepseek"
        assert provider.api_key_env == "DEEPSEEK_API_KEY"
        assert provider.default_model == "deepseek-chat"
        assert provider.model == "deepseek-chat"
        assert provider.base_url == "https://api.deepseek.com/v1"
        _capabilities_honest(provider)

    def test_content_returned_normally(self):
        body = {"choices": [{"message": {
            "role": "assistant",
            "content": "final answer",
            "reasoning_content": "chain of thought"}}]}
        transport = _FakeTransport([(200, body)])
        provider = DeepSeekProvider(api_key=FAKE_KEY, transport=transport)
        assert provider.chat(MESSAGES) == "final answer"

    def test_reasoning_only_response_falls_back(self):
        # deepseek-reasoner may emit reasoning_content with no content.
        body = {"choices": [{"message": {
            "role": "assistant",
            "content": "",
            "reasoning_content": "let me think through this"}}]}
        transport = _FakeTransport([(200, body)])
        provider = DeepSeekProvider(api_key=FAKE_KEY, transport=transport)
        assert provider.chat(MESSAGES) == "let me think through this"

    def test_missing_content_key_falls_back(self):
        body = {"choices": [{"message": {
            "role": "assistant",
            "reasoning_content": "silent reasoning"}}]}
        transport = _FakeTransport([(200, body)])
        provider = DeepSeekProvider(api_key=FAKE_KEY, transport=transport)
        assert provider.chat(MESSAGES) == "silent reasoning"

    def test_both_empty_raises_provider_error(self):
        body = {"choices": [{"message": {"role": "assistant",
                                        "content": "  ",
                                        "reasoning_content": ""}}]}
        transport = _FakeTransport([(200, body)])
        provider = DeepSeekProvider(api_key=FAKE_KEY, transport=transport)
        with pytest.raises(ProviderError, match="empty assistant text"):
            provider.chat(MESSAGES)

    def test_url_shaping(self):
        transport = _FakeTransport([(200, _ok_body())])
        provider = DeepSeekProvider(api_key=FAKE_KEY, transport=transport)
        provider.chat(MESSAGES)
        assert transport.calls[0]["path"] == "/chat/completions"
        assert transport.calls[0]["headers"]["Authorization"] == \
            f"Bearer {FAKE_KEY}"


# ----------------------------------------------------------------------
# R-033: Ollama hardening
# ----------------------------------------------------------------------

class _FakeReply:
    def __init__(self, payload: bytes):
        self._payload = payload

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class TestOllamaHardening:
    def test_malformed_host_not_a_url(self):
        provider = OllamaProvider(model="llama3.1", host="not a url")
        with pytest.raises(ProviderError) as excinfo:
            provider.chat(MESSAGES)
        assert not isinstance(excinfo.value, ValueError)
        assert "malformed" in str(excinfo.value).lower()

    def test_malformed_host_missing_scheme(self):
        # "localhost:11434" parses with an empty scheme — must map to
        # malformed-host, not to connection-refused/unreachable.
        provider = OllamaProvider(model="llama3.1", host="localhost:11434")
        with pytest.raises(ProviderError) as excinfo:
            provider.chat(MESSAGES)
        assert "malformed" in str(excinfo.value).lower()

    def test_malformed_host_ftp_scheme(self):
        provider = OllamaProvider(model="llama3.1", host="ftp://example.test/x")
        with pytest.raises(ProviderError) as excinfo:
            provider.chat(MESSAGES)
        assert "malformed" in str(excinfo.value).lower()

    def test_connection_refused_has_remedy(self):
        provider = OllamaProvider(model="llama3.1", host="http://127.0.0.1:1")
        with patch.object(urllib.request, "urlopen",
                          side_effect=ConnectionRefusedError("refused")):
            with pytest.raises(ProviderError) as excinfo:
                provider.chat(MESSAGES)
        text = str(excinfo.value).lower()
        assert "refused" in text
        assert "ollama serve" in text

    def test_malformed_json_is_provider_error(self):
        provider = OllamaProvider(model="llama3.1")
        with patch.object(urllib.request, "urlopen",
                          return_value=_FakeReply(b"this is not json{{")):
            with pytest.raises(ProviderError) as excinfo:
                provider.chat(MESSAGES)
        assert "malformed json" in str(excinfo.value).lower()

    def test_timeout_honored_on_urlopen(self):
        provider = OllamaProvider(model="llama3.1", timeout=5.0)
        seen = {}

        def fake_urlopen(request, timeout=None):
            seen["timeout"] = timeout
            return _FakeReply(
                b'{"message": {"role": "assistant", "content": "ok"}}')

        with patch.object(urllib.request, "urlopen", fake_urlopen):
            assert provider.chat(MESSAGES) == "ok"
        assert seen["timeout"] == 5.0

    def test_default_timeout_is_120(self):
        provider = OllamaProvider(model="llama3.1")
        assert provider.timeout == 120.0

    def test_list_models_uses_get_api_tags(self):
        provider = OllamaProvider(model="llama3.1")
        seen = {}

        def fake_get(path):
            seen["path"] = path
            return {"models": [{"name": "llama3.1"}, {"name": "mistral"}]}

        provider._get = fake_get  # stubbed seam: no live server
        assert provider.list_models() == ["llama3.1", "mistral"]
        assert seen["path"] == "/api/tags"

    def test_list_models_empty_raises(self):
        provider = OllamaProvider(model="llama3.1")
        provider._get = lambda path: {"models": []}
        with pytest.raises(ProviderError, match="no installed models"):
            provider.list_models()

    def test_list_models_validates_host_first(self):
        provider = OllamaProvider(model="llama3.1", host="not a url")
        with pytest.raises(ProviderError, match="malformed"):
            provider.list_models()

    def test_capabilities_honest(self):
        _capabilities_honest(OllamaProvider())


# ----------------------------------------------------------------------
# R-034: llama.cpp server
# ----------------------------------------------------------------------

class TestLlamaCpp:
    def test_attrs(self):
        provider = LlamaCppProvider()
        assert provider.name == "llama.cpp"
        assert provider.api_key_env is None
        assert provider.base_url == "http://localhost:8080/v1"
        _capabilities_honest(provider)

    def test_name_is_registry_safe(self):
        # Must not clash with any already-registered provider name.
        assert "llama.cpp" not in registry.list_providers()

    def test_no_authorization_header_without_key(self):
        transport = _FakeTransport([(200, _ok_body())])
        provider = LlamaCppProvider(transport=transport)
        assert provider.chat(MESSAGES) == "hi there"
        headers = transport.calls[0]["headers"]
        assert "Authorization" not in headers
        assert transport.calls[0]["path"] == "/chat/completions"

    def test_health_true_on_200(self):
        provider = LlamaCppProvider()
        seen = {}

        def fake_get(path):
            seen["path"] = path
            return 200, {"status": "ok"}

        provider._http_get = fake_get
        assert provider.health() is True
        assert seen["path"] == "/health"

    def test_health_false_on_non_200(self):
        provider = LlamaCppProvider()
        provider._http_get = lambda path: (503, {"status": "loading"})
        assert provider.health() is False

    def test_health_false_on_transport_failure(self):
        provider = LlamaCppProvider()

        def boom(path):
            raise ProviderError("connection refused")

        provider._http_get = boom
        assert provider.health() is False


# ----------------------------------------------------------------------
# R-035: vLLM
# ----------------------------------------------------------------------

class TestVLLM:
    def test_attrs(self):
        provider = VLLMProvider()
        assert provider.name == "vllm"
        assert provider.api_key_env is None
        assert provider.base_url == "http://localhost:8000/v1"
        _capabilities_honest(provider)

    def test_placeholder_token_sent_without_key(self):
        transport = _FakeTransport([(200, _ok_body())])
        provider = VLLMProvider(transport=transport)
        provider.chat(MESSAGES)
        headers = transport.calls[0]["headers"]
        assert headers["Authorization"] == f"Bearer {PLACEHOLDER_API_KEY}"
        assert PLACEHOLDER_API_KEY == "token-abc123"

    def test_real_key_overrides_placeholder(self):
        transport = _FakeTransport([(200, _ok_body())])
        provider = VLLMProvider(api_key="real-key", transport=transport)
        provider.chat(MESSAGES)
        headers = transport.calls[0]["headers"]
        assert headers["Authorization"] == "Bearer real-key"

    def test_openai_shape_parity(self):
        # Same messages/model must produce the identical request payload
        # and path as the base OpenAICompatProvider — only the
        # Authorization strategy differs.
        script = lambda: [(200, _ok_body())]  # noqa: E731
        vllm_transport = _FakeTransport(script())
        openai_transport = _FakeTransport(script())
        vllm = VLLMProvider(model="vllm-model", transport=vllm_transport)
        openai = OpenAICompatProvider(api_key=FAKE_KEY, model="vllm-model",
                                      transport=openai_transport)
        assert vllm.chat(MESSAGES) == openai.chat(MESSAGES) == "hi there"
        v_call, o_call = vllm_transport.calls[0], openai_transport.calls[0]
        assert v_call["path"] == o_call["path"] == "/chat/completions"
        assert v_call["payload"] == o_call["payload"]
        assert v_call["payload"]["model"] == "vllm-model"

    def test_auth_mapping_inherited(self):
        transport = _FakeTransport([(403, {"error": "forbidden"})])
        provider = VLLMProvider(transport=transport, max_retries=0)
        with pytest.raises(ProviderError, match="authentication failed"):
            provider.chat(MESSAGES)


# ----------------------------------------------------------------------
# R-036: LM Studio
# ----------------------------------------------------------------------

class TestLMStudio:
    def test_attrs(self):
        provider = LMStudioProvider()
        assert provider.name == "lmstudio"
        assert provider.api_key_env is None
        assert provider.base_url == "http://localhost:1234/v1"
        _capabilities_honest(provider)

    def test_chat_and_no_auth_header(self):
        transport = _FakeTransport([(200, _ok_body("lm studio says hi"))])
        provider = LMStudioProvider(transport=transport)
        assert provider.chat(MESSAGES) == "lm studio says hi"
        call = transport.calls[0]
        assert call["path"] == "/chat/completions"
        assert call["payload"]["model"] == "lmstudio-local"
        assert "Authorization" not in call["headers"]

    def test_model_override(self):
        transport = _FakeTransport([(200, _ok_body())])
        provider = LMStudioProvider(model="qwen3-8b", transport=transport)
        provider.chat(MESSAGES)
        assert transport.calls[0]["payload"]["model"] == "qwen3-8b"

    def test_retry_behavior_inherited(self):
        script = [(503, {"error": "busy"}), (200, _ok_body("recovered"))]
        transport = _FakeTransport(script)
        provider = LMStudioProvider(transport=transport, max_retries=2)
        assert provider.chat(MESSAGES) == "recovered"
        assert len(transport.calls) == 2


# ----------------------------------------------------------------------
# Cross-slice: constructor kwarg + inherited transport paths
# ----------------------------------------------------------------------

class TestSubclassConstructorExtras:
    @pytest.mark.parametrize("cls,default_env", [
        (OpenRouterProvider, "OPENROUTER_API_KEY"),
        (DeepSeekProvider, "DEEPSEEK_API_KEY"),
        (LlamaCppProvider, None),
        (VLLMProvider, None),
        (LMStudioProvider, None),
    ])
    def test_api_key_env_kwarg_override(self, cls, default_env):
        assert cls().api_key_env == default_env
        provider = cls(api_key_env="CUSTOM_ENV", transport=_FakeTransport([]))
        assert provider.api_key_env == "CUSTOM_ENV"

    def test_for_endpoint_inherited(self):
        provider = OpenRouterProvider.for_endpoint(
            "https://example.test/v1", api_key="k", model="m")
        assert isinstance(provider, OpenRouterProvider)
        assert provider.base_url == "https://example.test/v1"
        assert provider.model == "m"


class _FakeHTTPX2Response:
    def __init__(self, status_code, body=None, json_error=False):
        self.status_code = status_code
        self._body = body
        self._json_error = json_error

    def json(self):
        if self._json_error:
            raise ValueError("bad json")
        return self._body


class _FakeHTTPX2Client:
    """Fake httpx2.Client: records construction, scripted behavior."""

    def __init__(self, timeout=None, behavior=None):
        self.timeout = timeout
        self.behavior = behavior or {}
        self.posts = []
        self.gets = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def post(self, url, headers=None, json=None):
        self.posts.append({"url": url, "headers": headers, "json": json})
        return self._respond("post")

    def get(self, url, headers=None):
        self.gets.append({"url": url, "headers": headers})
        return self._respond("get")

    def _respond(self, method):
        behavior = self.behavior.get(method, "ok")
        if isinstance(behavior, BaseException):
            raise behavior
        return behavior


def _patch_httpx2_client(monkeypatch, module, behavior):
    """Patch module.httpx2.Client with the fake; keep real HTTPError."""
    seen = {}

    def factory(timeout=None):
        client = _FakeHTTPX2Client(timeout=timeout, behavior=behavior)
        seen["client"] = client
        return client

    monkeypatch.setattr(module.httpx2, "Client", factory)
    return seen


class TestRealPostInherited:
    """Inherited _real_post live path (patched httpx2.Client, no sockets)."""

    def test_real_post_success(self, monkeypatch):
        from mythic_agent.providers import openai_compat
        body = _ok_body("via httpx2")
        seen = _patch_httpx2_client(
            monkeypatch, openai_compat,
            {"post": _FakeHTTPX2Response(200, body)})
        provider = OpenAICompatProvider(api_key=FAKE_KEY, model="gpt-x")
        status, returned = provider._real_post(
            "/chat/completions", {"model": "gpt-x"}, provider._headers())
        assert status == 200
        assert returned == body
        client = seen["client"]
        assert client.timeout == 60.0
        assert client.posts[0]["url"] == \
            "https://api.openai.com/v1/chat/completions"

    def test_real_post_http_error_is_provider_error(self, monkeypatch):
        from mythic_agent.providers import openai_compat
        err = openai_compat.httpx2.HTTPError("connection dropped")
        _patch_httpx2_client(monkeypatch, openai_compat, {"post": err})
        provider = OpenAICompatProvider(api_key=FAKE_KEY)
        with pytest.raises(ProviderError, match="request failed"):
            provider._real_post("/chat/completions", {}, {})

    def test_real_post_malformed_json(self, monkeypatch):
        from mythic_agent.providers import openai_compat
        _patch_httpx2_client(
            monkeypatch, openai_compat,
            {"post": _FakeHTTPX2Response(200, json_error=True)})
        provider = OpenAICompatProvider(api_key=FAKE_KEY)
        with pytest.raises(ProviderError, match="malformed JSON"):
            provider._real_post("/chat/completions", {}, {})


class TestLlamaCppHttpGetLive:
    """_http_get live path with patched httpx2.Client (no sockets)."""

    def test_get_success_shapes_url(self, monkeypatch):
        from mythic_agent.providers import llamacpp
        seen = _patch_httpx2_client(
            monkeypatch, llamacpp,
            {"get": _FakeHTTPX2Response(200, {"status": "ok"})})
        provider = LlamaCppProvider()
        status, body = provider._http_get("/health")
        assert (status, body) == (200, {"status": "ok"})
        client = seen["client"]
        assert client.timeout == 60.0
        # /health lives at the host root, outside the /v1 chat prefix.
        assert client.gets[0]["url"] == "http://localhost:8080/health"

    def test_get_http_error_is_provider_error(self, monkeypatch):
        from mythic_agent.providers import llamacpp
        err = llamacpp.httpx2.HTTPError("down")
        _patch_httpx2_client(monkeypatch, llamacpp, {"get": err})
        provider = LlamaCppProvider()
        with pytest.raises(ProviderError, match="health check failed"):
            provider._http_get("/health")

    def test_get_malformed_json_returns_none_body(self, monkeypatch):
        from mythic_agent.providers import llamacpp
        _patch_httpx2_client(
            monkeypatch, llamacpp,
            {"get": _FakeHTTPX2Response(200, json_error=True)})
        provider = LlamaCppProvider()
        assert provider._http_get("/health") == (200, None)


class TestOllamaSeamLivePaths:
    """_get/_read_json live paths with patched urlopen (no sockets)."""

    def test_get_live_path_lists_models(self):
        provider = OllamaProvider(model="llama3.1")
        payload = b'{"models": [{"name": "phi4"}, {"name": "qwen3"}]}'
        with patch.object(urllib.request, "urlopen",
                          return_value=_FakeReply(payload)):
            assert provider.list_models() == ["phi4", "qwen3"]

    def test_non_object_json_body_is_provider_error(self):
        provider = OllamaProvider(model="llama3.1")
        with patch.object(urllib.request, "urlopen",
                          return_value=_FakeReply(b"[1, 2, 3]")):
            with pytest.raises(ProviderError, match="non-object JSON"):
                provider.chat(MESSAGES)

    def test_request_build_failure_maps_to_malformed(self, monkeypatch):
        provider = OllamaProvider(model="llama3.1")

        def boom(*args, **kwargs):
            raise ValueError("synthetic build failure")

        monkeypatch.setattr(urllib.request, "Request", boom)
        with pytest.raises(ProviderError, match="malformed"):
            provider.chat(MESSAGES)
        with pytest.raises(ProviderError, match="malformed"):
            provider._get("/api/tags")

    def test_invalid_ipv6_host_is_malformed_not_valueerror(self):
        # urlparse itself raises ValueError("Invalid IPv6 URL") here;
        # the adapter must still surface ProviderError.
        provider = OllamaProvider(model="llama3.1", host="http://[::1")
        with pytest.raises(ProviderError) as excinfo:
            provider.chat(MESSAGES)
        assert not isinstance(excinfo.value, ValueError)
        assert "malformed" in str(excinfo.value).lower()


class TestDeepSeekEdgeBranches:
    def test_body_without_choices_key(self):
        transport = _FakeTransport([(200, {"error": "weird"})])
        provider = DeepSeekProvider(api_key=FAKE_KEY, transport=transport)
        with pytest.raises(ProviderError, match="no choices"):
            provider.chat(MESSAGES)

    def test_non_dict_message(self):
        body = {"choices": ["not-a-dict"]}
        transport = _FakeTransport([(200, body)])
        provider = DeepSeekProvider(api_key=FAKE_KEY, transport=transport)
        with pytest.raises(ProviderError, match="empty assistant text"):
            provider.chat(MESSAGES)

    def test_null_content_and_null_reasoning(self):
        body = {"choices": [{"message": {"role": "assistant",
                                        "content": None,
                                        "reasoning_content": None}}]}
        transport = _FakeTransport([(200, body)])
        provider = DeepSeekProvider(api_key=FAKE_KEY, transport=transport)
        with pytest.raises(ProviderError, match="empty assistant text"):
            provider.chat(MESSAGES)
