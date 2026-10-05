"""Real owned subprocesses and free localhost HTTP cancellation/recovery."""

import asyncio
import json
import os
import re
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from mythic_agent.core.execution import run_cancellable_async, run_process
from mythic_agent.core.runtime import TurnCancelled


def python_command(script):
    return [sys.executable, "-u", "-c", script]


def process_alive(pid):
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel.OpenProcess(0x00100000, False, pid)
        if not handle:
            return False
        try:
            return kernel.WaitForSingleObject(handle, 0) == 258
        finally:
            kernel.CloseHandle(handle)
    result = subprocess.run(["ps", "-p", str(pid), "-o", "stat="],
                            capture_output=True, text=True, timeout=3)
    return result.returncode == 0 and bool(result.stdout.strip()) and not result.stdout.strip().startswith("Z")


def test_nonzero_exit_and_complete_unicode_output_have_progress(tmp_path):
    script = "import sys;sys.stdout.buffer.write(('Sigrún 🦉\\n'*10000).encode('utf-8'));sys.stdout.flush();sys.stderr.write('diagnostic\\n');sys.exit(7)"
    progress = []
    result = run_process(python_command(script), tmp_path, progress=progress.append, timeout=10)
    assert result.status == "failed" and result.returncode == 7
    assert result.output == "Sigrún 🦉\n" * 10000 + "diagnostic" + os.linesep
    assert "".join(progress) == result.output
    assert result.raw_output == result.output.encode("utf-8")
    assert "exit code: 7" in result.render()


@pytest.mark.parametrize("stop", ["timeout", "cancel", "parent_exit"])
def test_owned_descendant_terminated_and_partial_output_retained(tmp_path, stop):
    script = ("import subprocess,sys,time;"
              "child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)']);"
              "print('child:'+str(child.pid),flush=True);"
              + ("time.sleep(60)" if stop != "parent_exit" else "time.sleep(0.1)"))
    cancel, started = threading.Event(), threading.Event()
    def progress(text):
        if "child:" in text:
            started.set()
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(run_process, python_command(script), tmp_path,
                             cancel=cancel, timeout=2 if stop == "timeout" else 10,
                             grace=0.1, progress=progress)
        assert started.wait(5), "Fixture process did not start"
        if stop == "cancel":
            cancel.set()
        result = future.result(timeout=10)
    assert result.status == {"timeout": "timed_out", "cancel": "cancelled", "parent_exit": "completed"}[stop]
    pid = int(re.search(r"child:(\d+)", result.output)[1])
    assert not process_alive(pid), f"Owned child {pid} survived {stop}"
    assert not any(t.name == "mythic-process-output" for t in threading.enumerate())
    assert run_process(python_command("print('recovered')"), tmp_path).output == "recovered" + os.linesep


def test_cancelled_before_spawn_has_no_effect(tmp_path):
    cancel = threading.Event()
    cancel.set()
    result = run_process(python_command("open('unwanted','w').write('x')"), tmp_path, cancel=cancel)
    assert result.status == "cancelled" and result.returncode is None
    assert not (tmp_path / "unwanted").exists()


def test_broken_progress_callback_does_not_abandon_capture(tmp_path):
    def broken(text):
        raise ValueError("fixture adapter failed")
    result = run_process(python_command("print('complete')"), tmp_path, progress=broken)
    assert result.output == "complete" + os.linesep and result.status == "completed"


def test_timeout_leaves_unrelated_process_running(tmp_path):
    unrelated = subprocess.Popen(python_command("import time;time.sleep(60)"))
    try:
        result = run_process(python_command("import time;print('partial',flush=True);time.sleep(60)"),
                             tmp_path, timeout=0.5, grace=0.1)
        assert result.status == "timed_out" and result.output == "partial" + os.linesep
        assert unrelated.poll() is None
    finally:
        unrelated.terminate()
        unrelated.wait(timeout=5)


@pytest.mark.parametrize("setting", ["command_timeout", "github_timeout", "approval_timeout",
                                     "process_kill_grace", "cancellation_poll_interval"])
def test_execution_budgets_reject_unbounded_values(setting):
    from mythic_agent.core.runtime import runtime_settings
    for invalid in (float("inf"), float("nan"), 0, True):
        with pytest.raises(ValueError):
            runtime_settings({"runtime": {setting: invalid}})


def test_async_operation_cancel_drains_cleanup_and_supports_embedding_loop():
    cancel, started, cleaned = threading.Event(), threading.Event(), threading.Event()
    async def operation():
        started.set()
        try:
            await asyncio.sleep(60)
        finally:
            cleaned.set()
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(run_cancellable_async, operation, cancel)
        assert started.wait(3)
        cancel.set()
        with pytest.raises(TurnCancelled):
            future.result(timeout=3)
    assert cleaned.is_set()
    async def embedding():
        async def immediate():
            return "embedded"
        return run_cancellable_async(immediate, threading.Event())
    assert asyncio.run(embedding()) == "embedded"


