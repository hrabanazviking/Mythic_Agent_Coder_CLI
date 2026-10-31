"""M-024 — Local runtimes II: LM Studio, llama.cpp, any local port.

TIER: unit

(The loopback class below runs a real local HTTP server, but it is
still unit-tier: loopback only, no external network, no live server.)

Covers the M-024 discovery kindness — the same kindness M-023 gave
Ollama — on the three local OpenAI-compatible doors:

* the shared :class:`LocalCompatProvider` surface (served models via
  ``GET /models``, presence, honest not-present answers carrying
  their remedy, unreachable answers carrying the start remedy,
  non-200 answers surfaced as the server's own answer) exercised
  through :class:`GenericLocalCompatProvider` — the "any local
  OpenAI-compatible port" door,
* LM Studio's native surface (downloaded / loaded via
  ``GET /api/v0/models``, per-model detail via
  ``GET /api/v0/models/<id>``, the honest fallback when a build has
  no native API),
* llama.cpp's native surface (served model via ``GET /v1/models``
  with basename matching, ``GET /props``, a discover() that refuses
  to dress an unhealthy server up as a snapshot),
* a REAL loopback proof: one ThreadingHTTPServer on 127.0.0.1
  speaking all three doors' shapes, exercised unpatched,
* the TUI ``/local`` command driven through the CommandHandler with
  fake providers patched into the shared registry.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from mythic_agent.providers.base import ProviderError
from mythic_agent.providers.llamacpp import LlamaCppProvider
from mythic_agent.providers.lmstudio import LMStudioProvider
from mythic_agent.providers.openai_compat import (
    GenericLocalCompatProvider,
    LocalCompatProvider,
)

MODELS_BODY = {"data": [{"id": "qwen3-8b"}, {"id": "llama-3.1-8b"}]}


def _generic(get=None):
    provider = GenericLocalCompatProvider()
    if get is not None:
        provider._get_json = get
    return provider


# ----------------------------------------------------------------------
# Shared surface via the generic door (any local port)
# ----------------------------------------------------------------------

class TestGenericDiscovery:
    def test_is_local_compat(self):
        assert isinstance(_generic(), LocalCompatProvider)

    def test_served_models_uses_get_models(self):
        seen = {}

        def fake_get(path):
            seen["path"] = path
            return 200, MODELS_BODY

        assert _generic(get=fake_get).served_models() == [
            "qwen3-8b", "llama-3.1-8b"]
        assert seen["path"] == "/models"

    def test_served_models_empty_is_honest(self):
        provider = _generic(get=lambda path: (200, {"data": []}))
        assert provider.served_models() == []

    def test_served_models_skips_malformed_entries(self):
        body = {"data": [{"id": "phi4"}, {"name": "x"}, "junk", {}]}
        provider = _generic(get=lambda path: (200, body))
        assert provider.served_models() == ["phi4"]

    def test_served_models_non_200_is_servers_own_answer(self):
        provider = _generic(get=lambda path: (503, None))
        with pytest.raises(ProviderError) as excinfo:
            provider.served_models()
        assert "HTTP 503" in str(excinfo.value)
        assert "unreachable" not in str(excinfo.value)

    def test_list_models_empty_is_error_with_remedy(self):
        provider = _generic(get=lambda path: (200, {"data": []}))
        with pytest.raises(ProviderError) as excinfo:
            provider.list_models()
        assert "reported no models" in str(excinfo.value)

    def test_list_models_returns_served(self):
        provider = _generic(get=lambda path: (200, MODELS_BODY))
        assert provider.list_models() == ["qwen3-8b", "llama-3.1-8b"]

    def test_model_present(self):
        provider = _generic(get=lambda path: (200, MODELS_BODY))
        assert provider.model_present("qwen3-8b") is True
        assert provider.model_present("ghost") is False

    def test_model_present_empty_name_rejected(self):
        provider = _generic(get=lambda path: (200, MODELS_BODY))
        with pytest.raises(ProviderError, match="No model name"):
            provider.model_present("  ")

    def test_ensure_returns_name_when_served(self):
        provider = _generic(get=lambda path: (200, MODELS_BODY))
        assert provider.ensure_model("qwen3-8b") == "qwen3-8b"

    def test_ensure_absent_is_honest_with_remedy(self):
        provider = _generic(get=lambda path: (200, MODELS_BODY))
        with pytest.raises(ProviderError) as excinfo:
            provider.ensure_model("ghost")
        text = str(excinfo.value)
        assert "not present" in text
        assert "Serve 'ghost'" in text

    def test_ensure_empty_name_rejected(self):
        provider = _generic(get=lambda path: (200, MODELS_BODY))
        with pytest.raises(ProviderError, match="No model configured"):
            provider.ensure_model("")

    def test_discover_snapshot(self):
        provider = _generic(get=lambda path: (200, MODELS_BODY))
        snap = provider.discover()
        assert snap["host"] == "http://localhost:1234/v1"
        assert snap["served"] == ["qwen3-8b", "llama-3.1-8b"]

    def test_unreachable_carries_start_remedy(self):
        def boom(path):
            raise ProviderError(
                "local-openai is unreachable at "
                "http://localhost:1234/v1: ConnectError. "
                + _generic()._start_remedy())

        provider = _generic(get=boom)
        with pytest.raises(ProviderError) as excinfo:
            provider.discover()
        assert "Start the local server" in str(excinfo.value)


# ----------------------------------------------------------------------
# LM Studio native surface
# ----------------------------------------------------------------------

NATIVE = {"data": [
    {"id": "qwen3-8b", "type": "llm", "state": "loaded"},
    {"id": "llama-3.1-8b", "type": "llm", "state": "not-loaded"},
    {"id": "text-embedding-nomic", "type": "embeddings",
     "state": "not-loaded"},
]}


def _lmstudio(get=None, root_get=None):
    provider = LMStudioProvider()
    if get is not None:
        provider._get_json = get
    if root_get is not None:
        provider._root_get = root_get
    return provider


def _native_root(body=NATIVE, status=200):
    def fake_root(path):
        assert path == "/api/v0/models"
        return status, body
    return fake_root


class TestLMStudioDiscovery:
    def test_downloaded_from_native(self):
        provider = _lmstudio(root_get=_native_root())
        assert provider.downloaded_models() == [
            "qwen3-8b", "llama-3.1-8b", "text-embedding-nomic"]

    def test_loaded_from_native_state(self):
        provider = _lmstudio(root_get=_native_root())
        assert provider.loaded_models() == ["qwen3-8b"]

    def test_native_absent_falls_back_to_served(self):
        provider = _lmstudio(
            get=lambda path: (200, MODELS_BODY),
            root_get=_native_root(status=404, body=None))
        assert provider.downloaded_models() == ["qwen3-8b",
                                                "llama-3.1-8b"]
        assert provider.loaded_models() == ["qwen3-8b", "llama-3.1-8b"]

    def test_native_error_status_surfaced(self):
        provider = _lmstudio(root_get=_native_root(status=500,
                                                   body=None))
        with pytest.raises(ProviderError, match="HTTP 500"):
            provider.downloaded_models()

    def test_present_checks_downloaded_not_just_loaded(self):
        provider = _lmstudio(root_get=_native_root())
        assert provider.model_present("llama-3.1-8b") is True
        assert provider.model_present("ghost") is False

    def test_ensure_absent_remedy_names_download(self):
        provider = _lmstudio(root_get=_native_root())
        with pytest.raises(ProviderError) as excinfo:
            provider.ensure_model("ghost")
        text = str(excinfo.value)
        assert "not present" in text
        assert "Download 'ghost'" in text

    def test_show_model_native_detail(self):
        def fake_root(path):
            assert path == "/api/v0/models/qwen3-8b"
            return 200, {"id": "qwen3-8b", "type": "llm",
                         "state": "loaded"}

        provider = _lmstudio(root_get=fake_root)
        info = provider.show_model("qwen3-8b")
        assert info["state"] == "loaded"

    def test_show_model_404_is_honest_not_present(self):
        provider = _lmstudio(
            root_get=lambda path: (404, {"error": "not found"}))
        with pytest.raises(ProviderError) as excinfo:
            provider.show_model("ghost")
        text = str(excinfo.value)
        assert "not present" in text
        assert "Download 'ghost'" in text

    def test_show_model_empty_name_rejected(self):
        provider = _lmstudio(root_get=lambda path: (200, {}))
        with pytest.raises(ProviderError, match="No model name"):
            provider.show_model("")

    def test_discover_snapshot(self):
        provider = _lmstudio(
            get=lambda path: (200, MODELS_BODY),
            root_get=_native_root())
        snap = provider.discover()
        assert snap["host"] == "http://localhost:1234/v1"
        assert snap["served"] == ["qwen3-8b", "llama-3.1-8b"]
        assert snap["downloaded"] == [
            "qwen3-8b", "llama-3.1-8b", "text-embedding-nomic"]
        assert snap["loaded"] == ["qwen3-8b"]


# ----------------------------------------------------------------------
# llama.cpp native surface
# ----------------------------------------------------------------------

LLAMA_MODELS = {"data": [{"id": "/models/qwen3-8b.gguf"}]}
LLAMA_PROPS = {"model_path": "/models/qwen3-8b.gguf",
               "total_slots": 4, "build_info": "b1"}


def _llamacpp(http_get=None):
    provider = LlamaCppProvider()
    if http_get is not None:
        provider._http_get = http_get
    return provider


def _llama_router(models=LLAMA_MODELS, props=LLAMA_PROPS, health=200):
    def fake_get(path):
        if path == "/v1/models":
            return 200, models
        if path == "/props":
            return 200, props
        if path == "/health":
            return health, {"status": "ok" if health == 200 else "x"}
        raise AssertionError(path)
    return fake_get


class TestLlamaCppDiscovery:
    def test_served_models_via_v1_models(self):
        provider = _llamacpp(http_get=_llama_router())
        assert provider.served_models() == ["/models/qwen3-8b.gguf"]

    def test_served_non_200_surfaced(self):
        provider = _llamacpp(
            http_get=lambda path: (503, {"status": "loading"}))
        with pytest.raises(ProviderError, match="HTTP 503"):
            provider.served_models()

    def test_present_exact_and_basename(self):
        provider = _llamacpp(http_get=_llama_router())
        assert provider.model_present("/models/qwen3-8b.gguf") is True
        assert provider.model_present("qwen3-8b.gguf") is True
        assert provider.model_present("other.gguf") is False

    def test_ensure_absent_remedy_names_relaunch(self):
        provider = _llamacpp(http_get=_llama_router())
        with pytest.raises(ProviderError) as excinfo:
            provider.ensure_model("other.gguf")
        text = str(excinfo.value)
        assert "not present" in text
        assert "llama-server -m other.gguf" in text

    def test_props(self):
        provider = _llamacpp(http_get=_llama_router())
        assert provider.props()["model_path"] == "/models/qwen3-8b.gguf"

    def test_props_non_200_surfaced(self):
        provider = _llamacpp(http_get=lambda path: (404, None))
        with pytest.raises(ProviderError, match="HTTP 404"):
            provider.props()

    def test_discover_healthy(self):
        provider = _llamacpp(http_get=_llama_router())
        snap = provider.discover()
        assert snap["host"] == "http://localhost:8080/v1"
        assert snap["served"] == ["/models/qwen3-8b.gguf"]
        assert snap["healthy"] is True
        assert snap["model_path"] == "/models/qwen3-8b.gguf"

    def test_discover_unhealthy_is_honest_error(self):
        provider = _llamacpp(http_get=_llama_router(health=503))
        with pytest.raises(ProviderError) as excinfo:
            provider.discover()
        text = str(excinfo.value)
        assert "unreachable" in text
        assert "llama-server -m" in text

    def test_discover_props_failure_degrades_to_unknown_path(self):
        def router(path):
            if path == "/props":
                return 500, None
            return _llama_router()(path)

        provider = _llamacpp(http_get=router)
        snap = provider.discover()
        assert snap["model_path"] is None
        assert snap["served"] == ["/models/qwen3-8b.gguf"]


# ----------------------------------------------------------------------
# Real loopback proof (no stubbed seams, no patched transport)
# ----------------------------------------------------------------------

class _LocalHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # keep the test log clean
        pass

    def _send(self, code, obj):
        raw = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == "/v1/models":
            self._send(200, {"data": [{"id": "qwen3-8b"},
                                      {"id": "/models/qwen3-8b.gguf"}]})
        elif self.path == "/api/v0/models":
            self._send(200, NATIVE)
        elif self.path.startswith("/api/v0/models/"):
            wanted = self.path.rsplit("/", 1)[-1]
            for entry in NATIVE["data"]:
                if entry["id"] == wanted:
                    self._send(200, entry)
                    return
            self._send(404, {"error": "model not found"})
        elif self.path == "/health":
            self._send(200, {"status": "ok"})
        elif self.path == "/props":
            self._send(200, LLAMA_PROPS)
        else:
            self._send(404, {"error": "unknown path"})


@pytest.fixture()
def loopback():
    server = ThreadingHTTPServer(("127.0.0.1", 0), _LocalHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}/v1"
    yield base
    server.shutdown()
    thread.join(timeout=5)


class TestLoopback:
    def test_generic_discovery_over_real_http(self, loopback):
        provider = GenericLocalCompatProvider(base_url=loopback)
        assert provider.served_models() == [
            "qwen3-8b", "/models/qwen3-8b.gguf"]
        assert provider.ensure_model("qwen3-8b") == "qwen3-8b"
        assert provider.discover()["served"][0] == "qwen3-8b"

    def test_lmstudio_discovery_over_real_http(self, loopback):
        provider = LMStudioProvider(base_url=loopback)
        assert provider.downloaded_models() == [
            "qwen3-8b", "llama-3.1-8b", "text-embedding-nomic"]
        assert provider.loaded_models() == ["qwen3-8b"]
        assert provider.show_model("llama-3.1-8b")["state"] == \
            "not-loaded"
        with pytest.raises(ProviderError, match="not present"):
            provider.show_model("ghost")

    def test_llamacpp_discovery_over_real_http(self, loopback):
        provider = LlamaCppProvider(base_url=loopback)
        assert provider.health() is True
        snap = provider.discover()
        assert snap["model_path"] == "/models/qwen3-8b.gguf"
        assert provider.model_present("qwen3-8b.gguf") is True


# ----------------------------------------------------------------------
# TUI /local command
# ----------------------------------------------------------------------

class _FakeLocalProvider:
    """Stands in for a local provider in the handler (no sockets)."""

    last = None

    def __init__(self):
        self.base_url = "http://localhost:9999/v1"
        _FakeLocalProvider.last = self

    def discover(self):
        return {"host": self.base_url, "served": ["qwen3-8b"],
                "downloaded": ["qwen3-8b", "llama-3.1-8b"],
                "loaded": ["qwen3-8b"]}

    def ensure_model(self, name):
        if name == "ghost":
            raise ProviderError(
                f"Model 'ghost' is not present on this fake at "
                f"{self.base_url}. Download 'ghost' first.")
        return name

    def show_model(self, name):
        return {"id": name, "type": "llm", "state": "loaded"}


class _DownProvider(_FakeLocalProvider):
    def discover(self):
        raise ProviderError(
            "llama.cpp is unreachable at http://localhost:8080/v1. "
            "Start the server with `llama-server -m <model.gguf>`.")


@pytest.fixture()
def handler(monkeypatch):
    from mythic_agent.agents import command_handler as handler_module
    from mythic_agent.agents.command_handler import CommandHandler
    from mythic_agent.providers import registry as registry_module

    monkeypatch.setitem(registry_module._REGISTRY, "lmstudio",
                        _FakeLocalProvider)
    monkeypatch.setitem(registry_module._REGISTRY, "llama.cpp",
                        _DownProvider)
    monkeypatch.setitem(registry_module._REGISTRY, "local-openai",
                        _FakeLocalProvider)
    published = []
    monkeypatch.setattr(
        handler_module, "publish_sync",
        lambda event, **kwargs: published.append((event, kwargs)))
    instance = CommandHandler.__new__(CommandHandler)
    instance.published = published
    return instance


def _published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestLocalCommandHandler:
    def test_list_all_shows_up_and_down_doors_honestly(self, handler):
        handler._handle_local("")
        text = _published_text(handler)
        assert "qwen3-8b" in text
        assert "llama-server -m" in text

    def test_provider_list_shows_downloaded_and_loaded(self, handler):
        handler._handle_local("lmstudio list")
        text = _published_text(handler)
        assert "Serving: qwen3-8b" in text
        assert "Downloaded:" in text
        assert "Loaded: qwen3-8b" in text

    def test_show_present(self, handler):
        handler._handle_local("lmstudio show qwen3-8b")
        text = _published_text(handler)
        assert "qwen3-8b" in text
        assert "llm" in text

    def test_show_absent_is_honest_with_remedy(self, handler):
        handler._handle_local("lmstudio show ghost")
        text = _published_text(handler)
        assert "not present" in text
        assert "Download 'ghost'" in text

    def test_usage_on_unknown_provider(self, handler):
        handler._handle_local("bogus list")
        assert "Usage: /local" in _published_text(handler)

    def test_usage_on_bad_shape(self, handler):
        handler._handle_local("lmstudio show")
        assert "Usage: /local" in _published_text(handler)


class TestChatScreenRouting:
    def test_local_routes_as_system_command(self, monkeypatch):
        from mythic_agent.ui.screens import chat_screen
        from mythic_agent.ui.screens.chat_screen import MainChatScreen

        calls = []
        monkeypatch.setattr(
            chat_screen.SecureAPI, "publish_system_command",
            staticmethod(lambda cmd, args: calls.append((cmd, args))))
        screen = MainChatScreen.__new__(MainChatScreen)
        log_lines = []

        class _Log:
            def write(self, *args, **kwargs):
                log_lines.append(" ".join(str(a) for a in args))

        screen.handle_command("/local lmstudio list", _Log())
        assert calls == [("/local", "lmstudio list")]
