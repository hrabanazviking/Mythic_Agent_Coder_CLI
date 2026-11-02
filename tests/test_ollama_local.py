"""M-023 — Local runtimes I: Ollama discovery, pull/list, honest absence.

TIER: unit

(The loopback class below runs a real local HTTP server, but it is
still unit-tier: loopback only, no external network, no live Ollama.)

Covers the M-023 surface on OllamaProvider and the TUI ``/ollama``
command:

* ``running_models()`` via ``GET /api/ps`` — including the honest
  empty answer (nothing loaded is a state, not an error),
* ``model_present()`` / ``ensure_model()`` — presence against
  ``/api/tags`` with the ``:latest`` implication, and the honest
  "model not present" error carrying its pull remedy,
* ``show_model()`` via ``POST /api/show`` and ``pull_model()`` via
  ``POST /api/pull`` (stubbed ``_post``/``_get`` seams),
* HTTP-error honesty: a server 404 "model not found" body surfaces
  as a not-present ProviderError, never as "unreachable",
* ``discover()`` — the installed+running snapshot,
* a REAL loopback proof: a ThreadingHTTPServer on 127.0.0.1 speaking
  the Ollama API shapes, exercised through the unpatched transport,
* the TUI ``/ollama`` command (list / pull / show / usage / error
  remedy) driven through ``MainChatScreen.handle_command`` with a
  fake provider and a collecting log.
"""

from __future__ import annotations

import io
import json
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

import pytest

from mythic_agent.providers.base import ProviderError
from mythic_agent.providers.ollama import OllamaProvider

MESSAGES = [{"role": "user", "content": "hello"}]


def _provider(get=None, post=None):
    provider = OllamaProvider(model="llama3.1")
    if get is not None:
        provider._get = get
    if post is not None:
        provider._post = post
    return provider


# ----------------------------------------------------------------------
# Running-model discovery (/api/ps)
# ----------------------------------------------------------------------

class TestRunningModels:
    def test_running_models_uses_get_api_ps(self):
        seen = {}

        def fake_get(path):
            seen["path"] = path
            return {"models": [{"name": "llama3.1"},
                               {"name": "qwen3:8b"}]}

        provider = _provider(get=fake_get)
        assert provider.running_models() == ["llama3.1", "qwen3:8b"]
        assert seen["path"] == "/api/ps"

    def test_running_models_empty_is_honest_not_an_error(self):
        provider = _provider(get=lambda path: {"models": []})
        assert provider.running_models() == []

    def test_running_models_skips_nameless_entries(self):
        provider = _provider(get=lambda path: {"models": [
            {"name": "phi4"}, {"size": 3}, "junk", {}]})
        assert provider.running_models() == ["phi4"]

    def test_running_models_malformed_body_is_empty(self):
        provider = _provider(get=lambda path: {"models": "nope"})
        assert provider.running_models() == []


# ----------------------------------------------------------------------
# Presence: model_present / ensure_model (/api/tags)
# ----------------------------------------------------------------------

TAGS = {"models": [{"name": "llama3.1:latest"}, {"name": "mistral"}]}


class TestPresence:
    def test_present_exact(self):
        provider = _provider(get=lambda path: TAGS)
        assert provider.model_present("mistral") is True

    def test_present_with_implied_latest_tag(self):
        provider = _provider(get=lambda path: TAGS)
        assert provider.model_present("llama3.1") is True

    def test_absent_is_false(self):
        provider = _provider(get=lambda path: TAGS)
        assert provider.model_present("phi4") is False

    def test_absent_on_empty_server_is_false(self):
        provider = _provider(get=lambda path: {"models": []})
        assert provider.model_present("phi4") is False

    def test_empty_name_rejected(self):
        provider = _provider(get=lambda path: TAGS)
        with pytest.raises(ProviderError, match="No model name"):
            provider.model_present("  ")

    def test_ensure_returns_name_when_present(self):
        provider = _provider(get=lambda path: TAGS)
        assert provider.ensure_model("mistral") == "mistral"

    def test_ensure_absent_is_honest_with_remedy(self):
        provider = _provider(get=lambda path: TAGS)
        with pytest.raises(ProviderError) as excinfo:
            provider.ensure_model("phi4")
        text = str(excinfo.value)
        assert "not present" in text
        assert "ollama pull phi4" in text
        assert "/ollama pull phi4" in text

    def test_ensure_empty_name_rejected(self):
        provider = _provider(get=lambda path: TAGS)
        with pytest.raises(ProviderError, match="No model configured"):
            provider.ensure_model("")


