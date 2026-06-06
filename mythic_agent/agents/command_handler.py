import os
import shlex
import subprocess
import logging
from pathlib import Path

from ..core.secure_api import subscribe, publish_sync
from ..core.config_manager import config_manager

class CommandHandler:
    """
    Subscribes to system commands from the UI and executes them safely
    in the background, returning context or results via the event bus.
    """
    def __init__(self):
        subscribe("system_command_executed", self._handle_command)
        self.project_root = None
        
        # Load the initial project root from config
        config = config_manager.load_config()
        working_dir_str = config.get("working_directory")
        if working_dir_str:
            self.project_root = Path(working_dir_str).expanduser().resolve()
        else:
            default_wd = config_manager.MYTHIC_DIR / "mythic_longhall"
            default_wd.mkdir(parents=True, exist_ok=True)
            self.project_root = default_wd

    def _handle_command(self, command: str, args: str):
        """Routes the slash commands from the UI."""
        cmd = command.lower()
        logging.info(f"CommandHandler received: {cmd} {args}")
        
        try:
            if cmd == "/gh":
                self._handle_gh(args)
            elif cmd == "/status":
                self._handle_status(args)
            elif cmd == "/commit":
                self._handle_commit(args)
            elif cmd == "/test":
                self._handle_test(args)
            elif cmd == "/doctor":
                self._handle_doctor(args)
            elif cmd == "/undo":
                self._handle_undo(args)
            elif cmd == "/issue":
                self._handle_issue(args)
            elif cmd == "/pr":
                self._handle_pr(args)
            elif cmd == "/tutorial":
                self._handle_tutorial()
            elif cmd == "/clear":
                self._handle_clear()
            elif cmd == "/compact":
                self._handle_compact()
            elif cmd == "/cost":
                self._handle_cost()
            elif cmd == "/review":
                self._handle_review(args)
        except Exception as e:
            logging.error(f"Command Execution Error: {e}", exc_info=True)
            publish_sync("agent_chat_chunk", agent_name="Primary", text=f"\n[bold red]System Command Error: {e}[/bold red]\n")

    def _get_gh_env(self) -> dict:
        config = config_manager.load_config()
        gh_token = config.get("github", {}).get("token", "")
        env = os.environ.copy()
        if gh_token:
            env["GH_TOKEN"] = gh_token
        return env
        
    def _get_gh_repo(self) -> str:
        config = config_manager.load_config()
        return config.get("github", {}).get("repo_url", "")

    def _handle_gh(self, args: str):
        if not args:
            publish_sync("agent_chat_chunk", agent_name="Primary", text="\n[red]Usage: /gh <command>[/red]\n")
            return
            
        cmd_list = ["gh"] + shlex.split(args)
        try:
            result = subprocess.run(cmd_list, capture_output=True, text=True, env=self._get_gh_env(), timeout=30)
            output = result.stdout if result.returncode == 0 else result.stderr
        except subprocess.TimeoutExpired:
            output = "[red]Command timed out after 30 seconds.[/red]"
        except FileNotFoundError:
            output = "[red]Error: 'gh' CLI not found. Please install the GitHub CLI.[/red]"
        publish_sync("agent_chat_chunk", agent_name="Primary", text=f"\n[dim]> gh {args}[/dim]\n{output.strip()}\n")

    def _handle_status(self, args: str):
        try:
            result = subprocess.run(["git", "status"], capture_output=True, text=True, cwd=str(self.project_root), timeout=15)
            output = result.stdout if result.returncode == 0 else result.stderr
        except subprocess.TimeoutExpired:
            output = "[red]git status timed out.[/red]"
        except FileNotFoundError:
            output = "[red]Error: 'git' not found. Is git installed?[/red]"
        publish_sync("agent_chat_chunk", agent_name="Primary", text=f"\n[dim]> git status[/dim]\n{output.strip()}\n")

    def _handle_commit(self, args: str):
        if not args:
            publish_sync("agent_chat_chunk", agent_name="Primary", text="\n[red]Usage: /commit <message>[/red]\n")
            return
            
        try:
            subprocess.run(["git", "add", "."], cwd=str(self.project_root), check=True, timeout=30)
            subprocess.run(["git", "commit", "-m", args], cwd=str(self.project_root), check=True, timeout=30)
        except subprocess.CalledProcessError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary", text=f"\n[red]Commit failed: {e}[/red]\n")
            return
        except subprocess.TimeoutExpired:
            publish_sync("agent_chat_chunk", agent_name="Primary", text="\n[red]Commit timed out.[/red]\n")
            return
        except FileNotFoundError:
            publish_sync("agent_chat_chunk", agent_name="Primary", text="\n[red]Error: 'git' not found.[/red]\n")
            return
        publish_sync("agent_chat_chunk", agent_name="Primary", text=f"\n[green]Successfully committed: {args}[/green]\n[dim]Pushing to repository...[/dim]\n")
        
        try:
            res = subprocess.run(["git", "push"], cwd=str(self.project_root), capture_output=True, text=True, env=self._get_gh_env(), timeout=60)
            if res.returncode == 0:
                publish_sync("agent_chat_chunk", agent_name="Primary", text="[green]Successfully pushed to remote.[/green]\n")
            else:
                publish_sync("agent_chat_chunk", agent_name="Primary", text=f"[red]Push failed: {res.stderr}[/red]\n")
        except subprocess.TimeoutExpired:
            publish_sync("agent_chat_chunk", agent_name="Primary", text="[red]git push timed out after 60 seconds.[/red]\n")

    def _handle_test(self, args: str):
        if not args:
            publish_sync("agent_chat_chunk", agent_name="Primary", text="\n[red]Usage: /test <command>[/red]\n")
            return
            
        cmd_list = shlex.split(args)
        try:
            result = subprocess.run(cmd_list, capture_output=True, text=True, cwd=str(self.project_root), timeout=120)
            output = result.stdout + "\n" + result.stderr
        except subprocess.TimeoutExpired:
            output = "Test command timed out after 120 seconds."
        except FileNotFoundError:
            output = f"Command not found: {cmd_list[0] if cmd_list else args}"
        publish_sync("agent_chat_chunk", agent_name="Primary", text=f"\n[dim]> {args}[/dim]\n{output.strip()}\n[blue]Test results fed into agent context.[/blue]\n")
        
        # Pass back to the LLM agent using the secure API
        context = f"I ran tests using '{args}'. The output was:\n\n```\n{output}\n```\nDoes this output reveal any bugs? If so, please fix them."
        publish_sync("ui_chat_request", user_input=context, target_agent="Primary")

    def _handle_doctor(self, args: str):
        if not args:
            publish_sync("agent_chat_chunk", agent_name="Primary", text="\n[red]Usage: /doctor <command>[/red]\n")
            return
            
        cmd_list = shlex.split(args)
        try:
            result = subprocess.run(cmd_list, capture_output=True, text=True, cwd=str(self.project_root), timeout=60)
            output = result.stdout + "\n" + result.stderr
        except subprocess.TimeoutExpired:
            output = "Doctor command timed out after 60 seconds."
        except FileNotFoundError:
            output = f"Command not found: {cmd_list[0] if cmd_list else args}"
        publish_sync("agent_chat_chunk", agent_name="Primary", text=f"\n[dim]> {args}[/dim]\n{output.strip()}\n[blue]Doctor output fed into agent context. Auto-fixing...[/blue]\n")
        
        context = f"I ran '{args}' to check for issues. The output was:\n\n```\n{output}\n```\nPlease fix any errors shown in this output."
        publish_sync("ui_chat_request", user_input=context, target_agent="Primary")

    def _handle_undo(self, args: str):
        try:
            subprocess.run(["git", "reset", "--hard", "HEAD~1"], cwd=str(self.project_root), check=True, timeout=30)
            publish_sync("agent_chat_chunk", agent_name="Primary", text="\n[green]Successfully rolled back to the previous state using git reset.[/green]\n")
        except subprocess.CalledProcessError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary", text=f"\n[red]Undo failed: {e.stderr or str(e)}[/red]\n")
        except subprocess.TimeoutExpired:
            publish_sync("agent_chat_chunk", agent_name="Primary", text="\n[red]git reset timed out.[/red]\n")
        except FileNotFoundError:
            publish_sync("agent_chat_chunk", agent_name="Primary", text="\n[red]Error: 'git' not found.[/red]\n")

    def _handle_issue(self, args: str):
        if not args:
            publish_sync("agent_chat_chunk", agent_name="Primary", text="\n[red]Usage: /issue <title>[/red]\n")
            return
            
        cmd_list = ["gh", "issue", "create"]
        repo = self._get_gh_repo()
        if repo:
            cmd_list.extend(["--repo", repo])
        cmd_list.extend(["--title", args, "--body", "Generated by Mythic Agent"])
        
        try:
            result = subprocess.run(cmd_list, capture_output=True, text=True, env=self._get_gh_env(), timeout=30)
            output = result.stdout if result.returncode == 0 else result.stderr
        except subprocess.TimeoutExpired:
            output = "[red]gh issue create timed out.[/red]"
        except FileNotFoundError:
            output = "[red]Error: 'gh' CLI not found.[/red]"
        publish_sync("agent_chat_chunk", agent_name="Primary", text=f"\n[dim]> Create Issue[/dim]\n{output.strip()}\n")

    def _handle_pr(self, args: str):
        if not args:
            publish_sync("agent_chat_chunk", agent_name="Primary", text="\n[red]Usage: /pr <title>[/red]\n")
            return
            
        cmd_list = ["gh", "pr", "create"]
        repo = self._get_gh_repo()
        if repo:
            cmd_list.extend(["--repo", repo])
        cmd_list.extend(["--title", args, "--body", "Generated by Mythic Agent"])
        
        try:
            result = subprocess.run(cmd_list, capture_output=True, text=True, env=self._get_gh_env(), timeout=30)
            output = result.stdout if result.returncode == 0 else result.stderr
        except subprocess.TimeoutExpired:
            output = "[red]gh pr create timed out.[/red]"
        except FileNotFoundError:
            output = "[red]Error: 'gh' CLI not found.[/red]"
        publish_sync("agent_chat_chunk", agent_name="Primary", text=f"\n[dim]> Create Pull Request[/dim]\n{output.strip()}\n")

    def _handle_tutorial(self):
        tutorial_text = """
[bold cyan]Mythic Agent Vibe Coding Tutorial[/bold cyan]

[bold yellow]What is Vibe Coding?[/bold yellow]
Vibe coding is the art of steering autonomous AI agents using natural language intents, high-level directives, and "vibes" rather than writing every line of code manually. You are the Architect; the Agent is the Builder.

[bold yellow]Core Principles:[/bold yellow]
1. [green]Declare the Goal:[/green] Tell the agent *what* you want, not necessarily *how* to do it. (e.g., "Build a React login page with glassmorphism")
2. [green]Iterate Rapidly:[/green] Run the code, observe the UI/errors, and feed the "vibe" back to the agent. (e.g., "It looks too corporate, make it more cyber-pagan")
3. [green]Use Context:[/green] Use `/add file.py` or `/btw <message>` to inject context without forcing a major re-write.
4. [green]Steer Strongly:[/green] If the agent is drifting, use `/steer <directive>` to forcefully inject a high-priority system-level instruction.
5. [green]Let it Work:[/green] The agent can loop and use tools autonomously. Trust the loop. Use F3 to spawn specialized subagents for parallel work.

[bold yellow]Example Flow:[/bold yellow]
- You: "Create a fast API server in main.py that returns hello world."
- (Agent builds it)
- You: "/test pytest"
- (Agent reads the test output and fixes its own bugs automatically)
- You: "Perfect. Now vibe check the response format, make it return JSON with a mythic aesthetic."

[dim]Press F2 to adjust your team of subagents. Happy coding![/dim]
"""
        publish_sync("agent_chat_chunk", agent_name="Primary", text=f"\n{tutorial_text}\n")

    def _handle_clear(self):
        # We broadcast the clear signal to the Primary agent
        publish_sync("agent_clear_history", target_agent="Primary")

    def _handle_compact(self):
        # Broadcast compact signal
        publish_sync("agent_compact_history", target_agent="Primary")

    def _handle_cost(self):
        # Dynamically import AGENT_REGISTRY to avoid circular imports if any
        from .llm import AGENT_REGISTRY
        agent = AGENT_REGISTRY.get("Primary")
        if agent:
            tokens = agent.total_tokens
            # Rough estimate: Claude 3 Haiku costs ~$0.25 / 1M input + ~$1.25 / 1M output
            # We'll just provide a blended rough estimate of $0.50 per 1M tokens.
            cost_est = (tokens / 1_000_000) * 0.50
            cost_str = f"${cost_est:.4f}" if cost_est > 0.001 else "< $0.001"
            text = f"\n[bold cyan]Token Usage & Cost (Primary Agent)[/bold cyan]\nTotal Tokens: {tokens:,}\nEstimated Cost: {cost_str}\n"
        else:
            text = "\n[dim]Agent is not initialized yet.[/dim]\n"
        publish_sync("agent_chat_chunk", agent_name="Primary", text=text)

    def _handle_review(self, args: str):
        try:
            result = subprocess.run(["git", "diff", "HEAD"], capture_output=True, text=True, cwd=str(self.project_root), timeout=15)
            diff_output = result.stdout
        except subprocess.TimeoutExpired:
            publish_sync("agent_chat_chunk", agent_name="Primary", text="\n[red]git diff timed out.[/red]\n")
            return
        except FileNotFoundError:
            publish_sync("agent_chat_chunk", agent_name="Primary", text="\n[red]Error: 'git' not found.[/red]\n")
            return
        if not diff_output.strip():
            publish_sync("agent_chat_chunk", agent_name="Primary", text="\n[dim]No uncommitted changes to review.[/dim]\n")
            return
            
        publish_sync("agent_chat_chunk", agent_name="Primary", text="\n[dim]> /review[/dim]\n[blue]Submitting current working diff for autonomous code review...[/blue]\n")
        
        context = f"Please do a thorough code review of my uncommitted changes. Point out any logic errors, aesthetic improvements, or architectural issues:\n\n```diff\n{diff_output}\n```\n"
        publish_sync("ui_chat_request", user_input=context, target_agent="Primary")

# Global singleton
command_handler = CommandHandler()
