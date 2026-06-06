import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from ..core.secure_api import publish_sync

logger = logging.getLogger("mythic_data_loader")

class RobustDataLoader:
    """
    Implements Thor Guardian's principle of 'Járngreipr' (Iron Gloves) for safe handling
    of potentially corrupt or varied data structures.
    """
    
    @staticmethod
    def load_json(filepath: Union[str, Path], fallback: Any = None) -> Any:
        """Safely loads JSON data."""
        path = Path(filepath)
        if not path.exists():
            logger.warning(f"File not found: {path}")
            return fallback

        try:
            content = path.read_text(encoding="utf-8").strip()
            if not content:
                logger.warning(f"File is empty: {path}")
                return fallback
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"JSON Parsing Error in {path}: {e}")
            publish_sync("ui_notification", title="Data Error", message=f"Failed to parse {path.name}.", severity="error")
            return fallback
        except Exception as e:
            logger.error(f"Unexpected error reading {path}: {e}")
            return fallback

    @staticmethod
    def load_markdown(filepath: Union[str, Path], fallback: str = "") -> str:
        """Safely loads Markdown data."""
        path = Path(filepath)
        if not path.exists():
            return fallback

        try:
            return path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Unexpected error reading Markdown {path}: {e}")
            return fallback

    @staticmethod
    def load_yaml(filepath: Union[str, Path], fallback: Any = None) -> Any:
        """Safely loads YAML data, if pyyaml is installed."""
        path = Path(filepath)
        if not path.exists():
            return fallback

        try:
            import yaml
            content = path.read_text(encoding="utf-8")
            return yaml.safe_load(content)
        except ImportError:
            logger.error("PyYAML is not installed. Cannot load YAML.")
            return fallback
        except Exception as e:
            logger.error(f"Error reading YAML {path}: {e}")
            return fallback

    @staticmethod
    def read_any(filepath: Union[str, Path]) -> Any:
        """Autodetects format and safely loads data."""
        path = Path(filepath)
        if path.suffix == ".json":
            return RobustDataLoader.load_json(path)
        elif path.suffix in [".yaml", ".yml"]:
            return RobustDataLoader.load_yaml(path)
        elif path.suffix in [".md", ".txt"]:
            return RobustDataLoader.load_markdown(path)
        else:
            # Fallback to plain text
            try:
                return path.read_text(encoding="utf-8")
            except Exception as e:
                logger.error(f"Failed to read file {path}: {e}")
                return None

# Singleton data loader instance
data_loader = RobustDataLoader()
