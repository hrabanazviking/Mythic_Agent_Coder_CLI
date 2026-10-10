"""R-022 / roadmap 022 — Static Analysis Gate.

Runs scripts/static_gate.py in-process and asserts it passes. Any hard
finding (compile error, SyntaxWarning, bare except, eval/exec) fails the
suite loudly instead of rotting silently.
"""

import importlib.util
import pathlib
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def _load_gate():
    spec = importlib.util.spec_from_file_location(
        "static_gate", REPO_ROOT / "scripts" / "static_gate.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_static_gate_passes():
    gate = _load_gate()
    hard, info = gate.check_ast()
    assert hard == [], f"static gate hard findings: {hard}"
    assert gate.check_compile() == []


def test_static_gate_main_exits_zero(capsys):
    gate = _load_gate()
    assert gate.main() == 0
    out = capsys.readouterr().out
    assert "GATE PASSED" in out


def test_gate_scans_expected_roots():
    gate = _load_gate()
    files = gate._iter_py_files()
    assert len(files) > 100
    assert all(
        str(p).startswith(str(REPO_ROOT / "mythic_agent"))
        or str(p).startswith(str(REPO_ROOT / "tests"))
        for p in files
    )
    assert not any("__pycache__" in p.parts for p in files)


def test_todo_debt_is_reported_not_hidden():
    gate = _load_gate()
    _, info = gate.check_ast()
    # Debt markers exist in the repo; the gate must surface them, not fail.
    assert isinstance(info["todo_markers"], list)
