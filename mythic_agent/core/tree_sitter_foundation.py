"""Tree-sitter foundation (All-Features roadmap slice M-043).

Part III — Code Intelligence — opens here. The coder must
understand code, not just grep it, and grammar-backed parsing
is the floor that understanding stands on.

What ships in this slice:

* The language catalogue as data
  (``mythic_agent/data/tree_sitter_languages.yaml``): the major
  languages in roadmap order — Python first, then
  JavaScript, TypeScript, Rust, Go, and Mojo-aware — each
  grammar-backed language naming its grammar package (the
  optional ``code-intelligence`` extra in ``pyproject.toml``),
  its upstream, and its licence notice, counted from the
  packages' own wheel metadata. Mojo carries no grammar: no
  tree-sitter grammar package for Mojo is published, and the
  catalogue says so instead of inventing one.
* The parse layer in this module. When the extra is installed,
  a source parses through its real tree-sitter grammar and the
  parse is labelled ``backend="tree_sitter"``. When it is not,
  Python alone keeps parsing — through the standard library's
  :mod:`ast`, exactly the road
  ``mythic_agent.context.symbols`` already walks — and that
  parse is labelled ``backend="python_ast"``, never dressed as
  grammar-backed. Every other language without its grammar
  refuses with :class:`ParseUnavailableError`, naming the
  package to install. Availability is probed live from real
  imports (:func:`probe_availability`); nothing is claimed
  from the catalogue alone.

The tree and the definitions this layer returns
(:class:`ParseNode`, :class:`Definition`) are the shape
Part III's repo map (M-044) and symbol graph (M-046) build on:
node types, byte and point spans, and per-language definition
extraction driven by the catalogue's ``definition_nodes``
(the node types each grammar really produces), never by a
second hand list in code.
"""

from __future__ import annotations

__all__ = [
    "BACKENDS",
    "CATALOG_RESOURCE",
    "CATALOG_SCHEMA",
    "CATALOG_SLICE",
    "ROADMAP_LANGUAGES",
    "STATUSES",
    "Any",
    "Availability",
    "Definition",
    "Dict",
    "LanguageCatalog",
    "LanguageDef",
    "List",
    "Optional",
    "ParseNode",
    "ParseUnavailableError",
    "ParsedSource",
    "Tuple",
    "availability_for",
    "detect_language",
    "extract_definitions",
    "load_catalog",
    "parse_source",
    "probe_availability",
    "render_markdown",
    "validate_catalog",
]

import ast as _ast
import importlib
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource
from .validation import ValidationError

try:
    import tree_sitter as _tree_sitter
except ImportError:  # the code-intelligence extra is not installed
    _tree_sitter = None  # type: ignore[assignment]

#: Resource name of the catalogue data file inside ``mythic_agent/data``.
CATALOG_RESOURCE = "tree_sitter_languages.yaml"

#: The only schema this loader accepts.
CATALOG_SCHEMA = "mythic.tree_sitter_languages/1"

#: The slice that owns this catalogue.
CATALOG_SLICE = "M-043"

#: The languages the roadmap names for this slice, in roadmap order.
ROADMAP_LANGUAGES = ("python", "javascript", "typescript", "rust", "go", "mojo")

#: The grammar statuses a catalogue entry may carry.
STATUSES = ("grammar-declared", "no-grammar-package")

#: The parse backends a parse may honestly claim.
BACKENDS = ("tree_sitter", "python_ast")

_EXTENSION_RE = re.compile(r"^\.[a-z0-9]+$")


class ParseUnavailableError(RuntimeError):
    """No honest parse exists for this language in this environment.

    Raised when a language's grammar package is not installed
    (and it is not Python, the one language with a stdlib
    fallback), or when the catalogue records no grammar for
    the language at all. The message names the remedy where
    one exists; a parse is never invented to avoid raising.
    """


@dataclass(frozen=True)
class LanguageDef:
    """One language in the catalogue."""

    id: str
    language: str
    title: str
    extensions: Tuple[str, ...]
    status: str
    grammar_package: Optional[str]
    grammar_module: Optional[str]
    grammar_factory: Optional[str]
    grammar_version_seen: Optional[str]
    licence: Optional[str]
    upstream: Optional[str]
    licence_notice: Optional[str]
    definition_nodes: Tuple[Tuple[str, str], ...]
    notes: str

    def definition_kind(self, node_type: str) -> Optional[str]:
        """The definition kind for *node_type*, or None."""
        for known, kind in self.definition_nodes:
            if known == node_type:
                return kind
        return None


