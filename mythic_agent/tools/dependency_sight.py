"""Dependency sight (M-061).

Part III — Code Intelligence. The roadmap's words for
this slice: "read the dependency graph, changelogs, and
known-vulnerability data for the project's stack; an
upgrade is proposed with its blast radius, never applied
silently."

What ships here, in
``mythic_agent/tools/dependency_sight.py``:

* **The graph.** The project's own declared requirements
  read from ``pyproject.toml`` (stdlib ``tomllib``, the
  M-012 census's own road): every core dependency, every
  extra's dependencies, and the build-system requirements,
  each with the groups that declare it and the specs it is
  declared with. Where the M-012 census knows a package,
  its licence / necessity / import name ride along — this
  module builds on the census and the dependency audit's
  import-scan shape; it duplicates neither.
* **Installed truth.** A package's installed version is
  measured in the running environment with
  ``importlib.metadata``. A package that is not installed
  reports ``unknown`` — never a guessed version.
* **Changelogs.** LOCAL data only: changelog files in
  the workspace (``CHANGELOG*``, ``HISTORY*``, ``NEWS*``)
  searched for the package's name. When no local
  changelog data exists, the report says exactly that.
* **Vulnerabilities.** LOCAL data only: advisory /
  audit files present in the workspace. When no local
  vulnerability data source exists, the report says
  known-vulnerability status is NOT PROVEN / no local
  data — never a fake "no vulnerabilities" clean bill.
* **Proposals.** Given a package and a user-supplied
  target version, a proposal as data: the declared
  spec(s) and installed version, the target, the blast
  radius (which workspace files import the package,
  counted from the tree by an AST import scan in the
  dependency audit's shape), the groups it belongs to,
  and whether anything else pins it. A proposal for an
  undeclared package is refused plainly.
* **The surfaces.** ``Agent.dependency_sight()`` /
  ``Agent.dependency_proposal()`` and ``/deps`` on the
  terminal and TUI system-command roads, sharing this
  module's parser and formatter: ``/deps``,
  ``/deps show``, ``/deps <package>`` and
  ``/deps propose <package> <version>``. The setting
  ``dependency_sight`` (on by default) closes the road
  plainly when the user says so.

Honesty rules, pinned by the slice's tests:

* **No network road exists in this module at all.**
  Changelogs and vulnerability data come only from the
  workspace itself; online lookup is M-059's web road,
  never a hidden second door here.
* **Unknown stays unknown.** An uninstalled package's
  version is unknown; a stack with no local vulnerability
  data has NOT PROVEN vulnerability status — absence of
  local data is never dressed as absence of problems.
* **A proposal is never applied.** This module has no
  apply/write path for upgrades at all — proposing
  changes no file, and no other road here writes either.
* **Off means off.** With ``dependency_sight`` false, no
  file is read on this road at all.
"""

from __future__ import annotations

__all__ = [
    "DEPS_SLICE",
    "PLAIN_EXPLANATION",
    "USAGE",
    "BlastRadius",
    "DepNode",
    "DepsReport",
    "LocalMention",
    "Proposal",
    "declared_dependencies",
    "dependency_proposal",
    "dependency_sight",
    "enabled_from_config",
    "find_changelog",
    "find_vulnerabilities",
    "format_deps_report",
    "installed_version_for",
    "normalize_name",
    "parse_deps_args",
    "render_markdown",
    "scan_imports",
]

import ast
import importlib.metadata
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

DEPS_SLICE = "M-061"

#: Changelog file families searched for local data.
CHANGELOG_PREFIXES = ("changelog", "history", "news")

#: Basename fragments that mark a local vulnerability
#: data source (an advisory or audit file in the tree).
VULN_MARKERS = ("advis", "vulnerab", "pip-audit", "safety", "osv")

#: Directories the import scan never enters.
_SKIP_DIRS = {".git", ".hg", ".svn", "__pycache__",
              "node_modules", "dist", "build",
              ".venv", ".venv-baseline", "venv"}

#: Caps for the workspace scans; every cut is named.
MAX_SCAN_FILES = 2000
MAX_FILE_BYTES = 256_000
MAX_MENTIONS = 10

_NAME_CUT_RE = re.compile(r"[;\[\s<>=!~]")

