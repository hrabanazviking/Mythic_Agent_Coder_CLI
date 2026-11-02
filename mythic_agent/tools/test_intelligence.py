"""Test intelligence (M-056).

Part III — Code Intelligence. Test discovery per project,
"run only what this change touches" selection from the
symbol graph, and flaky-test marking from history —
never from vibes.

What ships here, in ``mythic_agent/tools/test_intelligence.py``:

* **Discovery, from pytest's own collection.**
  :func:`discover_tests` runs ``pytest --collect-only -q``
  as a subprocess on the project root and parses the
  nodeids pytest itself prints. That collection is the
  ground truth: a pytest that is missing or fails is an
  honest ``failed`` report carrying its own words, never
  an invented list, and a project with no tests reports
  ``no-tests``.
* **Selection, from the symbol graph.**
  :func:`select_tests` takes changed files, reads the
  symbols each changed file defines from the house code
  index (M-046's :class:`~mythic_agent.tools.code_index.SymbolIndex`),
  and selects the discovered tests that touch the change:
  a test file that itself changed, a test that imports a
  changed module (or a symbol from it), and a test whose
  text references a symbol a changed file defines. When
  there are no changed files, when discovery cannot
  answer, or when nothing matches, the selection is an
  honest **whole-suite fallback** with its reason stated
  — never an empty list dressed as confidence.
* **Flaky marking, from recorded history only.**
  Outcomes a pytest run actually named are appended to a
  JSONL history store (``.mythic/test_history.jsonl``
  under the project root) by :func:`record_run`, which
  reads the runner's own words (verbose ``<node> PASSED``
  / ``FAILED`` rows and the short summary's ``FAILED`` /
  ``ERROR`` lines, on the M-055 detection pattern).
  A test is marked flaky only when its recorded history
  shows BOTH a pass and a fail for the same nodeid across
  at least :data:`FLAKY_MIN_RUNS` recorded runs. No
  history means no mark; a stable pass is not flaky and
  a stable fail is not flaky — it is just failing.
* **The wiring.** On the agent tool road
  (``run_command`` in ``agents/tools.py`), a pytest
  command's named outcomes are recorded to history via
  :func:`record_note_for_command`, gated by the setting
  ``test_intelligence`` (on by default). Recording never
  alters the command's result, and a history failure is
  swallowed there — the road that reports is ``/testintel``.
* **The surfaces.** ``Agent.test_intel_status()`` /
  ``test_intel_select()`` / ``test_intel_history()`` and
  ``/testintel`` on the terminal and TUI system-command
  roads (bare or ``show`` for the board, ``select <file>
  ...`` for a selection, ``history`` for the history and
  its flaky marks), sharing this module's parser and
  formatters.

Honesty rules, pinned by the slice's tests:

* **Collection is the truth.** Discovery never guesses
  a test list from file names; it reports what pytest
  collected, or why it could not.
* **Fallback is a first-class answer.** An unanswerable
  selection says "run the whole suite" and says why.
* **Flaky is a history verdict.** It is computed only
  from recorded outcomes, with the counts shown.
"""

from __future__ import annotations

__all__ = [
    "FLAKY_MIN_RUNS",
    "PLAIN_EXPLANATION",
    "TEST_INTELLIGENCE_SLICE",
    "USAGE",
    "DiscoveryReport",
    "FlakyMark",
    "HistoryReport",
    "SelectionReport",
    "TestStat",
    "board_report",
    "default_history_path",
    "discover_tests",
    "enabled_from_config",
    "flaky_marks",
    "format_test_intel_board",
    "format_test_intel_history",
    "format_test_intel_selection",
    "history_report",
    "load_history",
    "outcomes_from_output",
    "parse_test_intel_args",
    "record_note_for_command",
    "record_outcomes",
    "record_run",
    "render_markdown",
    "select_tests",
]

import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from .code_index import SymbolIndex
from .debug_loop import is_pytest_command

TEST_INTELLIGENCE_SLICE = "M-056"

#: Recorded runs a nodeid needs (with both outcomes) before
#: history may call it flaky.
FLAKY_MIN_RUNS = 3

PLAIN_EXPLANATION = (
    "Test intelligence knows this project's tests the "
    "honest way: /testintel shows the tests pytest itself "
    "collects, /testintel select <changed-file> ... picks "
    "only the tests that touch a change — from the symbol "
    "graph, with a plain whole-suite fallback when the "
    "graph cannot answer — and a test is marked flaky "
    "only when its recorded run history shows both a pass "
    "and a fail, never from a guess."
)

