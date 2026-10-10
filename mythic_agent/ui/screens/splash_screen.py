
__all__ = [
    "Agent",
    "App",
    "Binding",
    "Button",
    "Center",
    "Checkbox",
    "Collapsible",
    "ComposeResult",
    "DEFAULT_GLOBAL_RULES",
    "DEFAULT_PRIMARY_NAME",
    "DEFAULT_SUBAGENTS",
    "DEFAULT_SYSTEM_PROMPT",
    "Footer",
    "Header",
    "Horizontal",
    "Input",
    "Label",
    "LoadingIndicator",
    "Markdown",
    "Middle",
    "ModalScreen",
    "Path",
    "RichLog",
    "Screen",
    "Select",
    "SplashScreen",
    "Static",
    "SubagentSelectionModal",
    "TextArea",
    "Vertical",
    "VerticalScroll",
    "config_manager",
    "publish_sync",
    "subscribe",
    "work",
]
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



class SplashScreen(Screen):
    """A simple splash screen with the logo."""
    
    CSS = """
    SplashScreen {
        align: center middle;
        background: $surface;
    }
    #logo {
        text-align: center;
        text-style: bold;
        color: $accent;
    }
    """
    
    def compose(self) -> ComposeResult:
        yield Static(
            "[bold cyan]"
            "███╗   ███╗██╗   ██╗████████╗██╗  ██╗██╗ ██████╗\n"
            "████╗ ████║╚██╗ ██╔╝╚══██╔══╝██║  ██║██║██╔════╝\n"
            "██╔████╔██║ ╚████╔╝    ██║   ███████║██║██║     \n"
            "██║╚██╔╝██║  ╚██╔╝     ██║   ██╔══██║██║██║     \n"
            "██║ ╚═╝ ██║   ██║      ██║   ██║  ██║██║╚██████╗\n"
            "╚═╝     ╚═╝   ╚═╝      ╚═╝   ╚═╝  ╚═╝╚═╝ ╚═════╝\n"
            "[/bold cyan]"
            "[bold yellow]"
            "               |\n"
            "              /|\\\n"
            "             / | \\\n"
            "            /  |  \\\n"
            "           /___|___\\\n"
            "               |\n"
            "       ________|________\n"
            "    /|__________________|\\_/,\n"
            "  o()o()o()o()o()o()o()o()o  >\n"
            "  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n"
            "[/bold yellow]\n"
            "[bold white]THE VIKING AI[/bold white]",
            id="logo"
        )
        yield LoadingIndicator()

    def on_mount(self) -> None:
        self.set_timer(2.0, self.finish_splash)
        
    def finish_splash(self) -> None:
        config = config_manager.load_config()
        base_url = config.get("base_url")
        api_key = config.get("api_keys", {}).get(base_url) if base_url else None
        
        if not api_key:
            import os
            if base_url and "deepseek" in base_url:
                api_key = os.environ.get("DEEPSEEK_API_KEY")
            elif base_url and "openrouter" in base_url:
                api_key = os.environ.get("OPENROUTER_API_KEY")
            elif base_url and "anthropic" in base_url:
                api_key = os.environ.get("ANTHROPIC_API_KEY")
            else:
                api_key = os.environ.get("OPENAI_API_KEY")
                
        if api_key and config.get("model"):
            self.app.switch_screen("main_chat")
        else:
            self.app.switch_screen("setup_wizard")

