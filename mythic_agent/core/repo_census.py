"""Repository Truth Census (slice R-001 / roadmap 001).

Automated, evidence-backed census of the ``mythic_agent`` package tree.

What it measures
----------------
* ``files``          - number of ``*.py`` files under ``mythic_agent/``
                       (``__pycache__`` directories are excluded)
* ``code_lines``     - physical source lines that are neither blank nor
                       pure comments (a line whose first non-whitespace
                       character is ``#``).  Docstrings and string
                       literals count as code lines: this is a cheap,
                       deterministic proxy, not a tokeniser-level count.
* ``classes``        - ``class`` statements found by ``ast`` parsing,
                       including nested classes
* ``functions``      - ``def`` / ``async def`` statements found by
                       ``ast`` parsing, including methods and nested defs
* ``test_files``     - number of ``test_*.py`` files under ``tests/``
* ``tests_collected``- number of ``def test*`` functions collected by
                       ``ast`` parsing of the files under ``tests/``
                       (module-level functions and methods alike; this
                       mirrors collection without importing or running
                       anything)
* ``modules``        - sorted dotted module names of every ``*.py``
                       file in the package (``__init__.py`` maps to its
                       package name)

A file that fails ``ast`` parsing is still counted for ``files`` and
``code_lines`` but contributes zero to ``classes``/``functions``.

Snapshot workflow
-----------------
1. ``snapshot(path)`` writes a canonical JSON receipt of the current
   census (stable key order, stable digest).
2. ``verify_snapshot(path)`` re-runs the census and returns a list of
   human-readable drift messages (module added/removed, counts changed).
   An empty list means the live tree matches the snapshot.

Regenerating the receipt (``docs/REPO_CENSUS.md``)
--------------------------------------------------
Run from the repository root with the project venv::

    ./venv/bin/python -m mythic_agent.core.repo_census receipt \
        --out docs/REPO_CENSUS.md

The ``snapshot`` sub-command writes a JSON receipt instead::

    ./venv/bin/python -m mythic_agent.core.repo_census snapshot \
        --out docs/REPO_CENSUS.json
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PACKAGE_NAME = "mythic_agent"
TESTS_DIR_NAME = "tests"
TOOL_TAG = "repo_census/R-001"

#: Repository root resolved from this file's location; monkeypatchable so
#: tests can point the census at a scratch tree.
REPO_ROOT: Path = Path(__file__).resolve().parents[2]


class SnapshotError(Exception):
    """Raised when a snapshot file cannot be read or trusted."""


def _package_dir(root: Path) -> Path:
    return Path(root) / PACKAGE_NAME


def _tests_dir(root: Path) -> Path:
    return Path(root) / TESTS_DIR_NAME


def _iter_package_files(root: Path):
    """Yield ``*.py`` files under ``mythic_agent/``, excluding ``__pycache__``."""
    package = _package_dir(root)
    if not package.is_dir():
        return
    for path in sorted(package.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        yield path


def _iter_test_files(root: Path):
    """Yield ``test_*.py`` files under ``tests/``, excluding ``__pycache__``."""
    tests = _tests_dir(root)
    if not tests.is_dir():
        return
    for path in sorted(tests.rglob("test_*.py")):
        if "__pycache__" in path.parts:
            continue
        yield path


def _module_name(package: Path, path: Path) -> str:
    """Dotted module name for a package file (``__init__.py`` -> package)."""
    rel = path.relative_to(package).with_suffix("")
    parts = list(rel.parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join([package.name, *parts])


def _code_lines(source: str) -> int:
    """Count lines that are neither blank nor pure comments."""
    count = 0
    for line in source.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        count += 1
    return count


def _ast_counts(source: str) -> tuple[int, int]:
    """Return ``(classes, functions)`` found by ``ast`` parsing.

    Files that fail to parse contribute ``(0, 0)`` rather than
    raising: the census records what is provable, not guesses.
    """
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return 0, 0
    classes = 0
    functions = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes += 1
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions += 1
    return classes, functions


def _test_defs_in(source: str) -> int:
    """Count ``def test*`` functions in a test module source."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return 0
    return sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test")
    )


