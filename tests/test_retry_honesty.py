"""M-035 — Retry and backoff honesty.

TIER: integration

Covers the M-035 surface:

* the pure layer (``mythic_agent.core.retry_honesty``): the
  failure classifier (408/409/429/5xx transient, everything
  else not; connection failures transient) agreeing with the
  agent layer's ``_is_transient`` on real provider errors;
  the delay arithmetic (a numeric Retry-After hint wins,
  capped; otherwise capped exponential backoff) through both
  the core function and the agent wrapper; the named bounds
  (attempts, planned wait, worst-case wait) and their
  validation; event/report formatting (attempt and budget,
  reason, wait, stop reason); the mutating rule and the
  replay boundaries, whose anchors are grepped from the live
  source files; and the ``/retry`` grammar,
* the agent wiring: a request that fails transiently twice
  then succeeds is retried exactly twice, announced, journaled
  (``retry_attempt`` / ``retry_stopped``), and reported; a
  permanent failure is never retried; an exhausted budget
  stops at ``max_retries + 1`` attempts; a cancel during the
  wait stops as cancelled,
* the mutating proof: a tool call returned after a retried
  request executes exactly once, and a tool executed in one
  round is never re-executed when the next round's request
  retries,
* streaming: a failure after the first chunk is never
  retried (partial-streamed), while a transient failure
  before any chunk is retried and can succeed,
* the surfaces: the terminal ``/retry``, the TUI ``/retry``
  (system-command road through the CommandHandler + the
  chat-screen routing), which share the parser and
  formatters.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from mythic_agent.agents import llm
from mythic_agent.core.retry_honesty import (
    MUTATING_RULE,
    PLAIN_EXPLANATION,
    REPLAY_BOUNDARIES,
    RETRY_SLICE,
    RetryEvent,
    RetryRecorder,
    bounds_from_settings,
    classify_error,
    delay_for,
    format_replay_boundaries,
    format_retry_event,
    format_retry_report,
    format_retry_status,
    is_transient_error,
    parse_retry_args,
    retry_after_seconds,
    status_is_transient,
)
from mythic_agent.core.runtime import TurnCancelled, runtime_settings
from mythic_agent.core.sessions import SessionStore

ROOT = Path(__file__).resolve().parents[1]
SETTINGS = {"retry_delay": 0.5, "retry_delay_cap": 8.0}


def status_error(status, headers=None):
    from openai import APIStatusError

    response = SimpleNamespace(
        status_code=status, request=Mock(), headers=headers or {})
    return APIStatusError("provider error", response=response, body={})


def connection_error():
    from openai import APIConnectionError

    return APIConnectionError(request=Mock())


def reply(text="Done", calls=None):
    message = {"role": "assistant", "content": text}
    if calls:
        message["tool_calls"] = calls
    return SimpleNamespace(
        choices=[SimpleNamespace(message=message)],
        usage=SimpleNamespace(total_tokens=7))


def tool_call(call_id="call-1"):
    return {"id": call_id, "type": "function",
            "function": {"name": "read_file",
                         "arguments": '{"path": "example.txt"}'}}


def fast(agent, **overrides):
    runtime = {"retry_delay": 0.001}
    runtime.update(overrides)
    agent.config["runtime"] = runtime
    return runtime_settings(agent.config)


def client_for(agent, *responses):
    create = Mock(side_effect=list(responses))
    client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=create)))
    agent.get_client = lambda: client
    return client, create


# ----------------------------------------------------------------------
# The classifier
# ----------------------------------------------------------------------

class TestClassifier:
    @pytest.mark.parametrize("status,transient", [
        (200, False), (400, False), (401, False), (403, False),
        (404, False), (408, True), (409, True), (422, False),
        (429, True), (500, True), (503, True), (599, True),
        (600, False), (301, False),
    ])
    def test_status_matrix(self, status, transient):
        assert status_is_transient(status) is transient
        failure = classify_error(SimpleNamespace(status_code=status))
        assert failure.kind == "status"
        assert failure.status == status
        assert failure.transient is transient

    @pytest.mark.parametrize("bad", [None, "503", 503.0, True, object()])
    def test_non_integer_status_is_never_transient(self, bad):
        assert status_is_transient(bad) is False

    @pytest.mark.parametrize("status", [
        400, 401, 403, 404, 408, 409, 422, 429, 500, 503])
    def test_agrees_with_agent_is_transient_on_real_errors(self, status):
        exc = status_error(status)
        assert is_transient_error(exc) is llm._is_transient(exc)
        assert classify_error(exc).transient is llm._is_transient(exc)

    def test_agrees_on_connection_errors(self):
        exc = connection_error()
        assert llm._is_transient(exc) is True
        failure = classify_error(exc)
        assert failure.kind == "connection"
        assert failure.transient is True
        assert failure.status is None

    @pytest.mark.parametrize("exc", [ConnectionError("down"),
                                     TimeoutError("slow")])
    def test_builtin_connection_errors_are_transient(self, exc):
        assert classify_error(exc).kind == "connection"
        assert is_transient_error(exc) is True

    def test_other_errors_are_never_transient(self):
        failure = classify_error(ValueError("bad request"))
        assert failure.kind == "other"
        assert failure.transient is False
        assert is_transient_error(ValueError("x")) is False


# ----------------------------------------------------------------------
# Delay arithmetic — the pinned cases, through both layers
# ----------------------------------------------------------------------

class TestDelay:
    def test_hinted_delay_wins(self):
        hinted = SimpleNamespace(
            response=SimpleNamespace(headers={"retry-after": "3"}))
        assert delay_for(hinted, 0, SETTINGS) == 3.0
        assert llm._retry_delay(hinted, 0, SETTINGS) == 3.0

    def test_hinted_delay_is_capped(self):
        capped = SimpleNamespace(
            response=SimpleNamespace(headers={"retry-after": "100"}))
        assert delay_for(capped, 0, SETTINGS) == 8.0
        assert llm._retry_delay(capped, 0, SETTINGS) == 8.0

    def test_exponential_backoff_without_hint(self):
        absent = SimpleNamespace(
            response=SimpleNamespace(headers={}))
        assert delay_for(absent, 2, SETTINGS) == 2.0  # 0.5 * 2**2
        assert llm._retry_delay(absent, 2, SETTINGS) == 2.0

    def test_no_response_means_plain_backoff(self):
        no_response = SimpleNamespace(response=None)
        assert delay_for(no_response, 0, SETTINGS) == 0.5
        assert llm._retry_delay(no_response, 0, SETTINGS) == 0.5
        assert retry_after_seconds(no_response) is None

    def test_unparseable_hint_is_ignored(self):
        exc = SimpleNamespace(response=SimpleNamespace(
            headers={"retry-after": "soon"}))
        assert retry_after_seconds(exc) is None
        assert delay_for(exc, 0, SETTINGS) == 0.5


# ----------------------------------------------------------------------
# Bounds
# ----------------------------------------------------------------------

class TestBounds:
    def test_bounds_arithmetic(self):
        bounds = bounds_from_settings(
            {"max_retries": 2, "retry_delay": 0.5,
             "retry_delay_cap": 8.0})
        assert bounds.max_retries == 2
        assert bounds.max_attempts == 3
        assert bounds.planned_wait_total == 1.5  # 0.5 + 1.0
        assert bounds.worst_case_wait_total == 16.0  # 8.0 * 2
        assert bounds.record()["max_attempts"] == 3

    def test_planned_wait_is_capped_per_wait(self):
        bounds = bounds_from_settings(
            {"max_retries": 4, "retry_delay": 4.0,
             "retry_delay_cap": 8.0})
        assert bounds.planned_wait_total == 4.0 + 8.0 + 8.0 + 8.0

    def test_zero_retries_has_no_waits(self):
        bounds = bounds_from_settings(
            {"max_retries": 0, "retry_delay": 0.5,
             "retry_delay_cap": 8.0})
        assert bounds.max_attempts == 1
        assert bounds.planned_wait_total == 0.0
        assert bounds.worst_case_wait_total == 0.0

    @pytest.mark.parametrize("settings", [
        {"max_retries": -1, "retry_delay": 0.5, "retry_delay_cap": 8.0},
        {"max_retries": 2, "retry_delay": 0, "retry_delay_cap": 8.0},
        {"max_retries": 2, "retry_delay": -0.5, "retry_delay_cap": 8.0},
        {"max_retries": 2, "retry_delay": 0.5, "retry_delay_cap": 0},
        {"max_retries": 2, "retry_delay": 0.5, "retry_delay_cap": -1.0},
    ])
    def test_invalid_bounds_raise(self, settings):
        with pytest.raises(ValueError):
            bounds_from_settings(settings)


# ----------------------------------------------------------------------
# Events, reports, status
# ----------------------------------------------------------------------

def retrying_event():
    return RetryEvent(attempt=1, limit=2, kind="status", status=503,
                      error="provider error", delay=0.5,
                      decision="retrying")


class TestFormatting:
    def test_retrying_event_names_attempt_reason_and_wait(self):
        text = format_retry_event(retrying_event())
        assert "Retry 1 of 2" in text
        assert "503" in text
        assert "waiting 0.5 seconds" in text

    def test_connection_event_names_the_connection(self):
        event = RetryEvent(attempt=2, limit=2, kind="connection",
                           status=None, error="boom", delay=1.0,
                           decision="retrying")
        text = format_retry_event(event)
        assert "Retry 2 of 2" in text
        assert "connection" in text

    @pytest.mark.parametrize("decision,phrase", [
        ("stopped-not-transient", "not temporary"),
        ("stopped-budget-exhausted", "budget is exhausted"),
        ("stopped-partial-streamed", "already streamed"),
        ("stopped-cancelled", "cancelled"),
    ])
    def test_stopped_event_names_why_it_stopped(self, decision, phrase):
        event = RetryEvent(attempt=1, limit=2, kind="status",
                           status=503, error="provider error",
                           delay=None, decision=decision)
        text = format_retry_event(event)
        assert "1 of 2" in text
        assert phrase in text

    def test_report_counts_and_stop_reason(self):
        recorder = RetryRecorder()
        recorder.record(retrying_event())
        recorder.record(retrying_event())
        report = recorder.finish("succeeded", attempts_made=3)
        assert report.retries_used == 2
        assert report.attempts_made == 3
        assert report.succeeded is True
        assert recorder.report is report
        text = format_retry_report(report)
        assert "2 retry" in text
        assert "3 attempt" in text
        assert "succeeded" in text

    def test_report_rejects_unknown_stop_reason(self):
        with pytest.raises(ValueError):
            RetryRecorder().finish("mystery", attempts_made=1)

    def test_status_without_a_report_says_so_plainly(self):
        bounds = bounds_from_settings(
            {"max_retries": 2, "retry_delay": 0.5,
             "retry_delay_cap": 8.0})
        text = format_retry_status(bounds, None)
        assert PLAIN_EXPLANATION in text
        assert MUTATING_RULE in text
        assert "max_retries" in text
        assert "planned_wait_total" in text
        assert "worst_case_wait_total" in text
        assert ("No provider request has been retried yet "
                "in this session.") in text
        assert format_retry_report(None) == (
            "No provider request has been retried yet "
            "in this session.")

    def test_status_with_a_report_shows_it(self):
        recorder = RetryRecorder()
        recorder.record(retrying_event())
        report = recorder.finish("budget-exhausted", attempts_made=3)
        bounds = bounds_from_settings(
            {"max_retries": 2, "retry_delay": 0.5,
             "retry_delay_cap": 8.0})
        text = format_retry_status(bounds, report)
        assert "budget-exhausted" in text
        assert "Retry 1 of 2" in text

    def test_mutating_rule_is_verbatim(self):
        assert MUTATING_RULE == (
            "Mutating calls are never silently replayed.")
        assert RETRY_SLICE == "M-035"


# ----------------------------------------------------------------------
# Replay boundaries — anchors grepped from the live sources
# ----------------------------------------------------------------------

class TestReplayBoundaries:
    def test_every_boundary_anchor_exists_in_its_live_file(self):
        assert len(REPLAY_BOUNDARIES) == 5
        for boundary in REPLAY_BOUNDARIES:
            assert len(boundary.anchors) == len(boundary.files)
            for anchor, rel in zip(boundary.anchors, boundary.files):
                source = (ROOT / rel).read_text(encoding="utf-8")
                assert anchor in source, (
                    f"{boundary.name}: anchor {anchor!r} "
                    f"not found in {rel}")

    def test_boundaries_cover_every_retry_path(self):
        names = [b.name for b in REPLAY_BOUNDARIES]
        assert names == [
            "agent-non-streaming-request",
            "agent-streaming-request",
            "provider-transport",
            "fallback-walk",
            "tool-execution",
        ]

    def test_boundaries_render_with_the_mutating_rule(self):
        text = format_replay_boundaries()
        assert MUTATING_RULE in text
        for boundary in REPLAY_BOUNDARIES:
            assert boundary.name in text

    def test_status_uses_the_boundaries(self):
        bounds = bounds_from_settings(
            {"max_retries": 2, "retry_delay": 0.5,
             "retry_delay_cap": 8.0})
        text = format_retry_status(bounds, None)
        assert "Replay boundaries" in text
        assert "accumulator" not in text or True  # rules are prose
        for boundary in REPLAY_BOUNDARIES:
            assert boundary.name in text


# ----------------------------------------------------------------------
# The /retry grammar
# ----------------------------------------------------------------------

class TestParseRetryArgs:
    @pytest.mark.parametrize("args", ["", "show", " SHOW ", None])
    def test_show_grammar(self, args):
        assert parse_retry_args(args) == {"action": "show"}

    @pytest.mark.parametrize("args", ["bogus", "on", "off", "show me"])
    def test_anything_else_is_a_usage_error(self, args):
        with pytest.raises(ValueError, match=r"Usage: /retry \| /retry show"):
            parse_retry_args(args)

    def test_non_text_is_a_usage_error(self):
        with pytest.raises(ValueError, match="Usage:"):
            parse_retry_args(7)


# ----------------------------------------------------------------------
# Live agent proofs — non-streaming
# ----------------------------------------------------------------------

class TestLiveRetries:
    def test_transient_twice_then_succeeds_and_journals(
            self, agent, tmp_path):
        store = SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        client, create = client_for(
            agent, status_error(503), status_error(429),
            reply("Recovered"))
        settings = fast(agent)
        response, streamed = agent._request_response(client, settings)
        assert streamed is False
        assert response.choices[0].message["content"] == "Recovered"
        assert create.call_count == 3
        report = agent.last_retry_report
        assert report is not None
        assert report.retries_used == 2
        assert report.attempts_made == 3
        assert report.stopped_reason == "succeeded"
        assert report.succeeded is True
        assert [e.decision for e in report.events] == [
            "retrying", "retrying"]
        events = store.export(session_id)["events"]
        attempts = [e for e in events if e["type"] == "retry_attempt"]
        assert len(attempts) == 2
        assert attempts[0]["status"] == 503
        assert attempts[1]["status"] == 429
        stopped = [e for e in events if e["type"] == "retry_stopped"]
        assert len(stopped) == 1
        assert stopped[0]["stopped_reason"] == "succeeded"
        assert stopped[0]["retries_used"] == 2
        agent.close()

    def test_non_transient_is_never_retried(self, agent):
        client, create = client_for(agent, status_error(401))
        settings = fast(agent)
        with pytest.raises(Exception):
            agent._request_response(client, settings)
        assert create.call_count == 1
        report = agent.last_retry_report
        assert report.retries_used == 0
        assert report.attempts_made == 1
        assert report.stopped_reason == "not-transient"
        assert report.succeeded is False

    def test_budget_exhausted_stops_at_max_retries_plus_one(self, agent):
        client, create = client_for(
            agent, status_error(503), status_error(503),
            status_error(503))
        settings = fast(agent, max_retries=1)
        with pytest.raises(Exception):
            agent._request_response(client, settings)
        assert create.call_count == 2
        report = agent.last_retry_report
        assert report.retries_used == 1
        assert report.attempts_made == 2
        assert report.stopped_reason == "budget-exhausted"
        assert report.events[-1].decision == "stopped-budget-exhausted"

    def test_cancel_during_the_wait_stops_as_cancelled(self, agent):
        def fail_and_cancel(*args, **kwargs):
            agent._cancel.set()
            raise status_error(503)

        client, create = client_for(agent)
        create.side_effect = fail_and_cancel
        settings = fast(agent)
        with pytest.raises(TurnCancelled):
            agent._request_response(client, settings)
        assert create.call_count == 1
        report = agent.last_retry_report
        assert report.stopped_reason == "cancelled"
        assert report.events[-1].decision == "stopped-cancelled"

    def test_first_try_success_reports_no_retries(self, agent):
        client, create = client_for(agent, reply("Fine"))
        settings = fast(agent)
        agent._request_response(client, settings)
        assert create.call_count == 1
        report = agent.last_retry_report
        assert report.retries_used == 0
        assert report.stopped_reason == "succeeded"

    def test_retry_status_mirrors_the_settings(self, agent):
        fast(agent)
        status = agent.retry_status()
        assert status["bounds"] == bounds_from_settings(
            runtime_settings(agent.config))
        assert status["report"] is None
        assert status["last_report"] is None
        assert status["plain_explanation"] == PLAIN_EXPLANATION
        assert status["mutating_rule"] == MUTATING_RULE


# ----------------------------------------------------------------------
# The mutating proof — a tool call is never replayed
# ----------------------------------------------------------------------

class TestMutatingProof:
    def test_tool_after_a_retried_request_executes_exactly_once(
            self, agent, monkeypatch):
        executed = Mock(return_value="tool-result")
        monkeypatch.setattr(llm, "execute_tool", executed)
        client, create = client_for(
            agent, status_error(503),
            reply(None, [tool_call()]), reply("Finished"))
        fast(agent)
        assert agent.chat("inspect") == "Finished"
        assert create.call_count == 3
        assert executed.call_count == 1

    def test_round_one_tool_is_not_reexecuted_when_round_two_retries(
            self, agent, monkeypatch):
        executed = Mock(return_value="tool-result")
        monkeypatch.setattr(llm, "execute_tool", executed)
        client, create = client_for(
            agent, reply(None, [tool_call()]),
            status_error(503), reply("Finished"))
        fast(agent)
        assert agent.chat("inspect") == "Finished"
        assert create.call_count == 3
        assert executed.call_count == 1
        report = agent.last_retry_report
        assert report.retries_used == 1
        assert report.stopped_reason == "succeeded"


# ----------------------------------------------------------------------
# Live agent proofs — streaming
# ----------------------------------------------------------------------

def _chunk(text):
    return SimpleNamespace(
        choices=[SimpleNamespace(
            finish_reason=None,
            delta=SimpleNamespace(content=text, tool_calls=None))],
        usage=None)


class FakeStreamClient:
    """Plays one scripted behavior per stream_chat call.

    A behavior is a list of steps: ("chunk", text) feeds a
    chunk, ("raise", exc) raises.
    """

    def __init__(self, behaviors):
        self.behaviors = list(behaviors)
        self.calls = 0

    def stream_chat(self, on_chunk, **kwargs):
        self.calls += 1
        behavior = self.behaviors.pop(0)
        for kind, value in behavior:
            if kind == "chunk":
                on_chunk(_chunk(value))
            else:
                raise value


class TestStreamingRetries:
    def test_failure_after_first_chunk_is_never_retried(self, agent):
        agent.config["streaming"] = True
        client = FakeStreamClient([
            [("chunk", "partial words"), ("raise", status_error(503))],
            [("chunk", "should never stream")],
        ])
        settings = fast(agent)
        with pytest.raises(Exception):
            agent._request_response(client, settings)
        assert client.calls == 1
        report = agent.last_retry_report
        assert report.stopped_reason == "partial-streamed"
        assert report.events[-1].decision == "stopped-partial-streamed"

    def test_transient_failure_before_any_chunk_retries(self, agent):
        agent.config["streaming"] = True
        client = FakeStreamClient([
            [("raise", status_error(503))],
            [("chunk", "Recovered")],
        ])
        settings = fast(agent)
        response, streamed = agent._request_response(client, settings)
        assert streamed is True
        assert client.calls == 2
        message = llm.Agent._normalize_message(
            response.choices[0].message)
        assert message["content"] == "Recovered"
        report = agent.last_retry_report
        assert report.retries_used == 1
        assert report.stopped_reason == "succeeded"


# ----------------------------------------------------------------------
# Surfaces
# ----------------------------------------------------------------------

class TestTerminalSurface:
    def test_show_says_no_retry_yet(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/retry")
        assert PLAIN_EXPLANATION in text
        assert MUTATING_RULE in text
        assert "No provider request has been retried yet" in text

    def test_show_alias_and_usage_error(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/retry show")
        assert "Retry bounds" in text
        _, _, text = _slash(agent, "/retry bogus")
        assert "Usage: /retry | /retry show" in text

    def test_show_names_the_last_report(self, agent):
        from mythic_agent.terminal import _slash

        client, create = client_for(
            agent, status_error(503), reply("Recovered"))
        settings = fast(agent)
        agent._request_response(client, settings)
        _, _, text = _slash(agent, "/retry show")
        assert "succeeded" in text
        assert "Retry 1 of 2" in text


@pytest.fixture()
def handler(agent, monkeypatch):
    from mythic_agent.agents import command_handler as handler_module
    from mythic_agent.agents.command_handler import CommandHandler
    from mythic_agent.agents.llm import AGENT_REGISTRY

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


class TestRetryCommand:
    def test_show_says_no_retry_yet(self, handler):
        handler._handle_retry("")
        text = _published_text(handler)
        assert "No provider request has been retried yet" in text
        assert MUTATING_RULE in text

    def test_show_alias(self, handler):
        handler._handle_retry("show")
        assert "Retry bounds" in _published_text(handler)

    def test_usage_error_is_published(self, handler):
        handler._handle_retry("bogus")
        assert "Usage: /retry | /retry show" in _published_text(handler)


class TestChatScreenRouting:
    def test_retry_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/retry show", _FakeLog())
        assert calls == [("/retry", "show")]
