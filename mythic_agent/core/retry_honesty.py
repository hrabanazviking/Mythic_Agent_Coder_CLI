"""Retry and backoff honesty (All-Features roadmap slice M-035).

Part II — The Provider Ocean — gives its retry road an honest
record here: bounded retries on transient failures only, and
mutating calls never silently replayed (the house rule from
Sagnaskemma's hardening, applied here).

What already shipped, and what this slice adds:

* ``Agent._request_response`` / ``Agent._request_streaming``
  (``mythic_agent.agents.llm``) already retried provider
  requests with a bounded budget: connection errors and HTTP
  408/409/429/5xx were retried with capped exponential backoff
  (a numeric Retry-After hint wins, capped), streaming retries
  only before the first chunk, and the provider transport
  (``mythic_agent.providers.openai_compat``) already retried
  its POST on retriable statuses — but the only trace was a
  vague "Provider temporarily unavailable; retry N." line, and
  nothing recorded *why* a retry happened, how long the wait
  was, or why retrying stopped.
* This slice is the honest record. The pure layer lives here:
  the failure classifier (duck-typed, agreeing with the agent
  layer's historical classification), the delay arithmetic,
  the named bounds a settings dict implies, the retry events
  and per-request report the agent layer records and journals,
  the replay boundaries that state — with source anchors the
  tests grep for — why no retry path can re-execute a tool
  call or any other mutating call, and the plain-words
  surfaces the terminal and the TUI share. The agent layer
  owns the live loops: it records events through
  :class:`RetryRecorder`, publishes the formatted event
  sentence for each retry, journals ``retry_attempt`` /
  ``retry_stopped`` session events, and keeps the finished
  report as ``Agent.last_retry_report``.

Honesty rules, enforced here and pinned by the slice's tests:

* **Retries are bounded.** The budget is the configured
  ``max_retries``: at most that many retries, at most
  ``max_retries + 1`` attempts, and the waits are capped —
  the planned wait and the worst-case wait are both named
  by :func:`bounds_from_settings`, never hidden.
* **Only temporary failures are retried.** A connection
  problem, or HTTP 408, 409, 429, or any 5xx status. Auth,
  bad-request, and other permanent failures stop at once.
* **Every retry is announced with its reason and its wait,**
  and why retrying stopped is recorded in the report.
* **Mutating calls are never silently replayed.** A retry
  repeats only a provider *request* that produced no usable
  response; a tool call executes exactly once, after one
  returned response, in the agent layer — see
  :data:`REPLAY_BOUNDARIES`.
"""

from __future__ import annotations

__all__ = [
    "MUTATING_RULE",
    "PLAIN_EXPLANATION",
    "REPLAY_BOUNDARIES",
    "RETRY_DECISIONS",
    "RETRY_SLICE",
    "STOPPED_REASONS",
    "TRANSIENT_STATUSES",
    "Any",
    "Dict",
    "FailureClass",
    "List",
    "Optional",
    "ReplayBoundary",
    "RetryBounds",
    "RetryEvent",
    "RetryRecorder",
    "RetryReport",
    "Tuple",
    "bounds_from_settings",
    "classify_error",
    "delay_for",
    "format_replay_boundaries",
    "format_retry_event",
    "format_retry_report",
    "format_retry_status",
    "is_transient_error",
    "parse_retry_args",
    "retry_after_seconds",
    "status_is_transient",
]

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

#: The slice that owns this module.
RETRY_SLICE = "M-035"

#: Retry honesty explained in plain words — the text every
#: surface shows. Retries are bounded, only for temporary
#: failures, each one announced, and the stop reason recorded.
PLAIN_EXPLANATION = (
    "Retry honesty: when a provider request fails in a "
    "temporary way — a connection problem, or the provider "
    "answering 408, 409, 429, or a 5xx status — Mythic may "
    "try again, but only a bounded number of times (the "
    "configured retry budget), and each retry is announced "
    "with its reason and how long the wait will be. Permanent "
    "failures — a bad key, a bad request, a missing model — "
    "are never retried. Why retrying stopped is recorded in "
    "the retry report (see /retry). A tool call, or any other "
    "mutating call, is never silently replayed: a retry only "
    "repeats a provider request that produced no usable "
    "response, and tool calls run exactly once, after one "
    "response has been returned."
)

