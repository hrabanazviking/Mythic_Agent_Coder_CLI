"""Coverage sight (M-057).

Part III — Code Intelligence. Line coverage overlaid on
edited files, and a change landing with zero covering
tests flagged to the Auditor.

What ships here, in ``mythic_agent/tools/coverage_sight.py``:

* **Coverage data is coverage.py's own, never estimated.**
  :func:`load_coverage` reads the data a real coverage.py
  run left behind: its JSON report (``coverage.json``,
  the ``coverage json`` output) when one is present at the
  project root, else its data file (``.coverage``) read
  through the coverage API itself. Both sources give, per
  file, exactly the lines coverage.py measured as executed
  and missed. No source present is an honest ``no-data``
  report naming the remedy (run the tests under coverage);
  a malformed report is ``failed`` with its reason; no
  overlay is ever invented from file contents or guesses.
* **The overlay.** :func:`overlay_report` lays that data
  over the files an edit touched: per file, the executable
  lines, how many ran, the missed line numbers, and the
  percentage — each number coverage.py's, recomputed only
  by counting its executed/missed lists. A touched file
  the data does not know is ``not-in-coverage``; a touched
  file that is not there is ``not-found``. When the caller
  names the exact edited lines, the overlay also reports
  those lines' own account.
* **Zero cover is flagged to the Auditor.** A touched
  file is zero-cover when coverage data exists for it,
  it has executable lines, and none of them ran — no
  test (indeed nothing under coverage) covered it — or
  when named edited lines include executable lines and
  none of those ran. :func:`flag_zero_cover` writes each
  such flag to the house audit log
  (:class:`mythic_agent.core.audit.AuditLog`, action
  ``coverage.zero_cover``), the append-only record the
  Auditor reads; :func:`coverage_check` — the surface's
  check road — writes the flags as part of checking, and
  reports how many it wrote. Flagging never edits code
  and never blocks a change; it makes the absence visible
  to the Auditor, which is the roadmap's words.
* **The surfaces.** ``Agent.coverage_status()`` /
  ``Agent.coverage_check()`` and ``/coverage`` on the
  terminal and TUI system-command roads (bare or ``show``
  for the board, ``check <file> ...`` for an overlay),
  sharing this module's parser and formatters. The
  setting ``coverage_sight`` (on by default) closes the
  road plainly when the user says so.

Honesty rules, pinned by the slice's tests:

* **Only measured lines.** Executed and missed lines
  come from coverage.py's data alone; a percentage is a
  count of those lines, never a model of the file.
* **Absence is named, not zero.** No coverage data for
  a project is ``no-data`` and a file missing from the
  data is ``not-in-coverage`` — neither is reported as
  0% covered, and neither raises a zero-cover flag,
  because nothing was measured.
* **A flag needs a measurement.** Zero cover is claimed
  only where data exists and shows executable lines
  that never ran.
"""

from __future__ import annotations

__all__ = [
    "COVERAGE_SLICE",
    "PLAIN_EXPLANATION",
    "USAGE",
    "ZERO_COVER_ACTION",
    "CoverageData",
    "FileCoverage",
    "FileOverlay",
    "OverlayReport",
    "board_report",
    "coverage_check",
    "default_json_names",
    "enabled_from_config",
    "find_coverage_source",
    "flag_zero_cover",
    "format_coverage_board",
    "format_coverage_overlay",
    "load_coverage",
    "parse_coverage_args",
    "render_markdown",
]

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from ..core.audit import AuditLog

COVERAGE_SLICE = "M-057"

#: The audit-log action a zero-cover flag is written under.
ZERO_COVER_ACTION = "coverage.zero_cover"

PLAIN_EXPLANATION = (
    "Coverage sight lays a real coverage run's own "
    "numbers over the files a change touched: /coverage "
    "shows whether this project has coverage data at all "
    "and what it totals, and /coverage check <file> ... "
    "shows, per file, which lines coverage.py measured "
    "as run and which it measured as missed. A touched "
    "file whose measured lines never ran at all is "
    "flagged to the Auditor in the audit log. No data "
    "says so plainly — coverage is never estimated."
)

USAGE = ("Usage: /coverage [show] | "
         "/coverage check <file> [<file> ...]")

#: coverage.py JSON report names looked for at the root,
#: in order: the conventional `coverage json` outputs.
_JSON_NAMES = ("coverage.json", ".coverage.json")


