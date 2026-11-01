"""M-036 — Rate-limit weather.

TIER: integration

Covers the M-036 surface:

* the pure layer (``mythic_agent.core.rate_limit_weather``):
  the limit-header parser for the doors' real header
  families (OpenAI-style ``x-ratelimit-*`` and Anthropic-style
  ``anthropic-ratelimit-*``; durations, ISO timestamps, and
  epochs read exactly; unreadable values stay unknown), the
  signal builders (a 429 is limited; headers alone are a
  quota signal; anything else is no signal), the board
  (unknown stays unknown, remaining-0 is limited until the
  reset, an expired limit is over, a success clears a limit),
  the queue decision (wait within the named bound; proceed —
  with the reason stated — beyond it or when the reset is
  unknown), and the crew-work planner (ready/deferred,
  nothing dropped, order kept),
* the agent wiring: a live 429 is recorded on the crew's
  shared board and journaled once as ``rate_limit_seen``; a
  success clears the door's weather; a request for a door
  limited until a near known reset is queued (announced,
  journaled ``rate_limit_queued``, cancellable) and then
  sent; a far-off or unknown reset never parks the session,
* the surfaces: the terminal ``/weather``, the TUI
  ``/weather`` (system-command road through the
  CommandHandler + the chat-screen routing), which share
  the parser and formatters.
"""

from __future__ import annotations

import time
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from mythic_agent.core.rate_limit_weather import (
    PLAIN_EXPLANATION,
    QUEUE_MAX_WAIT_S,
    WEATHER_SLICE,
    LimitSignal,
    ProviderWeather,
    WeatherBoard,
    format_queue_plan,
    format_weather,
    format_weather_status,
    parse_duration_seconds,
    parse_limit_headers,
    parse_reset_value,
    parse_weather_args,
    plan_crew_work,
    queue_decision,
    shared_board,
    signal_from_error,
    signal_from_headers,
    weather_key_for,
)
from mythic_agent.core.runtime import TurnCancelled, runtime_settings
from mythic_agent.core.sessions import SessionStore

NOW = 1_800_000_000.0  # a fixed epoch for the pure-layer tests


@pytest.fixture(autouse=True)
def clean_shared_board():
    board = shared_board()
    board.reset()
    yield board
    board.reset()


def status_error(status, headers=None):
    from openai import APIStatusError

    response = SimpleNamespace(
        status_code=status, request=Mock(), headers=headers or {})
    return APIStatusError("provider error", response=response, body={})


def reply(text="Done"):
    message = {"role": "assistant", "content": text}
    return SimpleNamespace(
        choices=[SimpleNamespace(message=message)],
        usage=SimpleNamespace(total_tokens=7))


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


def limited_signal(provider, *, at, until=None, after=None):
    return LimitSignal(
        provider=provider, kind="limited", observed_at=at,
        source="status-429", reset_at=until, retry_after_s=after)


# ----------------------------------------------------------------------
# Header parsing
# ----------------------------------------------------------------------

