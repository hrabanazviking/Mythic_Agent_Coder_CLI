"""The Debugger (DAP) (M-054).

Part III — Code Intelligence. Breakpoints, step, continue,
variable inspection, exception stops for Python first
(debugpy), then the DAP-general road — the coder can
*watch* a bug happen.

What ships here, in ``mythic_agent/tools/debugger.py``
(the gap audit's named owner for the debugger-dap feature,
with ``mythic_agent/tools/review.py`` as its basis):

* **The adapter catalogue, as data.** :data:`ADAPTERS`
  names the Python-first adapter (debugpy, launched as
  ``<python> -m debugpy.adapter``). The client speaks the
  Debug Adapter Protocol itself, so the road is
  DAP-general by construction: any adapter speaking DAP
  can be driven through the same client; only the
  catalogue's Python entry is claimed proven here.
* **Honest discovery.** :func:`discover_adapters` reports
  installed / not-installed exactly as the import probe
  says (debugpy is a Python package, not a PATH binary).
  An adapter that is not installed is a reported state
  with its remedy, never a fake session: measured at
  scoping, debugpy is NOT installed in this environment,
  so a real session here reports ``not-installed`` and
  live proof rides a fake DAP adapter subprocess in the
  slice tests, speaking the real protocol.
* **The client.** :class:`DAPClient` speaks real DAP over
  Content-Length framing to an adapter subprocess:
  ``initialize`` -> ``launch``/``attach`` ->
  ``setBreakpoints`` / ``setExceptionBreakpoints`` ->
  ``configurationDone`` -> ``stopped`` events ->
  ``threads`` / ``stackTrace`` / ``scopes`` /
  ``variables`` -> ``next`` / ``stepIn`` / ``stepOut`` /
  ``continue`` -> ``disconnect``. A read thread owns the
  inbound stream so responses, events, and stop waits
  never race on it. An adapter request (a message with
  both an id and a command) is answered with an honest
  failure response rather than left hanging — this client
  implements no adapter-to-client requests.
* **Plain records.** :class:`Breakpoint`,
  :class:`StackFrame`, :class:`Scope`, :class:`Variable`,
  and :class:`StoppedInfo` carry the session's facts as
  data; :class:`DebugReport` is one whole run's account
  (adapter, breakpoints as the adapter settled them, the
  stop that was reached, threads, frames, scopes with
  their variables, the steps performed, the events seen).
* **The session driver.** :func:`run_debug_session` runs
  the whole road for one program: launch, set the asked
  breakpoints (in the program file) and exception stops,
  finish configuration, wait for the first stop, inspect
  (threads, stack, scopes, variables — one level of
  nested variables expanded), perform any asked steps
  (each followed by a fresh stop wait and inspection),
  then disconnect. A program that ends before any stop
  is reported ``terminated``, never dressed as stopped.
* **The switch.** The setting ``debugger`` (on by
  default) turns this road off when the user says so;
  while off, a run refuses plainly (``disabled``).
* **The surfaces.** ``Agent.debugger_status()`` is the
  discovery board and ``Agent.debug_run(...)`` one run;
  ``/debug`` (bare or ``show`` for the board, ``run
  <program> [break <line> ...] [exceptions] [then
  <step> ...]`` for a run) rides the terminal and the
  TUI system-command road, sharing this module's parser
  and formatters.

Debugger-in-the-loop (M-055 — re-running a failing test
under the debugger by the coder itself) lives in
``mythic_agent/tools/debug_loop.py``; it consumes this
slice's client and session records. The one road it
needed back here is the client's module launch
(``launch(module="pytest", ...)``), added with M-055.

Honesty rules, pinned by the slice's tests:

* **Absence is never a session.** A missing adapter is
  ``not-installed`` with its remedy; no breakpoints,
  frames, or variables are ever invented.
* **An adapter that dies, refuses, or never answers is
  an error in its own words.** A failed DAP response, a
  stream that ends mid-session, and a stop wait that
  times out each raise :class:`DAPError` naming what
  happened; nothing is retried silently.
* **Malformed wire data is refused, never guessed.** A
  frame without a Content-Length, a body that is not a
  JSON object, and a response whose ``success`` is false
  each surface plainly.
"""

from __future__ import annotations

__all__ = [
    "ADAPTERS",
    "DEBUGGER_SLICE",
    "EXCEPTION_FILTERS",
    "PLAIN_EXPLANATION",
    "STEP_ACTIONS",
    "USAGE",
    "AdapterDef",
    "Breakpoint",
    "DAPClient",
    "DAPError",
    "DebugReport",
    "Scope",
    "StackFrame",
    "StoppedInfo",
    "Variable",
    "adapter_for_language",
    "adapter_for_path",
    "discover_adapters",
    "enabled_from_config",
    "encode_message",
    "format_debug_board",
    "format_debug_report",
    "parse_debug_args",
    "read_message",
    "render_markdown",
    "run_debug_session",
]

