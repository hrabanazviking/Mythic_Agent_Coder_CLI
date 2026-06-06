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


PROVIDERS = [
    ("OpenRouter (Global)", "https://openrouter.ai/api/v1"),
    ("OpenAI (US)", "https://api.openai.com/v1"),
    ("Mistral AI (French)", "https://api.mistral.ai/v1"),
    ("DeepSeek (Chinese)", "https://api.deepseek.com/v1"),
    ("DashScope / Qwen (Chinese)", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
    ("Zhipu AI (Chinese)", "https://open.bigmodel.cn/api/paas/v4/"),
    ("Moonshot AI (Chinese)", "https://api.moonshot.cn/v1"),
    ("SiliconFlow (Chinese)", "https://api.siliconflow.cn/v1"),
    ("DeepInfra", "https://api.deepinfra.com/v1/openai"),
    ("Groq", "https://api.groq.com/openai/v1"),
    ("Together AI", "https://api.together.xyz/v1"),
    ("Fireworks AI", "https://api.fireworks.ai/inference/v1"),
    ("AnyScale", "https://api.endpoints.anyscale.com/v1"),
    ("OpenCode Go", "https://opencode.ai/zen/go/v1"),
]
def run_tui():
    agent = Agent(project_root=Path.cwd())
    app = MythicTUI(agent)
    app.run()

PROVIDERS = [
    ('OpenRouter (Global)', 'https://openrouter.ai/api/v1'),
    ('OpenAI (US)', 'https://api.openai.com/v1'),
    ('Mistral AI (French)', 'https://api.mistral.ai/v1'),
    ('DeepSeek (Chinese)', 'https://api.deepseek.com/v1'),
    ('DashScope / Qwen (Chinese)', 'https://dashscope.aliyuncs.com/compatible-mode/v1'),
    ('Zhipu AI (Chinese)', 'https://open.bigmodel.cn/api/paas/v4/'),
    ('Moonshot AI (Chinese)', 'https://api.moonshot.cn/v1'),
    ('SiliconFlow (Chinese)', 'https://api.siliconflow.cn/v1'),
    ('DeepInfra', 'https://api.deepinfra.com/v1/openai'),
    ('Groq', 'https://api.groq.com/openai/v1'),
    ('Together AI', 'https://api.together.xyz/v1'),
    ('Fireworks AI', 'https://api.fireworks.ai/inference/v1'),
    ('AnyScale', 'https://api.endpoints.anyscale.com/v1'),
    ('OpenCode Go', 'https://opencode.ai/zen/go/v1'),
]



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
        agent = self.app.agent
        base_url = agent.config.get("base_url")
        api_key = agent.get_api_key(base_url)
        
        if api_key and agent.config.get("model"):
            self.app.switch_screen("main_chat")
        else:
            self.app.switch_screen("setup_wizard")

