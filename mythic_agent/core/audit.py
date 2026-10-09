"""Append-only audit logging for safety-relevant events.

Every entry records who did what, when, and with what details, as one
JSON object per line in ``workspace/.mythic/audit.jsonl``.  The log is
append-only: existing entries are never modified or deleted through
this API.

Usage:
    from mythic_agent.core.audit import AuditLog
    audit = AuditLog(workspace_root)
    audit.log("tool.execute", actor="primary", details={"tool": "run_command"})
    for entry in audit.query({"action": "tool.execute"}):
        print(entry.timestamp, entry.details)
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AuditEntry:
    """One immutable audit record."""

    timestamp: str
    action: str
    actor: str
    details: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, action: str, actor: str, details: dict[str, Any] | None = None) -> "AuditEntry":
        return cls(
            timestamp=datetime.now(timezone.utc).isoformat(),
            action=action,
            actor=actor,
            details=dict(details or {}),
        )

    def to_json(self) -> str:
        return json.dumps(asdict(self), default=str)

    @classmethod
    def from_json(cls, line: str) -> "AuditEntry":
        obj = json.loads(line)
        return cls(
            timestamp=obj.get("timestamp", ""),
            action=obj.get("action", ""),
            actor=obj.get("actor", ""),
            details=obj.get("details", {}) or {},
        )


class AuditLog:
    """Append-only JSONL audit log rooted at a workspace."""

    LOG_DIRNAME = ".mythic"
    LOG_FILENAME = "audit.jsonl"

    def __init__(self, workspace_root: str | Path | None = None) -> None:
        self.workspace_root = Path(workspace_root) if workspace_root else Path.cwd()
        self.log_path = self.workspace_root / self.LOG_DIRNAME / self.LOG_FILENAME

    # -- writing -------------------------------------------------------------
    def log(self, action: str, actor: str, details: dict[str, Any] | None = None) -> AuditEntry:
        """Append one entry; create the log directory on first use."""
        if not action or not actor:
            raise ValueError("action and actor are required")
        entry = AuditEntry.create(action, actor, details)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as fh:
            fh.write(entry.to_json() + "\n")
        return entry

    # Convenience recorders for the events this slice mandates.
    def log_tool_execution(self, actor: str, tool: str, arguments: dict[str, Any] | None = None, result: str = "") -> AuditEntry:
        return self.log("tool.execute", actor, {"tool": tool, "arguments": arguments or {}, "result_summary": result[:200]})

    def log_file_write(self, actor: str, path: str, bytes_written: int = 0) -> AuditEntry:
        return self.log("file.write", actor, {"path": path, "bytes_written": bytes_written})

    def log_permission_decision(self, actor: str, tool: str, granted: bool, reason: str = "") -> AuditEntry:
        return self.log("permission.decision", actor, {"tool": tool, "granted": granted, "reason": reason})

    # -- reading -------------------------------------------------------------
    def query(self, filters: dict[str, Any] | None = None) -> list[AuditEntry]:
        """Return entries matching *filters* (exact match on top-level fields
        and, for ``details``, exact match on nested keys)."""
        filters = filters or {}
        matches: list[AuditEntry] = []
        if not self.log_path.exists():
            return matches
        with self.log_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = AuditEntry.from_json(line)
                except (json.JSONDecodeError, KeyError, TypeError):
                    continue
                if self._matches(entry, filters):
                    matches.append(entry)
        return matches

    @staticmethod
    def _matches(entry: AuditEntry, filters: dict[str, Any]) -> bool:
        for key, want in filters.items():
            if key == "details":
                if not isinstance(want, dict):
                    return False
                for dkey, dval in want.items():
                    if entry.details.get(dkey) != dval:
                        return False
                continue
            if getattr(entry, key, None) != want:
                return False
        return True

    def count(self) -> int:
        return len(self.query())