import importlib.util
import json
import shutil
import subprocess
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, BinaryIO, Callable, Dict, List, Optional, Tuple

from ..core.exceptions import MythicIntegrationError

DEBUGGER_SLICE = "M-054"

PLAIN_EXPLANATION = (
    "The debugger lets the coder watch a bug happen: "
    "/debug shows which debug adapters this machine has, "
    "and /debug run <program> [break <line> ...] "
    "[exceptions] [then next|stepin|stepout|continue ...] "
    "launches the program under the adapter, stops at the "
    "breakpoints, and shows the stack and the variables "
    "exactly as the adapter reports them. Python comes "
    "first, through debugpy; a machine without debugpy is "
    "told so plainly — no session is ever faked."
)

USAGE = ("Usage: /debug [show] | /debug run <program> "
         "[break <line> ...] [exceptions] "
         "[then next|stepin|stepout|continue ...]")

#: DAP step actions this road performs, in plain words.
STEP_ACTIONS = ("next", "stepin", "stepout", "continue")

_STEP_COMMANDS = {
    "next": "next",
    "stepin": "stepIn",
    "stepout": "stepOut",
    "continue": "continue",
}

#: Exception breakpoint filters debugpy understands.
EXCEPTION_FILTERS = ("all", "raised", "uncaught", "userUnhandled")


class DAPError(MythicIntegrationError, RuntimeError):
    """A debug adapter is missing, died, or answered badly."""


# ---------------------------------------------------------------------------
# The adapter catalogue
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AdapterDef:
    """One catalogued debug adapter, as data."""

    name: str
    languages: Tuple[str, ...]
    extensions: Tuple[str, ...]
    command: Tuple[str, ...]
    install_remedy: str
    module: str = ""   # a Python package whose presence proves install

    def installed(self) -> bool:
        """True exactly when the install probe finds it."""
        if self.module:
            try:
                return importlib.util.find_spec(self.module) is not None
            except (ImportError, ValueError):
                return False
        return shutil.which(self.command[0]) is not None

    def record(self, installed: Optional[bool] = None) -> Dict[str, Any]:
        found = self.installed() if installed is None else installed
        return {
            "name": self.name,
            "languages": list(self.languages),
            "extensions": list(self.extensions),
            "command": list(self.command),
            "installed": found,
            "install_remedy": None if found else self.install_remedy,
        }


ADAPTERS: Tuple[AdapterDef, ...] = (
    AdapterDef(
        name="debugpy",
        languages=("python",),
        extensions=(".py",),
        command=(sys.executable, "-m", "debugpy.adapter"),
        install_remedy="install debugpy (pip install debugpy) "
                       "so the debugpy adapter can be launched",
        module="debugpy",
    ),
)

_BY_LANGUAGE: Dict[str, AdapterDef] = {}
_BY_EXTENSION: Dict[str, AdapterDef] = {}
for _adapter in ADAPTERS:
    for _language in _adapter.languages:
        _BY_LANGUAGE[_language] = _adapter
    for _extension in _adapter.extensions:
        _BY_EXTENSION[_extension] = _adapter


def adapter_for_language(language: str) -> Optional[AdapterDef]:
    """The catalogued adapter for *language*, or None honestly."""
    return _BY_LANGUAGE.get(language.strip().lower())


def adapter_for_path(path: Path | str) -> Optional[AdapterDef]:
    """The catalogued adapter for a file's extension, or None."""
    return _BY_EXTENSION.get(Path(path).suffix.lower())


def discover_adapters() -> List[Dict[str, Any]]:
    """Every catalogued adapter's discovery record, in order."""
    return [adapter.record() for adapter in ADAPTERS]


# ---------------------------------------------------------------------------
# Plain records
# ---------------------------------------------------------------------------

@dataclass
class Breakpoint:
    """One breakpoint, as the adapter settled it."""

    line: int = 0
    verified: bool = False
    id: int = 0
    message: str = ""
    path: str = ""

    def __post_init__(self) -> None:
        if self.line < 1:
            raise ValueError(
                f"a breakpoint line must be >= 1, got {self.line!r}")

    @classmethod
    def from_dap(cls, raw: Any, path: str = "") -> "Breakpoint":
        if not isinstance(raw, dict):
            raise DAPError(f"breakpoint is not an object: {raw!r}")
        source = raw.get("source") or {}
        return cls(
            line=int(raw.get("line", 0) or 0),
            verified=bool(raw.get("verified", False)),
            id=int(raw.get("id", 0) or 0),
            message=str(raw.get("message", "") or ""),
            path=str(source.get("path", "") or path),
        )

    def record(self) -> Dict[str, Any]:
        return {
            "line": self.line, "verified": self.verified,
            "id": self.id, "message": self.message,
            "path": self.path,
        }

    def one_line(self) -> str:
        state = "verified" if self.verified else "NOT verified"
        where = f"{self.path}:{self.line}" if self.path else f"line {self.line}"
        suffix = f" — {self.message}" if self.message else ""
        return f"breakpoint at {where} ({state}){suffix}"


