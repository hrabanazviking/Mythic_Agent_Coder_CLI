"""Tests for M-063 — Type-aware Python depth.

TIER: integration

mypy/pyright findings are parsed only from the checkers'
own output contracts, triaged by kind, and charged to an
edit only when they are new against the before-content
account (line-blind multiset diff, the M-052 road).
Neither checker is installed in this environment, so the
absence verdict is proven honestly and live proof rides
fake runner binaries on PATH speaking the real output
contracts (the M-053 pattern). Every test runs on a
throwaway workspace.
"""

from __future__ import annotations

import importlib.util
import os
import stat
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mythic_agent.tools import type_depth as td
from mythic_agent.tools.type_depth import (
    PLAIN_EXPLANATION,
    TYPE_SLICE,
    USAGE,
    TypeFinding,
    check_after_edit,
    classify_finding,
    detect_runners,
    format_type_report,
    parse_mypy_output,
    parse_pyright_output,
    parse_types_args,
    render_markdown,
    run_type_check,
    triage_findings,
    type_depth,
    type_note_for_edit,
)

CLEAN = '"""Module docstring."""\n\n\ndef ok() -> int:\n    """Docstring."""\n    return 1\n'
BROKEN = CLEAN + "\n# TYPE_ERROR\n"
ATTR_BROKEN = CLEAN + "\n# TYPE_ATTR\n"

FAKE_MYPY = '''#!/usr/bin/env python3
import sys
from pathlib import Path

targets = [Path(a) for a in sys.argv[1:] if not a.startswith("-")]
files = []
for target in targets:
    if target.is_dir():
        files.extend(sorted(target.rglob("*.py")))
    elif target.is_file():
        files.append(target)
out = []
for path in files:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for lineno, line in enumerate(lines, 1):
        if "TYPE_ERROR" in line:
            out.append(
                f"{path}:{lineno}:5: error: Incompatible types in "
                f"assignment (expression has type \\"str\\", variable "
                f"has type \\"int\\")  [assignment]")
        if "TYPE_ATTR" in line:
            out.append(
                f"{path}:{lineno}:5: error: \\"int\\" has no attribute "
                f"\\"poke\\"  [attr-defined]")
        if "TYPE_ANNOT" in line:
            out.append(
                f"{path}:{lineno}:1: error: Function is missing a "
                f"return type annotation  [no-untyped-def]")
print("\\n".join(out))
sys.exit(1 if out else 0)
'''

FAKE_PYRIGHT = '''#!/usr/bin/env python3
import json
import sys
from pathlib import Path

targets = [Path(a) for a in sys.argv[1:] if not a.startswith("-")]
files = []
for target in targets:
    if target.is_dir():
        files.extend(sorted(target.rglob("*.py")))
    elif target.is_file():
        files.append(target)
diags = []
for path in files:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for lineno, line in enumerate(lines, 1):
        if "TYPE_ERROR" in line:
            diags.append({
                "file": str(path), "severity": "error",
                "message": "Expression of type \\"str\\" cannot be "
                           "assigned to declared type \\"int\\"",
                "range": {"start": {"line": lineno - 1, "character": 4},
                          "end": {"line": lineno - 1, "character": 9}},
                "rule": "reportAssignmentType"})
print(json.dumps({"generalDiagnostics": diags, "summary": {}}))
sys.exit(1 if diags else 0)
'''


@pytest.fixture()
def project(tmp_path: Path) -> Path:
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "mod.py").write_text(CLEAN, encoding="utf-8")
    return tmp_path


def _no_runners(monkeypatch):
    """Deterministic absence: no binary, no importable module."""
    monkeypatch.setattr(
        td.shutil, "which", lambda name: None)
    monkeypatch.setattr(
        importlib.util, "find_spec", lambda name: None)