PLAIN_EXPLANATION = (
    "Dependency sight reads the project's own dependency "
    "graph from pyproject.toml — every declared package, "
    "the groups that declare it, its specs, and the "
    "version actually installed (unknown when it is not "
    "installed, never guessed). /deps shows the graph, "
    "/deps <package> adds that package's local changelog "
    "mentions and its local vulnerability-data state, and "
    "/deps propose <package> <version> drafts an upgrade "
    "proposal with its blast radius — the workspace files "
    "that import the package, counted from the tree. "
    "Changelogs and vulnerability data are read only "
    "from files in this workspace: with no local data the "
    "report says so plainly, and known-vulnerability "
    "status stays NOT PROVEN rather than claiming a "
    "clean bill. A proposal is data only — it is never "
    "applied, and this road changes no file."
)

USAGE = ("Usage: /deps [show | <package> | "
         "propose <package> <version>]")


def enabled_from_config(config: Optional[Dict[str, Any]]) -> bool:
    """Dependency sight is on unless config says so."""
    if not config:
        return True
    return config.get("dependency_sight", True) is not False


def normalize_name(name: str) -> str:
    """PEP 503 normalisation: runs of -_. become one -."""
    return re.sub(r"[-_.]+", "-", (name or "").strip()).lower()


def _req_parts(raw: str) -> Tuple[str, str]:
    """(declared name, version spec) from one requirement string."""
    text = (raw or "").strip()
    match = _NAME_CUT_RE.search(text)
    if match is None:
        return text, ""
    name = text[:match.start()].strip()
    rest = text[match.start():].split(";")[0].strip()
    if rest.startswith("["):
        closing = rest.find("]")
        rest = rest[closing + 1:].strip() if closing >= 0 else ""
    return name, rest


def installed_version_for(name: str) -> Optional[str]:
    """The installed version of *name*, or None when absent.

    Measured with :mod:`importlib.metadata` in the
    running environment; an uninstalled package returns
    None (unknown), never a guessed version.
    """
    candidates = [name, name.replace("-", "_"), name.replace("_", "-")]
    for candidate in dict.fromkeys(candidates):
        try:
            return importlib.metadata.version(candidate)
        except importlib.metadata.PackageNotFoundError:
            continue
    return None


# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DepNode:
    """One declared dependency: its groups, specs, truth."""

    name: str  # PEP 503 normalised
    groups: Tuple[str, ...] = ()
    specs: Tuple[str, ...] = ()
    requirements: Tuple[str, ...] = ()
    installed_version: Optional[str] = None
    import_names: Tuple[str, ...] = ()
    census_id: str = ""
    licence: str = ""
    necessity: str = ""

    def record(self) -> Dict[str, Any]:
        return {"name": self.name,
                "groups": list(self.groups),
                "specs": list(self.specs),
                "requirements": list(self.requirements),
                "installed_version": self.installed_version,
                "import_names": list(self.import_names),
                "census_id": self.census_id,
                "licence": self.licence,
                "necessity": self.necessity}


@dataclass(frozen=True)
class LocalMention:
    """One local-data mention of a package, with its line."""

    path: str
    line: int
    text: str

    def record(self) -> Dict[str, Any]:
        return {"path": self.path, "line": self.line,
                "text": self.text}


@dataclass(frozen=True)
class BlastRadius:
    """The counted blast radius of touching one package."""

    package: str
    files: Tuple[str, ...] = ()

    @property
    def file_count(self) -> int:
        return len(self.files)

    def record(self) -> Dict[str, Any]:
        return {"package": self.package,
                "files": list(self.files),
                "file_count": len(self.files)}


@dataclass(frozen=True)
class Proposal:
    """One upgrade proposal — data only, never applied."""

    package: str
    target_version: str
    current_specs: Tuple[str, ...] = ()
    groups: Tuple[str, ...] = ()
    installed_version: Optional[str] = None
    blast_radius: BlastRadius = BlastRadius(package="")
    pinned_elsewhere: bool = False
    pin_note: str = ""
    applied: bool = False

    def record(self) -> Dict[str, Any]:
        return {"package": self.package,
                "target_version": self.target_version,
                "current_specs": list(self.current_specs),
                "groups": list(self.groups),
                "installed_version": self.installed_version,
                "blast_radius": self.blast_radius.record(),
                "pinned_elsewhere": self.pinned_elsewhere,
                "pin_note": self.pin_note,
                "applied": self.applied}


