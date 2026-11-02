"""Rate-limit weather (All-Features roadmap slice M-036).

Part II — The Provider Ocean — stops treating rate limits as
weather that is only discovered by flying into it. The
roadmap's three promises live here:

* **Per-provider quota/limit state** — recorded from *real*
  limit signals only: a 429 answer, the limit headers a door
  actually returns, and successes (a door that just answered
  is, at that moment, not limiting us). What no signal has
  ever said stays **unknown**, never guessed.
* **Surfaced before it bites** — the state is shown in plain
  words by :func:`format_weather_status` (the ``/weather``
  surface on the terminal and the TUI), naming for each door
  whether it is limited, until when, what quota the door
  itself reported, and what is simply not known.
* **Queueing of crew work around it** — :func:`queue_decision`
  says, for one door, whether work proceeds or waits for the
  reset, and :func:`plan_crew_work` partitions a batch of
  crew work into the work that can go now and the work held
  for a limited door. The agent layer applies the decision
  to every request it sends (crew members are Agents, so
  crew work rides the same queue): a request for a door
  whose weather says limited-with-a-known-reset is held —
  announced and journaled — until the reset, cancellably,
  up to :data:`QUEUE_MAX_WAIT_S`; beyond that cap, or when
  the reset is unknown, the request proceeds and the
  M-035 retries / M-030 fallback walk handle what comes —
  queueing for an unknown or far-off time would be a
  deadlock dressed as politeness, and the weather is still
  surfaced first.

What already shipped, and what this slice adds:

* 429s already fed M-035's retries (``core/retry_honesty``)
  and M-030's fallback walk (``core/fallback_chain``) *after*
  a request had failed, and ``providers/health.py`` keeps
  sliding-window success/latency scores — but no limit state
  was kept anywhere: no limit header but Retry-After was
  read, nothing recorded when a provider last limited or
  when it resets, and no surface showed the weather.
* This slice is that missing record. The pure layer lives
  here: the header parser for the doors' real header
  families, the signal/weather/board types, the queue
  decision and crew planner, and the plain-words surfaces
  the terminal and the TUI share. The board every agent in
  a crew records into is shared (:func:`shared_board`), so
  one member's 429 is the whole crew's weather.

Honesty rules, enforced here and pinned by the slice's tests:

* **Only real signals are recorded.** A 429, a limit header
  a door actually sent, a success. Nothing is inferred from
  a model name, a plan name, or a vendor's marketing page.
* **Unknown stays unknown.** A door no signal has described
  has weather ``unknown`` — which is *not* a limit: work for
  it proceeds, and the surface says plainly that its weather
  is unknown.
* **A reported number is the door's own number.** Quota
  figures are stored exactly as the headers carried them;
  an unparseable header value is recorded as unknown, never
  coerced into a plausible figure.
* **Weather expires honestly.** A limited door whose reset
  time has passed is no longer reported limited; a success
  clears a limit at once (the door demonstrably answered).
* **Queueing is bounded and announced.** A wait never
  exceeds :data:`QUEUE_MAX_WAIT_S`, every queued request is
  announced with its door and its wait, and the wait is
  cancellable — a cancelled queue sends nothing.
"""

from __future__ import annotations

__all__ = [
    "PLAIN_EXPLANATION",
    "QUEUE_MAX_WAIT_S",
    "WEATHER_SLICE",
    "WEATHER_STATES",
    "Any",
    "Dict",
    "LimitSignal",
    "List",
    "Optional",
    "ProviderWeather",
    "QueueDecision",
    "Tuple",
    "WeatherBoard",
    "format_queue_plan",
    "format_weather",
    "format_weather_status",
    "parse_duration_seconds",
    "parse_limit_headers",
    "parse_reset_value",
    "parse_weather_args",
    "plan_crew_work",
    "queue_decision",
    "shared_board",
    "signal_from_error",
    "signal_from_headers",
    "weather_key_for",
]

import re
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

#: The slice that owns this module.
WEATHER_SLICE = "M-036"

#: The longest a request will queue around a known limit.
#: Beyond this, the request proceeds (M-035/M-030 handle the
#: outcome) rather than parking the session.
QUEUE_MAX_WAIT_S = 600.0

#: The weather vocabulary. ``unknown`` is a first-class
#: state, never a synonym for clear or limited.
WEATHER_STATES = ("unknown", "clear", "limited")

