"""Debugger in the loop (M-055).

Part III — Code Intelligence. A failing test can be
re-run under the debugger by the coder itself, frames
and locals reported as evidence — M-054's debugger,
wired into the coder's own road.

What ships here, in ``mythic_agent/tools/debug_loop.py``:

* **Detection, from the test runner's own words.**
  :func:`failing_tests_from_output` reads a pytest run's
  output and returns the failing test nodes it actually
  names: the ``FAILED <node>`` lines of pytest's short
  test summary and the ``<node> FAILED`` rows of a
  verbose run. Nothing is inferred from prose, and a
  passing run yields an empty list. :func:`is_pytest_command`
  recognises a pytest invocation on the command road
  (``pytest ...`` or ``... -m pytest ...``).
* **Acceptance.** A test may also be named outright:
  :func:`split_test_node` parses ``path/to/test_file.py``
  or ``path/to/test_file.py::test_name[::...]`` and
  refuses anything that is not a Python file node.
* **The re-run.** :func:`debug_failing_test` drives
  M-054's :class:`~mythic_agent.tools.debugger.DAPClient`
  directly: the adapter launches the **pytest module**
  (debugpy's module launch, ``module: pytest``) with the
  one test node as its argument, exception breakpoints
  are set (filter ``all`` — the stop is where the failure
  raised), and any breakpoints the user named in the
  test file are set in that file. Configuration finishes,
  the first stop is awaited, and the inspection (threads,
  stack, scopes, variables — M-054's own records) becomes
  the evidence on a :class:`LoopReport`.
* **The wiring.** On the agent tool road
  (``run_command`` in ``agents/tools.py`), a pytest
  command whose result failed appends
  :func:`debug_note_for_command`: the first failing test
  the output names is re-run under the debugger and the
  formatted evidence — or the honest absence — is
  appended to the command result, in the same turn, on
  the M-052 truth-loop pattern. The setting
  ``debugger_in_loop`` (on by default) turns the wiring
  off; M-054's ``debugger`` switch gates the whole road.
* **The surfaces.** ``Agent.debug_loop(test, ...)``
  re-runs one named test; ``/debugloop`` rides the
  terminal and the TUI system-command roads (bare or
  ``show`` for the board, ``<test> [break <line> ...]``
  for a re-run), sharing this module's parser and
  formatters.

Honesty rules, pinned by the slice's tests:

* **Absence is never evidence.** Debugpy is NOT
  installed in this environment (measured at M-054's
  scoping), so a real re-run here reports
  ``not-installed`` with its remedy — no frames, no
  locals, nothing invented. Live proof rides a fake
  DAP adapter subprocess in the slice tests, speaking
  the real protocol, its module-launch arguments proven
  from the adapter's own log.
* **No stop is no evidence.** A re-run that ends before
  any stop reports ``terminated`` — the failure did not
  reproduce under the debugger (or no exception or
  breakpoint was hit) — never dressed as a stopped
  session with frames.
* **A debugger failure is never a test result.** An
  adapter that runs and then fails raises
  :class:`~mythic_agent.tools.debugger.DAPError`; the
  loop wiring catches it and appends an honest note
  saying the re-run could not be made — the original
  test result stands exactly as the runner reported it.
* **Detection names only what the runner named.** A
  failing test the output does not name is not re-run,
  and the note says the output named none.
"""

from __future__ import annotations

__all__ = [
    "DEBUG_LOOP_SLICE",
    "PLAIN_EXPLANATION",
    "USAGE",
    "LoopReport",
    "debug_failing_test",
    "debug_note_for_command",
    "enabled_from_config",
    "failing_tests_from_output",
    "format_debug_loop_board",
    "format_debug_loop_note",
    "format_debug_loop_report",
    "is_pytest_command",
    "parse_debug_loop_args",
    "render_markdown",
    "split_test_node",
]

import re
import shlex
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from . import debugger as debugger_module
from .debugger import DAPClient, DebugReport

DEBUG_LOOP_SLICE = "M-055"

PLAIN_EXPLANATION = (
    "When a test fails, the coder can watch it fail: "
    "/debugloop <test> re-runs that one test under the "
    "debugger (M-054) with exception stops on, and the "
    "stop's stack frames and local variables come back "
    "as evidence. On the coder's own road, a pytest "
    "command that fails gets the same treatment for the "
    "first failing test its output names. A machine "
    "without debugpy is told so plainly — no evidence "
    "is ever invented, and a re-run that never stops "
    "says the failure did not reproduce."
)

