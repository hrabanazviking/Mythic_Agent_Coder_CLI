"""Actual subprocess/HTTP protocol tests against a local, free fake provider."""

import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest


@pytest.fixture
def endpoint():
    requests = []
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            requests.append(request)
            assert self.path == "/v1/chat/completions"
            last = request["messages"][-1]
            content = last.get("content", "")
            if content == "fail":
                self.send_response(401)
                body = {"error": {"message": "fixture unauthorized", "type": "authentication_error"}}
            else:
                self.send_response(200)
                message = {"role": "assistant", "content": "Reply: " + (content or "")}
                if last["role"] == "user" and content in {"write", "read"}:
                    tool = "write_file" if content == "write" else "read_file"
                    arguments = {"path": "generated.py"}
                    if tool == "write_file":
                        arguments["content"] = "answer = 42\n"
                    message = {"role": "assistant", "content": "Inspecting tools", "tool_calls": [{
                        "id": "fixture-call", "type": "function", "function": {
                            "name": tool, "arguments": json.dumps(arguments),
                        },
                    }]}
                body = {"id": "fixture-response", "object": "chat.completion", "created": 1,
                        "model": "fixture-model", "choices": [{"index": 0, "message": message,
                        "finish_reason": "tool_calls" if message.get("tool_calls") else "stop"}],
                        "usage": {"prompt_tokens": 3, "completion_tokens": 4, "total_tokens": 7}}
            encoded = json.dumps(body).encode()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}/v1", requests
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)


def invoke(tmp_path, endpoint, *arguments, input_text=None):
    url, _ = endpoint
    env = os.environ.copy()
    for key in ("OPENAI_API_KEY", "DEEPSEEK_API_KEY", "OPENROUTER_API_KEY", "ANTHROPIC_API_KEY"):
        env.pop(key, None)
    env["MYTHIC_HOME"] = str(tmp_path / "app-state")
    env["NO_PROXY"] = "127.0.0.1,localhost"
    command = [sys.executable, "-m", "mythic_agent.cli", arguments[0],
               "--workspace", str(tmp_path), "--base-url", url, "--model", "fixture-model",
               *arguments[1:]]
    return subprocess.run(command, input=input_text, capture_output=True, text=True, env=env, timeout=15)


def test_one_shot_json_result_and_plain_text(tmp_path, endpoint):
    result = invoke(tmp_path, endpoint, "run", "hello", "--format", "json")
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["schema_version"] == 1
    assert output["status"] == "completed"
    assert output["text"] == "Reply: hello"
    assert output["total_tokens"] == 7
    assert output["workspace"] == str(tmp_path.resolve())
    plain = invoke(tmp_path, endpoint, "run", "hello")
    assert plain.returncode == 0
    assert plain.stdout == "Reply: hello\n"


def test_stdin_input_and_jsonl_are_clean_protocol(tmp_path, endpoint):
    result = invoke(tmp_path, endpoint, "run", "--format", "jsonl", input_text="hello from stdin")
    assert result.returncode == 0, result.stderr
    events = [json.loads(line) for line in result.stdout.splitlines()]
    assert all(event["schema_version"] == 1 for event in events)
    assert any(event["type"] == "assistant_delta" for event in events)
    assert events[-1]["type"] == "result"
    assert events[-1]["text"] == "Reply: hello from stdin"


def test_default_machine_policy_refuses_writes_without_prompting(tmp_path, endpoint):
    result = invoke(tmp_path, endpoint, "run", "write", "--format", "json")
    assert result.returncode == 3, result.stderr
    output = json.loads(result.stdout)
    assert output["status"] == "approval_required"
    assert output["denied_tools"] == ["write_file"]
    assert not (tmp_path / "generated.py").exists()
    assert "no operation" in endpoint[1][-1]["messages"][-1]["content"]


def test_explicit_trusted_mode_executes_tools_and_preserves_protocol(tmp_path, endpoint):
    result = invoke(tmp_path, endpoint, "run", "write", "--permission", "trusted", "--format", "json")
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "generated.py").read_text() == "answer = 42\n"
    assert json.loads(result.stdout)["total_tokens"] == 14
    history = endpoint[1][-1]["messages"]
    assert [message["role"] for message in history] == ["system", "user", "assistant", "tool"]


