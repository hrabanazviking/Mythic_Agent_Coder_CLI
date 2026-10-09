"""Static code review (Slice 44).

``review_file`` runs a set of lightweight, AST-based checks over a
Python file and returns a list of :class:`Issue` records:

- long functions (> 50 lines)
- missing docstrings (module, class, function)
- bare ``except:`` clauses
- ``TODO`` / ``FIXME`` comments
- unused imports (best effort, name-based)
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

__all__ = ["Issue", "SEVERITIES", "review_file", "review_project",
           "format_issues", "summary_counts"]

SEVERITIES = ("info", "warning", "error")

LONG_FUNCTION_LINES = 50


@dataclass(order=True)
class Issue:
    """A single review finding."""
    severity: str = field(compare=False)   # "info" | "warning" | "error"
    line: int = 0
    message: str = field(default="", compare=False)
    check: str = field(default="", compare=False)  # check name, e.g. "long-function"
    path: str = field(default="", compare=False)

    def __post_init__(self) -> None:
        if self.severity not in SEVERITIES:
            raise ValueError(f"severity must be one of {SEVERITIES}, got {self.severity!r}")

    def one_line(self) -> str:
        loc = f"{self.path}:{self.line}" if self.path else f"line {self.line}"
        return f"[{self.severity}] {loc} ({self.check}): {self.message}"


_TODO_RE = re.compile(r"\b(TODO|FIXME|XXX|HACK)\b\s*:?\s*(.*)")


class _ReviewVisitor(ast.NodeVisitor):
    def __init__(self, path: str) -> None:
        self.path = path
        self.issues: list[Issue] = []
        self._imports: dict[str, int] = {}   # name -> line
        self._names_used: set[str] = set()

    def _add(self, severity: str, line: int, message: str, check: str) -> None:
        self.issues.append(Issue(severity=severity, line=line,
                                 message=message, check=check, path=self.path))

    # -- missing docstrings -------------------------------------------

    def _check_docstring(self, node: ast.AST, kind: str, name: str) -> None:
        if not ast.get_docstring(node):
            self._add("info", getattr(node, "lineno", 0),
                      f"{kind} {name!r} is missing a docstring", "missing-docstring")

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._check_docstring(node, "Function", node.name)
        self._check_length(node)
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef  # type: ignore[assignment]

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._check_docstring(node, "Class", node.name)
        self.generic_visit(node)

    # -- long functions -------------------------------------------------

    def _check_length(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        end = getattr(node, "end_lineno", None) or node.lineno
        length = end - node.lineno + 1
        if length > LONG_FUNCTION_LINES:
            self._add("warning", node.lineno,
                      f"Function {node.name!r} is {length} lines long "
                      f"(> {LONG_FUNCTION_LINES}); consider splitting it",
                      "long-function")

    # -- bare except ----------------------------------------------------

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.type is None:
            self._add("error", node.lineno,
                      "Bare 'except:' catches everything including "
                      "KeyboardInterrupt/SystemExit; catch Exception instead",
                      "bare-except")
        self.generic_visit(node)

    # -- imports / name usage ------------------------------------------

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self._imports[alias.asname or alias.name.split(".")[0]] = node.lineno
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module == "__future__":
            return  # `from __future__ import annotations` is never "used" by name
        for alias in node.names:
            if alias.name != "*":
                self._imports[alias.asname or alias.name] = node.lineno
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load):
            self._names_used.add(node.id)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        # Count `os.path` style usage as a use of `os`.
        value = node.value
        while isinstance(value, ast.Attribute):
            value = value.value
        if isinstance(value, ast.Name):
            self._names_used.add(value.id)
        self.generic_visit(node)

    def unused_import_issues(self) -> list[Issue]:
        issues = []
        for name, lineno in sorted(self._imports.items(), key=lambda kv: kv[1]):
            if name not in self._names_used:
                issues.append(Issue(severity="warning", line=lineno,
                                    message=f"Imported name {name!r} is never used",
                                    check="unused-import", path=self.path))
        return issues


def _todo_issues(source: str, path: str) -> list[Issue]:
    issues: list[Issue] = []
    for lineno, line in enumerate(source.splitlines(), start=1):
        match = _TODO_RE.search(line)
        if match:
            tag, detail = match.group(1), match.group(2).strip()
            issues.append(Issue(
                severity="info", line=lineno,
                message=f"{tag} comment" + (f": {detail}" if detail else ""),
                check="todo-comment", path=path))
    return issues


def review_file(path: str | Path) -> list[Issue]:
    """Review a single Python file; return sorted :class:`Issue` list.

    Non-Python files return an empty list. Unparseable files yield a
    single error-severity issue instead of raising.
    """
    p = Path(path)
    display = str(p)
    if p.suffix != ".py":
        return []
    try:
        source = p.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [Issue(severity="error", line=0,
                      message=f"Cannot read file: {exc}", check="io-error",
                      path=display)]
    try:
        tree = ast.parse(source, filename=display)
    except SyntaxError as exc:
        return [Issue(severity="error", line=exc.lineno or 0,
                      message=f"Syntax error: {exc.msg}", check="syntax-error",
                      path=display)]

    issues: list[Issue] = []
    body = tree.body
    has_module_docstring = (
        bool(body) and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    )
    if not has_module_docstring:
        issues.append(Issue(severity="info", line=1,
                            message="Module is missing a docstring",
                            check="missing-docstring", path=display))
    visitor = _ReviewVisitor(display)
    visitor.visit(tree)
    issues += visitor.issues + visitor.unused_import_issues() + _todo_issues(source, display)
    issues.sort(key=lambda i: (i.line, SEVERITIES.index(i.severity)))
    return issues


def review_project(root: str | Path,
                   exclude: Optional[list[str]] = None) -> dict[str, list[Issue]]:
    """Review every ``*.py`` file under *root*.

    Returns a mapping of file path -> issues (files with no issues are
    omitted). *exclude* is a list of directory names to skip.
    """
    root = Path(root)
    excluded = set(exclude or []) | {"__pycache__", ".git", ".hg", "venv", ".venv",
                                     "node_modules", ".mythic", ".tox"}
    results: dict[str, list[Issue]] = {}
    for path in sorted(root.rglob("*.py")):
        if any(part in excluded for part in path.parts):
            continue
        issues = review_file(path)
        if issues:
            results[str(path)] = issues
    return results


def format_issues(issues: list[Issue]) -> str:
    """Render issues as human-readable lines."""
    if not issues:
        return "No issues found."
    return "\n".join(i.one_line() for i in issues)


def summary_counts(issues: list[Issue]) -> dict[str, int]:
    """Count issues by severity."""
    counts = {sev: 0 for sev in SEVERITIES}
    for issue in issues:
        counts[issue.severity] = counts.get(issue.severity, 0) + 1
    return counts
