"""Structural search (All-Features roadmap slice M-047).

Part III — Code Intelligence. Until this slice the coder
could grep text and look symbols up by name (M-046's graph),
but it could not ask the ast-grep question: *find every call
shaped like* ``foo($A, $$$)`` — a pattern over the code's
own structure, where the shape matters and the names are
variables. This slice is that pattern search, as a tool and
a TUI panel.

What ships here, in the gap audit's owning module
(``mythic_agent/tools/structural_search.py``):

* **The pattern language.** A pattern is written in the
  target language itself, with ast-grep's metavariables:
  ``$NAME`` matches exactly one node and captures it;
  ``$$$`` (or ``$$$NAME``) matches zero or more sibling
  nodes and, when named, captures their joined text. The
  metavariables are substituted with placeholder
  identifiers and the pattern is parsed through the M-043
  foundation (``parse_source`` — never a second parser),
  then matched structurally against every node of a target
  parse: node types must agree, leaf text must agree, a
  metavariable used twice must capture the same text
  twice, and every capture carries its source span. Each
  node of the target is tried, so nested matches are each
  reported. Bracket and separator punctuation is structural
  scaffolding and is dropped from child sequences on both
  sides (operators are not: ``$A + $B`` never matches
  ``$A - $B``), and a bare-expression pattern is unwrapped
  from its statement wrapper so it can match anywhere an
  expression can sit. A pattern that parses nowhere bare
  in a grammar that demands file context (Go, Rust) is
  tried inside declared context wraps — the wrap is
  scaffolding, located by byte range, never part of the
  shape searched for.
* **The search.** :func:`search_source` runs one compiled
  pattern over one source; :func:`search_workspace` walks
  a workspace on the symbol graph's own roads (the M-043
  catalogue's extensions, the same skip directories and
  size bounds) and searches every file *of the pattern's
  language*. Other languages are not this search's
  population — the result names the language it searched.
* **The surfaces.** ``Agent.structural_search()`` is the
  tool; ``/ssearch <language> <pattern>`` shows the matches
  on the terminal and TUI system-command roads, sharing
  this module's parser and formatter.

Honesty rules, pinned by the slice's tests:

* **A pattern that does not parse is refused, never
  text-searched instead.** A grammar-backed parse with
  errors, or a Python pattern the stdlib fallback cannot
  parse, raises :class:`PatternError` naming the pattern.
  A stray ``$`` that starts no metavariable is likewise a
  pattern error, as is one name used as both ``$NAME`` and
  ``$$$NAME``.
* **A language with no honest parse is refused.** Mojo —
  catalogued grammar-less by M-043 — raises the
  foundation's own :class:`ParseUnavailableError`; an
  uncatalogued language raises KeyError. No match is ever
  invented from text for a language the foundation cannot
  parse.
* **Unparseable files are skipped with their reasons**,
  exactly as the symbol graph records them (oversized,
  binary, not UTF-8, broken source); a file its grammar
  parses with errors is searched, with the error named in
  the result's warnings.
* **Search only.** This slice finds; it never edits. The
  rewrite half of the census feature — the same patterns
  as safe codemods — is M-048, and nothing here claims it.
"""

from __future__ import annotations

__all__ = [
    "MAX_SEARCH_FILE_BYTES",
    "MAX_SEARCH_FILES",
    "PLAIN_EXPLANATION",
    "STRUCTURAL_SEARCH_SLICE",
    "Capture",
    "CompiledPattern",
    "PatternError",
    "SearchSkippedFile",
    "StructuralMatch",
    "StructuralSearchResult",
    "compile_pattern",
    "format_search_status",
    "parse_search_args",
    "render_markdown",
    "search_source",
    "search_workspace",
]

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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
STRUCTURAL_SEARCH_SLICE = "M-047"

#: Scan bounds, the symbol graph's own values.
MAX_SEARCH_FILES = 500
MAX_SEARCH_FILE_BYTES = 262_144

