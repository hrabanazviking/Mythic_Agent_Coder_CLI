"""M-055 — Debugger in the loop.

TIER: integration

A failing test — named outright, or detected from a
pytest run's own FAILED lines — is re-run under M-054's
DAP client as a pytest module launch with exception
stops on; the stop's frames and locals return as
evidence. Absence is never evidence: debugpy is not
installed in this environment, so a real re-run reports
not-installed with its remedy, and live proof rides a
fake DAP adapter subprocess speaking the real protocol
(module launch and exception filters proven from the
adapter's own log). A re-run that never stops reports
that the failure did not reproduce.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mythic_agent.tools import debugger as dap
from mythic_agent.tools import debug_loop as loop
from mythic_agent.tools.debug_loop import (
    DEBUG_LOOP_SLICE, LoopReport, debug_failing_test,
    debug_note_for_command, enabled_from_config,
    failing_tests_from_output, format_debug_loop_board,
    format_debug_loop_report, is_pytest_command,
    parse_debug_loop_args, split_test_node,
)
from mythic_agent.tools.debugger import AdapterDef, DAPClient, DAPError

REPO_ROOT = Path(__file__).resolve().parent.parent

FAKE_ADAPTER = r'''
import json
import os
import sys


def read_message(stream):
    length = None
    while True:
        line = stream.readline()
        if not line:
            return None
        line = line.strip()
        if not line:
            break
        name, _, value = line.partition(b":")
        if name.strip().lower() == b"content-length":
            length = int(value.strip())
    body = stream.read(length)
    return json.loads(body.decode("utf-8"))


def send(stream, message):
    body = json.dumps(message).encode("utf-8")
    stream.write(b"Content-Length: %d\r\n\r\n" % len(body) + body)
    stream.flush()


def respond(stream, request, body=None):
    send(stream, {"seq": 0, "type": "response",
                  "request_seq": request["seq"],
                  "command": request["command"],
                  "success": True, "body": body or {}})


def event(stream, name, body=None):
    send(stream, {"seq": 0, "type": "event", "event": name,
                  "body": body or {}})


def main():
    log_path = sys.argv[1]
    mode = os.environ.get("FAKE_DAP_MODE", "normal")
    stream_in = sys.stdin.buffer
    stream_out = sys.stdout.buffer
    log = open(log_path, "a", encoding="utf-8")
    state = {"node": "", "line": 7}
    while True:
        message = read_message(stream_in)
        if message is None:
            return
        if message.get("type") == "response":
            continue
        command = message.get("command")
        if command:
            log.write(command + "\n")
            log.flush()
        args = message.get("arguments") or {}
        if command == "initialize":
            respond(stream_out, message,
                    {"supportsConfigurationDoneRequest": True})
        elif command == "launch":
            state["node"] = (args.get("args") or [""])[0]
            log.write("launch module=%s args=%s\n" % (
                args.get("module", ""), " ".join(args.get("args") or [])))
            log.flush()
            respond(stream_out, message)
        elif command == "setBreakpoints":
            bps = []
            for i, bp in enumerate(args.get("breakpoints") or []):
                state["line"] = bp["line"]
                bps.append({"id": i + 1, "verified": True,
                            "line": bp["line"],
                            "source": args.get("source") or {}})
            respond(stream_out, message, {"breakpoints": bps})
        elif command == "setExceptionBreakpoints":
            log.write("filters:%s\n" % ",".join(args.get("filters") or []))
            log.flush()
            respond(stream_out, message, {"breakpoints": []})
        elif command == "configurationDone":
            respond(stream_out, message)
            if mode == "exit-early":
                event(stream_out, "terminated", {"restart": False})
            else:
                event(stream_out, "stopped",
                      {"reason": "exception", "threadId": 1,
                       "allThreadsStopped": True,
                       "text": "AssertionError: assert 41 == 42"})
        elif command == "threads":
            respond(stream_out, message,
                    {"threads": [{"id": 1, "name": "main"}]})
        elif command == "stackTrace":
            node = state["node"]
            file_part, _, name = node.partition("::")
            path = file_part if os.path.isabs(file_part) else \
                os.path.join(os.getcwd(), file_part)
            respond(stream_out, message, {"stackFrames": [
                {"id": 100, "name": name or "test_body",
                 "source": {"path": path},
                 "line": state["line"], "column": 3},
                {"id": 101, "name": "run_one",
                 "source": {"path": path},
                 "line": 2, "column": 1}], "totalFrames": 2})
        elif command == "scopes":
            respond(stream_out, message, {"scopes": [
                {"name": "Locals", "variablesReference": 500,
                 "expensive": False}]})
        elif command == "variables":
            table = {
                500: [{"name": "x", "value": "41", "type": "int",
                       "variablesReference": 0, "evaluateName": "x"},
                      {"name": "items", "value": "[1, 2]",
                       "type": "list", "variablesReference": 600,
                       "evaluateName": "items"}],
                600: [{"name": "0", "value": "1", "type": "int",
                       "variablesReference": 0}],
            }
            respond(stream_out, message,
                    {"variables": table.get(
                        args.get("variablesReference"), [])})
        elif command == "disconnect":
            respond(stream_out, message)
            return


main()
'''


@pytest.fixture()
def fake_adapter(tmp_path):
    script = tmp_path / "fake_adapter.py"
    script.write_text(FAKE_ADAPTER, encoding="utf-8")
    log = tmp_path / "fake_adapter.log"
    adapter = AdapterDef(
        name="fake", languages=("python",), extensions=(".py",),
        command=(sys.executable, str(script), str(log)),
        install_remedy="install the fake adapter")
    return adapter, log


def _factory_for(adapter):
    return lambda adp, root: DAPClient(adapter, root, timeout=5.0)


def _test_file(tmp_path, name="test_bad.py"):
    target = tmp_path / name
    target.write_text(
        "def test_fails():\n    x = 41\n    assert x == 42\n",
        encoding="utf-8")
    return target


# ---------------------------------------------------------------- nodes

def test_slice_and_node_parsing():
    assert DEBUG_LOOP_SLICE == "M-055"
    assert split_test_node("tests/test_a.py") == ("tests/test_a.py", "")
    assert split_test_node("tests/test_a.py::test_b") == \
        ("tests/test_a.py", "test_b")
    assert split_test_node("t.py::TestC::test_b") == ("t.py", "TestC::test_b")
    for bad in ("", "notes.txt", "no_extension"):
        with pytest.raises(ValueError):
            split_test_node(bad)


def test_detection_reads_only_what_pytest_named():
    output = (
        "tests/test_a.py::test_one FAILED                     [ 50%]\n"
        "tests/test_a.py::test_two PASSED                     [100%]\n"
        "=========================== short test summary info =======\n"
        "FAILED tests/test_a.py::test_one - AssertionError: no\n"
        "FAILED tests/test_b.py::test_three - ValueError: boom\n"
        "2 failed, 1 passed in 0.42s\n")
    assert failing_tests_from_output(output) == [
        "tests/test_a.py::test_one", "tests/test_b.py::test_three"]
    assert failing_tests_from_output("3 passed in 0.10s\n") == []
    assert failing_tests_from_output("") == []
    # A FAILED word over something that is not a test node is not a test.
    assert failing_tests_from_output("FAILED to fetch the thing\n") == []


def test_is_pytest_command_shapes():
    assert is_pytest_command("pytest tests/ -q")
    assert is_pytest_command("python -m pytest tests/test_a.py -q")
    assert is_pytest_command(f"{sys.executable} -m pytest -q")
    assert not is_pytest_command("python -m unittest discover")
    assert not is_pytest_command("ls tests/")
    assert not is_pytest_command("")


def test_enabled_from_config_and_the_m054_gate():
    assert enabled_from_config(None) is True
    assert enabled_from_config({}) is True
    assert enabled_from_config({"debugger_in_loop": False}) is False
    assert enabled_from_config({"debugger": False}) is False
    assert enabled_from_config(
        {"debugger": True, "debugger_in_loop": True}) is True


# ---------------------------------------------------------------- absence

def test_rerun_reports_not_installed(tmp_path, monkeypatch):
    monkeypatch.setattr(
        dap.importlib.util, "find_spec", lambda name: None)
    _test_file(tmp_path)
    report = debug_failing_test(
        "test_bad.py::test_fails", root=tmp_path)
    assert isinstance(report, LoopReport)
    assert report.status == "not-installed"
    assert "pip install debugpy" in report.note
    assert report.debug is None


def test_rerun_reports_not_found_and_disabled(tmp_path):
    missing = debug_failing_test("test_gone.py::test_x", root=tmp_path)
    assert missing.status == "not-found"
    _test_file(tmp_path)
    off = debug_failing_test(
        "test_bad.py::test_fails", root=tmp_path, enabled=False)
    assert off.status == "disabled"
    assert off.debug is None


# ---------------------------------------------------------------- live proof

def test_live_rerun_gathers_frames_and_locals(tmp_path, fake_adapter):
    adapter, log = fake_adapter
    _test_file(tmp_path)
    report = debug_failing_test(
        "test_bad.py::test_fails", root=tmp_path, breakpoints=[3],
        client_factory=_factory_for(adapter))
    assert report.status == "evidence"
    assert report.source == "named"
    debug = report.debug
    assert debug is not None and debug.adapter == "debugpy"
    assert debug.stopped is not None
    assert debug.stopped.reason == "exception"
    assert "AssertionError" in debug.stopped.text
    assert debug.breakpoints[0].line == 3
    assert debug.breakpoints[0].verified is True
    assert [f.name for f in debug.frames] == ["test_fails", "run_one"]
    assert debug.frames[0].line == 3
    locals_scope = debug.scopes[0]
    assert [v.name for v in locals_scope.variables] == ["x", "items"]
    assert locals_scope.variables[0].value == "41"
    assert locals_scope.variables[1].children[0].value == "1"
    # The adapter's own log proves the module launch and the
    # exception road, in the client's order.
    wire = log.read_text(encoding="utf-8")
    assert "launch module=pytest args=test_bad.py::test_fails" in wire
    assert "filters:all" in wire
    order = [line for line in wire.splitlines() if line and
             not line.startswith(("launch ", "filters:"))]
    assert order[:5] == ["initialize", "launch", "setBreakpoints",
                         "setExceptionBreakpoints", "configurationDone"]


def test_live_rerun_without_a_stop_reports_not_reproduced(
        tmp_path, fake_adapter, monkeypatch):
    adapter, _log = fake_adapter
    monkeypatch.setenv("FAKE_DAP_MODE", "exit-early")
    _test_file(tmp_path)
    report = debug_failing_test(
        "test_bad.py::test_fails", root=tmp_path,
        client_factory=_factory_for(adapter))
    assert report.status == "terminated"
    assert "did not reproduce" in report.note
    assert report.debug is not None and report.debug.frames == []


def test_adapter_failure_raises_in_its_own_words(tmp_path, fake_adapter):
    _test_file(tmp_path)
    broken = AdapterDef(
        name="fake", languages=("python",), extensions=(".py",),
        command=(sys.executable, "-c", "raise SystemExit(3)"),
        install_remedy="install the fake adapter")
    with pytest.raises(DAPError):
        debug_failing_test(
            "test_bad.py::test_fails", root=tmp_path,
            client_factory=_factory_for(broken))


# ---------------------------------------------------------------- the note road

FAILED_OUTPUT = (
    "=========================== short test summary info =======\n"
    "FAILED test_bad.py::test_fails - AssertionError: assert 41 == 42\n"
    "FAILED test_other.py::test_also - ValueError: boom\n"
    "2 failed in 0.31s\n")


def test_note_for_command_roads(tmp_path, monkeypatch):
    monkeypatch.setattr(
        dap.importlib.util, "find_spec", lambda name: None)
    _test_file(tmp_path)
    # Not a pytest command: no note, whatever the output says.
    assert debug_note_for_command("ls", FAILED_OUTPUT, root=tmp_path) == ""
    # A passing pytest run names no failing test: no note.
    assert debug_note_for_command(
        "pytest -q", "3 passed in 0.1s\n", root=tmp_path) == ""
    # A failed pytest run: the first failing test is re-run;
    # here the adapter is absent, so the note is the honest
    # absence, and the second failing test is accounted for.
    note = debug_note_for_command(
        "python -m pytest -q", FAILED_OUTPUT, root=tmp_path)
    assert "Debugger in the loop" in note
    assert "not-installed" in note
    assert "test_bad.py::test_fails" in note
    assert "test_other.py::test_also" in note


def test_note_for_command_with_evidence(tmp_path, fake_adapter):
    adapter, _log = fake_adapter
    _test_file(tmp_path)
    _test_file(tmp_path, "test_other.py")
    note = debug_note_for_command(
        "pytest -q", FAILED_OUTPUT, root=tmp_path,
        client_factory=_factory_for(adapter))
    assert "stopped: exception" in note
    assert "x: int = 41" in note
    assert "further failing" in note


def test_note_for_command_swallows_a_debugger_failure(tmp_path):
    broken = AdapterDef(
        name="fake", languages=("python",), extensions=(".py",),
        command=(sys.executable, "-c", "raise SystemExit(3)"),
        install_remedy="install the fake adapter")
    _test_file(tmp_path)
    note = debug_note_for_command(
        "pytest -q", FAILED_OUTPUT, root=tmp_path,
        client_factory=_factory_for(broken))
    assert "could not be re-run under the debugger" in note


def test_execute_tool_failed_pytest_appends_the_loop_note(
        tmp_path, monkeypatch):
    from mythic_agent.agents.tools import execute_tool
    from mythic_agent.core.policy import ToolPolicy
    monkeypatch.setattr(
        dap.importlib.util, "find_spec", lambda name: None)
    _test_file(tmp_path)
    result = execute_tool(
        "run_command",
        {"command": f"{sys.executable} -m pytest test_bad.py -q "
                    f"-p no:cacheprovider"},
        tmp_path, policy=ToolPolicy("trusted"))
    assert "exit code: 1" in result
    assert "Debugger in the loop" in result
    assert "not-installed" in result


def test_execute_tool_failed_pytest_loop_off_stays_plain(tmp_path):
    from mythic_agent.agents.tools import execute_tool
    from mythic_agent.core.policy import ToolPolicy

    class _Agent:
        name = "Primary"
        project_root = tmp_path
        config = {"debugger_in_loop": False}
        tool_policy = ToolPolicy("trusted")
        _cancel = None

    _test_file(tmp_path)
    result = execute_tool(
        "run_command",
        {"command": f"{sys.executable} -m pytest test_bad.py -q "
                    f"-p no:cacheprovider"},
        tmp_path, agent=_Agent(), policy=ToolPolicy("trusted"))
    assert "exit code: 1" in result
    assert "Debugger in the loop" not in result


# ---------------------------------------------------------------- surfaces

def test_parse_debug_loop_args():
    assert parse_debug_loop_args("") == {"action": "show"}
    assert parse_debug_loop_args("show") == {"action": "show"}
    parsed = parse_debug_loop_args("tests/test_a.py::test_b break 5 break 9")
    assert parsed == {"action": "run", "test": "tests/test_a.py::test_b",
                      "breakpoints": [5, 9]}
    for bad in ("show extra", "notes.txt", "t.py break", "t.py break x",
                "t.py break 0", "t.py wat 3"):
        with pytest.raises(ValueError):
            parse_debug_loop_args(bad)


def test_format_board_and_report(tmp_path, monkeypatch):
    monkeypatch.setattr(
        dap.importlib.util, "find_spec", lambda name: None)
    board = format_debug_loop_board(
        {"adapters": dap.discover_adapters(),
         "plain_explanation": loop.PLAIN_EXPLANATION})
    assert "debugpy" in board and "NOT INSTALLED" in board
    _test_file(tmp_path)
    report = debug_failing_test("test_bad.py::test_fails", root=tmp_path)
    text = format_debug_loop_report(
        {"report": report.record(),
         "plain_explanation": loop.PLAIN_EXPLANATION})
    assert "Debugger in the loop" in text and "not-installed" in text


def test_agent_and_terminal_surfaces(tmp_path, monkeypatch):
    from mythic_agent.agents.llm import Agent
    from mythic_agent.terminal import _slash
    monkeypatch.setattr(
        dap.importlib.util, "find_spec", lambda name: None)
    agent = Agent.__new__(Agent)
    agent.project_root = tmp_path
    agent.config = {}
    _test_file(tmp_path)
    status = agent.debug_loop("test_bad.py::test_fails", breakpoints=[2])
    assert status["report"]["status"] == "not-installed"
    with pytest.raises(ValueError):
        agent.debug_loop("../outside.py::test_x")
    handled, _, text = _slash(agent, "/debugloop")
    assert handled and "Debug adapters:" in text
    handled, _, text = _slash(agent, "/debugloop test_bad.py::test_fails")
    assert handled and "not-installed" in text
    handled, _, text = _slash(agent, "/debugloop notes.txt")
    assert handled and "Usage" in text


def test_agent_debug_loop_respects_the_switches(tmp_path):
    from mythic_agent.agents.llm import Agent
    agent = Agent.__new__(Agent)
    agent.project_root = tmp_path
    _test_file(tmp_path)
    agent.config = {"debugger_in_loop": False}
    assert agent.debug_loop("test_bad.py::test_fails")[
        "report"]["status"] == "disabled"
    agent.config = {"debugger": False}
    assert agent.debug_loop("test_bad.py::test_fails")[
        "report"]["status"] == "disabled"


def test_config_catalogue_carries_the_loop_setting():
    from mythic_agent.core.config_catalog import load_catalog
    catalog = load_catalog()
    rows = [s for s in catalog.settings if s.name == "debugger_in_loop"]
    assert len(rows) == 1
    assert rows[0].id == "S-44"


def test_render_markdown_names_the_slice():
    text = loop.render_markdown()
    assert "M-055" in text and "/debugloop" in text
    assert "not-installed" in text
