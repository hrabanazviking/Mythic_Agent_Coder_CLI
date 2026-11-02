"""Structural rewrite (All-Features roadmap slice M-048).

Part III — Code Intelligence. M-047 taught the coder to find
code by its shape (``foo($A, $$$)`` over the M-043 parses);
this slice is the other half of that census feature: the
same patterns as *safe codemods* — a replacement template
in the same pattern language, per-site diff previews, and
application only through the house edit journal, only for
files that are still exactly what the plan saw.

What ships here, beside M-047's search
(``mythic_agent/tools/structural_search.py`` — this module
compiles and searches through it, never a second parser):

* **The replacement template.** :func:`compile_replacement`
  compiles the replacement through M-047's own machinery
  (:func:`compile_pattern`), so a replacement is exactly as
  grammatical as the pattern it answers. Its metavariables
  are filled per match: a ``$NAME`` placeholder takes the
  text the pattern's ``$NAME`` captured at that site, a
  ``$$$NAME`` placeholder takes the joined text of the
  pattern's ``$$$NAME`` capture. The placeholder spans are
  located in the compiled replacement's parse nodes (their
  byte spans in the substituted replacement text), so a
  repeated metavariable renders the same text everywhere
  it appears.
* **The plan.** :func:`plan_rewrite` searches the workspace
  and turns every match into a :class:`RewriteSite`: the
  matched span (line/column and byte offsets recomputed
  from the source), the rendered replacement, a per-site
  unified-diff preview against the file as it stands, and
  the sha256 of the file's content at plan time, beside the
  file's full new content once all its sites apply. A plan
  writes nothing — it is the preview, as data.
* **The application.** :func:`apply_rewrite` applies a
  plan, and only a plan (no preview, no application, by
  construction): each file is re-read and its hash compared
  with the plan's; a changed file is refused whole and left
  untouched, and the surviving content is written through
  the journal-first :class:`EditJournal` (``core/edits.py``)
  — one journaled write per file, spans applied descending
  at plan time. One file's refusal never blocks the others.
* **The surfaces.** ``Agent.structural_rewrite()`` is the
  tool (preview by default; application only when asked);
  ``/srewrite [apply] <language> <pattern> => <replacement>``
  shows the previews on the terminal and TUI system-command
  roads, sharing this module's parser and formatter.

Honesty rules, pinned by the slice's tests:

* **A replacement that cannot be filled is refused before
  anything is planned.** A replacement that does not parse
  in its language raises :class:`PatternError`, exactly as
  an unparseable pattern does in M-047; so does a
  replacement carrying an unnamed ``$$$`` (there is nothing
  it could be filled with), a replacement metavariable the
  search pattern never captures, and a kind mismatch — a
  name the pattern captures once used as ``$$$NAME`` in
  the replacement, or the other way round.
* **Overlapping sites are refused, never force-edited.**
  Two matches in one file whose spans overlap (nested
  matches are the common case) are each recorded on the
  plan as refused, with the reason; the file's planned new
  content leaves both alone.
* **A stale file is refused whole.** If a file's content
  changed between the plan and the application, its hash
  no longer matches the plan's and nothing in it is
  written — the answer is a fresh plan, not a forced edit.
* **The search's honesty rides along.** Files M-047's
  search skipped are carried on the plan with their
  reasons; Mojo and uncatalogued languages are refused by
  the same errors M-047 raises.
"""

from __future__ import annotations

__all__ = [
    "PLAIN_EXPLANATION",
    "STRUCTURAL_REWRITE_SLICE",
    "CompiledReplacement",
    "FileOutcome",
    "FileRewrite",
    "RewritePlan",
    "RewriteResult",
    "RewriteSite",
    "apply_rewrite",
    "compile_replacement",
    "format_rewrite_status",
    "parse_rewrite_args",
    "plan_rewrite",
    "render_markdown",
    "render_replacement",
]

import difflib
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..core.edits import EditJournal
from ..core.tree_sitter_foundation import LanguageCatalog
from ..core.workspace import canonical_workspace_root
from .structural_search import (
    Capture,
    CompiledPattern,
    PatternError,
    SearchSkippedFile,
    StructuralMatch,
    compile_pattern,
    search_workspace,
)

