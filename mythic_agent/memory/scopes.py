"""Workspace memory scoping.

The core memory manager historically keyed all state by agent name alone, so two
distinct workspaces running an agent with the same name silently shared memory
(see TASK_development_roadmap.md).  This module provides :class:`WorkspaceScope`,
a small value object that namespaces memory keys by workspace ID so memory is
isolated per workspace.
"""


from __future__ import annotations

__all__ = [
    "Any",
    "Path",
    "WorkspaceScope",
    "sanitize_segment",
    "scope_for_root",
    "scoped_agent_key",
]

import re
from pathlib import Path
from typing import Any

# Characters unsafe in filenames / storage keys are collapsed to "_".
_SAFE_CHUNK = re.compile(r"[^A-Za-z0-9_-]+")


def sanitize_segment(value: str) -> str:
    """Make an arbitrary string safe for use in a key or filename segment."""
    cleaned = _SAFE_CHUNK.sub("_", value.strip())
    return cleaned.strip("_") or "default"


class WorkspaceScope:
    """Namespaces memory keys for one workspace.

    Args:
        workspace_id: Stable identity of the workspace (see
            :func:`mythic_agent.core.workspace.workspace_id`, a sha256 of the
            resolved workspace root).

    Keys produced by :meth:`namespace` take the form
    ``"<workspace_id>:<key>"`` for in-memory/storage keys.  File-system callers
    should use :meth:`safe_namespace`, which yields an equivalent but
    filename-safe token.
    """

    def __init__(self, workspace_id: str | None):
        self.workspace_id = workspace_id or "default"

    @property
    def is_default(self) -> bool:
        """True when no explicit workspace was supplied (legacy behavior)."""
        return self.workspace_id == "default"

    def namespace(self, key: str) -> str:
        """Return ``key`` namespaced by the workspace id: ``"<ws>:<key>"``."""
        return f"{self.workspace_id}:{key}"

    def safe_namespace(self, key: str) -> str:
        """Filename-safe variant of :meth:`namespace`."""
        return f"{sanitize_segment(self.workspace_id)}_{sanitize_segment(key)}"

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"WorkspaceScope(workspace_id={self.workspace_id!r})"


def scope_for_root(root: Path | str | None) -> WorkspaceScope:
    """Build a :class:`WorkspaceScope` from a workspace root path."""
    from ..core.workspace import resolve_workspace, workspace_id

    if root is None:
        return WorkspaceScope(None)
    resolved = resolve_workspace(root)
    return WorkspaceScope(workspace_id(resolved))


def scoped_agent_key(workspace_id: str | None, agent_name: str, key: str) -> str:
    """Canonical namespaced memory key: ``"<workspace_id>:<agent_name>:<key>"``."""
    return WorkspaceScope(workspace_id).namespace(f"{agent_name}:{key}")
