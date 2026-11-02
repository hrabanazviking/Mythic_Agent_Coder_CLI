"""M-053 — Formatter covenant.

TIER: integration

The project's own formatter config is honoured exactly;
the coder never reformats untouched code; format diffs
are separated from logic diffs in review. Absence is
never a style: no configured formatter formats nothing,
a configured-but-missing binary says not-installed, and
live proof rides a fake formatter binary on PATH
speaking the real stdin/stdout contract.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mythic_agent.tools import format_covenant as covenant
from mythic_agent.tools.format_covenant import (
    FormatReport, FormatterSpec, apply_format, discover_formatter,
    enabled_from_config, format_covenant_report, format_format_report,
    formatter_names, parse_format_args, preview_format, run_formatter,
    separate_diffs,
)


MESSY = "x = 1   \n y = 2\t\n"
FORMATTED = "x = 1\n y = 2\n"


def _fake_formatter(tmp_path: Path, name: str = "black") -> Path:
    """A fake formatter binary: strips trailing whitespace via stdin."""
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    script = bindir / name
    script.write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        "data = sys.stdin.read()\n"
        "lines = [line.rstrip() for line in data.splitlines()]\n"
        "sys.stdout.write('\\n'.join(lines) + '\\n')\n",
        encoding="utf-8")
    script.chmod(0o755)
    return bindir


def _project(tmp_path: Path, monkeypatch, config: str = "[tool.black]\n"):
    """A project root naming black, with the fake binary on PATH."""
    root = tmp_path / "proj"
    root.mkdir(exist_ok=True)
    (root / "pyproject.toml").write_text(config, encoding="utf-8")
    bindir = _fake_formatter(tmp_path)
    monkeypatch.setenv(
        "PATH", str(bindir) + os.pathsep + os.environ.get("PATH", ""))
    target = root / "mod.py"
    target.write_text(MESSY, encoding="utf-8")
    return root, target


# ---------------------------------------------------------------- discovery

def test_formatter_names_in_preference_order():
    assert formatter_names() == ("black", "ruff", "isort", "yapf")


def test_discover_none_without_any_config(tmp_path):
    assert discover_formatter(tmp_path) is None


def test_discover_none_when_binary_exists_but_project_names_nothing(
        tmp_path, monkeypatch):
    _fake_formatter(tmp_path)
    monkeypatch.setenv(
        "PATH", str(tmp_path / "bin") + os.pathsep + os.environ.get("PATH", ""))
    assert discover_formatter(tmp_path) is None


def test_discover_configured_but_not_installed(tmp_path, monkeypatch):
    (tmp_path / "pyproject.toml").write_text("[tool.black]\n", encoding="utf-8")
    monkeypatch.setattr(covenant.shutil, "which", lambda name: None)
    spec = discover_formatter(tmp_path)
    assert spec is not None and spec.name == "black"
    assert spec.installed is False and spec.config_source == "pyproject.toml"


def test_discover_does_not_fall_through_to_unchosen_formatter(
        tmp_path, monkeypatch):
    # The project names yapf only; black's binary exists but
    # the project never chose it — yapf's honest absence wins.
    root, _target = _project(tmp_path, monkeypatch, config="[tool.yapf]\n")
    spec = discover_formatter(root)
    assert spec is not None and spec.name == "yapf" and spec.installed is False


def test_discover_ruff_via_own_config_file(tmp_path, monkeypatch):
    root = tmp_path / "proj"
    root.mkdir()
    (root / "ruff.toml").write_text("", encoding="utf-8")
    monkeypatch.setattr(
        covenant.shutil, "which",
        lambda name: "/usr/bin/ruff" if name == "ruff" else None)
    spec = discover_formatter(root)
    assert spec is not None and spec.name == "ruff"
    assert spec.argv() == ["/usr/bin/ruff", "format", "-"]
    assert spec.config_source == "ruff.toml"


def test_discover_finds_configured_black_with_fake_binary(tmp_path, monkeypatch):
    root, _target = _project(tmp_path, monkeypatch)
    spec = discover_formatter(root)
    assert spec is not None and spec.name == "black" and spec.installed
    assert spec.argv()[1:] == ["-"]


# ---------------------------------------------------------------- diffs

def test_separate_diffs_split_logic_from_format():
    diffs = separate_diffs("a = 1\n", "a = 2   \n", "a = 2\n")
    assert diffs["logic_changed_lines"] == 2  # -a = 1 / +a = 2
    assert diffs["format_changed_lines"] == 2  # -a = 2   / +a = 2
    assert "a = 1" in diffs["logic_diff"]
    assert "a = 1" not in diffs["format_diff"]


def test_separate_diffs_empty_when_nothing_changes():
    diffs = separate_diffs("a = 1\n", "a = 1\n", "a = 1\n")
    assert diffs == {"logic_diff": "", "logic_changed_lines": 0,
                     "format_diff": "", "format_changed_lines": 0}


# ---------------------------------------------------------------- preview

def test_preview_refuses_untouched_file(tmp_path, monkeypatch):
    root, target = _project(tmp_path, monkeypatch)
    other = root / "other.py"
    other.write_text(MESSY, encoding="utf-8")
    report = preview_format(target, root=root, touched=[other])
    assert report.status == "not-touched"
    assert target.read_text(encoding="utf-8") == MESSY


def test_preview_not_configured_formats_nothing(tmp_path):
    target = tmp_path / "mod.py"
    target.write_text(MESSY, encoding="utf-8")
    report = preview_format(target, root=tmp_path, touched=[target])
    assert report.status == "not-configured" and report.would_change is False
    assert target.read_text(encoding="utf-8") == MESSY


def test_preview_not_installed_is_honest(tmp_path, monkeypatch):
    (tmp_path / "pyproject.toml").write_text("[tool.black]\n", encoding="utf-8")
    monkeypatch.setattr(covenant.shutil, "which", lambda name: None)
    target = tmp_path / "mod.py"
    target.write_text(MESSY, encoding="utf-8")
    report = preview_format(target, root=tmp_path, touched=[target])
    assert report.status == "not-installed"
    assert report.formatter is not None and report.formatter.name == "black"


def test_preview_disabled_when_covenant_off(tmp_path, monkeypatch):
    root, target = _project(tmp_path, monkeypatch)
    report = preview_format(target, root=root, touched=[target], enabled=False)
    assert report.status == "disabled"


def test_preview_ok_separates_diffs_and_writes_nothing(tmp_path, monkeypatch):
    root, target = _project(tmp_path, monkeypatch)
    before = "x = 1   \n"
    report = preview_format(target, root=root, touched=[target],
                            before_content=before)
    assert report.status == "ok" and report.would_change is True
    assert report.formatted_content == FORMATTED
    assert report.logic_changed_lines > 0 and report.format_changed_lines > 0
    assert " y = 2" in report.logic_diff
    assert target.read_text(encoding="utf-8") == MESSY  # preview wrote nothing


def test_preview_clean_file_would_change_nothing(tmp_path, monkeypatch):
    root, target = _project(tmp_path, monkeypatch)
    target.write_text(FORMATTED, encoding="utf-8")
    report = preview_format(target, root=root, touched=[target])
    assert report.status == "ok" and report.would_change is False
    assert report.format_changed_lines == 0


def test_preview_missing_file_is_an_error_report(tmp_path, monkeypatch):
    root, target = _project(tmp_path, monkeypatch)
    ghost = root / "ghost.py"
    report = preview_format(ghost, root=root, touched=[ghost])
    assert report.status == "error"


def test_run_formatter_failure_raises_with_its_words(tmp_path):
    bindir = tmp_path / "bin"
    bindir.mkdir()
    script = bindir / "black"
    script.write_text("#!/bin/sh\necho cannot parse >&2\nexit 3\n",
                      encoding="utf-8")
    script.chmod(0o755)
    spec = FormatterSpec(name="black", binary=str(script),
                         argv_tail=("-",), config_source="pyproject.toml")
    with pytest.raises(RuntimeError, match="cannot parse"):
        run_formatter(spec, "anything\n")


# ---------------------------------------------------------------- apply

def test_apply_writes_formatted_through_the_journal(tmp_path, monkeypatch):
    root, target = _project(tmp_path, monkeypatch)
    report = format_covenant_report(target, root=root, touched=[target],
                                    apply=True)
    assert report.status == "applied" and report.applied is True
    assert target.read_text(encoding="utf-8") == FORMATTED


def test_apply_refused_when_file_changed_since_preview(tmp_path, monkeypatch):
    root, target = _project(tmp_path, monkeypatch)
    report = preview_format(target, root=root, touched=[target])
    assert report.status == "ok"
    target.write_text("changed = True   \n", encoding="utf-8")
    refused = apply_format(report, root=root)
    assert refused.status == "refused-stale" and refused.applied is False
    assert target.read_text(encoding="utf-8") == "changed = True   \n"


def test_apply_of_clean_preview_is_a_noop_note(tmp_path, monkeypatch):
    root, target = _project(tmp_path, monkeypatch)
    target.write_text(FORMATTED, encoding="utf-8")
    report = preview_format(target, root=root, touched=[target])
    applied = apply_format(report, root=root)
    assert applied.applied is False and "nothing to apply" in applied.note


def test_apply_never_runs_for_untouched_preview(tmp_path, monkeypatch):
    root, target = _project(tmp_path, monkeypatch)
    report = preview_format(target, root=root, touched=[])
    assert report.status == "not-touched"
    applied = apply_format(report, root=root)
    assert applied.applied is False
    assert target.read_text(encoding="utf-8") == MESSY


# ---------------------------------------------------------------- surfaces

def test_enabled_from_config_defaults_on():
    assert enabled_from_config(None) is True
    assert enabled_from_config({}) is True
    assert enabled_from_config({"formatter_covenant": False}) is False


def test_parse_format_args():
    assert parse_format_args("mod.py") == {"action": "preview", "path": "mod.py"}
    assert parse_format_args("mod.py apply") == {"action": "apply",
                                                 "path": "mod.py"}
    for bad in ("", "a b c", "mod.py sideways"):
        with pytest.raises(ValueError):
            parse_format_args(bad)


def test_format_report_record_round_trips():
    report = FormatReport(path="x.py", status="ok", would_change=True)
    record = report.record()
    assert record["path"] == "x.py" and record["formatter"] is None
    text = format_format_report(
        {"report": record, "plain_explanation": covenant.PLAIN_EXPLANATION})
    assert "Formatter covenant for x.py" in text


def test_agent_format_covenant(tmp_path):
    from mythic_agent.agents.llm import Agent
    agent = Agent.__new__(Agent)
    agent.project_root = tmp_path
    agent.config = {}
    (tmp_path / "mod.py").write_text(MESSY, encoding="utf-8")
    status = agent.format_covenant("mod.py")
    assert status["report"]["status"] == "not-configured"
    with pytest.raises(ValueError):
        agent.format_covenant("../outside.py")


def test_agent_format_covenant_respects_the_switch(tmp_path):
    from mythic_agent.agents.llm import Agent
    agent = Agent.__new__(Agent)
    agent.project_root = tmp_path
    agent.config = {"formatter_covenant": False}
    (tmp_path / "mod.py").write_text(MESSY, encoding="utf-8")
    status = agent.format_covenant("mod.py")
    assert status["report"]["status"] == "disabled"


def test_terminal_format_command(tmp_path):
    from mythic_agent.agents.llm import Agent
    from mythic_agent.terminal import _slash
    agent = Agent.__new__(Agent)
    agent.project_root = tmp_path
    agent.config = {}
    (tmp_path / "mod.py").write_text(MESSY, encoding="utf-8")
    handled, _, text = _slash(agent, "/format mod.py")
    assert handled and "not-configured" in text
    handled, _, text = _slash(agent, "/format")
    assert handled and "Usage" in text


def test_render_markdown_names_the_slice():
    text = covenant.render_markdown()
    assert "M-053" in text and "/format <path>" in text
    assert "black" in text and "yapf" in text
