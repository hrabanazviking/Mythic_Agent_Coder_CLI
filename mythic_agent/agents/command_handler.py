import os
import shlex
import subprocess
import logging
import threading
from functools import wraps
from types import SimpleNamespace
from pathlib import Path

from ..core.secure_api import subscribe, publish_sync
from ..core.config_manager import config_manager
from ..core.policy import ToolPolicy
from ..core.execution import run_process
from ..core.runtime import TurnCancelled, runtime_settings


def requires_permission(name):
    """Guard private helpers too, so direct adapters cannot bypass the dispatcher."""
    def decorate(method):
        @wraps(method)
        def guarded(self, args):
            if not self._policy().authorize(name, {"arguments": args}):
                publish_sync("agent_chat_chunk", agent_name="Primary",
                             text=f"\nPermission denied for {name}; no operation was performed.\n")
                return
            if self._cancel_event().is_set():
                raise TurnCancelled("Command cancelled before execution")
            return method(self, args)
        return guarded
    return decorate

class CommandHandler:
    """
    Subscribes to system commands from the UI and executes them safely
    in the background, returning context or results via the event bus.
    """
    def __init__(self):
        self._command_lock = threading.Lock()
        self._commands_lock = threading.Lock()
        self._commands = {}
        self._local = threading.local()
        self._pending_commit: str | None = None  # S10: message awaiting /commit --confirm
        subscribe("system_command_executed", self._dispatch_command)
        from ..core.workspace import resolve_workspace
        self.project_root = resolve_workspace(config=config_manager.load_config())

    def _dispatch_command(self, command: str, args: str):
        if command.lower() == "/stop":
            with self._commands_lock:
                for cancel in self._commands.values():
                    cancel.set()
            return
        token, cancel = object(), threading.Event()
        with self._commands_lock:
            self._commands[token] = cancel
        def execute():
            acquired = False
            try:
                while not cancel.is_set():
                    acquired = self._command_lock.acquire(timeout=0.05)
                    if acquired:
                        break
                self._local.cancel = cancel
                if acquired and not cancel.is_set():
                    self._handle_command(command, args)
            finally:
                if acquired:
                    self._command_lock.release()
                with self._commands_lock:
                    self._commands.pop(token, None)
        threading.Thread(target=execute, name="mythic-slash-command", daemon=True).start()

    def _primary(self):
        from .llm import AGENT_REGISTRY
        return AGENT_REGISTRY.get("Primary")

    def _cancel_event(self):
        local = getattr(self, "_local", None)
        return getattr(local, "cancel", None) or getattr(self, "cancel_event", None) or threading.Event()

    def _policy(self):
        if hasattr(self, "policy"):
            return self.policy
        primary = self._primary()
        if primary and primary.tui_app:
            from .tools import prompt_approval_sync
            import json
            def approve(name, arguments):
                text = primary.redactor.text(name + ": " + json.dumps(arguments, ensure_ascii=False))
                return prompt_approval_sync(text, primary.tui_app, self._cancel_event(),
                                             runtime_settings(primary.config)["approval_timeout"])
            return ToolPolicy(primary.tool_policy.mode, approve)
        return primary.tool_policy if primary else ToolPolicy("read-only")

    def _root(self):
        primary = self._primary()
        return primary.project_root if primary else self.project_root

    def _redact(self, text: str) -> str:
        """Strip API keys/tokens from command output before it reaches logs or the UI.

        Uses mythic_agent/core/redaction.py: configured secrets from the config
        plus env vars, and common token shapes (sk-*, ghp_*, github_pat_*).
        """
        text = text or ""
        try:
            from ..core.redaction import SecretRedactor
            return SecretRedactor(config_manager.load_config()).text(text)
        except Exception:
            from ..core.redaction import redact_text
            return redact_text(text)

    def _run(self, command, *, cwd=None, timeout=300, env=None, check=False, **unused):
        primary = self._primary()
        settings = runtime_settings(primary.config if primary else {})
        # S10: an explicit cwd is honored; the workspace is the default.
        workspace = Path(cwd).expanduser() if cwd else self._root()
        result = run_process(command, workspace, cancel=self._cancel_event(),
                             timeout=min(timeout, settings["command_timeout"]),
                             grace=settings["process_kill_grace"], env=env,
                             progress=lambda text: publish_sync("agent_command_output", agent_name="Primary", text=text))
        if result.status == "cancelled":
            raise TurnCancelled(result.render())
        if check and result.status != "completed":
            raise subprocess.CalledProcessError(result.returncode or 1, command, output=result.render())
        return SimpleNamespace(returncode=result.returncode, stdout=result.render(), stderr="",
                               status=result.status, output=result.output)

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
        except TurnCancelled as e:
            publish_sync("agent_chat_chunk", agent_name="Primary", text=f"\nCommand cancelled: {e}\n")
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

    @requires_permission("github_execute")
    def _handle_gh(self, args: str):
        if not args:
            publish_sync("agent_chat_chunk", agent_name="Primary", text="\n[red]Usage: /gh <command>[/red]\n")
            return
            
        cmd_list = ["gh"] + shlex.split(args)
        try:
            # S10: gh always runs with the workspace as cwd.
            result = self._run(cmd_list, capture_output=True, text=True,
                               env=self._get_gh_env(), timeout=30,
                               cwd=str(self.project_root))
            output = self._redact(result.stdout)
        except subprocess.TimeoutExpired:
            output = "[red]Command timed out after 30 seconds.[/red]"
        except FileNotFoundError:
            output = "[red]Error: 'gh' CLI not found. Please install the GitHub CLI.[/red]"
        publish_sync("agent_chat_chunk", agent_name="Primary", text=f"\n[dim]> gh {args}[/dim]\n{output.strip()}\n")

    def _handle_status(self, args: str):
        try:
            result = self._run(["git", "status"], capture_output=True, text=True, cwd=str(self.project_root), timeout=15)
            output = self._redact(result.stdout)
        except subprocess.TimeoutExpired:
            output = "[red]git status timed out.[/red]"
        except FileNotFoundError:
            output = "[red]Error: 'git' not found. Is git installed?[/red]"
        publish_sync("agent_chat_chunk", agent_name="Primary", text=f"\n[dim]> git status[/dim]\n{output.strip()}\n")

    @requires_permission("git_commit")
    def _handle_commit(self, args: str):
        """Two-step commit: preview the change set, then confirm.

        ``/commit <message>`` shows ``git status --short`` and ``git diff --stat``
        without staging anything and asks for confirmation; ``/commit --confirm``
        stages, commits, and pushes. The permission gate stays on the entry
        point so private mutators always consult the policy.
        """
        args = (args or "").strip()
        if args.startswith("--confirm"):
            message = args[len("--confirm"):].strip() or self._pending_commit
            self._pending_commit = None
            if not message:
                publish_sync("agent_chat_chunk", agent_name="Primary",
                             text="\n[red]Nothing to confirm. Run /commit <message> first to preview the change set.[/red]\n")
                return
            self._commit_confirmed(message)
            return
        if not args:
            publish_sync("agent_chat_chunk", agent_name="Primary", text="\n[red]Usage: /commit <message>[/red]\n")
            return
        try:
            status_result = self._run(["git", "status", "--short"], timeout=15)
            diff_result = self._run(["git", "diff", "--stat"], timeout=15)
        except subprocess.TimeoutExpired:
            publish_sync("agent_chat_chunk", agent_name="Primary", text="\n[red]Commit preview timed out.[/red]\n")
            return
        except FileNotFoundError:
            publish_sync("agent_chat_chunk", agent_name="Primary", text="\n[red]Error: 'git' not found.[/red]\n")
            return
        status_out = self._redact(status_result.stdout).strip()
        diff_out = self._redact(diff_result.stdout).strip()
        self._pending_commit = args
        publish_sync("agent_chat_chunk", agent_name="Primary", text=(
            "\n[bold cyan]Commit preview[/bold cyan] (nothing staged or committed yet)\n"
            "[dim]> git status --short[/dim]\n" + (status_out or "[dim](working tree clean)[/dim]") + "\n"
            "[dim]> git diff --stat[/dim]\n" + (diff_out or "[dim](no changes)[/dim]") + "\n"
            f"\n[bold yellow]Proposed message:[/bold yellow] {args}\n"
            "[yellow]Run [/yellow][bold]/commit --confirm[/bold][yellow] to stage, commit, and push.[/yellow]\n"))

    @requires_permission("git_commit")
    def _commit_confirmed(self, message: str):
        """Stage, commit, and push after the user confirmed the preview."""
        try:
            self._run(["git", "add", "."], cwd=str(self.project_root), check=True, timeout=30)
            self._run(["git", "commit", "-m", message], cwd=str(self.project_root), check=True, timeout=30)
        except subprocess.CalledProcessError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\nCommit failed: {self._redact(str(e))}\n{self._redact(e.output or chr(32))}\n")
            return
        except subprocess.TimeoutExpired:
            publish_sync("agent_chat_chunk", agent_name="Primary", text="\n[red]Commit timed out.[/red]\n")
            return
        except FileNotFoundError:
            publish_sync("agent_chat_chunk", agent_name="Primary", text="\n[red]Error: 'git' not found.[/red]\n")
            return
        publish_sync("agent_chat_chunk", agent_name="Primary", text=f"\n[green]Successfully committed: {message}[/green]\n[dim]Pushing to repository...[/dim]\n")

        try:
            res = self._run(["git", "push"], cwd=str(self.project_root), capture_output=True, text=True, env=self._get_gh_env(), timeout=60)
            if res.returncode == 0:
                publish_sync("agent_chat_chunk", agent_name="Primary", text="[green]Successfully pushed to remote.[/green]\n")
            else:
                publish_sync("agent_chat_chunk", agent_name="Primary", text=f"\nPush failed: {self._redact(res.stdout)}\n")
        except subprocess.TimeoutExpired:
            publish_sync("agent_chat_chunk", agent_name="Primary", text="[red]git push timed out after 60 seconds.[/red]\n")

    @requires_permission("run_command")
    def _handle_test(self, args: str):
        if not args:
            publish_sync("agent_chat_chunk", agent_name="Primary", text="\n[red]Usage: /test <command>[/red]\n")
            return
            
        cmd_list = shlex.split(args)
        try:
            result = self._run(cmd_list, capture_output=True, text=True, cwd=str(self.project_root), timeout=120)
            output = self._redact(result.stdout + "\n" + result.stderr)
        except subprocess.TimeoutExpired:
            output = "Test command timed out after 120 seconds."
        except FileNotFoundError:
            output = f"Command not found: {cmd_list[0] if cmd_list else args}"
        publish_sync("agent_chat_chunk", agent_name="Primary", text=f"\n[dim]> {args}[/dim]\n{output.strip()}\n[blue]Test results fed into agent context.[/blue]\n")
        
        # Pass back to the LLM agent using the secure API
        context = f"I ran tests using '{args}'. The output was:\n\n```\n{output}\n```\nDoes this output reveal any bugs? If so, please fix them."
        publish_sync("ui_chat_request", user_input=context, target_agent="Primary")

    @requires_permission("run_command")
    def _handle_doctor(self, args: str):
        if not args:
            publish_sync("agent_chat_chunk", agent_name="Primary", text="\n[red]Usage: /doctor <command>[/red]\n")
            return
            
        cmd_list = shlex.split(args)
        try:
            result = self._run(cmd_list, capture_output=True, text=True, cwd=str(self.project_root), timeout=60)
            output = self._redact(result.stdout + "\n" + result.stderr)
        except subprocess.TimeoutExpired:
            output = "Doctor command timed out after 60 seconds."
        except FileNotFoundError:
            output = f"Command not found: {cmd_list[0] if cmd_list else args}"
        publish_sync("agent_chat_chunk", agent_name="Primary", text=f"\n[dim]> {args}[/dim]\n{output.strip()}\n[blue]Doctor output fed into agent context. Auto-fixing...[/blue]\n")
        
        context = f"I ran '{args}' to check for issues. The output was:\n\n```\n{output}\n```\nPlease fix any errors shown in this output."
        publish_sync("ui_chat_request", user_input=context, target_agent="Primary")

    @requires_permission("undo_edit")
    def _handle_undo(self, args: str):
        from ..core.edits import EditJournal
        from .llm import AGENT_REGISTRY
        primary = AGENT_REGISTRY.get("Primary")
        root = primary.project_root if primary else self.project_root
        try:
            result = EditJournal(root).undo()
        except Exception as exc:
            result = f"Undo failed; no Git reset was performed: {exc}"
        publish_sync("agent_chat_chunk", agent_name="Primary", text=f"\n{result}\n")

    @requires_permission("github_execute")
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
            # S10: gh always runs with the workspace as cwd.
            result = self._run(cmd_list, capture_output=True, text=True,
                               env=self._get_gh_env(), timeout=30,
                               cwd=str(self.project_root))
            output = self._redact(result.stdout)
        except subprocess.TimeoutExpired:
            output = "[red]gh issue create timed out.[/red]"
        except FileNotFoundError:
            output = "[red]Error: 'gh' CLI not found.[/red]"
        publish_sync("agent_chat_chunk", agent_name="Primary", text=f"\n[dim]> Create Issue[/dim]\n{output.strip()}\n")

    @requires_permission("github_execute")
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
            # S10: gh always runs with the workspace as cwd.
            result = self._run(cmd_list, capture_output=True, text=True,
                               env=self._get_gh_env(), timeout=30,
                               cwd=str(self.project_root))
            output = self._redact(result.stdout)
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
            result = self._run(["git", "diff", "HEAD"], capture_output=True, text=True, cwd=str(self.project_root), timeout=15)
            if result.status != "completed":
                publish_sync("agent_chat_chunk", agent_name="Primary", text=f"\nReview failed: {self._redact(result.stdout)}\n")
                return
            diff_output = result.output
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
        
        context = f"Please do a thorough code review of my uncommitted changes. Point out any logic errors, aesthetic improvements, or architectural issues:\n\n```diff\n{self._redact(diff_output)}\n```\n"
        publish_sync("ui_chat_request", user_input=context, target_agent="Primary")

# Global singleton
command_handler = CommandHandler()