#: The slice that owns this module.
STRUCTURAL_REWRITE_SLICE = "M-048"

#: The structural rewrite explained in plain words — the
#: sentences every surface shows.
PLAIN_EXPLANATION = (
    "Structural rewrite turns a structural search pattern "
    "into a safe codemod: /srewrite <language> <pattern> => "
    "<replacement> finds every match of the pattern (M-047) "
    "and shows, for each site, the exact diff the "
    "replacement would make there — the replacement is "
    "written in the same pattern language, and its $NAME / "
    "$$$NAME metavariables are filled with what the pattern "
    "captured at that site. A preview writes nothing. "
    "Applying (/srewrite apply ...) writes each file "
    "through the edit journal, and only when the file is "
    "still exactly what the plan saw: a file that changed "
    "since the plan, and sites that overlap another match, "
    "are refused plainly, never force-edited. A replacement "
    "that does not parse, names a metavariable the pattern "
    "never captured, or uses an unnamed $$$ is refused "
    "before anything is planned."
)

_USAGE = "Usage: /srewrite [apply] <language> <pattern> => <replacement>"

#: The metavariable grammar, shared with M-047: the same
#: substitution, so a replacement's placeholders are spelled
#: exactly as the search's are.
_META_RE = re.compile(r"\$\$\$([A-Z][A-Z0-9_]*)?|\$([A-Z][A-Z0-9_]*)")


def _single_spelling(name: str) -> str:
    """The placeholder identifier for ``$NAME`` — M-047's
    own spelling, from its substitution."""
    return f"__mythic_meta_{name.lower()}__"


def _many_spelling(name: Optional[str]) -> str:
    """The placeholder identifier for ``$$$NAME`` (or the
    unnamed ``$$$``) — M-047's own spelling."""
    if name is None:
        return "__mythic_meta_many__"
    return f"__mythic_meta_many_{name.lower()}__"


def _plain_substituted(text: str) -> str:
    """*text* with its metavariables substituted, before any
    context wrap — the replacement's own text, placeholders
    in place of metavariables."""
    def _placeholder(match: "re.Match[str]") -> str:
        many_name, single_name = match.group(1), match.group(2)
        if single_name is not None:
            return _single_spelling(single_name)
        return _many_spelling(many_name)

    return _META_RE.sub(_placeholder, text)


# ---------------------------------------------------------------------------
# compiling a replacement
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CompiledReplacement:
    """One replacement template, compiled through M-047's
    machinery and checked against its search pattern.

    ``compiled`` is the replacement's own
    :class:`CompiledPattern`; every metavariable it uses is
    one the search pattern captures, of the same kind.
    """

    text: str
    language: str
    compiled: CompiledPattern


def compile_replacement(
    text: str, language: str, pattern: CompiledPattern,
    catalog: Optional[LanguageCatalog] = None,
) -> CompiledReplacement:
    """Compile *text* as the replacement for *pattern*.

    The replacement is written in the pattern language,
    with the same metavariables, and compiles through
    :func:`compile_pattern` — so a replacement that does
    not parse in *language* raises :class:`PatternError`,
    and a grammar-less or uncatalogued language raises
    M-047's own errors. Three further refusals, all plain:
    an unnamed ``$$$`` in the replacement (it names no
    capture, so nothing could fill it); a metavariable the
    search pattern never captures; and a kind mismatch —
    a name the pattern captures as ``$NAME`` used as
    ``$$$NAME`` in the replacement, or the other way round.
    """
    compiled = compile_pattern(text, language, catalog=catalog)
    if any(name is None for name in compiled.manys.values()):
        raise PatternError(
            "The replacement uses an unnamed $$$ — it names "
            "no capture, so there is nothing it could be "
            "filled with. Name it ($$$NAME) after a $$$NAME "
            "the search pattern captures.")
    pattern_singles = set(pattern.singles.values())
    pattern_manys = {name for name in pattern.manys.values()
                     if name is not None}
    for name in compiled.singles.values():
        if name in pattern_manys:
            raise PatternError(
                f"${name} is a $$$ metavariable in the search "
                f"pattern (it captures zero or more nodes) but "
                f"a $ metavariable in the replacement (one "
                "node) — one name must mean one thing.")
        if name not in pattern_singles:
            raise PatternError(
                f"The replacement uses ${name}, which the "
                "search pattern never captures — a replacement "
                "can only be filled from the pattern's own "
                "captures.")
    for name in compiled.manys.values():
        if name in pattern_singles:
            raise PatternError(
                f"$$${name} is a $ metavariable in the search "
                f"pattern (it captures one node) but a $$$ "
                "metavariable in the replacement (zero or "
                "more nodes) — one name must mean one thing.")
        if name not in pattern_manys:
            raise PatternError(
                f"The replacement uses $$${name}, which the "
                "search pattern never captures — a replacement "
                "can only be filled from the pattern's own "
                "captures.")
    return CompiledReplacement(
        text=text, language=compiled.language, compiled=compiled)


