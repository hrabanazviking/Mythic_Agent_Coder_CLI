"""
TIER: unit
Tests for git-diff-aware context (Slice 060): staged/unstaged hunks as
context blocks, graceful handling of non-git directories, missing git
binaries and oversized diffs.
"""

import subprocess

import pytest

from mythic_agent.context import (
    ContextCompiler,
    GitDiffSource,
    collect_git_diff,
)


def _git(ws, *args):
    subprocess.run(["git", "-C", str(ws), *args],
                   check=True, capture_output=True)


def _repo(tmp_path):
    ws = tmp_path / "repo"
    ws.mkdir()
    _git(ws, "init")
    _git(ws, "config", "user.email", "test@example.com")
    _git(ws, "config", "user.name", "test")
    (ws / "file.txt").write_text("one\n")
    _git(ws, "add", ".")
    _git(ws, "commit", "-m", "init")
    return ws


# ---------------------------------------------------------------------------
# collection
# ---------------------------------------------------------------------------

def test_non_git_directory_is_graceful(tmp_path):
    diff = collect_git_diff(tmp_path)
    assert diff.is_git_repo is False
    assert diff.staged == "" and diff.unstaged == ""
    assert any("not a git repository" in w for w in diff.warnings)


def test_clean_repo_yields_empty_diffs(tmp_path):
    ws = _repo(tmp_path)
    diff = collect_git_diff(ws)
    assert diff.is_git_repo is True
    assert diff.staged == "" and diff.unstaged == ""
    assert diff.warnings == []


def test_unstaged_hunks_collected(tmp_path):
    ws = _repo(tmp_path)
    (ws / "file.txt").write_text("one\ntwo\n")
    diff = collect_git_diff(ws)
    assert "two" in diff.unstaged
    assert diff.staged == ""


def test_staged_hunks_collected(tmp_path):
    ws = _repo(tmp_path)
    (ws / "file.txt").write_text("one\ntwo\n")
    _git(ws, "add", ".")
    diff = collect_git_diff(ws)
    assert "two" in diff.staged


def test_diff_redacts_secrets(tmp_path):
    ws = _repo(tmp_path)
    (ws / "file.txt").write_text("api_key = 'sk-live-999-secret'\n")
    from mythic_agent.core.redaction import SecretRedactor
    redactor = SecretRedactor({"api_keys": {"x": "sk-live-999-secret"}})
    diff = collect_git_diff(ws, redactor=redactor)
    assert "sk-live-999-secret" not in diff.unstaged
    assert "[REDACTED]" in diff.unstaged


def test_oversized_diff_truncated(tmp_path):
    ws = _repo(tmp_path)
    (ws / "file.txt").write_text("x\n" * 10_000)
    diff = collect_git_diff(ws, max_diff_bytes=100)
    assert "[diff truncated]" in diff.unstaged
    assert any("truncated" in w for w in diff.warnings)


def test_missing_git_binary_is_graceful(tmp_path, monkeypatch):
    import shutil
    monkeypatch.setattr(shutil, "which", lambda name: None)
    diff = collect_git_diff(tmp_path)
    assert diff.is_git_repo is False
    assert any("git binary not found" in w for w in diff.warnings)


# ---------------------------------------------------------------------------
# compiler source integration
# ---------------------------------------------------------------------------

def test_git_diff_source_on_non_git_dir(tmp_path):
    compiler = ContextCompiler(tmp_path)
    compiler.add_source(GitDiffSource())
    compiled = compiler.compile()
    assert compiled.blocks == []


def test_git_diff_source_produces_blocks(tmp_path):
    ws = _repo(tmp_path)
    (ws / "file.txt").write_text("one\ntwo\n")
    _git(ws, "add", ".")
    (ws / "file.txt").write_text("one\ntwo\nthree\n")  # unstaged on top of staged
    compiler = ContextCompiler(ws)
    compiler.add_source(GitDiffSource())
    compiled = compiler.compile()
    names = {b.name for b in compiled.blocks}
    assert names == {"diff:staged", "diff:unstaged"}
    assert all(b.provenance["is_git_repo"] for b in compiled.blocks)