@dataclass
class StoppedInfo:
    """One ``stopped`` event, as a plain record."""

    reason: str = ""
    thread_id: int = 0
    description: str = ""
    text: str = ""
    all_threads_stopped: bool = False
    hit_breakpoint_ids: List[int] = field(default_factory=list)

    @classmethod
    def from_event(cls, body: Any) -> "StoppedInfo":
        if not isinstance(body, dict):
            raise DAPError(f"stopped event body is not an object: {body!r}")
        return cls(
            reason=str(body.get("reason", "") or ""),
            thread_id=int(body.get("threadId", 0) or 0),
            description=str(body.get("description", "") or ""),
            text=str(body.get("text", "") or ""),
            all_threads_stopped=bool(body.get("allThreadsStopped", False)),
            hit_breakpoint_ids=[int(x) for x in
                                body.get("hitBreakpointIds") or []],
        )

    def record(self) -> Dict[str, Any]:
        return {
            "reason": self.reason, "thread_id": self.thread_id,
            "description": self.description, "text": self.text,
            "all_threads_stopped": self.all_threads_stopped,
            "hit_breakpoint_ids": list(self.hit_breakpoint_ids),
        }

    def one_line(self) -> str:
        parts = [f"stopped: {self.reason or 'unknown reason'}"]
        if self.thread_id:
            parts.append(f"thread {self.thread_id}")
        if self.text:
            parts.append(self.text)
        elif self.description:
            parts.append(self.description)
        return " — ".join(parts)


@dataclass
class StackFrame:
    """One stack frame, as a plain record (1-based line/column)."""

    id: int = 0
    name: str = ""
    path: str = ""
    line: int = 0
    column: int = 0

    @classmethod
    def from_dap(cls, raw: Any) -> "StackFrame":
        if not isinstance(raw, dict):
            raise DAPError(f"stack frame is not an object: {raw!r}")
        source = raw.get("source") or {}
        return cls(
            id=int(raw.get("id", 0) or 0),
            name=str(raw.get("name", "") or ""),
            path=str(source.get("path", "") or ""),
            line=int(raw.get("line", 0) or 0),
            column=int(raw.get("column", 0) or 0),
        )

    def record(self) -> Dict[str, Any]:
        return {
            "id": self.id, "name": self.name, "path": self.path,
            "line": self.line, "column": self.column,
        }

    def one_line(self) -> str:
        where = f"{self.path}:{self.line}:{self.column}" \
            if self.path else f"line {self.line}"
        return f"{self.name or '(unnamed frame)'} at {where}"


@dataclass
class Variable:
    """One variable, as the adapter reports it."""

    name: str = ""
    value: str = ""
    type: str = ""
    variables_reference: int = 0
    evaluate_name: str = ""
    children: List["Variable"] = field(default_factory=list)

    @classmethod
    def from_dap(cls, raw: Any) -> "Variable":
        if not isinstance(raw, dict):
            raise DAPError(f"variable is not an object: {raw!r}")
        return cls(
            name=str(raw.get("name", "") or ""),
            value=str(raw.get("value", "") or ""),
            type=str(raw.get("type", "") or ""),
            variables_reference=int(raw.get("variablesReference", 0) or 0),
            evaluate_name=str(raw.get("evaluateName", "") or ""),
        )

    def record(self) -> Dict[str, Any]:
        return {
            "name": self.name, "value": self.value,
            "type": self.type,
            "variables_reference": self.variables_reference,
            "evaluate_name": self.evaluate_name,
            "children": [child.record() for child in self.children],
        }

    def one_line(self) -> str:
        typed = f": {self.type}" if self.type else ""
        return f"{self.name}{typed} = {self.value}"


@dataclass
class Scope:
    """One scope of one frame, with its variables."""

    name: str = ""
    variables_reference: int = 0
    expensive: bool = False
    variables: List[Variable] = field(default_factory=list)

    @classmethod
    def from_dap(cls, raw: Any) -> "Scope":
        if not isinstance(raw, dict):
            raise DAPError(f"scope is not an object: {raw!r}")
        return cls(
            name=str(raw.get("name", "") or ""),
            variables_reference=int(raw.get("variablesReference", 0) or 0),
            expensive=bool(raw.get("expensive", False)),
        )

    def record(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "variables_reference": self.variables_reference,
            "expensive": self.expensive,
            "variables": [var.record() for var in self.variables],
        }


