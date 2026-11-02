"""Code sensing (M-062) — dead code and duplication.

Part III — Code Intelligence. The roadmap's words for
this slice: "Dead-code and duplication sensing:
structural reports for the Cartographer; sensing only —
deletion is always a separate, approved slice."

What ships here, in ``mythic_agent/tools/code_sensing.py``:

* **Dead code, from the shipped scanner.** Dead-code
  sensing reuses the R-006 gate's own engine,
  :mod:`mythic_agent.core.dead_code_scan` — this module
  builds no second scanner. The scan covers the Python
  packages at the workspace's top level (directories
  carrying an ``__init__.py`` — the gate's own scope),
  and the report names exactly which packages were
  scanned; a workspace with no such package is told so
  plainly, never given a fake empty bill. Where a
  dead-code quarantine file exists at the scanned
  package's docs shelf (``docs/DEAD_CODE_QUARANTINE.txt``
  at the workspace root), its state is named: how many
  sensed items it already records and how many it does
  not — the gate's record, not a new one.
* **Duplication, structural only.** Every function and
  method body in the workspace's Python files (the tree
  pruned of VCS, caches and virtualenvs) is fingerprinted
  by its *structure*: the AST dumped with function,
  argument and variable names and every literal value
  normalised away, while node types, operators and
  attribute names are kept. Two bodies share a fingerprint
  only when they are the same shape of code — renamed
  copies and re-literal'd copies are caught; textual
  coincidence (same words, different shape) is not, and
  near-misses are never dressed as duplicates. Only
  bodies at or above a named size floor can form a
  cluster, so trivial getters and one-line stubs that
  inevitably share a shape never count.
* **A report shaped for the Cartographer.** One
  structural report: the dead items (file, line, name,
  kind, counted by kind and by file) and the duplication
  clusters (each member's file, line, name and size, and
  the cluster's total size) — the terrain map a later,
  separate clean-up slice would work from.
* **The surfaces.** ``Agent.code_sensing()`` and
  ``/sensing`` on the terminal and TUI system-command
  roads, sharing this module's parser and formatter:
  ``/sensing``, ``/sensing show``, ``/sensing dead``
  and ``/sensing dup``. The setting ``code_sensing``
  (on by default) closes the road plainly.

Honesty rules, pinned by the slice's tests:

* **Sensing only — nothing is ever deleted or edited.**
  This module has no delete, edit or write path at all;
  producing a report changes no file. Deletion is
  always a separate, approved slice.
* **Structure, not text.** A duplication cluster is an
  exact structural fingerprint match at or above the
  size floor — never a similarity score, never a guess.
* **Scope is named, never implied.** The dead-code
  road's package scope and the duplication road's
  pruned tree are stated in every report, with skipped
  and oversized files counted and named as warnings.
* **Off means off.** With ``code_sensing`` false, no
  file is read on this road at all.
"""

from __future__ import annotations

__all__ = [
    "MIN_CLUSTER_NODES",
    "PLAIN_EXPLANATION",
    "SENSING_SLICE",
    "USAGE",
    "DeadSense",
    "DupCluster",
    "DupMember",
    "SensingReport",
    "code_sensing",
    "enabled_from_config",
    "find_duplications",
    "format_sensing_report",
    "parse_sensing_args",
    "render_markdown",
    "scan_dead_code",
    "structural_fingerprint",
]

import ast
import copy
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SENSING_SLICE = "M-062"

#: A function body must carry at least this many AST
#: nodes before its shape can form a duplication
#: cluster — below it, shared shapes are inevitable
#: (getters, stubs) and prove nothing.
MIN_CLUSTER_NODES = 15

#: Directories the sensing scans never enter.
_SKIP_DIRS = {".git", ".hg", ".svn", "__pycache__",
              "node_modules", "dist", "build",
              ".venv", ".venv-baseline", "venv"}

#: Caps for the workspace scans; every cut is named.
MAX_SCAN_FILES = 2000
MAX_FILE_BYTES = 256_000
MAX_CLUSTERS = 50

