"""M-049 — LSP client I: diagnostics.

TIER: integration

Part III (Code Intelligence): language servers run beside the
app; their diagnostics flow into the coder's awareness. These
tests do not take the client's word for any of it:

* the server catalogue names the roadmap's four servers and
  honestly has no server for Mojo or unknown languages,
* discovery reports installed / not-installed exactly as the
  PATH lookup says, with the install remedy riding the
  not-installed record — absence is never a clean bill,
* diagnostics records map the wire truth (0-based spans,
  severity numbers 1–4) to plain records, and refuse a
  severity outside the protocol,
* the framing round-trips and refuses a frame without a
  Content-Length and a body that is not JSON,
* the client speaks the real lifecycle to a REAL subprocess
  fake language server (initialize -> initialized -> didOpen
  -> publishDiagnostics -> shutdown/exit, the order proven
  from the server's own log), including a server-to-client
  request answered mid-flight,
* a silent server times out as UNKNOWN, never as clean; a
  dying server and a refusing server raise in their own
  words; a missing binary raises carrying its remedy,
* the end-to-end helper reports no-server / not-installed as
  statuses (never as empty-but-clean), and the surfaces —
  the Agent tool, the terminal ``/lsp`` road, the TUI
  system-command road, the chat screen's routing — share
  the one parser and formatters,
* the gap audit's lsp row now names an existing module
  (its state stays MISSING: navigation M-050 and rename
  M-051 are still owed, and the state is pinned to the
  census).
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest

from mythic_agent.core.gap_audit import load_audit
from mythic_agent.integrations.lsp import (
    LSP_SLICE,
    PLAIN_EXPLANATION,
    SERVERS,
    Diagnostic,
    LSPClient,
    LSPError,
    ServerDef,
    diagnostics_for_file,
    discover_servers,
    encode_message,
    format_lsp_diagnostics,
    format_lsp_status,
    language_id_for,
    parse_lsp_args,
    path_to_uri,
    read_message,
    render_markdown,
    server_for_language,
    server_for_path,
    uri_to_path,
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


def main():
    log_path = sys.argv[1]
    mode = os.environ.get("FAKE_LSP_MODE", "normal")
    if mode == "die":
        return
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
            if mode == "error-init":
                send(stream_out, {"jsonrpc": "2.0",
                                  "id": message["id"],
                                  "error": {"code": -32603,
                                            "message": "boom init"}})
                continue
            send(stream_out, {"jsonrpc": "2.0", "id": message["id"],
                              "result": {
                                  "capabilities":
                                      {"textDocumentSync": 1},
                                  "serverInfo": {"name": "fake-ls",
                                                 "version": "1.0"}}})
        elif method == "textDocument/didOpen":
            if mode == "silent":
                continue
            doc = message["params"]["textDocument"]
            uri, text = doc["uri"], doc["text"]
            if "ask_first" in text:
                send(stream_out, {"jsonrpc": "2.0", "id": 99,
                                  "method": "workspace/configuration",
                                  "params": {"items": []}})
                read_message(stream_in)  # the client's null answer
                log.write("answered-configuration\n")
                log.flush()
            found = []
            for number, line in enumerate(text.splitlines()):
                at = line.find("undefined_name")
                if at >= 0:
                    found.append({
                        "range": {"start": {"line": number,
                                            "character": at},
                                  "end": {"line": number,
                                          "character": at + 14}},
                        "severity": 1,
                        "message": "undefined name 'undefined_name'",
                        "source": "fake-ls", "code": "F001"})
                at = line.find("todo_warn")
                if at >= 0:
                    found.append({
                        "range": {"start": {"line": number,
                                            "character": at},
                                  "end": {"line": number,
                                          "character": at + 9}},
                        "severity": 2,
                        "message": "a warning the server insists on",
                        "source": "fake-ls", "code": 42})
            send(stream_out, {
                "jsonrpc": "2.0",
                "method": "textDocument/publishDiagnostics",
                "params": {"uri": uri, "diagnostics": found}})
        elif method == "shutdown":
            send(stream_out, {"jsonrpc": "2.0", "id": message["id"],
                              "result": None})
        elif method == "exit":
            return


main()
'''


@pytest.fixture()
def fake_server(tmp_path):
    script = tmp_path / "fake_ls.py"
    script.write_text(FAKE_SERVER, encoding="utf-8")
    log = tmp_path / "fake_ls.log"
    server = ServerDef(
        name="fake", languages=("python",), extensions=(".py",),
        language_ids={"python": "python"},
        command=(sys.executable, str(script), str(log)),
        install_remedy="install the fake server")
    return server, log


def _no_servers_installed(monkeypatch):
    import mythic_agent.integrations.lsp as lsp_module
    monkeypatch.setattr(lsp_module.shutil, "which", lambda name: None)


# ---------------------------------------------------------------------------
# The catalogue and honest discovery
# ---------------------------------------------------------------------------

class TestCatalogue:
    def test_slice_and_servers(self):
        assert LSP_SLICE == "M-049"
        assert [s.name for s in SERVERS] == [
            "pyright", "typescript", "rust-analyzer", "gopls"]

    @pytest.mark.parametrize("language,name", [
        ("python", "pyright"), ("typescript", "typescript"),
        ("javascript", "typescript"), ("rust", "rust-analyzer"),
        ("go", "gopls")])
    def test_server_for_language(self, language, name):
        assert server_for_language(language).name == name
        assert server_for_language(language.upper()).name == name

    @pytest.mark.parametrize("language", ["mojo", "cobol", ""])
    def test_no_server_is_an_honest_none(self, language):
        assert server_for_language(language) is None

    @pytest.mark.parametrize("filename,name", [
        ("a.py", "pyright"), ("a.pyi", "pyright"),
        ("a.ts", "typescript"), ("a.jsx", "typescript"),
        ("a.rs", "rust-analyzer"), ("a.go", "gopls")])
    def test_server_for_path(self, filename, name):
        assert server_for_path(filename).name == name

    def test_server_for_unknown_extension(self):
        assert server_for_path("notes.mojo") is None
        assert server_for_path("README.txt") is None

    @pytest.mark.parametrize("filename,language_id", [
        ("a.py", "python"), ("a.ts", "typescript"),
        ("a.tsx", "typescriptreact"), ("a.js", "javascript"),
        ("a.jsx", "javascriptreact"), ("a.rs", "rust"),
        ("a.go", "go")])
    def test_language_ids(self, filename, language_id):
        assert language_id_for(filename) == language_id

    def test_language_id_unknown(self):
        assert language_id_for("notes.mojo") is None


class TestDiscovery:
    def test_board_shape(self):
        board = discover_servers()
        assert [e["name"] for e in board] == [s.name for s in SERVERS]
        for entry in board:
            assert entry["installed"] == (entry["path"] is not None)
            if entry["installed"]:
                assert entry["install_remedy"] is None
            else:
                assert entry["install_remedy"]

    def test_not_installed_carries_the_remedy(self, monkeypatch):
        _no_servers_installed(monkeypatch)
        board = discover_servers()
        assert all(not e["installed"] for e in board)
        pyright = board[0]
        assert "pip install pyright" in pyright["install_remedy"]


# ---------------------------------------------------------------------------
# Diagnostic records and URIs
# ---------------------------------------------------------------------------

class TestDiagnosticRecords:
    @pytest.mark.parametrize("number,word", [
        (1, "error"), (2, "warning"), (3, "information"), (4, "hint")])
    def test_severity_numbers_map(self, number, word):
        diagnostic = Diagnostic.from_lsp({
            "range": {"start": {"line": 0, "character": 0},
                      "end": {"line": 0, "character": 1}},
            "severity": number, "message": "m"}, "file:///x.py")
        assert diagnostic.severity == word

    def test_wire_positions_become_one_based(self):
        diagnostic = Diagnostic.from_lsp({
            "range": {"start": {"line": 2, "character": 4},
                      "end": {"line": 2, "character": 9}},
            "severity": 1, "message": "bad", "source": "pyright",
            "code": 7}, "file:///ws/a%20b.py")
        assert (diagnostic.line, diagnostic.character) == (3, 5)
        assert (diagnostic.end_line, diagnostic.end_character) == (3, 10)
        assert diagnostic.code == "7"
        assert diagnostic.path.endswith("a b.py")
        assert diagnostic.record()["severity"] == "error"

    @pytest.mark.parametrize("number", [0, 5, "high"])
    def test_severity_outside_the_protocol_is_refused(self, number):
        with pytest.raises(LSPError, match="outside the LSP range"):
            Diagnostic.from_lsp({
                "range": {"start": {"line": 0, "character": 0},
                          "end": {"line": 0, "character": 1}},
                "severity": number, "message": "m"}, "file:///x.py")

    def test_bad_severity_word_is_refused(self):
        with pytest.raises(ValueError, match="severity must be one of"):
            Diagnostic(severity="fatal")

    def test_one_line(self):
        diagnostic = Diagnostic(
            path="/ws/a.py", line=3, character=5, severity="error",
            message="bad", source="pyright", code="F001")
        assert diagnostic.one_line() == \
            "[error] /ws/a.py:3:5 (pyright): bad [F001]"

    def test_uri_round_trip(self, tmp_path):
        target = tmp_path / "a b.py"
        uri = path_to_uri(target)
        assert uri.startswith("file://")
        assert uri_to_path(uri) == str(target.resolve())


# ---------------------------------------------------------------------------
# Framing
# ---------------------------------------------------------------------------

class TestFraming:
    def test_round_trip(self):
        message = {"jsonrpc": "2.0", "id": 1, "method": "initialize"}
        stream = io.BytesIO(encode_message(message))
        assert read_message(stream) == message

    def test_clean_eof_is_none(self):
        assert read_message(io.BytesIO(b"")) is None

    def test_frame_without_content_length_is_refused(self):
        stream = io.BytesIO(b"Content-Type: x\r\n\r\n{}")
        with pytest.raises(LSPError, match="without a Content-Length"):
            read_message(stream)

    def test_non_json_body_is_refused(self):
        stream = io.BytesIO(b"Content-Length: 3\r\n\r\nnah")
        with pytest.raises(LSPError, match="not JSON"):
            read_message(stream)

    def test_non_object_body_is_refused(self):
        stream = io.BytesIO(b"Content-Length: 2\r\n\r\n[]")
        with pytest.raises(LSPError, match="not an object"):
            read_message(stream)


# ---------------------------------------------------------------------------
# The client against a real subprocess fake server
# ---------------------------------------------------------------------------

class TestClientLive:
    def test_handshake_returns_the_servers_own_words(self, fake_server):
        server, _ = fake_server
        client = LSPClient(server, REPO_ROOT)
        result = client.start()
        try:
            assert result["capabilities"] == {"textDocumentSync": 1}
            assert result["serverInfo"]["name"] == "fake-ls"
        finally:
            client.close()

    def test_diagnostics_flow(self, fake_server, tmp_path):
        server, log = fake_server
        target = tmp_path / "broken.py"
        target.write_text("x = 1\ny = undefined_name\n",
                          encoding="utf-8")
        client = LSPClient(server, tmp_path)
        client.start()
        try:
            report = client.diagnostics_for(target)
        finally:
            client.close()
        assert report.status == "ok"
        assert report.server == "fake-ls"
        assert len(report.diagnostics) == 1
        found = report.diagnostics[0]
        assert found.severity == "error"
        assert (found.line, found.character) == (2, 5)
        assert found.message == "undefined name 'undefined_name'"
        assert found.source == "fake-ls"
        assert found.code == "F001"
        assert report.counts()["error"] == 1
        methods = log.read_text(encoding="utf-8").splitlines()
        assert methods[0] == "initialize"
        assert "textDocument/didOpen" in methods
        assert methods[-2:] == ["shutdown", "exit"]

    def test_warning_and_clean_files(self, fake_server, tmp_path):
        server, _ = fake_server
        warned = tmp_path / "warned.py"
        warned.write_text("# todo_warn here\n", encoding="utf-8")
        clean = tmp_path / "clean.py"
        clean.write_text("x = 1\n", encoding="utf-8")
        client = LSPClient(server, tmp_path)
        client.start()
        try:
            warn_report = client.diagnostics_for(warned)
            clean_report = client.diagnostics_for(clean)
        finally:
            client.close()
        assert [d.severity for d in warn_report.diagnostics] == \
            ["warning"]
        assert warn_report.diagnostics[0].code == "42"
        # an empty list the server actually published is its
        # own answer — an ok report, not an absence report
        assert clean_report.status == "ok"
        assert clean_report.diagnostics == []

    def test_server_request_is_answered(self, fake_server, tmp_path):
        server, log = fake_server
        target = tmp_path / "asking.py"
        target.write_text("# ask_first\nx = undefined_name\n",
                          encoding="utf-8")
        client = LSPClient(server, tmp_path)
        client.start()
        try:
            report = client.diagnostics_for(target)
        finally:
            client.close()
        assert len(report.diagnostics) == 1
        assert "answered-configuration" in \
            log.read_text(encoding="utf-8")

    def test_silent_server_is_unknown_never_clean(
            self, fake_server, tmp_path, monkeypatch):
        server, _ = fake_server
        monkeypatch.setenv("FAKE_LSP_MODE", "silent")
        target = tmp_path / "quiet.py"
        target.write_text("x = 1\n", encoding="utf-8")
        client = LSPClient(server, tmp_path)
        client.start()
        try:
            with pytest.raises(LSPError, match="unknown, not clean"):
                client.diagnostics_for(target, timeout=1.0)
        finally:
            client.close()

    def test_dying_server_raises_in_plain_words(
            self, fake_server, monkeypatch):
        server, _ = fake_server
        monkeypatch.setenv("FAKE_LSP_MODE", "die")
        client = LSPClient(server, REPO_ROOT)
        with pytest.raises(LSPError):
            client.start()

    def test_refusing_server_raises_its_reason(
            self, fake_server, monkeypatch):
        server, _ = fake_server
        monkeypatch.setenv("FAKE_LSP_MODE", "error-init")
        client = LSPClient(server, REPO_ROOT)
        with pytest.raises(LSPError, match="refused initialize.*boom init"):
            client.start()

    def test_missing_binary_carries_its_remedy(self, tmp_path):
        server = ServerDef(
            name="ghost", languages=("python",), extensions=(".py",),
            language_ids={"python": "python"},
            command=("mythic-no-such-ls-xyz", "--stdio"),
            install_remedy="install the ghost server first")
        client = LSPClient(server, tmp_path)
        with pytest.raises(LSPError, match="install the ghost server"):
            client.start()

    def test_diagnostics_before_start_and_missing_file(
            self, fake_server, tmp_path):
        server, _ = fake_server
        client = LSPClient(server, tmp_path)
        target = tmp_path / "x.py"
        target.write_text("x = 1\n", encoding="utf-8")
        with pytest.raises(LSPError, match="not running"):
            client.diagnostics_for(target)
        client.start()
        try:
            with pytest.raises(LSPError, match="no such file"):
                client.diagnostics_for(tmp_path / "ghost.py")
        finally:
            client.close()


# ---------------------------------------------------------------------------
# The end-to-end helper: honest absence
# ---------------------------------------------------------------------------

class TestDiagnosticsForFile:
    def test_no_catalogued_server(self, tmp_path):
        target = tmp_path / "spell.mojo"
        target.write_text("fn main():\n    pass\n", encoding="utf-8")
        report = diagnostics_for_file(target)
        assert report.status == "no-server"
        assert report.server is None
        assert report.diagnostics == []
        assert "no language server is catalogued" in report.note

    def test_not_installed_is_a_status_never_a_clean_bill(
            self, tmp_path, monkeypatch):
        _no_servers_installed(monkeypatch)
        target = tmp_path / "a.py"
        target.write_text("x = undefined_name\n", encoding="utf-8")
        report = diagnostics_for_file(target)
        assert report.status == "not-installed"
        assert report.server == "pyright"
        assert report.diagnostics == []
        assert "not installed" in report.note
        assert "pip install pyright" in report.note

    def test_live_through_the_factory_seam(self, fake_server, tmp_path):
        server, _ = fake_server
        target = tmp_path / "broken.py"
        target.write_text("y = undefined_name\n", encoding="utf-8")
        report = diagnostics_for_file(
            target,
            client_factory=lambda srv, root: LSPClient(server, root))
        assert report.status == "ok"
        assert [d.severity for d in report.diagnostics] == ["error"]


# ---------------------------------------------------------------------------
# Surfaces
# ---------------------------------------------------------------------------

class TestParseAndFormat:
    @pytest.mark.parametrize("arguments,expected", [
        ("", {"action": "show"}), ("show", {"action": "show"}),
        ("check a.py", {"action": "check", "path": "a.py"}),
        ("a.py", {"action": "check", "path": "a.py"}),
        ("check dir/a b.py", {"action": "check", "path": "dir/a b.py"}),
    ])
    def test_grammar(self, arguments, expected):
        assert parse_lsp_args(arguments) == expected

    @pytest.mark.parametrize("arguments", ["check", "show extra"])
    def test_usage_errors(self, arguments):
        with pytest.raises(ValueError, match="Usage: /lsp"):
            parse_lsp_args(arguments)

    def test_board_format(self, monkeypatch):
        _no_servers_installed(monkeypatch)
        text = format_lsp_status({"servers": discover_servers()})
        assert PLAIN_EXPLANATION in text
        assert "pyright: NOT INSTALLED" in text
        assert "gopls: NOT INSTALLED" in text

    def test_report_formats(self, tmp_path):
        ok = {"report": {
            "path": "/ws/a.py", "server": "fake-ls", "status": "ok",
            "note": "", "counts": {}, "diagnostics": [{
                "path": "/ws/a.py", "line": 2, "character": 5,
                "end_line": 2, "end_character": 19,
                "severity": "error", "message": "bad",
                "source": "fake-ls", "code": "F001"}]}}
        text = format_lsp_diagnostics(ok)
        assert "fake-ls reported 1 problem(s)" in text
        assert "[error] /ws/a.py:2:5 (fake-ls): bad [F001]" in text
        missing = {"report": {
            "path": "/ws/a.py", "server": "pyright",
            "status": "not-installed", "note": "it is not here",
            "counts": {}, "diagnostics": []}}
        assert "NOT CHECKED" in format_lsp_diagnostics(missing)
        clean = {"report": {
            "path": "/ws/a.py", "server": "fake-ls", "status": "ok",
            "note": "", "counts": {}, "diagnostics": []}}
        assert "reported no problems" in format_lsp_diagnostics(clean)

    def test_render_markdown_names_the_board(self, monkeypatch):
        _no_servers_installed(monkeypatch)
        text = render_markdown()
        assert "pyright" in text and "not installed" in text


class TestGapAuditRow:
    def test_lsp_row_names_an_existing_module(self):
        audit = load_audit(repo_root=REPO_ROOT)
        row = audit.row("lsp-integration")
        assert row.owning_module == "mythic_agent/integrations/lsp.py"
        assert row.module_kind == "existing"
        # navigation (M-050) and rename (M-051) are still owed,
        # so the census-pinned state stays MISSING
        assert row.state == "MISSING"
        assert (REPO_ROOT / row.owning_module).is_file()


class TestAgentTool:
    def test_status_board(self, agent, monkeypatch):
        _no_servers_installed(monkeypatch)
        status = agent.lsp_status()
        assert [s["name"] for s in status["servers"]] == \
            [s.name for s in SERVERS]
        assert status["plain_explanation"] == PLAIN_EXPLANATION

    def test_diagnostics_not_installed(self, agent, monkeypatch):
        _no_servers_installed(monkeypatch)
        root = Path(agent.project_root)
        (root / "a.py").write_text("x = undefined_name\n",
                                   encoding="utf-8")
        status = agent.lsp_diagnostics("a.py")
        assert status["report"]["status"] == "not-installed"
        assert status["report"]["diagnostics"] == []

    def test_diagnostics_refuses_escape_and_missing(self, agent):
        with pytest.raises(ValueError):
            agent.lsp_diagnostics("../outside.py")
        with pytest.raises(ValueError, match="no such file"):
            agent.lsp_diagnostics("ghost.py")


class TestTerminalSurface:
    def test_board_flow(self, agent, monkeypatch):
        from mythic_agent.terminal import _slash

        _no_servers_installed(monkeypatch)
        _, _, text = _slash(agent, "/lsp")
        assert "pyright: NOT INSTALLED" in text

    def test_check_flow_reports_not_checked(self, agent, monkeypatch):
        from mythic_agent.terminal import _slash

        _no_servers_installed(monkeypatch)
        root = Path(agent.project_root)
        (root / "a.py").write_text("x = 1\n", encoding="utf-8")
        _, _, text = _slash(agent, "/lsp check a.py")
        assert "NOT CHECKED" in text

    def test_usage_error_is_plain(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/lsp check")
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


class TestLspCommand:
    def test_board(self, handler, agent, monkeypatch):
        _no_servers_installed(monkeypatch)
        handler._handle_lsp("")
        assert "pyright: NOT INSTALLED" in _published_text(handler)

    def test_check(self, handler, agent, monkeypatch):
        _no_servers_installed(monkeypatch)
        root = Path(agent.project_root)
        (root / "a.py").write_text("x = 1\n", encoding="utf-8")
        handler._handle_lsp("check a.py")
        assert "NOT CHECKED" in _published_text(handler)

    def test_usage_error_is_plain(self, handler, agent):
        handler._handle_lsp("check")
        assert "Usage: /lsp" in _published_text(handler)


class TestChatScreenRouting:
    def test_lsp_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/lsp check a.py", _FakeLog())
        assert calls == [("/lsp", "check a.py")]
