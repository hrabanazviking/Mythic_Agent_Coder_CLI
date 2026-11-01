"""New-provider test kit (All-Features roadmap slice M-041).

Part II — The Provider Ocean — closes its building road here.
A new registry entry used to ship on the M-019 data tests
alone: those pins check the entry's declared shape against
the live adapter classes, never its behaviour. This slice is
the conformance kit a new entry must pass before it ships —
five checks, in the roadmap's order, proven against a door:

* ``registry`` — the entry resolves (aliases included), its
  default model is in its own model list, and — for an
  OpenAI-compatible entry — the M-020 universal adapter built
  purely from the entry reports exactly the entry's recorded
  capabilities at exactly the entry's endpoint.
* ``chat`` — a real chat through the universal adapter
  returns non-empty assistant text from the door.
* ``tools`` — the door is sent the kit's own tool with the
  choice forced to that tool, and its reply, parsed by the
  shipped tool-negotiation parser, carries that call.
* ``streaming`` — the door's streamed reply, read through
  the shipped streaming parser, yields text and ends.
* ``errors`` — a malformed request (an empty message list)
  is answered with an HTTP error, never a success, and the
  adapter raises :class:`ProviderError` on invalid input
  before any transport happens.

The live road is the universal adapter, because that is the
road a new entry joins: M-019's extension rule says a new
OpenAI-compatible door is a registry entry, and a wholly new
dialect is a new adapter, never a registry edit alone.

Honesty rules, enforced here and pinned by the slice's tests:

* **A check a door does not claim is skipped, never passed.**
  When the entry's recorded capabilities say ``tool_calling``
  or ``streaming`` is false, that check is ``skipped`` with
  the reason — the kit proves what a door claims, and says
  plainly what it did not prove.
* **A non-compatible dialect is NOT PROVEN, never passed.**
  Its live checks are skipped with the reason (its own
  adapter's suite is its proof), the ``registry`` check still
  runs, and the verdict is ``not-proven``.
* **The verdict is earned.** ``passed`` requires no failed
  check AND a chat check that actually ran and passed;
  any failure is ``failed``; anything else is
  ``not-proven``. The script and the CLI exit 0 only on
  ``passed`` — a new entry must pass, not merely not fail.
* **No key value ever rides the kit.** The key is used only
  in the Authorization header (and the quirk headers the
  entry declares); every check detail is redacted and
  bounded before it is recorded, and the slice's tests pin a
  door that echoes its key in an error body.
"""

from __future__ import annotations

__all__ = [
    "CHECKS",
    "KIT_SLICE",
    "KIT_TOOL",
    "PLAIN_EXPLANATION",
    "STATUSES",
    "VERDICTS",
    "Any",
    "Callable",
    "Dict",
    "KitCheck",
    "KitReport",
    "List",
    "Optional",
    "Tuple",
    "default_post_json",
    "default_post_lines",
    "format_kit_status",
    "parse_kit_args",
    "run_kit",
]

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

from .provider_registry import ProviderDef, ProviderRegistry, load_registry

#: The slice that owns this kit.
KIT_SLICE = "M-041"

#: The kit's checks, in the roadmap's order (registry first:
#: an entry that cannot resolve has no behaviour to prove).
CHECKS: Tuple[str, ...] = ("registry", "chat", "tools", "streaming", "errors")

#: One check's possible outcomes.
STATUSES: Tuple[str, ...] = ("passed", "failed", "skipped")

#: The kit's verdicts, in honesty order.
VERDICTS: Tuple[str, ...] = ("passed", "failed", "not-proven")

#: The tool the kit asks a door to call. It exists only for
#: the kit; no surface executes it.
KIT_TOOL = "kit_echo"

#: The prompt every kit chat sends.
_KIT_PROMPT = "Reply with the word ok."

#: The default per-request budget for a kit run, in seconds.
DEFAULT_TIMEOUT = 15.0

