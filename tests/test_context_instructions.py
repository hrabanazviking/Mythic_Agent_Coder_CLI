"""
TIER: unit
Tests for the repository instruction resolver (Slice 054) and layered
precedence with conflict resolution and provenance (Slice 055).
"""

import os

import pytest

from mythic_agent.context import (
    InstructionResolver,
    apply_precedence,
    parse_directives,
)
from mythic_agent.context.instructions import InstructionFile


def _ws_with(tmp_path, files):
    for rel, content in files.items():
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content)
    return tmp_path


# ---------------------------------------------------------------------------
# Slice 054: discovery
# ---------------------------------------------------------------------------

def test_discovers_repo_and_dir_layers(tmp_path):
    ws = _ws_with(tmp_path, {
        "AGENTS.md": "# repo rules",
        "sub/.muserules": "# dir rules",
        "sub/nested/.mythic": "# nested rules",
        "other.txt": "ignored",
    })
    resolver = InstructionResolver(ws)
    files = resolver.discover()
    by_rel = {f.provenance["relative"]: f.layer for f in files}
    assert by_rel == {
        "AGENTS.md": "repo",
        os.path.join("sub", ".muserules"): "dir",
        os.path.join("sub", "nested", ".mythic"): "dir",
    }
    assert resolver.warnings == []


def test_no_instruction_files_is_empty(tmp_path):
    assert InstructionResolver(tmp_path).discover() == []


def test_oversized_file_skipped_with_warning(tmp_path):
    ws = _ws_with(tmp_path, {"AGENTS.md": "x" * 100})
    resolver = InstructionResolver(ws, max_file_bytes=10)
    assert resolver.discover() == []
    assert any("oversized" in w for w in resolver.warnings)


def test_binary_file_skipped_as_malformed(tmp_path):
    ws = _ws_with(tmp_path, {"AGENTS.md": b"\x00\x01binary\xff"})
    resolver = InstructionResolver(ws)
    assert resolver.discover() == []
    assert any("malformed" in w for w in resolver.warnings)


def test_non_utf8_file_skipped_as_malformed(tmp_path):
    ws = _ws_with(tmp_path, {"AGENTS.md": "héllo".encode("latin-1")})
    resolver = InstructionResolver(ws)
    assert resolver.discover() == []
    assert any("malformed" in w for w in resolver.warnings)


def test_symlink_escape_blocked(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "AGENTS.md").write_text("# outside rules")
    ws = tmp_path / "ws"
    ws.mkdir()
    os.symlink(outside / "AGENTS.md", ws / "AGENTS.md")
    resolver = InstructionResolver(ws)
    assert resolver.discover() == []
    assert any("blocked" in w for w in resolver.warnings)


def test_cross_workspace_isolation(tmp_path):
    ws_a = _ws_with(tmp_path / "a", {"AGENTS.md": "# a rules"})
    _ws_with(tmp_path / "b", {"AGENTS.md": "# b rules"})
    files = InstructionResolver(ws_a).discover()
    assert len(files) == 1
    assert "# a rules" in files[0].content
    assert all("b" not in f.provenance["relative"] for f in files)


def test_total_budget_cap(tmp_path):
    ws = _ws_with(tmp_path, {
        "AGENTS.md": "a" * 40,
        "sub/.muserules": "b" * 40,
    })
    resolver = InstructionResolver(ws, max_total_bytes=50)
    files = resolver.discover()
    assert len(files) == 1
    assert any("budget" in w for w in resolver.warnings)


def test_missing_workspace_raises():
    with pytest.raises(ValueError):
        InstructionResolver("/nonexistent-workspace-xyz")


# ---------------------------------------------------------------------------
# Slice 055: precedence
# ---------------------------------------------------------------------------

def _ifile(path, layer, content):
    return InstructionFile(path=path, layer=layer, content=content,
                           size=len(content))


def test_higher_precedence_key_wins_and_conflict_recorded():
    repo = [_ifile("r", "repo", "Timeout: 30")]
    dirf = [_ifile("d", "dir", "Timeout: 5")]
    result = apply_precedence("Timeout: 60", repo=repo, dir_files=dirf)
    merged = next(b for b in result.blocks if b.name == "instructions:merged")
    assert "Timeout: 60" in merged.content
    assert "Timeout: 5" not in merged.content
    assert "Timeout: 30" not in merged.content
    assert len(result.conflicts) == 2
    assert result.conflicts[0]["winner"]["layer"] == "system"
    assert result.conflicts[0]["overridden"]["layer"] == "repo"


def test_identical_key_redefinition_is_not_a_conflict():
    repo = [_ifile("r", "repo", "Timeout: 30")]
    dirf = [_ifile("d", "dir", "Timeout: 30")]
    result = apply_precedence("", repo=repo, dir_files=dirf)
    assert result.conflicts == []
    merged = next(b for b in result.blocks if b.name == "instructions:merged")
    assert merged.content.count("Timeout: 30") == 1


def test_bullet_directives_dedupe_across_layers():
    repo = [_ifile("r", "repo", "- Never force-push\n- Run tests")]
    dirf = [_ifile("d", "dir", "- Never force-push")]
    result = apply_precedence("", repo=repo, dir_files=dirf)
    merged = next(b for b in result.blocks if b.name == "instructions:merged")
    assert merged.content.count("Never force-push") == 1
    assert "Run tests" in merged.content


def test_file_layer_is_lowest_precedence():
    result = apply_precedence(
        "", file_directives=[("explicit", "Mode: strict")],
        repo=[_ifile("r", "repo", "Mode: relaxed")])
    merged = next(b for b in result.blocks if b.name == "instructions:merged")
    assert "Mode: relaxed" in merged.content
    assert result.conflicts[0]["winner"]["layer"] == "repo"
    assert result.conflicts[0]["overridden"]["layer"] == "file"


def test_provenance_tracks_every_directive():
    repo = [_ifile("r", "repo", "- Keep tests green\nTimeout: 30")]
    result = apply_precedence("Be helpful", repo=repo)
    layers = {p["layer"] for p in result.provenance}
    assert {"repo"} <= layers
    assert all("source" in p and "directive" in p for p in result.provenance)


def test_system_text_gets_own_block():
    result = apply_precedence("Be helpful")
    assert any(b.name == "instructions:system" for b in result.blocks)
    assert not any(b.name == "instructions:merged" for b in result.blocks)


def test_empty_input_yields_no_blocks():
    result = apply_precedence("")
    assert result.blocks == [] and result.conflicts == []


def test_parse_directives_extracts_keys_and_bullets():
    parsed = parse_directives("Timeout: 30\n- do the thing\nplain prose",
                              layer="repo", source="s")
    kinds = {d.kind for d in parsed}
    assert kinds == {"key", "bullet"}
    assert all(d.layer == "repo" and d.source == "s" for d in parsed)
