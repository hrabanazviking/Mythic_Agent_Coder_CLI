import json
import shutil
import logging
from pathlib import Path
from typing import Any, Dict
from .secure_api import publish_sync

logger = logging.getLogger("mythic_config_manager")

class ConfigManager:
    """
    Secure and robust configuration manager.
    Handles cross-platform paths using pathlib.
    Implements Thor Guardian's principle of 'safe handling' for file operations.
    """
    def __init__(self):
        self.MYTHIC_DIR = Path.home() / ".mythic"
        self.CONFIG_FILE = self.MYTHIC_DIR / "config.json"
        
        self.DEFAULT_MODEL = "deepseek-chat"
        self.DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
        self.CURRENT_CONFIG_VERSION = 1
        
        # Ensure directories exist
        try:
            self.MYTHIC_DIR.mkdir(exist_ok=True, parents=True)
            (self.MYTHIC_DIR / "status").mkdir(exist_ok=True, parents=True)
        except Exception as e:
            logger.error(f"Failed to create mythic directories: {e}")

    def load_config(self) -> Dict[str, Any]:
        """Safely loads configuration with fallback mechanisms."""
        old_config = Path.home() / ".mythic_config.json"
        
        # Migration from legacy location
        if old_config.exists() and not self.CONFIG_FILE.exists():
            try:
                shutil.copy2(old_config, self.CONFIG_FILE)
            except Exception as e:
                logger.error(f"Failed to migrate old config: {e}")

        if self.CONFIG_FILE.exists():
            try:
                content = self.CONFIG_FILE.read_text(encoding="utf-8")
                config = json.loads(content)
                config = self._upgrade_stale_data(config)
                return config
            except Exception as e:
                logger.error(f"Failed to load or parse {self.CONFIG_FILE}: {e}. Falling back to default.")
                
        return {
            "model": self.DEFAULT_MODEL, 
            "base_url": self.DEFAULT_BASE_URL,
            "api_keys": {},
            "config_version": self.CURRENT_CONFIG_VERSION
        }

    def _upgrade_stale_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Self-healing function to upgrade stale or outdated cached data."""
        version = config.get("config_version", 0)
        changed = False
        
        # 1. Ensure root schema integrity
        if "api_keys" not in config or not isinstance(config["api_keys"], dict):
            config["api_keys"] = {}
            changed = True
            
        if "model" not in config or not isinstance(config["model"], str):
            config["model"] = self.DEFAULT_MODEL
            changed = True
            
        if "base_url" not in config or not isinstance(config["base_url"], str):
            config["base_url"] = self.DEFAULT_BASE_URL
            changed = True
            
        # 2. Robust Subagent validation and stale-prompt auto-healing
        from mythic_agent.constants import DEFAULT_SUBAGENTS
        import copy
        
        if "sub_agents" in config:
            subs = config["sub_agents"]
            if not isinstance(subs, list):
                config["sub_agents"] = copy.deepcopy(DEFAULT_SUBAGENTS)
                changed = True
            else:
                valid_subs = []
                for sa in subs:
                    if isinstance(sa, dict) and "name" in sa and "prompt" in sa:
                        prompt = sa.get("prompt", "")
                        name = sa.get("name", "")
                        is_customized = sa.get("customized", False)
                        
                        # Auto-heal default agents if their prompt doesn't match the latest (stale cache)
                        default_match = next((d for d in DEFAULT_SUBAGENTS if d["name"] == name), None)
                        if default_match:
                            if not is_customized and prompt != default_match["prompt"]:
                                healed = copy.deepcopy(default_match)
                                healed["customized"] = False
                                valid_subs.append(healed)
                                changed = True
                            else:
                                sa["customized"] = is_customized
                                valid_subs.append(sa)
                        else:
                            sa["customized"] = True
                            valid_subs.append(sa)
                    else:
                        changed = True  # Discard malformed subagent entries
                        
                if not valid_subs:
                    config["sub_agents"] = copy.deepcopy(DEFAULT_SUBAGENTS)
                    changed = True
                else:
                    if config["sub_agents"] != valid_subs:
                        config["sub_agents"] = valid_subs
                        changed = True
        else:
            config["sub_agents"] = copy.deepcopy(DEFAULT_SUBAGENTS)
            changed = True

        # 3. Upgrade version schema
        self.CURRENT_CONFIG_VERSION = 2
        if version < self.CURRENT_CONFIG_VERSION:
            config["config_version"] = self.CURRENT_CONFIG_VERSION
            changed = True
            
        if changed:
            self.save_config(config)
            
        return config

    def save_config(self, config: Dict[str, Any]) -> bool:
        """Safely saves configuration with 0600 permissions."""
        try:
            # Járngreipr Principle: Save to temporary file first, then replace
            temp_file = self.CONFIG_FILE.with_suffix('.tmp')
            temp_file.write_text(json.dumps(config, indent=2))
            
            # Atomic replace
            temp_file.replace(self.CONFIG_FILE)
            
            # Secure permissions
            self.CONFIG_FILE.chmod(0o600)
            logger.debug("Configuration saved securely.")
            return True
        except Exception as e:
            logger.error(f"Failed to save configuration securely: {e}")
            publish_sync("ui_notification", title="Config Error", message=f"Failed to save settings: {e}", severity="error")
            return False

# Singleton instance
config_manager = ConfigManager()
