"""The Symbol Graph (All-Features roadmap slice M-046).

Part III — Code Intelligence. M-044's repo map knows files;
this slice knows symbols: definitions, references, imports,
and call edges extracted per language, as queryable data the
map, the search (M-047/M-058), and Part VI's task splitting
can stand on.

What already shipped, and what this slice adds:

* M-043 (``mythic_agent.core.tree_sitter_foundation``) parses
  source grammar-backed (or through Python's stdlib ``ast``
  fallback) and extracts definitions per language, driven by
  the language catalogue's own ``definition_nodes``.
* The elder ``mythic_agent.context.symbols`` index extracts
  Python def/class symbols per file; the elder
  ``mythic_agent.context.deps`` knows Python file-level
  import dependencies. Neither is a per-symbol graph.
* M-044's map builds its reference graph crudely from name
  mentions (a file references every file whose defined
  symbols it mentions). True per-symbol sites — where a name
  is defined, where it is used, what it calls, what a file
  imports — did not exist as data until this slice.
* This slice is that graph, in ``mythic_agent/context/
  symbol_graph.py``, beside the map it feeds.

The build, and the honesty rules pinned by its tests:

* **Definitions come from the M-043 parses, never a second
  extractor.** Each definition carries its file, name, kind,
  language, line, and the parse backend that served its file.
* **Edges come from the grammars' own node vocabularies.**
  For a tree-sitter parse, call nodes (``call`` /
  ``call_expression`` / ``new_expression``), import nodes
  (``import_statement`` / ``import_from_statement`` /
  ``use_declaration`` / ``import_declaration``), and
  identifier leaves are read off the M-043 parse tree; the
  node text is recovered by slicing the source at the node's
  own byte span. For Python's ``python_ast`` fallback
  backend, the same four edge kinds are read from the stdlib
  ``ast`` tree — the fallback's own road, exactly as
  ``context/symbols.py`` and ``context/deps.py`` walk it —
  and the graph names that backend on every definition.
* **Resolution is name-based, and says so.** A reference is
  an identifier occurrence whose name matches a definition
  somewhere in the graph (parameter names and definition
  name sites are bindings, not references; import subtrees
  are imports, not references). A call edge runs from the
  enclosing definition (or ``<module>``) to the callee name.
  Every reference and call carries the definition sites its
  name resolves to — all of them, when a name is defined
  more than once; ambiguity is recorded, never silently
  picked. Type-true resolution is the LSP road (M-050);
  nothing here dresses a name match as a type proof.
* **Imports carry the module as written**, plus its resolved
  workspace file where a road exists: Python dotted modules
  (absolute and relative) and JavaScript/TypeScript relative
  paths resolve against the scanned files; Go package paths
  and Rust ``use`` paths name packages/crates, not workspace
  files, and honestly record ``resolved_path=None``.
* **Nothing is invented for an ungraphed file.** A file that
  cannot be parsed honestly — Mojo, whose catalogue entry is
  grammar-less; a language whose grammar is not installed;
  broken Python on the ``ast`` fallback; an oversized or
  binary file — lands in ``skipped`` with the reason. A file
  the grammar parses with errors still graphs, with the
  error named in ``warnings``.
* **The capability table is part of the graph.** Every
  catalogued language reports which edge kinds this slice
  extracts for it (all four for the five grammar-backed
  languages; none for Mojo, with the reason) — a consumer
  can ask what the graph knows before trusting it.
"""

from __future__ import annotations

__all__ = [
    "EDGE_KINDS",
    "MAX_GRAPH_FILE_BYTES",
    "MAX_GRAPH_FILES",
    "MODULE_CALLER",
    "SYMBOL_GRAPH_SLICE",
    "CallEdge",
    "FileGraph",
    "GraphSkippedFile",
    "ImportEdge",
    "LanguageCapability",
    "ReferenceSite",
    "SymbolDefinition",
    "SymbolGraph",
    "build_symbol_graph",
    "extract_file_graph",
    "language_capabilities",
]

