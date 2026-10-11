"""Provider conformance suite (Slice 049).

A contract harness that runs every registered (or supplied) adapter
against the Slice 041–048 negotiation/normalization contracts using
fake fixtures only — no live provider calls, no network.

Checks performed per provider (each recorded as a :class:`CheckResult`
with ``passed`` / ``skipped`` / ``failed`` status):

1. ``capability-flags`` — ``capabilities()`` returns exactly the
   ``CAPABILITY_FLAGS`` keys with boolean values.
2. ``validate-messages-accept`` — a valid OpenAI-style message list
   passes through unchanged.
3. ``validate-messages-reject`` — bad role / empty list raise
   :class:`ProviderError`.
4. ``chat-fake-transport`` — providers constructed with an injected
   fake ``transport=`` seam answer ``chat()`` through it; providers
   without the seam, or still wired to their live ``_real_post``,
   are *skipped* (live calls are never made here).
5. ``iter-chunks-contract`` — providers without the ``streaming``
   flag must raise :class:`ProviderError` from ``iter_chunks``;
   streaming-capable adapters are *skipped* (live streaming is not
   exercised by this harness).
6. ``structured-output`` — ``json_mode`` providers: ``negotiate``
   yields a native fragment and ``parse_json`` round-trips; others:
   ``prepare`` falls back to a system instruction and the fence
   fallback parses.
7. ``vision`` — vision providers normalize a data-URL image part;
   non-vision providers honor the strip/raise downgrade policy.
8. ``reasoning`` — ``ReasoningConfig(mode="off")`` negotiates to
   ``{}`` on every provider.
9. ``usage`` — synthetic raw usage normalizes to :class:`ChatUsage`
   with non-negative counts.
10. ``cost`` — :class:`CostLedger` prices a synthetic call without
    error (temporary workspace; never the caller's ledger).
11. ``health`` — :class:`ProviderHealth` scores synthetic
    success/failure histories inside [0, 1].

:func:`run_conformance` returns a :class:`ConformanceReport`;
:func:`render` prints it as text and :meth:`ConformanceReport.to_json`
serializes the machine-readable form. :func:`run_pantheon` runs the
harness over a list of providers and returns all reports.
"""


from __future__ import annotations

__all__ = [
    "CheckResult",
    "ConformanceReport",
    "Provider",
    "ProviderError",
    "render",
    "run_conformance",
    "run_pantheon",
    "write_report",
]

import base64
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

from . import reasoning as reasoning_module
from . import streaming as streaming_module
from . import structured_output as structured_module
from . import usage as usage_module
from . import vision as vision_module
from .base import ChatUsage, Provider, ProviderError
from .cost_ledger import CostLedger
from .health import ProviderHealth
from .reasoning import ReasoningConfig


@dataclass
class CheckResult:
    """One conformance check outcome."""

    name: str
    status: str  # "passed" | "failed" | "skipped"
    detail: str = ""

    def __post_init__(self) -> None:
        if self.status not in ("passed", "failed", "skipped"):
            raise ValueError(f"Bad check status {self.status!r}")

    @property
    def passed(self) -> bool:
        return self.status == "passed"


@dataclass
class ConformanceReport:
    """Machine-readable conformance result for one provider."""

    provider: str
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(check.status != "failed" for check in self.checks)

    @property
    def summary(self) -> dict[str, int]:
        counts = {"passed": 0, "failed": 0, "skipped": 0}
        for check in self.checks:
            counts[check.status] += 1
        return counts

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "passed": self.passed,
            "summary": self.summary,
            "checks": [
                {"name": c.name, "status": c.status, "detail": c.detail}
                for c in self.checks
            ],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


def _check(name: str, func: Callable[[], str]) -> CheckResult:
    """Run one check; ProviderError/AssertionError -> failed, SkipCheck -> skipped."""
    try:
        detail = func()
    except _SkipCheck as exc:
        return CheckResult(name=name, status="skipped", detail=str(exc))
    except (ProviderError, AssertionError, ValueError, TypeError) as exc:
        return CheckResult(name=name, status="failed",
                           detail=f"{type(exc).__name__}: {exc}")
    return CheckResult(name=name, status="passed", detail=detail or "")


class _SkipCheck(Exception):
    """Raised inside a check to mark it skipped (documented reason)."""


_SAMPLE_MESSAGES = [
    {"role": "system", "content": "You are helpful."},
    {"role": "user", "content": "Say ok."},
]

_SAMPLE_SCHEMA = {
    "type": "object",
    "properties": {"answer": {"type": "string"}},
    "required": ["answer"],
}

