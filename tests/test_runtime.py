import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from openai.types.chat import ChatCompletionMessage

from mythic_agent.core.runtime import TurnCancelled, runtime_settings
from mythic_agent.core.secure_api import EventBus, subscribe, unsubscribe


def reply(content="Done", calls=None):
    message = ChatCompletionMessage(role="assistant", content=content, tool_calls=calls)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)],
                           usage=SimpleNamespace(total_tokens=7))


def tool_call(name="read_file", args='{"path":"example.txt"}', call_id="call-1"):
    return {"id": call_id, "type": "function", "function": {"name": name, "arguments": args}}


def client_for(agent, *responses):
    create = Mock(side_effect=list(responses))
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    agent.get_client = lambda: client
    return create


def test_first_and_multiple_turns_call_provider(agent):
    create = client_for(agent, reply("Hello"), reply("Again"))
    assert agent.chat("first") == "Hello"
    assert agent.chat("second") == "Again"
    assert create.call_count == 2
    assert agent.last_result.status == "completed"
    assert agent.total_tokens == 14
    assert [m["role"] for m in agent.messages] == ["system", "user", "assistant", "user", "assistant"]
    json.dumps(agent.messages)


def test_text_and_multiple_tools_share_one_assistant_message(agent):
    (agent.project_root / "example.txt").write_text("source")
    calls = [tool_call(), tool_call("missing_tool", "{}", "call-2")]
    create = client_for(agent, reply("Inspecting", calls), reply("Finished"))
    assert agent.chat("inspect") == "Finished"
    history = create.call_args_list[1].kwargs["messages"]
    assert [m["role"] for m in history] == ["system", "user", "assistant", "tool", "tool"]
    assert history[2]["content"] == "Inspecting"
    assert [m["tool_call_id"] for m in history[3:]] == ["call-1", "call-2"]
    assert history[3]["content"] == "source"
    assert "Unknown tool" in history[4]["content"]
    json.dumps(agent.messages)


@pytest.mark.parametrize("arguments", ["{bad", "[]", "null"])
def test_invalid_tool_json_becomes_result(agent, arguments):
    client_for(agent, reply(None, [tool_call(args=arguments)]), reply())
    agent.chat("inspect")
    assert agent.messages[3]["role"] == "tool"
    assert "failed" in agent.messages[3]["content"] or "JSON object" in agent.messages[3]["content"]


def test_tool_exception_has_a_paired_result(agent, monkeypatch):
    from mythic_agent.agents import llm
    monkeypatch.setattr(llm, "execute_tool", Mock(side_effect=OSError("disk unavailable")))
    client_for(agent, reply(None, [tool_call()]), reply())
    agent.chat("inspect")
    assert "disk unavailable" in agent.messages[3]["content"]


def test_callbacks_can_snapshot_history_and_defer_clear(agent):
    captured = []
    def callback(agent_name, text):
        captured.append(agent.history_snapshot())
        if text == "Done":
            agent._handle_clear_history(agent_name)
    subscribe("agent_chat_chunk", callback)
    try:
        client_for(agent, reply())
        assert agent.chat("inspect") == "Done"
        assert len(agent.messages) == 1
        assert captured
    finally:
        unsubscribe("agent_chat_chunk", callback)


def test_large_history_is_not_silently_discarded(agent):
    agent.messages.extend({"role": "user", "content": str(i)} for i in range(110))
    client_for(agent, reply())
    agent.chat("next")
    assert len(agent.messages) == 113


def test_manual_compaction_keeps_complete_last_turn(agent):
    create = client_for(agent, reply(None, [tool_call()]), reply(), reply("Second"))
    agent.chat("first")
    agent.chat("second")
    agent._handle_compact_history(agent.name)
    assert [m["role"] for m in agent.messages] == ["system", "user", "assistant"]
    archived = json.loads(agent.vector_db.archived[0].removeprefix("Archived Context: "))
    assert [m["role"] for m in archived] == ["user", "assistant", "tool", "assistant"]
    assert create.call_count == 3