import ast as _ast
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..core.tree_sitter_foundation import (
    LanguageCatalog,
    ParseNode,
    ParseUnavailableError,
    ParsedSource,
    detect_language,
    load_catalog,
    parse_source,
)
from ..core.workspace import assert_within_workspace, canonical_workspace_root

#: The slice that owns this module.
SYMBOL_GRAPH_SLICE = "M-046"

#: The edge kinds this slice extracts, in roadmap order.
EDGE_KINDS = ("definitions", "references", "imports", "calls")

#: The caller name recorded for a call made outside any definition.
MODULE_CALLER = "<module>"

#: Scan bounds, named like the repo map's own bounds.
MAX_GRAPH_FILES = 500
MAX_GRAPH_FILE_BYTES = 262_144

_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv",
              "dist", "build", ".hg", ".svn"}

#: Grammar node types that introduce an import, per language.
_IMPORT_NODES: Dict[str, Tuple[str, ...]] = {
    "python": ("import_statement", "import_from_statement"),
    "javascript": ("import_statement",),
    "typescript": ("import_statement",),
    "rust": ("use_declaration",),
    "go": ("import_declaration",),
}

#: Grammar node types that are a call, per language.
_CALL_NODES: Dict[str, Tuple[str, ...]] = {
    "python": ("call",),
    "javascript": ("call_expression", "new_expression"),
    "typescript": ("call_expression", "new_expression"),
    "rust": ("call_expression",),
    "go": ("call_expression",),
}

#: Grammar leaf types that carry a name.
_IDENTIFIER_TYPES = (
    "identifier", "type_identifier", "field_identifier",
    "property_identifier", "package_identifier",
)

#: Grammar containers whose ``identifier`` children are bindings
#: (parameter names), not references. Other identifier kinds
#: inside them (a type annotation's ``type_identifier``) still
#: count as references.
_PARAMETER_CONTAINERS = (
    "parameters", "formal_parameters", "parameter_list",
    "parameter_declaration", "required_parameter",
    "optional_parameter",
)


@dataclass(frozen=True)
class LanguageCapability:
    """Which edge kinds the graph extracts for one language."""

    language: str
    kinds: Tuple[str, ...]
    note: str

    def record(self) -> Dict[str, object]:
        """This capability as a plain mapping."""
        return {"language": self.language, "kinds": list(self.kinds),
                "note": self.note}


@dataclass(frozen=True)
class SymbolDefinition:
    """One definition site in the graph, from an M-043 parse."""

    path: str
    name: str
    kind: str
    language: str
    line: int
    column: int
    backend: str

    @property
    def id(self) -> str:
        """This site's stable id: ``path:line:name``."""
        return f"{self.path}:{self.line}:{self.name}"

    def record(self) -> Dict[str, object]:
        """This definition as a plain mapping."""
        return {
            "id": self.id, "path": self.path, "name": self.name,
            "kind": self.kind, "language": self.language,
            "line": self.line, "column": self.column,
            "backend": self.backend,
        }


@dataclass(frozen=True)
class ReferenceSite:
    """One identifier occurrence matching a defined name.

    ``resolved_to`` carries the ids of every definition with
    this name in the graph — name-based resolution, recorded
    with all its ambiguity (see the module docstring).
    """

    path: str
    name: str
    line: int
    column: int
    enclosing: str
    resolved_to: Tuple[str, ...]

    def record(self) -> Dict[str, object]:
        """This reference as a plain mapping."""
        return {
            "path": self.path, "name": self.name, "line": self.line,
            "column": self.column, "enclosing": self.enclosing,
            "resolved_to": list(self.resolved_to),
        }


@dataclass(frozen=True)
class ImportEdge:
    """One import in one file: the module as written, and the
    workspace file it resolves to where a road exists."""

    path: str
    module: str
    line: int
    resolved_path: Optional[str]

    def record(self) -> Dict[str, object]:
        """This import as a plain mapping."""
        return {
            "path": self.path, "module": self.module, "line": self.line,
            "resolved_path": self.resolved_path,
        }


