"""Type-annotation coverage measurement for the ``mythic_agent`` package.

Pure, print-free helpers: every public function returns data (dataclasses or
plain dicts) and never writes to stdout/stderr.

The core measurement is stdlib ``ast`` based, so it works on a bare checkout.
``mypy`` is *preferred* when present but never required: :func:`mypy_available`
reports whether a mypy installation can be found, and :func:`mypy_check` runs a
complementary strictness pass only when it is.  The annotation-coverage gate
itself is defined purely by :func:`measure`.

Counting rules (documented here so the numbers are reproducible):

* Every ``def``/``async def`` found by walking each module's AST is counted,
  including methods and nested functions.
* Parameters: ``posonly`` + positional + keyword-only + ``*args`` + ``**kwargs``.
  For methods (a function defined directly inside a class body), a leading
  ``self`` or ``cls`` parameter is excluded — it is never annotated by
  convention and would otherwise distort the signal.
* Returns: one slot per function; annotated when a return annotation exists.
* Excluded from the gate: ``__init__.py`` files and test files (anything under
  a ``tests`` directory or named ``test_*.py`` / ``*_test.py``).
* Files that fail to parse are skipped and listed in ``CoverageReport.skipped``
  rather than aborting the whole measurement.
"""


from __future__ import annotations

__all__ = [
    "CoverageReport",
    "ModuleCoverage",
    "Path",
    "dataclass",
    "field",
    "measure",
    "measure_module",
    "mypy_available",
    "mypy_check",
]

import ast
import importlib.util
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

_PACKAGE_NAME = "mythic_agent"


def mypy_available() -> bool:
    """Return True when a mypy installation is importable or on PATH.

    When True, callers may prefer :func:`mypy_check` for a strictness pass;
    the ast-based coverage numbers remain the authoritative gate either way.
    """
    if importlib.util.find_spec("mypy") is not None:
        return True
    return shutil.which("mypy") is not None


