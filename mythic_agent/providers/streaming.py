"""Streaming normalization (Slice 044).

Raw wire line streams (SSE or line-delimited JSON) are parsed into a
single normalized event stream of :class:`StreamEvent` records:

* ``"text"`` — assistant text delta (``StreamEvent.text``).
* ``"tool_call_delta"`` — tool-call fragment
  (``StreamEvent.tool_call``: ``{"id", "name", "arguments_delta"}``).
* ``"usage"`` — token usage (``StreamEvent.usage``: :class:`ChatUsage`,
  normalized by :mod:`mythic_agent.providers.usage`).
* ``"error"`` — a provider-sent error payload
  (``StreamEvent.error``); parsing stops after it.
* ``"done"`` — end of stream.

Parsers:

* :func:`parse_openai_sse` — ``data: {...}`` lines, ``data: [DONE]``
  terminates. A data payload with an ``"error"`` key emits one
  ``"error"`` event and stops. Malformed JSON raises
  :class:`ProviderError` (a corrupt mid-stream frame is a provider
  failure, not a skippable line).
* :func:`parse_ndjson` — one JSON object per line: ``{"text": ...}``,
  ``{"tool_call_delta": {...}}``, ``{"usage": {...}}``,
  ``{"error": ...}``, ``{"done": true}``.
* :func:`parse_ollama_ndjson` — Ollama's native ``/api/chat`` stream
  shape: ``{"message": {"content": ...}, "done": false}`` per line,
  ``"done": true`` terminates (final line may carry
  ``prompt_eval_count`` / ``eval_count`` usage).

:func:`iter_events` dispatches on the provider family
(``"ollama"`` → Ollama NDJSON; everything else → SSE) so adapters and
tests share one entry point.

Cancellation safety:

* Every parser is a generator: closing it mid-stream (``gen.close()``)
  discards partial state and never raises — partial text already
  yielded is simply lost, which :func:`collect` documents.
* :func:`collect` drains an event stream into text, invoking an
  optional ``cancel`` callable per event; when it returns True,
  :class:`CancelledStream` is raised with the partial text attached.

No network is touched; parsers operate on in-memory line iterables.
Real byte streams come from adapters through the fake-transport seam
in tests.
"""


from __future__ import annotations

__all__ = [
    "CancelledStream",
    "Provider",
    "ProviderError",
    "StreamEvent",
    "collect",
    "iter_events",
    "parse_ndjson",
    "parse_ollama_ndjson",
    "parse_openai_sse",
]

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Iterator, Optional

from .base import ChatUsage, Provider, ProviderError
from . import usage as usage_module


class CancelledStream(ProviderError):
    """A streaming drain was cancelled; ``partial_text`` holds the text
    collected before cancellation."""

    def __init__(self, message: str, partial_text: str = "") -> None:
        super().__init__(message)
        self.partial_text = partial_text


@dataclass
class StreamEvent:
    """One normalized streaming event."""

    #: "text" | "tool_call_delta" | "usage" | "error" | "done".
    kind: str
    #: Text delta (kind == "text").
    text: str = ""
    #: Tool-call fragment (kind == "tool_call_delta"):
    #: {"id": str, "name": str, "arguments_delta": str}.
    tool_call: dict[str, Any] = field(default_factory=dict)
    #: Usage record (kind == "usage").
    usage: Optional[ChatUsage] = None
    #: Provider-sent error message (kind == "error").
    error: str = ""

    def __post_init__(self) -> None:
        if self.kind not in (
                "text", "tool_call_delta", "usage", "error", "done"):
            raise ValueError(f"Unknown stream event kind {self.kind!r}")


def _decode_line(line: str, lineno: int) -> Any:
    try:
        return json.loads(line)
    except ValueError as exc:
        raise ProviderError(
            f"Malformed stream frame on line {lineno}: not valid JSON."
        ) from exc


def parse_openai_sse(lines: Iterable[str]) -> Iterator[StreamEvent]:
    """Parse an OpenAI-style SSE stream into normalized events."""
    for lineno, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line or line.startswith(":"):
            continue  # blank line or SSE comment/ping
        if not line.startswith("data:"):
            raise ProviderError(
                f"Malformed SSE frame on line {lineno}: "
                f"expected 'data:', got {line[:24]!r}")
        data = line[5:].strip()
        if data == "[DONE]":
            yield StreamEvent(kind="done")
            return
        payload = _decode_line(data, lineno)
        if not isinstance(payload, dict):
            raise ProviderError(
                f"Malformed SSE frame on line {lineno}: "
                "expected a JSON object.")
        if "error" in payload:
            detail = payload["error"]
            message = (detail.get("message") if isinstance(detail, dict)
                       else str(detail))
            yield StreamEvent(kind="error", error=str(message))
            return
        if "usage" in payload and not payload.get("choices"):
            yield StreamEvent(
                kind="usage",
                usage=usage_module.normalize_usage_dict(
                    payload["usage"], family="openai"))
            continue
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ProviderError(
                f"Malformed SSE frame on line {lineno}: "
                "expected a 'choices' list.")
        delta = choices[0].get("delta") if isinstance(
            choices[0], dict) else None
        if not isinstance(delta, dict):
            continue  # e.g. role-only delta; nothing to emit
        content = delta.get("content")
        if isinstance(content, str) and content:
            yield StreamEvent(kind="text", text=content)
        tool_calls = delta.get("tool_calls")
        if isinstance(tool_calls, list):
            for fragment in tool_calls:
                if not isinstance(fragment, dict):
                    continue
                function = fragment.get("function") or {}
                yield StreamEvent(kind="tool_call_delta", tool_call={
                    "id": str(fragment.get("id", "")),
                    "name": str(function.get("name", "")),
                    "arguments_delta": str(
                        function.get("arguments", "")),
                })
        finish = choices[0].get("finish_reason")
        if finish in ("stop", "length", "tool_calls"):
            yield StreamEvent(kind="done")
            return


