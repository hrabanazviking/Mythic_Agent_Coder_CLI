"""Beyond-grep local search (M-058).

Part III — Code Intelligence. One local search with three
modes, ranked by the symbol graph instead of raw match
order — the roadmap's words for this slice.

What ships here, in ``mythic_agent/tools/local_search.py``:

* **Text mode — an in-process, ripgrep-class engine.**
  No external binary is invoked and none is required:
  the workspace is walked in deterministic (sorted)
  order, every text file is searched line by line with
  a regular expression, and matches carry path, line,
  and column. Files that cannot honestly be searched —
  binary, not UTF-8, over the size bound, unreadable —
  are skipped with their reasons, and the file/result
  caps name themselves in the report's warnings when
  they cut anything off. An invalid regex is refused
  as a pattern error, never silently searched as
  literal text.
* **Fuzzy mode.** The query's characters must appear
  in the line in order (a subsequence match,
  case-insensitive); the strength of a fuzzy match is
  an auditable score — matched characters earn,
  consecutive runs and word-boundary starts earn more,
  and gaps cost — and that score rides into the ranking
  with its reason named.
* **Structural mode.** Delegated whole to M-047's
  :mod:`mythic_agent.tools.structural_search` — the
  pattern is compiled and searched by that engine,
  never by a second structural matcher here. Its
  refusals (a pattern that does not parse, a language
  with no honest parse) stay refusals on this road too.
* **Ranking by the symbol graph.** M-046's
  :func:`mythic_agent.context.symbol_graph.build_symbol_graph`
  is built once per search. A match on a definition
  site earns the most; a match whose line names a
  symbol the graph defines earns by that symbol's
  reference count (capped); a match in a file the
  graph's references touch often earns by that count
  (capped). Every match carries its total score and
  the plain reasons that earned it, so the order can
  be audited, never merely trusted. When the graph
  cannot be built, the matches are reported unranked
  in match order with the reason named in the
  warnings — raw order is never dressed as ranking.
* **The surfaces.** ``Agent.local_search()`` and
  ``/search`` on the terminal and TUI system-command
  roads, sharing this module's parser and formatter:
  ``/search [text] <regex>``, ``/search fuzzy
  <query>``, ``/search structural <language>
  <pattern>``. The setting ``local_search`` (on by
  default) closes the road plainly when the user
  says so.

Honesty rules, pinned by the slice's tests:

* **In-process means in-process.** No subprocess, no
  ripgrep binary, no shelling out — the engine is this
  module, so its behaviour is the same on every
  machine the package runs on.
* **A refused pattern stays refused.** Invalid regex
  and unparseable structural patterns raise; neither
  is quietly retried as a different kind of search.
* **Ranking is arithmetic, not vibes.** Every point
  in a match's score traces to a named reason with
  the graph fact behind it; a symbol the graph does
  not know earns nothing.
* **Absence is named.** A search with no matches says
  so; a skipped file says why; a truncated result set
  says it was truncated.
"""

from __future__ import annotations

__all__ = [
    "LOCAL_SEARCH_SLICE",
    "MAX_LOCAL_FILE_BYTES",
    "MAX_LOCAL_FILES",
    "MAX_RESULTS",
    "MODES",
    "PLAIN_EXPLANATION",
    "USAGE",
    "LocalMatch",
    "LocalSearchReport",
    "SkippedFile",
    "enabled_from_config",
    "format_local_search",
    "fuzzy_score",
    "parse_local_search_args",
    "render_markdown",
    "search",
]

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from ..core.workspace import assert_within_workspace, canonical_workspace_root

LOCAL_SEARCH_SLICE = "M-058"

#: The modes behind the one surface, in roadmap order.
MODES = ("text", "fuzzy", "structural")

#: Scan bounds. Files past the count bound are not
#: searched and the cap is named; a file past the byte
#: bound is skipped with its size as the reason.
MAX_LOCAL_FILES = 2000
MAX_LOCAL_FILE_BYTES = 1_048_576

#: How many matches one search reports. More matches
#: than this are truncated, and the report says so.
MAX_RESULTS = 200

#: Ranking weights (see the ranking section below).
_DEFINITION_SITE_POINTS = 50
_SYMBOL_REFERENCE_CAP = 20
_FILE_REFERENCE_CAP = 10

