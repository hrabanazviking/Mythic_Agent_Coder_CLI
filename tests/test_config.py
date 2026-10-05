"""Settings recovery uses isolated state and never reads live credentials."""

import copy
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import pytest

from mythic_agent.core.config_manager import ConfigManager
from mythic_agent.core.runtime import runtime_settings


def test_reads_preserve_original_bytes_unknown_data_and_custom_prompts(tmp_path):
    manager = ConfigManager(tmp_path)
    original = {"config_version": "wrong", "model": "custom-model", "future": {"setting": 42},
                "sub_agents": [{"name": "Architect", "prompt": "Keep my customized persona"}]}
    content = json.dumps(original, indent=4).encode()
    manager.CONFIG_FILE.write_bytes(content)
    config = manager.load_config()
    assert manager.CONFIG_FILE.read_bytes() == content
    assert config["model"] == "custom-model"
    assert config["config_version"] == manager.defaults["config_version"] == manager.CURRENT_CONFIG_VERSION
    assert config["future"] == original["future"]
    architect = next(a for a in config["sub_agents"] if a["name"] == "Architect")
    assert architect["prompt"] == "Keep my customized persona"
    assert architect["customized"] is True
    assert config["recovery"]["config_version"] == "wrong"
    assert not list(tmp_path.glob("*.bak"))


@pytest.mark.parametrize("content", [b"{broken", b"[]", b"null", b"123", b"\xff"])
def test_malformed_source_preserved_until_explicit_save(tmp_path, content):
    manager = ConfigManager(tmp_path)
    manager.CONFIG_FILE.write_bytes(content)
    config = manager.load_config()
    assert manager.last_load_warning
    assert manager.CONFIG_FILE.read_bytes() == content
    assert manager.save_config(config)
    backups = list(tmp_path.glob("config.recovery.*.bak"))
    assert len(backups) == 1 and backups[0].read_bytes() == content
    assert json.loads(manager.CONFIG_FILE.read_text())["model"] == manager.DEFAULT_MODEL


def test_wrong_fields_and_malformed_recovery_do_not_discard_other_settings(tmp_path):
    manager = ConfigManager(tmp_path)
    original = {"model": "custom", "base_url": [], "api_keys": {"valid": "fixture", "bad": 42},
                "github": {"token": [], "extension": "keep"}, "auto_accept_permissions": "false",
                "runtime": {"max_retries": "forever", "request_timeout": float("inf"), "extension": 12},
                "sub_agents": [None, {"name": "Custom", "prompt": "Keep"}, {"name": "Custom", "prompt": "Duplicate"}],
                "recovery": {"runtime": "old", "github": False}}
    manager.CONFIG_FILE.write_text(json.dumps(original))
    config = manager.load_config()
    assert config["model"] == "custom"
    assert config["api_keys"] == {"valid": "fixture"}
    assert config["auto_accept_permissions"] is False
    assert config["runtime"] == {"extension": 12}
    assert config["github"]["extension"] == "keep"
    assert config["recovery"]["original_runtime"] == "old"
    assert config["recovery"]["original_github"] is False
    assert len(config["recovery"]["invalid_sub_agents"]) == 2
    assert manager._upgrade_stale_data(config) == config


def test_environment_overrides_are_temporary_and_explicit_root_wins(tmp_path, monkeypatch):
    monkeypatch.setenv("MYTHIC_HOME", str(tmp_path / "ignored"))
    monkeypatch.setenv("MYTHIC_MODEL", "environment-model")
    monkeypatch.setenv("MYTHIC_BASE_URL", "http://localhost:1/v1")
    monkeypatch.setenv("MYTHIC_WORKSPACE", str(tmp_path))
    manager = ConfigManager(tmp_path / "explicit")
    assert manager.MYTHIC_DIR == (tmp_path / "explicit").resolve()
    config = manager.load_config()
    assert config["model"] == "environment-model"
    assert config["working_directory"] == str(tmp_path)
    assert not manager.CONFIG_FILE.exists()


def test_atomic_save_failure_preserves_previous_config_and_cleans_temps(tmp_path, monkeypatch):
    from mythic_agent.core import storage
    manager = ConfigManager(tmp_path)
    config = manager.load_config()
    assert manager.save_config(config)
    content = manager.CONFIG_FILE.read_bytes()
    changed = {**config, "model": "different"}
    def failure(*args):
        raise OSError("fixture replace failure")
    monkeypatch.setattr(storage.os, "replace", failure)
    assert manager.save_config(changed) is False
    assert manager.CONFIG_FILE.read_bytes() == content
    assert not list(tmp_path.glob(".mythic-state-*"))


def test_serialized_process_saves_leave_complete_valid_json(tmp_path):
    script = "from mythic_agent.core.config_manager import ConfigManager; import sys; m=ConfigManager(sys.argv[1]); c=m.load_config(); c['model']=sys.argv[2]; assert m.save_config(c)"
    def save(index):
        return subprocess.run([sys.executable, "-c", script, str(tmp_path), f"process-{index}"],
                              capture_output=True, text=True, timeout=15)
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(save, range(6)))
    assert all(result.returncode == 0 for result in results), [r.stderr for r in results]
    assert json.loads((tmp_path / "config.json").read_text())["model"].startswith("process-")
    assert not list(tmp_path.glob(".mythic-state-*"))


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission bits are not Windows ACLs")
def test_config_and_recovery_files_are_private(tmp_path):
    manager = ConfigManager(tmp_path / "state")
    manager.CONFIG_FILE.write_bytes(b"{broken")
    assert manager.save_config(manager.load_config())
    for path in [manager.CONFIG_FILE, *manager.MYTHIC_DIR.glob("*.bak")]:
        assert path.stat().st_mode & 0o777 == 0o600
    assert manager.MYTHIC_DIR.stat().st_mode & 0o777 == 0o700


@pytest.mark.parametrize("value", [float("inf"), float("nan"), -1, True])
def test_runtime_rejects_nonfinite_or_invalid_timeouts(value):
    with pytest.raises(ValueError):
        runtime_settings({"runtime": {"request_timeout": value}})


def test_future_versions_unknown_fields_and_input_objects_preserved(tmp_path):
    manager = ConfigManager(tmp_path)
    config = {"config_version": 999, "model": "custom", "unknown": {"nested": [1, 2]}}
    before = copy.deepcopy(config)
    assert manager.save_config(config)
    assert config == before
    loaded = manager.load_config()
    assert loaded["config_version"] == 999
    assert loaded["unknown"] == config["unknown"]
