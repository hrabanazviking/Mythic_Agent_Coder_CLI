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
                    COMMANDS = ["/setup", "/add", "/commit", "/issue", "/pr", "/status", "/gh", "/test", "/undo", "/doctor", "/flirt", "/lick", "/hug", "/kiss", "/snuggle", "/cuddle", "/tickle", "/wink", "/rose", "/mead", "/ale", "/beer", "/cookies", "/candy", "/love", "/btw", "/steer", "/stop", "/tutorial", "/quit", "/help", "/exit"]
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

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id != "chat-input":
            return
            
        val = event.value
        try:
            lbl = self.query_one("#autocomplete-suggestions", Label)
            if val.startswith("/"):
                COMMANDS = ["/setup", "/add", "/commit", "/issue", "/pr", "/status", "/gh", "/test", "/undo", "/doctor", "/flirt", "/lick", "/hug", "/kiss", "/snuggle", "/cuddle", "/tickle", "/wink", "/rose", "/mead", "/ale", "/beer", "/cookies", "/candy", "/love", "/btw", "/steer", "/stop", "/tutorial", "/quit", "/help", "/exit"]
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
                    "/commit": "Usage: /commit [message]\nAutomatically stages all changes, generates a commit message if none provided, and pushes to GitHub.",
                    "/issue": "Usage: /issue <title>\nCreates a new GitHub issue using the gh CLI tool.",
                    "/pr": "Usage: /pr\nCreates a Pull Request using the gh CLI tool.",
                    "/status": "Usage: /status\nShows current git status and recent commits.",
                    "/gh": "Usage: /gh <args>\nRuns arbitrary native GitHub CLI commands.",
                    "/test": "Usage: /test\nRuns pytest natively in the repository.",
                    "/undo": "Usage: /undo\nRolls back the last file edit made by the agent by running `git reset --hard` and checking out the last stable state.",
                    "/doctor": "Usage: /doctor\nExamines the output of the last failed command and automatically generates a fix.",
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
            if "[Ghost]" not in active:
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
            
            SecureAPI.publish_ghost_chat_request(f"{action_text} {args}", target_agent=active)
            chat_log.write(f"[magenta]{action_text}[/magenta] {args}")
        elif cmd in ["/gh", "/status", "/commit", "/test", "/doctor", "/undo", "/issue", "/pr", "/stop"]:
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
