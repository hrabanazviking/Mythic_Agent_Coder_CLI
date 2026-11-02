"""Edit-time truth loop (M-052).

Part III — Code Intelligence. After every edit, the file
is checked again and only the *new* errors return to the
coder as facts to fix before the turn ends — the field's
quiet superpower, and the formatter-linter-loop row of the
gap audit (its owning basis is ``tools/review.py``).

What ships here, in ``mythic_agent/tools/edit_truth.py``:

* **Three legs, each honest about absence.** The house
  review (:func:`mythic_agent.tools.review.review_file`,
  run on the before-content through a temporary twin so
  the pre-edit state is measured, never guessed), the
  language server's diagnostics (M-049's
  :func:`mythic_agent.integrations.lsp.diagnostics_for_file`),
  and a configured linter (``ruff`` or ``flake8``, found
  on ``PATH`` or named by the project's own config files;
  run as a subprocess with a bounded wait). A leg that
  cannot run is a *status on the report*, never a clean
  bill: no server installed says ``not-installed``, no
  linter found says ``not-configured``, and neither is
  ever dressed as "no problems".
* **Only new findings are charged to the edit.** Before
  and after findings are compared as multisets keyed on
  (source, severity, check, message) — line numbers are
  deliberately *not* part of the key, so a pre-existing
  finding that merely shifted lines when code above it
  moved is not charged to this edit. What remains after
  the diff is the edit's own new truth; findings the edit
  *removed* are counted as resolved, never hidden.
* **The wiring.** The agent tool road
  (``write_file`` / ``replace_file_content`` in
  ``agents/tools.py``) captures the before-content,
  writes through the house edit journal as it always
  has, then runs :func:`truth_note_for_edit`: when the
  edit introduced new error-severity findings, the
  formatted report is appended to the tool result, so
  the coder sees the facts in the same turn. A clean
  edit's tool result is unchanged. The setting
  ``edit_truth_loop`` (on by default) turns the wiring
  off when the user says so. A failure inside the loop
  itself never breaks the edit — it is appended as an
  honest note saying the check could not run.
* **The surfaces.** ``Agent.edit_truth(path)`` checks one
  file as it stands (its "new" findings are its current
  error findings, there being no edit to diff against),
  and ``/truth <path>`` rides the terminal and the TUI
  system-command roads, sharing this module's parser and
  formatter. No formatter is run here: honouring the
  project's formatter config exactly is the formatter
  covenant, M-053, and nothing here claims it.

Honesty rules, pinned by the slice's tests:

* **Absence is never cleanliness.** Only a leg with
  status ``ok`` may be read as "this checker looked".
* **Pre-existing findings are not the edit's fault.**
  The multiset diff, line-blind, is the charge sheet.
* **The loop never edits.** It reports; fixing is the
  coder's next act, in the same turn, with the facts in
  hand.
"""

from __future__ import annotations

__all__ = [
    "EDIT_TRUTH_SLICE",
    "PLAIN_EXPLANATION",
    "USAGE",
    "Finding",
    "LegReport",
    "TruthReport",
    "check_after_edit",
    "check_file_now",
    "detect_linter",
    "diff_findings",
    "enabled_from_config",
    "findings_from_diagnostics",
    "findings_from_review",
    "format_truth_note",
    "format_truth_report",
    "parse_truth_args",
    "render_markdown",
    "review_content_findings",
    "run_linter",
    "truth_note_for_edit",
]

import shutil
import subprocess
import tempfile
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from .review import Issue, review_file

EDIT_TRUTH_SLICE = "M-052"

PLAIN_EXPLANATION = (
    "After an edit, the file is checked again — the house "
    "review, the language server where one truly runs, and "
    "the project's linter where one is truly configured — "
    "and only the errors the edit itself introduced come "
    "back, as facts to fix before the turn ends. A checker "
    "that is not there says so plainly; it never pretends "
    "the file is clean. /truth <path> shows one file's "
    "standing account."
)

USAGE = "Usage: /truth <path>"

SEVERITIES = ("error", "warning", "info", "hint")

