"""
TIER: unit
The OpenAI-compatible universal adapter (All-Features roadmap M-020).

One adapter serving every compatible endpoint: the registry's seven
``openai_compatible`` entries are each constructed purely from their
registry data (endpoint, key env, default model, capabilities, and the
per-provider ``quirks`` declared in M-020) and proven serving — over a
real loopback HTTP endpoint, not just a stubbed transport — with
observable behaviour matching the shipped preset adapters:

* DeepSeek's ``reasoning-content-fallback`` quirk,
* OpenRouter's ``app-identification-headers`` quirk,
* vLLM's ``placeholder-bearer-auth`` quirk.

Non-compatible dialects (native SDK, Ollama-native) are refused, and
an unknown registry name stays unknown.
"""

import copy
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from mythic_agent.core.provider_registry import (
    QUIRKS,
    load_registry,
    render_markdown,
    validate_registry,
)
from mythic_agent.providers.base import ProviderError
from mythic_agent.providers.openai_compat import (
    PLACEHOLDER_API_KEY,
    UniversalOpenAICompatProvider,
)
from mythic_agent.providers.openrouter import (
    DEFAULT_HTTP_REFERER as PRESET_REFERER,
)
from mythic_agent.providers.openrouter import (
    DEFAULT_X_TITLE as PRESET_X_TITLE,
)
from mythic_agent.providers.registry import get_provider
from mythic_agent.resources import load_resource

COMPATIBLE = (
    "deepseek",
    "llama.cpp",
    "lmstudio",
    "local-openai",
    "openai",
    "openrouter",
    "vllm",
)

MESSAGES = [{"role": "user", "content": "ping"}]


@pytest.fixture(scope="module")
def registry():
    return load_registry()


def _ok_transport(text="fake reply"):
    def transport(path, payload, headers):
        return 200, {"choices": [{"message": {"content": text}}]}

    return transport


# -- construction purely from registry data --------------------------------


def test_every_compatible_entry_constructs_from_data_alone(registry):
    entries = registry.by_dialect("openai_compatible")
    assert tuple(p.name for p in entries) == COMPATIBLE
    for entry in entries:
        adapter = UniversalOpenAICompatProvider(entry)
        assert adapter.name == entry.name
        assert adapter.base_url == entry.endpoint
        assert adapter.model == entry.default_model
        assert adapter.api_key_env == entry.api_key_env
        assert adapter.capabilities() == dict(entry.capabilities)


def test_from_registry_resolves_aliases_and_refuses_unknown():
    assert UniversalOpenAICompatProvider.from_registry("gpt").name == "openai"
    assert (
        UniversalOpenAICompatProvider.from_registry("LM-STUDIO").name
        == "lmstudio"
    )
    with pytest.raises(KeyError):
        UniversalOpenAICompatProvider.from_registry("no-such-door")


@pytest.mark.parametrize("name", ["anthropic", "google", "ollama"])
def test_non_compatible_dialects_are_refused(name):
    with pytest.raises(ProviderError):
        UniversalOpenAICompatProvider.from_registry(name)


def test_universal_matches_each_preset_adapter(registry):
    for entry in registry.by_dialect("openai_compatible"):
        preset = get_provider(entry.name, api_key="k")
        universal = UniversalOpenAICompatProvider(entry, api_key="k")
        assert universal.name == preset.name
        assert universal.default_model == preset.default_model
        assert universal.api_key_env == preset.api_key_env
        assert universal.base_url == preset.base_url
        assert universal.capabilities() == preset.capabilities()
        assert universal._headers() == preset._headers()


# -- quirks -----------------------------------------------------------------


def test_quirks_vocabulary_is_exactly_the_three_preset_behaviours():
    assert QUIRKS == (
        "app-identification-headers",
        "placeholder-bearer-auth",
        "reasoning-content-fallback",
    )


def test_shipped_quirks_match_the_preset_behaviours(registry):
    assert registry.provider("deepseek").quirks == (
        "reasoning-content-fallback",
    )
    assert registry.provider("openrouter").quirks == (
        "app-identification-headers",
    )
    assert registry.provider("vllm").quirks == ("placeholder-bearer-auth",)
    for name in ("llama.cpp", "lmstudio", "local-openai", "openai"):
        assert registry.provider(name).quirks == ()
    # No quirk is declared but unused by the vocabulary, and every
    # vocabulary quirk is carried by exactly one shipped entry.
    declared = [q for p in registry.providers for q in p.quirks]
    assert sorted(declared) == sorted(QUIRKS)


def test_reasoning_fallback_quirk_serves_reasoning_only_bodies():
    def reasoning_transport(path, payload, headers):
        return 200, {
            "choices": [{"message": {"content": "", "reasoning_content": "thought"}}]
        }

    deepseek = UniversalOpenAICompatProvider.from_registry(
        "deepseek", transport=reasoning_transport
    )
    assert deepseek.chat(MESSAGES) == "thought"
    # Without the quirk, the same body is the usual empty-text error.
    openai = UniversalOpenAICompatProvider.from_registry(
        "openai", transport=reasoning_transport
    )
    with pytest.raises(ProviderError):
        openai.chat(MESSAGES)


