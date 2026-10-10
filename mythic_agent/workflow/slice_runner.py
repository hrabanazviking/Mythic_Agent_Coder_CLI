"""Sequential acceptance-gate runner for Mythic Engineering slices.

Each slice's acceptance gates run one after another.  After every gate the
runner writes a checkpoint to ``<MYTHIC_DIR>/slices/<name>.json`` so
:func:`SliceRunner.resume` can continue a run from the last completed gate
after an interruption or a failed gate.
"""


from __future__ import annotations

__all__ = [
    "Any",
    "CheckpointError",
    "GateResult",
    "Optional",
    "Path",
    "SliceDefinition",
    "SliceResult",
    "SliceRunner",
    "config_manager",
    "dataclass",
    "field",
]

import dataclasses
import json
import logging
import re
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from ..core.config_manager import config_manager
from ..core.exceptions import MythicExecutionError


class CheckpointError(MythicExecutionError):
    """Raised when a slice checkpoint is missing or unreadable."""


@dataclass
class SliceDefinition:
    """Definition of one Mythic Engineering work slice."""

    name: str
    description: str
    work_order_path: Optional[str] = None
    acceptance_gates: list[str] = field(default_factory=list)


@dataclass
class GateResult:
    """Outcome of a single acceptance-gate command."""

    index: int
    command: str
    returncode: int
    stdout: str
    stderr: str
    passed: bool
    duration_s: float


@dataclass
class SliceResult:
    """Aggregated outcome of a slice run."""

    slice_name: str
    success: bool
    gate_results: list[GateResult]
    log: str
    completed_gates: int = 0
    total_gates: int = 0


