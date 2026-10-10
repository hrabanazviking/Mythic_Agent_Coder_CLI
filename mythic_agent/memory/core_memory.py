
__all__ = [
    "CoreMemoryManager",
    "Optional",
    "Path",
    "WorkspaceScope",
    "config_manager",
]
import json
import os
import logging
import threading
import tempfile
from pathlib import Path
from typing import Optional
from ..core.config_manager import config_manager
from .scopes import WorkspaceScope

class CoreMemoryManager:
    """Manages the AI OS Core Memory that persists across compactions and sessions.

    Memory is namespaced by workspace ID (see
    :class:`mythic_agent.memory.scopes.WorkspaceScope`) so agents with the same
    name in different workspaces cannot see or mutate each other's memory.

    Args:
        agent_name: Name of the owning agent.
        workspace_id: Stable workspace identity (see
            :func:`mythic_agent.core.workspace.workspace_id`).  When omitted the
            legacy un-namespaced file layout is used for backward
            compatibility; passing an explicit workspace id is strongly
            recommended.
    """

    def __init__(self, agent_name: str, workspace_id: Optional[str] = None):
        self.agent_name = agent_name
        self.scope = WorkspaceScope(workspace_id)
        self.memory_dir = config_manager.MYTHIC_DIR / "memory" / "core"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        if self.scope.is_default:
            # Legacy layout for callers that do not pass a workspace.
            self.memory_file = self.memory_dir / f"{self.agent_name}_core.json"
        else:
            self.memory_file = (
                self.memory_dir / f"{self.scope.safe_namespace(self.agent_name)}_core.json"
            )
        self._lock = threading.Lock()
        
        self.memory_blocks = {
            "persona": "You are a highly capable AI assistant.",
            "human": "No user details provided yet.",
            "project": "No active project specified.",
            "long_term_notes": "No long-term notes."
        }
        self.load()

    def load(self) -> dict:
        with self._lock:
            if self.memory_file.exists():
                try:
                    with open(self.memory_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        self.memory_blocks.update(data)
                except json.JSONDecodeError as e:
                    logging.error(f"Core memory corrupted for {self.agent_name}. Self-healing... Error: {e}")
                    # Move corrupted file out of the way
                    corrupted_file = self.memory_file.with_suffix('.json.corrupted')
                    try:
                        os.replace(self.memory_file, corrupted_file)
                    except OSError:
                        pass
                except Exception as e:
                    logging.error(f"Failed to load core memory for {self.agent_name}: {e}")
            return self.memory_blocks

    def _atomic_save(self) -> None:
        """Internal lock-assumed atomic save."""
        temp_path = None
        try:
            # Create a temporary file in the same directory
            fd, temp_path = tempfile.mkstemp(dir=self.memory_dir, prefix=f"{self.agent_name}_", suffix=".tmp")
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(self.memory_blocks, f, indent=4)
            # Atomically replace the target file
            os.replace(temp_path, self.memory_file)
        except Exception as e:
            logging.error(f"Failed to atomic save core memory for {self.agent_name}: {e}")
            # Cleanup temp file if possible
            if temp_path is not None:
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    def save(self) -> None:
        with self._lock:
            self._atomic_save()

    def append(self, block: str, content: str) -> bool:
        with self._lock:
            if block not in self.memory_blocks:
                return False
            current = self.memory_blocks[block]
            self.memory_blocks[block] = f"{current}\n{content}"
            self._atomic_save()
            return True

    def replace(self, block: str, content: str) -> bool:
        with self._lock:
            if block not in self.memory_blocks:
                return False
            self.memory_blocks[block] = content
            self._atomic_save()
            return True

    def format_for_prompt(self) -> str:
        """Returns the core memory formatted as a Markdown block to be injected into the system prompt."""
        with self._lock:
            return (
                f"\n\n=== AI OS CORE MEMORY ===\n"
                f"[Persona Block]\n{self.memory_blocks['persona']}\n\n"
                f"[Human Block]\n{self.memory_blocks['human']}\n\n"
                f"[Project Block]\n{self.memory_blocks['project']}\n\n"
                f"[Long-Term Notes]\n{self.memory_blocks['long_term_notes']}\n"
                f"=========================\n"
            )
