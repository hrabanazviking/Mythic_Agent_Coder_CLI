"""
TIER: unit
Project-Aesir-as-a-provider gate (All-Features roadmap slice M-025).

Aesir's API as it stands (its own docs/NATIVE_SERVICE.md,
docs/API_SUPPORT_MATRIX_V1.md and scripts/fixtures/api_contract_v1.json)
has two doors: the native authenticated door (127.0.0.1:18434 —
/health/ready, /health/live, /v1/generate, /v1/models,
/v1/chat/completions) and the --ollama door (127.0.0.1:11434).
These tests prove the adapter speaks the native door for chat and
generation, reports capability limits exactly as Aesir reports them
(streaming yes; general tool calling, vision and general JSON mode
no; one resident model; the catalog is not readiness), keeps the
service key out of every error, and reads the Ollama door's snapshot
honestly. Stubbed seams everywhere, plus one real loopback HTTP
server speaking Aesir's shapes.
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from mythic_agent.providers.aesir import AesirProvider
from mythic_agent.providers.base import (
    ProviderError,
    ProviderNotConfigured,
)
from mythic_agent.providers.registry import get_provider, list_providers

FAKE_KEY = "fake-aesir-key-0123456789abcdef"

READY = {"schema_version": 1, "status": "ready", "ready": True,
         "backend": "cuda", "profile": "gemma4", "context": 512,
         "model": "gemma4-e2b:latest", "digest": "sha256:abc123"}
CATALOG = {"object": "list",
           "data": [{"id": "gemma4-e2b:latest", "object": "model"},
                    {"id": "llama3-8b:latest", "object": "model"}]}


def _chat_transport(text="hello from aesir"):
    def transport(path, payload, headers):
        return 200, {"choices": [{"message": {"role": "assistant",
                                              "content": text}}]}
    return transport


def _provider(**kwargs):
    kwargs.setdefault("api_key", FAKE_KEY)
    kwargs.setdefault("transport", _chat_transport())
    return AesirProvider(**kwargs)


def _stub_get(provider, routes):
    """routes: url-suffix -> (status, body). Records requested urls."""
    seen = []

    def fake_get(url):
        seen.append(url)
        for suffix, answer in routes.items():
            if url.endswith(suffix):
                return answer
        return 404, {"error": {"code": 404, "message": "Not Found"}}

    provider._get_at = fake_get
    return seen


# ----------------------------------------------------------------------
# Identity, registry, capabilities — as Aesir reports them
# ----------------------------------------------------------------------

def test_identity_and_defaults():
    provider = _provider()
    assert provider.name == "aesir"
    assert provider.default_model == "aesir-local"
    assert provider.api_key_env == "AESIR_API_KEY"
    assert provider.base_url == "http://127.0.0.1:18434/v1"
    assert provider.ollama_base_url == "http://127.0.0.1:11434"


def test_registered_in_the_runtime_registry():
    assert "aesir" in list_providers()
    assert isinstance(get_provider("aesir", api_key=FAKE_KEY), AesirProvider)
    assert isinstance(get_provider("AESIR", api_key=FAKE_KEY), AesirProvider)


def test_capabilities_are_aesirs_own_report():
    caps = _provider().capabilities()
    assert caps == {"streaming": True, "tool_calling": False,
                    "vision": False, "json_mode": False}


# ----------------------------------------------------------------------
# Chat through the native door's OpenAI-subset route
# ----------------------------------------------------------------------

def test_chat_speaks_the_chat_completions_route():
    seen = {}

    def transport(path, payload, headers):
        seen.update(path=path, payload=payload, headers=headers)
        return 200, {"choices": [{"message": {"content": "Four"}}]}

    provider = _provider(transport=transport, model="gemma4-e2b:latest")
    text = provider.chat([{"role": "user", "content": "2+2?"}],
                         temperature=0, max_tokens=16)
    assert text == "Four"
    assert seen["path"] == "/chat/completions"
    assert seen["payload"]["model"] == "gemma4-e2b:latest"
    assert seen["payload"]["temperature"] == 0
    assert seen["headers"]["Authorization"] == f"Bearer {FAKE_KEY}"


def test_chat_refuses_general_tool_calling():
    provider = _provider()
    with pytest.raises(ProviderError, match="tool calling"):
        provider.chat([{"role": "user", "content": "hi"}],
                      tools=[{"type": "function",
                              "function": {"name": "x"}}])


def test_chat_refuses_tool_role_messages():
    provider = _provider()
    with pytest.raises(ProviderError, match="tool-role"):
        provider.chat([{"role": "tool", "content": "result"}])


def test_chat_refuses_multimodal_content():
    provider = _provider()
    with pytest.raises(ProviderError, match="string message content"):
        provider.chat([{"role": "user",
                        "content": [{"type": "image_url"}]}])


def test_chat_refuses_non_boolean_response_format():
    provider = _provider()
    with pytest.raises(ProviderError, match="Boolean"):
        provider.chat([{"role": "user", "content": "hi"}],
                      response_format={"type": "json_object"})


def test_chat_passes_the_strict_boolean_subset_through():
    seen = {}

    def transport(path, payload, headers):
        seen.update(payload)
        return 200, {"choices": [{"message": {"content": "true"}}]}

    provider = _provider(transport=transport)
    fmt = {"type": "json_schema",
           "json_schema": {"name": "answer", "strict": True,
                           "schema": {"type": "boolean"}}}
    assert provider.chat([{"role": "user", "content": "ok?"}],
                         response_format=fmt) == "true"
    assert seen["response_format"] == fmt


def test_chat_auth_failure_never_leaks_the_key():
    def transport(path, payload, headers):
        return 401, {"error": {"code": 401, "message": "unauthorized"}}

    provider = _provider(transport=transport)
    with pytest.raises(ProviderError) as excinfo:
        provider.chat([{"role": "user", "content": "hi"}])
    assert FAKE_KEY not in str(excinfo.value)
    assert "401" in str(excinfo.value)


def test_chat_empty_model_raises_provider_error():
    provider = _provider()
    provider.model = ""
    with pytest.raises(ProviderError):
        provider.chat([{"role": "user", "content": "hi"}], model="")


# ----------------------------------------------------------------------
# Key custody: env, explicit, and Aesir's own key file
# ----------------------------------------------------------------------

def test_key_file_is_loaded_and_never_echoed(tmp_path):
    key_file = tmp_path / "service.key"
    key_file.write_text(FAKE_KEY + "\n", encoding="utf-8")
    provider = AesirProvider(api_key_file=str(key_file),
                             transport=_chat_transport())
    assert provider.api_key == FAKE_KEY


def test_missing_key_file_is_not_configured_with_remedy(tmp_path):
    with pytest.raises(ProviderNotConfigured, match="keygen"):
        AesirProvider(api_key_file=str(tmp_path / "nope.key"),
                      transport=_chat_transport())


def test_empty_key_file_is_not_configured(tmp_path):
    key_file = tmp_path / "service.key"
    key_file.write_text("\n", encoding="utf-8")
    with pytest.raises(ProviderNotConfigured):
        AesirProvider(api_key_file=str(key_file),
                      transport=_chat_transport())


# ----------------------------------------------------------------------
# Health, catalog, residency — catalog is not readiness
# ----------------------------------------------------------------------

def test_health_true_only_on_a_ready_200():
    provider = _provider()
    _stub_get(provider, {"/health/ready": (200, READY)})
    assert provider.health() is True
    _stub_get(provider, {"/health/ready": (503, {"ready": False})})
    assert provider.health() is False


def test_health_false_when_unreachable():
    provider = _provider()

    def boom(url):
        raise ProviderError("aesir is unreachable")

    provider._get_at = boom
    assert provider.health() is False
    assert provider.resident_model() is None


def test_catalog_models_reads_v1_models():
    provider = _provider()
    _stub_get(provider, {"/v1/models": (200, CATALOG)})
    assert provider.catalog_models() == ["gemma4-e2b:latest",
                                          "llama3-8b:latest"]
    assert provider.list_models() == provider.catalog_models()
    assert provider.model_present("llama3-8b:latest") is True
    assert provider.model_present("nope") is False


def test_resident_model_comes_from_the_readiness_record():
    provider = _provider()
    _stub_get(provider, {"/health/ready": (200, READY)})
    assert provider.resident_model() == "gemma4-e2b:latest"


def test_ensure_model_resident_passes():
    provider = _provider()
    _stub_get(provider, {"/health/ready": (200, READY),
                         "/v1/models": (200, CATALOG)})
    assert provider.ensure_model("gemma4-e2b:latest") == "gemma4-e2b:latest"


def test_ensure_model_catalog_but_not_resident_refuses_with_remedy():
    provider = _provider()
    _stub_get(provider, {"/health/ready": (200, READY),
                         "/v1/models": (200, CATALOG)})
    with pytest.raises(ProviderError, match="not the resident model"):
        provider.ensure_model("llama3-8b:latest")


def test_ensure_model_absent_refuses_with_import_remedy():
    provider = _provider()
    _stub_get(provider, {"/health/ready": (200, READY),
                         "/v1/models": (200, CATALOG)})
    with pytest.raises(ProviderError, match="aesir create"):
        provider.ensure_model("never-imported")


def test_discover_snapshot_names_resident_and_catalog():
    provider = _provider()
    _stub_get(provider, {"/health/ready": (200, READY),
                         "/v1/models": (200, CATALOG)})
    snap = provider.discover()
    assert snap["mode"] == "native"
    assert snap["ready"] is True
    assert snap["backend"] == "cuda"
    assert snap["context"] == 512
    assert snap["resident"] == "gemma4-e2b:latest"
    assert snap["catalog"] == ["gemma4-e2b:latest", "llama3-8b:latest"]


def test_discover_not_ready_raises_instead_of_dressing_up():
    provider = _provider()
    _stub_get(provider, {"/health/ready": (503, {"ready": False})})
    with pytest.raises(ProviderError, match="not ready"):
        provider.discover()


# ----------------------------------------------------------------------
# Native generation — Aesir's own flat shape
# ----------------------------------------------------------------------

def test_native_generate_speaks_v1_generate_and_returns_the_record():
    seen = {}

    def transport(path, payload, headers):
        seen.update(path=path, payload=payload)
        return 200, {"text": "Four", "finish_reason": "eos",
                     "prompt_tokens": 9, "generated_tokens": 1,
                     "backend": "cuda", "cpu_offload": 0,
                     "model": "gemma4-e2b:latest"}

    provider = _provider(transport=transport)
    record = provider.native_generate("What is two plus two?",
                                      max_tokens=16, temperature=0)
    assert seen["path"] == "/generate"
    assert seen["payload"]["prompt"] == "What is two plus two?"
    assert record["text"] == "Four"
    assert record["backend"] == "cuda"


def test_native_generate_refuses_unknown_fields_by_name():
    provider = _provider()
    with pytest.raises(ProviderError, match="tools"):
        provider.native_generate("hi", tools=[])


def test_native_generate_refuses_an_empty_prompt():
    provider = _provider()
    with pytest.raises(ProviderError, match="prompt"):
        provider.native_generate("   ")


# ----------------------------------------------------------------------
# Reported capabilities — live fields from the server itself
# ----------------------------------------------------------------------

def test_reported_capabilities_unreachable_stays_honest():
    provider = _provider()

    def boom(url):
        raise ProviderError("aesir is unreachable")

    provider._get_at = boom
    report = provider.reported_capabilities()
    assert report["reachable"] is False
    assert report["backend"] is None
    assert report["tool_calling"] is False
    assert report["embeddings"] is False
    assert report["resident_models"] == 1
    assert report["catalog_is_readiness"] is False


def test_reported_capabilities_live_fields_come_from_ready():
    provider = _provider()
    _stub_get(provider, {"/health/ready": (200, READY)})
    report = provider.reported_capabilities()
    assert report["reachable"] is True
    assert report["backend"] == "cuda"
    assert report["profile"] == "gemma4"
    assert report["context"] == 512
    assert report["model"] == "gemma4-e2b:latest"
    assert report["model_digest"] == "sha256:abc123"


# ----------------------------------------------------------------------
# The Ollama-compatible door's snapshot
# ----------------------------------------------------------------------

def test_ollama_snapshot_reads_version_catalog_and_resident():
    provider = _provider()
    _stub_get(provider, {
        "/api/version": (200, {"version": "0.1.0-aesir"}),
        "/api/tags": (200, {"models": [{"name": "gemma4-e2b:latest"},
                                       {"name": "llama3-8b:latest"}]}),
        "/api/ps": (200, {"models": [{"name": "gemma4-e2b:latest"}]}),
    })
    snap = provider.ollama_snapshot()
    assert snap["mode"] == "ollama"
    assert snap["version"] == "0.1.0-aesir"
    assert snap["catalog"] == ["gemma4-e2b:latest", "llama3-8b:latest"]
    assert snap["resident"] == ["gemma4-e2b:latest"]


def test_ollama_snapshot_down_door_raises_with_its_remedy():
    provider = _provider()
    _stub_get(provider, {"/api/version": (404, {"error": "Not Found"})})
    with pytest.raises(ProviderError, match="--ollama"):
        provider.ollama_snapshot()


# ----------------------------------------------------------------------
# A real loopback server speaking Aesir's shapes
# ----------------------------------------------------------------------

class _AesirHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # silence test server logging
        pass

    def _send(self, obj, status=200):
        raw = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == "/health/ready":
            self._send(READY)
        elif self.path == "/health/live":
            self._send({"schema_version": 1, "status": "ok",
                        "scope": "process"})
        elif self.path == "/v1/models":
            self._send(CATALOG)
        elif self.path == "/api/version":
            self._send({"version": "0.1.0-aesir"})
        elif self.path == "/api/tags":
            self._send({"models": [{"name": "gemma4-e2b:latest"}]})
        elif self.path == "/api/ps":
            self._send({"models": [{"name": "gemma4-e2b:latest"}]})
        else:
            self._send({"error": "Not Found"}, status=404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(length) or b"{}")
        if self.path == "/v1/chat/completions":
            assert self.headers.get("Authorization") == f"Bearer {FAKE_KEY}"
            self._send({"choices": [{"message": {
                "role": "assistant", "content": "live hello"}}]})
        elif self.path == "/v1/generate":
            self._send({"text": "live four", "finish_reason": "eos",
                        "prompt_tokens": 5, "generated_tokens": 2,
                        "backend": "cuda", "cpu_offload": 0,
                        "model": body.get("model") or "gemma4-e2b:latest"})
        else:
            self._send({"error": "Not Found"}, status=404)


def test_real_loopback_aesir_server_end_to_end():
    server = ThreadingHTTPServer(("127.0.0.1", 0), _AesirHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        port = server.server_address[1]
        base = f"http://127.0.0.1:{port}"
        provider = AesirProvider(api_key=FAKE_KEY, base_url=base + "/v1",
                                 ollama_base_url=base,
                                 model="gemma4-e2b:latest")
        assert provider.chat([{"role": "user", "content": "hi"}]) == "live hello"
        assert provider.native_generate("2+2?")["text"] == "live four"
        assert provider.health() is True
        assert provider.live()["status"] == "ok"
        snap = provider.discover()
        assert snap["resident"] == "gemma4-e2b:latest"
        assert snap["catalog"][0] == "gemma4-e2b:latest"
        ollama = provider.ollama_snapshot()
        assert ollama["version"] == "0.1.0-aesir"
        assert ollama["resident"] == ["gemma4-e2b:latest"]
    finally:
        server.shutdown()
        thread.join(timeout=5)
