"""M-039 — Provider health board.

TIER: integration

Covers the M-039 surface:

* the pure layer (``mythic_agent.core.provider_health``):
  one entry per M-019 registry door — reachable /
  unreachable / needs-key / unknown, latency measured around
  a real probe or None, the last error in the probe's own
  words,
* the honesty rules: a door never probed is unknown with no
  latency and no error; a remote door without a held key is
  needs-key (its M-032 custody state named) and is never
  probed; native-SDK doors are unknown because no address
  is invented for them; local doors probe their live
  endpoints (compatible /models, Ollama /api/tags, Aesir
  /health/ready with ready:true the only healthy answer),
* custody without secrets: a held key is used as the
  probe's Authorization header and appears in no entry,
  record, or formatted line,
* the remembered M-036 weather riding along where a board
  has seen a door,
* the surfaces: ``mythic doctor --live`` grown into the
  board (text + ``--json`` carrying ``provider_health``)
  and ``Agent.provider_health()``.
"""

from __future__ import annotations

import json

import pytest

from mythic_agent.core.provider_health import (
    HEALTH_SLICE,
    PLAIN_EXPLANATION,
    STATUSES,
    build_board,
    format_board,
    probe_url_for,
)
from mythic_agent.core.provider_registry import load_registry


def _clock(step=0.25):
    state = {"t": 1000.0}

    def tick():
        state["t"] += step
        return state["t"]

    return tick


def _prober(answers=None, failures=None):
    """A fake prober: url -> (status, body); records calls."""
    calls = []
    answers = answers or {}
    failures = failures or {}

    def probe(url, headers, timeout):
        calls.append((url, dict(headers), timeout))
        if url in failures:
            raise failures[url]
        return answers.get(url, (200, "{}"))

    probe.calls = calls
    return probe


def _board(prober, **kwargs):
    kwargs.setdefault("environ", {})
    kwargs.setdefault("config", {})
    kwargs.setdefault("clock", _clock())
    kwargs.setdefault("now", 5000.0)
    return build_board(prober=prober, **kwargs)


# ----------------------------------------------------------------------
# The board's shape — one honest entry per registry door
# ----------------------------------------------------------------------

class TestBoardShape:
    def test_slice_statuses_and_explanation(self):
        assert HEALTH_SLICE == "M-039"
        assert STATUSES == ("reachable", "unreachable", "needs-key", "unknown")
        assert "never probed" in PLAIN_EXPLANATION
        assert "needs-key" in PLAIN_EXPLANATION

    def test_one_entry_per_registry_door_in_order(self):
        board = _board(_prober(), probe=False)
        registry = load_registry()
        assert [e.provider for e in board.entries] == list(registry.names())
        assert board.generated_at == 5000.0
        record = board.record()
        assert record["slice"] == "M-039"
        assert len(record["entries"]) == len(registry.providers)

    def test_probe_urls_follow_each_dialect(self):
        registry = load_registry()
        assert probe_url_for(registry.provider("openai")) == \
            "https://api.openai.com/v1/models"
        assert probe_url_for(registry.provider("ollama")) == \
            "http://localhost:11434/api/tags"
        assert probe_url_for(registry.provider("aesir")) == \
            "http://127.0.0.1:18434/health/ready"
        assert probe_url_for(registry.provider("anthropic")) is None
        assert probe_url_for(registry.provider("google")) is None

    def test_offline_board_is_all_unknown_and_invents_nothing(self):
        prober = _prober()
        board = _board(prober, probe=False)
        assert prober.calls == []
        for entry in board.entries:
            assert entry.status == "unknown"
            assert entry.probed is False
            assert entry.latency_ms is None
            assert entry.last_error is None
        assert board.counts() == {
            "reachable": 0, "unreachable": 0,
            "needs-key": 0, "unknown": len(board.entries)}


# ----------------------------------------------------------------------
# Probing — local doors live, remote doors gated on their key
# ----------------------------------------------------------------------

