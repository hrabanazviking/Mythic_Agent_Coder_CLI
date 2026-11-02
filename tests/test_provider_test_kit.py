"""M-041 — New-provider test kit.

TIER: integration

Covers the M-041 surface:

* the kit layer (``mythic_agent.core.provider_test_kit``):
  five checks in roadmap order (registry, chat, tools,
  streaming, errors) proven against a door through the
  M-020 universal adapter, with the evidence stated plainly
  per check,
* the honesty rules: a check a door does not claim (its
  registry capabilities say no) is skipped with the reason,
  never passed; a non-compatible dialect is NOT PROVEN,
  never passed; the verdict is passed only when nothing
  failed and chat actually ran; no key value ever rides a
  check detail, a record, or a formatted line,
* the real wire proof: a loopback OpenAI-compatible door
  (chat, forced tool call, SSE streaming, a malformed
  request answered with an HTTP error) passes the whole kit
  through the default urllib wire,
* the surfaces: the conformance script
  (``scripts/provider_test_kit.py``), the ``mythic testkit``
  CLI subcommand, ``Agent.test_kit()``, and ``/testkit`` on
  the terminal + TUI system-command roads sharing one
  parser + formatter.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from mythic_agent.core.provider_registry import load_registry
from mythic_agent.core.provider_test_kit import (
    CHECKS,
    KIT_SLICE,
    KIT_TOOL,
    PLAIN_EXPLANATION,
    VERDICTS,
    format_kit_status,
    parse_kit_args,
    run_kit,
)
from mythic_agent.resources import load_resource

SENTINEL = "sk-kit-sentinel-12345"

MESSAGES_OK = {"choices": [{"message": {"content": "kit ok"}}]}


def _wire(*, chat_status=200, chat_body=None, malformed_status=400,
          tool_calls=True, echo_key=False):
    """Fake wire seams: (post_json, post_lines, calls)."""
    calls = []

    def post_json(url, headers, payload, timeout):
        calls.append(("json", url, dict(headers), payload))
        if payload.get("messages") == []:
            body = {"error": {"message": "messages must not be empty"}}
            if echo_key:
                body["error"]["message"] += f" (key {SENTINEL})"
            return malformed_status, json.dumps(body)
        if "tools" in payload:
            message = {"content": "", "tool_calls": [{
                "id": "kit-call", "type": "function",
                "function": {"name": KIT_TOOL,
                             "arguments": json.dumps({"word": "ok"})},
            }]} if tool_calls else {"content": "no tools here"}
            return 200, json.dumps({"choices": [{"message": message}]})
        body = chat_body if chat_body is not None else MESSAGES_OK
        return chat_status, json.dumps(body)

    def post_lines(url, headers, payload, timeout):
        calls.append(("lines", url, dict(headers), payload))
        return 200, [
            'data: {"choices": [{"delta": {"content": "kit "}}]}\n',
            'data: {"choices": [{"delta": {"content": "ok"}, '
            '"finish_reason": "stop"}]}\n',
            "data: [DONE]\n",
        ]

    post_json.calls = calls
    return post_json, post_lines, calls


def _run(name="openai", wire=None, **kwargs):
    post_json, post_lines, _ = wire or _wire()
    kwargs.setdefault("environ", {})
    kwargs.setdefault("api_key", SENTINEL)
    return run_kit(name, post_json=post_json, post_lines=post_lines,
                   **kwargs)


def _checks(report):
    return {c.name: c for c in report.checks}


# ----------------------------------------------------------------------
# The kit — checks, verdict, honesty
# ----------------------------------------------------------------------

class TestKit:
    def test_vocabulary_is_the_roadmap_kit(self):
        assert KIT_SLICE == "M-041"
        assert CHECKS == ("registry", "chat", "tools", "streaming",
                          "errors")
        assert VERDICTS == ("passed", "failed", "not-proven")
        assert KIT_TOOL == "kit_echo"
        assert "NOT PROVEN" in PLAIN_EXPLANATION

    def test_a_conforming_door_passes_every_check(self):
        report = _run()
        assert report.verdict == "passed"
        assert [c.name for c in report.checks] == list(CHECKS)
        assert all(c.status == "passed" for c in report.checks)
        assert report.summary() == {"passed": 5, "failed": 0,
                                     "skipped": 0}
        record = report.record()
        assert record["slice"] == "M-041"
        assert record["provider"] == "openai"
        assert record["verdict"] == "passed"

    def test_alias_resolves_and_the_forced_tool_is_the_kit_tool(self):
        post_json, post_lines, calls = _wire()
        report = run_kit("gpt", environ={}, api_key=SENTINEL,
                         post_json=post_json, post_lines=post_lines)
        assert report.provider == "openai"
        tool_payloads = [p for kind, _, _, p in calls
                         if kind == "json" and "tools" in p]
        assert tool_payloads
        assert tool_payloads[0]["tool_choice"] == {
            "type": "function", "function": {"name": KIT_TOOL}}

    def test_unknown_provider_stays_unknown(self):
        with pytest.raises(KeyError):
            _run("no-such-door")

    def test_chat_failure_fails_the_verdict(self):
        report = _run(wire=_wire(chat_status=500,
                                 chat_body={"error": {"message": "boom"}}))
        assert _checks(report)["chat"].status == "failed"
        assert report.verdict == "failed"

    def test_a_door_that_never_calls_the_tool_fails_tools(self):
        report = _run(wire=_wire(tool_calls=False))
        assert _checks(report)["tools"].status == "failed"
        assert "no kit_echo call" in _checks(report)["tools"].detail
        assert report.verdict == "failed"

    def test_a_malformed_request_answered_with_success_fails_errors(self):
        report = _run(wire=_wire(malformed_status=200))
        # The 200 malformed answer also carries no choices, so the
        # wire half is what the detail names.
        assert _checks(report)["errors"].status == "failed"
        assert "HTTP 200" in _checks(report)["errors"].detail
        assert report.verdict == "failed"

    def test_no_key_value_rides_the_report(self):
        report = _run(wire=_wire(echo_key=True, chat_body={
            "choices": [{"message": {"content": f"echo {SENTINEL}"}}]}))
        assert report.verdict == "passed"
        assert SENTINEL not in json.dumps(report.record())
        text = format_kit_status({"report": report.record()})
        assert SENTINEL not in text
        assert "***REDACTED***" in _checks(report)["chat"].detail


class TestHonesty:
    def test_native_dialect_is_not_proven_never_passed(self):
        report = _run("anthropic")
        assert report.verdict == "not-proven"
        checks = _checks(report)
        assert checks["registry"].status == "passed"
        for name in ("chat", "tools", "streaming", "errors"):
            assert checks[name].status == "skipped"
            assert "NOT PROVEN" in checks[name].detail
        assert report.summary() == {"passed": 1, "failed": 0,
                                    "skipped": 4}

    def test_ollama_native_is_not_proven_too(self):
        report = _run("ollama")
        assert report.verdict == "not-proven"
        assert _checks(report)["chat"].status == "skipped"

    def test_unclaimed_capabilities_are_skipped_with_the_reason(self):
        data = copy.deepcopy(load_resource("provider_registry.yaml"))
        for entry in data["providers"]:
            if entry["name"] == "openai":
                entry["capabilities"]["tool_calling"] = False
                entry["capabilities"]["streaming"] = False
        registry = load_registry(data)
        report = _run(registry=registry)
        checks = _checks(report)
        assert checks["tools"].status == "skipped"
        assert "declares tool_calling: no" in checks["tools"].detail
        assert checks["streaming"].status == "skipped"
        assert "declares streaming: no" in checks["streaming"].detail
        # Chat was still proven, so the verdict is honestly passed
        # with the skips named in the summary.
        assert report.verdict == "passed"
        assert report.summary() == {"passed": 3, "failed": 0,
                                     "skipped": 2}


# ----------------------------------------------------------------------
# Parser + formatter
# ----------------------------------------------------------------------

class TestSurfaceText:
    def test_parser_names_the_door_and_optional_url(self):
        assert parse_kit_args("openai") == {
            "action": "run", "provider": "openai", "base_url": None}
        assert parse_kit_args("openai http://127.0.0.1:9/v1") == {
            "action": "run", "provider": "openai",
            "base_url": "http://127.0.0.1:9/v1"}
        for bad in ("", "  ", "a b c"):
            with pytest.raises(ValueError, match="Usage: /testkit"):
                parse_kit_args(bad)

    def test_format_carries_every_check_and_the_verdict(self):
        report = _run()
        text = format_kit_status({"report": report.record()})
        assert "verdict: passed" in text
        for name in CHECKS:
            assert f"{name}: passed" in text
        assert PLAIN_EXPLANATION in text


# ----------------------------------------------------------------------
# The real wire proof — a loopback door through the default wire
# ----------------------------------------------------------------------

class _DoorHandler(BaseHTTPRequestHandler):
    """A minimal conforming OpenAI-compatible door."""

    def do_POST(self):  # noqa: N802 - BaseHTTPRequestHandler's name
        length = int(self.headers.get("Content-Length") or 0)
        payload = json.loads(self.rfile.read(length) if length else b"{}")
        if payload.get("messages") == []:
            return self._reply(400, {"error": {
                "message": "messages must not be empty"}})
        if payload.get("stream"):
            lines = [
                'data: {"choices": [{"delta": {"content": "loop "}}]}',
                'data: {"choices": [{"delta": {"content": "ok"}, '
                '"finish_reason": "stop"}]}',
                "data: [DONE]",
                "",
            ]
            raw = "\n".join(lines).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        if "tools" in payload:
            message = {"content": "", "tool_calls": [{
                "id": "door-call", "type": "function",
                "function": {"name": KIT_TOOL,
                             "arguments": json.dumps({"word": "ok"})}}]}
        else:
            message = {"content": "loopback ok"}
        return self._reply(200, {"choices": [{"message": message}]})

    def _reply(self, status, body):
        raw = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *args):  # keep the test output clean
        pass


@pytest.fixture()
def door():
    server = ThreadingHTTPServer(("127.0.0.1", 0), _DoorHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}/v1"
    server.shutdown()
    thread.join(timeout=5)


class TestLoopbackDoor:
    def test_the_whole_kit_passes_over_real_http(self, door):
        report = run_kit("openai", base_url=door, api_key=SENTINEL,
                         environ={})
        assert report.verdict == "passed", report.record()
        assert all(c.status == "passed" for c in report.checks)
        assert SENTINEL not in json.dumps(report.record())

    def test_cli_passes_the_door_and_rejects_unknown(
            self, door, monkeypatch, capsys):
        from mythic_agent.cli import main

        monkeypatch.setenv("OPENAI_API_KEY", SENTINEL)
        assert main(["testkit", "openai", "--base-url", door,
                     "--json"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["verdict"] == "passed"
        assert payload["checks"][1]["name"] == "chat"
        assert main(["testkit", "no-such-door"]) == 2

    def test_script_passes_the_door(self, door, monkeypatch, capsys):
        monkeypatch.setenv("OPENAI_API_KEY", SENTINEL)
        script = Path(__file__).resolve().parent.parent / "scripts" / \
            "provider_test_kit.py"
        spec = importlib.util.spec_from_file_location(
            "provider_test_kit_script", script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert module.main(["openai", "--base-url", door]) == 0
        out = capsys.readouterr().out
        assert "verdict: passed" in out
        assert module.main(["no-such-door"]) == 2


# ----------------------------------------------------------------------
# The agent + the terminal/TUI roads
# ----------------------------------------------------------------------

@pytest.fixture()
def fake_wire(monkeypatch):
    from mythic_agent.core import provider_test_kit

    post_json, post_lines, calls = _wire()
    monkeypatch.setattr(provider_test_kit, "default_post_json", post_json)
    monkeypatch.setattr(provider_test_kit, "default_post_lines", post_lines)
    return calls


class TestAgent:
    def test_agent_report_matches_the_pure_kit(self, agent, fake_wire,
                                                monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", SENTINEL)
        status = agent.test_kit("openai")
        report = run_kit("openai", environ={},
                         **_wire_kwargs())
        assert status["report"]["verdict"] == \
            report.verdict == "passed"
        assert status["plain_explanation"] == PLAIN_EXPLANATION

    def test_agent_unknown_provider_raises(self, agent, fake_wire):
        with pytest.raises(KeyError):
            agent.test_kit("no-such-door")


def _wire_kwargs():
    post_json, post_lines, _ = _wire()
    return {"api_key": SENTINEL, "post_json": post_json,
            "post_lines": post_lines}


class TestTerminalSurface:
    def test_run_prints_the_verdict(self, agent, fake_wire, monkeypatch):
        from mythic_agent.terminal import _slash

        monkeypatch.setenv("OPENAI_API_KEY", SENTINEL)
        _, _, text = _slash(agent, "/testkit openai")
        assert "verdict: passed" in text
        assert PLAIN_EXPLANATION in text

    def test_usage_and_unknown_are_plain(self, agent, fake_wire):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/testkit")
        assert text.startswith("Usage: /testkit")
        _, _, text = _slash(agent, "/testkit no-such-door")
        assert "no provider" in text


@pytest.fixture()
def handler(agent, fake_wire, monkeypatch):
    from mythic_agent.agents import command_handler as handler_module
    from mythic_agent.agents.command_handler import CommandHandler
    from mythic_agent.agents.llm import AGENT_REGISTRY

    monkeypatch.setenv("OPENAI_API_KEY", SENTINEL)
    published = []
    monkeypatch.setattr(
        handler_module, "publish_sync",
        lambda event, **kwargs: published.append((event, kwargs)))
    AGENT_REGISTRY["Primary"] = agent
    instance = CommandHandler.__new__(CommandHandler)
    instance.published = published
    yield instance
    AGENT_REGISTRY.pop("Primary", None)


def _published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestTestkitCommand:
    def test_run_prints_the_verdict(self, handler):
        handler._handle_testkit("openai")
        text = _published_text(handler)
        assert "verdict: passed" in text
        assert PLAIN_EXPLANATION in text

    def test_usage_error_is_plain(self, handler):
        handler._handle_testkit("")
        assert "Usage: /testkit" in _published_text(handler)


class TestChatScreenRouting:
    def test_testkit_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/testkit openai", _FakeLog())
        assert calls == [("/testkit", "openai")]
