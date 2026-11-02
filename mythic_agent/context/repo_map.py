"""The Repo Map (All-Features roadmap slice M-044).

Part III — Code Intelligence. Aider's crown, made kinder: a
token-budgeted map of the whole repo — files, classes,
functions, signatures — ranked by relevance to the current
task, refreshed incrementally.

What already shipped, and what this slice adds:

* M-043 (``mythic_agent.core.tree_sitter_foundation``) parses
  source grammar-backed (or through Python's stdlib ``ast``
  fallback) and extracts definitions per language, driven by
  the language catalogue's own ``definition_nodes``.
* The elder ``mythic_agent.context.symbols`` index extracts
  Python def/class symbols per file and ranks files by symbol
  mentions in a query — per-file, unranked across the repo,
  with no reference graph and no map.
* M-038's long-context strategy names ``repo_map`` as the
  first source in both known load orders; until this slice
  no map existed for that name to mean.
* This slice is the map itself, in the gap audit's owning
  module (``mythic_agent/context/repo_map.py``, proposed in
  M-003's audit with the context compiler as its basis).

The build, and the honesty rules pinned by its tests:

* **Definitions come from the M-043 parses, never a second
  extractor.** Each entry carries its file's definitions —
  name, kind, language, the signature line as written in the
  source, and its line — and names the parse backend that
  served the file (``tree_sitter`` / ``python_ast``).
* **Ranking is PageRank over the reference graph, as the
  field does.** A file references every other file whose
  defined symbol names it mentions in its own source text
  (identifier mentions, the shipped symbol index's own
  notion of a mention). PageRank (damping 0.85) runs over
  that graph; task relevance multiplies it: the score is
  ``pagerank * (1 + matched)`` where ``matched`` counts the
  entry's defined symbols and file name the task's
  identifiers name. With no task, the score is the PageRank
  itself. Sorting is deterministic (score desc, path asc).
* **Every ranking is explainable.** Each entry carries its
  reasons in plain words: its PageRank and inbound count,
  the task symbols it matched, what it defines, what it
  references. No score is ever presented without its why.
* **The budget is enforced by the shipped token estimator.**
  Entries are taken in rank order while their rendered text
  (plus the map header) fits ``budget_tokens``, counted with
  :class:`mythic_agent.context.budget.TokenEstimator`.
  Entries beyond the budget are named in ``omitted`` —
  never silently dropped — and the rendered map never
  exceeds the budget under the estimator it was built with.
* **Refresh is incremental, by content hash.** Pass a
  previous map back as ``previous``: a file whose sha256 is
  unchanged reuses its previous parse (counted in
  ``reused_files``); a changed or new file is parsed
  (counted in ``reparsed_files``); a vanished file drops
  out. The graph, ranks, reasons, and budget are always
  recomputed — a reused parse is never a reused ranking.
* **Nothing is invented for an unparseable file.** A file
  that cannot be parsed honestly — Mojo, whose catalogue
  entry is grammar-less; a language whose grammar is not
  installed; broken Python on the ``ast`` fallback; an
  oversized or binary file — lands in ``skipped`` with the
  reason, and contributes no entry. A file the grammar
  parses with errors still maps, with the error named in
  ``warnings``.

Surfaces in this slice: the pure build layer plus
:class:`RepoMapSource`, a context-compiler source serving
the rendered map (proven against the real compiler in the
slice's tests). The context runtime's default source list
is NOT changed here — the map's TUI is M-045's road, and
runtime wiring is a later, named step, not a claim made
by this slice.
"""

from __future__ import annotations

__all__ = [
    "DEFAULT_MAP_BUDGET_TOKENS",
    "MAX_MAP_FILE_BYTES",
    "MAX_MAP_FILES",
    "PAGERANK_DAMPING",
    "REPO_MAP_SLICE",
    "MapDefinition",
    "MapEntry",
    "RepoMap",
    "RepoMapSource",
    "SkippedFile",
    "build_repo_map",
    "compute_pagerank",
    "render_repo_map",
]

import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..core.tree_sitter_foundation import (
    LanguageCatalog,
    ParseUnavailableError,
    detect_language,
    load_catalog,
    parse_source,
)
from ..core.workspace import assert_within_workspace, canonical_workspace_root
from .budget import TokenEstimator
from .compiler import ContextBlock, ContextSource

#: The slice that owns this module.
REPO_MAP_SLICE = "M-044"

#: The map's default token budget (Aider's --map-tokens
#: default is likewise 1000: a map is a compass, not the
#: territory — the files themselves are loaded separately).
DEFAULT_MAP_BUDGET_TOKENS = 1000

#: Scan bounds, named like the symbol index's own bounds:
#: at most this many candidate files, each at most this big.
MAX_MAP_FILES = 500
MAX_MAP_FILE_BYTES = 262_144