@pytest.mark.parametrize("blocked_stage", ["chat", "embedding", "remote_recall"])
def test_blocked_http_request_cancel_closes_connection_and_fresh_turn_works(agent, blocked_stage):
    started, disconnected = threading.Event(), threading.Event()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def do_POST(self):
            data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            is_chat = "messages" in data
            text = data["messages"][-1]["content"] if is_chat else data.get("input", data.get("query"))
            if text == "wait" and ((is_chat and blocked_stage == "chat") or
                                    (not is_chat and blocked_stage != "chat")):
                started.set()
                self.connection.settimeout(5)
                try:
                    if self.connection.recv(1) == b"":
                        disconnected.set()
                except (OSError, TimeoutError):
                    pass
                return
            if is_chat:
                response = {"id": "fixture", "object": "chat.completion", "created": 1,
                    "model": "fixture", "choices": [{"index": 0, "message": {"role": "assistant", "content": "Recovered"}, "finish_reason": "stop"}]}
            elif "input" in data:
                response = {"object": "list", "data": [{"object": "embedding", "index": 0, "embedding": [1.0, 0.0, 0.0]}],
                            "model": "fixture", "usage": {"prompt_tokens": 1, "total_tokens": 1}}
            else:
                response = {"results": []}
            body = json.dumps(response).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    agent.config["base_url"] = f"http://127.0.0.1:{server.server_port}/v1"
    agent.config["api_keys"] = {agent.config["base_url"]: "fixture-local-only"}
    if blocked_stage == "embedding":
        from mythic_agent.memory.vector_db import LightweightJSONVectorDB
        memory = LightweightJSONVectorDB("cancel-fixture", agent.config["base_url"], "fixture-local-only")
        memory.records = [{"text": "fixture", "vector": [1.0, 0.0, 0.0], "metadata": {}}]
        memory.bind_execution(agent._cancel, agent.config)
        agent.vector_db = memory
    elif blocked_stage == "remote_recall":
        from mythic_agent.memory.vector_db import RemoteRAGProvider
        memory = RemoteRAGProvider("fixture", agent.config["base_url"])
        memory.bind_execution(agent._cancel, agent.config)
        agent.vector_db = memory
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(agent.chat, "wait")
            assert started.wait(5)
            before = time.monotonic()
            agent.cancel()
            with pytest.raises(TurnCancelled):
                future.result(timeout=3)
            assert time.monotonic() - before < 3
        assert disconnected.wait(3), "Cancelled request connection remained open"
        assert agent.last_result.status == "cancelled"
        assert agent.chat("continue") == "Recovered"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_cancelled_tool_turn_retains_partial_output_and_closes_all_calls(agent, tmp_path):
    from types import SimpleNamespace
    from unittest.mock import Mock
    from mythic_agent.core.sessions import SessionStore, validate_messages
    from mythic_agent.core.secure_api import subscribe, unsubscribe
    from mythic_agent.agents import llm
    import shlex
    script = "import time;print('partial-output',flush=True);time.sleep(60)"
    argv = python_command(script)
    command = subprocess.list2cmdline(argv) if os.name == "nt" else shlex.join(argv)
    tool_message = {"role": "assistant", "content": None, "tool_calls": [
        {"id": "command", "type": "function", "function": {"name": "run_command", "arguments": json.dumps({"command": command})}},
        {"id": "write", "type": "function", "function": {"name": "write_file", "arguments": json.dumps({"path": "unwanted", "content": "x"})}},
    ]}
    def response(message):
        return SimpleNamespace(choices=[SimpleNamespace(message=message)], usage=None)
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=Mock(side_effect=[
        response(tool_message), response({"role": "assistant", "content": "Recovered"})]))))
    agent.get_client = lambda: client
    store = SessionStore(agent.project_root, tmp_path / "state")
    session_id = agent.attach_session(store)
    started = threading.Event()
    def progress(agent_name, text):
        if "partial-output" in text:
            started.set()
    subscribe("agent_command_output", progress)
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(agent.chat, "execute fixture")
            assert started.wait(5)
            agent.cancel()
            with pytest.raises(TurnCancelled):
                future.result(timeout=5)
        context = store.load(session_id)["context"]
        assert validate_messages(context) == {}
        results = [m for m in context if m["role"] == "tool"]
        assert "partial-output" in results[0]["content"] and "cancelled" in results[0]["content"]
        assert "cancelled" in results[1]["content"]
        assert not (agent.project_root / "unwanted").exists()
        assert store.load(session_id)["status"] == "cancelled"
        assert agent.chat("continue") == "Recovered"
    finally:
        unsubscribe("agent_command_output", progress)
        agent.close()


def test_background_slash_stop_reaps_execution_and_cancels_queued_command(agent):
    from mythic_agent.agents.command_handler import CommandHandler
    from mythic_agent.core.policy import ToolPolicy
    from mythic_agent.core.secure_api import subscribe, unsubscribe
    import shlex
    handler = CommandHandler()
    handler.project_root, handler.policy = agent.project_root, ToolPolicy("trusted")
    started = threading.Event()
    def progress(agent_name, text):
        if "slash-started" in text:
            started.set()
    subscribe("agent_command_output", progress)
    try:
        handler._dispatch_command("/test", shlex.join(python_command("import time;print('slash-started',flush=True);time.sleep(60)")))
        assert started.wait(5)
        handler._dispatch_command("/test", shlex.join(python_command("open('queued-unwanted','w').write('x')")))
        handler._dispatch_command("/stop", "")
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            with handler._commands_lock:
                if not handler._commands:
                    break
            time.sleep(0.02)
        with handler._commands_lock:
            assert not handler._commands
        assert not (agent.project_root / "queued-unwanted").exists()
    finally:
        handler._dispatch_command("/stop", "")
        unsubscribe("agent_command_output", progress)
        unsubscribe("system_command_executed", handler._dispatch_command)
