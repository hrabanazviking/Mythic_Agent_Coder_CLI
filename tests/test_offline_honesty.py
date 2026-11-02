"""M-040 — Offline honesty.

TIER: integration

Covers the M-040 surface:

* the pure layer (``mythic_agent.core.offline_honesty``): the
  assessment over an M-039 health board — ``online`` when any
  door answered its probe, ``offline`` (with the exact
  declaration and the non-model tools that still work) only
  when a probed board shows no door can serve, and ``unknown``
  when the board cannot honestly say,
* the honesty rules: an unprobed board claims nothing; a
  keyed door the board cannot probe (a native-SDK door whose
  address belongs to its vendor's kit) blocks the offline
  claim; one reachable door — local or remote — is online,
* the still-working tools are real: each offered command is
  run against the live CLI (``mythic review`` statically
  reviews a file, ``mythic metrics`` answers for a workspace,
  ``mythic sessions --search`` searches) and needs no model,
* the wiring: ``Agent.offline_status()``, the terminal and
  TUI ``/offline`` surfaces sharing one parser + formatter,
  and ``mythic doctor --live`` carrying the assessment
  beside its board (text declaration + ``--json`` record).
"""

from __future__ import annotations

import json

import pytest

from mythic_agent.core.offline_honesty import (
    DECLARATION,
    OFFLINE_SLICE,
    PLAIN_EXPLANATION,
    STATES,
    STILL_AVAILABLE,
    assess_board,
    format_offline_status,
    parse_offline_args,
)
from mythic_agent.core.provider_health import build_board


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
        if url in answers:
            return answers[url]
        raise ConnectionError(f"connection refused at {url}")

    probe.calls = calls
    return probe


def _board(prober, **kwargs):
    kwargs.setdefault("environ", {})
    kwargs.setdefault("config", {})
    kwargs.setdefault("clock", _clock())
    kwargs.setdefault("now", 5000.0)
    return build_board(prober=prober, **kwargs)


# ----------------------------------------------------------------------
# The assessment — the honesty rules
# ----------------------------------------------------------------------

class TestAssessment:
    def test_slice_states_and_declaration(self):
        assert OFFLINE_SLICE == "M-040"
        assert STATES == ("online", "offline", "unknown")
        assert "no network" in DECLARATION
        assert "no local model" in DECLARATION
        assert "claims nothing" in PLAIN_EXPLANATION

    def test_all_doors_down_is_offline_with_the_declaration(self):
        assessment = assess_board(_board(_prober()))
        assert assessment.state == "offline"
        assert assessment.probed is True
        assert assessment.reachable == ()
        assert assessment.declaration == DECLARATION
        assert assessment.still_available == STILL_AVAILABLE
        reasons = " ".join(assessment.reasons)
        assert "ollama" in reasons          # probed, not answering
        assert "deepseek" in reasons        # needs its key
        record = assessment.record()
        assert record["slice"] == "M-040"
        assert record["state"] == "offline"
        assert [o["name"] for o in record["still_available"]] == [
            "review", "metrics", "session search"]

    def test_one_reachable_local_door_is_online(self):
        prober = _prober(answers={
            "http://localhost:11434/api/tags": (200, "{}")})
        assessment = assess_board(_board(prober))
        assert assessment.state == "online"
        assert assessment.reachable == ("ollama",)
        assert assessment.declaration is None
        assert assessment.still_available == ()

    def test_one_reachable_remote_door_is_online(self):
        prober = _prober(answers={
            "https://api.openai.com/v1/models": (200, "{}")})
        board = _board(prober, environ={"OPENAI_API_KEY": "sk-test"})
        assessment = assess_board(board)
        assert assessment.state == "online"
        assert "openai" in assessment.reachable

    def test_unprobed_board_claims_nothing(self):
        assessment = assess_board(_board(_prober(), probe=False))
        assert assessment.state == "unknown"
        assert assessment.probed is False
        assert assessment.declaration is None
        assert "never guessed" in " ".join(assessment.reasons)

    def test_keyed_native_door_blocks_the_offline_claim(self):
        # Anthropic's key is held, but the board cannot probe
        # its SDK-owned address — it may still serve, so the
        # app must not claim offline.
        board = _board(_prober(), environ={
            "ANTHROPIC_API_KEY": "sk-ant"})
        assessment = assess_board(board)
        assert assessment.state == "unknown"
        assert assessment.declaration is None
        assert "anthropic" in " ".join(assessment.reasons)

    def test_unkeyed_native_door_does_not_block_the_claim(self):
        # The same door with no key held cannot serve either,
        # so a fully probed, fully down board is offline.
        assessment = assess_board(_board(_prober()))
        assert assessment.state == "offline"
        assert "anthropic" in " ".join(assessment.reasons)


# ----------------------------------------------------------------------
# The still-working tools are real CLI surfaces
# ----------------------------------------------------------------------

class TestStillAvailable:
    def test_offers_are_the_roadmap_trio_in_order(self):
        assert [o.name for o in STILL_AVAILABLE] == [
            "review", "metrics", "session search"]
        assert [o.command for o in STILL_AVAILABLE] == [
            "mythic review <path>", "mythic metrics",
            "mythic sessions --search <query>"]

    def test_review_command_runs_without_a_model(self, tmp_path):
        from mythic_agent.cli import main

        target = tmp_path / "clean.py"
        target.write_text("def ok():\n    return 1\n", encoding="utf-8")
        assert main(["review", str(target)]) == 0

    def test_metrics_command_runs_without_a_model(self, tmp_path):
        from mythic_agent.cli import main

        assert main(["metrics", "--workspace", str(tmp_path)]) == 0

    def test_session_search_runs_without_a_model(self, tmp_path):
        from mythic_agent.cli import main

        assert main(["sessions", "--workspace", str(tmp_path),
                     "--search", "anything"]) == 0