@dataclass
class DebugReport:
    """One debug run's whole account."""

    program: str = ""
    adapter: Optional[str] = None
    status: str = "ok"   # ok | not-installed | no-adapter | disabled |
                         # terminated
    note: str = ""
    breakpoints: List[Breakpoint] = field(default_factory=list)
    stopped: Optional[StoppedInfo] = None
    threads: List[Dict[str, Any]] = field(default_factory=list)
    frames: List[StackFrame] = field(default_factory=list)
    scopes: List[Scope] = field(default_factory=list)
    steps_performed: List[str] = field(default_factory=list)
    events: List[Dict[str, Any]] = field(default_factory=list)
    terminated: bool = False

    def record(self) -> Dict[str, Any]:
        return {
            "program": self.program, "adapter": self.adapter,
            "status": self.status, "note": self.note,
            "breakpoints": [bp.record() for bp in self.breakpoints],
            "stopped": self.stopped.record() if self.stopped else None,
            "threads": [dict(t) for t in self.threads],
            "frames": [frame.record() for frame in self.frames],
            "scopes": [scope.record() for scope in self.scopes],
            "steps_performed": list(self.steps_performed),
            "events": [dict(e) for e in self.events],
            "terminated": self.terminated,
        }


# ---------------------------------------------------------------------------
# DAP framing (the LSP framing shape, DAP's own messages)
# ---------------------------------------------------------------------------

def encode_message(message: Dict[str, Any]) -> bytes:
    """One message as a Content-Length framed DAP frame."""
    body = json.dumps(message).encode("utf-8")
    return b"Content-Length: %d\r\n\r\n" % len(body) + body