@dataclass(frozen=True)
class LanguageCatalog:
    """The validated tree-sitter language catalogue."""

    source_note: str
    extension_rule: str
    core_package: str
    core_import_name: str
    core_licence: str
    core_upstream: str
    languages: Tuple[LanguageDef, ...]

    def names(self) -> Tuple[str, ...]:
        """Every catalogued language, in catalogue order."""
        return tuple(entry.language for entry in self.languages)

    def language(self, name: str) -> LanguageDef:
        """The entry for *name* (KeyError when uncatalogued)."""
        key = (name or "").strip().lower()
        for entry in self.languages:
            if entry.language == key:
                return entry
        raise KeyError(f"no language {name!r}")

    def languages_with(self, status: str) -> Tuple[LanguageDef, ...]:
        """Every entry carrying *status*, in catalogue order."""
        return tuple(e for e in self.languages if e.status == status)

    def for_extension(self, extension: str) -> Optional[LanguageDef]:
        """The entry claiming *extension* (e.g. ``.py``), or None."""
        key = (extension or "").strip().lower()
        if not key.startswith("."):
            key = "." + key
        for entry in self.languages:
            if key in entry.extensions:
                return entry
        return None


@dataclass(frozen=True)
class Availability:
    """One language's live grammar availability, probed not assumed."""

    language: str
    available: bool
    detail: str


@dataclass(frozen=True)
class ParseNode:
    """One node of a parse tree, on either backend."""

    type: str
    start_byte: int
    end_byte: int
    start_point: Tuple[int, int]
    end_point: Tuple[int, int]
    children: Tuple["ParseNode", ...] = ()

    def walk(self) -> Tuple["ParseNode", ...]:
        """This node and every descendant, in document order."""
        out: List[ParseNode] = [self]
        for child in self.children:
            out.extend(child.walk())
        return tuple(out)


@dataclass(frozen=True)
class Definition:
    """One definition extracted from a parse."""

    name: str
    kind: str
    language: str
    node_type: str
    start_point: Tuple[int, int]
    end_point: Tuple[int, int]


@dataclass(frozen=True)
class ParsedSource:
    """One parsed source: its tree, backend, and error truth."""

    language: str
    backend: str
    root: ParseNode
    has_error: bool
    definitions: Tuple[Definition, ...]


