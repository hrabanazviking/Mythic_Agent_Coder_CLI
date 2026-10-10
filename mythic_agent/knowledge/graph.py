"""Project knowledge graphs (Slice 41).

``KnowledgeGraph`` stores entities (symbols, modules, concepts) and the
relations between them, answers "how does X work?" style queries, and
persists to JSON. ``build_graph_from_index`` constructs one from the
AST symbol index (:mod:`mythic_agent.tools.code_index`).
"""


from __future__ import annotations

__all__ = [
    "Any",
    "CALLS",
    "CONTAINS",
    "DEFINES_METHOD",
    "IMPORTS",
    "KnowledgeGraph",
    "LOCATED_IN",
    "Optional",
    "Path",
    "build_graph_from_index",
    "build_graph_from_project",
    "deque",
]

import json
import threading
from collections import deque
from pathlib import Path
from typing import Any, Optional

try:  # Optional: richer graphs when the symbol index is available.
    from mythic_agent.tools.code_index import SymbolIndex
except Exception:  # pragma: no cover - defensive import
    SymbolIndex = None  # type: ignore[assignment,misc]

__all__ = ["KnowledgeGraph", "build_graph_from_index", "build_graph_from_project"]

# Relation labels used when building graphs from the code index.
CONTAINS = "contains"            # module -> symbol defined in it
DEFINES_METHOD = "defines"      # class -> method
IMPORTS = "imports"             # module -> imported name
CALLS = "calls"                 # function -> symbol referenced in its body
LOCATED_IN = "located_in"       # symbol -> file path