def test_app_identification_headers_quirk_matches_the_preset():
    adapter = UniversalOpenAICompatProvider.from_registry(
        "openrouter", api_key="k", transport=_ok_transport()
    )
    headers = adapter._headers()
    assert headers["HTTP-Referer"] == PRESET_REFERER
    assert headers["X-Title"] == PRESET_X_TITLE
    plain = UniversalOpenAICompatProvider.from_registry(
        "openai", api_key="k", transport=_ok_transport()
    )
    assert "HTTP-Referer" not in plain._headers()


def test_placeholder_bearer_quirk_only_when_no_key():
    vllm = UniversalOpenAICompatProvider.from_registry(
        "vllm", transport=_ok_transport()
    )
    assert vllm._headers()["Authorization"] == f"Bearer {PLACEHOLDER_API_KEY}"
    keyed = UniversalOpenAICompatProvider.from_registry(
        "vllm", api_key="real", transport=_ok_transport()
    )
    assert keyed._headers()["Authorization"] == "Bearer real"
    local = UniversalOpenAICompatProvider.from_registry(
        "lmstudio", transport=_ok_transport()
    )
    assert "Authorization" not in local._headers()


def test_render_markdown_names_the_quirks(registry):
    text = render_markdown(registry)
    for quirk in QUIRKS:
        assert quirk in text


# -- registry validation of quirks ------------------------------------------


def _mutated(mutator):
    data = copy.deepcopy(load_resource("provider_registry.yaml"))
    mutator(data)
    return data


def test_validator_rejects_an_unknown_quirk():
    def spoil(d):
        d["providers"][1]["quirks"] = ["teleports"]

    assert any("quirk" in p for p in validate_registry(_mutated(spoil)))


def test_validator_rejects_a_quirk_on_a_native_entry():
    def spoil(d):
        d["providers"][0]["quirks"] = ["reasoning-content-fallback"]

    assert any("quirks" in p for p in validate_registry(_mutated(spoil)))


def test_validator_rejects_a_repeated_quirk():
    def spoil(d):
        d["providers"][1]["quirks"] = [
            "reasoning-content-fallback",
            "reasoning-content-fallback",
        ]

    assert any("repeat" in p for p in validate_registry(_mutated(spoil)))


def test_validator_rejects_a_missing_quirks_field():
    def spoil(d):
        del d["providers"][1]["quirks"]

    assert any("quirks" in p for p in validate_registry(_mutated(spoil)))


# -- the loopback proof: every compatible entry actually serving ------------


class _LoopbackHandler(BaseHTTPRequestHandler):
    """A minimal chat-completions endpoint recording what it received."""

    recorded = {}
    reasoning_only = False

    def do_POST(self):  # noqa: N802 - BaseHTTPRequestHandler's name
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else b""
        type(self).recorded = {
            "path": self.path,
            "headers": dict(self.headers.items()),
            "payload": json.loads(body) if body else {},
        }
        if type(self).reasoning_only:
            message = {"content": "", "reasoning_content": "loopback thought"}
        else:
            message = {"content": "loopback reply"}
        raw = json.dumps({"choices": [{"message": message}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *args):  # keep the test output clean
        pass


@pytest.fixture()
def loopback():
    _LoopbackHandler.recorded = {}
    _LoopbackHandler.reasoning_only = False
    server = ThreadingHTTPServer(("127.0.0.1", 0), _LoopbackHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}/v1"
    server.shutdown()
    thread.join(timeout=5)


@pytest.mark.parametrize("name", COMPATIBLE)
def test_each_compatible_entry_serves_over_loopback(loopback, name):
    _LoopbackHandler.reasoning_only = name == "deepseek"
    adapter = UniversalOpenAICompatProvider.from_registry(
        name, api_key="loopback-key", base_url=loopback
    )
    reply = adapter.chat(MESSAGES)
    assert reply == ("loopback thought" if name == "deepseek" else "loopback reply")
    recorded = _LoopbackHandler.recorded
    assert recorded["path"] == "/v1/chat/completions"
    assert recorded["payload"]["model"] == adapter.default_model
    headers = {k.lower(): v for k, v in recorded["headers"].items()}
    # Every door, keyed explicitly here, sends that key as its bearer.
    assert headers.get("authorization") == "Bearer loopback-key"
    if name == "openrouter":
        assert headers.get("http-referer") == PRESET_REFERER
        assert headers.get("x-title") == PRESET_X_TITLE


def test_keyless_local_doors_send_no_auth_over_loopback(loopback):
    for name in ("llama.cpp", "lmstudio", "local-openai"):
        adapter = UniversalOpenAICompatProvider.from_registry(
            name, base_url=loopback
        )
        assert adapter.chat(MESSAGES) == "loopback reply"
        headers = {
            k.lower() for k in _LoopbackHandler.recorded["headers"]
        }
        assert "authorization" not in headers
    vllm = UniversalOpenAICompatProvider.from_registry("vllm", base_url=loopback)
    assert vllm.chat(MESSAGES) == "loopback reply"
    headers = {
        k.lower(): v for k, v in _LoopbackHandler.recorded["headers"].items()
    }
    assert headers.get("authorization") == f"Bearer {PLACEHOLDER_API_KEY}"