PLAIN_EXPLANATION = (
    "Code sensing is a read-only structural report for "
    "the Cartographer. /sensing shows both halves, "
    "/sensing dead lists code the shipped dead-code "
    "scanner finds defined but never referenced in the "
    "workspace's Python packages, and /sensing dup lists "
    "duplication clusters — function bodies whose AST "
    "structure is identical once names and literal values "
    "are normalised away, at or above a size floor so "
    "trivial shapes never count. Sensing only: this road "
    "never deletes or edits anything; deletion is always "
    "a separate, approved slice."
)

USAGE = "Usage: /sensing [show | dead | dup]"


def enabled_from_config(config: Optional[Dict[str, Any]]) -> bool:
    """Code sensing is on unless config says so."""
    if not config:
        return True
    return config.get("code_sensing", True) is not False


# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DeadSense:
    """One dead-code item, workspace-relative."""

    path: str
    line: int
    name: str
    kind: str

    def record(self) -> Dict[str, Any]:
        return {"path": self.path, "line": self.line,
                "name": self.name, "kind": self.kind}


@dataclass(frozen=True)
class DupMember:
    """One function body inside a duplication cluster."""

    path: str
    line: int
    name: str
    nodes: int
    lines: int

    def record(self) -> Dict[str, Any]:
        return {"path": self.path, "line": self.line,
                "name": self.name, "nodes": self.nodes,
                "lines": self.lines}


@dataclass(frozen=True)
class DupCluster:
    """One structural fingerprint shared by 2+ bodies."""

    fingerprint: str
    nodes: int
    members: Tuple[DupMember, ...] = ()

    @property
    def total_nodes(self) -> int:
        return self.nodes * len(self.members)

    def record(self) -> Dict[str, Any]:
        return {"fingerprint": self.fingerprint,
                "nodes": self.nodes,
                "members": [m.record() for m in self.members],
                "member_count": len(self.members),
                "total_nodes": self.total_nodes}


@dataclass
class SensingReport:
    """One sensing call's whole account."""

    kind: str = "show"  # show | dead | dup
    status: str = "ok"  # ok | disabled | error
    packages_scanned: List[str] = field(default_factory=list)
    files_scanned: int = 0
    dead_items: List[DeadSense] = field(default_factory=list)
    clusters: List[DupCluster] = field(default_factory=list)
    quarantine_recorded: int = 0
    quarantine_unrecorded: int = 0
    warnings: List[str] = field(default_factory=list)
    note: str = ""

    def dead_names(self) -> Tuple[str, ...]:
        """Every sensed dead item's name, in report order."""
        return tuple(item.name for item in self.dead_items)

    def counts(self) -> Tuple[int, int, int]:
        """(dead items, duplication clusters, files scanned)."""
        return (len(self.dead_items), len(self.clusters),
                self.files_scanned)

    def record(self) -> Dict[str, Any]:
        return {"kind": self.kind, "status": self.status,
                "packages_scanned": list(self.packages_scanned),
                "files_scanned": self.files_scanned,
                "dead_items": [i.record() for i in self.dead_items],
                "clusters": [c.record() for c in self.clusters],
                "quarantine_recorded": self.quarantine_recorded,
                "quarantine_unrecorded": self.quarantine_unrecorded,
                "warnings": list(self.warnings),
                "note": self.note}


# ---------------------------------------------------------------------------
# Dead code: the shipped scanner, over the workspace's packages
# ---------------------------------------------------------------------------

def _package_dirs(root: Path) -> List[Path]:
    """Top-level Python packages (dirs carrying __init__.py)."""
    if not root.is_dir():
        return []
    found = []
    for child in sorted(root.iterdir(), key=lambda p: p.name):
        if not child.is_dir():
            continue
        if child.name in _SKIP_DIRS or child.name.startswith("."):
            continue
        if (child / "__init__.py").is_file():
            found.append(child)
    return found