def enabled_from_config(config: Optional[Dict[str, Any]]) -> bool:
    """Coverage sight is on unless config says so."""
    if not config:
        return True
    return config.get("coverage_sight", True) is not False


def default_json_names() -> List[str]:
    """The JSON report filenames searched at a project root."""
    return list(_JSON_NAMES)


# ---------------------------------------------------------------------------
# Coverage data, from coverage.py's own output
# ---------------------------------------------------------------------------

@dataclass
class FileCoverage:
    """One file's measured lines, exactly as coverage.py left them."""

    path: str = ""
    executed: List[int] = field(default_factory=list)
    missing: List[int] = field(default_factory=list)

    @property
    def statements(self) -> List[int]:
        return sorted(set(self.executed) | set(self.missing))

    @property
    def percent(self) -> float:
        total = len(self.statements)
        if not total:
            return 100.0
        return 100.0 * len(set(self.executed)) / total

    def record(self) -> Dict[str, Any]:
        return {"path": self.path,
                "executed": list(self.executed),
                "missing": list(self.missing),
                "statements": len(self.statements),
                "percent": round(self.percent, 2)}


@dataclass
class CoverageData:
    """A whole coverage data source's account for one project."""

    root: str = ""
    status: str = "no-data"  # ok | no-data | failed | disabled
    source: str = ""
    source_kind: str = ""  # json | data-file | ""
    files: Dict[str, FileCoverage] = field(default_factory=dict)
    note: str = ""

    @property
    def percent(self) -> float:
        executed = sum(len(set(f.executed)) for f in self.files.values())
        total = sum(len(f.statements) for f in self.files.values())
        if not total:
            return 0.0
        return 100.0 * executed / total

    def record(self) -> Dict[str, Any]:
        return {"root": self.root, "status": self.status,
                "source": self.source, "source_kind": self.source_kind,
                "files": {name: f.record()
                          for name, f in sorted(self.files.items())},
                "file_count": len(self.files),
                "percent": round(self.percent, 2),
                "note": self.note}


def _rel_key(name: str, base: Path) -> str:
    """A coverage file key as a root-relative posix path."""
    raw = Path(name)
    if raw.is_absolute():
        try:
            return raw.resolve().relative_to(base).as_posix()
        except ValueError:
            return raw.as_posix()
    return raw.as_posix()


def find_coverage_source(root: Optional[Path | str] = None
                         ) -> Optional[Path]:
    """The coverage data source at a project root, if any.

    A JSON report is preferred (it is the portable,
    readable form); the ``.coverage`` data file is the
    fallback. ``None`` means no coverage run has left
    data here — an honest absence, not a measurement.
    """
    base = Path(root).resolve() if root is not None else Path.cwd()
    for name in _JSON_NAMES:
        candidate = base / name
        if candidate.is_file():
            return candidate
    data_file = base / ".coverage"
    if data_file.is_file():
        return data_file
    return None


def _load_json(source: Path, base: Path, data: CoverageData) -> None:
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        data.status = "failed"
        data.note = (f"the coverage report {source.name} could "
                     f"not be read as coverage JSON: {exc} — no "
                     f"overlay was invented")
        return
    files = payload.get("files") if isinstance(payload, dict) else None
    if not isinstance(files, dict):
        data.status = "failed"
        data.note = (f"the coverage report {source.name} has no "
                     f"'files' account — it is not a coverage.py "
                     f"JSON report, and no overlay was invented")
        return
    for name, entry in files.items():
        if not isinstance(entry, dict):
            continue
        executed = sorted({int(n) for n in entry.get("executed_lines") or []
                           if isinstance(n, int) or str(n).isdigit()})
        missing = sorted({int(n) for n in entry.get("missing_lines") or []
                          if isinstance(n, int) or str(n).isdigit()})
        key = _rel_key(str(name), base)
        data.files[key] = FileCoverage(
            path=key, executed=executed, missing=missing)
    data.status = "ok"
    data.source_kind = "json"
    data.note = (f"coverage.py JSON report {source.name}: "
                 f"{len(data.files)} file(s) measured")