def _install(monkeypatch, tmp_path: Path, name: str, script: str):
    bin_dir = tmp_path / "fakebin"
    bin_dir.mkdir(exist_ok=True)
    binary = bin_dir / name
    binary.write_text(script, encoding="utf-8")
    binary.chmod(binary.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv(
        "PATH", os.pathsep.join(
            [str(bin_dir), "/usr/bin", "/bin"]))
    monkeypatch.setattr(
        importlib.util, "find_spec", lambda mod: None)
    return binary


def _finding(message="Incompatible types in assignment",
             code="assignment", line=5, path="x.py",
             runner="mypy"):
    return TypeFinding(
        runner=runner, severity="error", path=path, line=line,
        code=code, message=message,
        category=classify_finding(code, message))


# ---------------------------------------------------------------- identity

def test_slice_identity_and_config():
    assert TYPE_SLICE == "M-063"
    assert td.enabled_from_config(None) is True
    assert td.enabled_from_config({}) is True
    assert td.enabled_from_config({"type_depth": False}) is False
    assert "NOT" in PLAIN_EXPLANATION and "PROVEN" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /types")


# ---------------------------------------------------------------- parsers

def test_parse_mypy_contract_lines_only():
    text = (
        'pkg/mod.py:7:5: error: Incompatible types in assignment '
        '(expression has type "str", variable has type "int")  [assignment]\n'
        'pkg/mod.py:9:1: error: Function is missing a return type '
        'annotation  [no-untyped-def]\n'
        'pkg/mod.py:11: warning: Something worth a look  [misc]\n'
        'pkg/mod.py:12: note: A side remark\n'
        'Found 3 errors in 1 file (checked 1 source file)\n'
        'this is not a mypy line at all\n')
    findings = parse_mypy_output(text)
    assert len(findings) == 4
    first = findings[0]
    assert (first.runner, first.path, first.line, first.col) == \
        ("mypy", "pkg/mod.py", 7, 5)
    assert first.code == "assignment"
    assert first.category == "incompatible"
    assert "Incompatible types" in first.message
    assert findings[1].category == "annotation"
    assert findings[2].severity == "warning"
    assert findings[3].severity == "info"  # a mypy note rides as info


def test_parse_pyright_json_contract():
    text = (
        '{"generalDiagnostics": ['
        '{"file": "/w/pkg/mod.py", "severity": "error", '
        '"message": "Expression of type \\"str\\" cannot be assigned '
        'to declared type \\"int\\"", '
        '"range": {"start": {"line": 6, "character": 4}, '
        '"end": {"line": 6, "character": 9}}, '
        '"rule": "reportAssignmentType"}, '
        '{"file": "/w/pkg/mod.py", "severity": "warning", '
        '"message": "Type is partially unknown", '
        '"range": {"start": {"line": 0, "character": 0}, '
        '"end": {"line": 0, "character": 1}}, '
        '"rule": "reportUnknownType"}], "summary": {}}')
    findings = parse_pyright_output(text)
    assert len(findings) == 2
    first = findings[0]
    assert first.runner == "pyright"
    assert (first.line, first.col) == (7, 5)  # 0-based -> 1-based
    assert first.code == "reportAssignmentType"
    assert first.category == "incompatible"
    assert findings[1].severity == "warning"
    assert parse_pyright_output("{not json") == []


def test_parse_pyright_text_contract():
    text = (
        "  /w/pkg/mod.py:3:5 - error: \"int\" has no attribute "
        "\"poke\" (reportAttributeAccessIssue)\n"
        "  /w/pkg/mod.py is not a finding\n")
    findings = parse_pyright_output(text)
    assert len(findings) == 1
    assert findings[0].category == "attribute"
    assert findings[0].code == "reportAttributeAccessIssue"
    assert (findings[0].line, findings[0].col) == (3, 5)


def test_classify_finding_kinds():
    assert classify_finding("no-untyped-def", "missing annotation") == \
        "annotation"
    assert classify_finding("assignment", "Incompatible types") == \
        "incompatible"
    assert classify_finding("attr-defined", '"int" has no attribute') == \
        "attribute"
    assert classify_finding("name-defined", 'Name "x" is not defined') == \
        "name"
    assert classify_finding("weird-code", "Something else entirely") == \
        "other"


# ---------------------------------------------------------------- detection

def test_detect_runners_honest_absence(monkeypatch, project):
    _no_runners(monkeypatch)
    runners = detect_runners(project)
    assert [r.name for r in runners] == ["mypy", "pyright"]
    assert all(r.status == "not-installed" for r in runners)
    assert all(not r.available for r in runners)
    assert all("not installed" in r.note for r in runners)


def test_detect_runners_configured_by_the_project(monkeypatch, project):
    _no_runners(monkeypatch)
    (project / "mypy.ini").write_text("[mypy]\n", encoding="utf-8")
    (project / "pyrightconfig.json").write_text("{}", encoding="utf-8")
    runners = {r.name: r for r in detect_runners(project)}
    assert runners["mypy"].configured is True
    assert runners["pyright"].configured is True
    # configuration never invents an installation
    assert runners["mypy"].available is False


def test_standing_check_without_runners_is_not_proven(
        monkeypatch, project):
    _no_runners(monkeypatch)
    report = type_depth(project, project / "pkg" / "mod.py")
    assert report.status == "not-installed"
    assert report.findings == []
    assert "NOT PROVEN" in report.note
    assert report.runner_names() == ()


# ---------------------------------------------------------------- live fakes

def test_fake_mypy_live_run(monkeypatch, tmp_path, project):
    _install(monkeypatch, tmp_path, "mypy", FAKE_MYPY)
    target = project / "pkg" / "mod.py"
    target.write_text(BROKEN, encoding="utf-8")
    report = run_type_check(project, [target])
    assert report.status == "ok"
    assert report.runner_names() == ("mypy",)
    assert len(report.findings) == 1
    finding = report.findings[0]
    assert finding.category == "incompatible"
    assert finding.verdict == "standing"
    assert finding.code == "assignment"
    clean = run_type_check(project, [project / "pkg" / "__init__.py"])
    assert clean.status == "ok" and clean.findings == []


def test_fake_pyright_live_run(monkeypatch, tmp_path, project):
    _install(monkeypatch, tmp_path, "pyright", FAKE_PYRIGHT)
    target = project / "pkg" / "mod.py"
    target.write_text(BROKEN, encoding="utf-8")
    report = run_type_check(project, [target])
    assert report.status == "ok"
    assert report.runner_names() == ("pyright",)
    assert len(report.findings) == 1
    assert report.findings[0].code == "reportAssignmentType"
    assert report.findings[0].line == len(BROKEN.splitlines())


# ---------------------------------------------------------------- triage

def test_triage_charges_only_new_and_is_line_blind():
    before = [_finding(line=5)]
    after = [_finding(line=42), _finding(
        message='"int" has no attribute "poke"',
        code="attr-defined", line=9)]
    triaged, resolved, preexisting = triage_findings(after, before)
    assert preexisting == 1 and resolved == 0
    by_code = {f.code: f.verdict for f in triaged}
    assert by_code == {"assignment": "pre-existing",
                       "attr-defined": "broke-here"}


def test_triage_counts_resolved():
    triaged, resolved, preexisting = triage_findings(
        [], [_finding(), _finding()])
    assert triaged == [] and resolved == 2 and preexisting == 0


def test_check_after_edit_charges_broke_here(
        monkeypatch, tmp_path, project):
    _install(monkeypatch, tmp_path, "mypy", FAKE_MYPY)
    target = project / "pkg" / "mod.py"
    target.write_text(BROKEN, encoding="utf-8")
    report = check_after_edit(target, before_content=CLEAN,
                              root=project)
    assert report.status == "ok"
    assert report.has_new_errors
    assert len(report.new_findings) == 1
    assert report.new_findings[0].verdict == "broke-here"
    assert report.preexisting_count == 0
    note = type_note_for_edit(target, CLEAN, root=project)
    assert "Type depth" in note and "broke" not in note.split(":")[0]
    assert "fix them before the turn ends" in note


def test_check_after_edit_preexisting_is_never_charged(
        monkeypatch, tmp_path, project):
    _install(monkeypatch, tmp_path, "mypy", FAKE_MYPY)
    target = project / "pkg" / "mod.py"
    target.write_text("\n\n" + BROKEN, encoding="utf-8")
    report = check_after_edit(
        target, before_content=BROKEN, root=project)
    assert report.preexisting_count == 1
    assert report.new_findings == []
    assert type_note_for_edit(target, BROKEN, root=project) == ""


def test_check_after_edit_counts_resolved(
        monkeypatch, tmp_path, project):
    _install(monkeypatch, tmp_path, "mypy", FAKE_MYPY)
    target = project / "pkg" / "mod.py"
    target.write_text(CLEAN, encoding="utf-8")
    report = check_after_edit(target, before_content=BROKEN,
                              root=project)
    assert report.resolved_count == 1
    assert report.new_findings == []


def test_new_file_charges_everything(monkeypatch, tmp_path, project):
    _install(monkeypatch, tmp_path, "mypy", FAKE_MYPY)
    target = project / "pkg" / "mod.py"
    target.write_text(ATTR_BROKEN, encoding="utf-8")
    report = check_after_edit(target, before_content=None,
                              root=project)
    assert len(report.new_findings) == 1
    assert report.new_findings[0].category == "attribute"


def test_no_runner_charges_nothing(monkeypatch, project):
    _no_runners(monkeypatch)
    target = project / "pkg" / "mod.py"
    target.write_text(BROKEN, encoding="utf-8")
    report = check_after_edit(target, before_content=CLEAN,
                              root=project)
    assert report.status == "not-installed"
    assert report.new_findings == []
    assert type_note_for_edit(target, CLEAN, root=project) == ""


# ---------------------------------------------------------------- standing

def test_type_depth_standing_file_and_workspace(
        monkeypatch, tmp_path, project):
    _install(monkeypatch, tmp_path, "mypy", FAKE_MYPY)
    target = project / "pkg" / "mod.py"
    target.write_text(BROKEN, encoding="utf-8")
    one = type_depth(project, target)
    assert one.status == "ok" and len(one.findings) == 1
    whole = type_depth(project)
    assert whole.status == "ok" and len(whole.findings) == 1
    assert whole.coverage is None  # no coverage-neighbour package here


def test_type_depth_coverage_account_from_the_neighbour(
        monkeypatch, tmp_path):
    _no_runners(monkeypatch)
    pkg = tmp_path / "mythic_agent"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "mod.py").write_text(CLEAN, encoding="utf-8")
    report = type_depth(tmp_path)
    assert report.status == "not-installed"
    assert report.coverage is not None
    assert report.coverage["functions"] == 1
    assert report.coverage["params_pct"] == 100.0


