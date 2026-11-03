"""Type-aware Python depth (M-063).

Part III — Code Intelligence. The roadmap's words for
this slice: "Type-aware Python depth: mypy/pyright
findings triaged into the review; the coder fixes types
it broke in the same turn."

What ships here, in ``mythic_agent/tools/type_depth.py``:

* **Two runners, each honest about absence.** ``mypy``
  and ``pyright`` are detected as they truly are: a
  binary on ``PATH`` or an importable module, and
  whether the project itself configures the runner
  (``mypy.ini`` / ``.mypy.ini`` / ``[tool.mypy]`` /
  ``setup.cfg`` for mypy; ``pyrightconfig.json`` /
  ``[tool.pyright]`` for pyright). A runner that is not
  there reports ``not-installed`` — measured in this
  campaign's own environment at build time: NEITHER
  runner is installed here, so a live type verdict on
  this machine is NOT PROVEN until one is, and no report
  from this module ever dresses that absence as a clean
  bill. Live proof therefore rides fake runner binaries
  on ``PATH`` speaking the real output contracts (the
  M-053 pattern), plus the parsers proven directly on
  recorded real-format output.
* **The neighbour is reused, never duplicated.**
  Annotation coverage and the mypy error-count road are
  :mod:`mythic_agent.core.type_coverage`'s (M-007-era,
  R-007) — this module builds on its ``measure()`` for
  the standing coverage account and adds the finding
  level depth (parsed findings, triage, charging) that
  the coverage module never claimed.
* **Triage into the review.** Every parsed finding is
  classified by kind from its checker code/rule (or,
  failing that, its message): ``annotation``,
  ``incompatible``, ``attribute``, ``name`` or
  ``other`` — a deterministic classification from the
  checker's own words, never a guess at severity the
  checker did not state.
* **Broke-here vs pre-existing, charged like M-052.**
  For an edit, the before-content is checked through a
  temporary twin (the M-052 road) and the after findings
  are diffed against the before account as a line-blind
  multiset on (runner, code, message, path): what
  remains is ``broke-here`` — the coder's own breakage,
  returned in the same turn on the write/replace tool
  road beside M-052's truth note, gated by the
  ``type_depth`` setting; what matched is
  ``pre-existing`` and is counted, never charged;
  findings an edit removed are counted as resolved.
  A standing check (no edit) charges nothing: its
  findings are ``standing``.
* **The surfaces.** ``Agent.type_depth(path=None)`` and
  ``/types [show | <path>]`` on the terminal and TUI
  system-command roads, sharing this module's parser
  and formatter. The setting ``type_depth`` (on by
  default) closes the road plainly.

Honesty rules, pinned by the slice's tests:

* **Absence is never cleanliness.** No runner installed
  is a ``not-installed`` report saying a live type
  verdict is NOT PROVEN — never zero findings dressed
  as "no problems".
* **Only the checker's own words are parsed.** A line
  that matches neither runner's output contract is
  ignored by that parser, never reinterpreted.
* **Pre-existing findings are not the edit's fault.**
  The line-blind multiset diff is the charge sheet.
* **This road never edits.** It reports; fixing is the
  coder's next act, in the same turn.
"""

from __future__ import annotations

__all__ = [
    "PLAIN_EXPLANATION",
    "TYPE_SLICE",
    "USAGE",
    "RunnerInfo",
    "TypeFinding",
    "TypeReport",
    "check_after_edit",
    "classify_finding",
    "detect_runners",
    "enabled_from_config",
    "format_type_report",
    "parse_pyright_output",
    "parse_mypy_output",
    "parse_types_args",
    "render_markdown",
    "run_type_check",
    "triage_findings",
    "type_depth",
    "type_note_for_edit",
]

import importlib.util
import json
import re
import shutil
import subprocess
import tempfile
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

TYPE_SLICE = "M-063"

