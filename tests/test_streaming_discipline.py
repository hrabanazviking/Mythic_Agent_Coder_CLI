"""M-034 — Streaming discipline.

TIER: integration

Covers the M-034 surface:

* the pure layer (``mythic_agent.core.streaming_discipline``):
  a killed stream's partial becomes a marked partial assistant
  message — the marker line plus the partial, verbatim, a plain
  ``{"role", "content"}`` message with no tool calls and no
  extra keys; an empty partial salvages nothing; detection and
  the last-partial search round-trip; the resume gate is M-027
  capability truth (only known-true streaming allows; unknown
  or known-false refuses plainly, naming the model); the resume
  prompt asks for a continuation from exactly where the partial
  stopped, without repeating what was said,
* the agent wiring: a stream cancelled mid-flight leaves the
  salvaged partial as the last assistant message in the live
  history AND in the session store's persisted context after
  ``turn_finished``; the journal stays consistent
  (``validate_messages`` clean, no dangling tool calls, events
  in stream_interrupted → message → turn_finished order); an
  empty partial salvages nothing live either,
* restore-on-resume: a session whose journal holds a
  ``stream_interrupted`` checkpoint whose partial never made
  it into the context is salvaged by a fresh agent's resume,
  journaled as ``stream_salvaged_on_resume``,
* ``Agent.resume_thought``: refuses plainly (changing and
  journaling nothing) with no partial waiting or on a model
  whose streaming is not known-true; on a known-streaming
  model it journals ``thought_resumed`` first, then runs the
  continuation as an ordinary turn and returns its text,
* the surfaces: the terminal ``/resume-thought`` and the TUI
  ``/resume-thought`` (system-command road through the
  CommandHandler + chat-screen routing), which share the
  parser and formatters; the show surface says plainly when
  no partial is waiting.
"""

from __future__ import annotations

import copy
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from mythic_agent.core.runtime import TurnCancelled
from mythic_agent.core.sessions import SessionStore, validate_messages
from mythic_agent.core.streaming_discipline import (
    PARTIAL_MARKER,
    PLAIN_EXPLANATION,
    can_resume,
    find_partial,
    format_resume_status,
    is_partial_message,
    parse_resume_args,
    partial_text_of,
    resume_prompt,
    salvage_message,
    salvage_notice,
)

KNOWN_STREAMING = "deepseek-chat"     # M-027: streaming true
UNKNOWN_STREAMING = "grok-4"          # M-027: streaming unknown (null)


def store_for(tmp_path, workspace=None):
    return SessionStore(workspace or tmp_path, tmp_path / "state")


def reply(text):
    return SimpleNamespace(
        choices=[SimpleNamespace(
            message={"role": "assistant", "content": text})],
        usage=SimpleNamespace(total_tokens=7))


def _chunk(text):
    return SimpleNamespace(
        choices=[SimpleNamespace(
            finish_reason=None,
            delta=SimpleNamespace(content=text, tool_calls=None))],
        usage=None)


class FakeStreamingClient:
    """Feeds *partial* to the accumulator, then dies mid-stream."""

    def __init__(self, partial):
        self.partial = partial

    def stream_chat(self, on_chunk, **kwargs):
        if self.partial:
            on_chunk(_chunk(self.partial))
        raise TurnCancelled("Turn cancelled during streaming")


def _cancelled_agent(agent, tmp_path, partial):
    """Drive one streaming turn that is cancelled mid-stream."""
    agent.config["streaming"] = True
    store = store_for(tmp_path)
    session_id = agent.attach_session(store)
    agent.get_client = lambda: FakeStreamingClient(partial)
    with pytest.raises(TurnCancelled):
        agent.chat("tell me something long")
    return store, session_id


# ----------------------------------------------------------------------
# The pure salvage layer
# ----------------------------------------------------------------------

class TestSalvageMessage:
    @pytest.mark.parametrize("empty", ["", "   ", "\n \t", None, 7])
    def test_empty_partial_salvages_nothing(self, empty):
        assert salvage_message(empty) is None

    def test_salvage_is_a_plain_marked_assistant_message(self):
        message = salvage_message("The answer begins")
        assert message == {
            "role": "assistant",
            "content": PARTIAL_MARKER + "\nThe answer begins"}
        assert set(message) == {"role", "content"}
        assert "tool_calls" not in message

    def test_partial_is_kept_verbatim(self):
        partial = "  spaced words \nsecond line  "
        message = salvage_message(partial)
        assert message["content"].endswith(partial)
        assert partial_text_of(message) == partial

    def test_marker_states_partial_in_plain_words(self):
        assert "Partial answer" in PARTIAL_MARKER
        assert "not complete" in PARTIAL_MARKER