def test_type_depth_disabled_missing_and_no_package(
        monkeypatch, tmp_path):
    _no_runners(monkeypatch)
    off = type_depth(tmp_path, enabled=False)
    assert off.status == "disabled" and off.findings == []
    missing = type_depth(tmp_path / "nope")
    assert missing.status == "error" and "no workspace" in missing.note
    (tmp_path / "loose.py").write_text("x = 1\n", encoding="utf-8")
    bare = type_depth(tmp_path)
    assert bare.status == "error"
    assert "not a clean bill" in bare.note


def test_type_depth_never_writes(monkeypatch, tmp_path, project):
    _install(monkeypatch, tmp_path, "mypy", FAKE_MYPY)
    (project / "pkg" / "mod.py").write_text(BROKEN, encoding="utf-8")
    before = {p.relative_to(project).as_posix(): p.read_bytes()
              for p in project.rglob("*") if p.is_file()}
    type_depth(project)
    after = {p.relative_to(project).as_posix(): p.read_bytes()
             for p in project.rglob("*") if p.is_file()}
    assert before == after
    for forbidden in ("fix_types", "apply_type_fix", "edit_file"):
        assert not hasattr(td, forbidden)


# ---------------------------------------------------------------- surfaces

def test_parse_types_args_roads_and_usage_errors():
    assert parse_types_args("") == {"action": "show", "path": None}
    assert parse_types_args("show") == {"action": "show", "path": None}
    assert parse_types_args("mod.py") == \
        {"action": "show", "path": "mod.py"}
    assert parse_types_args("show mod.py") == \
        {"action": "show", "path": "mod.py"}
    for bad in ("a.py b.py", "show a.py b.py"):
        with pytest.raises(ValueError) as excinfo:
            parse_types_args(bad)
        assert "Usage" in str(excinfo.value)