PLAIN_EXPLANATION = (
    "Type depth runs the project's type checkers — mypy "
    "and pyright, whichever truly exist — and triages "
    "their findings into the review, classified by kind. "
    "After an edit, only the type errors the edit itself "
    "introduced come back as broke-here facts to fix in "
    "the same turn; pre-existing findings are counted, "
    "never charged. A checker that is not installed says "
    "so plainly: its absence is never a clean bill, and "
    "a live type verdict without a checker is NOT "
    "PROVEN. /types shows the standing account, /types "
    "<path> one file's."
)

USAGE = "Usage: /types [show | <path>]"

SEVERITIES = ("error", "warning", "info")

CATEGORIES = ("annotation", "incompatible", "attribute",
              "name", "other")

#: Runner configuration files / markers, per runner.
_MYPY_CONFIG_FILES = ("mypy.ini", ".mypy.ini")
_PYRIGHT_CONFIG_FILES = ("pyrightconfig.json",)

_MYPY_LINE = re.compile(
    r"^(?P<path>.+?):(?P<line>\d+)(?::(?P<col>\d+))?: "
    r"(?P<severity>error|warning|note): (?P<message>.*)$")
_MYPY_CODE = re.compile(r"\[(?P<code>[a-z0-9-]+)\]\s*$")
_PYRIGHT_LINE = re.compile(
    r"^\s*(?P<path>.+?):(?P<line>\d+):(?P<col>\d+) - "
    r"(?P<severity>error|warning|information): "
    r"(?P<message>.*)$")
_PYRIGHT_RULE = re.compile(r"\((?P<rule>[A-Za-z0-9]+)\)\s*$")


@dataclass
class TypeFinding:
    """One type-checker finding, in a runner-neutral shape."""

    runner: str = ""        # mypy | pyright
    severity: str = "error"
    path: str = ""
    line: int = 0
    col: int = 0
    code: str = ""          # mypy error code / pyright rule
    message: str = ""
    category: str = "other"
    verdict: str = "standing"  # standing | broke-here | pre-existing

    def __post_init__(self) -> None:
        if self.severity not in SEVERITIES:
            raise ValueError(
                f"severity must be one of {SEVERITIES}, "
                f"got {self.severity!r}")
        if self.category not in CATEGORIES:
            raise ValueError(
                f"category must be one of {CATEGORIES}, "
                f"got {self.category!r}")

    def key(self) -> Tuple[str, str, str, str]:
        """The charge-sheet key — deliberately line-blind."""
        return (self.runner, self.code, self.message, self.path)

    def record(self) -> Dict[str, Any]:
        return {"runner": self.runner, "severity": self.severity,
                "path": self.path, "line": self.line,
                "col": self.col, "code": self.code,
                "message": self.message, "category": self.category,
                "verdict": self.verdict}

    def one_line(self) -> str:
        where = f"{self.path}:{self.line}" if self.path else f"line {self.line}"
        code = f"/{self.code}" if self.code else ""
        return (f"[{self.severity}] {where} "
                f"({self.runner}{code}, {self.category}, "
                f"{self.verdict}): {self.message}")


@dataclass
class RunnerInfo:
    """One runner's honest state in this environment."""

    name: str = ""              # mypy | pyright
    available: bool = False
    configured: bool = False
    command: List[str] = field(default_factory=list)
    status: str = "not-installed"  # ok | not-installed | error
    note: str = ""
    findings: List[TypeFinding] = field(default_factory=list)

    def record(self) -> Dict[str, Any]:
        return {"name": self.name, "available": self.available,
                "configured": self.configured,
                "command": list(self.command),
                "status": self.status, "note": self.note,
                "findings": [f.record() for f in self.findings]}