def _placeholder_spans(
    compiled: CompiledPattern,
) -> List[Tuple[int, int, str]]:
    """Every placeholder occurrence in a compiled template:
    (start_byte, end_byte, capture_name) in the coordinates
    of its ``substituted_text``.

    The occurrences are the parse nodes whose own text is
    exactly a placeholder identifier — the same test M-047's
    matcher applies — found by walking the template's
    pattern nodes. Spans are deduplicated: a node and its
    child never both carry one site.
    """
    raw = compiled.substituted_text.encode("utf-8")
    names: Dict[str, str] = {}
    for placeholder, name in compiled.singles.items():
        names[placeholder] = name
    for placeholder, name in compiled.manys.items():
        if name is not None:
            names[placeholder] = name
    found: Dict[Tuple[int, int], Tuple[int, int, str]] = {}
    for top in compiled.nodes:
        for node in top.walk():
            text = raw[node.start_byte:node.end_byte].decode(
                "utf-8", errors="replace")
            name = names.get(text)
            if name is not None:
                found[(node.start_byte, node.end_byte)] = (
                    node.start_byte, node.end_byte, name)
    return sorted(found.values())


def render_replacement(replacement: CompiledReplacement,
                       match: StructuralMatch) -> str:
    """Render *replacement* for one *match*: every
    placeholder span in the template is filled with the
    text the match captured under that name, so a repeated
    metavariable renders the same text everywhere.

    The rendering works on the template's plain substituted
    text — the replacement as written, placeholders in
    place — so context-wrap scaffolding M-047 may have
    parsed the template inside (Go, Rust) never leaks into
    the rendered code.
    """
    compiled = replacement.compiled
    candidate = compiled.substituted_text.encode("utf-8")
    plain = _plain_substituted(replacement.text).encode("utf-8")
    offset = candidate.find(plain)
    if offset < 0:  # the bare parse: the candidate is the plain text
        offset = 0
        plain = candidate
    captures = {capture.name: capture.text
                for capture in match.captures}
    rendered = plain
    spans = [
        (start - offset, end - offset, name)
        for start, end, name in _placeholder_spans(compiled)
        if offset <= start and end <= offset + len(plain)
    ]
    for start, end, name in sorted(spans, reverse=True):
        rendered = (rendered[:start]
                    + captures.get(name, "").encode("utf-8")
                    + rendered[end:])
    return rendered.decode("utf-8")


# ---------------------------------------------------------------------------
# spans: byte offsets for a match, recomputed from its source
# ---------------------------------------------------------------------------

def _match_byte_span(source: str,
                     match: StructuralMatch) -> Tuple[int, int]:
    """The (start_byte, end_byte) of *match* in *source*.

    :class:`StructuralMatch` carries line/column spans, not
    byte offsets; the columns the M-043 backends report are
    byte columns within their line (tree-sitter points and
    the ast fallback's ``col_offset`` alike), so the byte
    offset is the line's start byte plus the column.
    """
    raw = source.encode("utf-8")
    line_starts = [0]
    for line in raw.splitlines(keepends=True):
        line_starts.append(line_starts[-1] + len(line))
    start = line_starts[match.line - 1] + match.column
    end = line_starts[match.end_line - 1] + match.end_column
    return start, end