USAGE = ("Usage: /testintel [show] | "
         "/testintel select <changed-file> [...] | "
         "/testintel history")

_NODE_LINE = re.compile(r"^([^\s]+\.py::[^\s]+)$")
_VERBOSE_OUTCOME = re.compile(
    r"^(\S+::\S+)\s+(PASSED|FAILED|ERROR|SKIPPED)\b", re.MULTILINE)
_SUMMARY_FAIL = re.compile(r"^(FAILED|ERROR)\s+(\S+)", re.MULTILINE)


def enabled_from_config(config: Optional[Dict[str, Any]]) -> bool:
    """Test intelligence is on unless config says so."""
    if not config:
        return True
    return config.get("test_intelligence", True) is not False


def default_history_path(root: Path | str) -> Path:
    """The project's recorded test-history store."""
    return Path(root) / ".mythic" / "test_history.jsonl"


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

@dataclass
class DiscoveryReport:
    """What pytest collected for one project, or why not."""

    root: str = ""
    status: str = "ok"  # ok | no-tests | failed | disabled | not-found
    tests: List[str] = field(default_factory=list)
    note: str = ""

    def record(self) -> Dict[str, Any]:
        return {"root": self.root, "status": self.status,
                "tests": list(self.tests), "note": self.note,
                "count": len(self.tests)}


def _parse_collected(output: str) -> List[str]:
    found: List[str] = []
    for line in (output or "").splitlines():
        match = _NODE_LINE.match(line.strip())
        if match and match.group(1) not in found:
            found.append(match.group(1))
    return found


def discover_tests(root: Optional[Path | str] = None, *,
                   timeout: float = 60.0,
                   enabled: bool = True,
                   runner: Optional[Callable[..., Tuple[int, str]]] = None
                   ) -> DiscoveryReport:
    """Collect a project's tests via ``pytest --collect-only -q``.

    The subprocess output is the only source of nodeids.
    A missing project, a switched-off road, a pytest that
    cannot run, and an empty collection are each their own
    honest status. *runner* (a callable taking
    ``(argv, cwd, timeout)`` and returning ``(code, output)``)
    exists so tests can prove the failure roads without
    uninstalling pytest.
    """
    base = Path(root).resolve() if root is not None else Path.cwd()
    report = DiscoveryReport(root=str(base))
    if not enabled:
        report.status = "disabled"
        report.note = ("test intelligence is off, so no tests "
                       "were collected")
        return report
    if not base.is_dir():
        report.status = "not-found"
        report.note = f"the project root {base} is not there"
        return report
    argv = [sys.executable, "-m", "pytest", "--collect-only", "-q",
            "-p", "no:cacheprovider", "--no-header"]
    try:
        if runner is not None:
            code, output = runner(argv, base, timeout)
        else:
            proc = subprocess.run(
                argv, cwd=str(base), capture_output=True, text=True,
                timeout=timeout)
            code, output = proc.returncode, (proc.stdout or "") + \
                (proc.stderr or "")
    except (OSError, subprocess.TimeoutExpired) as exc:
        report.status = "failed"
        report.note = (f"pytest collection could not run: {exc} — "
                       f"no test list was invented")
        return report
    report.tests = _parse_collected(output)
    if code == 0 and report.tests:
        report.status = "ok"
        report.note = (f"pytest collected {len(report.tests)} "
                       f"test(s) for this project")
        return report
    if code == 5 or (code == 0 and not report.tests):
        report.status = "no-tests"
        report.tests = []
        report.note = ("pytest collected no tests for this "
                       "project — the list is empty because the "
                       "project has none, not because of a guess")
        return report
    report.status = "failed"
    tail = " ".join((output or "").strip().splitlines()[-3:])
    report.note = (f"pytest collection failed (exit {code})"
                   + (f": {tail[:300]}" if tail else "")
                   + " — no test list was invented")
    report.tests = []
    return report


# ---------------------------------------------------------------------------
# History + flaky marking
# ---------------------------------------------------------------------------