def test_format_and_render(monkeypatch, tmp_path, project):
    _install(monkeypatch, tmp_path, "mypy", FAKE_MYPY)
    target = project / "pkg" / "mod.py"
    target.write_text(BROKEN, encoding="utf-8")
    report = type_depth(project, target)
    text = format_type_report(
        {"report": report.record(),
         "plain_explanation": PLAIN_EXPLANATION})
    assert "Type depth (M-063)" in text
    assert "mypy: ran" in text
    assert "Incompatible types" in text
    md = render_markdown(report)
    assert "Type Depth" in md and "1 broke-here" not in md
    assert "Incompatible types" in md


def _bare_agent(root: Path, config=None):
    from mythic_agent.agents.llm import Agent

    agent = Agent.__new__(Agent)
    agent.project_root = root
    agent.config = config or {}
    agent._session_store = None
    agent.session_id = None
    return agent


def test_agent_surfaces(monkeypatch, tmp_path, project):
    _install(monkeypatch, tmp_path, "mypy", FAKE_MYPY)
    (project / "pkg" / "mod.py").write_text(BROKEN, encoding="utf-8")
    agent = _bare_agent(project)
    status = agent.type_depth("pkg/mod.py")
    assert status["report"]["status"] == "ok"
    assert len(status["report"]["findings"]) == 1
    whole = agent.type_depth()
    assert len(whole["report"]["findings"]) == 1


