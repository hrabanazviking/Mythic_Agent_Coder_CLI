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



class CommandApproval(ModalScreen[bool]):
    """Modal dialog to approve bash commands."""
    
    CSS = """
    CommandApproval {
        align: center middle;
        background: $background 80%;
    }
    #dialog {
        padding: 1 2;
        width: 60;
        height: auto;
        border: thick red;
        background: $surface;
    }
    """
    def __init__(self, command: str, on_approve, on_reject, **kwargs):
        super().__init__(**kwargs)
        self.command_text = command
        self.on_approve = on_approve
        self.on_reject = on_reject
        
    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("[bold red]⚠️  Security Approval Required[/bold red]\n")
            yield Label(f"The agent wants to run the following command:\n\n[bold white]{self.command_text}[/bold white]\n")
            with Horizontal():
                yield Button("Allow", id="allow", variant="success")
                yield Button("Reject", id="reject", variant="error")
                
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "allow":
            self.on_approve()
            self.dismiss(True)
        else:
            self.on_reject()
            self.dismiss(False)

class GithubConfigModal(ModalScreen[None]):
    """Modal dialog to configure GitHub settings."""
    
    CSS = """
    GithubConfigModal {
        align: center middle;
        background: $background 80%;
    }
    #gh-dialog {
        padding: 1 2;
        width: 60;
        height: auto;
        border: heavy $secondary;
        background: $surface;
    }
    .gh-step {
        margin-bottom: 1;
    }
    #gh-buttons {
        height: 3;
        margin-top: 1;
    }
    """
    
    def compose(self) -> ComposeResult:
        with Vertical(id="gh-dialog"):
            yield Label("[bold cyan]Configure GitHub[/bold cyan]", classes="gh-step")
            yield Label("GitHub Repository (e.g., owner/repo):", classes="gh-step")
            yield Input(placeholder="owner/repo", id="gh-repo-input", classes="gh-step")
            
            yield Label("GitHub Personal Access Token (PAT):", classes="gh-step")
            yield Input(password=True, placeholder="ghp_...", id="gh-token-input", classes="gh-step")
            
            with Horizontal(id="gh-buttons"):
                yield Button("Cancel", id="gh-cancel", variant="error")
                yield Button("Save Config", id="gh-save", variant="success")

    def on_mount(self) -> None:
        config = self.app.agent.config.get("github", {})
        self.query_one("#gh-repo-input", Input).value = config.get("repo_url", "")
        self.query_one("#gh-token-input", Input).value = config.get("token", "")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "gh-cancel":
            self.dismiss()
        elif event.button.id == "gh-save":
            repo = self.query_one("#gh-repo-input", Input).value.strip()
            token = self.query_one("#gh-token-input", Input).value.strip()
            
            if "github" not in self.app.agent.config:
                self.app.agent.config["github"] = {}
                
            self.app.agent.config["github"]["repo_url"] = repo
            self.app.agent.config["github"]["token"] = token
            self.app.agent.save_config()  # We need to implement save_config in Agent
            self.dismiss()