@dataclass
class DepsReport:
    """One dependency-sight call's whole account."""

    kind: str = "show"  # show | package | propose
    package: str = ""
    target_version: str = ""
    status: str = "ok"  # ok | disabled | error
    nodes: List[DepNode] = field(default_factory=list)
    node: Optional[DepNode] = None
    changelog_status: str = ""  # found | no-local-data
    changelog_files: List[str] = field(default_factory=list)
    changelog_hits: List[LocalMention] = field(default_factory=list)
    vuln_status: str = ""  # local-data | no-local-data
    vuln_sources: List[str] = field(default_factory=list)
    vuln_hits: List[LocalMention] = field(default_factory=list)
    blast_radius: Optional[BlastRadius] = None
    proposal: Optional[Proposal] = None
    warnings: List[str] = field(default_factory=list)
    note: str = ""

    def names(self) -> Tuple[str, ...]:
        """Every declared package name, in graph order."""
        return tuple(n.name for n in self.nodes)

    def counts(self) -> Tuple[int, int]:
        """(declared packages, changelog files searched)."""
        return (len(self.nodes), len(self.changelog_files))

    def record(self) -> Dict[str, Any]:
        return {"kind": self.kind, "package": self.package,
                "target_version": self.target_version,
                "status": self.status,
                "nodes": [n.record() for n in self.nodes],
                "node": self.node.record() if self.node else None,
                "changelog_status": self.changelog_status,
                "changelog_files": list(self.changelog_files),
                "changelog_hits": [h.record()
                                   for h in self.changelog_hits],
                "vuln_status": self.vuln_status,
                "vuln_sources": list(self.vuln_sources),
                "vuln_hits": [h.record() for h in self.vuln_hits],
                "blast_radius": (self.blast_radius.record()
                                 if self.blast_radius else None),
                "proposal": (self.proposal.record()
                             if self.proposal else None),
                "warnings": list(self.warnings),
                "note": self.note}


# ---------------------------------------------------------------------------
# The graph: declared requirements from pyproject.toml
# ---------------------------------------------------------------------------

def _census_by_name() -> Dict[str, Any]:
    """The M-012 census keyed by normalised name ({} if unreadable)."""
    try:
        from ..core.dependency_census import load_census

        census = load_census()
    except Exception:
        return {}
    return {normalize_name(d.name): d for d in census.dependencies}


def declared_dependencies(
        workspace: Any, *,
        version_lookup: Optional[Callable[[str], Optional[str]]] = None,
) -> Tuple[List[DepNode], List[str]]:
    """The declared graph: (nodes, warnings) from pyproject.toml.

    Core dependencies, every extra, and the build-system
    requirements — each node carrying the groups that
    declare it, the distinct specs it is declared with,
    the raw requirement strings, the M-012 census's
    licence/necessity/import name where the census knows
    the package, and its honestly measured installed
    version (None = uninstalled = unknown).
    """
    lookup = version_lookup or installed_version_for
    root = Path(workspace)
    pyproject = root / "pyproject.toml"
    warnings: List[str] = []
    if not pyproject.is_file():
        return [], [f"no pyproject.toml at {root} — "
                    "no declared dependency graph to read"]
    try:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return [], [f"pyproject.toml could not be read: {exc}"]
    raw_groups: Dict[str, List[str]] = {}
    project = data.get("project", {})
    for req in project.get("dependencies", []) or []:
        raw_groups.setdefault("core", []).append(req)
    for extra, reqs in (project.get("optional-dependencies", {})
                        or {}).items():
        for req in reqs or []:
            raw_groups.setdefault(extra, []).append(req)
    build = data.get("build-system", {})
    for req in build.get("requires", []) or []:
        raw_groups.setdefault("build-system", []).append(req)
    grouped: Dict[str, Dict[str, Any]] = {}
    for group, reqs in raw_groups.items():
        for raw in reqs:
            name, spec = _req_parts(raw)
            key = normalize_name(name)
            if not key:
                continue
            slot = grouped.setdefault(
                key, {"groups": set(), "specs": set(), "raw": []})
            slot["groups"].add(group)
            if spec:
                slot["specs"].add(spec)
            slot["raw"].append(raw)
    census = _census_by_name()
    nodes: List[DepNode] = []
    for key in sorted(grouped):
        slot = grouped[key]
        entry = census.get(key)
        if entry is not None:
            import_names = (entry.import_name,)
        else:
            import_names = (key.replace("-", "_"),)
        nodes.append(DepNode(
            name=key,
            groups=tuple(sorted(slot["groups"])),
            specs=tuple(sorted(slot["specs"])),
            requirements=tuple(slot["raw"]),
            installed_version=lookup(key),
            import_names=import_names,
            census_id=entry.id if entry is not None else "",
            licence=entry.licence if entry is not None else "",
            necessity=entry.necessity if entry is not None else ""))
    return nodes, warnings


