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
from mythic_agent.ui.components.subagent_editor import SubagentEditorWidget
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



class SetupScreen(Screen):
    """Wizard to setup provider and fetch models."""
    
    CSS = """
    SetupScreen {
        align: center middle;
    }
    #setup-scroll {
        width: 80;
        height: 80%;
        border: heavy $warning;
        padding: 1 2;
        background: $surface;
    }
    .step {
        margin-bottom: 1;
    }
    #setup-buttons {
        height: 3;
        margin-top: 1;
    }
    #cancel-btn {
        margin-right: 2;
    }
    #system-prompt-input {
        min-height: 4;
        height: auto;
        border: solid $accent;
    }
    #user-data-input {
        min-height: 4;
        height: auto;
        border: solid $accent;
    }
    #global-rules-input {
        min-height: 4;
        height: auto;
        border: solid yellow;
    }

    #global-rules-label {
    }
    #primary-header {
        height: 3;
        margin-bottom: 1;
    }
    #primary-label {
        width: 1fr;
        content-align: left middle;
    }
    """

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="setup-scroll"):
            yield Label("[bold yellow]⚔️  Forge Your Viking Team ⚔️[/bold yellow]", classes="step")
            yield Label("1. Choose your Divine Source (LLM Provider):", classes="step")
            yield Select(PROVIDERS, prompt="Provider", id="provider-select")
            
            yield Label("2. Offer your Tribute (API Key):", classes="step")
            yield Input(password=True, placeholder="sk-...", id="api-key-input")
            
            yield Button("Consult the Runes (Fetch Models)", id="fetch-btn", variant="primary", classes="step")
            
            yield LoadingIndicator(id="loading", classes="step")
            yield Label("", id="error-msg", classes="step")
            
            yield Label("3. Select your Weapon (Model):", classes="step")
            yield Select([], prompt="Model", id="model-select", disabled=True)
            
            yield Label("4. The Battlefield (Working Directory):", classes="step")
            yield Input(placeholder="e.g. /home/user/projects (Leave blank to use current folder)", id="working-dir-input", classes="step")
            
            yield Label("5. Who is the User? (User Name - Optional):", classes="step")
            yield Input(placeholder="Your Name (e.g. Volmarr)", id="user-name-input", classes="step")
            
            yield Label("6. The User's Lore (User Data - Optional):", classes="step")
            yield TextArea(id="user-data-input", classes="step")
            
            with Horizontal(id="primary-header"):
                yield Label("7. The Jarl's Identity (Primary Agent Name & Prompt):", id="primary-label")
                yield Button("Reset to Default", id="reset-primary-btn", variant="primary")
            yield Input(id="primary-agent-name", placeholder="e.g. Runa Gridweaver", classes="step")
            yield TextArea(id="system-prompt-input", classes="step")
            
            with Horizontal(id="global-rules-header"):
                yield Label("8. The Elder's Laws (Global Rules applied to ALL):", id="global-rules-label")
                yield Button("Reset to Default", id="reset-rules-btn", variant="primary")
            yield TextArea(id="global-rules-input", classes="step")
            
            yield SubagentEditorWidget(id="subagent-editor-widget")

            with Horizontal(id="setup-buttons"):
                yield Button("Flee", id="cancel-btn", variant="error")
                yield Button("To Valhalla! (Save)", id="save-btn", variant="warning", disabled=True)

    def on_mount(self) -> None:
        self.query_one("#loading").display = False
        self.query_one("#error-msg").display = False
        
        config = config_manager.load_config()
        has_config = bool(config.get("model") and config.get("base_url"))
        
        if config.get("base_url"):
            provider_select = self.query_one("#provider-select", Select)
            try:
                provider_select.value = config["base_url"]
            except Exception:
                pass
                
            key = config.get("api_keys", {}).get(config["base_url"])
            if key:
                self.query_one("#api-key-input", Input).value = key
                
        if config.get("model"):
            model = config["model"]
            model_select = self.query_one("#model-select", Select)
            model_select.set_options([(model, model)])
            model_select.value = model
            model_select.disabled = False
            self.query_one("#save-btn").disabled = False
            
        wd = config.get("working_directory", "")
        self.query_one("#working-dir-input", Input).value = wd
            
        user_name = config.get("user_name", "")
        self.query_one("#user-name-input", Input).value = user_name
        
        user_data = config.get("user_data", "")
        self.query_one("#user-data-input", TextArea).text = user_data
        
        sys_prompt = config.get("system_prompt")
        if sys_prompt is not None:
            self.query_one("#system-prompt-input", TextArea).text = sys_prompt
        else:
            self.query_one("#system-prompt-input", TextArea).text = DEFAULT_SYSTEM_PROMPT
            
        primary_name = config.get("primary_agent_name", DEFAULT_PRIMARY_NAME)
        self.query_one("#primary-agent-name", Input).value = primary_name
            
        global_rules = config.get("global_rules")
        if global_rules is not None:
            self.query_one("#global-rules-input", TextArea).text = global_rules
        else:
            self.query_one("#global-rules-input", TextArea).text = DEFAULT_GLOBAL_RULES
            
        sub_agents = config.get("sub_agents", [])
        self.query_one("#subagent-editor-widget").set_subagents(sub_agents)
            
        cancel_btn = self.query_one("#cancel-btn", Button)
        if not has_config:
            cancel_btn.disabled = True

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        try:
            if event.button.id == "fetch-btn":
                await self.handle_fetch()
            elif event.button.id == "save-btn":
                self.handle_save()
            elif event.button.id == "cancel-btn":
                self.app.switch_screen("main_chat")
            elif event.button.id == "reset-rules-btn":
                self.query_one("#global-rules-input", TextArea).text = DEFAULT_GLOBAL_RULES
            elif event.button.id == "reset-primary-btn":
                self.query_one("#primary-agent-name", Input).value = DEFAULT_PRIMARY_NAME
                self.query_one("#system-prompt-input", TextArea).text = DEFAULT_SYSTEM_PROMPT
        except Exception as e:
            self.app.notify(f"Error handling button press: {str(e)}", severity="error", timeout=5)
            
    async def handle_fetch(self) -> None:
        try:
            provider_url = self.query_one("#provider-select", Select).value
            api_key = self.query_one("#api-key-input", Input).value
            error_msg = self.query_one("#error-msg", Label)
            
            if not provider_url or not api_key:
                error_msg.update("[red]Please select a provider and enter an API key.[/red]")
                error_msg.display = True
                return
                
            error_msg.display = False
            self.query_one("#loading").display = True
            self.query_one("#fetch-btn").disabled = True
            
            self.fetch_models_bg(provider_url, api_key)
        except Exception as e:
            self.query_one("#loading").display = False
            if self.query_one("#fetch-btn"):
                self.query_one("#fetch-btn").disabled = False
            self.app.notify(f"Error preparing fetch: {str(e)}", severity="error", timeout=5)
        
    @work(exclusive=True, thread=True)
    def fetch_models_bg(self, base_url: str, api_key: str) -> None:
        try:
            from mythic_agent.agents.llm import Agent
            models = Agent().fetch_models(base_url, api_key)
            self.app.call_from_thread(self.on_fetch_success, models)
        except Exception as e:
            self.app.call_from_thread(self.on_fetch_error, str(e))
            
    def on_fetch_success(self, models: list[str]) -> None:
        self.query_one("#loading").display = False
        self.query_one("#fetch-btn").disabled = False
        
        model_select = self.query_one("#model-select", Select)
        options = [(m, m) for m in models]
        model_select.set_options(options)
        model_select.disabled = False
        self.query_one("#save-btn").disabled = False
        
    def on_fetch_error(self, error: str) -> None:
        self.query_one("#loading").display = False
        self.query_one("#fetch-btn").disabled = False
        error_msg = self.query_one("#error-msg", Label)
        error_msg.update(f"[red]{error}[/red]")
        error_msg.display = True

    def handle_save(self) -> None:
        try:
            base_url = self.query_one("#provider-select", Select).value
            api_key = self.query_one("#api-key-input", Input).value
            model_select = self.query_one("#model-select", Select)
            model = model_select.value
            sys_prompt = self.query_one("#system-prompt-input", TextArea).text
            primary_name = self.query_one("#primary-agent-name", Input).value.strip() or "Mythic"
            global_rules = self.query_one("#global-rules-input", TextArea).text
            working_dir = self.query_one("#working-dir-input", Input).value.strip()
            user_name = self.query_one("#user-name-input", Input).value.strip()
            user_data = self.query_one("#user-data-input", TextArea).text.strip()
            
            if not model or str(model) == "Select.BLANK":
                error_msg = self.query_one("#error-msg", Label)
                error_msg.update("[red]Please explicitly select a model from the dropdown first.[/red]")
                error_msg.display = True
                return
                
            model = str(model)
            
            config = config_manager.load_config()
            
            # Save current state of subagents
            config["sub_agents"] = self.query_one("#subagent-editor-widget").get_subagents()
                
            config["primary_agent_name"] = primary_name
            config["system_prompt"] = sys_prompt
            config["global_rules"] = global_rules
            config["working_directory"] = working_dir
            config["user_name"] = user_name
            config["user_data"] = user_data
            
            config["model"] = model
            config["base_url"] = str(base_url)
            if "api_keys" not in config:
                config["api_keys"] = {}
            if api_key:
                config["api_keys"][str(base_url)] = str(api_key)
                
            config_manager.save_config(config)
            
            # Update the Primary Agent with the new config at runtime
            from mythic_agent.agents.llm import AGENT_REGISTRY
            if "Primary" in AGENT_REGISTRY:
                AGENT_REGISTRY["Primary"].config = config
                if working_dir:
                    from pathlib import Path
                    AGENT_REGISTRY["Primary"].project_root = Path(working_dir).expanduser().resolve()
            
            self.app.switch_screen("main_chat")
        except Exception as e:
            self.app.notify(f"Error saving configuration: {str(e)}", severity="error", timeout=5)

