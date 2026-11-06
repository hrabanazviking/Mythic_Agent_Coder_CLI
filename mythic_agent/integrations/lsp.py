"""LSP client I — diagnostics (M-049), II — navigation (M-050),
and III — rename and code actions (M-051).

Part III — Code Intelligence. Language servers (pyright,
typescript-language-server, rust-analyzer, gopls…) run beside
the app as their own processes; this module is the client that
speaks to them, so their diagnostics flow into the coder's
awareness and can be shown in the TUI's margin, and their
navigation answers — where a name is defined, where it is
used, what the server says about a spot, and the workspace's
symbols — come back as plain records the agent can act on
(slice M-050: go-to-definition, references, hover, and
workspace symbols as agent tools, so 'where is this used?'
gets the server's true answer, never a name-based guess).
The edit-time truth loop that will consume these
diagnostics after every edit (M-052) is a later slice on
this same road — it is not built here and nothing here
claims it.

What ships here, in ``mythic_agent/integrations/lsp.py`` (the
gap audit's named owner for the lsp-integration feature, with
``mythic_agent/tools/review.py`` as its basis — the review
loop is where these diagnostics will land in M-052):

* **The server catalogue, as data.** :data:`SERVERS` names
  the four roadmap servers with the languages each serves,
  the file extensions that select it, the language ids the
  protocol wants, its stdio command, and its install remedy.
  A language with no catalogued server (Mojo today) honestly
  has no server — never an invented one.
* **Honest discovery.** :func:`discover_servers` looks each
  server's binary up on ``PATH`` and reports installed /
  not-installed with the binary's resolved path or the
  install remedy. A server that is not installed is a
  reported state, never an error and never a fake clean
  bill: a diagnostics report for its files says
  ``not-installed`` and carries no diagnostics at all, so
  "no problems reported" is never confused with "the server
  said the file is clean".
* **The client.** :class:`LSPClient` speaks real LSP over
  stdio: Content-Length framed JSON-RPC, the
  ``initialize`` → ``initialized`` handshake, ``didOpen``,
  and the server's ``publishDiagnostics`` notifications,
  then ``shutdown`` / ``exit``. Server-to-client requests
  are answered with a null result rather than left hanging.
  A read thread owns the inbound stream so requests,
  notifications, and the diagnostics wait never race on it.
* **Diagnostics as plain records.** :class:`Diagnostic`
  carries the 1-based line/column span, the severity word
  (LSP's 1–4 mapped to error/warning/information/hint), the
  message verbatim, and the server's source and code where
  it gave them. :class:`DiagnosticsReport` is one file's
  whole account: its status (``ok`` / ``not-installed`` /
  ``no-server``), the server's name, and its diagnostics.
* **Navigation as plain records (M-050).**
  :class:`NavLocation` is one span (a definition site, a
  reference site, a symbol's home), :class:`HoverInfo` is
  what the server says about one spot (its contents in
  plain text, extracted from the protocol's string /
  MarkupContent / MarkedString shapes), and
  :class:`WorkspaceSymbol` is one workspace symbol
  (SymbolInformation and hierarchical DocumentSymbol
  answers flattened to the same record). The client's
  ``definition`` / ``references`` / ``hover`` /
  ``workspace_symbols`` methods ride the same request road
  as the handshake; the end-to-end helpers
  (:func:`definition_for_file` and its kin) report
  no-server / not-installed exactly the way
  :func:`diagnostics_for_file` does — an absent server is
  a status with its remedy, never an invented answer and
  never an empty-but-ok one.
* **Rename and code actions (M-051).** A rename is asked
  for only after ``textDocument/prepareRename`` says the
  spot can be renamed — a null answer or a server error is
  a refusal in the server's terms, never a guess. The
  ``textDocument/rename`` WorkspaceEdit (both the
  ``changes`` and ``documentChanges`` shapes) becomes a
  per-file edit *plan* (:class:`WorkspaceEditPlan`): plain
  records, a plan-time sha256 per file, and per-site and
  per-file unified-diff previews as data — no preview, no
  application (the M-048 house rule). Overlapping edits in
  one file and malformed edits are refused plainly.
  ``textDocument/codeAction`` answers become
  :class:`CodeActionRecord` plain records (title, kind,
  diagnostics carried, whether the action carries an edit
  and/or a command). Application — of a rename plan or of
  a code action's edit — exists only through
  :func:`apply_workspace_edit_plan`, which writes through
  the house :class:`EditJournal` (journal-first) and
  refuses a file whose hash changed since the plan,
  whole. A code action's *command* is never executed:
  no house road runs server commands, and the record
  says so honestly instead of faking execution.
* **The surfaces.** ``Agent.lsp_status()`` is the discovery
  board and ``Agent.lsp_diagnostics(path)`` one file's
  report; ``/lsp`` (bare or ``show`` for the board,
  ``check <path>`` for one file) rides the terminal and the
  TUI system-command road, sharing this module's parser and
  formatters. M-050 adds the navigation agent tools
  (``Agent.lsp_definition`` / ``lsp_references`` /
  ``lsp_hover`` / ``lsp_workspace_symbols``) and the
  ``/lsp def|refs|hover|symbols`` subcommands on the same
  two roads, sharing the same parser and the navigation
  formatter. M-051 adds ``Agent.lsp_rename()`` (preview by
  default; application only when explicitly asked) and
  ``Agent.lsp_code_actions()``, plus the ``/lsp rename``
  and ``/lsp actions`` subcommands on the same two roads,
  sharing the same parser and the rename / code-action
  formatters.

Honesty rules, pinned by the slice's tests:

* **Absence is never cleanliness.** Only a report with
  status ``ok`` may be read as "the server looked and this
  is what it said" — and even then an empty diagnostic list
  is the *server's* answer, recorded as its answer.
* **A server that dies or never answers is an error in its
  own words.** A process that exits mid-handshake, a reply
  carrying a JSON-RPC error, and a diagnostics wait that
  times out each raise :class:`LSPError` naming what
  happened; nothing is retried silently and no partial
  diagnostics are dressed up as the whole answer.
* **Malformed wire data is refused, never guessed.** A
  frame without a Content-Length, a body that is not a
  JSON object, and a diagnostic whose severity number is
  outside 1–4 each raise plainly.
"""

from __future__ import annotations

__all__ = [
    "LSP_NAVIGATION_SLICE",
    "LSP_RENAME_SLICE",
    "LSP_SLICE",
    "NAVIGATION_PLAIN_EXPLANATION",
    "PLAIN_EXPLANATION",
    "RENAME_PLAIN_EXPLANATION",
    "SERVERS",
    "SEVERITIES",
    "SYMBOL_KINDS",
    "CodeActionRecord",
    "CodeActionsReport",
    "Diagnostic",
    "DiagnosticsReport",
    "EditFileOutcome",
    "FileEditPlan",
    "HoverInfo",
    "LSPClient",
    "LSPError",
    "NavLocation",
    "NavigationReport",
    "PlannedTextEdit",
    "RenamePreparation",
    "RenameReport",
    "ServerDef",
    "WorkspaceEditPlan",
    "WorkspaceEditResult",
    "WorkspaceSymbol",
    "apply_workspace_edit_plan",
    "code_actions_for_file",
    "definition_for_file",
    "diagnostics_for_file",
    "discover_servers",
    "encode_message",
    "format_lsp_code_actions",
    "format_lsp_diagnostics",
    "format_lsp_navigation",
    "format_lsp_rename",
    "format_lsp_status",
    "hover_for_file",
    "language_id_for",
    "parse_lsp_args",
    "parse_workspace_edit",
    "path_to_uri",
    "read_message",
    "references_for_file",
    "rename_for_file",
    "render_markdown",
    "server_for_language",
    "server_for_path",
    "uri_to_path",
    "workspace_symbols_for",
]

import difflib
import hashlib
import json
import shutil
import subprocess
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, BinaryIO, Callable, Dict, List, Optional, Tuple
from urllib.parse import unquote, urlparse

from ..core.edits import EditJournal
from ..core.exceptions import MythicIntegrationError

LSP_SLICE = "M-049"

LSP_NAVIGATION_SLICE = "M-050"

LSP_RENAME_SLICE = "M-051"

RENAME_PLAIN_EXPLANATION = (
    "The language server truly knows every place a name "
    "lives — its definition, its uses, its re-exports and "
    "imports — so a rename asked of the server propagates "
    "by the server's own knowledge, never by text "
    "substitution. /lsp rename <path> <line> <character> "
    "<new-name> first asks the server whether that spot "
    "can be renamed at all (a spot it refuses is refused "
    "in its words), then shows the rename as a per-file "
    "plan with a diff preview for every site — a preview "
    "writes nothing. Adding 'apply' writes the plan "
    "through the edit journal, and only for files still "
    "exactly what the plan saw: a file that changed since "
    "the plan is refused whole. /lsp actions <path> <line> "
    "<character> lists the fixes and refactors the server "
    "offers at a spot; 'apply <n>' applies the chosen "
    "action's edit the same journaled way. An action that "
    "carries only a server command is reported honestly — "
    "Mythic does not execute server commands, so the "
    "command is named, never faked as run."
)

NAVIGATION_PLAIN_EXPLANATION = (
    "The language server truly knows what a name means in "
    "its language, so Mythic can ask it the navigation "
    "questions and get true answers: where a name is "
    "defined (/lsp def <path> <line> <character>), every "
    "place it is used (/lsp refs), what the server says "
    "about a spot (/lsp hover), and the workspace's symbols "
    "(/lsp symbols [query]). The positions are the editor's "
    "1-based line and character. A server that is not "
    "installed is reported as not installed — its silence "
    "is never dressed up as an answer, and a name-based "
    "guess is never presented as the server's truth."
)

PLAIN_EXPLANATION = (
    "Language servers are separate programs that truly "
    "understand one language — what a name means, whether a "
    "call type-checks. Mythic can run the server for a "
    "file's language beside the app and ask it what is wrong: "
    "/lsp shows which servers this machine has, and /lsp "
    "check <path> shows one file's diagnostics in the "
    "server's own words. A server that is not installed is "
    "reported as not installed, with how to install it — "
    "that is never shown as a clean file."
)

#: LSP DiagnosticSeverity numbers, in protocol order.
SEVERITIES = ("error", "warning", "information", "hint")

_SEVERITY_BY_NUMBER = {1: "error", 2: "warning",
                       3: "information", 4: "hint"}


class LSPError(MythicIntegrationError, RuntimeError):
    """A language server is missing, died, or answered badly."""