class TestHeaderParsing:
    def test_slice_and_explanation(self):
        assert WEATHER_SLICE == "M-036"
        assert "unknown" in PLAIN_EXPLANATION
        assert QUEUE_MAX_WAIT_S == 600.0

    def test_openai_family(self):
        fields = parse_limit_headers({
            "x-ratelimit-limit-requests": "100",
            "x-ratelimit-remaining-requests": "0",
            "x-ratelimit-reset-requests": "6m0s",
            "x-ratelimit-limit-tokens": "30000",
            "x-ratelimit-remaining-tokens": "12000",
            "x-ratelimit-reset-tokens": "1s",
        }, now=NOW)
        assert fields["limit_requests"] == 100
        assert fields["remaining_requests"] == 0
        assert fields["limit_tokens"] == 30000
        assert fields["remaining_tokens"] == 12000
        # The requests reset is read first (family order).
        assert fields["reset_at"] == NOW + 360.0

    def test_anthropic_family_and_iso_reset(self):
        fields = parse_limit_headers({
            "anthropic-ratelimit-requests-limit": "50",
            "anthropic-ratelimit-requests-remaining": "49",
            "anthropic-ratelimit-requests-reset":
                "2027-01-15T10:00:00Z",
        }, now=NOW)
        assert fields["limit_requests"] == 50
        assert fields["remaining_requests"] == 49
        assert fields["reset_at"] == parse_reset_value(
            "2027-01-15T10:00:00Z", now=NOW)

    def test_retry_after_numeric_only(self):
        fields = parse_limit_headers({"retry-after": "12"}, now=NOW)
        assert fields["retry_after_s"] == 12.0
        fields = parse_limit_headers(
            {"retry-after": "tomorrow-ish"}, now=NOW)
        assert fields["retry_after_s"] is None

    def test_unreadable_values_stay_unknown(self):
        fields = parse_limit_headers({
            "x-ratelimit-remaining-requests": "plenty",
            "x-ratelimit-reset-requests": "whenever",
        }, now=NOW)
        assert fields["remaining_requests"] is None
        assert fields["reset_at"] is None

    def test_no_headers_no_fields(self):
        fields = parse_limit_headers({}, now=NOW)
        assert all(value is None for value in fields.values())
        fields = parse_limit_headers(None, now=NOW)
        assert all(value is None for value in fields.values())

    @pytest.mark.parametrize("text,expected", [
        ("1s", 1.0), ("6m0s", 360.0), ("500ms", 0.5),
        ("1h30m", 5400.0), ("2m", 120.0),
    ])
    def test_durations(self, text, expected):
        assert parse_duration_seconds(text) == expected

    @pytest.mark.parametrize("text", ["", "soon", "10", "1x", "m0s"])
    def test_non_durations(self, text):
        assert parse_duration_seconds(text) is None

    def test_reset_epoch_and_small_number(self):
        assert parse_reset_value(1_900_000_000, now=NOW) == 1_900_000_000
        assert parse_reset_value("42", now=NOW) == NOW + 42.0
        assert parse_reset_value("never", now=NOW) is None


# ----------------------------------------------------------------------
# Signals
# ----------------------------------------------------------------------

class TestSignals:
    def test_429_is_a_limited_signal_with_its_headers(self):
        exc = status_error(429, {
            "x-ratelimit-remaining-requests": "0",
            "x-ratelimit-reset-requests": "30s",
            "retry-after": "30"})
        signal = signal_from_error(exc, "openai", now=NOW)
        assert signal is not None
        assert signal.kind == "limited"
        assert signal.source == "status-429"
        assert signal.remaining_requests == 0
        assert signal.reset_at == NOW + 30.0
        assert signal.retry_after_s == 30.0

    def test_non_429_without_headers_is_no_signal(self):
        assert signal_from_error(status_error(503), "openai",
                                 now=NOW) is None
        assert signal_from_error(status_error(401), "openai",
                                 now=NOW) is None

    def test_headers_on_another_status_are_a_quota_signal(self):
        exc = status_error(200, {"x-ratelimit-remaining-tokens": "9"})
        # A 200 never reaches the error path in life, but the
        # builder's rule is duck-typed and pinned here.
        signal = signal_from_error(exc, "openai", now=NOW)
        assert signal is not None and signal.kind == "quota"

    def test_headers_signal_none_when_nothing_said(self):
        assert signal_from_headers({}, "openai", now=NOW) is None
        signal = signal_from_headers(
            {"x-ratelimit-limit-requests": "10"}, "openai", now=NOW)
        assert signal is not None and signal.kind == "quota"
        assert signal.limit_requests == 10


# ----------------------------------------------------------------------
# The board
# ----------------------------------------------------------------------