class TestPartialDetection:
    def test_is_partial_message(self):
        assert is_partial_message(salvage_message("words"))
        assert not is_partial_message(
            {"role": "assistant", "content": "ordinary answer"})
        assert not is_partial_message(
            {"role": "user", "content": PARTIAL_MARKER + "\nx"})
        assert not is_partial_message("not a message")

    def test_partial_text_of_non_partial_is_none(self):
        assert partial_text_of(
            {"role": "assistant", "content": "plain"}) is None

    def test_find_partial_returns_the_last_one(self):
        messages = [
            {"role": "system", "content": "sys"},
            salvage_message("first partial"),
            {"role": "user", "content": "again"},
            salvage_message("second partial"),
        ]
        assert find_partial(messages) == (3, "second partial")

    def test_find_partial_none_when_no_partial(self):
        assert find_partial([{"role": "user", "content": "hi"}]) is None
        assert find_partial([]) is None


# ----------------------------------------------------------------------
# The resume gate (M-027 capability truth)
# ----------------------------------------------------------------------

class TestResumeGate:
    def test_known_streaming_model_allows(self):
        decision = can_resume(KNOWN_STREAMING)
        assert decision.allowed is True
        assert decision.streaming is True
        assert decision.record()["model"] == KNOWN_STREAMING

    def test_unknown_streaming_model_refuses_plainly(self):
        decision = can_resume(UNKNOWN_STREAMING)
        assert decision.allowed is False
        assert decision.streaming is None
        assert UNKNOWN_STREAMING in decision.reason
        assert "not known to support resuming" in decision.reason

    def test_unlisted_model_refuses_as_unknown(self):
        decision = can_resume("no-such-model")
        assert decision.allowed is False
        assert decision.streaming is None

    def test_known_non_streaming_model_refuses(self):
        caps = SimpleNamespace(
            for_model=lambda name: SimpleNamespace(streaming=False))
        decision = can_resume("some-model", capabilities=caps)
        assert decision.allowed is False
        assert decision.streaming is False
        assert "some-model" in decision.reason

    def test_no_model_refuses(self):
        assert can_resume("").allowed is False
        assert can_resume(None).allowed is False


class TestResumeWords:
    def test_resume_prompt_continues_without_repeating(self):
        prompt = resume_prompt("the partial tail")
        assert "continue" in prompt
        assert "exactly where it stopped" in prompt
        assert "Do not repeat" in prompt
        assert "partial" in prompt

    def test_salvage_notice_says_what_was_kept_and_how_to_resume(self):
        notice = salvage_notice("kept words here")
        assert "kept in the conversation" in notice
        assert "not complete" in notice
        assert "/resume-thought" in notice
        assert str(len("kept words here")) in notice

    def test_plain_explanation_names_the_discipline(self):
        assert "partial answer" in PLAIN_EXPLANATION
        assert "/resume-thought" in PLAIN_EXPLANATION


# ----------------------------------------------------------------------
# The /resume-thought grammar + status formatter
# ----------------------------------------------------------------------

class TestParseAndFormat:
    @pytest.mark.parametrize("text,action", [
        ("", "resume"), (None, "resume"), ("resume", "resume"),
        ("show", "show"), ("status", "show"), (" SHOW ", "show"),
    ])
    def test_parse_actions(self, text, action):
        assert parse_resume_args(text)["action"] == action

    def test_parse_usage_errors(self):
        with pytest.raises(ValueError, match="Usage"):
            parse_resume_args("bogus")
        with pytest.raises(ValueError, match="must be text"):
            parse_resume_args(7)

    def test_status_says_plainly_when_no_partial_waits(self):
        text = format_resume_status(None, can_resume(KNOWN_STREAMING))
        assert "No interrupted answer is waiting" in text
        assert PLAIN_EXPLANATION in text

    def test_status_shows_the_waiting_partial_and_open_gate(self):
        partial = {"partial_text": "half an answer"}
        text = format_resume_status(partial, can_resume(KNOWN_STREAMING))
        assert "A partial answer is waiting" in text
        assert "half an answer" in text
        assert "open" in text

    def test_status_shows_the_closed_gate_reason(self):
        partial = {"partial_text": "half an answer"}
        text = format_resume_status(partial, can_resume(UNKNOWN_STREAMING))
        assert "closed" in text
        assert "not known to support resuming" in text


