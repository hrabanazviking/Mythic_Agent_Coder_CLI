"""Execution sandboxing for shell commands.

Wraps command execution with guardrails: a denylist of destructive
commands, wall-clock timeouts, RSS memory limits (POSIX ``resource``
module), and an optional no-network mode (``LD_PRELOAD`` stub honored
by the caller when available).  :func:`dry_run` explains what a command
would do without running anything.

Usage:
    from mythic_agent.core.sandbox import Sandbox
    sb = Sandbox(timeout=30.0, memory_limit_mb=512, no_network=True)
    result = sb.run("git status", cwd="/path/to/project")
    print(result.stdout)
"""


from __future__ import annotations

__all__ = [
    "Any",
    "Path",
    "Sandbox",
    "SandboxError",
    "SandboxResult",
    "dataclass",
    "field",
]

import os
import re
import shlex
import signal
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .exceptions import MythicSandboxError


#: Regex fragments matching destructive shell invocations.  Any match
#: against the command string aborts execution with a refusal.
_DENYLIST_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\brm\b[^;&|]*\s-[a-zA-Z]*r[a-zA-Z]*f", "recursive force deletion (rm -rf)"),
    (r"\bmkfs\b", "filesystem creation (mkfs)"),
    (r"\bdd\b\s+[^;&|]*of=\s*/dev/", "raw device write (dd of=/dev/...)"),
    (r"\b(shred|wipefs|blkdiscard|hdparm)\b", "disk-wiping utility"),
    (r"\bshutdown\b|\breboot\b|\bhalt\b|\bpoweroff\b", "system shutdown/reboot"),
    (r":\s*\(\s*\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;", "fork bomb"),
    (r"\b(mkswap|swapoff|swapon)\b", "swap manipulation"),
    (r"\b(sysctl\s+-w|echo\s+[^>]*>\s*/proc/sys)\b", "kernel parameter write"),
    (r">\s*/dev/(sd[a-z]|hd[a-z]|nvme\d*n\d+)", "raw block-device overwrite"),
    (r"\bchmod\s+-R\s+777\s+/\b", "world-writable chmod of filesystem root"),
    (r"\bchown\s+-R\b[^;&|]*\s+/\b", "recursive chown of filesystem root"),
    (r"\bcurl\b.*\|\s*(sh|bash)\b", "pipe-to-shell download"),
    (r"\bwget\b.*\|\s*(sh|bash)\b", "pipe-to-shell download"),
)


@dataclass
class SandboxResult:
    """Outcome of a sandboxed command run."""

    command: str
    returncode: int
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False
    killed_by_memory: bool = False
    duration_s: float = 0.0

    @property
    def ok(self) -> bool:
        return self.returncode == 0 and not self.timed_out

    def render(self) -> str:
        status = "timed out" if self.timed_out else f"exit {self.returncode}"
        head = f"$ {self.command}\n[{status} in {self.duration_s:.2f}s]"
        body = f"\n{self.stdout.rstrip()}" if self.stdout.strip() else ""
        err = f"\n[stderr]\n{self.stderr.rstrip()}" if self.stderr.strip() else ""
        return head + body + err


class SandboxError(MythicSandboxError):
    """Raised when a command is refused or cannot be sandboxed."""