_TINY_PNG_B64 = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64).decode()


def _sample_image_part() -> dict[str, Any]:
    return {"type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{_TINY_PNG_B64}"}}


def _sample_raw_usage(provider: Provider) -> Any:
    name = (getattr(provider, "name", "") or "").lower()
    if name in ("anthropic", "claude"):
        return {"input_tokens": 12, "output_tokens": 5,
                "cache_creation_input_tokens": 3,
                "cache_read_input_tokens": 4}
    if name in ("google", "gemini"):
        return {"usageMetadata": {"promptTokenCount": 12,
                                  "candidatesTokenCount": 5,
                                  "totalTokenCount": 17,
                                  "cachedContentTokenCount": 3}}
    if name == "ollama":
        return {"prompt_eval_count": 12, "eval_count": 5}
    return {"usage": {"prompt_tokens": 12, "completion_tokens": 5,
                      "total_tokens": 17}}


def run_conformance(provider: Provider) -> ConformanceReport:
    """Run the contract harness against ``provider`` (fake fixtures only)."""
    report = ConformanceReport(provider=provider.name)
    caps = provider.capabilities()

    def capability_flags() -> str:
        expected = set(Provider.CAPABILITY_FLAGS)
        assert isinstance(caps, dict), "capabilities() must return a dict"
        assert set(caps.keys()) == expected, (
            f"flag keys {sorted(caps.keys())} != {sorted(expected)}")
        assert all(isinstance(v, bool) for v in caps.values()), (
            "every capability flag must be a bool")
        return f"flags={sorted(caps.keys())}"
    report.checks.append(_check("capability-flags", capability_flags))

    def validate_accept() -> str:
        out = Provider.validate_messages(_SAMPLE_MESSAGES)
        assert out == _SAMPLE_MESSAGES, "valid messages must pass through"
        return "2 messages accepted"
    report.checks.append(_check("validate-messages-accept", validate_accept))

    def validate_reject() -> str:
        for bad in ([], [{"role": "bogus", "content": "x"}],
                    [{"role": "user", "content": 42}]):
            try:
                Provider.validate_messages(bad)  # type: ignore[arg-type]
            except ProviderError:
                continue
            raise AssertionError(f"malformed input accepted: {bad!r}")
        return "empty/bad-role/bad-content rejected"
    report.checks.append(_check("validate-messages-reject", validate_reject))

    def chat_fake_transport() -> str:
        seam = getattr(provider, "_transport", None)
        if not callable(seam):
            raise _SkipCheck(
                "no _transport fake seam; live calls never made here")
        live = getattr(provider, "_real_post", None)
        if live is not None and seam == live:
            # Bound-method equality: the provider is wired to its real
            # HTTP transport. Never fire it from the harness.
            raise _SkipCheck(
                "live _transport; pass a provider built with a fake "
                "transport= seam to exercise chat()")
        text = provider.chat(_SAMPLE_MESSAGES)
        if not isinstance(text, str) or not text.strip():
            raise AssertionError(
                f"chat() returned empty/non-text: {text!r}")
        return f"chat() answered through the injected seam: {text[:40]!r}"
    report.checks.append(_check("chat-fake-transport", chat_fake_transport))

    def iter_chunks_contract() -> str:
        if caps.get("streaming"):
            raise _SkipCheck(
                "streaming advertised; live streaming not exercised here")
        try:
            gen = provider.iter_chunks(_SAMPLE_MESSAGES)
            # If it returned a generator, draining must raise.
            for _ in gen:
                pass
        except ProviderError:
            return "iter_chunks raises ProviderError (no streaming)"
        raise AssertionError(
            "non-streaming provider yielded chunks without error")
    report.checks.append(_check("iter-chunks-contract", iter_chunks_contract))

    def structured_output() -> str:
        if caps.get("json_mode"):
            fragment = structured_module.negotiate(
                provider, _SAMPLE_SCHEMA, name="answer")
            assert fragment, "negotiate() returned an empty fragment"
            decoded = structured_module.parse_json(
                provider, '{"answer": "yes"}')
            assert decoded == {"answer": "yes"}, decoded
            return f"native fragment keys={sorted(fragment.keys())}"
        messages, fragment = structured_module.prepare(
            provider, _SAMPLE_MESSAGES, _SAMPLE_SCHEMA)
        assert fragment == {}, "non-native prepare must return no fragment"
        assert len(messages) == len(_SAMPLE_MESSAGES) + 1, (
            "fallback must append exactly one system message")
        decoded = structured_module.parse_json(
            provider, '```json\n{"answer": "yes"}\n```')
        assert decoded == {"answer": "yes"}, decoded
        return "fallback: system instruction + fence parse"
    report.checks.append(_check("structured-output", structured_output))

    def vision() -> str:
        parts = [{"type": "text", "text": "Describe this."},
                 _sample_image_part()]
        if caps.get("vision"):
            payload = vision_module.normalize(provider, parts)
            assert payload.dropped == 0, "nothing should be dropped"
            assert payload.content, "normalized content must not be empty"
            return (f"wire parts={len(payload.content)} "
                    f"images={len(payload.images)}")
        payload = vision_module.normalize(
            provider, parts, on_unsupported="strip")
        assert payload.dropped == 1, "exactly one image part must drop"
        assert all(p.get("type") == "text" for p in payload.content), (
            "only text may survive the strip policy")
        try:
            vision_module.normalize(provider, parts, on_unsupported="raise")
        except ProviderError:
            return "strip drops 1 image; raise policy raises"
        raise AssertionError("raise policy did not raise")
    report.checks.append(_check("vision", vision))

    def reasoning() -> str:
        fragment = reasoning_module.negotiate(
            provider, ReasoningConfig(mode="off"))
        assert fragment == {}, f"mode='off' must give {{}}, got {fragment}"
        return "mode='off' -> {}"
    report.checks.append(_check("reasoning", reasoning))

    def usage() -> str:
        record = usage_module.normalize(
            provider, _sample_raw_usage(provider))
        assert isinstance(record, ChatUsage), type(record).__name__
        assert record.prompt_tokens >= 0 and record.completion_tokens >= 0
        assert record.total_tokens >= 0
        estimated = usage_module.normalize(provider, None,
                                           fallback_text="hello world")
        assert estimated.estimated is True, "fallback must flag estimated"
        return (f"prompt={record.prompt_tokens} "
                f"completion={record.completion_tokens} "
                f"cached={record.cached_tokens}")
    report.checks.append(_check("usage", usage))

    def cost() -> str:
        import tempfile
        with tempfile.TemporaryDirectory(
                prefix="mythic-conformance-") as tmpdir:
            ledger = CostLedger(workspace_root=tmpdir)
            record = usage_module.normalize(
                provider, _sample_raw_usage(provider))
            call = ledger.record(provider.name, provider.model or "m",
                                 record)
        assert call.provider == provider.name
        assert call.cost_usd >= 0.0
        return (f"cost_usd={call.cost_usd} priced={call.priced}")
    report.checks.append(_check("cost", cost))

    def health() -> str:
        tracker = ProviderHealth()
        for _ in range(5):
            tracker.record(provider.name, ok=True, latency_s=0.1)
        tracker.record(provider.name, ok=False, latency_s=0.2)
        score = tracker.score(provider.name)
        assert 0.0 <= score <= 1.0, f"score out of range: {score}"
        assert score > 0.5, f"mostly-healthy provider scored {score}"
        return f"score={score}"
    report.checks.append(_check("health", health))

    # Streaming parser sanity (provider-independent wire shapes).
    def streaming_parsers() -> str:
        sse_lines = [
            'data: {"choices": [{"delta": {"content": "hi"}}]}',
            'data: {"choices": [{"delta": {}, "finish_reason": "stop"}]}',
        ]
        events = list(streaming_module.parse_openai_sse(sse_lines))
        kinds = [event.kind for event in events]
        assert kinds == ["text", "done"], kinds
        text = streaming_module.collect(iter(events))
        assert text == "hi", text
        return "SSE text+done parsed and collected"
    report.checks.append(_check("streaming-parsers", streaming_parsers))

    return report


def run_pantheon(providers: list[Provider]) -> list[ConformanceReport]:
    """Run :func:`run_conformance` over every provider in ``providers``."""
    return [run_conformance(provider) for provider in providers]


def render(report: ConformanceReport) -> str:
    """Render a report as human-readable text."""
    lines = [f"Conformance: {report.provider} "
             f"({'PASS' if report.passed else 'FAIL'})"]
    for check in report.checks:
        mark = {"passed": "ok", "failed": "FAIL",
                "skipped": "skip"}[check.status]
        line = f"  [{mark:>4}] {check.name}"
        if check.detail:
            line += f" — {check.detail}"
        lines.append(line)
    summary = report.summary
    lines.append(
        f"  {summary['passed']} passed, {summary['failed']} failed, "
        f"{summary['skipped']} skipped")
    return "\n".join(lines)


def write_report(report: ConformanceReport, path: str | Path) -> Path:
    """Write the machine-readable JSON report to ``path``."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(report.to_json(), encoding="utf-8")
    return target
