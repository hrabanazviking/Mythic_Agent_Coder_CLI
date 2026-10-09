"""S07 provider adapter tests: loopback auth, retry budget, SSE streaming, doctor.

All provider traffic goes to in-process fake HTTP fixtures; no real
provider is ever contacted.
"""

import copy
import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace

import pytest

from mythic_agent.agents import llm
from mythic_agent.core.execution import is_loopback_url
from mythic_agent.core.policy import ToolPolicy
from mythic_agent.core.runtime import runtime_settings
from mythic_agent.core.secure_api import subscribe, unsubscribe


class OfflineMemory:
    def search(self, query, top_k=2):
        return []

    def insert(self, text, metadata=None):
        pass


class FakeProvider:
    """Configurable OpenAI-compatible fake with a request journal.

    ``plan`` is a queue of per-POST behaviors; when empty, POSTs get a
    default JSON echo. Behaviors:
      ("json", 200)                 -- echo chat completion
      ("status", code, headers, body) -- raw JSON status response
      ("sse", [chunk, ...])         -- Server-Sent Events stream
      ("sse-raw", text)             -- raw SSE bytes (malformed streams)
    GET /v1/models returns a one-model discovery document.
    """

    def __init__(self):
        self.calls = []
        self.plan = []
        self._lock = threading.Lock()
        provider = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                if self.path == "/v1/models":
                    body = {"object": "list",
                            "data": [{"id": "fixture-model", "object": "model"}]}
                    encoded = json.dumps(body).encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(encoded)))
                    self.end_headers()
                    self.wfile.write(encoded)
                else:
                    self.send_response(404)
                    self.end_headers()

            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0) or 0)
                request = json.loads(self.rfile.read(length) or b"{}")
                with provider._lock:
                    provider.calls.append(request)
                    behavior = provider.plan.pop(0) if provider.plan else ("json", 200)
                kind = behavior[0]
                if kind == "status":
                    _, status, headers, body = behavior
                    encoded = json.dumps(body).encode()
                    self.send_response(status)
                    for name, value in headers.items():
                        self.send_header(name, value)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(encoded)))
                    self.end_headers()
                    self.wfile.write(encoded)
                elif kind == "sse":
                    self.send_response(200)
                    self.send_header("Content-Type", "text/event-stream")
                    self.end_headers()
                    for chunk in behavior[1]:
                        self.wfile.write(f"data: {json.dumps(chunk)}\n\n".encode())
                        self.wfile.flush()
                    self.wfile.write(b"data: [DONE]\n\n")
                    self.wfile.flush()
                elif kind == "sse-raw":
                    self.send_response(200)
                    self.send_header("Content-Type", "text/event-stream")
                    self.end_headers()
                    self.wfile.write(behavior[1].encode())
                    self.wfile.flush()
                else:
                    last = request["messages"][-1]
                    content = last.get("content", "")
                    message = {"role": "assistant", "content": "Reply: " + (content or "")}
                    body = {"id": "fixture-response", "object": "chat.completion",
                            "created": 1, "model": "fixture-model",
                            "choices": [{"index": 0, "message": message,
                                         "finish_reason": "stop"}],
                            "usage": {"prompt_tokens": 3, "completion_tokens": 4,
                                      "total_tokens": 7}}
                    encoded = json.dumps(body).encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(encoded)))
                    self.end_headers()
                    self.wfile.write(encoded)

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    @property
    def base_url(self):
        return f"http://127.0.0.1:{self.server.server_port}/v1"

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)


def _sse_chunk(delta, finish_reason=None, usage=None):
    chunk = {"id": "sse-fixture", "object": "chat.completion.chunk", "created": 1,
             "model": "fixture-model",
             "choices": [{"index": 0, "delta": delta, "finish_reason": finish_reason}]}
    if usage is not None:
        chunk["usage"] = usage
    return chunk


def _sse_text_and_tools():
    """Fragmented text plus tool name/arguments split across chunks."""
    return [
        _sse_chunk({"role": "assistant", "content": "Reply"}),
        _sse_chunk({"content": ": hel"}),
        _sse_chunk({"content": "lo"}),
        _sse_chunk({"tool_calls": [{"index": 0, "id": "call-1", "type": "function",
                                    "function": {"name": "read_file", "arguments": ""}}]}),
        _sse_chunk({"tool_calls": [{"index": 0,
                                    "function": {"arguments": '{"path": "no'}}]}),
        _sse_chunk({"tool_calls": [{"index": 0,
                                    "function": {"arguments": 'tes.md"}'}}]}),
        _sse_chunk({}, finish_reason="tool_calls",
                   usage={"prompt_tokens": 3, "completion_tokens": 4, "total_tokens": 7}),
    ]


def _sse_final_text():
    return [
        _sse_chunk({"role": "assistant", "content": "Reply"}),
        _sse_chunk({"content": ": explicit context"}),
        _sse_chunk({}, finish_reason="stop",
                   usage={"prompt_tokens": 3, "completion_tokens": 4, "total_tokens": 7}),
    ]


