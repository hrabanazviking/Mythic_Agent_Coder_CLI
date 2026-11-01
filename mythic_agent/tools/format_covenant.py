"""Formatter covenant (M-053).

Part III — Code Intelligence. The project's own formatter
config is honoured exactly; the coder never reformats
untouched code; format diffs are separated from logic
diffs in review.

What ships here, in
``mythic_agent/tools/format_covenant.py``:

* **Discovery with M-052's honesty.** A formatter counts
  only when its binary is on ``PATH`` *and* the project
  itself names it: a ``[tool.<name>]`` section in
  ``pyproject.toml``, its own config file at the project
  root (``ruff.toml`` / ``.ruff.toml`` for ruff,
  ``.isort.cfg`` for isort, ``.style.yapf`` for yapf), or
  its section in ``setup.cfg`` / ``tox.ini``. Candidates
  in preference order: black, ruff (``ruff format``),
  isort, yapf. Where no formatter is configured the
  report says ``not-configured`` and nothing is
  formatted; where one is configured but its binary is
  absent the report says ``not-installed`` — never an
  invented house style.
* **Touched code only.** The formatter runs only on
  files the caller names as touched by the edit. A file
  outside the touched set is refused plainly
  (``not-touched``), never reformatted. On the
  ``/format`` surface road the file the user names is
  itself the touched file — the user's own act names it.
* **Preview never writes.** The formatter runs in
  stdin/stdout mode (``black -``, ``ruff format -``,
  ``isort -``, ``yapf``), so a preview changes nothing
  on disk. Its output is the would-be content, carried
  as data.
* **Diffs separated as data.** The report carries two
  unified diffs: the *logic* diff (content before the
  edit -> content as edited) and the *format* diff
  (content as edited -> the formatter's output), each
  with its changed-line count, so review can show
  format changes apart from logic changes.
* **Application is explicit and journaled.** Only an
  explicit apply writes, only through the house
  :class:`EditJournal` (journal-first), only for a
  touched file, and only when the file still matches
  the previewed content — a file changed since the
  preview is refused whole (``refused-stale``).
* **The switch.** The setting ``formatter_covenant``
  (on by default) turns the covenant road off when the
  user says so; while off, preview and apply refuse
  plainly (``disabled``).

The surfaces: ``Agent.format_covenant(path, ...)``
checks one touched file (preview by default), and
``/format <path> [apply]`` rides the terminal and the
TUI system-command roads, sharing this module's parser
and formatter.

Honesty rules, pinned by the slice's tests:

* **Absence is never a style.** No configured formatter
  means no formatting, stated plainly.
* **Untouched code is never reformatted.** The touched
  set is the whole permission; there is no other road.
* **A preview writes nothing.** Only an explicit,
  journaled apply on an unchanged, touched file writes.
"""

from __future__ import annotations

__all__ = [
    "FORMAT_COVENANT_SLICE",
    "PLAIN_EXPLANATION",
    "USAGE",
    "FormatReport",
    "FormatterSpec",
    "apply_format",
    "discover_formatter",
    "enabled_from_config",
    "format_covenant_report",
    "format_format_report",
    "formatter_names",
    "parse_format_args",
    "preview_format",
    "render_markdown",
    "run_formatter",
    "separate_diffs",
]

import difflib
import hashlib
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from ..core.edits import EditJournal

FORMAT_COVENANT_SLICE = "M-053"

PLAIN_EXPLANATION = (
    "The project's own formatter — the one its config "
    "files name — may reformat only the code an edit "
    "touched, never anything else. /format <path> shows "
    "what that formatter would change in one touched "
    "file, with the format changes shown separately "
    "from the edit's own changes; /format <path> apply "
    "writes them through the edit journal. A project "
    "with no formatter configured is told so plainly "
    "and nothing is reformatted in a made-up style."
)

USAGE = "Usage: /format <path> [apply]"


@dataclass(frozen=True)
class FormatterSpec:
    """One formatter the project truly configured."""

    name: str = ""            # black | ruff | isort | yapf
    binary: str = ""          # resolved path, "" when absent
    argv_tail: Tuple[str, ...] = ()
    config_source: str = ""   # where the project names it

    @property
    def installed(self) -> bool:
        return bool(self.binary)

    def argv(self) -> List[str]:
        return [self.binary, *self.argv_tail]

    def record(self) -> Dict[str, Any]:
        return {
            "name": self.name, "binary": self.binary,
            "argv_tail": list(self.argv_tail),
            "config_source": self.config_source,
            "installed": self.installed,
        }


