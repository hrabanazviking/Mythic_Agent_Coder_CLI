import os
import sqlite3
import stat
import subprocess
from pathlib import Path

import pytest

from mythic_agent.agents.tools import execute_tool, truncate_output
from mythic_agent.core.edits import EditJournal
from mythic_agent.core.workspace import resolve_workspace


@pytest.mark.parametrize("tool,arguments", [
    ("read_file", {"path": "../outside.txt"}),
    ("write_file", {"path": "../outside.txt", "content": "changed"}),
    ("list_dir", {"path": ".."}),
    ("grep_search", {"path": "..", "query": "private"}),
    ("read_file", {"path": "C:\\private\\outside.txt"}),
])
def test_file_tools_refuse_workspace_escapes(agent, tool, arguments):
    outside = agent.project_root.parent / "outside.txt"
    outside.write_text("private")
    result = execute_tool(tool, arguments, agent.project_root)
    assert "outside the workspace" in result or "outside the workspace" in result.lower()
    assert outside.read_text() == "private"


def test_symlink_escape_is_refused_and_search_does_not_follow_it(agent):
    outside = agent.project_root.parent / "outside.txt"
    outside.write_text("private")
    link = agent.project_root / "linked.txt"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("Creating symlinks is not permitted by this platform/account")
    assert "outside the workspace" in execute_tool("read_file", {"path": "linked.txt"}, agent.project_root)
    result = execute_tool("grep_search", {"path": ".", "query": "private"}, agent.project_root)
    assert "private" not in result


@pytest.mark.parametrize("args", [{"path": 1, "content": "x"}, {"path": "x"}, {"path": "x", "content": False}])
def test_file_argument_errors_have_no_side_effects(agent, args):
    assert execute_tool("write_file", args, agent.project_root).startswith("Error:")
    assert not (agent.project_root / "x").exists()


def test_git_metadata_cannot_be_edited(agent):
    result = execute_tool("write_file", {"path": ".git/config", "content": "x"}, agent.project_root)
    assert "Git metadata" in result
    assert not (agent.project_root / ".git/config").exists()


def test_write_replace_undo_preserve_git_history_index_and_unrelated_work(agent):
    root = agent.project_root
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=root).decode().strip()
    git("init")
    git("config", "user.name", "Test")
    git("config", "user.email", "test@example.invalid")
    target = root / "source.txt"
    target.write_text("original\n")
    unrelated = root / "other.txt"
    unrelated.write_text("base\n")
    git("add", "source.txt", "other.txt")
    git("commit", "-m", "baseline")
    head = git("rev-parse", "HEAD")
    unrelated.write_text("staged user work\n")
    git("add", "other.txt")
    index = git("diff", "--cached")
    target.write_text("user work\n")
    assert "Successfully" in execute_tool("write_file", {"path": "source.txt", "content": "agent work\n"}, root)
    assert "Successfully" in execute_tool("replace_file_content", {
        "path": "source.txt", "target_content": "agent", "replacement_content": "updated",
    }, root)
    journal = EditJournal(root)
    assert "Restored" in journal.undo()
    assert target.read_text() == "agent work\n"
    assert "Restored" in journal.undo()
    assert target.read_text() == "user work\n"
    assert unrelated.read_text() == "staged user work\n"
    assert git("rev-parse", "HEAD") == head
    assert git("diff", "--cached") == index


def test_stale_undo_preserves_user_edits_and_new_file_undo_is_scoped(agent):
    root = agent.project_root
    journal = EditJournal(root)
    journal.write("new.txt", "created")
    (root / "new.txt").write_text("edited by user")
    assert "refused" in journal.undo()
    assert (root / "new.txt").read_text() == "edited by user"
    (root / "new.txt").write_text("created")
    (root / "unrelated.txt").write_text("keep")
    assert "Restored" in journal.undo()
    assert not (root / "new.txt").exists()
    assert (root / "unrelated.txt").read_text() == "keep"


