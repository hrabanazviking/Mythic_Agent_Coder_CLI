"""AST-aware code understanding for the Mythic agent (Slice 19).

``SymbolIndex`` builds a per-workspace index of Python symbols
(functions, classes, imports) using the ``ast`` module. Indexes are
cached and invalidated when a file's mtime changes.
"""

__all__ = [
    "Optional",
    "Path",
    "Symbol",
    "SymbolIndex",
    "dataclass",
    "field",
    "refresh_mtime",
]

import ast
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

__all__ = ["Symbol", "SymbolIndex"]


@dataclass
class Symbol:
    """A named symbol discovered in a Python source file."""
    name: str
    kind: str            # "function" | "class" | "import" | "method" ...
    path: Path
    lineno: int
    qualified: str = ""  # e.g. "MyClass.my_method" or "module.Class"
    docstring: str = ""

    def location(self) -> str:
        """Human-readable ``path:line`` location."""
        return f"{self.path}:{self.lineno}"


class _SymbolVisitor(ast.NodeVisitor):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.symbols: list[Symbol] = []
        self._scope: list[str] = []

    def _record(self, node: ast.AST, kind: str, name: str) -> None:
        qualified = ".".join(self._scope + [name]) if self._scope else name
        doc = ast.get_docstring(node, clean=False) or ""
        self.symbols.append(Symbol(
            name=name, kind=kind, path=self.path,
            lineno=getattr(node, "lineno", 0),
            qualified=qualified,
            docstring=doc.strip().splitlines()[0] if doc.strip() else "",
        ))

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        kind = "method" if self._scope else "function"
        self._record(node, kind, node.name)
        self._scope.append(node.name)
        self.generic_visit(node)
        self._scope.pop()

    visit_AsyncFunctionDef = visit_FunctionDef  # type: ignore[assignment]

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._record(node, "class", node.name)
        self._scope.append(node.name)
        self.generic_visit(node)
        self._scope.pop()

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            label = alias.asname or alias.name.split(".")[0]
            self.symbols.append(Symbol(
                name=label, kind="import", path=self.path, lineno=node.lineno,
                qualified=label, docstring=alias.name,
            ))

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        for alias in node.names:
            if alias.name == "*":
                continue
            label = alias.asname or alias.name
            self.symbols.append(Symbol(
                name=label, kind="import", path=self.path, lineno=node.lineno,
                qualified=label, docstring=f"{module}.{alias.name}",
            ))


@dataclass
class _FileEntry:
    mtime: float
    symbols: list[Symbol] = field(default_factory=list)


class SymbolIndex:
    """Per-workspace symbol index backed by ``ast``.

    The index is lazy: files are parsed on first access and re-parsed
    when their mtime changes.
    """

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self._files: dict[Path, _FileEntry] = {}

    # -- indexing ------------------------------------------------------

    def index_file(self, path: str | Path) -> list[Symbol]:
        """Parse *path* and return its symbols (cached by mtime)."""
        path = Path(path)
        if not path.is_absolute():
            path = (self.root / path).resolve()
        else:
            path = path.resolve()
        try:
            mtime = path.stat().st_mtime
        except OSError:
            self._files.pop(path, None)
            return []
        entry = self._files.get(path)
        if entry is not None and entry.mtime == mtime:
            return entry.symbols
        symbols: list[Symbol] = []
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source, filename=str(path))
        except (SyntaxError, ValueError, OSError):
            symbols = []
        else:
            visitor = _SymbolVisitor(path)
            visitor.visit(tree)
            symbols = visitor.symbols
        self._files[path] = _FileEntry(mtime=mtime, symbols=symbols)
        return symbols

    def index_workspace(self) -> int:
        """Index every ``*.py`` file under the root. Returns symbol count."""
        total = 0
        for path in self.root.rglob("*.py"):
            if path.is_file():
                total += len(self.index_file(path))
        return total

    def invalidate(self, path: Optional[str | Path] = None) -> None:
        """Drop cached entries: one file, or the whole index if *path* is None."""
        if path is None:
            self._files.clear()
            return
        p = Path(path)
        if not p.is_absolute():
            p = (self.root / p).resolve()
        else:
            p = p.resolve()
        self._files.pop(p, None)

    # -- lookup --------------------------------------------------------

    def find_definition(self, symbol: str,
                        root: Optional[str | Path] = None) -> Optional[str]:
        """Return ``path:line`` of the best definition of *symbol*, or None."""
        search_root = Path(root) if root is not None else self.root
        best: Optional[Symbol] = None
        for path in search_root.rglob("*.py"):
            if not path.is_file():
                continue
            for sym in self.index_file(path):
                if sym.name != symbol and sym.qualified != symbol:
                    continue
                # Prefer real definitions over imports; prefer top-level.
                rank = {"class": 0, "function": 0, "method": 1, "import": 2}
                if best is None or (
                    rank.get(sym.kind, 3) < rank.get(best.kind, 3)
                    or (rank.get(sym.kind, 3) == rank.get(best.kind, 3)
                        and sym.lineno < best.lineno)
                ):
                    best = sym
        return best.location() if best else None

    def find_references(self, symbol: str,
                        root: Optional[str | Path] = None) -> list[str]:
        """Simple text search for *symbol* (word-boundary) in ``*.py`` files.

        Returns ``path:line`` strings sorted by path then line.
        """
        search_root = Path(root) if root is not None else self.root
        pattern = re.compile(r"\b" + re.escape(symbol) + r"\b")
        hits: list[str] = []
        for path in search_root.rglob("*.py"):
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for lineno, line in enumerate(text.splitlines(), start=1):
                if pattern.search(line):
                    hits.append(f"{path}:{lineno}")
        hits.sort(key=lambda h: (h.rsplit(":", 1)[0], int(h.rsplit(":", 1)[1])))
        return hits

    def invalidate_stale(self, root: Optional[str | Path] = None) -> int:
        """Re-check mtimes of cached files; drop changed ones. Returns count."""
        search_root = Path(root) if root is not None else self.root
        dropped = 0
        for path, entry in list(self._files.items()):
            try:
                mtime = path.stat().st_mtime
            except OSError:
                self._files.pop(path, None)
                dropped += 1
                continue
            if mtime != entry.mtime:
                self._files.pop(path, None)
                dropped += 1
        # Pick up brand-new files.
        for path in search_root.rglob("*.py"):
            if path.is_file() and path.resolve() not in self._files:
                self.index_file(path)
        return dropped


def refresh_mtime(path: str | Path) -> None:
    """Utility for tests: bump a file's mtime reliably."""
    p = Path(path)
    now = time.time()
    p.touch()
    import os
    os.utime(p, (now + 2, now + 2))