#: Candidates in preference order: (name, argv tail after
#: the binary, own config files at the root, ini sections).
_CANDIDATES: Tuple[Tuple[str, Tuple[str, ...],
                         Tuple[str, ...], Tuple[str, ...]], ...] = (
    ("black", ("-",), (), ()),
    ("ruff", ("format", "-"), ("ruff.toml", ".ruff.toml"), ()),
    ("isort", ("-",), (".isort.cfg",), ("isort",)),
    ("yapf", (), (".style.yapf",), ("yapf",)),
)


def formatter_names() -> Tuple[str, ...]:
    """The candidate formatter names, in preference order."""
    return tuple(name for name, _tail, _files, _ini in _CANDIDATES)


def _project_names_formatter(root: Path, name: str,
                             own_files: Sequence[str],
                             ini_sections: Sequence[str]) -> str:
    """Where *root* names formatter *name*, or ""."""
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        try:
            text = pyproject.read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
        if f"[tool.{name}]" in text or f"[tool.{name}." in text:
            return "pyproject.toml"
        if name == "ruff" and "[tool.ruff" in text:
            return "pyproject.toml"
    for filename in own_files:
        if (root / filename).exists():
            return filename
    for ini_name in ("setup.cfg", "tox.ini"):
        ini = root / ini_name
        if not ini.exists():
            continue
        try:
            ini_text = ini.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for section in ini_sections:
            if f"[{section}]" in ini_text:
                return ini_name
    return ""


def discover_formatter(root: Path | str) -> Optional[FormatterSpec]:
    """The project's formatter, exactly as it declares it.

    The first candidate (in preference order) the project
    names wins. Its binary is resolved on ``PATH``; a
    configured formatter with no binary still returns a
    spec (``installed`` is False) so callers can say
    ``not-installed`` honestly instead of falling through
    to a formatter the project never chose. ``None``
    means the project names no formatter at all.
    """
    base = Path(root)
    for name, tail, own_files, ini_sections in _CANDIDATES:
        source = _project_names_formatter(base, name, own_files, ini_sections)
        if not source:
            continue
        resolved = shutil.which(name)
        return FormatterSpec(
            name=name, binary=resolved or "",
            argv_tail=tail, config_source=source)
    return None


FormatterRunner = Callable[[FormatterSpec, str], str]


def run_formatter(spec: FormatterSpec, content: str, *,
                  timeout: float = 30.0) -> str:
    """Run *spec*'s formatter on *content* via stdin.

    Returns the formatted text. Raises ``RuntimeError``
    with the formatter's own words when it fails — a
    formatter's refusal is a fact, never swallowed.
    """
    try:
        result = subprocess.run(
            spec.argv(), input=content, capture_output=True,
            text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"the {spec.name} formatter could not run: {exc}")
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()[:300]
        raise RuntimeError(
            f"the {spec.name} formatter refused the file "
            f"(exit {result.returncode}): {detail}")
    return result.stdout


def _unified(before: str, after: str, label: str) -> Tuple[str, int]:
    """One unified diff and its changed-line count."""
    if before == after:
        return "", 0
    lines = list(difflib.unified_diff(
        before.splitlines(), after.splitlines(),
        fromfile=f"{label}/before", tofile=f"{label}/after",
        lineterm=""))
    changed = sum(1 for line in lines
                  if line[:1] in ("+", "-")
                  and not line.startswith(("+++", "---")))
    return "\n".join(lines), changed


def separate_diffs(before_content: str, edited_content: str,
                   formatted_content: str) -> Dict[str, Any]:
    """Logic and format diffs, separated as data.

    The logic diff is the edit itself (before -> edited);
    the format diff is only what the formatter would add
    on top (edited -> formatted). Either may be empty.
    """
    logic_diff, logic_lines = _unified(before_content, edited_content, "logic")
    format_diff, format_lines = _unified(edited_content, formatted_content,
                                         "format")
    return {
        "logic_diff": logic_diff, "logic_changed_lines": logic_lines,
        "format_diff": format_diff, "format_changed_lines": format_lines,
    }