USAGE = ("Usage: /debugloop [show] | "
         "/debugloop <test-file>[::test-name] [break <line> ...]")

#: pytest's short-summary failure lines: ``FAILED <node> - <why>``.
_FAILED_SUMMARY = re.compile(r"^FAILED\s+(\S+)", re.MULTILINE)
#: Verbose rows: ``<node> FAILED [ 42%]``.
_FAILED_VERBOSE = re.compile(r"^(\S+::\S+)\s+FAILED\b", re.MULTILINE)


def split_test_node(node: str) -> Tuple[str, str]:
    """Split a test node into (file path, test name or "").

    The file must be a Python file; the name, when
    present, is everything after the first ``::``.
    Anything else is refused plainly.
    """
    text = (node or "").strip()
    if not text:
        raise ValueError(f"{USAGE} — a test must be named")
    file_part, _, name = text.partition("::")
    if Path(file_part).suffix.lower() != ".py":
        raise ValueError(
            f"a test node must name a Python test file, got {node!r}")
    return file_part, name.strip()


def failing_tests_from_output(output: str) -> List[str]:
    """The failing test nodes a pytest output actually names.

    Both of pytest's own failure spellings are read —
    the short summary's ``FAILED <node>`` lines and a
    verbose run's ``<node> FAILED`` rows — in output
    order, each node once. A node is kept only when it
    parses as a test node; summary decoration never
    becomes a test.
    """
    found: List[str] = []
    for match in list(_FAILED_SUMMARY.finditer(output or "")) + \
            list(_FAILED_VERBOSE.finditer(output or "")):
        node = match.group(1).rstrip(",")
        try:
            split_test_node(node)
        except ValueError:
            continue
        if node not in found:
            found.append(node)
    # Output order across both spellings: re-sort by position.
    positions = {}
    for match in list(_FAILED_SUMMARY.finditer(output or "")) + \
            list(_FAILED_VERBOSE.finditer(output or "")):
        node = match.group(1).rstrip(",")
        if node in found and node not in positions:
            positions[node] = match.start()
    return sorted(found, key=lambda n: positions.get(n, 0))


def is_pytest_command(command: str) -> bool:
    """True when *command* invokes pytest, in its common shapes."""
    try:
        tokens = shlex.split(command or "")
    except ValueError:
        tokens = (command or "").split()
    for index, token in enumerate(tokens):
        base = Path(token).name
        if base in ("pytest", "py.test"):
            return True
        if token == "-m" and index + 1 < len(tokens) \
                and tokens[index + 1] == "pytest":
            return True
    return False


@dataclass
class LoopReport:
    """One failing test's debugger-in-the-loop account."""

    test: str = ""
    file: str = ""
    status: str = "evidence"   # evidence | not-installed | no-adapter |
                               # disabled | terminated | not-found
    note: str = ""
    source: str = "named"      # named | detected
    debug: Optional[DebugReport] = None

    def record(self) -> Dict[str, Any]:
        return {
            "test": self.test, "file": self.file,
            "status": self.status, "note": self.note,
            "source": self.source,
            "debug": self.debug.record() if self.debug else None,
        }