class TestProbing:
    def test_local_doors_reachable_with_measured_latency(self):
        prober = _prober(answers={
            "http://127.0.0.1:18434/health/ready":
                (200, '{"ready": true}'),
        })
        board = _board(prober)
        for name in ("llama.cpp", "lmstudio", "local-openai",
                     "ollama", "vllm", "aesir"):
            entry = board.entry(name)
            assert entry.status == "reachable", name
            assert entry.probed is True
            assert entry.latency_ms == pytest.approx(250.0)
            assert entry.last_error is None
        probed_urls = {url for url, _, _ in prober.calls}
        assert "http://localhost:11434/api/tags" in probed_urls
        assert "http://127.0.0.1:18434/health/ready" in probed_urls

    def test_remote_doors_without_a_key_are_needs_key_never_probed(self):
        prober = _prober()
        board = _board(prober)
        for name in ("deepseek", "openai", "openrouter", "groq",
                     "fireworks", "mistral", "together", "xai"):
            entry = board.entry(name)
            assert entry.status == "needs-key", name
            assert entry.probed is False
            assert entry.latency_ms is None
            assert entry.last_error is None
            assert entry.custody == "missing"
            assert entry.key_present is False
            assert "Kista" in entry.detail
        probed_urls = {url for url, _, _ in prober.calls}
        assert not any("api.openai.com" in url for url in probed_urls)
        assert not any("api.deepseek.com" in url for url in probed_urls)

    def test_native_sdk_doors_are_unknown_and_never_probed(self):
        prober = _prober()
        board = _board(prober, environ={
            "ANTHROPIC_API_KEY": "sk-ant", "GOOGLE_API_KEY": "g-key"})
        for name in ("anthropic", "google"):
            entry = board.entry(name)
            assert entry.status == "unknown", name
            assert entry.probed is False
            assert entry.endpoint is None
            assert "software kit" in entry.detail
        # Custody still tells the truth: the env key is held.
        assert board.entry("anthropic").custody == "environment"
        assert board.entry("anthropic").key_present is True

    def test_transport_failure_is_unreachable_with_its_own_words(self):
        url = "http://localhost:11434/api/tags"
        prober = _prober(failures={
            url: ConnectionError("connection refused at localhost:11434")})
        board = _board(prober)
        entry = board.entry("ollama")
        assert entry.status == "unreachable"
        assert entry.latency_ms == pytest.approx(250.0)
        assert "connection refused" in entry.last_error
        assert "ConnectionError" in entry.last_error

    def test_non_200_is_unreachable_with_the_status_as_error(self):
        prober = _prober(answers={
            "http://localhost:8080/v1/models": (503, "busy")})
        board = _board(prober)
        entry = board.entry("llama.cpp")
        assert entry.status == "unreachable"
        assert entry.last_error == "HTTP 503"

    def test_aesir_200_without_ready_true_is_not_healthy(self):
        prober = _prober(answers={
            "http://127.0.0.1:18434/health/ready":
                (200, '{"ready": false}')})
        board = _board(prober)
        entry = board.entry("aesir")
        assert entry.status == "unreachable"
        assert "ready is not true" in entry.last_error

    def test_counts_close_over_the_whole_board(self):
        board = _board(_prober(answers={
            "http://127.0.0.1:18434/health/ready":
                (200, '{"ready": true}')}),
            environ={"OPENAI_API_KEY": "sk-test"})
        counts = board.counts()
        assert sum(counts.values()) == len(board.entries)
        # 6 local reachable + openai reachable with its env key.
        assert counts["reachable"] == 7
        assert counts["needs-key"] == 7
        assert counts["unknown"] == 2  # the two native-SDK doors
        assert counts["unreachable"] == 0


# ----------------------------------------------------------------------
# Custody — where the key lives, never what it is
# ----------------------------------------------------------------------