# ---------------------------------------------------------------------------
# The server catalogue
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ServerDef:
    """One catalogued language server, as data."""

    name: str
    languages: Tuple[str, ...]
    extensions: Tuple[str, ...]
    language_ids: Dict[str, str]
    command: Tuple[str, ...]
    install_remedy: str

    @property
    def binary(self) -> str:
        return self.command[0]

    def installed_path(self) -> Optional[str]:
        """The binary's resolved PATH location, or None."""
        return shutil.which(self.binary)

    def language_id(self, language: str) -> str:
        return self.language_ids[language]

    def record(self, installed_path: Optional[str] = None) -> Dict[str, Any]:
        """This server's discovery record (no secrets ride it)."""
        found = self.installed_path() if installed_path is None \
            else installed_path
        return {
            "name": self.name,
            "languages": list(self.languages),
            "extensions": list(self.extensions),
            "command": list(self.command),
            "installed": found is not None,
            "path": found,
            "install_remedy": None if found is not None
            else self.install_remedy,
        }


SERVERS: Tuple[ServerDef, ...] = (
    ServerDef(
        name="pyright",
        languages=("python",),
        extensions=(".py", ".pyi"),
        language_ids={"python": "python"},
        command=("pyright-langserver", "--stdio"),
        install_remedy="install pyright (pip install pyright, or "
                       "npm install -g pyright) so pyright-langserver "
                       "is on PATH",
    ),
    ServerDef(
        name="typescript",
        languages=("typescript", "javascript"),
        extensions=(".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"),
        language_ids={"typescript": "typescript",
                      "typescriptreact": "typescriptreact",
                      "javascript": "javascript",
                      "javascriptreact": "javascriptreact"},
        command=("typescript-language-server", "--stdio"),
        install_remedy="install it with npm install -g "
                       "typescript-language-server typescript",
    ),
    ServerDef(
        name="rust-analyzer",
        languages=("rust",),
        extensions=(".rs",),
        language_ids={"rust": "rust"},
        command=("rust-analyzer",),
        install_remedy="install it with rustup component add "
                       "rust-analyzer",
    ),
    ServerDef(
        name="gopls",
        languages=("go",),
        extensions=(".go",),
        language_ids={"go": "go"},
        command=("gopls",),
        install_remedy="install it with go install "
                       "golang.org/x/tools/gopls@latest and put "
                       "the Go bin directory on PATH",
    ),
)

_BY_LANGUAGE: Dict[str, ServerDef] = {}
_BY_EXTENSION: Dict[str, ServerDef] = {}
for _server in SERVERS:
    for _language in _server.languages:
        _BY_LANGUAGE[_language] = _server
    for _extension in _server.extensions:
        _BY_EXTENSION[_extension] = _server

#: File extension -> Mythic language name, for language-id lookup.
_LANGUAGE_BY_EXTENSION: Dict[str, str] = {
    ".py": "python", ".pyi": "python",
    ".ts": "typescript", ".tsx": "typescriptreact",
    ".js": "javascript", ".jsx": "javascriptreact",
    ".mjs": "javascript", ".cjs": "javascript",
    ".rs": "rust", ".go": "go",
}


def server_for_language(language: str) -> Optional[ServerDef]:
    """The catalogued server for *language*, or None honestly."""
    return _BY_LANGUAGE.get(language.strip().lower())


def server_for_path(path: Path | str) -> Optional[ServerDef]:
    """The catalogued server for a file's extension, or None."""
    return _BY_EXTENSION.get(Path(path).suffix.lower())


def language_id_for(path: Path | str) -> Optional[str]:
    """The LSP languageId for a file, or None when unknown."""
    language = _LANGUAGE_BY_EXTENSION.get(Path(path).suffix.lower())
    if language is None:
        return None
    server = server_for_path(path)
    if server is None:
        return language
    return server.language_ids.get(language, language)


def discover_servers() -> List[Dict[str, Any]]:
    """Every catalogued server's discovery record, in order."""
    return [server.record() for server in SERVERS]


# ---------------------------------------------------------------------------
# URIs
# ---------------------------------------------------------------------------

def path_to_uri(path: Path | str) -> str:
    """A local file path as an LSP ``file://`` URI."""
    return Path(path).resolve().as_uri()


def uri_to_path(uri: str) -> str:
    """An LSP ``file://`` URI back to a local path string."""
    parsed = urlparse(uri)
    return unquote(parsed.path)


# ---------------------------------------------------------------------------
# Diagnostics as plain records
# ---------------------------------------------------------------------------

@dataclass
class Diagnostic:
    """One diagnostic, in the server's own words."""

    path: str = ""
    line: int = 1
    character: int = 1
    end_line: int = 1
    end_character: int = 1
    severity: str = "error"
    message: str = ""
    source: str = ""
    code: str = ""

    def __post_init__(self) -> None:
        if self.severity not in SEVERITIES:
            raise ValueError(
                f"severity must be one of {SEVERITIES}, "
                f"got {self.severity!r}")

    @classmethod
    def from_lsp(cls, raw: Dict[str, Any], uri: str) -> "Diagnostic":
        """Build a record from one LSP Diagnostic object.

        LSP positions are 0-based; the record is 1-based, the
        way editors and people count. A severity number
        outside 1–4 is refused plainly, never guessed.
        """
        if not isinstance(raw, dict):
            raise LSPError(f"diagnostic is not an object: {raw!r}")
        span = raw.get("range") or {}
        start = span.get("start") or {}
        end = span.get("end") or {}
        number = raw.get("severity", 1)
        if number not in _SEVERITY_BY_NUMBER:
            raise LSPError(
                f"diagnostic severity {number!r} is outside the "
                f"LSP range 1-4")
        code = raw.get("code", "")
        return cls(
            path=uri_to_path(uri) if uri.startswith("file://") else uri,
            line=int(start.get("line", 0)) + 1,
            character=int(start.get("character", 0)) + 1,
            end_line=int(end.get("line", start.get("line", 0))) + 1,
            end_character=int(end.get("character",
                                     start.get("character", 0))) + 1,
            severity=_SEVERITY_BY_NUMBER[number],
            message=str(raw.get("message", "")),
            source=str(raw.get("source", "") or ""),
            code="" if code is None else str(code),
        )

    def record(self) -> Dict[str, Any]:
        return {
            "path": self.path, "line": self.line,
            "character": self.character,
            "end_line": self.end_line,
            "end_character": self.end_character,
            "severity": self.severity, "message": self.message,
            "source": self.source, "code": self.code,
        }

    def one_line(self) -> str:
        where = f"{self.path}:{self.line}:{self.character}" \
            if self.path else f"{self.line}:{self.character}"
        origin = self.source or "lsp"
        suffix = f" [{self.code}]" if self.code else ""
        return f"[{self.severity}] {where} ({origin}): " \
               f"{self.message}{suffix}"


# ---------------------------------------------------------------------------
# Navigation records (M-050)
# ---------------------------------------------------------------------------

#: LSP SymbolKind numbers 1–26, as plain kind words.
SYMBOL_KINDS = (
    "file", "module", "namespace", "package", "class",
    "method", "property", "field", "constructor", "enum",
    "interface", "function", "variable", "constant", "string",
    "number", "boolean", "array", "object", "key",
    "null", "enum_member", "struct", "event", "operator",
    "type_parameter",
)

_SYMBOL_KIND_BY_NUMBER = {
    number: word for number, word in enumerate(SYMBOL_KINDS, start=1)}


def _span_fields(span: Dict[str, Any]) -> Tuple[int, int, int, int]:
    """One LSP Range as 1-based (line, character, end_line, end_character)."""
    start = span.get("start") or {}
    end = span.get("end") or {}
    line = int(start.get("line", 0)) + 1
    character = int(start.get("character", 0)) + 1
    end_line = int(end.get("line", start.get("line", 0))) + 1
    end_character = int(end.get("character",
                                start.get("character", 0))) + 1
    return line, character, end_line, end_character


@dataclass
class NavLocation:
    """One place the server points at, as a 1-based record."""

    path: str = ""
    line: int = 1
    character: int = 1
    end_line: int = 1
    end_character: int = 1

    @classmethod
    def from_lsp_location(cls, raw: Any) -> "NavLocation":
        """Build a record from an LSP Location or LocationLink.

        A Location carries ``{uri, range}``; a LocationLink
        carries ``{targetUri, targetRange,
        targetSelectionRange}`` — the selection range (the
        name itself) wins over the full target range.
        Anything else is refused plainly, never guessed.
        """
        if not isinstance(raw, dict):
            raise LSPError(f"location is not an object: {raw!r}")
        if "targetUri" in raw or "targetRange" in raw \
                or "targetSelectionRange" in raw:
            uri = raw.get("targetUri")
            span = raw.get("targetSelectionRange") \
                or raw.get("targetRange")
        else:
            uri = raw.get("uri")
            span = raw.get("range")
        if not uri or not isinstance(span, dict):
            raise LSPError(
                f"location is malformed (it needs a uri and a "
                f"range): {raw!r}")
        line, character, end_line, end_character = _span_fields(span)
        return cls(
            path=uri_to_path(uri) if str(uri).startswith("file://")
            else str(uri),
            line=line, character=character,
            end_line=end_line, end_character=end_character)

    @classmethod
    def from_range(cls, span: Dict[str, Any], path: str) -> "NavLocation":
        """A bare LSP Range at a known path, as a record."""
        line, character, end_line, end_character = _span_fields(span)
        return cls(path=path, line=line, character=character,
                   end_line=end_line, end_character=end_character)

    def record(self) -> Dict[str, Any]:
        return {
            "path": self.path, "line": self.line,
            "character": self.character,
            "end_line": self.end_line,
            "end_character": self.end_character,
        }

    def one_line(self) -> str:
        if self.path:
            return f"{self.path}:{self.line}:{self.character}"
        return f"{self.line}:{self.character}"


def _hover_text(contents: Any) -> str:
    """Hover contents in any protocol shape, as plain text.

    The shapes: a plain string; a MarkupContent
    ``{kind, value}``; a MarkedString — a string, or
    ``{language, value}`` whose value (the code, for a code
    marked string) is the text; and a list of any of those,
    joined by a blank line.
    """
    if contents is None:
        return ""
    if isinstance(contents, str):
        return contents
    if isinstance(contents, dict):
        value = contents.get("value")
        return "" if value is None else str(value)
    if isinstance(contents, (list, tuple)):
        parts = [_hover_text(item) for item in contents]
        return "\n\n".join(part for part in parts if part)
    return ""