#: Linter candidates, in preference order: (binary, argv tail).
_LINTERS: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("ruff", ("check", "--output-format", "concise")),
    ("flake8", ("--format", "%(path)s:%(row)d:%(col)d: %(code)s %(text)s")),
)

@dataclass
class Finding:
    """One checker finding, in a source-neutral shape."""

    source: str = ""        # review | lsp | linter
    severity: str = "error"
    line: int = 0
    message: str = ""
    check: str = ""
    path: str = ""

    def __post_init__(self) -> None:
        if self.severity not in SEVERITIES:
            raise ValueError(
                f"severity must be one of {SEVERITIES}, "
                f"got {self.severity!r}")

    def key(self) -> Tuple[str, str, str, str]:
        """The charge-sheet key — deliberately line-blind."""
        return (self.source, self.severity, self.check, self.message)

    def record(self) -> Dict[str, Any]:
        return {
            "source": self.source, "severity": self.severity,
            "line": self.line, "message": self.message,
            "check": self.check, "path": self.path,
        }

    def one_line(self) -> str:
        where = f"{self.path}:{self.line}" if self.path else f"line {self.line}"
        return f"[{self.severity}] {where} ({self.source}/{self.check}): {self.message}"


@dataclass
class LegReport:
    """One checker's account: ran, or honestly did not."""

    name: str = ""          # review | lsp | linter
    status: str = "ok"      # ok | not-installed | no-server | not-configured | error
    note: str = ""
    findings: List[Finding] = field(default_factory=list)

    def record(self) -> Dict[str, Any]:
        return {
            "name": self.name, "status": self.status,
            "note": self.note,
            "findings": [f.record() for f in self.findings],
        }


@dataclass
class TruthReport:
    """One file's before/after truth account for one edit."""

    path: str = ""
    legs_before: List[LegReport] = field(default_factory=list)
    legs_after: List[LegReport] = field(default_factory=list)
    new_findings: List[Finding] = field(default_factory=list)
    resolved_count: int = 0
    preexisting_count: int = 0

    @property
    def new_errors(self) -> List[Finding]:
        return [f for f in self.new_findings if f.severity == "error"]

    @property
    def has_new_errors(self) -> bool:
        return bool(self.new_errors)

    def leg_statuses(self) -> Dict[str, str]:
        return {leg.name: leg.status for leg in self.legs_after}

    def record(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "legs_before": [leg.record() for leg in self.legs_before],
            "legs_after": [leg.record() for leg in self.legs_after],
            "new_findings": [f.record() for f in self.new_findings],
            "new_errors": [f.record() for f in self.new_errors],
            "resolved_count": self.resolved_count,
            "preexisting_count": self.preexisting_count,
            "has_new_errors": self.has_new_errors,
            "leg_statuses": self.leg_statuses(),
        }


# ---------------------------------------------------------------------------
# Findings from each leg's native shape
# ---------------------------------------------------------------------------

def findings_from_review(issues: Sequence[Issue]) -> List[Finding]:
    """House review issues as truth findings."""
    return [
        Finding(source="review", severity=issue.severity,
                line=issue.line, message=issue.message,
                check=issue.check, path=issue.path)
        for issue in issues
    ]


def findings_from_diagnostics(report: Any) -> List[Finding]:
    """An LSP diagnostics report's diagnostics as findings."""
    diagnostics = getattr(report, "diagnostics", []) or []
    return [
        Finding(source="lsp", severity=d.severity, line=d.line,
                message=d.message, check=d.code or d.source or "lsp",
                path=d.path)
        for d in diagnostics
    ]


def review_content_findings(content: str, path: Path | str) -> List[Finding]:
    """Review findings for *content* as if it were *path*.

    The before-state of an edit no longer exists on disk
    once the edit lands, so the before leg reviews a
    temporary twin carrying the same suffix; the reported
    path is the real file's, never the twin's.
    """
    target = Path(path)
    if target.suffix != ".py":
        return []
    with tempfile.NamedTemporaryFile(
            "w", suffix=".py", prefix=".mythic-truth-",
            dir=str(target.parent) if target.parent.exists() else None,
            delete=False, encoding="utf-8") as handle:
        handle.write(content)
        twin = Path(handle.name)
    try:
        issues = review_file(twin)
    finally:
        twin.unlink(missing_ok=True)
    findings = findings_from_review(issues)
    for finding in findings:
        finding.path = str(target)
    return findings