# ---------------------------------------------------------------------------
# Local data: changelogs + vulnerability sources (never the network)
# ---------------------------------------------------------------------------

def _workspace_files(root: Path) -> List[Path]:
    """Every file under *root*, pruned, in deterministic order."""
    if not root.is_dir():
        return []
    found = [p for p in root.rglob("*")
             if p.is_file()
             and not any(part in _SKIP_DIRS or part.startswith(".venv")
                         for part in p.parts)]
    return sorted(found, key=lambda p: p.as_posix())


def _read_text(path: Path) -> Optional[str]:
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return None
    except OSError:
        return None
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _mentions(root: Path, files: List[Path],
              package: str) -> List[LocalMention]:
    """Lines naming *package* (or its -/_/space spellings)."""
    variants = {package.lower(), package.replace("-", "_").lower(),
                package.replace("-", " ").lower(),
                package.replace("_", "-").lower()}
    hits: List[LocalMention] = []
    for path in files:
        text = _read_text(path)
        if text is None:
            continue
        try:
            rel = path.relative_to(root).as_posix()
        except ValueError:
            rel = path.name
        for number, line in enumerate(text.splitlines(), start=1):
            lowered = line.lower()
            if any(variant in lowered for variant in variants):
                hits.append(LocalMention(
                    path=rel, line=number,
                    text=" ".join(line.split())[:200]))
                if len(hits) >= MAX_MENTIONS:
                    return hits
    return hits


def find_changelog(workspace: Any, package: str) -> Dict[str, Any]:
    """Local changelog data for *package* — files + mentions.

    Only files in the workspace are read. With no local
    changelog file at all, the status is ``no-local-data``
    and the note says exactly that; changelog files that
    exist but never name the package say that instead.
    """
    root = Path(workspace)
    files = [p for p in _workspace_files(root)
             if p.name.lower().startswith(CHANGELOG_PREFIXES)]
    rels = []
    for path in files:
        try:
            rels.append(path.relative_to(root).as_posix())
        except ValueError:
            rels.append(path.name)
    if not files:
        return {"status": "no-local-data", "files": [],
                "hits": [],
                "note": ("no local changelog data — no "
                         "CHANGELOG, HISTORY or NEWS file "
                         "exists in this workspace, and "
                         "nothing was fetched from anywhere")}
    hits = _mentions(root, files, normalize_name(package))
    if not hits:
        return {"status": "no-local-data", "files": rels,
                "hits": [],
                "note": (f"local changelog file(s) exist "
                         f"({', '.join(rels)}) but none "
                         f"mentions {package} — no local "
                         "changelog data for it")}
    return {"status": "found", "files": rels,
            "hits": hits, "note": ""}


def find_vulnerabilities(workspace: Any,
                         package: str) -> Dict[str, Any]:
    """Local vulnerability data for *package* — honestly bounded.

    Only advisory/audit files present in the workspace
    count as a data source. With none, the status is
    ``no-local-data`` and the note states that
    known-vulnerability status is NOT PROVEN — never a
    clean bill. With sources, their mentions of the
    package are reported; silence in them is reported
    as silence, not as safety.
    """
    root = Path(workspace)
    files = [p for p in _workspace_files(root)
             if any(marker in p.name.lower()
                    for marker in VULN_MARKERS)]
    rels = []
    for path in files:
        try:
            rels.append(path.relative_to(root).as_posix())
        except ValueError:
            rels.append(path.name)
    if not files:
        return {"status": "no-local-data", "sources": [],
                "hits": [],
                "note": ("no local vulnerability data source "
                         "exists in this workspace (no "
                         "advisory or audit file) — "
                         "known-vulnerability status is NOT "
                         "PROVEN (no local data); this is "
                         "not a claim that the stack is "
                         "vulnerability-free, and nothing "
                         "was fetched from anywhere")}
    hits = _mentions(root, files, normalize_name(package))
    note = ""
    if not hits:
        note = (f"the local vulnerability source(s) "
                f"({', '.join(rels)}) do not mention "
                f"{package} — silence in local data is "
                "not a clean bill")
    return {"status": "local-data", "sources": rels,
            "hits": hits, "note": note}