def outcomes_from_output(output: str) -> Dict[str, str]:
    """The per-test outcomes a pytest output actually names.

    Verbose rows (``<node> PASSED`` / ``FAILED`` / ``ERROR``
    / ``SKIPPED``) and the short summary's ``FAILED`` /
    ``ERROR`` lines are read, in output order. A passing
    test a quiet (``-q``) run does not name is not recorded
    — history holds only what the runner said.
    """
    found: Dict[str, str] = {}
    hits: List[Tuple[int, str, str]] = []
    for match in _VERBOSE_OUTCOME.finditer(output or ""):
        node = match.group(1).rstrip(",")
        if ".py::" in node:
            hits.append((match.start(), node, match.group(2).lower()))
    for match in _SUMMARY_FAIL.finditer(output or ""):
        node = match.group(2).rstrip(",")
        if ".py::" in node:
            hits.append((match.start(), node, match.group(1).lower()))
    for _pos, node, outcome in sorted(hits):
        found[node] = outcome
    return found


def record_outcomes(outcomes: Dict[str, str], *,
                    root: Optional[Path | str] = None,
                    history_path: Optional[Path | str] = None,
                    when: Optional[str] = None) -> int:
    """Append one run's named outcomes to the history store.

    Returns how many outcome records were written. Each
    record is one JSON line: node, outcome, and the run's
    timestamp — the raw material flaky marking reads.
    """
    if not outcomes:
        return 0
    base = Path(root).resolve() if root is not None else Path.cwd()
    path = Path(history_path) if history_path is not None else \
        default_history_path(base)
    stamp = when or datetime.now(timezone.utc).isoformat()
    path.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with path.open("a", encoding="utf-8") as handle:
        for node, outcome in outcomes.items():
            handle.write(json.dumps(
                {"ts": stamp, "node": node, "outcome": outcome},
                sort_keys=True) + "\n")
            written += 1
    return written


def record_run(output: str, *,
               root: Optional[Path | str] = None,
               history_path: Optional[Path | str] = None,
               when: Optional[str] = None) -> int:
    """Record the outcomes one pytest run's output names."""
    return record_outcomes(
        outcomes_from_output(output), root=root,
        history_path=history_path, when=when)


def load_history(*, root: Optional[Path | str] = None,
                 history_path: Optional[Path | str] = None
                 ) -> List[Dict[str, Any]]:
    """Every recorded outcome, oldest first; [] when none.

    A line that is not a well-formed record is skipped —
    a corrupt line never becomes an outcome.
    """
    base = Path(root).resolve() if root is not None else Path.cwd()
    path = Path(history_path) if history_path is not None else \
        default_history_path(base)
    if not path.is_file():
        return []
    records: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except ValueError:
            continue
        if isinstance(item, dict) and item.get("node") and \
                item.get("outcome") in ("passed", "failed", "error", "skipped"):
            records.append(item)
    return records


@dataclass
class TestStat:
    """One test's recorded account."""

    node: str = ""
    runs: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    skipped: int = 0

    def record(self) -> Dict[str, Any]:
        return {"node": self.node, "runs": self.runs,
                "passed": self.passed, "failed": self.failed,
                "errors": self.errors, "skipped": self.skipped}


@dataclass
class FlakyMark:
    """Whether history — and only history — calls a test flaky."""

    node: str = ""
    flaky: bool = False
    runs: int = 0
    passed: int = 0
    failed: int = 0
    reason: str = ""

    def record(self) -> Dict[str, Any]:
        return {"node": self.node, "flaky": self.flaky,
                "runs": self.runs, "passed": self.passed,
                "failed": self.failed, "reason": self.reason}


def _stats(records: List[Dict[str, Any]]) -> Dict[str, TestStat]:
    stats: Dict[str, TestStat] = {}
    for item in records:
        stat = stats.setdefault(item["node"], TestStat(node=item["node"]))
        stat.runs += 1
        if item["outcome"] == "passed":
            stat.passed += 1
        elif item["outcome"] == "failed":
            stat.failed += 1
        elif item["outcome"] == "error":
            stat.errors += 1
        else:
            stat.skipped += 1
    return stats