@dataclass
class TypeReport:
    """One type-depth account: standing, or for one edit."""

    path: str = ""
    status: str = "ok"  # ok | disabled | error | not-installed
    runners: List[RunnerInfo] = field(default_factory=list)
    findings: List[TypeFinding] = field(default_factory=list)
    new_findings: List[TypeFinding] = field(default_factory=list)
    resolved_count: int = 0
    preexisting_count: int = 0
    coverage: Optional[Dict[str, Any]] = None
    note: str = ""

    @property
    def new_errors(self) -> List[TypeFinding]:
        return [f for f in self.new_findings
                if f.severity == "error"]

    @property
    def has_new_errors(self) -> bool:
        return bool(self.new_errors)

    def runner_names(self) -> Tuple[str, ...]:
        """Every runner that truly ran, in report order."""
        return tuple(r.name for r in self.runners
                     if r.status == "ok")

    def counts(self) -> Tuple[int, int, int]:
        """(findings, broke-here, pre-existing)."""
        return (len(self.findings), len(self.new_findings),
                self.preexisting_count)

    def record(self) -> Dict[str, Any]:
        return {"path": self.path, "status": self.status,
                "runners": [r.record() for r in self.runners],
                "findings": [f.record() for f in self.findings],
                "new_findings": [f.record() for f in self.new_findings],
                "new_errors": [f.record() for f in self.new_errors],
                "resolved_count": self.resolved_count,
                "preexisting_count": self.preexisting_count,
                "has_new_errors": self.has_new_errors,
                "coverage": self.coverage,
                "note": self.note}


# ---------------------------------------------------------------------------
# Classification — from the checker's own code/rule/message
# ---------------------------------------------------------------------------

def classify_finding(code: str, message: str) -> str:
    """One finding's kind, from its code/rule or message."""
    token = (code or "").lower()
    words = (message or "").lower()
    if ("annot" in token or "untyped" in token
            or token in ("type-arg",)
            or "annotation" in words or "untyped" in words):
        return "annotation"
    if ("attr" in token or "attribute" in token
            or "optional" in token or "member" in token
            or "has no attribute" in words):
        return "attribute"
    if (token in ("name-defined", "name-error")
            or "undefined" in token or "unknown" in token
            or "not defined" in words or "undefined" in words):
        return "name"
    if (token in ("assignment", "arg-type", "return-value",
                  "return", "call-arg", "call-overload",
                   "operator", "index", "incompatible",
                   "misc")
            or "incompatible" in token or "assignment" in token
            or "incompatible" in words
            or "cannot be assigned" in words):
        return "incompatible"
    return "other"


# ---------------------------------------------------------------------------
# Parsers — only the checkers' own output contracts
# ---------------------------------------------------------------------------

def parse_mypy_output(text: str) -> List[TypeFinding]:
    """Findings from mypy text output (its real contract).

    Lines are ``path:line[:col]: error|warning|note:
    message [code]``; ``note`` lines ride as ``info``.
    Lines outside the contract are ignored, never
    reinterpreted.
    """
    findings: List[TypeFinding] = []
    for raw in (text or "").splitlines():
        match = _MYPY_LINE.match(raw.strip())
        if match is None:
            continue
        message = match.group("message").strip()
        code = ""
        code_match = _MYPY_CODE.search(message)
        if code_match is not None:
            code = code_match.group("code")
            message = message[:code_match.start()].strip()
        severity = match.group("severity")
        findings.append(TypeFinding(
            runner="mypy",
            severity="info" if severity == "note" else severity,
            path=match.group("path"), line=int(match.group("line")),
            col=int(match.group("col") or 0), code=code,
            message=message,
            category=classify_finding(code, message)))
    return findings