@pytest.mark.parametrize("target", ["", "repeated", "missing"])
def test_ambiguous_replace_is_refused(agent, target):
    path = agent.project_root / "source.txt"
    path.write_text("repeated repeated")
    result = execute_tool("replace_file_content", {
        "path": "source.txt", "target_content": target, "replacement_content": "x",
    }, agent.project_root)
    assert "exactly one" in result
    assert path.read_text() == "repeated repeated"


def test_full_file_and_command_outputs_are_preserved(agent):
    large = "example\n" * 5000
    (agent.project_root / "large.txt").write_text(large)
    assert execute_tool("read_file", {"path": "large.txt"}, agent.project_root) == large
    assert truncate_output(large) == large


def test_failed_atomic_replace_preserves_original(agent, monkeypatch):
    from mythic_agent.core import edits
    path = agent.project_root / "source.txt"
    path.write_text("original")
    journal = EditJournal(agent.project_root)
    def fail(*args):
        raise OSError("replace failure")
    monkeypatch.setattr(edits.os, "replace", fail)
    with pytest.raises(OSError, match="replace failure"):
        journal.write("source.txt", "new")
    assert path.read_text() == "original"
    assert not list(agent.project_root.glob(".mythic-edit-*"))
    assert "No agent edit" in journal.undo()


def test_journal_recovers_replace_completed_before_receipt_commit(agent):
    journal = EditJournal(agent.project_root)
    journal.write("source.txt", "new")
    with sqlite3.connect(journal.database) as connection:
        connection.execute("UPDATE edits SET status='prepared'")
    assert "Restored" in EditJournal(agent.project_root).undo()
    assert not (agent.project_root / "source.txt").exists()


def test_pending_receipt_with_divergent_file_does_not_erase_user_work(agent):
    journal = EditJournal(agent.project_root)
    journal.write("source.txt", "agent")
    with sqlite3.connect(journal.database) as connection:
        connection.execute("UPDATE edits SET status='prepared'")
    (agent.project_root / "source.txt").write_text("user")
    assert "refused" in EditJournal(agent.project_root).undo()
    assert (agent.project_root / "source.txt").read_text() == "user"


def test_concurrent_journals_preserve_a_complete_undo_chain(agent):
    from concurrent.futures import ThreadPoolExecutor
    root = agent.project_root
    (root / "source.txt").write_text("original")
    first, second = EditJournal(root), EditJournal(root)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(journal.write, "source.txt", text)
                   for journal, text in [(first, "first"), (second, "second")]]
        for future in futures:
            future.result(timeout=5)
    last = (root / "source.txt").read_text()
    assert "Restored" in first.undo()
    assert (root / "source.txt").read_text() in {"first", "second"} - {last}
    assert "Restored" in second.undo()
    assert (root / "source.txt").read_text() == "original"


@pytest.mark.skipif(os.name == "nt", reason="POSIX executable permission contract")
def test_edit_preserves_modes_and_mode_changes_prevent_undo(agent):
    path = agent.project_root / "script.sh"
    path.write_text("original")
    path.chmod(0o755)
    journal = EditJournal(agent.project_root)
    journal.write("script.sh", "new")
    assert stat.S_IMODE(path.stat().st_mode) == 0o755
    path.chmod(0o700)
    assert "refused" in journal.undo()
    assert stat.S_IMODE(path.stat().st_mode) == 0o700


def test_explicit_workspace_precedes_stored_config(agent, tmp_path):
    other = tmp_path / "other"
    other.mkdir()
    assert resolve_workspace(agent.project_root, {"working_directory": str(other)}) == agent.project_root


def test_slash_undo_never_executes_git_reset(agent, monkeypatch):
    from mythic_agent.agents.command_handler import CommandHandler
    journal = EditJournal(agent.project_root)
    journal.write("source.txt", "created")
    handler = CommandHandler.__new__(CommandHandler)
    handler.project_root = agent.project_root
    def forbidden(*args, **kwargs):
        raise AssertionError("Undo must not invoke Git")
    monkeypatch.setattr(subprocess, "run", forbidden)
    handler._handle_undo("")
    assert not (agent.project_root / "source.txt").exists()
