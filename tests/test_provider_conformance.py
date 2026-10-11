"""TIER: unit

Unit tests for slice 049 (provider conformance suite).

Fake fixtures only: the harness runs against fake providers and
providers constructed with fake transports. No live calls, no
network, no real keys.
"""

import json

import pytest

from mythic_agent.providers import conformance
from mythic_agent.providers.base import Provider, ProviderError
from mythic_agent.providers.conformance import (
    CheckResult,
    ConformanceReport,
    render,
    run_conformance,
    run_pantheon,
    write_report,
)
from mythic_agent.providers.openai_compat import OpenAICompatProvider


# ----------------------------------------------------------------------
# Fakes
# ----------------------------------------------------------------------

def _make_provider(name, flags):
    def capabilities(self):
        return dict(flags)

    def chat(self, messages, **kwargs):
        raise ProviderError("fake: chat not implemented")

    return type(f"_Provider_{name}", (Provider,), {
        "name": name,
        "capabilities": capabilities,
        "chat": chat,
    })()


def _boom_transport(path, payload, headers):
    raise AssertionError("conformance must never touch the network")


def _ok_transport(path, payload, headers):
    return (200, {"choices": [{"message": {"content": "ok",
                                           "role": "assistant"}}]})


# ----------------------------------------------------------------------
# CheckResult / ConformanceReport
# ----------------------------------------------------------------------

def test_check_result_status_validation():
    with pytest.raises(ValueError):
        CheckResult(name="x", status="maybe")
    assert CheckResult(name="x", status="passed").passed is True
    assert CheckResult(name="x", status="skipped").passed is False


def test_report_passed_property():
    report = ConformanceReport(provider="p", checks=[
        CheckResult(name="a", status="passed"),
        CheckResult(name="b", status="skipped"),
    ])
    assert report.passed is True
    report.checks.append(CheckResult(name="c", status="failed"))
    assert report.passed is False


def test_report_json_round_trip():
    report = ConformanceReport(provider="p", checks=[
        CheckResult(name="a", status="passed", detail="fine")])
    data = json.loads(report.to_json())
    assert data["provider"] == "p"
    assert data["passed"] is True
    assert data["summary"] == {"passed": 1, "failed": 0, "skipped": 0}
    assert data["checks"][0]["name"] == "a"


# ----------------------------------------------------------------------
# run_conformance(): fake providers
# ----------------------------------------------------------------------

def test_conformance_openai_family_provider():
    provider = OpenAICompatProvider(api_key="fake-key",
                                    transport=_ok_transport)
    report = run_conformance(provider)
    assert report.provider == "openai"
    by_name = {c.name: c for c in report.checks}
    assert by_name["capability-flags"].status == "passed"
    assert by_name["chat-fake-transport"].status == "passed"
    assert by_name["structured-output"].status == "passed"
    assert by_name["vision"].status == "passed"
    assert by_name["iter-chunks-contract"].status == "skipped"
    assert report.passed is True


def test_conformance_visionless_jsonless_provider():
    provider = _make_provider("novel", {
        "streaming": False, "tool_calling": False,
        "vision": False, "json_mode": False})
    report = run_conformance(provider)
    by_name = {c.name: c for c in report.checks}
    assert by_name["chat-fake-transport"].status == "skipped"
    assert by_name["iter-chunks-contract"].status == "passed"
    assert by_name["structured-output"].status == "passed"
    assert by_name["vision"].status == "passed"
    assert report.passed is True


def test_conformance_detects_bad_capabilities():
    # A provider whose runtime capabilities() lies (probe at class
    # definition saw good flags; we corrupt the instance afterwards).
    provider = _make_provider("badcaps", {
        "streaming": True, "tool_calling": False,
        "vision": False, "json_mode": False})
    provider.capabilities = lambda: {"streaming": "yes"}  # type: ignore[method-assign]
    report = run_conformance(provider)
    by_name = {c.name: c for c in report.checks}
    assert by_name["capability-flags"].status == "failed"
    assert "boolean" in by_name["capability-flags"].detail.lower() or \
        "keys" in by_name["capability-flags"].detail.lower()
    assert report.passed is False


def test_conformance_chat_failure_is_recorded():
    def failing_transport(path, payload, headers):
        return (500, {"error": "boom"})

    provider = OpenAICompatProvider(api_key="fake-key",
                                    transport=failing_transport)
    report = run_conformance(provider)
    by_name = {c.name: c for c in report.checks}
    # The fake 500 must surface as a failed check, not a crash.
    assert by_name["chat-fake-transport"].status == "failed"
    assert report.passed is False


# ----------------------------------------------------------------------
# run_pantheon / render / write_report
# ----------------------------------------------------------------------

def test_run_pantheon_returns_all_reports():
    providers = [
        OpenAICompatProvider(api_key="fake-key", transport=_ok_transport),
        _make_provider("novel", {"streaming": False, "tool_calling": False,
                                 "vision": False, "json_mode": False}),
    ]
    reports = run_pantheon(providers)
    assert [r.provider for r in reports] == ["openai", "novel"]
    assert all(r.passed for r in reports)


def test_render_marks_status():
    report = ConformanceReport(provider="p", checks=[
        CheckResult(name="a", status="passed", detail="fine"),
        CheckResult(name="b", status="failed", detail="broken"),
        CheckResult(name="c", status="skipped", detail="n/a"),
    ])
    text = render(report)
    assert "FAIL" in text
    assert "[  ok] a" in text
    assert "[FAIL] b" in text
    assert "[skip] c" in text
    assert "1 passed, 1 failed, 1 skipped" in text


def test_write_report(tmp_path):
    report = ConformanceReport(provider="p", checks=[
        CheckResult(name="a", status="passed")])
    path = write_report(report, tmp_path / "reports" / "p.json")
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["provider"] == "p"