def _load_data_file(source: Path, base: Path, data: CoverageData) -> None:
    try:
        from coverage import Coverage
    except ImportError:
        data.status = "failed"
        data.note = ("a .coverage data file is present but the "
                     "coverage package is not installed to read "
                     "it — install coverage, or write its JSON "
                     "report (`coverage json`); no overlay "
                     "was invented")
        return
    try:
        cov = Coverage(data_file=str(source))
        cov.load()
        measured = cov.get_data()
        for filename in measured.measured_files():
            executed = sorted(measured.lines(filename) or [])
            _fname, statements, _excluded, missing, _fmt = \
                cov.analysis2(filename)
            key = _rel_key(filename, base)
            data.files[key] = FileCoverage(
                path=key, executed=executed,
                missing=sorted(missing))
    except Exception as exc:  # coverage raises its own error family
        data.status = "failed"
        data.files = {}
        data.note = (f"the .coverage data file could not be "
                     f"read by coverage itself: {exc} — no "
                     f"overlay was invented")
        return
    data.status = "ok"
    data.source_kind = "data-file"
    data.note = (f"coverage.py data file .coverage: "
                 f"{len(data.files)} file(s) measured")


def load_coverage(root: Optional[Path | str] = None, *,
                  source: Optional[Path | str] = None,
                  enabled: bool = True) -> CoverageData:
    """Load a project's coverage data from coverage.py's output.

    *source* names one report/data file explicitly; without
    it, :func:`find_coverage_source` searches the root.
    Every absence is its own honest status — see the
    module docstring.
    """
    base = Path(root).resolve() if root is not None else Path.cwd()
    data = CoverageData(root=str(base))
    if not enabled:
        data.status = "disabled"
        data.note = ("coverage sight is off, so no coverage "
                     "data was read")
        return data
    if not base.is_dir():
        data.status = "no-data"
        data.note = f"the project root {base} is not there"
        return data
    chosen = Path(source) if source is not None else \
        find_coverage_source(base)
    if chosen is None:
        data.status = "no-data"
        data.note = ("no coverage data here yet — run the tests "
                     "under coverage first (`coverage run -m "
                     "pytest`, then `coverage json`); nothing "
                     "was estimated in its place")
        return data
    if not chosen.is_file():
        data.status = "no-data"
        data.note = f"the named coverage source {chosen} is not there"
        return data
    data.source = str(chosen)
    if chosen.name in _JSON_NAMES or chosen.suffix == ".json":
        _load_json(chosen, base, data)
    else:
        _load_data_file(chosen, base, data)
    return data


# ---------------------------------------------------------------------------
# The overlay on edited files
# ---------------------------------------------------------------------------

@dataclass
class FileOverlay:
    """Coverage laid over one touched file."""

    path: str = ""
    status: str = "no-data"  # ok | no-data | not-in-coverage | not-found
    statements: int = 0
    covered: int = 0
    missed_lines: List[int] = field(default_factory=list)
    percent: float = 0.0
    zero_cover: bool = False
    edited_executable: List[int] = field(default_factory=list)
    edited_covered: List[int] = field(default_factory=list)
    note: str = ""

    def record(self) -> Dict[str, Any]:
        return {"path": self.path, "status": self.status,
                "statements": self.statements,
                "covered": self.covered,
                "missed_lines": list(self.missed_lines),
                "percent": round(self.percent, 2),
                "zero_cover": self.zero_cover,
                "edited_executable": list(self.edited_executable),
                "edited_covered": list(self.edited_covered),
                "note": self.note}


@dataclass
class OverlayReport:
    """The overlay over every file a change touched."""

    root: str = ""
    status: str = "ok"  # ok | no-data | failed | disabled
    source: str = ""
    files: List[FileOverlay] = field(default_factory=list)
    flags: List[Dict[str, Any]] = field(default_factory=list)
    flags_written: int = 0
    note: str = ""

    @property
    def zero_cover_files(self) -> List[str]:
        return [f.path for f in self.files if f.zero_cover]

    def record(self) -> Dict[str, Any]:
        return {"root": self.root, "status": self.status,
                "source": self.source,
                "files": [f.record() for f in self.files],
                "zero_cover_files": self.zero_cover_files,
                "flags": list(self.flags),
                "flags_written": self.flags_written,
                "note": self.note}