def debug_failing_test(test: str, *,
                       breakpoints: Optional[List[int]] = None,
                       root: Optional[Path | str] = None,
                       timeout: float = 10.0,
                       enabled: bool = True,
                       source: str = "named",
                       client_factory: Optional[
                           Callable[..., DAPClient]] = None
                       ) -> LoopReport:
    """Re-run one failing test under the debugger, as evidence.

    The adapter launches the pytest module with the one
    test node; exception stops are on (filter ``all``)
    and *breakpoints* (lines in the test file) are set
    when named. Absence — no adapter for the file, an
    adapter not installed, the road switched off, a
    test file that is not there — is a report, never
    raised and never dressed as evidence. An adapter
    that runs and then fails raises
    :class:`~mythic_agent.tools.debugger.DAPError`.
    """
    file_part, _name = split_test_node(test)
    base = Path(root).resolve() if root is not None else Path.cwd()
    target = Path(file_part)
    if not target.is_absolute():
        target = base / target
    report = LoopReport(test=test, file=str(target), source=source)
    if not enabled:
        report.status = "disabled"
        report.note = ("the debugger in the loop is off, so the "
                       "failing test was not re-run under the "
                       "debugger")
        return report
    if not target.is_file():
        report.status = "not-found"
        report.note = (f"the test file {target} is not there — "
                       f"nothing was re-run")
        return report
    adapter = debugger_module.adapter_for_path(target)
    if adapter is None:
        report.status = "no-adapter"
        report.note = (f"no debug adapter is catalogued for "
                       f"{target.suffix or 'this file'} files — "
                       f"the test was not re-run under a debugger")
        return report
    if not adapter.installed() and client_factory is None:
        report.status = "not-installed"
        report.note = (f"the {adapter.name} debug adapter is not "
                       f"installed, so the failing test was not "
                       f"re-run under the debugger and no evidence "
                       f"was gathered; {adapter.install_remedy}")
        return report
    factory = client_factory or (
        lambda adp, rt: DAPClient(adp, rt, timeout=timeout))
    client = factory(adapter, base)
    client.start()
    debug = DebugReport(program=test, adapter=adapter.name)
    try:
        client.launch(module="pytest", args=[
            test, "-q", "-p", "no:cacheprovider", "--no-header"])
        if breakpoints:
            debug.breakpoints = client.set_breakpoints(
                target, list(breakpoints))
        client.set_exception_breakpoints(["all"])
        client.configuration_done()
        stopped = client.wait_stopped(since=0, timeout=timeout)
        debug.events = client.events
        if stopped is None:
            report.status = "terminated"
            debug.status = "terminated"
            debug.terminated = True
            report.note = ("the re-run ended before any stop — "
                           "the failure did not reproduce under "
                           "the debugger, or no exception or "
                           "breakpoint was hit; no evidence was "
                           "gathered")
            report.debug = debug
            return report
        debug.stopped = stopped
        seen = client.inspect(stopped.thread_id or None)
        debug.threads = seen["threads"]
        debug.frames = seen["frames"]
        debug.scopes = seen["scopes"]
        report.status = "evidence"
        where = debug.frames[0].one_line() if debug.frames else ""
        report.note = (f"stopped ({stopped.reason})"
                       + (f" at {where}" if where else "")
                       + " — frames and locals below are the "
                         "adapter's own report")
        report.debug = debug
        return report
    finally:
        client.close()


def enabled_from_config(config: Optional[Dict[str, Any]]) -> bool:
    """The loop is on unless config says so — and M-054's switch gates it."""
    if not config:
        return True
    if config.get("debugger", True) is False:
        return False
    return config.get("debugger_in_loop", True) is not False


def debug_note_for_command(command: str, output: str, *,
                           root: Optional[Path | str] = None,
                           enabled: bool = True,
                           client_factory: Optional[
                               Callable[..., DAPClient]] = None
                           ) -> str:
    """The loop's note for one finished command, or "" for none.

    Only a pytest command earns a note, and only when
    its output names a failing test. The first failing
    test is re-run under the debugger; the note is the
    formatted loop report (evidence, or the honest
    absence). A debugger failure becomes an honest note
    — it never alters or replaces the command's result.
    """
    if not enabled or not is_pytest_command(command):
        return ""
    failing = failing_tests_from_output(output)
    if not failing:
        return ""
    try:
        report = debug_failing_test(
            failing[0], root=root, enabled=True, source="detected",
            client_factory=client_factory)
    except Exception as exc:  # the loop never breaks the command
        return (f"\n\nDebugger in the loop: the failing test "
                f"{failing[0]} could not be re-run under the "
                f"debugger: {exc}")
    extra = ""
    if len(failing) > 1:
        extra = (f"\n  ({len(failing) - 1} further failing test(s) "
                 f"were named by the run and not re-run: "
                 f"{', '.join(failing[1:])})")
    return "\n\n" + format_debug_loop_report(
        {"report": report.record(),
         "plain_explanation": PLAIN_EXPLANATION}) + extra


# ---------------------------------------------------------------------------
# Surfaces: parser, formatters, markdown
# ---------------------------------------------------------------------------

