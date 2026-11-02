"""M-050 — LSP client II: navigation.

TIER: integration

Part III (Code Intelligence): the language server's
navigation answers — go-to-definition, references, hover,
workspace symbols — as agent tools, so 'where is this
used?' gets a true answer. These tests do not take the
client's word for any of it:

* the plain records map the wire truth (0-based spans
  becoming 1-based records; Location and LocationLink both
  read, the link's selection range winning; SymbolKind
  1–26 mapped and out-of-range refused; malformed
  locations refused),
* hover contents are extracted from every protocol shape
  (plain string, MarkupContent, MarkedString string and
  code dict, lists joined by a blank line), and a null
  hover is the server's answer, never an error,
* workspace symbols read both wire shapes —
  SymbolInformation and hierarchical DocumentSymbol
  entries flattened recursively,
* the client speaks the four navigation requests to a
  REAL subprocess fake language server (wire positions
  proven 0-based from the server's own log, the references
  includeDeclaration flag proven to change the answer,
  didOpen sent once per file),
* the end-to-end helpers report no-server / not-installed
  as statuses, never as empty-but-ok answers, and refuse
  non-positive positions plainly,
* the surfaces — the Agent tools, the terminal ``/lsp``
  road, the TUI system-command road, the chat screen's
  routing — share the one parser and formatter, and the
  gap audit's lsp row still stays MISSING (rename M-051
  is still owed).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from mythic_agent.core.gap_audit import load_audit
from mythic_agent.integrations.lsp import (
    LSP_NAVIGATION_SLICE,
    LSP_SLICE,
    NAVIGATION_PLAIN_EXPLANATION,
    SYMBOL_KINDS,
    HoverInfo,
    LSPClient,
    LSPError,
    NavLocation,
    ServerDef,
    WorkspaceSymbol,
    definition_for_file,
    format_lsp_navigation,
    hover_for_file,
    parse_lsp_args,
    references_for_file,
    workspace_symbols_for,
)

REPO_ROOT = Path(__file__).resolve().parent.parent

FAKE_SERVER = r'''
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


def loc(uri, line, char, end_char):
    return {"uri": uri, "range": {
        "start": {"line": line, "character": char},
        "end": {"line": line, "character": end_char}}}


def main():
    log_path = sys.argv[1]
    stream_in = sys.stdin.buffer
    stream_out = sys.stdout.buffer
    log = open(log_path, "a", encoding="utf-8")
    docs = {}
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
            docs[doc["uri"]] = doc["text"]
            send(stream_out, {
                "jsonrpc": "2.0",
                "method": "textDocument/publishDiagnostics",
                "params": {"uri": doc["uri"], "diagnostics": []}})
        elif method == "textDocument/definition":
            params = message["params"]
            pos = params["position"]
            uri = params["textDocument"]["uri"]
            log.write("definition %d:%d\n" % (pos["line"],
                                              pos["character"]))
            log.flush()
            if (pos["line"], pos["character"]) == (4, 2):
                result = [
                    loc(uri, 0, 0, 9),
                    {"targetUri": uri,
                     "targetRange": {
                         "start": {"line": 9, "character": 0},
                         "end": {"line": 12, "character": 3}},
                     "targetSelectionRange": {
                         "start": {"line": 10, "character": 4},
                         "end": {"line": 10, "character": 13}}}]
            elif (pos["line"], pos["character"]) == (0, 0):
                result = loc(uri, 2, 1, 8)
            elif (pos["line"], pos["character"]) == (9, 9):
                result = None
            else:
                result = [loc(uri, 1, 0, 5)]
            send(stream_out, {"jsonrpc": "2.0", "id": message["id"],
                              "result": result})
        elif method == "textDocument/references":
            params = message["params"]
            pos = params["position"]
            uri = params["textDocument"]["uri"]
            include = params["context"]["includeDeclaration"]
            log.write("references %d:%d include=%s\n"
                      % (pos["line"], pos["character"], include))
            log.flush()
            result = [loc(uri, 0, 0, 9), loc(uri, 3, 2, 11),
                      loc(uri, 7, 5, 14)]
            if not include:
                result = result[1:]
            send(stream_out, {"jsonrpc": "2.0", "id": message["id"],
                              "result": result})
        elif method == "textDocument/hover":
            params = message["params"]
            pos = params["position"]
            if (pos["line"], pos["character"]) == (0, 0):
                result = {"contents": {
                    "kind": "markdown",
                    "value": "**thing** - a markdown hover"},
                    "range": {
                        "start": {"line": 0, "character": 0},
                        "end": {"line": 0, "character": 5}}}
            elif (pos["line"], pos["character"]) == (1, 0):
                result = {"contents": [
                    "plain marked",
                    {"language": "python", "value": "x = 1"},
                    "tail"]}
            elif (pos["line"], pos["character"]) == (2, 0):
                result = None
            elif (pos["line"], pos["character"]) == (3, 0):
                result = {"contents": "a plain string hover"}
            else:
                result = {"contents": {
                    "kind": "plaintext", "value": "default hover"}}
            send(stream_out, {"jsonrpc": "2.0", "id": message["id"],
                              "result": result})
        elif method == "workspace/symbol":
            query = message["params"].get("query", "")
            log.write("symbols query=%r\n" % query)
            log.flush()
            if query == "hier":
                result = [{
                    "name": "Outer", "kind": 5,
                    "uri": "file:///ws/a.py",
                    "range": {
                        "start": {"line": 0, "character": 0},
                        "end": {"line": 9, "character": 3}},
                    "selectionRange": {
                        "start": {"line": 0, "character": 6},
                        "end": {"line": 0, "character": 11}},
                    "children": [{
                        "name": "inner_method", "kind": 6,
                        "range": {
                            "start": {"line": 2, "character": 4},
                            "end": {"line": 4, "character": 8}},
                        "selectionRange": {
                            "start": {"line": 2, "character": 8},
                            "end": {"line": 2, "character": 20}}}]}]
            else:
                result = [
                    {"name": "my_func", "kind": 12,
                     "location": loc("file:///ws/a.py", 4, 0, 9),
                     "containerName": "MyModule"},
                    {"name": "MyClass", "kind": 5,
                     "location": loc("file:///ws/b.py", 0, 6, 13)}]
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
    script = tmp_path / "fake_ls_nav.py"
    script.write_text(FAKE_SERVER, encoding="utf-8")
    log = tmp_path / "fake_ls_nav.log"
    server = ServerDef(
        name="fake", languages=("python",), extensions=(".py",),
        language_ids={"python": "python"},
        command=(sys.executable, str(script), str(log)),
        install_remedy="install the fake server")
    return server, log


@pytest.fixture()
def target_file(tmp_path):
    target = tmp_path / "a.py"
    target.write_text(
        "thing = 1\n"
        "def my_func():\n"
        "    return thing\n"
        "\n"
        "y = my_func()\n", encoding="utf-8")
    return target


def _no_servers_installed(monkeypatch):
    import mythic_agent.integrations.lsp as lsp_module
    monkeypatch.setattr(lsp_module.shutil, "which", lambda name: None)


def _factory_for(server):
    return lambda srv, root: LSPClient(server, root)


# ---------------------------------------------------------------------------
# Plain records
# ---------------------------------------------------------------------------

class TestNavLocation:
    def test_location_shape_and_one_based(self):
        found = NavLocation.from_lsp_location({
            "uri": "file:///ws/a%20b.py",
            "range": {"start": {"line": 2, "character": 4},
                      "end": {"line": 2, "character": 9}}})
        assert (found.line, found.character) == (3, 5)
        assert (found.end_line, found.end_character) == (3, 10)
        assert found.path.endswith("a b.py")
        assert found.record()["line"] == 3
        assert found.one_line().endswith("a b.py:3:5")

    def test_location_link_prefers_selection_range(self):
        found = NavLocation.from_lsp_location({
            "targetUri": "file:///ws/a.py",
            "targetRange": {"start": {"line": 9, "character": 0},
                            "end": {"line": 12, "character": 3}},
            "targetSelectionRange": {
                "start": {"line": 10, "character": 4},
                "end": {"line": 10, "character": 13}}})
        assert (found.line, found.character) == (11, 5)
        assert (found.end_line, found.end_character) == (11, 14)

    def test_location_link_falls_back_to_target_range(self):
        found = NavLocation.from_lsp_location({
            "targetUri": "file:///ws/a.py",
            "targetRange": {"start": {"line": 0, "character": 0},
                            "end": {"line": 0, "character": 3}}})
        assert (found.line, found.character) == (1, 1)

    @pytest.mark.parametrize("raw", [
        "not-a-location", 42, None,
        {"range": {"start": {"line": 0, "character": 0},
                   "end": {"line": 0, "character": 1}}},
        {"uri": "file:///ws/a.py"},
        {"targetUri": "file:///ws/a.py"},
    ])
    def test_malformed_location_is_refused(self, raw):
        with pytest.raises(LSPError, match="malformed|not an object"):
            NavLocation.from_lsp_location(raw)


class TestHoverInfo:
    def test_plain_string(self):
        info = HoverInfo.from_lsp_result(
            {"contents": "just text"}, "file.py")
        assert info.contents == "just text"
        assert info.range is None

    def test_markup_content(self):
        info = HoverInfo.from_lsp_result(
            {"contents": {"kind": "markdown", "value": "**bold**"}},
            "file.py")
        assert info.contents == "**bold**"

    def test_marked_string_code_dict_keeps_value(self):
        info = HoverInfo.from_lsp_result(
            {"contents": {"language": "python", "value": "x = 1"}},
            "file.py")
        assert info.contents == "x = 1"

    def test_list_joined_by_blank_line(self):
        info = HoverInfo.from_lsp_result(
            {"contents": ["one",
                          {"language": "python", "value": "two"},
                          {"kind": "plaintext", "value": "three"}]},
            "file.py")
        assert info.contents == "one\n\ntwo\n\nthree"

    def test_null_is_an_empty_answer_not_an_error(self):
        for result in (None, {}):
            info = HoverInfo.from_lsp_result(result, "file.py")
            assert info.contents == ""
            assert info.range is None
            assert info.record() == {"contents": "", "range": None}

    def test_range_becomes_a_one_based_location(self):
        info = HoverInfo.from_lsp_result(
            {"contents": "text",
             "range": {"start": {"line": 1, "character": 2},
                       "end": {"line": 1, "character": 7}}},
            "/ws/a.py")
        assert info.range.path == "/ws/a.py"
        assert (info.range.line, info.range.character) == (2, 3)
        assert info.record()["range"]["end_character"] == 8


class TestWorkspaceSymbolRecords:
    def test_symbol_information_shape(self):
        found = WorkspaceSymbol.flatten({
            "name": "my_func", "kind": 12,
            "location": {"uri": "file:///ws/a.py",
                         "range": {
                             "start": {"line": 4, "character": 0},
                             "end": {"line": 4, "character": 9}}},
            "containerName": "MyModule"})
        assert len(found) == 1
        symbol = found[0]
        assert symbol.name == "my_func"
        assert symbol.kind == "function"
        assert symbol.container_name == "MyModule"
        assert symbol.location.one_line() == "/ws/a.py:5:1"
        assert symbol.one_line() == \
            "my_func (function) at /ws/a.py:5:1 in MyModule"
        assert symbol.record()["location"]["line"] == 5

    def test_document_symbol_flattened_recursively(self):
        found = WorkspaceSymbol.flatten({
            "name": "Outer", "kind": 5, "uri": "file:///ws/a.py",
            "range": {"start": {"line": 0, "character": 0},
                      "end": {"line": 9, "character": 3}},
            "selectionRange": {"start": {"line": 0, "character": 6},
                               "end": {"line": 0, "character": 11}},
            "children": [{
                "name": "inner", "kind": 6,
                "range": {"start": {"line": 2, "character": 4},
                          "end": {"line": 4, "character": 8}},
                "selectionRange": {
                    "start": {"line": 2, "character": 8},
                    "end": {"line": 2, "character": 13}}}]})
        assert [s.name for s in found] == ["Outer", "inner"]
        assert found[0].location.path == "/ws/a.py"
        assert (found[0].location.line,
                found[0].location.character) == (1, 7)
        assert found[1].kind == "method"
        assert found[1].container_name == "Outer"
        # the child inherits the parent's document uri
        assert found[1].location.path == "/ws/a.py"
        assert (found[1].location.line,
                found[1].location.character) == (3, 9)

    def test_document_symbol_without_uri_is_honestly_pathless(self):
        found = WorkspaceSymbol.flatten({
            "name": "Loose", "kind": 13,
            "range": {"start": {"line": 0, "character": 0},
                      "end": {"line": 0, "character": 5}}})
        assert found[0].location.path == ""

    @pytest.mark.parametrize("number,word", [
        (1, "file"), (5, "class"), (12, "function"),
        (22, "enum_member"), (26, "type_parameter")])
    def test_kind_numbers_map(self, number, word):
        assert SYMBOL_KINDS[number - 1] == word
        found = WorkspaceSymbol.flatten({
            "name": "x", "kind": number,
            "location": {"uri": "file:///ws/a.py",
                         "range": {
                             "start": {"line": 0, "character": 0},
                             "end": {"line": 0, "character": 1}}}})
        assert found[0].kind == word

    @pytest.mark.parametrize("number", [0, 27, "class", None])
    def test_kind_outside_the_protocol_is_refused(self, number):
        with pytest.raises(LSPError, match="outside the LSP range"):
            WorkspaceSymbol.flatten({
                "name": "x", "kind": number,
                "location": {"uri": "file:///ws/a.py",
                             "range": {
                                 "start": {"line": 0, "character": 0},
                                 "end": {"line": 0, "character": 1}}}})

    def test_bad_kind_word_is_refused(self):
        with pytest.raises(ValueError, match="symbol kind must be"):
            WorkspaceSymbol(name="x", kind="gadget")


# ---------------------------------------------------------------------------
# The client against a real subprocess fake server
# ---------------------------------------------------------------------------

class TestClientNavigationLive:
    def test_definition_duality_and_wire_positions(
            self, fake_server, target_file, tmp_path):
        server, log = fake_server
        client = LSPClient(server, tmp_path)
        client.start()
        try:
            found = client.definition(target_file, 5, 3)
        finally:
            client.close()
        # one Location + one LocationLink (selection range wins)
        assert len(found) == 2
        assert (found[0].line, found[0].character) == (1, 1)
        assert (found[1].line, found[1].character) == (11, 5)
        assert (found[1].end_line, found[1].end_character) == (11, 14)
        # the wire saw 0-based positions for house 5,3
        lines = log.read_text(encoding="utf-8")
        assert "definition 4:2" in lines

    def test_definition_single_object_and_null(
            self, fake_server, target_file, tmp_path):
        server, _ = fake_server
        client = LSPClient(server, tmp_path)
        client.start()
        try:
            single = client.definition(target_file, 1, 1)
            unknown = client.definition(target_file, 10, 10)
        finally:
            client.close()
        assert len(single) == 1
        assert (single[0].line, single[0].character) == (3, 2)
        # a null result is the server's answer: no definition
        assert unknown == []

    def test_references_include_declaration_matters(
            self, fake_server, target_file, tmp_path):
        server, log = fake_server
        client = LSPClient(server, tmp_path)
        client.start()
        try:
            with_decl = client.references(target_file, 5, 3)
            without = client.references(
                target_file, 5, 3, include_declaration=False)
        finally:
            client.close()
        assert len(with_decl) == 3
        assert len(without) == 2
        assert with_decl[0].line == 1  # the declaration site
        lines = log.read_text(encoding="utf-8")
        assert "references 4:2 include=True" in lines
        assert "references 4:2 include=False" in lines

    def test_hover_shapes_live(self, fake_server, target_file, tmp_path):
        server, _ = fake_server
        client = LSPClient(server, tmp_path)
        client.start()
        try:
            markdown = client.hover(target_file, 1, 1)
            marked = client.hover(target_file, 2, 1)
            silent = client.hover(target_file, 3, 1)
            plain = client.hover(target_file, 4, 1)
        finally:
            client.close()
        assert markdown.contents == "**thing** - a markdown hover"
        assert markdown.range is not None
        assert (markdown.range.line, markdown.range.character) == (1, 1)
        assert marked.contents == "plain marked\n\nx = 1\n\ntail"
        assert silent.contents == ""
        assert plain.contents == "a plain string hover"

    def test_workspace_symbols_both_shapes_live(
            self, fake_server, tmp_path):
        server, log = fake_server
        client = LSPClient(server, tmp_path)
        client.start()
        try:
            flat = client.workspace_symbols("")
            hier = client.workspace_symbols("hier")
        finally:
            client.close()
        assert [s.name for s in flat] == ["my_func", "MyClass"]
        assert flat[0].container_name == "MyModule"
        assert flat[1].kind == "class"
        assert [s.name for s in hier] == ["Outer", "inner_method"]
        assert hier[1].container_name == "Outer"
        assert "symbols query='hier'" in log.read_text(encoding="utf-8")

    def test_didopen_sent_once_per_file(
            self, fake_server, target_file, tmp_path):
        server, log = fake_server
        client = LSPClient(server, tmp_path)
        client.start()
        try:
            client.definition(target_file, 5, 3)
            client.hover(target_file, 1, 1)
            client.references(target_file, 5, 3)
            report = client.diagnostics_for(target_file)
        finally:
            client.close()
        assert report.status == "ok"
        methods = log.read_text(encoding="utf-8").splitlines()
        assert methods.count("textDocument/didOpen") == 1

    def test_initialize_declares_navigation_capabilities(
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
        assert "definition" in text_document
        assert "references" in text_document
        assert text_document["hover"]["contentFormat"] == \
            ["markdown", "plaintext"]
        assert "symbol" in caps["workspace"]

    def test_navigation_before_start_and_bad_position(
            self, fake_server, target_file, tmp_path):
        server, _ = fake_server
        client = LSPClient(server, tmp_path)
        with pytest.raises(LSPError, match="not running"):
            client.definition(target_file, 1, 1)
        client.start()
        try:
            with pytest.raises(ValueError, match="positive integers"):
                client.definition(target_file, 0, 1)
            with pytest.raises(ValueError, match="positive integers"):
                client.hover(target_file, 1, 0)
        finally:
            client.close()


# ---------------------------------------------------------------------------
# The end-to-end helpers: honest absence
# ---------------------------------------------------------------------------

class TestNavigationHelpers:
    def test_definition_live_through_factory(
            self, fake_server, target_file):
        server, _ = fake_server
        report = definition_for_file(
            target_file, 5, 3, client_factory=_factory_for(server))
        assert report.status == "ok"
        assert report.action == "definition"
        assert report.server == "fake-ls"
        assert len(report.locations) == 2
        record = report.record()
        assert record["locations"][1]["line"] == 11
        assert record["hover"] is None
        assert record["symbols"] == []

    def test_references_and_hover_live_through_factory(
            self, fake_server, target_file):
        server, _ = fake_server
        refs = references_for_file(
            target_file, 5, 3, client_factory=_factory_for(server))
        assert refs.status == "ok"
        assert len(refs.locations) == 3
        hover = hover_for_file(
            target_file, 1, 1, client_factory=_factory_for(server))
        assert hover.status == "ok"
        assert hover.hover.contents == "**thing** - a markdown hover"

    def test_no_catalogued_server(self, tmp_path):
        target = tmp_path / "spell.mojo"
        target.write_text("fn main():\n    pass\n", encoding="utf-8")
        for helper in (definition_for_file, references_for_file,
                       hover_for_file):
            report = helper(target, 1, 1)
            assert report.status == "no-server"
            assert report.server is None
            assert report.locations == []
            assert "no language server is catalogued" in report.note

    def test_not_installed_is_a_status_never_an_answer(
            self, tmp_path, monkeypatch):
        _no_servers_installed(monkeypatch)
        target = tmp_path / "a.py"
        target.write_text("x = 1\n", encoding="utf-8")
        report = definition_for_file(target, 1, 1)
        assert report.status == "not-installed"
        assert report.server == "pyright"
        assert report.locations == []
        assert "not installed" in report.note
        assert "pip install pyright" in report.note

    @pytest.mark.parametrize("line,character", [
        (0, 1), (1, 0), (-1, 1), ("3", 1), (1, None), (True, 1)])
    def test_bad_positions_refused_plainly(
            self, tmp_path, line, character):
        target = tmp_path / "a.py"
        target.write_text("x = 1\n", encoding="utf-8")
        with pytest.raises(ValueError, match="positive integers"):
            definition_for_file(target, line, character)

    def test_workspace_symbols_live_through_factory(self, fake_server):
        server, _ = fake_server
        # with a factory supplied and nothing installed, the
        # first catalogued server is the one asked
        report = workspace_symbols_for(
            query="", client_factory=_factory_for(server))
        assert report.status == "ok"
        assert report.action == "symbols"
        assert [s.name for s in report.symbols] == ["my_func", "MyClass"]
        assert report.record()["symbols"][0]["container_name"] == \
            "MyModule"

    def test_workspace_symbols_explicit_server(self, fake_server):
        server, _ = fake_server
        report = workspace_symbols_for(
            query="hier", server_name="pyright",
            client_factory=_factory_for(server))
        assert report.status == "ok"
        assert [s.name for s in report.symbols] == \
            ["Outer", "inner_method"]

    def test_workspace_symbols_unknown_server_refused(self):
        with pytest.raises(ValueError, match="unknown language server"):
            workspace_symbols_for(server_name="ghost-ls")

    def test_workspace_symbols_not_installed(self, monkeypatch):
        _no_servers_installed(monkeypatch)
        report = workspace_symbols_for(query="x")
        assert report.status == "not-installed"
        assert report.server is None
        assert report.symbols == []
        assert "no language server is installed" in report.note
        assert "pip install pyright" in report.note

    def test_workspace_symbols_named_server_not_installed(
            self, monkeypatch):
        _no_servers_installed(monkeypatch)
        report = workspace_symbols_for(server_name="gopls")
        assert report.status == "not-installed"
        assert report.server == "gopls"
        assert report.symbols == []


# ---------------------------------------------------------------------------
# Surfaces
# ---------------------------------------------------------------------------

class TestParseNavigation:
    @pytest.mark.parametrize("arguments,expected", [
        ("def a.py 5 3", {"action": "definition", "path": "a.py",
                          "line": 5, "character": 3}),
        ("definition a.py 1 1", {"action": "definition", "path": "a.py",
                                 "line": 1, "character": 1}),
        ("refs a.py 5 3", {"action": "references", "path": "a.py",
                           "line": 5, "character": 3}),
        ("references a.py 2 9", {"action": "references", "path": "a.py",
                                 "line": 2, "character": 9}),
        ("hover a.py 4 1", {"action": "hover", "path": "a.py",
                            "line": 4, "character": 1}),
        ("symbols", {"action": "symbols", "query": ""}),
        ("symbols my func", {"action": "symbols", "query": "my func"}),
    ])
    def test_grammar(self, arguments, expected):
        assert parse_lsp_args(arguments) == expected

    @pytest.mark.parametrize("arguments", [
        "def a.py", "def a.py 5", "def a.py x 3", "refs a.py 1 y",
        "hover", "hover a.py 1 1 extra"])
    def test_usage_errors(self, arguments):
        with pytest.raises(ValueError, match="Usage: /lsp"):
            parse_lsp_args(arguments)


def _report_status(report):
    return {"report": report.record(),
            "plain_explanation": NAVIGATION_PLAIN_EXPLANATION}


class TestFormatNavigation:
    def test_definition_ok_and_empty(self, fake_server, target_file):
        server, _ = fake_server
        found = definition_for_file(
            target_file, 5, 3, client_factory=_factory_for(server))
        text = format_lsp_navigation(_report_status(found))
        assert "fake-ls found 2 definition(s)" in text
        assert ":11:5" in text
        empty = definition_for_file(
            target_file, 10, 10, client_factory=_factory_for(server))
        text = format_lsp_navigation(_report_status(empty))
        assert "the server found no definition" in text

    def test_references_empty_wording(self, tmp_path):
        from mythic_agent.integrations.lsp import NavigationReport
        report = NavigationReport(
            action="references", path="/ws/a.py", server="fake-ls",
            status="ok")
        text = format_lsp_navigation(_report_status(report))
        assert "the server found no references" in text

    def test_hover_ok_and_silent(self, fake_server, target_file):
        server, _ = fake_server
        spoken = hover_for_file(
            target_file, 1, 1, client_factory=_factory_for(server))
        text = format_lsp_navigation(_report_status(spoken))
        assert "**thing** - a markdown hover" in text
        silent = hover_for_file(
            target_file, 3, 1, client_factory=_factory_for(server))
        text = format_lsp_navigation(_report_status(silent))
        assert "the server said nothing about that spot" in text

    def test_symbols_rendering(self, fake_server):
        server, _ = fake_server
        report = workspace_symbols_for(
            query="", client_factory=_factory_for(server))
        text = format_lsp_navigation(_report_status(report))
        assert "my_func (function) at" in text
        assert "in MyModule" in text
        assert "MyClass (class) at" in text

    def test_absence_rendering(self, tmp_path, monkeypatch):
        _no_servers_installed(monkeypatch)
        target = tmp_path / "a.py"
        target.write_text("x = 1\n", encoding="utf-8")
        report = definition_for_file(target, 1, 1)
        text = format_lsp_navigation(_report_status(report))
        assert "NOT ANSWERED" in text
        assert "not installed" in text
        mojo = tmp_path / "spell.mojo"
        mojo.write_text("fn main():\n    pass\n", encoding="utf-8")
        report = hover_for_file(mojo, 1, 1)
        text = format_lsp_navigation(_report_status(report))
        assert "NOT ANSWERED" in text
        assert "no language server is catalogued" in text


class TestAgentNavigationTools:
    def test_definition_not_installed(self, agent, monkeypatch):
        _no_servers_installed(monkeypatch)
        root = Path(agent.project_root)
        (root / "a.py").write_text("x = 1\n", encoding="utf-8")
        status = agent.lsp_definition("a.py", 1, 1)
        assert status["report"]["status"] == "not-installed"
        assert status["report"]["locations"] == []
        assert status["plain_explanation"] == \
            NAVIGATION_PLAIN_EXPLANATION

    def test_references_hover_and_symbols_shapes(
            self, agent, monkeypatch):
        _no_servers_installed(monkeypatch)
        root = Path(agent.project_root)
        (root / "a.py").write_text("x = 1\n", encoding="utf-8")
        refs = agent.lsp_references("a.py", 1, 1)
        assert refs["report"]["action"] == "references"
        assert refs["report"]["status"] == "not-installed"
        hover = agent.lsp_hover("a.py", 1, 1)
        assert hover["report"]["action"] == "hover"
        assert hover["report"]["hover"] is None
        symbols = agent.lsp_workspace_symbols("func")
        assert symbols["report"]["action"] == "symbols"
        assert symbols["report"]["status"] == "not-installed"
        assert symbols["plain_explanation"] == \
            NAVIGATION_PLAIN_EXPLANATION

    def test_tools_refuse_escape_and_missing(self, agent):
        with pytest.raises(ValueError):
            agent.lsp_definition("../outside.py", 1, 1)
        with pytest.raises(ValueError):
            agent.lsp_references("../outside.py", 1, 1)
        with pytest.raises(ValueError):
            agent.lsp_hover("../outside.py", 1, 1)
        with pytest.raises(ValueError, match="no such file"):
            agent.lsp_definition("ghost.py", 1, 1)

    def test_slice_pins(self):
        assert LSP_SLICE == "M-049"
        assert LSP_NAVIGATION_SLICE == "M-050"
        assert "defined" in NAVIGATION_PLAIN_EXPLANATION


class TestTerminalNavigation:
    def test_def_flow_reports_not_answered(self, agent, monkeypatch):
        from mythic_agent.terminal import _slash

        _no_servers_installed(monkeypatch)
        root = Path(agent.project_root)
        (root / "a.py").write_text("x = 1\n", encoding="utf-8")
        _, _, text = _slash(agent, "/lsp def a.py 1 1")
        assert "NOT ANSWERED" in text

    def test_symbols_flow(self, agent, monkeypatch):
        from mythic_agent.terminal import _slash

        _no_servers_installed(monkeypatch)
        _, _, text = _slash(agent, "/lsp symbols func")
        assert "NOT ANSWERED" in text

    def test_hover_usage_error_is_plain(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/lsp hover a.py x 1")
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


class TestLspCommandNavigation:
    def test_def(self, handler, agent, monkeypatch):
        _no_servers_installed(monkeypatch)
        root = Path(agent.project_root)
        (root / "a.py").write_text("x = 1\n", encoding="utf-8")
        handler._handle_lsp("def a.py 1 1")
        assert "NOT ANSWERED" in _published_text(handler)

    def test_symbols(self, handler, agent, monkeypatch):
        _no_servers_installed(monkeypatch)
        handler._handle_lsp("symbols func")
        assert "NOT ANSWERED" in _published_text(handler)

    def test_usage_error_is_plain(self, handler, agent):
        handler._handle_lsp("refs a.py nope 1")
        assert "Usage: /lsp" in _published_text(handler)


class TestChatScreenRoutingNavigation:
    def test_navigation_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/lsp def a.py 5 3", _FakeLog())
        assert calls == [("/lsp", "def a.py 5 3")]


class TestGapAuditRowStillMissing:
    def test_lsp_row_state_stays_missing(self):
        audit = load_audit(repo_root=REPO_ROOT)
        row = audit.row("lsp-integration")
        assert row.owning_module == "mythic_agent/integrations/lsp.py"
        # rename (M-051) is still owed, so the census-pinned
        # state stays MISSING
        assert row.state == "MISSING"