@dataclass(frozen=True)
class CallEdge:
    """One call: from the enclosing definition (or
    ``<module>``) to the callee name, with the definition
    sites that name resolves to (empty when unresolved)."""

    path: str
    caller: str
    callee: str
    line: int
    column: int
    resolved_to: Tuple[str, ...]

    def record(self) -> Dict[str, object]:
        """This call as a plain mapping."""
        return {
            "path": self.path, "caller": self.caller,
            "callee": self.callee, "line": self.line,
            "column": self.column, "resolved_to": list(self.resolved_to),
        }


@dataclass(frozen=True)
class GraphSkippedFile:
    """One candidate file the graph honestly could not parse."""

    path: str
    reason: str

    def record(self) -> Dict[str, object]:
        """This skip as a plain mapping."""
        return {"path": self.path, "reason": self.reason}


@dataclass(frozen=True)
class FileGraph:
    """One file's extracted graph, resolved against a given
    definition index (its own file's, when extracted alone)."""

    path: str
    language: str
    backend: str
    definitions: Tuple[SymbolDefinition, ...]
    references: Tuple[ReferenceSite, ...]
    imports: Tuple[ImportEdge, ...]
    calls: Tuple[CallEdge, ...]

    def record(self) -> Dict[str, object]:
        """This file graph as a plain mapping."""
        return {
            "path": self.path, "language": self.language,
            "backend": self.backend,
            "definitions": [d.record() for d in self.definitions],
            "references": [r.record() for r in self.references],
            "imports": [i.record() for i in self.imports],
            "calls": [c.record() for c in self.calls],
        }


def language_capabilities(
    catalog: Optional[LanguageCatalog] = None,
) -> Tuple[LanguageCapability, ...]:
    """The edge kinds extracted per catalogued language.

    Grammar-backed languages carry all four kinds; a
    grammar-less language (Mojo) carries none, with the
    catalogue's own reason — the graph never claims an edge
    kind it cannot extract.
    """
    catalog = catalog or load_catalog()
    out: List[LanguageCapability] = []
    for entry in catalog.languages:
        if entry.status == "grammar-declared":
            out.append(LanguageCapability(
                language=entry.language, kinds=EDGE_KINDS,
                note="definitions from the M-043 parse; references, "
                     "imports, and calls from the grammar's node "
                     "vocabularies (Python's ast fallback backend "
                     "extracts the same four kinds)" if entry.language
                     == "python" else
                     "definitions from the M-043 parse; references, "
                     "imports, and calls from the grammar's node "
                     "vocabularies"))
        else:
            out.append(LanguageCapability(
                language=entry.language, kinds=(),
                note="no grammar package is published for this "
                     "language; no edges are extracted or invented "
                     "for it (its first-class road is M-064)"))
    return tuple(out)