def parse_pyright_output(text: str) -> List[TypeFinding]:
    """Findings from pyright output — JSON or text contract.

    ``--outputjson`` documents carry
    ``generalDiagnostics`` with 0-based range starts and
    a ``rule``; the text contract is
    ``path:line:col - error|warning|information: message
    (rule)``. Text outside either contract is ignored.
    """
    stripped = (text or "").strip()
    if stripped.startswith("{"):
        try:
            data = json.loads(stripped)
        except ValueError:
            return []
        findings = []
        for item in data.get("generalDiagnostics", []) or []:
            if not isinstance(item, dict):
                continue
            rule = str(item.get("rule") or "")
            message = str(item.get("message") or "")
            start = ((item.get("range") or {}).get("start") or {})
            severity = str(item.get("severity") or "error")
            findings.append(TypeFinding(
                runner="pyright",
                severity=("info" if severity == "information"
                          else severity),
                path=str(item.get("file") or ""),
                line=int(start.get("line") or 0) + 1,
                col=int(start.get("character") or 0) + 1,
                code=rule, message=message,
                category=classify_finding(rule, message)))
        return findings
    findings = []
    for raw in (text or "").splitlines():
        match = _PYRIGHT_LINE.match(raw)
        if match is None:
            continue
        message = match.group("message").strip()
        rule = ""
        rule_match = _PYRIGHT_RULE.search(message)
        if rule_match is not None:
            rule = rule_match.group("rule")
            message = message[:rule_match.start()].strip()
        severity = match.group("severity")
        findings.append(TypeFinding(
            runner="pyright",
            severity="info" if severity == "information" else severity,
            path=match.group("path"), line=int(match.group("line")),
            col=int(match.group("col")), code=rule, message=message,
            category=classify_finding(rule, message)))
    return findings


_PARSERS = {"mypy": parse_mypy_output, "pyright": parse_pyright_output}


# ---------------------------------------------------------------------------
# Detection — available, configured, honestly neither
# ---------------------------------------------------------------------------

def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _runner_command(name: str) -> List[str]:
    """The runner's argv prefix, or [] when it is absent."""
    binary = shutil.which(name)
    if binary is not None:
        if name == "mypy":
            return [binary, "--no-error-summary",
                    "--show-column-numbers", "--show-error-codes"]
        return [binary, "--outputjson"]
    if importlib.util.find_spec(name) is not None:
        import sys
        if name == "mypy":
            return [sys.executable, "-m", "mypy",
                    "--no-error-summary", "--show-column-numbers",
                    "--show-error-codes"]
        return [sys.executable, "-m", "pyright", "--outputjson"]
    return []


def _runner_configured(name: str, root: Path) -> bool:
    """True when the project itself configures *name*."""
    if name == "mypy":
        if any((root / f).is_file() for f in _MYPY_CONFIG_FILES):
            return True
        if "[tool.mypy" in _read_text(root / "pyproject.toml"):
            return True
        return "[mypy]" in _read_text(root / "setup.cfg")
    if any((root / f).is_file() for f in _PYRIGHT_CONFIG_FILES):
        return True
    return "[tool.pyright" in _read_text(root / "pyproject.toml")


def detect_runners(root: Path | str) -> List[RunnerInfo]:
    """Both runners' honest state for the project at *root*."""
    base = Path(root)
    runners: List[RunnerInfo] = []
    for name in ("mypy", "pyright"):
        command = _runner_command(name)
        configured = _runner_configured(name, base)
        if command:
            runners.append(RunnerInfo(
                name=name, available=True, configured=configured,
                command=command, status="ok"))
        else:
            runners.append(RunnerInfo(
                name=name, available=False, configured=configured,
                status="not-installed",
                note=(f"{name} is not installed (no binary on "
                      "PATH and no importable module), so it "
                      "checked nothing")))
    return runners


# ---------------------------------------------------------------------------
# Running — bounded subprocesses over named targets
# ---------------------------------------------------------------------------