@pytest.fixture
def provider_agent(tmp_path, monkeypatch):
    """In-process Agent pointed at a fake loopback provider, no API keys."""
    provider = FakeProvider()
    config = {"model": "fixture-model", "base_url": provider.base_url,
              "api_keys": {}, "streaming": False}
    monkeypatch.setattr(llm.config_manager, "MYTHIC_DIR", tmp_path / "state")
    monkeypatch.setattr(llm.config_manager, "load_config",
                        lambda: copy.deepcopy(config))
    monkeypatch.setattr(llm.config_manager, "save_config", lambda config: True)
    monkeypatch.setattr(llm, "get_vector_provider", lambda *args: OfflineMemory())
    for key in ("OPENAI_API_KEY", "DEEPSEEK_API_KEY", "OPENROUTER_API_KEY",
                "ANTHROPIC_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    instance = llm.Agent(project_root=tmp_path, config=copy.deepcopy(config))
    instance.tool_policy = ToolPolicy("trusted")
    yield instance, provider
    provider.close()
    unsubscribe("agent_clear_history", instance._handle_clear_history)
    unsubscribe("agent_compact_history", instance._handle_compact_history)


# ----------------------------------------------------------------------
# loopback detection and credential admission
# ----------------------------------------------------------------------

@pytest.mark.parametrize("url,expected", [
    ("http://127.0.0.1:8080/v1", True),
    ("http://127.0.0.2:8080/v1", True),
    ("http://localhost:8080/v1", True),
    ("http://[::1]:8080/v1", True),
    ("https://api.openai.com/v1", False),
    ("http://192.168.1.10:8080/v1", False),
    ("http://example.com/v1", False),
    ("not-a-url", False),
])
def test_is_loopback_url(url, expected):
    assert is_loopback_url(url) is expected


def test_loopback_needs_no_key_and_ignores_proxy_env(provider_agent):
    agent, provider = provider_agent
    # The sandbox's own lowercase no_proxy carries bracketed IPv6 entries
    # that crash naive proxy parsing; loopback must not consult it at all.
    client = agent.get_client()
    assert client.trust_env is False
    agent._append_message({"role": "user", "content": "hello"})
    response, streamed = agent._request_response(client, runtime_settings(agent.config))
    assert streamed is False
    assert response.choices[0].message.content == "Reply: hello"
    assert len(provider.calls) == 1


def test_remote_without_key_fails_before_any_network(provider_agent):
    agent, provider = provider_agent
    agent.config["base_url"] = "https://example.invalid/v1"
    with pytest.raises(llm.ProviderCredentialsError, match="No API key configured"):
        agent.get_client()
    assert provider.calls == []


# ----------------------------------------------------------------------
# retry budget
# ----------------------------------------------------------------------

def test_transient_429_with_retry_after_then_succeeds(provider_agent):
    agent, provider = provider_agent
    provider.plan = [
        ("status", 429, {"Retry-After": "0"}, {"error": {"message": "slow down"}}),
        ("json", 200),
    ]
    agent._append_message({"role": "user", "content": "hello"})
    client = agent.get_client()
    response, _ = agent._request_response(client, runtime_settings(agent.config))
    assert response.choices[0].message.content == "Reply: hello"
    assert len(provider.calls) == 2


def test_401_is_not_retried(provider_agent):
    from openai import AuthenticationError
    agent, provider = provider_agent
    provider.plan = [("status", 401, {}, {"error": {"message": "bad key"}})]
    agent._append_message({"role": "user", "content": "hello"})
    client = agent.get_client()
    with pytest.raises(AuthenticationError):
        agent._request_response(client, runtime_settings(agent.config))
    assert len(provider.calls) == 1


def test_retry_budget_exhausted_after_max_retries_plus_one(provider_agent):
    from openai import InternalServerError
    agent, provider = provider_agent
    provider.plan = [("status", 500, {}, {"error": {"message": "boom"}})] * 4
    agent._append_message({"role": "user", "content": "hello"})
    client = agent.get_client()
    with pytest.raises(InternalServerError):
        agent._request_response(client, runtime_settings(agent.config))
    assert len(provider.calls) == 3  # initial attempt + max_retries (2)


def test_retry_after_hint_is_honored_and_bounded():
    settings = {"retry_delay": 0.5, "retry_delay_cap": 8.0}
    hinted = SimpleNamespace(response=SimpleNamespace(headers={"retry-after": "3"}))
    assert llm._retry_delay(hinted, 0, settings) == 3.0
    capped = SimpleNamespace(response=SimpleNamespace(headers={"retry-after": "100"}))
    assert llm._retry_delay(capped, 0, settings) == 8.0
    absent = SimpleNamespace(response=SimpleNamespace(headers={}))
    assert llm._retry_delay(absent, 2, settings) == 2.0  # 0.5 * 2**2
    no_response = SimpleNamespace(response=None)
    assert llm._retry_delay(no_response, 0, settings) == 0.5


# ----------------------------------------------------------------------
# SSE streaming
# ----------------------------------------------------------------------

def test_streaming_reassembles_fragmented_text_and_tool_calls(provider_agent):
    agent, provider = provider_agent
    agent.config["streaming"] = True
    provider.plan = [("sse", _sse_text_and_tools())]
    agent._append_message({"role": "user", "content": "hello"})
    deltas = []

    def on_chunk(**payload):
        if payload.get("agent_name") == agent.name:
            deltas.append(payload.get("text", ""))

    subscribe("agent_chat_chunk", on_chunk)
    try:
        client = agent.get_client()
        response, streamed = agent._request_response(client, runtime_settings(agent.config))
    finally:
        unsubscribe("agent_chat_chunk", on_chunk)
    assert streamed is True
    message = llm.Agent._normalize_message(response.choices[0].message)
    assert message["content"] == "Reply: hello"
    assert message["tool_calls"] == [
        {"id": "call-1", "type": "function",
         "function": {"name": "read_file", "arguments": '{"path": "notes.md"}'}}]
    assert len(deltas) >= 2  # incremental text, emitted once per fragment
    assert "".join(deltas) == "Reply: hello"
    assert response.usage.total_tokens == 7


def test_malformed_stream_fails_without_tool_execution(provider_agent):
    agent, provider = provider_agent
    agent.config["streaming"] = True
    provider.plan = [("sse-raw", "data: {not valid json\n\n")]
    agent._append_message({"role": "user", "content": "hello"})
    client = agent.get_client()
    with pytest.raises(RuntimeError, match="[Ss]tream"):
        agent._request_response(client, runtime_settings(agent.config))
    assert len(provider.calls) == 1


def test_incomplete_tool_fragments_are_rejected(provider_agent):
    agent, provider = provider_agent
    agent.config["streaming"] = True
    provider.plan = [("sse", [
        _sse_chunk({"tool_calls": [{"index": 0, "function": {"arguments": "{}"}}]}),
        _sse_chunk({}, finish_reason="tool_calls"),
    ])]
    agent._append_message({"role": "user", "content": "hello"})
    client = agent.get_client()
    with pytest.raises(RuntimeError, match="incomplete tool call"):
        agent._request_response(client, runtime_settings(agent.config))


def test_streaming_turn_executes_tools_and_never_duplicates_text(provider_agent, tmp_path):
    agent, provider = provider_agent
    agent.config["streaming"] = True
    (tmp_path / "notes.md").write_text("explicit context")
    provider.plan = [("sse", _sse_text_and_tools()), ("sse", _sse_final_text())]
    deltas = []

    def on_chunk(**payload):
        if payload.get("agent_name") == agent.name:
            deltas.append(payload.get("text", ""))

    subscribe("agent_chat_chunk", on_chunk)
    try:
        text = agent.chat("hello")
    finally:
        unsubscribe("agent_chat_chunk", on_chunk)
    assert text == "Reply: explicit context"
    # Every fragment emitted exactly once; the final text was never re-emitted whole.
    assert "".join(deltas) == "Reply: helloReply: explicit context"
    assert agent.total_tokens == 14


# ----------------------------------------------------------------------
# mythic doctor --provider (subprocess, fake loopback fixture)
# ----------------------------------------------------------------------

def _write_config(home, base_url):
    home.mkdir(parents=True, exist_ok=True)
    config = {"model": "fixture-model", "base_url": base_url, "api_keys": {},
              "sub_agents": [], "config_version": 3}
    (home / "config.json").write_text(json.dumps(config))


def _doctor(tmp_path, *args):
    home = tmp_path / "doctor-home"
    env = os.environ.copy()
    for key in ("OPENAI_API_KEY", "DEEPSEEK_API_KEY", "OPENROUTER_API_KEY",
                "ANTHROPIC_API_KEY"):
        env.pop(key, None)
    env["MYTHIC_HOME"] = str(home)
    command = [sys.executable, "-m", "mythic_agent.cli", "doctor", *args]
    return subprocess.run(command, capture_output=True, text=True, env=env, timeout=60)


def _doctor_json(stdout):
    payload, _ = json.JSONDecoder().raw_decode(stdout[stdout.index("["):])
    return payload


def test_doctor_provider_live_against_loopback_fixture(tmp_path):
    provider = FakeProvider()
    try:
        _write_config(tmp_path / "doctor-home", provider.base_url)
        result = _doctor(tmp_path, "--provider", "--json")
        assert result.returncode == 0, result.stderr
        results = _doctor_json(result.stdout)
        by_name = {entry["name"]: entry for entry in results}
        assert by_name["provider"]["status"] == "ok"
        assert by_name["provider-live"]["status"] == "ok"
        assert "reachable" in by_name["provider-live"]["message"]
    finally:
        provider.close()


def test_doctor_provider_offline_check_only(tmp_path):
    provider = FakeProvider()
    try:
        _write_config(tmp_path / "doctor-home", provider.base_url)
        result = _doctor(tmp_path, "--check", "provider")
        assert result.returncode == 0, result.stderr
        assert "no key needed" in result.stdout
    finally:
        provider.close()


def test_doctor_provider_without_key_fails_fast_with_remedy(tmp_path):
    _write_config(tmp_path / "doctor-home", "https://example.invalid/v1")
    result = _doctor(tmp_path, "--provider")
    assert result.returncode == 1
    assert "No API key configured" in result.stdout