#: The house rule, carried verbatim: Sagnaskemma's hardening
#: rule, applied here.
MUTATING_RULE = "Mutating calls are never silently replayed."

#: The HTTP statuses that are always transient on their own.
#: Any 5xx status is transient too (see
#: :func:`status_is_transient`).
TRANSIENT_STATUSES = frozenset({408, 409, 429})


def status_is_transient(status: Any) -> bool:
    """True when HTTP *status* names a temporary failure.

    True for 408, 409, and 429, and for any status in the
    500–599 range. False for None, for non-integers (bools
    included), and for every other status — 2xx, 3xx, and the
    permanent 4xx failures (400, 401, 403, 404, 422, …) are
    never retried.
    """
    if isinstance(status, bool) or not isinstance(status, int):
        return False
    return status in TRANSIENT_STATUSES or 500 <= status <= 599


# ----------------------------------------------------------------------
# Failure classification — duck-typed, no provider imports
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class FailureClass:
    """How one failure is classified for retry purposes.

    ``kind`` is ``"connection"`` (no response ever arrived),
    ``"status"`` (the provider answered with an HTTP status),
    or ``"other"``. ``status`` is the integer HTTP status for
    a status failure, else None. ``transient`` says whether
    the failure may be retried at all.
    """

    kind: str
    status: Optional[int]
    transient: bool

    def record(self) -> Dict[str, Any]:
        """This classification as a plain mapping."""
        return {"kind": self.kind, "status": self.status,
                "transient": self.transient}


def classify_error(exc: Any) -> FailureClass:
    """Classify *exc* for retry purposes, by duck-typing.

    An integer ``status_code`` attribute makes a status
    failure, transient exactly when
    :func:`status_is_transient` says so. An exception whose
    type (or any base type) is named ``APIConnectionError``,
    or a builtin :class:`ConnectionError` / :class:`TimeoutError`,
    is a connection failure and always transient. Everything
    else is ``"other"`` and never transient. This agrees with
    the agent layer's historical classification
    (``Agent``'s ``_is_transient``) on real provider errors.
    """
    status = getattr(exc, "status_code", None)
    if isinstance(status, int) and not isinstance(status, bool):
        return FailureClass(kind="status", status=status,
                            transient=status_is_transient(status))
    type_names = {cls.__name__ for cls in type(exc).__mro__}
    if "APIConnectionError" in type_names or isinstance(
            exc, (ConnectionError, TimeoutError)):
        return FailureClass(kind="connection", status=None,
                            transient=True)
    return FailureClass(kind="other", status=None, transient=False)


def is_transient_error(exc: Any) -> bool:
    """True when *exc* is a temporary failure that may be retried."""
    return classify_error(exc).transient


# ----------------------------------------------------------------------
# Delay arithmetic — a numeric Retry-After hint wins, capped
# ----------------------------------------------------------------------


def retry_after_seconds(exc: Any) -> Optional[float]:
    """Bounded Retry-After hint in seconds, or None.

    Only the numeric (delay-seconds) form is honored; HTTP-date
    forms are ignored rather than misinterpreted.
    """
    try:
        headers = getattr(getattr(exc, "response", None), "headers", None)
        if not headers:
            return None
        value = headers.get("retry-after")
        if value is None:
            return None
        return max(0.0, float(value))
    except (TypeError, ValueError):
        return None


def _setting(settings: Any, key: str, default: Any = None) -> Any:
    if isinstance(settings, dict):
        return settings.get(key, default)
    return getattr(settings, key, default)


def delay_for(exc: Any, attempt: int, settings: Any) -> float:
    """Capped backoff for one retry: a server hint wins.

    *settings* is a settings mapping (or any object) carrying
    ``retry_delay`` and ``retry_delay_cap``. When *exc*
    carries a numeric Retry-After hint, the delay is that
    hint capped at ``retry_delay_cap``; otherwise it is
    ``retry_delay * 2 ** attempt``, likewise capped.
    """
    cap = _setting(settings, "retry_delay_cap")
    hinted = retry_after_seconds(exc)
    if hinted is not None:
        return min(cap, hinted)
    return min(cap, _setting(settings, "retry_delay") * 2 ** attempt)