# ---------------------------------------------------------------------------
# the plan
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RewriteSite:
    """One match turned into a planned edit: its span, its
    rendered replacement, its own diff preview, and its
    standing — planned, or refused with the reason."""

    path: str
    line: int
    column: int
    end_line: int
    end_column: int
    start_byte: int
    end_byte: int
    text: str
    captures: Tuple[Capture, ...]
    replacement: str
    diff: str
    status: str
    refusal_reason: Optional[str]

    def record(self) -> Dict[str, object]:
        """This site as a plain mapping."""
        return {
            "path": self.path, "line": self.line,
            "column": self.column, "end_line": self.end_line,
            "end_column": self.end_column,
            "start_byte": self.start_byte,
            "end_byte": self.end_byte, "text": self.text,
            "captures": [c.record() for c in self.captures],
            "replacement": self.replacement, "diff": self.diff,
            "status": self.status,
            "refusal_reason": self.refusal_reason,
        }


@dataclass(frozen=True)
class FileRewrite:
    """One file's planned outcome: the sha256 of its content
    at plan time and its full new content once every planned
    site in it applies."""

    path: str
    sha256: str
    new_content: str
    planned_sites: int
    refused_sites: int

    def record(self) -> Dict[str, object]:
        """This file plan as a plain mapping."""
        return {
            "path": self.path, "sha256": self.sha256,
            "new_content": self.new_content,
            "planned_sites": self.planned_sites,
            "refused_sites": self.refused_sites,
        }


@dataclass(frozen=True)
class RewritePlan:
    """One planned rewrite: every site with its preview,
    every file's planned content and plan-time hash, and
    the search's honest skips and warnings riding along."""

    workspace: str
    language: str
    pattern: str
    replacement: str
    sites: Tuple[RewriteSite, ...]
    files: Tuple[FileRewrite, ...]
    skipped: Tuple[SearchSkippedFile, ...]
    warnings: Tuple[str, ...]
    files_seen: int
    files_searched: int

    def record(self) -> Dict[str, object]:
        """This plan as a plain mapping."""
        planned = sum(1 for s in self.sites
                      if s.status == "planned")
        return {
            "slice": STRUCTURAL_REWRITE_SLICE,
            "workspace": self.workspace,
            "language": self.language, "pattern": self.pattern,
            "replacement": self.replacement,
            "sites": [s.record() for s in self.sites],
            "files": [f.record() for f in self.files],
            "skipped": [s.record() for s in self.skipped],
            "warnings": list(self.warnings),
            "files_seen": self.files_seen,
            "files_searched": self.files_searched,
            "counts": {
                "matches": len(self.sites), "planned": planned,
                "refused": len(self.sites) - planned,
                "files": len(self.files),
            },
        }


def _apply_sites(raw: bytes, sites: List[RewriteSite]) -> bytes:
    """*raw* with *sites*' rendered replacements applied,
    spans descending so earlier spans stay true."""
    out = raw
    for site in sorted(sites, key=lambda s: s.start_byte,
                       reverse=True):
        out = (out[:site.start_byte]
               + site.replacement.encode("utf-8")
               + out[site.end_byte:])
    return out


def _site_diff(path: str, original: str, site: RewriteSite,
               raw: bytes) -> str:
    """The unified diff of *original* with only *site*
    applied — each site's preview stands on its own."""
    changed = _apply_sites(raw, [site]).decode("utf-8")
    return "".join(difflib.unified_diff(
        original.splitlines(keepends=True),
        changed.splitlines(keepends=True),
        fromfile=path, tofile=path))


