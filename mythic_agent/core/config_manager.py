"""Non-mutating configuration reads and private, recoverable explicit saves."""

__all__ = [
    "Any",
    "ConfigManager",
    "Dict",
    "FileLock",
    "Path",
    "SecretRedactor",
    "atomic_private_json",
    "atomic_private_write",
    "config_manager",
    "files",
    "logger",
    "protect_logging",
    "publish_sync",
    "runtime_settings",
    "urlsplit",
]

import copy
import difflib
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


# ---------------------------------------------------------------------------
# Configuration Schema V2 (R-009)
# ---------------------------------------------------------------------------
# Canonical, human-readable description of every known top-level config key:
# its type, whether it is required, and its default. Types/defaults are
# derived from the actual ``config_defaults.yaml`` (plus ``runtime_defaults.yaml``
# for the nested ``runtime`` block); richer constraints (choices, minimums,
# URL/non-empty checks) are layered on top. ``validate_config`` checks a
# config against this schema WITHOUT mutating it; strict mode rejects unknown
# top-level keys; ``redacted_summary`` produces a logging-safe copy.
# ---------------------------------------------------------------------------

_STRICT_ENV_NAME = "MYTHIC_STRICT_CONFIG"
_STRICT_ENV_TRUE = {"1", "true", "yes", "on"}


class StrictConfigError(ValueError):
    """Raised when strict configuration mode rejects unknown top-level keys."""


def _env_requests_strict() -> bool:
    return os.environ.get(_STRICT_ENV_NAME, "").strip().lower() in _STRICT_ENV_TRUE


def _looks_like_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = urlsplit(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.hostname)
    except ValueError:
        return False


def _load_data_yaml(name: str) -> Any:
    return yaml.safe_load(files("mythic_agent.data").joinpath(name).read_text(encoding="utf-8"))


def _runtime_nested_schema() -> Dict[str, Dict[str, Any]]:
    """Nested schema for the ``runtime`` block, derived from runtime_defaults.yaml."""
    defaults = _load_data_yaml("runtime_defaults.yaml")
    int_minimums = {"max_retries": 0, "max_tool_rounds": 1, "max_tokens": 1}
    schema: Dict[str, Dict[str, Any]] = {}
    for key, default in defaults.items():
        if key in int_minimums:
            schema[key] = {"type": int, "required": False, "default": default,
                           "no_bool": True, "minimum": int_minimums[key]}
        else:
            schema[key] = {"type": (int, float), "required": False, "default": default,
                           "no_bool": True, "exclusive_minimum": 0}
    return schema


def _build_config_schema() -> Dict[str, Dict[str, Any]]:
    """Build the canonical CONFIG_SCHEMA from the real packaged defaults."""
    defaults = _load_data_yaml("config_defaults.yaml")
    required = {"config_version", "model", "base_url"}
    schema: Dict[str, Dict[str, Any]] = {}
    for key, default in defaults.items():
        schema[key] = {"type": type(default), "required": key in required,
                       "default": copy.deepcopy(default)}
    # Richer constraints layered over the YAML-derived types/defaults.
    schema["config_version"].update({"no_bool": True, "minimum": 1})
    schema["model"].update({"non_empty": True})
    schema["base_url"].update({"url": True})
    schema["api_keys"].update({"key_type": str, "value_type": str})
    schema["permission_mode"].update({"choices": ("read-only", "ask", "trusted")})
    schema["machine_permission_mode"].update({"choices": ("read-only", "ask", "trusted")})
    schema["runtime"].update({"schema": _runtime_nested_schema()})
    schema["github"].update({"schema": {
        "repo_url": {"type": str, "required": False, "default": ""},
        "token": {"type": str, "required": False, "default": ""},
    }})
    # Keys managed by the config system itself (not present in config_defaults.yaml).
    schema["sub_agents"] = {
        "type": list, "required": False, "default": [],
        "item_schema": {
            "name": {"type": str, "required": True, "default": ""},
            "prompt": {"type": str, "required": True, "default": ""},
        },
    }
    schema["recovery"] = {"type": dict, "required": False, "default": {}}
    schema["system_prompt"] = {"type": str, "required": False, "default": None}
    schema["primary_name"] = {"type": str, "required": False, "default": None}
    return schema


CONFIG_SCHEMA: Dict[str, Dict[str, Any]] = _build_config_schema()


def _describe_expected(expected: Any) -> str:
    if expected is int:
        return "int"
    if expected is float:
        return "float"
    if expected is str:
        return "str"
    if expected is bool:
        return "bool"
    if expected is dict:
        return "object"
    if expected is list:
        return "array"
    if isinstance(expected, tuple):
        if set(expected) == {int, float}:
            return "number"
        return " or ".join(_describe_expected(part) for part in expected)
    return getattr(expected, "__name__", str(expected))