# ----------------------------------------------------------------------
# Bounds — what a settings dict honestly promises
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class RetryBounds:
    """The named bounds implied by the retry settings.

    ``max_attempts`` is ``max_retries + 1`` (the first try
    plus every retry). ``planned_wait_total`` is the sum of
    the ordinary backoff waits — what a fully-retried request
    waits when no server hint intervenes.
    ``worst_case_wait_total`` is ``retry_delay_cap *
    max_retries``: a server hint could raise every wait to
    the cap, and no wait can exceed it.
    """

    max_retries: int
    max_attempts: int
    retry_delay: float
    retry_delay_cap: float
    planned_wait_total: float
    worst_case_wait_total: float

    def record(self) -> Dict[str, Any]:
        """These bounds as a plain mapping."""
        return {
            "max_retries": self.max_retries,
            "max_attempts": self.max_attempts,
            "retry_delay": self.retry_delay,
            "retry_delay_cap": self.retry_delay_cap,
            "planned_wait_total": self.planned_wait_total,
            "worst_case_wait_total": self.worst_case_wait_total,
        }


def bounds_from_settings(settings: Any) -> RetryBounds:
    """The :class:`RetryBounds` implied by *settings*.

    *settings* carries ``max_retries``, ``retry_delay``, and
    ``retry_delay_cap`` (the runtime settings). A negative
    ``max_retries`` or a non-positive delay or cap raises
    :class:`ValueError` — a budget that cannot be stated
    honestly is refused, never guessed at.
    """
    max_retries = _setting(settings, "max_retries", 2)
    retry_delay = _setting(settings, "retry_delay", 0.5)
    retry_delay_cap = _setting(settings, "retry_delay_cap", 8.0)
    if isinstance(max_retries, bool) or not isinstance(max_retries, int):
        raise ValueError(
            f"max_retries must be an integer, "
            f"got {type(max_retries).__name__}")
    if max_retries < 0:
        raise ValueError(
            f"max_retries must not be negative, got {max_retries}")
    for name, value in (("retry_delay", retry_delay),
                        ("retry_delay_cap", retry_delay_cap)):
        if isinstance(value, bool) or not isinstance(value, (int, float)) \
                or value <= 0:
            raise ValueError(
                f"{name} must be a positive number, got {value!r}")
    planned = sum(
        min(retry_delay_cap, retry_delay * 2 ** attempt)
        for attempt in range(max_retries))
    return RetryBounds(
        max_retries=max_retries,
        max_attempts=max_retries + 1,
        retry_delay=float(retry_delay),
        retry_delay_cap=float(retry_delay_cap),
        planned_wait_total=float(planned),
        worst_case_wait_total=float(retry_delay_cap * max_retries),
    )


# ----------------------------------------------------------------------
# Events and the per-request report
# ----------------------------------------------------------------------

#: Why one retry decision was taken. ``retrying`` means
#: another attempt follows after ``delay``; the ``stopped-*``
#: values name why no further attempt happens.
RETRY_DECISIONS = (
    "retrying",
    "stopped-not-transient",
    "stopped-budget-exhausted",
    "stopped-partial-streamed",
    "stopped-cancelled",
)

#: The fixed vocabulary for a finished report's stop reason:
#: ``succeeded`` (a response was returned), ``not-transient``
#: (a permanent failure, never retried), ``budget-exhausted``
#: (temporary failures used up the retry budget),
#: ``partial-streamed`` (part of a streamed answer had
#: already been emitted, so the request was not replayed),
#: ``cancelled`` (the turn was cancelled during the wait),
#: and ``failed`` (any other failure of the request).
STOPPED_REASONS = (
    "succeeded",
    "not-transient",
    "budget-exhausted",
    "partial-streamed",
    "cancelled",
    "failed",
)


