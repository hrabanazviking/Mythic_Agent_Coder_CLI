"""M-057 — Coverage sight.

TIER: integration

Coverage data is coverage.py's own: a tiny throwaway
project is run under a real `coverage run` (its JSON
report and its .coverage data file are both read), the
overlay over the touched files counts only the lines
that data names, an untouched module measured with zero
executed lines is flagged to the Auditor through the
house audit log, and every absence — no data, a file the
data never measured, a file that is not there — is named
honestly instead of being dressed as 0%.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mythic_agent.core.audit import AuditLog
from mythic_agent.tools import coverage_sight as sight
from mythic_agent.tools.coverage_sight import (
    COVERAGE_SLICE, ZERO_COVER_ACTION, board_report,
    coverage_check, enabled_from_config, find_coverage_source,
    flag_zero_cover, format_coverage_board,
    format_coverage_overlay, load_coverage, overlay_report,
    parse_coverage_args, render_markdown,
)

REPO_ROOT = Path(__file__).resolve().parent.parent

CALC = "def add(a, b):\n    return a + b\n\ndef mul(a, b):\n    return a * b\n"
UNTOUCHED = "def never(x):\n    return x + 1\n"


@pytest.fixture()
def project(tmp_path):
    """A tiny project: one partly-covered module, one untouched."""
    (tmp_path / "conftest.py").write_text("", encoding="utf-8")
    (tmp_path / "calc.py").write_text(CALC, encoding="utf-8")
    (tmp_path / "untouched.py").write_text(UNTOUCHED, encoding="utf-8")
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_calc.py").write_text(
        "from calc import add\n\n"
        "def test_add():\n    assert add(1, 2) == 3\n",
        encoding="utf-8")
    return tmp_path


def _run_coverage(project, *, make_json=True):
    """A real coverage.py run over the fixture project's tests."""
    run = subprocess.run(
        [sys.executable, "-m", "coverage", "run",
         f"--source={project}", "-m", "pytest", "-q",
         "-p", "no:cacheprovider"],
        cwd=str(project), capture_output=True, text=True, timeout=180)
    assert run.returncode == 0, run.stdout + run.stderr
    if make_json:
        out = subprocess.run(
            [sys.executable, "-m", "coverage", "json",
             "-o", "coverage.json"],
            cwd=str(project), capture_output=True, text=True,
            timeout=120)
        assert out.returncode == 0, out.stdout + out.stderr


# ---------------------------------------------------------------- basics

def test_slice_and_config_switch():
    assert COVERAGE_SLICE == "M-057"
    assert ZERO_COVER_ACTION == "coverage.zero_cover"
    assert enabled_from_config(None) is True
    assert enabled_from_config({}) is True
    assert enabled_from_config({"coverage_sight": False}) is False
    assert "coverage.json" in sight.default_json_names()


def test_setting_is_in_defaults_and_catalogue():
    import yaml

    defaults = yaml.safe_load(
        (REPO_ROOT / "mythic_agent/data/config_defaults.yaml")
        .read_text(encoding="utf-8"))
    assert defaults["coverage_sight"] is True
    from mythic_agent.core.config_catalog import load_catalog
    catalog = load_catalog()
    entry = {s.name: s for s in catalog.settings}["coverage_sight"]
    assert entry.id == "S-46"
    assert entry.default == "True"


# ---------------------------------------------------------------- no data

def test_no_data_is_honest_absence(project):
    assert find_coverage_source(project) is None
    data = load_coverage(project)
    assert data.status == "no-data"
    assert data.files == {}
    assert "coverage run" in data.note
    board = board_report(project)
    assert board["coverage"]["status"] == "no-data"
    text = format_coverage_board(board)
    assert "no-data" in text


def test_disabled_reads_nothing(project):
    data = load_coverage(project, enabled=False)
    assert data.status == "disabled"
    report = overlay_report(["calc.py"], root=project, enabled=False)
    assert report.status == "disabled"
    assert report.flags == []


def test_no_data_overlay_names_it(project):
    report = coverage_check(["calc.py"], root=project)
    assert report.status == "no-data"
    assert report.files[0].status == "no-data"
    assert report.flags_written == 0
    assert not (project / ".mythic" / "audit.jsonl").exists()


# ---------------------------------------------------------------- json road

def _write_json(project, files):
    payload = {"files": files, "totals": {}}
    (project / "coverage.json").write_text(
        json.dumps(payload), encoding="utf-8")


def test_json_report_is_parsed_as_measured(project):
    _write_json(project, {
        "calc.py": {"executed_lines": [1, 2, 4],
                    "missing_lines": [5],
                    "summary": {"percent_covered": 75.0}},
        "untouched.py": {"executed_lines": [],
                         "missing_lines": [1, 2],
                         "summary": {"percent_covered": 0.0}},
    })
    assert find_coverage_source(project) == project / "coverage.json"
    data = load_coverage(project)
    assert data.status == "ok" and data.source_kind == "json"
    calc = data.files["calc.py"]
    assert calc.statements == [1, 2, 4, 5]
    assert calc.percent == pytest.approx(75.0)
    assert data.files["untouched.py"].percent == 0.0