# ---------------------------------------------------------------------------
# The linter leg
# ---------------------------------------------------------------------------

def detect_linter(root: Path | str) -> Optional[Tuple[str, List[str]]]:
    """The project's linter, if one truly exists.

    A linter counts only when its binary is on ``PATH``
    *and* the project carries configuration naming it:
    its own config file at the root (``ruff.toml`` /
    ``.ruff.toml`` for ruff, ``.flake8`` for flake8), a
    ``[tool.<name>]`` section in ``pyproject.toml``, or a
    ``[flake8]`` section in ``setup.cfg`` / ``tox.ini``.
    A bare ``pyproject.toml`` with no linter section is
    not configuration. Nothing configured is ``None`` —
    reported, never invented.
    """
    base = Path(root)
    pyproject_text = ""
    pyproject = base / "pyproject.toml"
    if pyproject.exists():
        try:
            pyproject_text = pyproject.read_text(
                encoding="utf-8", errors="replace")
        except OSError:
            pyproject_text = ""
    ini_text = ""
    for ini_name in ("setup.cfg", "tox.ini", ".flake8"):
        ini = base / ini_name
        if ini.exists():
            try:
                ini_text += ini.read_text(
                    encoding="utf-8", errors="replace")
            except OSError:
                pass
    for binary, tail in _LINTERS:
        resolved = shutil.which(binary)
        if resolved is None:
            continue
        named = (base / f"{binary}.toml").exists() or \
            (base / f".{binary}.toml").exists() or \
            f"[tool.{binary}" in pyproject_text or \
            (binary == "flake8" and "[flake8]" in ini_text)
        if named:
            return binary, [resolved, *tail]
    return None