#: PageRank damping factor (the field's standard 0.85).
PAGERANK_DAMPING = 0.85

_PAGERANK_ITERATIONS = 100
_PAGERANK_TOLERANCE = 1e-8

_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv",
              "dist", "build", ".hg", ".svn"}
_SIGNATURE_MAX_CHARS = 120


@dataclass(frozen=True)
class MapDefinition:
    """One definition in a mapped file, from the M-043 parse."""

    name: str
    kind: str
    language: str
    signature: str
    line: int

    def record(self) -> Dict[str, object]:
        """This definition as a plain mapping."""
        return {
            "name": self.name, "kind": self.kind,
            "language": self.language, "signature": self.signature,
            "line": self.line,
        }


@dataclass(frozen=True)
class MapEntry:
    """One ranked file in the map, with its reasons.

    ``token_cost`` is the rendered entry's cost under the
    estimator the map was built with, and ``rendered`` is
    that exact rendered text (the map's rendering is a join
    of these, so the budget arithmetic closes byte-for-byte).
    ``content_hash`` is the file's sha256 — the incremental
    refresh key.
    """

    path: str
    language: str
    backend: str
    definitions: Tuple[MapDefinition, ...]
    references_out: Tuple[str, ...]
    references_in: Tuple[str, ...]
    pagerank: float
    matched_symbols: Tuple[str, ...]
    path_matched: bool
    score: float
    reasons: Tuple[str, ...]
    token_cost: int
    rendered: str
    content_hash: str

    def record(self) -> Dict[str, object]:
        """This entry as a plain mapping."""
        return {
            "path": self.path, "language": self.language,
            "backend": self.backend,
            "definitions": [d.record() for d in self.definitions],
            "references_out": list(self.references_out),
            "references_in": list(self.references_in),
            "pagerank": self.pagerank,
            "matched_symbols": list(self.matched_symbols),
            "path_matched": self.path_matched,
            "score": self.score, "reasons": list(self.reasons),
            "token_cost": self.token_cost,
            "content_hash": self.content_hash,
        }


@dataclass(frozen=True)
class SkippedFile:
    """One candidate file the map honestly could not parse."""

    path: str
    reason: str

    def record(self) -> Dict[str, object]:
        """This skip as a plain mapping."""
        return {"path": self.path, "reason": self.reason}


@dataclass(frozen=True)
class RepoMap:
    """One built map: the ranked entries inside the budget,
    and everything the build honestly left out or reused."""

    workspace: str
    query: str
    budget_tokens: int
    entries: Tuple[MapEntry, ...]
    omitted: Tuple[str, ...]
    skipped: Tuple[SkippedFile, ...]
    warnings: Tuple[str, ...]
    files_seen: int
    reused_files: int
    reparsed_files: int

    def record(self) -> Dict[str, object]:
        """This map as a plain mapping (entries rendered-free)."""
        return {
            "workspace": self.workspace, "query": self.query,
            "budget_tokens": self.budget_tokens,
            "entries": [e.record() for e in self.entries],
            "omitted": list(self.omitted),
            "skipped": [s.record() for s in self.skipped],
            "warnings": list(self.warnings),
            "files_seen": self.files_seen,
            "reused_files": self.reused_files,
            "reparsed_files": self.reparsed_files,
        }


def compute_pagerank(
    nodes: Tuple[str, ...],
    edges: Dict[str, Tuple[str, ...]],
    *,
    damping: float = PAGERANK_DAMPING,
) -> Dict[str, float]:
    """PageRank over *edges* (path -> referenced paths).

    Deterministic: nodes are visited in the given (sorted)
    order, dangling nodes distribute their rank evenly over
    every node, and iteration stops when the largest change
    falls below tolerance (or at the named iteration cap).
    Ranks sum to 1 for a non-empty graph.
    """
    ordered = tuple(sorted(nodes))
    if not ordered:
        return {}
    count = len(ordered)
    outbound: Dict[str, Tuple[str, ...]] = {
        node: tuple(sorted(set(edges.get(node, ())) - {node}))
        for node in ordered
    }
    rank = {node: 1.0 / count for node in ordered}
    for _ in range(_PAGERANK_ITERATIONS):
        dangling = sum(rank[n] for n in ordered if not outbound[n])
        base = (1.0 - damping) / count + damping * dangling / count
        new = {node: base for node in ordered}
        for node in ordered:
            targets = outbound[node]
            if not targets:
                continue
            share = damping * rank[node] / len(targets)
            for target in targets:
                if target in new:
                    new[target] += share
        delta = max(abs(new[n] - rank[n]) for n in ordered)
        rank = new
        if delta < _PAGERANK_TOLERANCE:
            break
    return rank


