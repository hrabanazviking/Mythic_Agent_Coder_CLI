"""Mojo as a first-class language (M-064).

Part III — Code Intelligence. The roadmap's words for
this slice: "Mojo as a first-class language: parsing via
tree-sitter grammar where available, the house Mojo
skills wired as knowledge — Mythic is the only CLI that
truly speaks Mojo (Aesir's home tongue)."

What ships here, in ``mythic_agent/tools/mojo_sight.py``:

* **Recognition through the shipped catalogue.** A file
  is Mojo when M-043's tree-sitter foundation catalogue
  says so (``detect_language`` over the L-06 entry:
  ``.mojo``). No second extension list is invented here.
* **Parsing via tree-sitter where available — honestly.**
  The foundation's ``parse_source`` is tried first for
  every Mojo source. Measured in this campaign's own
  environment at build time: the tree-sitter core package
  IS installed, but NO Mojo grammar package exists (the
  catalogue's L-06 status is ``no-grammar-package``), so
  the foundation refuses and this module falls back to
  its own structural scan, labelled with its own backend
  name ``mojo-scan`` — never ``tree_sitter``. Where a
  real grammar ever loads, the foundation's definitions
  ride the same report with backend ``tree_sitter``.
  A grammar-backed Mojo parse on this machine today is
  NOT PROVEN, and no report dresses the scan as one.
* **The structural scan.** Definitions (functions —
  ``def`` and legacy ``fn`` — structs, traits, and
  ``comptime``/``alias`` constants), imports, and
  decorators, each with its line. The scan is a
  line-level structural reading, stated as such; it is
  not a grammar and claims no tree.
* **The removed-syntax watch.** The house Mojo skills
  record syntax the latest Mojo removed; the scan flags
  each occurrence with its replacement: ``alias`` →
  ``comptime``, ``let`` → ``var``, the ``borrowed`` /
  ``inout`` / ``owned`` conventions → ``imm`` / ``mut`` /
  ``var``, ``@parameter if``/``for`` → ``comptime``,
  ``@value`` → ``@fieldwise_init`` + trait conformance,
  ``@register_passable`` → the RegisterPassable traits,
  ``Stringable`` → ``Writable`` / ``write_to``, non-std
  imports → ``std.*``, and ``fn`` → ``def``.
* **The house skills wired as knowledge.** Distilled,
  searchable entries (K-01..), each naming its source
  skill — ``mojo-syntax``, ``mojo-gpu-fundamentals``,
  ``mojo-python-interop``. Those skills' full texts live
  outside this repo (Volmarr's custom skills) and the
  official Mojo documentation rides the Mojo Docs MCP
  connector; both are named here as external references,
  never copied wholesale or faked in-repo.
* **The surfaces.** ``Agent.mojo_sight(...)`` and
  ``/mojo [show | <path> | knowledge [term]]`` on the
  terminal and TUI system-command roads, sharing this
  module's parser and formatter. The setting
  ``mojo_sight`` (on by default) closes the road plainly.

Honesty rules, pinned by the slice's tests:

* **No grammar, no tree-sitter claim.** The backend is
  named per file from what actually parsed it.
* **Absence is named.** A workspace with no Mojo files
  says so; a knowledge search with no match says so.
* **This road never edits.** It reports and teaches;
  fixing removed syntax is the coder's next act.
"""

from __future__ import annotations

__all__ = [
    "PLAIN_EXPLANATION",
    "MOJO_SLICE",
    "USAGE",
    "REMOVED_SYNTAX",
    "KNOWLEDGE",
    "GrammarStatus",
    "MojoDefinition",
    "RemovedFinding",
    "FileScan",
    "KnowledgeEntry",
    "MojoReport",
    "enabled_from_config",
    "grammar_status",
    "is_mojo_path",
    "scan_source",
    "find_mojo_files",
    "search_knowledge",
    "mojo_sight",
    "parse_mojo_args",
    "format_mojo_report",
    "render_markdown",
]

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

MOJO_SLICE = "M-064"

