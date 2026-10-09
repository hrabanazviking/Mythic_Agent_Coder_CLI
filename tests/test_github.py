"""Slice 36 GitHub integration tests.

The ``gh`` CLI is never executed: ``_run_gh`` (and ``subprocess.run``
for the missing-binary case) is stubbed in every test.
"""

import json
import subprocess

import pytest

from mythic_agent.integrations import github
from mythic_agent.integrations.github import GitHubCLIError


def _stub_run_gh(monkeypatch, stdout, calls=None):
    def fake(*args, **kwargs):
        if calls is not None:
            calls.append(args)
        return stdout
    monkeypatch.setattr(github, "_run_gh", fake)


def test_create_pr_returns_parsed_record(monkeypatch, capsys):
    calls = []
    record = {"number": 42, "url": "https://github.com/o/r/pull/42",
              "title": "Add feature", "state": "open"}
    _stub_run_gh(monkeypatch, json.dumps(record), calls)
    result = github.create_pr("Add feature", "body text", "main", "feature/x")
    assert result == record
    args = calls[0]
    assert args[:2] == ("pr", "create")
    assert "--title" in args and "Add feature" in args
    assert "--base" in args and "main" in args
    assert "--head" in args and "feature/x" in args


def test_create_pr_validates_inputs(monkeypatch):
    _stub_run_gh(monkeypatch, "{}")
    with pytest.raises(ValueError):
        github.create_pr("   ", "body", "main", "head")
    with pytest.raises(ValueError):
        github.create_pr("title", "body", "", "head")


def test_list_issues_parses_json_and_forwards_flags(monkeypatch):
    calls = []
    issues = [{"number": 7, "title": "Bug", "state": "open",
               "labels": [{"name": "bug"}], "url": "u"}]
    _stub_run_gh(monkeypatch, json.dumps(issues), calls)
    result = github.list_issues(state="open", limit=5, labels=["bug"])
    assert result == issues
    args = calls[0]
    assert args[:2] == ("issue", "list")
    assert "--limit" in args and "5" in args
    assert "--label" in args and "bug" in args


def test_list_issues_rejects_bad_state_and_limit(monkeypatch):
    _stub_run_gh(monkeypatch, "[]")
    with pytest.raises(ValueError):
        github.list_issues(state="bogus")
    with pytest.raises(ValueError):
        github.list_issues(limit=0)


def test_get_actions_status_parses_runs(monkeypatch):
    calls = []
    runs = [{"databaseId": "123", "name": "CI", "status": "completed",
             "conclusion": "success", "headBranch": "main", "url": "u"}]
    _stub_run_gh(monkeypatch, json.dumps(runs), calls)
    result = github.get_actions_status(limit=3, branch="main")
    assert result == runs
    args = calls[0]
    assert args[:2] == ("run", "list")
    assert "--branch" in args and "main" in args


def test_add_pr_comment_posts_body(monkeypatch):
    calls = []
    _stub_run_gh(monkeypatch, "", calls)
    github.add_pr_comment(12, "Looks good")
    assert calls[0][:3] == ("pr", "comment", "12")
    assert "Looks good" in calls[0]


def test_run_gh_wraps_missing_binary(monkeypatch):
    def fake_run(*args, **kwargs):
        raise FileNotFoundError("gh")
    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(GitHubCLIError) as exc:
        github._run_gh("pr", "list")
    assert "not installed" in str(exc.value)


def test_run_gh_wraps_nonzero_exit(monkeypatch):
    class FakeCompleted:
        returncode = 1
        stdout = ""
        stderr = "auth failed: not logged in"

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: FakeCompleted())
    with pytest.raises(GitHubCLIError) as exc:
        github._run_gh("pr", "list")
    assert "exit 1" in str(exc.value)
    assert "not logged in" in str(exc.value)


def test_cli_issues_end_to_end(monkeypatch, capsys):
    _stub_run_gh(monkeypatch, json.dumps([
        {"number": 3, "title": "Fix crash", "state": "open",
         "labels": [{"name": "bug"}], "url": "u"}]))
    assert github.main(["issues", "--limit", "1"]) == 0
    out = capsys.readouterr().out
    assert "#3 [open] Fix crash [bug]" in out


def test_cli_pr_end_to_end(monkeypatch, capsys):
    _stub_run_gh(monkeypatch, json.dumps(
        {"number": 9, "url": "https://x/pr/9", "title": "T", "state": "open"}))
    assert github.main(["pr", "--title", "T", "--base", "main",
                        "--head", "feat"]) == 0
    assert "Created PR #9" in capsys.readouterr().out


def test_cli_error_returns_nonzero(monkeypatch, capsys):
    def boom(*args, **kwargs):
        raise GitHubCLIError("gh exploded")
    monkeypatch.setattr(github, "_run_gh", boom)
    assert github.main(["issues"]) == 1
    assert "gh exploded" in capsys.readouterr().err


def test_register_cli_adds_gh_group():
    import argparse
    parser = argparse.ArgumentParser(prog="mythic")
    github.register_cli(parser.add_subparsers(dest="command"))
    args = parser.parse_args(
        ["gh", "pr", "--title", "T", "--base", "main", "--head", "f"])
    assert args.command == "gh"
    assert args.gh_command == "pr"
    assert args.title == "T"
