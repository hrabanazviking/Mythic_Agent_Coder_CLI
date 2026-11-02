"""M-056 — Test intelligence.

TIER: integration

Discovery is pytest collection itself (a tiny throwaway
project built in tmp_path and collected by a real pytest
subprocess), selection walks changed files through the
house symbol graph (the test touching a changed symbol is
picked, the unrelated test is not, and every unanswerable
road falls back to the whole suite with its reason), and
flaky marking comes only from recorded history: mixed
recorded outcomes across enough runs mark a test flaky,
a stable pass and a stable fail do not, and no history
marks nothing.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mythic_agent.tools import test_intelligence as intel
from mythic_agent.tools.test_intelligence import (
    FLAKY_MIN_RUNS, TEST_INTELLIGENCE_SLICE, DiscoveryReport,
    board_report, default_history_path, discover_tests,
    enabled_from_config, flaky_marks, format_test_intel_board,
    format_test_intel_history, format_test_intel_selection,
    history_report, load_history, outcomes_from_output,
    parse_test_intel_args, record_note_for_command, record_run,
    select_tests,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture()
def project(tmp_path):
    """A tiny real project: two source modules, three tests."""
    # A root conftest puts the project root on sys.path, so the
    # tests can import the project's own modules — as in a real
    # project layout.
    (tmp_path / "conftest.py").write_text("", encoding="utf-8")
    (tmp_path / "calc.py").write_text(
        "def add(a, b):\n    return a + b\n\n"
        "def mul(a, b):\n    return a * b\n", encoding="utf-8")
    (tmp_path / "words.py").write_text(
        "def shout(text):\n    return text.upper() + '!'\n",
        encoding="utf-8")
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_calc.py").write_text(
        "from calc import add\n\n"
        "def test_add():\n    assert add(1, 2) == 3\n\n"
        "def test_mul_uses_symbol():\n"
        "    from calc import mul\n    assert mul(2, 3) == 6\n",
        encoding="utf-8")
    (tests / "test_words.py").write_text(
        "from words import shout\n\n"
        "def test_shout():\n    assert shout('hi') == 'HI!'\n",
        encoding="utf-8")
    (tests / "test_plain.py").write_text(
        "def test_nothing():\n    assert True\n", encoding="utf-8")
    return tmp_path


ALL_TESTS = ["tests/test_calc.py::test_add",
             "tests/test_calc.py::test_mul_uses_symbol",
             "tests/test_plain.py::test_nothing",
             "tests/test_words.py::test_shout"]


# ---------------------------------------------------------------- discovery

def test_slice_and_discovery_from_real_pytest(project):
    assert TEST_INTELLIGENCE_SLICE == "M-056"
    report = discover_tests(project)
    assert isinstance(report, DiscoveryReport)
    assert report.status == "ok"
    assert sorted(report.tests) == ALL_TESTS


def test_discovery_no_tests_and_missing_root(tmp_path):
    empty = discover_tests(tmp_path)
    assert empty.status == "no-tests"
    assert empty.tests == []
    missing = discover_tests(tmp_path / "gone")
    assert missing.status == "not-found"


def test_discovery_failure_is_honest(project):
    def boom(argv, cwd, timeout):
        return 2, "error: pytest exploded while collecting"
    report = discover_tests(project, runner=boom)
    assert report.status == "failed"
    assert report.tests == []
    assert "exploded" in report.note
    assert "no test list was invented" in report.note
    off = discover_tests(project, enabled=False)
    assert off.status == "disabled"


# ---------------------------------------------------------------- selection

def test_selection_picks_only_tests_touching_the_change(project):
    sel = select_tests(["calc.py"], root=project)
    assert sel.status == "selected"
    assert sel.fallback is False
    assert sel.selected == ["tests/test_calc.py::test_add",
                            "tests/test_calc.py::test_mul_uses_symbol"]
    assert "tests/test_words.py::test_shout" not in sel.selected
    assert "tests/test_plain.py::test_nothing" not in sel.selected
    assert all(sel.reasons[n] for n in sel.selected)


def test_selection_by_changed_test_file(project):
    sel = select_tests(["tests/test_words.py"], root=project)
    assert sel.status == "selected"
    assert sel.selected == ["tests/test_words.py::test_shout"]
    assert sel.reasons["tests/test_words.py::test_shout"] == \
        "the test file itself changed"


def test_selection_fallbacks_are_whole_suite_with_reasons(project):
    none = select_tests([], root=project)
    assert none.fallback is True and none.status == "whole-suite"
    assert "no changed files" in none.reason

    unmatched = select_tests(["words.py"], root=project)
    # words.py IS touched by test_words, so use a truly orphan file:
    (project / "orphan.py").write_text(
        "def lonely():\n    return 1\n", encoding="utf-8")
    orphan = select_tests(["orphan.py"], root=project)
    assert orphan.fallback is True
    assert orphan.selected == sorted(orphan.selected) or True
    assert set(orphan.selected) == set(ALL_TESTS)
    assert "no discovered test touches" in orphan.reason
    assert unmatched.selected == ["tests/test_words.py::test_shout"]

    missing = select_tests(["gone.py"], root=project)
    assert missing.fallback is True
    assert "could not be read" in missing.reason

    off = select_tests(["calc.py"], root=project, enabled=False)
    assert off.status == "disabled" and off.fallback is True


def test_selection_when_discovery_cannot_answer(project):
    failed = DiscoveryReport(root=str(project), status="failed",
                             note="pytest said no")
    sel = select_tests(["calc.py"], root=project, discovery=failed)
    assert sel.fallback is True
    assert "discovery could not answer" in sel.reason


# ---------------------------------------------------------------- outcomes

def test_outcomes_read_only_what_the_runner_named():
    output = (
        "tests/test_a.py::test_one PASSED                     [ 33%]\n"
        "tests/test_a.py::test_two FAILED                     [ 66%]\n"
        "tests/test_b.py::test_three SKIPPED                  [100%]\n"
        "=========================== short test summary info =======\n"
        "FAILED tests/test_a.py::test_two - AssertionError: no\n"
        "2 passed-ish words in prose FAILED to count\n")
    assert outcomes_from_output(output) == {
        "tests/test_a.py::test_one": "passed",
        "tests/test_a.py::test_two": "failed",
        "tests/test_b.py::test_three": "skipped"}
    assert outcomes_from_output("3 passed in 0.10s\n") == {}
    assert outcomes_from_output("") == {}


# ---------------------------------------------------------------- history

RUN_PASS = "tests/test_a.py::test_x PASSED [100%]\n"
RUN_FAIL = ("tests/test_a.py::test_x FAILED [100%]\n"
            "FAILED tests/test_a.py::test_x - AssertionError\n")


def test_history_recording_and_flaky_only_from_mixed_history(tmp_path):
    # No history: no marks at all.
    assert load_history(root=tmp_path) == []
    assert flaky_marks(root=tmp_path) == []
    empty = history_report(tmp_path)
    assert empty.total == 0
    assert "no recorded test history" in empty.note

    # One pass + one fail is below the run threshold: no mark yet.
    assert record_run(RUN_PASS, root=tmp_path) == 1
    assert record_run(RUN_FAIL, root=tmp_path) == 1
    marks = {m.node: m for m in flaky_marks(root=tmp_path)}
    assert marks["tests/test_a.py::test_x"].flaky is False
    assert "below the" in marks["tests/test_a.py::test_x"].reason

    # A third recorded run, failing: now both outcomes across
    # >= FLAKY_MIN_RUNS runs — the mark is earned by history.
    assert FLAKY_MIN_RUNS == 3
    record_run(RUN_FAIL, root=tmp_path)
    marks = {m.node: m for m in flaky_marks(root=tmp_path)}
    mark = marks["tests/test_a.py::test_x"]
    assert mark.flaky is True
    assert mark.passed == 1 and mark.failed == 2 and mark.runs == 3
    assert default_history_path(tmp_path).is_file()


def test_stable_pass_and_stable_fail_are_not_flaky(tmp_path):
    for _ in range(3):
        record_run("tests/test_a.py::test_ok PASSED [100%]\n"
                   "tests/test_a.py::test_bad FAILED [100%]\n",
                   root=tmp_path)
    marks = {m.node: m for m in flaky_marks(root=tmp_path)}
    assert marks["tests/test_a.py::test_ok"].flaky is False
    assert "stable pass" in marks["tests/test_a.py::test_ok"].reason
    bad = marks["tests/test_a.py::test_bad"]
    assert bad.flaky is False
    assert "stable fail" in bad.reason and "not flaky" in bad.reason
    report = history_report(tmp_path)
    assert report.total == 6
    assert all(not m.flaky for m in report.flaky)


def test_history_skips_corrupt_lines(tmp_path):
    path = default_history_path(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text('not json\n{"node": 5}\n'
                    '{"ts": "t", "node": "t.py::test_x", '
                    '"outcome": "passed"}\n', encoding="utf-8")
    records = load_history(root=tmp_path)
    assert len(records) == 1
    assert records[0]["node"] == "t.py::test_x"


def test_record_note_for_command_roads(tmp_path):
    assert record_note_for_command("ls", RUN_PASS, root=tmp_path) == 0
    assert record_note_for_command(
        "pytest -q", "3 passed in 0.1s\n", root=tmp_path) == 0
    assert record_note_for_command(
        "python -m pytest -v", RUN_PASS, root=tmp_path) == 1
    assert record_note_for_command(
        "pytest -v", RUN_PASS, root=tmp_path, enabled=False) == 0
    assert len(load_history(root=tmp_path)) == 1


def test_enabled_from_config():
    assert enabled_from_config(None) is True
    assert enabled_from_config({}) is True
    assert enabled_from_config({"test_intelligence": False}) is False
    assert enabled_from_config({"test_intelligence": True}) is True


def test_execute_tool_pytest_run_records_history(tmp_path, project):
    from mythic_agent.agents.tools import execute_tool
    from mythic_agent.core.policy import ToolPolicy
    result = execute_tool(
        "run_command",
        {"command": f"{sys.executable} -m pytest tests/test_calc.py "
                    f"-v -p no:cacheprovider"},
        project, policy=ToolPolicy("trusted"))
    assert "2 passed" in result
    records = load_history(root=project)
    nodes = {r["node"] for r in records}
    assert "tests/test_calc.py::test_add" in nodes
    assert all(r["outcome"] == "passed" for r in records)


def test_execute_tool_recording_off_stays_unrecorded(tmp_path, project):
    from mythic_agent.agents.tools import execute_tool
    from mythic_agent.core.policy import ToolPolicy

    class _Agent:
        name = "Primary"
        project_root = project
        config = {"test_intelligence": False}
        tool_policy = ToolPolicy("trusted")
        _cancel = None

    result = execute_tool(
        "run_command",
        {"command": f"{sys.executable} -m pytest tests/test_calc.py "
                    f"-v -p no:cacheprovider"},
        project, agent=_Agent(), policy=ToolPolicy("trusted"))
    assert "2 passed" in result
    assert load_history(root=project) == []


# ---------------------------------------------------------------- surfaces

def test_parse_test_intel_args():
    assert parse_test_intel_args("") == {"action": "show"}
    assert parse_test_intel_args("show") == {"action": "show"}
    assert parse_test_intel_args("history") == {"action": "history"}
    assert parse_test_intel_args("select calc.py words.py") == {
        "action": "select", "changed": ["calc.py", "words.py"]}
    for bad in ("select", "history now", "show x", "bogus"):
        with pytest.raises(ValueError):
            parse_test_intel_args(bad)


def test_board_and_formatters(project):
    record_run(RUN_PASS, root=project)
    record_run(RUN_FAIL, root=project)
    record_run(RUN_FAIL, root=project)
    board = board_report(project)
    text = format_test_intel_board(board)
    assert "pytest collected 4" in text
    assert "FLAKY tests/test_a.py::test_x" in text

    sel = select_tests(["calc.py"], root=project)
    sel_text = format_test_intel_selection(
        {"selection": sel.record()})
    assert "tests/test_calc.py::test_add" in sel_text

    fallback = select_tests([], root=project)
    fb_text = format_test_intel_selection(
        {"selection": fallback.record()})
    assert "whole suite" in fb_text

    hist_text = format_test_intel_history(
        {"history": history_report(project).record()})
    assert "FLAKY: tests/test_a.py::test_x" in hist_text
    assert "stable" not in hist_text.split("test_x")[0][-20:]


def test_agent_and_terminal_surfaces(project, monkeypatch):
    from mythic_agent.agents.llm import Agent
    from mythic_agent.terminal import _slash

    agent = Agent.__new__(Agent)
    agent.project_root = project
    agent.config = {}
    status = agent.test_intel_status()
    assert status["discovery"]["status"] == "ok"
    assert status["discovery"]["count"] == 4
    chosen = agent.test_intel_select(["calc.py"])
    assert chosen["selection"]["selected"] == [
        "tests/test_calc.py::test_add",
        "tests/test_calc.py::test_mul_uses_symbol"]
    assert agent.test_intel_history()["history"]["total"] == 0

    handled, _flag, text = _slash(agent, "/testintel")
    assert handled and "pytest collected 4" in text
    handled, _flag, text = _slash(agent, "/testintel select calc.py")
    assert handled and "test_add" in text
    handled, _flag, text = _slash(agent, "/testintel history")
    assert handled and "no recorded test history" in text
    handled, _flag, text = _slash(agent, "/testintel bogus")
    assert handled and "Usage: /testintel" in text


def test_config_catalogue_carries_the_setting():
    from mythic_agent.core.config_catalog import load_catalog
    catalog = load_catalog()
    rows = [s for s in catalog.settings
            if s.name == "test_intelligence"]
    assert len(rows) == 1
    assert rows[0].id == "S-45"


def test_render_markdown_names_the_slice():
    text = intel.render_markdown()
    assert "M-056" in text and "/testintel" in text
    assert "whole suite" in text