def _signature_line(lines: List[str], row: int) -> str:
    if row < 0 or row >= len(lines):
        return ""
    text = " ".join(lines[row].split())
    if len(text) > _SIGNATURE_MAX_CHARS:
        text = text[:_SIGNATURE_MAX_CHARS - 3] + "..."
    return text


def _render_entry(path: str, definitions: Tuple[MapDefinition, ...]) -> str:
    if not definitions:
        return f"{path}:\n  (no definitions)"
    lines = [f"{path}:"]
    for definition in definitions:
        lines.append(f"  {definition.signature}")
    return "\n".join(lines)


def _header(query: str, budget_tokens: int) -> str:
    lines = [f"# Repo Map (budget {budget_tokens} tokens)"]
    if query:
        lines.append(f"Task: {query}")
    return "\n".join(lines)


@dataclass(frozen=True)
class _ParsedFile:
    path: str
    language: str
    backend: str
    definitions: Tuple[MapDefinition, ...]
    identifiers: Tuple[str, ...]
    content_hash: str


def build_repo_map(
    workspace: Path | str,
    *,
    query: str = "",
    budget_tokens: int = DEFAULT_MAP_BUDGET_TOKENS,
    estimator: Optional[TokenEstimator] = None,
    catalog: Optional[LanguageCatalog] = None,
    previous: Optional[RepoMap] = None,
    max_files: int = MAX_MAP_FILES,
    max_file_bytes: int = MAX_MAP_FILE_BYTES,
) -> RepoMap:
    """Build the repo map for *workspace*.

    Files are discovered in deterministic (sorted) order
    among the M-043 catalogue's extensions; each is parsed
    through the foundation (or its parse reused from
    *previous* when the content hash is unchanged), the
    reference graph and PageRank are computed over all
    parsed files, task relevance is applied from *query*,
    and entries are taken in rank order while the rendered
    map fits *budget_tokens* under *estimator*.
    """
    if budget_tokens < 0:
        raise ValueError("budget_tokens must be non-negative")
    if max_files <= 0:
        raise ValueError("max_files must be positive")
    if max_file_bytes <= 0:
        raise ValueError("max_file_bytes must be positive")
    root = canonical_workspace_root(workspace)
    estimator = estimator or TokenEstimator()
    catalog = catalog or load_catalog()
    task = (query or "").strip()
    previous_by_path: Dict[str, MapEntry] = (
        {e.path: e for e in previous.entries} if previous else {})
    if previous:
        for path in previous.omitted:
            # An omitted entry's parse is not stored on the
            # map (only ranked entries are), so an omitted
            # file is simply parsed again — never guessed.
            previous_by_path.pop(path, None)

    parsed: List[_ParsedFile] = []
    skipped: List[SkippedFile] = []
    warnings: List[str] = []
    files_seen = 0
    reused = 0
    reparsed = 0
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
                    f"repo map file cap reached ({max_files}); "
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
                skipped.append(SkippedFile(rel, f"unreadable: {exc}"))
                continue
            if len(raw) > max_file_bytes:
                skipped.append(SkippedFile(
                    rel, f"too large for the map ({len(raw)} bytes "
                         f"> {max_file_bytes})"))
                continue
            if b"\x00" in raw:
                skipped.append(SkippedFile(rel, "binary file"))
                continue
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                skipped.append(SkippedFile(rel, "not utf-8 text"))
                continue
            content_hash = hashlib.sha256(raw).hexdigest()
            prior = previous_by_path.get(rel)
            if prior is not None and prior.content_hash == content_hash:
                parsed.append(_ParsedFile(
                    path=rel, language=prior.language,
                    backend=prior.backend,
                    definitions=prior.definitions,
                    identifiers=tuple(sorted(set(
                        _IDENT_RE.findall(text)))),
                    content_hash=content_hash))
                reused += 1
                continue
            try:
                result = parse_source(language, text, catalog=catalog)
            except ParseUnavailableError as exc:
                skipped.append(SkippedFile(rel, str(exc)))
                continue
            except SyntaxError as exc:
                skipped.append(SkippedFile(
                    rel, f"unparseable ({language} backend): {exc}"))
                continue
            reparsed += 1
            if result.has_error:
                warnings.append(f"{rel}: parsed with errors")
            lines = text.splitlines()
            definitions = tuple(
                MapDefinition(
                    name=d.name, kind=d.kind, language=d.language,
                    signature=_signature_line(lines, d.start_point[0]),
                    line=d.start_point[0] + 1)
                for d in result.definitions)
            parsed.append(_ParsedFile(
                path=rel, language=language, backend=result.backend,
                definitions=definitions,
                identifiers=tuple(sorted(set(_IDENT_RE.findall(text)))),
                content_hash=content_hash))

    # The reference graph: a file references every other file
    # whose defined symbol names it mentions by name.
    defined_in: Dict[str, List[str]] = {}
    for item in parsed:
        for name in {d.name.lower() for d in item.definitions}:
            defined_in.setdefault(name, []).append(item.path)
    edges: Dict[str, Tuple[str, ...]] = {}
    for item in parsed:
        targets = set()
        for ident in item.identifiers:
            for owner in defined_in.get(ident.lower(), ()):
                if owner != item.path:
                    targets.add(owner)
        edges[item.path] = tuple(sorted(targets))
    ranks = compute_pagerank(
        tuple(item.path for item in parsed), edges)

    query_idents = {i.lower() for i in _IDENT_RE.findall(task)}
    scored: List[MapEntry] = []
    for item in parsed:
        inbound = tuple(sorted(
            p.path for p in parsed if item.path in edges[p.path]))
        matched = tuple(sorted(
            {d.name for d in item.definitions
             if d.name.lower() in query_idents}))
        stem = Path(item.path).stem.lower()
        path_matched = bool(stem and stem in query_idents)
        multiplier = 1 + len(matched) + (1 if path_matched else 0)
        score = ranks.get(item.path, 0.0) * multiplier
        reasons: List[str] = []
        if inbound:
            reasons.append(
                f"PageRank {ranks.get(item.path, 0.0):.4f} from "
                f"{len(inbound)} inbound reference(s) "
                f"({', '.join(inbound[:3])}"
                f"{', ...' if len(inbound) > 3 else ''})")
        else:
            reasons.append(
                f"PageRank {ranks.get(item.path, 0.0):.4f} — no "
                "inbound references; this is the graph floor")
        if matched:
            reasons.append(
                f"matches the task: defines {', '.join(matched)}")
        if path_matched:
            reasons.append("file name matches the task")
        if item.definitions:
            names = ", ".join(d.name for d in item.definitions[:5])
            reasons.append(
                f"defines {len(item.definitions)} symbol(s): {names}"
                f"{', ...' if len(item.definitions) > 5 else ''}")
        else:
            reasons.append("defines no symbols the catalogue extracts")
        if edges[item.path]:
            reasons.append(
                f"references {len(edges[item.path])} file(s): "
                f"{', '.join(edges[item.path][:3])}"
                f"{', ...' if len(edges[item.path]) > 3 else ''}")
        rendered = _render_entry(item.path, item.definitions)
        scored.append(MapEntry(
            path=item.path, language=item.language, backend=item.backend,
            definitions=item.definitions,
            references_out=edges[item.path], references_in=inbound,
            pagerank=ranks.get(item.path, 0.0),
            matched_symbols=matched, path_matched=path_matched,
            score=score, reasons=tuple(reasons),
            token_cost=estimator.count(rendered),
            rendered=rendered, content_hash=item.content_hash))
    scored.sort(key=lambda e: (-e.score, e.path))

    header = _header(task, budget_tokens)
    spent = estimator.count(header)
    entries: List[MapEntry] = []
    omitted: List[str] = []
    for entry in scored:
        cost = entry.token_cost + 1  # the joining newline's share
        if spent + cost <= budget_tokens:
            entries.append(entry)
            spent += cost
        else:
            omitted.extend(e.path for e in scored[len(entries):])
            break
    return RepoMap(
        workspace=str(root), query=task, budget_tokens=budget_tokens,
        entries=tuple(entries), omitted=tuple(omitted),
        skipped=tuple(skipped), warnings=tuple(warnings),
        files_seen=files_seen, reused_files=reused,
        reparsed_files=reparsed)


