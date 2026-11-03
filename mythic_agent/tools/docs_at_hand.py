"""Docs-at-hand (M-060).

Part III — Code Intelligence. The roadmap's words for
this slice: "the project's own docs, plus offline doc
packs for its stack, searchable from the TUI (the Mojo
Docs MCP pattern, generalised)."

What ships here, in ``mythic_agent/tools/docs_at_hand.py``:

* **Discovery.** The workspace's own documentation —
  Markdown, plain-text and reStructuredText files at the
  project root and under ``docs/`` — plus *offline doc
  packs*: any directory under ``.mythic/docpacks/`` is a
  pack for one piece of the stack (a library, a language,
  a tool), and every doc file inside it joins the shelf.
  Each doc is catalogued with its title (its first
  heading, else its first line), its source (``project``
  or the pack's name) and its size.
* **Search.** An in-process index over titles, headings
  and body text. A query's terms score a doc — a title
  match earns most, then headings, then body frequency —
  and every hit carries its score, its reasons, a
  snippet and the line the snippet came from. No
  external index, no daemon, no network.
* **Read.** One doc read whole by name — its shelf path,
  its file name, or its title — under a character cap
  that names itself when it cuts.
* **The surfaces.** ``Agent.docs_list()`` /
  ``Agent.docs_search()`` / ``Agent.docs_read()`` and
  ``/docs`` on the terminal and TUI system-command
  roads, sharing this module's parser and formatter:
  ``/docs list``, ``/docs search <query...>`` and
  ``/docs read <name...>``. The setting ``docs_at_hand``
  (on by default) closes the road plainly when the user
  says so.

Honesty rules, pinned by the slice's tests:

* **Offline means offline.** This module contains no
  network road at all — docs-at-hand is the complement
  to M-059's web tools, never a hidden second door to
  them. A doc that is not on the shelf is reported as
  absent, never fetched and never invented.
* **A name is never guessed.** A read name matching no
  doc is an error report naming the miss; a name
  matching several docs is refused with the candidates
  listed.
* **The shelf stays the shelf.** Paths escaping the
  doc roots (the project root, ``docs/``, a pack dir)
  are refused; symlinked escapes are resolved and
  refused the same way.
* **Caps name themselves.** Search results and read
  text are bounded, and every cut is named in the
  report's warnings.
* **Off means off.** With ``docs_at_hand`` false, no
  file is read on this road at all.
"""

from __future__ import annotations

__all__ = [
    "DOCS_SLICE",
    "DOC_EXTENSIONS",
    "MAX_DOC_BYTES",
    "MAX_HITS",
    "MAX_READ_CHARS",
    "PACKS_DIRNAME",
    "PLAIN_EXPLANATION",
    "USAGE",
    "DocEntry",
    "DocHit",
    "DocsReport",
    "discover_docs",
    "docs_list",
    "docs_read",
    "docs_search",
    "enabled_from_config",
    "format_docs_report",
    "parse_docs_args",
    "render_markdown",
]

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

DOCS_SLICE = "M-060"

#: File kinds that count as documentation on the shelf.
DOC_EXTENSIONS = (".md", ".txt", ".rst")

#: Where offline doc packs live, inside the workspace:
#: ``.mythic/docpacks/<pack-name>/<doc files...>``.
PACKS_DIRNAME = Path(".mythic") / "docpacks"

#: A doc file past this size is catalogued but not
#: indexed or read — and the report says so.
MAX_DOC_BYTES = 1_000_000

#: How many hits one search reports; the cut is named.
MAX_HITS = 10

#: How much of one doc a read returns; the cut is named.
MAX_READ_CHARS = 20_000

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.*)$")
_RST_HEADING_RE = re.compile(r"^[=\-~^\"#]{3,}$")

