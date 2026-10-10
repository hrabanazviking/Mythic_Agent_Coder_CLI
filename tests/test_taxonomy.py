"""R-023 / roadmap 023 — Test Taxonomy gate.

TIER: unit

Asserts the taxonomy contract from docs/TEST_TAXONOMY.md:
every test module carries a TIER line, tiers are registered pytest markers,
and live-tier tests skip without MYTHIC_LIVE_TESTS=1.
"""

import ast
import pathlib

import pytest

TESTS_DIR = pathlib.Path(__file__).resolve().parent
VALID_TIERS = {"unit", "integration", "live"}
# Modules that landed from parallel workers mid-rebuild; their TIER lines
# are added before this run closes (see docs/TEST_TAXONOMY.md).
PENDING_TIER: set[str] = set()


def _module_tier(path: pathlib.Path) -> str | None:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    doc = ast.get_docstring(tree) or ""
    for line in doc.splitlines():
        line = line.strip()
        if line.startswith("TIER:"):
            return line.split("TIER:", 1)[1].strip()
    return None


def test_every_test_module_declares_a_tier():
    missing = []
    bad = []
    for path in sorted(TESTS_DIR.glob("test_*.py")):
        if path.name in PENDING_TIER:
            continue
        tier = _module_tier(path)
        if tier is None:
            missing.append(path.name)
        elif tier not in VALID_TIERS:
            bad.append(f"{path.name}: {tier!r}")
    assert not missing, f"modules without TIER line: {missing}"
    assert not bad, f"modules with invalid tier: {bad}"


def test_tier_markers_are_registered():
    markers = pytest.config.getini("markers") if hasattr(pytest, "config") else []
    # Fallback: read pyproject directly; the registered list is authoritative.
    import tomllib

    pyproject = TESTS_DIR.parent / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    registered = " ".join(data["tool"]["pytest"]["ini_options"]["markers"])
    for tier in VALID_TIERS:
        assert tier in registered, f"tier marker {tier!r} not registered"


def test_live_tier_skips_by_default():
    import os
    import subprocess
    import sys

    probe = (
        "import pytest\n"
        "@pytest.mark.live\n"
        "def test_probe():\n"
        "    raise AssertionError('live test must not execute')\n"
    )
    probe_file = TESTS_DIR / "test_live_probe_tmp.py"
    probe_file.write_text('"""\nTIER: live\nLive-tier skip probe.\n"""\n' + probe)
    try:
        env = {k: v for k, v in os.environ.items() if k != "MYTHIC_LIVE_TESTS"}
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(probe_file), "-q", "-p", "no:cacheprovider"],
            capture_output=True,
            text=True,
            cwd=str(TESTS_DIR.parent),
            env={**env, "PYTHONPATH": str(TESTS_DIR.parent)},
            timeout=120,
        )
        assert "1 skipped" in result.stdout, result.stdout + result.stderr
    finally:
        probe_file.unlink(missing_ok=True)


def test_no_live_modules_exist_yet():
    live = [
        p.name
        for p in TESTS_DIR.glob("test_*.py")
        if _module_tier(p) == "live" and p.name not in PENDING_TIER
    ]
    assert live == [], f"unexpected live-tier modules: {live}"