PLAIN_EXPLANATION = (
    "Local search goes beyond grep behind one surface: "
    "/search <regex> searches every text file in the "
    "workspace in-process (no external tool), /search "
    "fuzzy <query> matches lines holding the query's "
    "characters in order, and /search structural "
    "<language> <pattern> finds code by its shape via "
    "the structural engine. Results are ranked by the "
    "symbol graph — definition sites first, then lines "
    "naming well-referenced symbols, then files the "
    "graph touches often — and every result carries "
    "its score and the reasons that earned it. A "
    "pattern that does not parse is refused, never "
    "quietly searched another way."
)

USAGE = ("Usage: /search [text] <regex> | "
         "/search fuzzy <query> | "
         "/search structural <language> <pattern>")

_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv",
              "dist", "build", ".hg", ".svn"}

_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def enabled_from_config(config: Optional[Dict[str, Any]]) -> bool:
    """Local search is on unless config says so."""
    if not config:
        return True
    return config.get("local_search", True) is not False


# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LocalMatch:
    """One match, with the score and reasons its rank rests on."""

    path: str
    line: int
    column: int
    text: str
    score: int = 0
    reasons: Tuple[str, ...] = ()
    captures: Tuple[Dict[str, Any], ...] = ()

    def record(self) -> Dict[str, Any]:
        return {"path": self.path, "line": self.line,
                "column": self.column, "text": self.text,
                "score": self.score, "reasons": list(self.reasons),
                "captures": [dict(c) for c in self.captures]}


@dataclass(frozen=True)
class SkippedFile:
    """One file the search honestly did not search, and why."""

    path: str
    reason: str

    def record(self) -> Dict[str, Any]:
        return {"path": self.path, "reason": self.reason}


@dataclass
class LocalSearchReport:
    """One search's whole account."""

    workspace: str = ""
    mode: str = "text"
    query: str = ""
    language: str = ""
    status: str = "ok"  # ok | disabled
    matches: List[LocalMatch] = field(default_factory=list)
    skipped: List[SkippedFile] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    files_seen: int = 0
    files_searched: int = 0
    ranking: str = "symbol-graph"  # symbol-graph | unranked
    truncated: bool = False
    note: str = ""

    def record(self) -> Dict[str, Any]:
        return {"workspace": self.workspace, "mode": self.mode,
                "query": self.query, "language": self.language,
                "status": self.status,
                "matches": [m.record() for m in self.matches],
                "skipped": [s.record() for s in self.skipped],
                "warnings": list(self.warnings),
                "files_seen": self.files_seen,
                "files_searched": self.files_searched,
                "ranking": self.ranking,
                "truncated": self.truncated,
                "note": self.note}


# ---------------------------------------------------------------------------
# Fuzzy scoring
# ---------------------------------------------------------------------------

def fuzzy_score(query: str, text: str) -> Optional[int]:
    """Score *query* as a subsequence of *text*, or None.

    Case-insensitive. Every matched character earns 1;
    a character continuing a run earns 5 more; a
    character starting a word (after a non-word
    character or at the line's start) earns 4 more;
    each skipped character between two matches costs 1.
    None means the query's characters do not appear in
    order — no match, however close it felt.
    """
    needle = (query or "").lower()
    if not needle:
        return None
    haystack = (text or "").lower()
    score = 0
    pos = 0
    prev_matched = False
    gap = 0
    for char in needle:
        found = haystack.find(char, pos)
        if found < 0:
            return None
        gap = found - pos if prev_matched or score else 0
        score += 1
        if prev_matched and found == pos:
            score += 5
        if found == 0 or not (haystack[found - 1].isalnum()
                              or haystack[found - 1] == "_"):
            score += 4
        if prev_matched:
            score -= gap
        prev_matched = True
        pos = found + 1
    return score


# ---------------------------------------------------------------------------
# The workspace walk (text + fuzzy modes)
# ---------------------------------------------------------------------------