class Sandbox:
    """Run shell commands under time, memory, and safety guardrails."""

    def __init__(
        self,
        *,
        timeout: float = 60.0,
        memory_limit_mb: int | None = 512,
        no_network: bool = False,
        env: dict[str, str] | None = None,
    ) -> None:
        self.timeout = timeout
        self.memory_limit_mb = memory_limit_mb
        self.no_network = no_network
        self.extra_env = dict(env or {})

    # -- pre-execution checks ------------------------------------------------
    def check_denied(self, cmd: str) -> str | None:
        """Return the refusal reason if *cmd* matches the denylist, else None."""
        for pattern, reason in _DENYLIST_PATTERNS:
            if re.search(pattern, cmd):
                return reason
        return None

    def _check_denied_or_raise(self, cmd: str) -> None:
        reason = self.check_denied(cmd)
        if reason is not None:
            raise SandboxError(f"Refused to run dangerous command ({reason}): {cmd[:120]}")

    # -- limits --------------------------------------------------------------
    def _limit_fn(self) -> None:
        """Child-side preexec_fn: cap address space via RLIMIT_AS."""
        if self.memory_limit_mb is None:
            return
        try:
            import resource  # POSIX only

            limit = self.memory_limit_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
        except (ImportError, ValueError, OSError):
            pass

    def _build_env(self) -> dict[str, str]:
        env = os.environ.copy()
        env.update(self.extra_env)
        if self.no_network:
            # Convention honored by our no-network runner shim when present.
            env["MYTHIC_SANDBOX_NO_NETWORK"] = "1"
        return env

    # -- execution -----------------------------------------------------------
    def run(
        self,
        cmd: str,
        cwd: str | Path | None = None,
        *,
        timeout: float | None = None,
    ) -> SandboxResult:
        """Run *cmd* under the sandbox limits and return a SandboxResult."""
        if not isinstance(cmd, str) or not cmd.strip():
            raise SandboxError("Command must be a nonempty string")
        self._check_denied_or_raise(cmd)
        workdir = str(cwd) if cwd is not None else str(Path.cwd())
        deadline = timeout if timeout is not None else self.timeout
        import time

        start = time.monotonic()
        timed_out = False
        try:
            proc = subprocess.run(
                cmd,
                shell=True,
                cwd=workdir,
                env=self._build_env(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=deadline,
                preexec_fn=self._limit_fn,
                start_new_session=True,
            )
            rc, out, err = proc.returncode, proc.stdout or "", proc.stderr or ""
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            out = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
            err = (exc.stderr or "") if isinstance(exc.stderr, str) else ""
            rc = 124
        duration = time.monotonic() - start
        killed_by_memory = rc in (137, 139, 134) and "Cannot allocate memory" in (err or "")
        return SandboxResult(
            command=cmd,
            returncode=rc,
            stdout=out,
            stderr=err,
            timed_out=timed_out,
            killed_by_memory=killed_by_memory,
            duration_s=duration,
        )

    # -- dry run --------------------------------------------------------------
    def dry_run(self, cmd: str) -> str:
        """Describe what *cmd* would do, without executing anything."""
        if not isinstance(cmd, str) or not cmd.strip():
            raise SandboxError("Command must be a nonempty string")
        reason = self.check_denied(cmd)
        if reason is not None:
            return f"REFUSED: this command would be blocked ({reason})."
        lines = [f"Would run (timeout={self.timeout}s): {cmd}"]
        try:
            tokens = shlex.split(cmd)
        except ValueError as exc:
            return "\n".join(lines + [f"Could not parse command: {exc}"])
        # Split pipelines/sequences into stages for per-stage explanation.
        stages: list = []
        current: list[str] = []
        for tok in tokens:
            if tok in {"|", "&&", ";", "||"}:
                if current:
                    stages.append(current)
                    current = []
            else:
                current.append(tok)
        if current:
            stages.append(current)
        for stage in stages:
            lines.append(f"  - {_explain_stage(stage)}")
        if self.memory_limit_mb is not None:
            lines.append(f"Memory cap: {self.memory_limit_mb} MB (RLIMIT_AS).")
        if self.no_network:
            lines.append("Network access: disabled (MYTHIC_SANDBOX_NO_NETWORK=1).")
        return "\n".join(lines)


def _explain_stage(tokens: list[str]) -> str:
    prog = tokens[0] if tokens else ""
    args = " ".join(tokens[1:]) if len(tokens) > 1 else ""
    known = {
        "ls": "list directory contents",
        "cd": "change directory",
        "pwd": "print working directory",
        "echo": "print text",
        "cat": "print file contents",
        "grep": "search text for a pattern",
        "find": "search for files",
        "git": "run a git operation",
        "python": "run the Python interpreter",
        "python3": "run the Python interpreter",
        "pytest": "run the test suite",
        "make": "run a make target",
        "npm": "run an npm command",
        "pip": "manage Python packages",
        "curl": "transfer data over HTTP",
        "wget": "download a file over HTTP",
        "tar": "archive/unarchive files",
        "zip": "compress files",
        "unzip": "extract a zip archive",
        "sed": "stream-edit text",
        "awk": "process text columns/rows",
        "sort": "sort lines of text",
        "head": "show the first lines of a file",
        "tail": "show the last lines of a file",
        "wc": "count lines/words/bytes",
        "diff": "compare two files",
        "mv": "move/rename files",
        "cp": "copy files",
        "mkdir": "create directories",
        "rmdir": "remove empty directories",
        "touch": "create or timestamp files",
        "chmod": "change file permissions",
        "chown": "change file ownership",
        "env": "show environment variables",
        "whoami": "print current user",
        "date": "print the date",
        "sleep": "pause execution",
    }
    what = known.get(prog, f"execute program '{prog}'")
    detail = f" ({args})" if args else ""
    return f"{what}{detail}"
