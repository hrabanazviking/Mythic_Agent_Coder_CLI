"""Tests for mythic_agent.tools.smart_files (Slice 18)."""

from pathlib import Path

import pytest

from mythic_agent.tools.smart_files import (
    fuzzy_find,
    fuzzy_score,
    load_gitignore,
    preview_edit,
    respect_gitignore,
)


@pytest.fixture()
def tree(tmp_path: Path) -> Path:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main_agent.py").write_text("x = 1\n")
    (tmp_path / "src" / "agent_tools.py").write_text("y = 2\n")
    (tmp_path / "src" / "readme.md").write_text("docs\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_agents.py").write_text("z = 3\n")
    (tmp_path / "build").mkdir()
    (tmp_path / "build" / "main_agent.pyc").write_text("bin\n")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "main_agent.py").write_text("vcs\n")
    return tmp_path


def test_fuzzy_score_exact_beats_partial():
    assert fuzzy_score("main_agent", "main_agent") == 1.0
    assert fuzzy_score("magnt", "main_agent") > fuzzy_score("magnt", "other_thing")


def test_fuzzy_score_subsequence_required():
    assert fuzzy_score("xyz", "main_agent") == 0.0
    assert fuzzy_score("main", "main_agent") > 0.0
    assert fuzzy_score("", "anything") == 1.0


def test_fuzzy_find_matches_by_name(tree: Path):
    hits = fuzzy_find("magnt", tree)
    names = [p.name for p in hits]
    assert "main_agent.py" in names
    # The exact-ish match should rank first.
    assert names[0] == "main_agent.py"


def test_fuzzy_find_respects_limit(tree: Path):
    hits = fuzzy_find("a", tree, limit=2)
    assert len(hits) <= 2


def test_fuzzy_find_skips_vcs_dirs(tree: Path):
    hits = fuzzy_find("main_agent", tree)
    assert all(".git" not in p.parts for p in hits)


def test_gitignore_filters_results(tree: Path):
    (tree / ".gitignore").write_text("*.pyc\nbuild/\n")
    hits = fuzzy_find("main_agent", tree)
    rels = [p.relative_to(tree).as_posix() for p in hits]
    assert "build/main_agent.pyc" not in rels
    assert "src/main_agent.py" in rels


def test_respect_gitignore_keeps_non_ignored(tmp_path: Path):
    keep = tmp_path / "keep.py"
    drop = tmp_path / "drop.log"
    keep.write_text("1"); drop.write_text("2")
    (tmp_path / ".gitignore").write_text("*.log\n")
    kept = respect_gitignore([keep, drop], tmp_path)
    assert kept == [keep]


def test_load_gitignore_skips_comments_and_blanks(tmp_path: Path):
    (tmp_path / ".gitignore").write_text("# comment\n\n*.log\n")
    assert load_gitignore(tmp_path) == ["*.log"]
    assert load_gitignore(tmp_path / "missing") == []


def test_preview_edit_shows_unified_diff(tmp_path: Path):
    f = tmp_path / "f.py"
    f.write_text("a = 1\nb = 2\n")
    diff = preview_edit(f, "a = 1", "a = 42")
    assert "-a = 1" in diff
    assert "+a = 42" in diff
    assert diff.startswith("--- a/")
    # Preview must not modify the file.
    assert f.read_text() == "a = 1\nb = 2\n"


def test_preview_edit_no_match_reports_no_changes(tmp_path: Path):
    f = tmp_path / "f.py"
    f.write_text("a = 1\n")
    diff = preview_edit(f, "zzz", "q")
    assert "no changes" in diff
