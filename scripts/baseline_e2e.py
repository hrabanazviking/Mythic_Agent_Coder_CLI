#!/usr/bin/env python3
"""Scripted end-to-end baseline task (All-Features roadmap slice M-007).

The "before" recording Part XI will compare against: a fixed script of
real tasks driven through the real CLI (`python -m mythic_agent.cli`)
against a local, free, fake OpenAI-compatible provider — the same
dialect the integration suite uses (`tests/test_cli.py`). No network,
no real provider, no API key: the provider is a loopback HTTP server
in this process that echoes prompts and issues one fixed tool call.

Scripted steps (ids E-01..E-04, mirrored in
``mythic_agent/data/baseline_freeze.yaml``):

- E-01  one-shot reply: ``run hello --format json`` completes with the
  echoed text and the fixture's token total.
- E-02  read-only refusal: ``run write --format json`` under the
  default machine policy is refused (exit 3, ``approval_required``)
  and no file is written.
- E-03  trusted write: ``run write --permission trusted --format
  json`` executes the write tool; the file lands with exact content.
- E-04  resume + sessions: a second turn resumes E-01's session in a
  new process (same session id, token total accumulates) and
  ``sessions`` lists the workspace's sessions — one per earlier
  ``run`` (E-01..E-03), E-01's among them — without contacting the
  provider again.

Usage:
    python scripts/baseline_e2e.py [--out REPORT.json]

Prints the JSON report to stdout; exit 0 iff every step passed.
Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


class _FixtureHandler(BaseHTTPRequestHandler):
    """Echo provider: replies 'Reply: <prompt>'; 'write'/'read' prompts
    first issue the matching tool call, exactly like tests/test_cli.py."""

    requests: list = []

    def log_message(self, *args):  # silence
        pass

    def do_POST(self):
        request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        type(self).requests.append(request)
        last = request["messages"][-1]
        content = last.get("content", "")
        self.send_response(200)
        message = {"role": "assistant", "content": "Reply: " + (content or "")}
        if last["role"] == "user" and content in {"write", "read"}:
            tool = "write_file" if content == "write" else "read_file"
            arguments = {"path": "generated.py"}
            if tool == "write_file":
                arguments["content"] = "answer = 42\n"
            message = {
                "role": "assistant",
                "content": "Inspecting tools",
                "tool_calls": [{
                    "id": "fixture-call",
                    "type": "function",
                    "function": {"name": tool, "arguments": json.dumps(arguments)},
                }],
            }
        body = {
            "id": "fixture-response",
            "object": "chat.completion",
            "created": 1,
            "model": "fixture-model",
            "choices": [{
                "index": 0,
                "message": message,
                "finish_reason": "tool_calls" if message.get("tool_calls") else "stop",
            }],
            "usage": {"prompt_tokens": 3, "completion_tokens": 4, "total_tokens": 7},
        }
        encoded = json.dumps(body).encode()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def _clean_env(app_state: Path) -> dict:
    env = os.environ.copy()
    for key in list(env):
        if key.endswith("_API_KEY") or "proxy" in key.lower():
            env.pop(key, None)
    env["NO_PROXY"] = "127.0.0.1,localhost"
    env["no_proxy"] = "127.0.0.1,localhost"
    env["MYTHIC_HOME"] = str(app_state)
    return env


def _invoke(workspace: Path, base_url: str, env: dict, *arguments: str,
            input_text: str | None = None) -> subprocess.CompletedProcess:
    command = [sys.executable, "-m", "mythic_agent.cli", arguments[0],
               "--workspace", str(workspace)]
    if arguments[0] != "sessions":
        command += ["--base-url", base_url, "--model", "fixture-model"]
    command += list(arguments[1:])
    return subprocess.run(command, input=input_text, capture_output=True,
                          text=True, env=env, timeout=60, cwd=REPO_ROOT)


def run_recording() -> dict:
    """Run the four scripted steps in a throwaway workspace; return the report."""
    _FixtureHandler.requests = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), _FixtureHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}/v1"
    steps: list[dict] = []

    def record(step_id: str, name: str, started: float, ok: bool, detail: str):
        steps.append({
            "id": step_id,
            "name": name,
            "passed": bool(ok),
            "duration_s": round(time.perf_counter() - started, 3),
            "detail": detail,
        })

    try:
        with tempfile.TemporaryDirectory(prefix="mythic-baseline-e2e-") as tmp:
            workspace = Path(tmp)
            env = _clean_env(workspace / "app-state")

            started = time.perf_counter()
            r1 = _invoke(workspace, base_url, env, "run", "hello", "--format", "json")
            out1 = json.loads(r1.stdout) if r1.returncode == 0 else {}
            record("E-01", "one-shot reply", started,
                   r1.returncode == 0 and out1.get("status") == "completed"
                   and out1.get("text") == "Reply: hello"
                   and out1.get("total_tokens") == 7,
                   f"exit={r1.returncode} status={out1.get('status')!r} "
                   f"text={out1.get('text')!r} tokens={out1.get('total_tokens')!r}")
            session_id = out1.get("session_id", "")

            started = time.perf_counter()
            r2 = _invoke(workspace, base_url, env, "run", "write", "--format", "json")
            out2 = json.loads(r2.stdout) if r2.stdout.strip() else {}
            record("E-02", "read-only write refusal", started,
                   r2.returncode == 3 and out2.get("status") == "approval_required"
                   and out2.get("denied_tools") == ["write_file"]
                   and not (workspace / "generated.py").exists(),
                   f"exit={r2.returncode} status={out2.get('status')!r} "
                   f"denied={out2.get('denied_tools')!r} file_written="
                   f"{(workspace / 'generated.py').exists()}")

            started = time.perf_counter()
            r3 = _invoke(workspace, base_url, env, "run", "write",
                         "--permission", "trusted", "--format", "json")
            written = (workspace / "generated.py")
            content = written.read_text() if written.exists() else None
            out3 = json.loads(r3.stdout) if r3.returncode == 0 else {}
            record("E-03", "trusted write executes", started,
                   r3.returncode == 0 and content == "answer = 42\n"
                   and out3.get("total_tokens") == 14,
                   f"exit={r3.returncode} content={content!r} "
                   f"tokens={out3.get('total_tokens')!r}")

            started = time.perf_counter()
            before = len(_FixtureHandler.requests)
            r4 = _invoke(workspace, base_url, env, "run", "again",
                         "--resume", session_id, "--format", "json")
            out4 = json.loads(r4.stdout) if r4.returncode == 0 else {}
            listed = _invoke(workspace, base_url, env, "sessions")
            listed_ids = [s["id"] for s in json.loads(listed.stdout)["sessions"]] \
                if listed.returncode == 0 else []
            record("E-04", "resume + sessions list", started,
                   r4.returncode == 0 and out4.get("session_id") == session_id
                   and out4.get("total_tokens") == 14
                   and session_id in listed_ids and len(listed_ids) == 3
                   and len(_FixtureHandler.requests) == before + 1,
                   f"exit={r4.returncode} session_match="
                   f"{out4.get('session_id') == session_id} "
                   f"tokens={out4.get('total_tokens')!r} listed={listed_ids!r} "
                   f"provider_calls_for_resume+list="
                   f"{len(_FixtureHandler.requests) - before}")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    return {
        "script": "scripts/baseline_e2e.py",
        "provider": "loopback fake OpenAI-compatible fixture (no network, no key)",
        "steps": steps,
        "passed": sum(1 for s in steps if s["passed"]),
        "total": len(steps),
        "all_passed": all(s["passed"] for s in steps),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", help="Also write the JSON report to this path")
    args = parser.parse_args(argv)
    report = run_recording()
    text = json.dumps(report, indent=2)
    print(text)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
