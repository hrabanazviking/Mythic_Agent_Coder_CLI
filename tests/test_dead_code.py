"""Dead-code quarantine tests (roadmap slice R-006).

Covers the stdlib-ast scanner in mythic_agent.core.dead_code_scan and the
repository gate: no NEW dead code may appear beyond the quarantined list.
"""
import os
from pathlib import Path

import pytest

from mythic_agent.core.dead_code_scan import (
    load_quarantine,
    scan,
    write_quarantine,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGE = str(REPO_ROOT / "mythic_agent")
QUARANTINE = REPO_ROOT / "docs" / "DEAD_CODE_QUARANTINE.txt"


def _key(item):
    """Gate identity: (path, name, kind) — line numbers shift with edits.

    Paths are normalized to repo-relative so the comparison holds whether
    the scan ran with an absolute or a relative root.
    """
    path, _lineno, name, kind = item
    if os.path.isabs(path):
        path = os.path.relpath(path, str(REPO_ROOT))
    return (path, name, kind)


def test_scanner_finds_deliberately_dead_function(tmp_path):
    (tmp_path / "mod.py").write_text(
        "def used():\n"
        "    return 1\n"
        "\n"
        "def totally_dead_helper():\n"
        "    return 2\n"
        "\n"
        "print(used())\n"
    )
    items = scan(str(tmp_path))
    names = {name for _, _, name, _ in items}
    assert "totally_dead_helper" in names
    assert "used" not in names


def test_scanner_does_not_flag_function_referenced_elsewhere(tmp_path):
    (tmp_path / "a.py").write_text(
        "def shared_helper():\n"
        "    return 1\n"
    )
    (tmp_path / "b.py").write_text(
        "from a import shared_helper\n"
        "\n"
        "print(shared_helper())\n"
    )
    items = scan(str(tmp_path))
    names = {name for _, _, name, _ in items}
    assert "shared_helper" not in names


def test_scanner_respects_all_whitelist(tmp_path):
    (tmp_path / "mod.py").write_text(
        '__all__ = ["exported"]\n'
        "\n"
        "def exported():\n"
        "    return 1\n"
        "\n"
        "def not_exported():\n"
        "    return 2\n"
    )
    items = scan(str(tmp_path))
    names = {name for _, _, name, _ in items}
    assert "exported" not in names
    assert "not_exported" in names


def test_quarantine_roundtrip(tmp_path):
    items = [("mythic_agent/x.py", 10, "dead_fn", "function")]
    path = tmp_path / "q.txt"
    write_quarantine(items, str(path))
    assert load_quarantine(str(path)) == items


def test_no_new_dead_code_beyond_quarantine():
    """Gate: every currently-dead item must already be quarantined.

    Fails when a scan finds a dead item that is not recorded in
    docs/DEAD_CODE_QUARANTINE.txt, i.e. when NEW dead code appears.
    """
    assert QUARANTINE.exists(), (
        f"quarantine inventory missing: {QUARANTINE}"
    )
    quarantined = {_key(item) for item in load_quarantine(str(QUARANTINE))}
    current = scan(PACKAGE)
    new_items = [_key(item) for item in current
                 if _key(item) not in quarantined]
    assert not new_items, (
        "NEW dead code found beyond docs/DEAD_CODE_QUARANTINE.txt; "
        "either remove it or re-run the quarantine scan and record it:\n"
        + "\n".join(f"  {path}:{name} ({kind})"
                    for path, name, kind in sorted(new_items))
    )


def test_scanner_module_importable_and_fast():
    items = scan(PACKAGE)
    assert isinstance(items, list)
    assert all(len(item) == 4 for item in items)