#: The structural search explained in plain words — the
#: sentences every surface shows.
PLAIN_EXPLANATION = (
    "Structural search finds code by its shape, not its "
    "text: write a pattern in the language itself, like "
    "foo($A, $$$) — $NAME matches exactly one piece of code "
    "and captures it, $$$ matches zero or more pieces in a "
    "row ($$$NAME captures them). /ssearch <language> "
    "<pattern> runs it over every file of that language in "
    "the workspace and lists each match with its captures. "
    "A pattern that does not parse in its language is "
    "refused, never quietly text-searched instead; a "
    "language with no grammar is refused the same way. "
    "Search only — the rewrite that would change the "
    "matched code is the next slice (M-048), not this one."
)

_USAGE = "Usage: /ssearch <language> <pattern>"

_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv",
              "dist", "build", ".hg", ".svn"}

#: Parse-tree root types whose children are the pattern.
_ROOT_TYPES = ("module", "program", "source_file", "Module")

_META_RE = re.compile(r"\$\$\$([A-Z][A-Z0-9_]*)?|\$([A-Z][A-Z0-9_]*)")


class PatternError(ValueError):
    """The pattern itself is not valid in its language.

    Raised when a pattern does not parse, when a ``$``
    starts no metavariable, when one name is used as both
    a single and a multi metavariable, or when the pattern
    produces no nodes at all. Always a refusal with the
    reason — never a silent fall back to text search.
    """


@dataclass(frozen=True)
class Capture:
    """One metavariable's capture: the text it matched and
    the span it came from (line 1-based, column 0-based)."""

    name: str
    text: str
    line: int
    column: int
    end_line: int
    end_column: int

    def record(self) -> Dict[str, object]:
        """This capture as a plain mapping."""
        return {
            "name": self.name, "text": self.text, "line": self.line,
            "column": self.column, "end_line": self.end_line,
            "end_column": self.end_column,
        }


@dataclass(frozen=True)
class StructuralMatch:
    """One place a pattern matched: the file, the span, the
    matched text, and every named capture."""

    path: str
    line: int
    column: int
    end_line: int
    end_column: int
    text: str
    captures: Tuple[Capture, ...]

    def record(self) -> Dict[str, object]:
        """This match as a plain mapping."""
        return {
            "path": self.path, "line": self.line,
            "column": self.column, "end_line": self.end_line,
            "end_column": self.end_column, "text": self.text,
            "captures": [c.record() for c in self.captures],
        }


@dataclass(frozen=True)
class SearchSkippedFile:
    """One candidate file the search honestly could not parse."""

    path: str
    reason: str

    def record(self) -> Dict[str, object]:
        """This skip as a plain mapping."""
        return {"path": self.path, "reason": self.reason}


@dataclass(frozen=True)
class CompiledPattern:
    """One pattern, parsed through the M-043 foundation.

    ``nodes`` are the pattern's top-level parse nodes (the
    root's children for a module/program root).
    ``singles`` maps each single-metavariable placeholder
    identifier to its capture name; ``manys`` maps each
    multi-metavariable placeholder to its capture name, or
    None for an unnamed ``$$$``. ``backend`` names the
    backend that parsed the pattern itself.
    """

    text: str
    language: str
    backend: str
    substituted_text: str
    nodes: Tuple[ParseNode, ...]
    singles: Dict[str, str]
    manys: Dict[str, Optional[str]]
    metavariables: Tuple[str, ...]


@dataclass(frozen=True)
class StructuralSearchResult:
    """One workspace search: every match, every skipped
    file with its reason, and the honest counts."""

    workspace: str
    language: str
    pattern: str
    matches: Tuple[StructuralMatch, ...]
    skipped: Tuple[SearchSkippedFile, ...]
    warnings: Tuple[str, ...]
    files_seen: int
    files_searched: int

    def record(self) -> Dict[str, object]:
        """This result as a plain mapping."""
        return {
            "slice": STRUCTURAL_SEARCH_SLICE,
            "workspace": self.workspace, "language": self.language,
            "pattern": self.pattern,
            "matches": [m.record() for m in self.matches],
            "skipped": [s.record() for s in self.skipped],
            "warnings": list(self.warnings),
            "files_seen": self.files_seen,
            "files_searched": self.files_searched,
        }