def parse_debug_loop_args(arguments: str) -> Dict[str, Any]:
    """Parse ``/debugloop`` arguments: the board, or one re-run."""
    text = (arguments or "").strip()
    if not text or text == "show":
        return {"action": "show"}
    tokens = text.split()
    if tokens[0] == "show":
        raise ValueError(f"{USAGE} — show takes no further words")
    test = tokens[0]
    try:
        split_test_node(test)
    except ValueError as exc:
        raise ValueError(f"{USAGE} — {exc}") from exc
    breakpoints: List[int] = []
    index = 1
    while index < len(tokens):
        token = tokens[index]
        if token == "break":
            if index + 1 >= len(tokens):
                raise ValueError(f"{USAGE} — break needs a line number")
            try:
                line = int(tokens[index + 1])
            except ValueError:
                raise ValueError(
                    f"{USAGE} — a break line must be a whole number"
                ) from None
            if line < 1:
                raise ValueError(f"{USAGE} — a break line must be >= 1")
            breakpoints.append(line)
            index += 2
            continue
        raise ValueError(f"{USAGE} — unexpected word {token!r}")
    return {"action": "run", "test": test, "breakpoints": breakpoints}


def format_debug_loop_board(status: Dict[str, Any]) -> str:
    """The board: how the loop stands on this machine."""
    lines = [PLAIN_EXPLANATION, "", "Debug adapters:"]
    for entry in status["adapters"]:
        if entry["installed"]:
            lines.append(
                f"  {entry['name']}: installed — serves "
                f"{', '.join(entry['languages'])}")
        else:
            lines.append(
                f"  {entry['name']}: NOT INSTALLED — serves "
                f"{', '.join(entry['languages'])}; "
                f"{entry['install_remedy']}")
    return "\n".join(lines)


def format_debug_loop_report(status: Dict[str, Any]) -> str:
    """One loop re-run's account, as plain words."""
    report = status["report"]
    lines = [f"Debugger in the loop — re-run of {report['test']}:"]
    if report["status"] != "evidence":
        lines.append(f"  {report['status']} — {report['note']}")
        return "\n".join(lines)
    debug = report["debug"] or {}
    lines.append(f"  adapter: {debug.get('adapter')}")
    for raw in debug.get("breakpoints") or []:
        bp = debugger_module.Breakpoint(
            line=raw["line"], verified=raw["verified"], id=raw["id"],
            message=raw["message"], path=raw["path"])
        lines.append(f"  {bp.one_line()}")
    stopped = debug.get("stopped")
    if stopped:
        info = debugger_module.StoppedInfo(
            reason=stopped["reason"], thread_id=stopped["thread_id"],
            description=stopped["description"], text=stopped["text"],
            all_threads_stopped=stopped["all_threads_stopped"],
            hit_breakpoint_ids=stopped["hit_breakpoint_ids"])
        lines.append(f"  {info.one_line()}")
    if debug.get("frames"):
        lines.append("  stack (top first):")
        for raw in debug["frames"]:
            frame = debugger_module.StackFrame(
                id=raw["id"], name=raw["name"], path=raw["path"],
                line=raw["line"], column=raw["column"])
            lines.append(f"    {frame.one_line()}")
    for scope in debug.get("scopes") or []:
        lines.append(f"  scope {scope['name']}:")
        for var in scope["variables"]:
            lines.append(f"    {var['name']}: {var['type']} = {var['value']}"
                         if var["type"] else
                         f"    {var['name']} = {var['value']}")
            for child in var["children"]:
                lines.append(f"      {child['name']} = {child['value']}")
    if report["note"]:
        lines.append(f"  {report['note']}")
    lines.append(status.get("plain_explanation", ""))
    return "\n".join(lines)


#: The note formatter is the report formatter — one shape everywhere.
format_debug_loop_note = format_debug_loop_report


def render_markdown() -> str:
    """The slice's plain account, as markdown."""
    return (
        f"# Debugger in the loop ({DEBUG_LOOP_SLICE})\n\n"
        f"{PLAIN_EXPLANATION}\n\n"
        f"A failing test — named outright, or detected "
        f"from a pytest run's own FAILED lines — is "
        f"re-run under M-054's DAP client as a pytest "
        f"module launch with exception stops on; the "
        f"stop's frames and the top frame's locals return "
        f"as evidence. An adapter that is not installed "
        f"reports not-installed with its remedy, a re-run "
        f"that never stops reports that the failure did "
        f"not reproduce, and a debugger failure is an "
        f"honest note, never a test result.\n\n"
        f"{USAGE}\n"
    )