PLAIN_EXPLANATION = (
    "Mojo sight makes Mojo a first-class language here. "
    "/mojo scans the workspace's .mojo files: definitions, "
    "imports and decorators are read structurally, and "
    "syntax the latest Mojo removed is flagged with its "
    "replacement from the house Mojo skills. Parsing rides "
    "the tree-sitter foundation where a Mojo grammar truly "
    "loads; no Mojo grammar package exists today, so the "
    "scan's own backend is named honestly and a "
    "grammar-backed parse is NOT PROVEN here. /mojo "
    "knowledge [term] searches the distilled house-skill "
    "knowledge wired into this module."
)

USAGE = "Usage: /mojo [show | <path> | knowledge [term]]"

#: Directories the workspace scan never enters.
_SKIP_DIRS = {".git", ".hg", ".svn", "__pycache__",
              "node_modules", "dist", "build",
              ".venv", ".venv-baseline", "venv"}

#: Caps for the workspace scan; every cut is named.
MAX_SCAN_FILES = 500
MAX_FILE_BYTES = 256_000


def enabled_from_config(config: Optional[Dict[str, Any]]) -> bool:
    """Mojo sight is on unless config says so."""
    if not config:
        return True
    return config.get("mojo_sight", True) is not False


# ---------------------------------------------------------------------------
# Grammar status: the foundation's own probe, reused
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GrammarStatus:
    """The Mojo grammar's true state in this environment."""

    language: str
    catalog_status: str
    available: bool
    detail: str

    def record(self) -> Dict[str, Any]:
        return {"language": self.language,
                "catalog_status": self.catalog_status,
                "available": self.available,
                "detail": self.detail}


def grammar_status() -> GrammarStatus:
    """Probe Mojo's grammar through the M-043 foundation.

    The catalogue entry and the live availability probe
    are the foundation's own; nothing is re-measured or
    re-declared here.
    """
    from ..core import tree_sitter_foundation as foundation

    catalog = foundation.load_catalog()
    entry = catalog.language("mojo")
    probe = foundation.availability_for("mojo", catalog)
    return GrammarStatus(
        language=entry.language, catalog_status=entry.status,
        available=probe.available, detail=probe.detail)


def is_mojo_path(path: Any) -> bool:
    """True when the foundation catalogue calls *path* Mojo."""
    from ..core import tree_sitter_foundation as foundation

    return foundation.detect_language(str(path)) == "mojo"


# ---------------------------------------------------------------------------
# The removed-syntax watch (from the house mojo-syntax skill)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RemovedRule:
    """One removed form and its replacement."""

    rule: str
    pattern: "re.Pattern[str]"
    replacement: str


REMOVED_SYNTAX: Tuple[RemovedRule, ...] = (
    RemovedRule(
        "alias-definition",
        re.compile(r"^\s*alias\s+[A-Za-z_]\w*\s*="),
        "comptime X = ... (alias is removed)"),
    RemovedRule(
        "let-binding",
        re.compile(r"^\s*let\s+[A-Za-z_]\w*"),
        "var x = ... (there is no let keyword)"),
    RemovedRule(
        "parameter-decorator",
        re.compile(r"@parameter\s+(if|for)\b"),
        "comptime if / comptime for"),
    RemovedRule(
        "value-decorator",
        re.compile(r"@value\b"),
        "@fieldwise_init + explicit trait conformance"),
    RemovedRule(
        "register-passable-decorator",
        re.compile(r"@register_passable\b"),
        "the RegisterPassable / TrivialRegisterPassable traits"),
    RemovedRule(
        "argument-convention",
        re.compile(r"\b(borrowed|inout|owned)\b"),
        "imm (read), mut (inout), var (owned)"),
    RemovedRule(
        "stringable",
        re.compile(r"\bStringable\b"),
        "Writable / write_to"),
    RemovedRule(
        "non-std-import",
        re.compile(r"^\s*from\s+(collections|memory|sys|os|pathlib|python)"
                   r"\s+import\b"),
        "from std.<module> import ..."),
    RemovedRule(
        "fn-definition",
        re.compile(r"^\s*fn\s+[A-Za-z_]\w*"),
        "def (fn is removed in the latest Mojo)"),
)