def test_loop_budget_produces_failure_instead_of_infinite_loop(agent):
    agent.config["runtime"] = {"max_tool_rounds": 2}
    create = client_for(agent, reply(None, [tool_call()]), reply(None, [tool_call(call_id="call-2")]))
    with pytest.raises(RuntimeError, match="budget exhausted"):
        agent.chat("loop")
    assert create.call_count == 2
    assert agent.last_result.status == "failed"


def test_cancel_before_tools_yields_paired_results(agent):
    def callback(agent_name, text):
        agent.cancel()
    subscribe("agent_chat_chunk", callback)
    try:
        client_for(agent, reply("Starting", [tool_call()]))
        with pytest.raises(TurnCancelled):
            agent.chat("inspect")
        assert agent.messages[-1]["role"] == "tool"
        assert "cancelled" in agent.messages[-1]["content"]
        assert agent.last_result.status == "cancelled"
    finally:
        unsubscribe("agent_chat_chunk", callback)
    client_for(agent, reply("Recovered"))
    assert agent.chat("continue") == "Recovered"


def test_keyboard_interrupt_closes_pending_tool_calls(agent, monkeypatch):
    from mythic_agent.agents import llm
    monkeypatch.setattr(llm, "execute_tool", Mock(side_effect=KeyboardInterrupt))
    client_for(agent, reply(None, [tool_call(), tool_call(call_id="call-2")]))
    with pytest.raises(TurnCancelled):
        agent.chat("inspect")
    assert [m["tool_call_id"] for m in agent.messages if m["role"] == "tool"] == ["call-1", "call-2"]
    assert agent.last_result.status == "cancelled"


def test_permanent_failure_is_not_retried(agent):
    create = client_for(agent, ValueError("bad request"))
    with pytest.raises(ValueError):
        agent.chat("inspect")
    assert create.call_count == 1
    assert agent.last_result.status == "failed"


@pytest.mark.parametrize("status", [401, 429, 503])
def test_provider_status_retry_classification(agent, status):
    from openai import APIStatusError
    response = SimpleNamespace(status_code=status, request=Mock(), headers={})
    error = APIStatusError("provider error", response=response, body={})
    agent.config["runtime"] = {"retry_delay": 0.001}
    create = client_for(agent, error, reply("Recovered"))
    if status == 401:
        with pytest.raises(APIStatusError):
            agent.chat("inspect")
        assert create.call_count == 1
    else:
        assert agent.chat("inspect") == "Recovered"
        assert create.call_count == 2


def test_concurrent_turns_are_serialized_without_holding_history_lock(agent):
    import threading
    from concurrent.futures import ThreadPoolExecutor
    started, release = threading.Event(), threading.Event()
    def response(**kwargs):
        assert agent.history_snapshot()
        if kwargs["messages"][-1]["content"] == "first":
            started.set()
            assert release.wait(5)
        return reply()
    create = Mock(side_effect=response)
    agent.get_client = lambda: SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(agent.chat, "first")
        assert started.wait(5)
        second = pool.submit(agent.chat, "second")
        assert create.call_count == 1
        release.set()
        assert first.result(timeout=5) == "Done"
        assert second.result(timeout=5) == "Done"
    assert [m["role"] for m in agent.messages] == ["system", "user", "assistant", "user", "assistant"]


def test_empty_response_is_visible_failure(agent):
    client_for(agent, reply(None))
    with pytest.raises(RuntimeError, match="empty assistant"):
        agent.chat("inspect")


def test_event_dispatch_uses_snapshot():
    bus = EventBus()
    calls = []
    def first():
        calls.append("first")
        bus.unsubscribe("event", first)
    def second():
        calls.append("second")
    bus.subscribe("event", first)
    bus.subscribe("event", second)
    bus.publish_sync("event")
    assert calls == ["first", "second"]


@pytest.mark.parametrize("override", [{"max_retries": -1}, {"max_tool_rounds": True}, {"request_timeout": 0}])
def test_runtime_budgets_are_validated(override):
    with pytest.raises(ValueError):
        runtime_settings({"runtime": override})
