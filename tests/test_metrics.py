"""Slice 48: metrics and tracing."""

import json
import time

import pytest

from mythic_agent.core.metrics import Metrics, Span, Trace


def test_timer_records():
    m = Metrics()
    with m.timer("turn"):
        time.sleep(0.01)
    data = m.to_dict()["timers"]["turn"]
    assert data["count"] == 1
    assert data["total_s"] > 0
    assert data["avg_s"] == pytest.approx(data["total_s"])


def test_counter_and_gauge():
    m = Metrics()
    c = m.counter("tool_calls")
    c.inc()
    c.inc(2)
    assert c.count == 3
    g = m.gauge("queue_depth", 7)
    assert g.value == 7.0
    m.gauge("queue_depth", 2)
    assert m.to_dict()["gauges"]["queue_depth"] == 2.0


def test_counter_rejects_negative():
    m = Metrics()
    with pytest.raises(ValueError):
        m.counter("x").inc(-1)


def test_trace_nesting():
    m = Metrics()
    with m.trace("turn", agent="primary") as root:
        with Trace("tool_call") as child:
            with Trace("retry") as grandchild:
                pass
    assert root.name == "turn"
    assert len(root.children) == 1
    assert root.children[0].name == "tool_call"
    assert root.children[0].children[0].name == "retry"
    assert child.parent_id == root.span_id
    # one finished root tree attached to the metrics registry
    assert len(m.traces) == 1
    assert m.traces[0].span_id == root.span_id


def test_trace_records_errors():
    m = Metrics()
    with pytest.raises(RuntimeError):
        with m.trace("failing"):
            raise RuntimeError("boom")
    tree = m.traces[0].to_dict()
    assert "RuntimeError" in tree["attributes"]["error"]


def test_trace_is_thread_local_and_restores():
    m = Metrics()
    with m.trace("outer"):
        pass
    assert len(m.traces) == 1
    with m.trace("second"):
        pass
    assert len(m.traces) == 2


def test_export_to_json():
    m = Metrics()
    with m.timer("t"):
        pass
    m.counter("c").inc()
    m.gauge("g", 1.5)
    with m.trace("root"):
        pass
    doc = json.loads(m.to_json())
    assert set(doc) == {"timers", "counters", "gauges", "traces"}
    assert doc["counters"]["c"] == 1
    assert len(doc["traces"]) == 1


def test_save_and_render(tmp_path):
    m = Metrics()
    m.counter("hits").inc(4)
    out = m.save(tmp_path / "metrics.json")
    assert out.exists()
    assert json.loads(out.read_text())["counters"]["hits"] == 4
    text = m.render()
    assert "counter hits: 4" in text
    assert "Metrics:" in text


def test_span_dict_shape():
    with Trace("leaf", attributes={"k": "v"}) as span:
        pass
    d = span.to_dict()
    assert d["name"] == "leaf"
    assert d["parent_id"] is None
    assert d["attributes"] == {"k": "v"}
    assert d["children"] == []


def test_from_dict_roundtrip():
    from mythic_agent.core.metrics import Metrics as _M
    m = _M()
    with m.timer("t"):
        pass
    m.counter("c").inc(3)
    m.gauge("g", 2.5)
    with m.trace("root"):
        pass
    m2 = _M.from_dict(m.to_dict())
    d2 = m2.to_dict()
    assert d2["counters"]["c"] == 3
    assert d2["gauges"]["g"] == 2.5
    assert d2["timers"]["t"]["count"] == 1
    assert len(d2["traces"]) == 1
