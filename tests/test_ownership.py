"""Roadmap 005 / R-005 — Source Ownership Map gates.

The ownership map is a GENERATED artifact: docs/OWNERSHIP.md must be produced
by scripts/gen_ownership.py (never hand-written). These tests gate it:
  1. every mythic_agent/**/*.py module (excluding __pycache__) appears in the doc
  2. the doc is fresh: regenerating it yields identical content modulo the timestamp
  3. a module with zero git history fails loudly with its name (no silent skips)
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC = REPO_ROOT / "docs" / "OWNERSHIP.md"
GEN_SCRIPT = REPO_ROOT / "scripts" / "gen_ownership.py"
PACKAGE_DIR = REPO_ROOT / "mythic_agent"

TIMESTAMP_LINE_PREFIX = "> Generated at: "
REGEN_NOTE = "do not edit by hand"
REGEN_CMD = "python scripts/gen_ownership.py"


def _load_gen_module():
    spec = importlib.util.spec_from_file_location("gen_ownership", GEN_SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _discover_modules() -> list[str]:
    return sorted(
        str(p.relative_to(REPO_ROOT)).replace("\\", "/")
        for p in PACKAGE_DIR.rglob("*.py")
        if "__pycache__" not in p.parts
    )


def _read_machine_index() -> dict:
    """Parse the machine-readable ```json section of docs/OWNERSHIP.md."""
    text = DOC.read_text(encoding="utf-8")
    anchor = "## Machine-readable module index"
    assert anchor in text, "doc is missing the machine-readable section"
    fenced = text.split(anchor, 1)[1]
    start = fenced.index("```json")
    end = fenced.index("```", start + len("```json"))
    return json.loads(fenced[start + len("```json"): end])


def _normalize(doc_text: str) -> list[str]:
    """Doc lines with the generation timestamp line stripped."""
    return [
        line
        for line in doc_text.splitlines()
        if not line.startswith(TIMESTAMP_LINE_PREFIX)
    ]


def test_doc_exists_and_carries_regeneration_note():
    assert GEN_SCRIPT.is_file(), "generator script missing"
    assert DOC.is_file(), "docs/OWNERSHIP.md missing — run the generator"
    text = DOC.read_text(encoding="utf-8")
    assert REGEN_NOTE in text, "doc lacks the do-not-hand-edit regeneration note"
    assert REGEN_CMD in text, "doc lacks the regeneration command"
    assert TIMESTAMP_LINE_PREFIX.rstrip(": ") in text, "doc lacks a generation timestamp"


def test_every_module_appears_in_doc():
    index = _read_machine_index()
    doc_modules = [m["module"] for m in index["modules"]]
    assert len(doc_modules) == len(set(doc_modules)), "duplicate modules in doc index"
    assert set(doc_modules) == set(_discover_modules()), (
        "doc index does not cover the current module tree"
    )
    assert index["total_modules"] == len(doc_modules)


def test_rollup_is_consistent_with_module_index():
    index = _read_machine_index()
    owners = [m["owner"] for m in index["modules"]]
    rollup = {r["author"]: r for r in index["rollup"]}
    assert sum(r["modules_owned"] for r in rollup.values()) == len(owners)
    for author, row in rollup.items():
        assert row["modules_owned"] == owners.count(author), (
            f"rollup count mismatch for {author}"
        )
    # shares must be real fractions of real commit counts
    for m in index["modules"]:
        assert 0.0 < m["share"] <= 1.0
        assert m["owner_commits"] <= m["total_commits"]
        assert m["owner_commits"] / m["total_commits"] == pytest.approx(
            m["share"], abs=1e-3
        )


def test_ownership_names_come_from_real_git_log():
    proc = subprocess.run(
        ["git", "log", "--format=%an", "--", "mythic_agent/"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    real_authors = {line for line in proc.stdout.splitlines() if line}
    assert real_authors, "no authors found in git history"
    index = _read_machine_index()
    for m in index["modules"]:
        assert m["owner"] in real_authors, (
            f"invented authorship: {m['owner']} not in git log for {m['module']}"
        )
    for r in index["rollup"]:
        assert r["author"] in real_authors


def test_doc_is_fresh(tmp_path: Path):
    """Regenerating the doc yields identical content modulo the timestamp line."""
    import sys

    regen = tmp_path / "OWNERSHIP.regen.md"
    run = subprocess.run(
        [sys.executable, str(GEN_SCRIPT), "--out", str(regen)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert run.returncode == 0, f"generator failed: {run.stderr}"
    current = DOC.read_text(encoding="utf-8")
    fresh = regen.read_text(encoding="utf-8")
    assert _normalize(current) == _normalize(fresh), (
        "docs/OWNERSHIP.md is stale — regenerate with `python scripts/gen_ownership.py`"
    )

def test_zero_git_history_fails_loudly():
    """A module with zero git history must raise with its name — no silent skip."""
    gen = _load_gen_module()
    probe = PACKAGE_DIR / "__zz_probe_zero_history__.py"
    rel = str(probe.relative_to(REPO_ROOT)).replace("\\", "/")
    probe.write_text("# zero-history probe\n", encoding="utf-8")
    try:
        # confirm the probe really has no git history (untracked, uncommitted)
        log = subprocess.run(
            ["git", "log", "--format=%an", "--", rel],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert not log.stdout.strip(), "probe unexpectedly has git history"
        with pytest.raises(gen.ZeroHistoryError) as excinfo:
            gen.ownership_for_file(rel)
        assert rel in str(excinfo.value), (
            "loud failure must name the module with zero history"
        )
    finally:
        probe.unlink(missing_ok=True)


def test_generator_reports_all_modules():
    """Sanity: the generator discovers the same tree the test scans."""
    gen = _load_gen_module()
    assert gen.discover_modules() == _discover_modules()