def plan_rewrite(
    root: Path | str, pattern_text: str, replacement_text: str,
    language: str,
    *,
    catalog: Optional[LanguageCatalog] = None,
) -> RewritePlan:
    """Plan a structural rewrite over the workspace at *root*.

    Compiles the pattern and the replacement (their
    refusals ride through), runs M-047's workspace search,
    and turns every match into a site with its rendered
    replacement and per-site diff preview. Matches in one
    file whose spans overlap are each marked refused, with
    the reason — neither is applied. A file that cannot be
    re-read at plan time is recorded in ``skipped`` with
    the reason. Planning writes nothing.
    """
    pattern = compile_pattern(pattern_text, language,
                              catalog=catalog)
    replacement = compile_replacement(
        replacement_text, language, pattern, catalog=catalog)
    result = search_workspace(root, pattern, catalog=catalog)
    workspace = canonical_workspace_root(root)
    skipped: List[SearchSkippedFile] = list(result.skipped)

    by_path: Dict[str, List[StructuralMatch]] = {}
    for match in result.matches:
        by_path.setdefault(match.path, []).append(match)

    sites: List[RewriteSite] = []
    files: List[FileRewrite] = []
    for path in sorted(by_path):
        try:
            raw = (workspace / path).read_bytes()
        except OSError as exc:
            skipped.append(SearchSkippedFile(
                path, f"unreadable at plan time: {exc}"))
            continue
        try:
            original = raw.decode("utf-8")
        except UnicodeDecodeError:
            skipped.append(SearchSkippedFile(
                path, "not utf-8 text at plan time"))
            continue
        file_sites: List[RewriteSite] = []
        for match in by_path[path]:
            start, end = _match_byte_span(original, match)
            file_sites.append(RewriteSite(
                path=path, line=match.line, column=match.column,
                end_line=match.end_line,
                end_column=match.end_column, start_byte=start,
                end_byte=end, text=match.text,
                captures=match.captures,
                replacement=render_replacement(replacement, match),
                diff="", status="planned", refusal_reason=None))
        # Overlapping spans in one file are refused, each
        # with its reason — nested matches land here.
        refused: Dict[int, str] = {}
        for i, site in enumerate(file_sites):
            for j, other in enumerate(file_sites):
                if i != j and site.start_byte < other.end_byte \
                        and other.start_byte < site.end_byte:
                    refused[i] = (
                        "this site's span overlaps another "
                        f"match in {path} (line {other.line}) — "
                        "overlapping sites are refused, never "
                        "force-edited")
                    break
        settled: List[RewriteSite] = []
        for i, site in enumerate(file_sites):
            status = "refused" if i in refused else "planned"
            settled.append(RewriteSite(
                path=site.path, line=site.line,
                column=site.column, end_line=site.end_line,
                end_column=site.end_column,
                start_byte=site.start_byte, end_byte=site.end_byte,
                text=site.text, captures=site.captures,
                replacement=site.replacement,
                diff=_site_diff(path, original, site, raw),
                status=status, refusal_reason=refused.get(i)))
        planned = [s for s in settled if s.status == "planned"]
        new_content = _apply_sites(raw, planned).decode("utf-8")
        files.append(FileRewrite(
            path=path,
            sha256=hashlib.sha256(raw).hexdigest(),
            new_content=new_content,
            planned_sites=len(planned),
            refused_sites=len(settled) - len(planned)))
        sites.extend(settled)
    sites.sort(key=lambda s: (s.path, s.line, s.column))
    return RewritePlan(
        workspace=str(workspace), language=pattern.language,
        pattern=pattern_text, replacement=replacement_text,
        sites=tuple(sites), files=tuple(files),
        skipped=tuple(skipped), warnings=result.warnings,
        files_seen=result.files_seen,
        files_searched=result.files_searched)


# ---------------------------------------------------------------------------
# the application
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FileOutcome:
    """One file's application outcome: applied, refused
    (stale or overlap), or errored — always with the reason
    when it was not applied."""

    path: str
    status: str
    reason: str
    sites_applied: int

    def record(self) -> Dict[str, object]:
        """This outcome as a plain mapping."""
        return {
            "path": self.path, "status": self.status,
            "reason": self.reason,
            "sites_applied": self.sites_applied,
        }