def test_read_only_tools_are_available(tmp_path, endpoint):
    (tmp_path / "generated.py").write_text("original")
    result = invoke(tmp_path, endpoint, "run", "read", "--format", "json")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["text"] == "Reply: original"


def test_noninteractive_ask_returns_approval_required(tmp_path, endpoint):
    result = invoke(tmp_path, endpoint, "run", "write", "--permission", "ask", "--format", "json")
    assert result.returncode == 3
    assert json.loads(result.stdout)["status"] == "approval_required"
    assert not (tmp_path / "generated.py").exists()


def test_provider_auth_failure_has_structured_error_and_no_retry(tmp_path, endpoint):
    result = invoke(tmp_path, endpoint, "run", "fail", "--format", "json")
    assert result.returncode == 1
    output = json.loads(result.stdout)
    assert output["status"] == "failed"
    assert "fixture unauthorized" in output["error"]
    assert len(endpoint[1]) == 1


def test_empty_prompt_is_invalid_input_before_provider_call(tmp_path, endpoint):
    result = invoke(tmp_path, endpoint, "run", "", "--format", "json")
    assert result.returncode == 2
    assert json.loads(result.stdout)["status"] == "invalid_input"
    assert not endpoint[1]


def test_scripted_human_loop_clear_add_and_multiple_turns(tmp_path, endpoint):
    (tmp_path / "notes.md").write_text("explicit context")
    result = invoke(tmp_path, endpoint, "chat", input_text="hello\n/clear\n/add notes.md\nagain\n/quit\n")
    assert result.returncode == 0, result.stderr
    assert "Reply: hello" in result.stdout
    assert "Reply: again" in result.stdout
    history = endpoint[1][-1]["messages"]
    assert [message["role"] for message in history] == ["system", "user", "user"]
    assert "explicit context" in history[1]["content"]


def test_human_undo_uses_shared_journal(tmp_path, endpoint):
    (tmp_path / "generated.py").write_text("user original")
    result = invoke(tmp_path, endpoint, "chat", "--permission", "trusted", input_text="write\n/undo\n/quit\n")
    assert result.returncode == 0, result.stderr
    assert "Restored the last agent edit" in result.stdout
    assert (tmp_path / "generated.py").read_text() == "user original"


def test_per_run_provider_overrides_do_not_persist(tmp_path, endpoint):
    state = tmp_path / "app-state"
    state.mkdir()
    original = {"model": "stored-model", "base_url": "http://localhost:1/v1", "api_keys": {},
                "sub_agents": [], "config_version": 2}
    (state / "config.json").write_text(json.dumps(original))
    result = invoke(tmp_path, endpoint, "run", "hello", "--format", "json")
    assert result.returncode == 0, result.stderr
    saved = json.loads((state / "config.json").read_text())
    assert saved["model"] == "stored-model"
    assert saved["base_url"] == "http://localhost:1/v1"


def test_default_tui_dependency_failure_is_actionable(monkeypatch, capsys):
    import builtins
    from mythic_agent.cli import main
    original = builtins.__import__
    def importing(name, *args, **kwargs):
        if name == "ui.main_app":
            raise ModuleNotFoundError("No textual", name="textual")
        return original(name, *args, **kwargs)
    monkeypatch.setattr(builtins, "__import__", importing)
    assert main([]) == 2
    assert "tui extra" in capsys.readouterr().err


def test_captured_stderr_prevents_inherited_console_approval(monkeypatch):
    from unittest.mock import Mock
    from mythic_agent.terminal import _approve
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(sys.stderr, "isatty", lambda: False)
    approval_input = Mock()
    monkeypatch.setattr("builtins.input", approval_input)
    assert _approve("write_file", {}) is False
    approval_input.assert_not_called()


def test_approval_eof_is_a_recorded_denial(monkeypatch):
    from unittest.mock import Mock
    from mythic_agent.core.policy import ToolPolicy
    from mythic_agent.terminal import _approve
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(sys.stderr, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", Mock(side_effect=EOFError))
    policy = ToolPolicy("ask", _approve)
    assert policy.authorize("write_file", {}) is False
    assert policy.denials == ["write_file"]