def read_message(stream: BinaryIO) -> Optional[Dict[str, Any]]:
    """Read one framed message; None at a clean end of stream.

    A frame without a Content-Length header, and a body
    that is not a JSON object, are refused plainly.
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
                raise DAPError(
                    f"bad Content-Length header: {value!r}") from exc
    if content_length is None:
        raise DAPError("DAP frame arrived without a Content-Length")
    body = b""
    while len(body) < content_length:
        chunk = stream.read(content_length - len(body))
        if not chunk:
            return None
        body += chunk
    try:
        parsed = json.loads(body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise DAPError(f"DAP frame body is not JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise DAPError(f"DAP message is not an object: {parsed!r}")
    return parsed


# ---------------------------------------------------------------------------
# The client
# ---------------------------------------------------------------------------

class DAPClient:
    """One debug adapter process, spoken to over stdio.

    The transport is a subprocess by default; tests may
    hand in a *process_factory* returning any object with
    binary ``stdin`` / ``stdout`` streams plus ``poll()``,
    ``terminate()``, and ``kill()`` — the shape
    :class:`subprocess.Popen` already has.
    """

    def __init__(self, adapter: AdapterDef, root: Path | str, *,
                 process_factory: Optional[Callable[..., Any]] = None,
                 timeout: float = 10.0) -> None:
        self.adapter = adapter
        self.root = Path(root).resolve()
        self.timeout = timeout
        self._factory = process_factory or subprocess.Popen
        self._process: Any = None
        self._seq = 0
        self._pending: Dict[int, Dict[str, Any]] = {}
        self._pending_errors: Dict[int, str] = {}
        self._events: List[Dict[str, Any]] = []
        self._stopped: List[StoppedInfo] = []
        self._terminated = False
        self._condition = threading.Condition()
        self._reader: Optional[threading.Thread] = None
        self._reader_error: Optional[str] = None
        self._closed = False

    # -- lifecycle ----------------------------------------------------

    def start(self) -> Dict[str, Any]:
        """Launch the adapter and run the initialize handshake.

        Returns the adapter's initialize result body (its
        declared capabilities, in its own words). An
        adapter that is not installed raises
        :class:`DAPError` carrying its install remedy.
        """
        if self._process is not None:
            raise DAPError(f"{self.adapter.name} is already running")
        if not self.adapter.installed() \
                and self._factory is subprocess.Popen:
            raise DAPError(
                f"the {self.adapter.name} debug adapter is not "
                f"installed: {self.adapter.install_remedy}")
        try:
            self._process = self._factory(
                list(self.adapter.command),
                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, cwd=str(self.root))
        except FileNotFoundError as exc:
            raise DAPError(
                f"the {self.adapter.name} debug adapter is not "
                f"installed: {self.adapter.install_remedy}") from exc
        self._reader = threading.Thread(
            target=self._read_loop, name=f"dap-{self.adapter.name}",
            daemon=True)
        self._reader.start()
        return self._request("initialize", {
            "adapterID": self.adapter.name,
            "clientID": "mythic",
            "clientName": "Mythic Agent Coder",
            "pathFormat": "path",
            "linesStartAt1": True,
            "columnsStartAt1": True,
            "supportsVariableType": True,
        })

    def close(self) -> None:
        """Disconnect politely, then end the process firmly."""
        if self._process is None or self._closed:
            return
        self._closed = True
        try:
            self._request("disconnect", {"restart": False}, timeout=5.0)
        except DAPError:
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

    disconnect = close

    def __enter__(self) -> "DAPClient":
        self.start()
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # -- session road ---------------------------------------------------

    def _require_running(self) -> None:
        if self._process is None:
            raise DAPError(
                f"the {self.adapter.name} debug adapter is not "
                f"running; start the client first")

    def launch(self, program: Optional[Path | str] = None, *,
               module: Optional[str] = None,
               args: Optional[List[str]] = None,
               stop_on_entry: bool = False) -> Dict[str, Any]:
        """Launch *program* — or the named *module* — under the adapter.

        Exactly one of *program* / *module* is required. The
        module road (added for M-055's debugger-in-the-loop,
        which launches ``pytest`` itself) is debugpy's own
        module launch: the adapter runs the module the way
        ``python -m <module>`` would, with *args* as its
        arguments.
        """
        self._require_running()
        if (program is None) == (module is None):
            raise ValueError(
                "launch needs exactly one of a program or a module")
        arguments: Dict[str, Any] = {
            "args": list(args or []),
            "cwd": str(self.root),
            "stopOnEntry": bool(stop_on_entry),
            "noDebug": False,
        }
        if module is not None:
            if not str(module).strip():
                raise ValueError("a launch module must be named")
            arguments["module"] = str(module)
        else:
            target = Path(program)  # type: ignore[arg-type]
            if not target.is_absolute():
                target = self.root / target
            arguments["program"] = str(target)
        return self._request("launch", arguments)

    def attach(self, *, process_id: Optional[int] = None,
               port: Optional[int] = None,
               host: Optional[str] = None) -> Dict[str, Any]:
        """Attach to a process/port the adapter names."""
        self._require_running()
        arguments: Dict[str, Any] = {}
        if process_id is not None:
            arguments["processId"] = int(process_id)
        if port is not None:
            arguments["port"] = int(port)
        if host is not None:
            arguments["host"] = str(host)
        if not arguments:
            raise ValueError(
                "attach needs a process id or a port to attach to")
        return self._request("attach", arguments)

    def set_breakpoints(self, path: Path | str,
                        lines: List[int]) -> List[Breakpoint]:
        """Set breakpoints at *lines* (1-based) in one file."""
        self._require_running()
        target = Path(path)
        if not target.is_absolute():
            target = self.root / target
        for line in lines:
            if isinstance(line, bool) or not isinstance(line, int) \
                    or line < 1:
                raise ValueError(
                    f"breakpoint lines must be positive integers, "
                    f"got {line!r}")
        body = self._request("setBreakpoints", {
            "source": {"path": str(target), "name": target.name},
            "breakpoints": [{"line": line} for line in lines],
            "sourceModified": False,
        })
        return [Breakpoint.from_dap(raw, path=str(target))
                for raw in body.get("breakpoints") or []]

    def set_exception_breakpoints(
            self, filters: Optional[List[str]] = None) -> Dict[str, Any]:
        """Ask for exception stops under the named filters."""
        self._require_running()
        chosen = list(filters or ["all"])
        for name in chosen:
            if name not in EXCEPTION_FILTERS:
                raise ValueError(
                    f"exception filter must be one of "
                    f"{EXCEPTION_FILTERS}, got {name!r}")
        return self._request(
            "setExceptionBreakpoints", {"filters": chosen})

    def configuration_done(self) -> Dict[str, Any]:
        """Tell the adapter configuration is finished."""
        self._require_running()
        return self._request("configurationDone", {})

    @property
    def events(self) -> List[Dict[str, Any]]:
        with self._condition:
            return [dict(event) for event in self._events]

    @property
    def terminated(self) -> bool:
        with self._condition:
            return self._terminated

    def wait_stopped(self, *, since: int = 0,
                     timeout: Optional[float] = None
                     ) -> Optional[StoppedInfo]:
        """Wait for a stopped event after index *since*.

        Returns the stop, or None when the program
        terminated first. A wait that passes with neither
        raises :class:`DAPError` — "still running" is
        unknown, never dressed as a stop.
        """
        wait = self.timeout if timeout is None else timeout
        with self._condition:
            arrived = self._condition.wait_for(
                lambda: len(self._stopped) > since
                or self._terminated
                or self._reader_error is not None,
                timeout=wait)
            if self._reader_error is not None:
                raise DAPError(self._reader_error)
            if len(self._stopped) > since:
                return self._stopped[since]
            if self._terminated:
                return None
            if not arrived:
                raise DAPError(
                    f"the {self.adapter.name} debug adapter "
                    f"reported no stop within {wait:g}s — the "
                    f"program's state is unknown, not stopped")
        raise DAPError("the stop wait failed")

    def stopped_count(self) -> int:
        with self._condition:
            return len(self._stopped)

    # -- inspection -----------------------------------------------------

    def threads(self) -> List[Dict[str, Any]]:
        """The debuggee's threads, as plain dicts."""
        self._require_running()
        body = self._request("threads", {})
        found = []
        for raw in body.get("threads") or []:
            if not isinstance(raw, dict):
                raise DAPError(f"thread is not an object: {raw!r}")
            found.append({"id": int(raw.get("id", 0) or 0),
                          "name": str(raw.get("name", "") or "")})
        return found

    def stack_trace(self, thread_id: int, *,
                    levels: int = 20) -> List[StackFrame]:
        """One thread's stack frames, top first."""
        self._require_running()
        body = self._request("stackTrace", {
            "threadId": int(thread_id), "startFrame": 0,
            "levels": int(levels)})
        return [StackFrame.from_dap(raw)
                for raw in body.get("stackFrames") or []]

    def scopes(self, frame_id: int) -> List[Scope]:
        """One frame's scopes (variables not yet loaded)."""
        self._require_running()
        body = self._request("scopes", {"frameId": int(frame_id)})
        return [Scope.from_dap(raw) for raw in body.get("scopes") or []]

    def variables(self, variables_reference: int) -> List[Variable]:
        """The variables under one variablesReference."""
        self._require_running()
        body = self._request(
            "variables", {"variablesReference": int(variables_reference)})
        return [Variable.from_dap(raw)
                for raw in body.get("variables") or []]

    def inspect(self, thread_id: Optional[int] = None) -> Dict[str, Any]:
        """Threads + top-frame stack/scopes/variables, as data.

        Variables ride their scopes; a variable that itself
        carries a variablesReference is expanded one level
        into its ``children`` — deeper nesting is the
        adapter's data, asked for explicitly, never
        recursed without bound.
        """
        found_threads = self.threads()
        chosen = thread_id
        if chosen is None:
            chosen = found_threads[0]["id"] if found_threads else 0
        frames: List[StackFrame] = []
        scopes: List[Scope] = []
        if chosen:
            frames = self.stack_trace(chosen)
        if frames:
            scopes = self.scopes(frames[0].id)
            for scope in scopes:
                if scope.variables_reference:
                    scope.variables = self.variables(
                        scope.variables_reference)
                    for variable in scope.variables:
                        if variable.variables_reference:
                            variable.children = self.variables(
                                variable.variables_reference)
        return {"threads": found_threads, "thread_id": chosen,
                "frames": frames, "scopes": scopes}

    # -- stepping ---------------------------------------------------------

    def step(self, action: str, thread_id: int) -> None:
        """Perform one step action for *thread_id*.

        The action word is one of :data:`STEP_ACTIONS`;
        the request is sent and the caller waits for the
        following stop with :meth:`wait_stopped`.
        """
        normalized = (action or "").strip().lower().replace("_", "")
        if normalized not in _STEP_COMMANDS:
            raise ValueError(
                f"step action must be one of {STEP_ACTIONS}, "
                f"got {action!r}")
        self._require_running()
        self._request(_STEP_COMMANDS[normalized],
                      {"threadId": int(thread_id)})

    # -- wire machinery ---------------------------------------------------

    def _read_loop(self) -> None:
        stream = self._process.stdout
        try:
            while True:
                message = read_message(stream)
                if message is None:
                    break
                self._dispatch(message)
        except (DAPError, OSError) as exc:
            with self._condition:
                if self._reader_error is None:
                    self._reader_error = (
                        f"the {self.adapter.name} debug adapter's "
                        f"stream failed: {exc}")
                self._condition.notify_all()
            return
        with self._condition:
            if self._reader_error is None and not self._closed:
                self._reader_error = (
                    f"the {self.adapter.name} debug adapter "
                    f"exited before its work was done")
            self._condition.notify_all()

    def _dispatch(self, message: Dict[str, Any]) -> None:
        kind = message.get("type")
        if kind == "event":
            event_name = str(message.get("event", "") or "")
            body = message.get("body") or {}
            with self._condition:
                self._events.append(
                    {"event": event_name, "body": body})
                if event_name == "stopped":
                    self._stopped.append(StoppedInfo.from_event(body))
                if event_name in ("terminated", "exited"):
                    self._terminated = True
                self._condition.notify_all()
            return
        if kind == "request":
            # An adapter-to-client request: this client
            # implements none, so it answers with an honest
            # failure rather than leaving the adapter hanging.
            self._send({
                "seq": 0, "type": "response",
                "request_seq": message.get("seq", 0),
                "command": str(message.get("command", "") or ""),
                "success": False,
                "message": "Mythic implements no adapter-to-client "
                           "requests in this slice (M-054)",
            })
            return
        if kind == "response":
            with self._condition:
                ident = message.get("request_seq")
                if message.get("success"):
                    body = message.get("body")
                    self._pending[ident] = \
                        body if isinstance(body, dict) else {}
                else:
                    self._pending_errors[ident] = str(
                        message.get("message", "") or
                        "the adapter refused the request")
                self._condition.notify_all()

    def _send(self, message: Dict[str, Any]) -> None:
        process = self._process
        if process is None or process.stdin is None:
            raise DAPError(
                f"the {self.adapter.name} debug adapter is not "
                f"running")
        if not message.get("seq"):
            self._seq += 1
            message = {"seq": self._seq, **message}
        try:
            process.stdin.write(encode_message(message))
            process.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            raise DAPError(
                f"writing to the {self.adapter.name} debug "
                f"adapter failed: {exc}") from exc

    def _request(self, command: str, arguments: Optional[Any], *,
                 timeout: Optional[float] = None) -> Dict[str, Any]:
        self._seq += 1
        ident = self._seq
        self._send({"seq": ident, "type": "request",
                    "command": command, "arguments": arguments})
        wait = self.timeout if timeout is None else timeout
        with self._condition:
            arrived = self._condition.wait_for(
                lambda: ident in self._pending
                or ident in self._pending_errors
                or self._reader_error is not None,
                timeout=wait)
            if ident in self._pending_errors:
                raise DAPError(
                    f"the {self.adapter.name} debug adapter "
                    f"refused {command}: "
                    f"{self._pending_errors.pop(ident)}")
            if ident in self._pending:
                return self._pending.pop(ident)
            if self._reader_error is not None:
                raise DAPError(self._reader_error)
            if not arrived:
                raise DAPError(
                    f"the {self.adapter.name} debug adapter did "
                    f"not answer {command} within {wait:g}s")
        raise DAPError(f"the {command} request failed")


