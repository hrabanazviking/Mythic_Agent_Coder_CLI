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
        height: 8;
        border: solid $accent;
    }
    #user-data-input {
        height: 6;
        border: solid $accent;
    }
    #global-rules-input {
        height: 6;
        border: solid yellow;
    }
    #subagents-header {
        height: 3;
        margin-top: 1;
        margin-bottom: 1;
    }
    #subagents-label {
        width: 1fr;
        content-align: left middle;
    }
    #subagent-select {
        margin-bottom: 1;
    }
    #subagent-editor {
        border: heavy $primary;
        padding: 1;
        margin-bottom: 1;
    }
    #active-subagent-name {
        margin-bottom: 1;
    }
    #active-subagent-prompt {
        height: 6;
    }
    #subagent-buttons {
        height: 3;
        margin-bottom: 1;
    }
    #global-rules-label {
    }
    #global-rules-input {
        height: 6;
        border: solid yellow;
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
            
            yield Label("9. Summon Shield-Maidens & Warriors (Sub-Agents):", classes="step")
            
            with Horizontal(id="subagents-header"):
                yield Select([], id="subagent-select", prompt="Select a Warrior to Edit")
                yield Button("+ Create New Warrior", id="create-subagent-btn", variant="success")
                
            with Vertical(id="subagent-editor"):
                yield Input(id="active-subagent-name", placeholder="Warrior Name")
                with Horizontal(id="subagent-buttons"):
                    yield Button("Reset to Default", id="reset-active-subagent-btn", variant="primary")
                    yield Button("Delete Warrior", id="delete-active-subagent-btn", variant="error")
                yield TextArea(id="active-subagent-prompt", classes="step")
            
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
        if not sub_agents:
            self.current_subagents = copy.deepcopy(DEFAULT_SUBAGENTS)
        else:
            self.current_subagents = copy.deepcopy(sub_agents)
            
        self.update_subagent_dropdown()
            
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
            elif event.button.id == "create-subagent-btn":
                new_idx = len(self.current_subagents)
                self.current_subagents.append({"name": "New Warrior", "prompt": "You are a helpful warrior."})
                self.update_subagent_dropdown(new_idx)
            elif event.button.id == "reset-active-subagent-btn":
                self.reset_active_subagent()
            elif event.button.id == "delete-active-subagent-btn":
                self.delete_active_subagent()
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

    def update_subagent_dropdown(self, select_index: int | None = None) -> None:
        try:
            if not getattr(self, 'current_subagents', None):
                self.current_subagents = copy.deepcopy(DEFAULT_SUBAGENTS)
            select = self.query_one("#subagent-select", Select)
            options = [(sa["name"], i) for i, sa in enumerate(self.current_subagents)]
            
            self._loading_subagent = True
            select.set_options(options)
            if select_index is not None:
                select.value = select_index
            elif options:
                select.value = 0
            self._loading_subagent = False
            
            if select_index is not None:
                self.load_subagent(select_index)
            elif options:
                self.load_subagent(0)
        except Exception as e:
            self._loading_subagent = False
            self.app.notify(f"Error updating dropdown: {str(e)}", severity="error", timeout=5)

    def on_select_changed(self, event: Select.Changed) -> None:
        if getattr(self, '_loading_subagent', False):
            return
        try:
            val = event.value
            if event.select.id == "subagent-select" and val is not None and str(val) != "Select.BLANK":
                if hasattr(val, "value"):  # Handle textual version differences
                    val = val.value
                try:
                    idx = int(val)
                    self.load_subagent(idx)
                except ValueError:
                    pass
        except Exception as e:
            self.app.notify(f"Error handling selection: {str(e)}", severity="error", timeout=5)

    def load_subagent(self, index: int) -> None:
        try:
            if not getattr(self, 'current_subagents', None) or index < 0 or index >= len(self.current_subagents):
                return
            self.active_subagent_index = index
            sub_agent = self.current_subagents[index]
            
            self._loading_subagent = True
            self.query_one("#active-subagent-name", Input).value = sub_agent["name"]
            self.query_one("#active-subagent-prompt", TextArea).text = sub_agent["prompt"]
            self._loading_subagent = False
        except Exception as e:
            self._loading_subagent = False
            self.app.notify(f"Error loading subagent: {str(e)}", severity="error", timeout=5)

    def on_input_changed(self, event: Input.Changed) -> None:
        if getattr(self, '_loading_subagent', False):
            return
        try:
            if event.input.id == "active-subagent-name" and hasattr(self, 'active_subagent_index'):
                self.current_subagents[self.active_subagent_index]["name"] = event.value
        except Exception as e:
            self.app.notify(f"Error handling input: {str(e)}", severity="error", timeout=5)

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        if getattr(self, '_loading_subagent', False):
            return
        try:
            if event.text_area.id == "active-subagent-prompt" and hasattr(self, 'active_subagent_index'):
                self.current_subagents[self.active_subagent_index]["prompt"] = event.text_area.text
        except Exception as e:
            self.app.notify(f"Error handling text area: {str(e)}", severity="error", timeout=5)

    def reset_active_subagent(self) -> None:
        try:
            idx = getattr(self, 'active_subagent_index', 0)
            if not getattr(self, 'current_subagents', None) or idx >= len(self.current_subagents):
                return
            default = next((sa for sa in DEFAULT_SUBAGENTS if sa["name"] == self.current_subagents[idx]["name"]), {"name": "New Warrior", "prompt": "You are a helpful warrior."})
            self.current_subagents[idx] = copy.deepcopy(default)
            self.load_subagent(idx)
        except Exception as e:
            self.app.notify(f"Error resetting subagent: {str(e)}", severity="error", timeout=5)

    def delete_active_subagent(self) -> None:
        try:
            if getattr(self, 'current_subagents', None) and len(self.current_subagents) > 1:
                idx = getattr(self, 'active_subagent_index', 0)
                if idx < len(self.current_subagents):
                    del self.current_subagents[idx]
                    self.update_subagent_dropdown(0)
        except Exception as e:
            self.app.notify(f"Error deleting subagent: {str(e)}", severity="error", timeout=5)

    def handle_save(self) -> None:
        try:
            # Sync active editor to memory
            if hasattr(self, 'active_subagent_index'):
                self.current_subagents[self.active_subagent_index]["name"] = self.query_one("#active-subagent-name", Input).value.strip()
                self.current_subagents[self.active_subagent_index]["prompt"] = self.query_one("#active-subagent-prompt", TextArea).text.strip()
                
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
            valid_sub_agents = []
            for sa in self.current_subagents:
                if sa.get("name") and sa.get("prompt"):
                    valid_sub_agents.append(sa)
            config["sub_agents"] = valid_sub_agents
                
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