def run_linter(path: Path, root: Path, *,
               argv: Optional[List[str]] = None,
               timeout: float = 30.0) -> LegReport:
    """Run the linter leg on one file, honestly."""
    detected = detect_linter(root) if argv is None else ("custom", argv)
    if detected is None:
        return LegReport(
            name="linter", status="not-configured",
            note="no linter is configured for this project "
                 "(no ruff/flake8 binary with project config), "
                 "so no linter checked this file")
    name, command = detected
    try:
        result = subprocess.run(
            [*command, str(path)], cwd=str(root),
            capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return LegReport(
            name="linter", status="error",
            note=f"the {name} linter could not run: {exc}")
    findings: List[Finding] = []
    for line in (result.stdout or "").splitlines():
        finding = _parse_linter_line(line, str(path))
        if finding is not None:
            findings.append(finding)
    if result.returncode not in (0, 1):
        return LegReport(
            name="linter", status="error",
            note=f"the {name} linter exited {result.returncode}: "
                 f"{(result.stderr or '').strip()[:200]}",
            findings=findings)
    return LegReport(name="linter", status="ok", findings=findings)


def _parse_linter_line(line: str, path: str) -> Optional[Finding]:
    """One `path:line:col: CODE message` linter line, or None."""
    parts = line.split(":", 3)
    if len(parts) < 4:
        return None
    try:
        lineno = int(parts[1].strip())
    except ValueError:
        return None
    rest = parts[3].strip()
    code, _, message = rest.partition(" ")
    return Finding(
        source="linter", severity="error", line=lineno,
        message=message or rest, check=code or "lint", path=path)


# ---------------------------------------------------------------------------
# The diff — only new findings are charged to the edit
# ---------------------------------------------------------------------------

def diff_findings(before: Sequence[Finding],
                  after: Sequence[Finding]) -> Tuple[List[Finding], int, int]:
    """(new findings, resolved count, pre-existing count).

    Multiset diff on the line-blind key: an after-finding
    whose key still has an unmatched before-instance is
    pre-existing; the rest are new. Before-instances with
    no after twin were resolved by the edit.
    """
    remaining: Counter = Counter(f.key() for f in before)
    new: List[Finding] = []
    preexisting = 0
    for finding in after:
        key = finding.key()
        if remaining[key] > 0:
            remaining[key] -= 1
            preexisting += 1
        else:
            new.append(finding)
    resolved = sum(remaining.values())
    return new, resolved, preexisting


# ---------------------------------------------------------------------------
# The loop itself
# ---------------------------------------------------------------------------

DiagnosticsProvider = Callable[..., Any]
LinterRunner = Callable[..., LegReport]


def _legs(path: Path, root: Path, *,
          content: Optional[str],
          diagnostics_provider: Optional[DiagnosticsProvider],
          linter_runner: Optional[LinterRunner]) -> List[LegReport]:
    legs: List[LegReport] = []
    if content is None:
        review_findings = findings_from_review(review_file(path))
    else:
        review_findings = review_content_findings(content, path)
    legs.append(LegReport(name="review", status="ok",
                          findings=review_findings))
    provider = diagnostics_provider
    if provider is None:
        from ..integrations.lsp import diagnostics_for_file
        provider = diagnostics_for_file
    try:
        report = provider(path, root=root)
        legs.append(LegReport(
            name="lsp", status=getattr(report, "status", "ok"),
            note=getattr(report, "note", ""),
            findings=findings_from_diagnostics(report)))
    except Exception as exc:  # a dying server is a leg status, not a crash
        legs.append(LegReport(
            name="lsp", status="error",
            note=f"the language server check failed: {exc}"))
    runner = linter_runner or run_linter
    if content is None:
        legs.append(runner(path, root))
    else:
        # A before-content linter run would need the twin on
        # disk under its real name; the linter leg is an
        # after-only leg for content snapshots, stated plainly.
        legs.append(LegReport(
            name="linter", status="not-configured",
            note="the linter leg runs on the file on disk; "
                 "a content snapshot has no linter account"))
    return legs


def check_after_edit(path: Path | str, *,
                     before_content: Optional[str] = None,
                     root: Optional[Path | str] = None,
                     diagnostics_provider: Optional[DiagnosticsProvider] = None,
                     linter_runner: Optional[LinterRunner] = None
                     ) -> TruthReport:
    """One edit's truth: check *path* now, diffed to before.

    *before_content* is the file's text before the edit
    (``None`` for a newly created file, whose every finding
    is new; ``""`` is a real empty before-state). The LSP
    leg's before account cannot be re-asked after the edit
    — servers answer for the file as it stands — so the
    before diff rests on the review leg and any linter
    account of the after state, and the LSP findings are
    charged as new only when they are error severity and
    the review leg's before account had no error with the
    same message; this bound is stated, never hidden: it
    is why LSP warnings are reported on the standing
    account (:func:`check_file_now`) rather than charged.
    """
    target = Path(path)
    base = Path(root).resolve() if root is not None else target.resolve().parent
    if not target.is_absolute():
        target = base / target
    if before_content is None:
        before_legs: List[LegReport] = []
        before_findings: List[Finding] = []
    else:
        before_legs = _legs(target, base, content=before_content,
                            diagnostics_provider=diagnostics_provider,
                            linter_runner=linter_runner)
        before_findings = [
            f for leg in before_legs if leg.name == "review"
            for f in leg.findings]
    after_legs = _legs(target, base, content=None,
                       diagnostics_provider=diagnostics_provider,
                       linter_runner=linter_runner)
    after_review = [f for leg in after_legs if leg.name == "review"
                    for f in leg.findings]
    new, resolved, preexisting = diff_findings(before_findings, after_review)
    # LSP errors the edit introduced: an LSP error whose
    # message no before review error carried is charged;
    # the rest ride the standing account, not the charge sheet.
    before_messages = {f.message for f in before_findings
                       if f.severity == "error"}
    for leg in after_legs:
        if leg.name != "lsp" or leg.status != "ok":
            continue
        for finding in leg.findings:
            if finding.severity == "error" and \
                    finding.message not in before_messages:
                new.append(finding)
    # Linter findings are after-only (the before file is
    # gone); an error the review before-account already
    # carried by message is not charged twice.
    for leg in after_legs:
        if leg.name != "linter" or leg.status != "ok":
            continue
        for finding in leg.findings:
            if finding.message not in before_messages:
                new.append(finding)
    return TruthReport(
        path=str(target), legs_before=before_legs,
        legs_after=after_legs, new_findings=new,
        resolved_count=resolved, preexisting_count=preexisting)


def check_file_now(path: Path | str, *,
                   root: Optional[Path | str] = None,
                   diagnostics_provider: Optional[DiagnosticsProvider] = None,
                   linter_runner: Optional[LinterRunner] = None
                   ) -> TruthReport:
    """One file's standing account: every current error is 'new'.

    There is no edit to diff against, so the report's new
    findings are the file's current error-severity findings
    from every leg that truly ran.
    """
    target = Path(path)
    base = Path(root).resolve() if root is not None else target.resolve().parent
    if not target.is_absolute():
        target = base / target
    legs = _legs(target, base, content=None,
                 diagnostics_provider=diagnostics_provider,
                 linter_runner=linter_runner)
    current = [f for leg in legs for f in leg.findings
               if f.severity == "error"]
    return TruthReport(
        path=str(target), legs_before=[], legs_after=legs,
        new_findings=current, resolved_count=0, preexisting_count=0)


def enabled_from_config(config: Optional[Dict[str, Any]]) -> bool:
    """The loop is on unless the config says ``edit_truth_loop: false``."""
    if not config:
        return True
    return config.get("edit_truth_loop", True) is not False


def truth_note_for_edit(path: Path | str, before_content: Optional[str], *,
                        root: Optional[Path | str] = None) -> str:
    """The tool-result note for one edit: '' when clean.

    Non-empty only when the edit introduced new
    error-severity findings. A loop failure is a note,
    never a failed edit.
    """
    try:
        report = check_after_edit(path, before_content=before_content,
                                  root=root)
    except Exception as exc:
        return (f"\nEdit-time truth check could not run: {exc}. "
                f"The edit itself stands; check the file before "
                f"the turn ends.")
    if not report.has_new_errors:
        return ""
    return "\n" + format_truth_note(report)


# ---------------------------------------------------------------------------
# Surfaces: parser, formatters, markdown
# ---------------------------------------------------------------------------

def parse_truth_args(arguments: str) -> Dict[str, Any]:
    """Parse ``/truth`` arguments: exactly one path."""
    parts = (arguments or "").split()
    if len(parts) != 1:
        raise ValueError(USAGE)
    return {"action": "check", "path": parts[0]}


def format_truth_note(report: TruthReport) -> str:
    """The compact in-turn note: new errors as facts."""
    lines = [
        f"Edit-time truth: this edit introduced "
        f"{len(report.new_errors)} new error(s) in {report.path} — "
        f"fix them before the turn ends:",
    ]
    lines.extend(f"  {f.one_line()}" for f in report.new_errors)
    for leg in report.legs_after:
        if leg.status != "ok":
            lines.append(f"  ({leg.name}: {leg.status} — {leg.note})")
    return "\n".join(lines)


def format_truth_report(status: Dict[str, Any]) -> str:
    """Render an ``Agent.edit_truth`` status dict."""
    report = status.get("report") or {}
    lines = [f"Truth for {report.get('path', '')}:"]
    for leg in report.get("legs_after", []):
        if leg["status"] == "ok":
            lines.append(
                f"  {leg['name']}: ran — {len(leg['findings'])} finding(s)")
        else:
            lines.append(f"  {leg['name']}: {leg['status']} — {leg['note']}")
    errors = report.get("new_errors", [])
    if errors:
        lines.append(f"Current errors ({len(errors)}):")
        for item in errors:
            finding = Finding(**{k: item[k] for k in
                                 ("source", "severity", "line", "message",
                                  "check", "path")})
            lines.append(f"  {finding.one_line()}")
    else:
        lines.append("Current errors: none from the legs that ran.")
    lines.append(status.get("plain_explanation", ""))
    return "\n".join(lines)


def render_markdown() -> str:
    """The slice's plain account, as markdown."""
    return (
        f"# Edit-time truth loop ({EDIT_TRUTH_SLICE})\n\n"
        f"{PLAIN_EXPLANATION}\n\n"
        f"{USAGE}\n"
    )