def validate_catalog(data: Any) -> List[str]:
    """Return a list of human-readable problems with catalogue *data*."""
    problems: List[str] = []
    if not isinstance(data, dict):
        return [f"catalogue root must be a mapping, got {type(data).__name__}"]
    if data.get("schema") != CATALOG_SCHEMA:
        problems.append(
            f"schema must be {CATALOG_SCHEMA!r}, got {data.get('schema')!r}")
    if data.get("catalog_slice") != CATALOG_SLICE:
        problems.append(
            f"catalog_slice must be {CATALOG_SLICE!r}, "
            f"got {data.get('catalog_slice')!r}")
    for key in ("source_note", "extension_rule"):
        if not isinstance(data.get(key), str) or not data[key]:
            problems.append(f"{key} must be a non-empty string")
    for key in ("core_package", "core_import_name", "core_licence",
                "core_upstream"):
        if not isinstance(data.get(key), str) or not data[key]:
            problems.append(f"{key} must be a non-empty string")
    languages = data.get("languages")
    if not isinstance(languages, list) or not languages:
        problems.append("languages must be a non-empty list")
        return problems
    seen_languages: List[str] = []
    seen_extensions: Dict[str, str] = {}
    for position, entry in enumerate(languages, start=1):
        if not isinstance(entry, dict):
            problems.append(f"language entry is not a mapping: {entry!r}")
            continue
        eid = entry.get("id")
        expected = f"L-{position:02d}"
        if eid != expected:
            problems.append(
                f"language entry {eid!r}: ids must be sequential, "
                f"expected {expected}")
        name = entry.get("language")
        label = name if isinstance(name, str) and name else repr(entry)[:60]
        if not isinstance(name, str) or not name or name != name.strip().lower():
            problems.append(f"language {label}: language must be a lowercase string")
        elif name in seen_languages:
            problems.append(f"language {label}: duplicate language")
        else:
            seen_languages.append(name)
        if not isinstance(entry.get("title"), str) or not entry["title"]:
            problems.append(f"language {label}: title must be non-empty")
        extensions = entry.get("extensions")
        if (not isinstance(extensions, list) or not extensions
                or not all(isinstance(e, str) and _EXTENSION_RE.match(e)
                           for e in extensions or [])):
            problems.append(
                f"language {label}: extensions must be a non-empty list "
                "of dotted lowercase extensions")
        else:
            for ext in extensions:
                if ext in seen_extensions:
                    problems.append(
                        f"language {label}: extension {ext} already "
                        f"claimed by {seen_extensions[ext]}")
                seen_extensions[ext] = str(name)
        status = entry.get("status")
        if status not in STATUSES:
            problems.append(
                f"language {label}: status must be one of {STATUSES}, "
                f"got {status!r}")
        nodes = entry.get("definition_nodes")
        if not isinstance(nodes, dict):
            problems.append(f"language {label}: definition_nodes must be a mapping")
            nodes = {}
        elif list(nodes) != sorted(nodes):
            problems.append(
                f"language {label}: definition_nodes must be in sorted "
                "node-type order")
        elif not all(isinstance(k, str) and k and isinstance(v, str) and v
                     for k, v in nodes.items()):
            problems.append(
                f"language {label}: definition_nodes must map node types "
                "to non-empty kinds")
        if status == "grammar-declared":
            for key in ("grammar_package", "grammar_module",
                        "grammar_factory", "grammar_version_seen",
                        "licence", "upstream", "licence_notice"):
                if not isinstance(entry.get(key), str) or not entry[key]:
                    problems.append(
                        f"language {label}: a grammar-declared entry must "
                        f"carry a non-empty {key} (licences are noticed, "
                        "grammars are named)")
            if not nodes:
                problems.append(
                    f"language {label}: a grammar-declared entry must name "
                    "the definition node types its grammar produces")
        elif status == "no-grammar-package":
            for key in ("grammar_package", "grammar_module",
                        "grammar_factory", "grammar_version_seen",
                        "licence", "upstream", "licence_notice"):
                if entry.get(key) is not None:
                    problems.append(
                        f"language {label}: a no-grammar-package entry must "
                        f"record {key} as null — no grammar may be invented")
            if nodes:
                problems.append(
                    f"language {label}: a no-grammar-package entry must "
                    "declare no definition nodes")
        if not isinstance(entry.get("notes"), str) or not entry["notes"]:
            problems.append(f"language {label}: notes must be non-empty")
    if tuple(seen_languages) != ROADMAP_LANGUAGES:
        problems.append(
            f"languages must be exactly the roadmap languages in roadmap "
            f"order {ROADMAP_LANGUAGES}, got {tuple(seen_languages)}")
    return problems


def _to_catalog(data: Dict[str, Any]) -> LanguageCatalog:
    return LanguageCatalog(
        source_note=data["source_note"],
        extension_rule=data["extension_rule"],
        core_package=data["core_package"],
        core_import_name=data["core_import_name"],
        core_licence=data["core_licence"],
        core_upstream=data["core_upstream"],
        languages=tuple(
            LanguageDef(
                id=e["id"], language=e["language"], title=e["title"],
                extensions=tuple(e["extensions"]), status=e["status"],
                grammar_package=e["grammar_package"],
                grammar_module=e["grammar_module"],
                grammar_factory=e["grammar_factory"],
                grammar_version_seen=e["grammar_version_seen"],
                licence=e["licence"], upstream=e["upstream"],
                licence_notice=e["licence_notice"],
                definition_nodes=tuple(sorted(e["definition_nodes"].items())),
                notes=e["notes"],
            )
            for e in data["languages"]
        ),
    )


def load_catalog(data: Optional[Dict[str, Any]] = None) -> LanguageCatalog:
    """Load and validate the shipped language catalogue (or *data*)."""
    raw = data if data is not None else load_resource(CATALOG_RESOURCE)
    problems = validate_catalog(raw)
    if problems:
        raise ValidationError(
            "tree-sitter language catalogue failed validation: "
            + "; ".join(problems))
    return _to_catalog(raw)  # type: ignore[arg-type]


def _load_grammar_language(entry: LanguageDef):
    """Build the tree-sitter Language for *entry*, or raise ImportError."""
    if _tree_sitter is None:
        raise ImportError("tree_sitter is not installed")
    module = importlib.import_module(entry.grammar_module or "")
    factory = getattr(module, entry.grammar_factory or "")
    return _tree_sitter.Language(factory())


