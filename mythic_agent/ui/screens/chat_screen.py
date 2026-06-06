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
    """
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=True),
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
                yield Label("[green]/clear[/green]  - Clear history")
                yield Label("[green]/add[/green]    - Add file to context")
                yield Label("[green]/commit[/green] - Auto-commit and push")
                yield Label("[green]/issue[/green]  - Create a GitHub issue")
                yield Label("[green]/pr[/green]     - Create a Pull Request")
                yield Label("[green]/status[/green] - Check Git status")
                yield Label("[green]/gh[/green]      - Run GitHub CLI")
                yield Label("[green]/test[/green]    - Run tests")
                yield Label("[green]/undo[/green]    - Undo last file edit")
                yield Label("[green]/doctor[/green]  - Auto-fix issues")
                yield Label("[green]/copy[/green]   - Copy last AI response")
                yield Label("[green]/btw[/green]    - Add silent context")
                yield Label("[green]/steer[/green]  - Steer the AI")
                yield Label("[green]/flirt[/green]  - Flirt with Viking coder")
                yield Label("[green]/pet[/green]    - Hatch a coding pet")
                yield Label("[green]/quit[/green]   - Exit")
                yield Label("\n[dim]Press F2 to quickly access setup.[/dim]")
                yield Label("\n[dim]Interactions: 0[/dim]", id="interaction-count")
                yield Label("[dim]Tokens Used: 0[/dim]", id="token-count")
                yield Label("\n[bold yellow]⚔️ Active Warriors[/bold yellow]\n[dim]None[/dim]", id="active-agents-label")
                yield Button("Configure GitHub", id="github-config-btn", variant="primary")
                yield Checkbox("Mythic Engineering Mode", id="mythic-engineering-checkbox")
                yield Checkbox("Auto-accept security permissions", id="auto-accept-checkbox")
        yield Footer()

    def on_mount(self) -> None:
        chat_log = self.query_one("#chat-log", RichLog)
        chat_log.write("Welcome to the Viking Mythic Agent! Press F2 to configure your team.\n")
        chat_log.write("[dim]Type /help for a list of runic commands.[/dim]")
        self.query_one("#loading-indicator").display = False
        self.query_one("#chat-input").focus()
        self.update_model_status()
        self.app.set_interval(5.0, self.update_model_status)
        
        # Load Checkbox states
        is_mythic = self.app.agent.config.get("mythic_engineering_mode", False)
        self.query_one("#mythic-engineering-checkbox", Checkbox).value = is_mythic
        
        is_auto = self.app.agent.config.get("auto_accept_permissions", False)
        self.query_one("#auto-accept-checkbox", Checkbox).value = is_auto

    def update_model_status(self) -> None:
        config = self.app.agent.config
        model = config.get("model", "Unknown Model")
        base_url = config.get("base_url", "Unknown Provider")
        
        # Format provider nicely
        provider = "OpenRouter" if "openrouter" in base_url else "DeepSeek" if "deepseek" in base_url else "OpenAI" if "openai" in base_url else base_url
            
        btn = self.query_one("#model-status-btn", Button)
        btn.label = f"⚙️  {provider} : {model} (Click to change)"

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "model-status-btn":
            self.action_setup()
        elif event.button.id == "github-config-btn":
            self.app.push_screen(GithubConfigModal())

    def action_setup(self) -> None:
        self.app.switch_screen("setup_wizard")
        
    def action_select_agent(self) -> None:
        self.app.push_screen(SubagentSelectionModal(), self.on_agent_selected)
        
    def on_agent_selected(self, agent_name: str | None) -> None:
        if agent_name:
            self.app.active_chat_agent = agent_name
            chat_log = self.query_one("#chat-log", RichLog)
            display_name = agent_name
            if agent_name == "Primary":
                display_name = self.app.agent.config.get("primary_agent_name", "Primary Agent")
            chat_log.write(f"\n[bold cyan]⚔️ You are now speaking directly with {display_name}![/bold cyan]")

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        chat_log = self.query_one("#chat-log", RichLog)
        status = "enabled" if event.value else "disabled"
        
        if event.checkbox.id == "mythic-engineering-checkbox":
            self.app.agent.config["mythic_engineering_mode"] = event.value
            self.app.agent.save_config()
            chat_log.write(f"[bold magenta]Mythic Engineering Mode {status}![/bold magenta]")
            
        elif event.checkbox.id == "auto-accept-checkbox":
            self.app.agent.config["auto_accept_permissions"] = event.value
            self.app.agent.save_config()
            chat_log.write(f"[bold red]Auto-accept security permissions {status}![/bold red]")

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        import logging
        user_input = event.value.strip()
        if not user_input:
            return
            
        event.input.value = ""
        chat_log = self.query_one("#chat-log", RichLog)
        
        # Calculate interactions (user messages)
        interactions = len([m for m in self.app.agent.messages if m.get("role") == "user"]) + 1
        self.query_one("#interaction-count", Label).update(f"\n[dim]Interactions: {interactions}[/dim]")

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
            chat_log.write("  [green]/clear[/green]  - Clear conversation history")
            chat_log.write("  [green]/add[/green]    - Explicitly add a file to the LLM context")
            chat_log.write("  [green]/commit[/green] - Auto-commit and push changes to GitHub")
            chat_log.write("  [green]/issue[/green]  - Create a GitHub issue (e.g. /issue Fix bug)")
            chat_log.write("  [green]/pr[/green]     - Create a GitHub Pull Request")
            chat_log.write("  [green]/status[/green] - Check Git status")
            chat_log.write("  [green]/gh[/green]      - Run native GitHub CLI command")
            chat_log.write("  [green]/test[/green]    - Run tests natively")
            chat_log.write("  [green]/undo[/green]    - Roll back the last agent file edit (Git reset)")
            chat_log.write("  [green]/doctor[/green]  - Auto-fix a command output")
            chat_log.write("  [green]/copy[/green]   - Copy the last AI response to your clipboard")
            chat_log.write("  [green]/btw[/green]    - Add context without forcing an immediate response")
            chat_log.write("  [green]/steer[/green]  - Give the AI a strong steering instruction (system prompt)")
            chat_log.write("  [green]/flirt[/green]  - Flirt with your Viking coder")
            chat_log.write("  [green]/pet[/green]    - Hatch a tiny coding pet")
            chat_log.write("  [green]/tutorial[/green] - Learn vibe coding, program usage, and language basics")
            chat_log.write("  [green]/quit[/green]   - Leave Valhalla (Exit)")
        elif cmd == "/clear":
            self.app.agent.messages = self.app.agent.messages[:1]
            chat_log.write("[green]Conversation cleared.[/green]")
        elif cmd == "/copy":
            last_msg = None
            for m in reversed(self.app.agent.messages):
                if m.get("role") == "assistant" and m.get("content"):
                    last_msg = m["content"]
                    break
            if last_msg:
                try:
                    self.app.copy_to_clipboard(last_msg)
                    chat_log.write("[green]Copied last response to clipboard![/green]")
                except Exception as e:
                    chat_log.write(f"[red]Failed to copy to clipboard: {e}[/red]")
            else:
                chat_log.write("[red]No recent response found to copy.[/red]")
        elif cmd == "/add":
            if not args:
                chat_log.write("[red]Usage: /add <file_path>[/red]")
            else:
                try:
                    content = Path(args).read_text(encoding="utf-8")
                    self.app.agent.messages.append({"role": "user", "content": f"Here is the content of {args}:\n\n```\n{content}\n```"})
                    chat_log.write(f"[green]Added {args} to context.[/green]")
                except Exception as e:
                    chat_log.write(f"[red]Error reading {args}: {e}[/red]")
        elif cmd == "/btw":
            if not args:
                chat_log.write("[red]Usage: /btw <message>[/red]")
            else:
                self.app.agent.messages.append({"role": "user", "content": f"By the way (for your context, no need to act on this alone unless asked): {args}"})
                self.app.agent.messages.append({"role": "assistant", "content": "Acknowledged."})
                chat_log.write(f"[green]Added to context: {args}[/green]")
        elif cmd == "/steer":
            if not args:
                chat_log.write("[red]Usage: /steer <instruction>[/red]")
            else:
                self.app.agent.messages.append({"role": "system", "content": f"USER STEERING INSTRUCTION (Priority): {args}"})
                chat_log.write(f"[bold yellow]Steering instruction applied: {args}[/bold yellow]")
        elif cmd == "/flirt":
            chat_log.write("[magenta]Sending flirty vibes...[/magenta]")
            self.run_agent_query("*winks and flirts with you playfully*")
        elif cmd == "/pet":
            if getattr(self.app, "pet_active", False):
                self.app.pet_active = False
                if hasattr(self.app, "pet_timer"):
                    self.app.pet_timer.pause()
                chat_log.write("\n[bold yellow]Your coding dragon curled up and went to sleep.[/bold yellow]")
            else:
                self.app.pet_active = True
                chat_log.write("\n[bold green]🥚 *CRACK* A tiny Mythic Coding Dragon has hatched![/bold green]")
                if hasattr(self.app, "pet_timer"):
                    self.app.pet_timer.resume()
                else:
                    self.app.pet_timer = self.set_interval(60.0, self.pet_speak)
        elif cmd == "/tutorial":
            from .tutorials import TUTORIALS
            topic = args.strip().lower()
            if not topic:
                topics = ", ".join([f"[bold]{k}[/bold]" for k in TUTORIALS.keys()])
                chat_log.write(f"\n[bold cyan]📚 Mythic Academy[/bold cyan]\nAvailable tutorials: {topics}\n[dim]Usage: /tutorial <topic>[/dim]")
            elif topic in TUTORIALS:
                chat_log.write(Markdown(TUTORIALS[topic]))
            else:
                chat_log.write(f"[red]Tutorial '{topic}' not found.[/red] Type /tutorial to see available topics.")
        elif cmd == "/gh":
            if not args:
                chat_log.write("[red]Usage: /gh <command>[/red]")
            else:
                import subprocess
                try:
                    gh_token = self.app.agent.config.get("github", {}).get("token", "")
                    env = os.environ.copy()
                    if gh_token:
                        env["GH_TOKEN"] = gh_token
                    import shlex
                    cmd_list = ["gh"] + shlex.split(args)
                    result = subprocess.run(cmd_list, capture_output=True, text=True, env=env)
                    output = result.stdout if result.returncode == 0 else result.stderr
                    chat_log.write(f"[dim]> gh {args}[/dim]\n{output.strip()}")
                except Exception as e:
                    chat_log.write(f"[red]Error running gh: {e}[/red]")
        elif cmd == "/status":
            chat_log.write("\n[bold cyan]⚔️ Warriors Status:[/bold cyan]")
            from mythic_agent.llm import AGENT_REGISTRY
            p_name = self.app.agent.config.get("primary_agent_name", "Primary Agent")
            chat_log.write(f"  ● [bold]{p_name}[/bold]: Active (Tokens: {self.app.agent.total_tokens})")
            
            sub_agents = self.app.agent.config.get("sub_agents", [])
            for sa in sub_agents:
                name = sa.get("name")
                is_running = name in self.app.active_subagents
                status_text = "[bold green]Running[/bold green]" if is_running else "[dim]Idle[/dim]"
                tokens = AGENT_REGISTRY[name].total_tokens if name in AGENT_REGISTRY else 0
                chat_log.write(f"  ● [bold]{name}[/bold]: {status_text} (Tokens: {tokens})")
                    
            if not sub_agents:
                chat_log.write("  [dim]No sub-agents configured.[/dim]")
                
            chat_log.write("\n[bold cyan]Git Status:[/bold cyan]")
            import subprocess
            try:
                result = subprocess.run(["git", "status"], capture_output=True, text=True, cwd=str(self.app.agent.project_root))
                output = result.stdout if result.returncode == 0 else result.stderr
                chat_log.write(f"[dim]> git status[/dim]\n{output.strip()}")
            except Exception as e:
                chat_log.write(f"[red]Error running git status: {e}[/red]")
        elif cmd == "/commit":
            if not args:
                chat_log.write("[red]Usage: /commit <message>[/red]")
            else:
                import subprocess
                try:
                    subprocess.run(["git", "add", "."], cwd=str(self.app.agent.project_root), check=True)
                    subprocess.run(["git", "commit", "-m", args], cwd=str(self.app.agent.project_root), check=True)
                    chat_log.write(f"[green]Successfully committed: {args}[/green]")
                    
                    # Push
                    chat_log.write("[dim]Pushing to repository...[/dim]")
                    gh_token = self.app.agent.config.get("github", {}).get("token", "")
                    env = os.environ.copy()
                    if gh_token:
                        env["GH_TOKEN"] = gh_token
                    res = subprocess.run(["git", "push"], cwd=str(self.app.agent.project_root), capture_output=True, text=True, env=env)
                    if res.returncode == 0:
                        chat_log.write("[green]Successfully pushed to remote.[/green]")
                    else:
                        chat_log.write(f"[red]Push failed: {res.stderr}[/red]")
                except Exception as e:
                    chat_log.write(f"[red]Failed to commit. Error: {e}[/red]")
        elif cmd == "/status":
            import subprocess
            try:
                result = subprocess.run(["git", "status"], cwd=str(self.app.agent.project_root), capture_output=True, text=True)
                chat_log.write(f"[dim]> git status[/dim]\n{result.stdout.strip()}")
            except Exception as e:
                chat_log.write(f"[red]Failed to get status. Error: {e}[/red]")
        elif cmd == "/issue":
            if not args:
                chat_log.write("[red]Usage: /issue <title>[/red]")
            else:
                import subprocess
                try:
                    gh_token = self.app.agent.config.get("github", {}).get("token", "")
                    env = os.environ.copy()
                    if gh_token:
                        env["GH_TOKEN"] = gh_token
                    repo = self.app.agent.config.get("github", {}).get("repo_url", "")
                    cmd_list = ["gh", "issue", "create"]
                    if repo:
                        cmd_list.extend(["--repo", repo])
                    cmd_list.extend(["--title", args, "--body", "Generated by Mythic Agent"])
                    result = subprocess.run(cmd_list, capture_output=True, text=True, env=env)
                    output = result.stdout if result.returncode == 0 else result.stderr
                    chat_log.write(f"[dim]> Create Issue[/dim]\n{output.strip()}")
                except Exception as e:
                    chat_log.write(f"[red]Error creating issue: {e}[/red]")
        elif cmd == "/pr":
            if not args:
                chat_log.write("[red]Usage: /pr <title>[/red]")
            else:
                import subprocess
                try:
                    gh_token = self.app.agent.config.get("github", {}).get("token", "")
                    env = os.environ.copy()
                    if gh_token:
                        env["GH_TOKEN"] = gh_token
                    repo = self.app.agent.config.get("github", {}).get("repo_url", "")
                    cmd_list = ["gh", "pr", "create"]
                    if repo:
                        cmd_list.extend(["--repo", repo])
                    cmd_list.extend(["--title", args, "--body", "Generated by Mythic Agent"])
                    result = subprocess.run(cmd_list, capture_output=True, text=True, env=env)
                    output = result.stdout if result.returncode == 0 else result.stderr
                    chat_log.write(f"[dim]> Create Pull Request[/dim]\n{output.strip()}")
                except Exception as e:
                    chat_log.write(f"[red]Error creating PR: {e}[/red]")
        elif cmd == "/undo":
            import subprocess
            try:
                subprocess.run(["git", "reset", "--hard", "HEAD~1"], cwd=str(self.app.agent.project_root), check=True)
                chat_log.write("[green]Successfully rolled back to the previous state using git reset.[/green]")
            except Exception as e:
                chat_log.write(f"[red]Failed to undo. Are you in a git repository? Error: {e}[/red]")
        elif cmd == "/doctor":
            if not args:
                chat_log.write("[red]Usage: /doctor <command>[/red]")
            else:
                import subprocess, shlex
                try:
                    cmd_list = shlex.split(args)
                    result = subprocess.run(cmd_list, capture_output=True, text=True)
                    output = result.stdout + "\n" + result.stderr
                    chat_log.write(f"[dim]> {args}[/dim]\n{output.strip()}")
                    self.app.agent.messages.append({"role": "user", "content": f"I ran '{args}' to check for issues. The output was:\n\n```\n{output}\n```\nPlease fix any errors shown in this output."})
                    chat_log.write("[blue]Doctor output fed into agent context. Auto-fixing...[/blue]")
                    self.run_agent_query("Please analyze the output and fix the code.")
                except Exception as e:
                    chat_log.write(f"[red]Error running doctor command: {e}[/red]")
        elif cmd == "/test":
            if not args:
                chat_log.write("[red]Usage: /test <command>[/red]")
            else:
                import subprocess, shlex
                try:
                    cmd_list = shlex.split(args)
                    result = subprocess.run(cmd_list, capture_output=True, text=True)
                    output = result.stdout + "\n" + result.stderr
                    chat_log.write(f"[dim]> {args}[/dim]\n{output.strip()}")
                    self.app.agent.messages.append({"role": "user", "content": f"I ran tests using '{args}'. The output was:\n\n```\n{output}\n```\nDoes this output reveal any bugs? If so, please fix them."})
                    chat_log.write("[blue]Test results fed into agent context. Let's see what it says...[/blue]")
                    self.run_agent_query("Please analyze the test results.")
                except Exception as e:
                    chat_log.write(f"[red]Error running tests: {e}[/red]")
        else:
            chat_log.write(f"[red]Unknown command:[/red] {cmd}")



    def handle_input(self, user_input: str):
        chat_log = self.query_one("#chat-log", RichLog)
        if user_input.startswith("/"):
            self.handle_command(user_input, chat_log)
            return
            
        self.run_agent_query(user_input)

    @work(exclusive=True, thread=True)
    def run_agent_query(self, user_input: str | None) -> None:
        import logging
        chat_log = self.query_one("#chat-log", RichLog)
        
        def set_loading(state: bool):
            try:
                self.query_one("#loading-indicator").display = state
            except Exception:
                pass
        
        self.app.call_from_thread(set_loading, True)
        
        try:
            target_name = getattr(self.app, "active_chat_agent", "Primary")
            
            if target_name == "Primary":
                agent = self.app.agent
            else:
                from mythic_agent.llm import AGENT_REGISTRY, Agent
                if target_name not in AGENT_REGISTRY:
                    config = self.app.agent.config
                    sub_agents = config.get("sub_agents", [])
                    sub_config = next((s for s in sub_agents if s.get("name") == target_name), None)
                    if not sub_config:
                        self.app.call_from_thread(chat_log.write, f"\n[bold red]Error: Sub-agent '{target_name}' not found in config. Falling back to Primary.[/bold red]")
                        self.app.active_chat_agent = "Primary"
                        agent = self.app.agent
                    else:
                        sub_agent = Agent(project_root=self.app.agent.project_root)
                        sub_agent.name = target_name
                        sub_agent.config = dict(config)
                        
                        sub_system_prompt = sub_config.get("prompt", "You are a helpful sub-agent.")
                        global_rules = config.get("global_rules", "").strip()
                        status_rule = "You MUST use the `update_status` tool to autosave your current project status and keep track of what is going on."
                        if global_rules:
                            sub_system_prompt += f"\n\nGLOBAL RULES (You must strictly follow these):\n{global_rules}\n- {status_rule}"
                        else:
                            sub_system_prompt += f"\n\nGLOBAL RULES:\n- {status_rule}"
                            
                        from .llm import get_user_context
                        sub_system_prompt += get_user_context(config)
                            
                        sub_agent.messages = [{"role": "system", "content": sub_system_prompt}]
                        sub_agent.tui_app = self.app
                        AGENT_REGISTRY[target_name] = sub_agent
                        agent = sub_agent
                else:
                    agent = AGENT_REGISTRY[target_name]
                    
                self.app.call_from_thread(chat_log.write, f"[dim italic]→ Routing to {target_name}...[/dim italic]")

            def print_chunk(text: str):
                try:
                    self.app.call_from_thread(chat_log.write, Markdown(text))
                except Exception:
                    from rich.text import Text
                    self.app.call_from_thread(chat_log.write, Text(text))
                
            def print_tool(text: str):
                from rich.markup import escape
                try:
                    if "[+]" in text or "[~]" in text or "[-]" in text:
                        self.app.call_from_thread(chat_log.write, text)
                    else:
                        self.app.call_from_thread(chat_log.write, f"[dim]{escape(text)}[/dim]")
                except Exception:
                    from rich.text import Text
                    self.app.call_from_thread(chat_log.write, Text(text))
                
            agent.chat(user_input, print_chunk, print_tool)
        except Exception as exc:
            logging.exception(f"run_agent_query error: {exc}")
            self.app.call_from_thread(chat_log.write, f"\n[bold red]Error: {exc}[/bold red]")
        finally:
            self.app.call_from_thread(set_loading, False)

    def pet_speak(self) -> None:
        if not getattr(self.app, "pet_active", False):
            return
        import random
        quotes = [
            "rawr! *chews on a stray bracket*",
            "Did you remember to save? Just checking!",
            "I smell a bug... oh wait, it's just Python.",
            "*sleeps on your keyboard*",
            "Are you really going to name that variable 'temp'?",
            "*breathes tiny fire on a syntax error*",
            "More code! Feed me more code!",
            "Who needs documentation when you have ME?",
            "*chases a rogue pointer*",
            "git commit -m 'pet told me to'",
            "Why do humans always forget the semicolon?",
            "Look, a memory leak! Can I eat it?",
            "*curls up around your compiler*",
            "Are we pushing to production on a Friday? Brave human.",
            "*sits directly on your enter key*"
        ]
        chat_log = self.query_one("#chat-log", RichLog)
        msg = random.choice(quotes)
        chat_log.write(f"\n[bold magenta]🐉 Pet Dragon:[/bold magenta] [italic]{msg}[/italic]")

    def on_unmount(self) -> None:
        if hasattr(self.app, "pet_timer"):
            self.app.pet_timer.stop()