# ---------------------------------------------------------------------------
# compiling a pattern
# ---------------------------------------------------------------------------

def compile_pattern(
    text: str, language: str,
    catalog: Optional[LanguageCatalog] = None,
) -> CompiledPattern:
    """Compile *text* as a structural pattern for *language*.

    The pattern is written in the language itself, with
    ``$NAME`` / ``$$$`` / ``$$$NAME`` metavariables. The
    metavariables become placeholder identifiers and the
    result parses through the M-043 foundation, so a
    pattern is exactly as grammatical as the code it hunts.
    Raises :class:`PatternError` for a pattern that does
    not parse or is malformed, :class:`ParseUnavailableError`
    for a language with no honest parse, and KeyError for
    an uncatalogued language.
    """
    catalog = catalog or load_catalog()
    entry = catalog.language(language)  # KeyError: uncatalogued
    if not isinstance(text, str) or not text.strip():
        raise PatternError(
            "A structural pattern must be code in its language, "
            "with $NAME / $$$ metavariables — an empty pattern "
            "matches nothing and is refused.")
    singles: Dict[str, str] = {}
    manys: Dict[str, Optional[str]] = {}
    single_names: set = set()
    many_names: set = set()
    names: List[str] = []

    def _placeholder(match: "re.Match[str]") -> str:
        many_name, single_name = match.group(1), match.group(2)
        if single_name is not None:
            if single_name in many_names:
                raise PatternError(
                    f"${single_name} is used as both a single "
                    f"metavariable and a $$$ metavariable; one "
                    "name must mean one thing in a pattern.")
            placeholder = f"__mythic_meta_{single_name.lower()}__"
            singles[placeholder] = single_name
            single_names.add(single_name)
            if single_name not in names:
                names.append(single_name)
            return placeholder
        if many_name is not None and many_name in single_names:
            raise PatternError(
                f"${many_name} is used as both a single "
                f"metavariable and a $$$ metavariable; one "
                "name must mean one thing in a pattern.")
        if many_name is not None:
            many_names.add(many_name)
        placeholder = "__mythic_meta_many__" if many_name is None \
            else f"__mythic_meta_many_{many_name.lower()}__"
        manys[placeholder] = many_name
        if many_name is not None and many_name not in names:
            names.append(many_name)
        return placeholder

    substituted = _META_RE.sub(_placeholder, text)
    if "$" in substituted:
        raise PatternError(
            f"Pattern {text!r} carries a '$' that starts no "
            "metavariable: a metavariable is $NAME (one node) "
            "or $$$ / $$$NAME (zero or more nodes), with NAME "
            "in capitals.")
    # The pattern is tried bare first. Some grammars accept
    # nothing at file level but declarations in a package
    # (Go) or items (Rust), so a bare expression pattern is
    # then tried inside declared context wraps — a package
    # clause, a function body, a variable initialiser. The
    # wrap is scaffolding only: the pattern's nodes are the
    # maximal parse nodes inside the pattern's own byte
    # range of the wrapped text, and the wrap never becomes
    # part of the shape that is searched for.
    attempts: List[Tuple[str, str]] = [("", "")]
    attempts.extend(_CONTEXT_WRAPS.get(entry.language, ()))
    failure = ""
    for prefix, suffix in attempts:
        candidate = prefix + substituted + suffix
        try:
            parsed = parse_source(entry.language, candidate,
                                  catalog=catalog)
        except SyntaxError as exc:
            failure = str(exc)
            continue
        if parsed.has_error:
            failure = "the grammar reports errors in it"
            continue
        if not prefix and not suffix:
            nodes = parsed.root.children \
                if parsed.root.type in _ROOT_TYPES else (parsed.root,)
        else:
            nodes = _nodes_in_range(
                parsed.root, len(prefix.encode("utf-8")),
                len(prefix.encode("utf-8"))
                + len(substituted.encode("utf-8")))
        if not nodes:
            failure = "it produced no code nodes"
            continue
        # A pattern written as a bare expression parses
        # inside a statement wrapper (tree-sitter's
        # expression_statement, the ast fallback's Expr);
        # the shape the user means is the expression itself,
        # which may sit anywhere — inside a return, an
        # assignment, another call — not only as a statement
        # of its own. Unwrap a lone wrapper.
        unwrapped: List[ParseNode] = []
        for node in nodes:
            while node.type in ("expression_statement", "Expr"):
                significant = _significant(node.children)
                if len(significant) != 1:
                    break
                node = significant[0]
            unwrapped.append(node)
        return CompiledPattern(
            text=text, language=entry.language,
            backend=parsed.backend, substituted_text=candidate,
            nodes=tuple(unwrapped), singles=singles, manys=manys,
            metavariables=tuple(names))
    raise PatternError(
        f"Pattern {text!r} does not parse as "
        f"{entry.language} ({failure}), bare or inside a "
        "declared context wrap, so there is no shape to "
        "search for.")