def render_repo_map(repo_map: RepoMap) -> str:
    """Render *repo_map* exactly as its budget was counted:
    the header plus the included entries' rendered text."""
    parts = [_header(repo_map.query, repo_map.budget_tokens)]
    parts.extend(e.rendered for e in repo_map.entries)
    return "\n".join(parts)


class RepoMapSource(ContextSource):
    """Compiler source serving the repo map (slice M-044).

    Builds the map for the compilation's workspace and query
    under its own named budget and yields it as one block;
    a workspace with no mappable files yields no block.
    """

    def __init__(self, *, priority: int = 3, enabled: bool = True,
                 budget_tokens: int = DEFAULT_MAP_BUDGET_TOKENS) -> None:
        self.name = "repo-map"
        self.priority = priority
        self.enabled = enabled
        self.budget_tokens = budget_tokens

    def collect(self, ctx) -> List[ContextBlock]:
        repo_map = build_repo_map(
            ctx.workspace, query=ctx.query or "",
            budget_tokens=self.budget_tokens)
        if not repo_map.entries:
            return []
        return [ContextBlock(
            name="repo-map",
            content=render_repo_map(repo_map),
            priority=self.priority,
            provenance={
                "files_seen": repo_map.files_seen,
                "files_mapped": len(repo_map.entries),
                "files_omitted": len(repo_map.omitted),
                "files_skipped": len(repo_map.skipped),
            })]
