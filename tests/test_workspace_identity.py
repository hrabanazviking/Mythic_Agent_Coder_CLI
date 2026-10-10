"""R-018: workspace identity invariants.

A workspace's identity is SHA-256 over its canonical (realpath) location.
Every spelling of the same directory -- trailing slash, ``.``/``..``
segments, symlinks, relative vs absolute -- must collapse to ONE identity;
distinct directories must never collide; containment breaches raise
``SecurityError`` so a path inside workspace A can never resolve into
workspace B.
"""

import os

import pytest

from mythic_agent.core.exceptions import MythicSecurityError
from mythic_agent.core.workspace import (
    SecurityError,
    assert_within_workspace,
    canonical_workspace_root,
    resolve_file,
    workspace_id,
)


@pytest.fixture
def ws(tmp_path):
    directory = tmp_path / "ws"
    directory.mkdir()
    (directory / "sub").mkdir()
    return directory


def _spellings(ws, tmp_path, monkeypatch):
    """Every spelling of the same directory."""
    link = tmp_path / "ws-link"
    if not link.exists():
        link.symlink_to(ws, target_is_directory=True)
    monkeypatch.chdir(tmp_path)
    return [
        ws,
        str(ws),
        str(ws) + "/",
        str(ws) + "//",
        ws / ".",
        ws / "sub" / "..",
        ws / "sub" / "." / "..",
        link,
        str(link) + "/",
        # relative spelling, resolved against the (patched) cwd
        os.path.relpath(ws, tmp_path),
    ]


def test_spellings_collapse_to_one_identity(ws, tmp_path, monkeypatch):
    identities = {workspace_id(spelling) for spelling in _spellings(ws, tmp_path, monkeypatch)}
    assert len(identities) == 1


def test_symlink_to_dir_shares_target_identity(ws, tmp_path):
    link = tmp_path / "alias"
    link.symlink_to(ws, target_is_directory=True)
    assert workspace_id(link) == workspace_id(ws)
    assert canonical_workspace_root(link) == ws.resolve()


def test_distinct_directories_have_distinct_identities(tmp_path):
    first = tmp_path / "a"
    second = tmp_path / "b"
    first.mkdir()
    second.mkdir()
    assert workspace_id(first) != workspace_id(second)


def test_case_variants_not_folded_together(tmp_path):
    """No naive lowercasing: on a case-sensitive FS, differently-cased names
    are genuinely different directories and must keep distinct identities."""
    lower = tmp_path / "casedir"
    upper = tmp_path / "CASEDIR"
    lower.mkdir()
    try:
        upper.mkdir()
    except FileExistsError:
        pytest.skip("filesystem folds case; OS-level canonicalization applies")
    if lower.resolve() == upper.resolve():
        pytest.skip("filesystem folds case; OS-level canonicalization applies")
    assert workspace_id(lower) != workspace_id(upper)


def test_workspace_id_accepts_str_and_path(ws):
    assert workspace_id(str(ws)) == workspace_id(ws)


def test_nonexistent_path_raises_clear_error(tmp_path):
    missing = tmp_path / "does-not-exist"
    with pytest.raises(ValueError, match="not an existing directory"):
        workspace_id(missing)
    with pytest.raises(ValueError, match="not an existing directory"):
        canonical_workspace_root(str(missing))


def test_file_is_not_a_workspace(tmp_path):
    regular = tmp_path / "file.txt"
    regular.write_text("x")
    with pytest.raises(ValueError, match="not an existing directory"):
        workspace_id(regular)


def test_dotdot_escape_raises_security_error(ws):
    with pytest.raises(SecurityError, match="outside"):
        resolve_file(ws, "../escape.txt")
    # SecurityError stays catchable as ValueError (backwards compatibility).
    with pytest.raises(ValueError, match="outside"):
        resolve_file(ws, "../../etc/passwd")


def test_symlink_escape_raises_security_error(ws, tmp_path):
    outside = tmp_path / "secret.txt"
    outside.write_text("top secret")
    link = ws / "link.txt"
    link.symlink_to(outside)
    with pytest.raises(SecurityError):
        resolve_file(ws, "link.txt")


def test_security_error_taxonomy():
    assert issubclass(SecurityError, ValueError)
    assert issubclass(SecurityError, MythicSecurityError)


def test_cross_workspace_isolation(tmp_path):
    workspace_a = tmp_path / "workspace-a"
    workspace_b = tmp_path / "workspace-b"
    workspace_a.mkdir()
    workspace_b.mkdir()
    (workspace_b / "secret.txt").write_text("b's secret")

    # Distinct workspaces, distinct identities.
    assert workspace_id(workspace_a) != workspace_id(workspace_b)

    # A path inside A stays inside A.
    inside = assert_within_workspace(workspace_a, workspace_a / "notes.txt")
    assert inside == (workspace_a / "notes.txt").resolve()

    # A path inside B never resolves as inside A: escape attempt.
    with pytest.raises(SecurityError, match="escapes workspace"):
        assert_within_workspace(workspace_a, workspace_b / "secret.txt")
    with pytest.raises(SecurityError, match="escapes workspace"):
        assert_within_workspace(workspace_a, "../workspace-b/secret.txt")

    # The workspace root itself counts as contained.
    assert assert_within_workspace(workspace_a, workspace_a) == workspace_a.resolve()


def test_resolve_file_still_resolves_inside_paths(ws):
    assert resolve_file(ws, "sub/../sub") == (ws / "sub").resolve()
    assert resolve_file(ws, "new-file.txt") == (ws / "new-file.txt").resolve()