#: Rate-limit weather explained in plain words — the text
#: every surface shows.
PLAIN_EXPLANATION = (
    "Rate-limit weather: Mythic remembers what each "
    "provider door has actually told it about its limits — "
    "a 429 answer, the quota headers the door itself sends, "
    "and successes. /weather shows, per door, whether it is "
    "limited and until when, what quota the door reported, "
    "and what is simply unknown (unknown is not a limit and "
    "never blocks work). Before a request is sent to a door "
    "whose weather says it is limited until a known reset "
    "time, the request is queued around the limit — held, "
    "announced, and cancellable, for at most "
    f"{int(QUEUE_MAX_WAIT_S)} seconds; if the wait would be "
    "longer, or the door never said when the limit resets, "
    "the request goes ahead and the retry and fallback "
    "machinery handles what comes. Crew members share one "
    "weather board, so one member's limit is the whole "
    "crew's weather."
)


# ----------------------------------------------------------------------
# Header parsing — only what a door actually sent
# ----------------------------------------------------------------------

#: Header families as name templates (``{quota}`` is
#: ``requests`` or ``tokens``). The two families order their
#: parts differently — OpenAI's is ``x-ratelimit-limit-…``
#: while Anthropic's is ``anthropic-ratelimit-…-limit`` — so
#: each part is a full template, never a shared prefix game.
_HEADER_FAMILIES = (
    ("anthropic-ratelimit-{quota}-limit",
     "anthropic-ratelimit-{quota}-remaining",
     "anthropic-ratelimit-{quota}-reset"),
    ("x-ratelimit-limit-{quota}",
     "x-ratelimit-remaining-{quota}",
     "x-ratelimit-reset-{quota}"),
)

_DURATION_PART = re.compile(r"(\d+(?:\.\d+)?)\s*(ms|s|m|h)")
_DURATION_UNITS = {"ms": 0.001, "s": 1.0, "m": 60.0, "h": 3600.0}


def parse_duration_seconds(value: Any) -> Optional[float]:
    """Parse a provider reset duration (``"6m0s"``, ``"1s"``).

    Returns seconds, or None when the value is not a
    duration this parser can read exactly — never a guess.
    """
    if not isinstance(value, str):
        return None
    text = value.strip().lower()
    if not text:
        return None
    total = 0.0
    pos = 0
    matched = False
    for match in _DURATION_PART.finditer(text):
        if text[pos:match.start()].strip():
            return None
        total += float(match.group(1)) * _DURATION_UNITS[match.group(2)]
        pos = match.end()
        matched = True
    if not matched or text[pos:].strip():
        return None
    return total