def _check_value(path: str, value: Any, entry: Dict[str, Any], problems: list) -> None:
    """Append dotted-path problems for one value; never mutates anything."""
    expected = entry.get("type")
    if expected is not None:
        ok = isinstance(value, expected)
        if ok and entry.get("no_bool") and isinstance(value, bool):
            ok = False
        if not ok:
            problems.append(f"{path}: expected {_describe_expected(expected)}, "
                            f"got {type(value).__name__}")
            return
    choices = entry.get("choices")
    if choices is not None and value not in choices:
        problems.append(f"{path}: expected one of {list(choices)}, got {value!r}")
    minimum = entry.get("minimum")
    if minimum is not None and isinstance(value, (int, float)) and value < minimum:
        problems.append(f"{path}: expected >= {minimum}, got {value!r}")
    exclusive_minimum = entry.get("exclusive_minimum")
    if (exclusive_minimum is not None and isinstance(value, (int, float))
            and value <= exclusive_minimum):
        problems.append(f"{path}: expected > {exclusive_minimum}, got {value!r}")
    if entry.get("non_empty") and isinstance(value, str) and not value.strip():
        problems.append(f"{path}: must not be empty")
    if entry.get("url") and not _looks_like_url(value):
        problems.append(f"{path}: expected a valid http(s) URL, got {value!r}")
    nested = entry.get("schema")
    if nested is not None and isinstance(value, dict):
        for sub_key, sub_entry in nested.items():
            sub_path = f"{path}.{sub_key}"
            if sub_key not in value:
                if sub_entry.get("required"):
                    problems.append(f"{sub_path}: missing required key")
                continue
            _check_value(sub_path, value[sub_key], sub_entry, problems)
    value_type = entry.get("value_type")
    key_type = entry.get("key_type")
    if (value_type is not None or key_type is not None) and isinstance(value, dict):
        for item_key, item_value in value.items():
            item_path = f"{path}.{item_key}" if isinstance(item_key, str) else f"{path}[{item_key!r}]"
            if key_type is not None and not isinstance(item_key, key_type):
                problems.append(f"{item_path}: expected key {_describe_expected(key_type)}, "
                                f"got {type(item_key).__name__}")
            if value_type is not None:
                ok = isinstance(item_value, value_type)
                if ok and value_type is int and isinstance(item_value, bool):
                    ok = False
                if not ok:
                    problems.append(f"{item_path}: expected {_describe_expected(value_type)}, "
                                    f"got {type(item_value).__name__}")
    item_schema = entry.get("item_schema")
    if item_schema is not None and isinstance(value, list):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]"
            if not isinstance(item, dict):
                problems.append(f"{item_path}: expected object, got {type(item).__name__}")
                continue
            for sub_key, sub_entry in item_schema.items():
                sub_path = f"{item_path}.{sub_key}"
                if sub_key not in item:
                    if sub_entry.get("required"):
                        problems.append(f"{sub_path}: missing required key")
                    continue
                _check_value(sub_path, item[sub_key], sub_entry, problems)


def validate_config(config: Dict[str, Any]) -> list:
    """Return human-readable dotted-path problems for ``config``.

    Read-only: the input is never mutated. Unknown keys are intentionally NOT
    reported here (unknown-key policy belongs to strict mode).
    """
    problems: list = []
    if not isinstance(config, dict):
        return [f"config: expected object, got {type(config).__name__}"]
    for key, entry in CONFIG_SCHEMA.items():
        if key not in config:
            if entry.get("required"):
                problems.append(f"{key}: missing required key")
            continue
        _check_value(key, config[key], entry, problems)
    return problems


def _strict_unknown_messages(config: Dict[str, Any]) -> list:
    """Build one error message per unknown top-level key, with 'did you mean' hints."""
    messages: list = []
    known = list(CONFIG_SCHEMA)
    for key in config:
        if key in CONFIG_SCHEMA:
            continue
        hint = difflib.get_close_matches(key, known, n=1, cutoff=0.6)
        message = f"unknown configuration key '{key}' at '{key}'"
        if hint:
            message += f" (did you mean '{hint[0]}'?)"
        messages.append(message)
    return messages


def redacted_summary(config: Dict[str, Any]) -> Dict[str, Any]:
    """Return a logging-safe copy of ``config`` using SecretRedactor semantics.

    Secrets are replaced with ``[REDACTED]`` while the overall structure is
    kept intact. The input is never mutated.
    """
    source = config if isinstance(config, dict) else {}
    return SecretRedactor(copy.deepcopy(source)).sanitize(copy.deepcopy(source))


class ConfigManager:
    def __init__(self, root: Path | str | None = None, strict: bool = False):
        self.strict = bool(strict) or _env_requests_strict()
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
        self._enforce_strict_keys(raw)
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

    def _enforce_strict_keys(self, config: Any) -> None:
        """Raise StrictConfigError on unknown top-level keys when strict mode is on."""
        if not self.strict or not isinstance(config, dict):
            return
        messages = _strict_unknown_messages(config)
        if messages:
            raise StrictConfigError("; ".join(messages))

    def save_config(self, config: Dict[str, Any]) -> bool:
        """Explicit save; failures leave the original file intact/recoverable."""
        self._enforce_strict_keys(config)
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