def probe_availability(
    catalog: Optional[LanguageCatalog] = None,
) -> Tuple[Availability, ...]:
    """Probe every catalogued language's grammar, live, in order.

    A language is ``available`` only when the core package and
    its grammar package both import and the grammar constructs
    in this environment. A no-grammar language is unavailable
    with the catalogue's own reason. Nothing here trusts the
    catalogue's declaration — it is re-proven per call.
    """
    catalog = catalog or load_catalog()
    out: List[Availability] = []
    for entry in catalog.languages:
        if entry.status == "no-grammar-package":
            out.append(Availability(
                language=entry.language, available=False,
                detail="no grammar package is published for this "
                       "language; the catalogue records none"))
            continue
        if _tree_sitter is None:
            out.append(Availability(
                language=entry.language, available=False,
                detail="the tree-sitter core package is not installed "
                       "(install mythic-agent[code-intelligence])"))
            continue
        try:
            _load_grammar_language(entry)
        except Exception as exc:  # import or capsule construction failed
            out.append(Availability(
                language=entry.language, available=False,
                detail=f"grammar package {entry.grammar_package} did not "
                       f"load: {exc}"))
            continue
        out.append(Availability(
            language=entry.language, available=True,
            detail=f"grammar {entry.grammar_package} "
                   f"{entry.grammar_version_seen} loaded"))
    return tuple(out)


def availability_for(
    language: str, catalog: Optional[LanguageCatalog] = None,
) -> Availability:
    """The probed availability of one *language* (KeyError if unknown)."""
    catalog = catalog or load_catalog()
    entry = catalog.language(language)
    for item in probe_availability(catalog):
        if item.language == entry.language:
            return item
    raise KeyError(f"no language {language!r}")  # unreachable by construction


def detect_language(
    filename: str, catalog: Optional[LanguageCatalog] = None,
) -> Optional[str]:
    """The catalogued language for *filename*'s extension, or None."""
    catalog = catalog or load_catalog()
    suffix = ""
    if "." in (filename or ""):
        suffix = "." + filename.rsplit(".", 1)[-1].lower()
    entry = catalog.for_extension(suffix) if suffix else None
    return entry.language if entry else None


def _convert_ts_node(node: Any, source: bytes) -> ParseNode:
    return ParseNode(
        type=node.type,
        start_byte=node.start_byte, end_byte=node.end_byte,
        start_point=(node.start_point[0], node.start_point[1]),
        end_point=(node.end_point[0], node.end_point[1]),
        children=tuple(_convert_ts_node(c, source) for c in node.children),
    )


def _ts_definitions(
    node: Any, entry: LanguageDef, out: List[Definition],
) -> None:
    kind = entry.definition_kind(node.type)
    if kind is not None:
        name_node = node.child_by_field_name("name")
        if name_node is not None:
            out.append(Definition(
                name=name_node.text.decode("utf-8", errors="replace"),
                kind=kind, language=entry.language, node_type=node.type,
                start_point=(node.start_point[0], node.start_point[1]),
                end_point=(node.end_point[0], node.end_point[1]),
            ))
    for child in node.children:
        _ts_definitions(child, entry, out)


def _parse_with_tree_sitter(entry: LanguageDef, source: str) -> ParsedSource:
    language = _load_grammar_language(entry)
    parser = _tree_sitter.Parser(language)  # type: ignore[union-attr]
    raw = source.encode("utf-8")
    tree = parser.parse(raw)
    definitions: List[Definition] = []
    _ts_definitions(tree.root_node, entry, definitions)
    return ParsedSource(
        language=entry.language, backend="tree_sitter",
        root=_convert_ts_node(tree.root_node, raw),
        has_error=bool(tree.root_node.has_error),
        definitions=tuple(definitions),
    )