@dataclass(frozen=True)
class SymbolGraph:
    """One built graph over a workspace: every definition,
    reference, import, and call the build honestly extracted,
    plus everything it skipped and why."""

    workspace: str
    definitions: Tuple[SymbolDefinition, ...]
    references: Tuple[ReferenceSite, ...]
    imports: Tuple[ImportEdge, ...]
    calls: Tuple[CallEdge, ...]
    skipped: Tuple[GraphSkippedFile, ...]
    warnings: Tuple[str, ...]
    files_seen: int
    capabilities: Tuple[LanguageCapability, ...]

    # -- per-symbol queries (the map / search / splitting road) --

    def definitions_named(self, name: str) -> Tuple[SymbolDefinition, ...]:
        """Every definition of *name* (case-insensitive)."""
        key = (name or "").lower()
        return tuple(d for d in self.definitions if d.name.lower() == key)

    def definitions_in(self, path: str) -> Tuple[SymbolDefinition, ...]:
        """Every definition in the file at *path*."""
        return tuple(d for d in self.definitions if d.path == path)

    def references_to(self, name: str) -> Tuple[ReferenceSite, ...]:
        """Every reference site whose name matches *name*."""
        key = (name or "").lower()
        return tuple(r for r in self.references if r.name.lower() == key)

    def callers_of(self, name: str) -> Tuple[CallEdge, ...]:
        """Every call edge whose callee matches *name*."""
        key = (name or "").lower()
        return tuple(c for c in self.calls if c.callee.lower() == key)

    def callees_of(self, name: str) -> Tuple[CallEdge, ...]:
        """Every call edge made from inside a definition
        named *name* (or from ``<module>``)."""
        key = (name or "").lower()
        return tuple(c for c in self.calls if c.caller.lower() == key)

    def unresolved_calls(self) -> Tuple[CallEdge, ...]:
        """Call edges whose callee no definition in the graph
        carries — recorded, never hidden."""
        return tuple(c for c in self.calls if not c.resolved_to)

    def imports_of(self, path: str) -> Tuple[ImportEdge, ...]:
        """Every import edge in the file at *path*."""
        return tuple(i for i in self.imports if i.path == path)

    def file_edges(self) -> Dict[str, Tuple[str, ...]]:
        """Derived file dependencies, for the map and for
        Part VI's task splitting: a file points at every other
        file it imports (resolved), references a definition
        in, or calls a definition in."""
        defs_by_id = {d.id: d for d in self.definitions}
        edges: Dict[str, set] = {}
        paths = {d.path for d in self.definitions}
        paths.update(i.path for i in self.imports)
        paths.update(r.path for r in self.references)
        paths.update(c.path for c in self.calls)
        for path in paths:
            edges[path] = set()
        for edge in self.imports:
            if edge.resolved_path and edge.resolved_path != edge.path:
                edges[edge.path].add(edge.resolved_path)
        for site in self.references:
            for target in site.resolved_to:
                owner = defs_by_id[target].path
                if owner != site.path:
                    edges[site.path].add(owner)
        for edge in self.calls:
            for target in edge.resolved_to:
                owner = defs_by_id[target].path
                if owner != edge.path:
                    edges[edge.path].add(owner)
        return {path: tuple(sorted(edges[path])) for path in sorted(edges)}

    def record(self) -> Dict[str, object]:
        """This graph as a plain mapping."""
        return {
            "workspace": self.workspace,
            "definitions": [d.record() for d in self.definitions],
            "references": [r.record() for r in self.references],
            "imports": [i.record() for i in self.imports],
            "calls": [c.record() for c in self.calls],
            "skipped": [s.record() for s in self.skipped],
            "warnings": list(self.warnings),
            "files_seen": self.files_seen,
            "capabilities": [c.record() for c in self.capabilities],
            "file_edges": {k: list(v)
                           for k, v in self.file_edges().items()},
        }


# ---------------------------------------------------------------------------
# per-file extraction
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class _RawSite:
    name: str
    line: int
    column: int
    enclosing: str


@dataclass(frozen=True)
class _RawImport:
    module: str
    line: int


@dataclass(frozen=True)
class _RawFile:
    language: str
    backend: str
    definitions: Tuple[SymbolDefinition, ...]
    references: Tuple[_RawSite, ...]
    imports: Tuple[_RawImport, ...]
    calls: Tuple[_RawSite, ...]  # name = callee, enclosing = caller


def _node_text(raw: bytes, node: ParseNode) -> str:
    return raw[node.start_byte:node.end_byte].decode(
        "utf-8", errors="replace")


def _enclosing_for(
    spans: Tuple[Tuple[Tuple[int, int], Tuple[int, int], str], ...],
    point: Tuple[int, int],
) -> str:
    """The innermost definition whose span contains *point*."""
    best: Optional[str] = None
    best_key: Optional[Tuple[Tuple[int, int], Tuple[int, int]]] = None
    for start, end, name in spans:
        if start <= point < end:
            # Innermost = latest start, then earliest end.
            key = (start, end)
            if best_key is None or start > best_key[0] or (
                    start == best_key[0] and end < best_key[1]):
                best, best_key = name, key
    return best if best is not None else MODULE_CALLER