#: Provider test kit explained in plain words — the sentence
#: every surface shows.
PLAIN_EXPLANATION = (
    "New-provider test kit: before a new registry entry "
    "ships, it must pass five checks proven against its door "
    "— the entry resolves and the universal adapter built "
    "from it matches it, a real chat answers, a forced tool "
    "call comes back when the door claims tool calling, a "
    "streamed reply yields text and ends when the door "
    "claims streaming, and a malformed request is answered "
    "with an error, never a success. A check the door does "
    "not claim is skipped with the reason, never passed "
    "silently; a door whose dialect the universal adapter "
    "cannot serve is NOT PROVEN, never passed. The verdict "
    "is passed only when nothing failed and chat was "
    "actually proven."
)


@dataclass(frozen=True)
class KitCheck:
    """One kit check's outcome: status plus plain evidence.

    ``detail`` is the evidence in the check's own words —
    redacted (no key value) and bounded before it is stored.
    """

    name: str
    status: str
    detail: str

    def record(self) -> Dict[str, Any]:
        """This check as a plain mapping."""
        return {"name": self.name, "status": self.status,
                "detail": self.detail}


@dataclass(frozen=True)
class KitReport:
    """The kit's whole report for one registry entry."""

    provider: str
    title: str
    dialect: str
    endpoint: Optional[str]
    model: str
    checks: Tuple[KitCheck, ...]

    @property
    def verdict(self) -> str:
        """passed / failed / not-proven — the honesty rules above."""
        if any(check.status == "failed" for check in self.checks):
            return "failed"
        chat = next((c for c in self.checks if c.name == "chat"), None)
        if chat is not None and chat.status == "passed":
            return "passed"
        return "not-proven"

    def summary(self) -> Dict[str, int]:
        """How many checks stand in each status, in kit order."""
        counts = {status: 0 for status in STATUSES}
        for check in self.checks:
            counts[check.status] += 1
        return counts

    def record(self) -> Dict[str, Any]:
        """This report as a plain mapping."""
        return {
            "slice": KIT_SLICE,
            "provider": self.provider,
            "title": self.title,
            "dialect": self.dialect,
            "endpoint": self.endpoint,
            "model": self.model,
            "verdict": self.verdict,
            "summary": self.summary(),
            "checks": [check.record() for check in self.checks],
        }


# ----------------------------------------------------------------------
# The wire — one honest POST seam, in two shapes (JSON and lines)
# ----------------------------------------------------------------------


def default_post_json(url: str, headers: Dict[str, str],
                      payload: Dict[str, Any],
                      timeout: float) -> Tuple[int, str]:
    """POST *payload* as JSON to *url*; return (status, body text).

    A non-2xx HTTP answer is the server's own answer and is
    returned, not raised. A transport failure raises, and the
    kit records the failure's own words as the check detail.
    """
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as reply:
            return reply.status, reply.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read().decode("utf-8", "replace")
        except Exception:
            body = ""
        return exc.code, body


def default_post_lines(url: str, headers: Dict[str, str],
                       payload: Dict[str, Any],
                       timeout: float) -> Tuple[int, List[str]]:
    """POST *payload* as JSON; return (status, response lines).

    The streaming shape of :func:`default_post_json`: the
    door's streamed reply read line by line (bounded at
    10,000 lines — a stream that never ends is not a pass).
    """
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as reply:
            lines = []
            for raw in reply:
                lines.append(raw.decode("utf-8", "replace"))
                if len(lines) >= 10000:
                    break
            return reply.status, lines
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read().decode("utf-8", "replace")
        except Exception:
            body = ""
        return exc.code, [body]


def _clean(text: Any, key: Optional[str]) -> str:
    """A check detail: the evidence's own words, redacted + bounded."""
    out = str(text)
    if key:
        out = out.replace(key, "***REDACTED***")
    try:
        from .redaction import redact_text
        out = redact_text(out)
    except Exception:
        pass
    return out[:200]