# ----------------------------------------------------------------------
# Live salvage — a stream cancelled mid-flight
# ----------------------------------------------------------------------

class TestLiveSalvage:
    def test_cancelled_stream_salvages_the_partial(self, agent, tmp_path):
        store, session_id = _cancelled_agent(
            agent, tmp_path, "The answer begins and then")
        history = agent.history_snapshot()
        last = history[-1]
        assert last == {
            "role": "assistant",
            "content": PARTIAL_MARKER + "\nThe answer begins and then"}
        assert agent.salvaged_partial()["partial_text"] == \
            "The answer begins and then"
        # The persisted context after turn_finished holds it too.
        exported = store.export(session_id)
        assert exported["context"][-1] == last
        assert exported["status"] == "cancelled"
        agent.close()

    def test_journal_integrity_after_a_killed_stream(self, agent, tmp_path):
        store, session_id = _cancelled_agent(
            agent, tmp_path, "Words before the cut")
        exported = store.export(session_id)
        # History validates clean: no dangling tool calls, and the
        # salvage is a plain message every provider can be sent.
        assert validate_messages(exported["context"]) == {}
        for message in exported["context"]:
            if message.get("role") == "assistant":
                assert "tool_calls" not in message
        events = exported["events"]
        types = [e["type"] for e in events]
        assert "stream_interrupted" in types
        interrupted = events[types.index("stream_interrupted")]
        assert interrupted["partial_text"] == "Words before the cut"
        assert interrupted["salvaged"] is True
        # Order: the interrupt is recorded, the salvage lands as a
        # message, and the turn finishes on that same history.
        assert types.index("stream_interrupted") < \
            len(types) - 1 - types[::-1].index("message")
        assert types[-1] == "turn_finished"
        agent.close()

    def test_empty_partial_salvages_nothing_live(self, agent, tmp_path):
        store, session_id = _cancelled_agent(agent, tmp_path, "")
        history = agent.history_snapshot()
        assert find_partial(history) is None
        assert agent.salvaged_partial() is None
        assert history[-1]["role"] == "user"
        exported = store.export(session_id)
        assert validate_messages(exported["context"]) == {}
        interrupted = [e for e in exported["events"]
                       if e["type"] == "stream_interrupted"]
        assert len(interrupted) == 1
        assert interrupted[0]["salvaged"] is False
        agent.close()


# ----------------------------------------------------------------------
# Restore-on-resume — the checkpoint's consumer
# ----------------------------------------------------------------------

class TestRestoreOnResume:
    def test_resume_restores_a_partial_that_never_reached_context(
            self, agent, tmp_path):
        from mythic_agent.agents import llm

        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        # A stream died and the process died with it: the journal
        # holds the checkpoint, the context holds no salvage.
        agent._checkpoint({
            "type": "stream_interrupted",
            "partial_text": "Words from a stream that died",
            "salvaged": False})
        assert find_partial(agent.history_snapshot()) is None
        agent.close()

        fresh = llm.Agent(project_root=tmp_path)
        try:
            store2 = store_for(tmp_path)
            fresh.attach_session(store2, resume=session_id)
            history = fresh.history_snapshot()
            found = find_partial(history)
            assert found is not None
            assert found[1] == "Words from a stream that died"
            assert validate_messages(history) == {}
            exported = store2.export(session_id)
            assert exported["context"][-1] == history[-1]
            types = [e["type"] for e in exported["events"]]
            assert "stream_salvaged_on_resume" in types
        finally:
            fresh.close()

    def test_resume_does_not_duplicate_a_live_salvage(
            self, agent, tmp_path):
        from mythic_agent.agents import llm

        store, session_id = _cancelled_agent(
            agent, tmp_path, "Salvaged by the live turn")
        before = agent.history_snapshot()
        agent.close()

        fresh = llm.Agent(project_root=tmp_path)
        try:
            store2 = store_for(tmp_path)
            fresh.attach_session(store2, resume=session_id)
            assert fresh.history_snapshot() == before
            types = [e["type"] for e in store2.export(session_id)["events"]]
            assert "stream_salvaged_on_resume" not in types
        finally:
            fresh.close()