def _definition_name_bytes(
    parsed: ParsedSource, raw: bytes,
    definition_types: Dict[str, str],
) -> set:
    """Byte offsets of definition *name* sites in a tree parse.

    A definition node (a node type the catalogue maps to a
    definition kind) contributes the first identifier leaf
    whose text is the name the foundation extracted for the
    definition starting at that node. Those sites are
    bindings, not references.
    """
    by_start = {d.start_point: d for d in parsed.definitions}
    marked: set = set()

    def visit(node: ParseNode) -> None:
        if node.type in definition_types:
            definition = by_start.get(node.start_point)
            if definition is not None:
                for leaf in node.walk():
                    if leaf.type in _IDENTIFIER_TYPES and \
                            _node_text(raw, leaf) == definition.name:
                        marked.add(leaf.start_byte)
                        break
        for child in node.children:
            visit(child)

    visit(parsed.root)
    return marked


def _binding_bytes(parsed: ParsedSource, raw: bytes) -> set:
    """Byte offsets of variable-binding name sites (JS/TS
    ``variable_declarator`` first names) — bindings, like
    definition names, are not references."""
    marked: set = set()

    def visit(node: ParseNode) -> None:
        if node.type == "variable_declarator" and node.children:
            first = node.children[0]
            if first.type in _IDENTIFIER_TYPES:
                marked.add(first.start_byte)
        for child in node.children:
            visit(child)

    visit(parsed.root)
    return marked


def _callee_of(node: ParseNode, raw: bytes) -> Optional[ParseNode]:
    """The named callee leaf of a call node, or None when the
    callee has no name (a call of a call result, a subscript…)."""
    for fn in node.children:
        if fn.type in ("arguments", "argument_list"):
            continue
        if fn.type in _IDENTIFIER_TYPES:
            return fn
        leaves = [n for n in fn.walk() if n.type in _IDENTIFIER_TYPES]
        if leaves:
            return leaves[-1]
    return None


def _import_modules(language: str, node: ParseNode, raw: bytes) -> List[str]:
    """The module strings one import node names, as written."""
    text = _node_text(raw, node).strip()
    if language == "python":
        if node.type == "import_from_statement":
            match = re.match(r"from\s+(.+?)\s+import\b", text, re.DOTALL)
            return [match.group(1).strip()] if match else []
        rest = text[len("import"):].strip()
        modules = []
        for part in rest.split(","):
            module = part.split(" as ")[0].strip()
            if module:
                modules.append(module)
        return modules
    if language in ("javascript", "typescript"):
        for leaf in node.walk():
            if leaf.type == "string":
                value = _node_text(raw, leaf).strip()
                if len(value) >= 2 and value[0] in "'\"`":
                    return [value[1:-1]]
                return [value]
        return []
    if language == "rust":
        body = text[len("use"):].strip().rstrip(";").strip()
        return [body] if body else []
    if language == "go":
        modules = []
        for leaf in node.walk():
            if leaf.type in ("interpreted_string_literal",
                             "raw_string_literal"):
                value = _node_text(raw, leaf).strip()
                if len(value) >= 2:
                    modules.append(value[1:-1])
        return modules
    return []


def _extract_tree(
    path: str, parsed: ParsedSource, source: str,
    definition_types: Dict[str, str],
) -> _RawFile:
    raw = source.encode("utf-8")
    language = parsed.language
    definitions = tuple(
        SymbolDefinition(
            path=path, name=d.name, kind=d.kind, language=d.language,
            line=d.start_point[0] + 1, column=d.start_point[1],
            backend=parsed.backend)
        for d in parsed.definitions)
    spans = tuple(
        (d.start_point, d.end_point, d.name) for d in parsed.definitions)
    skip_bytes = _definition_name_bytes(parsed, raw, definition_types)
    skip_bytes |= _binding_bytes(parsed, raw)
    import_nodes = set(_IMPORT_NODES.get(language, ()))
    call_nodes = set(_CALL_NODES.get(language, ()))
    references: List[_RawSite] = []
    imports: List[_RawImport] = []
    calls: List[_RawSite] = []

    def visit(node: ParseNode, in_params: bool) -> None:
        if node.type == "package_clause":
            # A package declaration names the file's own package,
            # not a use of any symbol (Go's ``package main`` is
            # not a reference to a function named main).
            return
        if node.type in import_nodes:
            for module in _import_modules(language, node, raw):
                imports.append(_RawImport(
                    module=module, line=node.start_point[0] + 1))
            return
        in_params = in_params or node.type in _PARAMETER_CONTAINERS
        if node.type in call_nodes:
            callee = _callee_of(node, raw)
            if callee is not None:
                point = callee.start_point
                calls.append(_RawSite(
                    name=_node_text(raw, callee),
                    line=point[0] + 1, column=point[1],
                    enclosing=_enclosing_for(spans, point)))
        if node.type in _IDENTIFIER_TYPES:
            if node.start_byte not in skip_bytes and not (
                    in_params and node.type == "identifier"):
                point = node.start_point
                references.append(_RawSite(
                    name=_node_text(raw, node),
                    line=point[0] + 1, column=point[1],
                    enclosing=_enclosing_for(spans, point)))
        for child in node.children:
            visit(child, in_params)

    visit(parsed.root, False)
    return _RawFile(
        language=language, backend=parsed.backend,
        definitions=definitions,
        references=tuple(references), imports=tuple(imports),
        calls=tuple(calls))


