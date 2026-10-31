"""M-026 — The gateways: OpenRouter's browsable catalogue + kin gateways.

TIER: unit

(The loopback class below runs a real local HTTP server, but it is
still unit-tier: loopback only, no external network, no live gateway.)

Covers the M-026 surface:

* ``OpenRouterProvider.catalogue()`` — the public ``GET /models``
  door normalised exactly as the gateway reports it (id, name,
  context length, modality, per-token prices, max completion);
  fields the door does not report stay None — unknown = unknown,
* ``catalogue_entry()`` / ``search_catalogue()`` — exact-id lookup
  with an honest not-in-catalogue error, and case-insensitive
  id/name search,
* error honesty: unreachable gateway, non-200 answer, and malformed
  body each surface as their own ProviderError — never a stale or
  invented list,
* a REAL loopback proof: a ThreadingHTTPServer on 127.0.0.1 speaking
  the catalogue shape, read through the unpatched ``_get_json``,
* the kin gateways (groq, together, fireworks, xai, mistral) as
  first-class registry citizens: preset class == registry data ==
  runtime registry, and the universal adapter constructs each from
  its entry alone,
* the TUI ``/gateway`` command (list / search / show / usage /
  honest error) and its system-command routing in the chat screen.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from mythic_agent.core.provider_registry import load_registry
from mythic_agent.providers.base import ProviderError
from mythic_agent.providers.gateways import (
    FireworksProvider,
    GroqProvider,
    MistralProvider,
    TogetherProvider,
    XAIProvider,
)
from mythic_agent.providers.openai_compat import UniversalOpenAICompatProvider
from mythic_agent.providers.openrouter import OpenRouterProvider
from mythic_agent.providers.registry import get_provider, list_providers

# A catalogue body in the shape the live door returned on 2026-10-31
# (fields verified against the real response that day; values here
# are fixtures, not live data).
CATALOGUE_BODY = {
    "data": [
        {
            "id": "acme/acme-coder-1",
            "name": "Acme: Coder 1",
            "context_length": 200000,
            "architecture": {
                "modality": "text+image->text",
                "input_modalities": ["text", "image"],
                "output_modalities": ["text"],
                "tokenizer": "Other",
                "instruct_type": None,
            },
            "pricing": {"prompt": "0.000001", "completion": "0.000002"},
            "top_provider": {
                "context_length": 200000,
                "max_completion_tokens": 8192,
                "is_moderated": False,
            },
        },
        {
            "id": "acme/acme-mini",
            "name": "Acme: Mini",
            "context_length": 32000,
            "architecture": {"modality": "text->text"},
            "pricing": {"prompt": "0.0000001"},
            "top_provider": {},
        },
        {"name": "No id at all — must be skipped"},
        "not-even-a-dict",
    ]
}


def _provider(body=CATALOGUE_BODY, status=200):
    provider = OpenRouterProvider(api_key="fake-key")
    provider._get_json = lambda path: (status, body)
    return provider


# ----------------------------------------------------------------------
# The catalogue, normalised as reported
# ----------------------------------------------------------------------

class TestCatalogue:
    def test_entries_normalised_and_idless_skipped(self):
        entries = _provider().catalogue()
        assert [e["id"] for e in entries] == [
            "acme/acme-coder-1", "acme/acme-mini"]

    def test_reported_fields_carried_exactly(self):
        entry = _provider().catalogue()[0]
        assert entry["name"] == "Acme: Coder 1"
        assert entry["context_length"] == 200000
        assert entry["modality"] == "text+image->text"
        assert entry["input_modalities"] == ["text", "image"]
        assert entry["output_modalities"] == ["text"]
        assert entry["prompt_price"] == "0.000001"
        assert entry["completion_price"] == "0.000002"
        assert entry["max_completion_tokens"] == 8192

    def test_unreported_fields_are_none_never_guessed(self):
        entry = _provider().catalogue()[1]
        assert entry["completion_price"] is None
        assert entry["max_completion_tokens"] is None
        assert entry["input_modalities"] is None
        assert entry["output_modalities"] is None

    def test_entry_by_exact_id(self):
        entry = _provider().catalogue_entry("acme/acme-mini")
        assert entry["context_length"] == 32000

    def test_entry_absent_is_an_honest_error(self):
        with pytest.raises(ProviderError) as excinfo:
            _provider().catalogue_entry("acme/ghost")
        assert "not in the openrouter catalogue" in str(excinfo.value)

    def test_entry_empty_id_rejected(self):
        with pytest.raises(ProviderError):
            _provider().catalogue_entry("  ")

    def test_search_matches_id_and_name_case_insensitively(self):
        provider = _provider()
        assert [e["id"] for e in provider.search_catalogue("CODER")] == [
            "acme/acme-coder-1"]
        assert [e["id"] for e in provider.search_catalogue("mini")] == [
            "acme/acme-mini"]
        assert provider.search_catalogue("zzz-no-match") == []

    def test_search_empty_query_rejected(self):
        with pytest.raises(ProviderError):
            _provider().search_catalogue("")

    def test_non_200_surfaces_the_gateways_own_status(self):
        with pytest.raises(ProviderError) as excinfo:
            _provider(status=503).catalogue()
        assert "HTTP 503" in str(excinfo.value)

    def test_malformed_body_is_an_error_not_an_empty_list(self):
        with pytest.raises(ProviderError):
            _provider(body={"unexpected": True}).catalogue()
        with pytest.raises(ProviderError):
            _provider(body=["not", "a", "dict"]).catalogue()

    def test_unreachable_gateway_says_so_with_its_remedy(self):
        provider = OpenRouterProvider(
            api_key="fake-key", base_url="http://127.0.0.1:1/v1",
            timeout=2.0)
        with pytest.raises(ProviderError) as excinfo:
            provider.catalogue()
        assert "unreachable" in str(excinfo.value)
        assert "network" in str(excinfo.value)


# ----------------------------------------------------------------------
# A real loopback proof of the catalogue door
# ----------------------------------------------------------------------

class _CatalogueHandler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 - the server's own spelling
        if self.path == "/v1/models":
            payload = json.dumps(CATALOGUE_BODY).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args):  # keep the test log clean
        pass


class TestCatalogueLoopback:
    def test_catalogue_over_real_http(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), _CatalogueHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            port = server.server_address[1]
            provider = OpenRouterProvider(
                api_key="fake-key", base_url=f"http://127.0.0.1:{port}/v1")
            entries = provider.catalogue()
            assert [e["id"] for e in entries] == [
                "acme/acme-coder-1", "acme/acme-mini"]
            assert provider.catalogue_entry(
                "acme/acme-coder-1")["max_completion_tokens"] == 8192
        finally:
            server.shutdown()
            server.server_close()


# ----------------------------------------------------------------------
# The kin gateways as first-class citizens
# ----------------------------------------------------------------------

KIN = {
    "groq": (GroqProvider, "llama-3.3-70b-versatile", "GROQ_API_KEY",
             "https://api.groq.com/openai/v1"),
    "together": (TogetherProvider, "meta-llama/Llama-3.3-70B-Instruct-Turbo",
                 "TOGETHER_API_KEY", "https://api.together.xyz/v1"),
    "fireworks": (FireworksProvider,
                  "accounts/fireworks/models/llama-v3p3-70b-instruct",
                  "FIREWORKS_API_KEY",
                  "https://api.fireworks.ai/inference/v1"),
    "xai": (XAIProvider, "grok-4", "XAI_API_KEY", "https://api.x.ai/v1"),
    "mistral": (MistralProvider, "mistral-large-latest", "MISTRAL_API_KEY",
                "https://api.mistral.ai/v1"),
}


class TestKinGateways:
    @pytest.mark.parametrize("name", sorted(KIN))
    def test_preset_class_facts(self, name):
        cls, model, env, endpoint = KIN[name]
        assert cls.name == name
        assert cls.default_model == model
        assert cls.api_key_env == env
        assert cls.base_url_default == endpoint

    @pytest.mark.parametrize("name", sorted(KIN))
    def test_runtime_registry_resolves_each_kin(self, name):
        cls = KIN[name][0]
        assert isinstance(get_provider(name), cls)
        assert name in list_providers()

    @pytest.mark.parametrize("name", sorted(KIN))
    def test_registry_data_matches_the_preset(self, name):
        cls, model, env, endpoint = KIN[name]
        entry = load_registry().provider(name)
        assert entry.adapter == f"mythic_agent.providers.gateways:{cls.__name__}"
        assert entry.default_model == model
        assert entry.api_key_env == env
        assert entry.endpoint == endpoint
        assert entry.dialect == "openai_compatible"
        assert entry.locality == "remote"
        # The static list is honestly just the default — the live
        # catalogue is the gateway's own /models door.
        assert entry.models == (model,)

    @pytest.mark.parametrize("name", sorted(KIN))
    def test_universal_adapter_constructs_each_kin_from_data(self, name):
        cls, model, env, endpoint = KIN[name]

        def transport(path, payload, headers):
            assert payload["model"] == model
            return 200, {"choices": [{"message": {"content": "pong"}}]}

        provider = UniversalOpenAICompatProvider.from_registry(
            name, api_key="fake-key", transport=transport)
        assert provider.name == name
        assert provider.base_url == endpoint
        assert provider.chat([{"role": "user", "content": "ping"}]) == "pong"

    def test_the_ocean_now_counts_sixteen_doors(self):
        registry = load_registry()
        assert len(registry.providers) == 16
        assert len(registry.by_locality("remote")) == 10
        assert len(registry.by_dialect("openai_compatible")) == 12
        gateway_names = {
            p.name for p in registry.providers
            if p.name in KIN or p.name == "openrouter"}
        assert gateway_names == set(KIN) | {"openrouter"}


# ----------------------------------------------------------------------
# The /gateway TUI command
# ----------------------------------------------------------------------

class _FakeGatewayProvider:
    """Stands in for OpenRouterProvider in the handler (no sockets)."""

    base_url = "https://openrouter.ai/api/v1"

    def catalogue(self):
        provider = _provider()
        return provider.catalogue()

    def search_catalogue(self, query):
        return _provider().search_catalogue(query)

    def catalogue_entry(self, model_id):
        return _provider().catalogue_entry(model_id)


@pytest.fixture()
def handler(monkeypatch):
    from mythic_agent.agents import command_handler as handler_module
    from mythic_agent.agents.command_handler import CommandHandler
    from mythic_agent.providers import registry as registry_module

    monkeypatch.setitem(
        registry_module._REGISTRY, "openrouter", _FakeGatewayProvider)
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


class TestGatewayCommand:
    def test_list_is_default_and_counts_the_catalogue(self, handler):
        handler._handle_gateway("")
        text = _published_text(handler)
        assert "2 models" in text
        assert "acme/acme-coder-1" in text
        assert "context 200000" in text

    def test_search_filters(self, handler):
        handler._handle_gateway("search mini")
        text = _published_text(handler)
        assert "1 matching" in text
        assert "acme/acme-mini" in text
        assert "acme-coder" not in text

    def test_show_reports_the_gateways_facts(self, handler):
        handler._handle_gateway("show acme/acme-coder-1")
        text = _published_text(handler)
        assert "Context: 200000 tokens" in text
        assert "Max completion: 8192 tokens" in text
        assert "Prompt price: 0.000001 per token" in text

    def test_show_absent_is_the_honest_error(self, handler):
        handler._handle_gateway("show acme/ghost")
        assert "not in the openrouter catalogue" in _published_text(handler)

    def test_usage_on_garbage(self, handler):
        handler._handle_gateway("frobnicate")
        assert "Usage: /gateway" in _published_text(handler)


class TestChatScreenRouting:
    def test_gateway_routes_as_system_command(self, monkeypatch):
        from mythic_agent.ui.screens import chat_screen
        from mythic_agent.ui.screens.chat_screen import MainChatScreen

        class _FakeLog:
            def __init__(self):
                self.lines = []

            def write(self, *args, **kwargs):
                self.lines.append(" ".join(str(a) for a in args))

        calls = []
        monkeypatch.setattr(
            chat_screen.SecureAPI, "publish_system_command",
            staticmethod(lambda cmd, args: calls.append((cmd, args))))
        screen = MainChatScreen.__new__(MainChatScreen)
        screen.handle_command("/gateway search llama", _FakeLog())
        assert calls == [("/gateway", "search llama")]
