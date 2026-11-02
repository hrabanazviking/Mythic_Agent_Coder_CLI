"""M-038 — Long-context strategy per model.

TIER: integration

Covers the M-038 surface:

* the pure layer (``mythic_agent.core.long_context``): the
  strategy is chosen only from M-027's recorded
  ``context_tokens`` — a known context of 1,000,000+ is
  map-first (budget a quarter of the window, wide selection,
  repo map leading the load order); a known smaller context
  is retrieval-first (budget a sixteenth of the window,
  floored at 500 and capped at 8,000, selection run harder
  than the shipped default); an unknown context — a
  placeholder, an unlisted model, or no model — claims no
  strategy and falls back to the shipped default budget on
  the retrieval road, saying so plainly,
* the boundary, proven on synthetic capability data: exactly
  1,000,000 is map-first, 999,999 is retrieval-first,
* the wiring into the live road: ``prompt_file_context``
  takes its budget and selection width from the config
  model's strategy unless the caller passes an explicit
  budget, which always wins exactly as given,
* ``Agent.context_strategy`` (current model judged, another
  model previewable without touching the session),
* the surfaces: the terminal ``/longcontext`` and the TUI
  ``/longcontext`` (system-command road through the
  CommandHandler + chat-screen routing), sharing the parser
  and formatters.
"""

from __future__ import annotations

import pytest

from mythic_agent.context.runtime import FILE_CONTEXT_BUDGET_TOKENS
from mythic_agent.core.long_context import (
    LONG_CONTEXT_SLICE,
    MAP_FIRST_MIN_CONTEXT,
    PLAIN_EXPLANATION,
    STRATEGY_IDS,
    format_longcontext_status,
    format_strategy_plan,
    parse_longcontext_args,
    plan_from_config,
    strategy_for_model,
)
from mythic_agent.core.model_capabilities import load_capabilities


def _caps_with(context, model="synthetic-model"):
    """Validated capability data holding one synthetic model."""
    return load_capabilities({
        "schema": "mythic.model_capabilities/1",
        "capabilities_slice": "M-027",
        "source_note": "Synthetic data for the M-038 boundary tests.",
        "models": [{
            "model": model, "providers": ["synthetic"],
            "context_tokens": context, "max_output_tokens": None,
            "tool_calling": None, "vision": None, "reasoning": None,
            "streaming": None, "json_mode": None,
            "source": "Synthetic.", "notes": "Synthetic.",
        }],
    })


# ----------------------------------------------------------------------
# The chooser — M-027 truth governs
# ----------------------------------------------------------------------