class KnowledgeGraph:
    """A directed, labeled multigraph of project knowledge.

    Entities have a ``name`` and a ``type`` (e.g. ``"module"``,
    ``"function"``, ``"class"``, ``"concept"``). Relations are labeled
    edges ``(a) -[rel]-> (b)``.
    """

    def __init__(self) -> None:
        self._entities: dict[str, dict[str, Any]] = {}
        self._edges: dict[str, list[tuple[str, str]]] = {}
        self._lock = threading.Lock()

    # -- mutation --------------------------------------------------------

    def add_entity(self, name: str, type: str, **attrs: Any) -> str:
        """Add (or update) an entity; returns the entity name."""
        with self._lock:
            entity = self._entities.setdefault(name, {"name": name, "type": type})
            entity["type"] = type
            entity.update(attrs)
            self._edges.setdefault(name, [])
        return name

    def add_relation(self, a: str, b: str, rel: str) -> None:
        """Add a labeled edge from entity *a* to entity *b*.

        Both endpoints are created as untyped entities if they do not
        already exist (their type can be set later via
        :meth:`add_entity`).
        """
        with self._lock:
            self._entities.setdefault(a, {"name": a, "type": "unknown"})
            self._entities.setdefault(b, {"name": b, "type": "unknown"})
            self._edges.setdefault(a, [])
            if (b, rel) not in self._edges[a]:
                self._edges[a].append((b, rel))

    # -- lookup ----------------------------------------------------------

    def entity(self, name: str) -> Optional[dict[str, Any]]:
        """Return the attribute dict for *name*, or None."""
        with self._lock:
            ent = self._entities.get(name)
            return dict(ent) if ent is not None else None

    def relations(self, name: str) -> list[tuple[str, str, str]]:
        """Return ``(source, target, relation)`` edges touching *name*."""
        with self._lock:
            out = [(name, tgt, rel) for tgt, rel in self._edges.get(name, [])]
            incoming = [(src, name, rel)
                        for src, edges in self._edges.items()
                        for tgt, rel in edges if tgt == name]
        return out + incoming

    def entities_of_type(self, type: str) -> list[str]:
        """Return names of all entities with the given *type*."""
        with self._lock:
            return [n for n, e in self._entities.items() if e.get("type") == type]

    def neighbors(self, name: str, rel: Optional[str] = None) -> list[str]:
        """Names reachable from *name* via outgoing edges (optionally filtered)."""
        with self._lock:
            return [tgt for tgt, r in self._edges.get(name, [])
                    if rel is None or r == rel]

    def __len__(self) -> int:
        with self._lock:
            return len(self._entities)

    # -- query -----------------------------------------------------------

    def query(self, entity: str) -> dict[str, Any]:
        """Answer "how does *entity* work?" with a structured summary.

        Returns a dict with ``entity``, ``type``, ``summary`` (one-line
        human description), ``relations`` (grouped by label), and
        ``related`` (2-hop neighbor names). Raises ``KeyError`` when the
        entity is unknown.
        """
        ent = self.entity(entity)
        if ent is None:
            raise KeyError(f"unknown entity: {entity!r}")

        grouped: dict[str, list[str]] = {}
        with self._lock:
            for tgt, rel in self._edges.get(entity, []):
                grouped.setdefault(rel, []).append(tgt)
            for src, edges in self._edges.items():
                for tgt, rel in edges:
                    if tgt == entity:
                        grouped.setdefault(f"incoming:{rel}", []).append(src)

        two_hop: set[str] = set()
        with self._lock:
            one_hop = {tgt for tgt, _ in self._edges.get(entity, [])}
            for hop in one_hop:
                for tgt, _ in self._edges.get(hop, []):
                    if tgt != entity:
                        two_hop.add(tgt)

        kind = ent.get("type", "unknown")
        bits: list[str] = []
        if kind == "module":
            bits.append(f"module {entity}")
            n = len(grouped.get(CONTAINS, []))
            if n:
                bits.append(f"defines {n} symbol(s)")
        elif kind in ("function", "method", "class"):
            where = ent.get("location", "")
            bits.append(f"{kind} {entity}" + (f" at {where}" if where else ""))
            doc = ent.get("docstring", "")
            if doc:
                bits.append(f"- {doc}")
        else:
            bits.append(f"{kind}: {entity}")
        for rel, targets in sorted(grouped.items()):
            if not rel.startswith("incoming:"):
                bits.append(f"{rel} -> {', '.join(sorted(targets)[:5])}"
                            + (" ..." if len(targets) > 5 else ""))

        return {
            "entity": entity,
            "type": kind,
            "summary": "; ".join(bits),
            "relations": {k: sorted(v) for k, v in grouped.items()},
            "related": sorted(two_hop),
        }

    def explain(self, entity: str) -> str:
        """Plain-text "how does X work?" answer built on :meth:`query`."""
        q = self.query(entity)
        lines = [f"**{q['entity']}** ({q['type']}): {q['summary']}"]
        for rel, targets in sorted(q["relations"].items()):
            if not rel.startswith("incoming:"):
                lines.append(f"- {rel}: {', '.join(targets)}")
        if q["related"]:
            lines.append(f"Related: {', '.join(q['related'][:10])}")
        return "\n".join(lines)

    def architecture_summary(self) -> str:
        """One-paragraph overview of the modules and their wiring."""
        modules = self.entities_of_type("module")
        lines = [f"{len(modules)} modules, {len(self)} entities total."]
        for mod in sorted(modules):
            defined = self.neighbors(mod, CONTAINS)
            imported = self.neighbors(mod, IMPORTS)
            tail = []
            if defined:
                tail.append(f"defines {len(defined)}")
            if imported:
                tail.append(f"imports {', '.join(sorted(imported)[:6])}")
            lines.append(f"- {mod}" + (f" ({'; '.join(tail)})" if tail else ""))
        return "\n".join(lines)

    # -- persistence -----------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        with self._lock:
            return {
                "entities": {n: dict(e) for n, e in self._entities.items()},
                "edges": {s: [[t, r] for t, r in edges]
                          for s, edges in self._edges.items()},
            }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "KnowledgeGraph":
        graph = cls()
        for name, attrs in data.get("entities", {}).items():
            etype = attrs.get("type", "unknown")
            extra = {k: v for k, v in attrs.items() if k not in ("name", "type")}
            graph.add_entity(name, etype, **extra)
        for src, edges in data.get("edges", {}).items():
            for tgt, rel in edges:
                graph.add_relation(src, tgt, rel)
        return graph

    def save(self, path: str | Path) -> Path:
        """Persist the graph to *path* as JSON (parents created)."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True),
                        encoding="utf-8")
        return path

    @classmethod
    def load(cls, path: str | Path) -> "KnowledgeGraph":
        """Load a graph previously saved with :meth:`save`."""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_dict(data)


def _module_name(root: Path, path: Path) -> str:
    try:
        rel = path.resolve().relative_to(root.resolve())
    except ValueError:
        rel = path
    stem = rel.with_suffix("")
    return ".".join(stem.parts)


def build_graph_from_index(index: Any, root: Optional[str | Path] = None) -> KnowledgeGraph:
    """Build a ``KnowledgeGraph`` from a ``SymbolIndex`` (Slice 19).

    Falls back to a plain directory walk when the symbol index module is
    unavailable or *index* is None.
    """
    graph = KnowledgeGraph()
    if index is None:
        return graph

    root_path = Path(root) if root is not None else getattr(index, "root", Path("."))
    try:
        n_symbols = index.index_workspace()
    except Exception:
        n_symbols = 0

    symbol_map: dict[str, str] = {}  # symbol name -> entity key

    # Access the private file cache defensively; re-derive from files if needed.
    entries = getattr(index, "_files", {})
    for path in sorted(entries):
        module = _module_name(root_path, Path(path))
        graph.add_entity(module, "module", location=str(path))
        for sym in entries[path].symbols:
            qualified = sym.qualified or sym.name
            # Namespace by module so identically-named symbols in
            # different modules do not collide.
            key = f"{module}.{qualified}" if not qualified.startswith(module + ".") else qualified
            entity_type = {"function": "function", "method": "method",
                           "class": "class", "import": "import"}.get(sym.kind, "symbol")
            graph.add_entity(key, entity_type,
                             location=sym.location() if hasattr(sym, "location") else "",
                             docstring=getattr(sym, "docstring", ""))
            graph.add_relation(module, key, CONTAINS)
            graph.add_relation(key, str(path), LOCATED_IN)
            if sym.kind == "method":
                cls_key = ".".join(key.split(".")[:-1])
                if cls_key and cls_key != module:
                    graph.add_relation(cls_key, key, DEFINES_METHOD)
            if sym.kind == "import":
                graph.add_relation(module, key, IMPORTS)
            symbol_map.setdefault(sym.name, key)

    # Second pass: CALLS edges — parse each file's AST and link callers to
    # callees by name (simple heuristic: match call names to known symbols).
    import ast as _ast

    for path in sorted(entries):
        module = _module_name(root_path, Path(path))
        try:
            tree = _ast.parse(Path(path).read_text(encoding="utf-8", errors="replace"))
        except (SyntaxError, ValueError, OSError):
            continue

        class _CallVisitor(_ast.NodeVisitor):
            def __init__(self) -> None:
                self._stack: list[str] = []

            @property
            def _caller(self) -> Optional[str]:
                if not self._stack:
                    return None
                return module + "." + ".".join(self._stack)

            def visit_ClassDef(self, node: _ast.ClassDef) -> None:
                self._stack.append(node.name)
                self.generic_visit(node)
                self._stack.pop()

            def visit_FunctionDef(self, node: _ast.FunctionDef) -> None:
                self._stack.append(node.name)
                self.generic_visit(node)
                self._stack.pop()

            visit_AsyncFunctionDef = visit_FunctionDef

            def visit_Call(self, node: _ast.Call) -> None:
                callee: Optional[str] = None
                if isinstance(node.func, _ast.Name):
                    callee = node.func.id
                elif isinstance(node.func, _ast.Attribute):
                    callee = node.func.attr
                caller = self._caller
                if callee and caller and callee in symbol_map:
                    graph.add_relation(caller, symbol_map[callee], CALLS)
                self.generic_visit(node)

        _CallVisitor().visit(tree)

    graph.add_entity("_meta", "meta", symbols=n_symbols)
    return graph


def build_graph_from_project(root: str | Path) -> KnowledgeGraph:
    """Build a ``KnowledgeGraph`` for a project root.

    Uses :class:`mythic_agent.tools.code_index.SymbolIndex` when
    available, otherwise indexes module files directly.
    """
    root = Path(root)
    if SymbolIndex is not None:
        index = SymbolIndex(root)
        return build_graph_from_index(index, root)

    graph = KnowledgeGraph()
    for path in sorted(root.rglob("*.py")):
        module = _module_name(root, path)
        graph.add_entity(module, "module", location=str(path))
    return graph