def _parse_python_ast(entry: LanguageDef, source: str) -> ParsedSource:
    """The stdlib fallback: Python via :mod:`ast`, honestly labelled.

    Raises :class:`SyntaxError` for unparseable source, exactly
    as ``mythic_agent.context.symbols.extract_symbols`` does —
    the fallback never pretends a broken file parsed.
    """
    tree = _ast.parse(source)
    lines = source.encode("utf-8").splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))

    def byte_at(point: Tuple[int, int]) -> int:
        row, col = point
        if row >= len(offsets):
            return offsets[-1]
        return offsets[row] + col

    definitions: List[Definition] = []

    def convert(node: _ast.AST) -> ParseNode:
        start = (getattr(node, "lineno", 1) - 1,
                 getattr(node, "col_offset", 0))
        end = (getattr(node, "end_lineno", None) or start[0] + 1,
               getattr(node, "end_col_offset", 0))
        end = (end[0] - 1, end[1])
        if isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
            definitions.append(Definition(
                name=node.name, kind="function", language="python",
                node_type=type(node).__name__, start_point=start,
                end_point=end))
        elif isinstance(node, _ast.ClassDef):
            definitions.append(Definition(
                name=node.name, kind="class", language="python",
                node_type=type(node).__name__, start_point=start,
                end_point=end))
        return ParseNode(
            type=type(node).__name__,
            start_byte=byte_at(start), end_byte=byte_at(end),
            start_point=start, end_point=end,
            children=tuple(convert(c) for c in _ast.iter_child_nodes(node)),
        )

    root = convert(tree)
    return ParsedSource(
        language=entry.language, backend="python_ast", root=root,
        has_error=False, definitions=tuple(definitions),
    )


def parse_source(
    language: str, source: str,
    catalog: Optional[LanguageCatalog] = None,
) -> ParsedSource:
    """Parse *source* as *language*, honestly, or refuse.

    Grammar-backed when the language's grammar loads in this
    environment; Python falls back to the stdlib ``ast``
    backend when it does not (the returned parse says which
    backend served it). Any other language without a loadable
    grammar raises :class:`ParseUnavailableError`. An unknown
    language name raises KeyError from the catalogue.
    """
    catalog = catalog or load_catalog()
    entry = catalog.language(language)
    if not isinstance(source, str):
        raise ValidationError(
            f"source must be str, got {type(source).__name__}")
    if entry.status == "no-grammar-package":
        raise ParseUnavailableError(
            f"no tree-sitter grammar package is published for "
            f"{entry.title}; {entry.language} is catalogued "
            "Mojo-aware but no parse is invented for it")
    try:
        return _parse_with_tree_sitter(entry, source)
    except Exception:
        if entry.language == "python":
            return _parse_python_ast(entry, source)
        raise ParseUnavailableError(
            f"the grammar for {entry.title} ({entry.grammar_package}) "
            "is not installed in this environment; install it with "
            "pip install 'mythic-agent[code-intelligence]'") from None


def extract_definitions(
    language: str, source: str,
    catalog: Optional[LanguageCatalog] = None,
) -> Tuple[Definition, ...]:
    """The definitions in *source*, via :func:`parse_source`."""
    return parse_source(language, source, catalog=catalog).definitions


def render_markdown(catalog: LanguageCatalog) -> str:
    """Render the catalogue: grammars with licences, then the honest gap."""
    declared = catalog.languages_with("grammar-declared")
    grammarless = catalog.languages_with("no-grammar-package")
    lines = [
        "# Tree-Sitter Languages — grammars as data, licences noticed",
        "",
        f"*Slice {CATALOG_SLICE} of the All-Features road (Part III — "
        "Code Intelligence).*",
        "",
        catalog.source_note,
        "",
        f"**{len(catalog.languages)} languages** "
        f"({len(declared)} grammar-backed, {len(grammarless)} "
        f"grammar-less), core package `{catalog.core_package}` "
        f"({catalog.core_licence}, {catalog.core_upstream}).",
        "",
        f"*{catalog.extension_rule}*",
        "",
        "## Grammar-backed",
        "",
    ]
    for entry in declared:
        kinds = ", ".join(
            f"{node}→{kind}" for node, kind in entry.definition_nodes)
        lines.append(
            f"- **{entry.language}** — {entry.title}: grammar "
            f"`{entry.grammar_package}` {entry.grammar_version_seen}, "
            f"{entry.licence}, {entry.upstream}; extensions "
            f"{', '.join(entry.extensions)}; definitions: {kinds}. "
            f"Licence notice: {entry.licence_notice}")
    lines.append("")
    lines.append("## Grammar-less (honest)")
    lines.append("")
    for entry in grammarless:
        lines.append(
            f"- **{entry.language}** — {entry.title}: no grammar "
            f"package; extensions {', '.join(entry.extensions)}. "
            f"{entry.notes}")
    lines.append("")
    return "\n".join(lines)
