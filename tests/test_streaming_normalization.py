"""TIER: unit

Unit tests for slice 044 (streaming normalization).

No network, no sockets, no real keys: parsers operate on in-memory
line iterables; cancellation is exercised through the ``cancel``
callable and generator ``close()``.
"""

import json

import pytest

from mythic_agent.providers import streaming
from mythic_agent.providers.base import Provider, ProviderError
from mythic_agent.providers.streaming import (
    CancelledStream,
    StreamEvent,
    collect,
    iter_events,
    parse_ndjson,
    parse_ollama_ndjson,
    parse_openai_sse,
)


# ----------------------------------------------------------------------
# Fakes
# ----------------------------------------------------------------------

def _make_provider(name):
    flags = {"streaming": True, "tool_calling": True,
             "vision": False, "json_mode": False}

    def capabilities(self):
        return dict(flags)

    def chat(self, messages, **kwargs):
        raise ProviderError("fake: chat not implemented")

    return type(f"_Provider_{name}", (Provider,), {
        "name": name,
        "capabilities": capabilities,
        "chat": chat,
    })()


def _sse(*payloads):
    lines = []
    for payload in payloads:
        lines.append("data: " + (payload if isinstance(payload, str)
                                 else json.dumps(payload)))
    return lines


# ----------------------------------------------------------------------
# StreamEvent validation
# ----------------------------------------------------------------------

def test_stream_event_rejects_bad_kind():
    with pytest.raises(ValueError):
        StreamEvent(kind="mystery")


# ----------------------------------------------------------------------
# parse_openai_sse(): normal behavior
# ----------------------------------------------------------------------

def test_sse_text_and_done():
    lines = _sse({"choices": [{"delta": {"content": "Hello"}}]},
                 {"choices": [{"delta": {}, "finish_reason": "stop"}]})
    events = list(parse_openai_sse(lines))
    assert [e.kind for e in events] == ["text", "done"]
    assert events[0].text == "Hello"


def test_sse_done_marker():
    events = list(parse_openai_sse(["data: [DONE]"]))
    assert [e.kind for e in events] == ["done"]


def test_sse_skips_blanks_and_comments():
    lines = ["", ": ping",
             *_sse({"choices": [{"delta": {"content": "x"}}]}),
             "data: [DONE]"]
    events = list(parse_openai_sse(lines))
    assert [e.kind for e in events] == ["text", "done"]


def test_sse_tool_call_deltas():
    delta = {
        "tool_calls": [
            {"id": "c1",
             "function": {"name": "get_weather",
                          "arguments": '{"city":'}}
        ]
    }
    lines = _sse({"choices": [{"delta": delta}]},
                 {"choices": [{"delta": {}, "finish_reason": "tool_calls"}]})
    events = list(parse_openai_sse(lines))
    assert events[0].kind == "tool_call_delta"
    assert events[0].tool_call == {
        "id": "c1", "name": "get_weather",
        "arguments_delta": '{"city":'}
    assert events[1].kind == "done"


def test_sse_usage_event():
    lines = _sse({"usage": {"prompt_tokens": 10, "completion_tokens": 4,
                            "total_tokens": 14}})
    events = list(parse_openai_sse(lines))
    assert len(events) == 1
    assert events[0].kind == "usage"
    assert events[0].usage.prompt_tokens == 10
    assert events[0].usage.completion_tokens == 4


def test_sse_error_event_stops_stream():
    lines = _sse({"error": {"message": "boom"}},
                 {"choices": [{"delta": {"content": "never"}}]})
    events = list(parse_openai_sse(lines))
    assert len(events) == 1
    assert events[0].kind == "error"
    assert events[0].error == "boom"


# ----------------------------------------------------------------------
# parse_openai_sse(): failure behavior
# ----------------------------------------------------------------------

def test_sse_malformed_json_raises():
    with pytest.raises(ProviderError):
        list(parse_openai_sse(["data: {not json"]))


def test_sse_non_data_line_raises():
    with pytest.raises(ProviderError):
        list(parse_openai_sse(['{"choices": []}']))


def test_sse_non_object_payload_raises():
    with pytest.raises(ProviderError):
        list(parse_openai_sse(["data: [1, 2]"]))


def test_sse_missing_choices_raises():
    with pytest.raises(ProviderError):
        list(parse_openai_sse(['data: {"hello": "world"}']))