@dataclass(frozen=True)
class RetryEvent:
    """One retry decision for one provider request.

    ``attempt`` is the retry number, 1-based: retry 1 is the
    second try of the request. ``limit`` is the request's
    ``max_retries``. ``kind`` / ``status`` come from
    :func:`classify_error`; ``error`` is the failure's text;
    ``delay`` is the wait before the next attempt when
    ``decision`` is ``"retrying"``, else None.
    """

    attempt: int
    limit: int
    kind: str
    status: Optional[int]
    error: str
    delay: Optional[float]
    decision: str

    def record(self) -> Dict[str, Any]:
        """This event as a plain mapping (the journal shape)."""
        return {"attempt": self.attempt, "limit": self.limit,
                "kind": self.kind, "status": self.status,
                "error": self.error, "delay": self.delay,
                "decision": self.decision}


def _reason_phrase(event: RetryEvent) -> str:
    if event.kind == "connection":
        return "the provider connection failed"
    if event.kind == "status":
        return f"the provider returned HTTP {event.status}"
    return f"the request failed ({event.error})" if event.error \
        else "the request failed"


_STOP_PHRASES = {
    "stopped-not-transient": (
        "stopped because the failure is not temporary, "
        "so it is never retried"),
    "stopped-budget-exhausted": (
        "stopped because the retry budget is exhausted"),
    "stopped-partial-streamed": (
        "stopped because part of the answer had already "
        "streamed, and a partial answer is never replayed"),
    "stopped-cancelled": (
        "stopped because the turn was cancelled"),
}


def format_retry_event(event: RetryEvent) -> str:
    """One plain sentence: the decision, its reason, its wait.

    A retrying event names the retry number and budget, why
    the request is being retried, and the wait. A stopped
    event names why retrying stopped.
    """
    head = f"Retry {event.attempt} of {event.limit}: "
    if event.decision == "retrying":
        wait = event.delay if event.delay is not None else 0.0
        return (
            head + f"{_reason_phrase(event)} "
            f"({event.error}); waiting {wait:g} seconds "
            "before trying again.")
    phrase = _STOP_PHRASES.get(
        event.decision, "stopped")
    if event.kind == "status":
        why = f"the provider returned HTTP {event.status} ({event.error})"
    elif event.kind == "connection":
        why = f"the provider connection failed ({event.error})"
    else:
        why = f"the request failed ({event.error})"
    return head + f"not retrying — {phrase}: {why}."


@dataclass(frozen=True)
class RetryReport:
    """The finished record of one provider request's retries.

    ``events`` are the request's retry decisions in order;
    ``retries_used`` counts the ``retrying`` decisions;
    ``attempts_made`` counts every try of the request;
    ``stopped_reason`` is one of :data:`STOPPED_REASONS`;
    ``succeeded`` is True exactly when a response was
    returned (``stopped_reason == "succeeded"``).
    """

    events: Tuple[RetryEvent, ...]
    retries_used: int
    attempts_made: int
    stopped_reason: str
    succeeded: bool

    def record(self) -> Dict[str, Any]:
        """This report as a plain mapping."""
        return {
            "events": [event.record() for event in self.events],
            "retries_used": self.retries_used,
            "attempts_made": self.attempts_made,
            "stopped_reason": self.stopped_reason,
            "succeeded": self.succeeded,
        }


