"""Non-mutating configuration reads and private, recoverable explicit saves."""

import copy
import json
import logging
import os
import uuid
from importlib.resources import files
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlsplit

import yaml
from filelock import FileLock

from .runtime import runtime_settings
from .secure_api import publish_sync
from .storage import atomic_private_json, atomic_private_write
from .redaction import SecretRedactor, protect_logging

logger = logging.getLogger("mythic_config_manager")


class ConfigManager:
    def __init__(self, root: Path | str | None = None):
        configured = os.environ.get("MYTHIC_HOME")
        self.MYTHIC_DIR = Path(root or configured or Path.home() / ".mythic").expanduser().resolve()
        self.CONFIG_FILE = self.MYTHIC_DIR / "config.json"
        self._allow_legacy = root is None and not configured
        self.defaults = yaml.safe_load(files("mythic_agent.data").joinpath(
            "config_defaults.yaml").read_text(encoding="utf-8"))
        self.DEFAULT_MODEL = self.defaults["model"]
        self.DEFAULT_BASE_URL = self.defaults["base_url"]
        self.CURRENT_CONFIG_VERSION = self.defaults["config_version"]
        self.last_load_warning: str | None = None
        try:
            self.MYTHIC_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
            (self.MYTHIC_DIR / "status").mkdir(parents=True, exist_ok=True, mode=0o700)
        except OSError as exc:
            logger.error("State directory unavailable: %s", type(exc).__name__)

    def load_config(self) -> Dict[str, Any]:
        """Read/normalize in memory; preserve original bytes and customized prompts."""
        self.last_load_warning = None
        source = self.CONFIG_FILE
        legacy = Path.home() / ".mythic_config.json"
        if not source.exists() and self._allow_legacy and legacy.exists():
            source = legacy
        raw: dict[str, Any] = {}
        if source.exists():
            try:
                parsed = json.loads(source.read_text(encoding="utf-8"))
                if not isinstance(parsed, dict):
                    raise ValueError("Configuration root must be an object")
                raw = parsed
            except (OSError, ValueError) as exc:
                self.last_load_warning = f"Settings unreadable ({type(exc).__name__}); original preserved."
                logger.warning(self.last_load_warning)
        config = self._upgrade_stale_data(raw)
        overrides = {"MYTHIC_MODEL": "model", "MYTHIC_BASE_URL": "base_url",
                     "MYTHIC_WORKSPACE": "working_directory", "MYTHIC_PERMISSION": "machine_permission_mode"}
        for environment, key in overrides.items():
            value = os.environ.get(environment)
            if value:
                valid = (self._valid_url(value) if key == "base_url" else
                         value in {"read-only", "ask", "trusted"} if key == "machine_permission_mode" else True)
                if valid:
                    config[key] = value
                else:
                    logger.warning("Invalid %s override ignored", environment)
        protect_logging(SecretRedactor(config))
        return config

    @staticmethod
    def _valid_url(value: Any) -> bool:
        if not isinstance(value, str):
            return False
        try:
            parsed = urlsplit(value)
            return parsed.scheme in {"http", "https"} and bool(parsed.hostname)
        except ValueError:
            return False

    def _upgrade_stale_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Preserve all unknown/custom data; recover invalid known fields separately."""
        result = copy.deepcopy(config)
        recovery = result.get("recovery")
        recovery = copy.deepcopy(recovery) if isinstance(recovery, dict) else (
            {"original_recovery": recovery} if "recovery" in result else {})
        for key, default in self.defaults.items():
            value = result.get(key, default)
            valid = isinstance(value, type(default)) and not (
                isinstance(default, int) and not isinstance(default, bool) and isinstance(value, bool))
            if key == "model":
                valid = valid and bool(value.strip())
            if key == "base_url":
                valid = self._valid_url(value)
            if key in {"permission_mode", "machine_permission_mode"}:
                valid = valid and value in {"read-only", "ask", "trusted"}
            if not valid:
                recovery[key] = value
                value = copy.deepcopy(default)
            result[key] = copy.deepcopy(value)
        for key in ("system_prompt", "primary_name"):
            if key in result and not isinstance(result[key], str):
                recovery[key] = result.pop(key)
        if result["config_version"] < self.CURRENT_CONFIG_VERSION:
            result["config_version"] = self.CURRENT_CONFIG_VERSION
        self._repair_keys(result, recovery)
        self._repair_runtime(result, recovery)
        self._repair_subagents(result, recovery)
        if recovery:
            result["recovery"] = recovery
        return result

    def _repair_keys(self, result: dict[str, Any], recovery: dict[str, Any]) -> None:
        keys = result["api_keys"]
        valid = {key: value for key, value in keys.items()
                 if isinstance(key, str) and isinstance(value, str)}
        if valid != keys:
            recovery["api_keys"] = keys
            result["api_keys"] = valid
        for key, default in self.defaults["github"].items():
            if not isinstance(result["github"].get(key, default), str):
                self._record_invalid(recovery, "github", key, result["github"][key])
                result["github"][key] = default

    def _repair_runtime(self, result: dict[str, Any], recovery: dict[str, Any]) -> None:
        for key, value in list(result["runtime"].items()):
            try:
                runtime_settings({"runtime": {key: value}})
            except ValueError:
                self._record_invalid(recovery, "runtime", key, value)
                result["runtime"].pop(key)

    @staticmethod
    def _record_invalid(recovery: dict[str, Any], group: str, key: str, value: Any) -> None:
        if not isinstance(recovery.get(group, {}), dict):
            recovery[f"original_{group}"] = recovery[group]
            recovery[group] = {}
        recovery.setdefault(group, {})[key] = value

    def _repair_subagents(self, result: dict[str, Any], recovery: dict[str, Any]) -> None:
        from ..constants import DEFAULT_SUBAGENTS
        defaults = {entry["name"]: entry for entry in DEFAULT_SUBAGENTS}
        raw = result.get("sub_agents", [])
        if not isinstance(raw, list):
            recovery["sub_agents"] = raw
            raw = []
        valid = []
        seen = set()
        invalid = []
        for entry in raw:
            if not isinstance(entry, dict) or not all(isinstance(entry.get(k), str) for k in ("name", "prompt")):
                invalid.append(entry)
                continue
            if not entry["name"].strip() or entry["name"] in seen:
                invalid.append(entry)
                continue
            seen.add(entry["name"])
            entry = copy.deepcopy(entry)
            default = defaults.get(entry["name"])
            entry["customized"] = not default or entry["prompt"] != default["prompt"] or bool(entry.get("customized"))
            valid.append(entry)
        if invalid:
            recovery["invalid_sub_agents"] = invalid
        for name, entry in defaults.items():
            if name not in seen:
                valid.append({**copy.deepcopy(entry), "customized": False})
        result["sub_agents"] = valid

    def _preserve_original(self) -> None:
        if not self.CONFIG_FILE.exists():
            return
        content = self.CONFIG_FILE.read_bytes()
        try:
            parsed = json.loads(content)
            if isinstance(parsed, dict) and self._upgrade_stale_data(parsed) == parsed:
                return
        except (ValueError, UnicodeError):
            pass
        backup = self.MYTHIC_DIR / f"config.recovery.{uuid.uuid4().hex}.bak"
        atomic_private_write(backup, content)

    def save_config(self, config: Dict[str, Any]) -> bool:
        """Explicit save; failures leave the original file intact/recoverable."""
        try:
            if not isinstance(config, dict):
                raise ValueError("Configuration root must be an object")
            normalized = self._upgrade_stale_data(config)
            protect_logging(SecretRedactor(normalized))
            json.dumps(normalized, allow_nan=False)  # Validate before touching any file.
            self.MYTHIC_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
            timeout = runtime_settings(normalized)["edit_lock_timeout"]
            with FileLock(str(self.CONFIG_FILE.with_suffix(".lock")), timeout=timeout):
                if self.CONFIG_FILE.is_symlink():
                    raise ValueError("Refusing to replace a symlink configuration file")
                self._preserve_original()
                atomic_private_json(self.CONFIG_FILE, normalized)
            return True
        except Exception as exc:
            logger.error("Settings save failed: %s", type(exc).__name__)
            publish_sync("ui_notification", title="Config Error",
                         message="Settings could not be saved; previous settings were preserved.", severity="error")
            return False


config_manager = ConfigManager()