def _headers_for(entry: ProviderDef, key: Optional[str]) -> Dict[str, str]:
    """The headers a kit request sends, quirks included (M-020)."""
    from ..providers.openai_compat import (
        DEFAULT_HTTP_REFERER,
        DEFAULT_X_TITLE,
        PLACEHOLDER_API_KEY,
    )

    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    elif entry.has_quirk("placeholder-bearer-auth"):
        headers["Authorization"] = f"Bearer {PLACEHOLDER_API_KEY}"
    if entry.has_quirk("app-identification-headers"):
        headers["HTTP-Referer"] = DEFAULT_HTTP_REFERER
        headers["X-Title"] = DEFAULT_X_TITLE
    return headers


# ----------------------------------------------------------------------
# The kit
# ----------------------------------------------------------------------


def run_kit(name: str, *,
            registry: Optional[ProviderRegistry] = None,
            base_url: Optional[str] = None,
            api_key: Optional[str] = None,
            model: Optional[str] = None,
            environ: Any = None,
            timeout: float = DEFAULT_TIMEOUT,
            post_json: Optional[Callable] = None,
            post_lines: Optional[Callable] = None) -> KitReport:
    """Run the five kit checks for the registry entry *name*.

    Aliases resolve through the registry; an unknown name
    raises KeyError — an unknown door is unknown, never
    guessed. ``base_url`` aims the kit at another door for
    the same entry (a local test door, a staging door); the
    key is *api_key* when given, else the entry's own key
    environment variable read from *environ*. ``post_json``
    and ``post_lines`` are the injectable wire seams.
    """
    import os

    reg = registry if registry is not None else load_registry()
    entry = reg.provider(name)
    env = os.environ if environ is None else environ
    key = api_key
    if key is None and entry.api_key_env:
        candidate = env.get(entry.api_key_env) if env is not None else None
        key = candidate if candidate else None
    endpoint = (base_url or entry.endpoint or "").rstrip("/") or None
    chosen_model = model or entry.default_model
    wire_json = post_json if post_json is not None else default_post_json
    wire_lines = post_lines if post_lines is not None else default_post_lines
    compatible = entry.dialect == "openai_compatible"
    checks: List[KitCheck] = []

    def record(check_name: str, status: str, detail: Any) -> None:
        checks.append(KitCheck(name=check_name, status=status,
                               detail=_clean(detail, key)))

    # -- registry ------------------------------------------------------
    if not compatible:
        record("registry", "passed",
               f"entry {entry.name!r} resolves ({entry.title}); "
               f"dialect {entry.dialect!r} is served by its own "
               "adapter, so the adapter-match half of this check "
               "does not apply.")
    else:
        try:
            from ..providers.openai_compat import (
                UniversalOpenAICompatProvider,
            )

            probe_adapter = UniversalOpenAICompatProvider(
                entry, api_key=key, base_url=endpoint,
                transport=lambda path, payload, headers: (200, {}))
            problems = []
            if probe_adapter.capabilities() != dict(entry.capabilities):
                problems.append("adapter capabilities differ from the entry")
            if endpoint is not None and probe_adapter.base_url != endpoint:
                problems.append("adapter endpoint differs from the entry")
            if entry.default_model not in entry.models:
                problems.append("default model is not in the entry's models")
            if problems:
                record("registry", "failed", "; ".join(problems))
            else:
                record("registry", "passed",
                       f"entry {entry.name!r} resolves and the universal "
                       f"adapter built from it matches it: endpoint "
                       f"{endpoint}, default model {entry.default_model!r}, "
                       "capabilities exactly as recorded.")
        except Exception as exc:  # an entry its adapter refuses is a fail
            record("registry", "failed",
                   f"{type(exc).__name__}: {exc}")

    if not compatible:
        reason = (
            f"dialect {entry.dialect!r} is not served by the universal "
            "adapter, so the kit's live road cannot prove this door; "
            "its own adapter's suite is its proof. NOT PROVEN here.")
        for check_name in ("chat", "tools", "streaming", "errors"):
            record(check_name, "skipped", reason)
        return KitReport(provider=entry.name, title=entry.title,
                         dialect=entry.dialect, endpoint=endpoint,
                         model=chosen_model, checks=tuple(checks))
    if endpoint is None:
        for check_name in ("chat", "tools", "streaming", "errors"):
            record(check_name, "skipped",
                   "the entry records no endpoint, so no door can "
                   "be aimed at; NOT PROVEN here.")
        return KitReport(provider=entry.name, title=entry.title,
                         dialect=entry.dialect, endpoint=endpoint,
                         model=chosen_model, checks=tuple(checks))

    from ..providers.base import ProviderError
    from ..providers.openai_compat import UniversalOpenAICompatProvider

    def transport(path: str, payload: Dict[str, Any],
                  headers: Dict[str, str]) -> Tuple[int, Any]:
        status, raw = wire_json(endpoint + path, headers, payload, timeout)
        try:
            return status, json.loads(raw) if raw else None
        except ValueError:
            return status, None

    adapter = UniversalOpenAICompatProvider(
        entry, api_key=key, model=chosen_model, base_url=endpoint,
        max_retries=0, transport=transport)
    headers = _headers_for(entry, key)
    chat_url = endpoint + "/chat/completions"

    # -- chat ------------------------------------------------------------
    try:
        reply = adapter.chat([{"role": "user", "content": _KIT_PROMPT}])
        record("chat", "passed",
               f"the door answered a real chat through the universal "
               f"adapter: {reply.strip()[:80]!r}")
    except Exception as exc:
        record("chat", "failed", f"{type(exc).__name__}: {exc}")

    # -- tools -----------------------------------------------------------
    if not entry.capability("tool_calling"):
        record("tools", "skipped",
               "the entry declares tool_calling: no, so the kit "
               "claims nothing about tools for this door.")
    else:
        try:
            from ..providers.tool_negotiation import negotiate, parse_tool_calls

            spec = {"name": KIT_TOOL,
                    "description": "The test kit's own tool: call it "
                                   "with the word ok.",
                    "parameters": {"type": "object",
                                   "properties": {
                                       "word": {"type": "string"}},
                                   "required": ["word"]}}
            payload = {"model": chosen_model,
                       "messages": [{"role": "user",
                                     "content": "Call the kit_echo "
                                                "tool with the word ok."}],
                       **negotiate(adapter, [spec]),
                       "tool_choice": {"type": "function",
                                       "function": {"name": KIT_TOOL}}}
            status, raw = wire_json(chat_url, headers, payload, timeout)
            if status != 200:
                record("tools", "failed",
                       f"the door answered the forced tool call with "
                       f"HTTP {status}, not a tool call.")
            else:
                body = json.loads(raw) if raw else None
                calls = parse_tool_calls(adapter, body)
                named = [c for c in calls if c.name == KIT_TOOL]
                if named:
                    record("tools", "passed",
                           f"the door called {KIT_TOOL} as forced, "
                           f"with arguments {named[0].arguments!r}.")
                else:
                    record("tools", "failed",
                           "the door answered HTTP 200 but no "
                           f"{KIT_TOOL} call came back (calls seen: "
                           f"{[c.name for c in calls]!r}).")
        except Exception as exc:
            record("tools", "failed", f"{type(exc).__name__}: {exc}")

    # -- streaming ---------------------------------------------------------
    if not entry.capability("streaming"):
        record("streaming", "skipped",
               "the entry declares streaming: no, so the kit "
               "claims nothing about streaming for this door.")
    else:
        try:
            from ..providers.streaming import parse_openai_sse

            payload = {"model": chosen_model,
                       "messages": [{"role": "user",
                                     "content": _KIT_PROMPT}],
                       "stream": True}
            status, lines = wire_lines(chat_url, headers, payload, timeout)
            if status != 200:
                record("streaming", "failed",
                       f"the door answered the streaming request with "
                       f"HTTP {status}, not a stream.")
            else:
                events = list(parse_openai_sse(lines))
                text = "".join(e.text for e in events if e.kind == "text")
                errors = [e for e in events if e.kind == "error"]
                done = any(e.kind == "done" for e in events)
                if errors:
                    record("streaming", "failed",
                           f"the stream carried an error event: "
                           f"{errors[0].error}")
                elif text and done:
                    record("streaming", "passed",
                           f"the streamed reply yielded text and ended: "
                           f"{text.strip()[:80]!r}")
                elif not text:
                    record("streaming", "failed",
                           "the stream yielded no text at all.")
                else:
                    record("streaming", "failed",
                           "the stream yielded text but never ended "
                           "(no done event).")
        except Exception as exc:
            record("streaming", "failed", f"{type(exc).__name__}: {exc}")

    # -- errors ------------------------------------------------------------
    try:
        status, _raw = wire_json(
            chat_url, headers,
            {"model": chosen_model, "messages": []}, timeout)
        wire_ok = status >= 400
        local_ok = False
        local_detail = ""
        try:
            adapter.chat([])
        except ProviderError as exc:
            local_ok = True
            local_detail = str(exc)
        except Exception as exc:  # wrong error type is not the contract
            local_detail = f"raised {type(exc).__name__}, not ProviderError"
        if wire_ok and local_ok:
            record("errors", "passed",
                   f"a malformed request (empty message list) was "
                   f"answered with HTTP {status}, never a success, "
                   f"and the adapter raises ProviderError on invalid "
                   f"input before transport: {local_detail}")
        elif not wire_ok:
            record("errors", "failed",
                   f"a malformed request (empty message list) was "
                   f"answered with HTTP {status} — a conforming door "
                   "answers it with an error, never a success.")
        else:
            record("errors", "failed",
                   f"the adapter did not raise ProviderError on "
                   f"invalid input: {local_detail or 'chat([]) returned'}")
    except Exception as exc:
        record("errors", "failed", f"{type(exc).__name__}: {exc}")

    return KitReport(provider=entry.name, title=entry.title,
                     dialect=entry.dialect, endpoint=endpoint,
                     model=chosen_model, checks=tuple(checks))