class RetryRecorder:
    """The agent layer's simple per-request event recorder.

    Record each decision with :meth:`record`; close the
    request out with :meth:`finish`, which builds (and keeps)
    the :class:`RetryReport`. :attr:`report` is the finished
    report, or None while the request is still running.
    """

    def __init__(self) -> None:
        self._events: List[RetryEvent] = []
        self._report: Optional[RetryReport] = None

    def record(self, event: RetryEvent) -> RetryEvent:
        """Append *event* to this request's record."""
        if event.decision not in RETRY_DECISIONS:
            raise ValueError(
                f"Unknown retry decision {event.decision!r}; "
                "the decisions are: " + ", ".join(RETRY_DECISIONS) + ".")
        self._events.append(event)
        return event

    @property
    def events(self) -> Tuple[RetryEvent, ...]:
        """The events recorded so far, in order."""
        return tuple(self._events)

    @property
    def report(self) -> Optional[RetryReport]:
        """The finished report, or None before :meth:`finish`."""
        return self._report

    def finish(self, stopped_reason: str,
               attempts_made: int) -> RetryReport:
        """Close the request out and return its report."""
        if stopped_reason not in STOPPED_REASONS:
            raise ValueError(
                f"Unknown stopped reason {stopped_reason!r}; "
                "the reasons are: " + ", ".join(STOPPED_REASONS) + ".")
        retries_used = sum(
            1 for event in self._events if event.decision == "retrying")
        self._report = RetryReport(
            events=tuple(self._events),
            retries_used=retries_used,
            attempts_made=attempts_made,
            stopped_reason=stopped_reason,
            succeeded=stopped_reason == "succeeded")
        return self._report


_REPORT_PHRASES = {
    "succeeded": "the request succeeded",
    "not-transient": (
        "the failure was not temporary, so it was not retried"),
    "budget-exhausted": "the retry budget was exhausted",
    "partial-streamed": (
        "part of the answer had already streamed, "
        "so the request was not replayed"),
    "cancelled": "the turn was cancelled",
    "failed": "the request failed",
}


def format_retry_report(report: Optional[RetryReport]) -> str:
    """The report in plain words: what happened, and why it stopped.

    None (no request has finished) renders the plain
    no-retry-yet sentence the status surface also uses.
    """
    if report is None:
        return ("No provider request has been retried yet "
                "in this session.")
    phrase = _REPORT_PHRASES.get(report.stopped_reason,
                                 report.stopped_reason)
    lines = [
        f"Last provider request: {report.attempts_made} "
        f"attempt(s) made, {report.retries_used} retry(ies) "
        f"used — {phrase} "
        f"(stopped reason: {report.stopped_reason}).",
    ]
    for event in report.events:
        lines.append("  " + format_retry_event(event))
    return "\n".join(lines)


# ----------------------------------------------------------------------
# Replay boundaries — why no retry can re-execute a mutating call
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class ReplayBoundary:
    """One retry-capable path, and why it cannot replay a call.

    ``anchors`` are literal strings the slice's tests grep
    for in the live source files named by ``files`` (parallel
    to ``anchors``): the boundary is pinned to the real code,
    not to a description of it.
    """

    name: str
    path_label: str
    rule: str
    anchors: Tuple[str, ...]
    files: Tuple[str, ...] = ()


