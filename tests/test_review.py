"""Tests for mythic_agent.tools.review (Slice 44)."""

from pathlib import Path

import pytest

from mythic_agent.tools.review import (
    Issue,
    format_issues,
    review_file,
    review_project,
    summary_counts,
)


@pytest.fixture()
def bad_file(tmp_path: Path) -> Path:
    lines = ['"""Module docstring."""', "import os", "import sys", ""]
    lines.append("def undocumented(a, b):")
    lines.append("    return a + b  # TODO: handle edge cases")
    lines.append("")
    lines.append("def risky():")
    lines.append("    try:")
    lines.append("        return 1")
    lines.append("    except:")
    lines.append("        return 0")
    lines.append("")
    lines.append("def long_function():")
    lines += ["    x = 1"] * 55
    lines.append("    return x")
    path = tmp_path / "bad.py"
    path.write_text("\n".join(lines) + "\n")
    return path


def _by_check(issues, check):
    return [i for i in issues if i.check == check]


def test_missing_docstring(bad_file: Path):
    issues = review_file(bad_file)
    found = _by_check(issues, "missing-docstring")
    names = {i.message for i in found}
    assert any("undocumented" in m for m in names)
    assert any("risky" in m for m in names)
    # Module docstring present -> no module-level finding.
    assert not any("Module is missing" in m for m in names)


def test_long_function(bad_file: Path):
    found = _by_check(review_file(bad_file), "long-function")
    assert len(found) == 1
    assert found[0].severity == "warning"
    assert "55" in found[0].message or "long" in found[0].message


def test_bare_except_is_error(bad_file: Path):
    found = _by_check(review_file(bad_file), "bare-except")
    assert len(found) == 1
    assert found[0].severity == "error"


def test_todo_comment(bad_file: Path):
    found = _by_check(review_file(bad_file), "todo-comment")
    assert len(found) == 1
    assert found[0].severity == "info"
    assert "TODO" in found[0].message


def test_unused_import(bad_file: Path):
    found = _by_check(review_file(bad_file), "unused-import")
    names = {i.message for i in found}
    assert any("'os'" in m for m in names)
    assert any("'sys'" in m for m in names)


def test_clean_file_has_no_issues(tmp_path: Path):
    path = tmp_path / "clean.py"
    path.write_text(
        '"""Clean module."""\n'
        "import os\n\n"
        "def used(path):\n"
        '    """Use the import."""\n'
        "    return os.path.basename(path)\n"
    )
    assert review_file(path) == []


def test_non_python_file_ignored(tmp_path: Path):
    path = tmp_path / "notes.txt"
    path.write_text("TODO: not python\n")
    assert review_file(path) == []


def test_syntax_error_is_error_issue(tmp_path: Path):
    path = tmp_path / "broken.py"
    path.write_text("def broken(:\n")
    issues = review_file(path)
    assert len(issues) == 1
    assert issues[0].severity == "error"
    assert issues[0].check == "syntax-error"


def test_issue_dataclass_validation():
    with pytest.raises(ValueError):
        Issue(severity="critical", line=1, message="x", check="y")
    issue = Issue(severity="warning", line=3, message="m", check="c", path="f.py")
    assert "[warning] f.py:3 (c): m" == issue.one_line()


def test_issues_sorted_by_line(bad_file: Path):
    issues = review_file(bad_file)
    lines = [i.line for i in issues]
    assert lines == sorted(lines)


def test_format_and_summary(bad_file: Path):
    issues = review_file(bad_file)
    text = format_issues(issues)
    assert "[error]" in text and "[warning]" in text
    counts = summary_counts(issues)
    assert counts["error"] >= 1
    assert sum(counts.values()) == len(issues)
    assert format_issues([]) == "No issues found."


def test_review_project(tmp_path: Path, bad_file: Path):
    good = tmp_path / "good.py"
    good.write_text('"""Fine."""\n')
    results = review_project(tmp_path)
    assert str(bad_file) in results
    assert str(good) not in results  # no issues -> omitted


def test_cli_review_command(tmp_path: Path, bad_file: Path, capsys):
    from mythic_agent import cli
    rc = cli.main(["review", str(bad_file)])
    assert rc == 1  # error-severity issue present
    out = capsys.readouterr().out
    assert "bare-except" in out
    assert "issue(s)" in out


def test_cli_review_missing_path(capsys):
    from mythic_agent import cli
    rc = cli.main(["review", "/does/not/exist.py"])
    assert rc == 2


def test_cli_review_json(tmp_path: Path, bad_file: Path, capsys):
    import json
    from mythic_agent import cli
    rc = cli.main(["review", str(bad_file), "--json", "--severity", "error"])
    assert rc == 1
    data = json.loads(capsys.readouterr().out)
    assert all(d["severity"] == "error" for d in data)
    assert any(d["check"] == "bare-except" for d in data)