@dataclass
class FormatReport:
    """One touched file's formatter-covenant account."""

    path: str = ""
    status: str = ""          # ok | not-configured | not-installed |
                              # not-touched | disabled | refused-stale |
                              # error | applied
    note: str = ""
    formatter: Optional[FormatterSpec] = None
    would_change: bool = False
    formatted_content: str = ""
    content_sha256: str = ""  # the previewed on-disk content
    logic_diff: str = ""
    logic_changed_lines: int = 0
    format_diff: str = ""
    format_changed_lines: int = 0
    applied: bool = False

    def record(self) -> Dict[str, Any]:
        return {
            "path": self.path, "status": self.status,
            "note": self.note,
            "formatter": self.formatter.record() if self.formatter else None,
            "would_change": self.would_change,
            "formatted_content": self.formatted_content,
            "content_sha256": self.content_sha256,
            "logic_diff": self.logic_diff,
            "logic_changed_lines": self.logic_changed_lines,
            "format_diff": self.format_diff,
            "format_changed_lines": self.format_changed_lines,
            "applied": self.applied,
        }


def _touched_contains(touched: Sequence[Path | str],
                      target: Path) -> bool:
    wanted = target.resolve()
    for entry in touched:
        candidate = Path(entry)
        if not candidate.is_absolute():
            candidate = target.parent / candidate
        try:
            if candidate.resolve() == wanted:
                return True
        except OSError:
            continue
    return False


def preview_format(path: Path | str, *,
                   root: Optional[Path | str] = None,
                   touched: Sequence[Path | str] = (),
                   before_content: Optional[str] = None,
                   runner: Optional[FormatterRunner] = None,
                   enabled: bool = True) -> FormatReport:
    """What the project's formatter would do to one file.

    *touched* is the permission: the files the edit
    touched. *before_content* is the file's text before
    the edit (for the logic diff); it defaults to the
    current content, which makes the logic diff empty —
    the standing account of a file the user names.
    Nothing is written, whatever the outcome.
    """
    target = Path(path)
    base = Path(root).resolve() if root is not None else target.resolve().parent
    if not target.is_absolute():
        target = base / target
    report = FormatReport(path=str(target))
    if not enabled:
        report.status = "disabled"
        report.note = ("the formatter covenant is off "
                       "(formatter_covenant: false), so no "
                       "formatter was run")
        return report
    if not _touched_contains(touched, target):
        report.status = "not-touched"
        report.note = ("this file was not touched by the edit, "
                       "and the covenant never reformats "
                       "untouched code")
        return report
    spec = discover_formatter(base)
    if spec is None:
        report.status = "not-configured"
        report.note = ("this project names no formatter "
                       "(no black/ruff/isort/yapf configuration), "
                       "so nothing was formatted and no style "
                       "was invented")
        return report
    report.formatter = spec
    if not spec.installed:
        report.status = "not-installed"
        report.note = (f"the project configures {spec.name} "
                       f"({spec.config_source}) but no {spec.name} "
                       f"binary is on PATH, so nothing was formatted")
        return report
    try:
        current = target.read_text(encoding="utf-8")
    except OSError as exc:
        report.status = "error"
        report.note = f"the file could not be read: {exc}"
        return report
    report.content_sha256 = hashlib.sha256(
        current.encode("utf-8")).hexdigest()
    run = runner or run_formatter
    try:
        formatted = run(spec, current)
    except RuntimeError as exc:
        report.status = "error"
        report.note = str(exc)
        return report
    before = current if before_content is None else before_content
    diffs = separate_diffs(before, current, formatted)
    report.logic_diff = diffs["logic_diff"]
    report.logic_changed_lines = diffs["logic_changed_lines"]
    report.format_diff = diffs["format_diff"]
    report.format_changed_lines = diffs["format_changed_lines"]
    report.formatted_content = formatted
    report.would_change = formatted != current
    report.status = "ok"
    report.note = (f"{spec.name} (configured in {spec.config_source}) "
                   f"would change {report.format_changed_lines} line(s)"
                   if report.would_change else
                   f"{spec.name} (configured in {spec.config_source}) "
                   f"would change nothing")
    return report


