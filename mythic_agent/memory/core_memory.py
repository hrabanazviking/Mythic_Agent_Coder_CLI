import json
import os
from pathlib import Path
from ..core.config_manager import config_manager

class CoreMemoryManager:
    """Manages the AI OS Core Memory that persists across compactions and sessions."""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.memory_dir = config_manager.MYTHIC_DIR / "memory" / "core"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.memory_file = self.memory_dir / f"{self.agent_name}_core.json"
        
        self.memory_blocks = {
            "persona": "You are a highly capable AI assistant.",
            "human": "No user details provided yet.",
            "project": "No active project specified.",
            "long_term_notes": "No long-term notes."
        }
        self.load()

    def load(self) -> dict:
        if self.memory_file.exists():
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.memory_blocks.update(data)
            except Exception as e:
                import logging
                logging.error(f"Failed to load core memory for {self.agent_name}: {e}")
        return self.memory_blocks

    def save(self) -> None:
        try:
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(self.memory_blocks, f, indent=4)
        except Exception as e:
            import logging
            logging.error(f"Failed to save core memory for {self.agent_name}: {e}")

    def append(self, block: str, content: str) -> bool:
        if block not in self.memory_blocks:
            return False
        current = self.memory_blocks[block]
        self.memory_blocks[block] = f"{current}\n{content}"
        self.save()
        return True

    def replace(self, block: str, content: str) -> bool:
        if block not in self.memory_blocks:
            return False
        self.memory_blocks[block] = content
        self.save()
        return True

    def format_for_prompt(self) -> str:
        """Returns the core memory formatted as a Markdown block to be injected into the system prompt."""
        return (
            f"\n\n=== AI OS CORE MEMORY ===\n"
            f"[Persona Block]\n{self.memory_blocks['persona']}\n\n"
            f"[Human Block]\n{self.memory_blocks['human']}\n\n"
            f"[Project Block]\n{self.memory_blocks['project']}\n\n"
            f"[Long-Term Notes]\n{self.memory_blocks['long_term_notes']}\n"
            f"=========================\n"
        )
