"""M-070 — Part III gate.

TIER: integration

The Part III gate (``mythic_agent/data/part3_gate.yaml`` +
``mythic_agent.core.part3_gate``): on benchmark-pack-style
throwaway repos, a cross-file rename, a structural codemod,
and a debugger-caught bug, all completed with Part III's new
senses, evidence banked against the M-007 baseline.

These tests do not take the record's word for any of it:

* the gate record loads and validates, its slices are
  M-043..M-069 with titles matching the roadmap data, and
  its baseline matches the live M-007 freeze,
* the rename is RE-PROVEN LIVE: the exercise repo's
  ``compute_total`` is renamed across both files through
  M-051's LSP rename road against a fake language server
  speaking the real protocol, M-046's symbol graph proves
  the cross-file reference before and its absence after,
  and the hidden grading tests pass in full,
* the codemod is RE-PROVEN LIVE through M-048's structural
  plan/apply road (per-site previews, journal application),
  and its hidden grading tests pass in full,
* the debug catch is RE-PROVEN LIVE through M-055's
  debugger-in-the-loop against a fake DAP adapter speaking
  the real protocol: the exception stop's frame and the
  local ``x = 41`` are the catching evidence,
* the M-008 pack itself is exercised with the new senses:
  B-01 materialised, its symbol graph naming ``paginate``,
* the honesty bounds hold: no live language server and no
  real debugpy session is claimed anywhere in the record.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

from mythic_agent.context.symbol_graph import build_symbol_graph
from mythic_agent.core.baseline_freeze import load_freeze
from mythic_agent.core.benchmark_tasks import load_pack, materialize
from mythic_agent.core.part3_gate import (
    EXERCISE_IDS,
    GATE_SLICE,
    Gate,
    grade_exercise,
    load_gate,
    materialise_exercise,
    render_markdown,
    validate_gate,
    verify_rename,
)
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.validation import ValidationError
from mythic_agent.resources import load_resource


@pytest.fixture(scope="module")
def gate() -> Gate:
    return load_gate()


def test_shipped_gate_loads_and_validates(gate):
    assert isinstance(gate, Gate)
    assert validate_gate(load_resource("part3_gate.yaml")) == []
    assert gate.gate_slice == GATE_SLICE == "M-070"
    assert gate.part == 3
    assert gate.part_title == "Code Intelligence"
    assert gate.verdict == "PASS"


def test_slices_cover_part3_in_order(gate):
    assert gate.slice_ids() == tuple(f"M-{n:03d}" for n in range(43, 70))
    road = load_roadmap()
    for ref in gate.slices:
        assert road.slice(ref.slice).title == ref.title, ref.slice
    assert road.part(3).title == gate.part_title
    done_ids = [s.id for s in road.done()]
    assert [f"M-{n:03d}" for n in range(43, 70)] == [
        d for d in done_ids if "M-043" <= d <= "M-069"]
    nxt = road.next_slice()
    assert nxt is not None
    assert nxt.id == "M-070" or nxt.part >= 4


def test_baseline_matches_the_live_freeze(gate):
    freeze = load_freeze()
    assert gate.baseline_resource == "baseline_freeze.yaml"
    assert gate.baseline_totals() == freeze.suite_totals() == \
        (1467, 1464, 2, 1)


def test_exercises_shape_and_honesty(gate):
    assert gate.exercise_ids() == EXERCISE_IDS == \
        ("rename", "codemod", "debug")
    assert len(gate.completed_exercises()) == 3
    kinds = {e.id: e.evidence_kind for e in gate.exercises}
    assert kinds == {
        "rename": "fake-server-measured",
        "codemod": "structural-measured",
        "debug": "fake-adapter-measured"}
    for exercise in gate.exercises:
        assert exercise.status == "completed"
        assert exercise.evidence
        assert exercise.seed_paths()
        for sid in exercise.owning_slices:
            assert "M-043" <= sid <= "M-069"


def test_render_markdown_reports_the_gate(gate):
    text = render_markdown(gate)
    assert "PASS" in text
    assert "M-043..M-069" in text
    assert "1467 collected" in text
    for exercise_id in EXERCISE_IDS:
        assert gate.exercise(exercise_id).title in text


def test_benchmark_pack_under_the_new_senses(tmp_path):
    pack = load_pack()
    task = next(t for t in pack.tasks if t.id == "B-01")
    root = materialize(task, tmp_path / "b01", solved=False)
    graph = build_symbol_graph(root)
    defs = graph.definitions_named("paginate")
    assert len(defs) == 1 and defs[0].path == "paging.py"


# ----------------------------------------------------------------------
# Exercise 1 — the cross-file rename, re-proven live (M-051 road)
# ----------------------------------------------------------------------

FAKE_LSP_SERVER = r'''
import json
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
    return json.loads(stream.read(length).decode("utf-8"))


def send(stream, message):
    body = json.dumps(message).encode("utf-8")
    stream.write(b"Content-Length: %d\r\n\r\n" % len(body) + body)
    stream.flush()


def edit(line, start, end, text):
    return {"range": {
        "start": {"line": line, "character": start},
        "end": {"line": line, "character": end}}, "newText": text}


def main():
    stream_in, stream_out = sys.stdin.buffer, sys.stdout.buffer
    while True:
        message = read_message(stream_in)
        if message is None:
            return
        method = message.get("method")
        if method == "initialize":
            send(stream_out, {"jsonrpc": "2.0", "id": message["id"],
                              "result": {"capabilities":
                                         {"textDocumentSync": 1},
                                         "serverInfo":
                                         {"name": "fake-ls",
                                          "version": "1.0"}}})
        elif method == "textDocument/didOpen":
            doc = message["params"]["textDocument"]
            send(stream_out, {
                "jsonrpc": "2.0",
                "method": "textDocument/publishDiagnostics",
                "params": {"uri": doc["uri"], "diagnostics": []}})
        elif method == "textDocument/prepareRename":
            pos = message["params"]["position"]
            send(stream_out, {"jsonrpc": "2.0", "id": message["id"],
                              "result": {"range": {
                                  "start": {"line": pos["line"],
                                            "character": pos["character"]},
                                  "end": {"line": pos["line"],
                                          "character": pos["character"]
                                          + 13}},
                                  "placeholder": "compute_total"}})
        elif method == "textDocument/rename":
            params = message["params"]
            uri = params["textDocument"]["uri"]
            new_name = params["newName"]
            other = uri.rsplit("/", 1)[0] + (
                "/main.py" if uri.endswith("/helpers.py")
                else "/helpers.py")
            if uri.endswith("/helpers.py"):
                mine = [edit(0, 4, 17, new_name), edit(4, 8, 21, new_name)]
                theirs = [edit(0, 20, 33, new_name),
                          edit(2, 9, 22, new_name)]
            else:
                mine = [edit(0, 20, 33, new_name),
                        edit(2, 9, 22, new_name)]
                theirs = [edit(0, 4, 17, new_name),
                          edit(4, 8, 21, new_name)]
            send(stream_out, {"jsonrpc": "2.0", "id": message["id"],
                              "result": {"changes":
                                         {uri: mine, other: theirs}}})
        elif method == "shutdown":
            send(stream_out, {"jsonrpc": "2.0", "id": message["id"],
                              "result": None})
        elif method == "exit":
            return


main()
'''


@pytest.fixture()
def fake_lsp(tmp_path):
    from mythic_agent.integrations.lsp import LSPClient, ServerDef
    script = tmp_path / "fake_ls_gate.py"
    script.write_text(FAKE_LSP_SERVER, encoding="utf-8")
    server = ServerDef(
        name="fake", languages=("python",), extensions=(".py",),
        language_ids={"python": "python"},
        command=(sys.executable, str(script)),
        install_remedy="install the fake server")
    return lambda srv, root: LSPClient(server, root)


def test_rename_exercise_reproven_live(gate, tmp_path, fake_lsp):
    from mythic_agent.integrations.lsp import rename_for_file
    exercise = gate.exercise("rename")
    root = materialise_exercise(exercise, tmp_path / "rename")
    # The symbol graph proves the cross-file reach first.
    before = build_symbol_graph(root)
    assert len(before.definitions_named("compute_total")) == 1
    assert before.definitions_named("compute_total")[0].path == \
        "helpers.py"
    assert any(r.path == "main.py"
               for r in before.references_to("compute_total"))
    assert before.file_edges()["main.py"] == ("helpers.py",)
    # The seed alone does not satisfy the grading tests.
    assert grade_exercise(exercise, root) != (3, 3)
    report = rename_for_file(
        "helpers.py", 1, 5, "summarise_total", root=root, apply=True,
        client_factory=fake_lsp)
    assert report.status == "ok", report.note
    assert report.plan is not None
    assert sorted(Path(f.path).name for f in report.plan.files) == \
        ["helpers.py", "main.py"]
    assert sum(len(f.edits) for f in report.plan.files) == \
        exercise.details["sites"] == 4
    assert verify_rename(exercise, root) == []
    after = build_symbol_graph(root)
    assert len(after.definitions_named("summarise_total")) == 1
    assert after.definitions_named("compute_total") == ()
    assert grade_exercise(exercise, root) == (3, 3)


# ----------------------------------------------------------------------
# Exercise 2 — the structural codemod, re-proven live (M-048 road)
# ----------------------------------------------------------------------

def test_codemod_exercise_reproven_live(gate, tmp_path):
    from mythic_agent.tools.structural_rewrite import (
        apply_rewrite, plan_rewrite)
    exercise = gate.exercise("codemod")
    root = materialise_exercise(exercise, tmp_path / "codemod")
    assert grade_exercise(exercise, root) != (2, 2)
    plan = plan_rewrite(
        root, exercise.details["pattern"],
        exercise.details["replacement"], "python")
    planned = [s for s in plan.sites if s.status == "planned"]
    assert len(planned) == exercise.details["sites"] == 2
    assert all(s.diff for s in planned)  # every site previewed
    # Planning alone writes nothing.
    assert "legacy_add(1, 2)" in \
        (root / "calc.py").read_text(encoding="utf-8")
    result = apply_rewrite(root, plan)
    assert [o.status for o in result.outcomes] == ["applied"]
    assert grade_exercise(exercise, root) == (2, 2)


# ----------------------------------------------------------------------
# Exercise 3 — the debugger-caught bug, re-proven live (M-055 road)
# ----------------------------------------------------------------------

FAKE_DAP_ADAPTER = r'''
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
    return json.loads(stream.read(length).decode("utf-8"))


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
    stream_in, stream_out = sys.stdin.buffer, sys.stdout.buffer
    state = {"node": "", "line": 3}
    while True:
        message = read_message(stream_in)
        if message is None:
            return
        if message.get("type") == "response":
            continue
        command = message.get("command")
        if not command:
            continue
        args = message.get("arguments") or {}
        if command == "initialize":
            respond(stream_out, message,
                    {"supportsConfigurationDoneRequest": True})
        elif command == "launch":
            state["node"] = (args.get("args") or [""])[0]
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
            respond(stream_out, message, {"breakpoints": []})
        elif command == "configurationDone":
            respond(stream_out, message)
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
            table = {500: [{"name": "x", "value": "41", "type": "int",
                            "variablesReference": 0,
                            "evaluateName": "x"}]}
            respond(stream_out, message,
                    {"variables": table.get(
                        args.get("variablesReference"), [])})
        elif command == "disconnect":
            respond(stream_out, message)
            return


main()
'''


@pytest.fixture()
def fake_dap(tmp_path):
    from mythic_agent.tools.debugger import AdapterDef, DAPClient
    script = tmp_path / "fake_adapter_gate.py"
    script.write_text(FAKE_DAP_ADAPTER, encoding="utf-8")
    adapter = AdapterDef(
        name="fake", languages=("python",), extensions=(".py",),
        command=(sys.executable, str(script)),
        install_remedy="install the fake adapter")
    return lambda adp, root: DAPClient(adapter, root, timeout=5.0)


def test_debug_exercise_reproven_live(gate, tmp_path, fake_dap):
    from mythic_agent.tools.debug_loop import debug_failing_test
    exercise = gate.exercise("debug")
    root = materialise_exercise(exercise, tmp_path / "debug")
    report = debug_failing_test(
        exercise.details["test_node"], root=root,
        breakpoints=[exercise.details["frame_line"]],
        client_factory=fake_dap)
    assert report.status == "evidence", report.note
    debug = report.debug
    assert debug is not None and debug.stopped is not None
    assert debug.stopped.reason == exercise.details["stopped_reason"]
    assert "AssertionError" in debug.stopped.text
    assert debug.frames[0].name == "test_fails"
    assert debug.frames[0].line == exercise.details["frame_line"] == 3
    variables = debug.scopes[0].variables
    assert [(v.name, v.value) for v in variables] == [
        (exercise.details["local_name"],
         exercise.details["local_value"])] == [("x", "41")]


# ----------------------------------------------------------------------
# Validator honesty
# ----------------------------------------------------------------------

def _mutated(mutator):
    data = copy.deepcopy(load_resource("part3_gate.yaml"))
    mutator(data)
    return data


def test_validator_rejects_a_non_pass_verdict():
    data = _mutated(lambda d: d.update(verdict="FAIL"))
    assert any("PASS" in p for p in validate_gate(data))


def test_validator_rejects_a_missing_slice():
    data = _mutated(lambda d: d["slices"].pop())
    assert any("27" in p for p in validate_gate(data))


def test_validator_rejects_an_uncompleted_exercise():
    def spoil(d):
        d["exercises"][1]["status"] = "queued"

    assert any("completed" in p for p in validate_gate(_mutated(spoil)))


def test_validator_rejects_a_live_server_claim():
    def spoil(d):
        d["exercises"][0]["evidence_kind"] = "live-server-measured"

    assert any("evidence_kind" in p for p in validate_gate(_mutated(spoil)))


def test_validator_rejects_broken_baseline_arithmetic():
    def spoil(d):
        d["baseline"]["passed"] = 1

    assert any("arithmetic" in p for p in validate_gate(_mutated(spoil)))


def test_validator_rejects_a_one_file_rename():
    def spoil(d):
        d["exercises"][0]["seed_files"].pop()

    assert any("rename" in p for p in validate_gate(_mutated(spoil)))


def test_load_raises_on_invalid_data():
    with pytest.raises(ValidationError):
        load_gate({"schema": "nope", "slices": [], "exercises": [],
                   "baseline": {}})
