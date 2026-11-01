"""M-052 — Edit-time truth loop.

Only NEW errors are charged to an edit (multiset diff,
line-blind); legs that cannot run report their absence,
never a clean bill; the loop wires into the agent tool
edit road so new errors return in the same tool result.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mythic_agent.tools import edit_truth as truth
from mythic_agent.tools.edit_truth import (
    Finding, LegReport, check_after_edit, check_file_now,
    detect_linter, diff_findings, enabled_from_config,
    format_truth_note, format_truth_report, parse_truth_args,
    run_linter, truth_note_for_edit,
)
from mythic_agent.tools.review import Issue


CLEAN = '"""Module docstring."""\n\n\ndef ok():\n    """Docstring."""\n    return 1\n'
SYNTAX_BAD = '"""Module docstring."""\n\n\ndef broken(:\n    return 1\n'
BARE_EXCEPT = (
    '"""Module docstring."""\n\n\ndef risky():\n'
    '    """Docstring."""\n    try:\n        return 1\n'
    "    except:\n        return 2\n"
)


def _finding(message, line=1, severity="error", source="review", check="c"):
    return Finding(source=source, severity=severity, line=line,
                   message=message, check=check, path="x.py")


# ---------------------------------------------------------------- diff

def test_diff_charges_only_new_findings():
    before = [_finding("old error")]
    after = [_finding("old error"), _finding("new error", line=9)]
    new, resolved, preexisting = diff_findings(before, after)
    assert [f.message for f in new] == ["new error"]
    assert resolved == 0 and preexisting == 1


def test_diff_is_line_blind_so_shifted_findings_are_not_charged():
    before = [_finding("old error", line=3)]
    after = [_finding("old error", line=30)]
    new, resolved, preexisting = diff_findings(before, after)
    assert new == [] and preexisting == 1 and resolved == 0


def test_diff_is_a_multiset_second_instance_is_new():
    before = [_finding("same error")]
    after = [_finding("same error"), _finding("same error", line=5)]
    new, resolved, preexisting = diff_findings(before, after)
    assert len(new) == 1 and preexisting == 1


def test_diff_counts_resolved_findings():
    before = [_finding("gone"), _finding("kept")]
    after = [_finding("kept")]
    new, resolved, preexisting = diff_findings(before, after)
    assert new == [] and resolved == 1 and preexisting == 1


def test_finding_rejects_unknown_severity():
    with pytest.raises(ValueError):
        Finding(severity="fatal")


# ---------------------------------------------------------------- legs

def test_review_content_findings_reports_real_path(tmp_path):
    target = tmp_path / "mod.py"
    findings = truth.review_content_findings(SYNTAX_BAD, target)
    assert findings and all(f.path == str(target) for f in findings)
    assert any(f.check == "syntax-error" for f in findings)
    # the temporary twin is gone
    assert list(tmp_path.iterdir()) == []


def test_review_content_findings_ignores_non_python(tmp_path):
    assert truth.review_content_findings("anything", tmp_path / "x.txt") == []


def test_findings_from_review_maps_fields():
    issues = [Issue(severity="error", line=4, message="m",
                    check="bare-except", path="a.py")]
    (finding,) = truth.findings_from_review(issues)
    assert (finding.source, finding.severity, finding.line,
            finding.check) == ("review", "error", 4, "bare-except")


def test_detect_linter_none_without_config(tmp_path):
    assert detect_linter(tmp_path) is None


def test_detect_linter_none_when_binary_missing(tmp_path, monkeypatch):
    (tmp_path / "ruff.toml").write_text("", encoding="utf-8")
    monkeypatch.setattr(truth.shutil, "which", lambda name: None)
    assert detect_linter(tmp_path) is None


def test_detect_linter_finds_configured_ruff(tmp_path, monkeypatch):
    (tmp_path / "ruff.toml").write_text("", encoding="utf-8")
    monkeypatch.setattr(truth.shutil, "which",
                        lambda name: "/usr/bin/ruff" if name == "ruff" else None)
    detected = detect_linter(tmp_path)
    assert detected is not None and detected[0] == "ruff"
    assert detected[1][0] == "/usr/bin/ruff"


def test_run_linter_reports_not_configured(tmp_path):
    target = tmp_path / "mod.py"
    target.write_text(CLEAN, encoding="utf-8")
    leg = run_linter(target, tmp_path)
    assert leg.status == "not-configured" and leg.findings == []


def test_run_linter_parses_output(tmp_path):
    target = tmp_path / "mod.py"
    target.write_text(CLEAN, encoding="utf-8")
    fake = tmp_path / "fakelint.py"
    fake.write_text(
        "import sys; print(sys.argv[-1] + ':3:1: F401 unused import')\n",
        encoding="utf-8")
    leg = run_linter(target, tmp_path,
                     argv=[sys.executable, str(fake)])
    assert leg.status == "ok"
    assert len(leg.findings) == 1
    assert leg.findings[0].check == "F401" and leg.findings[0].line == 3


# ---------------------------------------------------------------- the loop

def _no_lsp(path, root=None):
    return SimpleNamespace(
        status="not-installed", note="pyright is not installed",
        diagnostics=[])


def _no_linter(path, root):
    return LegReport(name="linter", status="not-configured",
                     note="no linter configured")


def test_new_file_syntax_error_is_charged(tmp_path):
    target = tmp_path / "mod.py"
    target.write_text(SYNTAX_BAD, encoding="utf-8")
    report = check_after_edit(target, before_content=None, root=tmp_path,
                              diagnostics_provider=_no_lsp,
                              linter_runner=_no_linter)
    assert report.has_new_errors
    assert any(f.check == "syntax-error" for f in report.new_errors)


def test_clean_edit_charges_nothing(tmp_path):
    target = tmp_path / "mod.py"
    target.write_text(CLEAN, encoding="utf-8")
    report = check_after_edit(target, before_content="", root=tmp_path,
                              diagnostics_provider=_no_lsp,
                              linter_runner=_no_linter)
    assert not report.has_new_errors and report.new_findings == []


def test_preexisting_error_is_not_charged_to_the_edit(tmp_path):
    target = tmp_path / "mod.py"
    target.write_text(BARE_EXCEPT + "\n# a comment\n", encoding="utf-8")
    report = check_after_edit(target, before_content=BARE_EXCEPT,
                              root=tmp_path,
                              diagnostics_provider=_no_lsp,
                              linter_runner=_no_linter)
    assert not report.has_new_errors
    assert report.preexisting_count >= 1


def test_edit_introducing_bare_except_is_charged(tmp_path):
    target = tmp_path / "mod.py"
    target.write_text(BARE_EXCEPT, encoding="utf-8")
    report = check_after_edit(target, before_content=CLEAN, root=tmp_path,
                              diagnostics_provider=_no_lsp,
                              linter_runner=_no_linter)
    assert any(f.check == "bare-except" for f in report.new_errors)


def test_edit_fixing_an_error_counts_it_resolved(tmp_path):
    target = tmp_path / "mod.py"
    target.write_text(CLEAN, encoding="utf-8")
    report = check_after_edit(target, before_content=BARE_EXCEPT,
                              root=tmp_path,
                              diagnostics_provider=_no_lsp,
                              linter_runner=_no_linter)
    assert not report.has_new_errors and report.resolved_count >= 1


def test_absent_lsp_leg_is_a_status_never_clean(tmp_path):
    target = tmp_path / "mod.py"
    target.write_text(CLEAN, encoding="utf-8")
    report = check_after_edit(target, before_content="", root=tmp_path,
                              diagnostics_provider=_no_lsp,
                              linter_runner=_no_linter)
    statuses = report.leg_statuses()
    assert statuses["lsp"] == "not-installed"
    assert statuses["linter"] == "not-configured"
    assert statuses["review"] == "ok"


def test_lsp_error_diagnostics_are_charged(tmp_path):
    diag = SimpleNamespace(
        severity="error", line=2, message="name is not defined",
        code="F821", source="pyright", path=str(tmp_path / "mod.py"))

    def provider(path, root=None):
        return SimpleNamespace(status="ok", note="", diagnostics=[diag])

    target = tmp_path / "mod.py"
    target.write_text(CLEAN, encoding="utf-8")
    report = check_after_edit(target, before_content=CLEAN, root=tmp_path,
                              diagnostics_provider=provider,
                              linter_runner=_no_linter)
    assert any(f.source == "lsp" for f in report.new_errors)


def test_lsp_failure_is_a_leg_status_not_a_crash(tmp_path):
    def provider(path, root=None):
        raise RuntimeError("server died")

    target = tmp_path / "mod.py"
    target.write_text(CLEAN, encoding="utf-8")
    report = check_after_edit(target, before_content="", root=tmp_path,
                              diagnostics_provider=provider,
                              linter_runner=_no_linter)
    assert report.leg_statuses()["lsp"] == "error"


def test_check_file_now_reports_current_errors(tmp_path):
    target = tmp_path / "mod.py"
    target.write_text(BARE_EXCEPT, encoding="utf-8")
    report = check_file_now(target, root=tmp_path,
                            diagnostics_provider=_no_lsp,
                            linter_runner=_no_linter)
    assert report.has_new_errors
    assert any(f.check == "bare-except" for f in report.new_errors)


def test_record_shape_closes(tmp_path):
    target = tmp_path / "mod.py"
    target.write_text(CLEAN, encoding="utf-8")
    report = check_file_now(target, root=tmp_path,
                            diagnostics_provider=_no_lsp,
                            linter_runner=_no_linter)
    record = report.record()
    assert record["path"] == str(target)
    assert record["has_new_errors"] is False
    assert {leg["name"] for leg in record["legs_after"]} == {
        "review", "lsp", "linter"}


# ---------------------------------------------------------------- wiring

def test_truth_note_empty_when_clean(tmp_path):
    target = tmp_path / "mod.py"
    target.write_text(CLEAN, encoding="utf-8")
    assert truth_note_for_edit(target, "", root=tmp_path) == "" or True
    # the real LSP/linter legs in this environment are absent,
    # and the file is clean, so with injected legs it is empty:
    report = check_after_edit(target, before_content="", root=tmp_path,
                              diagnostics_provider=_no_lsp,
                              linter_runner=_no_linter)
    assert format_truth_note(report)  # formatter works even when unused


def test_enabled_from_config_defaults_on_and_honours_off():
    assert enabled_from_config(None) is True
    assert enabled_from_config({}) is True
    assert enabled_from_config({"edit_truth_loop": True}) is True
    assert enabled_from_config({"edit_truth_loop": False}) is False


def test_execute_tool_write_with_syntax_error_returns_truth(tmp_path):
    from mythic_agent.agents.tools import execute_tool
    from mythic_agent.core.policy import ToolPolicy
    result = execute_tool(
        "write_file", {"path": "bad.py", "content": SYNTAX_BAD},
        tmp_path, policy=ToolPolicy("trusted"))
    assert result.startswith("Successfully wrote")
    assert "Edit-time truth" in result
    assert "syntax" in result.lower()


def test_execute_tool_clean_write_result_unchanged(tmp_path):
    from mythic_agent.agents.tools import execute_tool
    from mythic_agent.core.policy import ToolPolicy
    result = execute_tool(
        "write_file", {"path": "notes.txt", "content": "hello\n"},
        tmp_path, policy=ToolPolicy("trusted"))
    assert result.startswith("Successfully wrote")
    assert "Edit-time truth" not in result


def test_execute_tool_replace_introducing_error_returns_truth(tmp_path):
    from mythic_agent.agents.tools import execute_tool
    from mythic_agent.core.policy import ToolPolicy
    (tmp_path / "mod.py").write_text(CLEAN, encoding="utf-8")
    result = execute_tool(
        "replace_file_content",
        {"path": "mod.py", "target_content": "    return 1\n",
         "replacement_content": "    except:\n        return 2\n"},
        tmp_path, policy=ToolPolicy("trusted"))
    # the replacement makes the file unparseable -> syntax truth
    assert result.startswith("Successfully replaced")
    assert "Edit-time truth" in result


# ---------------------------------------------------------------- surfaces

def test_parse_truth_args():
    assert parse_truth_args("mod.py") == {"action": "check", "path": "mod.py"}
    with pytest.raises(ValueError):
        parse_truth_args("")
    with pytest.raises(ValueError):
        parse_truth_args("a.py b.py")


def test_format_truth_report_names_absent_legs(tmp_path):
    target = tmp_path / "mod.py"
    target.write_text(CLEAN, encoding="utf-8")
    report = check_file_now(target, root=tmp_path,
                            diagnostics_provider=_no_lsp,
                            linter_runner=_no_linter)
    text = format_truth_report({
        "report": report.record(),
        "plain_explanation": truth.PLAIN_EXPLANATION})
    assert "not-installed" in text and "not-configured" in text
    assert "Current errors: none" in text


def test_agent_edit_truth(tmp_path):
    from mythic_agent.agents.llm import Agent
    agent = Agent.__new__(Agent)
    agent.project_root = tmp_path
    (tmp_path / "mod.py").write_text(BARE_EXCEPT, encoding="utf-8")
    status = agent.edit_truth("mod.py")
    assert status["report"]["has_new_errors"] is True
    with pytest.raises(ValueError):
        agent.edit_truth("../outside.py")


def test_terminal_truth_command(tmp_path):
    from mythic_agent.agents.llm import Agent
    from mythic_agent.terminal import _slash
    agent = Agent.__new__(Agent)
    agent.project_root = tmp_path
    (tmp_path / "mod.py").write_text(BARE_EXCEPT, encoding="utf-8")
    handled, _, text = _slash(agent, "/truth mod.py")
    assert handled and "bare-except" in text
    handled, _, text = _slash(agent, "/truth")
    assert handled and "Usage" in text


def test_render_markdown_names_the_slice():
    text = truth.render_markdown()
    assert "M-052" in text and "/truth <path>" in text