def _overlay_one(rel: str, target: Path, base: Path,
                 data: CoverageData,
                 edited: Optional[Sequence[int]]) -> FileOverlay:
    overlay = FileOverlay(path=rel)
    if data.status != "ok":
        overlay.status = "no-data"
        overlay.note = ("no coverage data to lay over this "
                        "file — see the board for why")
        return overlay
    if not target.is_file():
        overlay.status = "not-found"
        overlay.note = "the touched file is not there"
        return overlay
    measured = data.files.get(rel)
    if measured is None:
        overlay.status = "not-in-coverage"
        overlay.note = ("coverage data exists, but this file "
                        "is not in it — it was not measured, "
                        "which is not the same as 0%")
        return overlay
    overlay.status = "ok"
    overlay.statements = len(measured.statements)
    overlay.covered = len(set(measured.executed))
    overlay.missed_lines = list(measured.missing)
    overlay.percent = measured.percent
    if edited:
        statements = set(measured.statements)
        executed = set(measured.executed)
        overlay.edited_executable = sorted(
            {int(n) for n in edited} & statements)
        overlay.edited_covered = sorted(
            set(overlay.edited_executable) & executed)
    if overlay.statements and overlay.covered == 0:
        overlay.zero_cover = True
        overlay.note = ("zero cover: none of this file's "
                        f"{overlay.statements} measured line(s) "
                        "ran under coverage — flagged to the "
                        "Auditor")
    elif overlay.edited_executable and not overlay.edited_covered:
        overlay.zero_cover = True
        overlay.note = ("zero cover on the edited lines: "
                        f"{len(overlay.edited_executable)} edited "
                        "line(s) are executable and none of them "
                        "ran under coverage — flagged to the "
                        "Auditor")
    elif overlay.statements:
        overlay.note = (f"{overlay.covered} of "
                        f"{overlay.statements} measured line(s) ran")
    else:
        overlay.note = ("the file has no executable lines in "
                        "the coverage data")
    return overlay


def overlay_report(changed_files: List[str], *,
                   root: Optional[Path | str] = None,
                   edited_lines: Optional[Dict[str, Sequence[int]]] = None,
                   enabled: bool = True,
                   data: Optional[CoverageData] = None
                   ) -> OverlayReport:
    """Lay coverage over the files a change touched.

    Pure reading: this function writes no flags. The
    flag-writing road is :func:`coverage_check`.
    """
    base = Path(root).resolve() if root is not None else Path.cwd()
    changed = [str(c) for c in (changed_files or []) if str(c).strip()]
    report = OverlayReport(root=str(base))
    cov = data if data is not None else load_coverage(
        base, enabled=enabled)
    report.source = cov.source
    if cov.status == "disabled":
        report.status = "disabled"
        report.note = cov.note
        return report
    if cov.status != "ok":
        report.status = cov.status
        report.note = cov.note
    else:
        report.note = cov.note
    edited_map = {str(k): list(v) for k, v in (edited_lines or {}).items()}
    for item in changed:
        raw = Path(item)
        target = raw if raw.is_absolute() else base / raw
        try:
            rel = target.resolve().relative_to(base).as_posix()
        except ValueError:
            rel = raw.as_posix()
        edited = edited_map.get(item) or edited_map.get(rel)
        report.files.append(_overlay_one(rel, target, base, cov, edited))
    report.flags = [
        {"file": f.path, "action": ZERO_COVER_ACTION,
         "statements": f.statements, "covered": f.covered,
         "note": f.note}
        for f in report.files if f.zero_cover]
    return report


def flag_zero_cover(report: OverlayReport, *,
                    root: Optional[Path | str] = None,
                    actor: str = "coverage_sight") -> int:
    """Write an overlay's zero-cover flags to the audit log.

    One append-only :class:`AuditLog` entry per zero-cover
    file, action ``coverage.zero_cover`` — the record the
    Auditor reads. Returns how many flags were written.
    A report with no zero-cover files writes none.
    """
    base = Path(root).resolve() if root is not None else \
        Path(report.root or ".")
    log = AuditLog(base)
    written = 0
    for overlay in report.files:
        if not overlay.zero_cover:
            continue
        log.log(ZERO_COVER_ACTION, actor, {
            "file": overlay.path,
            "statements": overlay.statements,
            "covered": overlay.covered,
            "percent": round(overlay.percent, 2),
            "edited_executable": list(overlay.edited_executable),
            "reason": overlay.note,
            "slice": COVERAGE_SLICE,
        })
        written += 1
    return written