# ----------------------------------------------------------------------
# Parser + formatter
# ----------------------------------------------------------------------

class TestSurfaceText:
    def test_parser_accepts_bare_and_show_only(self):
        assert parse_offline_args("") == {"action": "show"}
        assert parse_offline_args("show") == {"action": "show"}
        assert parse_offline_args(None) == {"action": "show"}
        with pytest.raises(ValueError, match="Usage: /offline"):
            parse_offline_args("restart the world")

    def test_format_offline_carries_declaration_and_tools(self):
        assessment = assess_board(_board(_prober()))
        text = format_offline_status({"assessment": assessment.record()})
        assert "state — offline" in text
        assert DECLARATION in text
        assert "mythic review <path>" in text
        assert "mythic metrics" in text
        assert "mythic sessions --search <query>" in text
        assert PLAIN_EXPLANATION in text

    def test_format_online_names_the_answering_doors(self):
        prober = _prober(answers={
            "http://localhost:11434/api/tags": (200, "{}")})
        assessment = assess_board(_board(prober))
        text = format_offline_status({"assessment": assessment.record()})
        assert "state — online" in text
        assert "ollama" in text
        assert DECLARATION not in text


# ----------------------------------------------------------------------
# The agent
# ----------------------------------------------------------------------

class TestAgent:
    def test_unprobed_status_is_unknown_never_offline(self, agent):
        status = agent.offline_status(probe=False)
        assert status["assessment"]["state"] == "unknown"
        assert status["assessment"]["declaration"] is None
        assert status["plain_explanation"] == PLAIN_EXPLANATION
        assert status["board"]["entries"]  # the board rides along

    def test_status_matches_the_pure_layer(self, agent, monkeypatch):
        from mythic_agent.core import provider_health

        monkeypatch.setattr(provider_health, "default_prober",
                            _prober())
        status = agent.offline_status()
        board = build_board(agent.config, environ={},
                            prober=_prober(), clock=_clock(), now=1.0)
        assert status["assessment"]["state"] == \
            assess_board(board).state == "offline"
        assert status["assessment"]["declaration"] == DECLARATION


# ----------------------------------------------------------------------
# Surfaces — terminal + TUI command road + doctor
# ----------------------------------------------------------------------

class TestTerminalSurface:
    def test_show_prints_the_declaration_when_offline(
            self, agent, monkeypatch):
        from mythic_agent.core import provider_health
        from mythic_agent.terminal import _slash

        monkeypatch.setattr(provider_health, "default_prober",
                            _prober())
        _, _, text = _slash(agent, "/offline")
        assert "state — offline" in text
        assert DECLARATION in text
        assert PLAIN_EXPLANATION in text

    def test_usage_error_is_plain(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/offline bogus")
        assert text.startswith("Usage: /offline")


@pytest.fixture()
def handler(agent, monkeypatch):
    from mythic_agent.agents import command_handler as handler_module
    from mythic_agent.agents.command_handler import CommandHandler
    from mythic_agent.agents.llm import AGENT_REGISTRY
    from mythic_agent.core import provider_health

    monkeypatch.setattr(provider_health, "default_prober", _prober())
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


class TestOfflineCommand:
    def test_show_prints_the_declaration_when_offline(self, handler):
        handler._handle_offline("")
        text = _published_text(handler)
        assert "state — offline" in text
        assert DECLARATION in text


class TestChatScreenRouting:
    def test_offline_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/offline show", _FakeLog())
        assert calls == [("/offline", "show")]


class TestDoctorSurface:
    def _stub_doctor(self, monkeypatch):
        from mythic_agent import doctor
        from mythic_agent.core import provider_health
        from mythic_agent.core.config_manager import config_manager

        monkeypatch.setattr(config_manager, "load_config", lambda: {})
        monkeypatch.setattr(provider_health, "default_prober", _prober())
        monkeypatch.setattr(
            doctor, "check_provider_live",
            lambda timeout=15.0: doctor.HealthResult(
                "provider-live", doctor.HealthStatus.SKIP, "stubbed"))
        return doctor

    def test_doctor_live_prints_the_declaration(self, monkeypatch, capsys):
        doctor = self._stub_doctor(monkeypatch)
        doctor.main(["--live"])
        out = capsys.readouterr().out
        assert "Provider health board:" in out
        assert DECLARATION in out
        assert "mythic sessions --search <query>" in out

    def test_doctor_live_json_carries_the_assessment(
            self, monkeypatch, capsys):
        doctor = self._stub_doctor(monkeypatch)
        doctor.main(["--live", "--json"])
        out = capsys.readouterr().out
        payload, _ = json.JSONDecoder().raw_decode(out[out.index("{"):])
        assert payload["offline"]["slice"] == "M-040"
        assert payload["offline"]["state"] == "offline"
        assert payload["offline"]["declaration"] == DECLARATION
        assert "provider_health" in payload