@dataclass(frozen=True)
class RemovedFinding:
    """One removed-syntax occurrence, with its replacement."""

    line: int
    rule: str
    text: str
    replacement: str

    def record(self) -> Dict[str, Any]:
        return {"line": self.line, "rule": self.rule,
                "text": self.text, "replacement": self.replacement}


# ---------------------------------------------------------------------------
# The structural scan
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MojoDefinition:
    """One definition the scan read, with its line."""

    name: str
    kind: str  # function | struct | trait | constant
    line: int

    def record(self) -> Dict[str, Any]:
        return {"name": self.name, "kind": self.kind,
                "line": self.line}


_DEF_RES: Tuple[Tuple[str, "re.Pattern[str]"], ...] = (
    ("function", re.compile(r"^\s*(?:def|fn)\s+([A-Za-z_]\w*)")),
    ("struct", re.compile(r"^\s*struct\s+([A-Za-z_]\w*)")),
    ("trait", re.compile(r"^\s*trait\s+([A-Za-z_]\w*)")),
    ("constant", re.compile(r"^\s*(?:comptime|alias)\s+([A-Za-z_]\w*)\s*=")),
)
_IMPORT_RE = re.compile(
    r"^\s*(?:from\s+([\w\.]+)\s+import\s+(.+)|import\s+([\w\.]+))\s*$")
_DECORATOR_RE = re.compile(r"^\s*@([A-Za-z_][\w\.]*)")


@dataclass
class FileScan:
    """One Mojo file's whole structural account."""

    path: str
    backend: str = "mojo-scan"  # mojo-scan | tree_sitter
    definitions: List[MojoDefinition] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    findings: List[RemovedFinding] = field(default_factory=list)
    lines: int = 0
    note: str = ""

    def definition_names(self) -> Tuple[str, ...]:
        return tuple(d.name for d in self.definitions)

    def record(self) -> Dict[str, Any]:
        return {"path": self.path, "backend": self.backend,
                "definitions": [d.record() for d in self.definitions],
                "imports": list(self.imports),
                "decorators": list(self.decorators),
                "findings": [f.record() for f in self.findings],
                "lines": self.lines, "note": self.note}