class TestChooser:
    def test_slice_and_explanation(self):
        assert LONG_CONTEXT_SLICE == "M-038"
        assert MAP_FIRST_MIN_CONTEXT == 1_000_000
        assert STRATEGY_IDS == ("map_first", "retrieval_first", "unknown")
        assert "million" in PLAIN_EXPLANATION
        assert "unknown" in PLAIN_EXPLANATION

    def test_million_class_is_map_first(self):
        plan = strategy_for_model("gemini-2.5-pro")
        assert plan.strategy == "map_first"
        assert plan.context_tokens == 1_048_576
        assert plan.budget_tokens == 1_048_576 // 4
        assert plan.top_n == 8
        assert plan.map_first is True
        assert plan.retrieval_aggressive is False
        assert plan.load_order[0] == "repo_map"
        assert "map-first" in plan.reason

    def test_every_million_class_record_is_map_first(self):
        caps = load_capabilities()
        for record in caps.records:
            if (record.context_tokens is not None
                    and record.context_tokens >= MAP_FIRST_MIN_CONTEXT):
                plan = strategy_for_model(record.model, caps)
                assert plan.strategy == "map_first", record.model
                assert plan.budget_tokens == record.context_tokens // 4

    def test_smaller_known_context_is_retrieval_first(self):
        plan = strategy_for_model("deepseek-chat")
        assert plan.strategy == "retrieval_first"
        assert plan.context_tokens == 128_000
        assert plan.budget_tokens == 8_000  # 128k // 16, at the cap
        assert plan.top_n == 5
        assert plan.map_first is False
        assert plan.retrieval_aggressive is True
        assert plan.load_order[0] == "repo_map"

    def test_retrieval_budget_formula_floor_and_cap(self):
        # 200k // 16 = 12,500 -> capped at 8,000.
        assert strategy_for_model("claude-sonnet-4-5").budget_tokens == 8_000
        # 16,385 // 16 = 1,024 -> inside floor/cap, used as-is.
        assert strategy_for_model("gpt-3.5-turbo").budget_tokens == 1_024
        # A tiny synthetic window floors at 500.
        plan = strategy_for_model("synthetic-model", _caps_with(4_000))
        assert plan.budget_tokens == 500

    def test_boundary_exactly_a_million(self):
        caps = _caps_with(1_000_000)
        assert strategy_for_model(
            "synthetic-model", caps).strategy == "map_first"
        caps = _caps_with(999_999)
        assert strategy_for_model(
            "synthetic-model", caps).strategy == "retrieval_first"

    def test_every_known_record_matches_its_strategy(self):
        caps = load_capabilities()
        for record in caps.records:
            plan = strategy_for_model(record.model, caps)
            assert plan.context_tokens == record.context_tokens
            if record.context_tokens is None:
                assert plan.strategy == "unknown", record.model
            elif record.context_tokens >= MAP_FIRST_MIN_CONTEXT:
                assert plan.strategy == "map_first", record.model
            else:
                assert plan.strategy == "retrieval_first", record.model

    def test_unknown_context_claims_nothing(self):
        for model in ("grok-4", "aesir-local", "openrouter/auto",
                      "no-such-model"):
            plan = strategy_for_model(model)
            assert plan.strategy == "unknown", model
            assert plan.context_tokens is None
            assert plan.budget_tokens == FILE_CONTEXT_BUDGET_TOKENS
            assert plan.top_n == 3
            assert plan.map_first is False
            assert "unknown" in plan.reason

    def test_no_model_is_unknown(self):
        for model in (None, "", "   "):
            plan = strategy_for_model(model)
            assert plan.strategy == "unknown"
            assert plan.budget_tokens == FILE_CONTEXT_BUDGET_TOKENS
        assert "No model is selected" in strategy_for_model(None).reason

    def test_plan_record_round_trips(self):
        plan = strategy_for_model("gemini-1.5-pro")
        record = plan.record()
        assert record["strategy"] == "map_first"
        assert record["load_order"] == list(plan.load_order)
        assert record["context_tokens"] == 1_048_576

    def test_plan_from_config(self):
        plan = plan_from_config({"model": "gpt-3.5-turbo"})
        assert plan.strategy == "retrieval_first"
        assert plan_from_config({}).strategy == "unknown"
        with pytest.raises(ValueError, match="must be a mapping"):
            plan_from_config("not-a-config")


# ----------------------------------------------------------------------
# Parsing and formatting
# ----------------------------------------------------------------------

class TestSurfacesPure:
    def test_parse_show_forms(self):
        for text in (None, "", "show", "status", "SHOW"):
            assert parse_longcontext_args(text) == {
                "action": "show", "model": None}

    def test_parse_preview_forms(self):
        assert parse_longcontext_args("gpt-5") == {
            "action": "preview", "model": "gpt-5"}
        assert parse_longcontext_args("show gpt-5") == {
            "action": "preview", "model": "gpt-5"}
        # A model name keeps its case — names are data, not grammar.
        assert parse_longcontext_args("Gemini-2.5-Pro")["model"] == \
            "Gemini-2.5-Pro"

    def test_parse_non_text_raises(self):
        with pytest.raises(ValueError, match="must be text"):
            parse_longcontext_args(42)

    def test_format_plan_names_numbers_and_reason(self):
        text = format_strategy_plan(strategy_for_model("gemini-2.5-pro"))
        assert "map_first" in text
        assert "262,144" in text
        assert "1,048,576 tokens" in text

    def test_format_status_carries_the_explanation(self):
        status = {"plan": strategy_for_model("deepseek-chat").record()}
        text = format_longcontext_status(status)
        assert "retrieval_first" in text
        assert PLAIN_EXPLANATION in text
        assert "explicit budget" in text


# ----------------------------------------------------------------------
# The live road — prompt_file_context takes the plan
# ----------------------------------------------------------------------

class _CapturingCompiler:
    """A ContextCompiler stand-in recording budget + sources."""

    instances = []

    def __init__(self, workspace, **kwargs):
        self.kwargs = kwargs
        self.sources = []
        _CapturingCompiler.instances.append(self)

    def add_source(self, source):
        self.sources.append(source)
        return source

    def compile(self, query=None):
        class _Compiled:
            blocks = []
        return _Compiled()


