"""Dependency-aware file selection (Slice 059).

Builds a local import graph from :mod:`ast` over the workspace's Python
files, then includes the importers and importees of a seed file inside
the token budget.  Only intra-workspace imports resolve; third-party and
stdlib imports are ignored (they are not context the model needs from
the repo).
"""

from __future__ import annotations

__all__ = [
    "build_import_graph",
    "extract_imports",
    "module_key",
    "related_modules",
    "select_related",
]

import ast
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..core.workspace import assert_within_workspace, canonical_workspace_root
from .budget import TokenEstimator
from .compiler import ContextBlock, ContextSource


MAX_FILES = 200
MAX_FILE_BYTES = 65_536
_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv",
              "dist", "build", ".hg", ".svn"}


def extract_imports(source: str) -> list[str]:
    """Return dotted module names imported by Python *source* (:mod:`ast`).

    Raises :class:`SyntaxError` for unparseable source.
    """
    tree = ast.parse(source)
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.append(node.module)
    return names


def module_key(path: Path, root: Path) -> str:
    """Dotted module key for *path* relative to *root*.

    ``pkg/__init__.py`` -> ``pkg``; ``pkg/mod.py`` -> ``pkg.mod``.
    """
    relative = path.relative_to(root).with_suffix("")
    parts = list(relative.parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _key_to_path(key: str, root: Path) -> Path | None:
    candidate = root.joinpath(*key.split(".")).with_suffix(".py")
    if candidate.is_file():
        return candidate
    package = root.joinpath(*key.split("."), "__init__.py")
    if package.is_file():
        return package
    return None


@dataclass
class ImportGraph:
    """Intra-workspace import graph: module key -> imported module keys."""

    edges: dict[str, set[str]]
    key_to_doc: dict[str, str]  # module key -> workspace-relative path
    warnings: list[str]


def build_import_graph(
    workspace: Path | str,
    *,
    max_files: int = MAX_FILES,
    max_file_bytes: int = MAX_FILE_BYTES,
) -> ImportGraph:
    """Parse Python files and map local imports between them."""
    root = canonical_workspace_root(workspace)
    key_to_doc: dict[str, str] = {}
    sources: dict[str, str] = {}
    warnings: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = sorted(d for d in dirnames
                             if d not in _SKIP_DIRS and not d.startswith("."))
        for name in sorted(filenames):
            if len(sources) >= max_files:
                warnings.append(f"import graph file cap reached ({max_files})")
                break
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
            key = module_key(resolved, root)
            key_to_doc[key] = str(resolved.relative_to(root))
            sources[key] = text
    edges: dict[str, set[str]] = {key: set() for key in sources}
    for key, text in sources.items():
        try:
            imported = extract_imports(text)
        except SyntaxError as exc:
            warnings.append(f"unparseable {key_to_doc[key]}: {exc}")
            continue
        for name in imported:
            target = _key_to_path(name, root)
            if target is not None:
                edges[key].add(module_key(target, root))
    return ImportGraph(edges=edges, key_to_doc=key_to_doc, warnings=warnings)


def related_modules(graph: ImportGraph, seed_key: str, depth: int = 1) -> set[str]:
    """Importees and importers of *seed_key* within *depth* hops."""
    if depth < 1:
        raise ValueError("depth must be >= 1")
    importers: dict[str, set[str]] = {}
    for key, targets in graph.edges.items():
        for target in targets:
            importers.setdefault(target, set()).add(key)
    seen = {seed_key}
    frontier = {seed_key}
    for _ in range(depth):
        nxt: set[str] = set()
        for key in frontier:
            nxt.update(graph.edges.get(key, set()))
            nxt.update(importers.get(key, set()))
        nxt -= seen
        seen.update(nxt)
        frontier = nxt
    seen.discard(seed_key)
    return seen


def select_related(
    seed: Path | str,
    workspace: Path | str,
    *,
    depth: int = 1,
    budget_tokens: int = 2000,
    include_seed: bool = True,
    estimator: TokenEstimator | None = None,
) -> tuple[list[tuple[str, str]], list[str]]:
    """Return ``(doc_id, relation)`` pairs around *seed* inside the budget.

    *relation* is ``"seed"``, ``"imports"`` (seed imports it) or
    ``"imported-by"``.  The seed always comes first.
    """
    estimator = estimator or TokenEstimator()
    root = canonical_workspace_root(workspace)
    seed_path = assert_within_workspace(root, Path(seed))
    graph = build_import_graph(root)
    seed_key = module_key(seed_path, root)
    related = related_modules(graph, seed_key, depth=depth)
    ordered = sorted(related)
    results: list[tuple[str, str]] = []
    remaining = budget_tokens
    if include_seed:
        doc = graph.key_to_doc.get(seed_key)
        if doc is not None:
            text = (root / doc).read_text(encoding="utf-8")
            cost = estimator.count(text)
            if cost <= remaining:
                results.append((doc, "seed"))
                remaining -= cost
    for key in ordered:
        doc = graph.key_to_doc.get(key)
        if doc is None:
            continue
        relation = ("imports" if key in graph.edges.get(seed_key, set())
                    else "imported-by")
        text = (root / doc).read_text(encoding="utf-8")
        cost = estimator.count(text)
        if cost <= remaining:
            results.append((doc, relation))
            remaining -= cost
    return results, graph.warnings


class DependencyFilesSource(ContextSource):
    """Compiler source including import-neighbours of a seed file (Slice 059).

    The seed is taken from ``ctx.config["context_seed_file"]`` when set;
    otherwise the source yields nothing (it never guesses a seed).
    """

    def __init__(self, *, priority: int = 5, enabled: bool = True,
                 depth: int = 1, budget_tokens: int = 2000) -> None:
        self.name = "dependency-files"
        self.priority = priority
        self.enabled = enabled
        self.depth = depth
        self.budget_tokens = budget_tokens

    def collect(self, ctx) -> list[ContextBlock]:
        seed = (ctx.config or {}).get("context_seed_file")
        if not seed:
            return []
        try:
            selected, warnings = select_related(
                seed, ctx.workspace, depth=self.depth,
                budget_tokens=self.budget_tokens)
        except Exception as exc:
            logging.getLogger(__name__).warning("dependency-files: %s", exc)
            return []
        for warning in warnings:
            logging.getLogger(__name__).warning("dependency-files: %s", warning)
        root = ctx.workspace
        blocks = []
        for doc_id, relation in selected:
            text = (root / doc_id).read_text(encoding="utf-8")
            blocks.append(ContextBlock(
                name=f"deps:{doc_id}",
                content=f"--- {doc_id} ({relation}) ---\n{text}",
                priority=self.priority,
                provenance={"doc_id": doc_id, "relation": relation}))
        return blocks
