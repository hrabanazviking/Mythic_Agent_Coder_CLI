#!/usr/bin/env python3
"""R-022 / roadmap 022 — Static Analysis Gate (stdlib only).

Runs a battery of static checks over the repository and exits non-zero on
any hard finding. Informational findings (print() usage, TODO debt) are
reported but do not fail the gate.

Hard gates:
  1. Byte-compilation of ``mythic_agent/`` and ``tests/`` with
     SyntaxWarning promoted to an error.
  2. No bare ``except:`` clauses anywhere (they swallow KeyboardInterrupt
     and hide bugs; dawn R-008 codified the exception taxonomy).
  3. No ``eval()`` / ``exec()`` calls anywhere.

Report-only:
  - ``print()`` calls in library code (legitimate in CLI/TUI surfaces).
  - TODO / FIXME / XXX / HACK markers (debt ledger).

Usage: ``python scripts/static_gate.py [--json]`` from the repo root.
Exit code 0 = gate passed.
"""

from __future__ import annotations

import ast
import compileall
import json
import pathlib
import re
import sys
import warnings

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SCAN_ROOTS = [REPO_ROOT / "mythic_agent", REPO_ROOT / "tests"]
TODO_RE = re.compile(r"\b(TODO|FIXME|XXX|HACK)\b")


def _iter_py_files() -> list[pathlib.Path]:
    files: list[pathlib.Path] = []
    for root in SCAN_ROOTS:
        files.extend(p for p in root.rglob("*.py") if "__pycache__" not in p.parts)
    return sorted(files)


def check_compile() -> list[str]:
    """Byte-compile everything with SyntaxWarning as an error."""
    errors: list[str] = []
    with warnings.catch_warnings():
        warnings.simplefilter("error", SyntaxWarning)
        ok = compileall.compile_dir(
            str(REPO_ROOT / "mythic_agent"), quiet=1, force=True
        ) and compileall.compile_dir(str(REPO_ROOT / "tests"), quiet=1, force=True)
    if not ok:
        errors.append("byte-compilation failed (see output above)")
    return errors


def check_ast() -> tuple[list[str], dict[str, list[str]]]:
    hard: list[str] = []
    info: dict[str, list[str]] = {"print_calls": [], "todo_markers": []}
    for path in _iter_py_files():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            hard.append(f"{path}:{exc.lineno}: syntax error: {exc.msg}")
            continue
        for node in ast.walk(tree):
            where = f"{path.relative_to(REPO_ROOT)}:{getattr(node, 'lineno', 0)}"
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                hard.append(f"{where}: bare 'except:' clause")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in ("eval", "exec"):
                    hard.append(f"{where}: {node.func.id}() call")
                elif node.func.id == "print":
                    info["print_calls"].append(where)
        for lineno, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if TODO_RE.search(line):
                info["todo_markers"].append(
                    f"{path.relative_to(REPO_ROOT)}:{lineno}: {line.strip()[:100]}"
                )
    return hard, info


def main() -> int:
    as_json = "--json" in sys.argv[1:]
    hard = check_compile()
    ast_hard, info = check_ast()
    hard.extend(ast_hard)
    report = {
        "files_scanned": len(_iter_py_files()),
        "hard_findings": hard,
        "print_calls": info["print_calls"],
        "todo_markers": info["todo_markers"],
        "passed": not hard,
    }
    if as_json:
        print(json.dumps(report, indent=2))
    else:
        print(f"static gate: {report['files_scanned']} files scanned")
        print(f"hard findings: {len(hard)}")
        for finding in hard:
            print(f"  FAIL {finding}")
        print(f"print() calls (info): {len(info['print_calls'])}")
        print(f"TODO markers (info): {len(info['todo_markers'])}")
        for marker in info["todo_markers"]:
            print(f"  DEBT {marker}")
        print("GATE PASSED" if not hard else "GATE FAILED")
    return 0 if not hard else 1


if __name__ == "__main__":
    sys.exit(main())