# ---------------------------------------------------------------------------
# One debug run, end to end
# ---------------------------------------------------------------------------

def run_debug_session(program: Path | str, *,
                      breakpoints: Optional[List[int]] = None,
                      steps: Optional[List[str]] = None,
                      stop_on_exception: bool = False,
                      root: Optional[Path | str] = None,
                      timeout: float = 10.0,
                      enabled: bool = True,
                      client_factory: Optional[
                          Callable[..., DAPClient]] = None
                      ) -> DebugReport:
    """One program's debug run, with honest absence.

    No catalogued adapter for the program's language, and
    a catalogued adapter that is not installed, are
    reports — never raised, never dressed as a session.
    An adapter that runs and then fails raises
    :class:`DAPError`. Breakpoints name lines in the
    program file itself (the Python-first road); the
    client's ``set_breakpoints`` is the general road for
    any file.
    """
    target = Path(program)
    base = Path(root).resolve() if root is not None \
        else target.resolve().parent
    if not target.is_absolute():
        target = base / target
    report = DebugReport(program=str(target))
    if not enabled:
        report.status = "disabled"
        report.note = ("the debugger is off (debugger: false), "
                       "so no adapter was launched")
        return report
    adapter = adapter_for_path(target)
    if adapter is None:
        report.status = "no-adapter"
        report.note = (f"no debug adapter is catalogued for "
                       f"{target.suffix or 'this file'} files — "
                       f"nothing debugged this program")
        return report
    report.adapter = adapter.name
    if not adapter.installed() and client_factory is None:
        report.status = "not-installed"
        report.note = (f"the {adapter.name} debug adapter is not "
                       f"installed, so no session was started; "
                       f"{adapter.install_remedy}")
        return report
    factory = client_factory or (
        lambda adp, rt: DAPClient(adp, rt, timeout=timeout))
    client = factory(adapter, base)
    client.start()
    try:
        client.launch(target)
        if breakpoints:
            report.breakpoints = client.set_breakpoints(
                target, list(breakpoints))
        if stop_on_exception:
            client.set_exception_breakpoints(["all"])
        client.configuration_done()
        stopped = client.wait_stopped(since=0, timeout=timeout)
        report.events = client.events
        if stopped is None:
            report.status = "terminated"
            report.terminated = True
            report.note = ("the program ended before any stop "
                           "was reached — no breakpoint was hit "
                           "and nothing was inspected")
            return report
        report.stopped = stopped
        seen = client.inspect(stopped.thread_id or None)
        report.threads = seen["threads"]
        report.frames = seen["frames"]
        report.scopes = seen["scopes"]
        for action in steps or []:
            since = client.stopped_count()
            thread_id = (report.stopped.thread_id if report.stopped
                         else seen["thread_id"])
            client.step(action, thread_id)
            report.steps_performed.append(
                action.strip().lower().replace("_", ""))
            nxt = client.wait_stopped(since=since, timeout=timeout)
            report.events = client.events
            if nxt is None:
                report.terminated = True
                report.note = ("the program ended during the "
                               "asked steps — the last inspection "
                               "is the one before it ended")
                break
            report.stopped = nxt
            seen = client.inspect(nxt.thread_id or None)
            report.threads = seen["threads"]
            report.frames = seen["frames"]
            report.scopes = seen["scopes"]
        if not report.note:
            where = report.frames[0].one_line() if report.frames else ""
            report.note = (f"stopped ({report.stopped.reason})"
                           + (f" at {where}" if where else ""))
        return report
    finally:
        client.close()


