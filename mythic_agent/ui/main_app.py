import asyncio
from pathlib import Path
from rich.markdown import Markdown
from textual import work
from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal, Center, Middle, VerticalScroll
from textual.screen import Screen, ModalScreen
from textual.widgets import Header, Footer, Input, RichLog, Static, Select, Button, Label, LoadingIndicator, TextArea, Checkbox, Collapsible
from textual.binding import Binding
import copy
from mythic_agent.agents.llm import Agent
from mythic_agent.ui.components.subagent_modal import SubagentSelectionModal
from mythic_agent.constants import DEFAULT_GLOBAL_RULES, DEFAULT_PRIMARY_NAME, DEFAULT_SYSTEM_PROMPT, DEFAULT_SUBAGENTS

from mythic_agent.core.secure_api import publish_sync, subscribe
from mythic_agent.core.config_manager import config_manager



from .components.modals import CommandApproval, GithubConfigModal
from .screens.splash_screen import SplashScreen
from .screens.setup_screen import SetupScreen
from .screens.chat_screen import MainChatScreen


class MythicTUI(App):
    """
    The main Textual application root.
    """
    BINDINGS = [
        ("ctrl+c", "", "Copy"), # Unbind default quit so widgets can handle copy natively
        ("ctrl+q", "quit", "Quit")
    ]
    
    SCREENS = {
        "splash": SplashScreen,
        "setup_wizard": SetupScreen,
        "main_chat": MainChatScreen,
    }

    def __init__(self):
        super().__init__()
        self.active_chat_agent = "Primary"
        self.pet_active = False
        self.pet_timer = None
        self.active_subagents = []
        
        # Subscribe to UI notifications
        subscribe("ui_notification", self._handle_notification)

    def _handle_notification(self, title: str, message: str, severity: str = "info"):
        self.call_from_thread(self.notify, message, title=title, severity=severity)

    def on_mount(self) -> None:
        self.push_screen(SplashScreen())

    def action_request_approval(self, command: str, on_approve, on_reject):
        self.push_screen(CommandApproval(command, on_approve, on_reject))

    def update_token_count(self, count: int) -> None:
        try:
            from .screens.chat_screen import MainChatScreen
            if isinstance(self.screen, MainChatScreen):
                self.screen.query_one("#token-count").update(f"[dim]Tokens Used: {count}[/dim]")
        except Exception:
            pass

    def copy_to_clipboard(self, text: str) -> None:
        """Copies text to the system clipboard using Pyperclip."""
        try:
            import pyperclip
            pyperclip.copy(text)
        except Exception as e:
            self.notify(f"Clipboard error: {e}", severity="error")

    def update_agent_status(self, name: str, is_active: bool) -> None:
        try:
            if is_active:
                if name not in self.active_subagents:
                    self.active_subagents.append(name)
            else:
                if name in self.active_subagents:
                    self.active_subagents.remove(name)
                
            from .llm import AGENT_REGISTRY
            chat_screen = self.query_one(MainChatScreen)
            lbl = chat_screen.query_one("#active-agents-label", Label)
            
            active_list = []
            for aname, agent in AGENT_REGISTRY.items():
                if aname == "Primary": continue
                status_color = "green" if aname in self.active_subagents else "dim"
                active_list.append(f"[{status_color}]● {aname}[/{status_color}]")
                
            lbl.update("\n[bold yellow]⚔️ Active Warriors[/bold yellow]\n" + "\n".join(active_list))
        except Exception as e:
            import logging
            logging.exception(f"Error in update_agent_status: {e}")

    def notify_message(self, message: str, sender: str):
        try:
            chat_screen = self.query_one(MainChatScreen)
            chat_log = chat_screen.query_one("#chat-log", RichLog)
            chat_log.write(Markdown(f"**[Raven from {sender}]:**\n\n{message}"))
            chat_screen.run_agent_query(None)
        except Exception as e:
            import logging
            logging.exception(f"Error in notify_message: {e}")