# ----------------------------------------------------------------------
# Agent.resume_thought
# ----------------------------------------------------------------------

class TestResumeThought:
    def test_no_partial_refuses_and_changes_nothing(self, agent):
        before = copy.deepcopy(agent.history_snapshot())
        with pytest.raises(RuntimeError, match="No interrupted answer"):
            agent.resume_thought()
        assert agent.history_snapshot() == before

    def test_unknown_streaming_model_refuses_plainly(
            self, agent, tmp_path):
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        agent._append_message(salvage_message("a partial waits"))
        before = copy.deepcopy(agent.history_snapshot())
        events_before = len(store.export(session_id)["events"])
        with pytest.raises(RuntimeError) as excinfo:
            agent.resume_thought()
        # The fixture model is unlisted: streaming unknown.
        assert "test-model" in str(excinfo.value)
        assert "not known to support resuming" in str(excinfo.value)
        assert agent.history_snapshot() == before
        exported = store.export(session_id)
        assert len(exported["events"]) == events_before
        assert "thought_resumed" not in [
            e["type"] for e in exported["events"]]
        agent.close()

    def test_happy_path_journals_then_continues(self, agent, tmp_path):
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        agent.config["model"] = KNOWN_STREAMING
        agent._append_message(salvage_message("The first half"))
        client = SimpleNamespace(chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=Mock(return_value=reply(" and the second half.")))))
        agent.get_client = lambda: client
        text = agent.resume_thought()
        assert text == " and the second half."
        history = agent.history_snapshot()
        # The partial stays, marked; the resume prompt went in as
        # the user turn; the continuation is the last message.
        assert is_partial_message(history[-3])
        assert history[-2]["role"] == "user"
        assert "Do not repeat" in history[-2]["content"]
        assert history[-1] == {"role": "assistant",
                               "content": " and the second half."}
        assert validate_messages(history) == {}
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "thought_resumed" in types
        assert types.index("thought_resumed") < types.index("turn_started")
        agent.close()


# ----------------------------------------------------------------------
# Surfaces
# ----------------------------------------------------------------------

class TestTerminalSurface:
    def test_show_says_plainly_when_no_partial_waits(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/resume-thought show")
        assert "No interrupted answer is waiting" in text

    def test_show_names_the_waiting_partial(self, agent):
        from mythic_agent.terminal import _slash

        agent._append_message(salvage_message("half a thought"))
        _, _, text = _slash(agent, "/resume-thought show")
        assert "A partial answer is waiting" in text

    def test_resume_runs_the_continuation(self, agent):
        from mythic_agent.terminal import _slash

        agent.config["model"] = KNOWN_STREAMING
        agent._append_message(salvage_message("The first half"))
        client = SimpleNamespace(chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=Mock(return_value=reply("the rest of it")))))
        agent.get_client = lambda: client
        _, _, text = _slash(agent, "/resume-thought")
        assert text == "the rest of it"

    def test_resume_refusal_is_the_message(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/resume-thought")
        assert "No interrupted answer is waiting" in text

    def test_usage_error_is_the_message(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/resume-thought bogus")
        assert "Usage:" in text


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


class TestResumeCommand:
    def test_show_says_plainly_when_no_partial_waits(self, handler):
        handler._handle_resume_thought("show")
        assert "No interrupted answer is waiting" in _published_text(handler)

    def test_resume_refusal_is_published(self, handler):
        handler._handle_resume_thought("")
        assert "No interrupted answer is waiting" in _published_text(handler)

    def test_resume_publishes_the_continuation(self, handler, agent):
        agent.config["model"] = KNOWN_STREAMING
        agent._append_message(salvage_message("The first half"))
        client = SimpleNamespace(chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=Mock(return_value=reply("continued here")))))
        agent.get_client = lambda: client
        handler._handle_resume_thought("")
        assert "continued here" in _published_text(handler)


class TestChatScreenRouting:
    def test_resume_thought_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/resume-thought show", _FakeLog())
        assert calls == [("/resume-thought", "show")]