class TestBoard:
    def test_unknown_stays_unknown(self):
        board = WeatherBoard(clock=lambda: NOW)
        weather = board.weather_for("never-seen", now=NOW)
        assert weather.state == "unknown"
        assert weather.is_limited(NOW) is False
        assert board.snapshot(now=NOW) == []

    def test_429_limits_until_the_reset(self):
        board = WeatherBoard(clock=lambda: NOW)
        board.record(limited_signal("openai", at=NOW, until=NOW + 60))
        weather = board.weather_for("openai", now=NOW)
        assert weather.state == "limited"
        assert weather.seconds_until_reset(NOW) == 60.0
        # After the reset the limit is honestly over.
        later = board.weather_for("openai", now=NOW + 61)
        assert later.effective_state(NOW + 61) == "clear"
        assert later.is_limited(NOW + 61) is False

    def test_429_without_a_reset_has_unknown_reset(self):
        board = WeatherBoard(clock=lambda: NOW)
        board.record(limited_signal("openai", at=NOW))
        weather = board.weather_for("openai", now=NOW)
        assert weather.state == "limited"
        assert weather.seconds_until_reset(NOW) is None

    def test_retry_after_sets_the_until(self):
        board = WeatherBoard(clock=lambda: NOW)
        board.record(limited_signal("openai", at=NOW, after=45))
        weather = board.weather_for("openai", now=NOW)
        assert weather.limited_until == NOW + 45

    def test_remaining_zero_headers_limit(self):
        board = WeatherBoard(clock=lambda: NOW)
        board.record_headers("openai", {
            "x-ratelimit-remaining-requests": "0",
            "x-ratelimit-reset-requests": "2m"}, now=NOW)
        weather = board.weather_for("openai", now=NOW)
        assert weather.state == "limited"
        assert weather.limited_until == NOW + 120

    def test_remaining_positive_headers_are_clear_with_quota(self):
        board = WeatherBoard(clock=lambda: NOW)
        board.record_headers("openai", {
            "x-ratelimit-limit-requests": "100",
            "x-ratelimit-remaining-requests": "87"}, now=NOW)
        weather = board.weather_for("openai", now=NOW)
        assert weather.state == "clear"
        assert weather.remaining_requests == 87
        assert weather.limit_requests == 100

    def test_success_clears_a_limit(self):
        board = WeatherBoard(clock=lambda: NOW)
        board.record(limited_signal("openai", at=NOW, until=NOW + 900))
        board.record_success("openai", now=NOW + 1)
        weather = board.weather_for("openai", now=NOW + 1)
        assert weather.state == "clear"
        assert weather.last_success_at == NOW + 1

    def test_record_error_and_validation(self):
        board = WeatherBoard(clock=lambda: NOW)
        weather = board.record_error(
            "openai", status_error(429, {"retry-after": "5"}), now=NOW)
        assert weather is not None and weather.state == "limited"
        assert board.record_error(
            "openai", status_error(400), now=NOW) is None
        with pytest.raises(ValueError):
            board.record(LimitSignal(
                provider="", kind="limited", observed_at=NOW,
                source="status-429"))
        with pytest.raises(ValueError):
            board.record(LimitSignal(
                provider="x", kind="guessed", observed_at=NOW,
                source="vibes"))


# ----------------------------------------------------------------------
# Queue decision + crew planner
# ----------------------------------------------------------------------

class TestQueueing:
    def test_clear_and_unknown_proceed(self):
        for state in ("clear", "unknown"):
            weather = ProviderWeather("openai", state=state)
            decision = queue_decision(weather, now=NOW)
            assert decision.action == "proceed"
            assert decision.wait_s == 0.0
            assert state in decision.reason

    def test_limited_with_near_reset_waits(self):
        weather = ProviderWeather(
            "openai", state="limited", limited_until=NOW + 30)
        decision = queue_decision(weather, now=NOW)
        assert decision.action == "wait"
        assert decision.wait_s == 30.0

    def test_limited_beyond_the_bound_proceeds_with_reason(self):
        weather = ProviderWeather(
            "openai", state="limited",
            limited_until=NOW + QUEUE_MAX_WAIT_S + 1)
        decision = queue_decision(weather, now=NOW)
        assert decision.action == "proceed"
        assert "queueing bound" in decision.reason

    def test_limited_with_unknown_reset_proceeds_with_reason(self):
        weather = ProviderWeather("openai", state="limited")
        decision = queue_decision(weather, now=NOW)
        assert decision.action == "proceed"
        assert "never said when" in decision.reason

    def test_expired_limit_proceeds(self):
        weather = ProviderWeather(
            "openai", state="limited", limited_until=NOW - 1)
        assert queue_decision(weather, now=NOW).action == "proceed"

    def test_plan_crew_work_partitions_and_keeps_order(self):
        board = WeatherBoard(clock=lambda: NOW)
        board.record(limited_signal("slow-door", at=NOW, until=NOW + 90))
        board.record_success("fast-door", now=NOW)
        items = [
            {"provider": "fast-door", "task": "a"},
            {"provider": "slow-door", "task": "b"},
            {"provider": "never-seen", "task": "c"},
            {"provider": "slow-door", "task": "d"},
        ]
        plan = plan_crew_work(items, board, now=NOW)
        assert [i["task"] for i in plan["ready"]] == ["a", "c"]
        assert [e["item"]["task"] for e in plan["deferred"]] == ["b", "d"]
        assert plan["deferred"][0]["resume_at"] == NOW + 90
        text = format_queue_plan(plan)
        assert "Ready now: 2" in text and "held" in text

    def test_plan_crew_work_unknown_reset_holds_with_none(self):
        board = WeatherBoard(clock=lambda: NOW)
        board.record(limited_signal("slow-door", at=NOW))
        plan = plan_crew_work(
            [{"provider": "slow-door", "task": "b"}], board, now=NOW)
        assert plan["ready"] == []
        assert plan["deferred"][0]["resume_at"] is None
        with pytest.raises(ValueError):
            plan_crew_work([{"task": "no door"}], board, now=NOW)


