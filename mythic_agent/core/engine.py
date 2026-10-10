
__all__ = [
    "MythicEngine",
    "Path",
    "SecretRedactor",
    "config_manager",
    "engine",
    "protect_logging",
    "publish_sync",
    "write_crash_report",
]
import logging
import os
from pathlib import Path

from .config_manager import config_manager
from .secure_api import publish_sync
from .redaction import SecretRedactor, protect_logging
from .journal import write_crash_report

class MythicEngine:
    """
    Central bootstrap engine for Mythic Agent.
    Ensures safe initialization order and catches unhandled exceptions.
    """
    def __init__(self) -> None:
        self._setup_logging()
        self.config = None
        self.primary_agent = None
        self.startup = None

    def _setup_logging(self) -> None:
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

    def initialize(self, workspace: str | Path | None = None, model: str | None = None,
                     base_url: str | None = None, resume: str | None = None,
                     permission: str | None = None) -> None:
        """Initializes configuration and internal APIs."""
        from .determinism import startup_sequence
        from .lifecycle import install_atexit, register_thread
        install_atexit()
        self.startup = startup_sequence()
        self.startup.record("logging")
        logging.info("Loading configuration...")
        self.config = config_manager.load_config()
        for key, value in (("model", model), ("base_url", base_url)):
            if value:
                self.config[key] = value
        protect_logging(SecretRedactor(self.config))
        self.startup.record("config")
        
        # Initialize Primary Agent and subscribe to events
        from mythic_agent.agents.llm import Agent, AGENT_REGISTRY, agent_manager
        from mythic_agent.agents.command_handler import command_handler # Ensure it's imported to subscribe
        import threading
        
        primary_agent = Agent(project_root=workspace, name="Primary", config=self.config)
        primary_agent._permission_override = permission
        self.primary_agent = primary_agent
        primary_agent.attach_session(resume=resume)
        AGENT_REGISTRY["Primary"] = primary_agent
        self.startup.record("agent", "Primary")

        # Crash recovery: replay any checkpoints journaled but never committed
        # by a previous process that died mid-write.
        try:
            from .recovery import recover_crashed_sessions
            recovered = recover_crashed_sessions(primary_agent, interactive=False)
            if recovered:
                logging.info("Recovered %d crashed session checkpoint(s): %s",
                             len(recovered), recovered)
        except Exception:
            logging.exception("Crash recovery check failed; continuing without recovery.")
        self.startup.record("recovery")
        
        # Start the inbox processing thread for the Primary agent
        t = threading.Thread(target=agent_manager._run_agent_loop, args=(primary_agent,),
                             name="mythic-primary-inbox", daemon=True)
        t.start()
        register_thread(t, threading.Event(), name="mythic-primary-inbox",
                        on_stop=lambda: primary_agent.inbox.put(None))
        self.startup.record("inbox_thread", "mythic-primary-inbox")
        
        logging.info("Engine initialization complete.")

    def close(self) -> None:
        if self.primary_agent:
            self.primary_agent.cancel()
            self.primary_agent.inbox.put(None)
            self.primary_agent.close()
            self.primary_agent = None

    def handle_crash(self, exc: Exception) -> None:
        """Thor Guardian fallback: writes a structured JSON crash report."""
        logging.exception("Fatal error in Mythic Engine:")

        session_id = None
        try:
            if self.primary_agent is not None:
                session_id = self.primary_agent.session_id
        except Exception:
            pass
        try:
            redactor = SecretRedactor(self.config or {})
            crash_file = write_crash_report(exc, session_id=session_id,
                                            mythic_dir=config_manager.MYTHIC_DIR,
                                            redactor=redactor)
            print(f"\n[!] Thor Guardian intercepted a crash. A report was saved to: {crash_file}\n")
        except Exception:
            print("\n[!] Thor Guardian intercepted a crash, but failed to write the report.")
            pass

# Singleton engine
engine = MythicEngine()