def _scan_lines(source: str) -> FileScan:
    """The line-level structural scan — stated as such."""
    scan = FileScan(path="")
    raw_lines = source.splitlines()
    scan.lines = len(raw_lines)
    for lineno, raw in enumerate(raw_lines, start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        for kind, pattern in _DEF_RES:
            match = pattern.match(raw)
            if match:
                scan.definitions.append(MojoDefinition(
                    name=match.group(1), kind=kind, line=lineno))
                break
        match = _IMPORT_RE.match(raw)
        if match:
            module = match.group(1) or match.group(3)
            scan.imports.append(module)
        match = _DECORATOR_RE.match(raw)
        if match:
            scan.decorators.append(match.group(1))
        for rule in REMOVED_SYNTAX:
            if rule.pattern.search(raw):
                scan.findings.append(RemovedFinding(
                    line=lineno, rule=rule.rule,
                    text=stripped[:120], replacement=rule.replacement))
    return scan


def scan_source(source: str, path: str = "") -> FileScan:
    """Scan one Mojo source: tree-sitter first, scan fallback.

    The foundation's parse is tried first; only a parse
    that truly returns labels the file ``tree_sitter``
    and contributes its definitions (the scan still reads
    imports, decorators and the removed-syntax watch —
    the foundation's definition nodes for Mojo are the
    catalogue's own, empty while no grammar exists).
    Any refusal falls back to the structural scan with
    the backend named ``mojo-scan``.
    """
    from ..core import tree_sitter_foundation as foundation

    scan = _scan_lines(source)
    scan.path = path
    try:
        parsed = foundation.parse_source("mojo", source)
    except Exception:
        parsed = None
    if parsed is not None:
        scan.backend = "tree_sitter"
        seen = {(d.name, d.kind) for d in scan.definitions}
        for definition in parsed.definitions:
            key = (definition.name, definition.kind)
            if key not in seen:
                seen.add(key)
                scan.definitions.append(MojoDefinition(
                    name=definition.name, kind=definition.kind,
                    line=definition.start_point[0] + 1))
        scan.definitions.sort(key=lambda d: d.line)
    return scan


def find_mojo_files(workspace: Any) -> Tuple[List[Path], List[str]]:
    """Every .mojo file under *workspace*, caps named."""
    root = Path(workspace)
    found: List[Path] = []
    warnings: List[str] = []
    if not root.is_dir():
        return found, warnings
    for candidate in sorted(root.rglob("*.mojo")):
        if any(part in _SKIP_DIRS or part.startswith(".venv")
               for part in candidate.parts):
            continue
        if len(found) >= MAX_SCAN_FILES:
            warnings.append(
                f"scan capped at {MAX_SCAN_FILES} Mojo files; "
                "further files were not read")
            break
        found.append(candidate)
    return found, warnings


# ---------------------------------------------------------------------------
# The house skills, wired as knowledge (distilled, sources named)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class KnowledgeEntry:
    """One distilled house-skill knowledge entry."""

    entry_id: str
    topic: str
    source: str
    body: str

    def record(self) -> Dict[str, Any]:
        return {"id": self.entry_id, "topic": self.topic,
                "source": self.source, "body": self.body}


KNOWLEDGE: Tuple[KnowledgeEntry, ...] = (
    KnowledgeEntry(
        "K-01", "removed syntax — do not generate these",
        "house skill: mojo-syntax",
        "Removed in the latest Mojo, with replacements: "
        "alias -> comptime; @parameter if/for -> comptime if/for; "
        "fn -> def; let -> var; borrowed -> imm; inout -> mut; "
        "owned -> var (as an argument convention); inout self in "
        "__init__ -> out self; @value -> @fieldwise_init + explicit "
        "trait conformance; @register_passable -> the "
        "RegisterPassable / TrivialRegisterPassable traits; "
        "Stringable / __str__ -> Writable / write_to; constrained() "
        "-> comptime assert. The /mojo scan flags these in a file "
        "with the replacement named."),
    KnowledgeEntry(
        "K-02", "comptime replaces alias and @parameter",
        "house skill: mojo-syntax",
        "comptime N = 1024 is a compile-time constant; comptime "
        "MyType = Int is a type alias; comptime if / comptime for "
        "are compile-time branches and loops; comptime assert "
        "cond, msg must sit inside a function body. Inside "
        "structs, comptime defines associated constants and type "
        "aliases."),
    KnowledgeEntry(
        "K-03", "argument conventions: imm, mut, var, out self",
        "house skill: mojo-syntax",
        "Read arguments are imm (the implicit default, rarely "
        "written); mutable arguments are mut; owned arguments are "
        "var. __init__ takes out self; a copy init is __init__(out "
        "self, *, copy: Self) and a move init is __init__(out "
        "self, *, deinit move: Self). The old borrowed / inout / "
        "owned spellings are removed."),
    KnowledgeEntry(
        "K-04", "standard library imports live under std.*",
        "house skill: mojo-syntax",
        "Write from std.collections import ..., from std.memory "
        "import ..., from std.sys import ..., from std.os import "
        "..., from std.pathlib import ... — the bare module names "
        "without the std. prefix are the old spelling. Python "
        "itself is from std.python import Python, PythonObject."),
    KnowledgeEntry(
        "K-05", "structs, traits and @fieldwise_init",
        "house skill: mojo-syntax",
        "@fieldwise_init generates __init__ from a struct's "
        "fields; trait conformance is declared in parentheses — "
        "struct Point(Copyable, Movable, Writable) — and traits "
        "combine with &: comptime KeyElement = Copyable & Hashable "
        "& Equatable. This replaces the removed @value decorator. "
        "String-producing types implement Writable / write_to, "
        "not Stringable / __str__."),
    KnowledgeEntry(
        "K-06", "string indexing returns StringSlice",
        "house skill: mojo-syntax",
        "s[byte=i] indexes a string by byte and returns a "
        "StringSlice; wrap it in String() when a String is "
        "needed. Plain s[i] is not the current spelling."),
    KnowledgeEntry(
        "K-07", "GPU programming is not CUDA",
        "house skill: mojo-gpu-fundamentals",
        "Mojo GPU code has no CUDA syntax: no __global__, "
        "__device__, __shared__ or <<<>>>. A kernel is a plain "
        "def; it is launched with ctx.enqueue_function[kernel]"
        "(args, grid_dim=..., block_dim=...); buffers come from "
        "ctx.enqueue_create_buffer[dtype](count) and move with "
        "ctx.enqueue_copy; ctx.synchronize() waits; barrier() "
        "from max.gpu.sync is the block barrier; thread_idx, "
        "block_idx and global_idx (from max.gpu) replace the "
        "CUDA index builtins; shared memory is stack_allocation "
        "with AddressSpace.SHARED; buffers free automatically "
        "when they go out of scope."),
    KnowledgeEntry(
        "K-08", "using Python from Mojo",
        "house skill: mojo-python-interop",
        "from std.python import Python, PythonObject; a module "
        "is Python.import_module(\"numpy\") and its objects are "
        "PythonObject. Converting a PythonObject to a Mojo value "
        "MUST use the py= keyword — Int(py=py_obj), Float64(py="
        "py_obj), String(py=py_obj) — never positional (Bool is "
        "the one exception). Mojo types implementing "
        "ConvertibleToPython auto-convert when passed to Python; "
        "value.to_python_object() converts explicitly."),
    KnowledgeEntry(
        "K-09", "the full texts and the official docs are external",
        "house skills + Mojo Docs MCP connector",
        "These entries are distilled from Volmarr's house Mojo "
        "skills (mojo-syntax, mojo-gpu-fundamentals, "
        "mojo-python-interop), whose full texts live outside "
        "this repo in his custom-skills keeping, and from the "
        "official Mojo documentation, which rides the Mojo Docs "
        "MCP connector. Neither full text is copied into this "
        "repo; when a question outgrows an entry here, those "
        "are the named roads to it."),
)


def search_knowledge(term: str = "") -> Tuple[KnowledgeEntry, ...]:
    """Knowledge entries matching *term* (empty = all)."""
    needle = (term or "").strip().lower()
    if not needle:
        return KNOWLEDGE
    return tuple(
        entry for entry in KNOWLEDGE
        if needle in entry.topic.lower()
        or needle in entry.body.lower()
        or needle in entry.source.lower())


# ---------------------------------------------------------------------------
# The report
# ---------------------------------------------------------------------------

@dataclass
class MojoReport:
    """One mojo-sight call's whole account."""

    kind: str = "show"  # show | file | knowledge
    status: str = "ok"  # ok | disabled | error
    grammar: Optional[GrammarStatus] = None
    files: List[FileScan] = field(default_factory=list)
    knowledge: List[KnowledgeEntry] = field(default_factory=list)
    knowledge_term: str = ""
    warnings: List[str] = field(default_factory=list)
    note: str = ""

    def totals(self) -> Tuple[int, int, int]:
        """(files scanned, definitions, removed-syntax findings)."""
        return (len(self.files),
                sum(len(f.definitions) for f in self.files),
                sum(len(f.findings) for f in self.files))

    def record(self) -> Dict[str, Any]:
        return {"kind": self.kind, "status": self.status,
                "grammar": self.grammar.record() if self.grammar else None,
                "files": [f.record() for f in self.files],
                "knowledge": [k.record() for k in self.knowledge],
                "knowledge_term": self.knowledge_term,
                "warnings": list(self.warnings),
                "note": self.note}


def _closed(kind: str) -> MojoReport:
    return MojoReport(
        kind=kind, status="disabled",
        note=("mojo sight is off (the mojo_sight setting), "
              "so no project file was read"))


def _scan_file(root: Path, target: Path) -> FileScan:
    try:
        relative = str(target.relative_to(root))
    except ValueError:
        relative = str(target)
    try:
        source = target.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        scan = FileScan(path=relative)
        scan.note = f"the file could not be read: {exc}"
        return scan
    return scan_source(source, relative)


def mojo_sight(
        workspace: Any, mode: str = "show", *,
        target: Optional[str] = None, term: str = "",
        enabled: bool = True,
) -> MojoReport:
    """One Mojo account — workspace scan, one file, or knowledge.

    Read-only: this function reads files and edits
    nothing. A missing workspace is an honest ``error``
    report. Raises :class:`ValueError` for an unknown
    mode.
    """
    kind = (mode or "show").strip().lower()
    if kind not in ("show", "file", "knowledge"):
        raise ValueError(f"{USAGE} — unknown mode {mode!r}")
    if not enabled:
        return _closed(kind)
    report = MojoReport(kind=kind)
    report.grammar = grammar_status()
    if kind == "knowledge":
        report.knowledge_term = (term or "").strip()
        report.knowledge = list(search_knowledge(report.knowledge_term))
        report.note = (
            "distilled from the house Mojo skills; the full "
            "texts and the official docs are external "
            "references, named in K-09"
            if report.knowledge else
            f"no house-skill knowledge matches "
            f"{report.knowledge_term!r} — the full skills are "
            "the external road named in K-09")
        return report
    root = Path(workspace)
    if not root.is_dir():
        report.status = "error"
        report.note = f"no workspace at {root} — nothing was scanned"
        return report
    if kind == "file":
        if not target:
            raise ValueError(f"{USAGE} — a file road needs its path")
        candidate = Path(target)
        if not candidate.is_absolute():
            candidate = root / candidate
        if not candidate.is_file():
            report.status = "error"
            report.note = f"no file at {target} — nothing was scanned"
            return report
        if not is_mojo_path(candidate):
            report.status = "error"
            report.note = (
                f"{target} is not a Mojo file — the tree-sitter "
                "catalogue knows Mojo by its .mojo extension")
            return report
        report.files = [_scan_file(root, candidate)]
        report.note = ("read-only — nothing was edited; fixing "
                       "removed syntax is a separate act")
        return report
    paths, warnings = find_mojo_files(root)
    report.warnings.extend(warnings)
    for path in paths:
        if path.stat().st_size > MAX_FILE_BYTES:
            report.warnings.append(
                f"{path.relative_to(root)} skipped: over the "
                f"{MAX_FILE_BYTES}-byte scan cap")
            continue
        report.files.append(_scan_file(root, path))
    if not report.files:
        report.note = ("no Mojo files in this workspace — Mojo "
                       "is recognised by its .mojo extension "
                       "wherever it lands")
    else:
        report.note = ("read-only — nothing was edited; fixing "
                       "removed syntax is a separate act")
    return report


# ---------------------------------------------------------------------------
# Surfaces: the shared parser + formatters
# ---------------------------------------------------------------------------

def parse_mojo_args(arguments: str) -> Dict[str, Any]:
    """Parse ``/mojo`` arguments into a mojo request.

    Grammar::

        /mojo
        /mojo show
        /mojo <path>
        /mojo knowledge [term ...]

    Raises :class:`ValueError` on a usage error.
    """
    text = (arguments or "").strip()
    if not text:
        return {"action": "show"}
    tokens = text.split()
    head = tokens[0].lower()
    if head == "show":
        if len(tokens) != 1:
            raise ValueError(f"{USAGE} — show takes no argument")
        return {"action": "show"}
    if head == "knowledge":
        return {"action": "knowledge",
                "term": " ".join(tokens[1:])}
    if len(tokens) != 1:
        raise ValueError(f"{USAGE} — name one file, or none")
    return {"action": "file", "target": tokens[0]}


def format_mojo_report(status: Dict[str, Any]) -> str:
    """One mojo call's account, from an Agent status mapping."""
    report = status["report"]
    lines = [f"Mojo sight ({MOJO_SLICE}): {report['kind']} — "
             "Mojo as a first-class language, read-only."]
    grammar = report.get("grammar")
    if grammar:
        if grammar["available"]:
            lines.append(
                f"  Grammar: tree-sitter grammar available — "
                f"{grammar['detail']}.")
        else:
            lines.append(
                "  Grammar: no tree-sitter grammar package for "
                f"Mojo ({grammar['detail']}); files are read by "
                "the mojo-scan structural backend, and a "
                "grammar-backed parse is NOT PROVEN here.")
    if report["kind"] in ("show", "file"):
        n_files, n_defs, n_findings = (
            len(report["files"]),
            sum(len(f["definitions"]) for f in report["files"]),
            sum(len(f["findings"]) for f in report["files"]))
        lines.append(
            f"  Scanned {n_files} Mojo file(s): {n_defs} "
            f"definition(s), {n_findings} removed-syntax "
            "finding(s).")
        for scanned in report["files"]:
            lines.append(
                f"    {scanned['path']} [{scanned['backend']}] — "
                f"{len(scanned['definitions'])} definition(s), "
                f"{len(scanned['imports'])} import(s), "
                f"{len(scanned['findings'])} finding(s)")
            for definition in scanned["definitions"]:
                lines.append(
                    f"      line {definition['line']}: "
                    f"{definition['kind']} {definition['name']}")
            for finding in scanned["findings"]:
                lines.append(
                    f"      line {finding['line']}: "
                    f"{finding['rule']} — use "
                    f"{finding['replacement']}")
            if scanned["note"]:
                lines.append(f"      {scanned['note']}")
    if report["kind"] == "knowledge":
        if report["knowledge_term"]:
            lines.append(
                f"  Knowledge matching {report['knowledge_term']!r}:")
        for entry in report["knowledge"]:
            lines.append(f"    {entry['id']} {entry['topic']} "
                         f"({entry['source']})")
            lines.append(f"      {entry['body']}")
    if report["note"]:
        lines.append(f"  {report['note']}")
    for warning in report["warnings"]:
        lines.append(f"  Warning: {warning}")
    lines.append(status["plain_explanation"])
    return "\n".join(lines)


def render_markdown(report: MojoReport) -> str:
    """Render *report* as a human report, from its own record.

    Built from :meth:`MojoReport.totals` and the file
    scans' own accessors, so the rendered page is
    computed from the same values the tests pin.
    """
    data = report.record()
    n_files, n_defs, n_findings = report.totals()
    grammar = data["grammar"] or {}
    lines = [
        "# Mojo Sight — Mojo as a first-class language",
        "",
        f"*Slice {MOJO_SLICE} of the All-Features road "
        "(Part III — Code Intelligence). Read-only — "
        "nothing is edited by this report.*",
        "",
        f"Grammar: catalogue status "
        f"`{grammar.get('catalog_status', 'unknown')}`, "
        f"available: {grammar.get('available', False)} — "
        f"{grammar.get('detail', '')}",
        "",
        f"**{n_files} Mojo file(s)** scanned, **{n_defs} "
        f"definition(s)**, **{n_findings} removed-syntax "
        "finding(s)**.",
        "",
    ]
    for scanned in data["files"]:
        lines.append(f"## `{scanned['path']}` [{scanned['backend']}]")
        lines.append("")
        for definition in scanned["definitions"]:
            lines.append(
                f"- line {definition['line']}: "
                f"{definition['kind']} `{definition['name']}`")
        for finding in scanned["findings"]:
            lines.append(
                f"- line {finding['line']}: {finding['rule']} — "
                f"use {finding['replacement']}")
        lines.append("")
    if data["knowledge"]:
        lines.append("## House-skill knowledge")
        lines.append("")
        for entry in data["knowledge"]:
            lines.append(
                f"- **{entry['id']} {entry['topic']}** "
                f"({entry['source']}): {entry['body']}")
        lines.append("")
    names = [name for scanned in report.files
             for name in scanned.definition_names()]
    lines.append("Definitions read: " + (", ".join(names) or "none"))
    lines.append("")
    return "\n".join(lines)