def flaky_marks(*, root: Optional[Path | str] = None,
                history_path: Optional[Path | str] = None,
                records: Optional[List[Dict[str, Any]]] = None,
                min_runs: int = FLAKY_MIN_RUNS) -> List[FlakyMark]:
    """Flaky verdicts from recorded history, one per known test.

    A test is flaky only when history shows at least one
    pass AND at least one fail (fail or error) across at
    least *min_runs* recorded runs. Everything else gets
    its honest reason: no history, too few runs, stable
    pass, or stable fail.
    """
    data = records if records is not None else load_history(
        root=root, history_path=history_path)
    marks: List[FlakyMark] = []
    for node, stat in sorted(_stats(data).items()):
        fails = stat.failed + stat.errors
        mark = FlakyMark(node=node, runs=stat.runs,
                         passed=stat.passed, failed=fails)
        if stat.passed and fails and stat.runs >= min_runs:
            mark.flaky = True
            mark.reason = (f"recorded history shows {stat.passed} "
                           f"pass(es) and {fails} fail(s) across "
                           f"{stat.runs} recorded runs")
        elif stat.passed and fails:
            mark.reason = (f"history shows both a pass and a fail, "
                           f"but only {stat.runs} recorded run(s) — "
                           f"below the {min_runs}-run threshold, so "
                           f"no flaky mark yet")
        elif stat.passed:
            mark.reason = "stable pass in recorded history"
        elif fails:
            mark.reason = ("stable fail in recorded history — "
                           "failing, not flaky")
        else:
            mark.reason = "only skipped in recorded history"
        marks.append(mark)
    return marks


@dataclass
class HistoryReport:
    """The whole history store's account for one project."""

    root: str = ""
    path: str = ""
    total: int = 0
    stats: List[TestStat] = field(default_factory=list)
    flaky: List[FlakyMark] = field(default_factory=list)
    note: str = ""

    def record(self) -> Dict[str, Any]:
        return {"root": self.root, "path": self.path,
                "total": self.total,
                "stats": [s.record() for s in self.stats],
                "flaky": [m.record() for m in self.flaky],
                "note": self.note}


def history_report(root: Optional[Path | str] = None, *,
                   history_path: Optional[Path | str] = None
                   ) -> HistoryReport:
    """Summarise the recorded history for one project."""
    base = Path(root).resolve() if root is not None else Path.cwd()
    path = Path(history_path) if history_path is not None else \
        default_history_path(base)
    records = load_history(root=base, history_path=path)
    stats = _stats(records)
    report = HistoryReport(
        root=str(base), path=str(path), total=len(records),
        stats=[stats[n] for n in sorted(stats)],
        flaky=flaky_marks(records=records))
    if not records:
        report.note = ("no recorded test history yet — no test "
                       "carries a flaky mark, because there is "
                       "nothing to mark from")
    else:
        marked = sum(1 for m in report.flaky if m.flaky)
        report.note = (f"{len(records)} recorded outcome(s) over "
                       f"{len(stats)} test(s); {marked} marked "
                       f"flaky from that history")
    return report


# ---------------------------------------------------------------------------
# Selection
# ---------------------------------------------------------------------------

@dataclass
class SelectionReport:
    """Which tests a change touches, or the whole-suite fallback."""

    root: str = ""
    status: str = "selected"  # selected | whole-suite | disabled
    changed: List[str] = field(default_factory=list)
    selected: List[str] = field(default_factory=list)
    reasons: Dict[str, str] = field(default_factory=dict)
    fallback: bool = False
    reason: str = ""
    discovery_status: str = ""

    def record(self) -> Dict[str, Any]:
        return {"root": self.root, "status": self.status,
                "changed": list(self.changed),
                "selected": list(self.selected),
                "reasons": dict(self.reasons),
                "fallback": self.fallback, "reason": self.reason,
                "discovery_status": self.discovery_status}


def _is_test_file(path: Path) -> bool:
    name = path.name
    return name.startswith("test_") and name.endswith(".py") or \
        name.endswith("_test.py")