# ----------------------------------------------------------------------
# Surface text — one parser + one formatter for every surface
# ----------------------------------------------------------------------


def parse_kit_args(text: Any) -> Dict[str, Any]:
    """Parse the ``/testkit`` slash-command argument string.

    ``/testkit <provider> [base-url]`` names the door to
    prove; anything else is a usage error, never a guess.
    """
    words = str(text or "").strip().split()
    if len(words) == 1:
        return {"action": "run", "provider": words[0], "base_url": None}
    if len(words) == 2:
        return {"action": "run", "provider": words[0],
                "base_url": words[1]}
    raise ValueError(
        "Usage: /testkit <provider> [base-url] — run the "
        "new-provider test kit (M-041) against a registry "
        "entry's door: registry, chat, tools, streaming, and "
        "errors, each proven or honestly skipped.")


def format_kit_status(status: Dict[str, Any]) -> str:
    """The ``/testkit`` report from an Agent status mapping."""
    report = status["report"]
    lines = [f"New-provider test kit ({KIT_SLICE}): "
             f"{report['provider']} ({report['title']}) — "
             f"verdict: {report['verdict']}."]
    lines.append(f"  door: {report['endpoint']} · "
                 f"model: {report['model']} · "
                 f"dialect: {report['dialect']}")
    for check in report["checks"]:
        lines.append(f"  {check['name']}: {check['status']} — "
                     f"{check['detail']}")
    lines.append(PLAIN_EXPLANATION)
    return "\n".join(lines)
