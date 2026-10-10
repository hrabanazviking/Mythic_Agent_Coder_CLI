"""Configuration Schema V2: canonical schema, strict mode, validation, redaction."""

import copy
import json
from importlib.resources import files

import pytest
import yaml

from mythic_agent.core.config_manager import (
    CONFIG_SCHEMA,
    ConfigManager,
    StrictConfigError,
    redacted_summary,
    validate_config,
)


def _load_defaults():
    return yaml.safe_load(files("mythic_agent.data").joinpath(
        "config_defaults.yaml").read_text(encoding="utf-8"))


def test_schema_covers_every_config_defaults_key_with_no_drift():
    defaults = _load_defaults()
    missing = [key for key in defaults if key not in CONFIG_SCHEMA]
    assert not missing, f"schema is missing keys from config_defaults.yaml: {missing}"
    for key, default in defaults.items():
        entry = CONFIG_SCHEMA[key]
        assert "type" in entry and "required" in entry and "default" in entry
        assert entry["default"] == default, f"schema default drifted for {key}"
        expected = entry["type"]
        assert isinstance(default, expected), f"schema type mismatch for {key}"


def test_schema_covers_runtime_defaults_keys():
    runtime_defaults = yaml.safe_load(files("mythic_agent.data").joinpath(
        "runtime_defaults.yaml").read_text(encoding="utf-8"))
    nested = CONFIG_SCHEMA["runtime"]["schema"]
    missing = [key for key in runtime_defaults if key not in nested]
    assert not missing, f"runtime schema missing keys: {missing}"


def test_strict_mode_rejects_unknown_key_with_dotted_path_and_suggestion(tmp_path, monkeypatch):
    monkeypatch.delenv("MYTHIC_STRICT_CONFIG", raising=False)
    manager = ConfigManager(tmp_path, strict=True)
    manager.CONFIG_FILE.write_text(json.dumps({"model": "x", "modle": "typo"}))
    with pytest.raises(StrictConfigError) as exc_info:
        manager.load_config()
    message = str(exc_info.value)
    assert "modle" in message
    assert "model" in message  # the "did you mean" hint
    assert "did you mean" in message


def test_strict_mode_can_come_from_environment(tmp_path, monkeypatch):
    monkeypatch.delenv("MYTHIC_STRICT_CONFIG", raising=False)
    assert ConfigManager(tmp_path / "plain").strict is False
    monkeypatch.setenv("MYTHIC_STRICT_CONFIG", "1")
    assert ConfigManager(tmp_path / "env").strict is True


def test_strict_mode_rejects_unknown_key_on_save(tmp_path, monkeypatch):
    monkeypatch.delenv("MYTHIC_STRICT_CONFIG", raising=False)
    manager = ConfigManager(tmp_path, strict=True)
    with pytest.raises(StrictConfigError):
        manager.save_config({"model": "x", "weird_typo_key": 1})


def test_non_strict_preserves_unknown_keys(tmp_path, monkeypatch):
    monkeypatch.delenv("MYTHIC_STRICT_CONFIG", raising=False)
    manager = ConfigManager(tmp_path)
    original = {"model": "custom", "custom_persona": {"voice": "whispery"}, "future_setting": 42}
    manager.CONFIG_FILE.write_text(json.dumps(original))
    config = manager.load_config()
    assert config["custom_persona"] == {"voice": "whispery"}
    assert config["future_setting"] == 42


def test_validate_config_finds_type_mismatches_with_dotted_paths():
    config = {
        "config_version": 3,
        "model": 123,
        "base_url": "https://example.com",
        "runtime": {"edit_lock_timeout": "soon", "max_retries": 2.5},
    }
    problems = validate_config(config)
    assert any(p.startswith("model:") and "expected str" in p and "got int" in p for p in problems), problems
    assert any(p.startswith("runtime.edit_lock_timeout:") and "expected number" in p
               and "got str" in p for p in problems), problems
    assert any(p.startswith("runtime.max_retries:") and "expected int" in p
               and "got float" in p for p in problems), problems


def test_validate_config_rejects_bool_for_int_and_bad_enum():
    problems = validate_config({
        "config_version": True,
        "model": "x",
        "base_url": "https://example.com",
        "permission_mode": "sometimes",
    })
    assert any(p.startswith("config_version:") and "expected int" in p for p in problems), problems
    assert any(p.startswith("permission_mode:") and "read-only" in p for p in problems), problems


def test_validate_config_reports_missing_required_keys():
    problems = validate_config({})
    paths = [p.split(":")[0] for p in problems]
    assert "config_version" in paths and "model" in paths and "base_url" in paths


def test_validate_config_does_not_mutate_input():
    config = {"config_version": 3, "model": 123, "base_url": "https://example.com",
              "runtime": {"edit_lock_timeout": "soon"}, "api_keys": {"k": 42}}
    before = copy.deepcopy(config)
    validate_config(config)
    assert config == before


def test_validate_config_clean_config_has_no_problems():
    manager = ConfigManager.__new__(ConfigManager)  # avoid touching the filesystem
    config = copy.deepcopy(_load_defaults())
    assert validate_config(config) == []


def test_malformed_json_still_loads_with_last_load_warning(tmp_path, monkeypatch):
    monkeypatch.delenv("MYTHIC_STRICT_CONFIG", raising=False)
    manager = ConfigManager(tmp_path)
    manager.CONFIG_FILE.write_bytes(b"{broken")
    config = manager.load_config()
    assert manager.last_load_warning
    assert config["model"] == manager.DEFAULT_MODEL
    assert config["config_version"] == manager.CURRENT_CONFIG_VERSION


def test_redacted_summary_never_contains_real_secret_values():
    fake_api_key = "sk-test-fake-12345"
    fake_token = "ghp-test-fake-99999"
    config = {
        "model": "deepseek-chat",
        "api_keys": {"openai": fake_api_key},
        "github": {"repo_url": "", "token": fake_token},
        "runtime": {"edit_lock_timeout": 20.0},
    }
    summary = redacted_summary(config)
    blob = json.dumps(summary)
    assert fake_api_key not in blob
    assert fake_token not in blob
    # Structure is kept, only secrets replaced.
    assert set(summary) == set(config)
    assert summary["api_keys"]["openai"] == "[REDACTED]"
    assert summary["github"]["token"] == "[REDACTED]"
    assert summary["model"] == "deepseek-chat"
    assert summary["runtime"] == {"edit_lock_timeout": 20.0}
    # Input untouched.
    assert config["api_keys"]["openai"] == fake_api_key


def test_redacted_summary_handles_non_dict_safely():
    assert redacted_summary({}) == {}