# ----------------------------------------------------------------------
# Weather keys, formatting, grammar
# ----------------------------------------------------------------------

class TestKeysAndSurfaces:
    def test_registry_door_keys_by_provider_name(self):
        config = {"base_url": "https://api.openai.com/v1",
                  "model": "gpt-4o"}
        assert weather_key_for(config) == "openai"

    def test_custom_door_keys_by_its_endpoint(self):
        config = {"base_url": "http://localhost:1/v1",
                  "model": "test-model"}
        assert weather_key_for(config) == "http://localhost:1/v1"

    def test_format_weather_states(self):
        unknown = format_weather(ProviderWeather("x"), now=NOW)
        assert "weather unknown" in unknown
        limited = ProviderWeather(
            "x", state="limited", limited_until=NOW + 30,
            remaining_requests=0, limit_requests=10)
        text = format_weather(limited, now=NOW)
        assert "LIMITED" in text and "requests 0 of 10 left" in text

    def test_status_format_names_every_door(self):
        board = WeatherBoard(clock=lambda: NOW)
        board.record_success("fast-door", now=NOW)
        text = format_weather_status(
            board, now=NOW, extra_providers=["mystery-door"])
        assert PLAIN_EXPLANATION in text
        assert "fast-door: clear" in text
        assert "mystery-door: weather unknown" in text

    def test_status_format_empty_board(self):
        board = WeatherBoard(clock=lambda: NOW)
        text = format_weather_status(board, now=NOW)
        assert "No door has reported" in text

    @pytest.mark.parametrize("args", ["", "show", " SHOW ", None])
    def test_show_grammar(self, args):
        assert parse_weather_args(args) == {"action": "show"}

    @pytest.mark.parametrize("args", ["bogus", "on", "clear x"])
    def test_anything_else_is_a_usage_error(self, args):
        with pytest.raises(ValueError, match="Usage: /weather"):
            parse_weather_args(args)

    def test_non_text_is_a_usage_error(self):
        with pytest.raises(ValueError, match="Usage:"):
            parse_weather_args(7)


# ----------------------------------------------------------------------
# Live agent proofs
# ----------------------------------------------------------------------