class _FunctionVisitor(ast.NodeVisitor):
    """Collect (is_method, function-node) pairs from a module AST."""

    def __init__(self) -> None:
        self.entries: list[tuple[bool, ast.FunctionDef | ast.AsyncFunctionDef]] = []
        self._class_depth = 0

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._class_depth += 1
        self.generic_visit(node)
        self._class_depth -= 1

    def _record(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self.entries.append((self._class_depth > 0, node))
        self.generic_visit(node)  # keep walking: nested defs count too

    visit_FunctionDef = _record
    visit_AsyncFunctionDef = _record


def _count_function(is_method: bool,
                    node: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[int, int, int, int]:
    """Return (params_total, params_annotated, returns_total, returns_annotated)."""
    args = node.args
    params: list[ast.arg] = [
        *args.posonlyargs,
        *args.args,
        *args.kwonlyargs,
    ]
    if args.vararg is not None:
        params.append(args.vararg)
    if args.kwarg is not None:
        params.append(args.kwarg)

    if is_method and params and params[0].arg in ("self", "cls"):
        params = params[1:]

    params_total = len(params)
    params_annotated = sum(1 for p in params if p.annotation is not None)
    returns_total = 1
    returns_annotated = 1 if node.returns is not None else 0
    return params_total, params_annotated, returns_total, returns_annotated


def _is_excluded(relative: Path) -> bool:
    name = relative.name
    if name == "__init__.py":
        return True
    if name.startswith("test_") or name.endswith("_test.py"):
        return True
    if "tests" in relative.parts:
        return True
    return False


def _dotted_name(package_dir: Path, path: Path) -> str:
    relative = path.relative_to(package_dir).with_suffix("")
    return ".".join([_PACKAGE_NAME, *relative.parts])


@dataclass
class ModuleCoverage:
    """Annotation counts for one module."""

    module: str
    path: str  # repo-relative POSIX path of the source file
    functions: int
    params_total: int
    params_annotated: int
    returns_total: int
    returns_annotated: int

    @property
    def params_pct(self) -> float:
        if self.params_total == 0:
            return 100.0
        return 100.0 * self.params_annotated / self.params_total

    @property
    def returns_pct(self) -> float:
        if self.returns_total == 0:
            return 100.0
        return 100.0 * self.returns_annotated / self.returns_total

    def to_dict(self) -> dict:
        return {
            "module": self.module,
            "path": self.path,
            "functions": self.functions,
            "params_total": self.params_total,
            "params_annotated": self.params_annotated,
            "returns_total": self.returns_total,
            "returns_annotated": self.returns_annotated,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ModuleCoverage":
        return cls(
            module=data["module"],
            path=data["path"],
            functions=data["functions"],
            params_total=data["params_total"],
            params_annotated=data["params_annotated"],
            returns_total=data["returns_total"],
            returns_annotated=data["returns_annotated"],
        )


@dataclass
class CoverageReport:
    """Package-wide annotation coverage."""

    root: str  # repo root the measurement was taken from
    mypy_available: bool
    modules: list[ModuleCoverage] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)  # unparsable files

    @property
    def module_count(self) -> int:
        return len(self.modules)

    @property
    def functions_total(self) -> int:
        return sum(m.functions for m in self.modules)

    @property
    def params_total(self) -> int:
        return sum(m.params_total for m in self.modules)

    @property
    def params_annotated(self) -> int:
        return sum(m.params_annotated for m in self.modules)

    @property
    def returns_total(self) -> int:
        return sum(m.returns_total for m in self.modules)

    @property
    def returns_annotated(self) -> int:
        return sum(m.returns_annotated for m in self.modules)

    @property
    def params_pct(self) -> float:
        if self.params_total == 0:
            return 100.0
        return 100.0 * self.params_annotated / self.params_total

    @property
    def returns_pct(self) -> float:
        if self.returns_total == 0:
            return 100.0
        return 100.0 * self.returns_annotated / self.returns_total

    def module_named(self, dotted_name: str) -> ModuleCoverage | None:
        for module in self.modules:
            if module.module == dotted_name:
                return module
        return None

    def to_dict(self) -> dict:
        return {
            "root": self.root,
            "mypy_available": self.mypy_available,
            "modules": [m.to_dict() for m in self.modules],
            "skipped": list(self.skipped),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CoverageReport":
        return cls(
            root=data["root"],
            mypy_available=data["mypy_available"],
            modules=[ModuleCoverage.from_dict(m) for m in data.get("modules", [])],
            skipped=list(data.get("skipped", [])),
        )


def measure_module(path: str | Path, *, package_dir: str | Path,
                   repo_root: str | Path) -> ModuleCoverage | None:
    """Measure one file; return None when the file is excluded from the gate."""
    package_dir = Path(package_dir)
    repo_root = Path(repo_root)
    path = Path(path)
    relative_to_package = path.relative_to(package_dir)
    if _is_excluded(relative_to_package):
        return None
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    visitor = _FunctionVisitor()
    visitor.visit(tree)
    params_total = params_annotated = 0
    returns_total = returns_annotated = 0
    for is_method, node in visitor.entries:
        pt, pa, rt, ra = _count_function(is_method, node)
        params_total += pt
        params_annotated += pa
        returns_total += rt
        returns_annotated += ra
    return ModuleCoverage(
        module=_dotted_name(package_dir, path),
        path=path.relative_to(repo_root).as_posix(),
        functions=len(visitor.entries),
        params_total=params_total,
        params_annotated=params_annotated,
        returns_total=returns_total,
        returns_annotated=returns_annotated,
    )


def measure(root: str | Path) -> CoverageReport:
    """Measure annotation coverage for every module in the package.

    ``root`` may be the repository root (containing ``mythic_agent/``) or the
    package directory itself.  Files that fail to parse are recorded in
    ``report.skipped`` instead of aborting the measurement.
    """
    root = Path(root).resolve()
    if (root / _PACKAGE_NAME).is_dir():
        package_dir = root / _PACKAGE_NAME
        repo_root = root
    elif root.name == _PACKAGE_NAME and root.is_dir():
        package_dir = root
        repo_root = root.parent
    else:
        raise ValueError(f"no {_PACKAGE_NAME!r} package found under {root}")

    modules: list[ModuleCoverage] = []
    skipped: list[str] = []
    for path in sorted(package_dir.rglob("*.py")):
        relative_to_package = path.relative_to(package_dir)
        if _is_excluded(relative_to_package):
            continue
        try:
            module = measure_module(path, package_dir=package_dir, repo_root=repo_root)
        except (SyntaxError, UnicodeDecodeError, OSError):
            skipped.append(path.relative_to(repo_root).as_posix())
            continue
        if module is not None:
            modules.append(module)

    return CoverageReport(
        root=repo_root.as_posix(),
        mypy_available=mypy_available(),
        modules=modules,
        skipped=skipped,
    )


def mypy_check(paths: list[str | Path], *, timeout: int = 180) -> dict[str, int] | None:
    """Run mypy over ``paths`` and return per-path error counts.

    Returns None when mypy is not installed.  This is a complementary
    strictness pass — the ast-based coverage gate does not depend on it.
    """
    if not mypy_available():
        return None
    str_paths = [str(p) for p in paths]
    try:
        proc = subprocess.run(
            ["mypy", "--no-error-summary", "--show-column-numbers", *str_paths],
            capture_output=True, text=True, timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    counts: dict[str, int] = {p: 0 for p in str_paths}
    for line in (proc.stdout + proc.stderr).splitlines():
        # mypy error lines look like: path:line:col: error: message [...]
        parts = line.split(":", 3)
        if len(parts) == 4 and parts[2].strip().isdigit() and "error:" in parts[3]:
            reported = parts[0]
            for key in counts:
                if reported == key or reported.endswith("/" + key.lstrip("/")):
                    counts[key] += 1
                    break
    return counts
