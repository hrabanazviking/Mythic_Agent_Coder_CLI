import logging
import sys
import traceback
import platform
from datetime import datetime
from pathlib import Path

from .config_manager import config_manager
from .secure_api import publish_sync

class MythicEngine:
    """
    Central bootstrap engine for Mythic Agent.
    Ensures safe initialization order and catches unhandled exceptions.
    """
    def __init__(self):
        self._setup_logging()
        self.config = None
        
    def _setup_logging(self):
        """Sets up robust cross-platform logging."""
        log_file = config_manager.MYTHIC_DIR / "agent.log"
        try:
            logging.basicConfig(
                filename=str(log_file),
                filemode="a",
                level=logging.INFO,
                format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
            )
            logging.info("Mythic Engine Initializing...")
        except Exception as e:
            # Fallback if file logging fails
            logging.basicConfig(level=logging.INFO)
            logging.error(f"Failed to setup file logging: {e}")

    def initialize(self):
        """Initializes configuration and internal APIs."""
        logging.info("Loading configuration...")
        self.config = config_manager.load_config()
        
        # Initialize Primary Agent and subscribe to events
        from mythic_agent.agents.llm import Agent, AGENT_REGISTRY, agent_manager
        from mythic_agent.agents.command_handler import command_handler # Ensure it's imported to subscribe
        import threading
        
        primary_agent = Agent(name="Primary")
        AGENT_REGISTRY["Primary"] = primary_agent
        
        # Start the inbox processing thread for the Primary agent
        t = threading.Thread(target=agent_manager._run_agent_loop, args=(primary_agent,), daemon=True)
        t.start()
        
        logging.info("Engine initialization complete.")

    def handle_crash(self, exc: Exception):
        """Thor Guardian fallback: Creates a comprehensive crash report."""
        logging.exception("Fatal error in Mythic Engine:")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        crash_file = Path.cwd() / f"mythic_crash_{timestamp}.txt"
        
        try:
            with crash_file.open("w", encoding="utf-8") as f:
                f.write("=== MYTHIC AGENT CRASH REPORT ===\n")
                f.write(f"Date: {datetime.now().isoformat()}\n")
                f.write(f"Python Version: {sys.version}\n")
                f.write(f"Platform: {platform.platform()}\n")
                f.write("\n=== TRACEBACK ===\n")
                f.write(traceback.format_exc())
            print(f"\n[!] Thor Guardian intercepted a crash. A report was saved to: {crash_file}\n")
        except Exception:
            print("\n[!] Thor Guardian intercepted a crash, but failed to write the report.")
            pass

# Singleton engine
engine = MythicEngine()
