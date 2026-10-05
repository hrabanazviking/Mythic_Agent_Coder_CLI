"""Explicit tool decisions shared by CLI adapters and the runtime."""

from dataclasses import dataclass, field
from importlib.resources import files
from typing import Any, Callable

import yaml
from .runtime import TurnCancelled


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
        if self.mode == "ask" and self.approval:
            try:
                if self.approval(name, arguments) is True:
                    return True
            except TurnCancelled:
                raise
            except Exception:
                pass  # A broken/closed approval adapter is a refusal.
        self.denials.append(name)
        return False

    def fork(self) -> "ToolPolicy":
        """Inherit decisions, with independent refusal receipts."""
        return ToolPolicy(self.mode, self.approval)


def policy_mode(config: dict[str, Any], *, machine: bool = False, override: str | None = None) -> str:
    if override is not None:
        return override
    if machine:
        return config.get("machine_permission_mode", "read-only")
    if config.get("auto_accept_permissions"):
        return "trusted"
    return config.get("permission_mode", "ask")
