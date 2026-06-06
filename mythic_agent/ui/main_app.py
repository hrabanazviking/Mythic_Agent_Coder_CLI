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


from .components.modals import CommandApproval, GithubConfigModal
from .screens.splash_screen import SplashScreen
from .screens.setup_screen import SetupScreen
from .screens.chat_screen import MainChatScreen


class MythicTUI(App):
    """The main Textual application."""
    
    SCREENS = {
        "splash": SplashScreen,
        "setup_wizard": SetupScreen,
        "main_chat": MainChatScreen,
    }

    def __init__(self, agent: Agent):
        super().__init__()
        self.agent = agent
        self.active_subagents = set()
        self.active_chat_agent = "Primary"
        self.agent.tui_app = self  # Give agent access to TUI for prompting

    def on_mount(self) -> None:
        self.title = "Mythic Agent"
        self.theme = "tokyo-night"
        self.push_screen("splash")

    def action_request_approval(self, command: str, on_approve, on_reject):
        self.push_screen(CommandApproval(command, on_approve, on_reject))

    def update_token_count(self, count: int) -> None:
        try:
            chat_screen = self.query_one(MainChatScreen)
            lbl = chat_screen.query_one("#token-count", Label)
            lbl.update(f"[dim]Tokens Used: {count}[/dim]")
        except Exception as e:
            import logging
            logging.exception(f"Error in update_token_count: {e}")

    def update_agent_status(self, name: str, is_active: bool) -> None:
        try:
            if is_active:
                self.active_subagents.add(name)
            else:
                self.active_subagents.discard(name)
                
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

