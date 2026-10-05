"""Explicit tool decisions shared by CLI adapters and the runtime."""

from dataclasses import dataclass, field
from importlib.resources import files
from typing import Any, Callable

import yaml


@dataclass
class ToolPolicy:
    mode: str
    approval: Callable[[str, dict[str, Any]], bool] | None = None
    denials: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.mode not in {"read-only", "ask", "trusted"}:
            raise ValueError("Permission mode must be read-only, ask or trusted")
        resource = files("mythic_agent.data").joinpath("permissions.yaml")
        self._read_tools = set(yaml.safe_load(resource.read_text(encoding="utf-8"))["read_only_tools"])

    def authorize(self, name: str, arguments: dict[str, Any]) -> bool:
        if self.mode == "trusted" or name in self._read_tools:
            return True
        if self.mode == "ask" and self.approval and self.approval(name, arguments):
            return True
        self.denials.append(name)
        return False