def scan_dead_code(
        workspace: Any,
) -> Tuple[List[DeadSense], List[str], List[str], int, int]:
    """Run the shipped dead-code scanner over the packages.

    Returns (items, packages, warnings, quarantine_recorded,
    quarantine_unrecorded). Items are workspace-relative.
    The scanner is :mod:`mythic_agent.core.dead_code_scan`
    — the R-006 gate's engine, reused, never duplicated.
    A workspace with no top-level Python package yields
    no items and a warning saying exactly that.
    """
    from ..core.dead_code_scan import load_quarantine, scan

    root = Path(workspace)
    packages = _package_dirs(root)
    warnings: List[str] = []
    if not packages:
        warnings.append(
            "no Python package (a top-level directory with "
            "__init__.py) exists in this workspace, so the "
            "dead-code scan had no package to cover — this "
            "is not a claim that the workspace has no dead "
            "code")
        return [], [], warnings, 0, 0
    items: List[DeadSense] = []
    for package in packages:
        for path, lineno, name, kind in scan(str(package)):
            raw = Path(path)
            try:
                rel = raw.relative_to(root).as_posix()
            except ValueError:
                rel = raw.name
            items.append(DeadSense(path=rel, line=lineno,
                                   name=name, kind=kind))
    items.sort(key=lambda i: (i.path, i.line))
    recorded = 0
    unrecorded = 0
    quarantine = root / "docs" / "DEAD_CODE_QUARANTINE.txt"
    if quarantine.is_file():
        known = set()
        for qpath, _line, qname, qkind in load_quarantine(
                str(quarantine)):
            known.add((qpath, qname, qkind))
        for item in items:
            if (item.path, item.name, item.kind) in known:
                recorded += 1
            else:
                unrecorded += 1
    return (items, [p.name for p in packages], warnings,
            recorded, unrecorded)


# ---------------------------------------------------------------------------
# Duplication: structural AST fingerprints
# ---------------------------------------------------------------------------

class _Normaliser(ast.NodeTransformer):
    """Normalise names and literals out of a body shape."""

    def visit_FunctionDef(self, node: ast.FunctionDef):
        node.name = "_"
        self.generic_visit(node)
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        node.name = "_"
        self.generic_visit(node)
        return node

    def visit_ClassDef(self, node: ast.ClassDef):
        node.name = "_"
        self.generic_visit(node)
        return node

    def visit_arg(self, node: ast.arg):
        node.arg = "_"
        self.generic_visit(node)
        return node

    def visit_Name(self, node: ast.Name):
        node.id = "_"
        return node

    def visit_Global(self, node: ast.Global):
        node.names = ["_"] * len(node.names)
        return node

    def visit_Nonlocal(self, node: ast.Nonlocal):
        node.names = ["_"] * len(node.names)
        return node

    def visit_Constant(self, node: ast.Constant):
        node.value = f"<{type(node.value).__name__}>"
        return node


def structural_fingerprint(node: ast.AST) -> Tuple[str, int]:
    """(fingerprint, node count) for one function body.

    The fingerprint is a hash of the AST dumped with
    names and literal values normalised away (see
    :class:`_Normaliser`); attribute names, operators
    and node types are kept, so the shape is structural.
    The input node is never mutated.
    """
    clone = _Normaliser().visit(copy.deepcopy(node))
    ast.fix_missing_locations(clone)
    dump = ast.dump(clone, include_attributes=False)
    count = sum(1 for _ in ast.walk(clone))
    return hashlib.sha256(dump.encode("utf-8")).hexdigest()[:12], count


def _python_files(root: Path) -> List[Path]:
    if not root.is_dir():
        return []
    found = [p for p in root.rglob("*.py")
             if p.is_file()
             and not any(part in _SKIP_DIRS or part.startswith(".venv")
                         for part in p.parts)]
    return sorted(found, key=lambda p: p.as_posix())