# ---------------------------------------------------------------------------
# Blast radius: the AST import scan (the audit's shape)
# ---------------------------------------------------------------------------

def scan_imports(workspace: Any) -> Tuple[Dict[str, set], List[str]]:
    """Map workspace-relative .py path -> top-level imports.

    The dependency audit's shape: stdlib ``ast`` over the
    tree, no imports executed. Binary, oversized and
    unparseable files are skipped, the skips named in the
    returned warnings; caps name themselves the same way.
    """
    root = Path(workspace)
    imports: Dict[str, set] = {}
    warnings: List[str] = []
    skipped = 0
    files = [p for p in _workspace_files(root)
             if p.suffix == ".py"]
    for path in files:
        if len(imports) + skipped >= MAX_SCAN_FILES:
            warnings.append(
                f"import scan file cap reached "
                f"({MAX_SCAN_FILES}); the rest of the tree "
                "was not scanned")
            break
        try:
            raw = path.read_bytes()
        except OSError:
            skipped += 1
            continue
        if len(raw) > MAX_FILE_BYTES or b"\x00" in raw:
            skipped += 1
            continue
        try:
            tree = ast.parse(raw.decode("utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            skipped += 1
            continue
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(a.name.split(".")[0]
                             for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                if not node.level and node.module:
                    names.add(node.module.split(".")[0])
        try:
            rel = path.relative_to(root).as_posix()
        except ValueError:
            rel = path.name
        imports[rel] = names
    if skipped:
        warnings.append(
            f"{skipped} Python file(s) were skipped by the "
            "import scan (unreadable, oversized, binary or "
            "unparseable) and are not counted in any blast "
            "radius")
    return imports, warnings


def _blast_radius(workspace: Any, node: DepNode,
                  report: DepsReport) -> BlastRadius:
    imports, warnings = scan_imports(workspace)
    report.warnings.extend(warnings)
    wanted = set(node.import_names)
    files = tuple(sorted(
        rel for rel, names in imports.items() if names & wanted))
    return BlastRadius(package=node.name, files=files)


# ---------------------------------------------------------------------------
# The three roads
# ---------------------------------------------------------------------------

def _closed(kind: str) -> DepsReport:
    return DepsReport(
        kind=kind, status="disabled",
        note=("dependency sight is off (the "
              "dependency_sight setting), so no project "
              "file was read"))


def _find_node(nodes: List[DepNode],
               package: str) -> Optional[DepNode]:
    key = normalize_name(package)
    for node in nodes:
        if node.name == key:
            return node
    return None


def dependency_sight(
        workspace: Any, package: Optional[str] = None, *,
        enabled: bool = True,
        version_lookup: Optional[Callable[[str], Optional[str]]] = None,
) -> DepsReport:
    """The dependency graph, or one package's full account.

    With no *package*: every declared dependency with its
    groups, specs and installed truth, plus whether any
    local changelog / vulnerability data exists at all.
    With a *package*: that node plus its blast radius,
    its local changelog mentions and its local
    vulnerability-data state. An undeclared package is
    an honest ``error`` report — nothing is invented.
    """
    kind = "package" if package else "show"
    report = DepsReport(kind=kind,
                        package=normalize_name(package or ""))
    if not enabled:
        return _closed(kind)
    nodes, warnings = declared_dependencies(
        workspace, version_lookup=version_lookup)
    report.nodes = nodes
    report.warnings.extend(warnings)
    if not nodes:
        report.status = "error"
        report.note = ("no declared dependencies were read — "
                       + ("; ".join(warnings) if warnings
                          else "the graph is empty"))
        return report
    root = Path(workspace)
    if not package:
        changelog_files = [
            p for p in _workspace_files(root)
            if p.name.lower().startswith(CHANGELOG_PREFIXES)]
        report.changelog_status = (
            "found" if changelog_files else "no-local-data")
        for path in changelog_files:
            try:
                report.changelog_files.append(
                    path.relative_to(root).as_posix())
            except ValueError:
                report.changelog_files.append(path.name)
        vuln = find_vulnerabilities(root, "")
        report.vuln_status = vuln["status"]
        report.vuln_sources = vuln["sources"]
        if vuln["status"] == "no-local-data":
            report.note = vuln["note"]
        return report
    node = _find_node(nodes, package)
    if node is None:
        report.status = "error"
        report.note = (f"{package} is not declared in this "
                       "project's pyproject.toml — dependency "
                       "sight invents nothing for undeclared "
                       "packages")
        return report
    report.node = node
    changelog = find_changelog(root, node.name)
    report.changelog_status = changelog["status"]
    report.changelog_files = changelog["files"]
    report.changelog_hits = changelog["hits"]
    vuln = find_vulnerabilities(root, node.name)
    report.vuln_status = vuln["status"]
    report.vuln_sources = vuln["sources"]
    report.vuln_hits = vuln["hits"]
    report.blast_radius = _blast_radius(root, node, report)
    notes = [n for n in (changelog["note"], vuln["note"]) if n]
    report.note = "; ".join(notes)
    return report


def dependency_proposal(
        workspace: Any, package: str, target_version: str, *,
        enabled: bool = True,
        version_lookup: Optional[Callable[[str], Optional[str]]] = None,
) -> DepsReport:
    """Draft an upgrade proposal for *package* — data only.

    The proposal carries the declared spec(s), the
    installed version, the target, the counted blast
    radius, the declaring groups, and whether anything
    else pins the package (declared in more than one
    group, or with more than one distinct spec). It is
    NEVER applied: this function writes nothing, and the
    module has no apply road at all. An undeclared
    package is refused plainly as an ``error`` report.
    Raises :class:`ValueError` for an empty package or
    target version.
    """
    wanted = (package or "").strip()
    target = (target_version or "").strip()
    report = DepsReport(kind="propose",
                        package=normalize_name(wanted),
                        target_version=target)
    if not enabled:
        return _closed("propose")
    if not wanted or not target:
        raise ValueError(
            f"{USAGE} — a proposal needs its package and "
            "its target version")
    nodes, warnings = declared_dependencies(
        workspace, version_lookup=version_lookup)
    report.nodes = nodes
    report.warnings.extend(warnings)
    node = _find_node(nodes, wanted)
    if node is None:
        report.status = "error"
        report.note = (f"{wanted} is not declared in this "
                       "project's pyproject.toml — no "
                       "proposal is drafted for an undeclared "
                       "package")
        return report
    report.node = node
    blast = _blast_radius(Path(workspace), node, report)
    pinned = len(node.groups) > 1 or len(node.specs) > 1
    if len(node.groups) > 1:
        pin_note = ("also declared in: "
                    + ", ".join(node.groups)
                    + " — an upgrade must move every "
                      "declaration together")
    elif len(node.specs) > 1:
        pin_note = ("declared with more than one spec: "
                    + ", ".join(node.specs))
    else:
        pin_note = ("declared only in "
                    + ", ".join(node.groups)
                    + " with the one spec above")
    report.proposal = Proposal(
        package=node.name, target_version=target,
        current_specs=node.specs, groups=node.groups,
        installed_version=node.installed_version,
        blast_radius=blast, pinned_elsewhere=pinned,
        pin_note=pin_note, applied=False)
    report.blast_radius = blast
    report.note = ("this is a proposal only — nothing was "
                   "applied and no file was changed; "
                   "applying an upgrade is a separate, "
                   "human-approved step outside this road")
    return report


# ---------------------------------------------------------------------------
# Surfaces: the shared parser + formatters
# ---------------------------------------------------------------------------

def parse_deps_args(arguments: str) -> Dict[str, Any]:
    """Parse ``/deps`` arguments into a deps request.

    Grammar::

        /deps
        /deps show
        /deps <package>
        /deps propose <package> <version>

    Raises :class:`ValueError` on a usage error.
    """
    text = (arguments or "").strip()
    if not text:
        return {"action": "show"}
    tokens = text.split()
    head = tokens[0].lower()
    if head == "show":
        if len(tokens) > 1:
            raise ValueError(f"{USAGE} — show takes no argument")
        return {"action": "show"}
    if head == "propose":
        if len(tokens) != 3:
            raise ValueError(
                f"{USAGE} — a proposal needs its package "
                "and its target version")
        return {"action": "propose", "package": tokens[1],
                "version": tokens[2]}
    if len(tokens) == 1:
        return {"action": "package", "package": tokens[0]}
    raise ValueError(
        f"{USAGE} — name one package, or propose one "
        "upgrade")


def _node_line(node: Dict[str, Any]) -> str:
    installed = node["installed_version"]
    truth = (f"installed {installed}" if installed
             else "not installed (version unknown)")
    spec = ", ".join(node["specs"]) if node["specs"] else "no spec"
    return (f"  {node['name']} [{', '.join(node['groups'])}] "
            f"{spec} — {truth}")


def format_deps_report(status: Dict[str, Any]) -> str:
    """One deps call's account, from an Agent deps-status mapping."""
    report = status["report"]
    if report["kind"] == "show":
        lines = [f"Dependency sight ({DEPS_SLICE}): "
                 f"{len(report['nodes'])} declared package(s)."]
        for node in report["nodes"]:
            lines.append(_node_line(node))
        lines.append(
            f"  Changelogs: {report['changelog_status']} "
            f"({len(report['changelog_files'])} local file(s)); "
            f"vulnerability data: {report['vuln_status']} "
            f"({len(report['vuln_sources'])} local source(s)).")
    elif report["kind"] == "package":
        node = report["node"] or {}
        lines = [f"Dependency sight ({DEPS_SLICE}): "
                 f"{report['package']}."]
        if node:
            lines.append(_node_line(node))
            if node["licence"]:
                lines.append(
                    f"  Census: {node['census_id']} — "
                    f"{node['licence']}, {node['necessity']}.")
        blast = report["blast_radius"] or {}
        lines.append(
            f"  Blast radius: {blast.get('file_count', 0)} "
            "workspace file(s) import it.")
        for path in blast.get("files", []):
            lines.append(f"    {path}")
        lines.append(
            f"  Changelog: {report['changelog_status']}.")
        for hit in report["changelog_hits"]:
            lines.append(
                f"    {hit['path']}:{hit['line']}: {hit['text']}")
        lines.append(
            f"  Vulnerabilities: {report['vuln_status']}.")
        for hit in report["vuln_hits"]:
            lines.append(
                f"    {hit['path']}:{hit['line']}: {hit['text']}")
    else:
        proposal = report["proposal"] or {}
        lines = [f"Upgrade proposal ({DEPS_SLICE}): "
                 f"{report['package']} -> "
                 f"{report['target_version']} (NOT applied)."]
        if proposal:
            lines.append(
                f"  Declared: {', '.join(proposal['groups'])}; "
                f"spec(s): "
                f"{', '.join(proposal['current_specs']) or 'none'}; "
                f"installed: "
                f"{proposal['installed_version'] or 'unknown'}.")
            blast = proposal["blast_radius"]
            lines.append(
                f"  Blast radius: {blast['file_count']} "
                "workspace file(s) import it.")
            for path in blast["files"]:
                lines.append(f"    {path}")
            lines.append(f"  Pins: {proposal['pin_note']}.")
    if report["note"]:
        lines.append(f"  {report['note']}")
    for warning in report["warnings"]:
        lines.append(f"  Warning: {warning}")
    lines.append(status["plain_explanation"])
    return "\n".join(lines)


def render_markdown(report: DepsReport) -> str:
    """Render *report* as a human report, from its own record.

    Built from :meth:`DepsReport.names` and
    :meth:`DepsReport.counts`, so the rendered page is
    computed from the same accessors the tests pin.
    """
    data = report.record()
    n_nodes, n_changelogs = report.counts()
    lines = [
        "# Dependency Sight — the declared graph",
        "",
        f"*Slice {DEPS_SLICE} of the All-Features road "
        "(Part III — Code Intelligence).*",
        "",
        f"**{n_nodes} declared package(s)**: "
        + (", ".join(f"`{name}`" for name in report.names())
           or "none"),
        "",
    ]
    for node in data["nodes"]:
        lines.append(_node_line(node))
    lines += ["", "## Local data", "",
              f"- Changelogs: {data['changelog_status']} "
              f"({n_changelogs} local file(s) searched)",
              f"- Vulnerability data: {data['vuln_status']} "
              f"({len(data['vuln_sources'])} local source(s))"]
    if data["proposal"]:
        proposal = data["proposal"]
        lines += ["", "## Proposal (never applied)", "",
                  f"- `{proposal['package']}` -> "
                  f"{proposal['target_version']}: "
                  f"{proposal['blast_radius']['file_count']} "
                  "file(s) in the blast radius; "
                  f"{proposal['pin_note']}"]
    if data["warnings"]:
        lines += ["", "## Warnings", ""]
        for warning in data["warnings"]:
            lines.append(f"- {warning}")
    lines.append("")
    return "\n".join(lines)
