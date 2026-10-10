"""Metrics and tracing for Mythic Agent.

:class:`Metrics` collects timers, counters, and gauges in memory and
exports them as JSON.  :class:`Trace` is a context manager that opens a
named span and attaches it to a parent, so spans nest into a tree for
distributed-trace style inspection.

Usage:
    from mythic_agent.core.metrics import Metrics, Trace
    m = Metrics()
    with m.timer("agent_turn"):
        ...
    m.counter("tool_calls").inc()
    m.gauge("queue_depth", 4)
    with Trace("turn", tracer=m) as span:
        with Trace("tool_call", tracer=m):
            ...
    print(m.to_json())
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from types import TracebackType
from typing import Any, Iterator


@dataclass
class Timer:
    """Accumulate elapsed seconds over repeated timed blocks."""

    name: str
    count: int = 0
    total_s: float = 0.0
    max_s: float = 0.0

    @property
    def avg_s(self) -> float:
        return self.total_s / self.count if self.count else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {"count": self.count, "total_s": round(self.total_s, 6),
                "avg_s": round(self.avg_s, 6), "max_s": round(self.max_s, 6)}


@dataclass
class Counter:
    name: str
    count: int = 0

    def inc(self, n: int = 1) -> int:
        if n < 0:
            raise ValueError("counter increment must be non-negative")
        self.count += n
        return self.count


@dataclass
class Gauge:
    name: str
    value: float = 0.0


@dataclass
class Span:
    """One node of a trace tree."""

    name: str
    span_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    start: float = field(default_factory=time.monotonic)
    end: float | None = None
    parent_id: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    children: list["Span"] = field(default_factory=list)

    @property
    def duration_s(self) -> float:
        return (self.end - self.start) if self.end is not None else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "span_id": self.span_id,
            "name": self.name,
            "parent_id": self.parent_id,
            "duration_s": round(self.duration_s, 6),
            "attributes": self.attributes,
            "children": [c.to_dict() for c in self.children],
        }


def _span_from_dict(data: dict[str, Any]) -> Span:
    span = Span(
        name=data.get("name", ""),
        span_id=data.get("span_id", ""),
        parent_id=data.get("parent_id"),
        attributes=dict(data.get("attributes") or {}),
    )
    span.children = [_span_from_dict(c) for c in data.get("children") or []]
    return span


_local = threading.local()


class Trace:
    """Context manager recording one span; nests into the active trace.

    The active trace is stored thread-locally, so nested ``with Trace``
    blocks form a parent/child tree.  When the outermost ``Trace`` exits,
    the finished tree is handed to the tracer (default: the most recently
    entered :class:`Metrics` that passed ``tracer=...`` — see
    :meth:`Metrics.trace`).
    """

    def __init__(self, name: str, *, attributes: dict[str, Any] | None = None) -> None:
        self.name = name
        self.attributes = dict(attributes or {})
        self._span = Span(name=name, attributes=dict(attributes or {}))
        self._owner: "Metrics | None" = None
        self._prev: Trace | None = None

    def __enter__(self) -> Span:
        parent = getattr(_local, "current", None)
        if parent is not None:
            self._span.parent_id = parent._span.span_id
            parent._span.children.append(self._span)
            self._owner = parent._owner
        self._prev = parent
        _local.current = self
        return self._span

    def __exit__(self, exc_type: type[BaseException] | None,
                   exc: BaseException | None, tb: TracebackType | None) -> None:
        self._span.end = time.monotonic()
        if exc_type is not None:
            self._span.attributes["error"] = f"{exc_type.__name__}: {exc}"
        _local.current = self._prev
        if self._prev is None and self._owner is not None:
            self._owner._finished_traces.append(self._span)
        return None

    @contextmanager
    def child(self, name: str, **attributes: Any) -> Iterator[Span]:
        with Trace(name, attributes=attributes) as span:
            yield span


class Metrics:
    """In-memory timer/counter/gauge registry plus finished trace trees."""

    def __init__(self) -> None:
        self._timers: dict[str, Timer] = {}
        self._counters: dict[str, Counter] = {}
        self._gauges: dict[str, Gauge] = {}
        self._finished_traces: list[Span] = []
        self._lock = threading.Lock()

    # -- primitives ----------------------------------------------------------
    @contextmanager
    def timer(self, name: str) -> Iterator[None]:
        start = time.monotonic()
        try:
            yield
        finally:
            elapsed = time.monotonic() - start
            with self._lock:
                t = self._timers.setdefault(name, Timer(name=name))
                t.count += 1
                t.total_s += elapsed
                t.max_s = max(t.max_s, elapsed)

    def counter(self, name: str) -> Counter:
        with self._lock:
            return self._counters.setdefault(name, Counter(name=name))

    def gauge(self, name: str, value: float | None = None) -> Gauge:
        with self._lock:
            g = self._gauges.setdefault(name, Gauge(name=name))
            if value is not None:
                g.value = float(value)
            return g

    # -- tracing -------------------------------------------------------------
    @contextmanager
    def trace(self, name: str, **attributes: Any) -> Iterator[Span]:
        """Open a root trace span attached to this Metrics registry."""
        trace = Trace(name, attributes=attributes)
        trace._owner = self
        with trace as span:
            yield span

    @property
    def traces(self) -> list[Span]:
        with self._lock:
            return list(self._finished_traces)

    # -- export --------------------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        with self._lock:
            return {
                "timers": {n: t.to_dict() for n, t in self._timers.items()},
                "counters": {n: c.count for n, c in self._counters.items()},
                "gauges": {n: g.value for n, g in self._gauges.items()},
                "traces": [s.to_dict() for s in self._finished_traces],
            }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Metrics":
        """Rebuild a registry from :meth:`to_dict` output."""
        m = cls()
        for name, t in (data.get("timers") or {}).items():
            timer = m._timers.setdefault(name, Timer(name=name))
            timer.count = int(t.get("count", 0))
            timer.total_s = float(t.get("total_s", 0.0))
            timer.max_s = float(t.get("max_s", 0.0))
        for name, count in (data.get("counters") or {}).items():
            m.counter(name).count = int(count)
        for name, value in (data.get("gauges") or {}).items():
            m.gauge(name, float(value))
        for span_data in data.get("traces") or []:
            m._finished_traces.append(_span_from_dict(span_data))
        return m

    def save(self, path: str | Path) -> Path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(self.to_json(), encoding="utf-8")
        return out

    def render(self) -> str:
        lines = ["Metrics:"]
        data = self.to_dict()
        for name, t in sorted(data["timers"].items()):
            lines.append(
                f"  timer {name}: {t['count']}x, avg {t['avg_s']:.4f}s, max {t['max_s']:.4f}s"
            )
        for name, count in sorted(data["counters"].items()):
            lines.append(f"  counter {name}: {count}")
        for name, value in sorted(data["gauges"].items()):
            lines.append(f"  gauge {name}: {value}")
        lines.append(f"Traces: {len(data['traces'])} finished span tree(s)")
        return "\n".join(lines)