class TestCustody:
    def test_env_key_lets_a_remote_door_be_probed_with_that_key(self):
        prober = _prober()
        board = _board(prober, environ={"OPENAI_API_KEY": "sk-secret-1"})
        entry = board.entry("openai")
        assert entry.status == "reachable"
        assert entry.custody == "environment"
        assert entry.key_present is True
        calls = {url: headers for url, headers, _ in prober.calls}
        assert calls["https://api.openai.com/v1/models"][
            "Authorization"] == "Bearer sk-secret-1"

    def test_no_key_value_appears_anywhere_on_the_board(self):
        secret = "sk-secret-must-not-leak"
        board = _board(_prober(), environ={"OPENAI_API_KEY": secret})
        assert secret not in json.dumps(board.record())
        assert secret not in format_board(board)

    def test_plaintext_config_key_is_named_plainly_and_used(self):
        config = {"api_keys": {
            "https://api.openai.com/v1": "sk-plain-2"}}
        board = _board(_prober(), config=config)
        entry = board.entry("openai")
        assert entry.custody == "plaintext"
        assert entry.key_present is True
        assert entry.status == "reachable"
        assert "sk-plain-2" not in json.dumps(board.record())

    def test_kista_vault_key_is_kista_custody(self, tmp_path):
        vault = tmp_path / "kista.json"
        vault.write_text(json.dumps({"OPENAI_API_KEY": "sk-vault-3"}),
                         encoding="utf-8")
        board = _board(_prober(), vault_file=str(vault))
        entry = board.entry("openai")
        assert entry.custody == "kista"
        assert entry.key_present is True
        assert entry.status == "reachable"
        assert "sk-vault-3" not in format_board(board)

    def test_kista_reference_in_config_resolves_through_the_vault(
            self, tmp_path):
        vault = tmp_path / "kista.json"
        vault.write_text(json.dumps({"DEEPSEEK_API_KEY": "sk-vault-4"}),
                         encoding="utf-8")
        config = {"api_keys": {
            "https://api.deepseek.com/v1": "kista:DEEPSEEK_API_KEY"}}
        board = _board(_prober(), config=config, vault_file=str(vault))
        entry = board.entry("deepseek")
        assert entry.custody == "kista"
        assert entry.status == "reachable"

    def test_unresolved_kista_reference_is_needs_key_not_dead(self, tmp_path):
        vault = tmp_path / "kista.json"
        vault.write_text("{}", encoding="utf-8")
        config = {"api_keys": {
            "https://api.deepseek.com/v1": "kista:DEEPSEEK_API_KEY"}}
        prober = _prober()
        board = _board(prober, config=config, vault_file=str(vault))
        entry = board.entry("deepseek")
        assert entry.custody == "kista"
        assert entry.key_present is False
        assert entry.status == "needs-key"
        assert all("deepseek" not in url for url, _, _ in prober.calls)

    def test_local_doors_need_no_key(self):
        board = _board(_prober(), probe=False)
        for name in ("ollama", "llama.cpp", "vllm"):
            entry = board.entry(name)
            assert entry.custody == "not-needed"
            assert entry.key_present is True


# ----------------------------------------------------------------------
# Remembered weather — the M-036 board rides along
# ----------------------------------------------------------------------

class TestRememberedWeather:
    def test_seen_door_carries_its_weather_unseen_doors_none(self):
        from mythic_agent.core.rate_limit_weather import WeatherBoard

        weather = WeatherBoard(clock=lambda: 4000.0)
        weather.record_success("ollama", now=4000.0)
        board = _board(_prober(), probe=False, weather_board=weather)
        assert board.entry("ollama").remembered_state == "clear"
        assert board.entry("openai").remembered_state is None
        assert "remembered weather clear" in format_board(board)


# ----------------------------------------------------------------------
# Formatting
# ----------------------------------------------------------------------

class TestFormatting:
    def test_format_board_names_status_latency_custody_and_lesson(self):
        board = _board(_prober(answers={
            "http://127.0.0.1:18434/health/ready":
                (200, '{"ready": true}')}),
            environ={"OPENAI_API_KEY": "sk-x"})
        text = format_board(board)
        assert "ollama: reachable" in text
        assert "250 ms" in text
        assert "openai: reachable" in text
        assert "deepseek: needs-key" in text
        assert "anthropic: unknown" in text
        assert PLAIN_EXPLANATION in text


# ----------------------------------------------------------------------
# The live road — the real loopback prober
# ----------------------------------------------------------------------