# ----------------------------------------------------------------------
# parse_ndjson()
# ----------------------------------------------------------------------

def test_ndjson_shapes():
    lines = [
        json.dumps({"text": "a"}),
        json.dumps({"tool_call_delta": {"id": "t1", "name": "f",
                                       "arguments_delta": "{}"}}),
        json.dumps({"usage": {"prompt_tokens": 3, "completion_tokens": 1}}),
        json.dumps({"done": True}),
    ]
    events = list(parse_ndjson(lines))
    assert [e.kind for e in events] == [
        "text", "tool_call_delta", "usage", "done"]
    assert events[0].text == "a"
    assert events[2].usage.total_tokens == 4


def test_ndjson_error_stops():
    events = list(parse_ndjson([json.dumps({"error": "kaput"})]))
    assert events[0].kind == "error"
    assert events[0].error == "kaput"


def test_ndjson_malformed_raises():
    with pytest.raises(ProviderError):
        list(parse_ndjson(["{oops"]))


# ----------------------------------------------------------------------
# parse_ollama_ndjson()
# ----------------------------------------------------------------------

def test_ollama_ndjson():
    lines = [
        json.dumps({"message": {"content": "Hel"}, "done": False}),
        json.dumps({"message": {"content": "lo"}, "done": False}),
        json.dumps({"message": {"content": ""}, "done": True,
                    "prompt_eval_count": 8, "eval_count": 2}),
    ]
    events = list(parse_ollama_ndjson(lines))
    assert [e.kind for e in events] == ["text", "text", "usage", "done"]
    assert events[2].usage.prompt_tokens == 8
    assert events[2].usage.completion_tokens == 2


# ----------------------------------------------------------------------
# iter_events(): family dispatch
# ----------------------------------------------------------------------

def test_iter_events_dispatch():
    sse = _sse({"choices": [{"delta": {"content": "s"}}]}, "[DONE]")
    events = list(iter_events(_make_provider("openai"), sse))
    assert [e.kind for e in events] == ["text", "done"]

    ollama_lines = [
        json.dumps({"message": {"content": "o"}, "done": False}),
        json.dumps({"message": {"content": ""}, "done": True}),
    ]
    events = list(iter_events(_make_provider("ollama"), ollama_lines))
    assert [e.kind for e in events] == ["text", "usage", "done"]


# ----------------------------------------------------------------------
# collect(): assembly, error, cancellation
# ----------------------------------------------------------------------

def test_collect_assembles_text():
    events = [StreamEvent(kind="text", text="a"),
              StreamEvent(kind="text", text="b"),
              StreamEvent(kind="done")]
    assert collect(iter(events)) == "ab"


def test_collect_raises_on_error_event():
    events = [StreamEvent(kind="text", text="a"),
              StreamEvent(kind="error", error="mid-stream boom")]
    with pytest.raises(ProviderError) as excinfo:
        collect(iter(events))
    assert "mid-stream boom" in str(excinfo.value)


def test_collect_cancellation():
    events = [StreamEvent(kind="text", text="a"),
              StreamEvent(kind="text", text="b"),
              StreamEvent(kind="done")]
    calls = {"n": 0}

    def cancel():
        calls["n"] += 1
        return calls["n"] >= 2

    with pytest.raises(CancelledStream) as excinfo:
        collect(iter(events), cancel=cancel)
    assert excinfo.value.partial_text == "ab"


def test_collect_no_cancel_runs_to_end():
    events = [StreamEvent(kind="text", text="x"), StreamEvent(kind="done")]
    assert collect(iter(events), cancel=lambda: False) == "x"


def test_collect_on_event_observer():
    seen = []
    events = [StreamEvent(kind="text", text="z"), StreamEvent(kind="done")]
    collect(iter(events), on_event=seen.append)
    assert [e.kind for e in seen] == ["text", "done"]


def test_generator_close_is_safe():
    lines = _sse({"choices": [{"delta": {"content": "a"}}]},
                 {"choices": [{"delta": {"content": "b"}}]},
                 "data: [DONE]")
    gen = parse_openai_sse(iter(lines))
    assert next(gen).text == "a"
    gen.close()  # must not raise; partial state is simply discarded
    with pytest.raises(StopIteration):
        next(gen)