#: Context wraps tried, in order, when a pattern does not
#: parse bare in its language: (prefix, suffix) pairs that
#: give the fragment the file context its grammar demands.
_CONTEXT_WRAPS: Dict[str, Tuple[Tuple[str, str], ...]] = {
    "go": (
        ("package mythicpattern\n", ""),
        ("package mythicpattern\nfunc __mythic_pattern__() {\n",
         "\n}"),
        ("package mythicpattern\nvar _ = ", "\n"),
    ),
    "rust": (
        ("fn __mythic_pattern__() {\n", "\n}"),
        ("fn __mythic_pattern__() { let _ = ", "; }\n"),
    ),
}


def _nodes_in_range(root: ParseNode, start: int,
                    end: int) -> Tuple[ParseNode, ...]:
    """The maximal parse nodes fully inside [start, end)."""
    out: List[ParseNode] = []

    def visit(node: ParseNode) -> None:
        if node.start_byte >= start and node.end_byte <= end \
                and node.start_byte < end:
            out.append(node)
            return
        if node.start_byte < end and node.end_byte > start:
            for child in node.children:
                visit(child)

    visit(root)
    return tuple(out)


# ---------------------------------------------------------------------------
# the structural match
# ---------------------------------------------------------------------------

def _node_text(raw: bytes, node: ParseNode) -> str:
    return raw[node.start_byte:node.end_byte].decode(
        "utf-8", errors="replace")


def _single_meta(pattern: CompiledPattern, raw: bytes,
                 node: ParseNode) -> Optional[str]:
    """The capture name when *node* is exactly a single
    metavariable placeholder, else None."""
    return pattern.singles.get(_node_text(raw, node).strip())


def _many_meta(pattern: CompiledPattern, raw: bytes,
               node: ParseNode) -> Tuple[bool, Optional[str]]:
    """(True, name) when *node* is exactly a multi
    metavariable placeholder (name None when unnamed)."""
    text = _node_text(raw, node).strip()
    if text in pattern.manys:
        return True, pattern.manys[text]
    return False, None


def _capture(name: str, text: str,
             start: Tuple[int, int],
             end: Tuple[int, int]) -> Capture:
    return Capture(name=name, text=text, line=start[0] + 1,
                   column=start[1], end_line=end[0] + 1,
                   end_column=end[1])


#: Bracket and separator punctuation the grammars carry as
#: child nodes. Their presence is implied by the structure
#: itself, and a ``$$$`` that consumes zero siblings must
#: not fail on the separator the pattern wrote before it —
#: so child sequences are matched with these dropped from
#: both sides. Operators are NOT dropped: ``$A + $B`` must
#: never match ``$A - $B`` (an operator node matches only
#: its own type). The ast fallback's context nodes
#: (``Load`` / ``Store`` / ``Del``) are scaffolding of the
#: same kind — every Name carries one, and it says nothing
#: about the shape — so they are dropped too; without that,
#: a Name would never reach its own text comparison.
_STRUCTURAL_PUNCTUATION = ("(", ")", "[", "]", "{", "}", ",", ";",
                           "Load", "Store", "Del")