@dataclass(frozen=True)
class RewriteResult:
    """One applied plan: the plan itself (previews included)
    and every file's outcome."""

    workspace: str
    plan: RewritePlan
    outcomes: Tuple[FileOutcome, ...]

    def record(self) -> Dict[str, object]:
        """This result as a plain mapping."""
        counts: Dict[str, int] = {}
        for outcome in self.outcomes:
            counts[outcome.status] = counts.get(outcome.status, 0) + 1
        return {
            "slice": STRUCTURAL_REWRITE_SLICE,
            "workspace": self.workspace,
            "plan": self.plan.record(),
            "outcomes": [o.record() for o in self.outcomes],
            "counts": counts,
        }


def apply_rewrite(root: Path | str,
                  plan: RewritePlan) -> RewriteResult:
    """Apply *plan* — and only a plan: application exists
    nowhere else, so no site is ever applied without its
    preview.

    Per file with planned sites: the file is re-read and
    its sha256 compared with the plan's. A mismatch refuses
    the whole file (``refused-stale``) and writes nothing
    in it. A file whose sites were all refused at plan time
    is ``refused-overlap``. Otherwise the planned new
    content is written through :class:`EditJournal` — one
    journaled write per file. A failure on one file is
    recorded and never blocks the others.
    """
    workspace = canonical_workspace_root(root)
    journal: Optional[EditJournal] = None
    outcomes: List[FileOutcome] = []
    for file_plan in plan.files:
        file_sites = [s for s in plan.sites
                      if s.path == file_plan.path]
        planned = [s for s in file_sites if s.status == "planned"]
        if not planned:
            reason = (file_sites[0].refusal_reason
                      if file_sites and
                      file_sites[0].refusal_reason
                      else "no applicable sites in this file")
            outcomes.append(FileOutcome(
                file_plan.path, "refused-overlap", reason, 0))
            continue
        try:
            raw = (workspace / file_plan.path).read_bytes()
        except OSError as exc:
            outcomes.append(FileOutcome(
                file_plan.path, "error",
                f"unreadable at apply time: {exc}", 0))
            continue
        if hashlib.sha256(raw).hexdigest() != file_plan.sha256:
            outcomes.append(FileOutcome(
                file_plan.path, "refused-stale",
                "the file changed since the plan was made — "
                "its content no longer matches the plan's "
                "hash, so the whole file is refused and "
                "nothing in it was written; plan again to "
                "rewrite its new shape", 0))
            continue
        try:
            if journal is None:
                journal = EditJournal(workspace)
            journal.write(file_plan.path, file_plan.new_content)
        except Exception as exc:
            outcomes.append(FileOutcome(
                file_plan.path, "error", str(exc), 0))
            continue
        outcomes.append(FileOutcome(
            file_plan.path, "applied", "", len(planned)))
    return RewriteResult(
        workspace=str(workspace), plan=plan,
        outcomes=tuple(outcomes))


# ---------------------------------------------------------------------------
# surfaces: the shared parser + formatters
# ---------------------------------------------------------------------------

def parse_rewrite_args(text: Any) -> Dict[str, Any]:
    """Parse the ``/srewrite`` slash-command argument string.

    Grammar::

        /srewrite <language> <pattern> => <replacement>
        /srewrite apply <language> <pattern> => <replacement>

    The first form previews; the ``apply`` form previews
    and applies. The language is the first word; the
    pattern and the replacement are split on the first
    `` => `` — both are code, and their spaces are their
    own. Returns a dict with keys ``action`` (``preview``
    or ``apply``), ``language``, ``pattern`` and
    ``replacement``. Raises :class:`ValueError` on a usage
    error.
    """
    if text is None:
        text = ""
    if not isinstance(text, str):
        raise ValueError(
            f"Rewrite arguments must be text, "
            f"got {type(text).__name__}")
    stripped = text.strip()
    if not stripped:
        raise ValueError(_USAGE)
    action = "preview"
    first, _, remainder = stripped.partition(" ")
    if first.lower() == "apply":
        action = "apply"
        stripped = remainder.strip()
        if not stripped:
            raise ValueError(_USAGE)
    language, _, tail = stripped.partition(" ")
    pattern, separator, replacement = tail.partition(" => ")
    pattern = pattern.strip()
    replacement = replacement.strip()
    if not separator or not language or not pattern \
            or not replacement:
        raise ValueError(_USAGE)
    return {"action": action, "language": language.lower(),
            "pattern": pattern, "replacement": replacement}


