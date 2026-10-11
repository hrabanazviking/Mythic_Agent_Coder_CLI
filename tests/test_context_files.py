"""
TIER: unit
Tests for explicit file context via @-mentions (Slice 056):
workspace containment, symlink-traversal blocking, and malformed /
missing / oversized-data behavior.
"""

import os

import pytest

from mythic_agent.context import (
    ContextCompiler,
    ExplicitFilesSource,
    TokenEstimator,
    extract_mentions,
    resolve_mentions,
)


def _ws(tmp_path):
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "src").mkdir(parents=True, exist_ok=True)
    (tmp_path / "src" / "main.py").write_text("print('hello')\n")
    (tmp_path / "notes.md").write_text("# notes\n")
    return tmp_path


# ---------------------------------------------------------------------------
# mention extraction
# ---------------------------------------------------------------------------

def test_extract_mentions_dedupes_and_preserves_order():
    assert extract_mentions("fix @src/main.py then check @src/main.py and @notes.md") == [
        "src/main.py", "notes.md"]
    assert extract_mentions("no mentions here") == []
    assert extract_mentions("@a @b@c") == ["a", "b", "c"]


# ---------------------------------------------------------------------------
# resolution + containment
# ---------------------------------------------------------------------------

def test_resolve_simple_mention(tmp_path):
    ws = _ws(tmp_path)
    result = resolve_mentions("look at @src/main.py", ws)
    assert len(result.files) == 1
    assert result.files[0].mention == "src/main.py"
    assert "print('hello')" in result.files[0].content
    assert result.files[0].provenance["relative"] == os.path.join("src", "main.py")
    assert result.warnings == []


def test_missing_file_warns(tmp_path):
    ws = _ws(tmp_path)
    result = resolve_mentions("look at @nope.py", ws)
    assert result.files == []
    assert any("missing" in w for w in result.warnings)


def test_dotdot_escape_blocked(tmp_path):
    ws = _ws(tmp_path)
    result = resolve_mentions("read @../outside.py", ws)
    assert result.files == []
    assert any("blocked" in w for w in result.warnings)


def test_absolute_cross_workspace_path_blocked(tmp_path):
    ws_a = _ws(tmp_path / "a")
    ws_b = _ws(tmp_path / "b")
    result = resolve_mentions(f"read @{ws_b / 'notes.md'}", ws_a)
    assert result.files == []
    assert any("blocked" in w for w in result.warnings)


def test_symlink_traversal_outside_workspace_blocked(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("top secret")
    ws = _ws(tmp_path / "ws")
    os.symlink(outside / "secret.txt", ws / "link.txt")
    result = resolve_mentions("read @link.txt", ws)
    assert result.files == []
    assert any("blocked" in w for w in result.warnings)


def test_symlink_inside_workspace_allowed(tmp_path):
    ws = _ws(tmp_path)
    os.symlink(ws / "notes.md", ws / "alias.md")
    result = resolve_mentions("read @alias.md", ws)
    assert len(result.files) == 1
    assert "# notes" in result.files[0].content


def test_directory_mention_warns(tmp_path):
    ws = _ws(tmp_path)
    result = resolve_mentions("read @src", ws)
    assert result.files == []
    assert any("directory" in w for w in result.warnings)


def test_binary_file_skipped_as_malformed(tmp_path):
    ws = _ws(tmp_path)
    (ws / "blob.bin").write_bytes(b"\x00\x01\x02binary")
    result = resolve_mentions("read @blob.bin", ws)
    assert result.files == []
    assert any("malformed" in w for w in result.warnings)


def test_oversized_file_truncated_with_flag(tmp_path):
    ws = _ws(tmp_path)
    result = resolve_mentions("read @src/main.py", ws, max_file_bytes=5)
    assert len(result.files) == 1
    assert result.files[0].truncated is True
    assert len(result.files[0].content.encode("utf-8")) <= 5


def test_missing_workspace_raises():
    with pytest.raises(ValueError):
        resolve_mentions("@x", "/nonexistent-workspace-xyz")


# ---------------------------------------------------------------------------
# compiler source integration
# ---------------------------------------------------------------------------

def test_explicit_files_source_via_compiler(tmp_path):
    ws = _ws(tmp_path)
    compiler = ContextCompiler(ws)
    compiler.add_source(ExplicitFilesSource())
    compiled = compiler.compile("please review @src/main.py")
    assert len(compiled.blocks) == 1
    assert "print('hello')" in compiled.blocks[0].content
    assert compiled.blocks[0].provenance["mention"] == "src/main.py"


def test_explicit_files_source_empty_query(tmp_path):
    ws = _ws(tmp_path)
    compiler = ContextCompiler(ws)
    compiler.add_source(ExplicitFilesSource())
    assert compiler.compile("no mentions").blocks == []


def test_source_records_token_counts(tmp_path):
    ws = _ws(tmp_path)
    est = TokenEstimator()
    result = resolve_mentions("@src/main.py", ws, estimator=est)
    assert result.files[0].tokens == est.count(result.files[0].content)
