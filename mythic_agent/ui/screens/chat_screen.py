import asyncio
import os
from pathlib import Path
from rich.markdown import Markdown
from textual import work
from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal, Center, Middle, VerticalScroll
from textual.screen import Screen, ModalScreen
from textual.widgets import Header, Footer, Input, RichLog, Static, Select, Button, Label, LoadingIndicator, TextArea, Checkbox, Collapsible
from textual.binding import Binding
import copy

from mythic_agent.ui.components.subagent_modal import SubagentSelectionModal
from mythic_agent.constants import DEFAULT_GLOBAL_RULES, DEFAULT_PRIMARY_NAME, DEFAULT_SYSTEM_PROMPT, DEFAULT_SUBAGENTS
import random

try:
    from PIL import Image
    def get_flattened_data(self):
        return self.getdata()
    if not hasattr(Image.Image, "get_flattened_data"):
        Image.Image.get_flattened_data = get_flattened_data
        
    from textual_image.widget import Image as TextualImage
    HAS_IMAGE_WIDGET = True
except Exception as e:
    import logging
    logging.error(f"Failed to load textual_image: {e}")
    HAS_IMAGE_WIDGET = False

from textual import events
from textual.containers import Vertical

class AspectRatioContainer(Vertical):
    def on_resize(self, event: events.Resize) -> None:
        # Character terminals are inherently ~2:1 vertical rectangles.
        # To render a 1:1 square image proportionally, height in lines should be width / 2.
        self.styles.height = max(1, event.size.width // 2)

from mythic_agent.core.secure_api import publish_sync, subscribe, SecureAPI
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
    from mythic_agent.ui.main_app import MythicTUI
    app = MythicTUI()
    app.run()


class MainChatScreen(Screen):
    """The main chat interface."""
    
    CSS = """
    #main-layout {
        height: 1fr;
    }
    #chat-container {
        width: 1fr;
        height: 1fr;
        border: heavy $warning;
        margin: 1;
    }
    #sidebar {
        width: 35;
        dock: right;
        border-left: solid green;
        background: $surface;
        padding: 1;
    }
    #chat-log {
        height: 1fr;
        background: $boost;
    }
    #chat-input-container {
        height: 3;
        margin: 1;
        border: tall $secondary;
    }
    #chat-input {
        width: 1fr;
        border: none;
    }
    #loading-indicator {
        height: 1;
        dock: bottom;
    }
    #model-status-btn {
        width: 100%;
        height: 1;
        border: none;
        background: $panel;
        color: $text;
        content-align: center middle;
    }
    #model-status-btn:hover {
        background: $accent;
        color: $text;
    }
    #footer-container {
        dock: bottom;
        height: 1;
        width: 100%;
        background: $primary-background;
    }
    Footer {
        width: 1fr;
    }
    #footer-agents-status {
        width: auto;
        color: yellow;
    }
    #agent-image-container {
        width: 100%;
    }
    #agent-image {
        width: 100%;
        height: 100%;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("f2", "setup", "Setup", show=True),
        Binding("f3", "select_agent", "Select Agent", show=True),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main-layout"):
            with Vertical(id="chat-container"):
                yield RichLog(id="chat-log", wrap=True, markup=True)
                yield LoadingIndicator(id="loading-indicator")
                yield Button("Loading model status...", id="model-status-btn")
                with Horizontal(id="chat-input-container"):
                    yield Label(" [bold yellow]ᛟ❯[/bold yellow] ", id="prompt-label")
                    yield Input(placeholder="Speak to the Seer... (Press Enter to send)", id="chat-input")
            with VerticalScroll(id="sidebar"):
                yield Label("[bold cyan]Instructions[/bold cyan]\n")
                yield Label("Welcome to Mythic Agent! Type naturally to code, or use these commands:\n")
                yield Label("[green]/help[/green]   - Commands list")
                yield Label("[green]/setup[/green]  - Open setup wizard")
                yield Label("[green]/add[/green]    - Add file to context")
                yield Label("[green]/commit[/green] - Commit and push")
                yield Label("[green]/issue[/green]  - Create GitHub issue")
                yield Label("[green]/pr[/green]     - Create GitHub PR")
                yield Label("[green]/status[/green] - Check Git status")
                yield Label("[green]/gh[/green]      - Run GitHub CLI")
                yield Label("[green]/test[/green]    - Run tests")
                yield Label("[green]/undo[/green]    - Undo last file edit")
                yield Label("[green]/doctor[/green]  - Auto-fix issues")
                yield Label("[green]/flirt[/green]   - Flirt with the Agent")
                yield Label("[green]/btw[/green]    - Add silent context")
                yield Label("[green]/steer[/green]  - Steer the AI")
                yield Label("[green]/quit[/green]   - Exit")
                yield Label("\n[dim]Press F2 to quickly access setup.[/dim]")
                yield Label("\n[dim]Interactions: 0[/dim]", id="interaction-count")
                yield Label("[dim]Tokens Used: 0[/dim]", id="token-count")
                yield Label("\n[bold yellow]⚔️ Active Warriors[/bold yellow]\n[dim]None[/dim]", id="active-agents-label")
                yield Checkbox("Mythic Engineering Mode", id="mythic-engineering-checkbox")
                yield Checkbox("Auto-accept security permissions", id="auto-accept-checkbox")
                if HAS_IMAGE_WIDGET:
                    with AspectRatioContainer(id="agent-image-container"):
                        yield TextualImage(None, id="agent-image")
                else:
                    yield Static("", id="agent-image")
                yield Button("GitHub Repo", id="github-repo-btn", variant="primary")
        with Horizontal(id="footer-container"):
            yield Footer()
            yield Static(" | Active Agents: None", id="footer-agents-status")

    def on_mount(self) -> None:
        self.active_subagents = []
        chat_log = self.query_one("#chat-log", RichLog)
        
        config = config_manager.load_config()
        self.set_interval(1.0, self._update_footer_agent_status)
        
        chat_log.write("Welcome to the Viking Mythic Agent! Press F2 to configure your team.\n")
        chat_log.write("[dim]Type /help for a list of runic commands.[/dim]")
        self.query_one("#loading-indicator").display = False
        self.query_one("#chat-input").focus()
        
        self.update_model_status()
        self.app.set_interval(5.0, self.update_model_status)
        
        # Load Config states
        config = config_manager.load_config()
        self.query_one("#mythic-engineering-checkbox", Checkbox).value = config.get("mythic_engineering_mode", False)
        self.query_one("#auto-accept-checkbox", Checkbox).value = config.get("auto_accept_permissions", False)
        
        # Subscribe to Pub/Sub events from Agents/Handlers
        subscribe("agent_chat_chunk", self._on_chat_chunk)
        subscribe("agent_chat_tool", self._on_chat_tool)
        subscribe("agent_chat_complete", self._on_chat_complete)
        subscribe("agent_chat_error", self._on_chat_error)
        subscribe("agent_token_update", self._on_token_update)
        subscribe("agent_status_changed", self._on_agent_status_changed)
        subscribe("subagent_message_received", self._on_subagent_message_received)
        
        # Load initial agent image
        primary_name = config.get("primary_agent_name", "Primary")
        self.update_agent_image(primary_name)

    def _on_chat_chunk(self, agent_name: str, text: str):
        self.app.call_from_thread(self._write_to_log, text, markdown=True)

    def _on_chat_tool(self, agent_name: str, text: str):
        self.app.call_from_thread(self._write_to_log, text, dim=True)
        
    def _on_chat_error(self, agent_name: str, error: str):
        self.app.call_from_thread(self._write_to_log, f"\n[bold red]Error ({agent_name}): {error}[/bold red]")
        current_agent = getattr(self.app, "active_chat_agent", "Primary")
        if agent_name == current_agent:
            self.app.call_from_thread(self._set_loading, False)

    def _on_chat_complete(self, agent_name: str):
        current_agent = getattr(self.app, "active_chat_agent", "Primary")
        if agent_name == current_agent:
            self.app.call_from_thread(self._set_loading, False)

    def _on_token_update(self, agent_name: str, total_tokens: int):
        self.app.call_from_thread(self.app.update_token_count, total_tokens)

    def _on_agent_status_changed(self, agent_name: str, is_active: bool):
        self.app.call_from_thread(self._update_agent_status_ui, agent_name, is_active)
        
    def _update_agent_status_ui(self, agent_name: str, is_active: bool):
        try:
            if is_active:
                if agent_name not in self.active_subagents:
                    self.active_subagents.append(agent_name)
            else:
                if agent_name in self.active_subagents:
                    self.active_subagents.remove(agent_name)
                
            from ..agents.llm import AGENT_REGISTRY
            
            # Update dots if we are viewing the agent whose status just changed
            current_agent = getattr(self.app, "active_chat_agent", "Primary")
            if agent_name == current_agent:
                self._set_loading(is_active)
            
            lbl = self.query_one("#active-agents-label", Label)
            
            active_list = []
            for aname, agent in AGENT_REGISTRY.items():
                if aname == "Primary": continue
                status_color = "green" if aname in self.active_subagents else "dim"
                active_list.append(f"[{status_color}]● {aname}[/{status_color}]")
                
            if not active_list:
                active_list = ["[dim]None[/dim]"]
                
            lbl.update("\n[bold yellow]⚔️ Active Warriors[/bold yellow]\n" + "\n".join(active_list))
        except Exception as e:
            import logging
            logging.exception(f"Error in _update_agent_status_ui: {e}")

    def _update_footer_agent_status(self) -> None:
        try:
            from ..agents.llm import AGENT_REGISTRY
            import time
            
            active_list = []
            for aname, agent in AGENT_REGISTRY.items():
                if aname == "Primary": continue
                if aname in self.active_subagents and getattr(agent, "active_task_start_time", None):
                    elapsed = int(time.time() - agent.active_task_start_time)
                    
                    if elapsed < 60:
                        time_str = f"{elapsed}s"
                    else:
                        mins = elapsed // 60
                        secs = elapsed % 60
                        time_str = f"{mins}m {secs}s"
                        
                    active_list.append(f"{aname} ({time_str})")
            
            lbl = self.query_one("#footer-agents-status", Static)
            if active_list:
                lbl.update(f" | Active Agents: {', '.join(active_list)}")
            else:
                lbl.update(" | Active Agents: None")
        except Exception as e:
            import logging
            logging.exception(f"Error in _update_footer_agent_status: {e}")

    def _on_subagent_message_received(self, sender: str, recipient: str, message: str):
        self.app.call_from_thread(self._notify_subagent_message, sender, message)
        
    def _notify_subagent_message(self, sender: str, message: str):
        try:
            chat_log = self.query_one("#chat-log", RichLog)
            chat_log.write(Markdown(f"**[Raven from {sender}]:**\n\n{message}"))
            # Optionally trigger the Primary agent to read it
            self.run_agent_query(None)
        except Exception as e:
            import logging
            logging.exception(f"Error in _notify_subagent_message: {e}")

    def _write_to_log(self, text: str, markdown: bool = False, dim: bool = False):
        try:
            chat_log = self.query_one("#chat-log", RichLog)
            if markdown:
                chat_log.write(Markdown(text))
            else:
                from rich.markup import escape
                if "[+]" in text or "[~]" in text or "[-]" in text or "[red]" in text or "[green]" in text or "[dim]" in text:
                    chat_log.write(text) # Preserve markup
                elif dim:
                    chat_log.write(f"[dim]{escape(text)}[/dim]")
                else:
                    chat_log.write(escape(text))
        except Exception:
            pass

    def _set_loading(self, state: bool):
        try:
            self.query_one("#loading-indicator").display = state
        except Exception:
            pass

    def update_model_status(self) -> None:
        config = config_manager.load_config()
        model = config.get("model", "Unknown Model")
        base_url = config.get("base_url", "Unknown Provider")
        
        provider = "OpenRouter" if "openrouter" in base_url else "DeepSeek" if "deepseek" in base_url else "OpenAI" if "openai" in base_url else base_url
            
        btn = self.query_one("#model-status-btn", Button)
        btn.label = f"⚙️  {provider} : {model} (Click to change)"

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "model-status-btn":
            self.action_setup()
        elif event.button.id == "github-repo-btn":
            import webbrowser
            webbrowser.open("https://github.com/hrabanazviking/Mythic_Agent_Coder_CLI")
            self._write_to_log("[dim]Opening GitHub repository in browser...[/dim]", dim=True)

    def action_setup(self) -> None:
        self.app.switch_screen("setup_wizard")
        
    def action_select_agent(self) -> None:
        self.app.push_screen(SubagentSelectionModal(), self.on_agent_selected)
        
    def on_agent_selected(self, agent_name: str | None) -> None:
        if agent_name:
            self.app.active_chat_agent = agent_name
            chat_log = self.query_one("#chat-log", RichLog)
            config = config_manager.load_config()
            display_name = agent_name
            if agent_name == "Primary":
                display_name = config.get("primary_agent_name", "Primary Agent")
            chat_log.write(f"\n[bold cyan]⚔️ You are now speaking directly with {display_name}![/bold cyan]")
            self.update_agent_image(display_name)

    def update_agent_image(self, agent_name: str) -> None:
        if not HAS_IMAGE_WIDGET:
            return
            
        try:
            agent_image_widget = self.query_one("#agent-image")
        except Exception:
            return

        agent_name_lower = agent_name.lower()
        prefix = ""
        if "runa" in agent_name_lower or "primary" in agent_name_lower:
            prefix = "Runa_Gridweaver_Freyasdottir"
        elif "forge" in agent_name_lower:
            prefix = "Forge_Worker"
        elif "thor" in agent_name_lower:
            prefix = "Thor"
        else:
            prefix = agent_name.split("-")[0].strip()

        chars_dir = Path("default_agent_characters")
        if not chars_dir.exists():
            return

        matches = []
        for f in chars_dir.glob(f"{prefix}*"):
            if f.suffix.lower() in [".jpg", ".jpeg", ".png", ".gif"]:
                matches.append(f)

        if not matches:
            if hasattr(agent_image_widget, "image"):
                agent_image_widget.image = None
            else:
                agent_image_widget.update("")
            return

        image_path = random.choice(matches)
        
        try:
            if hasattr(agent_image_widget, "image"):
                agent_image_widget.image = str(image_path)
            else:
                agent_image_widget.update("")
        except Exception as e:
            import logging
            logging.error(f"Failed to render image {image_path}: {e}")

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        chat_log = self.query_one("#chat-log", RichLog)
        status = "enabled" if event.value else "disabled"
        config = config_manager.load_config()
        
        if event.checkbox.id == "mythic-engineering-checkbox":
            config["mythic_engineering_mode"] = event.value
            config_manager.save_config(config)
            chat_log.write(f"[bold magenta]Mythic Engineering Mode {status}![/bold magenta]")
            
        elif event.checkbox.id == "auto-accept-checkbox":
            config["auto_accept_permissions"] = event.value
            config_manager.save_config(config)
            chat_log.write(f"[bold red]Auto-accept security permissions {status}![/bold red]")

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        import logging
        user_input = event.value.strip()
        if not user_input:
            return
            
        event.input.value = ""
        chat_log = self.query_one("#chat-log", RichLog)

        logging.info(f"User input: {user_input}")
        chat_log.write(Markdown(f"**You:** {user_input}"))
        
        if user_input.startswith("/"):
            self.handle_command(user_input, chat_log)
            return
            
        self.run_agent_query(user_input)

    def handle_command(self, command: str, chat_log: RichLog) -> None:
        parts = command.split()
        cmd = parts[0].lower()
        args = " ".join(parts[1:])

        if cmd in ("/quit", "/exit"):
            self.app.exit()
        elif cmd == "/setup":
            self.action_setup()
        elif cmd == "/help":
            chat_log.write("[bold cyan]Runic Commands:[/bold cyan]")
            chat_log.write("  [green]/setup[/green]  - Open Setup Wizard (F2)")
            chat_log.write("  [green]/add[/green]    - Explicitly add a file to the LLM context")
            chat_log.write("  [green]/commit[/green] - Auto-commit and push changes to GitHub")
            chat_log.write("  [green]/issue[/green]  - Create a GitHub issue")
            chat_log.write("  [green]/pr[/green]     - Create a GitHub Pull Request")
            chat_log.write("  [green]/status[/green] - Check Git status")
            chat_log.write("  [green]/gh[/green]      - Run native GitHub CLI command")
            chat_log.write("  [green]/test[/green]    - Run tests natively")
            chat_log.write("  [green]/undo[/green]    - Roll back the last agent file edit (Git reset)")
            chat_log.write("  [green]/doctor[/green]  - Auto-fix a command output")
            chat_log.write("  [green]/flirt[/green]   - Flirt with the Agent")
            chat_log.write("  [green]/btw[/green]    - Add context without forcing an immediate response")
            chat_log.write("  [green]/steer[/green]  - Give the AI a strong steering instruction (system prompt)")
            chat_log.write("  [green]/quit[/green]   - Leave Valhalla (Exit)")
        elif cmd == "/add":
            if not args:
                chat_log.write("[red]Usage: /add <file_path>[/red]")
            else:
                try:
                    content = Path(args).read_text(encoding="utf-8")
                    SecureAPI.publish_chat_request(f"Here is the content of {args}:\n\n```\n{content}\n```")
                    chat_log.write(f"[green]Added {args} to context.[/green]")
                except Exception as e:
                    chat_log.write(f"[red]Error reading {args}: {e}[/red]")
        elif cmd == "/btw":
            if not args:
                chat_log.write("[red]Usage: /btw <message>[/red]")
            else:
                SecureAPI.publish_chat_request(f"By the way (for your context, no need to act on this alone unless asked): {args}")
                chat_log.write(f"[green]Added to context: {args}[/green]")
        elif cmd == "/steer":
            if not args:
                chat_log.write("[red]Usage: /steer <instruction>[/red]")
            else:
                SecureAPI.publish_chat_request(f"USER STEERING INSTRUCTION (Priority): {args}")
                chat_log.write(f"[bold yellow]Steering instruction applied: {args}[/bold yellow]")
        elif cmd == "/flirt":
            SecureAPI.publish_chat_request(f"*flirts with you* {args}")
            chat_log.write(f"[magenta]*Flirts...*[/magenta] {args}")
        elif cmd in ["/gh", "/status", "/commit", "/test", "/doctor", "/undo", "/issue", "/pr"]:
            SecureAPI.publish_system_command(cmd, args)
        else:
            chat_log.write(f"[red]Unknown command:[/red] {cmd}")


    def run_agent_query(self, user_input: str) -> None:
        self._set_loading(True)
        target_name = getattr(self.app, "active_chat_agent", "Primary")
        
        chat_log = self.query_one("#chat-log", RichLog)
        chat_log.write(f"[dim italic]→ Routing to {target_name}...[/dim italic]")
        
        SecureAPI.publish_chat_request(user_input, target_agent=target_name)

    def on_unmount(self) -> None:
        if hasattr(self.app, "pet_timer"):
            self.app.pet_timer.stop()