def _one_line(text: str) -> str:
    """*text* on one line for a surface: the first line,
    with a marker when the text runs on."""
    lines = text.splitlines()
    if len(lines) <= 1:
        return text.strip()
    return lines[0].rstrip() + " …"


def format_rewrite_status(status: Dict[str, Any]) -> str:
    """The rewrite report, from an Agent rewrite-status
    mapping — the plan's previews, and the outcomes when
    the plan was applied."""
    result = status["result"]
    applied = "outcomes" in result
    plan = result["plan"] if applied else result
    counts = plan["counts"]
    verb = "applied" if applied else "preview only — nothing written"
    lines = [
        f"Structural rewrite ({STRUCTURAL_REWRITE_SLICE}): "
        f"{counts['matches']} site(s) for {plan['pattern']!r} "
        f"=> {plan['replacement']!r} in {plan['language']} "
        f"({counts['planned']} planned, {counts['refused']} "
        f"refused) — {verb}."]
    for site in plan["sites"]:
        lines.append(
            f"  {site['path']}:{site['line']}:"
            f"{site['column'] + 1}  "
            f"{_one_line(site['text'])} -> "
            f"{_one_line(site['replacement'])}")
        if site["status"] != "planned":
            lines.append(f"      refused: {site['refusal_reason']}")
        for diff_line in site["diff"].splitlines():
            lines.append(f"    {diff_line}")
    if not plan["sites"]:
        lines.append(
            "  No code in this workspace is shaped like the "
            "pattern — nothing to rewrite, and that is the "
            "answer, not an error.")
    if applied:
        for outcome in result["outcomes"]:
            detail = f" — {outcome['reason']}" if outcome["reason"] \
                else f" ({outcome['sites_applied']} site(s))"
            lines.append(
                f"  {outcome['status']}: {outcome['path']}{detail}")
    for skip in plan["skipped"]:
        lines.append(f"  Skipped {skip['path']}: {skip['reason']}")
    for warning in plan["warnings"]:
        lines.append(f"  Warning: {warning}")
    lines.append(status["plain_explanation"])
    return "\n".join(lines)


def render_markdown(plan: RewritePlan) -> str:
    """Render *plan* as a human report, built from its own
    sites, previews, and skips."""
    record = plan.record()
    counts = record["counts"]  # type: ignore[attr-defined]
    lines = [
        "# Structural Rewrite — the same patterns as safe codemods",
        "",
        f"*Slice {STRUCTURAL_REWRITE_SLICE} of the All-Features "
        "road (Part III — Code Intelligence). Every site "
        "carries its own diff preview; nothing is applied "
        "without one.*",
        "",
        f"**Pattern** `{plan.pattern}` => `{plan.replacement}` "
        f"({plan.language}): {counts['matches']} site(s), "
        f"{counts['planned']} planned, {counts['refused']} "
        "refused.",
        "",
        "## Sites",
        "",
    ]
    if plan.sites:
        for site in plan.sites:
            lines.append(
                f"- **{site.path}:{site.line}** — "
                f"`{_one_line(site.text)}` -> "
                f"`{_one_line(site.replacement)}` "
                f"({site.status})")
            if site.refusal_reason:
                lines.append(f"  - refused: {site.refusal_reason}")
            if site.diff:
                lines += ["", "  ```diff"]
                lines += [f"  {line}"
                          for line in site.diff.splitlines()]
                lines += ["  ```", ""]
    else:
        lines.append("- none")
    if plan.skipped:
        lines += ["", "## Skipped files", ""]
        for skip in plan.skipped:
            lines.append(f"- **{skip.path}**: {skip.reason}")
    if plan.warnings:
        lines += ["", "## Warnings", ""]
        for warning in plan.warnings:
            lines.append(f"- {warning}")
    lines.append("")
    return "\n".join(lines)