def _extract_python_ast(path: str, parsed: ParsedSource,
                         source: str) -> _RawFile:
    """The ast fallback backend's extraction (see docstring).

    Raises :class:`SyntaxError` for unparseable source, via
    the foundation parse that produced *parsed* — by the time
    this runs the parse has already succeeded, so the walk
    below cannot fail on syntax.
    """
    tree = _ast.parse(source)
    definitions = tuple(
        SymbolDefinition(
            path=path, name=d.name, kind=d.kind, language=d.language,
            line=d.start_point[0] + 1, column=d.start_point[1],
            backend=parsed.backend)
        for d in parsed.definitions)
    references: List[_RawSite] = []
    imports: List[_RawImport] = []
    calls: List[_RawSite] = []

    def enclosing(stack: List[str]) -> str:
        return stack[-1] if stack else MODULE_CALLER

    def visit(node: _ast.AST, stack: List[str]) -> None:
        if isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef,
                             _ast.ClassDef)):
            inner = stack + [node.name]
            for child in _ast.iter_child_nodes(node):
                visit(child, inner)
            return
        if isinstance(node, _ast.Import):
            for alias in node.names:
                imports.append(_RawImport(
                    module=alias.name, line=node.lineno))
            return
        if isinstance(node, _ast.ImportFrom):
            module = "." * node.level + (node.module or "")
            imports.append(_RawImport(module=module, line=node.lineno))
            return
        if isinstance(node, _ast.Call):
            callee: Optional[str] = None
            if isinstance(node.func, _ast.Name):
                callee = node.func.id
            elif isinstance(node.func, _ast.Attribute):
                callee = node.func.attr
            if callee is not None:
                calls.append(_RawSite(
                    name=callee, line=node.lineno,
                    column=node.col_offset, enclosing=enclosing(stack)))
        if isinstance(node, _ast.Name) and isinstance(node.ctx, _ast.Load):
            references.append(_RawSite(
                name=node.id, line=node.lineno, column=node.col_offset,
                enclosing=enclosing(stack)))
        if isinstance(node, _ast.Attribute):
            references.append(_RawSite(
                name=node.attr, line=node.lineno,
                column=node.col_offset, enclosing=enclosing(stack)))
        for child in _ast.iter_child_nodes(node):
            visit(child, stack)

    visit(tree, [])
    return _RawFile(
        language="python", backend=parsed.backend,
        definitions=definitions, references=tuple(references),
        imports=tuple(imports), calls=tuple(calls))


def _extract_raw(
    path: str, language: str, source: str,
    catalog: LanguageCatalog,
) -> _RawFile:
    parsed = parse_source(language, source, catalog=catalog)
    if parsed.backend == "python_ast":
        return _extract_python_ast(path, parsed, source)
    entry = catalog.language(language)
    return _extract_tree(
        path, parsed, source, dict(entry.definition_nodes))