def _read_source(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


@dataclass(frozen=True)
class Census:
    """Immutable result of a repository truth census."""

    files: int
    code_lines: int
    classes: int
    functions: int
    test_files: int
    tests_collected: int
    modules: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "files": self.files,
            "code_lines": self.code_lines,
            "classes": self.classes,
            "functions": self.functions,
            "test_files": self.test_files,
            "tests_collected": self.tests_collected,
            "modules": list(self.modules),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Census":
        if not isinstance(data, dict):
            raise SnapshotError(
                f"census payload must be a JSON object, got {type(data).__name__}"
            )
        required = (
            "files",
            "code_lines",
            "classes",
            "functions",
            "test_files",
            "tests_collected",
            "modules",
        )
        missing = [key for key in required if key not in data]
        if missing:
            raise SnapshotError(
                f"census payload is missing required field(s): {', '.join(missing)}"
            )
        modules = data["modules"]
        if not isinstance(modules, (list, tuple)):
            raise SnapshotError(
                f"census payload field 'modules' must be a list, "
                f"got {type(modules).__name__}"
            )
        try:
            return cls(
                files=int(data["files"]),
                code_lines=int(data["code_lines"]),
                classes=int(data["classes"]),
                functions=int(data["functions"]),
                test_files=int(data["test_files"]),
                tests_collected=int(data["tests_collected"]),
                modules=tuple(str(m) for m in modules),
            )
        except (TypeError, ValueError) as exc:
            raise SnapshotError(f"census payload has invalid field values: {exc}") from exc

    def digest(self) -> str:
        """Stable sha256 over canonical JSON (sort_keys=True)."""
        canonical = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def census(root: Path | None = None) -> Census:
    """Run the repository truth census against ``root`` (default REPO_ROOT)."""
    root = Path(root) if root is not None else REPO_ROOT
    package = _package_dir(root)

    files = 0
    code_lines = 0
    classes = 0
    functions = 0
    modules: list[str] = []
    for path in _iter_package_files(root):
        files += 1
        source = _read_source(path)
        code_lines += _code_lines(source)
        n_classes, n_functions = _ast_counts(source)
        classes += n_classes
        functions += n_functions
        modules.append(_module_name(package, path))

    test_files = 0
    tests_collected = 0
    for path in _iter_test_files(root):
        test_files += 1
        tests_collected += _test_defs_in(_read_source(path))

    return Census(
        files=files,
        code_lines=code_lines,
        classes=classes,
        functions=functions,
        test_files=test_files,
        tests_collected=tests_collected,
        modules=tuple(sorted(modules)),
    )


def _snapshot_payload(c: Census) -> dict[str, Any]:
    return {
        "tool": TOOL_TAG,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "census": c.to_dict(),
        "digest": c.digest(),
    }


def snapshot(path: str | Path, root: Path | None = None) -> Path:
    """Write a canonical JSON snapshot of the live census to ``path``.

    Returns the resolved path of the written file.
    """
    out = Path(path)
    c = census(root)
    out.write_text(
        json.dumps(_snapshot_payload(c), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return out


def _load_snapshot(path: Path) -> Census:
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise SnapshotError(f"snapshot file not found: {path}") from exc
    except OSError as exc:
        raise SnapshotError(f"cannot read snapshot file {path}: {exc}") from exc
    if not raw.strip():
        raise SnapshotError(f"snapshot file is empty: {path}")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SnapshotError(f"snapshot file {path} is not valid JSON: {exc}") from exc
    if not isinstance(data, dict) or "census" not in data:
        raise SnapshotError(
            f"snapshot file {path} is malformed: expected a JSON object "
            f"with a 'census' key"
        )
    stored = Census.from_dict(data["census"])
    expected_digest = data.get("digest")
    if expected_digest is not None and expected_digest != stored.digest():
        raise SnapshotError(
            f"snapshot file {path} is corrupt: stored digest does not match "
            f"the snapshot's own census payload"
        )
    return stored


_COUNT_LABELS = {
    "files": "package files",
    "code_lines": "code lines",
    "classes": "classes",
    "functions": "functions",
    "test_files": "test files",
    "tests_collected": "collected tests",
}


def verify_snapshot(path: str | Path, root: Path | None = None) -> list[str]:
    """Compare the live tree against a snapshot file.

    Returns human-readable drift messages; an empty list means clean.
    Raises :class:`SnapshotError` for unreadable/malformed snapshots.
    """
    stored = _load_snapshot(Path(path))
    live = census(root)
    stored_map = stored.to_dict()
    live_map = live.to_dict()
    drift: list[str] = []

    old_modules = set(stored.modules)
    new_modules = set(live.modules)
    for name in sorted(new_modules - old_modules):
        drift.append(f"module added: {name}")
    for name in sorted(old_modules - new_modules):
        drift.append(f"module removed: {name}")

    for field, label in _COUNT_LABELS.items():
        old = stored_map[field]
        new = live_map[field]
        if old != new:
            direction = "increased" if new > old else "decreased"
            drift.append(f"{label} {direction}: {old} -> {new}")

    return drift


def render_receipt(c: Census) -> str:
    """Render the live snapshot receipt (``docs/REPO_CENSUS.md``)."""
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds")
    modules_list = "\n".join(f"- `{name}`" for name in c.modules)
    return f"""# Repository Truth Census — Receipt

*Tool:* `{TOOL_TAG}` (`mythic_agent.core.repo_census`)
*Generated:* {generated} (UTC)
*Digest:* `{c.digest()}`

## Census

| Measure | Value |
|---|---|
| Package files (`mythic_agent/`) | {c.files} |
| Code lines (excl. blanks/comments) | {c.code_lines} |
| Classes | {c.classes} |
| Functions | {c.functions} |
| Test files (`tests/`) | {c.test_files} |
| Collected tests | {c.tests_collected} |
| Modules | {len(c.modules)} |

## Modules ({len(c.modules)})

{modules_list}

## How to regenerate

This document is **generated from the tool** — do not hand-edit the
numbers. Re-run from the repository root with the project venv:

```sh
./venv/bin/python -m mythic_agent.core.repo_census receipt \\
    --out docs/REPO_CENSUS.md
```

The JSON snapshot equivalent:

```sh
./venv/bin/python -m mythic_agent.core.repo_census snapshot \\
    --out docs/REPO_CENSUS.json
```

Drift check against a snapshot:

```python
from mythic_agent.core.repo_census import verify_snapshot
drift = verify_snapshot("docs/REPO_CENSUS.json")
assert not drift, drift
```
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Repository Truth Census (R-001)")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("snapshot", "receipt", "show", "verify"):
        p = sub.add_parser(name)
        if name in ("snapshot", "receipt"):
            p.add_argument("--out", required=True)
        elif name == "verify":
            p.add_argument("--snapshot", "--out", dest="snapshot_path", required=True)
    args = parser.parse_args(argv)

    if args.command == "snapshot":
        out = snapshot(args.out)
        print(f"snapshot written: {out}")
    elif args.command == "receipt":
        c = census()
        Path(args.out).write_text(render_receipt(c), encoding="utf-8")
        print(f"receipt written: {args.out}")
    elif args.command == "show":
        c = census()
        print(json.dumps(c.to_dict(), indent=2, sort_keys=True))
        print(f"digest: {c.digest()}")
    elif args.command == "verify":
        drift = verify_snapshot(args.snapshot_path)
        if drift:
            print("DRIFT DETECTED:")
            for message in drift:
                print(f"  - {message}")
            return 1
        print("snapshot matches live tree")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