def _walk_text_files(root: Path, report: LocalSearchReport,
                     max_files: int, max_file_bytes: int):
    """Yield (relative path, text) for every searchable file.

    Deterministic sorted order; every file that cannot
    honestly be searched lands in the report's skipped
    list with its reason, and the file cap names itself
    in the warnings when it cuts the walk short.
    """
    capped = False
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        if capped:
            break
        dirnames[:] = sorted(
            d for d in dirnames
            if d not in _SKIP_DIRS and not d.startswith("."))
        for name in sorted(filenames):
            if report.files_seen >= max_files:
                report.warnings.append(
                    f"local search file cap reached ({max_files}); "
                    "later files were not searched")
                capped = True
                break
            candidate = Path(dirpath) / name
            try:
                resolved = assert_within_workspace(root, candidate)
            except Exception as exc:
                report.warnings.append(f"blocked {candidate}: {exc}")
                continue
            rel = str(resolved.relative_to(root))
            report.files_seen += 1
            try:
                raw = resolved.read_bytes()
            except OSError as exc:
                report.skipped.append(SkippedFile(
                    rel, f"unreadable: {exc}"))
                continue
            if len(raw) > max_file_bytes:
                report.skipped.append(SkippedFile(
                    rel, f"too large for the search ({len(raw)} bytes "
                         f"> {max_file_bytes})"))
                continue
            if b"\x00" in raw:
                report.skipped.append(SkippedFile(rel, "binary file"))
                continue
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                report.skipped.append(SkippedFile(rel, "not utf-8 text"))
                continue
            report.files_searched += 1
            yield rel, text


def _text_matches(report: LocalSearchReport, root: Path, query: str,
                  max_files: int, max_file_bytes: int) -> None:
    try:
        pattern = re.compile(query)
    except re.error as exc:
        raise ValueError(
            f"the search pattern {query!r} is not a valid regular "
            f"expression: {exc} — it was not searched as literal "
            "text instead") from exc
    for rel, text in _walk_text_files(root, report, max_files,
                                      max_file_bytes):
        for lineno, line in enumerate(text.splitlines(), start=1):
            found = pattern.search(line)
            if found:
                report.matches.append(LocalMatch(
                    path=rel, line=lineno, column=found.start(),
                    text=line.strip()[:200]))


def _fuzzy_matches(report: LocalSearchReport, root: Path, query: str,
                   max_files: int, max_file_bytes: int) -> None:
    lowered = query.lower()
    for rel, text in _walk_text_files(root, report, max_files,
                                      max_file_bytes):
        for lineno, line in enumerate(text.splitlines(), start=1):
            score = fuzzy_score(query, line)
            if score is None:
                continue
            first = line.lower().find(lowered[0]) if lowered else 0
            report.matches.append(LocalMatch(
                path=rel, line=lineno, column=max(first, 0),
                text=line.strip()[:200], score=score,
                reasons=(f"fuzzy score {score}",)))


def _structural_matches(report: LocalSearchReport, root: Path,
                        query: str, language: str) -> None:
    from .structural_search import (
        PatternError, compile_pattern, search_workspace)

    try:
        compiled = compile_pattern(query, language)
    except PatternError:
        raise
    except Exception as exc:  # the foundation's refusals stay refusals
        raise ValueError(str(exc)) from exc
    result = search_workspace(root, compiled)
    report.files_seen = result.files_seen
    report.files_searched = result.files_searched
    report.skipped = [SkippedFile(s.path, s.reason)
                      for s in result.skipped]
    report.warnings.extend(result.warnings)
    for match in result.matches:
        first_line = match.text.splitlines()[0] if match.text else ""
        report.matches.append(LocalMatch(
            path=match.path, line=match.line, column=match.column,
            text=first_line.strip()[:200],
            captures=tuple(c.record() for c in match.captures)))


# ---------------------------------------------------------------------------
# Ranking by the symbol graph
# ---------------------------------------------------------------------------

