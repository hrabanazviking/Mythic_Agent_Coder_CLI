"""Parallel tool execution with dependency awareness (Slice 17).

:class:`ParallelExecutor` runs a batch of :class:`ToolCall` entries using a
thread pool. Calls that are independent run concurrently; when one call's
arguments reference another call's output, the dependent call waits until
its dependency has finished and receives the resolved output value.

Output references use the placeholder syntax ``${<call-id>.output}`` inside
string argument values, e.g. ``{"path": "${list.output}/report.txt"}``. The
executor substitutes the dependency's output text before executing the
dependent call.
"""

from __future__ import annotations

import concurrent.futures
import json
import re
from collections.abc import Callable, Mapping
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any

#: Matches ``${call-id.output}`` placeholders in argument values.
_OUTPUT_REF = re.compile(r"\$\{([A-Za-z0-9][A-Za-z0-9_-]*)\.output\}")


@dataclass
class ToolCall:
    """One requested tool invocation.

    ``id`` is generated automatically when omitted. Argument values may
    contain ``${<id>.output}`` placeholders that are resolved against the
    outputs of earlier calls.
    """

    name: str
    arguments: dict[str, Any] = field(default_factory=dict)
    id: str | None = None


@dataclass
class ToolResult:
    """The outcome of one executed :class:`ToolCall`."""

    call: ToolCall
    output: str
    ok: bool = True
    error: str | None = None


def _stringify(value: Any) -> str:
    try:
        return json.dumps(value, default=str)
    except (TypeError, ValueError):
        return str(value)


def referenced_ids(call: ToolCall) -> set[str]:
    """Return the ids of calls whose outputs *call* references."""
    return set(_OUTPUT_REF.findall(_stringify(call.arguments)))


def _resolve_arguments(arguments: Any, outputs: Mapping[str, str]) -> Any:
    """Recursively substitute ``${<id>.output}`` placeholders with outputs."""
    if isinstance(arguments, str):
        def replace(match: re.Match[str]) -> str:
            return outputs.get(match.group(1), match.group(0))
        return _OUTPUT_REF.sub(replace, arguments)
    if isinstance(arguments, Mapping):
        return {k: _resolve_arguments(v, outputs) for k, v in arguments.items()}
    if isinstance(arguments, (list, tuple)):
        return [_resolve_arguments(v, outputs) for v in arguments]
    return arguments


class DependencyError(ValueError):
    """A call references an unknown id, itself, or a dependency cycle."""


class ParallelExecutor:
    """Execute tool calls in parallel, honoring output dependencies.

    Parameters
    ----------
    max_workers:
        Size of the thread pool (default 4).
    execute:
        Callable taking the (dependency-resolved) :class:`ToolCall` and
        returning its :class:`ToolResult`. Defaults to the real agent tool
        dispatcher :func:`mythic_agent.agents.tools.execute_tool`.
    project_root:
        Workspace used by the default ``execute`` implementation.
    timeout:
        Optional per-wave wait budget in seconds; calls still running after
        the budget are reported as failed.
    """

    def __init__(
        self,
        max_workers: int = 4,
        execute: Callable[[ToolCall], ToolResult] | None = None,
        project_root: Any = None,
        timeout: float | None = None,
    ) -> None:
        if max_workers < 1:
            raise ValueError("max_workers must be at least 1")
        self.max_workers = max_workers
        self.project_root = project_root
        self.timeout = timeout
        self._execute = execute or self._default_execute

    # -- default backend -------------------------------------------------
    def _default_execute(self, call: ToolCall) -> ToolResult:
        from .tools import execute_tool  # lazy: keeps this module light to import

        try:
            output = execute_tool(call.name, dict(call.arguments), self.project_root)
            return ToolResult(call=call, output=output, ok=True)
        except Exception as exc:  # noqa: BLE001 - tool errors become results
            return ToolResult(call=call, output="", ok=False, error=str(exc))

    # -- public API ------------------------------------------------------
    def execute_all(self, calls: list[ToolCall]) -> list[ToolResult]:
        """Execute *calls*, returning results in the same order as *calls*.

        Independent calls run concurrently. A call whose arguments contain
        ``${<id>.output}`` waits for that dependency and runs with the
        substituted output. Raises :class:`DependencyError` on unknown
        references or dependency cycles.
        """
        if not calls:
            return []

        indexed = list(enumerate(calls))
        self._assign_ids(calls)
        waves = self._order_waves(calls)

        results: dict[str, ToolResult] = {}
        outputs: dict[str, str] = {}

        for wave in waves:
            resolved = [
                ToolCall(name=c.name, id=c.id,
                         arguments=_resolve_arguments(dict(c.arguments), outputs))
                for c in wave
            ]
            with ThreadPoolExecutor(max_workers=min(self.max_workers, len(resolved))) as pool:
                future_of = {pool.submit(self._run_one, rc): rc for rc in resolved}
                done, pending = concurrent.futures.wait(
                    future_of, timeout=self.timeout,
                    return_when=concurrent.futures.ALL_COMPLETED)
                for future in pending:
                    rc = future_of[future]
                    future.cancel()
                    results[rc.id] = ToolResult(call=rc, output="", ok=False,
                                               error="Timed out waiting for dependency wave")
                for future in done:
                    result = future.result()
                    results[result.call.id] = result
                    outputs[result.call.id] = result.output if result.ok else ""

        ordered = [results[c.id] for _, c in indexed]
        return ordered

    def _run_one(self, call: ToolCall) -> ToolResult:
        try:
            result = self._execute(call)
        except Exception as exc:  # noqa: BLE001 - never let a tool kill the wave
            return ToolResult(call=call, output="", ok=False, error=str(exc))
        if result.call.id is None:
            result.call.id = call.id
        return result

    # -- ordering ---------------------------------------------------------
    @staticmethod
    def _assign_ids(calls: list[ToolCall]) -> None:
        seen: set[str] = set()
        for index, call in enumerate(calls):
            if call.id is None:
                call.id = f"call-{index}"
            if call.id in seen:
                raise DependencyError(f"Duplicate tool call id: {call.id!r}")
            seen.add(call.id)

    def _order_waves(self, calls: list[ToolCall]) -> list[list[ToolCall]]:
        """Kahn's algorithm: levels of calls whose dependencies are satisfied."""
        by_id = {c.id: c for c in calls}
        deps: dict[str, set[str]] = {}
        for call in calls:
            refs = referenced_ids(call)
            for ref in refs:
                if ref not in by_id:
                    raise DependencyError(
                        f"Tool call {call.id!r} references unknown call id {ref!r}")
                if ref == call.id:
                    raise DependencyError(
                        f"Tool call {call.id!r} depends on itself")
            deps[call.id] = set(refs)

        waves: list[list[ToolCall]] = []
        remaining = {cid: set(d) for cid, d in deps.items()}
        id_to_call = by_id
        while remaining:
            ready = sorted(cid for cid, d in remaining.items() if not d)
            if not ready:
                cycle = ", ".join(sorted(remaining))
                raise DependencyError(f"Circular tool dependency: {cycle}")
            waves.append([id_to_call[cid] for cid in ready])
            done = set(ready)
            remaining = {cid: d - done for cid, d in remaining.items() if cid not in done}
        return waves