class TestLoopbackProber:
    def test_default_prober_against_a_real_loopback_server(self):
        import threading
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                body = (b'{"ready": true}' if self.path == "/health/ready"
                        else b'{"data": []}')
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            port = server.server_address[1]
            registry = load_registry({
                "schema": "mythic.provider_registry/1",
                "registry_slice": "M-019",
                "source_note": "Synthetic registry for the loopback proof.",
                "extension_rule": "Synthetic.",
                "aliases": {"loop": "loopback"},
                "providers": [{
                    "name": "loopback", "title": "Loopback door",
                    "adapter": "mythic_agent.providers.openai_compat:"
                               "OpenAICompatProvider",
                    "dialect": "openai_compatible", "locality": "local",
                    "endpoint": f"http://127.0.0.1:{port}/v1",
                    "auth_style": "none", "api_key_env": None,
                    "default_model": "loop-model",
                    "models": ["loop-model"],
                    "capabilities": {"streaming": True,
                                     "tool_calling": False,
                                     "vision": False, "json_mode": False},
                    "notes": "Synthetic loopback door.",
                    "quirks": [],
                }],
            })
            board = build_board({}, registry=registry, environ={},
                                now=5000.0)
            entry = board.entry("loopback")
            assert entry.status == "reachable"
            assert entry.latency_ms is not None and entry.latency_ms >= 0
            assert entry.last_error is None
        finally:
            server.shutdown()
            thread.join(timeout=5)

    def test_default_prober_refused_port_is_unreachable(self):
        board = build_board({}, environ={}, now=5000.0, timeout=2.0)
        # Nothing on this VM serves Ollama's door in the test env;
        # if something did, the entry would be reachable instead —
        # either way it must be probed and carry a latency.
        entry = board.entry("ollama")
        assert entry.probed is True
        assert entry.status in ("reachable", "unreachable")
        assert entry.latency_ms is not None
        if entry.status == "unreachable":
            assert entry.last_error


# ----------------------------------------------------------------------
# The agent + the doctor surface
# ----------------------------------------------------------------------

class TestAgentSurface:
    def test_agent_offline_board(self, agent):
        status = agent.provider_health(probe=False)
        assert status["plain_explanation"] == PLAIN_EXPLANATION
        entries = status["board"]["entries"]
        assert len(entries) == len(load_registry().providers)
        assert all(e["status"] == "unknown" for e in entries)


class TestDoctorSurface:
    def _stub_doctor(self, monkeypatch):
        from mythic_agent import doctor
        from mythic_agent.core import provider_health
        from mythic_agent.core.config_manager import config_manager

        monkeypatch.setattr(config_manager, "load_config", lambda: {})
        monkeypatch.setattr(provider_health, "default_prober",
                            _prober(answers={
                                "http://127.0.0.1:18434/health/ready":
                                    (200, '{"ready": true}')}))
        monkeypatch.setattr(
            doctor, "check_provider_live",
            lambda timeout=15.0: doctor.HealthResult(
                "provider-live", doctor.HealthStatus.SKIP, "stubbed"))
        return doctor

    def test_doctor_live_prints_the_board(self, monkeypatch, capsys):
        doctor = self._stub_doctor(monkeypatch)
        code = doctor.main(["--live"])
        out = capsys.readouterr().out
        assert "Provider health board:" in out
        assert "ollama: reachable" in out
        assert "deepseek: needs-key" in out
        assert code in (0, 1)

    def test_doctor_live_json_carries_provider_health(
            self, monkeypatch, capsys):
        doctor = self._stub_doctor(monkeypatch)
        doctor.main(["--live", "--json"])
        out = capsys.readouterr().out
        payload, _ = json.JSONDecoder().raw_decode(out[out.index("{"):])
        assert "checks" in payload
        board = payload["provider_health"]
        assert board["slice"] == "M-039"
        by_name = {e["provider"]: e for e in board["entries"]}
        assert by_name["ollama"]["status"] == "reachable"
        assert by_name["ollama"]["latency_ms"] is not None
        assert by_name["deepseek"]["status"] == "needs-key"
        assert by_name["anthropic"]["status"] == "unknown"
        assert sum(board["counts"].values()) == len(board["entries"])

    def test_doctor_without_live_has_no_board(self, capsys):
        from mythic_agent import doctor

        doctor.main([])
        out = capsys.readouterr().out
        assert "Provider health board:" not in out
