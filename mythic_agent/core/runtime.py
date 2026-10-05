"""Shared turn outcomes and validated operational settings."""

from dataclasses import dataclass
from importlib.resources import files
from typing import Any

import yaml


class TurnCancelled(RuntimeError):
    """A user stopped a turn; adapters must not report success."""


@dataclass(frozen=True)
class TurnResult:
    status: str
    text: str = ""
    error: str | None = None
    total_tokens: int = 0


def runtime_settings(config: dict[str, Any]) -> dict[str, Any]:
    resource = files("mythic_agent.data").joinpath("runtime_defaults.yaml")
    values = yaml.safe_load(resource.read_text(encoding="utf-8"))
    overrides = config.get("runtime", {})
    if not isinstance(overrides, dict):
        raise ValueError("runtime settings must be an object")
    values.update(overrides)
    for key in ("max_retries", "max_tool_rounds", "max_tokens"):
        value = values[key]
        minimum = 0 if key == "max_retries" else 1
        if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
            raise ValueError(f"{key} must be an integer >= {minimum}")
    for key in ("request_timeout", "retry_delay", "retry_delay_cap", "edit_lock_timeout"):
        value = values[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
            raise ValueError(f"{key} must be a positive number")
    return values