def _significant(children: Tuple[ParseNode, ...],
                 ) -> Tuple[ParseNode, ...]:
    return tuple(c for c in children
                 if c.type not in _STRUCTURAL_PUNCTUATION)


def _match_node(pattern: CompiledPattern, p_raw: bytes,
                p_node: ParseNode, t_raw: bytes, t_node: ParseNode,
                captures: Dict[str, Capture]) -> bool:
    """Whether pattern node *p_node* matches target node
    *t_node*, recording captures. On False the caller
    restores *captures* from its snapshot."""
    single = _single_meta(pattern, p_raw, p_node)
    if single is not None:
        text = _node_text(t_raw, t_node)
        existing = captures.get(single)
        if existing is not None and existing.text != text:
            return False
        captures[single] = _capture(
            single, text, t_node.start_point, t_node.end_point)
        return True
    is_many, many_name = _many_meta(pattern, p_raw, p_node)
    if is_many:
        # A multi metavariable outside a sibling sequence
        # (the pattern itself, a lone argument) captures the
        # one node it stands against, whole.
        if many_name is not None:
            text = _node_text(t_raw, t_node)
            existing = captures.get(many_name)
            if existing is not None and existing.text != text:
                return False
            captures[many_name] = _capture(
                many_name, text, t_node.start_point,
                t_node.end_point)
        return True
    if p_node.type != t_node.type:
        return False
    p_children = _significant(p_node.children)
    t_children = _significant(t_node.children)
    if not p_children or not t_children:
        # A leaf, or a node carrying only scaffolding (the
        # ast fallback's Load under a Name): its own text is
        # the shape.
        return _node_text(p_raw, p_node) == _node_text(t_raw, t_node)
    return _match_sequence(pattern, p_raw, p_children,
                           t_raw, t_children, captures)


def _match_sequence(pattern: CompiledPattern, p_raw: bytes,
                    p_children: Tuple[ParseNode, ...],
                    t_raw: bytes,
                    t_children: Tuple[ParseNode, ...],
                    captures: Dict[str, Capture]) -> bool:
    """Whether the pattern children match the target
    children as a sequence, with ``$$$`` consuming zero or
    more siblings (greedy, with backtracking)."""

    def rec(i: int, j: int) -> bool:
        if i == len(p_children):
            return j == len(t_children)
        p_node = p_children[i]
        is_many, many_name = _many_meta(pattern, p_raw, p_node)
        if is_many:
            for k in range(len(t_children) - j, -1, -1):
                snapshot = dict(captures)
                if many_name is not None:
                    if k:
                        start = t_children[j].start_point
                        end = t_children[j + k - 1].end_point
                        text = t_raw[
                            t_children[j].start_byte:
                            t_children[j + k - 1].end_byte].decode(
                                "utf-8", errors="replace")
                    else:
                        start = end = (
                            t_children[j].start_point
                            if j < len(t_children)
                            else t_children[-1].end_point
                            if t_children else p_node.start_point)
                        text = ""
                    existing = captures.get(many_name)
                    if existing is not None and existing.text != text:
                        captures.clear()
                        captures.update(snapshot)
                        continue
                    captures[many_name] = _capture(
                        many_name, text, start, end)
                if rec(i + 1, j + k):
                    return True
                captures.clear()
                captures.update(snapshot)
            return False
        if j >= len(t_children):
            return False
        snapshot = dict(captures)
        if _match_node(pattern, p_raw, p_node, t_raw,
                       t_children[j], captures) and rec(i + 1, j + 1):
            return True
        captures.clear()
        captures.update(snapshot)
        return False

    return rec(0, 0)