class TestRuntimeWiring:
    @pytest.fixture()
    def captured(self, monkeypatch, tmp_path):
        from mythic_agent.context import runtime

        _CapturingCompiler.instances = []
        monkeypatch.setattr(runtime, "ContextCompiler", _CapturingCompiler)
        workspace = tmp_path / "ws"
        workspace.mkdir()
        return runtime, workspace

    def test_strategy_supplies_budget_and_width(self, captured):
        runtime, workspace = captured
        out = runtime.prompt_file_context(
            {"model": "gemini-2.5-pro"}, workspace, "fix the thing")
        assert out == ""
        compiler = _CapturingCompiler.instances[-1]
        assert compiler.kwargs["budget_tokens"] == 262_144
        widths = {type(s).__name__: s.top_n for s in compiler.sources
                  if hasattr(s, "top_n")}
        assert widths == {"SemanticFilesSource": 8, "SymbolFilesSource": 8}

    def test_small_window_strategy_supplies_its_budget(self, captured):
        runtime, workspace = captured
        runtime.prompt_file_context(
            {"model": "gpt-3.5-turbo"}, workspace, "fix the thing")
        compiler = _CapturingCompiler.instances[-1]
        assert compiler.kwargs["budget_tokens"] == 1_024

    def test_unknown_model_keeps_the_shipped_default(self, captured):
        runtime, workspace = captured
        runtime.prompt_file_context(
            {"model": "test-model"}, workspace, "fix the thing")
        compiler = _CapturingCompiler.instances[-1]
        assert compiler.kwargs["budget_tokens"] == FILE_CONTEXT_BUDGET_TOKENS
        widths = {type(s).__name__: s.top_n for s in compiler.sources
                  if hasattr(s, "top_n")}
        assert widths == {"SemanticFilesSource": 3, "SymbolFilesSource": 3}

    def test_explicit_budget_always_wins(self, captured):
        runtime, workspace = captured
        runtime.prompt_file_context(
            {"model": "gemini-2.5-pro"}, workspace, "fix the thing",
            budget_tokens=1_234)
        compiler = _CapturingCompiler.instances[-1]
        assert compiler.kwargs["budget_tokens"] == 1_234
        widths = {type(s).__name__: s.top_n for s in compiler.sources
                  if hasattr(s, "top_n")}
        assert widths == {"SemanticFilesSource": 3, "SymbolFilesSource": 3}

    def test_explicit_budget_must_be_positive(self, captured):
        runtime, workspace = captured
        with pytest.raises(ValueError, match="must be positive"):
            runtime.prompt_file_context(
                {"model": "gpt-5"}, workspace, "fix", budget_tokens=0)

    def test_real_compilation_still_answers(self, tmp_path):
        from mythic_agent.context.runtime import prompt_file_context

        workspace = tmp_path / "ws"
        workspace.mkdir()
        (workspace / "app.py").write_text(
            "def zebrafish():\n    return 1\n", encoding="utf-8")
        out = prompt_file_context(
            {"model": "gemini-2.5-pro"}, workspace, "review @app.py please")
        assert "app.py" in out


# ----------------------------------------------------------------------
# The agent
# ----------------------------------------------------------------------

class TestAgent:
    def test_current_model_judged_by_default(self, agent):
        status = agent.context_strategy()
        assert status["model"] == "test-model"
        assert status["strategy"] == "unknown"
        assert status["context_tokens"] is None
        assert status["plain_explanation"] == PLAIN_EXPLANATION

    def test_preview_does_not_touch_the_session(self, agent):
        status = agent.context_strategy("gemini-2.5-pro")
        assert status["strategy"] == "map_first"
        assert agent.config["model"] == "test-model"

    def test_status_plan_matches_the_pure_layer(self, agent):
        agent.config["model"] = "deepseek-chat"
        status = agent.context_strategy()
        assert status["plan"] == strategy_for_model("deepseek-chat").record()


# ----------------------------------------------------------------------
# Surfaces — terminal + TUI command road
# ----------------------------------------------------------------------

class TestTerminalSurface:
    def test_show_reports_the_unknown_truth(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/longcontext")
        assert "unknown" in text
        assert PLAIN_EXPLANATION in text

    def test_preview_names_the_strategy(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/longcontext gemini-2.5-pro")
        assert "map_first" in text
        assert agent.config["model"] == "test-model"


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


class TestLongContextCommand:
    def test_show_reports_the_unknown_truth(self, handler):
        handler._handle_longcontext("")
        text = _published_text(handler)
        assert "unknown" in text
        assert PLAIN_EXPLANATION in text

    def test_preview_names_the_strategy(self, handler):
        handler._handle_longcontext("gpt-3.5-turbo")
        assert "retrieval_first" in _published_text(handler)


class TestChatScreenRouting:
    def test_longcontext_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/longcontext show", _FakeLog())
        assert calls == [("/longcontext", "show")]
