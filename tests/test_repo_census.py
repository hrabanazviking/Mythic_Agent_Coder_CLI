"""Slice R-001 / roadmap 001: repository truth census tests."""

import json

import pytest

from mythic_agent.core import repo_census
from mythic_agent.core.repo_census import (
    Census,
    SnapshotError,
    census,
    snapshot,
    verify_snapshot,
)


def test_census_is_stable_across_runs():
    """Two consecutive runs over the live tree produce identical digests."""
    first = census()
    second = census()
    assert first.digest() == second.digest()
    assert first.to_dict() == second.to_dict()


def test_census_modules_sorted_and_nonempty():
    c = census()
    assert c.modules, "expected at least one module in mythic_agent/"
    names = list(c.modules)
    assert names == sorted(names), "modules must be sorted"
    assert "mythic_agent.core.repo_census" in names
    assert names[0] == "mythic_agent", "package __init__ should sort first"


def test_census_counts_are_sane():
    c = census()
    assert c.files == len(c.modules)
    assert c.files > 0
    assert c.code_lines > c.files, "code lines should exceed file count"
    assert c.classes > 0
    assert c.functions > c.classes
    assert c.test_files > 0
    assert c.tests_collected > 0


def test_to_dict_from_dict_round_trip():
    c = census()
    rebuilt = Census.from_dict(c.to_dict())
    assert rebuilt == c
    assert rebuilt.digest() == c.digest()
    assert isinstance(rebuilt.modules, tuple)


def test_from_dict_rejects_malformed_payloads():
    with pytest.raises(SnapshotError, match="missing required"):
        Census.from_dict({"files": 1})
    with pytest.raises(SnapshotError, match="must be a JSON object"):
        Census.from_dict(["not", "a", "dict"])
    with pytest.raises(SnapshotError, match="invalid field values"):
        Census.from_dict(
            {
                "files": "many",
                "code_lines": 1,
                "classes": 1,
                "functions": 1,
                "test_files": 1,
                "tests_collected": 1,
                "modules": [],
            }
        )


def test_digest_is_stable_sha256_hex():
    c = census()
    d1, d2 = c.digest(), c.digest()
    assert d1 == d2
    assert len(d1) == 64 and all(ch in "0123456789abcdef" for ch in d1)


def _build_scratch_tree(tmp_path):
    pkg = tmp_path / "mythic_agent"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "alpha.py").write_text('"""Alpha module."""\n\n\nclass Widget:\n    def spin(self):\n        return True\n')
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_alpha.py").write_text("def test_spin():\n    assert True\n")
    return pkg


def test_snapshot_write_and_verify_clean(tmp_path, monkeypatch):
    _build_scratch_tree(tmp_path)
    monkeypatch.setattr(repo_census, "REPO_ROOT", tmp_path)
    snap = tmp_path / "census.json"
    out = snapshot(snap)
    assert out == snap
    payload = json.loads(snap.read_text(encoding="utf-8"))
    assert payload["tool"] == repo_census.TOOL_TAG
    assert "generated_at" in payload
    live = census(tmp_path)
    assert payload["digest"] == live.digest()
    assert Census.from_dict(payload["census"]) == live
    assert verify_snapshot(snap) == []


def test_verify_detects_added_module_drift(tmp_path, monkeypatch):
    pkg = _build_scratch_tree(tmp_path)
    monkeypatch.setattr(repo_census, "REPO_ROOT", tmp_path)
    snap = tmp_path / "census.json"
    snapshot(snap)
    (pkg / "sneaky.py").write_text("def sneak():\n    return 1\n")
    drift = verify_snapshot(snap)
    assert any(
        "module added" in m and "mythic_agent.sneaky" in m for m in drift
    ), drift
    assert any("package files" in m and "2 -> 3" in m for m in drift), drift
    assert any("functions" in m and "1 -> 2" in m for m in drift), drift


def test_verify_detects_removed_module_drift(tmp_path, monkeypatch):
    pkg = _build_scratch_tree(tmp_path)
    monkeypatch.setattr(repo_census, "REPO_ROOT", tmp_path)
    snap = tmp_path / "census.json"
    snapshot(snap)
    (pkg / "alpha.py").unlink()
    drift = verify_snapshot(snap)
    assert any(
        "module removed" in m and "mythic_agent.alpha" in m for m in drift
    ), drift


def test_verify_snapshot_missing_file_raises_clear_error(tmp_path):
    with pytest.raises(SnapshotError, match="not found"):
        verify_snapshot(tmp_path / "nope.json")


def test_verify_snapshot_empty_file_raises_clear_error(tmp_path):
    empty = tmp_path / "empty.json"
    empty.write_text("")
    with pytest.raises(SnapshotError, match="empty"):
        verify_snapshot(empty)


def test_verify_snapshot_malformed_json_raises_clear_error(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text('{"census": [not valid json')
    with pytest.raises(SnapshotError, match="not valid JSON"):
        verify_snapshot(bad)


def test_verify_snapshot_missing_census_key_raises_clear_error(tmp_path):
    wrong = tmp_path / "wrong.json"
    wrong.write_text(json.dumps({"tool": "repo_census/R-001"}))
    with pytest.raises(SnapshotError, match="malformed"):
        verify_snapshot(wrong)


def test_verify_snapshot_tampered_digest_raises_clear_error(tmp_path, monkeypatch):
    _build_scratch_tree(tmp_path)
    monkeypatch.setattr(repo_census, "REPO_ROOT", tmp_path)
    snap = tmp_path / "census.json"
    snapshot(snap)
    payload = json.loads(snap.read_text(encoding="utf-8"))
    payload["census"]["files"] = 9999  # tamper with the payload
    snap.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(SnapshotError, match="digest"):
        verify_snapshot(snap)