class _GraphRanker:
    """The graph facts ranking rests on, counted once."""

    def __init__(self, graph: Any) -> None:
        self.definition_sites: Dict[Tuple[str, int], str] = {}
        self.references_by_name: Dict[str, int] = {}
        self.references_by_file: Dict[str, int] = {}
        for definition in graph.definitions:
            key = (definition.path, definition.line)
            self.definition_sites.setdefault(key, definition.name)
        for site in graph.references:
            self.references_by_name[site.name.lower()] = \
                self.references_by_name.get(site.name.lower(), 0) + 1
            self.references_by_file[site.path] = \
                self.references_by_file.get(site.path, 0) + 1

    def rank(self, match: LocalMatch) -> LocalMatch:
        score = match.score
        reasons = list(match.reasons)
        defined_here = self.definition_sites.get((match.path, match.line))
        if defined_here is not None:
            score += _DEFINITION_SITE_POINTS
            reasons.append(
                f"defines {defined_here} "
                f"(+{_DEFINITION_SITE_POINTS})")
        named: List[str] = []
        for token in _IDENT_RE.findall(match.text):
            key = token.lower()
            if key in self.references_by_name and key not in named:
                named.append(key)
        for key in named:
            earned = min(self.references_by_name[key],
                         _SYMBOL_REFERENCE_CAP)
            score += earned
            reasons.append(
                f"names {key}, referenced "
                f"{self.references_by_name[key]} time(s) in the "
                f"graph (+{earned})")
        file_refs = self.references_by_file.get(match.path, 0)
        if file_refs:
            earned = min(file_refs, _FILE_REFERENCE_CAP)
            score += earned
            reasons.append(
                f"file carries {file_refs} graph reference(s) "
                f"(+{earned})")
        return LocalMatch(
            path=match.path, line=match.line, column=match.column,
            text=match.text, score=score, reasons=tuple(reasons),
            captures=match.captures)


def _apply_ranking(report: LocalSearchReport, root: Path) -> None:
    if not report.matches:
        return
    try:
        from ..context.symbol_graph import build_symbol_graph
        graph = build_symbol_graph(root)
    except Exception as exc:
        report.ranking = "unranked"
        report.warnings.append(
            f"the symbol graph could not be built ({exc}); "
            "results are in match order, unranked")
        report.matches.sort(key=lambda m: (m.path, m.line, m.column))
        return
    ranker = _GraphRanker(graph)
    report.matches = [ranker.rank(m) for m in report.matches]
    report.matches.sort(
        key=lambda m: (-m.score, m.path, m.line, m.column))


# ---------------------------------------------------------------------------
# The one search
# ---------------------------------------------------------------------------

def search(root: Optional[Path | str] = None, query: str = "", *,
           mode: str = "text", language: Optional[str] = None,
           enabled: bool = True,
           max_files: int = MAX_LOCAL_FILES,
           max_file_bytes: int = MAX_LOCAL_FILE_BYTES,
           max_results: int = MAX_RESULTS) -> LocalSearchReport:
    """Run one local search over a workspace.

    *mode* is one of :data:`MODES`. Structural mode
    requires *language* and delegates to M-047's engine.
    Raises :class:`ValueError` for a refused pattern
    (invalid regex, unparseable structural pattern, a
    missing language) and for an unknown mode — a
    refusal is never quietly searched another way.
    """
    if mode not in MODES:
        raise ValueError(
            f"unknown search mode {mode!r} — the modes are "
            f"{', '.join(MODES)}")
    if max_files <= 0:
        raise ValueError("max_files must be positive")
    if max_file_bytes <= 0:
        raise ValueError("max_file_bytes must be positive")
    if max_results <= 0:
        raise ValueError("max_results must be positive")
    base = Path(root).resolve() if root is not None else Path.cwd()
    report = LocalSearchReport(
        workspace=str(base), mode=mode, query=query,
        language=(language or "").lower())
    if not enabled:
        report.status = "disabled"
        report.ranking = "unranked"
        report.note = ("local search is off (the local_search "
                       "setting), so nothing was searched")
        return report
    if not (query or "").strip():
        raise ValueError(f"{USAGE} — a search needs its query")
    if not base.is_dir():
        report.note = f"the workspace {base} is not there"
        return report
    root_path = canonical_workspace_root(base)
    report.workspace = str(root_path)
    if mode == "text":
        _text_matches(report, root_path, query, max_files, max_file_bytes)
    elif mode == "fuzzy":
        _fuzzy_matches(report, root_path, query, max_files, max_file_bytes)
    else:
        if not report.language:
            raise ValueError(
                f"{USAGE} — structural search needs its language")
        _structural_matches(report, root_path, query, report.language)
    _apply_ranking(report, root_path)
    if len(report.matches) > max_results:
        report.truncated = True
        report.warnings.append(
            f"result cap reached ({max_results}); "
            f"{len(report.matches) - max_results} further match(es) "
            "were not shown")
        report.matches = report.matches[:max_results]
    if not report.matches:
        report.note = ("no matches — that is the answer, "
                       "not an error")
    return report


