"""Tests for mythic_agent.doctor (Slice 11)."""

import json

from mythic_agent.doctor import (
    HealthResult,
    HealthStatus,
    health_check,
    print_results,
    run_checks,
)


def test_health_check_decorator_registers():
    @health_check("test_dummy_xyz")
    def dummy():
        return HealthResult("test_dummy_xyz", HealthStatus.OK, "ok")
    results = run_checks(["test_dummy_xyz"])
    assert len(results) == 1
    assert results[0].name == "test_dummy_xyz"


def test_run_checks_returns_results():
    results = run_checks(["workspace", "dependencies"])
    assert len(results) == 2
    names = {r.name for r in results}
    assert names == {"workspace", "dependencies"}


def test_print_results_json(capsys):
    results = [
        HealthResult("a", HealthStatus.OK, "fine"),
        HealthResult("b", HealthStatus.FAIL, "broken", fix_hint="fix it"),
    ]
    code = print_results(results, as_json=True)
    assert code == 1
    out = capsys.readouterr().out
    data = json.loads(out)
    assert len(data) == 2
    assert data[1]["fix_hint"] == "fix it"


def test_print_results_text(capsys):
    results = [HealthResult("a", HealthStatus.OK, "fine")]
    code = print_results(results, as_json=False)
    assert code == 0
    out = capsys.readouterr().out
    assert "✓" in out
    assert "fine" in out


def test_workspace_check_passes():
    results = run_checks(["workspace"])
    assert results[0].status in (HealthStatus.OK, HealthStatus.WARNING)


def test_check_crash_becomes_fail():
    @health_check("test_crash_xyz")
    def crasher():
        raise RuntimeError("boom")
    results = run_checks(["test_crash_xyz"])
    assert results[0].status == HealthStatus.FAIL
    assert "boom" in results[0].message
