
__all__ = [
    "App",
    "AspectRatioContainer",
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
    "MainChatScreen",
    "Markdown",
    "Middle",
    "ModalScreen",
    "PROVIDERS",
    "Path",
    "RichLog",
    "Screen",
    "SecureAPI",
    "Select",
    "Static",
    "SubagentSelectionModal",
    "TextArea",
    "Vertical",
    "VerticalScroll",
    "config_manager",
    "events",
    "publish_sync",
    "run_tui",
    "small_terminal_warning",
    "subscribe",
    "terminal_too_small",
    "ui_thread",
    "work",
]
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
from mythic_agent.ui import ui_thread, terminal_too_small, small_terminal_warning


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
        Binding("f4", "toggle_voice", "Voice Mode", show=True),
        Binding("f5", "toggle_mute", "Mute TTS", show=True),
        Binding("escape", "exit_ghost", "Exit Ghost Session", show=True),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main-layout"):
            with Vertical(id="chat-container"):
                yield RichLog(id="chat-log", wrap=True, markup=True)
                yield LoadingIndicator(id="loading-indicator")
                yield Button("Loading model status...", id="model-status-btn")
                yield Label("", id="autocomplete-suggestions", markup=True)
                with Horizontal(id="chat-input-container"):
                    yield Label(" [bold yellow]ᛟ❯[/bold yellow] ", id="prompt-label")
                    from textual.suggester import SuggestFromList
                    COMMANDS = ["/setup", "/add", "/commit", "/issue", "/pr", "/status", "/gh", "/test", "/undo", "/doctor", "/ollama", "/local", "/gateway", "/clear", "/compact", "/cost", "/review", "/flirt", "/lick", "/hug", "/kiss", "/snuggle", "/cuddle", "/tickle", "/wink", "/rose", "/mead", "/ale", "/beer", "/cookies", "/candy", "/love", "/btw", "/steer", "/stop", "/tutorial", "/quit", "/help", "/exit"]
                    yield Input(placeholder="Speak to the Seer... (Press Enter to send)", id="chat-input", suggester=SuggestFromList(COMMANDS))
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
                yield Label("[green]...[/green]    - (and more emotes!)")
                yield Label("[green]/btw[/green]    - Add silent context")
                yield Label("[green]/steer[/green]  - Steer the AI")
                yield Label("[green]/stop[/green]   - Stop all agents")
                yield Label("[green]/tutorial[/green] - Vibe coding guide")
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

        # Adapt the layout for very small terminals (S09).
        self._apply_terminal_layout()
        
        self.update_model_status()
        self.app.set_interval(5.0, self.update_model_status)
        
        # Load Config states
        config = config_manager.load_config()
        self.query_one("#mythic-engineering-checkbox", Checkbox).value = config.get("mythic_engineering_mode", False)
        self.query_one("#auto-accept-checkbox", Checkbox).value = config.get("auto_accept_permissions", False)
        from mythic_agent.agents.llm import AGENT_REGISTRY
        primary = AGENT_REGISTRY.get("Primary")
        if primary:
            primary.bind_tui(self.app)
            chat_log.write(f"Permission mode: {primary.tool_policy.mode}")
            from mythic_agent.core.permission_profiles import format_permission_profile
            chat_log.write(format_permission_profile(primary.config))
            self.query_one("#auto-accept-checkbox", Checkbox).disabled = primary._permission_override is not None
        
        # Subscribe to Pub/Sub events from Agents/Handlers
        subscribe("agent_chat_chunk", self._on_chat_chunk)
        subscribe("agent_chat_tool", self._on_chat_tool)
        subscribe("agent_command_output", self._on_chat_tool)
        subscribe("agent_chat_complete", self._on_chat_complete)
        subscribe("agent_chat_spoken", self._on_agent_chat_spoken)
        subscribe("agent_chat_error", self._on_chat_error)
        subscribe("agent_token_update", self._on_token_update)
        subscribe("agent_status_changed", self._on_agent_status_changed)
        subscribe("subagent_message_received", self._on_subagent_message_received)
        
        # Load initial agent image
        primary_name = config.get("primary_agent_name", "Primary")
        self.update_agent_image(primary_name)
        
        # Start TTS manager
        from mythic_agent.core.tts import tts_manager
        tts_manager.start()

    def _on_agent_chat_spoken(self, agent_name: str, text: str):
        from mythic_agent.core.tts import tts_manager
        tts_manager.speak(agent_name, text)

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
        # Fix (S09): the pub/sub path runs on a worker thread. Route through a
        # screen method so the app lookup and widget touch happen on the UI thread.
        self.app.call_from_thread(self._apply_token_update, total_tokens)

    def _apply_token_update(self, total_tokens: int) -> None:
        """Runs on the app thread; update_token_count touches widgets."""
        self.app.update_token_count(total_tokens)

    def on_resize(self, event: events.Resize) -> None:
        self._apply_terminal_layout()

    def _apply_terminal_layout(self) -> None:
        """Hide the sidebar and simplify the layout on very small terminals."""
        try:
            too_small, (cols, rows) = terminal_too_small()
            sidebar = self.query_one("#sidebar")
            if too_small:
                if not getattr(self, "_small_terminal_warned", False):
                    self.query_one("#chat-log", RichLog).write(
                        small_terminal_warning(cols, rows)
                    )
                    self._small_terminal_warned = True
                sidebar.display = False
            else:
                self._small_terminal_warned = False
                sidebar.display = True
        except Exception:
            pass

    def _on_agent_status_changed(self, agent_name: str, is_active: bool):
        self.app.call_from_thread(self._update_agent_status_ui, agent_name, is_active)
        
    @ui_thread()
    def _update_agent_status_ui(self, agent_name: str, is_active: bool):
        try:
            if is_active:
                if agent_name not in self.active_subagents:
                    self.active_subagents.append(agent_name)
            else:
                if agent_name in self.active_subagents:
                    self.active_subagents.remove(agent_name)
                
            from mythic_agent.agents.llm import AGENT_REGISTRY
            
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
            from mythic_agent.agents.llm import AGENT_REGISTRY
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
        
    @ui_thread()
    def _notify_subagent_message(self, sender: str, message: str):
        try:
            chat_log = self.query_one("#chat-log", RichLog)
            chat_log.write(Markdown(f"**[Raven from {sender}]:**\n\n{message}"))
            # Notify the primary agent about the incoming subagent message
            # Do NOT call run_agent_query(None) — None would be stringified and corrupt context
            self.run_agent_query(f"[Subagent Message from {sender}]: {message}")
        except Exception as e:
            import logging
            logging.exception(f"Error in _notify_subagent_message: {e}")

    def _write_to_log(self, text: str, markdown: bool = False, dim: bool = False):
        try:
            chat_log = self.query_one("#chat-log", RichLog)
            if markdown:
                from rich.markdown import Markdown
                files_header = "[bold cyan]Files Changed:[/bold cyan]"
                if files_header in text:
                    parts = text.split(files_header)
                    if parts[0].strip():
                        chat_log.write(Markdown(parts[0]))
                    chat_log.write(files_header + parts[1])
                else:
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
        
    def action_exit_ghost(self) -> None:
        current = getattr(self.app, "active_chat_agent", "Primary")
        if "[Ghost]" in current:
            original_agent = current.replace("[Ghost] ", "").strip()
            self.on_agent_selected(original_agent)
            
    def on_agent_selected(self, agent_name: str | None) -> None:
        if agent_name:
            self.app.active_chat_agent = agent_name
            chat_log = self.query_one("#chat-log", RichLog)
            config = config_manager.load_config()
            display_name = agent_name
            if agent_name == "Primary":
                display_name = config.get("primary_agent_name", "Primary Agent")
                
            if "[Ghost]" in agent_name:
                chat_log.write(f"\n[bold magenta]✦ You have entered a subagent Ghost Session with {display_name.replace('[Ghost]', '').strip()}.[/bold magenta]")
                chat_log.write("[bold yellow]This is a temporary clone of the working agent. It is answering your messages instantly without interrupting its main workflow.[/bold yellow]")
                chat_log.write("[bold white]→ Press ESC to exit this subagent and return to the original agent.[/bold white]\n")
            else:
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
        if "alfhild" in agent_name_lower:
            prefix = "Alfhild_Nyxra_Gridhex"
        elif "runa" in agent_name_lower or "primary" in agent_name_lower:
            prefix = "Runa_Gridweaver_Freyasdottir"
        elif "forge" in agent_name_lower:
            prefix = "Forge_Worker"
        elif "thor" in agent_name_lower:
            prefix = "Thor"
        else:
            prefix = agent_name.split("-")[0].strip()

        # Use a path relative to this source file so it works regardless of CWD
        from mythic_agent.resources import character_directory
        chars_dir = character_directory()
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
            if not config_manager.save_config(config):
                return
            chat_log.write(f"[bold magenta]Mythic Engineering Mode {status}![/bold magenta]")
            
        elif event.checkbox.id == "auto-accept-checkbox":
            config["auto_accept_permissions"] = event.value
            if not config_manager.save_config(config):
                return
            from mythic_agent.agents.llm import AGENT_REGISTRY
            for agent in list(AGENT_REGISTRY.values()):
                if agent.tui_app:
                    agent.config["auto_accept_permissions"] = event.value
                    agent.bind_tui(agent.tui_app)
            chat_log.write(f"[bold red]Auto-accept security permissions {status}![/bold red]")

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id != "chat-input":
            return
            
        val = event.value
        try:
            lbl = self.query_one("#autocomplete-suggestions", Label)
            if val.startswith("/"):
                COMMANDS = ["/setup", "/add", "/commit", "/issue", "/pr", "/status", "/gh", "/test", "/undo", "/doctor", "/ollama", "/local", "/gateway", "/clear", "/compact", "/cost", "/review", "/flirt", "/lick", "/hug", "/kiss", "/snuggle", "/cuddle", "/tickle", "/wink", "/rose", "/mead", "/ale", "/beer", "/cookies", "/candy", "/love", "/btw", "/steer", "/stop", "/tutorial", "/quit", "/help", "/exit"]
                matches = [c for c in COMMANDS if c.startswith(val.lower())]
                if matches:
                    formatted = []
                    for i, m in enumerate(matches[:8]):
                        if i == 0:
                            formatted.append(f"[bold cyan]{m}[/bold cyan]")
                        else:
                            formatted.append(f"[dim]{m}[/dim]")
                    lbl.update(" ".join(formatted))
                else:
                    lbl.update("")
            else:
                lbl.update("")
        except Exception:
            pass

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        import logging
        user_input = event.value.strip()
        if not user_input:
            return
            
        event.input.value = ""
        try:
            self.query_one("#autocomplete-suggestions", Label).update("")
        except Exception:
            pass
            
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
            if not args:
                chat_log.write("[bold cyan]Runic Commands (Type /help <cmd> for details):[/bold cyan]")
                chat_log.write("  [green]/setup[/green]    - Open Setup Wizard (F2)")
                chat_log.write("  [green]/add[/green]      - Add a file to the LLM context")
                chat_log.write("  [green]/commit[/green]   - Commit and push to GitHub")
                chat_log.write("  [green]/issue[/green]    - Create a GitHub issue")
                chat_log.write("  [green]/pr[/green]       - Create a GitHub PR")
                chat_log.write("  [green]/status[/green]   - Check Git status")
                chat_log.write("  [green]/gh[/green]        - Run GitHub CLI")
                chat_log.write("  [green]/test[/green]      - Run tests")
                chat_log.write("  [green]/undo[/green]      - Roll back last file edit")
                chat_log.write("  [green]/doctor[/green]    - Auto-fix a command output")
                chat_log.write("  [green]/ollama[/green]    - Local Ollama models: list / pull / show")
                chat_log.write("  [green]/local[/green]     - Local runtimes (LM Studio / llama.cpp / any port): list / show")
                chat_log.write("  [green]/gateway[/green]   - Gateway catalogue (OpenRouter): list / search / show")
                chat_log.write("  [green]/model[/green]     - Show or switch the live model/provider (session, plan and crew kept)")
                chat_log.write("  [green]/route[/green]     - Show or set per-office model routes (crew roles on different models)")
                chat_log.write("  [green]/fallback[/green]  - Show or set the fallback chain (doors walked when a provider fails, with standing permission)")
                chat_log.write("  [green]/costroute[/green] - Cost-aware routing: prefer the cheaper adequate door for a task class (off by default, explained in plain words)")
                chat_log.write("  [green]/editformat[/green] - Edit-format plurality: whole-file, unified-diff, search-and-replace, or architect/editor split — picked per task and per model strength, journaled (auto by default)")
                chat_log.write("  [green]/hashanchor[/green] - Hash-anchored edits: lines named by their content hash; a moved target refuses cleanly and changes nothing (on by default)")
                chat_log.write("  [green]/repairloop[/green] - Apply-failure repair loop: a refused apply returns the true current text for one honest retry — bounded, visible, no fuzz (on by default)")
                chat_log.write("  [green]/hunkreview[/green] - Hunk-level review: a diff is shown hunk by hunk with accept/reject/edit per hunk — rejecting one hunk never kills the rest (on by default)")
                chat_log.write("  [green]/changeset[/green] - Multi-file change sets: work that lands together is named, reviewed file by file, and applied all-or-nothing with its test evidence attached (on by default)")
                chat_log.write("  [green]/rename[/green] - Rename/move files as first-class edits: history-preserving git mv, references updated via the Part III symbol graph, planned and journaled like any other edit (on by default)")
                chat_log.write("  [green]/generated[/green] - Generated-code honesty: generated files are marked, their generator is recorded, and a hand-edit to a generated file warns before saving (on by default)")
                chat_log.write("  [green]/largefile[/green] - Large-file and binary care: big files are edited by anchored chunks, binaries are never text-edited, and every size guard explains itself (on by default)")
                chat_log.write("  [green]/stash[/green] - The stash shelf: shelve work-in-progress by name, the tree goes back to clean, and the change restores in any later session - the shelf is a checksummed journal that survives crashes (on by default)")
                chat_log.write("  [green]/patch[/green] - Patch export/import: a reviewed change set becomes one portable patch file with its evidence header, and a patch file lands on another tree only whole - one stale file refuses everything (on by default)")
                chat_log.write("  [green]/diff[/green] - Diff theatre: one change staged unified or side-by-side, word-level changes picked out, whitespace-only lines judged and flagged - colour never the only signal (on by default)")
                chat_log.write("  [green]/blame[/green] - Blame and history sight: why is this line like this - git blame names the commit, the journal names the session that wrote it, and uncommitted lines are flagged as the working tree's own (on by default)")
                chat_log.write("  [green]/massedit[/green] - Guarded mass edits: a repo-wide edit is shown whole first - every file, hunk and risk in a dry-run report - and a plan changing two or more files, or any high-risk file, needs an approval bound to the report's fingerprint before a single byte moves (on by default)")
                chat_log.write("  [green]/posture[/green] - Permission profiles: the session's posture in one named answer - Read-Only Scout, Trusted Forge, Full Autonomy, or a custom posture - binding tools, paths, network and commands; the posture always rides the status line")
                chat_log.write("  [green]/remember[/green] - Remembered approvals: a standing always-allow for one exact scope - this command, with these arguments, in this project - created only by your explicit yes at the approval prompt, listed in one screen, and revocable from that same screen")
                chat_log.write("  [green]/sandbox[/green] - The OS sandbox: commands run under native OS confinement - Linux namespaces, macOS sandbox-exec, Windows job objects, each as far as it honestly goes - never Docker; the per-platform truth is part of the screen (on by default)")
                chat_log.write("  [green]/network[/green] - Network gates: outbound network is gated per tool and per domain - a tool may reach only the domains its allowlist entries name, everything else is refused by default, and every refusal is surfaced as news, never just a log line (on by default)")
                chat_log.write("  [green]/pathjail[/green] - Path jail: file tools are confined to the workspace plus named grants - a path is allowed only when its resolved path lands inside the workspace or a granted directory, symlink escapes are caught by resolution, everything else is refused by default, and every refusal is surfaced as news, never just a log line (on by default)")
                chat_log.write("  [green]/plan[/green] - Plan mode: a read-everything, write-nothing posture - while it is on the coder may read and plan but not write or execute, the plan is slices with acceptance checks in Part IX form, approving that one plan is the only gate to building, and every refusal is surfaced as news, never just a log line (off by default)")
                chat_log.write("  [green]/hooks[/green] - Hooks: user scripts run at seven lifecycle events - pre_tool, post_tool, pre_edit, post_edit, on_test, on_commit, on_session; exit 0 allows, exit 2 blocks, a JSON block blocks at any exit code, an error blocks before the act or at a gate and is news only after it, and every block is surfaced as news with the reason the coder must answer")
                chat_log.write("  [green]/hookpacks[/green] - Hook packs: the house hooks shipped as installable packs - tests_after_edits runs the test suite after edits, readme_guard guards the README with read-only checks only, verify_pushes verifies the work at commit time; installing a pack folds its hooks into the configured hooks, explicitly and idempotently, and a pack already fully installed changes nothing")
                chat_log.write("  [green]/background[/green] - Background tasks: long commands - builds, test suites, servers - run as managed jobs with a lifecycle of queued, running, then completed, failed or cancelled; start one, watch its bounded live tail, or kill it - a kill is recorded as a request first, then the real process is terminated and the job is cancelled; when a job finishes, its completion is session news")
                chat_log.write("  [green]/keeper[/green] - The keeper: work is watched for stalls - a background job, a crew member, a task - judged active, quiet or stalled from its last sign of life alone; a stalled watch is restarted while restarts remain and reported when they run out, and an owed intervention is session news")
                chat_log.write("  [green]/schedule[/green] - Scheduled work: cron-style jobs held as data - what to run as a list of words, never a shell string, when to run it (daily at a named time, weekly on a named weekday, or every so many minutes), whether it is enabled, and its approval posture; a due unattended job is carried out as a real background job and its run recorded, a job that needs approval is recorded as due and waiting and never run unattended, and a due moment is session news")
                chat_log.write("  [green]/fleet[/green] - Headless fleet mode: the mythic run road grown for CI - many tasks held as data, each a command as a list of words, never a shell string, in its repo, with its prompt; a fleet check carries the remaining tasks out as real background jobs in parallel and judges each from its real ending - passed, failed or error - the fleet verdict is mechanical and its exit code honest (0 only when every task passed, 1 for a failure, 2 for an error or an unfinished fleet), a passed task is never run again, and each completion is session news")
                chat_log.write("  [green]/budgets[/green] - Budgets as guardrails: a per-task or per-session budget may name a limit on tokens, on cost, on time and on commands - a dimension with no limit named is unlimited, and no default limit is invented; usage readings say what has actually been spent, read from the real roads (tokens and cost from the costs ledger, elapsed time from the session clock, commands from the held background jobs); the judge is mechanical - within below 80% of every limit, warning at or past 80%, exceeded at or past a limit - and an exceeded budget is a graceful pause at a resting point, published as a budget_paused session event, never a mid-edit death")
                chat_log.write("  [green]/halt[/green] - The kill switch everywhere: one command halts the coder, the crew, background jobs and pending approvals - instant, and total for the targets named; a target is halted only when the session actually holds live work for it, finished work is already stopped and never newly halted, and a merely queued crew task is a plan, not held work; held background jobs are killed through the background road, a running crew task on its backing job, the coder stops at the next boundary on its cancellation event, a pending approval waiting on that same event is refused, and every pull is a kill_switch_pulled session event")
                chat_log.write("  [green]/audit[/green] - Audit trail: every tool call, approval, edit and command in the journal, each stamped with its actor - the human, the coder, the crew or a hook; the trail is append-only, an entry once recorded is never changed or removed, and the export for review names every recorded entry in the order it was appended; every recorded entry is published as an audit_recorded session event")
                chat_log.write("  [green]/secrets[/green] - Secret hygiene in action: files are screened for commit by secret shape - a file whose name or text matches a known secret pattern is refused, naming the file and the pattern kinds only, its content never shown; tool results pass through the hygiene redaction before they enter the transcript, and every refusal is a secret_refusal session event")
                chat_log.write("  [green]/doctrine[/green] - Destructive-command doctrine: every command is judged against a written ladder - a reversible act can be undone and needs no approval, a costly act can be undone only at a price and asks once before it runs, an irreversible act can never be undone and needs explicit approval naming every target in plain words first; a command no pattern knows is unclassified and never claimed safe, and every costly or irreversible judgement is a destructive_act session event")
                chat_log.write("  [green]/rollback[/green] - Rollback drills: scripted disasters recovered in tests - a bad mass edit rolled back to its checkpoint, a wrong branch push attempt stopped before the remote, a corrupted session recovered from its journal - each drill's recovery road walks machinery the tree already ships, a result counts the steps that passed and its outcome is derived from that count, recovered only when every step passed and never rounded up, and every judged run is a rollback_drill_run session event")
                chat_log.write("  [green]/multirepo[/green] - Multi-repo workspaces: several repos under one session, each with its own policy - its mode (read-only, ask, or trusted), the branch its work targets, and whether its changes require review - and a change spanning repos is one change set reviewed whole, decided under one name and planned all-or-nothing so no repo part applies alone, and every held set is a multi_repo_change_set session event")
                chat_log.write("  [green]/remote[/green] - Remote and SSH work: the coder runs against a project on another machine through one connection - a target held as data (its address, user, port and the workspace root the project lives under there, and its one SSH connection, authenticating by agent, key file or password) and work plans of remote commands as argv word lists, never a shell string, and file operations against the remote root; a plan is judged whole against its target - an unknown target, a step outside the remote root, or a file operation that would copy a file back to this machine all refuse - and every judged plan is a remote_work_plan session event")
                chat_log.write("  [green]/grace[/green] - Offline and degraded grace: when part of the coder world fails - the model provider down, the language server (LSP) down, the network down - the coder narrows honestly and says what it lost in plain words, and what still stands; the state is judged only from evidence given - full only when the provider, the language server and the network all affirmatively answer, a dimension whose evidence is unknown named unknown and never guessed up or down, and one failure never invents another - and every judged assessment is a degradation_change session event")
                chat_log.write("  [green]/moment[/green] - Approval by phone-sized moments: an approval ask is a single, complete question with full context - what is asked, where it acts, and what it does - and each choice says what choosing it does, so the whole ask can be answered with one tap in one phone-sized moment; a moment missing any part, asking more than one question, carrying a choice with no stated effect, or running longer than one moment holds is judged incomplete and the missing parts are named - and every judged moment is an approval_moment session event")
                chat_log.write("  [green]/policy[/green] - Policy as code: one checked-in file (mythic-policy.yaml at the repo root) carries a team's rules - the permission posture, the path jail and its grants, and the hooks - and the agent loads it at session start and applies it through the journal-first setting roads, publishing the applied policy as session news; no file means no policy and nothing invented, and a file that fails validation is refused whole")
                chat_log.write("  [green]/crew[/green] - Agents as files: the crew is held as data - one record per member naming its name, the office it holds, its model route, the tools it works with, the posture it works under and the character file that carries its voice - the existing characters are the first castings and a new member joins as a record in a file, not a code change; held members spawn through the shipped sub-agent road under their record's posture - and every member that joins is a crew_member session event")
                chat_log.write("  [green]/offices[/green] - The six offices formalised: Skald (intent & vision), Architect (design), Forge Worker (build), Auditor (verify), Cartographer (map & research) and Scribe (memory & docs) - each held as data with its duties, its tools, what it takes in and produces, and its hand-off contracts; the shipped polymath and guardian offices are not among the six; every office taken up for the session is an office session event; /offices custom shows the user-defined custom offices beyond the six (M-123) - the roadmap's Gatekeeper and Benchmarker examples - held as data the same way, user-defined and never formalised, and every custom office taken up for the session is a custom_office session event")
                chat_log.write("  [green]/worktrees[/green] - Parallel worktrees: each building crew member works in its own git worktree on its own branch - never two writers in one tree - and the coordinator, who holds no worktree of their own in the plan, is the only one who merges, in slice order; the shipped example plan deals the M-121 casting one worktree each; every assignment taken up for the session is a worktree_assignment session event; this surface runs no git command and creates no worktree - the registry holds the plan as data")
                chat_log.write("  [green]/dealing[/green] - Task dealing: a plan's slices are dealt to the crew by office fit and current load - a slice goes first to a member holding the office its work fits, among equally fitting members to the least loaded - and the human may re-deal any slice to another member; the shipped example plan deals the next ten roadmap slices to the M-121 casting; every assignment dealt for the session is a task_dealing session event; there is no Part VIII board yet, so the dealing is visible on this surface, not on a board")
                chat_log.write("  [green]/comms[/green] - Crew comms: members hand structured hand-offs to each other - findings, a diff, or a question - each naming its sender, its recipient, the slice it belongs to, a title and a body; a member's question to the human is batched and asked once, together, with full context, never piecemeal; the shipped example ledger holds six hand-offs among the M-121 casting, three of them questions to the human; every hand-off handed for the session is a crew_handoff session event and every batched ask is one human_question_batch session event; there is no Part VIII board yet, so the hand-offs and the batch are visible on this surface, not on a board; this surface spawns no crew and delivers no message")
                chat_log.write("  [green]/deadlock[/green] - Cycle and deadlock watch: the coordinator's evidence - who delegates work on which slice to whom, and who holds which slice at which path - is checked mechanically for the three hazards that stall a crew, a delegation cycle, a merge conflict and duplicated work; the shipped example watch holds five delegations and five claims among the M-121 casting, yielding exactly three findings, one of each kind; every delegation or claim held for the session is a crew_delegation / crew_claim session event, every finding a deadlock_finding session event and every report one deadlock_report session event; there is no Part VIII board yet, so the findings are visible on this surface, not on a board; this surface spawns no crew, stops no member and runs no git")
                chat_log.write("  [green]/merge[/green] - Merge discipline: member branches merge in slice order along each member line, with a test gate recorded at each merge, and a red merge stops only its own line, not the whole crew; the shipped example plan holds seven steps and five recorded merges among the M-121 casting, yielding exactly three verdicts, one of each kind; every step or merge held for the session is a merge_step / merge_attempt session event, every verdict a merge_verdict session event and every report one merge_report session event; there is no Part VIII board yet, so the verdicts are visible on this surface, not on a board; this surface executes no git, performs no real merge and spawns or stops no crew")
                chat_log.write("  [green]/hetero[/green] - Heterogeneous crews: members ride different models on different providers - a Claude Architect, a local-LLM Forge Worker - with routing truth from Part II and budgets from Part V; the shipped example plan holds four assignments, two budgets and two readings among the M-121 casting, yielding exactly three verdicts, one of each kind; every assignment or reading held for the session is a hetero_assignment / hetero_reading session event, every verdict a hetero_verdict session event and every report one hetero_report session event; there is no Part VIII board yet, so the verdicts are visible on this surface, not on a board; this surface spawns no live crew, calls no real provider and performs no routing or billing")
                chat_log.write("  [green]/veto[/green] - The Auditor's veto: no slice is done until the Auditor's checks pass - the veto is a real gate, not a custom; the shipped example ledger holds three cases, six checks and five results among the Part VI slices, yielding exactly two verdicts, one of each kind, with M-128 passed and M-127 and M-129 vetoed; every case, check or result held for the session is a veto_case / veto_check / veto_result session event, every verdict a veto_verdict session event and every report one veto_report session event; there is no Part VIII board yet, so the verdicts are visible on this surface, not on a board; this surface runs no check, executes no test suite and banks nothing")
                chat_log.write("  [green]/swarm[/green] - Research swarms: a Cartographer-led fan-out for questions - one question dealt out to several members at once, each reading one focus of it (the docs, the options, the comparison), returning one digested answer with sources; the shipped example swarm holds one question, three assignments and three findings among the M-121 casting, led by the cartographer, yielding one complete digest standing on three sources; every question, assignment or finding held for the session is a swarm_question / swarm_assignment / swarm_finding session event and every digest report one swarm_digest session event; there is no Part VIII board yet, so the digest is visible on this surface, not on a board; this surface runs no research, calls no model and spawns no crew")
                chat_log.write("  [green]/panel[/green] - Review panels: one change put to two reviewers riding different models, each returning their own verdict in their own words; the shipped example panel holds the session-branching restore guard reviewed by the auditor (approve, on anthropic/claude-sonnet-4-5) and the guardian (request_changes, on ollama/llama3.1), yielding a disagreement that is surfaced, not averaged; every change or review held for the session is a panel_change / panel_review session event and every outcome report one panel_outcome session event; there is no Part VIII board yet, so the outcome is visible on this surface, not on a board; this surface runs no review, calls no model, executes no change and spawns no crew")
                chat_log.write("  [green]/editor[/green] - Editor bridges lite: any file or prompt draft takes a round-trip through your own $VISUAL/$EDITOR, judged by its content anchor - changed text lands, unchanged writes nothing, an emptied file refuses and an emptied prompt cancels (on by default)")
                chat_log.write("  [green]/issueslice[/green] - Issue-to-slice: a GitHub issue becomes a planned slice with acceptance checks drafted from its own words (on by default)")
                chat_log.write("  [green]/prcraft[/green] - PR craft: create, review, and respond to pull requests — review comments fetched as tasks; drafts post only at your word (on by default)")
                chat_log.write("  [green]/conflicts[/green] - Conflict workbench: merge/rebase conflicts shown as decisions with both sides' intent summarised from the real commits (on by default)")
                chat_log.write("  [green]/commitcraft[/green] - Commit craft: changes split into commits by concern, messages drafted from the actual diff, pushes under the house rules — fetch + remote-diff first, never force-push, verify the remote moved (on by default)")
                chat_log.write("  [green]/checkpoint[/green] - Named checkpoints: freeze the whole working tree plus session state under a name, and bring it back with one command (on by default)")
                chat_log.write("  [green]/branch[/green] - Session branching: fork a session at any message to try the other road — branches share history, diverge honestly, and can be compared (on by default)")
                chat_log.write("  [green]/autocommit[/green] - Auto-commit discipline: every accepted edit set lands as its own commit with a written message, on a working branch by default — never on a protected branch unasked (off by default)")
                chat_log.write("  [green]/guardians[/green] - README and licence guardians: a README is never overwritten and licence files are never touched, without the user's explicit word (guard on; the word is off by default)")
                chat_log.write("  [green]/kista[/green]     - Key custody: where each door's key lives (Kista holds the keys; the config holds references)")
                chat_log.write("  [green]/resume-thought[/green] - Streaming discipline: resume an interrupted answer from its salvaged partial (where the model is known to support it)")
                chat_log.write("  [green]/retry[/green] - Retry honesty: bounded retries on temporary failures only, each announced with its reason and wait; mutating calls are never silently replayed")
                chat_log.write("  [green]/vision[/green] - Vision input routing: image work goes only to a model known to see; otherwise refused plainly, with the switch offered")
                chat_log.write("  [green]/longcontext[/green] - Long-context strategy: how the repo is loaded is chosen from the model's recorded context size (map-first at a million tokens, retrieval-first below, honest unknown when unrecorded)")
                chat_log.write("  [green]/offline[/green] - Offline honesty: when no network route to a model and no local model answers, the app says exactly that and offers the non-model tools that still work (review, metrics, session search)")
                chat_log.write("  [green]/testkit[/green] - New-provider test kit: a registry entry must pass registry, chat, tools, streaming and errors proven against its door before it ships")
                chat_log.write("  [green]/map[/green] - The repo map, visible: browse the ranked files with the reasons the coder thinks each matters, ask one file's full account, and pin files to see them first (rank and score unchanged)")
                chat_log.write("  [green]/ssearch[/green] - Structural search: find code by its shape with an ast-grep-style pattern ($NAME captures one node, $$$ captures zero or more) over every file of a language")
                chat_log.write("  [green]/srewrite[/green] - Structural rewrite: the same patterns as safe codemods — per-site diff preview first, application through the edit journal only for files unchanged since the plan")
                chat_log.write("  [green]/lsp[/green] - Language servers: which servers this machine has, one file's real diagnostics, and true navigation answers — definition, references, hover, workspace symbols (a missing server is reported, never shown as an answer)")
                chat_log.write("  [green]/clear[/green]     - Clear agent memory")
                chat_log.write("  [green]/compact[/green]   - Compact agent memory")
                chat_log.write("  [green]/cost[/green]      - Estimate token cost")
                chat_log.write("  [green]/review[/green]    - Auto-review git diff")
                chat_log.write("  [green]/flirt[/green]     - Flirt with the Agent")
                chat_log.write("  [green]/lick[/green]      - Lick the Agent")
                chat_log.write("  [green]/hug[/green]       - Hug the Agent")
                chat_log.write("  [green]/kiss[/green]      - Kiss the Agent")
                chat_log.write("  [green]/snuggle[/green]   - Snuggle with the Agent")
                chat_log.write("  [green]/cuddle[/green]    - Cuddle the Agent")
                chat_log.write("  [green]/tickle[/green]    - Tickle the Agent")
                chat_log.write("  [green]/wink[/green]      - Wink at the Agent")
                chat_log.write("  [green]/rose[/green]      - Send a red rose")
                chat_log.write("  [green]/mead[/green]      - Send a drinking horn of mead")
                chat_log.write("  [green]/ale[/green]       - Send a tankard of ale")
                chat_log.write("  [green]/beer[/green]      - Send a stein of beer")
                chat_log.write("  [green]/cookies[/green]   - Give some cookies")
                chat_log.write("  [green]/candy[/green]     - Give a chocolate candy bar")
                chat_log.write("  [green]/love[/green]      - Give positive love energy")
                chat_log.write("  [green]/btw[/green]      - Add silent context to an agent")
                chat_log.write("  [green]/steer[/green]    - Give the AI a strong steering instruction")
                chat_log.write("  [green]/stop[/green]     - Stop all currently active agents")
                chat_log.write("  [green]/tutorial[/green] - Vibe coding guide")
                chat_log.write("  [green]/quit[/green]     - Leave Valhalla (Exit)")
            else:
                target_cmd = args.strip().lower()
                if not target_cmd.startswith("/"):
                    target_cmd = "/" + target_cmd
                    
                help_dict = {
                    "/setup": "Opens the Setup Wizard allowing you to configure APIs, subagents, and preferences.",
                    "/add": "Usage: /add <file_path>\nReads the file and explicitly adds its contents to the LLM's working memory.",
                    "/commit": "Usage: /commit <message>\nShows a preview (git status --short, git diff --stat) of what would be committed, then run /commit --confirm to stage, commit, and push.",
                    "/issue": "Usage: /issue <title>\nCreates a new GitHub issue using the gh CLI tool.",
                    "/pr": "Usage: /pr\nCreates a Pull Request using the gh CLI tool.",
                    "/status": "Usage: /status\nShows current git status and recent commits.",
                    "/gh": "Usage: /gh <args>\nRuns arbitrary native GitHub CLI commands.",
                    "/test": "Usage: /test\nRuns pytest natively in the repository.",
                    "/undo": "Usage: /undo [list|edit|command|checkpoint <id>|<count>|on|off]\nWalks edits, commands, and checkpoints as one timeline, newest first: bare /undo undoes the newest entry, a command undoes through its recorded footprint (labelled certain or best-effort), and an edit restores through the workspace journal. Preserves Git history, staged changes and unrelated files.",
                    "/doctor": "Usage: /doctor\nExamines the output of the last failed command and automatically generates a fix.",
                    "/ollama": "Usage: /ollama [list] | /ollama pull <model> | /ollama show <model>\nTalks to the local Ollama server (OLLAMA_HOST or http://localhost:11434): list shows installed and running models, pull downloads a model, show gives one model's details — or an honest 'not present' answer.",
                    "/local": "Usage: /local [list] | /local <lmstudio|llama.cpp|local-openai> show <model>\nDiscovers the local OpenAI-compatible runtimes (LM Studio http://localhost:1234, llama.cpp http://localhost:8080, or any local port): list shows what each server is serving, show gives one model's presence — or an honest 'not present' answer with its remedy.",
                    "/gateway": "Usage: /gateway [list] | /gateway search <text> | /gateway show <model>\nBrowses the OpenRouter gateway catalogue in-app (its public /models door — no key needed to browse): list shows the first models with the full count, search filters by id or name, show gives one model's reported context, modality and prices — or an honest 'not in the catalogue' answer. The kin gateways (groq, together, fireworks, xai, mistral) are providers in their own right; pick one as your provider to use its models.",
                    "/route": "Usage: /route | /route <office> | /route <office> <model> [url] | /route <office> --provider <name> [--model <model>] | /route clear <office>\nPer-office model routing (M-029): different models for different offices — a deep thinker for the Architect, a fast hand for the Forge Worker, a cheap scout for the Cartographer. An office with no route uses the session default; routes are recorded as a session journal event and crew members take a route when spawned or when re-routed while idle. The Primary office has no route of its own — its selection is the session default, changed with /model.",
                    "/model": "Usage: /model | /model <model> [url] | /model --provider <name> [--model <model>] [--reason <words...>]\nShows or switches the live session's model or provider (M-028): the session, its history and plan, and the crew are kept, and the switch is recorded as a session journal event with the reason when one is given. Providers the live session cannot speak (the native-SDK doors and Ollama's own API) are refused plainly, with the session unchanged.",
                    "/fallback": "Usage: /fallback | /fallback on | /fallback off | /fallback add <model> [url] | /fallback add --provider <name> [--model <model>] | /fallback clear\nFallback chains (M-030): when a provider fails or rate-limits, the session walks the configured doors in order — but only with your standing permission (/fallback on; off by default), and every walk is announced in the chat and recorded as a session journal event, never silent. Doors are validated through the provider registry; a native-SDK door, the current door, or a duplicate is refused plainly.",
                    "/costroute": "Usage: /costroute | /costroute on | /costroute off | /costroute <task-class>\nCost-aware routing (M-031): with mythic costs data, the router can prefer the cheaper adequate model for a task class (general, coding, reasoning, vision, long_context) — a setting, off by default, explained in plain words. It only chooses between doors you have already configured (your current door, your fallback chain, your role routes), only when the cheaper model's price is known and its abilities are known to fit the work, and it always says why; an applied switch is recorded as a session journal event with that reason.",
                    "/editformat": "Usage: /editformat | /editformat auto | /editformat <format> | /editformat <task-kind>\nEdit-format plurality (M-071): the coder picks how to change a file per task and per model strength — whole-file, unified-diff, search-and-replace blocks, or an Aider-style architect/editor split. Strength is capability truth (M-027): a proven-strong model gets a unified diff for multi-site work, a standard model gets search-and-replace blocks, and a model of unknown strength always gets the safest whole-file rewrite. Diffs and search blocks apply only on an exact match — no fuzz — and every pick is recorded as a session journal event with its reason. The setting (auto by default) can pin one format; creating a file is always whole-file.",
                    "/hashanchor": "Usage: /hashanchor | /hashanchor on | /hashanchor off\nHash-anchored edits (M-072): every line of a file carries a short SHA-256 content hash — its anchor. An anchored edit names the lines it touches by line range plus the anchor it saw, instead of re-sending the whole text; Mythic recomputes the anchor from the file as it stands and applies only on an exact match. A moved or changed target refuses cleanly, names the expected and current anchors, and changes nothing — no fuzz, ever. The gate ships on; /hashanchor off refuses anchored applies through the agent until it is turned back on.",
                    "/repairloop": "Usage: /repairloop | /repairloop on | /repairloop off\nApply-failure repair loop (M-073): when an edit refuses — a stale diff, a search block that does not match exactly once, an anchored target that moved — the coder is handed a repair packet: the refusal's reason plus the true current text of the refused target (a bounded window — the target's lines plus 5 lines of context, capped at 40 lines, with any truncation named). Exactly one honest retry may ride on the packet, judged by the same strict rules — no fuzz, ever; a second refusal ends the loop and says so. Every packet, retry, and outcome is recorded on the session journal. The gate ships on; /repairloop off keeps the plain refusal and makes no packet.",
                    "/conflicts": "Usage: /conflicts | /conflicts on | /conflicts off\nConflict workbench (M-081): merge and rebase conflicts are presented as decisions — each conflicted place is decided ours, theirs, both, or edited — with both sides' intent summarised from the actual commits and diffs (the commit subject and author, and the lines each side added and removed against the common base), never invented. Every place must be decided, resolved text still carrying a conflict marker is refused, and the chosen resolution is written through the edit journal, staged so git records it resolved, re-checked against the real index, and recorded on the session journal. The gate ships on; /conflicts off refuses resolutions through the agent until it is turned back on.",
                    "/hunkreview": "Usage: /hunkreview | /hunkreview on | /hunkreview off\nHunk-level review (M-074): a unified diff is split into its hunks and each hunk is accepted, rejected, or edited on its own. Rejecting one hunk never kills the rest — the accepted hunks are applied through the same strict applier as any diff (every hunk's context must match the file exactly; no fuzz, ever) and the rejected hunks are simply left out. An edit may change what a hunk becomes, never what it matches: its context and removed lines stay exactly as proposed, and the edited hunk is re-judged by the same strict rules before it applies. Every hunk must be decided before anything applies — nothing is accepted or dropped by default — and the whole review, with each hunk's decision, is recorded on the session journal. The gate ships on; /hunkreview off refuses reviewed applies through the agent until it is turned back on.",
                    "/changeset": "Usage: /changeset | /changeset on | /changeset off\nMulti-file change sets (M-084): a change set is a named, reviewable unit across files — one edit per file, each in a concrete edit format, each accepted or rejected on its own before anything applies. Rejecting one file never kills the rest. The whole set is judged in memory first through the same strict appliers as any single edit (exact matches only, no fuzz, ever): one stale file refuses the whole set and nothing is written; accepted edits are written through the edit journal under the set's name. The set carries its test evidence as data — the command that ran, the passed, failed, and skipped counts, and where the log lives — with the verdict computed from the counts; a set with no evidence attached says so plainly. The gate ships on; /changeset off refuses set applies through the agent until it is turned back on.",
                    "/rename": "Usage: /rename | /rename on | /rename off | /rename <old-path> <new-path>\nRename/move files as first-class edits (M-085): a rename is an edit with a name — the file moves by git mv so its history is preserved, and every file the Part III symbol graph says references the old path or module name is updated by exact-token replacement through the edit journal. The plan is computed whole in memory first; a destination that already exists, a missing source, or a move onto itself refuses and nothing moves. Graph-named files whose text holds no exact token are named as warnings, never silently passed over. The gate ships on; /rename off refuses moves through the agent until it is turned back on.",
                    "/generated": "Usage: /generated | /generated on | /generated off | /generated <path> | /generated mark <path> <generator>\nGenerated-code honesty (M-086): a generated file says so on its face - an explicit marker in its first lines - and that marker is read, never guessed: the generator it names is recorded exactly, and a marker naming none records the generator honestly as unknown. A hand-edit to a generated file, assessed through the agent save road, warns before saving - naming the generator and stating that the next regeneration will overwrite the edit. Marking writes one header line in the file comment style through the edit journal; a file already marked is never marked twice, and a conflicting generator name refuses. The gate ships on; /generated off suppresses the warnings (never the classification) until it is turned back on.",
                    "/largefile": "Usage: /largefile | /largefile on | /largefile off | /largefile <path>\nLarge-file and binary care (M-087): a file is judged once, from its true bytes - binary or text, small or large - and the judgement explains itself, naming the file's size, the limit it was judged against, and the road that applies. Binaries are never text-edited, whatever the gate says: the refusal holds with the care off. A text file over the whole-file limit is edited by anchored chunks only - each chunk carries the SHA-256 of its exact text, and a chunk edit whose anchor no longer matches refuses, naming both anchors, and writes nothing. Through the agent save road a binary refuses before any byte moves and a large file warns onto the chunk road. The gate ships on; /largefile off closes the chunk road through the agent until it is turned back on.",
                    "/stash": "Usage: /stash | /stash on | /stash off | /stash shelve <name> | /stash restore <name> | /stash drop <name>\nThe stash shelf (M-088): work-in-progress is shelved by name - the difference between the working tree and its base is captured under the name you choose, and the tree goes back to its base. A shelved entry restores in any later session: if a path it touches has moved since the shelve, the restore refuses and names every conflicted path, unless the moved changes are discarded on purpose through the agent road. The shelf itself is an append-only journal of checksummed records on disk, so it survives crashes; a torn or corrupted line is counted and skipped, never silently applied. Shelving nothing refuses, and names on the shelf are unique. The gate ships on; with /stash off, shelving and restoring through the agent refuse while the shelf stays readable.",
                    "/patch": "Usage: /patch | /patch on | /patch off | /patch export <set name> | /patch import <patch file>\nPatch export/import (M-089): a reviewed change set (M-084) becomes one portable patch file - a magic line, a checksummed evidence header naming every accepted file with its format, byte count and content anchor and every rejected file named as rejected, then each accepted payload byte-exact under its own length head. Import proves the checksum and every anchor before trusting a payload, rebuilds the set through the change-set roads, and judges it against the receiving tree through the same strict appliers as any edit: one stale file refuses the whole import and nothing is written. Only a fully decided set exports. The agent layer holds no stored change sets, so /patch export names that plainly and exports nothing - export runs through the agent road with the set itself. The gate ships on; /patch off refuses exports and imports through the agent until it is turned back on.",
                    "/editor": "Usage: /editor | /editor on | /editor off | /editor file <path> | /editor prompt\nEditor bridges lite (M-090): text about to be used - a file, a prompt draft, the text at an approval point - can take a round-trip through your own editor instead of being typed here. The editor is resolved VISUAL first, then EDITOR, split the way a shell splits it so 'code --wait' works as written; with neither set the bridge refuses and names the remedy, no editor is ever guessed. The text travels to a scratch file (a real file keeps its own suffix, a prompt travels as .md prose) and what comes back is judged by its SHA-256 content anchor: byte-identical is unchanged and writes nothing, changed file text is written through the edit journal, an emptied file refuses rather than silently truncating it, and an emptied prompt is a cancellation, never sent. This surface holds no draft, so /editor prompt names that plainly - a prompt round-trip runs through the agent road with the draft itself. The gate ships on; /editor off refuses round-trips through the agent until it is turned back on.",
                    "/diff": "Usage: /diff | /diff on | /diff off | /diff unified | /diff side-by-side | /diff whitespace | /diff whitespace off\nDiff theatre in the TUI (M-091): one change staged two ways - unified, one column in order, or side-by-side with the before and after facing each other - with the words that actually changed picked out inside a changed line. A whitespace toggle judges lines that differ only in whitespace as unchanged and flags them as whitespace-only on the line, never hiding them and never counting them as change. Colour is never the only signal: every line carries its written sign (+ added, - removed, blank for unchanged) and every view opens with a counted header. The gate ships on; /diff off refuses staging through the agent until it is turned back on.",
                    "/blame": "Usage: /blame | /blame on | /blame off | /blame <path> | /blame <path> <line> | /blame <path>:<line>\nBlame and history sight (M-092): ask why a line is the way it is, and two records answer together. Git blame - read from its porcelain form, never guessed - names the commit that last touched the line: its author, its date, its summary, the line itself. The tool's own journal is then matched against the same file and line: an entry that names the file and covers the line names the session that wrote it, and where no record reaches the line the answer says blame alone speaks - a session is never guessed. A line the working tree has not committed blames to no commit at all and is flagged as uncommitted, never dressed up as history. The gate ships on; /blame off refuses sight through the agent until it is turned back on.",
                    "/massedit": "Usage: /massedit | /massedit on | /massedit off\nGuarded mass edits (M-093): a repo-wide edit is first shown whole, as a dry-run report - every file it would touch, the hunks and added and removed lines a real diff counts, and the risks the texts themselves carry (binary content, a file emptied, a very large file, many hunks, a sensitive path). Nothing moves on the strength of the report alone: a plan that changes two or more files, or any file at high risk, needs an approval first, and the approval is bound to the report's exact fingerprint - change one byte afterwards and the approval no longer covers the plan. Approved edits land through the edit journal, one journaled write per changed file; a file proposed unchanged is listed as no change and never counted. The gate ships on; /massedit off refuses mass applies through the agent until it is turned back on.",
"/sandbox": "Usage: /sandbox | /sandbox on | /sandbox off | /sandbox truth | /sandbox plan <command> | /sandbox plan <platform> -- <command>\nThe OS sandbox (M-097): commands run under native OS confinement - Linux namespaces via unshare with a seccomp allowlist as plan data, macOS sandbox-exec with a deny-default profile, Windows Job Objects through a native helper still owed - never Docker, ever. The truth table claims proven nowhere: linux is limited (the namespace road is measured on this box; the seccomp filter is rendered as data, not installed, and no confinement run is claimed proven), macos is planned, windows is limited with no confined argv yet. With the gate off, commands take the elder Sandbox guardrail road unchanged and runs say so; a plan that confines nothing reports confined=False honestly, and requiring confinement on such a platform refuses.",
                                        "/network": "Usage: /network | /network on | /network off | /network list | /network check <tool> <host-or-url> | /network allow <tool> <domain>\nNetwork gates (M-098): outbound network is gated per tool and per domain - a tool may reach only the domains its allowlist entries name (a plain domain matches that host exactly; a *.domain matches subdomains at any depth but never the base host itself), everything else is refused by default, fail-closed, and an empty allowlist refuses every reach. Every refusal is surfaced as news - a network_refusal session event naming the tool, the host and the reason - never just a log line. Adding an entry and turning the gate on or off are journaled first, and a failed save restores the previous gate and allowlist exactly. With the gate off, denied reaches are not published as refusals and the status screen says the gate is off plainly. This layer holds the allowlist and decides; it opens no socket itself. The gate ships on.",
                                        "/pathjail": "Usage: /pathjail | /pathjail on | /pathjail off | /pathjail grants | /pathjail check <path> | /pathjail grant <abs-path>\nPath jail (M-099): file tools are confined to the workspace plus named grants - a path is allowed only when, after every symlink on it is resolved, it lands inside the workspace or inside a granted directory; everything else is refused by default, fail-closed, and an escape hidden behind a symlink is caught by resolving it, never assumed away. Every refusal is surfaced as news - a path_jail_refusal session event naming the resolved path and the reason - never just a log line. Adding a grant and turning the gate on or off are journaled first, and a failed save restores the previous gate and grants exactly. With the gate off, denied paths are not published as refusals and the status screen says the gate is off plainly. This layer judges paths; it opens no file itself. The gate ships on.",
                                        "/plan": "Usage: /plan | /plan on | /plan off | /plan approve | /plan build | /plan check <read|write|execute>\nPlan mode (M-100): a read-everything, write-nothing posture - while it is on, read effects are allowed and write and execute effects are denied, the plan it produces is an ordered list of slices, each with a title, an intent, and acceptance checks, in Part IX form, and approving that one plan is the only gate to building. Every refusal is surfaced as news - a plan_mode_refusal session event - never just a log line. Turning the gate on or off is journaled first, and a failed save restores the previous setting exactly. With the gate off, building is the normal posture and denied decisions are not published as refusals. This layer holds the current plan and judges effects and builds; it writes nothing itself. The gate ships off.",
                                        "/hooks": "Usage: /hooks | /hooks list | /hooks show | /hooks show <event> | /hooks check <event>\nHooks (M-101): user scripts the lifecycle runs at seven events - pre_tool, post_tool, pre_edit, post_edit, on_test, on_commit and on_session. Each run is judged mechanically from its exit code and JSON output alone: exit 0 allows, exit 2 blocks, a JSON record saying block blocks at any exit code, and any other failure is an error - blocking before the act (pre_tool, pre_edit) or at a gate (on_test, on_commit), news only after it (post_tool, post_edit, on_session). Every block is surfaced as news - a hook_block session event carrying the reason the coder must answer - never just a log line. /hooks check <event> runs that event's enabled hooks for real, in configured order, each bounded by its own timeout; /hooks show lists what is configured and runs nothing. This layer holds no gate of its own: the hooks list itself is the setting.",
                                        "/hookpacks": "Usage: /hookpacks | /hookpacks list | /hookpacks show | /hookpacks show <pack> | /hookpacks install <pack>\nHook packs (M-102): the house hooks shipped as installable packs - each pack a named, described set of hooks from the hooks lifecycle (M-101), validated through that layer. The shipped shelf holds three packs: tests_after_edits runs the test suite after edits, readme_guard guards the README with read-only checks only (the guard never modifies a README), and verify_pushes verifies the work at commit time before it can be pushed. /hookpacks shows the shelf and runs nothing; /hookpacks install <pack> folds the pack hooks into the configured hooks under the hooks setting - journal-first, storing plain hook records - and installing is idempotent: a pack already fully installed changes nothing and writes nothing. This layer validates and formats only; it runs no script itself.",
"/background": "Usage: /background | /background list | /background show [<job>] | /background tail [<job>] | /background kill <job> | /background start <command...>\nBackground tasks (M-103): long commands run as managed jobs - a command given as a list of words, never a shell string, with a lifecycle of queued, running, then completed, failed or cancelled. /background shows the held jobs; show names one job; tail shows the bounded live tail of one job (the newest job when no id is named) and counts the lines it dropped; start runs the command as a real subprocess with no shell, its output feeding the live tail as it arrives; kill records the kill request, terminates the real process, and cancels the job. When a job finishes, its completion is published as a background_job_completed session event - news, never just a log line. The registry is session state held by the agent; it is not a stored setting.",
"/keeper": "Usage: /keeper | /keeper show [<target>] | /keeper check | /keeper heartbeat <target>\nKeeper (M-104): the keeper pattern built in - work the session is watching (a background job from M-103, a crew member, any tracked task) is judged mechanically from the age of its last sign of life: younger than half its stall bound is active, older is quiet, at or past the bound is stalled. /keeper shows the held watches with their verdicts in words; check judges every watch now and acts - an owed intervention is published as a keeper_intervention session event, and a stalled background job is restarted for real while its restarts remain; when the restarts run out the stall is reported instead. heartbeat records a sign of life on one watch. Background jobs feed their watch heartbeats as they start, print, and finish. The registry is session state held by the agent; it is not a stored setting.",
"/schedule": "Usage: /schedule | /schedule show [<job>] | /schedule check\nScheduled work (M-105): cron-style jobs held as data for the session - what to run (a command as a list of words, never a shell string), when to run it (daily at a named time, weekly on a named weekday, or every so many minutes or hours), whether it is enabled, and its approval posture, the same approval lines as live work. /schedule shows the held jobs with their due state in words, judged against the recorded last run of each job; check judges every job now and acts - a due unattended job is carried out as a real background job through the M-103 road and its run is recorded, and a job that needs approval is published as due and waiting and never run. A due moment is published as a scheduled_job_due session event - news, never just a log line. The registry is session state held by the agent; it is not a stored setting.",
"/fleet": "Usage: /fleet | /fleet show [<task>] | /fleet verdict | /fleet resume\nHeadless fleet mode (M-106): the headless mythic run road grown for CI - many tasks held as data for the session, each what to run (a command as a list of words, never a shell string), in which repo, with the prompt the run names. /fleet shows the held tasks with their recorded verdicts and the fleet verdict with its honest exit code, in the run road's own mapping: 0 only when every task passed, 1 when a task ran and failed, 2 when a task errored or the fleet is unfinished - a failed task can never yield 0; verdict shows the fleet verdict alone; resume shows the resume plan from the recorded verdicts - what remains, what passed and will never run again, and what is held back until retrying failures is asked for. A fleet check carries the remaining tasks out as real background jobs through the M-103 road and judges each from its real ending; every completion is published as a fleet_task_completed session event - news, never just a log line. The registry is session state held by the agent; it is not a stored setting.",
"/budgets": "Usage: /budgets | /budgets show [<budget>] | /budgets check [<budget>]\nBudgets as guardrails (M-107): per-task or per-session budgets held as data for the session, each naming optional limits on tokens, cost, time and commands - a dimension with no limit named is unlimited and no default limit is invented. /budgets shows the held budgets with each verdict judged from its recorded usage reading, the used-of-limit amounts always stated in words; check judges the held budgets now against usage read from the real roads and acts - an exceeded budget pauses gracefully at this resting point and is published as a budget_paused session event, news, never just a log line, and never a mid-edit death. The registry is session state held by the agent; it is not a stored setting.",
"/halt": "Usage: /halt | /halt show [<halt>] | /halt pull [<target>]\nThe kill switch everywhere (M-108): one command halts the coder, the crew, background jobs and pending approvals, held as data for the session - a halt names its targets (all four by default, or one named target), who or what asked, and a reason, and is judged mechanically against what the session actually holds: a target is halted only when live work is held for it, a target whose work already finished is already stopped and never newly halted, a target holding nothing is nothing held, and a merely queued crew task is a plan, not held work. /halt shows the halts pulled with their verdicts; pull carries the halt out through the real roads - held background jobs are killed through the M-103 road and a running crew task on its backing job, the coder stops at the next runtime boundary on its own cancellation event, and a pending approval, which waits on that same event, is refused - and the pull is published as a kill_switch_pulled session event, news, never just a log line. The registry is session state held by the agent; it is not a stored setting.",
"/audit": "Usage: /audit | /audit show [<entry>] | /audit export\nAudit trail (M-109): every tool call, approval, edit and command in the journal, each stamped with its actor - the human, the coder, the crew or a hook - held as data for the session. /audit shows the trail in append order; show <entry> shows one entry; export renders the whole trail for review, naming every held entry with the counts by kind and by actor. The trail is append-only: an entry, once recorded, is never changed or removed, and every recorded entry is published as an audit_recorded session event, news, never just a log line. The registry is session state held by the agent; it is not a stored setting.",
"/secrets": "Usage: /secrets | /secrets show [<screening>] | /secrets check <file>\nSecret hygiene in action (M-110): the files screened this session, each verdict in words - clean, or commit refused with the secret pattern kinds named and the content never shown - held as data for the session. /secrets shows the screenings with every known secret pattern named; show <screening> shows one screening; check <file> screens one real file in the project now and holds its verdict. Files are also screened on the real commit road: a refused file refuses the whole commit and is published as a secret_refusal session event, news, never just a log line, and tool results pass through the hygiene redaction before they enter the transcript. The registry is session state held by the agent; it is not a stored setting.",
                                        "/doctrine": "Usage: /doctrine | /doctrine show [<judgement>] | /doctrine ladder | /doctrine check <command>\nDestructive-command doctrine (M-111): the commands judged this session, each judgement stating its rung and the approval it needs in words - reversible needs no approval, costly asks once before it runs, irreversible needs explicit approval naming every target first - held as data for the session. /doctrine shows the ladder, the held patterns and the judgements; show <judgement> shows one judgement; ladder shows the three rungs alone; check <command> judges one command now and holds its judgement. Real commands are judged on the run_command road as they run, and a costly or irreversible judgement is published as a destructive_act session event, news, never just a log line. The registry is session state held by the agent; it is not a stored setting.",
                                        "/rollback": "Usage: /rollback | /rollback show [<run>] | /rollback drills | /rollback run <drill>\nRollback drills (M-112): scripted disasters recovered in tests, held as data for the session - exactly three drills (a bad mass edit, a wrong branch push attempt, a corrupted session), each naming the recovery road it exercises over shipped machinery. /rollback shows the held results with every outcome stated in words; show <run> shows one run; drills shows the drill book alone; run <drill> names the one drill a run would exercise. A result is judged from the step count a real test run reported - recovered only when every step passed, never rounded up - and every judged run is published as a rollback_drill_run session event, news, never just a log line. The registry is session state held by the agent; it is not a stored setting.",
                                        "/multirepo": "Usage: /multirepo | /multirepo show [<set>] | /multirepo repos\nMulti-repo workspaces (M-113): several repos held under one session, each with its per-repo policy stated in words - its mode (read-only, ask, or trusted), the branch its work targets, and whether its changes require review - and the cross-repo change sets held with their decision counts. /multirepo shows the workspace and its sets; show <set> shows one set; repos shows the held repos alone. A cross-repo change is ONE change set on the M-084 machinery: every file in every repo is decided under one name and the set is planned whole, all-or-nothing - one undecided or stale file refuses the whole set for every repo - a repo the session does not hold refuses plainly, and a read-only repo refuses a change-set member at build time. Every held set is published as a multi_repo_change_set session event, news, never just a log line. The registry is session state held by the agent; it is not a stored setting.",
                                        "/remote": "Usage: /remote | /remote show [<plan>] | /remote targets\nRemote and SSH work (M-114): the targets held this session, each with its one connection stated in words - SSH, authenticating by the SSH agent, a key file or a password - its address, user and port, and the workspace root the project lives under on that machine - and the work plans held with their step counts. /remote shows the targets and their plans; show <plan> shows one plan; targets shows the held targets alone. A work plan is data: remote commands as argv word lists (never a shell string, the M-103 rule) and file operations (read, write, edit, list) against the remote root - there is no download or copy operation, because files stay on that machine. A plan is judged whole against its target before anything could run: an unknown target, a step outside the remote workspace root, or a file operation that would copy a file back to this machine all refuse plainly. Every judged plan is published as a remote_work_plan session event, news, never just a log line. The registry is session state held by the agent; it is not a stored setting.",
                                        "/grace": "Usage: /grace | /grace show [<record>] | /grace failures\nOffline and degraded grace (M-115): the degradation records held this session, each stating its state in words - full, degraded or unknown - with every failure named and everything it lost stated plainly, and what still stands. /grace shows the held records; show <record> shows one record; failures shows the three failure kinds alone, each with what it loses. A record is judged from evidence only: full is claimed only when the provider, the language server (LSP) and the network all affirmatively answer; a dimension whose evidence is unknown is named unknown, never guessed up or down; and one failure never invents another. Every judged assessment is published as a degradation_change session event, news, never just a log line. The registry is session state held by the agent; it is not a stored setting.",
                                        "/moment": "Usage: /moment | /moment show [<record>] | /moment parts\nApproval by phone-sized moments (M-116): the approval moments held this session, each a single, complete question with full context - what is asked, where it acts, and what it does - and each choice saying what choosing it does, so the whole ask can be answered with one tap. /moment shows the held moments; show <record> shows one moment; parts shows the parts a complete moment must carry alone. A moment missing any part is judged incomplete and the missing parts are named - completeness is derived from the moment given, never invented. Every judged moment is published as an approval_moment session event, news, never just a log line. The registry is session state held by the agent; it is not a stored setting.",
                                        "/policy": "Usage: /policy | /policy show | /policy plan | /policy sections | /policy apply\nPolicy as code (M-119): one checked-in file (mythic-policy.yaml at the repo root) carries a team's rules - the permission posture, the path jail and its grants, and the hooks - in the exact shapes the shipped roads consume. /policy shows the current policy state; plan shows the data-only application plan for the file on disk, applying nothing; sections names the sections the file carries; apply loads the file and applies its plan in a fixed order - posture, jail and grants, hooks - each step through its own journal-first setting road, with each step outcome recorded. The policy is loaded at session start and the applied policy is published as a project_policy session event, news, never just a log line. No file means no policy - never an invented default - and a file that fails validation is refused whole with the validator reason, applying nothing. A checked-in policy may never turn the path jail off. The registry is session state held by the agent; the settings it sets are the shipped permission_profile, path_jail, path_grants and hooks settings.",
                                        "/crew": "Usage: /crew | /crew show [<member>] | /crew office <office>\nAgents as files (M-121): the crew held as data - one record per member naming its name, the office it holds, its model route (or the session default), the tools it works with, the posture it works under and the character file that carries its voice - the shipped casting being the existing characters, and new members arriving as records in a file, not code. /crew shows the crew held this session (the shipped casting when none is held); show <member> shows one member; office <office> shows the member holding one office. A held member spawns through the shipped sub-agent road - fed its name, its M-029 office route and its record posture - and every member that joins is published as a crew_member session event, news, never just a log line. The spawn road only spawns names the session carries as sub-agent entries, so a member that arrived as a file alone cannot be spawned from its record alone. The registry is session state held by the agent; it is not a stored setting.",
                                        "/offices": "Usage: /offices | /offices show [<office>] | /offices handoffs <office> | /offices contract <from> <to> | /offices custom [show [<office>] | handoffs <office> | contract <from> <to>]\nThe six offices formalised (M-122): Skald (intent & vision), Architect (design), Forge Worker (build), Auditor (verify), Cartographer (map & research) and Scribe (memory & docs) - each held as data with its duties, its tools, what it takes in and produces, and its hand-off contracts - every office a shipped role-routing office, its tools exactly the M-121 casting tools for that office; the shipped polymath and guardian offices are not among the six and are not formalised here. /offices shows the offices held this session (the shipped book when none is held); show <office> shows one office; handoffs <office> shows one office hand-off contracts; contract <from> <to> shows the one contract between two offices. Every office taken up for the session is published as an office session event, news, never just a log line. /offices custom shows the user-defined custom offices (M-123) on the same grammar over the custom parser - the shipped custom book holding the roadmap's Gatekeeper and Benchmarker examples when none is held - and every custom office taken up is published as a custom_office session event; a custom office is user-defined, not formalised and never a cast member, so nothing on this surface spawns. The registry is session state held by the agent; it is not a stored setting.",
                                        "/dealing": "Usage: /dealing | /dealing show [<member>] | /dealing plan | /dealing loads\nTask dealing (M-125): a plan's slices are dealt to the crew by office fit and current load - a slice goes first to a member holding the office its work fits, and among equally fitting members to the least loaded, casting order breaking ties - and every dealt slice records the load its member holds after the deal; the human may re-deal any slice to another member of the casting. /dealing shows the assignments dealt this session (the shipped example dealing - the next ten roadmap slices, M-125 to M-134, dealt to the M-121 casting - when none is held); show <member> shows one member's assignments; plan shows the whole plan with its dealer; loads shows the whole crew's loads from what the session holds. Every assignment dealt for the session is published as a task_dealing session event, news, never just a log line. There is no Part VIII board yet: the dealing is visible on this surface, not on a board. This layer deals as data only: it starts no crew and spawns nothing. The registry is session state held by the agent; it is not a stored setting.",
                                        "/comms": "Usage: /comms | /comms show [<member>] | /comms ask | /comms kinds\nCrew comms (M-126): members hand structured hand-offs to each other - findings (what a member found), a diff (a change handed over), or a question (for its recipient) - each naming its sender, its recipient, the slice it belongs to, a title and a body, all validated as data. A member's question to the human is batched and asked once, with full context: every waiting question gathered in hand-off order into ONE human_question_batch session event, never asked piecemeal. /comms shows the hand-offs held this session (the shipped example ledger - six hand-offs among the M-121 casting, three of them questions to the human - when none is held); show <member> shows one member's hand-offs, and show human shows the hand-offs addressed to the human; ask shows the one batched ask; kinds shows the three kinds. Every hand-off handed for the session is published as a crew_handoff session event, news, never just a log line. There is no Part VIII board yet: the hand-offs and the batch are visible on this surface, not on a board. This layer holds hand-offs as data only: it spawns no crew and delivers no message. The registry is session state held by the agent; it is not a stored setting.",
                                        "/deadlock": "Usage: /deadlock | /deadlock show [<member>] | /deadlock kinds\nCycle and deadlock detection (M-127): the coordinator's watch over the crew, as data - a delegation (a delegator member, a delegatee member, the slice delegated) and a claim (a member, the slice it holds, the path it holds it at) - from which the findings are derived mechanically, never stored: a delegation_cycle (a chain of delegations looping back to its start, each member waiting on the next - a deadlock), a merge_conflict (two different members holding the same path) and duplicated_work (two different members holding the same slice); one member's own repeated holdings are never flagged. /deadlock shows the findings of the watch held this session (the shipped example watch - five delegations and five claims among the M-121 casting, kept by the guardian, yielding exactly three findings, one of each kind - when none is held); show <member> shows one member's findings; kinds shows the three kinds. Every delegation or claim held for the session is published as a crew_delegation / crew_claim session event, every finding as a deadlock_finding session event, and every report as ONE deadlock_report session event holding every finding, news, never just a log line. There is no Part VIII board yet: the findings are visible on this surface, not on a board. This layer holds the watch as data only: it spawns no crew, stops no member and runs no git - the coordinator acts on the findings through later roads. The registry is session state held by the agent; it is not a stored setting.",
                                        "/merge": "Usage: /merge | /merge show [<member>] | /merge lines | /merge kinds\nMerge discipline (M-128): the merging of member branches, as data - a step (a member, the slice it merges, the branch it merges from) and a recorded merge (a member, a slice, a branch, the test gate recorded at the merge and the outcome, green or red) - from which the verdicts and every line state are derived mechanically, never stored: an out_of_order merge (attempted out of its line slice order, or for a slice its line never planned) is refused and advances nothing, a missing_test_gate merge (a failed or missing gate) is flagged and advances nothing, and a line_stopped verdict marks a red merge stopping only its own line at that slice while every other line keeps merging. /merge shows the verdicts of the plan held this session (the shipped example plan - seven steps and five merges among the M-121 casting, kept by the forge_worker, yielding exactly three verdicts, one of each kind - when none is held); show <member> shows one member verdicts; lines shows every line state; kinds shows the three kinds. Every step or merge held for the session is published as a merge_step / merge_attempt session event, every verdict as a merge_verdict session event, and every report as ONE merge_report session event holding every verdict and line, news, never just a log line. There is no Part VIII board yet: the verdicts are visible on this surface, not on a board. This layer holds the merging as data only: it executes no git, performs no real merge and spawns or stops no crew - the coordinator acts on the verdicts through later roads. The registry is session state held by the agent; it is not a stored setting.",
                                        "/hetero": "Usage: /hetero | /hetero show [<member>] | /hetero routes | /hetero kinds\nHeterogeneous crews (M-129): the crew members riding different models on different providers, as data - an assignment (a member, a provider, a model, and the budget it rides under), the Part V budgets composed from M-107 and the usage readings - from which the verdicts and every route state are derived mechanically, never stored: an unknown_route assignment (the provider does not list the model it names, per the M-019 registry), a missing_budget assignment (it names no budget this plan holds), and an over_budget member (its reading judged exceeded by the M-107 budget judge). Route states carry the M-019 locality and dialect, the M-028 switchable reading, and the M-027 capability truth - a model context is known or honestly unknown, never guessed. /hetero shows the verdicts of the crew plan held this session (the shipped example plan - four assignments, two budgets and two readings among the M-121 casting, kept by the architect, yielding exactly three verdicts, one of each kind - when none is held); show <member> shows one member verdicts; routes shows every route state; kinds shows the three kinds. Every assignment or reading held for the session is published as a hetero_assignment / hetero_reading session event, every verdict as a hetero_verdict session event, and every report as ONE hetero_report session event holding every verdict and route, news, never just a log line. There is no Part VIII board yet: the verdicts are visible on this surface, not on a board. This layer holds the crew as data only: it spawns no live crew, calls no real provider and performs no routing or billing - the coordinator acts on the verdicts through later roads. The registry is session state held by the agent; it is not a stored setting.",
                                        "/veto": "Usage: /veto | /veto show [<slice>] | /veto gates | /veto kinds\nThe Auditor's veto (M-130): no slice is done until the Auditor's checks pass, as data - a case (one slice standing before the Auditor, with its title and its builder), the checks each slice carries (required or not), and the results (what the Auditor's run of each check found, passed or failed, with the evidence for it) - from which the verdicts and every gate state are derived mechanically, never stored: a failed_check veto (a required check the slice carries was run and the Auditor's result says it failed) and an unproven_check veto (a required check holds no result at all - a check with no evidence has not passed). A check that is not required never vetoes, and passing is a gate state, not a verdict: a slice passes exactly when every required check it carries holds a passing result. /veto shows the verdicts of the ledger held this session (the shipped example ledger - three cases, six checks and five results among the Part VI slices, kept by the auditor, yielding exactly two verdicts, one of each kind, with M-128 passed - when none is held); show <slice> shows one slice's verdicts; gates shows every case's gate state; kinds shows the two kinds. Every case, check or result held for the session is published as a veto_case / veto_check / veto_result session event, every verdict as a veto_verdict session event, and every report as ONE veto_report session event holding every verdict and gate, news, never just a log line. There is no Part VIII board yet: the verdicts are visible on this surface, not on a board. This layer holds the audit as data only: it runs no check, executes no test suite and banks nothing - the coordinator acts on the verdicts through later roads, and the banking road that will refuse a vetoed slice in code is a later slice (M-205 / M-206), not this one. The registry is session state held by the agent; it is not a stored setting.",
                                        "/swarm": "Usage: /swarm | /swarm show [<member>] | /swarm digest | /swarm sources | /swarm kinds\nResearch swarms (M-131): a Cartographer-led fan-out for questions, as data - a question (the question asked, and the member who leads the swarm), an assignment (one member dealt one focus of the question - the docs, the options or the comparison - with the brief they were dealt), and a finding (what one member's reading found, in plain words, with the sources it stands on) - from which the digest is derived mechanically from the findings alone, never stored: the answer joins the findings' summaries in assignment order, the sources are every source the findings cite, each once, in citing order, and the digest is complete exactly when every assignment holds a finding; an assignment whose member returned nothing is named in the digest as still out, never dropped, and a finding from a member who holds no assignment refuses. /swarm shows the swarm held this session (the shipped example swarm - one cartographer-led question, three assignments and three findings, yielding one complete digest on three sources - when none is held); show <member> shows one member's finding; digest shows the digested answer with its sources; sources shows the digest's sources; kinds shows the three focus kinds. Every question, assignment or finding held for the session is published as a swarm_question / swarm_assignment / swarm_finding session event, and every digest report as ONE swarm_digest session event holding the whole digested answer, news, never just a log line. There is no Part VIII board yet: the digest is visible on this surface, not on a board. This layer holds the swarm as data only: it runs no research, calls no model, opens no page and spawns no crew - the findings arrive through later roads. The registry is session state held by the agent; it is not a stored setting.",
                                        "/panel": "Usage: /panel | /panel show [<reviewer>] | /panel outcome | /panel verdicts | /panel kinds\nReview panels (M-132): one change put to two reviewers riding different models, as data - a change (the change under review, named and summarised in plain words), and a review (one reviewer's verdict - approve, request_changes or reject - the provider and model they rode, their notes in plain words and the concerns they name) - from which the outcome is derived mechanically from the two verdicts alone, never stored: two identical verdicts yield an agreed outcome naming the shared verdict, two differing verdicts yield a disagreement naming both positions - no middle verdict, no score, no tie-break - and fewer than two reviews yields awaiting, naming who has reported. No reviewer reads twice, no model is ridden twice, and a third review refuses. /panel shows the panel held this session (the shipped example panel - the session-branching restore guard, approved by the auditor on anthropic/claude-sonnet-4-5 and held to request_changes by the guardian on ollama/llama3.1, a disagreement surfaced - when none is held); show <reviewer> shows one reviewer's review; outcome shows the derived outcome with both positions named; verdicts shows the positions the panel holds; kinds shows the three verdict kinds. Every change or review held for the session is published as a panel_change / panel_review session event, and every outcome report as ONE panel_outcome session event holding the whole derived outcome, news, never just a log line. There is no Part VIII board yet: the outcome is visible on this surface, not on a board. This layer holds the panel as data only: it runs no review, calls no model, executes no change and spawns no crew - the reviews arrive through later roads. The registry is session state held by the agent; it is not a stored setting.",
                                        "/worktrees": "Usage: /worktrees | /worktrees show [<member>] | /worktrees plan | /worktrees merges\nParallel worktrees (M-124): each building crew member works in its own git worktree on its own branch - never two writers in one tree - and the coordinator, who holds no worktree of their own in the plan, is the only one who merges; a plan holds one assignment per member (the member, the office it holds, the slice it builds, its branch and its worktree path), and a duplicated member, branch or path refuses whole. /worktrees shows the assignments held this session (the shipped example plan - the M-121 casting dealt one worktree each, slices M-124 to M-131 - when none is held); show <member> shows one member's assignment; plan shows the whole plan with its coordinator; merges shows the merge plan derived from the assignments in slice order, every step merged by the coordinator. Every assignment taken up for the session is published as a worktree_assignment session event, news, never just a log line. This layer holds plans and assignments as data only: it runs no git command, creates no worktree and spawns nothing. The registry is session state held by the agent; it is not a stored setting.",
                                        "/remember": "Usage: /remember | /remember list | /remember forget <id> | /remember clear\nRemembered approvals (M-096): a standing answer with an exact scope - this command, with these arguments, in this project. It is created only when you say so out loud at the approval prompt (nothing is remembered silently, and /remember itself never creates one), it is listed in one screen with the id each entry is revoked by, and anything outside the exact scope is asked afresh. A remembered run_command whose command, arguments and project match exactly is allowed without asking again; forget and clear are journaled first, and a failed save preserves the list exactly.",
                    "/posture": "Usage: /posture | /posture <profile name> | /posture custom <name> | <title> | <tools> | <paths> | <network> | <commands>\nPermission profiles (M-095): the session works under one named posture - Read-Only Scout (read-only tools, read paths, network and commands denied), Trusted Forge (all tools, write paths, network and commands ask first - the default), Full Autonomy (all tools, write paths, network and commands allowed), or a custom posture validated to the same four bindings. The posture is always visible: its one sentence rides the status line, rendered from the profile itself. Changing the posture is journaled first, rebuilds the live tool policy in the new posture's mode, and a failed save restores the previous posture exactly. An unknown name refuses plainly and lists the shipped postures.",
                    "/issueslice": "Usage: /issueslice | /issueslice on | /issueslice off | /issueslice github <number>\nIssue-to-slice (M-083): a GitHub issue becomes a planned slice — title, summary, and acceptance checks in the roadmap slice's shape, with status planned. Every check is drafted from the issue's own words (a task-list item, a bullet under its acceptance heading, or its title) and keeps the exact words it came from; nothing is invented. The source is a seam: GitHub fetches through the gh road today; the Samverk source is named for Part X (M-242) and refuses honestly until that road provides the surfaces. Planning files nothing and is recorded on the session journal. The gate ships on; /issueslice off refuses planning through the agent until it is turned back on.",
                    "/prcraft": "Usage: /prcraft | /prcraft on | /prcraft off | /prcraft tasks <pr-number>\nPR craft (M-082): pull requests are created, reviewed, and answered from inside Mythic. A pull request is fetched as data and its review comments are fetched and turned into tasks — one task per comment, carrying its author, words, and place. Drafts are prepared locally and send nothing: a PR draft, a review draft (approve, comment, or request changes, with line notes riding in the review body), and a reply draft. Anything that would send as you posts only at your word: the draft must carry your own recorded word before the post road runs at all, and with no word recorded the post refuses and nothing is sent. The gate ships on; /prcraft off refuses fetches and posts through the agent until it is turned back on.",
                    "/commitcraft": "Usage: /commitcraft | /commitcraft on | /commitcraft off | /commitcraft plan | /commitcraft commit <concern> | /commitcraft push\nCommit craft (M-080): a working-tree change is split into commits by concern — code, tests, docs, and config land separately — and each message is drafted from its own actual diff. Pushing follows the house rules, wired in as refusals: fetch first, read the remote-diff, never force-push (a diverged remote refuses), and verify with ls-remote afterwards that the remote moved to the pushed head. Commit craft never commits on its own; the auto-commit trigger is M-078's seam, banked and reported honestly through it. The gate ships on; /commitcraft off refuses commits and pushes through the agent until it is turned back on.",
                    "/checkpoint": "Usage: /checkpoint | /checkpoint take <name> | /checkpoint restore <name> [discard] | /checkpoint on | /checkpoint off\nNamed checkpoints (M-075): take captures the whole working tree plus the current session state under a name you choose (before the auth rework); restore brings that tree and session back in one command. Checkpoints form a tree — each new one hangs from the one that was current when it was taken, and restoring an older checkpoint and taking a new one from there grows a branch; /checkpoint shows the whole tree, the journal view. Restore judges a dirty tree honestly: if the tree has changed since the last checkpoint was taken or restored, restore refuses and names the changed files — take a checkpoint of the current tree first, or restore with discard to throw those changes away on purpose. Session state returns only to the session it was captured from. The gate ships on; /checkpoint off refuses takes and restores through the agent until it is turned back on.",
                    "/branch": "Usage: /branch | /branch on | /branch off | /branch fork <message-index> [name] | /branch list | /branch compare <session-id> <session-id>\nSession branching (M-076): fork a session at any message — try the other road from here. The branch is a new session whose history is the parent's history up to and including the fork message, copied exactly; from there the two sessions are independent, and neither one's later messages ever touch the other. Every branch records its lineage — parent, fork message, root session — in its metadata, inside the frozen v1 session format, so any v1 reader still reads it. /branch compare names the messages two sessions share, the first message where they diverge, and each side's own messages after that point. The gate ships on; /branch off refuses forks through the agent until it is turned back on, while comparing and listing stay available.",
                    "/autocommit": "Usage: /autocommit | /autocommit on | /autocommit off | /autocommit allow-protected | /autocommit block-protected\nAuto-commit discipline (M-078): every accepted edit set lands as its own commit with a written message — one edit set, one commit, carrying exactly the accepted files. By default the commit lands on a working branch: on a protected branch (main, master, development, develop, and any you name in auto_commit_protected) the edits are moved onto the working branch (mythic/working unless you name another) and committed there, never onto the protected branch itself. Committing onto a protected branch takes your explicit standing word (/autocommit allow-protected), and a commit that lands there is recorded as on-protected. A blank message, an empty file set, or a detached head refuses and commits nothing. The discipline ships off; /autocommit on is the standing word that accepted edit sets land as commits.",
                    "/kista": "Usage: /kista | /kista adopt | /kista adopt <base-url>\nKey custody via Kista (M-032): providers read their keys from Kista, your own credential keeper; config files hold references (kista:<name>), never secrets. /kista shows, for every door, where its key lives and whether one is held — never a key value. /kista adopt moves a door's stored plain-text key into Kista's vault file (named by MYTHIC_KISTA_FILE) and leaves only the reference in the config, recorded as a session journal event. A missing key asks once, kindly, naming the reference to add.",
                    "/resume-thought": "Usage: /resume-thought | /resume-thought resume | /resume-thought show\nStreaming discipline (M-034): when a streaming answer is interrupted, the words it managed to say are kept in the conversation as a partial answer, clearly marked as not complete — never silently dropped, never presented as finished, and a killed stream never corrupts the journal. /resume-thought show says whether a partial is waiting (plainly, when none is). /resume-thought asks the model to continue from exactly where the partial stopped, without repeating what was already said — only where the current model's streaming ability is known to support resuming (M-027 capability truth); otherwise it refuses plainly, with the reason, and the partial stays in the conversation.",
                    "/retry": "Usage: /retry | /retry show\nRetry and backoff honesty (M-035): retries are bounded (the configured max_retries budget), only for temporary failures — a connection problem, or HTTP 408, 409, 429, or a 5xx status — and each retry is announced with its reason and its wait; why retrying stopped is recorded in the retry report. /retry shows the plain explanation, the named bounds (budget, waits, planned and worst-case wait totals), and the last request's report, or plainly that no provider request has been retried yet in this session. Mutating calls are never silently replayed: a retry repeats only a provider request that produced no usable response, streaming retries only before the first chunk, and a tool call executes exactly once after one returned response.",
                    "/weather": "Usage: /weather | /weather show\nRate-limit weather (M-036): Mythic remembers what each provider door has actually told it about its limits — a 429 answer, the quota headers the door itself sends, and successes — on one board the whole crew shares. /weather shows, per door, whether it is limited and until when, what quota the door reported, and what is simply unknown (unknown is not a limit and never blocks work). Before a request is sent to a door whose weather says limited until a known reset, the request is queued around the limit — held, announced, and cancellable, for at most 600 seconds; a longer or unknown reset is surfaced and the request proceeds to the retry and fallback machinery.",
                    "/vision": "Usage: /vision | /vision show | /vision switch\nVision input routing (M-037): image work is sent only to a model whose capability record (M-027) says it can see. /vision shows the current model's recorded sight truth — known to see, recorded as not able to see, or sight unknown — the doors you have set up whose models are known to see, and the switch on offer. When the current model is not known to see, image parts are refused before anything is sent: the refusal names the model and its record, is recorded as a session journal event, and is never a silent drop. /vision switch takes the offered switch to a configured known-seeing door through the journaled model switch. Text-only work is never gated.",
                    "/offline": "Usage: /offline | /offline show\nOffline honesty (M-040): the app reads the provider health board (M-039) and says plainly whether it is offline. It claims offline only when the board was actually probed and no door can serve — every local door unreachable, every remote door unreachable or missing its key, and no keyed door the board cannot probe still standing. The declaration is exact — no network route to a model, and no local model answering — and it names the non-model tools that still work: mythic review (static review), mythic metrics, and mythic sessions --search (session search). If any door answered, the app is online and says which doors answered; if the board was never probed or a keyed door's health is unknown to the board, the app claims nothing.",
                    "/testkit": "Usage: /testkit <provider> [base-url]\nNew-provider test kit (M-041): before a new registry entry ships, it must pass five checks proven against its door — the entry resolves and the universal adapter built from it matches it, a real chat answers, a forced tool call comes back when the door claims tool calling, a streamed reply yields text and ends when the door claims streaming, and a malformed request is answered with an error, never a success. A check the door does not claim is skipped with the reason, never passed silently; a door whose dialect the universal adapter cannot serve is NOT PROVEN, never passed. The verdict is passed only when nothing failed and chat was actually proven.",
                    "/map": "Usage: /map | /map <task words> | /map show <path> | /map pin <path> | /map unpin <path> | /map pins\nMap in the TUI (M-045): the repo map (M-044) made visible. /map browses the ranked files — pinned files first, then rank order — each with its true rank, its score, and the plain reasons the coder thinks it matters (its PageRank from the reference graph, the task symbols it matched, what it defines and references); /map <task words> ranks the map for that task. /map show <path> gives one file's full account — score arithmetic, definitions with their signature lines, references in and out, every reason — or its honest unmapped state (over the token budget, skipped with the build's reason, or absent). /map pin <path> pins a workspace file so it is shown first when browsing; a pin never changes a file's rank or score, and a pinned file the build left out is explained, never invented as an entry.",
                    "/ssearch": "Usage: /ssearch <language> <pattern>\nStructural search (M-047): find code by its shape, not its text — an ast-grep-style pattern written in the language itself, run over every file of that language in the workspace through the tree-sitter foundation (M-043). $NAME matches exactly one node and captures it; $$$ (or $$$NAME) matches zero or more sibling nodes and captures them when named; a metavariable used twice must capture the same text twice. Each match is listed with its place and its captures, and files that cannot be parsed are named as skipped, with the reason. A pattern that does not parse in its language is refused, never quietly text-searched instead; a language with no grammar (Mojo) is refused the same way. Search only — the rewrite that changes matched code is /srewrite (M-048).",
                    "/srewrite": "Usage: /srewrite [apply] <language> <pattern> => <replacement>\nStructural rewrite (M-048): the structural search patterns (M-047) as safe codemods. The replacement is written in the same pattern language; its $NAME / $$$NAME metavariables are filled with what the pattern captured at each site, and every site is shown with its own unified-diff preview before anything can be written. /srewrite previews only. /srewrite apply applies the plan through the edit journal, one journaled write per file, and only when the file is still exactly what the plan saw (its plan-time hash) — a file that changed since the plan is refused whole, and sites whose spans overlap another match (nested matches) are refused with the reason, never force-edited. A replacement that does not parse, names a metavariable the pattern never captured, uses an unnamed $$$, or mismatches a capture's kind is refused before anything is planned.",
                    "/lsp": "Usage: /lsp [show] | /lsp check <path> | /lsp def <path> <line> <character> | /lsp refs <path> <line> <character> | /lsp hover <path> <line> <character> | /lsp symbols [query]\nLanguage servers (M-049 diagnostics, M-050 navigation): /lsp shows the discovery board — every catalogued server with its installed state and, for a missing one, its install remedy. /lsp check <path> shows one file's diagnostics in the server's own words. /lsp def/refs/hover ask where a name at a 1-based line/character is defined, every place it is used, and what the server says about that spot; /lsp symbols lists the workspace's symbols. A server that is not installed is reported NOT CHECKED / NOT ANSWERED with the remedy — never as a clean file or a found answer.",
                    "/longcontext": "Usage: /longcontext | /longcontext show | /longcontext <model>\nLong-context strategy per model (M-038): how much of the repository is loaded for a model is chosen from that model's recorded context size (M-027 capability truth), never guessed. A model known to hold a million tokens or more loads map-first — the repo map leads, then broad file loading inside a quarter of the window. A model with a smaller known window leans on the repo map and retrieval — a sixteenth of the window (floored and capped), selection run harder than the default. When a model's context size is unknown, no strategy is claimed: the surface says so and the app uses its ordinary default budget on the retrieval road. /longcontext <model> previews another model's strategy without changing the session. An explicit budget passed to the context runtime always wins over the strategy's budget.",
                    "/clear": "Usage: /clear\nClears the agent's memory window (except the system prompt).",
                    "/compact": "Usage: /compact\nForces the LLM's context pruner to run early, archiving old messages to the VectorDB.",
                    "/cost": "Usage: /cost\nComputes and displays the token cost of the current session.",
                    "/review": "Usage: /review\nRuns `git diff` and injects the output into the agent's context for an autonomous code review.",
                    "/flirt": "Usage: /flirt <message>\nSpawns a temporary Ghost session to flirt with the current agent. Does not interrupt the agent's main workflow.",
                    "/lick": "Usage: /lick <message>\nSpawns a temporary Ghost session and explicitly sends the action *User licks you*. Fun alternative to /flirt.",
                    "/hug": "Usage: /hug <message>\nSpawns a temporary Ghost session and explicitly sends the action *User hugs you*.",
                    "/kiss": "Usage: /kiss <message>\nSpawns a temporary Ghost session and explicitly sends the action *User kisses you*.",
                    "/snuggle": "Usage: /snuggle <message>\nSpawns a temporary Ghost session and explicitly sends the action *User snuggles with you*.",
                    "/cuddle": "Usage: /cuddle <message>\nSpawns a temporary Ghost session and explicitly sends the action *User cuddles with you*.",
                    "/tickle": "Usage: /tickle <message>\nSpawns a temporary Ghost session and explicitly sends the action *User tickles you*.",
                    "/wink": "Usage: /wink <message>\nSpawns a temporary Ghost session and explicitly sends the action *User winks at you*.",
                    "/rose": "Usage: /rose <message>\nSpawns a temporary Ghost session and explicitly sends the action *User gives you a red rose*.",
                    "/mead": "Usage: /mead <message>\nSpawns a temporary Ghost session and explicitly sends the action *User gives you a drinking horn full of mead*.",
                    "/ale": "Usage: /ale <message>\nSpawns a temporary Ghost session and explicitly sends the action *User gives you a tankard of ale*.",
                    "/beer": "Usage: /beer <message>\nSpawns a temporary Ghost session and explicitly sends the action *User gives you a stein of beer*.",
                    "/cookies": "Usage: /cookies <message>\nSpawns a temporary Ghost session and explicitly sends the action *User gives you some cookies*.",
                    "/candy": "Usage: /candy <message>\nSpawns a temporary Ghost session and explicitly sends the action *User gives you a chocolate candy bar*.",
                    "/love": "Usage: /love <message>\nSpawns a temporary Ghost session and explicitly sends the action *User gives you positive love energy*.",
                    "/btw": "Usage: /btw <message>\nAdds context or notes to the agent via a Ghost session without forcing an immediate context break. Useful for side-chatter or corrections while it thinks.",
                    "/steer": "Usage: /steer <instruction>\nDirectly alters the ongoing task of the current active agent. Will immediately be appended to the active agent's prompt.",
                    "/stop": "Usage: /stop\nSends a kill signal to all currently active agents and subagents. Clears the background task queues.",
                    "/tutorial": "Usage: /tutorial\nDisplays a comprehensive guide to Vibe Coding and agent management.",
                    "/quit": "Usage: /quit\nImmediately terminates the Mythic Agent CLI interface."
                }
                
                if target_cmd in help_dict:
                    chat_log.write(f"\n[bold cyan]Help for {target_cmd}:[/bold cyan]")
                    chat_log.write(help_dict[target_cmd])
                else:
                    chat_log.write(f"[red]No detailed help available for {target_cmd}.[/red]")
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
                active = getattr(self.app, "active_chat_agent", "Primary")
                if "[Ghost]" not in active:
                    self.on_agent_selected(f"[Ghost] {active}")
                SecureAPI.publish_ghost_chat_request(f"By the way (for your context, no need to act on this alone unless asked): {args}", target_agent=active)
                chat_log.write(f"[magenta]Passed to ghost agent: {args}[/magenta]")
        elif cmd == "/steer":
            if not args:
                chat_log.write("[red]Usage: /steer <instruction>[/red]")
            else:
                # Steer explicitly still goes to the working original agent
                active = getattr(self.app, "active_chat_agent", "Primary")
                SecureAPI.publish_chat_request(f"USER STEERING INSTRUCTION (Priority): {args}", target_agent=active)
                chat_log.write(f"[bold yellow]Steering instruction applied: {args}[/bold yellow]")
        elif cmd in ["/flirt", "/lick", "/hug", "/kiss", "/snuggle", "/cuddle", "/tickle", "/wink", "/rose", "/mead", "/ale", "/beer", "/cookies", "/candy", "/love"]:
            active = getattr(self.app, "active_chat_agent", "Primary")
            is_busy = active in getattr(self, "active_subagents", [])
            
            if is_busy and "[Ghost]" not in active:
                self.on_agent_selected(f"[Ghost] {active}")
                
            action_text = {
                "/flirt": "*flirts with you*",
                "/lick": "*User licks you*",
                "/hug": "*User hugs you*",
                "/kiss": "*User kisses you*",
                "/snuggle": "*User snuggles with you*",
                "/cuddle": "*User cuddles with you*",
                "/tickle": "*User tickles you*",
                "/wink": "*User winks at you*",
                "/rose": "*User gives you a red rose*",
                "/mead": "*User gives you a drinking horn full of mead*",
                "/ale": "*User gives you a tankard of ale*",
                "/beer": "*User gives you a stein of beer*",
                "/cookies": "*User gives you some cookies*",
                "/candy": "*User gives you a chocolate candy bar*",
                "/love": "*User gives you positive love energy*"
            }[cmd]
            
            if is_busy:
                SecureAPI.publish_ghost_chat_request(f"{action_text} {args}", target_agent=active)
            else:
                SecureAPI.publish_chat_request(f"{action_text} {args}", target_agent=active)
            chat_log.write(f"[magenta]{action_text}[/magenta] {args}")
        elif cmd in ["/gh", "/status", "/commit", "/test", "/doctor", "/undo", "/issue", "/pr", "/stop", "/clear", "/compact", "/cost", "/review", "/ollama", "/local", "/gateway", "/model", "/route", "/fallback", "/costroute", "/editformat", "/hashanchor", "/repairloop", "/hunkreview", "/changeset", "/rename", "/generated", "/largefile", "/stash", "/patch", "/editor", "/issueslice""/editor", "/diff", "/blame", "/massedit", "/posture", "/remember", "/sandbox", "/network", "/pathjail", "/plan", "/hooks", "/hookpacks", "/background", "/keeper", "/schedule", "/fleet", "/budgets", "/halt", "/audit", "/secrets", "/doctrine", "/rollback", "/multirepo", "/remote", "/grace", "/moment", "/policy", "/crew", "/offices", "/worktrees", "/dealing", "/comms", "/deadlock", "/merge", "/hetero", "/veto", "/swarm", "/panel", "/issueslice", "/prcraft", "/conflicts", "/commitcraft", "/autocommit", "/guardians", "/checkpoint", "/branch", "/kista", "/resume-thought", "/retry", "/weather", "/vision", "/longcontext", "/offline", "/testkit", "/map", "/ssearch", "/srewrite", "/lsp"]:
            # M-023: /ollama rides this same system-command road — the
            # M-024: /local rides it too, for the same reason.
            # UI stays presentation-only (arch-conformance: no
            # providers.* imports here); the agents-layer
            # CommandHandler talks to the local Ollama server.
            SecureAPI.publish_system_command(cmd, args)
        else:
            chat_log.write(f"[red]Unknown command:[/red] {cmd}")


    def run_agent_query(self, user_input: str) -> None:
        self._set_loading(True)
        target_name = getattr(self.app, "active_chat_agent", "Primary")
        
        chat_log = self.query_one("#chat-log", RichLog)
        chat_log.write(f"[dim italic]→ Routing to {target_name}...[/dim italic]")
        
        SecureAPI.publish_chat_request(user_input, target_agent=target_name)

    @work(thread=True)
    def _transcribe_voice_task(self, wav_path: str) -> None:
        # Fix (S09): this runs on a worker thread — never touch widgets here.
        # Marshal the result back to the app thread with call_from_thread.
        from mythic_agent.core.audio import audio_recorder
        transcript = None
        error = None
        try:
            transcript = audio_recorder.transcribe(wav_path)
        except Exception as e:
            error = e
        self.app.call_from_thread(self._finish_voice_transcript, transcript, error)

    def _finish_voice_transcript(self, transcript, error) -> None:
        """Runs on the app thread; safe to query and update widgets."""
        chat_log = self.query_one("#chat-log", RichLog)
        if error is not None:
            chat_log.write(f"[red]Voice transcription error: {error}[/red]")
        elif transcript and transcript.strip():
            self._inject_voice_transcript(transcript.strip())
        else:
            chat_log.write("[dim]Could not transcribe audio or no speech detected.[/dim]")
        self.query_one("#prompt-label").update(" [bold yellow]ᛟ❯[/bold yellow] ")

    def _inject_voice_transcript(self, text: str) -> None:
        chat_log = self.query_one("#chat-log", RichLog)
        chat_log.write(f"\n[bold green]User (Voice):[/bold green] {text}")
        self.run_agent_query(text)

    def action_toggle_voice(self) -> None:
        from mythic_agent.core.audio import audio_recorder, HAS_AUDIO
        
        chat_log = self.query_one("#chat-log", RichLog)
        prompt_label = self.query_one("#prompt-label", Label)
        
        if not HAS_AUDIO:
            chat_log.write("[red]Audio dependencies (sounddevice) not available.[/red]")
            return
            
        if not audio_recorder.is_recording:
            if audio_recorder.start_recording():
                prompt_label.update(" [bold red]🎤 (F4 to stop)[/bold red] ")
                chat_log.write("[bold red]Recording started...[/bold red]")
        else:
            prompt_label.update(" [bold yellow]⏳[/bold yellow] ")
            chat_log.write("[dim]Stopping recording and transcribing...[/dim]")
            wav_path = audio_recorder.stop_recording()
            if wav_path:
                self._transcribe_voice_task(wav_path)
            else:
                prompt_label.update(" [bold yellow]ᛟ❯[/bold yellow] ")
                chat_log.write("[red]No audio captured.[/red]")

    def action_toggle_mute(self) -> None:
        from mythic_agent.core.tts import tts_manager
        is_muted = tts_manager.toggle_mute()
        chat_log = self.query_one("#chat-log", RichLog)
        if is_muted:
            chat_log.write("[bold yellow]TTS Muted (F5 to unmute).[/bold yellow]")
        else:
            chat_log.write("[bold green]TTS Unmuted.[/bold green]")

    def on_unmount(self) -> None:
        if hasattr(self.app, "pet_timer"):
            self.app.pet_timer.stop()
