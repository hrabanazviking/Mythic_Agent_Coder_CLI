"""M-051 — LSP client III: rename and code actions.

TIER: integration

Part III (Code Intelligence): a rename propagates through
re-exports and imports by the server's own knowledge,
diffed for approval like any edit, and the server's code
actions are listed and applied the same honest way. These
tests do not take the client's word for any of it:

* prepareRename honesty — a spot the server says cannot
  be renamed (a null answer or a server error) is refused
  plainly in the server's terms, and the rename request
  is never sent for such a spot,
* the WorkspaceEdit becomes a per-file plan (both the
  ``changes`` and ``documentChanges`` shapes; malformed
  edits, resource operations, non-file uris, missing
  files, and overlapping edits all refused plainly),
  carrying a plan-time sha256 per file and per-site and
  per-file unified-diff previews as data,
* application rides only the house EditJournal
  (journal-first, proven by undo), refuses a file whose
  hash changed since the plan whole, and writes nothing
  on a preview,
* code actions come back as plain records — a
  command-only action is reported honestly, its command
  never executed,
* the client speaks prepareRename / rename / codeAction
  to a REAL subprocess fake language server (wire
  positions proven 0-based from the server's own log, the
  rename's newName proven on the wire),
* the end-to-end helpers and the Agent / ``/lsp``
  surfaces report no-server / not-installed as statuses,
  never as a faked rename, and the gap audit's lsp row
  still stays MISSING (its state is pinned to the census
  by the audit's own validator).
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

from mythic_agent.core.gap_audit import load_audit
from mythic_agent.integrations.lsp import (
    COMMAND_NOT_EXECUTED_NOTE,
    LSP_RENAME_SLICE,
    RENAME_PLAIN_EXPLANATION,
    CodeActionRecord,
    LSPClient,
    LSPError,
    PlannedTextEdit,
    RenamePreparation,
    ServerDef,
    apply_workspace_edit_plan,
    code_actions_for_file,
    format_lsp_code_actions,
    format_lsp_rename,
    parse_lsp_args,
    parse_workspace_edit,
    path_to_uri,
    rename_for_file,
)

REPO_ROOT = Path(__file__).resolve().parent.parent

A_SOURCE = (
    "thing = 1\n"
    "def my_func():\n"
    "    return thing\n"
    "\n"
    "y = my_func()\n"
)
B_SOURCE = (
    "from a import my_func\n"
    "z = my_func()\n"
)

FAKE_SERVER = r'''
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
    body = stream.read(length)
    return json.loads(body.decode("utf-8"))


def send(stream, message):
    body = json.dumps(message).encode("utf-8")
    stream.write(b"Content-Length: %d\r\n\r\n" % len(body) + body)
    stream.flush()


def edit(line, start, end, text):
    return {"range": {
        "start": {"line": line, "character": start},
        "end": {"line": line, "character": end}}, "newText": text}


def rename_changes(uri, new_name):
    b_uri = uri.rsplit("/", 1)[0] + "/b.py"
    return {"changes": {
        uri: [edit(1, 4, 11, new_name), edit(4, 4, 11, new_name)],
        b_uri: [edit(0, 14, 21, new_name),
                edit(1, 4, 11, new_name)]}}


def main():
    log_path = sys.argv[1]
    stream_in = sys.stdin.buffer
    stream_out = sys.stdout.buffer
    log = open(log_path, "a", encoding="utf-8")
    while True:
        message = read_message(stream_in)
        if message is None:
            return
        method = message.get("method")
        if method:
            log.write(method + "\n")
            log.flush()
        if method == "initialize":
            caps = message["params"].get("capabilities", {})
            log.write("caps " + json.dumps(caps) + "\n")
            log.flush()
            send(stream_out, {"jsonrpc": "2.0", "id": message["id"],
                              "result": {
                                  "capabilities":
                                      {"textDocumentSync": 1},
                                  "serverInfo": {"name": "fake-ls",
                                                 "version": "1.0"}}})
        elif method == "textDocument/didOpen":
            doc = message["params"]["textDocument"]
            send(stream_out, {
                "jsonrpc": "2.0",
                "method": "textDocument/publishDiagnostics",
                "params": {"uri": doc["uri"], "diagnostics": []}})
        elif method == "textDocument/prepareRename":
            pos = message["params"]["position"]
            log.write("prepareRename %d:%d\n"
                      % (pos["line"], pos["character"]))
            log.flush()
            if (pos["line"], pos["character"]) == (9, 9):
                result = None
                send(stream_out, {"jsonrpc": "2.0",
                                  "id": message["id"],
                                  "result": result})
            elif (pos["line"], pos["character"]) == (8, 8):
                send(stream_out, {"jsonrpc": "2.0",
                                  "id": message["id"],
                                  "error": {
                                      "code": -32803,
                                      "message": "this spot is not "
                                      "renameable, says the "
                                      "server"}})
            else:
                send(stream_out, {"jsonrpc": "2.0",
                                  "id": message["id"],
                                  "result": {
                                      "range": {
                                          "start": {
                                              "line": pos["line"],
                                              "character":
                                                  pos["character"]},
                                          "end": {
                                              "line": pos["line"],
                                              "character":
                                                  pos["character"]
                                                  + 7}},
                                      "placeholder": "my_func"}})
        elif method == "textDocument/rename":
            params = message["params"]
            pos = params["position"]
            uri = params["textDocument"]["uri"]
            new_name = params["newName"]
            log.write("rename %d:%d newName=%s\n"
                      % (pos["line"], pos["character"], new_name))
            log.flush()
            if new_name == "via_docs":
                b_uri = uri.rsplit("/", 1)[0] + "/b.py"
                result = {"documentChanges": [
                    {"textDocument": {"uri": uri, "version": 3},
                     "edits": [edit(1, 4, 11, new_name),
                               edit(4, 4, 11, new_name)]},
                    {"textDocument": {"uri": b_uri, "version": 1},
                     "edits": [edit(0, 14, 21, new_name),
                               edit(1, 4, 11, new_name)]}]}
            else:
                result = rename_changes(uri, new_name)
            send(stream_out, {"jsonrpc": "2.0", "id": message["id"],
                              "result": result})
        elif method == "textDocument/codeAction":
            params = message["params"]
            span = params["range"]
            uri = params["textDocument"]["uri"]
            log.write("codeAction %d:%d-%d:%d\n"
                      % (span["start"]["line"],
                         span["start"]["character"],
                         span["end"]["line"],
                         span["end"]["character"]))
            log.flush()
            if (span["start"]["line"],
                    span["start"]["character"]) == (7, 7):
                result = []
            else:
                result = [
                    {"title": "Fix the call",
                     "kind": "quickfix",
                     "diagnostics": [{
                         "range": {
                             "start": {"line": 0, "character": 0},
                             "end": {"line": 0, "character": 5}},
                         "severity": 2,
                         "message": "thing is shadowed",
                         "source": "fake-ls", "code": "SHADOW"}],
                     "edit": {"changes": {uri: [
                         edit(4, 0, 13,
                              "y = my_func()  # fixed")]}}},
                    {"title": "Organize imports",
                     "kind": "source.organizeImports",
                     "command": {
                         "title": "Organize Imports",
                         "command": "fake.organizeImports",
                         "arguments": ["a.py"]}},
                    {"title": "Restart the fake server",
                     "command": "fake.restart",
                     "arguments": []}]
            send(stream_out, {"jsonrpc": "2.0", "id": message["id"],
                              "result": result})
        elif method == "shutdown":
            send(stream_out, {"jsonrpc": "2.0", "id": message["id"],
                              "result": None})
        elif method == "exit":
            return


main()
'''


@pytest.fixture()
def fake_server(tmp_path):
    script = tmp_path / "fake_ls_rename.py"
    script.write_text(FAKE_SERVER, encoding="utf-8")
    log = tmp_path / "fake_ls_rename.log"
    server = ServerDef(
        name="fake", languages=("python",), extensions=(".py",),
        language_ids={"python": "python"},
        command=(sys.executable, str(script), str(log)),
        install_remedy="install the fake server")
    return server, log


@pytest.fixture()
def target_files(tmp_path):
    a_file = tmp_path / "a.py"
    a_file.write_text(A_SOURCE, encoding="utf-8")
    b_file = tmp_path / "b.py"
    b_file.write_text(B_SOURCE, encoding="utf-8")
    return a_file, b_file


def _no_servers_installed(monkeypatch):
    import mythic_agent.integrations.lsp as lsp_module
    monkeypatch.setattr(lsp_module.shutil, "which", lambda name: None)


def _factory_for(server):
    return lambda srv, root: LSPClient(server, root)


def _edit(line, start, end, text):
    return {"range": {
        "start": {"line": line, "character": start},
        "end": {"line": line, "character": end}}, "newText": text}


# ---------------------------------------------------------------------------
# Plain records: planned edits and preparations
# ---------------------------------------------------------------------------

class TestPlannedTextEdit:
    def test_from_lsp_is_one_based(self, tmp_path):
        found = PlannedTextEdit.from_lsp(
            _edit(1, 4, 11, "better"), "/ws/a.py")
        assert (found.line, found.character) == (2, 5)
        assert (found.end_line, found.end_character) == (2, 12)
        assert found.new_text == "better"
        assert found.record()["new_text"] == "better"
        assert found.one_line() == "/ws/a.py:2:5 -> 'better'"

    @pytest.mark.parametrize("raw", [
        "not-an-edit", 42, None,
        {"newText": "x"},
        {"range": {"start": {"line": 0, "character": 0},
                   "end": {"line": 0, "character": 1}}},
        {"range": {"start": {"line": 0, "character": 0},
                   "end": {"line": 0, "character": 1}},
         "newText": 42},
        {"range": "span", "newText": "x"},
        {"range": {"start": {"line": 0.5, "character": 0},
                   "end": {"line": 0, "character": 1}},
         "newText": "x"},
        {"range": {"start": {"line": -1, "character": 0},
                   "end": {"line": 0, "character": 1}},
         "newText": "x"},
        {"range": {"start": {"line": 0, "character": 5},
                   "end": {"line": 0, "character": 2}},
         "newText": "x"},
        {"range": {"start": {"line": True, "character": 0},
                   "end": {"line": 0, "character": 1}},
         "newText": "x"},
    ])
    def test_malformed_edits_are_refused(self, raw):
        with pytest.raises(LSPError):
            PlannedTextEdit.from_lsp(raw, "/ws/a.py")


class TestRenamePreparation:
    def test_range_and_placeholder(self):
        prep = RenamePreparation.from_lsp_result(
            {"range": {"start": {"line": 1, "character": 4},
                       "end": {"line": 1, "character": 11}},
             "placeholder": "my_func"}, "/ws/a.py")
        assert prep.placeholder == "my_func"
        assert (prep.range.line, prep.range.character) == (2, 5)
        assert prep.record()["placeholder"] == "my_func"

    def test_bare_range(self):
        prep = RenamePreparation.from_lsp_result(
            {"start": {"line": 0, "character": 0},
             "end": {"line": 0, "character": 5}}, "/ws/a.py")
        assert (prep.range.line, prep.range.end_character) == (1, 6)
        assert prep.placeholder == ""

    def test_default_behavior(self):
        prep = RenamePreparation.from_lsp_result(
            {"defaultBehavior": True}, "/ws/a.py")
        assert prep.default_behavior is True
        assert prep.range is None

    @pytest.mark.parametrize("result", [None, {}])
    def test_null_is_a_refusal_in_the_servers_terms(self, result):
        with pytest.raises(LSPError, match="cannot be renamed"):
            RenamePreparation.from_lsp_result(result, "/ws/a.py")

    @pytest.mark.parametrize("result", [
        42, "range", {"placeholder": "x"}, {"range": "span"}])
    def test_malformed_results_are_refused(self, result):
        with pytest.raises(LSPError):
            RenamePreparation.from_lsp_result(result, "/ws/a.py")


# ---------------------------------------------------------------------------
# The WorkspaceEdit plan
# ---------------------------------------------------------------------------

class TestParseWorkspaceEdit:
    def test_changes_shape_plan(self, target_files, tmp_path):
        a_file, b_file = target_files
        raw = {"changes": {
            path_to_uri(a_file): [_edit(1, 4, 11, "better"),
                                  _edit(4, 4, 11, "better")],
            path_to_uri(b_file): [_edit(0, 14, 21, "better")]}}
        plan = parse_workspace_edit(raw, tmp_path)
        assert plan.edit_count == 3
        assert len(plan.files) == 2
        by_path = {f.path: f for f in plan.files}
        a_plan = by_path[str(a_file)]
        assert a_plan.sha256 == hashlib.sha256(
            A_SOURCE.encode("utf-8")).hexdigest()
        assert "def better():" in a_plan.new_content
        assert "y = better()" in a_plan.new_content
        assert "my_func" not in a_plan.new_content
        assert "-def my_func():" in a_plan.diff
        assert "+def better():" in a_plan.diff
        # every site carries its own preview
        for edit in a_plan.edits:
            assert edit.diff.startswith("---")
            assert "better" in edit.diff
        record = plan.record()
        assert record["counts"] == {"files": 2, "edits": 3}
        # planning writes nothing
        assert a_file.read_text(encoding="utf-8") == A_SOURCE

    def test_document_changes_shape_plan(self, target_files, tmp_path):
        a_file, _ = target_files
        raw = {"documentChanges": [
            {"textDocument": {"uri": path_to_uri(a_file),
                              "version": 7},
             "edits": [_edit(0, 0, 5, "stuff")]}]}
        plan = parse_workspace_edit(raw, tmp_path)
        assert plan.edit_count == 1
        assert plan.files[0].new_content.startswith("stuff = 1\n")

    def test_both_shapes_merge(self, target_files, tmp_path):
        a_file, _ = target_files
        raw = {
            "changes": {path_to_uri(a_file): [_edit(0, 0, 5, "stuff")]},
            "documentChanges": [
                {"textDocument": {"uri": path_to_uri(a_file)},
                 "edits": [_edit(4, 4, 11, "better")]}]}
        plan = parse_workspace_edit(raw, tmp_path)
        assert plan.edit_count == 2
        assert plan.files[0].new_content.startswith("stuff = 1\n")
        assert "y = better()" in plan.files[0].new_content

    @pytest.mark.parametrize("raw", [None, {}])
    def test_empty_answers_are_empty_plans(self, raw, tmp_path):
        plan = parse_workspace_edit(raw, tmp_path)
        assert plan.files == []
        assert plan.edit_count == 0

    @pytest.mark.parametrize("raw", [
        "edit", 42, [],
        {"somethingElse": {}},
        {"changes": []},
        {"changes": {"file:///ws/a.py": "not-a-list"}},
        {"documentChanges": {}},
        {"documentChanges": ["entry"]},
        {"documentChanges": [{"textDocument": {"uri": "file:///x"}}]},
        {"documentChanges": [{"kind": "create",
                              "uri": "file:///ws/new.py",
                              "options": {}}]},
        {"changes": {"https://example.com/a.py": [_edit(0, 0, 1, "x")]}},
    ])
    def test_malformed_workspace_edits_are_refused(self, raw, tmp_path):
        with pytest.raises(LSPError):
            parse_workspace_edit(raw, tmp_path)

    def test_missing_file_is_refused(self, tmp_path):
        raw = {"changes": {
            path_to_uri(tmp_path / "ghost.py"): [_edit(0, 0, 1, "x")]}}
        with pytest.raises(LSPError, match="not a file on disk"):
            parse_workspace_edit(raw, tmp_path)

    def test_overlapping_edits_are_refused(self, target_files, tmp_path):
        a_file, _ = target_files
        raw = {"changes": {path_to_uri(a_file): [
            _edit(1, 4, 11, "one"), _edit(1, 8, 15, "two")]}}
        with pytest.raises(LSPError, match="overlapping edits"):
            parse_workspace_edit(raw, tmp_path)

    def test_same_point_insertions_are_refused(self, target_files,
                                                tmp_path):
        a_file, _ = target_files
        raw = {"changes": {path_to_uri(a_file): [
            _edit(0, 5, 5, "x"), _edit(0, 5, 5, "y")]}}
        with pytest.raises(LSPError, match="overlapping edits"):
            parse_workspace_edit(raw, tmp_path)

    def test_adjacent_edits_do_not_overlap(self, target_files, tmp_path):
        a_file, _ = target_files
        raw = {"changes": {path_to_uri(a_file): [
            _edit(0, 0, 5, "stuff"), _edit(0, 8, 9, "2")]}}
        plan = parse_workspace_edit(raw, tmp_path)
        assert plan.files[0].new_content.startswith("stuff = 2\n")

    @pytest.mark.parametrize("bad_edit", [
        _edit(99, 0, 1, "x"), _edit(0, 0, 99, "x")])
    def test_edits_outside_the_file_are_refused(
            self, target_files, tmp_path, bad_edit):
        a_file, _ = target_files
        raw = {"changes": {path_to_uri(a_file): [bad_edit]}}
        with pytest.raises(LSPError):
            parse_workspace_edit(raw, tmp_path)


# ---------------------------------------------------------------------------
# Code action records
# ---------------------------------------------------------------------------

class TestCodeActionRecords:
    def test_full_code_action(self, target_files, tmp_path):
        a_file, _ = target_files
        record = CodeActionRecord.from_lsp({
            "title": "Fix it", "kind": "quickfix",
            "diagnostics": [{
                "range": {"start": {"line": 0, "character": 0},
                          "end": {"line": 0, "character": 5}},
                "severity": 1, "message": "broken",
                "source": "fake"}],
            "edit": {"changes": {path_to_uri(a_file): [
                _edit(0, 0, 5, "stuff")]}},
            "command": {"title": "Run", "command": "fake.run",
                        "arguments": []},
            "disabled": {"reason": "not in this context"},
            "isPreferred": True,
        }, tmp_path, document_uri=path_to_uri(a_file))
        assert record.has_edit and record.has_command
        assert record.diagnostics[0].severity == "error"
        assert record.diagnostics[0].message == "broken"
        assert record.disabled_reason == "not in this context"
        assert record.is_preferred is True
        plain = record.record()
        assert plain["has_edit"] and plain["has_command"]
        assert plain["command_executed"] is False
        assert plain["command_note"] == COMMAND_NOT_EXECUTED_NOTE
        assert plain["edit"]["counts"] == {"files": 1, "edits": 1}
        assert "carries an edit" in record.one_line()

    def test_bare_command(self, tmp_path):
        record = CodeActionRecord.from_lsp(
            {"title": "Restart", "command": "fake.restart",
             "arguments": [1]}, tmp_path)
        assert record.has_command and not record.has_edit
        assert record.kind == ""
        assert record.command["command"] == "fake.restart"
        assert record.command["arguments"] == [1]

    def test_action_with_neither(self, tmp_path):
        record = CodeActionRecord.from_lsp(
            {"title": "Explain", "kind": "refactor"}, tmp_path)
        assert not record.has_edit and not record.has_command
        assert record.record()["command_note"] == ""
        assert "no edit or command" in record.one_line()

    def test_malformed_edit_inside_action_is_refused(
            self, target_files, tmp_path):
        a_file, _ = target_files
        with pytest.raises(LSPError):
            CodeActionRecord.from_lsp({
                "title": "Bad",
                "edit": {"changes": {path_to_uri(a_file): [
                    {"range": "span", "newText": "x"}]}}}, tmp_path)

    def test_non_object_action_is_refused(self, tmp_path):
        with pytest.raises(LSPError, match="not an object"):
            CodeActionRecord.from_lsp("action", tmp_path)


# ---------------------------------------------------------------------------
# Application: journal-first, hash-guarded
# ---------------------------------------------------------------------------

class TestApplyPlan:
    def _plan(self, a_file, tmp_path):
        raw = {"changes": {path_to_uri(a_file): [
            _edit(1, 4, 11, "better"), _edit(4, 4, 11, "better")]}}
        return parse_workspace_edit(raw, tmp_path)

    def test_apply_writes_and_journals(self, agent, target_files):
        from mythic_agent.core.edits import EditJournal

        a_file, _ = target_files
        root = Path(agent.project_root)
        result = apply_workspace_edit_plan(root, self._plan(a_file, root))
        assert [o.status for o in result.outcomes] == ["applied"]
        assert result.outcomes[0].edits_applied == 2
        text = a_file.read_text(encoding="utf-8")
        assert "def better():" in text and "y = better()" in text
        # journal-first proof: the house journal can undo it
        assert "Restored" in EditJournal(root).undo()
        assert a_file.read_text(encoding="utf-8") == A_SOURCE

    def test_stale_file_is_refused_whole(self, agent, target_files):
        a_file, _ = target_files
        root = Path(agent.project_root)
        plan = self._plan(a_file, root)
        a_file.write_text(A_SOURCE + "# touched\n", encoding="utf-8")
        result = apply_workspace_edit_plan(root, plan)
        assert result.outcomes[0].status == "refused-stale"
        assert "changed since the plan" in result.outcomes[0].reason
        assert a_file.read_text(encoding="utf-8") == \
            A_SOURCE + "# touched\n"
        assert result.record()["counts"] == {"refused-stale": 1}

    def test_file_outside_workspace_is_refused(
            self, agent, target_files, tmp_path):
        # the plan was made against another root entirely
        a_file, _ = target_files
        plan = self._plan(a_file, tmp_path)
        other = Path(agent.project_root) / "elsewhere"
        other.mkdir()
        result = apply_workspace_edit_plan(other, plan)
        assert result.outcomes[0].status == \
            "refused-outside-workspace"
        assert a_file.read_text(encoding="utf-8") == A_SOURCE


# ---------------------------------------------------------------------------
# The client against a real subprocess fake server
# ---------------------------------------------------------------------------

class TestClientRenameLive:
    def test_prepare_rename_ok_and_wire_positions(
            self, fake_server, target_files, tmp_path):
        server, log = fake_server
        a_file, _ = target_files
        client = LSPClient(server, tmp_path)
        client.start()
        try:
            prep = client.prepare_rename(a_file, 2, 5)
        finally:
            client.close()
        assert prep.placeholder == "my_func"
        assert (prep.range.line, prep.range.character) == (2, 5)
        assert (prep.range.end_character) == 12
        # the wire saw 0-based positions for house 2,5
        assert "prepareRename 1:4" in log.read_text(encoding="utf-8")

    def test_prepare_rename_null_is_refused(
            self, fake_server, target_files, tmp_path):
        server, _ = fake_server
        a_file, _ = target_files
        client = LSPClient(server, tmp_path)
        client.start()
        try:
            with pytest.raises(LSPError, match="cannot be renamed"):
                client.prepare_rename(a_file, 10, 10)
        finally:
            client.close()

    def test_prepare_rename_server_error_is_refused_in_its_words(
            self, fake_server, target_files, tmp_path):
        server, _ = fake_server
        a_file, _ = target_files
        client = LSPClient(server, tmp_path)
        client.start()
        try:
            with pytest.raises(LSPError,
                               match="this spot is not renameable"):
                client.prepare_rename(a_file, 9, 9)
        finally:
            client.close()

    def test_rename_plan_propagates_across_files(
            self, fake_server, target_files, tmp_path):
        server, log = fake_server
        a_file, b_file = target_files
        client = LSPClient(server, tmp_path)
        client.start()
        try:
            plan = client.rename(a_file, 2, 5, "better_name")
        finally:
            client.close()
        assert plan.edit_count == 4
        by_path = {f.path: f for f in plan.files}
        assert "def better_name():" in by_path[str(a_file)].new_content
        assert "y = better_name()" in by_path[str(a_file)].new_content
        assert "from a import better_name" in \
            by_path[str(b_file)].new_content
        assert "z = better_name()" in by_path[str(b_file)].new_content
        lines = log.read_text(encoding="utf-8")
        assert "rename 1:4 newName=better_name" in lines
        # a plan writes nothing
        assert a_file.read_text(encoding="utf-8") == A_SOURCE
        assert b_file.read_text(encoding="utf-8") == B_SOURCE

    def test_rename_document_changes_shape_live(
            self, fake_server, target_files, tmp_path):
        server, _ = fake_server
        a_file, b_file = target_files
        client = LSPClient(server, tmp_path)
        client.start()
        try:
            plan = client.rename(a_file, 2, 5, "via_docs")
        finally:
            client.close()
        assert plan.edit_count == 4
        by_path = {f.path: f for f in plan.files}
        assert "def via_docs():" in by_path[str(a_file)].new_content
        assert "from a import via_docs" in \
            by_path[str(b_file)].new_content

    def test_rename_of_a_refused_spot_never_sends_the_rename(
            self, fake_server, target_files, tmp_path):
        server, log = fake_server
        a_file, _ = target_files
        client = LSPClient(server, tmp_path)
        client.start()
        try:
            with pytest.raises(LSPError, match="cannot be renamed"):
                client.rename(a_file, 10, 10, "better_name")
        finally:
            client.close()
        methods = log.read_text(encoding="utf-8").splitlines()
        assert not any(line.startswith("rename ")
                       for line in methods)
        assert "prepareRename 9:9" in methods

    @pytest.mark.parametrize("new_name", ["", "   ", "two words"])
    def test_bad_new_names_are_refused(
            self, fake_server, target_files, tmp_path, new_name):
        server, _ = fake_server
        a_file, _ = target_files
        client = LSPClient(server, tmp_path)
        client.start()
        try:
            with pytest.raises(ValueError):
                client.rename(a_file, 2, 5, new_name)
        finally:
            client.close()

    def test_code_actions_live(self, fake_server, target_files,
                               tmp_path):
        server, log = fake_server
        a_file, _ = target_files
        client = LSPClient(server, tmp_path)
        client.start()
        try:
            actions = client.code_actions(a_file, 2, 5)
            empty = client.code_actions(a_file, 8, 8)
        finally:
            client.close()
        assert [a.title for a in actions] == [
            "Fix the call", "Organize imports",
            "Restart the fake server"]
        fix, organize, restart = actions
        assert fix.kind == "quickfix" and fix.has_edit
        assert fix.diagnostics[0].severity == "warning"
        assert fix.diagnostics[0].message == "thing is shadowed"
        assert fix.edit.files[0].new_content.endswith(
            "y = my_func()  # fixed\n")
        assert organize.has_command and not organize.has_edit
        assert restart.has_command and restart.kind == ""
        assert restart.record()["command_executed"] is False
        assert empty == []
        assert "codeAction 1:4-1:4" in log.read_text(encoding="utf-8")

    def test_initialize_declares_rename_and_code_action(
            self, fake_server, tmp_path):
        server, log = fake_server
        client = LSPClient(server, tmp_path)
        client.start()
        client.close()
        caps_line = next(
            line for line in log.read_text(encoding="utf-8").splitlines()
            if line.startswith("caps "))
        caps = json.loads(caps_line[len("caps "):])
        text_document = caps["textDocument"]
        assert text_document["rename"] == {"prepareSupport": True}
        value_set = text_document["codeAction"][
            "codeActionLiteralSupport"]["codeActionKind"]["valueSet"]
        assert "quickfix" in value_set and "refactor" in value_set

    def test_rename_before_start_is_refused(
            self, fake_server, target_files, tmp_path):
        server, _ = fake_server
        a_file, _ = target_files
        client = LSPClient(server, tmp_path)
        with pytest.raises(LSPError, match="not running"):
            client.rename(a_file, 2, 5, "better_name")
        with pytest.raises(LSPError, match="not running"):
            client.code_actions(a_file, 2, 5)


# ---------------------------------------------------------------------------
# The end-to-end helpers: honest absence, preview, apply
# ---------------------------------------------------------------------------

class TestRenameHelpers:
    def test_rename_live_preview(self, fake_server, target_files):
        server, _ = fake_server
        a_file, _ = target_files
        report = rename_for_file(
            a_file, 2, 5, "better_name",
            client_factory=_factory_for(server))
        assert report.status == "ok"
        assert report.action == "rename"
        assert report.server == "fake-ls"
        assert report.preparation.placeholder == "my_func"
        assert report.plan.edit_count == 4
        assert report.applied is False
        assert report.outcomes == []
        record = report.record()
        assert record["plan"]["counts"] == {"files": 2, "edits": 4}
        assert record["preparation"]["placeholder"] == "my_func"
        assert a_file.read_text(encoding="utf-8") == A_SOURCE

    def test_rename_live_apply_journals_both_files(
            self, agent, fake_server, target_files):
        from mythic_agent.core.edits import EditJournal

        server, _ = fake_server
        a_file, b_file = target_files
        root = Path(agent.project_root)
        report = rename_for_file(
            a_file, 2, 5, "better_name", apply=True,
            client_factory=_factory_for(server))
        assert report.applied is True
        assert [o.status for o in report.outcomes] == \
            ["applied", "applied"]
        assert "def better_name():" in \
            a_file.read_text(encoding="utf-8")
        assert "from a import better_name" in \
            b_file.read_text(encoding="utf-8")
        # the last journaled write (b.py) undoes through the
        # house journal — the writes were journal-first
        assert "Restored" in EditJournal(root).undo()
        assert b_file.read_text(encoding="utf-8") == B_SOURCE

    def test_code_actions_live_list_and_apply(
            self, agent, fake_server, target_files):
        server, _ = fake_server
        a_file, _ = target_files
        listed = code_actions_for_file(
            a_file, 2, 5, client_factory=_factory_for(server))
        assert listed.status == "ok"
        assert len(listed.actions) == 3
        assert listed.applied_index is None
        applied = code_actions_for_file(
            a_file, 2, 5, apply_index=0,
            client_factory=_factory_for(server))
        assert applied.applied_index == 0
        assert [o.status for o in applied.outcomes] == ["applied"]
        assert a_file.read_text(encoding="utf-8").endswith(
            "y = my_func()  # fixed\n")

    def test_code_action_command_only_apply_is_honest(
            self, fake_server, target_files):
        server, _ = fake_server
        a_file, _ = target_files
        report = code_actions_for_file(
            a_file, 2, 5, apply_index=1,
            client_factory=_factory_for(server))
        assert report.outcomes == []
        assert "does not execute server commands" in \
            report.apply_note
        assert a_file.read_text(encoding="utf-8") == A_SOURCE

    def test_apply_index_past_the_list_is_refused(
            self, fake_server, target_files):
        server, _ = fake_server
        a_file, _ = target_files
        with pytest.raises(ValueError, match="does not exist"):
            code_actions_for_file(
                a_file, 2, 5, apply_index=7,
                client_factory=_factory_for(server))

    @pytest.mark.parametrize("bad", [-1, "0", True, 1.5])
    def test_bad_apply_index_is_refused(self, target_files, bad):
        a_file, _ = target_files
        with pytest.raises(ValueError, match="apply_index"):
            code_actions_for_file(a_file, 2, 5, apply_index=bad)

    def test_no_catalogued_server(self, tmp_path):
        target = tmp_path / "spell.mojo"
        target.write_text("fn main():\n    pass\n", encoding="utf-8")
        rename = rename_for_file(target, 1, 1, "new_name")
        assert rename.status == "no-server"
        assert rename.plan is None
        assert "no language server is catalogued" in rename.note
        actions = code_actions_for_file(target, 1, 1)
        assert actions.status == "no-server"
        assert actions.actions == []

    def test_not_installed_is_a_status_never_a_rename(
            self, tmp_path, monkeypatch):
        _no_servers_installed(monkeypatch)
        target = tmp_path / "a.py"
        target.write_text("x = 1\n", encoding="utf-8")
        rename = rename_for_file(target, 1, 1, "why")
        assert rename.status == "not-installed"
        assert rename.server == "pyright"
        assert rename.plan is None
        assert "pip install pyright" in rename.note
        actions = code_actions_for_file(target, 1, 1)
        assert actions.status == "not-installed"
        assert actions.actions == []
        assert target.read_text(encoding="utf-8") == "x = 1\n"

    def test_bad_position_and_name_refused(self, tmp_path):
        target = tmp_path / "a.py"
        target.write_text("x = 1\n", encoding="utf-8")
        with pytest.raises(ValueError, match="positive integers"):
            rename_for_file(target, 0, 1, "why")
        with pytest.raises(ValueError, match="non-empty"):
            rename_for_file(target, 1, 1, "  ")


# ---------------------------------------------------------------------------
# Surfaces: parser, formatters, Agent, both /lsp roads
# ---------------------------------------------------------------------------

class TestParseRenameActions:
    @pytest.mark.parametrize("arguments,expected", [
        ("rename a.py 2 5 better_name",
         {"action": "rename", "path": "a.py", "line": 2,
          "character": 5, "new_name": "better_name",
          "apply": False}),
        ("rename a.py 2 5 better_name apply",
         {"action": "rename", "path": "a.py", "line": 2,
          "character": 5, "new_name": "better_name",
          "apply": True}),
        ("actions a.py 2 5",
         {"action": "code_actions", "path": "a.py", "line": 2,
          "character": 5, "apply_index": None}),
        ("actions a.py 2 5 apply 2",
         {"action": "code_actions", "path": "a.py", "line": 2,
          "character": 5, "apply_index": 1}),
        ("codeactions a.py 1 1 apply 1",
         {"action": "code_actions", "path": "a.py", "line": 1,
          "character": 1, "apply_index": 0}),
    ])
    def test_grammar(self, arguments, expected):
        assert parse_lsp_args(arguments) == expected

    @pytest.mark.parametrize("arguments", [
        "rename a.py 2 5", "rename a.py 2 5 name extra",
        "rename a.py x 5 name", "rename a.py 2 5 name drop",
        "actions a.py 2", "actions a.py 2 5 apply",
        "actions a.py 2 5 apply 0", "actions a.py 2 5 apply x",
        "actions a.py 2 5 drop 1", "actions a.py y 5"])
    def test_usage_errors(self, arguments):
        with pytest.raises(ValueError, match="Usage: /lsp"):
            parse_lsp_args(arguments)


def _status(report):
    return {"report": report.record(),
            "plain_explanation": RENAME_PLAIN_EXPLANATION}


class TestFormatRenameActions:
    def test_rename_preview_shows_the_plan(self, fake_server,
                                           target_files):
        server, _ = fake_server
        a_file, _ = target_files
        report = rename_for_file(
            a_file, 2, 5, "better_name",
            client_factory=_factory_for(server))
        text = format_lsp_rename(_status(report))
        assert "planned 4 edit(s) across 2 file(s)" in text
        assert "preview only — nothing written" in text
        assert "+def better_name():" in text

    def test_rename_applied_wording(self, agent, fake_server,
                                    target_files):
        server, _ = fake_server
        a_file, _ = target_files
        report = rename_for_file(
            a_file, 2, 5, "better_name", apply=True,
            client_factory=_factory_for(server))
        text = format_lsp_rename(_status(report))
        assert "applied through the edit journal" in text
        assert "applied:" in text

    def test_rename_absence_wording(self, tmp_path, monkeypatch):
        _no_servers_installed(monkeypatch)
        target = tmp_path / "a.py"
        target.write_text("x = 1\n", encoding="utf-8")
        report = rename_for_file(target, 1, 1, "why")
        text = format_lsp_rename(_status(report))
        assert "NOT PLANNED" in text
        assert "not installed" in text

    def test_code_actions_listing(self, fake_server, target_files):
        server, _ = fake_server
        a_file, _ = target_files
        report = code_actions_for_file(
            a_file, 2, 5, client_factory=_factory_for(server))
        text = format_lsp_code_actions(_status(report))
        assert "offered 3 code action(s)" in text
        assert "[1] Fix the call (quickfix) — carries an edit" in text
        assert "[2] Organize imports" in text
        assert "carries a command (not executed)" in text
        assert "for 1 diagnostic(s)" in text
        assert "+y = my_func()  # fixed" in text

    def test_code_actions_empty_and_absence(
            self, fake_server, target_files, monkeypatch):
        server, _ = fake_server
        a_file, _ = target_files
        report = code_actions_for_file(
            a_file, 8, 8, client_factory=_factory_for(server))
        text = format_lsp_code_actions(_status(report))
        assert "offered no code actions" in text
        _no_servers_installed(monkeypatch)
        missing = code_actions_for_file(a_file, 1, 1)
        text = format_lsp_code_actions(_status(missing))
        assert "NOT ANSWERED" in text

    def test_code_actions_apply_note_shown(self, fake_server,
                                           target_files):
        server, _ = fake_server
        a_file, _ = target_files
        report = code_actions_for_file(
            a_file, 2, 5, apply_index=1,
            client_factory=_factory_for(server))
        text = format_lsp_code_actions(_status(report))
        assert "does not execute server commands" in text


class TestAgentRenameTools:
    def test_rename_not_installed(self, agent, monkeypatch):
        _no_servers_installed(monkeypatch)
        root = Path(agent.project_root)
        (root / "a.py").write_text("x = 1\n", encoding="utf-8")
        status = agent.lsp_rename("a.py", 1, 1, "why")
        assert status["report"]["status"] == "not-installed"
        assert status["report"]["plan"] is None
        assert status["report"]["applied"] is False
        assert status["plain_explanation"] == \
            RENAME_PLAIN_EXPLANATION

    def test_code_actions_shape(self, agent, monkeypatch):
        _no_servers_installed(monkeypatch)
        root = Path(agent.project_root)
        (root / "a.py").write_text("x = 1\n", encoding="utf-8")
        status = agent.lsp_code_actions("a.py", 1, 1)
        assert status["report"]["action"] == "code_actions"
        assert status["report"]["status"] == "not-installed"
        assert status["report"]["actions"] == []

    def test_tools_refuse_escape_and_missing(self, agent):
        with pytest.raises(ValueError):
            agent.lsp_rename("../outside.py", 1, 1, "why")
        with pytest.raises(ValueError):
            agent.lsp_code_actions("../outside.py", 1, 1)
        with pytest.raises(ValueError, match="no such file"):
            agent.lsp_rename("ghost.py", 1, 1, "why")

    def test_slice_pins(self):
        assert LSP_RENAME_SLICE == "M-051"
        assert "edit journal" in RENAME_PLAIN_EXPLANATION
        assert "does not execute server commands" in \
            RENAME_PLAIN_EXPLANATION


class TestTerminalRenameActions:
    def test_rename_flow_reports_not_planned(self, agent, monkeypatch):
        from mythic_agent.terminal import _slash

        _no_servers_installed(monkeypatch)
        root = Path(agent.project_root)
        (root / "a.py").write_text("x = 1\n", encoding="utf-8")
        _, _, text = _slash(agent, "/lsp rename a.py 1 1 why")
        assert "NOT PLANNED" in text

    def test_actions_flow_reports_not_answered(self, agent,
                                               monkeypatch):
        from mythic_agent.terminal import _slash

        _no_servers_installed(monkeypatch)
        root = Path(agent.project_root)
        (root / "a.py").write_text("x = 1\n", encoding="utf-8")
        _, _, text = _slash(agent, "/lsp actions a.py 1 1")
        assert "NOT ANSWERED" in text

    def test_rename_usage_error_is_plain(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/lsp rename a.py 1")
        assert text.startswith("Usage: /lsp")


@pytest.fixture()
def handler(agent, monkeypatch):
    from mythic_agent.agents import command_handler as handler_module
    from mythic_agent.agents.command_handler import CommandHandler
    from mythic_agent.agents.llm import AGENT_REGISTRY

    published = []
    monkeypatch.setattr(
        handler_module, "publish_sync",
        lambda event, **kwargs: published.append((event, kwargs)))
    AGENT_REGISTRY["Primary"] = agent
    instance = CommandHandler.__new__(CommandHandler)
    instance.published = published
    yield instance
    AGENT_REGISTRY.pop("Primary", None)


def _published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestLspCommandRenameActions:
    def test_rename(self, handler, agent, monkeypatch):
        _no_servers_installed(monkeypatch)
        root = Path(agent.project_root)
        (root / "a.py").write_text("x = 1\n", encoding="utf-8")
        handler._handle_lsp("rename a.py 1 1 why")
        assert "NOT PLANNED" in _published_text(handler)

    def test_actions(self, handler, agent, monkeypatch):
        _no_servers_installed(monkeypatch)
        root = Path(agent.project_root)
        (root / "a.py").write_text("x = 1\n", encoding="utf-8")
        handler._handle_lsp("actions a.py 1 1 apply 1")
        assert "NOT ANSWERED" in _published_text(handler)

    def test_usage_error_is_plain(self, handler, agent):
        handler._handle_lsp("rename a.py nope 1 why")
        assert "Usage: /lsp" in _published_text(handler)


class TestChatScreenRoutingRename:
    def test_rename_routes_as_system_command(self, monkeypatch):
        from mythic_agent.ui.screens import chat_screen
        from mythic_agent.ui.screens.chat_screen import MainChatScreen

        class _FakeLog:
            def write(self, *args, **kwargs):
                pass

        calls = []
        monkeypatch.setattr(
            chat_screen.SecureAPI, "publish_system_command",
            staticmethod(lambda cmd, args: calls.append((cmd, args))))
        screen = MainChatScreen.__new__(MainChatScreen)
        screen.handle_command(
            "/lsp rename a.py 2 5 better_name", _FakeLog())
        assert calls == [("/lsp", "rename a.py 2 5 better_name")]


class TestGapAuditRowAfterM051:
    def test_lsp_row_state_stays_missing_census_pinned(self):
        audit = load_audit(repo_root=REPO_ROOT)
        row = audit.row("lsp-integration")
        assert row.owning_module == \
            "mythic_agent/integrations/lsp.py"
        assert row.module_kind == "existing"
        # M-049+M-050+M-051 now build the whole row, but the
        # audit's state is pinned to the census by
        # validate_audit (row.state must equal the census
        # state) — no honest flip exists inside the
        # validators' current shape, so it stays MISSING,
        # recorded rather than forced.
        assert row.state == "MISSING"