class SliceRunner:
    """Runs :class:`SliceDefinition` acceptance gates sequentially.

    Args:
        checkpoint_dir: Where per-slice checkpoints live.  Defaults to
            ``<MYTHIC_DIR>/slices`` (normally ``~/.mythic/slices``).
        default_timeout: Per-gate subprocess timeout in seconds; ``None``
            means no timeout.
    """

    CHECKPOINT_VERSION = 1

    def __init__(
        self,
        checkpoint_dir: Path | str | None = None,
        default_timeout: float | None = None,
    ):
        self.checkpoint_dir = (
            Path(checkpoint_dir) if checkpoint_dir is not None
            else config_manager.MYTHIC_DIR / "slices"
        )
        self.default_timeout = default_timeout

    # ------------------------------------------------------------------ #
    # checkpoints                                                           #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _safe_name(name: str) -> str:
        safe = re.sub(r"[^A-Za-z0-9_-]+", "_", name).strip("_")
        if not safe:
            raise ValueError("Slice name must contain at least one safe character")
        return safe

    def _checkpoint_path(self, name: str) -> Path:
        return self.checkpoint_dir / f"{self._safe_name(name)}.json"

    def _write_checkpoint(
        self,
        definition: SliceDefinition,
        completed: int,
        gate_results: list[GateResult],
        log_lines: list[str],
    ) -> Path:
        """Persist run progress atomically after each gate."""
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        payload: dict[str, Any] = {
            "version": self.CHECKPOINT_VERSION,
            "definition": {
                "name": definition.name,
                "description": definition.description,
                "work_order_path": definition.work_order_path,
                "acceptance_gates": list(definition.acceptance_gates),
            },
            "completed_gates": completed,
            "complete": completed >= len(definition.acceptance_gates),
            "gate_results": [dataclasses.asdict(g) for g in gate_results],
            "log": log_lines,
        }
        path = self._checkpoint_path(definition.name)
        fd, tmp = tempfile.mkstemp(
            dir=self.checkpoint_dir, prefix=path.stem + "_", suffix=".tmp"
        )
        try:
            with open(fd, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            Path(tmp).replace(path)
        except Exception:
            Path(tmp).unlink(missing_ok=True)
            raise
        return path

    def _read_checkpoint(self, name: str) -> dict[str, Any]:
        path = self._checkpoint_path(name)
        if not path.exists():
            raise CheckpointError(f"No checkpoint found for slice {name!r}")
        try:
            with open(path, encoding="utf-8") as f:
                payload = json.load(f)
        except json.JSONDecodeError as exc:
            raise CheckpointError(f"Checkpoint for slice {name!r} is corrupted: {exc}") from exc
        if payload.get("version") != self.CHECKPOINT_VERSION:
            raise CheckpointError(
                f"Checkpoint for slice {name!r} has unsupported version "
                f"{payload.get('version')!r}"
            )
        return payload

    # ------------------------------------------------------------------ #
    # execution                                                             #
    # ------------------------------------------------------------------ #

    def _run_gate(
        self,
        index: int,
        command: str,
        cwd: Path | None,
        timeout: float | None,
    ) -> GateResult:
        """Execute one gate shell command and capture the outcome."""
        start = time.monotonic()
        try:
            proc = subprocess.run(
                command,
                shell=True,  # acceptance gates are shell commands by design
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=timeout,
            )
            stdout, stderr, returncode = proc.stdout, proc.stderr, proc.returncode
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            stderr = (exc.stderr or "") + f"\n[TIMEOUT after {timeout}s]"
            returncode = 124
        duration = time.monotonic() - start
        return GateResult(
            index=index,
            command=command,
            returncode=returncode,
            stdout=stdout or "",
            stderr=stderr or "",
            passed=returncode == 0,
            duration_s=duration,
        )

    def run(
        self,
        slice_def: SliceDefinition,
        *,
        timeout: float | None = None,
        _start_at: int = 0,
        _prior_results: list[GateResult] | None = None,
        _prior_log: list[str] | None = None,
    ) -> SliceResult:
        """Execute the slice's gates sequentially and return the aggregated result.

        Gates run in order; the first failing gate stops execution.  Progress
        is checkpointed after every gate so :meth:`resume` can continue later.

        Private ``_start_at`` / ``_prior_*`` parameters support resume and are
        not part of the public API.
        """
        timeout = self.default_timeout if timeout is None else timeout
        total = len(slice_def.acceptance_gates)
        gate_results: list[GateResult] = list(_prior_results or [])
        log_lines: list[str] = list(_prior_log or [])

        work_order = Path(slice_def.work_order_path).expanduser() if slice_def.work_order_path else None
        cwd = work_order.parent if work_order else None
        log_lines.append(
            f"=== Slice '{slice_def.name}': {slice_def.description} "
            f"({total} gate(s), starting at gate {_start_at}) ==="
        )

        for index in range(_start_at, total):
            command = slice_def.acceptance_gates[index]
            log_lines.append(f"[gate {index + 1}/{total}] $ {command}")
            result = self._run_gate(index, command, cwd, timeout)
            gate_results.append(result)
            log_lines.append(
                f"[gate {index + 1}/{total}] {'PASS' if result.passed else 'FAIL'} "
                f"(exit {result.returncode}, {result.duration_s:.2f}s)"
            )
            if result.stdout.strip():
                log_lines.append(f"  stdout: {result.stdout.strip()[:2000]}")
            if result.stderr.strip():
                log_lines.append(f"  stderr: {result.stderr.strip()[:2000]}")
            self._write_checkpoint(slice_def, index + 1, gate_results, log_lines)
            if not result.passed:
                log_lines.append(
                    f"=== Slice '{slice_def.name}' STOPPED at gate {index + 1}/{total} ==="
                )
                # Checkpoint the last *completed* gate so resume() re-attempts
                # the failed gate after the underlying issue is fixed.
                self._write_checkpoint(slice_def, index, gate_results, log_lines)
                return SliceResult(
                    slice_name=slice_def.name,
                    success=False,
                    gate_results=gate_results,
                    log="\n".join(log_lines),
                    completed_gates=index,
                    total_gates=total,
                )

        log_lines.append(f"=== Slice '{slice_def.name}' COMPLETE ({total}/{total} gates) ===")
        self._write_checkpoint(slice_def, total, gate_results, log_lines)
        return SliceResult(
            slice_name=slice_def.name,
            success=True,
            gate_results=gate_results,
            log="\n".join(log_lines),
            completed_gates=total,
            total_gates=total,
        )

    def resume(self, name: str, *, timeout: float | None = None) -> SliceResult:
        """Continue a previously checkpointed slice from its last completed gate.

        Raises:
            CheckpointError: If no checkpoint exists or it is unreadable.
        """
        payload = self._read_checkpoint(name)
        defn = payload["definition"]
        definition = SliceDefinition(
            name=defn["name"],
            description=defn["description"],
            work_order_path=defn.get("work_order_path"),
            acceptance_gates=defn["acceptance_gates"],
        )
        prior_results = [GateResult(**g) for g in payload.get("gate_results", [])]
        prior_log: list[str] = payload.get("log", [])
        completed = payload["completed_gates"]
        if payload.get("complete"):
            logging.info("Slice %r already complete; returning stored result.", name)
            return SliceResult(
                slice_name=definition.name,
                success=all(g.passed for g in prior_results),
                gate_results=prior_results,
                log="\n".join(prior_log),
                completed_gates=completed,
                total_gates=len(definition.acceptance_gates),
            )
        return self.run(
            definition,
            timeout=timeout,
            _start_at=completed,
            _prior_results=prior_results,
            _prior_log=prior_log,
        )