# ----------------------------------------------------------------------
# show_model (/api/show) and pull_model (/api/pull)
# ----------------------------------------------------------------------

class TestShowAndPull:
    def test_show_posts_name_to_api_show(self):
        seen = {}

        def fake_post(path, payload):
            seen["path"] = path
            seen["payload"] = payload
            return {"details": {"family": "llama", "parameter_size": "8B"},
                    "modified_at": "2026-01-01T00:00:00Z"}

        provider = _provider(post=fake_post)
        info = provider.show_model("llama3.1")
        assert seen == {"path": "/api/show",
                        "payload": {"name": "llama3.1"}}
        assert info["details"]["family"] == "llama"

    def test_show_empty_name_rejected_before_transport(self):
        def boom(path, payload):
            raise AssertionError("transport must not be called")

        provider = _provider(post=boom)
        with pytest.raises(ProviderError, match="No model name"):
            provider.show_model("")

    def test_pull_posts_name_non_streaming(self):
        seen = {}

        def fake_post(path, payload):
            seen["path"] = path
            seen["payload"] = payload
            return {"status": "success"}

        provider = _provider(post=fake_post)
        assert provider.pull_model("phi4") == {"status": "success"}
        assert seen == {"path": "/api/pull",
                        "payload": {"name": "phi4", "stream": False}}

    def test_pull_empty_name_rejected_before_transport(self):
        def boom(path, payload):
            raise AssertionError("transport must not be called")

        provider = _provider(post=boom)
        with pytest.raises(ProviderError, match="No model name"):
            provider.pull_model("   ")


# ----------------------------------------------------------------------
# discover() snapshot
# ----------------------------------------------------------------------

class TestDiscover:
    def test_discover_reports_installed_and_running(self):
        def fake_get(path):
            if path == "/api/tags":
                return TAGS
            if path == "/api/ps":
                return {"models": [{"name": "mistral"}]}
            raise AssertionError(path)

        provider = _provider(get=fake_get)
        snap = provider.discover()
        assert snap["host"] == "http://localhost:11434"
        assert snap["installed"] == ["llama3.1:latest", "mistral"]
        assert snap["running"] == ["mistral"]

    def test_discover_empty_server(self):
        provider = _provider(get=lambda path: {"models": []})
        snap = provider.discover()
        assert snap["installed"] == []
        assert snap["running"] == []


# ----------------------------------------------------------------------
# HTTP-error honesty in the live transport (_read_json)
# ----------------------------------------------------------------------

def _http_error(code, body: bytes):
    return urllib.error.HTTPError(
        "http://localhost:11434/api/chat", code, "err", hdrs=None,
        fp=io.BytesIO(body))


class TestHttpErrorHonesty:
    def test_404_model_not_found_is_not_present_not_unreachable(self):
        provider = OllamaProvider(model="ghost")
        body = json.dumps({"error": "model 'ghost' not found, "
                                    "try pulling it first"}).encode()
        with patch.object(urllib.request, "urlopen",
                          side_effect=_http_error(404, body)):
            with pytest.raises(ProviderError) as excinfo:
                provider.chat(MESSAGES)
        text = str(excinfo.value)
        assert "not present" in text
        assert "ollama pull" in text
        assert "unreachable" not in text

    def test_500_surfaces_server_detail(self):
        provider = OllamaProvider(model="llama3.1")
        body = json.dumps({"error": "internal boom"}).encode()
        with patch.object(urllib.request, "urlopen",
                          side_effect=_http_error(500, body)):
            with pytest.raises(ProviderError) as excinfo:
                provider.chat(MESSAGES)
        text = str(excinfo.value)
        assert "HTTP 500" in text
        assert "internal boom" in text
        assert "unreachable" not in text