def test_malformed_json_is_failed_not_invented(project):
    (project / "coverage.json").write_text("{nope", encoding="utf-8")
    data = load_coverage(project)
    assert data.status == "failed"
    assert data.files == {}


def test_json_without_files_is_failed(project):
    (project / "coverage.json").write_text(
        json.dumps({"hello": 1}), encoding="utf-8")
    data = load_coverage(project)
    assert data.status == "failed"
    assert "files" in data.note


# ---------------------------------------------------------------- real run

def test_real_coverage_json_overlay(project):
    _run_coverage(project)
    data = load_coverage(project)
    assert data.status == "ok" and data.source_kind == "json"
    report = overlay_report(["calc.py"], root=project)
    entry = report.files[0]
    assert entry.status == "ok"
    # def add / its return / def mul ran at import+test; only
    # mul's return (line 5) was measured missed.
    assert entry.missed_lines == [5]
    assert entry.covered == entry.statements - 1
    assert entry.zero_cover is False
    assert report.flags == []


def test_real_coverage_data_file_road(project):
    _run_coverage(project, make_json=False)
    assert find_coverage_source(project) == project / ".coverage"
    data = load_coverage(project)
    assert data.status == "ok" and data.source_kind == "data-file"
    entry = overlay_report(["calc.py"], root=project).files[0]
    assert entry.missed_lines == [5]
    assert entry.zero_cover is False


def test_zero_cover_flag_reaches_the_auditor(project):
    _run_coverage(project)
    report = coverage_check(["calc.py", "untouched.py"], root=project)
    by_path = {f.path: f for f in report.files}
    assert by_path["calc.py"].zero_cover is False
    assert by_path["untouched.py"].zero_cover is True
    assert by_path["untouched.py"].covered == 0
    assert by_path["untouched.py"].statements == 2
    assert report.zero_cover_files == ["untouched.py"]
    assert report.flags_written == 1
    entries = AuditLog(project).query({"action": ZERO_COVER_ACTION})
    assert len(entries) == 1
    assert entries[0].details["file"] == "untouched.py"
    assert entries[0].details["covered"] == 0
    assert entries[0].actor == "coverage_sight"


def test_overlay_alone_writes_no_flags(project):
    _run_coverage(project)
    report = overlay_report(["untouched.py"], root=project)
    assert report.zero_cover_files == ["untouched.py"]
    assert len(report.flags) == 1
    assert report.flags_written == 0
    assert not (project / ".mythic" / "audit.jsonl").exists()
    assert flag_zero_cover(report, root=project) == 1
    assert (project / ".mythic" / "audit.jsonl").exists()


def test_edited_lines_zero_cover_even_when_file_covered(project):
    _run_coverage(project)
    # Line 5 (mul's return) is executable and never ran.
    report = coverage_check(
        ["calc.py"], root=project, edited_lines={"calc.py": [5]})
    entry = report.files[0]
    assert entry.edited_executable == [5]
    assert entry.edited_covered == []
    assert entry.zero_cover is True
    assert report.flags_written == 1
    # Line 2 (add's return) ran — no flag.
    report2 = coverage_check(
        ["calc.py"], root=project, edited_lines={"calc.py": [2]})
    assert report2.files[0].zero_cover is False
    assert report2.flags_written == 0


def test_file_not_in_coverage_is_not_zero(project):
    _run_coverage(project)
    (project / "stray.py").write_text("X = 1\n", encoding="utf-8")
    report = coverage_check(["stray.py", "ghost.py"], root=project)
    by_path = {f.path: f for f in report.files}
    assert by_path["stray.py"].status == "not-in-coverage"
    assert by_path["stray.py"].zero_cover is False
    assert by_path["ghost.py"].status == "not-found"
    assert report.flags_written == 0


# ---------------------------------------------------------------- surfaces

def test_parser_roads():
    assert parse_coverage_args("") == {"action": "show"}
    assert parse_coverage_args("show") == {"action": "show"}
    assert parse_coverage_args("check a.py b.py") == {
        "action": "check", "changed": ["a.py", "b.py"]}
    with pytest.raises(ValueError):
        parse_coverage_args("check")
    with pytest.raises(ValueError):
        parse_coverage_args("show extra")
    with pytest.raises(ValueError):
        parse_coverage_args("bogus")


def test_formatters_and_markdown(project):
    _run_coverage(project)
    board_text = format_coverage_board(board_report(project))
    assert "Coverage data: ok" in board_text
    status = {"report": coverage_check(
        ["untouched.py"], root=project).record(),
        "plain_explanation": sight.PLAIN_EXPLANATION}
    text = format_coverage_overlay(status)
    assert "ZERO COVER" in text
    assert "flag(s) written to the audit log" in text
    md = render_markdown()
    assert "M-057" in md and ZERO_COVER_ACTION in md