def _resolve_raw(
    raw_file: _RawFile, path: str,
    index: Dict[str, Tuple[SymbolDefinition, ...]],
    files: set, root: Optional[Path],
) -> FileGraph:
    """Resolve one raw file's sites against a definition index."""
    def resolved(name: str) -> Tuple[str, ...]:
        return tuple(d.id for d in index.get(name.lower(), ()))

    references = tuple(sorted(
        (ReferenceSite(
            path=path, name=site.name, line=site.line,
            column=site.column, enclosing=site.enclosing,
            resolved_to=resolved(site.name))
         for site in raw_file.references
         if site.name.lower() in index),
        key=lambda r: (r.line, r.column, r.name)))
    calls = tuple(sorted(
        (CallEdge(
            path=path, caller=site.enclosing, callee=site.name,
            line=site.line, column=site.column,
            resolved_to=resolved(site.name))
         for site in raw_file.calls),
        key=lambda c: (c.line, c.column, c.callee)))
    imports = tuple(sorted(
        (ImportEdge(
            path=path, module=item.module, line=item.line,
            resolved_path=_resolve_import(
                raw_file.language, path, item.module, files, root))
         for item in raw_file.imports),
        key=lambda i: (i.line, i.module)))
    return FileGraph(
        path=path, language=raw_file.language, backend=raw_file.backend,
        definitions=tuple(sorted(
            raw_file.definitions, key=lambda d: (d.line, d.column, d.name))),
        references=references, imports=imports, calls=calls)


def _resolve_import(
    language: str, importer: str, module: str,
    files: set, root: Optional[Path],
) -> Optional[str]:
    """The workspace file *module* names from *importer*, or
    None where no road exists (see the module docstring)."""
    if root is None:
        return None
    if language == "python":
        level = len(module) - len(module.lstrip("."))
        dotted = module.lstrip(".")
        base = Path(importer).parent
        for _ in range(max(level - 1, 0)):
            base = base.parent
        parts = [p for p in dotted.split(".") if p]
        if level == 0:
            base = Path("")
        for candidate in _module_candidates(base, parts):
            if candidate in files:
                return candidate
        return None
    if language in ("javascript", "typescript"):
        if not module.startswith("."):
            return None
        base = Path(importer).parent / module
        candidates = [str(base)]
        for ext in (".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx"):
            candidates.append(str(base) + ext)
            candidates.append(str(base / "index") + ext)
        # A written .js specifier may name a .ts source.
        if module.endswith(".js"):
            candidates.append(str(base)[:-3] + ".ts")
            candidates.append(str(base)[:-3] + ".tsx")
        for candidate in candidates:
            normalised = str(Path(candidate))
            if normalised in files:
                return normalised
        return None
    return None


def _module_candidates(base: Path, parts: List[str]) -> List[str]:
    if not parts:
        return [str(base / "__init__.py")] if str(base) != "." else [
            "__init__.py"]
    joined = base.joinpath(*parts) if str(base) not in ("", ".") else \
        Path(*parts)
    return [str(joined.with_suffix(".py")), str(joined / "__init__.py")]


def extract_file_graph(
    path: str, language: str, source: str,
    catalog: Optional[LanguageCatalog] = None,
) -> FileGraph:
    """One source's graph, resolved against its own definitions.

    *path* is the workspace-relative name the sites carry.
    Imports record ``resolved_path=None`` — resolution needs
    the workspace, which :func:`build_symbol_graph` supplies.
    Raises the foundation's own errors: ParseUnavailableError
    for a grammar-less or grammar-missing language, SyntaxError
    for broken Python on the ast fallback, KeyError for an
    uncatalogued language.
    """
    catalog = catalog or load_catalog()
    raw_file = _extract_raw(path, language, source, catalog)
    index: Dict[str, List[SymbolDefinition]] = {}
    for definition in raw_file.definitions:
        index.setdefault(definition.name.lower(), []).append(definition)
    frozen = {k: tuple(v) for k, v in index.items()}
    return _resolve_raw(raw_file, path, frozen, set(), None)


# ---------------------------------------------------------------------------
# the workspace build
# ---------------------------------------------------------------------------

