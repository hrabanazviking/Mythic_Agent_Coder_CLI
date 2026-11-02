"""M-054 — The Debugger (DAP).

TIER: integration

Breakpoints, step, continue, variable inspection, and
exception stops for Python first (debugpy), on the
DAP-general road. Absence is never a session: debugpy is
not installed in this environment, so a real run reports
not-installed with its remedy, and live proof rides a
fake DAP adapter subprocess speaking the real protocol
(Content-Length framing, initialize -> launch ->
setBreakpoints -> setExceptionBreakpoints ->
configurationDone -> stopped -> threads/stackTrace/
scopes/variables -> steps -> disconnect), with the
command order proven from the adapter's own log.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mythic_agent.tools import debugger as dap
from mythic_agent.tools.debugger import (
    ADAPTERS, DEBUGGER_SLICE, AdapterDef, Breakpoint, DAPClient,
    DAPError, Scope, StackFrame, StoppedInfo, Variable,
    adapter_for_language, adapter_for_path, discover_adapters,
    enabled_from_config, encode_message, format_debug_board,
    format_debug_report, parse_debug_args, read_message,
    run_debug_session,
)

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
    if mode == "die":
        return
    stream_in = sys.stdin.buffer
    stream_out = sys.stdout.buffer
    log = open(log_path, "a", encoding="utf-8")
    state = {"line": 1, "program": ""}
    while True:
        message = read_message(stream_in)
        if message is None:
            return
        if message.get("type") == "response":
            log.write("client-response:%s\n" % message.get("success"))
            log.flush()
            continue
        command = message.get("command")
        if command:
            log.write(command + "\n")
            log.flush()
        args = message.get("arguments") or {}
        if mode == "silent":
            continue
        if command == "initialize":
            if mode == "refuse":
                send(stream_out, {
                    "seq": 0, "type": "response",
                    "request_seq": message["seq"],
                    "command": "initialize", "success": False,
                    "message": "boom init"})
                continue
            respond(stream_out, message,
                    {"supportsConfigurationDoneRequest": True})
        elif command == "launch":
            state["program"] = args.get("program", "")
            if "ask_first" in state["program"]:
                send(stream_out, {"seq": 99, "type": "request",
                                  "command": "runInTerminal",
                                  "arguments": {}})
                answer = read_message(stream_in)
                log.write("client-response:%s\n" % (
                    answer.get("success") if answer else None))
                log.write("answered-runInTerminal\n")
                log.flush()
            respond(stream_out, message)
        elif command == "attach":
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
                      {"reason": "breakpoint", "threadId": 1,
                       "allThreadsStopped": True,
                       "hitBreakpointIds": [1]})
        elif command == "threads":
            respond(stream_out, message,
                    {"threads": [{"id": 1, "name": "main"}]})
        elif command == "stackTrace":
            respond(stream_out, message, {"stackFrames": [
                {"id": 100, "name": "main",
                 "source": {"path": state["program"]},
                 "line": state["line"], "column": 1},
                {"id": 101, "name": "helper",
                 "source": {"path": state["program"]},
                 "line": 3, "column": 5}], "totalFrames": 2})
        elif command == "scopes":
            respond(stream_out, message, {"scopes": [
                {"name": "Locals", "variablesReference": 500,
                 "expensive": False},
                {"name": "Globals", "variablesReference": 501,
                 "expensive": False}]})
        elif command == "variables":
            ref = args.get("variablesReference")
            table = {
                500: [{"name": "x", "value": "41", "type": "int",
                       "variablesReference": 0, "evaluateName": "x"},
                      {"name": "items", "value": "[1, 2]",
                       "type": "list", "variablesReference": 600,
                       "evaluateName": "items"}],
                600: [{"name": "0", "value": "1", "type": "int",
                       "variablesReference": 0}],
                501: [{"name": "__name__", "value": "'__main__'",
                       "type": "str", "variablesReference": 0}],
            }
            respond(stream_out, message,
                    {"variables": table.get(ref, [])})
        elif command in ("next", "stepIn", "stepOut"):
            state["line"] += 1
            respond(stream_out, message)
            event(stream_out, "stopped",
                  {"reason": "step", "threadId": 1,
                   "allThreadsStopped": True})
        elif command == "continue":
            respond(stream_out, message, {"allThreadsContinued": True})
            event(stream_out, "terminated", {"restart": False})
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


def _program(tmp_path, name="buggy.py"):
    target = tmp_path / name
    target.write_text("x = 41\nprint(x + 1)\n", encoding="utf-8")
    return target


# ---------------------------------------------------------------- catalogue

def test_slice_and_catalogue():
    assert DEBUGGER_SLICE == "M-054"
    assert [a.name for a in ADAPTERS] == ["debugpy"]
    assert adapter_for_language("python").name == "debugpy"
    assert adapter_for_language("Python").name == "debugpy"
    assert adapter_for_path("a.py").name == "debugpy"
    assert adapter_for_language("mojo") is None
    assert adapter_for_path("a.rs") is None


def test_discovery_reports_debugpy_absent_here(monkeypatch):
    monkeypatch.setattr(
        dap.importlib.util, "find_spec", lambda name: None)
    found = discover_adapters()
    assert found[0]["installed"] is False
    assert "pip install debugpy" in found[0]["install_remedy"]


def test_discovery_reports_installed_when_the_package_is_found(monkeypatch):
    monkeypatch.setattr(
        dap.importlib.util, "find_spec", lambda name: object())
    found = discover_adapters()
    assert found[0]["installed"] is True
    assert found[0]["install_remedy"] is None


# ---------------------------------------------------------------- records

def test_breakpoint_record_from_dap():
    bp = Breakpoint.from_dap(
        {"id": 7, "verified": True, "line": 5,
         "source": {"path": "/x/a.py"}}, path="/fallback.py")
    assert (bp.id, bp.verified, bp.line, bp.path) == (7, True, 5, "/x/a.py")
    assert "verified" in bp.one_line()
    with pytest.raises(ValueError):
        Breakpoint(line=0)


def test_stopped_frame_scope_variable_records():
    stopped = StoppedInfo.from_event(
        {"reason": "exception", "threadId": 3, "text": "ValueError: boom",
         "hitBreakpointIds": []})
    assert stopped.reason == "exception" and stopped.thread_id == 3
    assert "ValueError" in stopped.one_line()
    frame = StackFrame.from_dap(
        {"id": 1, "name": "f", "source": {"path": "/x/a.py"},
         "line": 9, "column": 2})
    assert frame.one_line() == "f at /x/a.py:9:2"
    scope = Scope.from_dap({"name": "Locals", "variablesReference": 5})
    assert scope.variables == [] and scope.variables_reference == 5
    var = Variable.from_dap({"name": "x", "value": "1", "type": "int",
                             "variablesReference": 0})
    assert var.one_line() == "x: int = 1"
    with pytest.raises(DAPError):
        StackFrame.from_dap(["not", "a", "dict"])


def test_framing_round_trips_and_refuses_bad_frames():
    import io
    blob = encode_message({"seq": 1, "type": "request",
                           "command": "initialize"})
    assert read_message(io.BytesIO(blob))["command"] == "initialize"
    with pytest.raises(DAPError, match="Content-Length"):
        read_message(io.BytesIO(b"X-Other: 1\r\n\r\n{}"))
    body = b"[1, 2]"
    frame = b"Content-Length: %d\r\n\r\n" % len(body) + body
    with pytest.raises(DAPError, match="not an object"):
        read_message(io.BytesIO(frame))
    assert read_message(io.BytesIO(b"")) is None


# ---------------------------------------------------------------- honest absence

def test_run_reports_not_installed_without_a_factory(tmp_path, monkeypatch):
    monkeypatch.setattr(
        dap.importlib.util, "find_spec", lambda name: None)
    target = _program(tmp_path)
    report = run_debug_session(target, root=tmp_path, breakpoints=[1])
    assert report.status == "not-installed"
    assert report.adapter == "debugpy"
    assert "pip install debugpy" in report.note
    assert report.frames == [] and report.breakpoints == []


def test_run_reports_no_adapter_for_an_unknown_language(tmp_path):
    target = tmp_path / "main.rs"
    target.write_text("fn main() {}\n", encoding="utf-8")
    report = run_debug_session(target, root=tmp_path)
    assert report.status == "no-adapter" and report.adapter is None


def test_run_reports_disabled_when_the_switch_is_off(tmp_path):
    target = _program(tmp_path)
    report = run_debug_session(target, root=tmp_path, enabled=False)
    assert report.status == "disabled"
    assert enabled_from_config(None) is True
    assert enabled_from_config({"debugger": False}) is False
    assert enabled_from_config({"debugger": True}) is True


# ---------------------------------------------------------------- live proof

def test_live_session_breakpoint_inspection(tmp_path, fake_adapter):
    adapter, log = fake_adapter
    target = _program(tmp_path)
    report = run_debug_session(
        target, root=tmp_path, breakpoints=[2], stop_on_exception=True,
        client_factory=_factory_for(adapter))
    assert report.status == "ok"
    assert report.breakpoints[0].verified is True
    assert report.breakpoints[0].line == 2
    assert report.stopped is not None
    assert report.stopped.reason == "breakpoint"
    assert report.threads == [{"id": 1, "name": "main"}]
    assert [f.name for f in report.frames] == ["main", "helper"]
    assert report.frames[0].line == 2
    locals_scope = report.scopes[0]
    assert locals_scope.name == "Locals"
    by_name = {v.name: v for v in locals_scope.variables}
    assert by_name["x"].value == "41" and by_name["x"].type == "int"
    # One level of nested variables is expanded as children.
    assert by_name["items"].children[0].name == "0"
    assert by_name["items"].children[0].value == "1"
    assert any(e["event"] == "stopped" for e in report.events)
    order = log.read_text(encoding="utf-8").splitlines()
    assert order[:7] == ["initialize", "launch", "setBreakpoints",
                         "setExceptionBreakpoints", "filters:all",
                         "configurationDone", "threads"]
    assert "stackTrace" in order and "scopes" in order
    assert "variables" in order and order[-1] == "disconnect"


def test_live_session_step_then_inspect_again(tmp_path, fake_adapter):
    adapter, _log = fake_adapter
    target = _program(tmp_path)
    report = run_debug_session(
        target, root=tmp_path, breakpoints=[2], steps=["next"],
        client_factory=_factory_for(adapter))
    assert report.status == "ok"
    assert report.steps_performed == ["next"]
    assert report.stopped is not None and report.stopped.reason == "step"
    assert report.frames[0].line == 3  # the step moved the top frame


def test_live_session_continue_runs_to_termination(tmp_path, fake_adapter):
    adapter, _log = fake_adapter
    target = _program(tmp_path)
    report = run_debug_session(
        target, root=tmp_path, breakpoints=[1], steps=["continue"],
        client_factory=_factory_for(adapter))
    assert report.terminated is True
    assert report.steps_performed == ["continue"]
    assert "ended during the asked steps" in report.note


def test_live_session_program_ending_before_a_stop(
        tmp_path, fake_adapter, monkeypatch):
    adapter, _log = fake_adapter
    monkeypatch.setenv("FAKE_DAP_MODE", "exit-early")
    target = _program(tmp_path)
    report = run_debug_session(
        target, root=tmp_path, breakpoints=[1],
        client_factory=_factory_for(adapter))
    assert report.status == "terminated" and report.terminated is True
    assert report.frames == []


def test_adapter_to_client_request_is_answered_honestly(
        tmp_path, fake_adapter):
    adapter, log = fake_adapter
    target = _program(tmp_path, name="ask_first.py")
    report = run_debug_session(
        target, root=tmp_path, breakpoints=[1],
        client_factory=_factory_for(adapter))
    assert report.status == "ok"
    entries = log.read_text(encoding="utf-8").splitlines()
    assert "answered-runInTerminal" in entries
    assert "client-response:False" in entries


def test_refusing_adapter_raises_in_its_own_words(
        tmp_path, fake_adapter, monkeypatch):
    adapter, _log = fake_adapter
    monkeypatch.setenv("FAKE_DAP_MODE", "refuse")
    client = DAPClient(adapter, tmp_path, timeout=5.0)
    with pytest.raises(DAPError, match="boom init"):
        client.start()
    client.close()


def test_dying_adapter_raises_in_its_own_words(tmp_path, fake_adapter,
                                              monkeypatch):
    adapter, _log = fake_adapter
    monkeypatch.setenv("FAKE_DAP_MODE", "die")
    client = DAPClient(adapter, tmp_path, timeout=5.0)
    with pytest.raises(DAPError):
        client.start()
    client.close()


def test_client_validates_breakpoints_steps_and_attach(tmp_path, fake_adapter):
    adapter, _log = fake_adapter
    client = DAPClient(adapter, tmp_path, timeout=5.0)
    client.start()
    try:
        with pytest.raises(ValueError):
            client.set_breakpoints("buggy.py", [0])
        with pytest.raises(ValueError):
            client.set_exception_breakpoints(["everything"])
        with pytest.raises(ValueError):
            client.step("teleport", 1)
        with pytest.raises(ValueError):
            client.attach()
    finally:
        client.close()


# ---------------------------------------------------------------- surfaces

def test_parse_debug_args():
    assert parse_debug_args("") == {"action": "show"}
    assert parse_debug_args("show") == {"action": "show"}
    parsed = parse_debug_args(
        "run buggy.py break 5 break 12 exceptions then next then continue")
    assert parsed == {"action": "run", "program": "buggy.py",
                      "breakpoints": [5, 12], "steps": ["next", "continue"],
                      "stop_on_exception": True}
    for bad in ("show extra", "run", "run a.py break", "run a.py break x",
                "run a.py break 0", "run a.py then fly", "run a.py wat",
                "dance a.py"):
        with pytest.raises(ValueError):
            parse_debug_args(bad)


def test_format_board_and_report():
    board = format_debug_board(
        {"adapters": discover_adapters(),
         "plain_explanation": dap.PLAIN_EXPLANATION})
    assert "Debug adapters:" in board and "debugpy" in board
    report = run_debug_session(
        Path("nowhere.py"), root=REPO_ROOT)
    # nowhere.py does not exist, but absence of the adapter
    # is settled before any launch is attempted.
    assert report.status in ("not-installed", "no-adapter")
    text = format_debug_report(
        {"report": report.record(),
         "plain_explanation": dap.PLAIN_EXPLANATION})
    assert "Debug run of" in text


def test_agent_surfaces(tmp_path, monkeypatch):
    from mythic_agent.agents.llm import Agent
    monkeypatch.setattr(
        dap.importlib.util, "find_spec", lambda name: None)
    agent = Agent.__new__(Agent)
    agent.project_root = tmp_path
    agent.config = {}
    _program(tmp_path)
    board = agent.debugger_status()
    assert board["adapters"][0]["name"] == "debugpy"
    status = agent.debug_run("buggy.py", breakpoints=[1])
    assert status["report"]["status"] == "not-installed"
    with pytest.raises(ValueError):
        agent.debug_run("../outside.py")


def test_agent_debug_run_respects_the_switch(tmp_path):
    from mythic_agent.agents.llm import Agent
    agent = Agent.__new__(Agent)
    agent.project_root = tmp_path
    agent.config = {"debugger": False}
    _program(tmp_path)
    status = agent.debug_run("buggy.py")
    assert status["report"]["status"] == "disabled"


def test_terminal_debug_command(tmp_path, monkeypatch):
    from mythic_agent.agents.llm import Agent
    from mythic_agent.terminal import _slash
    monkeypatch.setattr(
        dap.importlib.util, "find_spec", lambda name: None)
    agent = Agent.__new__(Agent)
    agent.project_root = tmp_path
    agent.config = {}
    _program(tmp_path)
    handled, _, text = _slash(agent, "/debug")
    assert handled and "Debug adapters:" in text
    handled, _, text = _slash(agent, "/debug run buggy.py break 1")
    assert handled and "not-installed" in text
    handled, _, text = _slash(agent, "/debug dance")
    assert handled and "Usage" in text


def test_gap_audit_debugger_row_names_this_module():
    from mythic_agent.core.gap_audit import load_audit
    audit = load_audit()
    rows = [r for r in audit.rows if r.feature == "debugger-dap"]
    assert len(rows) == 1
    assert rows[0].owning_module == "mythic_agent/tools/debugger.py"
    assert (REPO_ROOT / rows[0].owning_module).is_file()


def test_render_markdown_names_the_slice():
    text = dap.render_markdown()
    assert "M-054" in text and "debugpy" in text
    assert "/debug" in text