def enabled_from_config(config: Optional[Dict[str, Any]]) -> bool:
    """The debugger is on unless the config says ``debugger: false``."""
    if not config:
        return True
    return config.get("debugger", True) is not False


# ---------------------------------------------------------------------------
# Surfaces: parser, formatters, markdown
# ---------------------------------------------------------------------------

def parse_debug_args(arguments: str) -> Dict[str, Any]:
    """Parse ``/debug`` arguments: the board, or one run."""
    text = (arguments or "").strip()
    if not text or text == "show":
        return {"action": "show"}
    tokens = text.split()
    if tokens[0] == "show":
        raise ValueError(f"{USAGE} — show takes no further words")
    if tokens[0] != "run" or len(tokens) < 2:
        raise ValueError(USAGE)
    program = tokens[1]
    breakpoints: List[int] = []
    steps: List[str] = []
    stop_on_exception = False
    index = 2
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
                raise ValueError(
                    f"{USAGE} — a break line must be >= 1")
            breakpoints.append(line)
            index += 2
            continue
        if token == "exceptions":
            stop_on_exception = True
            index += 1
            continue
        if token == "then":
            if index + 1 >= len(tokens):
                raise ValueError(f"{USAGE} — then needs a step action")
            action = tokens[index + 1].lower().replace("_", "")
            if action not in STEP_ACTIONS:
                raise ValueError(
                    f"{USAGE} — a step must be one of "
                    f"{', '.join(STEP_ACTIONS)}")
            steps.append(action)
            index += 2
            continue
        raise ValueError(f"{USAGE} — unexpected word {token!r}")
    return {"action": "run", "program": program,
            "breakpoints": breakpoints, "steps": steps,
            "stop_on_exception": stop_on_exception}