def _search_parsed(path: str, pattern: CompiledPattern,
                   parsed: ParsedSource,
                   source: str) -> List[StructuralMatch]:
    p_raw = pattern.substituted_text.encode("utf-8")
    t_raw = source.encode("utf-8")
    matches: List[StructuralMatch] = []
    for node in parsed.root.walk():
        for p_node in pattern.nodes:
            captures: Dict[str, Capture] = {}
            if _match_node(pattern, p_raw, p_node, t_raw, node,
                           captures):
                matches.append(StructuralMatch(
                    path=path, line=node.start_point[0] + 1,
                    column=node.start_point[1],
                    end_line=node.end_point[0] + 1,
                    end_column=node.end_point[1],
                    text=_node_text(t_raw, node),
                    captures=tuple(
                        captures[name]
                        for name in pattern.metavariables
                        if name in captures)))
                break
    return matches


def search_source(path: str, source: str,
                  pattern: CompiledPattern,
                  catalog: Optional[LanguageCatalog] = None,
                  ) -> Tuple[StructuralMatch, ...]:
    """Every structural match of *pattern* in one *source*.

    *path* is the name the matches carry. The source parses
    through the M-043 foundation in the pattern's language:
    ParseUnavailableError for a language with no honest
    parse and SyntaxError for broken Python on the ast
    fallback ride through, exactly as the foundation raises
    them — a match is never invented from text.
    """
    catalog = catalog or load_catalog()
    parsed = parse_source(pattern.language, source, catalog=catalog)
    return tuple(_search_parsed(path, pattern, parsed, source))


# ---------------------------------------------------------------------------
# the workspace search
# ---------------------------------------------------------------------------

def search_workspace(
    workspace: Path | str,
    pattern: CompiledPattern,
    *,
    catalog: Optional[LanguageCatalog] = None,
    max_files: int = MAX_SEARCH_FILES,
    max_file_bytes: int = MAX_SEARCH_FILE_BYTES,
) -> StructuralSearchResult:
    """Search *workspace* for *pattern*.

    Files are discovered in deterministic (sorted) order
    among the M-043 catalogue's extensions; only files of
    the pattern's language are this search's population.
    Each is parsed through the foundation (never a second
    parser) and searched; a file that cannot be parsed
    honestly lands in ``skipped`` with the reason.
    """
    if max_files <= 0:
        raise ValueError("max_files must be positive")
    if max_file_bytes <= 0:
        raise ValueError("max_file_bytes must be positive")
    root = canonical_workspace_root(workspace)
    catalog = catalog or load_catalog()

    matches: List[StructuralMatch] = []
    skipped: List[SearchSkippedFile] = []
    warnings: List[str] = []
    files_seen = 0
    files_searched = 0
    capped = False
    for dirpath, dirnames, filenames in os.walk(root,
                                                followlinks=False):
        if capped:
            break
        dirnames[:] = sorted(
            d for d in dirnames
            if d not in _SKIP_DIRS and not d.startswith("."))
        for name in sorted(filenames):
            if detect_language(name, catalog) != pattern.language:
                continue
            if files_seen >= max_files:
                warnings.append(
                    f"structural search file cap reached "
                    f"({max_files}); later files were not searched")
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
                skipped.append(SearchSkippedFile(
                    rel, f"unreadable: {exc}"))
                continue
            if len(raw) > max_file_bytes:
                skipped.append(SearchSkippedFile(
                    rel, f"too large for the search "
                         f"({len(raw)} bytes > {max_file_bytes})"))
                continue
            if b"\x00" in raw:
                skipped.append(SearchSkippedFile(rel, "binary file"))
                continue
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                skipped.append(SearchSkippedFile(
                    rel, "not utf-8 text"))
                continue
            try:
                parsed = parse_source(pattern.language, text,
                                      catalog=catalog)
            except ParseUnavailableError as exc:
                skipped.append(SearchSkippedFile(rel, str(exc)))
                continue
            except SyntaxError as exc:
                skipped.append(SearchSkippedFile(
                    rel, f"unparseable ({pattern.language} "
                         f"backend): {exc}"))
                continue
            if parsed.has_error:
                warnings.append(f"{rel}: parsed with errors")
            files_searched += 1
            matches.extend(
                _search_parsed(rel, pattern, parsed, text))
    matches.sort(key=lambda m: (m.path, m.line, m.column))
    return StructuralSearchResult(
        workspace=str(root), language=pattern.language,
        pattern=pattern.text, matches=tuple(matches),
        skipped=tuple(skipped), warnings=tuple(warnings),
        files_seen=files_seen, files_searched=files_searched)