PLAIN_EXPLANATION = (
    "Docs-at-hand keeps the project's own documentation "
    "within reach, offline: /docs list shows the shelf "
    "(the project's root and docs/ files, plus any doc "
    "packs under .mythic/docpacks/), /docs search <query> "
    "ranks the shelf's docs by title, heading and body "
    "matches with a snippet for each hit, and /docs read "
    "<name> shows one doc. Nothing is fetched from "
    "anywhere — a doc that is not on the shelf is "
    "reported absent, never invented."
)

USAGE = "Usage: /docs list | /docs search <query...> | /docs read <name...>"


def enabled_from_config(config: Optional[Dict[str, Any]]) -> bool:
    """Docs-at-hand is on unless config says so."""
    if not config:
        return True
    return config.get("docs_at_hand", True) is not False


def _tokens(text: str) -> List[str]:
    return _TOKEN_RE.findall((text or "").lower())


def _title_of(text: str, fallback: str) -> str:
    """A doc's title: first heading, else first plain line."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        heading = _HEADING_RE.match(line)
        if heading:
            return heading.group(1).strip()
        if i + 1 < len(lines) and _RST_HEADING_RE.match(
                lines[i + 1].strip()) and len(stripped) > 2:
            return stripped
        return stripped[:120]
    return fallback


# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DocEntry:
    """One doc on the shelf."""

    path: str  # path relative to the workspace root
    title: str
    source: str  # "project" or the pack's name
    size_bytes: int
    indexed: bool = True

    def record(self) -> Dict[str, Any]:
        return {"path": self.path, "title": self.title,
                "source": self.source,
                "size_bytes": self.size_bytes,
                "indexed": self.indexed}


@dataclass(frozen=True)
class DocHit:
    """One search hit — a doc, its score, and its proof."""

    entry: DocEntry
    score: int
    reasons: List[str]
    snippet: str
    line: int

    def record(self) -> Dict[str, Any]:
        data = self.entry.record()
        data.update({"score": self.score,
                     "reasons": list(self.reasons),
                     "snippet": self.snippet, "line": self.line})
        return data


@dataclass
class DocsReport:
    """One docs call's whole account."""

    kind: str = "list"  # list | search | read
    query: str = ""
    name: str = ""
    status: str = "ok"  # ok | disabled | error
    docs: List[DocEntry] = field(default_factory=list)
    hits: List[DocHit] = field(default_factory=list)
    doc: Optional[DocEntry] = None
    text: str = ""
    warnings: List[str] = field(default_factory=list)
    truncated: bool = False
    note: str = ""

    def record(self) -> Dict[str, Any]:
        return {"kind": self.kind, "query": self.query,
                "name": self.name, "status": self.status,
                "docs": [d.record() for d in self.docs],
                "hits": [h.record() for h in self.hits],
                "doc": self.doc.record() if self.doc else None,
                "text": self.text,
                "warnings": list(self.warnings),
                "truncated": self.truncated,
                "note": self.note}


# ---------------------------------------------------------------------------
# Discovery + the in-process index
# ---------------------------------------------------------------------------

def _doc_files(root: Path) -> List[Path]:
    """Every doc file under *root*, in deterministic order."""
    if not root.is_dir():
        return []
    found = [p for p in root.rglob("*")
             if p.is_file() and p.suffix.lower() in DOC_EXTENSIONS]
    return sorted(found, key=lambda p: p.as_posix())


