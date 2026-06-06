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
                return json.loads(content)
            except Exception as e:
                logger.error(f"Failed to load or parse {self.CONFIG_FILE}: {e}. Falling back to default.")
                
        return {
            "model": self.DEFAULT_MODEL, 
            "base_url": self.DEFAULT_BASE_URL,
            "api_keys": {}
        }

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