def coverage_check(changed_files: List[str], *,
                   root: Optional[Path | str] = None,
                   edited_lines: Optional[Dict[str, Sequence[int]]] = None,
                   enabled: bool = True) -> OverlayReport:
    """The check road: overlay + zero-cover flags to the Auditor."""
    report = overlay_report(
        changed_files, root=root, edited_lines=edited_lines,
        enabled=enabled)
    if report.status == "ok" and report.zero_cover_files:
        report.flags_written = flag_zero_cover(report, root=root)
    return report


# ---------------------------------------------------------------------------
# Board + surfaces
# ---------------------------------------------------------------------------

def board_report(root: Optional[Path | str] = None, *,
                 enabled: bool = True) -> Dict[str, Any]:
    """The /coverage board: does data exist, and what does it total?"""
    base = Path(root).resolve() if root is not None else Path.cwd()
    cov = load_coverage(base, enabled=enabled)
    return {"coverage": cov.record(),
            "plain_explanation": PLAIN_EXPLANATION}


def parse_coverage_args(arguments: str) -> Dict[str, Any]:
    """Parse ``/coverage`` arguments: board, or check <file> ..."""
    text = (arguments or "").strip()
    if not text or text == "show":
        return {"action": "show"}
    tokens = text.split()
    if tokens[0] == "show":
        raise ValueError(f"{USAGE} — show takes no further words")
    if tokens[0] == "check":
        if len(tokens) < 2:
            raise ValueError(
                f"{USAGE} — check needs at least one file")
        return {"action": "check", "changed": tokens[1:]}
    raise ValueError(f"{USAGE} — unexpected word {tokens[0]!r}")


def format_coverage_board(status: Dict[str, Any]) -> str:
    """The board: the data source's standing and totals."""
    cov = status["coverage"]
    lines = [PLAIN_EXPLANATION, "",
             f"Coverage data: {cov['status']} — {cov['note']}"]
    if cov["status"] == "ok":
        lines.append(
            f"  {cov['file_count']} file(s), {cov['percent']:.1f}% "
            f"of measured lines ran (source: {cov['source']})")
        for name, entry in list(cov["files"].items())[:50]:
            lines.append(
                f"  {name}: {entry['percent']:.1f}% "
                f"({entry['statements']} measured line(s), "
                f"{len(entry['missing'])} missed)")
    return "\n".join(lines)


def format_coverage_overlay(status: Dict[str, Any]) -> str:
    """One check's account: per-file overlay + flags written."""
    report = status["report"]
    lines = [f"Coverage over {len(report['files'])} touched file(s) "
             f"({report['status']}):"]
    for entry in report["files"]:
        if entry["status"] != "ok":
            lines.append(
                f"  {entry['path']}: {entry['status']} — "
                f"{entry['note']}")
            continue
        lines.append(
            f"  {entry['path']}: {entry['percent']:.1f}% — "
            f"{entry['covered']} of {entry['statements']} "
            f"measured line(s) ran; missed: "
            f"{entry['missed_lines'] or 'none'}")
        if entry["zero_cover"]:
            lines.append(f"    ZERO COVER — {entry['note']}")
    if report["flags_written"]:
        lines.append(
            f"  {report['flags_written']} zero-cover flag(s) "
            f"written to the audit log for the Auditor "
            f"({ZERO_COVER_ACTION})")
    elif report["zero_cover_files"]:
        lines.append(
            "  zero-cover file(s) present; no flags written "
            "on this road")
    return "\n".join(lines)


def render_markdown() -> str:
    """The slice's plain account, as markdown."""
    return (
        f"# Coverage sight ({COVERAGE_SLICE})\n\n"
        f"{PLAIN_EXPLANATION}\n\n"
        f"The data source is coverage.py's own output: its "
        f"JSON report ({' or '.join(default_json_names())}) "
        f"when present, else its `.coverage` data file read "
        f"through the coverage API. The overlay counts only "
        f"the executed and missed lines that data names. A "
        f"touched file with measured lines that never ran "
        f"is zero-cover, and the check road writes one "
        f"`{ZERO_COVER_ACTION}` flag per such file to the "
        f"append-only audit log the Auditor reads.\n\n"
        f"{USAGE}\n"
    )