@dataclass
class HoverInfo:
    """What the server says about one spot."""

    contents: str = ""
    range: Optional[NavLocation] = None

    @classmethod
    def from_lsp_result(cls, result: Any, path: str = "") -> "HoverInfo":
        """Build a record from one ``textDocument/hover`` result.

        A null result is the server's answer — it said
        nothing about that spot — so it becomes an empty
        record, not an error.
        """
        if result is None or result == {}:
            return cls(contents="", range=None)
        if not isinstance(result, dict):
            raise LSPError(
                f"hover result is not an object: {result!r}")
        span = result.get("range")
        location = NavLocation.from_range(span, path) \
            if isinstance(span, dict) else None
        return cls(contents=_hover_text(result.get("contents")),
                   range=location)

    def record(self) -> Dict[str, Any]:
        return {
            "contents": self.contents,
            "range": self.range.record() if self.range else None,
        }

    def one_line(self) -> str:
        return self.contents if self.contents \
            else "(the server said nothing about that spot)"


@dataclass
class WorkspaceSymbol:
    """One workspace symbol, as a plain record."""

    name: str = ""
    kind: str = "variable"
    container_name: str = ""
    location: NavLocation = field(default_factory=NavLocation)

    def __post_init__(self) -> None:
        if self.kind not in SYMBOL_KINDS:
            raise ValueError(
                f"symbol kind must be one of {SYMBOL_KINDS}, "
                f"got {self.kind!r}")

    @classmethod
    def flatten(cls, raw: Any, uri: str = "",
                container: str = "") -> List["WorkspaceSymbol"]:
        """One symbol entry (and its children) as flat records.

        Two wire shapes land here: SymbolInformation
        (``{name, kind, location, containerName}``) and
        hierarchical DocumentSymbol entries (``{name, kind,
        range, selectionRange, children}``), flattened
        recursively with the parent named as the children's
        container. A kind number outside 1–26 is refused
        plainly, never guessed.
        """
        if not isinstance(raw, dict):
            raise LSPError(f"symbol is not an object: {raw!r}")
        number = raw.get("kind")
        if number not in _SYMBOL_KIND_BY_NUMBER:
            raise LSPError(
                f"symbol kind {number!r} is outside the LSP "
                f"range 1-26")
        name = str(raw.get("name", ""))
        own_uri = str(raw.get("uri", "") or uri)
        wire_location = raw.get("location")
        if isinstance(wire_location, dict):
            location = NavLocation.from_lsp_location(wire_location)
            container_name = str(
                raw.get("containerName", "") or container)
        else:
            span = raw.get("selectionRange") or raw.get("range")
            if not isinstance(span, dict):
                raise LSPError(
                    f"symbol is malformed (it needs a location "
                    f"or a range): {raw!r}")
            path = uri_to_path(own_uri) \
                if own_uri.startswith("file://") else own_uri
            location = NavLocation.from_range(span, path)
            container_name = container
        found = [cls(name=name,
                     kind=_SYMBOL_KIND_BY_NUMBER[number],
                     container_name=container_name,
                     location=location)]
        for child in raw.get("children") or []:
            found.extend(cls.flatten(child, uri=own_uri,
                                     container=name))
        return found

    def record(self) -> Dict[str, Any]:
        return {
            "name": self.name, "kind": self.kind,
            "container_name": self.container_name,
            "location": self.location.record(),
        }

    def one_line(self) -> str:
        text = f"{self.name} ({self.kind}) at {self.location.one_line()}"
        if self.container_name:
            text += f" in {self.container_name}"
        return text


@dataclass
class NavigationReport:
    """One navigation question's whole account (M-050)."""

    action: str = ""
    path: str = ""
    server: Optional[str] = None
    status: str = "ok"   # ok | not-installed | no-server
    note: str = ""
    locations: List[NavLocation] = field(default_factory=list)
    hover: Optional[HoverInfo] = None
    symbols: List[WorkspaceSymbol] = field(default_factory=list)

    def record(self) -> Dict[str, Any]:
        return {
            "action": self.action, "path": self.path,
            "server": self.server, "status": self.status,
            "note": self.note,
            "locations": [loc.record() for loc in self.locations],
            "hover": self.hover.record() if self.hover else None,
            "symbols": [sym.record() for sym in self.symbols],
        }


@dataclass
class DiagnosticsReport:
    """One file's whole diagnostics account."""

    path: str = ""
    server: Optional[str] = None
    status: str = "ok"   # ok | not-installed | no-server
    note: str = ""
    diagnostics: List[Diagnostic] = field(default_factory=list)

    def counts(self) -> Dict[str, int]:
        tally = {name: 0 for name in SEVERITIES}
        for diagnostic in self.diagnostics:
            tally[diagnostic.severity] += 1
        return tally

    def record(self) -> Dict[str, Any]:
        return {
            "path": self.path, "server": self.server,
            "status": self.status, "note": self.note,
            "diagnostics": [d.record() for d in self.diagnostics],
            "counts": self.counts(),
        }


# ---------------------------------------------------------------------------
# Rename and code actions (M-051): WorkspaceEdit plans
# ---------------------------------------------------------------------------

def _checked_range(span: Any, what: str = "text edit"
                   ) -> Tuple[int, int, int, int]:
    """One LSP Range strictly checked, as 1-based span fields.

    Unlike the navigation road's lenient span reading, an
    edit that will be *applied* must be exact: a range that
    is not an object with integer 0-based start/end points,
    or that ends before it starts, is refused plainly.
    """
    if not isinstance(span, dict):
        raise LSPError(f"{what} range is not an object: {span!r}")
    start, end = span.get("start"), span.get("end")
    for point in (start, end):
        if not isinstance(point, dict) \
                or not isinstance(point.get("line"), int) \
                or isinstance(point.get("line"), bool) \
                or not isinstance(point.get("character"), int) \
                or isinstance(point.get("character"), bool) \
                or point["line"] < 0 or point["character"] < 0:
            raise LSPError(
                f"{what} range has a malformed start/end "
                f"point: {span!r}")
    line, character, end_line, end_character = _span_fields(span)
    if (end_line, end_character) < (line, character):
        raise LSPError(
            f"{what} range ends before it starts: {span!r}")
    return line, character, end_line, end_character


@dataclass
class PlannedTextEdit:
    """One planned text edit, as a 1-based plain record."""

    path: str = ""
    line: int = 1
    character: int = 1
    end_line: int = 1
    end_character: int = 1
    new_text: str = ""
    diff: str = ""

    @classmethod
    def from_lsp(cls, raw: Any, path: str) -> "PlannedTextEdit":
        """Build a record from one LSP TextEdit object.

        A missing range, a malformed range, and a missing
        or non-string ``newText`` are refused plainly —
        an edit that will land on disk is never guessed.
        """
        if not isinstance(raw, dict):
            raise LSPError(f"text edit is not an object: {raw!r}")
        if "range" not in raw:
            raise LSPError(f"text edit carries no range: {raw!r}")
        line, character, end_line, end_character = \
            _checked_range(raw["range"])
        new_text = raw.get("newText")
        if not isinstance(new_text, str):
            raise LSPError(
                f"text edit carries no string newText: {raw!r}")
        return cls(path=path, line=line, character=character,
                   end_line=end_line, end_character=end_character,
                   new_text=new_text)

    def record(self) -> Dict[str, Any]:
        return {
            "path": self.path, "line": self.line,
            "character": self.character,
            "end_line": self.end_line,
            "end_character": self.end_character,
            "new_text": self.new_text, "diff": self.diff,
        }

    def one_line(self) -> str:
        return f"{self.path}:{self.line}:{self.character} " \
               f"-> {self.new_text!r}"


def _line_starts(text: str) -> List[int]:
    starts = [0]
    for line in text.splitlines(keepends=True):
        starts.append(starts[-1] + len(line))
    return starts


def _edit_offset(starts: List[int], text: str, line: int,
                 character: int, path: str) -> int:
    if line - 1 >= len(starts):
        raise LSPError(
            f"an edit in {path} points at line {line}, beyond "
            f"the file's end — the edit is refused")
    offset = starts[line - 1] + (character - 1)
    if offset > len(text):
        raise LSPError(
            f"an edit in {path} points past the end of its "
            f"line {line} — the edit is refused")
    return offset


def _apply_planned_edits(text: str, edits: List[PlannedTextEdit],
                         path: str) -> str:
    """*text* with *edits* applied, spans descending."""
    starts = _line_starts(text)
    spans = [(_edit_offset(starts, text, e.line, e.character, path),
              _edit_offset(starts, text, e.end_line,
                           e.end_character, path), e)
             for e in edits]
    out = text
    for start, end, edit in sorted(
            spans, key=lambda item: item[0], reverse=True):
        out = out[:start] + edit.new_text + out[end:]
    return out


def _unified_diff(path: str, before: str, after: str) -> str:
    return "".join(difflib.unified_diff(
        before.splitlines(keepends=True),
        after.splitlines(keepends=True),
        fromfile=path, tofile=path))


@dataclass
class FileEditPlan:
    """One file's planned outcome: its plan-time sha256, its
    full new content, its edits (each with its own diff
    preview), and the whole-file diff preview."""

    path: str = ""
    sha256: str = ""
    new_content: str = ""
    edits: List[PlannedTextEdit] = field(default_factory=list)
    diff: str = ""

    def record(self) -> Dict[str, Any]:
        return {
            "path": self.path, "sha256": self.sha256,
            "new_content": self.new_content,
            "edits": [e.record() for e in self.edits],
            "diff": self.diff,
        }


@dataclass
class WorkspaceEditPlan:
    """A whole WorkspaceEdit as a per-file plan, as data.

    A plan writes nothing — it is the preview. Application
    exists only in :func:`apply_workspace_edit_plan`.
    """

    files: List[FileEditPlan] = field(default_factory=list)

    @property
    def edit_count(self) -> int:
        return sum(len(f.edits) for f in self.files)

    def record(self) -> Dict[str, Any]:
        return {
            "files": [f.record() for f in self.files],
            "counts": {"files": len(self.files),
                       "edits": self.edit_count},
        }