# ---------------------------------------------------------------------------
# Surfaces: the shared parser + formatters
# ---------------------------------------------------------------------------

def parse_local_search_args(arguments: str) -> Dict[str, Any]:
    """Parse ``/search`` arguments into a search request.

    Grammar::

        /search [text] <regex...>
        /search fuzzy <query...>
        /search structural <language> <pattern...>

    A bare first word that is not a mode is part of the
    text query — ``/search foo bar`` searches for the
    regex ``foo bar``. Raises :class:`ValueError` on a
    usage error.
    """
    text = (arguments or "").strip()
    if not text:
        raise ValueError(USAGE)
    tokens = text.split(None, 1)
    head = tokens[0].lower()
    rest = tokens[1].strip() if len(tokens) > 1 else ""
    if head == "text":
        if not rest:
            raise ValueError(f"{USAGE} — text search needs its pattern")
        return {"action": "search", "mode": "text", "query": rest,
                "language": None}
    if head == "fuzzy":
        if not rest:
            raise ValueError(f"{USAGE} — fuzzy search needs its query")
        return {"action": "search", "mode": "fuzzy", "query": rest,
                "language": None}
    if head == "structural":
        if not rest:
            raise ValueError(
                f"{USAGE} — structural search needs a language "
                "and a pattern")
        parts = rest.split(None, 1)
        if len(parts) < 2 or not parts[1].strip():
            raise ValueError(
                f"{USAGE} — structural search needs a pattern "
                "after its language")
        return {"action": "search", "mode": "structural",
                "query": parts[1].strip(),
                "language": parts[0].lower()}
    return {"action": "search", "mode": "text", "query": text,
            "language": None}


def format_local_search(status: Dict[str, Any]) -> str:
    """One search's account, from an Agent search-status mapping."""
    report = status["report"]
    lines = [
        f"Local search ({LOCAL_SEARCH_SLICE}, {report['mode']}): "
        f"{len(report['matches'])} match(es) for "
        f"{report['query']!r} in {report['files_searched']} of "
        f"{report['files_seen']} file(s) searched "
        f"(ranking: {report['ranking']})."]
    for match in report["matches"]:
        lines.append(
            f"  {match['path']}:{match['line']}:{match['column'] + 1}"
            f"  {match['text']}")
        detail = f"score {match['score']}"
        if match["reasons"]:
            detail += " — " + "; ".join(match["reasons"])
        lines.append(f"      {detail}")
        for capture in match["captures"]:
            lines.append(
                f"      ${capture['name']} = "
                f"{capture['text'] or '(nothing)'}")
    if report["note"]:
        lines.append(f"  {report['note']}")
    for skip in report["skipped"][:20]:
        lines.append(f"  Skipped {skip['path']}: {skip['reason']}")
    for warning in report["warnings"]:
        lines.append(f"  Warning: {warning}")
    lines.append(status["plain_explanation"])
    return "\n".join(lines)


def render_markdown(report: LocalSearchReport) -> str:
    """Render *report* as a human report, from its own record."""
    data = report.record()
    lines = [
        "# Local Search — beyond grep",
        "",
        f"*Slice {LOCAL_SEARCH_SLICE} of the All-Features "
        "road (Part III — Code Intelligence).*",
        "",
        f"**{data['mode']}** search for `{data['query']}`: "
        f"{len(data['matches'])} match(es) in "
        f"{data['files_searched']} of {data['files_seen']} "
        f"file(s) searched (ranking: {data['ranking']}).",
        "",
        "## Matches",
        "",
    ]
    if data["matches"]:
        for match in data["matches"]:
            lines.append(
                f"- **{match['path']}:{match['line']}** — "
                f"`{match['text']}` (score {match['score']}"
                + (": " + "; ".join(match["reasons"])
                   if match["reasons"] else "") + ")")
    else:
        lines.append("- none")
    if data["skipped"]:
        lines += ["", "## Skipped files", ""]
        for skip in data["skipped"]:
            lines.append(f"- **{skip['path']}**: {skip['reason']}")
    if data["warnings"]:
        lines += ["", "## Warnings", ""]
        for warning in data["warnings"]:
            lines.append(f"- {warning}")
    lines.append("")
    return "\n".join(lines)