def format_debug_board(status: Dict[str, Any]) -> str:
    """The discovery board, as plain words."""
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


def format_debug_report(status: Dict[str, Any]) -> str:
    """One debug run's report, as plain words."""
    report = status["report"]
    lines = [f"Debug run of {report['program']}:"]
    if report["status"] in ("no-adapter", "not-installed",
                            "disabled", "terminated"):
        lines.append(f"  {report['status']} — {report['note']}")
        return "\n".join(lines)
    lines.append(f"  adapter: {report['adapter']}")
    for raw in report["breakpoints"]:
        bp = Breakpoint(line=raw["line"], verified=raw["verified"],
                        id=raw["id"], message=raw["message"],
                        path=raw["path"])
        lines.append(f"  {bp.one_line()}")
    stopped = report["stopped"]
    if stopped:
        info = StoppedInfo(
            reason=stopped["reason"], thread_id=stopped["thread_id"],
            description=stopped["description"], text=stopped["text"],
            all_threads_stopped=stopped["all_threads_stopped"],
            hit_breakpoint_ids=stopped["hit_breakpoint_ids"])
        lines.append(f"  {info.one_line()}")
    if report["frames"]:
        lines.append("  stack (top first):")
        for raw in report["frames"]:
            frame = StackFrame(id=raw["id"], name=raw["name"],
                               path=raw["path"], line=raw["line"],
                               column=raw["column"])
            lines.append(f"    {frame.one_line()}")
    for scope in report["scopes"]:
        lines.append(f"  scope {scope['name']}:")
        for var in scope["variables"]:
            lines.append(f"    {var['name']}: {var['type']} = {var['value']}"
                         if var["type"] else
                         f"    {var['name']} = {var['value']}")
            for child in var["children"]:
                lines.append(
                    f"      {child['name']} = {child['value']}")
    if report["steps_performed"]:
        lines.append(
            f"  steps performed: {', '.join(report['steps_performed'])}")
    if report["note"]:
        lines.append(f"  {report['note']}")
    lines.append(status.get("plain_explanation", ""))
    return "\n".join(lines)


def render_markdown() -> str:
    """The slice's plain account, as markdown."""
    names = ", ".join(adapter.name for adapter in ADAPTERS)
    return (
        f"# The Debugger (DAP) ({DEBUGGER_SLICE})\n\n"
        f"{PLAIN_EXPLANATION}\n\n"
        f"Catalogued adapters: {names}. The client speaks "
        f"the Debug Adapter Protocol itself (initialize, "
        f"launch/attach, setBreakpoints, "
        f"setExceptionBreakpoints, configurationDone, "
        f"stopped events, threads, stackTrace, scopes, "
        f"variables, next/stepIn/stepOut/continue, "
        f"disconnect), so the road is DAP-general; an "
        f"adapter that is not installed reports "
        f"not-installed with its remedy and no session is "
        f"ever faked.\n\n"
        f"{USAGE}\n"
    )