def _read_text(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def discover_docs(workspace: Any) -> List[DocEntry]:
    """Catalogue the shelf: project docs + offline doc packs.

    Project docs are the doc files at the workspace root
    and under ``docs/``; a pack is any directory under
    ``.mythic/docpacks/`` and every doc file inside it.
    A file past :data:`MAX_DOC_BYTES` is catalogued with
    ``indexed=False`` — present, but not searched or read.
    """
    root = Path(workspace)
    entries: List[DocEntry] = []
    seen: set = set()

    def add(path: Path, source: str) -> None:
        try:
            resolved = path.resolve()
        except OSError:
            return
        if resolved in seen:
            return
        seen.add(resolved)
        try:
            rel = resolved.relative_to(root.resolve()).as_posix()
        except (ValueError, OSError):
            return
        try:
            size = resolved.stat().st_size
        except OSError:
            return
        text = _read_text(resolved) if size <= MAX_DOC_BYTES else None
        title = (_title_of(text, resolved.stem)
                 if text is not None else resolved.stem)
        entries.append(DocEntry(
            path=rel, title=title, source=source,
            size_bytes=size, indexed=size <= MAX_DOC_BYTES))

    for path in sorted(root.glob("*"), key=lambda p: p.as_posix()):
        if path.is_file() and path.suffix.lower() in DOC_EXTENSIONS:
            add(path, "project")
    for path in _doc_files(root / "docs"):
        add(path, "project")
    packs_root = root / PACKS_DIRNAME
    if packs_root.is_dir():
        for pack in sorted(packs_root.iterdir(),
                           key=lambda p: p.as_posix()):
            if pack.is_dir():
                for path in _doc_files(pack):
                    add(path, pack.name)
    return sorted(entries, key=lambda e: (e.source, e.path))


class _IndexedDoc:
    """One doc's searchable shape, built once per call."""

    def __init__(self, entry: DocEntry, text: str) -> None:
        self.entry = entry
        self.lines = text.splitlines()
        self.title_tokens = set(_tokens(entry.title))
        self.heading_tokens: set = set()
        self.body_counts: Dict[str, int] = {}
        for line in self.lines:
            heading = _HEADING_RE.match(line)
            if heading:
                self.heading_tokens.update(_tokens(heading.group(1)))
            for token in _tokens(line):
                self.body_counts[token] = \
                    self.body_counts.get(token, 0) + 1


def _index(workspace: Path,
           entries: List[DocEntry]) -> List[_IndexedDoc]:
    indexed: List[_IndexedDoc] = []
    for entry in entries:
        if not entry.indexed:
            continue
        text = _read_text(workspace / entry.path)
        if text is None:
            continue
        indexed.append(_IndexedDoc(entry, text))
    return indexed


def _snippet(doc: _IndexedDoc, terms: List[str]) -> (str, int):
    """The first body line naming a term, with its number."""
    wanted = set(terms)
    for number, line in enumerate(doc.lines, start=1):
        if wanted & set(_tokens(line)):
            return " ".join(line.split())[:200], number
    if doc.lines:
        return " ".join(doc.lines[0].split())[:200], 1
    return "", 0


# ---------------------------------------------------------------------------
# The three tools
# ---------------------------------------------------------------------------

def _closed(kind: str) -> DocsReport:
    return DocsReport(
        kind=kind, status="disabled",
        note=("docs-at-hand is off (the docs_at_hand "
              "setting), so no doc file was read"))


def docs_list(workspace: Any, *, enabled: bool = True) -> DocsReport:
    """The shelf's catalogue — every doc, source and title."""
    report = DocsReport(kind="list")
    if not enabled:
        return _closed("list")
    report.docs = discover_docs(workspace)
    if not report.docs:
        report.note = ("the shelf is empty — no doc files at "
                       "the project root or under docs/, and "
                       "no packs under .mythic/docpacks/")
    return report


def docs_search(workspace: Any, query: str, *, enabled: bool = True,
                max_hits: int = MAX_HITS) -> DocsReport:
    """Rank the shelf against *query*, best doc first.

    Raises :class:`ValueError` for an empty query. A
    query matching nothing is an honest empty report,
    never an error dressed as results.
    """
    if max_hits <= 0:
        raise ValueError("max_hits must be positive")
    text = (query or "").strip()
    report = DocsReport(kind="search", query=text)
    if not enabled:
        return _closed("search")
    if not text:
        raise ValueError(f"{USAGE} — a search needs its query")
    terms = _tokens(text)
    root = Path(workspace)
    entries = discover_docs(root)
    report.docs = entries
    hits: List[DocHit] = []
    for doc in _index(root, entries):
        score = 0
        reasons: List[str] = []
        title_hits = [t for t in terms if t in doc.title_tokens]
        if title_hits:
            earned = 50 * len(title_hits)
            score += earned
            reasons.append(
                f"title names {', '.join(title_hits)} (+{earned})")
        heading_hits = [t for t in terms
                        if t in doc.heading_tokens
                        and t not in title_hits]
        if heading_hits:
            earned = 20 * len(heading_hits)
            score += earned
            reasons.append(
                f"a heading names {', '.join(heading_hits)} "
                f"(+{earned})")
        body_total = 0
        for term in terms:
            count = doc.body_counts.get(term, 0)
            if count:
                body_total += min(count, 10)
        if body_total:
            score += body_total
            reasons.append(
                f"the body names the query terms {body_total} "
                f"time(s), capped per term (+{body_total})")
        if score:
            snippet, line = _snippet(doc, terms)
            hits.append(DocHit(entry=doc.entry, score=score,
                               reasons=reasons, snippet=snippet,
                               line=line))
    hits.sort(key=lambda h: (-h.score, h.entry.path))
    if len(hits) > max_hits:
        report.truncated = True
        report.warnings.append(
            f"hit cap reached ({max_hits}); "
            f"{len(hits) - max_hits} further doc(s) matched "
            "and were not shown")
        hits = hits[:max_hits]
    report.hits = hits
    if not hits:
        report.note = ("no doc on the shelf names those terms — "
                       "that is the answer, not an error")
    return report


def _resolve(entries: List[DocEntry], name: str) -> List[DocEntry]:
    """Every doc *name* could mean, most exact first."""
    wanted = (name or "").strip()
    lowered = wanted.lower()
    exact = [e for e in entries if e.path == wanted]
    if exact:
        return exact
    by_name = [e for e in entries
               if Path(e.path).name.lower() == lowered]
    if by_name:
        return by_name
    return [e for e in entries if e.title.lower() == lowered]


def docs_read(workspace: Any, name: str, *, enabled: bool = True,
              max_chars: int = MAX_READ_CHARS) -> DocsReport:
    """Read one doc whole, by shelf path, file name or title.

    A name matching nothing is an ``error`` report; a
    name matching several docs is refused with the
    candidates named — a doc is never guessed. A path
    escaping the shelf is refused the same way.
    """
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    wanted = (name or "").strip()
    report = DocsReport(kind="read", name=wanted)
    if not enabled:
        return _closed("read")
    if not wanted:
        raise ValueError(f"{USAGE} — a read needs its doc's name")
    root = Path(workspace)
    entries = discover_docs(root)
    matches = _resolve(entries, wanted)
    if not matches:
        report.status = "error"
        report.note = (f"no doc on the shelf answers to "
                       f"{wanted!r} — nothing was read and "
                       "nothing is invented here")
        return report
    if len(matches) > 1:
        report.status = "error"
        report.note = (
            f"{wanted!r} names {len(matches)} docs — "
            "name one by its shelf path: "
            + ", ".join(e.path for e in matches))
        return report
    entry = matches[0]
    report.doc = entry
    if not entry.indexed:
        report.status = "error"
        report.note = (f"{entry.path} is on the shelf but past "
                       f"the size bound ({MAX_DOC_BYTES} bytes), "
                       "so it is catalogued, not read")
        return report
    path = root / entry.path
    try:
        resolved = path.resolve()
        resolved.relative_to(root.resolve())
    except (ValueError, OSError):
        report.status = "error"
        report.note = (f"{entry.path} resolves outside the "
                       "workspace — refused, nothing was read")
        return report
    text = _read_text(path)
    if text is None:
        report.status = "error"
        report.note = (f"{entry.path} could not be read — "
                       "nothing is invented here")
        return report
    if len(text) > max_chars:
        report.truncated = True
        report.warnings.append(
            f"text cap reached ({max_chars} characters); the "
            "rest of the doc was not shown")
        text = text[:max_chars]
    report.text = text
    return report


# ---------------------------------------------------------------------------
# Surfaces: the shared parser + formatters
# ---------------------------------------------------------------------------

def parse_docs_args(arguments: str) -> Dict[str, Any]:
    """Parse ``/docs`` arguments into a docs request.

    Grammar::

        /docs list
        /docs search <query...>
        /docs read <name...>

    Raises :class:`ValueError` on a usage error.
    """
    text = (arguments or "").strip()
    if not text:
        raise ValueError(USAGE)
    tokens = text.split(None, 1)
    head = tokens[0].lower()
    rest = tokens[1].strip() if len(tokens) > 1 else ""
    if head == "list":
        if rest:
            raise ValueError(f"{USAGE} — list takes no argument")
        return {"action": "list"}
    if head == "search":
        if not rest:
            raise ValueError(f"{USAGE} — a search needs its query")
        return {"action": "search", "query": rest}
    if head == "read":
        if not rest:
            raise ValueError(f"{USAGE} — a read needs its doc's name")
        return {"action": "read", "name": rest}
    raise ValueError(f"{USAGE} — the roads are list, search and read")


def format_docs_report(status: Dict[str, Any]) -> str:
    """One docs call's account, from an Agent docs-status mapping."""
    report = status["report"]
    if report["kind"] == "list":
        lines = [f"Docs-at-hand ({DOCS_SLICE}): "
                 f"{len(report['docs'])} doc(s) on the shelf."]
        for doc in report["docs"]:
            lines.append(
                f"  [{doc['source']}] {doc['path']} — {doc['title']}")
    elif report["kind"] == "search":
        lines = [f"Docs search ({DOCS_SLICE}): "
                 f"{len(report['hits'])} hit(s) for "
                 f"{report['query']!r}."]
        for hit in report["hits"]:
            lines.append(
                f"  [{hit['score']}] {hit['path']} — {hit['title']}")
            lines.append(
                f"      line {hit['line']}: {hit['snippet']}")
            for reason in hit["reasons"]:
                lines.append(f"      {reason}")
    else:
        doc = report["doc"] or {}
        lines = [f"Docs read ({DOCS_SLICE}): "
                 f"{doc.get('path', report['name'])} — "
                 f"{doc.get('title', '')}"]
        if report["text"]:
            lines.append(report["text"])
    if report["note"]:
        lines.append(f"  {report['note']}")
    for warning in report["warnings"]:
        lines.append(f"  Warning: {warning}")
    lines.append(status["plain_explanation"])
    return "\n".join(lines)


def render_markdown(report: DocsReport) -> str:
    """Render *report* as a human report, from its own record."""
    data = report.record()
    lines = [
        "# Docs-at-Hand — the shelf",
        "",
        f"*Slice {DOCS_SLICE} of the All-Features road "
        "(Part III — Code Intelligence).*",
        "",
    ]
    if data["kind"] == "list":
        lines.append(f"**{len(data['docs'])} doc(s)** on the shelf:")
        lines.append("")
        for doc in data["docs"]:
            lines.append(
                f"- [{doc['source']}] `{doc['path']}` — {doc['title']}")
    elif data["kind"] == "search":
        lines.append(
            f"**Search** for `{data['query']}`: "
            f"{len(data['hits'])} hit(s).")
        lines += ["", "## Hits", ""]
        if data["hits"]:
            for hit in data["hits"]:
                lines.append(
                    f"- `{hit['path']}` ({hit['score']}): "
                    f"{hit['snippet']}")
        else:
            lines.append("- none")
    else:
        doc = data["doc"] or {}
        lines.append(f"**Read** `{doc.get('path', data['name'])}`.")
        lines += ["", data["text"] or "(no text)"]
    if data["warnings"]:
        lines += ["", "## Warnings", ""]
        for warning in data["warnings"]:
            lines.append(f"- {warning}")
    lines.append("")
    return "\n".join(lines)