class TestLiveWeather:
    def test_429_is_recorded_and_journaled_once(self, agent, tmp_path):
        store = SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        client, create = client_for(
            agent, status_error(429, {"retry-after": "30"}),
            reply("Recovered"))
        settings = fast(agent)
        response, _ = agent._request_response(client, settings)
        assert response.choices[0].message["content"] == "Recovered"
        assert create.call_count == 2
        status = agent.weather_status()
        assert status["current_provider"] == agent._weather_key()
        # The success after the 429 is itself a signal: the
        # door answered, so its weather is clear again — but
        # the limit was seen and journaled.
        assert status["current"]["state"] == "clear"
        events = store.export(session_id)["events"]
        seen = [e for e in events if e["type"] == "rate_limit_seen"]
        assert len(seen) == 1
        assert seen[0]["provider"] == agent._weather_key()
        agent.close()

    def test_429_without_recovery_leaves_limited_weather(self, agent):
        client, _ = client_for(
            agent, status_error(429, {"retry-after": "120"}),
            status_error(429, {"retry-after": "120"}),
            status_error(429, {"retry-after": "120"}))
        settings = fast(agent)
        with pytest.raises(Exception):
            agent._request_response(client, settings)
        current = agent.weather_status()["current"]
        assert current["state"] == "limited"
        assert current["seconds_until_reset"] is not None
        assert current["seconds_until_reset"] > 0

    def test_non_limit_failure_records_nothing(self, agent):
        client, _ = client_for(agent, status_error(401))
        settings = fast(agent)
        with pytest.raises(Exception):
            agent._request_response(client, settings)
        board = agent._weather_board
        assert board.snapshot() == []

    def test_streaming_429_is_recorded(self, agent):
        def stream_chat(accumulator, **kwargs):
            raise status_error(429, {"retry-after": "60"})

        client = SimpleNamespace(stream_chat=stream_chat)
        settings = fast(agent)
        with pytest.raises(Exception):
            agent._request_streaming(client, settings)
        current = agent.weather_status()["current"]
        assert current["state"] == "limited"

    def test_request_queues_around_a_near_limit(self, agent, tmp_path):
        store = SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        key = agent._weather_key()
        agent._weather_board.record(LimitSignal(
            provider=key, kind="limited", observed_at=time.time(),
            source="status-429", retry_after_s=0.3))
        client, create = client_for(agent, reply("After the wait"))
        settings = fast(agent)
        started = time.monotonic()
        response, _ = agent._request_with_fallback(settings)
        elapsed = time.monotonic() - started
        assert response.choices[0].message["content"] == "After the wait"
        assert create.call_count == 1
        assert elapsed >= 0.25
        events = store.export(session_id)["events"]
        queued = [e for e in events if e["type"] == "rate_limit_queued"]
        assert len(queued) == 1
        assert queued[0]["provider"] == key
        agent.close()

    def test_cancelled_queue_sends_nothing(self, agent):
        key = agent._weather_key()
        agent._weather_board.record(LimitSignal(
            provider=key, kind="limited", observed_at=time.time(),
            source="status-429", retry_after_s=30))
        client, create = client_for(agent, reply("Never sent"))
        settings = fast(agent)
        agent._cancel.set()
        with pytest.raises(TurnCancelled):
            agent._request_with_fallback(settings)
        assert create.call_count == 0

    def test_far_limit_does_not_park_the_session(self, agent):
        key = agent._weather_key()
        agent._weather_board.record(LimitSignal(
            provider=key, kind="limited", observed_at=time.time(),
            source="status-429",
            retry_after_s=QUEUE_MAX_WAIT_S + 120))
        client, create = client_for(agent, reply("Went ahead"))
        settings = fast(agent)
        started = time.monotonic()
        response, _ = agent._request_with_fallback(settings)
        assert time.monotonic() - started < 5
        assert response.choices[0].message["content"] == "Went ahead"
        assert create.call_count == 1

    def test_unknown_reset_limit_does_not_park_the_session(self, agent):
        key = agent._weather_key()
        agent._weather_board.record(LimitSignal(
            provider=key, kind="limited", observed_at=time.time(),
            source="status-429"))
        client, create = client_for(agent, reply("Went ahead"))
        settings = fast(agent)
        response, _ = agent._request_with_fallback(settings)
        assert response.choices[0].message["content"] == "Went ahead"
        assert create.call_count == 1

    def test_shared_board_is_the_same_for_every_agent(self, agent):
        assert agent._weather_board is shared_board()


# ----------------------------------------------------------------------
# Surfaces
# ----------------------------------------------------------------------

class TestTerminalSurface:
    def test_show_reports_unknown_weather(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/weather")
        assert PLAIN_EXPLANATION in text
        assert "weather unknown" in text

    def test_show_names_a_limited_door(self, agent):
        agent._weather_board.record(LimitSignal(
            provider=agent._weather_key(), kind="limited",
            observed_at=time.time(), source="status-429",
            retry_after_s=90))
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/weather show")
        assert "LIMITED" in text

    def test_usage_error(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/weather bogus")
        assert "Usage: /weather" in text


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


class TestWeatherCommand:
    def test_show_reports_unknown_weather(self, handler):
        handler._handle_weather("")
        text = _published_text(handler)
        assert PLAIN_EXPLANATION in text
        assert "weather unknown" in text

    def test_usage_error_is_published(self, handler):
        handler._handle_weather("bogus")
        assert "Usage: /weather" in _published_text(handler)


class TestChatScreenRouting:
    def test_weather_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/weather show", _FakeLog())
        assert calls == [("/weather", "show")]
