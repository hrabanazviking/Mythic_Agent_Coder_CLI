"""Symbol-aware file selection (Slice 058).

Uses :mod:`ast` from the standard library to extract ``def``/``class``
symbols from Python files.  Files are ranked by how many of their
symbols are mentioned in the query (identifier-aware, case-insensitive),
so a query about ``rebuild_system_prompt`` surfaces the file that
defines it.
"""

from __future__ import annotations

__all__ = [
    "Symbol",
    "SymbolIndex",
    "extract_symbols",
    "index_workspace",
    "rank_by_symbol_mentions",
    "select_by_symbols",
]

import ast
import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..core.workspace import assert_within_workspace, canonical_workspace_root
from .budget import TokenEstimator
from .compiler import ContextBlock, ContextSource


IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

MAX_FILES = 200
MAX_FILE_BYTES = 65_536
_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv",
              "dist", "build", ".hg", ".svn"}


@dataclass
class Symbol:
    """One extracted definition."""

    name: str
    kind: str  # "function", "async function" or "class"
    lineno: int
    qualified: str


def extract_symbols(source: str) -> list[Symbol]:
    """Extract ``def``/``class`` symbols from Python *source* via :mod:`ast`.

    Raises :class:`SyntaxError` for unparseable source; callers decide
    whether to skip with a warning.
    """
    tree = ast.parse(source)
    symbols: list[Symbol] = []

    def visit(node: ast.AST, prefix: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                kind = ("class" if isinstance(child, ast.ClassDef)
                        else "async function" if isinstance(child, ast.AsyncFunctionDef)
                        else "function")
                qualified = f"{prefix}.{child.name}" if prefix else child.name
                symbols.append(Symbol(name=child.name, kind=kind,
                                     lineno=child.lineno, qualified=qualified))
                visit(child, qualified)
            else:
                visit(child, prefix)

    visit(tree, "")
    return symbols


@dataclass
class SymbolIndex:
    """Per-file symbol tables for one workspace."""

    files: dict[str, list[Symbol]]  # workspace-relative path -> symbols
    warnings: list[str] = field(default_factory=list)


def index_workspace(
    workspace: Path | str,
    *,
    max_files: int = MAX_FILES,
    max_file_bytes: int = MAX_FILE_BYTES,
) -> SymbolIndex:
    """Extract symbols from ``.py`` files under *workspace*.

    Files that fail to parse are skipped with a warning; every skipped
    file is reported, never silently ignored.
    """
    root = canonical_workspace_root(workspace)
    index: dict[str, list[Symbol]] = {}
    warnings: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = sorted(d for d in dirnames
                             if d not in _SKIP_DIRS and not d.startswith("."))
        for name in sorted(filenames):
            if len(index) >= max_files:
                warnings.append(f"symbol index file cap reached ({max_files})")
                return SymbolIndex(files=index, warnings=warnings)
            if not name.endswith(".py"):
                continue
            candidate = Path(dirpath) / name
            try:
                resolved = assert_within_workspace(root, candidate)
            except Exception as exc:
                warnings.append(f"blocked {candidate}: {exc}")
                continue
            try:
                raw = resolved.read_bytes()
            except OSError as exc:
                warnings.append(f"unreadable {resolved}: {exc}")
                continue
            if len(raw) > max_file_bytes or b"\x00" in raw:
                continue
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                warnings.append(f"malformed (not utf-8): {resolved}")
                continue
            try:
                symbols = extract_symbols(text)
            except SyntaxError as exc:
                warnings.append(f"unparseable {resolved}: {exc}")
                continue
            index[str(resolved.relative_to(root))] = symbols
    return SymbolIndex(files=index, warnings=warnings)


def rank_by_symbol_mentions(
    query: str, index: SymbolIndex
) -> list[tuple[str, int]]:
    """Rank indexed files by symbol mentions in *query*.

    Returns ``(doc_id, hit_count)`` sorted by hit count desc, then
    doc_id asc (deterministic).  Matching is case-insensitive on
    identifiers; a mention matches a symbol when the identifier equals
    the symbol name or a dotted suffix of its qualified name.
    """
    query_idents = {ident.lower() for ident in IDENT_RE.findall(query or "")}
    if not query_idents:
        return []
    ranked: list[tuple[str, int]] = []
    for doc_id, symbols in index.files.items():
        hits = 0
        for symbol in symbols:
            parts = {symbol.name.lower()}
            parts.update(symbol.qualified.lower().split("."))
            if query_idents & parts:
                hits += 1
        if hits:
            ranked.append((doc_id, hits))
    ranked.sort(key=lambda pair: (-pair[1], pair[0]))
    return ranked


def select_by_symbols(
    query: str,
    workspace: Path | str,
    *,
    top_n: int = 5,
    budget_tokens: int = 2000,
    estimator: TokenEstimator | None = None,
) -> tuple[list[tuple[str, list[Symbol]]], list[str]]:
    """Select up to *top_n* files by symbol mentions inside *budget_tokens*."""
    if top_n <= 0:
        raise ValueError("top_n must be positive")
    if budget_tokens < 0:
        raise ValueError("budget_tokens must be non-negative")
    estimator = estimator or TokenEstimator()
    index = index_workspace(workspace)
    ranked = rank_by_symbol_mentions(query, index)
    root = canonical_workspace_root(workspace)
    selected: list[tuple[str, list[Symbol]]] = []
    remaining = budget_tokens
    for doc_id, _hits in ranked:
        if len(selected) >= top_n:
            break
        text = (root / doc_id).read_text(encoding="utf-8")
        cost = estimator.count(text)
        if cost <= remaining:
            selected.append((doc_id, index.files[doc_id]))
            remaining -= cost
    return selected, index.warnings


class SymbolFilesSource(ContextSource):
    """Compiler source selecting files by symbol mentions (Slice 058)."""

    def __init__(self, *, priority: int = 4, enabled: bool = True,
                 top_n: int = 5, budget_tokens: int = 2000) -> None:
        self.name = "symbol-files"
        self.priority = priority
        self.enabled = enabled
        self.top_n = top_n
        self.budget_tokens = budget_tokens

    def collect(self, ctx) -> list[ContextBlock]:
        if not (ctx.query or "").strip():
            return []
        selected, warnings = select_by_symbols(
            ctx.query, ctx.workspace, top_n=self.top_n,
            budget_tokens=self.budget_tokens)
        for warning in warnings:
            logging.getLogger(__name__).warning("symbol-files: %s", warning)
        root = ctx.workspace
        blocks = []
        for doc_id, symbols in selected:
            text = (root / doc_id).read_text(encoding="utf-8")
            header = ", ".join(f"{s.qualified} ({s.kind})" for s in symbols[:20])
            blocks.append(ContextBlock(
                name=f"symbols:{doc_id}",
                content=f"--- {doc_id} ---\nsymbols: {header}\n{text}",
                priority=self.priority,
                provenance={"doc_id": doc_id, "symbol_count": len(symbols)}))
        return blocks