def parse_workspace_edit(raw: Any, root: Path | str) -> WorkspaceEditPlan:
    """Parse one LSP WorkspaceEdit into a per-file plan.

    Both wire shapes are read: ``changes`` (uri -> a list
    of TextEdits) and ``documentChanges`` (TextDocumentEdit
    entries). Resource operations (create/rename/delete
    file entries in ``documentChanges``) are refused
    plainly — this road applies text edits only. Each
    planned file is read at plan time: its sha256 is the
    plan's, and every edit carries its own unified-diff
    preview beside the file's whole diff. Edits that
    overlap in one file, edits pointing outside the file,
    edits for a file that does not exist, and malformed
    edits are all refused plainly, never guessed.
    """
    base = Path(root).resolve()
    if raw is None or raw == {}:
        return WorkspaceEditPlan()
    if not isinstance(raw, dict):
        raise LSPError(f"workspace edit is not an object: {raw!r}")
    by_uri: Dict[str, List[Any]] = {}
    if "changes" in raw:
        changes = raw["changes"]
        if not isinstance(changes, dict):
            raise LSPError(
                f"workspace edit 'changes' is not an object: "
                f"{changes!r}")
        for uri, edits in changes.items():
            if not isinstance(edits, list):
                raise LSPError(
                    f"workspace edit changes for {uri!r} are "
                    f"not a list: {edits!r}")
            by_uri.setdefault(str(uri), []).extend(edits)
    if "documentChanges" in raw:
        document_changes = raw["documentChanges"]
        if not isinstance(document_changes, list):
            raise LSPError(
                f"workspace edit 'documentChanges' is not a "
                f"list: {document_changes!r}")
        for entry in document_changes:
            if not isinstance(entry, dict):
                raise LSPError(
                    f"documentChanges entry is not an object: "
                    f"{entry!r}")
            if "kind" in entry:
                raise LSPError(
                    f"workspace edit carries a {entry['kind']!r} "
                    f"file operation — this road applies text "
                    f"edits only, so the whole edit is refused")
            document = entry.get("textDocument")
            if not isinstance(document, dict) \
                    or not document.get("uri") \
                    or not isinstance(entry.get("edits"), list):
                raise LSPError(
                    f"documentChanges entry is malformed (it "
                    f"needs a textDocument uri and an edits "
                    f"list): {entry!r}")
            by_uri.setdefault(str(document["uri"]), []).extend(
                entry["edits"])
    if "changes" not in raw and "documentChanges" not in raw:
        raise LSPError(
            f"workspace edit carries neither 'changes' nor "
            f"'documentChanges': {raw!r}")
    files: List[FileEditPlan] = []
    for uri in sorted(by_uri):
        if not uri.startswith("file://"):
            raise LSPError(
                f"workspace edit targets a non-file uri "
                f"{uri!r} — the whole edit is refused")
        path = uri_to_path(uri)
        target = Path(path)
        if not target.is_absolute():
            target = base / target
        if not target.is_file():
            raise LSPError(
                f"workspace edit targets {path}, which is not "
                f"a file on disk — the whole edit is refused")
        raw_bytes = target.read_bytes()
        try:
            original = raw_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise LSPError(
                f"workspace edit targets {path}, which is not "
                f"utf-8 text — the whole edit is refused") from exc
        edits = [PlannedTextEdit.from_lsp(item, str(target))
                 for item in by_uri[uri]]
        if not edits:
            continue
        starts = _line_starts(original)
        spans = [(_edit_offset(starts, original, e.line,
                               e.character, str(target)),
                  _edit_offset(starts, original, e.end_line,
                               e.end_character, str(target)))
                 for e in edits]
        for i, (start, end) in enumerate(spans):
            for j, (other_start, other_end) in enumerate(spans):
                if i == j:
                    continue
                overlaps = start < other_end and other_start < end
                same_insert = start == end == other_start == other_end
                if overlaps or same_insert:
                    raise LSPError(
                        f"overlapping edits in {target} (line "
                        f"{edits[i].line} and line "
                        f"{edits[j].line}) — overlapping edits "
                        f"are refused, never force-edited")
        settled: List[PlannedTextEdit] = []
        for edit in edits:
            preview = _apply_planned_edits(original, [edit],
                                           str(target))
            settled.append(PlannedTextEdit(
                path=edit.path, line=edit.line,
                character=edit.character, end_line=edit.end_line,
                end_character=edit.end_character,
                new_text=edit.new_text,
                diff=_unified_diff(str(target), original, preview)))
        new_content = _apply_planned_edits(original, settled,
                                           str(target))
        files.append(FileEditPlan(
            path=str(target),
            sha256=hashlib.sha256(raw_bytes).hexdigest(),
            new_content=new_content, edits=settled,
            diff=_unified_diff(str(target), original, new_content)))
    return WorkspaceEditPlan(files=files)


@dataclass
class EditFileOutcome:
    """One file's application outcome, with its reason."""

    path: str = ""
    status: str = ""   # applied | refused-stale |
    # refused-outside-workspace | error
    reason: str = ""
    edits_applied: int = 0

    def record(self) -> Dict[str, Any]:
        return {
            "path": self.path, "status": self.status,
            "reason": self.reason,
            "edits_applied": self.edits_applied,
        }


@dataclass
class WorkspaceEditResult:
    """One applied plan: the plan and every file's outcome."""

    plan: WorkspaceEditPlan = field(default_factory=WorkspaceEditPlan)
    outcomes: List[EditFileOutcome] = field(default_factory=list)

    def record(self) -> Dict[str, Any]:
        counts: Dict[str, int] = {}
        for outcome in self.outcomes:
            counts[outcome.status] = counts.get(outcome.status, 0) + 1
        return {
            "plan": self.plan.record(),
            "outcomes": [o.record() for o in self.outcomes],
            "counts": counts,
        }


def apply_workspace_edit_plan(root: Path | str,
                              plan: WorkspaceEditPlan
                              ) -> WorkspaceEditResult:
    """Apply *plan* — and only a plan (no preview, no
    application, by construction).

    Per file: the file is re-read and its sha256 compared
    with the plan's; a mismatch refuses the whole file
    (``refused-stale``) and writes nothing in it. A file
    outside the workspace is refused. Otherwise the planned
    new content is written through the house
    :class:`EditJournal` — journal-first, one journaled
    write per file. One file's refusal never blocks the
    others.
    """
    base = Path(root).resolve()
    journal: Optional[EditJournal] = None
    outcomes: List[EditFileOutcome] = []
    for file_plan in plan.files:
        target = Path(file_plan.path)
        try:
            relative = target.resolve().relative_to(base)
        except ValueError:
            outcomes.append(EditFileOutcome(
                file_plan.path, "refused-outside-workspace",
                "the planned file is outside this workspace, "
                "so the edit journal cannot write it — the "
                "file is refused and nothing was written in it",
                0))
            continue
        try:
            raw = target.read_bytes()
        except OSError as exc:
            outcomes.append(EditFileOutcome(
                file_plan.path, "error",
                f"unreadable at apply time: {exc}", 0))
            continue
        if hashlib.sha256(raw).hexdigest() != file_plan.sha256:
            outcomes.append(EditFileOutcome(
                file_plan.path, "refused-stale",
                "the file changed since the plan was made — "
                "its content no longer matches the plan's "
                "hash, so the whole file is refused and "
                "nothing in it was written; plan again to "
                "edit its new shape", 0))
            continue
        try:
            if journal is None:
                journal = EditJournal(base)
            journal.write(relative.as_posix(), file_plan.new_content)
        except Exception as exc:
            outcomes.append(EditFileOutcome(
                file_plan.path, "error", str(exc), 0))
            continue
        outcomes.append(EditFileOutcome(
            file_plan.path, "applied", "", len(file_plan.edits)))
    return WorkspaceEditResult(plan=plan, outcomes=outcomes)


@dataclass
class RenamePreparation:
    """The server's prepareRename answer, as a plain record."""

    range: Optional[NavLocation] = None
    placeholder: str = ""
    default_behavior: bool = False

    @classmethod
    def from_lsp_result(cls, result: Any,
                        path: str = "") -> "RenamePreparation":
        """Build a record from one prepareRename result.

        A null (or empty) result is the server saying this
        spot cannot be renamed — refused plainly in those
        terms, never guessed around. The wire shapes: a
        bare Range, a ``{range, placeholder}`` pair, and a
        ``{defaultBehavior}`` answer.
        """
        if result is None or result == {}:
            raise LSPError(
                "the server says this spot cannot be renamed "
                "(prepareRename returned no renameable range)")
        if not isinstance(result, dict):
            raise LSPError(
                f"prepareRename result is not an object: "
                f"{result!r}")
        if "start" in result and "end" in result:
            return cls(range=NavLocation.from_range(result, path))
        if isinstance(result.get("range"), dict):
            return cls(
                range=NavLocation.from_range(result["range"], path),
                placeholder=str(result.get("placeholder", "") or ""))
        if "defaultBehavior" in result:
            return cls(default_behavior=bool(result["defaultBehavior"]))
        raise LSPError(
            f"prepareRename result is malformed (it needs a "
            f"range or a defaultBehavior): {result!r}")

    def record(self) -> Dict[str, Any]:
        return {
            "range": self.range.record() if self.range else None,
            "placeholder": self.placeholder,
            "default_behavior": self.default_behavior,
        }


#: Why a code action's command is never run, in plain words.
COMMAND_NOT_EXECUTED_NOTE = (
    "this action carries a server command, and Mythic does "
    "not execute server commands — no house road runs them; "
    "only an action's edit can be applied")


@dataclass
class CodeActionRecord:
    """One code action the server offers, as a plain record."""

    title: str = ""
    kind: str = ""
    diagnostics: List[Diagnostic] = field(default_factory=list)
    edit: Optional[WorkspaceEditPlan] = None
    command: Optional[Dict[str, Any]] = None
    disabled_reason: str = ""
    is_preferred: bool = False

    @property
    def has_edit(self) -> bool:
        return self.edit is not None

    @property
    def has_command(self) -> bool:
        return self.command is not None

    @classmethod
    def from_lsp(cls, raw: Any, root: Path | str,
                 document_uri: str = "") -> "CodeActionRecord":
        """Build a record from one codeAction result entry.

        Two wire shapes land here: a bare Command
        (``{title, command: <string>, arguments}``) and a
        CodeAction (``{title, kind, diagnostics, edit,
        command: <Command object>, disabled,
        isPreferred}``). The action's edit, where it
        carries one, is parsed into a plan at list time —
        so it carries its plan-time hashes and previews,
        and a malformed edit is refused plainly here,
        never at apply time.
        """
        if not isinstance(raw, dict):
            raise LSPError(f"code action is not an object: {raw!r}")
        title = str(raw.get("title", "") or "")
        wire_command = raw.get("command")
        command: Optional[Dict[str, Any]] = None
        if isinstance(wire_command, str):
            # A bare Command entry.
            return cls(
                title=title, kind="",
                command={"title": title, "command": wire_command,
                         "arguments": raw.get("arguments") or []})
        if isinstance(wire_command, dict):
            command = {
                "title": str(wire_command.get("title", "") or ""),
                "command": str(wire_command.get("command", "") or ""),
                "arguments": wire_command.get("arguments") or [],
            }
        diagnostics = [
            Diagnostic.from_lsp(item, document_uri)
            for item in raw.get("diagnostics") or []]
        edit = None
        if raw.get("edit") is not None:
            edit = parse_workspace_edit(raw["edit"], root)
        disabled = raw.get("disabled")
        disabled_reason = ""
        if isinstance(disabled, dict):
            disabled_reason = str(disabled.get("reason", "") or "")
        return cls(
            title=title, kind=str(raw.get("kind", "") or ""),
            diagnostics=diagnostics, edit=edit, command=command,
            disabled_reason=disabled_reason,
            is_preferred=bool(raw.get("isPreferred", False)))

    def record(self) -> Dict[str, Any]:
        return {
            "title": self.title, "kind": self.kind,
            "diagnostics": [d.record() for d in self.diagnostics],
            "has_edit": self.has_edit,
            "has_command": self.has_command,
            "edit": self.edit.record() if self.edit else None,
            "command": self.command,
            "command_executed": False,
            "command_note": COMMAND_NOT_EXECUTED_NOTE
            if self.has_command else "",
            "disabled_reason": self.disabled_reason,
            "is_preferred": self.is_preferred,
        }

    def one_line(self) -> str:
        carries = []
        if self.has_edit:
            carries.append("carries an edit")
        if self.has_command:
            carries.append("carries a command (not executed)")
        if not carries:
            carries.append("carries no edit or command")
        kind = f" ({self.kind})" if self.kind else ""
        return f"{self.title}{kind} — {', '.join(carries)}"