def build_symbol_graph(
    workspace: Path | str,
    *,
    catalog: Optional[LanguageCatalog] = None,
    max_files: int = MAX_GRAPH_FILES,
    max_file_bytes: int = MAX_GRAPH_FILE_BYTES,
) -> SymbolGraph:
    """Build the symbol graph for *workspace*.

    Files are discovered in deterministic (sorted) order among
    the M-043 catalogue's extensions; each is parsed and
    extracted through the foundation (never a second parser),
    then every site is resolved against the whole graph's
    definition index and every import against the scanned
    file set.
    """
    if max_files <= 0:
        raise ValueError("max_files must be positive")
    if max_file_bytes <= 0:
        raise ValueError("max_file_bytes must be positive")
    root = canonical_workspace_root(workspace)
    catalog = catalog or load_catalog()

    raw_files: Dict[str, _RawFile] = {}
    skipped: List[GraphSkippedFile] = []
    warnings: List[str] = []
    files_seen = 0
    capped = False
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        if capped:
            break
        dirnames[:] = sorted(
            d for d in dirnames
            if d not in _SKIP_DIRS and not d.startswith("."))
        for name in sorted(filenames):
            language = detect_language(name, catalog)
            if language is None:
                continue
            if files_seen >= max_files:
                warnings.append(
                    f"symbol graph file cap reached ({max_files}); "
                    "later files were not scanned")
                capped = True
                break
            candidate = Path(dirpath) / name
            try:
                resolved = assert_within_workspace(root, candidate)
            except Exception as exc:
                warnings.append(f"blocked {candidate}: {exc}")
                continue
            rel = str(resolved.relative_to(root))
            files_seen += 1
            try:
                raw = resolved.read_bytes()
            except OSError as exc:
                skipped.append(GraphSkippedFile(
                    rel, f"unreadable: {exc}"))
                continue
            if len(raw) > max_file_bytes:
                skipped.append(GraphSkippedFile(
                    rel, f"too large for the graph ({len(raw)} bytes "
                         f"> {max_file_bytes})"))
                continue
            if b"\x00" in raw:
                skipped.append(GraphSkippedFile(rel, "binary file"))
                continue
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                skipped.append(GraphSkippedFile(rel, "not utf-8 text"))
                continue
            try:
                parsed = parse_source(language, text, catalog=catalog)
            except ParseUnavailableError as exc:
                skipped.append(GraphSkippedFile(rel, str(exc)))
                continue
            except SyntaxError as exc:
                skipped.append(GraphSkippedFile(
                    rel, f"unparseable ({language} backend): {exc}"))
                continue
            if parsed.has_error:
                warnings.append(f"{rel}: parsed with errors")
            if parsed.backend == "python_ast":
                raw_files[rel] = _extract_python_ast(rel, parsed, text)
            else:
                entry = catalog.language(language)
                raw_files[rel] = _extract_tree(
                    rel, parsed, text, dict(entry.definition_nodes))

    index_lists: Dict[str, List[SymbolDefinition]] = {}
    for raw_file in raw_files.values():
        for definition in raw_file.definitions:
            index_lists.setdefault(
                definition.name.lower(), []).append(definition)
    index = {
        key: tuple(sorted(value, key=lambda d: (d.path, d.line, d.name)))
        for key, value in index_lists.items()
    }
    files = set(raw_files) | {s.path for s in skipped}

    definitions: List[SymbolDefinition] = []
    references: List[ReferenceSite] = []
    imports: List[ImportEdge] = []
    calls: List[CallEdge] = []
    for rel in sorted(raw_files):
        file_graph = _resolve_raw(
            raw_files[rel], rel, index, files, root)
        definitions.extend(file_graph.definitions)
        references.extend(file_graph.references)
        imports.extend(file_graph.imports)
        calls.extend(file_graph.calls)
    return SymbolGraph(
        workspace=str(root),
        definitions=tuple(sorted(
            definitions, key=lambda d: (d.path, d.line, d.name))),
        references=tuple(sorted(
            references, key=lambda r: (r.path, r.line, r.column, r.name))),
        imports=tuple(sorted(
            imports, key=lambda i: (i.path, i.line, i.module))),
        calls=tuple(sorted(
            calls, key=lambda c: (c.path, c.line, c.column, c.callee))),
        skipped=tuple(skipped), warnings=tuple(warnings),
        files_seen=files_seen,
        capabilities=language_capabilities(catalog))