def parse_reset_value(value: Any, *, now: float) -> Optional[float]:
    """Parse a quota-reset header value into epoch seconds.

    Honoured forms, each read exactly: an ISO-8601 timestamp,
    a duration string (``"6m0s"`` — relative to *now*), a
    large number (epoch seconds), and a small number
    (seconds from *now*). Anything else is None — unknown,
    never coerced.
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        return number if number > 1_000_000_000 else now + number
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    if "T" in text or text.endswith("Z"):
        try:
            stamp = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=timezone.utc)
        return stamp.timestamp()
    duration = parse_duration_seconds(text)
    if duration is not None:
        return now + duration
    try:
        number = float(text)
    except ValueError:
        return None
    return number if number > 1_000_000_000 else now + number


def _header_int(headers: Dict[str, Any], name: str) -> Optional[int]:
    value = headers.get(name)
    if value is None:
        return None
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return None


def parse_limit_headers(headers: Any, *, now: float) -> Dict[str, Any]:
    """Read the limit fields out of a door's response headers.

    Looks for the two header families the doors in the
    registry actually use (OpenAI-style ``x-ratelimit-*`` and
    Anthropic-style ``anthropic-ratelimit-*``), for both the
    requests and the tokens quota. Every field that is
    absent — or present but unreadable — comes back None:
    unknown, never invented. Also reads ``retry-after``
    (numeric seconds only, per M-035's rule).
    """
    result: Dict[str, Any] = {
        "limit_requests": None,
        "remaining_requests": None,
        "limit_tokens": None,
        "remaining_tokens": None,
        "reset_at": None,
        "retry_after_s": None,
    }
    if not headers:
        return result
    try:
        lowered = {str(k).lower(): v for k, v in dict(headers).items()}
    except (TypeError, ValueError):
        return result
    for limit_t, remaining_t, reset_t in _HEADER_FAMILIES:
        for quota, field_limit, field_remaining in (
                ("requests", "limit_requests", "remaining_requests"),
                ("tokens", "limit_tokens", "remaining_tokens")):
            if result[field_limit] is None:
                result[field_limit] = _header_int(
                    lowered, limit_t.format(quota=quota))
            if result[field_remaining] is None:
                result[field_remaining] = _header_int(
                    lowered, remaining_t.format(quota=quota))
            if result["reset_at"] is None:
                raw_reset = lowered.get(reset_t.format(quota=quota))
                if raw_reset is not None:
                    result["reset_at"] = parse_reset_value(
                        raw_reset, now=now)
    retry_after = lowered.get("retry-after")
    if retry_after is not None:
        try:
            result["retry_after_s"] = max(0.0, float(
                str(retry_after).strip()))
        except (TypeError, ValueError):
            result["retry_after_s"] = None
    return result


# ----------------------------------------------------------------------
# Signals and weather
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class LimitSignal:
    """One real limit signal, exactly as it was observed.

    ``kind`` is ``"limited"`` (a 429), ``"quota"`` (limit
    headers without a 429), or ``"success"`` (the door
    answered). Quota figures are the door's own numbers or
    None; ``reset_at`` is epoch seconds or None.
    """

    provider: str
    kind: str
    observed_at: float
    source: str
    limit_requests: Optional[int] = None
    remaining_requests: Optional[int] = None
    limit_tokens: Optional[int] = None
    remaining_tokens: Optional[int] = None
    reset_at: Optional[float] = None
    retry_after_s: Optional[float] = None


def signal_from_headers(headers: Any, provider: str, *,
                        now: float) -> Optional[LimitSignal]:
    """Build a quota signal from response headers, if any.

    Returns None when the headers carry no limit field at
    all — a door that said nothing about limits has told us
    nothing, and nothing is recorded.
    """
    fields = parse_limit_headers(headers, now=now)
    if all(value is None for value in fields.values()):
        return None
    return LimitSignal(
        provider=provider, kind="quota", observed_at=now,
        source="headers", **fields)


def signal_from_error(exc: Any, provider: str, *,
                      now: float) -> Optional[LimitSignal]:
    """Build a signal from a failed provider request.

    A 429 is a ``"limited"`` signal (carrying whatever limit
    headers rode along); any other failure carrying limit
    headers is a ``"quota"`` signal; anything else is None.
    The error's status and headers are read duck-typed, the
    same way M-035 reads Retry-After.
    """
    status = getattr(exc, "status_code", None)
    if status is None:
        status = getattr(
            getattr(exc, "response", None), "status_code", None)
    headers = getattr(
        getattr(exc, "response", None), "headers", None)
    fields = parse_limit_headers(headers, now=now)
    if status == 429:
        return LimitSignal(
            provider=provider, kind="limited", observed_at=now,
            source="status-429", **fields)
    if all(value is None for value in fields.values()):
        return None
    return LimitSignal(
        provider=provider, kind="quota", observed_at=now,
        source="headers", **fields)


@dataclass
class ProviderWeather:
    """The recorded weather for one provider door."""

    provider: str
    state: str = "unknown"
    observed_at: Optional[float] = None
    source: Optional[str] = None
    limit_requests: Optional[int] = None
    remaining_requests: Optional[int] = None
    limit_tokens: Optional[int] = None
    remaining_tokens: Optional[int] = None
    reset_at: Optional[float] = None
    retry_after_s: Optional[float] = None
    limited_until: Optional[float] = None
    last_success_at: Optional[float] = None

    def effective_state(self, now: float) -> str:
        """The state at *now* — an expired limit is over."""
        if self.state == "limited" and self.limited_until is not None \
                and now >= self.limited_until:
            return "clear"
        return self.state

    def is_limited(self, now: float) -> bool:
        return self.effective_state(now) == "limited"

    def seconds_until_reset(self, now: float) -> Optional[float]:
        """Seconds until the limit resets, or None if unknown."""
        if not self.is_limited(now):
            return 0.0
        if self.limited_until is None:
            return None
        return max(0.0, self.limited_until - now)

    def to_dict(self, now: float) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "state": self.effective_state(now),
            "observed_at": self.observed_at,
            "source": self.source,
            "limit_requests": self.limit_requests,
            "remaining_requests": self.remaining_requests,
            "limit_tokens": self.limit_tokens,
            "remaining_tokens": self.remaining_tokens,
            "reset_at": self.reset_at,
            "retry_after_s": self.retry_after_s,
            "limited_until": self.limited_until,
            "seconds_until_reset": self.seconds_until_reset(now),
            "last_success_at": self.last_success_at,
        }


class WeatherBoard:
    """Per-provider limit weather, recorded from real signals.

    Thread-safe: a whole crew records into one board. The
    injectable ``clock`` (epoch seconds) makes expiry
    deterministic in tests.
    """

    def __init__(self, *, clock=None) -> None:
        self._clock = clock or time.time
        self._lock = threading.Lock()
        self._weather: Dict[str, ProviderWeather] = {}

    # -- recording ----------------------------------------------------

    def record(self, signal: LimitSignal) -> ProviderWeather:
        """Fold one signal into the board; return the weather."""
        if not isinstance(signal.provider, str) or not signal.provider:
            raise ValueError(
                f"provider must be a non-empty string, "
                f"got {signal.provider!r}")
        if signal.kind not in ("limited", "quota", "success"):
            raise ValueError(f"unknown signal kind {signal.kind!r}")
        with self._lock:
            weather = self._weather.setdefault(
                signal.provider, ProviderWeather(signal.provider))
            weather.observed_at = signal.observed_at
            weather.source = signal.source
            for name in ("limit_requests", "remaining_requests",
                         "limit_tokens", "remaining_tokens",
                         "reset_at", "retry_after_s"):
                value = getattr(signal, name)
                if value is not None:
                    setattr(weather, name, value)
            if signal.kind == "success":
                weather.state = "clear"
                weather.limited_until = None
                weather.last_success_at = signal.observed_at
            elif signal.kind == "limited":
                weather.state = "limited"
                weather.limited_until = self._limited_until(signal)
            else:  # quota headers without a 429
                exhausted = (
                    signal.remaining_requests == 0
                    or signal.remaining_tokens == 0)
                if exhausted:
                    weather.state = "limited"
                    weather.limited_until = self._limited_until(signal)
                elif signal.remaining_requests is not None \
                        or signal.remaining_tokens is not None:
                    weather.state = "clear"
                    weather.limited_until = None
            return weather

    @staticmethod
    def _limited_until(signal: LimitSignal) -> Optional[float]:
        if signal.reset_at is not None:
            return signal.reset_at
        if signal.retry_after_s is not None:
            return signal.observed_at + signal.retry_after_s
        return None

    def record_error(self, provider: str, exc: Any, *,
                     now: Optional[float] = None) -> Optional[ProviderWeather]:
        """Record whatever limit signal *exc* carries, if any."""
        stamp = self._clock() if now is None else now
        signal = signal_from_error(exc, provider, now=stamp)
        if signal is None:
            return None
        return self.record(signal)

    def record_headers(self, provider: str, headers: Any, *,
                       now: Optional[float] = None) -> Optional[ProviderWeather]:
        """Record the limit headers a response carried, if any."""
        stamp = self._clock() if now is None else now
        signal = signal_from_headers(headers, provider, now=stamp)
        if signal is None:
            return None
        return self.record(signal)

    def record_success(self, provider: str, *,
                       now: Optional[float] = None) -> ProviderWeather:
        """Record that *provider* just answered successfully."""
        stamp = self._clock() if now is None else now
        return self.record(LimitSignal(
            provider=provider, kind="success", observed_at=stamp,
            source="success"))

    # -- reading --------------------------------------------------------

    def weather_for(self, provider: str, *,
                    now: Optional[float] = None) -> ProviderWeather:
        """The weather for *provider* — unknown if never seen."""
        stamp = self._clock() if now is None else now
        with self._lock:
            weather = self._weather.get(provider)
            if weather is None:
                return ProviderWeather(provider)
            # Return a snapshot copy so callers never observe a
            # half-folded record.
            return ProviderWeather(**{
                name: getattr(weather, name)
                for name in ProviderWeather.__dataclass_fields__})

    def snapshot(self, *, now: Optional[float] = None) -> List[ProviderWeather]:
        """Every recorded door's weather, in provider order."""
        stamp = self._clock() if now is None else now
        with self._lock:
            names = sorted(self._weather)
        return [self.weather_for(name, now=stamp) for name in names]

    def reset(self, provider: Optional[str] = None) -> None:
        """Drop one door's weather (or the whole board)."""
        with self._lock:
            if provider is None:
                self._weather.clear()
            else:
                self._weather.pop(provider, None)


# ----------------------------------------------------------------------
# The shared board — one crew, one weather
# ----------------------------------------------------------------------

_SHARED_BOARD: Optional[WeatherBoard] = None
_SHARED_LOCK = threading.Lock()


def shared_board() -> WeatherBoard:
    """The process-wide board every agent records into."""
    global _SHARED_BOARD
    with _SHARED_LOCK:
        if _SHARED_BOARD is None:
            _SHARED_BOARD = WeatherBoard()
        return _SHARED_BOARD


def weather_key_for(config: Any) -> str:
    """The board key for a session's current door.

    The provider name when the door's endpoint is one the
    M-019 registry knows (M-028's exact-endpoint inference);
    otherwise the endpoint itself — a custom door is its own
    weather key, never conflated with a named provider.
    """
    from .model_switch import infer_provider

    getter = config.get if isinstance(config, dict) else None
    base_url = getter("base_url") if getter else getattr(
        config, "base_url", None)
    provider = infer_provider(base_url)
    if provider:
        return provider
    if isinstance(base_url, str) and base_url:
        return base_url
    model = getter("model") if getter else getattr(config, "model", None)
    return str(model) if model else "default door"


# ----------------------------------------------------------------------
# Queueing — work arranged around the weather
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class QueueDecision:
    """Whether one request proceeds now or waits out a limit."""

    provider: str
    action: str  # "proceed" | "wait"
    wait_s: float
    reason: str
    state: str
    limited_until: Optional[float] = None


def queue_decision(weather: ProviderWeather, *,
                   now: float) -> QueueDecision:
    """Decide one door's work from its weather at *now*.

    * Not limited (clear or unknown) → proceed; unknown is
      stated as unknown, never dressed as clear.
    * Limited with a known reset within the queue cap →
      wait for the reset.
    * Limited with a reset beyond the cap, or with no known
      reset → proceed: the wait cannot be bounded honestly,
      the reason says so, and the weather has still been
      surfaced before the request goes.
    """
    state = weather.effective_state(now)
    if state != "limited":
        reason = (
            f"{weather.provider}: weather is {state} — no "
            f"recorded limit keeps this work waiting.")
        return QueueDecision(weather.provider, "proceed", 0.0,
                             reason, state, weather.limited_until)
    wait = weather.seconds_until_reset(now)
    if wait is None:
        return QueueDecision(
            weather.provider, "proceed", 0.0,
            f"{weather.provider}: this door is recorded "
            f"limited, but it never said when the limit "
            f"resets — the work cannot queue for an unknown "
            f"time, so it proceeds and the retry/fallback "
            f"machinery handles the outcome.", state,
            weather.limited_until)
    if wait > QUEUE_MAX_WAIT_S:
        return QueueDecision(
            weather.provider, "proceed", 0.0,
            f"{weather.provider}: this door is limited for "
            f"another {wait:.0f}s — longer than the "
            f"{int(QUEUE_MAX_WAIT_S)}s queueing bound — so "
            f"the work proceeds and the retry/fallback "
            f"machinery handles the outcome.", state,
            weather.limited_until)
    return QueueDecision(
        weather.provider, "wait", wait,
        f"{weather.provider}: this door is limited until "
        f"its reset in {wait:.0f}s — the work queues around "
        f"the limit and goes when the reset passes.", state,
        weather.limited_until)


def plan_crew_work(items: Any, board: WeatherBoard, *,
                   now: Optional[float] = None) -> Dict[str, Any]:
    """Partition crew work around the board's weather.

    *items* is an iterable of mappings each carrying a
    ``"provider"`` key (the door the work needs). Returns
    ``{"ready": [...], "deferred": [...]}``: ready items in
    their original order, and deferred entries naming the
    item, its door, when it may go (``resume_at`` — None
    when the door never said, which means held until the
    weather changes), and the plain reason. Nothing is
    dropped and no order is changed within either list.
    """
    stamp = board._clock() if now is None else now
    ready: List[Any] = []
    deferred: List[Dict[str, Any]] = []
    for item in items:
        provider = item.get("provider") if isinstance(item, dict) else None
        if not isinstance(provider, str) or not provider:
            raise ValueError(
                f"crew work items must name their provider door, "
                f"got {item!r}")
        weather = board.weather_for(provider, now=stamp)
        if weather.is_limited(stamp):
            deferred.append({
                "item": item,
                "provider": provider,
                "resume_at": weather.limited_until,
                "reason": (
                    f"{provider} is recorded limited"
                    + (f" until its reset in "
                       f"{weather.seconds_until_reset(stamp):.0f}s"
                       if weather.limited_until is not None
                       else " with no known reset time")
                    + " — this work is held, not dropped."),
            })
        else:
            ready.append(item)
    return {"ready": ready, "deferred": deferred}


# ----------------------------------------------------------------------
# Surfaces — the plain-words weather report
# ----------------------------------------------------------------------


def _quota_text(weather: ProviderWeather) -> str:
    parts = []
    for label, remaining, limit in (
            ("requests", weather.remaining_requests,
             weather.limit_requests),
            ("tokens", weather.remaining_tokens,
             weather.limit_tokens)):
        if remaining is not None or limit is not None:
            parts.append(
                f"{label} {remaining if remaining is not None else 'unknown'}"
                f" of {limit if limit is not None else 'unknown'} left")
    return "; ".join(parts) if parts else "quota unknown"


def format_weather(weather: ProviderWeather, *, now: float) -> str:
    """One door's weather as one plain sentence."""
    state = weather.effective_state(now)
    if state == "unknown":
        return (f"{weather.provider}: weather unknown — no "
                f"limit signal has ever been recorded for this "
                f"door, so nothing about its limits is claimed.")
    if state == "clear":
        extra = _quota_text(weather)
        return (f"{weather.provider}: clear — the door is not "
                f"limiting us on the last signal "
                f"({weather.source or 'unknown source'}); {extra}.")
    wait = weather.seconds_until_reset(now)
    until = (f"for another {wait:.0f}s (reset at "
             f"{time.strftime('%H:%M:%S', time.localtime(weather.limited_until))})"
             if wait is not None else "with no known reset time")
    return (f"{weather.provider}: LIMITED {until}; "
            f"{_quota_text(weather)}.")


def format_weather_status(board: WeatherBoard, *,
                          now: Optional[float] = None,
                          extra_providers: Any = ()) -> str:
    """The ``/weather`` report: explanation + every door."""
    stamp = board._clock() if now is None else now
    lines = [PLAIN_EXPLANATION, ""]
    weathers = board.snapshot(now=stamp)
    seen = {w.provider for w in weathers}
    for name in extra_providers or ():
        if name not in seen:
            weathers.append(board.weather_for(name, now=stamp))
            seen.add(name)
    if not weathers:
        lines.append(
            "No door has reported any limit weather yet — "
            "every door's weather is unknown.")
    for weather in weathers:
        lines.append(format_weather(weather, now=stamp))
    return "\n".join(lines)


def format_queue_plan(plan: Dict[str, Any]) -> str:
    """A crew-work plan (from :func:`plan_crew_work`), plainly."""
    lines = [f"Ready now: {len(plan['ready'])}; "
             f"held for a limited door: {len(plan['deferred'])}."]
    for entry in plan["deferred"]:
        lines.append(f"Held: {entry['reason']}")
    return "\n".join(lines)


def parse_weather_args(args: Any) -> Dict[str, Any]:
    """The one ``/weather`` grammar both surfaces share.

    ``/weather`` and ``/weather show`` show the board; any
    other words are a usage error, never guessed at.
    """
    if args is not None and not isinstance(args, str):
        raise ValueError(
            "Usage: /weather — show the rate-limit weather for "
            "every provider door (per-door limit state, the quota "
            "the door itself reported, and what is unknown).")
    text = args if isinstance(args, str) else ""
    words = text.lower().split()
    if not words or words == ["show"]:
        return {"action": "show"}
    raise ValueError(
        "Usage: /weather — show the rate-limit weather for "
        "every provider door (per-door limit state, the quota "
        "the door itself reported, and what is unknown).")