@dataclass
class RenameReport:
    """One rename question's whole account (M-051)."""

    action: str = "rename"
    path: str = ""
    server: Optional[str] = None
    status: str = "ok"   # ok | not-installed | no-server
    note: str = ""
    new_name: str = ""
    preparation: Optional[RenamePreparation] = None
    plan: Optional[WorkspaceEditPlan] = None
    outcomes: List[EditFileOutcome] = field(default_factory=list)
    applied: bool = False

    def record(self) -> Dict[str, Any]:
        return {
            "action": self.action, "path": self.path,
            "server": self.server, "status": self.status,
            "note": self.note, "new_name": self.new_name,
            "preparation": self.preparation.record()
            if self.preparation else None,
            "plan": self.plan.record() if self.plan else None,
            "outcomes": [o.record() for o in self.outcomes],
            "applied": self.applied,
        }


@dataclass
class CodeActionsReport:
    """One code-action question's whole account (M-051)."""

    action: str = "code_actions"
    path: str = ""
    server: Optional[str] = None
    status: str = "ok"   # ok | not-installed | no-server
    note: str = ""
    actions: List[CodeActionRecord] = field(default_factory=list)
    outcomes: List[EditFileOutcome] = field(default_factory=list)
    applied_index: Optional[int] = None
    apply_note: str = ""

    def record(self) -> Dict[str, Any]:
        return {
            "action": self.action, "path": self.path,
            "server": self.server, "status": self.status,
            "note": self.note,
            "actions": [a.record() for a in self.actions],
            "outcomes": [o.record() for o in self.outcomes],
            "applied_index": self.applied_index,
            "apply_note": self.apply_note,
        }


# ---------------------------------------------------------------------------
# JSON-RPC framing
# ---------------------------------------------------------------------------

def encode_message(message: Dict[str, Any]) -> bytes:
    """One message as a Content-Length framed LSP frame."""
    body = json.dumps(message).encode("utf-8")
    return b"Content-Length: %d\r\n\r\n" % len(body) + body