def find_duplications(
        workspace: Any,
) -> Tuple[List[DupCluster], int, List[str]]:
    """Structural duplication clusters over the workspace.

    Returns (clusters, files_scanned, warnings). Only
    function/method bodies at or above
    :data:`MIN_CLUSTER_NODES` can cluster, and a cluster
    needs two or more bodies sharing one fingerprint.
    Unreadable, oversized, binary and unparseable files
    are skipped and counted in the warnings.
    """
    root = Path(workspace)
    warnings: List[str] = []
    files = _python_files(root)
    scanned = 0
    skipped = 0
    groups: Dict[str, Dict[str, Any]] = {}
    for path in files:
        if scanned + skipped >= MAX_SCAN_FILES:
            warnings.append(
                f"duplication scan file cap reached "
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
        scanned += 1
        try:
            rel = path.relative_to(root).as_posix()
        except ValueError:
            rel = path.name
        for node in ast.walk(tree):
            if not isinstance(
                    node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            fingerprint, count = structural_fingerprint(node)
            if count < MIN_CLUSTER_NODES:
                continue
            lines = (node.end_lineno or node.lineno) - node.lineno + 1
            slot = groups.setdefault(
                fingerprint, {"nodes": count, "members": []})
            slot["members"].append(DupMember(
                path=rel, line=node.lineno, name=node.name,
                nodes=count, lines=lines))
    clusters = []
    for fingerprint, slot in groups.items():
        if len(slot["members"]) < 2:
            continue
        members = tuple(sorted(
            slot["members"], key=lambda m: (m.path, m.line)))
        clusters.append(DupCluster(
            fingerprint=fingerprint, nodes=slot["nodes"],
            members=members))
    clusters.sort(key=lambda c: (-c.total_nodes, c.fingerprint))
    if len(clusters) > MAX_CLUSTERS:
        warnings.append(
            f"duplication cluster cap reached ({MAX_CLUSTERS} "
            f"of {len(clusters)} clusters shown); the rest "
            "were sensed but not listed")
        clusters = clusters[:MAX_CLUSTERS]
    if skipped:
        warnings.append(
            f"{skipped} Python file(s) were skipped by the "
            "duplication scan (unreadable, oversized, binary "
            "or unparseable) and are not counted in any "
            "cluster")
    return clusters, scanned, warnings


# ---------------------------------------------------------------------------
# The sensing road
# ---------------------------------------------------------------------------

def _closed(kind: str) -> SensingReport:
    return SensingReport(
        kind=kind, status="disabled",
        note=("code sensing is off (the code_sensing "
              "setting), so no project file was read"))


def code_sensing(
        workspace: Any, mode: str = "show", *,
        enabled: bool = True,
) -> SensingReport:
    """One structural sensing report — dead, dup, or both.

    Sensing only: this function reads files and deletes
    or edits nothing. A missing workspace is an honest
    ``error`` report. Raises :class:`ValueError` for an
    unknown mode.
    """
    kind = (mode or "show").strip().lower()
    if kind not in ("show", "dead", "dup"):
        raise ValueError(f"{USAGE} — unknown mode {mode!r}")
    report = SensingReport(kind=kind)
    if not enabled:
        return _closed(kind)
    root = Path(workspace)
    if not root.is_dir():
        report.status = "error"
        report.note = (f"no workspace at {root} — nothing "
                       "was sensed")
        return report
    if kind in ("show", "dead"):
        (report.dead_items, report.packages_scanned,
         dead_warnings, report.quarantine_recorded,
         report.quarantine_unrecorded) = scan_dead_code(root)
        report.warnings.extend(dead_warnings)
    if kind in ("show", "dup"):
        (report.clusters, report.files_scanned,
         dup_warnings) = find_duplications(root)
        report.warnings.extend(dup_warnings)
    elif kind == "dead":
        report.files_scanned = len(_python_files(root))
    report.note = ("sensing only — nothing was deleted or "
                   "edited; deletion is always a separate, "
                   "approved slice")
    return report


# ---------------------------------------------------------------------------
# Surfaces: the shared parser + formatters
# ---------------------------------------------------------------------------

def parse_sensing_args(arguments: str) -> Dict[str, Any]:
    """Parse ``/sensing`` arguments into a sensing request.

    Grammar::

        /sensing
        /sensing show
        /sensing dead
        /sensing dup

    Raises :class:`ValueError` on a usage error.
    """
    text = (arguments or "").strip()
    if not text:
        return {"action": "show"}
    tokens = text.split()
    if len(tokens) != 1:
        raise ValueError(f"{USAGE} — name one road, or none")
    head = tokens[0].lower()
    if head in ("show", "dead"):
        return {"action": head}
    if head in ("dup", "duplicates", "duplication"):
        return {"action": "dup"}
    raise ValueError(f"{USAGE} — unknown road {tokens[0]!r}")


def format_sensing_report(status: Dict[str, Any]) -> str:
    """One sensing call's account, from an Agent status mapping."""
    report = status["report"]
    lines = [f"Code sensing ({SENSING_SLICE}): "
             f"{report['kind']} — sensing only, nothing "
             "deleted or edited."]
    if report["kind"] in ("show", "dead"):
        lines.append(
            f"  Dead code: {len(report['dead_items'])} item(s) "
            f"in package(s): "
            f"{', '.join(report['packages_scanned']) or 'none'}.")
        for item in report["dead_items"]:
            lines.append(
                f"    {item['path']}:{item['line']}: "
                f"{item['name']} ({item['kind']})")
        if report["quarantine_recorded"] or \
                report["quarantine_unrecorded"]:
            lines.append(
                f"  Quarantine: {report['quarantine_recorded']} "
                "recorded, "
                f"{report['quarantine_unrecorded']} not yet "
                "recorded.")
    if report["kind"] in ("show", "dup"):
        lines.append(
            f"  Duplication: {len(report['clusters'])} "
            f"cluster(s) over {report['files_scanned']} "
            "Python file(s).")
        for cluster in report["clusters"]:
            lines.append(
                f"    cluster {cluster['fingerprint']} — "
                f"{cluster['member_count']} bodies x "
                f"{cluster['nodes']} nodes:")
            for member in cluster["members"]:
                lines.append(
                    f"      {member['path']}:{member['line']}: "
                    f"{member['name']} ({member['lines']} lines)")
    if report["note"]:
        lines.append(f"  {report['note']}")
    for warning in report["warnings"]:
        lines.append(f"  Warning: {warning}")
    lines.append(status["plain_explanation"])
    return "\n".join(lines)


def render_markdown(report: SensingReport) -> str:
    """Render *report* as a human report, from its own record.

    Built from :meth:`SensingReport.dead_names` and
    :meth:`SensingReport.counts`, so the rendered page is
    computed from the same accessors the tests pin.
    """
    data = report.record()
    n_dead, n_clusters, n_files = report.counts()
    lines = [
        "# Code Sensing — dead code and duplication",
        "",
        f"*Slice {SENSING_SLICE} of the All-Features road "
        "(Part III — Code Intelligence). Sensing only — "
        "nothing is deleted or edited by this report.*",
        "",
        f"**{n_dead} dead item(s)** sensed in package(s) "
        + (", ".join(f"`{name}`" for name in data["packages_scanned"])
           or "none")
        + f"; **{n_clusters} duplication cluster(s)** over "
        f"{n_files} Python file(s).",
        "",
        "## Dead code",
        "",
    ]
    for item in data["dead_items"]:
        lines.append(
            f"- `{item['path']}:{item['line']}` — "
            f"{item['name']} ({item['kind']})")
    if not data["dead_items"]:
        lines.append("- none sensed in the scanned scope")
    lines += ["", "## Duplication clusters", ""]
    for cluster in data["clusters"]:
        lines.append(
            f"- cluster `{cluster['fingerprint']}` — "
            f"{cluster['member_count']} bodies x "
            f"{cluster['nodes']} nodes "
            f"({cluster['total_nodes']} total): "
            + ", ".join(
                f"`{m['path']}:{m['line']}` {m['name']}"
                for m in cluster["members"]))
    if not data["clusters"]:
        lines.append("- none sensed at or above the size floor")
    lines.append("")
    lines.append("Dead names sensed: "
                 + (", ".join(report.dead_names()) or "none"))
    lines.append("")
    return "\n".join(lines)