# ----------------------------------------------------------------------
# Real loopback proof (no stubbed seams, no patched transport)
# ----------------------------------------------------------------------

class _OllamaHandler(BaseHTTPRequestHandler):
    installed = [{"name": "llama3.1:latest"}, {"name": "mistral"}]
    running = [{"name": "mistral"}]
    pulled = []

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
        if self.path == "/api/tags":
            self._send(200, {"models": self.installed})
        elif self.path == "/api/ps":
            self._send(200, {"models": self.running})
        else:
            self._send(404, {"error": "unknown path"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        payload = json.loads(self.rfile.read(length) or b"{}")
        if self.path == "/api/pull":
            type(self).pulled.append(payload["name"])
            self._send(200, {"status": "success"})
        elif self.path == "/api/show":
            names = [m["name"] for m in self.installed]
            if any(OllamaProvider._name_matches(n, payload["name"])
                   for n in names):
                self._send(200, {"details": {"family": "llama",
                                             "parameter_size": "8B"},
                                 "modified_at": "2026-01-01T00:00:00Z"})
            else:
                self._send(404, {"error": f"model '{payload['name']}' "
                                          "not found"})
        else:
            self._send(404, {"error": "unknown path"})


@pytest.fixture()
def loopback():
    _OllamaHandler.pulled = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), _OllamaHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host = f"http://127.0.0.1:{server.server_address[1]}"
    yield host
    server.shutdown()
    thread.join(timeout=5)


class TestLoopback:
    def test_discovery_over_real_http(self, loopback):
        provider = OllamaProvider(host=loopback)
        assert provider.list_models() == ["llama3.1:latest", "mistral"]
        assert provider.running_models() == ["mistral"]
        snap = provider.discover()
        assert snap["installed"] == ["llama3.1:latest", "mistral"]
        assert snap["running"] == ["mistral"]

    def test_presence_and_show_over_real_http(self, loopback):
        provider = OllamaProvider(host=loopback)
        assert provider.model_present("llama3.1") is True
        assert provider.model_present("ghost") is False
        info = provider.show_model("mistral")
        assert info["details"]["family"] == "llama"

    def test_show_missing_model_is_honest_over_real_http(self, loopback):
        provider = OllamaProvider(host=loopback)
        with pytest.raises(ProviderError) as excinfo:
            provider.show_model("ghost")
        assert "not present" in str(excinfo.value)

    def test_pull_over_real_http(self, loopback):
        provider = OllamaProvider(host=loopback)
        assert provider.pull_model("phi4") == {"status": "success"}
        assert _OllamaHandler.pulled == ["phi4"]


# ----------------------------------------------------------------------
# TUI /ollama command: chat screen routing + CommandHandler behaviour
# ----------------------------------------------------------------------

class _FakeLog:
    def __init__(self):
        self.lines = []

    def write(self, *args, **kwargs):
        self.lines.append(" ".join(str(a) for a in args))

    @property
    def text(self):
        return "\n".join(self.lines)


class _FakeProvider:
    """Stands in for OllamaProvider in the handler (no sockets)."""

    last = None

    def __init__(self, host=None):
        self.host = host
        _FakeProvider.last = self

    def discover(self):
        return {"host": self.host,
                "installed": ["llama3.1:latest", "mistral"],
                "running": ["mistral"]}

    def pull_model(self, name):
        self.pulled = name
        return {"status": "success"}

    def ensure_model(self, name):
        if name == "ghost":
            raise ProviderError(
                f"Model 'ghost' is not present in Ollama at {self.host}. "
                "Pull it with `ollama pull ghost` or from the TUI with "
                "`/ollama pull ghost`.")
        return name

    def show_model(self, name):
        return {"details": {"family": "llama", "parameter_size": "7B"},
                "modified_at": "2026-01-01T00:00:00Z"}


@pytest.fixture()
def fake_registry(monkeypatch):
    from mythic_agent.providers import registry as registry_module

    # The handler obtains its provider through the shared registry,
    # so the fake is patched into the registry's own table.
    monkeypatch.setitem(registry_module._REGISTRY, "ollama", _FakeProvider)
    return registry_module


class _AllowPolicy:
    def authorize(self, name, arguments):
        return True


class _DenyPolicy:
    def authorize(self, name, arguments):
        return False


@pytest.fixture()
def handler(monkeypatch, fake_registry):
    from mythic_agent.agents import command_handler as handler_module
    from mythic_agent.agents.command_handler import CommandHandler

    published = []
    monkeypatch.setattr(
        handler_module, "publish_sync",
        lambda event, **kwargs: published.append((event, kwargs)))
    instance = CommandHandler.__new__(CommandHandler)
    instance.policy = _AllowPolicy()
    instance.published = published
    return instance


def _published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestChatScreenRouting:
    def test_ollama_routes_as_system_command(self, monkeypatch):
        from mythic_agent.ui.screens import chat_screen
        from mythic_agent.ui.screens.chat_screen import MainChatScreen

        calls = []
        monkeypatch.setattr(
            chat_screen.SecureAPI, "publish_system_command",
            staticmethod(lambda cmd, args: calls.append((cmd, args))))
        screen = MainChatScreen.__new__(MainChatScreen)
        screen.handle_command("/ollama pull phi4", _FakeLog())
        assert calls == [("/ollama", "pull phi4")]


class TestOllamaCommandHandler:
    def test_list_is_default_and_marks_running(self, handler):
        handler._handle_ollama("")
        text = _published_text(handler)
        assert "llama3.1:latest" in text
        assert "mistral" in text
        assert "(running)" in text

    def test_list_explicit(self, handler):
        handler._handle_ollama("list")
        assert "Installed models:" in _published_text(handler)

    def test_pull(self, handler):
        handler._handle_ollama("pull phi4")
        assert _FakeProvider.last.pulled == "phi4"
        assert "success" in _published_text(handler)

    def test_pull_denied_by_policy(self, handler):
        handler.policy = _DenyPolicy()
        handler._handle_ollama("pull phi4")
        assert getattr(_FakeProvider.last, "pulled", None) is None
        assert "Permission denied" in _published_text(handler)

    def test_show_present(self, handler):
        handler._handle_ollama("show mistral")
        text = _published_text(handler)
        assert "mistral" in text
        assert "llama 7B" in text

    def test_show_absent_is_honest_with_remedy(self, handler):
        handler._handle_ollama("show ghost")
        text = _published_text(handler)
        assert "not present" in text
        assert "/ollama pull ghost" in text

    def test_usage_on_bad_shape(self, handler):
        handler._handle_ollama("pull")
        assert "Usage: /ollama" in _published_text(handler)

    def test_unreachable_server_error_carries_remedy(self, handler,
                                                     monkeypatch):
        from mythic_agent.providers import registry as registry_module

        class _DownProvider(_FakeProvider):
            def discover(self):
                raise ProviderError(
                    "Ollama is unreachable at http://localhost:11434. "
                    "Start it with `ollama serve` and pull a model with "
                    "`ollama pull <model>`.")

        monkeypatch.setitem(registry_module._REGISTRY, "ollama",
                            _DownProvider)
        handler._handle_ollama("list")
        assert "ollama serve" in _published_text(handler)