def read_message(stream: BinaryIO) -> Optional[Dict[str, Any]]:
    """Read one framed message; None at a clean end of stream.

    A frame without a Content-Length header, and a body that
    is not a JSON object, are refused plainly.
    """
    content_length: Optional[int] = None
    while True:
        line = stream.readline()
        if not line:
            return None
        stripped = line.strip()
        if not stripped:
            break
        name, _, value = stripped.partition(b":")
        if name.strip().lower() == b"content-length":
            try:
                content_length = int(value.strip())
            except ValueError as exc:
                raise LSPError(
                    f"bad Content-Length header: {value!r}") from exc
    if content_length is None:
        raise LSPError("LSP frame arrived without a Content-Length")
    body = b""
    while len(body) < content_length:
        chunk = stream.read(content_length - len(body))
        if not chunk:
            return None
        body += chunk
    try:
        parsed = json.loads(body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise LSPError(f"LSP frame body is not JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise LSPError(f"LSP message is not an object: {parsed!r}")
    return parsed


# ---------------------------------------------------------------------------
# The client
# ---------------------------------------------------------------------------

class LSPClient:
    """One language server process, spoken to over stdio.

    The transport is a subprocess by default; tests may hand
    in a *process_factory* returning any object with binary
    ``stdin`` / ``stdout`` streams plus ``poll()``,
    ``terminate()``, and ``kill()`` — the shape
    :class:`subprocess.Popen` already has.
    """

    def __init__(self, server: ServerDef, root: Path | str, *,
                 process_factory: Optional[Callable[..., Any]] = None,
                 timeout: float = 10.0) -> None:
        self.server = server
        self.root = Path(root).resolve()
        self.timeout = timeout
        self._factory = process_factory or subprocess.Popen
        self._process: Any = None
        self._next_id = 0
        self._pending: Dict[int, Dict[str, Any]] = {}
        self._pending_errors: Dict[int, str] = {}
        self._diagnostics: Dict[str, List[Diagnostic]] = {}
        self._condition = threading.Condition()
        self._reader: Optional[threading.Thread] = None
        self._reader_error: Optional[str] = None
        self._server_name = server.name
        self._closed = False
        self._opened_uris: set = set()

    # -- lifecycle ----------------------------------------------------

    def start(self) -> Dict[str, Any]:
        """Launch the server and run the initialize handshake.

        Returns the server's initialize result (its declared
        capabilities, in its own words). A binary that is not
        installed raises :class:`LSPError` carrying the
        catalogue's install remedy.
        """
        if self._process is not None:
            raise LSPError(f"{self.server.name} is already running")
        if self.server.installed_path() is None and \
                self._factory is subprocess.Popen:
            raise LSPError(
                f"the {self.server.name} language server is not "
                f"installed: {self.server.install_remedy}")
        try:
            self._process = self._factory(
                list(self.server.command),
                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, cwd=str(self.root))
        except FileNotFoundError as exc:
            raise LSPError(
                f"the {self.server.name} language server is not "
                f"installed: {self.server.install_remedy}") from exc
        self._reader = threading.Thread(
            target=self._read_loop, name=f"lsp-{self.server.name}",
            daemon=True)
        self._reader.start()
        root_uri = path_to_uri(self.root)
        result = self._request("initialize", {
            "processId": None,
            "rootUri": root_uri,
            "capabilities": {
                "textDocument": {
                    "publishDiagnostics": {
                        "relatedInformation": True,
                        "versionSupport": True,
                    },
                    "synchronization": {"didSave": True},
                    "definition": {},
                    "references": {},
                    "hover": {
                        "contentFormat": ["markdown", "plaintext"],
                    },
                    "rename": {"prepareSupport": True},
                    "codeAction": {
                        "codeActionLiteralSupport": {
                            "codeActionKind": {
                                "valueSet": [
                                    "", "quickfix", "refactor",
                                    "refactor.extract",
                                    "refactor.inline",
                                    "refactor.rewrite", "source",
                                    "source.organizeImports",
                                ],
                            },
                        },
                    },
                },
                "workspace": {
                    "configuration": True,
                    "symbol": {},
                },
            },
            "workspaceFolders": [{"uri": root_uri,
                                  "name": self.root.name}],
        })
        info = result.get("serverInfo") or {}
        if info.get("name"):
            self._server_name = str(info["name"])
        self._notify("initialized", {})
        return result

    def close(self) -> None:
        """Shut the server down politely, then firmly if needed.

        After the ``exit`` notification the process is given
        a bounded moment to end on its own — terminating it
        the instant the notification is flushed would kill
        it before it could act on the shutdown it just
        acknowledged, which under load loses the orderly
        end entirely.
        """
        if self._process is None or self._closed:
            return
        self._closed = True
        try:
            self._request("shutdown", None, timeout=5.0)
        except LSPError:
            pass
        try:
            self._notify("exit", None)
        except LSPError:
            pass
        process, self._process = self._process, None
        try:
            if process.poll() is None:
                try:
                    process.wait(timeout=2.0)
                except Exception:
                    process.terminate()
        except Exception:
            pass

    def __enter__(self) -> "LSPClient":
        self.start()
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # -- documents ------------------------------------------------------

    def _require_running(self) -> None:
        if self._process is None:
            raise LSPError(
                f"the {self.server.name} language server is not "
                f"running; start the client first")

    def _resolve_target(self, path: Path | str) -> Path:
        target = Path(path)
        if not target.is_absolute():
            target = self.root / target
        if not target.is_file():
            raise LSPError(f"no such file to check: {target}")
        return target

    def _open_document(self, path: Path | str) -> Tuple[Path, str]:
        """Open one file in the server, once per URI per client.

        Returns the resolved target and its URI. Every
        question about a file (diagnostics, definition,
        references, hover) opens it through here, so the
        ``didOpen`` notification is sent exactly once.
        """
        self._require_running()
        target = self._resolve_target(path)
        uri = path_to_uri(target)
        if uri not in self._opened_uris:
            text = target.read_text(encoding="utf-8",
                                    errors="replace")
            language_id = language_id_for(target) or "plaintext"
            self._notify("textDocument/didOpen", {
                "textDocument": {
                    "uri": uri, "languageId": language_id,
                    "version": 1, "text": text,
                },
            })
            self._opened_uris.add(uri)
        return target, uri

    @staticmethod
    def _validate_position(line: Any, character: Any) -> None:
        if isinstance(line, bool) or isinstance(character, bool) \
                or not isinstance(line, int) \
                or not isinstance(character, int) \
                or line < 1 or character < 1:
            raise ValueError(
                f"line and character must be positive integers "
                f"(1-based, the way editors count), got "
                f"line={line!r}, character={character!r}")

    def _position_params(self, path: Path | str, line: int,
                         character: int) -> Tuple[Path, Dict[str, Any]]:
        self._validate_position(line, character)
        target, uri = self._open_document(path)
        return target, {
            "textDocument": {"uri": uri},
            "position": {"line": line - 1,
                         "character": character - 1},
        }

    # -- diagnostics ----------------------------------------------------

    def diagnostics_for(self, path: Path | str, *,
                        timeout: Optional[float] = None
                        ) -> DiagnosticsReport:
        """Open one file in the server and collect its diagnostics.

        Waits until the server publishes diagnostics for the
        file's URI or *timeout* passes. A timeout raises
        :class:`LSPError` — the server looked but its answer
        never arrived is not the same as a clean file, and it
        is never reported as one.
        """
        target, uri = self._open_document(path)
        wait = self.timeout if timeout is None else timeout
        with self._condition:
            arrived = self._condition.wait_for(
                lambda: uri in self._diagnostics
                or self._reader_error is not None,
                timeout=wait)
            if self._reader_error is not None:
                raise LSPError(self._reader_error)
            if not arrived:
                raise LSPError(
                    f"the {self.server.name} language server sent "
                    f"no diagnostics for {target.name} within "
                    f"{wait:g}s — its answer is unknown, not clean")
            found = list(self._diagnostics.get(uri, []))
        return DiagnosticsReport(
            path=str(target), server=self._server_name,
            status="ok", diagnostics=found)

    # -- navigation (M-050) ---------------------------------------------

    @staticmethod
    def _locations_from_result(result: Any) -> List[NavLocation]:
        """A definition/references result as location records.

        The wire answer may be null (no answer — an empty
        list, the server's own answer), one Location or
        LocationLink object, or a list of them.
        """
        if result is None or result == {} or result == []:
            return []
        if isinstance(result, dict):
            return [NavLocation.from_lsp_location(result)]
        if isinstance(result, list):
            return [NavLocation.from_lsp_location(raw)
                    for raw in result]
        raise LSPError(
            f"navigation result is not a location or a list: "
            f"{result!r}")

    def definition(self, path: Path | str, line: int,
                   character: int) -> List[NavLocation]:
        """Where the name at a 1-based position is defined."""
        _target, params = self._position_params(path, line, character)
        result = self._request("textDocument/definition", params)
        return self._locations_from_result(result)

    def references(self, path: Path | str, line: int, character: int,
                   include_declaration: bool = True
                   ) -> List[NavLocation]:
        """Every place the name at a 1-based position is used."""
        _target, params = self._position_params(path, line, character)
        params["context"] = {
            "includeDeclaration": bool(include_declaration)}
        result = self._request("textDocument/references", params)
        return self._locations_from_result(result)

    def hover(self, path: Path | str, line: int,
              character: int) -> HoverInfo:
        """What the server says about a 1-based position."""
        target, params = self._position_params(path, line, character)
        result = self._request("textDocument/hover", params)
        return HoverInfo.from_lsp_result(result, path=str(target))

    # -- rename and code actions (M-051) ----------------------------

    def prepare_rename(self, path: Path | str, line: int,
                       character: int) -> RenamePreparation:
        """Whether the server says a 1-based spot can be renamed.

        A spot the server refuses — a null answer, or a
        server error riding the request road — is refused
        plainly here, in the server's terms; a rename is
        never guessed around that answer.
        """
        target, params = self._position_params(path, line, character)
        result = self._request("textDocument/prepareRename", params)
        return RenamePreparation.from_lsp_result(result,
                                                 path=str(target))

    def rename(self, path: Path | str, line: int, character: int,
               new_name: str, *,
               _preparation: Optional[RenamePreparation] = None
               ) -> WorkspaceEditPlan:
        """Plan a rename of the name at a 1-based position.

        prepareRename is asked first (unless a preparation
        is handed in); its refusal ends the rename before
        the rename request is ever sent. The server's
        WorkspaceEdit comes back as a per-file plan —
        nothing is written by planning.
        """
        if not isinstance(new_name, str) or not new_name.strip():
            raise ValueError(
                "the new name must be a non-empty string")
        if any(ch.isspace() for ch in new_name):
            raise ValueError(
                f"the new name {new_name!r} contains whitespace "
                f"— a renamed symbol's name is one word")
        if _preparation is None:
            self.prepare_rename(path, line, character)
        _target, params = self._position_params(path, line, character)
        params["newName"] = new_name
        result = self._request("textDocument/rename", params)
        return parse_workspace_edit(result, self.root)

    def code_actions(self, path: Path | str, line: int,
                     character: int, *,
                     end_line: Optional[int] = None,
                     end_character: Optional[int] = None
                     ) -> List[CodeActionRecord]:
        """The code actions the server offers at a position.

        The asked range is the position itself, or the
        position through *end_line* / *end_character* where
        given. Each action's edit is parsed into a plan at
        list time, so listing is also the preview.
        """
        self._validate_position(line, character)
        if end_line is None:
            end_line = line
        if end_character is None:
            end_character = character
        self._validate_position(end_line, end_character)
        target, uri = self._open_document(path)
        result = self._request("textDocument/codeAction", {
            "textDocument": {"uri": uri},
            "range": {
                "start": {"line": line - 1,
                          "character": character - 1},
                "end": {"line": end_line - 1,
                        "character": end_character - 1},
            },
            "context": {"diagnostics": []},
        })
        if result is None or result == {} or result == []:
            return []
        if not isinstance(result, list):
            raise LSPError(
                f"codeAction result is not a list: {result!r}")
        return [CodeActionRecord.from_lsp(raw, self.root,
                                          document_uri=uri)
                for raw in result]

    def workspace_symbols(self, query: str = "") -> List[WorkspaceSymbol]:
        """The workspace's symbols, optionally filtered by *query*."""
        self._require_running()
        result = self._request("workspace/symbol", {"query": query})
        if result is None or result == {} or result == []:
            return []
        if not isinstance(result, list):
            raise LSPError(
                f"workspace/symbol result is not a list: {result!r}")
        found: List[WorkspaceSymbol] = []
        for raw in result:
            found.extend(WorkspaceSymbol.flatten(raw))
        return found

    # -- wire machinery -------------------------------------------------

    def _read_loop(self) -> None:
        stream = self._process.stdout
        try:
            while True:
                message = read_message(stream)
                if message is None:
                    break
                self._dispatch(message)
        except (LSPError, OSError) as exc:
            with self._condition:
                if self._reader_error is None:
                    self._reader_error = (
                        f"the {self.server.name} language server's "
                        f"stream failed: {exc}")
                self._condition.notify_all()
            return
        with self._condition:
            if self._reader_error is None and not self._closed:
                self._reader_error = (
                    f"the {self.server.name} language server "
                    f"exited before its work was done")
            self._condition.notify_all()

    def _dispatch(self, message: Dict[str, Any]) -> None:
        method = message.get("method")
        if method == "textDocument/publishDiagnostics":
            params = message.get("params") or {}
            uri = str(params.get("uri", ""))
            found = [Diagnostic.from_lsp(raw, uri)
                     for raw in params.get("diagnostics", [])]
            with self._condition:
                self._diagnostics[uri] = found
                self._condition.notify_all()
            return
        if "id" in message and method is not None:
            # A server-to-client request: answer null rather
            # than leave the server waiting on us forever.
            self._send({"jsonrpc": "2.0", "id": message["id"],
                        "result": None})
            return
        if "id" in message:
            with self._condition:
                ident = message["id"]
                error = message.get("error")
                if error is not None:
                    self._pending_errors[ident] = str(
                        error.get("message", error))
                else:
                    self._pending[ident] = message.get("result") or {}
                self._condition.notify_all()

    def _send(self, message: Dict[str, Any]) -> None:
        process = self._process
        if process is None or process.stdin is None:
            raise LSPError(
                f"the {self.server.name} language server is not "
                f"running")
        try:
            process.stdin.write(encode_message(message))
            process.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            raise LSPError(
                f"writing to the {self.server.name} language "
                f"server failed: {exc}") from exc

    def _notify(self, method: str, params: Optional[Any]) -> None:
        self._send({"jsonrpc": "2.0", "method": method,
                    "params": params})

    def _request(self, method: str, params: Optional[Any], *,
                 timeout: Optional[float] = None) -> Dict[str, Any]:
        self._next_id += 1
        ident = self._next_id
        self._send({"jsonrpc": "2.0", "id": ident,
                    "method": method, "params": params})
        wait = self.timeout if timeout is None else timeout
        with self._condition:
            arrived = self._condition.wait_for(
                lambda: ident in self._pending
                or ident in self._pending_errors
                or self._reader_error is not None,
                timeout=wait)
            if ident in self._pending_errors:
                raise LSPError(
                    f"the {self.server.name} language server "
                    f"refused {method}: "
                    f"{self._pending_errors.pop(ident)}")
            if ident in self._pending:
                return self._pending.pop(ident)
            if self._reader_error is not None:
                raise LSPError(self._reader_error)
            if not arrived:
                raise LSPError(
                    f"the {self.server.name} language server did "
                    f"not answer {method} within {wait:g}s")
        raise LSPError(f"the {self.server.name} request failed")


# ---------------------------------------------------------------------------
# One file's report, end to end
# ---------------------------------------------------------------------------

def diagnostics_for_file(path: Path | str, *,
                         root: Optional[Path | str] = None,
                         timeout: float = 10.0,
                         client_factory: Optional[
                             Callable[..., LSPClient]] = None
                         ) -> DiagnosticsReport:
    """One file's diagnostics report, with honest absence.

    No catalogued server for the file's language, and a
    catalogued server that is not installed, are reports —
    never raised, never dressed as a clean file. A server
    that runs and then fails raises :class:`LSPError`.
    """
    target = Path(path)
    base = Path(root).resolve() if root is not None \
        else target.resolve().parent
    if not target.is_absolute():
        target = base / target
    server = server_for_path(target)
    if server is None:
        return DiagnosticsReport(
            path=str(target), server=None, status="no-server",
            note=f"no language server is catalogued for "
                 f"{target.suffix or 'this file'} files — "
                 f"nothing checked this file")
    if server.installed_path() is None and client_factory is None:
        return DiagnosticsReport(
            path=str(target), server=server.name,
            status="not-installed",
            note=f"the {server.name} language server is not "
                 f"installed, so nothing checked this file; "
                 f"{server.install_remedy}")
    factory = client_factory or (
        lambda srv, rt: LSPClient(srv, rt, timeout=timeout))
    client = factory(server, base)
    client.start()
    try:
        return client.diagnostics_for(target, timeout=timeout)
    finally:
        client.close()


# ---------------------------------------------------------------------------
# Navigation questions, end to end (M-050)
# ---------------------------------------------------------------------------

def _navigation_report(action: str, target: Path,
                       server: Optional[ServerDef], status: str,
                       note: str) -> NavigationReport:
    return NavigationReport(
        action=action, path=str(target),
        server=server.name if server is not None else None,
        status=status, note=note)


def _file_navigation(action: str, path: Path | str, line: int,
                     character: int, *,
                     root: Optional[Path | str],
                     timeout: float,
                     client_factory: Optional[
                         Callable[..., LSPClient]],
                     ask: Callable[..., Any]
                     ) -> NavigationReport:
    """One file navigation question, with honest absence.

    Mirrors :func:`diagnostics_for_file`: no catalogued
    server and a server that is not installed are reports —
    never raised, never dressed as a found answer. A server
    that runs and then fails raises :class:`LSPError`.
    """
    LSPClient._validate_position(line, character)
    target = Path(path)
    base = Path(root).resolve() if root is not None \
        else target.resolve().parent
    if not target.is_absolute():
        target = base / target
    server = server_for_path(target)
    if server is None:
        return _navigation_report(
            action, target, None, "no-server",
            f"no language server is catalogued for "
            f"{target.suffix or 'this file'} files — "
            f"nothing answered this question")
    if server.installed_path() is None and client_factory is None:
        return _navigation_report(
            action, target, server, "not-installed",
            f"the {server.name} language server is not "
            f"installed, so nothing answered this question; "
            f"{server.install_remedy}")
    factory = client_factory or (
        lambda srv, rt: LSPClient(srv, rt, timeout=timeout))
    client = factory(server, base)
    client.start()
    try:
        report = _navigation_report(action, target, server, "ok", "")
        report.server = getattr(client, "_server_name", server.name)
        ask(client, target, report)
        return report
    finally:
        client.close()


def definition_for_file(path: Path | str, line: int, character: int, *,
                        root: Optional[Path | str] = None,
                        timeout: float = 10.0,
                        client_factory: Optional[
                            Callable[..., LSPClient]] = None
                        ) -> NavigationReport:
    """Where the name at a 1-based position is defined, end to end."""
    def _ask(client: LSPClient, target: Path,
             report: NavigationReport) -> None:
        report.locations = client.definition(target, line, character)

    return _file_navigation(
        "definition", path, line, character, root=root,
        timeout=timeout, client_factory=client_factory, ask=_ask)


def references_for_file(path: Path | str, line: int, character: int, *,
                        root: Optional[Path | str] = None,
                        timeout: float = 10.0,
                        client_factory: Optional[
                            Callable[..., LSPClient]] = None
                        ) -> NavigationReport:
    """Every use of the name at a 1-based position, end to end."""
    def _ask(client: LSPClient, target: Path,
             report: NavigationReport) -> None:
        report.locations = client.references(target, line, character)

    return _file_navigation(
        "references", path, line, character, root=root,
        timeout=timeout, client_factory=client_factory, ask=_ask)


def hover_for_file(path: Path | str, line: int, character: int, *,
                   root: Optional[Path | str] = None,
                   timeout: float = 10.0,
                   client_factory: Optional[
                       Callable[..., LSPClient]] = None
                   ) -> NavigationReport:
    """What the server says about a 1-based position, end to end."""
    def _ask(client: LSPClient, target: Path,
             report: NavigationReport) -> None:
        report.hover = client.hover(target, line, character)

    return _file_navigation(
        "hover", path, line, character, root=root,
        timeout=timeout, client_factory=client_factory, ask=_ask)


def workspace_symbols_for(*, root: Optional[Path | str] = None,
                          query: str = "",
                          server_name: Optional[str] = None,
                          timeout: float = 10.0,
                          client_factory: Optional[
                              Callable[..., LSPClient]] = None
                          ) -> NavigationReport:
    """The workspace's symbols, with honest absence.

    The server is chosen by: an explicit *server_name*
    (an unknown name raises :class:`ValueError` plainly),
    else the first installed catalogued server, else —
    when a *client_factory* is supplied — the first
    catalogued server, else a not-installed report naming
    that no language server is installed, with the remedies.
    """
    base = Path(root).resolve() if root is not None else Path.cwd()
    server: Optional[ServerDef] = None
    if server_name is not None:
        wanted = server_name.strip().lower()
        for candidate in SERVERS:
            if candidate.name.lower() == wanted:
                server = candidate
                break
        if server is None:
            raise ValueError(
                f"unknown language server {server_name!r} — the "
                f"catalogued servers are "
                f"{', '.join(s.name for s in SERVERS)}")
    else:
        for candidate in SERVERS:
            if candidate.installed_path() is not None:
                server = candidate
                break
        if server is None and client_factory is not None:
            server = SERVERS[0]
    if server is None:
        remedies = "; ".join(
            f"{s.name}: {s.install_remedy}" for s in SERVERS)
        return NavigationReport(
            action="symbols", path=str(base), server=None,
            status="not-installed",
            note=f"no language server is installed, so nothing "
                 f"answered this question; {remedies}")
    if server.installed_path() is None and client_factory is None:
        return _navigation_report(
            "symbols", base, server, "not-installed",
            f"the {server.name} language server is not "
            f"installed, so nothing answered this question; "
            f"{server.install_remedy}")
    factory = client_factory or (
        lambda srv, rt: LSPClient(srv, rt, timeout=timeout))
    client = factory(server, base)
    client.start()
    try:
        report = _navigation_report("symbols", base, server, "ok", "")
        report.server = getattr(client, "_server_name", server.name)
        report.symbols = client.workspace_symbols(query)
        return report
    finally:
        client.close()


# ---------------------------------------------------------------------------
# Rename and code actions, end to end (M-051)
# ---------------------------------------------------------------------------

def _target_and_server(path: Path | str,
                       root: Optional[Path | str]
                       ) -> Tuple[Path, Path, Optional[ServerDef]]:
    target = Path(path)
    base = Path(root).resolve() if root is not None \
        else target.resolve().parent
    if not target.is_absolute():
        target = base / target
    return target, base, server_for_path(target)


def rename_for_file(path: Path | str, line: int, character: int,
                    new_name: str, *,
                    root: Optional[Path | str] = None,
                    timeout: float = 10.0,
                    apply: bool = False,
                    client_factory: Optional[
                        Callable[..., LSPClient]] = None
                    ) -> RenameReport:
    """Plan (and, only when *apply*, apply) a rename, end to end.

    Honest absence mirrors :func:`diagnostics_for_file`:
    no catalogued server and a server that is not
    installed are reports — never a faked rename, never a
    text substitution dressed as one. With *apply* false
    the report carries the plan and writes nothing; with
    *apply* true the plan is applied through
    :func:`apply_workspace_edit_plan` (the EditJournal
    road) and the report carries every file's outcome.
    """
    LSPClient._validate_position(line, character)
    if not isinstance(new_name, str) or not new_name.strip():
        raise ValueError("the new name must be a non-empty string")
    target, base, server = _target_and_server(path, root)
    if server is None:
        return RenameReport(
            path=str(target), server=None, status="no-server",
            new_name=new_name,
            note=f"no language server is catalogued for "
                 f"{target.suffix or 'this file'} files — "
                 f"nothing planned this rename")
    if server.installed_path() is None and client_factory is None:
        return RenameReport(
            path=str(target), server=server.name,
            status="not-installed", new_name=new_name,
            note=f"the {server.name} language server is not "
                 f"installed, so nothing planned this rename; "
                 f"{server.install_remedy}")
    factory = client_factory or (
        lambda srv, rt: LSPClient(srv, rt, timeout=timeout))
    client = factory(server, base)
    client.start()
    try:
        preparation = client.prepare_rename(target, line, character)
        plan = client.rename(target, line, character, new_name,
                             _preparation=preparation)
        report = RenameReport(
            path=str(target),
            server=getattr(client, "_server_name", server.name),
            status="ok", new_name=new_name,
            preparation=preparation, plan=plan)
    finally:
        client.close()
    if apply and plan is not None:
        result = apply_workspace_edit_plan(base, plan)
        report.outcomes = result.outcomes
        report.applied = True
    return report


def code_actions_for_file(path: Path | str, line: int, character: int, *,
                          root: Optional[Path | str] = None,
                          timeout: float = 10.0,
                          apply_index: Optional[int] = None,
                          client_factory: Optional[
                              Callable[..., LSPClient]] = None
                          ) -> CodeActionsReport:
    """List (and, only when *apply_index* is given, apply
    one of) a file's code actions, end to end.

    Honest absence mirrors :func:`rename_for_file`.
    *apply_index* is the 0-based index into the listed
    actions: an index past the list is refused plainly.
    Applying an action applies its WorkspaceEdit through
    the journal road; an action with no edit — in
    particular a command-only action — is reported in the
    report's ``apply_note``, its command never executed.
    """
    LSPClient._validate_position(line, character)
    if apply_index is not None and (
            isinstance(apply_index, bool)
            or not isinstance(apply_index, int)
            or apply_index < 0):
        raise ValueError(
            f"apply_index must be a non-negative integer or "
            f"None, got {apply_index!r}")
    target, base, server = _target_and_server(path, root)
    if server is None:
        return CodeActionsReport(
            path=str(target), server=None, status="no-server",
            note=f"no language server is catalogued for "
                 f"{target.suffix or 'this file'} files — "
                 f"nothing listed any code actions")
    if server.installed_path() is None and client_factory is None:
        return CodeActionsReport(
            path=str(target), server=server.name,
            status="not-installed",
            note=f"the {server.name} language server is not "
                 f"installed, so nothing listed any code "
                 f"actions; {server.install_remedy}")
    factory = client_factory or (
        lambda srv, rt: LSPClient(srv, rt, timeout=timeout))
    client = factory(server, base)
    client.start()
    try:
        actions = client.code_actions(target, line, character)
        report = CodeActionsReport(
            path=str(target),
            server=getattr(client, "_server_name", server.name),
            status="ok", actions=actions)
    finally:
        client.close()
    if apply_index is not None:
        if apply_index >= len(actions):
            raise ValueError(
                f"code action #{apply_index + 1} does not "
                f"exist — the server offered "
                f"{len(actions)} action(s)")
        chosen = actions[apply_index]
        report.applied_index = apply_index
        if chosen.edit is not None:
            result = apply_workspace_edit_plan(base, chosen.edit)
            report.outcomes = result.outcomes
            report.apply_note = (
                f"applied action #{apply_index + 1} "
                f"({chosen.title}) through the edit journal")
        elif chosen.has_command:
            report.apply_note = (
                f"action #{apply_index + 1} ({chosen.title}) "
                f"carries no edit — {COMMAND_NOT_EXECUTED_NOTE}")
        else:
            report.apply_note = (
                f"action #{apply_index + 1} ({chosen.title}) "
                f"carries no edit and no command — there was "
                f"nothing to apply")
    return report


# ---------------------------------------------------------------------------
# Surfaces: parser, formatters, markdown
# ---------------------------------------------------------------------------

_USAGE = (
    "Usage: /lsp [show] | /lsp check <path> | "
    "/lsp def <path> <line> <character> | "
    "/lsp refs <path> <line> <character> | "
    "/lsp hover <path> <line> <character> | "
    "/lsp symbols [query...] | "
    "/lsp rename <path> <line> <character> <new-name> [apply] | "
    "/lsp actions <path> <line> <character> [apply <n>]")

_POSITION_ACTIONS = {
    "def": "definition", "definition": "definition",
    "refs": "references", "references": "references",
    "hover": "hover",
}


def parse_lsp_args(arguments: str) -> Dict[str, Any]:
    """Parse ``/lsp`` arguments: the board, a check, or navigation."""
    text = (arguments or "").strip()
    if not text or text == "show":
        return {"action": "show"}
    parts = text.split(None, 1)
    if parts[0] == "check":
        if len(parts) < 2 or not parts[1].strip():
            raise ValueError(f"{_USAGE} — check needs a file path")
        return {"action": "check", "path": parts[1].strip()}
    if parts[0] == "show":
        raise ValueError(f"{_USAGE} — show takes no further words")
    if parts[0] in _POSITION_ACTIONS:
        action = _POSITION_ACTIONS[parts[0]]
        tokens = text.split()
        if len(tokens) != 4:
            raise ValueError(
                f"{_USAGE} — {parts[0]} needs a file path, a "
                f"line, and a character")
        try:
            line = int(tokens[2])
            character = int(tokens[3])
        except ValueError:
            raise ValueError(
                f"{_USAGE} — line and character must be "
                f"whole numbers") from None
        return {"action": action, "path": tokens[1],
                "line": line, "character": character}
    if parts[0] == "symbols":
        query = parts[1].strip() if len(parts) > 1 else ""
        return {"action": "symbols", "query": query}
    if parts[0] == "rename":
        tokens = text.split()
        if len(tokens) not in (5, 6):
            raise ValueError(
                f"{_USAGE} — rename needs a file path, a "
                f"line, a character, and a new name")
        apply_flag = False
        if len(tokens) == 6:
            if tokens[5] != "apply":
                raise ValueError(
                    f"{_USAGE} — rename's last word may only "
                    f"be 'apply'")
            apply_flag = True
        try:
            line = int(tokens[2])
            character = int(tokens[3])
        except ValueError:
            raise ValueError(
                f"{_USAGE} — line and character must be "
                f"whole numbers") from None
        return {"action": "rename", "path": tokens[1],
                "line": line, "character": character,
                "new_name": tokens[4], "apply": apply_flag}
    if parts[0] in ("actions", "codeactions", "code-actions"):
        tokens = text.split()
        if len(tokens) not in (4, 6):
            raise ValueError(
                f"{_USAGE} — actions needs a file path, a "
                f"line, and a character, optionally followed "
                f"by 'apply <n>'")
        apply_index: Optional[int] = None
        if len(tokens) == 6:
            if tokens[4] != "apply":
                raise ValueError(
                    f"{_USAGE} — actions' extra words may "
                    f"only be 'apply <n>'")
            try:
                number = int(tokens[5])
            except ValueError:
                raise ValueError(
                    f"{_USAGE} — apply needs the action's "
                    f"number, a whole number") from None
            if number < 1:
                raise ValueError(
                    f"{_USAGE} — actions are numbered from 1")
            apply_index = number - 1
        try:
            line = int(tokens[2])
            character = int(tokens[3])
        except ValueError:
            raise ValueError(
                f"{_USAGE} — line and character must be "
                f"whole numbers") from None
        return {"action": "code_actions", "path": tokens[1],
                "line": line, "character": character,
                "apply_index": apply_index}
    # A bare path is a check of that path, the kind reading.
    return {"action": "check", "path": text}


def format_lsp_status(status: Dict[str, Any]) -> str:
    """The discovery board, as plain words."""
    lines = [PLAIN_EXPLANATION, "", "Language servers:"]
    for entry in status["servers"]:
        if entry["installed"]:
            lines.append(
                f"  {entry['name']}: installed "
                f"({entry['path']}) — serves "
                f"{', '.join(entry['languages'])}")
        else:
            lines.append(
                f"  {entry['name']}: NOT INSTALLED — serves "
                f"{', '.join(entry['languages'])}; "
                f"{entry['install_remedy']}")
    return "\n".join(lines)


def format_lsp_diagnostics(status: Dict[str, Any]) -> str:
    """One file's report, as plain words."""
    report = status["report"]
    lines = [f"Diagnostics for {report['path']}:"]
    if report["status"] == "no-server":
        lines.append(f"  {report['note']}")
        return "\n".join(lines)
    if report["status"] == "not-installed":
        lines.append(
            f"  NOT CHECKED — {report['note']}")
        return "\n".join(lines)
    found = report["diagnostics"]
    if not found:
        lines.append(
            f"  {report['server']} reported no problems.")
        return "\n".join(lines)
    lines.append(
        f"  {report['server']} reported {len(found)} "
        f"problem(s):")
    for raw in found:
        diagnostic = Diagnostic(**{
            key: raw[key] for key in (
                "path", "line", "character", "end_line",
                "end_character", "severity", "message",
                "source", "code")})
        lines.append(f"  {diagnostic.one_line()}")
    return "\n".join(lines)


_NAVIGATION_TITLES = {
    "definition": "Definition",
    "references": "References",
    "hover": "Hover",
    "symbols": "Workspace symbols",
}


def format_lsp_navigation(status: Dict[str, Any]) -> str:
    """One navigation report, as plain words (M-050)."""
    report = status["report"]
    action = report["action"]
    title = _NAVIGATION_TITLES.get(action, "Navigation")
    if action == "symbols":
        lines = [f"Workspace symbols in {report['path']}:"]
    else:
        lines = [f"{title} for {report['path']}:"]
    if report["status"] in ("no-server", "not-installed"):
        lines.append(f"  NOT ANSWERED — {report['note']}")
        return "\n".join(lines)
    if action in ("definition", "references"):
        found = report["locations"]
        if not found:
            lines.append(
                f"  the server found no "
                f"{'definition' if action == 'definition' else 'references'}.")
            return "\n".join(lines)
        lines.append(
            f"  {report['server']} found {len(found)} "
            f"{'definition' if action == 'definition' else 'reference'}(s):")
        for raw in found:
            location = NavLocation(**{
                key: raw[key] for key in (
                    "path", "line", "character", "end_line",
                    "end_character")})
            lines.append(f"  {location.one_line()}")
        return "\n".join(lines)
    if action == "hover":
        hover = report["hover"]
        contents = hover["contents"] if hover else ""
        if not contents:
            lines.append("  the server said nothing about that spot")
            return "\n".join(lines)
        lines.append(f"  {report['server']} says:")
        for chunk in contents.splitlines():
            lines.append(f"  {chunk}")
        return "\n".join(lines)
    if action == "symbols":
        found = report["symbols"]
        if not found:
            lines.append(f"  {report['server']} found no symbols.")
            return "\n".join(lines)
        lines.append(
            f"  {report['server']} found {len(found)} symbol(s):")
        for raw in found:
            location = NavLocation(**{
                key: raw["location"][key] for key in (
                    "path", "line", "character", "end_line",
                    "end_character")})
            symbol = WorkspaceSymbol(
                name=raw["name"], kind=raw["kind"],
                container_name=raw["container_name"],
                location=location)
            lines.append(f"  {symbol.one_line()}")
        return "\n".join(lines)
    lines.append(f"  {report['note']}")
    return "\n".join(lines)


def format_lsp_rename(status: Dict[str, Any]) -> str:
    """One rename report, as plain words (M-051)."""
    report = status["report"]
    lines = [f"Rename in {report['path']} "
             f"-> {report['new_name']!r}:"]
    if report["status"] in ("no-server", "not-installed"):
        lines.append(f"  NOT PLANNED — {report['note']}")
        return "\n".join(lines)
    plan = report["plan"]
    if plan is None or not plan["files"]:
        lines.append(
            f"  {report['server']} planned no edits — "
            f"there is nothing to rename.")
        return "\n".join(lines)
    counts = plan["counts"]
    verb = "applied through the edit journal" \
        if report["applied"] else "preview only — nothing written"
    lines.append(
        f"  {report['server']} planned {counts['edits']} "
        f"edit(s) across {counts['files']} file(s) — {verb}.")
    for file_plan in plan["files"]:
        lines.append(f"  {file_plan['path']}:")
        for edit in file_plan["edits"]:
            lines.append(
                f"    line {edit['line']}, character "
                f"{edit['character']} -> {edit['new_text']!r}")
        for diff_line in file_plan["diff"].splitlines():
            lines.append(f"    {diff_line}")
    for outcome in report["outcomes"]:
        detail = f" — {outcome['reason']}" if outcome["reason"] \
            else f" ({outcome['edits_applied']} edit(s))"
        lines.append(
            f"  {outcome['status']}: {outcome['path']}{detail}")
    return "\n".join(lines)


def format_lsp_code_actions(status: Dict[str, Any]) -> str:
    """One code-action report, as plain words (M-051)."""
    report = status["report"]
    lines = [f"Code actions for {report['path']}:"]
    if report["status"] in ("no-server", "not-installed"):
        lines.append(f"  NOT ANSWERED — {report['note']}")
        return "\n".join(lines)
    found = report["actions"]
    if not found:
        lines.append(
            f"  {report['server']} offered no code actions "
            f"at that spot.")
        return "\n".join(lines)
    lines.append(
        f"  {report['server']} offered {len(found)} "
        f"code action(s):")
    for number, action in enumerate(found, start=1):
        carries = []
        if action["has_edit"]:
            carries.append("carries an edit")
        if action["has_command"]:
            carries.append("carries a command (not executed)")
        if not carries:
            carries.append("carries no edit or command")
        kind = f" ({action['kind']})" if action["kind"] else ""
        lines.append(
            f"  [{number}] {action['title']}{kind} — "
            f"{', '.join(carries)}")
        if action["diagnostics"]:
            lines.append(
                f"      for {len(action['diagnostics'])} "
                f"diagnostic(s)")
        if action["disabled_reason"]:
            lines.append(
                f"      disabled: {action['disabled_reason']}")
        if action["has_edit"] and action["edit"]:
            for file_plan in action["edit"]["files"]:
                for diff_line in file_plan["diff"].splitlines():
                    lines.append(f"      {diff_line}")
    if report["apply_note"]:
        lines.append(f"  {report['apply_note']}")
    for outcome in report["outcomes"]:
        detail = f" — {outcome['reason']}" if outcome["reason"] \
            else f" ({outcome['edits_applied']} edit(s))"
        lines.append(
            f"  {outcome['status']}: {outcome['path']}{detail}")
    return "\n".join(lines)


def render_markdown(servers: Optional[List[Dict[str, Any]]] = None
                    ) -> str:
    """The server catalogue as markdown (the human report)."""
    board = discover_servers() if servers is None else servers
    lines = ["# Language servers (M-049, navigation M-050, "
             "rename and code actions M-051)", ""]
    for entry in board:
        state = "installed" if entry["installed"] \
            else "not installed"
        lines.append(
            f"- **{entry['name']}** ({state}) — "
            f"{', '.join(entry['languages'])}: "
            f"`{' '.join(entry['command'])}`")
    return "\n".join(lines) + "\n"