# ---------------------------------------------------------------------------
# surfaces: the shared parser + formatters
# ---------------------------------------------------------------------------

def parse_search_args(text: Any) -> Dict[str, Any]:
    """Parse the ``/ssearch`` slash-command argument string.

    Grammar::

        /ssearch <language> <pattern>

    The language is the first word (a language the M-043
    catalogue names); the pattern is the rest of the line,
    verbatim — it is code, and its spaces are its own.
    Returns a dict with keys ``action`` (``search``),
    ``language`` and ``pattern``. Raises :class:`ValueError`
    on a usage error.
    """
    if text is None:
        text = ""
    if not isinstance(text, str):
        raise ValueError(
            f"Search arguments must be text, "
            f"got {type(text).__name__}")
    stripped = text.strip()
    if not stripped:
        raise ValueError(_USAGE)
    language, _, pattern = stripped.partition(" ")
    pattern = pattern.strip()
    if not pattern:
        raise ValueError(_USAGE)
    return {"action": "search", "language": language.lower(),
            "pattern": pattern}


def _one_line(text: str) -> str:
    """*text* on one line for a surface: the first line,
    with a marker when the match runs on."""
    lines = text.splitlines()
    if len(lines) <= 1:
        return text.strip()
    return lines[0].rstrip() + " …"


def format_search_status(status: Dict[str, Any]) -> str:
    """The search report, from an Agent search-status mapping."""
    result = status["result"]
    lines = [
        f"Structural search ({STRUCTURAL_SEARCH_SLICE}): "
        f"{len(result['matches'])} match(es) for "
        f"{result['pattern']!r} in {result['language']} "
        f"({result['files_searched']} of {result['files_seen']} "
        f"file(s) searched)."]
    for match in result["matches"]:
        lines.append(
            f"  {match['path']}:{match['line']}:{match['column'] + 1}"
            f"  {_one_line(match['text'])}")
        for capture in match["captures"]:
            lines.append(
                f"      ${capture['name']} = "
                f"{_one_line(capture['text']) or '(nothing)'}")
    if not result["matches"]:
        lines.append(
            "  No code in this workspace is shaped like the "
            "pattern — that is the answer, not an error.")
    for skip in result["skipped"]:
        lines.append(f"  Skipped {skip['path']}: {skip['reason']}")
    for warning in result["warnings"]:
        lines.append(f"  Warning: {warning}")
    lines.append(status["plain_explanation"])
    return "\n".join(lines)


def render_markdown(result: StructuralSearchResult) -> str:
    """Render *result* as a human report, built from its
    own matches, captures, and skips."""
    lines = [
        "# Structural Search — code found by its shape",
        "",
        f"*Slice {STRUCTURAL_SEARCH_SLICE} of the All-Features "
        "road (Part III — Code Intelligence). Search only; "
        "the rewrite is M-048.*",
        "",
        f"**Pattern** `{result.pattern}` "
        f"({result.language}): {len(result.matches)} match(es) "
        f"in {result.files_searched} of {result.files_seen} "
        "file(s) searched.",
        "",
        "## Matches",
        "",
    ]
    if result.matches:
        for match in result.matches:
            lines.append(
                f"- **{match.path}:{match.line}** — "
                f"`{_one_line(match.text)}`")
            for capture in match.captures:
                lines.append(
                    f"  - ${capture.name} = "
                    f"`{_one_line(capture.text) or '(nothing)'}` "
                    f"(line {capture.line})")
    else:
        lines.append("- none")
    if result.skipped:
        lines += ["", "## Skipped files", ""]
        for skip in result.skipped:
            lines.append(f"- **{skip.path}**: {skip.reason}")
    if result.warnings:
        lines += ["", "## Warnings", ""]
        for warning in result.warnings:
            lines.append(f"- {warning}")
    lines.append("")
    return "\n".join(lines)