#: Every retry-capable path in the package, in walk order,
#: with the reason it cannot re-execute a mutating call.
REPLAY_BOUNDARIES: Tuple[ReplayBoundary, ...] = (
    ReplayBoundary(
        name="agent-non-streaming-request",
        path_label=(
            "Agent non-streaming request retry — "
            "mythic_agent/agents/llm.py (Agent._request_response)"),
        rule=(
            "The retry happens before any response is "
            "returned: the loop repeats only the model "
            "request, and no tool call from that request "
            "exists yet, so nothing has run that could "
            "be replayed."),
        anchors=("def _request_response",
                 "client.chat.completions.create"),
        files=("mythic_agent/agents/llm.py",
               "mythic_agent/agents/llm.py"),
    ),
    ReplayBoundary(
        name="agent-streaming-request",
        path_label=(
            "Agent streaming request retry — "
            "mythic_agent/agents/llm.py (Agent._request_streaming)"),
        rule=(
            "The retry happens only before the first chunk: "
            "once any part of the answer has been emitted "
            "(accumulator.emitted), the request is never "
            "retried, so an emitted partial is never "
            "replayed and no tool fragment from it can "
            "execute twice."),
        anchors=("def _request_streaming", "accumulator.emitted"),
        files=("mythic_agent/agents/llm.py",
               "mythic_agent/agents/llm.py"),
    ),
    ReplayBoundary(
        name="provider-transport",
        path_label=(
            "Provider transport retry — "
            "mythic_agent/providers/openai_compat.py "
            "(_request_with_retries)"),
        rule=(
            "The transport repeats only the model request "
            "POST on a retriable status. No tool execution "
            "exists in that layer at all: tools execute "
            "only in the agent layer, after one returned "
            "response."),
        anchors=("_request_with_retries", "RETRIABLE_STATUSES"),
        files=("mythic_agent/providers/openai_compat.py",
               "mythic_agent/providers/openai_compat.py"),
    ),
    ReplayBoundary(
        name="fallback-walk",
        path_label=(
            "Fallback walk — "
            "mythic_agent/agents/llm.py (Agent._walk_fallback)"),
        rule=(
            "The walk repeats only the model request on "
            "the next door, through _request_response. "
            "Tool results already in the history belong "
            "to finished rounds and are never re-executed; "
            "the new door's response is the only one whose "
            "calls can run."),
        anchors=("def _walk_fallback", "_request_response"),
        files=("mythic_agent/agents/llm.py",
               "mythic_agent/agents/llm.py"),
    ),
    ReplayBoundary(
        name="tool-execution",
        path_label=(
            "Tool execution itself — "
            "mythic_agent/agents/llm.py (Agent._execute_call) "
            "and mythic_agent/core/execution.py"),
        rule=(
            "In the agent's turn loop, execute_tool is "
            "called from exactly one site (_execute_call), "
            "once per returned tool call, and the execution "
            "layer's own provider client passes "
            "max_retries=0 — tool execution is never itself "
            "retried or replayed by any retry loop."),
        anchors=("def _execute_call", "max_retries=0"),
        files=("mythic_agent/agents/llm.py",
               "mythic_agent/core/execution.py"),
    ),
)


def format_replay_boundaries() -> str:
    """The replay boundaries in plain words, one block each."""
    lines = ["  Replay boundaries — " + MUTATING_RULE]
    for boundary in REPLAY_BOUNDARIES:
        lines.append(f"    {boundary.name} — {boundary.path_label}")
        lines.append(f"      {boundary.rule}")
    return "\n".join(lines)


# ----------------------------------------------------------------------
# The /retry grammar + the status surface
# ----------------------------------------------------------------------


def parse_retry_args(args: Any) -> Dict[str, Any]:
    """Parse the ``/retry`` slash-command argument string.

    Grammar::

        /retry        -> show the retry status
        /retry show   -> show the retry status

    Returns ``{"action": "show"}``. Anything else raises
    :class:`ValueError` with the usage line.
    """
    if args is None:
        args = ""
    if not isinstance(args, str):
        raise ValueError("Usage: /retry | /retry show")
    stripped = args.strip().lower()
    if stripped in ("", "show"):
        return {"action": "show"}
    raise ValueError("Usage: /retry | /retry show")


def format_retry_status(bounds: RetryBounds,
                        report: Optional[RetryReport]) -> str:
    """The visible status: explanation, bounds, rule, last report.

    Shows the plain explanation, the named bounds the current
    settings imply, the mutating rule, the replay boundaries,
    and the last request's report — or, when no request has
    been retried yet in this session, that plain sentence.
    """
    lines = [
        PLAIN_EXPLANATION,
        "  Retry bounds (from the current settings):",
        f"    max_retries: {bounds.max_retries} "
        f"(at most {bounds.max_attempts} attempt(s) per request)",
        f"    retry_delay: {bounds.retry_delay:g} seconds "
        "(the first wait; each later wait doubles)",
        f"    retry_delay_cap: {bounds.retry_delay_cap:g} seconds "
        "(no single wait is longer than this)",
        f"    planned_wait_total: {bounds.planned_wait_total:g} "
        "seconds (all ordinary waits added together)",
        f"    worst_case_wait_total: "
        f"{bounds.worst_case_wait_total:g} seconds "
        "(if every wait rose to the cap on a server hint)",
        "  " + MUTATING_RULE,
        format_replay_boundaries(),
    ]
    if report is None:
        lines.append(
            "  No provider request has been retried yet "
            "in this session.")
    else:
        lines.append("  " + format_retry_report(report))
    return "\n".join(lines)