def test_agent_respects_the_config_switch(project):
    agent = _bare_agent(project, {"type_depth": False})
    status = agent.type_depth("pkg/mod.py")
    assert status["report"]["status"] == "disabled"
    assert status["report"]["findings"] == []


def test_terminal_road(project):
    from mythic_agent.terminal import _slash

    agent = _bare_agent(project)
    handled, _, text = _slash(agent, "/types")
    assert handled and "Type depth (M-063)" in text
    handled, _, text = _slash(agent, "/types pkg/mod.py")
    assert handled and "Type depth (M-063)" in text
    handled, _, text = _slash(agent, "/types a.py b.py")
    assert handled and "Usage" in text


def test_execute_tool_write_charges_type_breakage(
        monkeypatch, tmp_path):
    _install(monkeypatch, tmp_path, "mypy", FAKE_MYPY)
    from mythic_agent.agents.tools import execute_tool
    from mythic_agent.core.policy import ToolPolicy

    agent = SimpleNamespace(config={}, project_root=tmp_path)
    result = execute_tool(
        "write_file", {"path": "mod.py", "content": BROKEN},
        tmp_path, agent=agent, policy=ToolPolicy("trusted"))
    assert result.startswith("Successfully wrote")
    assert "Type depth: this edit introduced" in result


def test_execute_tool_clean_write_has_no_type_note(
        monkeypatch, tmp_path):
    _install(monkeypatch, tmp_path, "mypy", FAKE_MYPY)
    from mythic_agent.agents.tools import execute_tool
    from mythic_agent.core.policy import ToolPolicy

    agent = SimpleNamespace(config={}, project_root=tmp_path)
    result = execute_tool(
        "write_file", {"path": "mod.py", "content": CLEAN},
        tmp_path, agent=agent, policy=ToolPolicy("trusted"))
    assert result.startswith("Successfully wrote")
    assert "Type depth" not in result
    off = execute_tool(
        "write_file", {"path": "mod2.py", "content": BROKEN},
        tmp_path,
        agent=SimpleNamespace(
            config={"type_depth": False}, project_root=tmp_path),
        policy=ToolPolicy("trusted"))
    assert "Type depth" not in off


def test_config_catalogue_carries_the_setting():
    from mythic_agent.core.config_catalog import load_catalog

    catalog = load_catalog()
    names = {s.name for s in catalog.settings}
    assert "type_depth" in names
    entry = [s for s in catalog.settings
             if s.name == "type_depth"][0]
    assert entry.id == "S-53"
