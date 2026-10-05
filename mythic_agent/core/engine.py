import logging
import os
import sys
import traceback
import platform
from datetime import datetime
from pathlib import Path

from .config_manager import config_manager
from .secure_api import publish_sync
from .redaction import SecretRedactor, protect_logging
from .storage import atomic_private_write

class MythicEngine:
    """
    Central bootstrap engine for Mythic Agent.
    Ensures safe initialization order and catches unhandled exceptions.
    """
    def __init__(self):
        self._setup_logging()
        self.config = None
        self.primary_agent = None
        
    def _setup_logging(self):
        """Sets up robust cross-platform logging."""
        log_file = config_manager.MYTHIC_DIR / "agent.log"
        try:
            descriptor = os.open(log_file, os.O_CREAT | os.O_APPEND | os.O_WRONLY, 0o600)
            os.close(descriptor)
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

    def initialize(self, workspace=None, model=None, base_url=None, resume=None, permission=None):
        """Initializes configuration and internal APIs."""
        logging.info("Loading configuration...")
        self.config = config_manager.load_config()
        for key, value in (("model", model), ("base_url", base_url)):
            if value:
                self.config[key] = value
        protect_logging(SecretRedactor(self.config))
        
        # Initialize Primary Agent and subscribe to events
        from mythic_agent.agents.llm import Agent, AGENT_REGISTRY, agent_manager
        from mythic_agent.agents.command_handler import command_handler # Ensure it's imported to subscribe
        import threading
        
        primary_agent = Agent(project_root=workspace, name="Primary", config=self.config)
        primary_agent._permission_override = permission
        self.primary_agent = primary_agent
        primary_agent.attach_session(resume=resume)
        AGENT_REGISTRY["Primary"] = primary_agent
        
        # Start the inbox processing thread for the Primary agent
        t = threading.Thread(target=agent_manager._run_agent_loop, args=(primary_agent,), daemon=True)
        t.start()
        
        logging.info("Engine initialization complete.")

    def close(self):
        if self.primary_agent:
            self.primary_agent.cancel()
            self.primary_agent.inbox.put(None)
            self.primary_agent.close()
            self.primary_agent = None

    def handle_crash(self, exc: Exception):
        """Thor Guardian fallback: Creates a comprehensive crash report."""
        logging.exception("Fatal error in Mythic Engine:")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        crash_file = config_manager.MYTHIC_DIR / f"mythic_crash_{timestamp}.txt"
        
        try:
            redactor = SecretRedactor(self.config or {})
            report = ("=== MYTHIC AGENT CRASH REPORT ===\n"
                      f"Date: {datetime.now().isoformat()}\nPython Version: {sys.version}\n"
                      f"Platform: {platform.platform()}\n\n=== TRACEBACK ===\n"
                      + traceback.format_exc())
            atomic_private_write(crash_file, redactor.text(report).encode("utf-8"))
            print(f"\n[!] Thor Guardian intercepted a crash. A report was saved to: {crash_file}\n")
        except Exception:
            print("\n[!] Thor Guardian intercepted a crash, but failed to write the report.")
            pass

# Singleton engine
engine = MythicEngine()