def apply_format(report: FormatReport, *,
                 root: Optional[Path | str] = None,
                 journal: Optional[EditJournal] = None) -> FormatReport:
    """Write a preview's formatted content, journal-first.

    Only a preview with status ``ok`` that would change
    something may be applied, and only while the file
    still matches the previewed content — a file changed
    since the preview is refused whole. The write goes
    through the house :class:`EditJournal`, never around
    it. Mutates and returns *report*.
    """
    if report.status != "ok" or not report.would_change:
        if report.status == "ok":
            report.note = "nothing to apply: the formatter would change nothing"
        return report
    target = Path(report.path)
    base = Path(root).resolve() if root is not None else target.resolve().parent
    try:
        current = target.read_text(encoding="utf-8")
    except OSError as exc:
        report.status = "error"
        report.note = f"the file could not be re-read for applying: {exc}"
        return report
    if hashlib.sha256(current.encode("utf-8")).hexdigest() != report.content_sha256:
        report.status = "refused-stale"
        report.note = ("the file changed since the preview, so "
                       "nothing was written; preview it again "
                       "to see the formatter's current account")
        return report
    writer = journal or EditJournal(base)
    relative = str(target.relative_to(base)) if target.is_relative_to(base) \
        else str(target)
    writer.write(relative, report.formatted_content)
    report.applied = True
    report.status = "applied"
    report.note = (f"{report.formatter.name if report.formatter else 'the formatter'} "
                   f"changes applied through the edit journal "
                   f"({report.format_changed_lines} format line(s), "
                   f"shown separately from the edit's "
                   f"{report.logic_changed_lines} logic line(s))")
    return report


def enabled_from_config(config: Optional[Dict[str, Any]]) -> bool:
    """The covenant is on unless the config says ``formatter_covenant: false``."""
    if not config:
        return True
    return config.get("formatter_covenant", True) is not False


def format_covenant_report(path: Path | str, *,
                           root: Optional[Path | str] = None,
                           touched: Sequence[Path | str] = (),
                           before_content: Optional[str] = None,
                           apply: bool = False,
                           runner: Optional[FormatterRunner] = None,
                           enabled: bool = True,
                           journal: Optional[EditJournal] = None
                           ) -> FormatReport:
    """Preview one touched file, and apply only when asked."""
    report = preview_format(
        path, root=root, touched=touched,
        before_content=before_content, runner=runner, enabled=enabled)
    if apply:
        report = apply_format(report, root=root, journal=journal)
    return report


# ---------------------------------------------------------------------------
# Surfaces: parser, formatters, markdown
# ---------------------------------------------------------------------------

def parse_format_args(arguments: str) -> Dict[str, Any]:
    """Parse ``/format`` arguments: one path, optional ``apply``."""
    parts = (arguments or "").split()
    if len(parts) == 1:
        return {"action": "preview", "path": parts[0]}
    if len(parts) == 2 and parts[1] == "apply":
        return {"action": "apply", "path": parts[0]}
    raise ValueError(USAGE)


def format_format_report(status: Dict[str, Any]) -> str:
    """Render an ``Agent.format_covenant`` status dict."""
    report = status.get("report") or {}
    lines = [f"Formatter covenant for {report.get('path', '')}:"]
    formatter = report.get("formatter") or {}
    if formatter:
        lines.append(
            f"  formatter: {formatter.get('name', '')} "
            f"(configured in {formatter.get('config_source', '')})")
    lines.append(f"  status: {report.get('status', '')} — {report.get('note', '')}")
    if report.get("status") in ("ok", "applied"):
        lines.append(
            f"  logic changes: {report.get('logic_changed_lines', 0)} line(s) "
            f"(the edit itself)")
        lines.append(
            f"  format changes: {report.get('format_changed_lines', 0)} line(s) "
            f"(the formatter, shown separately)")
        if report.get("format_diff"):
            lines.append("Format diff (formatter only):")
            lines.append(report["format_diff"])
    lines.append(status.get("plain_explanation", ""))
    return "\n".join(lines)


def render_markdown() -> str:
    """The slice's plain account, as markdown."""
    names = ", ".join(formatter_names())
    return (
        f"# Formatter covenant ({FORMAT_COVENANT_SLICE})\n\n"
        f"{PLAIN_EXPLANATION}\n\n"
        f"Formatters the covenant can honour, in preference "
        f"order: {names}. A formatter counts only when the "
        f"project's own config names it and its binary is "
        f"installed; otherwise nothing is formatted and the "
        f"report says why.\n\n"
        f"{USAGE}\n"
    )
