"""GitHub deep integration via the ``gh`` CLI (Slice 36).

All operations shell out to the user's own ``gh`` binary, so auth
(tokens, SSH) stays exactly where the user configured it and no
credentials ever pass through Mythic. Every function returns plain
parsed data; subprocess failures raise :class:`GitHubCLIError`.

CLI wiring::

    mythic gh pr --title "Add feature" --body "..." --base main --head feature/x
    mythic gh issues [--state open] [--limit 30]
    mythic gh runs [--limit 20]

To wire into ``mythic_agent.cli.main`` (one line, no other changes)::

    from .integrations.github import register_cli
    register_cli(commands)
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from typing import Any, Optional

_GH_TIMEOUT = 60


class GitHubCLIError(RuntimeError):
    """The ``gh`` CLI is missing, unauthenticated, or reported a failure."""


def _run_gh(*args: str, timeout: float = _GH_TIMEOUT) -> str:
    """Run ``gh`` with ``args``; return stdout or raise GitHubCLIError."""
    try:
        completed = subprocess.run(
            ["gh", *args], capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError as exc:
        raise GitHubCLIError(
            "The GitHub CLI (`gh`) is not installed. "
            "Install it from https://cli.github.com and run `gh auth login`.") from exc
    except subprocess.TimeoutExpired as exc:
        raise GitHubCLIError(f"`gh` timed out after {timeout}s") from exc
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise GitHubCLIError(
            f"`gh {' '.join(args)}` failed (exit {completed.returncode})"
            + (f": {detail}" if detail else ""))
    return completed.stdout


def create_pr(title: str, body: str, base: str, head: str,
              draft: bool = False) -> dict[str, Any]:
    """Create a pull request and return its parsed record.

    Returns ``{"number", "url", "title", "state"}``. ``head`` is the
    branch containing the changes; ``base`` is the target branch.
    """
    if not title.strip():
        raise ValueError("PR title must not be empty")
    if not head.strip() or not base.strip():
        raise ValueError("PR head and base branches must not be empty")
    args = ["pr", "create", "--title", title, "--body", body,
            "--base", base, "--head", head,
            "--json", "number,url,title,state"]
    if draft:
        args.append("--draft")
    return json.loads(_run_gh(*args))


def list_issues(state: str = "open", limit: int = 30,
                labels: Optional[list[str]] = None) -> list[dict[str, Any]]:
    """List issues; returns ``[{"number", "title", "state", "labels", "url"}]``."""
    if state not in ("open", "closed", "all"):
        raise ValueError(f"Invalid issue state: {state!r}")
    if limit < 1:
        raise ValueError("limit must be >= 1")
    args = ["issue", "list", "--state", state, "--limit", str(limit),
            "--json", "number,title,state,labels,url"]
    if labels:
        args += ["--label", ",".join(labels)]
    return json.loads(_run_gh(*args))


def get_actions_status(limit: int = 20,
                       branch: Optional[str] = None) -> list[dict[str, Any]]:
    """Return recent workflow runs: ``databaseId, name, status, conclusion, headBranch, url``."""
    if limit < 1:
        raise ValueError("limit must be >= 1")
    args = ["run", "list", "--limit", str(limit),
            "--json", "databaseId,displayTitle,name,status,conclusion,headBranch,url"]
    if branch:
        args += ["--branch", branch]
    return json.loads(_run_gh(*args))


def add_pr_comment(number: int, body: str) -> None:
    """Post a review-style comment on pull request ``number``."""
    if number < 1:
        raise ValueError("PR number must be >= 1")
    if not body.strip():
        raise ValueError("Comment body must not be empty")
    _run_gh("pr", "comment", str(number), "--body", body)


def _add_gh_subcommands(gh_sub: Any) -> None:
    """Attach ``pr`` / ``issues`` / ``runs`` to an argparse subparsers object."""
    pr = gh_sub.add_parser("pr", help="Create a pull request")
    pr.add_argument("--title", required=True, help="PR title")
    pr.add_argument("--body", default="", help="PR body")
    pr.add_argument("--base", required=True, help="Target branch")
    pr.add_argument("--head", required=True, help="Source branch")
    pr.add_argument("--draft", action="store_true", help="Create as draft")
    pr.set_defaults(func=_cli_create_pr)

    issues = gh_sub.add_parser("issues", help="List issues")
    issues.add_argument("--state", default="open", choices=["open", "closed", "all"])
    issues.add_argument("--limit", type=int, default=30)
    issues.add_argument("--label", action="append", dest="labels", default=None)
    issues.set_defaults(func=_cli_list_issues)

    runs = gh_sub.add_parser("runs", help="Show GitHub Actions run status")
    runs.add_argument("--limit", type=int, default=20)
    runs.add_argument("--branch", default=None)
    runs.set_defaults(func=_cli_actions_status)


def register_cli(subparsers: Any) -> None:
    """Add the ``gh`` command group to an argparse subparsers object.

    Wiring point for ``mythic_agent.cli.main`` (one line, no other changes)::

        from .integrations.github import register_cli
        register_cli(commands)
    """
    gh = subparsers.add_parser("gh", help="GitHub workflows via the gh CLI")
    _add_gh_subcommands(gh.add_subparsers(dest="gh_command", required=True))


def _cli_create_pr(args: argparse.Namespace) -> int:
    record = create_pr(args.title, args.body, args.base, args.head, draft=args.draft)
    print(f"Created PR #{record.get('number')}: {record.get('url')}")
    return 0


def _cli_list_issues(args: argparse.Namespace) -> int:
    for issue in list_issues(args.state, args.limit, args.labels):
        labels = ",".join(l.get("name", "") for l in issue.get("labels", []))
        suffix = f" [{labels}]" if labels else ""
        print(f"#{issue.get('number')} [{issue.get('state')}] {issue.get('title')}{suffix}")
    return 0


def _cli_actions_status(args: argparse.Namespace) -> int:
    for run in get_actions_status(args.limit, args.branch):
        conclusion = run.get("conclusion") or run.get("status")
        print(f"{run.get('databaseId')} {run.get('name')} "
              f"({run.get('headBranch')}): {conclusion}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Standalone entry point for the ``gh`` command group.

    ``argv`` holds the arguments *after* ``gh``, e.g.
    ``main(["issues", "--limit", "5"])``. Used by tests and as the wiring
    reference for ``mythic gh ...``.
    """
    parser = argparse.ArgumentParser(prog="mythic gh",
                                     description="GitHub workflows via the gh CLI")
    _add_gh_subcommands(parser.add_subparsers(dest="gh_command", required=True))
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except GitHubCLIError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