def _run_one(runner: RunnerInfo, targets: Sequence[Path],
             root: Path, *, timeout: float) -> RunnerInfo:
    """Run one available runner over *targets*."""
    if not runner.available:
        return runner
    try:
        result = subprocess.run(
            [*runner.command, *[str(t) for t in targets]],
            cwd=str(root), capture_output=True, text=True,
            timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        runner.status = "error"
        runner.note = f"the {runner.name} runner could not run: {exc}"
        return runner
    output = (result.stdout or "") + (result.stderr or "")
    runner.findings = _PARSERS[runner.name](output)
    if runner.name == "pyright" and result.returncode not in (0, 1):
        runner.status = "error"
        runner.note = (f"pyright exited {result.returncode}: "
                       f"{(result.stderr or '').strip()[:200]}")
    return runner


def run_type_check(root: Path | str, targets: Sequence[Path | str], *,
                   timeout: float = 60.0) -> TypeReport:
    """Run every available runner over *targets*.

    No available runner is a ``not-installed`` report —
    a live type verdict is NOT PROVEN here, never a
    clean bill. Findings carry the ``standing`` verdict.
    """
    base = Path(root)
    paths = [Path(t) for t in targets]
    report = TypeReport(
        path=", ".join(str(p) for p in paths))
    report.runners = [
        _run_one(runner, paths, base, timeout=timeout)
        for runner in detect_runners(base)]
    report.findings = [f for r in report.runners
                       for f in r.findings]
    if not any(r.status == "ok" for r in report.runners):
        report.status = "not-installed"
        report.note = (
            "no type checker is installed (mypy and pyright "
            "both absent), so no live type verdict exists "
            "here — NOT PROVEN, never a clean bill")
    return report


def _coverage_account(root: Path) -> Optional[Dict[str, Any]]:
    """The standing annotation-coverage account, if any.

    Reuses :mod:`mythic_agent.core.type_coverage` — its
    ``measure()`` is package-specific, so a workspace
    without that package honestly gets ``None``.
    """
    if not (root / "mythic_agent").is_dir():
        return None
    from ..core.type_coverage import measure

    report = measure(root)
    return {"root": report.root,
            "mypy_available": report.mypy_available,
            "modules": report.module_count,
            "functions": report.functions_total,
            "params_pct": round(report.params_pct, 2),
            "returns_pct": round(report.returns_pct, 2),
            "skipped": list(report.skipped)}


# ---------------------------------------------------------------------------
# Triage — the line-blind charge sheet, as in M-052
# ---------------------------------------------------------------------------

def triage_findings(
        after: Sequence[TypeFinding],
        before: Sequence[TypeFinding],
) -> Tuple[List[TypeFinding], int, int]:
    """(triaged after findings, resolved, pre-existing).

    Multiset diff on the line-blind key: an after-finding
    with an unmatched before twin is ``broke-here``; a
    matched one is ``pre-existing``. Before findings with
    no after twin were resolved by the edit.
    """
    remaining: Counter = Counter(f.key() for f in before)
    triaged: List[TypeFinding] = []
    preexisting = 0
    for finding in after:
        if remaining[finding.key()] > 0:
            remaining[finding.key()] -= 1
            finding.verdict = "pre-existing"
            preexisting += 1
        else:
            finding.verdict = "broke-here"
        triaged.append(finding)
    return triaged, sum(remaining.values()), preexisting


def _findings_for_content(content: str, target: Path,
                          root: Path, *,
                          timeout: float) -> List[TypeFinding]:
    """Runner findings for *content* as if it were *target*.

    The before-state of an edit no longer exists on disk,
    so the runners check a temporary twin carrying the
    same suffix in the same directory; reported paths are
    the real file's, never the twin's.
    """
    if target.suffix != ".py":
        return []
    with tempfile.NamedTemporaryFile(
            "w", suffix=".py", prefix=".mythic-type-",
            dir=str(target.parent) if target.parent.exists() else None,
            delete=False, encoding="utf-8") as handle:
        handle.write(content)
        twin = Path(handle.name)
    try:
        report = run_type_check(root, [twin], timeout=timeout)
    finally:
        twin.unlink(missing_ok=True)
    findings = report.findings
    for finding in findings:
        finding.path = str(target)
    return findings


def check_after_edit(path: Path | str, *,
                     before_content: Optional[str] = None,
                     root: Optional[Path | str] = None,
                     timeout: float = 60.0) -> TypeReport:
    """One edit's type account: after, diffed to before.

    *before_content* is the file's text before the edit
    (``None`` for a newly created file, whose every
    finding is broke-here). With no runner installed the
    report is ``not-installed`` and charges nothing.
    """
    target = Path(path)
    base = Path(root).resolve() if root is not None else target.resolve().parent
    if not target.is_absolute():
        target = base / target
    after = run_type_check(base, [target], timeout=timeout)
    if after.status == "not-installed":
        after.path = str(target)
        return after
    before = [] if before_content is None else _findings_for_content(
        before_content, target, base, timeout=timeout)
    triaged, resolved, preexisting = triage_findings(
        after.findings, before)
    after.path = str(target)
    after.findings = triaged
    after.new_findings = [f for f in triaged
                          if f.verdict == "broke-here"]
    after.resolved_count = resolved
    after.preexisting_count = preexisting
    return after


# ---------------------------------------------------------------------------
# The standing road + the same-turn note
# ---------------------------------------------------------------------------

def enabled_from_config(config: Optional[Dict[str, Any]]) -> bool:
    """Type depth is on unless config says ``type_depth: false``."""
    if not config:
        return True
    return config.get("type_depth", True) is not False


def type_depth(workspace: Any, path: Any = None, *,
               enabled: bool = True,
               timeout: float = 60.0) -> TypeReport:
    """One standing type account — a file's, or the workspace's.

    With *path*, the runners check that one file. Without
    it, they check the workspace's top-level Python
    packages and the report also carries the annotation
    coverage account where the coverage neighbour's
    package exists. A missing workspace is an honest
    ``error`` report; a switched-off road reads nothing.
    """
    if not enabled:
        return TypeReport(
            status="disabled",
            note=("type depth is off (the type_depth "
                  "setting), so no project file was read"))
    root = Path(workspace)
    if not root.is_dir():
        return TypeReport(
            status="error",
            note=f"no workspace at {root} — nothing was checked")
    if path is not None:
        target = Path(path)
        if not target.is_absolute():
            target = root / target
        if not target.is_file():
            return TypeReport(
                path=str(target), status="error",
                note=f"no such file to check: {path}")
        report = run_type_check(root, [target], timeout=timeout)
        report.path = str(target)
        return report
    packages = [child for child in sorted(root.iterdir())
                if child.is_dir()
                and (child / "__init__.py").is_file()
                and not child.name.startswith(".")]
    if not packages:
        report = TypeReport(
            status="error",
            note=("no Python package (a top-level directory "
                  "with __init__.py) exists in this workspace, "
                  "so the standing type check had no package "
                  "to cover — this is not a clean bill"))
        report.coverage = _coverage_account(root)
        return report
    report = run_type_check(root, packages, timeout=timeout)
    report.coverage = _coverage_account(root)
    return report


def type_note_for_edit(path: Path | str,
                       before_content: Optional[str], *,
                       root: Optional[Path | str] = None) -> str:
    """The tool-result note for one edit: '' when clean.

    Non-empty only when the edit introduced new
    error-severity type findings, or when the check
    itself could not run (an honest note, never a failed
    edit). No runner installed is silence on this road —
    the standing account names that absence; an edit is
    not charged for a checker that does not exist.
    """
    try:
        report = check_after_edit(
            path, before_content=before_content, root=root)
    except Exception as exc:
        return (f"\nType check could not run: {exc}. "
                f"The edit itself stands; check the file's "
                f"types before the turn ends.")
    if report.status == "not-installed" or not report.has_new_errors:
        return ""
    lines = [
        f"Type depth: this edit introduced "
        f"{len(report.new_errors)} new type error(s) in "
        f"{report.path} — fix them before the turn ends:",
    ]
    lines.extend(f"  {f.one_line()}" for f in report.new_errors)
    return "\n" + "\n".join(lines)


# ---------------------------------------------------------------------------
# Surfaces: the shared parser + formatters
# ---------------------------------------------------------------------------

def parse_types_args(arguments: str) -> Dict[str, Any]:
    """Parse ``/types`` arguments.

    Grammar::

        /types
        /types show
        /types <path>
        /types show <path>

    Raises :class:`ValueError` on a usage error.
    """
    tokens = (arguments or "").split()
    if not tokens:
        return {"action": "show", "path": None}
    if tokens[0] == "show":
        if len(tokens) == 1:
            return {"action": "show", "path": None}
        if len(tokens) == 2:
            return {"action": "show", "path": tokens[1]}
        raise ValueError(f"{USAGE} — name one path, or none")
    if len(tokens) == 1:
        return {"action": "show", "path": tokens[0]}
    raise ValueError(f"{USAGE} — name one path, or none")


def format_type_report(status: Dict[str, Any]) -> str:
    """One type-depth call's account, from an Agent status mapping."""
    report = status["report"]
    lines = [f"Type depth ({TYPE_SLICE}): "
             f"{report['path'] or 'workspace'} — "
             f"status {report['status']}."]
    for runner in report["runners"]:
        if runner["status"] == "ok":
            lines.append(
                f"  {runner['name']}: ran "
                f"({'configured' if runner['configured'] else 'unconfigured'})"
                f" — {len(runner['findings'])} finding(s)")
        else:
            lines.append(
                f"  {runner['name']}: {runner['status']} — "
                f"{runner['note']}")
    n_findings, n_new, n_pre = (len(report["findings"]),
                                len(report["new_findings"]),
                                report["preexisting_count"])
    lines.append(
        f"  Findings: {n_findings} ({n_new} broke-here, "
        f"{n_pre} pre-existing, "
        f"{report['resolved_count']} resolved).")
    for finding in report["findings"]:
        item = TypeFinding(**{k: finding[k] for k in
                              ("runner", "severity", "path", "line",
                               "col", "code", "message", "category",
                               "verdict")})
        lines.append(f"    {item.one_line()}")
    coverage = report.get("coverage")
    if coverage:
        lines.append(
            f"  Annotation coverage: {coverage['functions']} "
            f"function(s), params {coverage['params_pct']}%, "
            f"returns {coverage['returns_pct']}%.")
    if report["note"]:
        lines.append(f"  {report['note']}")
    lines.append(status["plain_explanation"])
    return "\n".join(lines)


def render_markdown(report: TypeReport) -> str:
    """Render *report* as a human report, from its own record.

    Built from :meth:`TypeReport.runner_names` and
    :meth:`TypeReport.counts`, so the rendered page is
    computed from the same accessors the tests pin.
    """
    data = report.record()
    n_findings, n_new, n_pre = report.counts()
    runners = ", ".join(report.runner_names()) or "none"
    lines = [
        "# Type Depth — mypy/pyright findings, triaged",
        "",
        f"*Slice {TYPE_SLICE} of the All-Features road "
        "(Part III — Code Intelligence). Triage only — "
        "nothing is edited by this report.*",
        "",
        f"**{n_findings} finding(s)** from runner(s): "
        f"{runners}; **{n_new} broke-here**, "
        f"**{n_pre} pre-existing**, "
        f"{data['resolved_count']} resolved.",
        "",
        "## Findings",
        "",
    ]
    for finding in data["findings"]:
        lines.append(
            f"- `{finding['path']}:{finding['line']}` — "
            f"[{finding['severity']}] {finding['message']} "
            f"({finding['runner']}/{finding['code'] or '-'}, "
            f"{finding['category']}, {finding['verdict']})")
    if not data["findings"]:
        lines.append("- none from the runners that ran")
    lines.append("")
    return "\n".join(lines)