def parse_ndjson(lines: Iterable[str]) -> Iterator[StreamEvent]:
    """Parse generic line-delimited JSON events into normalized events."""
    for lineno, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line:
            continue
        payload = _decode_line(line, lineno)
        if not isinstance(payload, dict):
            raise ProviderError(
                f"Malformed NDJSON frame on line {lineno}: "
                "expected a JSON object.")
        if "error" in payload:
            yield StreamEvent(kind="error", error=str(payload["error"]))
            return
        if payload.get("done"):
            usage_raw = payload.get("usage")
            if isinstance(usage_raw, dict):
                yield StreamEvent(
                    kind="usage",
                    usage=usage_module.normalize_usage_dict(
                        usage_raw, family="openai"))
            yield StreamEvent(kind="done")
            return
        usage_raw = payload.get("usage")
        if isinstance(usage_raw, dict):
            yield StreamEvent(
                kind="usage",
                usage=usage_module.normalize_usage_dict(
                    usage_raw, family="openai"))
        if "text" in payload:
            text = payload["text"]
            if not isinstance(text, str):
                raise ProviderError(
                    f"Malformed NDJSON frame on line {lineno}: "
                    "'text' must be a string.")
            if text:
                yield StreamEvent(kind="text", text=text)
        fragment = payload.get("tool_call_delta")
        if isinstance(fragment, dict):
            yield StreamEvent(kind="tool_call_delta", tool_call={
                "id": str(fragment.get("id", "")),
                "name": str(fragment.get("name", "")),
                "arguments_delta": str(fragment.get("arguments_delta", "")),
            })


def parse_ollama_ndjson(lines: Iterable[str]) -> Iterator[StreamEvent]:
    """Parse Ollama's native ``/api/chat`` stream into normalized events."""
    for lineno, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line:
            continue
        payload = _decode_line(line, lineno)
        if not isinstance(payload, dict):
            raise ProviderError(
                f"Malformed Ollama frame on line {lineno}: "
                "expected a JSON object.")
        if "error" in payload:
            yield StreamEvent(kind="error", error=str(payload["error"]))
            return
        message = payload.get("message") or {}
        content = message.get("content") if isinstance(message, dict) else ""
        if isinstance(content, str) and content:
            yield StreamEvent(kind="text", text=content)
        if payload.get("done"):
            yield StreamEvent(
                kind="usage",
                usage=usage_module.normalize_usage_dict(payload,
                                                        family="ollama"))
            yield StreamEvent(kind="done")
            return


def iter_events(provider: Provider,
                raw_lines: Iterable[str]) -> Iterator[StreamEvent]:
    """Yield normalized events for ``provider`` from ``raw_lines``.

    Family dispatch: ``"ollama"`` uses the Ollama NDJSON parser; all
    other adapters use the OpenAI SSE parser.
    """
    name = (getattr(provider, "name", "") or "").lower()
    if name == "ollama":
        yield from parse_ollama_ndjson(raw_lines)
    else:
        yield from parse_openai_sse(raw_lines)


def collect(
    events: Iterable[StreamEvent],
    *,
    cancel: Optional[Callable[[], bool]] = None,
    on_event: Optional[Callable[[StreamEvent], None]] = None,
) -> str:
    """Drain ``events`` into the concatenated assistant text.

    ``cancel`` is consulted after every event; when it returns True,
    :class:`CancelledStream` is raised carrying the partial text.
    ``on_event`` observes each event (logging, metrics). A provider
    ``"error"`` event raises :class:`ProviderError`.
    """
    parts: list[str] = []
    for event in events:
        if on_event is not None:
            on_event(event)
        if event.kind == "text":
            parts.append(event.text)
        elif event.kind == "error":
            raise ProviderError(
                f"Provider stream error: {event.error or 'unknown error'}")
        if cancel is not None and cancel():
            raise CancelledStream(
                "Stream collection cancelled by caller.",
                partial_text="".join(parts))
    return "".join(parts)