def _module_name(path: Path, base: Path) -> str:
    try:
        rel = path.resolve().relative_to(base)
    except ValueError:
        rel = Path(path.name)
    parts = list(rel.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def select_tests(changed_files: List[str], *,
                 root: Optional[Path | str] = None,
                 enabled: bool = True,
                 discovery: Optional[DiscoveryReport] = None
                 ) -> SelectionReport:
    """Select the tests a change touches, from the symbol graph.

    A discovered test is selected when its file is itself
    changed, when it imports a changed module or a symbol
    from one, or when its text references a symbol a
    changed file defines (per the M-046 code index). Any
    road that cannot answer — no changed files, discovery
    failed, a changed file the graph cannot read, or no
    matches at all — returns the whole-suite fallback
    with its reason, never an empty confident selection.
    """
    base = Path(root).resolve() if root is not None else Path.cwd()
    changed = [str(c) for c in (changed_files or []) if str(c).strip()]
    report = SelectionReport(root=str(base), changed=changed)
    if not enabled:
        report.status = "disabled"
        report.fallback = True
        report.reason = ("test intelligence is off, so no "
                         "selection was made — run the whole suite")
        return report
    if not changed:
        report.status = "whole-suite"
        report.fallback = True
        report.reason = ("no changed files were named, so there "
                         "is nothing to select from — run the "
                         "whole suite")
        return report
    disc = discovery if discovery is not None else discover_tests(base)
    report.discovery_status = disc.status
    if disc.status != "ok":
        report.status = "whole-suite"
        report.fallback = True
        report.selected = list(disc.tests)
        report.reason = (f"test discovery could not answer "
                         f"({disc.status}: {disc.note}) — run "
                         f"the whole suite")
        return report
    index = SymbolIndex(base)
    # Group discovered tests by their file, read once each.
    tests_by_file: Dict[str, List[str]] = {}
    for node in disc.tests:
        tests_by_file.setdefault(node.split("::")[0], []).append(node)
    file_text: Dict[str, str] = {}
    file_imports: Dict[str, List[Any]] = {}
    for rel in tests_by_file:
        target = base / rel
        try:
            file_text[rel] = target.read_text(
                encoding="utf-8", errors="replace")
        except OSError:
            file_text[rel] = ""
        file_imports[rel] = [s for s in index.index_file(target)
                             if s.kind == "import"]
    unreadable: List[str] = []
    for item in changed:
        raw = Path(item)
        target = raw if raw.is_absolute() else base / raw
        try:
            rel_changed = str(target.resolve().relative_to(base))
        except ValueError:
            rel_changed = str(raw)
        if _is_test_file(target):
            for node in tests_by_file.get(rel_changed, []):
                report.selected.append(node)
                report.reasons[node] = "the test file itself changed"
            continue
        if not target.is_file():
            unreadable.append(item)
            continue
        module = _module_name(target, base)
        symbols = {s.name for s in index.index_file(target)
                   if s.kind != "import" and s.name}
        patterns = {name: re.compile(r"\b" + re.escape(name) + r"\b")
                    for name in symbols}
        for rel, nodes in tests_by_file.items():
            if rel == rel_changed:
                continue
            why = ""
            for imp in file_imports.get(rel, []):
                origin = imp.docstring or ""
                if module and (origin == module or
                                origin.startswith(module + ".")):
                    why = f"imports {origin} from the changed file"
                    break
            if not why and patterns:
                text = file_text.get(rel, "")
                for name, pattern in patterns.items():
                    if pattern.search(text):
                        why = (f"references {name}, defined in "
                               f"the changed file {rel_changed}")
                        break
            if why:
                for node in nodes:
                    if node not in report.selected:
                        report.selected.append(node)
                    report.reasons.setdefault(node, why)
    report.selected = [n for n in disc.tests if n in set(report.selected)]
    if unreadable and not report.selected:
        report.status = "whole-suite"
        report.fallback = True
        report.selected = list(disc.tests)
        report.reason = (f"the changed file(s) {', '.join(unreadable)} "
                         f"could not be read by the symbol graph — "
                         f"run the whole suite")
        return report
    if not report.selected:
        report.status = "whole-suite"
        report.fallback = True
        report.selected = list(disc.tests)
        report.reason = ("no discovered test touches the changed "
                         "file(s) by import or symbol reference — "
                         "run the whole suite rather than trust "
                         "an empty selection")
        return report
    report.status = "selected"
    extra = (f" ({len(unreadable)} changed file(s) could not be "
             f"read and were not selected from)" if unreadable else "")
    report.reason = (f"{len(report.selected)} of {len(disc.tests)} "
                     f"discovered test(s) touch the change{extra}")
    return report


# ---------------------------------------------------------------------------
# Board + wiring
# ---------------------------------------------------------------------------

def board_report(root: Optional[Path | str] = None, *,
                 enabled: bool = True) -> Dict[str, Any]:
    """The /testintel board: discovery + history + flaky marks."""
    base = Path(root).resolve() if root is not None else Path.cwd()
    disc = discover_tests(base, enabled=enabled)
    hist = history_report(base)
    return {"discovery": disc.record(), "history": hist.record(),
            "plain_explanation": PLAIN_EXPLANATION}


def record_note_for_command(command: str, output: str, *,
                            root: Optional[Path | str] = None,
                            enabled: bool = True) -> int:
    """Record a finished pytest command's named outcomes.

    Returns how many outcomes were written (0 for a
    non-pytest command, a switched-off road, or a run whose
    output names no per-test outcome). Never raises: the
    wiring caller treats history as a note, not a result.
    """
    if not enabled or not is_pytest_command(command):
        return 0
    try:
        return record_run(output, root=root)
    except Exception:
        return 0


# ---------------------------------------------------------------------------
# Surfaces: parser, formatters, markdown
# ---------------------------------------------------------------------------

def parse_test_intel_args(arguments: str) -> Dict[str, Any]:
    """Parse ``/testintel`` arguments: board, select, or history."""
    text = (arguments or "").strip()
    if not text or text == "show":
        return {"action": "show"}
    tokens = text.split()
    if tokens[0] == "show":
        raise ValueError(f"{USAGE} — show takes no further words")
    if tokens[0] == "history":
        if len(tokens) != 1:
            raise ValueError(f"{USAGE} — history takes no further words")
        return {"action": "history"}
    if tokens[0] == "select":
        if len(tokens) < 2:
            raise ValueError(
                f"{USAGE} — select needs at least one changed file")
        return {"action": "select", "changed": tokens[1:]}
    raise ValueError(f"{USAGE} — unexpected word {tokens[0]!r}")


def format_test_intel_board(status: Dict[str, Any]) -> str:
    """The board: discovery standing + history standing."""
    disc = status["discovery"]
    hist = status["history"]
    lines = [PLAIN_EXPLANATION, "",
             f"Discovery: {disc['status']} — {disc['note']}"]
    for node in disc["tests"][:50]:
        lines.append(f"  {node}")
    if disc["count"] > 50:
        lines.append(f"  … and {disc['count'] - 50} more")
    lines.append(f"History: {hist['note']}")
    for mark in hist["flaky"]:
        if mark["flaky"]:
            lines.append(f"  FLAKY {mark['node']} — {mark['reason']}")
    return "\n".join(lines)


def format_test_intel_selection(status: Dict[str, Any]) -> str:
    """One selection's account, fallback included."""
    sel = status["selection"]
    lines = [f"Test selection for {', '.join(sel['changed']) or '(none)'}:"]
    if sel["fallback"]:
        lines.append(f"  whole suite — {sel['reason']}")
        return "\n".join(lines)
    for node in sel["selected"]:
        lines.append(f"  {node} — {sel['reasons'].get(node, 'touches the change')}")
    lines.append(f"  {sel['reason']}")
    return "\n".join(lines)


def format_test_intel_history(status: Dict[str, Any]) -> str:
    """The history account: per-test counts and flaky marks."""
    hist = status["history"]
    lines = [f"Recorded test history ({hist['path']}):",
             f"  {hist['note']}"]
    for stat in hist["stats"]:
        lines.append(
            f"  {stat['node']}: {stat['runs']} run(s) — "
            f"{stat['passed']} passed, {stat['failed']} failed, "
            f"{stat['errors']} error, {stat['skipped']} skipped")
    for mark in hist["flaky"]:
        label = "FLAKY" if mark["flaky"] else "not flaky"
        lines.append(f"  {label}: {mark['node']} — {mark['reason']}")
    return "\n".join(lines)


def render_markdown() -> str:
    """The slice's plain account, as markdown."""
    return (
        f"# Test intelligence ({TEST_INTELLIGENCE_SLICE})\n\n"
        f"{PLAIN_EXPLANATION}\n\n"
        f"Discovery is pytest collection itself, run on the "
        f"project and parsed from its own output. Selection "
        f"walks changed files through the M-046 symbol "
        f"graph — imports of a changed module and references "
        f"to its symbols select the tests that touch it, "
        f"and any road that cannot answer falls back to the "
        f"whole suite with its reason stated. Flaky marks "
        f"come only from the recorded JSONL history under "
        f"`.mythic/`: both a pass and a fail for the same "
        f"test across at least {FLAKY_MIN_RUNS} recorded "
        f"runs, or there is no mark.\n\n"
        f"{USAGE}\n"
    )
