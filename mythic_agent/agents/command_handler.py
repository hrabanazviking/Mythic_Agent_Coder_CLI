
__all__ = [
    "CommandHandler",
    "Path",
    "SimpleNamespace",
    "ToolPolicy",
    "TurnCancelled",
    "command_handler",
    "config_manager",
    "publish_sync",
    "requires_permission",
    "run_process",
    "runtime_settings",
    "subscribe",
    "wraps",
]
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
                try:
                    from ..core.lifecycle import unregister_thread
                    unregister_thread(threading.current_thread())
                except Exception:
                    pass
        from ..core.thread_audit import THREAD_REGISTRY
        command_thread = threading.Thread(
            target=execute, name=f"mythic-slash-command:{id(token):x}", daemon=True)
        THREAD_REGISTRY.assert_single_owner(f"mythic-slash-command:{id(token):x}")
        command_thread.start()
        THREAD_REGISTRY.register(command_thread, f"mythic-slash-command:{id(token):x}")
        from ..core.lifecycle import register_thread
        register_thread(command_thread, cancel,
                        name=f"mythic-slash-command:{id(token):x}")

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
            elif cmd == "/ollama":
                self._handle_ollama(args)
            elif cmd == "/local":
                self._handle_local(args)
            elif cmd == "/gateway":
                self._handle_gateway(args)
            elif cmd == "/model":
                self._handle_model(args)
            elif cmd == "/route":
                self._handle_route(args)
            elif cmd == "/fallback":
                self._handle_fallback(args)
            elif cmd == "/costroute":
                self._handle_costroute(args)
            elif cmd == "/editformat":
                self._handle_editformat(args)
            elif cmd == "/hashanchor":
                self._handle_hashanchor(args)
            elif cmd == "/repairloop":
                self._handle_repairloop(args)
            elif cmd == "/hunkreview":
                self._handle_hunkreview(args)
            elif cmd == "/changeset":
                self._handle_changeset(args)
            elif cmd == "/rename":
                self._handle_rename(args)
            elif cmd == "/generated":
                self._handle_generated(args)
            elif cmd == "/largefile":
                self._handle_largefile(args)
            elif cmd == "/stash":
                self._handle_stash(args)
            elif cmd == "/patch":
                self._handle_patch(args)
            elif cmd == "/editor":
                self._handle_editor(args)
            elif cmd == "/issueslice":
                self._handle_issueslice(args)
            elif cmd == "/diff":
                self._handle_diff(args)
            elif cmd == "/blame":
                self._handle_blame(args)
            elif cmd == "/massedit":
                self._handle_massedit(args)
            elif cmd == "/posture":
                self._handle_posture(args)
            elif cmd == "/remember":
                self._handle_remember(args)
            elif cmd == "/sandbox":
                self._handle_sandbox(args)
            elif cmd == "/network":
                self._handle_network(args)
            elif cmd == "/pathjail":
                self._handle_pathjail(args)
            elif cmd == "/plan":
                self._handle_plan(args)
            elif cmd == "/hooks":
                self._handle_hooks(args)
            elif cmd == "/hookpacks":
                self._handle_hookpacks(args)
            elif cmd == "/background":
                self._handle_background(args)
            elif cmd == "/keeper":
                self._handle_keeper(args)
            elif cmd == "/schedule":
                self._handle_schedule(args)
            elif cmd == "/fleet":
                self._handle_fleet(args)
            elif cmd == "/budgets":
                self._handle_budgets(args)
            elif cmd == "/halt":
                self._handle_halt(args)
            elif cmd == "/audit":
                self._handle_audit(args)
            elif cmd == "/secrets":
                self._handle_secrets(args)
            elif cmd == "/doctrine":
                self._handle_doctrine(args)
            elif cmd == "/rollback":
                self._handle_rollback(args)
            elif cmd == "/multirepo":
                self._handle_multirepo(args)
            elif cmd == "/remote":
                self._handle_remote(args)
            elif cmd == "/grace":
                self._handle_grace(args)
            elif cmd == "/moment":
                self._handle_moment(args)
            elif cmd == "/policy":
                self._handle_policy(args)
            elif cmd == "/crew":
                self._handle_crew(args)
            elif cmd == "/offices":
                self._handle_offices(args)
            elif cmd == "/worktrees":
                self._handle_worktrees(args)
            elif cmd == "/dealing":
                self._handle_dealing(args)
            elif cmd == "/comms":
                self._handle_comms(args)
            elif cmd == "/deadlock":
                self._handle_deadlock(args)
            elif cmd == "/merge":
                self._handle_merge(args)
            elif cmd == "/hetero":
                self._handle_hetero(args)
            elif cmd == "/veto":
                self._handle_veto(args)
            elif cmd == "/swarm":
                self._handle_swarm(args)
            elif cmd == "/panel":
                self._handle_panel(args)
            elif cmd == "/memory":
                self._handle_memory(args)
            elif cmd == "/standup":
                self._handle_standup(args)
            elif cmd == "/crewsize":
                self._handle_crewsize(args)
            elif cmd == "/voices":
                self._handle_voices(args)
            elif cmd == "/externals":
                self._handle_externals(args)
            elif cmd == "/replay":
                self._handle_replay(args)
            elif cmd == "/foster":
                self._handle_foster(args)
            elif cmd == "/costcourt":
                self._handle_costcourt(args)
            elif cmd == "/dogfood":
                self._handle_dogfood(args)
            elif cmd == "/solo":
                self._handle_solo(args)
            elif cmd == "/templates":
                self._handle_templates(args)
            elif cmd == "/interrupts":
                self._handle_interrupts(args)
            elif cmd == "/crewschedules":
                self._handle_crewschedules(args)
            elif cmd == "/conflicts":
                self._handle_conflicts(args)
            elif cmd == "/commitcraft":
                self._handle_commitcraft(args)
            elif cmd == "/checkpoint":
                self._handle_checkpoint(args)
            elif cmd == "/branch":
                self._handle_branch(args)
            elif cmd == "/autocommit":
                self._handle_autocommit(args)
            elif cmd == "/guardians":
                self._handle_guardians(args)
            elif cmd == "/prcraft":
                self._handle_prcraft(args)
            elif cmd == "/kista":
                self._handle_kista(args)
            elif cmd == "/resume-thought":
                self._handle_resume_thought(args)
            elif cmd == "/retry":
                self._handle_retry(args)
            elif cmd == "/weather":
                self._handle_weather(args)
            elif cmd == "/vision":
                self._handle_vision(args)
            elif cmd == "/longcontext":
                self._handle_longcontext(args)
            elif cmd == "/offline":
                self._handle_offline(args)
            elif cmd == "/testkit":
                self._handle_testkit(args)
            elif cmd == "/map":
                self._handle_map(args)
            elif cmd == "/ssearch":
                self._handle_ssearch(args)
            elif cmd == "/srewrite":
                self._handle_srewrite(args)
            elif cmd == "/lsp":
                self._handle_lsp(args)
            elif cmd == "/truth":
                self._handle_truth(args)
            elif cmd == "/format":
                self._handle_format(args)
            elif cmd == "/debug":
                self._handle_debug(args)
            elif cmd == "/debugloop":
                self._handle_debug_loop(args)
            elif cmd == "/testintel":
                self._handle_test_intel(args)
            elif cmd == "/coverage":
                self._handle_coverage(args)
            elif cmd == "/search":
                self._handle_local_search(args)
            elif cmd == "/web":
                self._handle_web(args)
            elif cmd == "/docs":
                self._handle_docs(args)
            elif cmd == "/deps":
                self._handle_deps(args)
            elif cmd == "/sensing":
                self._handle_sensing(args)
            elif cmd == "/types":
                self._handle_types(args)
            elif cmd == "/mojo":
                self._handle_mojo(args)
            elif cmd == "/sql":
                self._handle_sql(args)
            elif cmd == "/config":
                self._handle_config(args)
            elif cmd == "/assets":
                self._handle_assets(args)
            elif cmd == "/langpacks":
                self._handle_langpacks(args)
            elif cmd == "/intelcache":
                self._handle_intelcache(args)
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
        """M-077: /undo — one timeline of edits, commands, checkpoints.

        Bare ``/undo`` undoes the newest timeline entry
        (with no primary agent attached, or the timeline
        gate off, it keeps its original last-edit road
        exactly); ``/undo list`` shows the timeline;
        ``/undo edit`` / ``/undo command`` undo the newest
        entry of a strand, walked from the top;
        ``/undo checkpoint <id>`` restores through the
        M-075 seam; ``/undo <count>`` walks back that many
        entries; ``/undo on`` / ``off`` is the gate.
        """
        from ..core.edits import EditJournal
        from ..core.undo_timeline import (
            TimelineEntry,
            enabled_from_config,
            format_setting_change,
            format_undo_outcome,
            format_undo_timeline,
            parse_undo_args,
        )
        from .llm import AGENT_REGISTRY

        primary = AGENT_REGISTRY.get("Primary")
        root = primary.project_root if primary else self.project_root
        try:
            request = parse_undo_args(args)
        except ValueError as exc:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n{exc}\n")
            return

        def legacy() -> str:
            try:
                return EditJournal(root).undo()
            except Exception as exc:
                return f"Undo failed; no Git reset was performed: {exc}"

        if primary is None:
            if request["action"] == "next" and request["count"] == 1:
                result = legacy()
            elif request["action"] == "kind" \
                    and request.get("kind") == "edit":
                result = legacy()
            else:
                result = ("The undo timeline needs the primary "
                          "agent; only the original last-edit "
                          "/undo is available right now.")
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n{result}\n")
            return
        if request["action"] == "show":
            status = primary.undo_timeline_status()
            entries = [TimelineEntry(**entry)
                       for entry in status["entries"]]
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n{format_undo_timeline(primary.config, entries, checkpoint_wired=status['checkpoint_wired'])}\n")
            return
        if request["action"] == "setting":
            try:
                record = primary.set_undo_timeline(request["enabled"])
                result = format_setting_change(record)
            except (ValueError, KeyError, RuntimeError) as exc:
                result = str(exc)
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n{result}\n")
            return
        if not enabled_from_config(primary.config):
            if request["action"] == "next" and request["count"] == 1:
                result = legacy()
            else:
                result = ("Undo timeline is off — /undo keeps its "
                          "original last-edit behaviour; turn it "
                          "on with /undo on.")
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n{result}\n")
            return
        try:
            if request["action"] == "kind":
                result = format_undo_outcome(
                    primary.undo_kind(request["kind"]))
            elif request["action"] == "checkpoint":
                result = format_undo_outcome(
                    primary.restore_checkpoint_via_seam(
                        request["checkpoint_id"]))
            else:
                messages = []
                for _ in range(request["count"]):
                    record = primary.undo_newest()
                    messages.append(format_undo_outcome(record))
                    if not record.get("changed"):
                        break
                result = "\n".join(messages)
        except ValueError as exc:
            result = str(exc)
        publish_sync("agent_chat_chunk", agent_name="Primary",
                     text=f"\n{result}\n")

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

    def _handle_ollama(self, args: str):
        """M-023: /ollama list|pull|show against the local Ollama server.

        The provider comes from the shared registry; every failure is
        a MythicProviderError whose text already carries its remedy
        (start the server / pull the model), published verbatim.
        Pulling downloads onto the machine, so it is gated like the
        other mutating commands; list/show are read-only.
        """
        from ..core.exceptions import MythicProviderError
        from ..providers.registry import get_provider

        provider = get_provider(
            "ollama",
            host=os.environ.get("OLLAMA_HOST", "http://localhost:11434"))
        sub = (args or "").split()
        action = sub[0].lower() if sub else "list"
        try:
            if action == "list" and len(sub) <= 1:
                snap = provider.discover()
                installed, running = snap["installed"], snap["running"]
                lines = [f"\n[bold cyan]Ollama at {snap['host']}[/bold cyan]"]
                if installed:
                    lines.append("Installed models:")
                    for name in installed:
                        mark = " [green](running)[/green]" \
                            if name in running else ""
                        lines.append(f"  {name}{mark}")
                    if not running:
                        lines.append(
                            "[dim]No model is loaded right now; one "
                            "loads when you chat with it.[/dim]")
                else:
                    lines.append(
                        "No models installed yet. Pull one with "
                        "/ollama pull <model>.")
                text = "\n".join(lines) + "\n"
            elif action == "pull" and len(sub) == 2:
                if not self._policy().authorize(
                        "run_command", {"arguments": sub[1]}):
                    publish_sync(
                        "agent_chat_chunk", agent_name="Primary",
                        text="\nPermission denied for run_command; "
                             "no operation was performed.\n")
                    return
                publish_sync(
                    "agent_chat_chunk", agent_name="Primary",
                    text=f"\nPulling {sub[1]} — this can take a while "
                         "for a large model...\n")
                result = provider.pull_model(sub[1])
                text = f"\n[green]Pull of {sub[1]}: " \
                       f"{result.get('status', 'done')}.[/green]\n"
            elif action == "show" and len(sub) == 2:
                provider.ensure_model(sub[1])
                info = provider.show_model(sub[1])
                details = info.get("details", {}) or {}
                summary = " ".join(
                    p for p in (details.get("family", ""),
                                details.get("parameter_size", "")) if p)
                text = f"\n[bold cyan]{sub[1]}[/bold cyan]" + \
                    (f" — {summary}" if summary else "") + \
                    f"\nModified: {info.get('modified_at', 'unknown')}\n"
            else:
                text = "\n[red]Usage: /ollama [list] | /ollama pull " \
                       "<model> | /ollama show <model>[/red]\n"
        except MythicProviderError as e:
            text = f"\n[red]{e}[/red]\n"
        publish_sync("agent_chat_chunk", agent_name="Primary", text=text)

    #: M-024: /local provider spellings -> registry names.
    _LOCAL_PROVIDERS = {
        "lmstudio": "lmstudio",
        "lm-studio": "lmstudio",
        "llama.cpp": "llama.cpp",
        "llamacpp": "llama.cpp",
        "llama-cpp": "llama.cpp",
        "local-openai": "local-openai",
        "generic": "local-openai",
        "local": "local-openai",
    }

    def _handle_local(self, args: str):
        """M-024: /local — discovery for LM Studio / llama.cpp / any port.

        ``/local`` (or ``/local list``) snapshots every local
        OpenAI-compatible door; a door that is down renders its own
        honest error line (which carries its start remedy) and never
        hides the other doors. ``/local <provider> show <model>``
        gives one model's presence + detail, or the honest
        not-present answer with its remedy. Read-only throughout.
        """
        from ..core.exceptions import MythicProviderError
        from ..providers.registry import get_provider

        parts = (args or "").split()
        if parts and parts[0].lower() in self._LOCAL_PROVIDERS:
            registry_name = self._LOCAL_PROVIDERS[parts[0].lower()]
            rest = parts[1:]
            provider = get_provider(registry_name)
            try:
                if not rest or rest[0].lower() == "list" \
                        and len(rest) <= 1:
                    snap = provider.discover()
                    lines = [f"\n[bold cyan]{registry_name} at "
                             f"{snap['host']}[/bold cyan]"]
                    served = snap.get("served") or []
                    if served:
                        lines.append("Serving: " + ", ".join(served))
                    else:
                        lines.append("Serving: nothing right now.")
                    if snap.get("downloaded") is not None:
                        downloaded = snap["downloaded"]
                        lines.append(
                            "Downloaded: " + (", ".join(downloaded)
                                              if downloaded else "none"))
                    if snap.get("loaded"):
                        lines.append("Loaded: "
                                     + ", ".join(snap["loaded"]))
                    if snap.get("model_path"):
                        lines.append(f"Model file: {snap['model_path']}")
                    text = "\n".join(lines) + "\n"
                elif rest[0].lower() == "show" and len(rest) == 2:
                    provider.ensure_model(rest[1])
                    show = getattr(provider, "show_model", None)
                    if show is not None:
                        info = show(rest[1])
                        bits = " ".join(
                            str(info.get(k)) for k in ("type", "state")
                            if info.get(k))
                        text = f"\n[bold cyan]{rest[1]}[/bold cyan]" + \
                            (f" — {bits}" if bits else "") + \
                            f"\nPresent on {registry_name} at " \
                            f"{provider.base_url}.\n"
                    else:
                        text = f"\n[bold cyan]{rest[1]}[/bold cyan] — " \
                               f"serving on {registry_name} at " \
                               f"{provider.base_url}.\n"
                else:
                    text = "\n[red]Usage: /local [list] | /local " \
                           "<lmstudio|llama.cpp|local-openai> show " \
                           "<model>[/red]\n"
            except MythicProviderError as e:
                text = f"\n[red]{e}[/red]\n"
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=text)
            return
        if parts and parts[0].lower() != "list":
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text="\n[red]Usage: /local [list] | /local "
                     "<lmstudio|llama.cpp|local-openai> show "
                     "<model>[/red]\n")
            return
        lines = ["\n[bold cyan]Local runtimes[/bold cyan]"]
        for registry_name in ("lmstudio", "llama.cpp", "local-openai"):
            provider = get_provider(registry_name)
            try:
                snap = provider.discover()
                served = snap.get("served") or []
                lines.append(
                    f"{registry_name} at {snap['host']}: "
                    + (", ".join(served) if served
                       else "serving nothing right now"))
            except MythicProviderError as e:
                lines.append(f"{registry_name}: {e}")
        publish_sync("agent_chat_chunk", agent_name="Primary",
                     text="\n".join(lines) + "\n")

    #: M-026: how many catalogue rows /gateway list prints before it
    #: points at search — a gateway catalogue runs to hundreds.
    _GATEWAY_LIST_LIMIT = 25

    def _gateway_line(self, entry: dict) -> str:
        """One catalogue row: id, context, modality, prices as reported."""
        bits = []
        if entry.get("context_length"):
            bits.append(f"context {entry['context_length']}")
        if entry.get("modality"):
            bits.append(entry["modality"])
        if entry.get("prompt_price") is not None:
            bits.append(f"in {entry['prompt_price']}/tok")
        if entry.get("completion_price") is not None:
            bits.append(f"out {entry['completion_price']}/tok")
        suffix = " — " + ", ".join(bits) if bits else ""
        return f"  {entry['id']}{suffix}"

    def _handle_gateway(self, args: str):
        """M-026: /gateway — browse the OpenRouter catalogue in-app.

        ``/gateway`` (or ``/gateway list``) prints the first rows of
        the gateway's live catalogue with its full size;
        ``/gateway search <text>`` filters it; ``/gateway show
        <model>`` gives one model's reported facts, or the honest
        not-in-catalogue answer. The kin gateways (groq, together,
        fireworks, xai, mistral) are registry citizens whose live
        catalogues are their own /models doors; this browser reads
        OpenRouter's public door, which needs no key. Read-only.
        """
        from ..core.exceptions import MythicProviderError
        from ..providers.registry import get_provider

        provider = get_provider("openrouter")
        parts = (args or "").split()
        action = parts[0].lower() if parts else "list"
        try:
            if action == "list" and len(parts) <= 1:
                entries = provider.catalogue()
                lines = [f"\n[bold cyan]OpenRouter catalogue at "
                         f"{provider.base_url} — {len(entries)} "
                         "models[/bold cyan]"]
                for entry in entries[:self._GATEWAY_LIST_LIMIT]:
                    lines.append(self._gateway_line(entry))
                if len(entries) > self._GATEWAY_LIST_LIMIT:
                    lines.append(
                        f"[dim]… and {len(entries) - self._GATEWAY_LIST_LIMIT} "
                        "more — narrow it with /gateway search "
                        "<text>.[/dim]")
                text = "\n".join(lines) + "\n"
            elif action == "search" and len(parts) >= 2:
                query = " ".join(parts[1:])
                entries = provider.search_catalogue(query)
                lines = [f"\n[bold cyan]OpenRouter catalogue — "
                         f"{len(entries)} matching {query!r}[/bold cyan]"]
                for entry in entries[:self._GATEWAY_LIST_LIMIT]:
                    lines.append(self._gateway_line(entry))
                if not entries:
                    lines.append(
                        "No model id or name contains that text.")
                text = "\n".join(lines) + "\n"
            elif action == "show" and len(parts) == 2:
                entry = provider.catalogue_entry(parts[1])
                lines = [f"\n[bold cyan]{entry['id']}[/bold cyan]"]
                if entry.get("name"):
                    lines.append(f"Name: {entry['name']}")
                if entry.get("context_length"):
                    lines.append(
                        f"Context: {entry['context_length']} tokens")
                if entry.get("max_completion_tokens"):
                    lines.append(
                        "Max completion: "
                        f"{entry['max_completion_tokens']} tokens")
                if entry.get("modality"):
                    lines.append(f"Modality: {entry['modality']}")
                if entry.get("prompt_price") is not None:
                    lines.append(
                        f"Prompt price: {entry['prompt_price']} per token")
                if entry.get("completion_price") is not None:
                    lines.append(
                        "Completion price: "
                        f"{entry['completion_price']} per token")
                text = "\n".join(lines) + "\n"
            else:
                text = "\n[red]Usage: /gateway [list] | /gateway " \
                       "search <text> | /gateway show <model>[/red]\n"
        except MythicProviderError as e:
            text = f"\n[red]{e}[/red]\n"
        publish_sync("agent_chat_chunk", agent_name="Primary", text=text)

    def _handle_model(self, args: str):
        """M-028: /model — mid-session model/provider switching.

        ``/model`` shows the Primary agent's current selection;
        ``/model <model> [url]`` switches model (and door) on the
        live session; ``/model --provider <name> [--model <model>]
        [--reason <words...>]`` switches provider through the
        M-019 registry. The agent layer owns the switch itself
        (between-turns only, journaled as a session event, session /
        plan / crew preserved); every refusal — unknown provider, a
        native-dialect door the live session cannot speak, a turn
        in flight, a failed save — is published verbatim, and a
        refused switch changes nothing.
        """
        from ..core.model_switch import format_switch_record, parse_switch_args

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_switch_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if not any(request.values()):
            provider = primary.active_provider()
            label = f" via {provider}" if provider else ""
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]Model:[/bold cyan] "
                     f"{primary.config.get('model')}{label} "
                     f"({primary.config.get('base_url')})\n"
                     "[dim]Switch with /model <model> [url] or "
                     "/model --provider <name> — the session, its "
                     "plan and the crew are kept.[/dim]\n")
            return
        try:
            record = primary.switch_model(
                request["model"], provider=request["provider"],
                base_url=request["base_url"], reason=request["reason"])
        except (ValueError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync("agent_chat_chunk", agent_name="Primary",
                     text=f"\n[green]{format_switch_record(record)}[/green]\n")

    def _handle_route(self, args: str):
        """M-029: /route — per-office model routing.

        ``/route`` lists every office with its effective model and
        whether that comes from a role route or the session default;
        ``/route <office>`` shows one office; ``/route <office>
        <model> [url]`` or ``/route <office> --provider <name>
        [--model <model>]`` sets the office's route; ``/route clear
        <office>`` returns it to the session default. The agent
        layer owns the change (validated through the M-028
        resolver, journaled as a session event, saved to config);
        every refusal is published verbatim and changes nothing.
        """
        from ..core.role_routing import (
            format_route_change,
            format_routes,
            parse_route_args,
            resolve_route,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_route_args(args)
        except (ValueError, KeyError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] == "list":
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_routes(primary.config)}[/bold cyan]\n"
                     "[dim]Set one with /route <office> <model> [url] "
                     "or /route <office> --provider <name>; clear one "
                     "with /route clear <office>.[/dim]\n")
            return
        if request["action"] == "show":
            try:
                route = resolve_route(primary.config, request["office"])
                shown = primary.role_route(request["office"])
            except ValueError as e:
                publish_sync("agent_chat_chunk", agent_name="Primary",
                             text=f"\n[red]{e}[/red]\n")
                return
            assert shown["source"] == route.source
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{route.office}:[/bold cyan] "
                     f"{route.describe()}\n")
            return
        try:
            if request["action"] == "clear":
                record = primary.clear_role_route(request["office"])
            else:
                record = primary.set_role_route(
                    request["office"], model=request["model"],
                    provider=request["provider"],
                    base_url=request["base_url"])
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync("agent_chat_chunk", agent_name="Primary",
                     text=f"\n[green]{format_route_change(record)}[/green]\n")

    def _handle_fallback(self, args: str):
        """M-030: /fallback — the fallback chain and its permission.

        ``/fallback`` shows the chain, the standing permission and
        the current door; ``/fallback on`` / ``off`` gives or
        withdraws the standing permission; ``/fallback add <model>
        [url]`` or ``/fallback add --provider <name>`` appends a
        door; ``/fallback clear`` empties the chain. The agent
        layer owns every change (validated through the M-028
        resolver, journaled as a session event, saved to config);
        when a provider later fails, the walk itself is announced
        by the agent in the chat path — never silent.
        """
        from ..core.fallback_chain import (
            chain_from_config,
            format_chain,
            format_fallback_change,
            parse_fallback_args,
            permission_from_config,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_fallback_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] == "show":
            status = primary.fallback_status()
            assert status["permission"] == permission_from_config(
                primary.config)
            assert [(c["model"], c["base_url"]) for c in status["chain"]] == [
                (e.model, e.base_url)
                for e in chain_from_config(primary.config)]
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_chain(primary.config)}[/bold cyan]\n"
                     "[dim]Add a door with /fallback add <model> [url] "
                     "or /fallback add --provider <name>; give standing "
                     "permission with /fallback on.[/dim]\n")
            return
        try:
            if request["action"] == "permission":
                record = primary.set_fallback_permission(request["enabled"])
            elif request["action"] == "clear":
                record = primary.clear_fallback_chain()
            else:
                record = primary.add_fallback_entry(
                    model=request["model"], provider=request["provider"],
                    base_url=request["base_url"])
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync("agent_chat_chunk", agent_name="Primary",
                     text=f"\n[green]{format_fallback_change(record)}[/green]\n")

    def _handle_editformat(self, args: str):
        """M-071: /editformat — edit-format plurality, in plain words.

        ``/editformat`` shows the setting (auto by default),
        the four formats, and the auto picks for the current
        model; ``/editformat <format>`` pins a format (or
        ``auto`` unpins it — journaled by the agent layer);
        ``/editformat <task-kind>`` asks for the pick for
        that kind of work and journals the choice on the
        session with its reason, as the roadmap requires.
        """
        from ..core.edit_formats import (
            format_choice,
            format_edit_formats,
            format_setting_change,
            parse_editformat_args,
            setting_from_config,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_editformat_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] == "show":
            status = primary.edit_format_status()
            assert status["setting"] == setting_from_config(
                primary.config)
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_edit_formats(primary.config)}[/bold cyan]\n"
                     "[dim]Pin a format with /editformat <format>, "
                     "return to auto with /editformat auto, or ask "
                     "for a pick with /editformat <task-kind>.[/dim]\n")
            return
        try:
            if request["action"] == "setting":
                record = primary.set_edit_format(request["value"])
                publish_sync(
                    "agent_chat_chunk", agent_name="Primary",
                    text=f"\n[green]{format_setting_change(record)}[/green]\n")
                return
            record = primary.choose_edit_format(request["task_kind"])
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{format_choice(record['choice'])}[/bold cyan]\n")

    def _handle_hashanchor(self, args: str):
        """M-072: /hashanchor — hash-anchored edits, in plain words.

        ``/hashanchor`` shows the gate (on by default), the
        plain-words explanation, and a small file in anchored
        form; ``/hashanchor on`` / ``off`` changes the gate
        (journaled by the agent layer).
        """
        from ..core.hash_anchored import (
            enabled_from_config,
            format_hash_anchored,
            format_setting_change,
            parse_hashanchor_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_hashanchor_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] == "show":
            status = primary.hash_anchor_status()
            assert status["enabled"] == enabled_from_config(
                primary.config)
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_hash_anchored(primary.config)}[/bold cyan]\n"
                     "[dim]Turn the gate off with /hashanchor off, "
                     "or back on with /hashanchor on.[/dim]\n")
            return
        try:
            record = primary.set_hash_anchored(request["enabled"])
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[green]{format_setting_change(record)}[/green]\n")

    def _handle_repairloop(self, args: str):
        """M-073: /repairloop — the apply-failure repair loop.

        ``/repairloop`` shows the gate (on by default), the
        plain-words explanation, and a worked refusal → packet
        → one-retry example; ``/repairloop on`` / ``off``
        changes the gate (journaled by the agent layer).
        """
        from ..core.apply_repair import (
            enabled_from_config,
            format_apply_repair,
            format_setting_change,
            parse_repairloop_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_repairloop_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] == "show":
            status = primary.repair_loop_status()
            assert status["enabled"] == enabled_from_config(
                primary.config)
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_apply_repair(primary.config)}[/bold cyan]\n"
                     "[dim]Turn the gate off with /repairloop off, "
                     "or back on with /repairloop on.[/dim]\n")
            return
        try:
            record = primary.set_apply_repair(request["enabled"])
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[green]{format_setting_change(record)}[/green]\n")


    def _handle_hunkreview(self, args: str):
        """M-074: /hunkreview — hunk-level review.

        ``/hunkreview`` shows the gate (on by default), the
        plain-words explanation, and a worked accept / reject
        / edit example over a two-hunk diff; ``/hunkreview
        on`` / ``off`` changes the gate (journaled by the
        agent layer).
        """
        from ..core.hunk_review import (
            enabled_from_config,
            format_hunk_review,
            format_setting_change,
            parse_hunkreview_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_hunkreview_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] == "show":
            status = primary.hunk_review_status()
            assert status["enabled"] == enabled_from_config(
                primary.config)
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_hunk_review(primary.config)}[/bold cyan]\n"
                     "[dim]Turn the gate off with /hunkreview off, "
                     "or back on with /hunkreview on.[/dim]\n")
            return
        try:
            record = primary.set_hunk_review(request["enabled"])
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[green]{format_setting_change(record)}[/green]\n")

    def _handle_changeset(self, args: str):
        """M-084: /changeset — multi-file change sets.

        ``/changeset`` shows the gate (on by default), the
        plain-words explanation, and a worked two-file
        accept / reject example with its test evidence
        attached; ``/changeset on`` / ``off`` changes the
        gate (journaled by the agent layer).
        """
        from ..core.change_sets import (
            enabled_from_config,
            format_change_sets,
            format_setting_change,
            parse_changeset_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_changeset_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] == "show":
            status = primary.change_set_status()
            assert status["enabled"] == enabled_from_config(
                primary.config)
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_change_sets(primary.config)}[/bold cyan]\n"
                     "[dim]Turn the gate off with /changeset off, "
                     "or back on with /changeset on.[/dim]\n")
            return
        try:
            record = primary.set_change_sets(request["enabled"])
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[green]{format_setting_change(record)}[/green]\n")

    def _handle_rename(self, args: str):
        """M-085: /rename — rename/move files as first-class edits.

        ``/rename`` shows the gate (on by default), the
        plain-words explanation, and a worked example plan;
        ``/rename on`` / ``off`` changes the gate (journaled
        by the agent layer); ``/rename <old> <new>``
        executes one move through the agent (git mv plus
        the graph's reference updates).
        """
        from ..core.rename_move import (
            enabled_from_config,
            format_move_record,
            format_rename_move,
            format_setting_change,
            parse_rename_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_rename_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] == "show":
            status = primary.rename_move_status()
            assert status["enabled"] == enabled_from_config(
                primary.config)
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_rename_move(primary.config)}[/bold cyan]\n"
                     "[dim]Turn the gate off with /rename off, "
                     "or back on with /rename on.[/dim]\n")
            return
        try:
            if request["action"] in ("on", "off"):
                record = primary.set_rename_move(
                    request["action"] == "on")
                publish_sync(
                    "agent_chat_chunk", agent_name="Primary",
                    text=f"\n[green]{format_setting_change(record)}[/green]\n")
                return
            record = primary.rename_move_file(
                request["source"], request["destination"])
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[green]{format_move_record(record)}[/green]\n")

    def _handle_generated(self, args: str):
        """M-086: /generated - generated-code honesty.

        ``/generated`` shows the gate (on by default), the
        plain-words explanation, and a worked example;
        ``/generated on`` / ``off`` changes the gate
        (journaled by the agent layer); ``/generated
        <path>`` classifies one file from its own face;
        ``/generated mark <path> <generator>`` marks one
        file with its generator's name.
        """
        from ..core.generated_code import (
            enabled_from_config,
            format_generated_code,
            format_generated_record,
            format_setting_change,
            parse_generated_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_generated_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] == "show":
            status = primary.generated_code_status()
            assert status["enabled"] == enabled_from_config(
                primary.config)
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_generated_code(primary.config)}[/bold cyan]\n"
                     "[dim]Turn the gate off with /generated off, "
                     "or back on with /generated on.[/dim]\n")
            return
        try:
            if request["action"] in ("on", "off"):
                record = primary.set_generated_code(
                    request["action"] == "on")
                publish_sync(
                    "agent_chat_chunk", agent_name="Primary",
                    text=f"\n[green]{format_setting_change(record)}[/green]\n")
                return
            if request["action"] == "check":
                data = primary.check_generated_code(request["path"])
            else:
                data = primary.mark_generated_file(
                    request["path"], request["generator"])
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[green]{format_generated_record(data)}[/green]\n")

    def _handle_largefile(self, args: str):
        """M-087: /largefile - large-file and binary care.

        ``/largefile`` shows the gate (on by default), the
        plain-words explanation, and a worked example of
        each road; ``/largefile on`` / ``off`` changes the
        gate (journaled by the agent layer); ``/largefile
        <path>`` classifies one file from its true bytes -
        a large text file also shows its anchored chunk
        plan, and a binary is refused in plain words.
        """
        from ..core.large_file_care import (
            enabled_from_config,
            format_file_care,
            format_large_file_care,
            format_setting_change,
            parse_largefile_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_largefile_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] == "show":
            status = primary.large_file_care_status()
            assert status["enabled"] == enabled_from_config(
                primary.config)
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_large_file_care(primary.config)}[/bold cyan]\n"
                     "[dim]Turn the gate off with /largefile off, "
                     "or back on with /largefile on.[/dim]\n")
            return
        try:
            if request["action"] in ("on", "off"):
                record = primary.set_large_file_care(
                    request["action"] == "on")
                publish_sync(
                    "agent_chat_chunk", agent_name="Primary",
                    text=f"\n[green]{format_setting_change(record)}[/green]\n")
                return
            data = primary.check_large_file(request["path"])
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        text = format_file_care(data)
        if data.get("chunk_plan"):
            text = text + "\n" + data["chunk_plan"]
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[green]{text}[/green]\n")


    def _handle_stash(self, args: str):
        """M-088: /stash - the stash shelf.

        ``/stash`` shows the gate (on by default), the
        plain-words explanation, and the live shelf;
        ``/stash on`` / ``off`` changes the gate
        (journaled by the agent layer); ``/stash shelve
        <name>`` shelves the tree's work-in-progress by
        name and the tree goes back to its base;
        ``/stash restore <name>`` brings it back (a
        moved tree refuses, naming the conflicts);
        ``/stash drop <name>`` drops an entry.
        """
        from ..core.stash_shelf import (
            enabled_from_config,
            format_setting_change,
            format_shelf_entry,
            format_shelf_list,
            format_stash_shelf,
            parse_stash_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_stash_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] == "show":
            status = primary.stash_shelf_status()
            assert status["enabled"] == enabled_from_config(
                primary.config)
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_stash_shelf(primary.config)}[/bold cyan]\n"
                     f"{format_shelf_list(status['entries'])}\n"
                     "[dim]Shelve work with /stash shelve <name>, "
                     "bring it back with /stash restore <name>.[/dim]\n")
            return
        try:
            if request["action"] in ("on", "off"):
                record = primary.set_stash_shelf(
                    request["action"] == "on")
                publish_sync(
                    "agent_chat_chunk", agent_name="Primary",
                    text=f"\n[green]{format_setting_change(record)}[/green]\n")
                return
            if request["action"] == "shelve":
                record = primary.shelve_stash(request["name"])
                text = (f"Shelved {record['name']!r} - the tree is "
                        "back to its base.\n"
                        + format_shelf_entry(record["entry"]))
            elif request["action"] == "restore":
                record = primary.restore_stash(request["name"])
                text = (f"Restored {record['name']!r}: "
                        f"{record['files']} file(s) back in the "
                        "tree, off the shelf.")
            else:
                record = primary.drop_stash(request["name"])
                text = (f"Dropped {record['name']!r} from the "
                        "stash shelf; the tree was not changed.")
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[green]{text}[/green]\n")

    def _handle_patch(self, args: str):
        """M-089: /patch - patch export/import.

        ``/patch`` shows the gate (on by default) and the
        plain-words explanation with a worked example;
        ``/patch on`` / ``off`` changes the gate (journaled
        by the agent layer); ``/patch import <patch file>``
        lands a proven patch file on the real tree, whole
        or not at all; ``/patch export <set name>`` refuses
        plainly - the agent layer holds no stored change
        sets, so export runs through the agent road with
        the set itself.
        """
        from ..core.patch_exchange import (
            enabled_from_config,
            format_patch_exchange,
            format_setting_change,
            parse_patch_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_patch_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] == "show":
            status = primary.patch_exchange_status()
            assert status["enabled"] == enabled_from_config(
                primary.config)
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_patch_exchange(primary.config)}[/bold cyan]\n"
                     "[dim]Import a patch file with /patch import "
                     "<patch file>.[/dim]\n")
            return
        try:
            if request["action"] in ("on", "off"):
                record = primary.set_patch_exchange(
                    request["action"] == "on")
                publish_sync(
                    "agent_chat_chunk", agent_name="Primary",
                    text=f"\n[green]{format_setting_change(record)}[/green]\n")
                return
            if request["action"] == "import":
                record = primary.import_patch_from_file(request["ref"])
                text = (f"Imported patch {record['name']!r} from "
                        f"{record['source']}: {record['applied']} "
                        f"file(s) applied, {record['changed_files']} "
                        "changed.")
            else:
                text = (f"There is no change set named "
                        f"{request['name']!r} held by this session - "
                        "change sets are values the agent layer "
                        "builds and applies (M-084), not a stored "
                        "shelf; export one through the agent road "
                        "(export_patch_to_file) with the set itself. "
                        "Nothing was exported.")
                publish_sync(
                    "agent_chat_chunk", agent_name="Primary",
                    text=f"\n[red]{text}[/red]\n")
                return
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[green]{text}[/green]\n")

    def _handle_editor(self, args: str):
        """M-090: /editor - editor bridges lite.

        ``/editor`` shows the gate (on by default), the
        plain-words explanation, and the editor resolved
        from the environment; ``/editor on`` / ``off``
        changes the gate (journaled by the agent layer);
        ``/editor file <path>`` round-trips a real file
        through the user's editor; ``/editor prompt``
        refuses plainly on this surface - it holds no
        draft, so a prompt round-trip runs through the
        agent road with the draft text itself.
        """
        from ..core.editor_bridge import (
            enabled_from_config,
            format_editor_bridge,
            format_setting_change,
            parse_editor_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_editor_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] == "show":
            status = primary.editor_bridge_status()
            assert status["enabled"] == enabled_from_config(
                primary.config)
            if status["editor"] is not None:
                editor_line = (
                    f"Editor: {status['editor']['name']} "
                    f"(from {status['editor']['source']}: "
                    f"{status['editor']['raw']})")
            else:
                editor_line = f"Editor: none - {status['editor_error']}"
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_editor_bridge(primary.config)}[/bold cyan]\n"
                     f"{editor_line}\n"
                     "[dim]Round-trip a file with /editor file "
                     "<path>.[/dim]\n")
            return
        if request["action"] == "prompt":
            text = ("This surface holds no draft - a prompt "
                    "round-trip runs through the agent road "
                    "(edit_prompt_in_editor) with the draft text "
                    "itself. Nothing was sent.")
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{text}[/red]\n")
            return
        try:
            if request["action"] in ("on", "off"):
                record = primary.set_editor_bridge(
                    request["action"] == "on")
                publish_sync(
                    "agent_chat_chunk", agent_name="Primary",
                    text=f"\n[green]{format_setting_change(record)}[/green]\n")
                return
            record = primary.edit_file_in_editor(request["path"])
            text = (f"Editor round-trip (file) {record['label']}: "
                    f"{record['status']}\n  {record['reason']}")
            if record["status"] == "changed":
                text += "\n  The changed text was written to the file."
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[green]{text}[/green]\n")

    def _handle_diff(self, args: str):
        """M-091: /diff - diff theatre in the TUI.

        ``/diff`` shows the gate (on by default), the
        plain-words explanation, and one demo change
        staged both ways; ``/diff on`` / ``off`` changes
        the gate (journaled by the agent layer);
        ``/diff unified`` / ``side-by-side`` stages the
        demo change in that view through the agent road,
        and ``/diff whitespace`` / ``whitespace off``
        stages it with the whitespace toggle judged.
        """
        from ..core.diff_theatre import (
            enabled_from_config,
            format_diff_theatre,
            format_setting_change,
            parse_diff_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_diff_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] == "show":
            status = primary.diff_theatre_status()
            assert status["enabled"] == enabled_from_config(
                primary.config)
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_diff_theatre(primary.config)}[/bold cyan]\n")
            return
        demo_before = "alpha\nbeta old gamma\ndelta\n"
        demo_after = "alpha\nbeta new gamma\ndelta\n"
        try:
            if request["action"] in ("on", "off"):
                record = primary.set_diff_theatre(
                    request["action"] == "on")
                publish_sync(
                    "agent_chat_chunk", agent_name="Primary",
                    text=f"\n[green]{format_setting_change(record)}[/green]\n")
                return
            if request["action"] == "view":
                record = primary.show_diff_theatre(
                    demo_before, demo_after, view=request["view"])
            else:
                record = primary.show_diff_theatre(
                    demo_before, demo_after,
                    ignore_whitespace=request["ignore_whitespace"])
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[green]{record['rendered']}[/green]\n")

    def _handle_blame(self, args: str):
        """M-092: /blame - blame and history sight.

        ``/blame`` shows the gate (on by default), the
        plain-words explanation, a demo file blamed, and
        its second line explained by blame and journal
        together; ``/blame on`` / ``off`` changes the gate
        (journaled by the agent layer); ``/blame <path>``
        blames the whole file through the agent road and
        ``/blame <path> <line>`` (or ``<path>:<line>``)
        asks why that one line is the way it is.
        """
        from ..core.blame_sight import (
            enabled_from_config,
            format_blame_sight,
            format_setting_change,
            parse_blame_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_blame_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] == "show":
            status = primary.blame_sight_status()
            assert status["enabled"] == enabled_from_config(
                primary.config)
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_blame_sight(primary.config)}[/bold cyan]\n")
            return
        try:
            if request["action"] in ("on", "off"):
                record = primary.set_blame_sight(
                    request["action"] == "on")
                publish_sync(
                    "agent_chat_chunk", agent_name="Primary",
                    text=f"\n[green]{format_setting_change(record)}[/green]\n")
                return
            record = primary.show_blame_sight(
                request["path"], request["line"])
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[green]{record['rendered']}[/green]\n")

    def _handle_massedit(self, args: str):
        """M-093: /massedit - guarded mass edits.

        ``/massedit`` shows the gate (on by default),
        the plain-words explanation, and a demo plan
        dry-run whole - files, hunks, risks, and the
        approval its fingerprint would need;
        ``/massedit on`` / ``off`` changes the gate
        (journaled by the agent layer). Applying a
        mass edit runs through the agent road with
        the plan itself, never through this surface.
        """
        from ..core.mass_edit_guard import (
            enabled_from_config,
            format_mass_edit_guard,
            format_setting_change,
            parse_mass_edit_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_mass_edit_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] == "show":
            status = primary.mass_edit_guard_status()
            assert status["enabled"] == enabled_from_config(
                primary.config)
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_mass_edit_guard(primary.config)}[/bold cyan]\n")
            return
        try:
            record = primary.set_mass_edit_guard(
                request["action"] == "on")
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[green]{format_setting_change(record)}[/green]\n")

    def _handle_posture(self, args: str):
        """M-095: /posture - permission profiles.

        ``/posture`` shows the current posture (the
        status-line sentence itself), every shipped
        posture, and the ToolPolicy mode the current
        one rides as; ``/posture <name>`` changes the
        posture (journaled by the agent layer, the live
        policy rebuilt in the new mode); ``/posture
        custom <name> | <title> | <tools> | <paths> |
        <network> | <commands>`` sets a validated custom
        posture. An unknown name refuses plainly with
        the shipped names listed.
        """
        from ..core.permission_profiles import (
            format_permission_profiles,
            format_profile_change,
            parse_posture_args,
            policy_mode_for,
            stored_profile,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_posture_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] == "show":
            status = primary.permission_profile_status()
            assert status["policy_mode"] == policy_mode_for(
                stored_profile(primary.config))
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_permission_profiles(primary.config)}[/bold cyan]\n")
            return
        try:
            record = primary.set_permission_profile(
                request["profile"])
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[green]{format_profile_change(record)}[/green]\n")

    def _handle_remember(self, args: str):
        """M-096: /remember - remembered approvals.

        ``/remember`` (or ``list`` / ``show``) shows the
        one screen: every remembered approval with its
        exact scope and id, or the plain none;
        ``/remember forget <id>`` revokes the named one
        and ``/remember clear`` revokes all (both
        journaled by the agent layer). Creating one is
        not a /remember verb: an approval is remembered
        only by the user's explicit yes at the approval
        prompt, never silently and never from this
        command's grammar.
        """
        from ..core.remembered_approvals import (
            PLAIN_EXPLANATION,
            USAGE,
            parse_remember_args,
            stored_approvals,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_remember_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] == "list":
            status = primary.remembered_approvals_status()
            assert status["count"] == len(
                stored_approvals(primary.config))
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=(f"\n[bold cyan]Remembered approvals "
                      f"(M-096) - {PLAIN_EXPLANATION}\n\n"
                      f"{status['screen']}\n\n{USAGE}\n"
                      "An approval is remembered only by "
                      "your explicit yes at the approval "
                      "prompt; /remember itself never "
                      "creates one.[/bold cyan]\n"))
            return
        try:
            if request["action"] == "forget":
                record = primary.revoke_remembered_approval(
                    request["id"])
                args_text = " ".join(
                    record["args_pattern"]) or "(no args)"
                message = (
                    f"Revoked remembered approval: "
                    f"{record['command']} {args_text} in "
                    f"{record['path']} [{record['id'][:12]}] - "
                    f"{record['total']} remembered now.")
            else:
                record = primary.clear_remembered_approvals()
                message = (
                    f"Cleared {record['cleared']} remembered "
                    f"approval(s); none remain.")
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[green]{message}[/green]\n")

    def _handle_sandbox(self, args: str):
        """M-097: /sandbox - the OS sandbox (native).

        ``/sandbox`` shows the whole slice (the gate, the
        per-platform truth table, and a sample Linux plan);
        ``on`` / ``off`` steer the gate (journaled by the
        agent layer); ``truth`` shows the platform truth
        table alone; ``plan <command>`` builds one
        command's confinement plan for the current
        platform and ``plan <platform> -- <command>``
        names the platform. Nothing here runs a command -
        running under a plan is the agent layer's
        ``run_os_sandboxed`` road.
        """
        from ..core.os_sandbox import (
            enabled_from_config,
            format_confinement_plan,
            format_gate_change,
            format_platform_truth,
            parse_sandbox_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_sandbox_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] in ("show", "truth", "plan"):
            try:
                if request["action"] == "show":
                    status = primary.os_sandbox_status()
                    assert status["enabled"] == enabled_from_config(
                        primary.config)
                    text = status["screen"]
                elif request["action"] == "truth":
                    text = format_platform_truth()
                else:
                    plan = primary.os_sandbox_plan(
                        request["command"],
                        platform=request["platform"])
                    text = format_confinement_plan(plan)
            except ValueError as e:
                publish_sync("agent_chat_chunk", agent_name="Primary",
                             text=f"\n[red]{e}[/red]\n")
                return
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{text}[/bold cyan]\n")
            return
        try:
            record = primary.set_os_sandbox(request["action"] == "on")
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[green]{format_gate_change(record)}[/green]\n")

    def _handle_network(self, args: str):
        """M-098: /network - the network gates.

        ``/network`` shows the whole slice (the gate and
        its allowlist); ``on`` / ``off`` steer the gate
        (journaled by the agent layer); ``list`` shows the
        allowlist alone; ``check <tool> <host>`` decides one
        reach (a denied reach under the gate is published
        by the agent layer as session news); ``allow <tool>
        <domain>`` adds one allowlist entry. Nothing here
        opens a socket - deciding is the pure layer's work
        and holding the list is the agent layer's.
        """
        from ..core.network_gates import (
            enabled_from_config,
            format_allowlist,
            format_gate_change,
            format_network_decision,
            gates_from_config,
            parse_network_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_network_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] in ("show", "list"):
            try:
                if request["action"] == "show":
                    status = primary.network_gates_status()
                    assert status["enabled"] == enabled_from_config(
                        primary.config)
                    text = status["screen"]
                else:
                    text = format_allowlist(
                        gates_from_config(primary.config).entries)
            except ValueError as e:
                publish_sync("agent_chat_chunk", agent_name="Primary",
                             text=f"\n[red]{e}[/red]\n")
                return
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{text}[/bold cyan]\n")
            return
        try:
            if request["action"] == "check":
                decision = primary.check_network_reach(
                    request["tool"], request["target"])
                text = format_network_decision(decision)
                publish_sync(
                    "agent_chat_chunk", agent_name="Primary",
                    text=f"\n[bold cyan]{text}[/bold cyan]\n")
                return
            if request["action"] == "allow":
                record = primary.add_network_allowlist_entry(
                    request["entry"])
                entry = record["entry"]
                publish_sync(
                    "agent_chat_chunk", agent_name="Primary",
                    text=(f"\n[green]Network allowlist: "
                          f"{entry['tool']}: {entry['domain']} "
                          f"added.[/green]\n"))
                return
            record = primary.set_network_gates(
                request["action"] == "on")
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[green]{format_gate_change(record)}[/green]\n")

    def _handle_pathjail(self, args: str):
        """M-099: /pathjail - the path jail.

        ``/pathjail`` shows the whole slice (the gate,
        the resolved workspace and its grants); ``on`` /
        ``off`` steer the gate (journaled by the agent
        layer); ``grants`` shows the grant list alone;
        ``check <path>`` decides one path (a denied path
        under the gate is published by the agent layer
        as session news); ``grant <abs-path>`` names one
        grant root. Nothing here opens a file - judging
        is the pure layer's work and holding the grants
        is the agent layer's.
        """
        from ..core.path_jail import (
            enabled_from_config,
            format_gate_change,
            format_grants,
            format_jail_decision,
            grants_from_config,
            parse_pathjail_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_pathjail_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] in ("show", "grants"):
            try:
                if request["action"] == "show":
                    status = primary.path_jail_status()
                    assert status["enabled"] == enabled_from_config(
                        primary.config)
                    text = status["screen"]
                else:
                    text = format_grants(
                        grants_from_config(primary.config))
            except ValueError as e:
                publish_sync("agent_chat_chunk", agent_name="Primary",
                             text=f"\n[red]{e}[/red]\n")
                return
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{text}[/bold cyan]\n")
            return
        try:
            if request["action"] == "check":
                decision = primary.check_path_jail(request["path"])
                text = format_jail_decision(decision)
                publish_sync(
                    "agent_chat_chunk", agent_name="Primary",
                    text=f"\n[bold cyan]{text}[/bold cyan]\n")
                return
            if request["action"] == "grant":
                record = primary.add_path_grant(request["grant"])
                publish_sync(
                    "agent_chat_chunk", agent_name="Primary",
                    text=(f"\n[green]Path grant: "
                          f"{record['grant']} added.[/green]\n"))
                return
            record = primary.set_path_jail(request["action"] == "on")
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[green]{format_gate_change(record)}[/green]\n")

    def _handle_plan(self, args: str):
        """M-100: /plan - plan mode perfected.

        ``/plan`` shows the whole slice (the gate and the
        held plan); ``on`` / ``off`` steer the gate
        (journaled by the agent layer); ``approve``
        approves the held plan - the one gate to building;
        ``build`` asks the build gate (a refused build
        under the gate is published by the agent layer as
        session news); ``check <effect>`` decides one tool
        effect (a denied effect under the gate is likewise
        published as session news). Nothing here writes or
        runs anything - judging is the pure layer's work
        and holding the plan is the agent layer's.
        """
        from ..core.plan_mode import (
            enabled_from_config,
            format_gate_change,
            format_plan,
            format_refusal,
            parse_plan_args,
            refusal_for_build,
            refusal_for_effect,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_plan_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] == "show":
            try:
                status = primary.plan_mode_status()
                assert status["enabled"] == enabled_from_config(
                    primary.config)
                text = status["screen"]
            except ValueError as e:
                publish_sync("agent_chat_chunk", agent_name="Primary",
                             text=f"\n[red]{e}[/red]\n")
                return
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{text}[/bold cyan]\n")
            return
        try:
            if request["action"] == "check":
                decision = primary.check_plan_effect(request["effect"])
                if decision == "allow":
                    text = (f"Plan allowed: a {request['effect']} "
                            f"effect is allowed.")
                else:
                    text = format_refusal(
                        refusal_for_effect(
                            enabled_from_config(primary.config),
                            request["effect"])) + "."
                publish_sync(
                    "agent_chat_chunk", agent_name="Primary",
                    text=f"\n[bold cyan]{text}[/bold cyan]\n")
                return
            if request["action"] == "approve":
                plan = primary.approve_current_plan()
                publish_sync(
                    "agent_chat_chunk", agent_name="Primary",
                    text=(f"\n[green]Plan approved: {plan.title} - "
                          f"building is now allowed in plan "
                          f"posture.\n{format_plan(plan)}[/green]\n"))
                return
            if request["action"] == "build":
                if primary.check_plan_build():
                    text = "Building allowed: the build gate is open."
                else:
                    text = format_refusal(
                        refusal_for_build(
                            enabled_from_config(primary.config),
                            primary.current_plan())) + "."
                publish_sync(
                    "agent_chat_chunk", agent_name="Primary",
                    text=f"\n[bold cyan]{text}[/bold cyan]\n")
                return
            record = primary.set_plan_mode(request["action"] == "on")
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[green]{format_gate_change(record)}[/green]\n")

    def _handle_hooks(self, args: str):
        """M-101: /hooks - the full lifecycle.

        /hooks shows every configured hook;
        show <event> (or a bare event word) shows one
        event's hooks; check <event> runs that event's
        enabled hooks for real and reports each verdict -
        a blocking verdict is published by the agent layer
        as session news, with the reason the coder must
        answer. Judging is the pure layer's work and
        running is the agent layer's; nothing here runs a
        script itself.
        """
        from ..core.hooks import (
            format_hooks,
            format_verdict,
            hooks_from_config,
            parse_hooks_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, event = parse_hooks_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if action == "show":
            try:
                if event is None:
                    text = primary.hooks_status()["screen"]
                else:
                    named = [h for h in hooks_from_config(
                        primary.config) if h.event == event]
                    text = format_hooks(named)
            except ValueError as e:
                publish_sync("agent_chat_chunk", agent_name="Primary",
                             text=f"\n[red]{e}[/red]\n")
                return
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{text}[/bold cyan]\n")
            return
        try:
            verdicts = primary.run_hooks(event)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if not verdicts:
            text = (f"No hooks are configured for {event}; "
                    f"nothing ran.")
        else:
            text = "\n".join(format_verdict(v) for v in verdicts)
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_hookpacks(self, args: str):
        """M-102: /hookpacks - hook packs.

        /hookpacks shows the shipped shelf; show <pack>
        (or a bare pack name) shows one pack and the
        hooks it carries; install <pack> installs one
        pack through the agent layer - journal-first,
        the merged hooks stored as plain hook records
        under the M-101 hooks setting, and a pack that
        is already fully installed changes nothing and
        writes nothing. Judging is the pure layer's work
        and storing is the agent layer's; nothing here
        writes a setting itself.
        """
        from ..core.hook_packs import (
            format_pack,
            get_pack,
            parse_hook_packs_args,
        )
        from ..core.hooks import format_hooks

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, pack_name = parse_hook_packs_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if action == "show":
            try:
                if pack_name is None:
                    text = primary.hook_packs_status()["screen"]
                else:
                    pack = get_pack(pack_name)
                    text = (format_pack(pack) + "\n"
                            + format_hooks(list(pack.hooks)))
            except ValueError as e:
                publish_sync("agent_chat_chunk", agent_name="Primary",
                             text=f"\n[red]{e}[/red]\n")
                return
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{text}[/bold cyan]\n")
            return
        try:
            record = primary.install_hook_pack(pack_name)
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if not record["changed"]:
            text = (f"Hook pack {pack_name} is already installed; "
                    f"nothing changed.")
        else:
            text = (f"Hook pack installed: {pack_name} "
                    f"({len(record['added'])} hook(s) added).")
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[green]{text}[/green]\n")

    def _handle_background(self, args: str):
        """M-103: /background - background tasks.

        /background shows the held jobs; show <job> (or
        a bare job id) shows one job; tail [<job>] shows
        one job's live tail (the newest job when no id
        is named); kill <job> records the kill request,
        terminates the real process, and lands the
        cancellation; start <command...> starts the
        command as a real job - split into argv words,
        never run through a shell. When a job finishes,
        the agent layer publishes its completion as
        session news. Judging is the pure layer's work
        and running is the agent layer's; nothing here
        runs a process itself.
        """
        import shlex

        from ..core.background_tasks import (
            format_completion,
            format_job,
            parse_background_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_background_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "show":
                if target is None:
                    text = primary.background_jobs_status()["screen"]
                else:
                    text = format_job(primary.get_background_job(target))
            elif action == "tail":
                text = primary.background_job_tail(target)
            elif action == "kill":
                primary.kill_background_job(target)
                text = format_completion(primary.get_background_job(target))
            else:  # start
                argv = shlex.split(target)
                record = primary.start_background_job(argv)
                job = primary.get_background_job(record["job_id"])
                text = f"Background job started: {format_job(job)}"
        except (KeyError, ValueError, OSError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_keeper(self, args: str):
        """M-104: /keeper - the keeper pattern.

        /keeper shows the held watches, each judged in
        words - active, quiet, or stalled, from its last
        sign of life alone; show <target> (or a bare
        target id) shows one watch; check judges every
        watch now and acts on what is owed - an owed
        intervention is published as session news, and
        a stalled background job is restarted for real
        while its restarts remain; heartbeat <target>
        records a sign of life on one watch. Judging is
        the pure layer's work and restarting is the
        agent layer's; nothing here starts a timer.
        """
        from ..core.keeper import format_watch_target, parse_keeper_args

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_keeper_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "show":
                status = primary.keeper_status()
                if target is None:
                    text = status["screen"]
                else:
                    text = format_watch_target(
                        primary.get_keeper_target(target), status["now"])
            elif action == "check":
                text = primary.keeper_check()["screen"]
            else:  # heartbeat
                primary.keeper_heartbeat(target)
                status = primary.keeper_status()
                text = format_watch_target(
                    primary.get_keeper_target(target), status["now"])
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_schedule(self, args: str):
        """M-105: /schedule - scheduled work.

        /schedule shows the held jobs, each judged in
        words - not due, due, overdue, waiting for
        approval, or disabled, against its own
        recorded last run; show <job> (or a bare job
        id) shows one job's verdict; check judges
        every job now and acts on what is owed - an
        owed due moment is published as session news,
        a due unattended job is carried out for real
        as a background job and its run recorded,
        and a job that needs approval is published
        as waiting and never run. Judging is the pure
        layer's work and running is the agent layer's
        through the M-103 road; nothing here starts
        a timer.
        """
        from ..core.scheduled_work import (
            format_verdict,
            parse_schedule_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_schedule_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "show":
                status = primary.scheduled_work_status()
                if target is None:
                    text = status["screen"]
                else:
                    text = format_verdict(
                        primary.get_scheduled_verdict(
                            target, status["now"]))
            else:  # check
                text = primary.scheduled_check()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_fleet(self, args: str):
        """M-106: /fleet - headless fleet mode.

        /fleet shows the held tasks with their recorded
        verdicts and the fleet verdict with its honest
        exit code; show <task> (or a bare task id) shows
        one task with its verdict; verdict shows the
        fleet verdict alone; resume shows the resume
        plan - what remains to run, what passed and will
        never run again, and what is held back until
        retrying failures is asked for. Judging and
        planning are the pure layer's work; running the
        fleet is the agent layer's fleet_check, carried
        out for real through the M-103 road - nothing
        here starts a run.
        """
        from ..core.fleet_mode import (
            format_fleet_task,
            parse_fleet_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_fleet_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "show":
                status = primary.fleet_status()
                if target is None:
                    text = status["screen"]
                else:
                    text = format_fleet_task(
                        primary.get_fleet_task(target),
                        primary.get_fleet_verdict(target))
            elif action == "verdict":
                text = primary.fleet_status()["verdict_screen"]
            else:  # resume
                text = primary.fleet_resume_plan()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_budgets(self, args: str):
        """M-107: /budgets - budgets as guardrails.

        /budgets shows the held budgets with each
        budget's verdict judged from its recorded
        usage reading - within, warning, or exceeded,
        with the used-of-limit amounts always stated
        in words; show <budget> (or a bare budget id)
        shows one budget with its verdict; check
        judges every held budget now (check <budget>
        judges one) and acts on what is owed - an
        exceeded budget is carried out as a graceful
        pause at this resting point and published as
        a budget_paused session event, never a
        mid-edit death. Judging is the pure layer's
        work; recording real usage from the real
        roads and carrying the pause out are the
        agent layer's. The registry is session state
        held by the agent; it is not a stored setting.
        """
        from ..core.budgets import (
            format_budget,
            parse_budgets_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_budgets_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "show":
                if target is None:
                    text = primary.budget_status()["screen"]
                else:
                    text = format_budget(
                        primary.get_budget(target),
                        primary.get_budget_verdict(target))
            elif target is None:  # check
                text = primary.budget_check()["screen"]
            else:
                text = primary.budget_check(target)["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_halt(self, args: str):
        """M-108: /halt - the kill switch everywhere.

        /halt shows the halts pulled this session
        with each pull's verdict - halted, already
        stopped, or nothing held, per target, in
        words; show <halt> (or a bare halt id) shows
        one halt with its verdict; pull pulls the
        switch on every target and pull <target>
        pulls it on one target alone, carrying the
        halt out through the real roads - held
        background jobs are killed through the M-103
        road (a running crew task rides that same
        road, on its backing job), the coder's own
        cancellation event is set so in-flight work
        stops at the next boundary, and a pending
        approval, which waits on that same event, is
        refused - and the pull is published as a
        kill_switch_pulled session event. Judging is
        the pure layer's work; reading the holdings
        from the real roads and carrying the halt out
        are the agent layer's. The registry is
        session state held by the agent; it is not a
        stored setting.
        """
        from ..core.kill_switch import (
            format_halt,
            parse_halt_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_halt_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "show":
                if target is None:
                    text = primary.kill_switch_status()["screen"]
                else:
                    text = format_halt(
                        primary.get_halt(target),
                        primary.get_halt_verdict(target))
            else:
                spec: dict = {"actor": "user"}
                if target is not None:
                    spec["targets"] = [target]
                text = primary.pull_kill_switch(spec)["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_audit(self, args: str):
        """M-109: /audit - the audit trail.

        /audit shows the session's trail - every tool
        call, approval, edit and command recorded as it
        happened, each stamped with its actor (the
        human, the coder, the crew or a hook); show
        <entry> (or a bare entry id) shows one entry;
        export renders the whole trail as a text export
        for review, naming every held entry in append
        order with the counts by kind and by actor. The
        trail is append-only: no road here edits,
        removes or reorders an entry, and reading it
        records nothing. The registry is session state
        held by the agent; it is not a stored setting.
        """
        from ..core.audit_trail import (
            format_entry,
            parse_audit_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_audit_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "export":
                text = primary.audit_export()["text"]
            elif target is None:
                text = primary.audit_status()["screen"]
            else:
                text = format_entry(primary.get_audit_entry(target))
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_secrets(self, args: str):
        """M-110: /secrets - secret hygiene in action.

        /secrets shows the files screened this session
        with each verdict - clean, or commit refused
        with the secret pattern kinds named (content
        is never shown); show <screening> (or a bare
        screening id) shows one screening; check <file>
        screens one real file in the project now and
        holds the verdict - a refused verdict is
        published as a secret_refusal session event.
        Reading the screenings screens and publishes
        nothing. The registry is session state held by
        the agent; it is not a stored setting.
        """
        from ..core.secret_hygiene import (
            format_screening,
            parse_secrets_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_secrets_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "check":
                text = primary.screen_project_file(target)["screen"]
            elif target is None:
                text = primary.secret_hygiene_status()["screen"]
            else:
                text = format_screening(primary.get_screening(target))
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_doctrine(self, args: str):
        """M-111: /doctrine - the destructive-command doctrine.

        /doctrine shows the commands judged this
        session with each judgement's rung and the
        approval it needs, stated in words; show
        <judgement> (or a bare judgement id) shows one
        judgement; ladder shows the three-rung ladder
        alone; check <command> judges one command now
        and holds the judgement - a costly or
        irreversible judgement is published as a
        destructive_act session event, its headline
        naming an irreversible act's targets in plain
        words first. Reading the judgements judges and
        publishes nothing beyond the check road's own
        judgement. The registry is session state held
        by the agent; it is not a stored setting.
        """
        from ..core.destructive_doctrine import (
            format_judgement,
            format_ladder,
            parse_doctrine_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_doctrine_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "ladder":
                text = format_ladder()
            elif action == "check":
                text = primary.judge_command(target)["screen"]
            elif target is None:
                text = primary.doctrine_status()["screen"]
            else:
                text = format_judgement(primary.get_judgement(target))
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_rollback(self, args: str):
        """M-112: /rollback - the rollback drills.

        /rollback shows the drill results held this
        session with each outcome stated in words;
        show <run> (or a bare run id) shows one run;
        drills shows the drill book alone; run
        <drill> names the one held drill a run would
        exercise, with its recovery road. Reading
        judges and publishes nothing: a result is
        held only when a drill run's reported step
        count is judged through the agent. The
        registry is session state held by the agent;
        it is not a stored setting.
        """
        from ..core.rollback_drills import (
            format_drill,
            format_drills,
            format_result,
            parse_rollback_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_rollback_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "drills":
                text = format_drills()
            elif action == "run":
                text = format_drill(target)
            elif target is None:
                text = primary.rollback_status()["screen"]
            else:
                text = format_result(primary.get_drill_run(target))
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_multirepo(self, args: str):
        """M-113: /multirepo - the multi-repo workspaces.

        /multirepo shows the repos held this session
        with each repo's policy stated in words, and
        the cross-repo change sets held with their
        decision counts; show <set> (or a bare set
        id) shows one set; repos shows the held
        repos alone. Reading registers, builds and
        publishes nothing: a set is held only when a
        cross-repo change is built through the
        agent. The registry is session state held by
        the agent; it is not a stored setting.
        """
        from ..core.multi_repo import (
            format_cross_set,
            format_repos,
            parse_multirepo_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_multirepo_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "repos":
                text = format_repos(primary._multi_repo_registry())
            elif target is None:
                text = primary.multi_repo_status()["screen"]
            else:
                text = format_cross_set(primary.get_cross_repo_set(target))
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_remote(self, args: str):
        """M-114: /remote - remote and SSH work.

        /remote shows the targets held this session
        with the one connection each is reached
        through, and the work plans held with their
        step counts; show <plan> (or a bare plan id)
        shows one plan; targets shows the held
        targets alone. Reading registers, judges and
        publishes nothing: a plan is held only when
        remote work is judged through the agent. The
        registry is session state held by the agent;
        it is not a stored setting.
        """
        from ..core.remote_work import (
            format_targets,
            format_work_plan,
            parse_remote_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_remote_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "targets":
                text = format_targets(primary._remote_work_registry())
            elif target is None:
                text = primary.remote_work_status()["screen"]
            else:
                text = format_work_plan(primary.get_remote_work_plan(target))
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_grace(self, args: str):
        """M-115: /grace - offline and degraded grace.

        /grace shows the degradation records held
        this session, each stating its state and
        everything it lost in plain words; show
        <record> (or a bare record id) shows one
        record; failures shows the three failure
        kinds alone. Reading judges, registers and
        publishes nothing: a record is held only when
        degradation is judged through the agent. The
        registry is session state held by the agent;
        it is not a stored setting.
        """
        from ..core.offline_grace import (
            format_assessment,
            format_failures,
            parse_grace_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_grace_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "failures":
                text = format_failures()
            elif target is None:
                text = primary.grace_status()["screen"]
            else:
                text = format_assessment(primary.get_grace_record(target))
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_moment(self, args: str):
        """M-116: /moment - approval by phone-sized moments.

        /moment shows the approval moments held this
        session, each a single, complete question
        with full context; show <record> (or a bare
        record id) shows one moment; parts shows the
        parts a complete moment must carry alone.
        Reading judges, registers and publishes
        nothing: a moment is held only when an
        approval ask is judged through the agent. The
        registry is session state held by the agent;
        it is not a stored setting.
        """
        from ..core.approval_moments import (
            format_assessment,
            format_parts,
            parse_moment_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_moment_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "parts":
                text = format_parts()
            elif target is None:
                text = primary.approval_moment_status()["screen"]
            else:
                text = format_assessment(primary.get_approval_moment(target))
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_policy(self, args: str):
        """M-119: /policy - policy as code.

        ``/policy`` shows the current policy state
        (the held policy, or the policy the file on
        disk names, or the plain no-policy state);
        ``/policy plan`` shows the data-only plan for
        the file on disk, applying nothing; ``/policy
        sections`` names the sections the file
        carries; ``/policy apply`` loads the file and
        applies its plan through the agent layer's
        journal-first roads. A file that fails
        validation is refused whole and said so
        plainly; no file is a plain no-policy answer.
        """
        from ..core.policy_file import (
            format_plan,
            format_policy_sections,
            parse_policy_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_policy_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] == "show":
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{primary.project_policy_status()['screen']}[/bold cyan]\n")
            return
        if request["action"] == "apply":
            outcome = primary.apply_project_policy()
            style = "red" if outcome["status"] == "refused" else "green"
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[{style}]{outcome['screen']}[/{style}]\n")
            return
        try:
            policy = primary.policy_on_disk()
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]Project policy refused: {e}[/red]\n")
            return
        text = (format_plan(policy)
                if request["action"] == "plan"
                else format_policy_sections(policy))
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_crew(self, args: str):
        """M-121: /crew - agents as files.

        ``/crew`` shows the crew held this session
        (the shipped casting - the existing characters
        as data - when none is held yet); ``/crew show
        <member>`` (or a bare member id) shows one
        member; ``/crew office <office>`` shows the
        member holding one office. Reading registers,
        spawns and publishes nothing: a member is held
        only when it joins through the agent layer,
        and held members spawn through the shipped
        sub-agent road. The registry is session state
        held by the agent; it is not a stored setting.
        """
        from ..core.crew_members import format_member, parse_crew_args

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_crew_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "office":
                text = format_member(
                    primary.crew_member_for_office(target))
            elif target is None:
                text = primary.crew_status()["screen"]
            else:
                text = format_member(primary.find_crew_member(target))
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_offices(self, args: str):
        """M-122: /offices - the six offices formalised.

        ``/offices`` shows the offices held this
        session (the shipped book - the six offices
        formalised as data - when none is held yet);
        ``/offices show <office>`` (or a bare office
        id) shows one office; ``/offices handoffs
        <office>`` shows one office's hand-off
        contracts; ``/offices contract <from> <to>``
        shows the one contract between two offices.
        Reading registers and publishes nothing as
        session news: an office is held only when it
        is taken up through the agent layer, and a
        held office is published as an office session
        event. The registry is session state held by
        the agent; it is not a stored setting.
        ``/offices custom ...`` is the M-123 custom
        offices surface, handled by
        :meth:`_handle_offices_custom` on the pure
        layer's custom parser + formatters.
        """
        from ..core.offices import format_office, parse_offices_args

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        _words = (args or "").strip().split()
        if _words and _words[0].lower() == "custom":
            self._handle_offices_custom(" ".join(_words[1:]))
            return
        try:
            action, target = parse_offices_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "handoffs":
                definition = primary.find_office_definition(target)
                lines = [format_office(definition)]
                for contract in definition.handoffs:
                    lines.append(
                        f"  -> {contract.to_office}: "
                        f"{contract.artifact} - {contract.condition}")
                text = "\n".join(lines)
            elif action == "contract":
                from_office, to_office = target
                contract = primary.office_contract(from_office, to_office)
                text = (f"  {from_office} -> {to_office}: "
                        f"{contract.artifact} - {contract.condition}")
            elif target is None:
                text = primary.offices_status()["screen"]
            else:
                text = format_office(primary.find_office_definition(target))
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_offices_custom(self, args: str):
        """M-123: /offices custom - user-defined offices.

        ``/offices custom`` shows the custom offices
        held this session (the shipped custom book -
        the roadmap's Gatekeeper and Benchmarker
        examples - when none is held yet);
        ``/offices custom show <office>`` (or a bare
        custom office id) shows one office;
        ``/offices custom handoffs <office>`` shows
        one office's hand-off contracts;
        ``/offices custom contract <from> <to>``
        shows the one contract between two offices
        (the from-office is a custom office; the
        target may be a formalised office or a custom
        office). A custom office is a user-defined
        role, not a formalised office and not a cast
        member: nothing here spawns, and spawning
        stays the M-121 crew road's. Reading registers
        and publishes nothing as session news: a custom
        office is held only when it is taken up
        through the agent layer, and a held custom
        office is published as a custom_office session
        event. The registry is session state held by
        the agent; it is not a stored setting.
        """
        from ..core.custom_offices import (
            format_custom_office,
            parse_custom_offices_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_custom_offices_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "handoffs":
                definition = primary.find_custom_office_definition(target)
                lines = [format_custom_office(definition)]
                for contract in definition.handoffs:
                    lines.append(
                        f"  -> {contract.to_office}: "
                        f"{contract.artifact} - {contract.condition}")
                text = "\n".join(lines)
            elif action == "contract":
                from_office, to_office = target
                contract = primary.custom_office_contract(
                    from_office, to_office)
                text = (f"  {from_office} -> {to_office}: "
                        f"{contract.artifact} - {contract.condition}")
            elif target is None:
                text = primary.custom_offices_status()["screen"]
            else:
                text = format_custom_office(
                    primary.find_custom_office_definition(target))
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_worktrees(self, args: str):
        """M-124: /worktrees - parallel worktrees.

        ``/worktrees`` shows the worktree
        assignments held this session (the shipped
        example plan - the M-121 casting dealt one
        worktree each - when none is held yet);
        ``/worktrees show <member>`` (or a bare
        member id) shows one member's assignment;
        ``/worktrees plan`` shows the whole plan
        with its coordinator; ``/worktrees merges``
        shows the coordinator merge plan derived in
        slice order. Reading registers and
        publishes nothing as session news: an
        assignment is held only when it is taken up
        through the agent layer, and a held
        assignment is published as a
        worktree_assignment session event. This
        road runs no git command and creates no
        worktree: the registry holds the plan as
        data, and spawning stays the M-121 crew
        road's. The registry is session state held
        by the agent; it is not a stored setting.
        """
        from ..core.worktrees import (
            format_assignment,
            format_assignments,
            format_merge_plan,
            parse_worktrees_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_worktrees_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "plan":
                plan = primary.worktree_plan()
                text = (format_assignments(plan)
                        + f"\nCoordinator: {plan.coordinator} - "
                        "the coordinator merges, and holds no "
                        "worktree in the plan.")
            elif action == "merges":
                text = format_merge_plan(primary.worktree_plan())
            elif target is None:
                text = primary.worktrees_status()["screen"]
            else:
                text = format_assignment(
                    primary.find_worktree_assignment(target))
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_dealing(self, args: str):
        """M-125: /dealing - task dealing.

        ``/dealing`` shows the dealt assignments
        held this session (the shipped example
        dealing - the next ten roadmap slices dealt
        to the M-121 casting - when none is held
        yet); ``/dealing show <member>`` (or a bare
        member id) shows one member's assignments;
        ``/dealing plan`` shows the whole plan with
        its dealer; ``/dealing loads`` shows the
        crew's loads from what the session holds.
        Reading registers and publishes nothing as
        session news: an assignment is held only
        when it is dealt through the agent layer,
        and a held assignment is published as a
        task_dealing session event. This road starts
        no crew and spawns nothing: the registry
        holds the dealing as data, and there is no
        Part VIII board yet - this surface is where
        the dealing is visible. The registry is
        session state held by the agent; it is not
        a stored setting.
        """
        from ..core.task_dealing import (
            format_assignments,
            format_loads,
            format_tasks,
            parse_dealing_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_dealing_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "plan":
                plan = primary.dealing_plan()
                text = (format_tasks(plan)
                        + f"\nDealer: {plan.dealer} - "
                        "the dealer deals by office fit and "
                        "current load, and the human may "
                        "re-deal any slice.")
            elif action == "loads":
                text = format_loads(primary.dealing_loads())
            elif target is None:
                text = primary.task_dealing_status()["screen"]
            else:
                text = format_assignments(
                    primary.find_dealt_assignments(target))
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_comms(self, args: str):
        """M-126: /comms - crew comms.

        ``/comms`` shows the hand-offs held this
        session (the shipped example ledger - six
        hand-offs among the M-121 casting - when none
        is held yet); ``/comms show <member>`` (or a
        bare member id, or ``human``) shows one
        member's hand-offs; ``/comms ask`` shows the
        one batched ask of the questions waiting for
        the human, each with its full context;
        ``/comms kinds`` shows the hand-off kinds.
        Reading registers and publishes nothing as
        session news: a hand-off is held only when it
        is handed through the agent layer, and a held
        hand-off is published as a crew_handoff
        session event, a batched ask as ONE
        human_question_batch session event. This road
        spawns no crew and delivers no message: the
        registry holds the hand-offs as data, and
        there is no Part VIII board yet - this surface
        is where the hand-offs and the batch are
        visible. The registry is session state held
        by the agent; it is not a stored setting.
        """
        from ..core.crew_comms import (
            format_handoffs,
            format_human_batch,
            format_kinds,
            parse_comms_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_comms_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "ask":
                text = format_human_batch(
                    primary.human_question_batch())
            elif action == "kinds":
                text = format_kinds()
            elif target is None:
                text = primary.crew_comms_status()["screen"]
            else:
                text = format_handoffs(
                    primary.find_handoffs(target))
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_deadlock(self, args: str):
        """M-127: /deadlock - cycle and deadlock watch.

        ``/deadlock`` shows the findings of the watch
        held this session (the shipped example watch -
        five delegations and five claims among the
        M-121 casting, yielding exactly three findings,
        one of each kind - when none is held yet);
        ``/deadlock show <member>`` (or a bare member
        id) shows one member's findings; ``/deadlock
        kinds`` shows the finding kinds. Reading
        registers and publishes nothing as session
        news: evidence is held only when it is given
        through the agent layer, and held evidence is
        published as a crew_delegation / crew_claim
        session event, each finding as a
        deadlock_finding session event and each report
        as ONE deadlock_report session event. This
        road spawns no crew, stops no member and runs
        no git: the registry holds the evidence as
        data, and there is no Part VIII board yet -
        this surface is where the findings are
        visible. The registry is session state held
        by the agent; it is not a stored setting.
        """
        from ..core.deadlock_watch import (
            format_findings,
            format_kinds,
            parse_deadlock_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_deadlock_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "kinds":
                text = format_kinds()
            elif target is None:
                text = primary.deadlock_status()["screen"]
            else:
                text = format_findings(
                    primary.find_findings(target))
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_merge(self, args: str):
        """M-128: /merge - merge discipline.

        ``/merge`` shows the verdicts of the plan
        held this session (the shipped example plan -
        seven steps and five merges among the M-121
        casting, yielding exactly three verdicts, one
        of each kind - when none is held yet);
        ``/merge show <member>`` (or a bare member id)
        shows one member's verdicts; ``/merge lines``
        shows every line's state; ``/merge kinds``
        shows the verdict kinds. Reading registers
        and publishes nothing as session news:
        evidence is held only when it is given through
        the agent layer, and held evidence is
        published as a merge_step / merge_attempt
        session event, each verdict as a merge_verdict
        session event and each report as ONE
        merge_report session event. This road executes
        no git, performs no merge and spawns or stops
        no crew: the registry holds the evidence as
        data, and there is no Part VIII board yet -
        this surface is where the verdicts are
        visible. The registry is session state held by
        the agent; it is not a stored setting.
        """
        from ..core.merge_discipline import (
            format_kinds,
            format_lines,
            format_verdicts,
            parse_merge_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_merge_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "kinds":
                text = format_kinds()
            elif action == "lines":
                text = format_lines(primary.merge_report())
            elif target is None:
                text = primary.merge_status()["screen"]
            else:
                text = format_verdicts(
                    primary.find_verdicts(target))
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_hetero(self, args: str):
        """M-129: /hetero - heterogeneous crews.

        ``/hetero`` shows the verdicts of the crew
        plan held this session (the shipped example
        plan - four assignments, two budgets and two
        readings among the M-121 casting, yielding
        exactly three verdicts, one of each kind -
        when none is held yet); ``/hetero show
        <member>`` (or a bare member id) shows one
        member's verdicts; ``/hetero routes`` shows
        every route's state; ``/hetero kinds`` shows
        the verdict kinds. Reading registers and
        publishes nothing as session news: evidence
        is held only when it is given through the
        agent layer, and held evidence is published
        as a hetero_assignment / hetero_reading
        session event, each verdict as a
        hetero_verdict session event and each report
        as ONE hetero_report session event. This
        road spawns no crew, calls no real provider
        and performs no routing or billing: the
        registry holds the evidence as data, and
        there is no Part VIII board yet - this
        surface is where the verdicts are visible.
        The registry is session state held by the
        agent; it is not a stored setting.
        """
        from ..core.heterogeneous_crews import (
            format_kinds,
            format_routes,
            format_verdicts,
            parse_hetero_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_hetero_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "kinds":
                text = format_kinds()
            elif action == "routes":
                text = format_routes(primary.hetero_report())
            elif target is None:
                text = primary.hetero_status()["screen"]
            else:
                text = format_verdicts(
                    primary.find_hetero_verdicts(target))
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_veto(self, args: str):
        """M-130: /veto - the Auditor's veto.

        ``/veto`` shows the verdicts of the veto
        ledger held this session (the shipped example
        ledger - three cases, six checks and five
        results among the Part VI slices, kept by the
        auditor, yielding exactly two verdicts, one
        of each kind - when none is held yet);
        ``/veto show <slice>`` (or a bare slice id)
        shows one slice's verdicts; ``/veto gates``
        shows every case's gate state; ``/veto kinds``
        shows the verdict kinds. Reading registers and
        publishes nothing as session news: evidence
        is held only when it is given through the
        agent layer, and held evidence is published
        as a veto_case / veto_check / veto_result
        session event, each verdict as a veto_verdict
        session event and each report as ONE
        veto_report session event. This road runs no
        check, executes no test suite and banks
        nothing: the registry holds the evidence as
        data, and there is no Part VIII board yet -
        this surface is where the verdicts are
        visible. The registry is session state held
        by the agent; it is not a stored setting.
        """
        from ..core.auditor_veto import (
            format_gates,
            format_kinds,
            format_verdicts,
            parse_veto_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_veto_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "kinds":
                text = format_kinds()
            elif action == "gates":
                text = format_gates(primary.veto_report())
            elif target is None:
                text = primary.veto_status()["screen"]
            else:
                text = format_verdicts(
                    primary.find_veto_verdicts(target))
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_swarm(self, args: str):
        """M-131: /swarm - research swarms.

        ``/swarm`` shows the swarm held this session
        (the shipped example swarm - one
        cartographer-led question, three assignments
        and three findings, yielding one complete
        digest on three sources - when none is held
        yet); ``/swarm show <member>`` (or a bare
        member id) shows one member's finding;
        ``/swarm digest`` shows the digested answer
        with its sources; ``/swarm sources`` shows
        the digest's sources; ``/swarm kinds`` shows
        the focus kinds. Reading registers and
        publishes nothing as session news: pieces
        are held only when they are given through
        the agent layer, and held pieces are
        published as a swarm_question /
        swarm_assignment / swarm_finding session
        event, each digest report as ONE
        swarm_digest session event. This road runs
        no research, calls no model and spawns no
        crew: the registry holds the swarm as data,
        and there is no Part VIII board yet - this
        surface is where the digest is visible. The
        registry is session state held by the agent;
        it is not a stored setting.
        """
        from ..core.research_swarms import (
            digest_plain_words,
            format_finding,
            format_focus_kinds,
            parse_swarm_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_swarm_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "kinds":
                text = format_focus_kinds()
            elif action == "digest":
                digest = primary.swarm_digest()
                lines = [digest_plain_words(digest), "Sources:"]
                lines.extend(
                    f"- {name}" for name in digest.sources)
                text = "\n".join(lines)
            elif action == "sources":
                digest = primary.swarm_digest()
                text = "\n".join(
                    f"- {name}" for name in digest.sources) \
                    if digest.sources \
                    else "No sources are cited yet."
            elif target is None:
                text = primary.swarm_status()["screen"]
            else:
                text = "\n".join(
                    format_finding(finding)
                    for finding
                    in primary.find_swarm_findings(target))
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_panel(self, args: str):
        """M-132: /panel - review panels.

        ``/panel`` shows the panel held this session
        (the shipped example panel - the
        session-branching restore guard, approved by
        the auditor on anthropic/claude-sonnet-4-5
        and held to request_changes by the guardian
        on ollama/llama3.1, a disagreement surfaced -
        when none is held yet); ``/panel show
        <reviewer>`` (or a bare reviewer id) shows
        one reviewer's review; ``/panel outcome``
        shows the derived outcome with both
        positions named; ``/panel verdicts`` shows
        the positions the panel holds; ``/panel
        kinds`` shows the verdict kinds. Reading
        registers and publishes nothing as session
        news: pieces are held only when they are
        given through the agent layer, and held
        pieces are published as a panel_change /
        panel_review session event, each outcome
        report as ONE panel_outcome session event.
        This road runs no review, calls no model,
        executes no change and spawns no crew: the
        registry holds the panel as data, and there
        is no Part VIII board yet - this surface is
        where the outcome is visible. The registry
        is session state held by the agent; it is
        not a stored setting.
        """
        from ..core.review_panels import (
            format_review,
            format_verdict_kinds,
            outcome_plain_words,
            parse_panel_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_panel_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "kinds":
                text = format_verdict_kinds()
            elif action == "outcome":
                outcome = primary.panel_outcome()
                lines = [outcome_plain_words(outcome)]
                if outcome.reviewers:
                    lines.append("Positions:")
                    lines.extend(
                        f"- {r} holds {v}" for r, v in zip(
                            outcome.reviewers,
                            outcome.verdicts))
                text = "\n".join(lines)
            elif action == "verdicts":
                outcome = primary.panel_outcome()
                text = "\n".join(
                    f"- {r}: {v}" for r, v in zip(
                        outcome.reviewers,
                        outcome.verdicts)) \
                    if outcome.verdicts \
                    else "No verdicts are held yet."
            elif target is None:
                text = primary.panel_status()["screen"]
            else:
                text = "\n".join(
                    format_review(review)
                    for review
                    in primary.find_panel_reviews(target))
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_memory(self, args: str):
        """M-133: /memory - crew memory.

        ``/memory`` shows the memory held this
        session (the shipped example memory - the
        auditor's broken-checkpoint-chain fact, the
        guardian's portaudio-env-import fact and the
        scribe's verify-remote-moved fact - when
        none is held yet); ``/memory show <member>``
        (or a bare member id) shows one member's
        notebook; ``/memory search <words>`` searches
        every notebook at once; ``/memory tag
        <tag>`` shows the entries carrying one tag;
        ``/memory entry <entry-id>`` shows one
        entry; ``/memory members`` lists the
        notebook holders. Reading registers and
        publishes nothing as session news: entries
        are held only when they are given through
        the agent layer, and held entries are
        published as a crew_memory_entry session
        event, each memory report as ONE crew_memory
        session event. This road persists nothing,
        syncs nothing, calls no model and spawns no
        crew: the registry holds the memory as data,
        and there is no Part VIII board yet - this
        surface is where the memory is visible. The
        registry is session state held by the agent;
        it is not a stored setting.
        """
        from ..core.crew_memory import (
            format_entry,
            format_notebook,
            parse_memory_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_memory_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "members":
                memory = primary.crew_memory()
                text = "\n".join(
                    f"- {member}" for member in memory.members()) \
                    if memory.members() \
                    else "No notebooks are held yet."
            elif action == "search":
                found = primary.search_crew_memory(target)
                text = "\n".join(
                    format_entry(entry) for entry in found) \
                    if found else "No facts match that search."
            elif action == "tag":
                found = primary.find_memory_entries_by_tag(target)
                text = "\n".join(
                    format_entry(entry) for entry in found) \
                    if found else "No facts match that search."
            elif action == "entry":
                text = format_entry(
                    primary.get_memory_entry(target))
            elif target is None:
                text = primary.crew_memory_status()["screen"]
            else:
                text = format_notebook(
                    primary.crew_memory().notebook_for(target))
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_standup(self, args: str):
        """M-134: /standup - stand-ups.

        ``/standup`` shows the stand-up held this
        session (the shipped example stand-up - five
        items at the M-133 slice boundary across
        done, doing, blocked and needs-you - when
        none is held yet); ``/standup digest`` shows
        the digest derived from its entries;
        ``/standup done`` / ``doing`` / ``blocked`` /
        ``needs-you`` show one state's section;
        ``/standup entry <entry-id>`` shows one
        entry; ``/standup kinds`` lists the four
        states. Reading registers and publishes
        nothing as session news: entries are held
        only when they are given through the agent
        layer, and held entries are published as a
        stand_up_entry session event, each digest
        report as ONE stand_up_digest session event.
        This road schedules nothing, sends nothing,
        posts nothing, calls no model and persists
        nothing: the registry holds the stand-up as
        data, and there is no Part VIII board yet -
        this surface is where the digest is visible.
        The registry is session state held by the
        agent; it is not a stored setting.
        """
        from ..core.stand_ups import (
            format_digest,
            format_entries,
            format_entry,
            format_status_kinds,
            parse_stand_up_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_stand_up_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "kinds":
                text = format_status_kinds()
            elif action == "digest":
                text = format_digest(primary.stand_up())
            elif action == "section":
                text = format_entries(primary.stand_up(), target)
            elif action == "entry":
                text = format_entry(
                    primary.get_stand_up_entry(target))
            else:
                text = primary.stand_up_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_crewsize(self, args: str):
        """M-135: /crewsize - crew sizing honesty.

        ``/crewsize`` shows the sizing book held this
        session (the shipped example book - four cases
        at the M-134 slice boundary covering solo,
        pair, crew and full-crew - when none is held
        yet); ``/crewsize recommend <case-id>`` shows
        one case's derived recommendation;
        ``/crewsize case <case-id>`` shows one case;
        ``/crewsize solo`` / ``pair`` / ``crew`` /
        ``full-crew`` show one size band;
        ``/crewsize kinds`` lists the four size bands.
        Reading registers and publishes nothing as
        session news: cases are held only when they
        are given through the agent layer, and held
        cases are published as a crew_sizing_case
        session event, each sizing report as ONE
        crew_sizing_recommendation_set session event.
        This road spawns nothing, sizes no live crew,
        persists nothing, calls no model and claims
        no board: the registry holds the sizing as
        data, and there is no Part VIII board yet -
        this surface is where the sizing is visible.
        The registry is session state held by the
        agent; it is not a stored setting.
        """
        from ..core.crew_sizing import (
            format_shape,
            format_shapes,
            format_size_kinds,
            parse_crew_size_args,
            recommendation_plain_words,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_crew_size_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "kinds":
                text = format_size_kinds()
            elif action == "recommend":
                text = recommendation_plain_words(
                    primary.get_sizing_case(target))
            elif action == "case":
                text = format_shape(primary.get_sizing_case(target))
            elif action == "band":
                text = format_shapes(primary.crew_sizing(), target)
            else:
                text = primary.crew_sizing_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_voices(self, args: str):
        """M-136: /voices - agent character voices.

        ``/voices`` shows the voice book held this
        session (the shipped example book - four
        members of the house cast at the M-135 slice
        boundary, one in each register - when none is
        held yet); ``/voices profile <member-id>``
        shows one member's voice; ``/voices report
        <report-id>`` shows one report; ``/voices
        plain`` / ``warm`` / ``wry`` / ``grim`` show
        one register's voices; ``/voices registers``
        lists the four registers. Reading registers
        and publishes nothing as session news: voices
        are held only when they are given through the
        agent layer, and held voices are published as
        a character_voice_profile session event, each
        voice report as ONE character_voice_report
        session event. This road generates nothing,
        persists nothing, calls no model and claims
        no board: the registry holds the voices as
        data, and there is no Part VIII board yet -
        this surface is where the voices are visible.
        The registry is session state held by the
        agent; it is not a stored setting.
        """
        from ..core.character_voices import (
            format_profile,
            format_profiles,
            format_registers,
            format_report,
            parse_voice_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_voice_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "registers":
                text = format_registers()
            elif action == "profile":
                text = format_profile(primary.get_voice_profile(target))
            elif action == "report":
                text = format_report(primary.voice_report(target))
            elif action == "register":
                text = format_profiles(primary.character_voices(), target)
            else:
                text = primary.character_voices_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_externals(self, args: str):
        """M-137: /externals - external agents as crew.

        ``/externals`` shows the seat book held this
        session (the shipped example book - two
        outside agents at the M-136 slice boundary,
        one under each budget scope - when none is
        held yet); ``/externals seat <member-id>``
        shows one member's seat; ``/externals check
        <member-id>`` derives one seat's check;
        ``/externals mcp`` shows the seats riding the
        MCP transport; ``/externals transports``
        lists the transports. Reading registers and
        publishes nothing as session news: seats are
        held only when they are given through the
        agent layer, and held seats are published as
        an external_seat session event. This road
        opens no MCP session, spawns no agent,
        persists nothing, calls no model and claims
        no board: the registry holds the seats as
        data, and there is no Part VIII board yet -
        this surface is where the seats are visible.
        The registry is session state held by the
        agent; it is not a stored setting.
        """
        from ..core.external_agents import (
            format_check,
            format_seat,
            format_seats,
            format_transports,
            parse_external_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_external_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "transports":
                text = format_transports()
            elif action == "seat":
                text = format_seat(primary.get_external_seat(target))
            elif action == "check":
                text = format_check(primary.external_seat_check(target))
            elif action == "transport":
                text = format_seats(primary.external_agents(), target)
            else:
                text = primary.external_agents_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_replay(self, args: str):
        """M-138: /replay - crew replay.

        ``/replay`` shows the replay book held this
        session (the shipped example book - five
        hand-offs at the M-137 slice boundary and one
        pinned trace - when none is held yet);
        ``/replay step <step-id>`` shows one step;
        ``/replay trace <step-id>`` derives the trace
        of the decision that step carries. Reading
        registers and publishes nothing as session
        news: steps are held only when they are given
        through the agent layer, and held steps are
        published as a crew_replay_step session event.
        This road reads no live journal, re-executes
        no step, spawns no agent, persists nothing,
        calls no model and claims no board: the
        registry holds the steps as data, and there is
        no Part VIII board yet - this surface is where
        the replay is visible. The registry is session
        state held by the agent; it is not a stored
        setting.
        """
        from ..core.crew_replay import (
            format_step,
            format_steps,
            format_trace,
            parse_replay_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_replay_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "step":
                text = format_step(primary.get_replay_step(target))
            elif action == "trace":
                text = format_trace(primary.replay_trace(target))
            else:
                text = primary.crew_replay_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_foster(self, args: str):
        """M-139: /foster - failure fostering.

        ``/foster`` shows the fostering book held this
        session (the shipped example book - the M-139
        task dealt to forge_worker and the M-138 task
        dealt to scribe, three reports, one pinned
        re-deal and one pinned escalation - when none
        is held yet); ``/foster report <report-id>``
        shows one failure report; ``/foster redeal
        <slice-id>`` shows the re-deal the book holds
        for that slice; ``/foster escalation
        <report-id>`` derives the escalation of that
        report's failure. Reading registers and
        publishes nothing as session news: dealings
        and reports are held only when they are given
        through the agent layer, and held reports are
        published as a failure_report session event.
        This road re-deals no task to a live agent,
        delivers no escalation, spawns no agent,
        persists nothing, calls no model and claims no
        board: the registry holds the fostering as
        data, and there is no Part VIII board yet -
        this surface is where the fostering is
        visible. The registry is session state held by
        the agent; it is not a stored setting.
        """
        from ..core.failure_fostering import (
            format_escalation,
            format_redeal,
            format_report,
            parse_fostering_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_fostering_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "report":
                text = format_report(primary.get_failure_report(target))
            elif action == "redeal":
                book = primary.failure_fostering()
                redeal = None
                if book is not None:
                    for held_redeal in book.redeals:
                        if held_redeal.slice_id == target:
                            redeal = held_redeal
                            break
                if redeal is None:
                    raise KeyError(
                        f"no re-deal in the book: {target!r}")
                text = format_redeal(redeal)
            elif action == "escalation":
                text = format_escalation(
                    primary.fostering_escalation(target))
            else:
                text = primary.failure_fostering_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_costcourt(self, args: str):
        """M-140: /costcourt - cost court.

        ``/costcourt`` shows the court book held this
        session (the shipped example book - five run
        records at the M-139 slice boundary and the
        Scribe's ledger of them - when none is held
        yet); ``/costcourt entry <entry-id>`` shows
        one run record; ``/costcourt member
        <member-id>`` shows one member's records;
        ``/costcourt slice <slice-id>`` shows one
        slice's records; ``/costcourt ledger`` shows
        the Scribe's ledger derived from the whole
        book. Reading registers and publishes nothing
        as session news: records are held only when
        they are given through the agent layer, and
        held records are published as a
        cost_court_entry session event. This road
        calls no model, bills no one, charges nothing,
        persists nothing and claims no board: the
        registry holds the court as data, and there
        is no Part VIII board yet - this surface is
        where the court is visible. The registry is
        session state held by the agent; it is not a
        stored setting.
        """
        from ..core.cost_court import (
            format_entries,
            format_entry,
            format_ledger,
            parse_cost_court_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_cost_court_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "entry":
                text = format_entry(primary.get_cost_entry(target))
            elif action == "member":
                text = format_entries(primary.cost_court(), target)
            elif action == "slice":
                held = primary.cost_court().entries_on(target)
                if held:
                    text = "\n".join(format_entry(e) for e in held)
                else:
                    text = "No run records are held."
            elif action == "ledger":
                text = format_ledger(primary.scribe_ledger())
            else:
                text = primary.cost_court_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_dogfood(self, args: str):
        """M-141: /dogfood - the Mythic Coder building itself.

        ``/dogfood`` shows the dogfood book held this
        session (the shipped example book - six build
        records at the M-140 slice boundary and the
        coordinator's ledger of them - when none is held
        yet); ``/dogfood entry <entry-id>`` shows
        one build record; ``/dogfood member
        <member-id>`` shows one member's records;
        ``/dogfood slice <slice-id>`` shows one
        slice's records; ``/dogfood part
        <part-number>`` shows one part's report;
        ``/dogfood ledger`` shows the coordinator's
        ledger derived from the whole book. Reading
        registers and publishes nothing as session
        news: records are held only when they are
        given through the agent layer, and held
        records are published as a dogfood_entry
        session event. This road builds nothing live,
        runs no crew, calls no model, spawns no agent,
        merges or banks nothing, persists nothing and
        claims no board: the registry holds the dogfood
        as data, no build here claims a build happened
        live, and there is no Part VIII board yet -
        this surface is where the dogfood is visible.
        The registry is session state held by the
        agent; it is not a stored setting.
        """
        from ..core.dogfood import (
            format_entries,
            format_entry,
            format_ledger,
            format_report,
            parse_dogfood_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_dogfood_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "entry":
                text = format_entry(primary.get_dogfood_entry(target))
            elif action == "member":
                text = format_entries(primary.dogfood(), target)
            elif action == "slice":
                held = primary.dogfood().entries_on(target)
                if held:
                    text = "\n".join(format_entry(e) for e in held)
                else:
                    text = "No build records are held."
            elif action == "part":
                text = format_report(primary.dogfood_report(target))
            elif action == "ledger":
                text = format_ledger(primary.coordinator_ledger())
            else:
                text = primary.dogfood_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_solo(self, args: str):
        """M-142: /solo - solo mode dignity.

        ``/solo`` shows the solo mode book held this
        session (the shipped example book - eight
        capability records at the M-141 slice boundary
        and the parity ledger of them - when none is
        held yet); ``/solo capability
        <capability-id>`` shows one capability record;
        ``/solo member <member-id>`` shows the records
        one member amplifies; ``/solo report
        <member-id>`` shows one member's amplification
        report; ``/solo ledger`` shows the parity
        ledger derived from the whole book. Reading
        registers and publishes nothing as session
        news: records are held only when they are
        given through the agent layer, and held
        records are published as a solo_capability
        session event. This road disables no crew,
        spawns no agent, runs no agent, calls no model,
        persists nothing and claims no board: the
        registry holds the solo mode as data, no record
        here claims a crew was ever switched off or
        on, and there is no Part VIII board yet - this
        surface is where the solo mode is visible. The
        registry is session state held by the agent;
        it is not a stored setting.
        """
        from ..core.solo_mode import (
            format_capabilities,
            format_capability,
            format_ledger,
            format_report,
            parse_solo_mode_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_solo_mode_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "capability":
                text = format_capability(primary.get_solo_capability(target))
            elif action == "member":
                text = format_capabilities(primary.solo_mode(), target)
            elif action == "report":
                text = format_report(primary.solo_mode_report(target))
            elif action == "ledger":
                text = format_ledger(primary.parity_ledger())
            else:
                text = primary.solo_mode_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_templates(self, args: str):
        """M-143: /templates - crew templates.

        ``/templates`` shows the crew template book
        held this session (the shipped example book -
        four template records at the M-142 slice
        boundary, the roadmap's four named formations,
        and its pinned index - when none is held yet);
        ``/templates template <template>`` shows one
        formation record, summoned by name;
        ``/templates member <member-id>`` shows the
        formations one member stands in; ``/templates
        roster <template>`` shows one formation's
        derived roster; ``/templates index`` shows the
        template index derived from the whole book.
        Reading registers and publishes nothing as
        session news: records are held only when they
        are given through the agent layer, and held
        records are published as crew_template,
        crew_formation_roster and crew_template_index
        session events. This road summons no crew,
        spawns no agent, runs no agent, calls no model,
        persists nothing and claims no board: the
        registry holds the templates as data, no record
        here claims a crew was ever summoned or run,
        and there is no Part VIII board yet - this
        surface is where the crew templates are
        visible. The registry is session state held by
        the agent; it is not a stored setting.
        """
        from ..core.crew_templates import (
            format_index,
            format_roster,
            format_template,
            format_templates,
            parse_crew_templates_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_crew_templates_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "template":
                text = format_template(primary.get_crew_template(target))
            elif action == "member":
                text = format_templates(primary.crew_templates(), target)
            elif action == "roster":
                text = format_roster(primary.crew_template_roster(target))
            elif action == "index":
                text = format_index(primary.crew_template_index())
            else:
                text = primary.crew_templates_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")



    def _handle_interrupts(self, args: str):
        """M-144: /interrupts - crew interrupts with grace.

        ``/interrupts`` shows the crew interrupt book
        held this session (the shipped example book -
        four interrupt records at the M-143 slice
        boundary, the roadmap's three pause scopes, and
        its pinned index - when none is held yet);
        ``/interrupts interrupt <interrupt-id>`` shows
        one pause record; ``/interrupts member
        <member-id>`` shows the pauses naming one
        member; ``/interrupts slice <slice-id>`` shows
        the pauses naming one slice; ``/interrupts
        report <interrupt-id>`` shows one pause's
        derived consistency report; ``/interrupts
        index`` shows the interrupt index derived from
        the whole book. Reading registers and publishes
        nothing as session news: records are held only
        when they are given through the agent layer,
        and held records are published as crew_interrupt,
        crew_interrupt_consistency and
        crew_interrupt_index session events. This road
        pauses no member, halts no crew, signals no
        process, touches no worktree, writes no journal,
        persists nothing and claims no board: the
        registry holds the interrupts as data, no record
        here claims a pause was ever carried out, and
        there is no Part VIII board yet - this surface
        is where the crew interrupts are visible. The
        registry is session state held by the agent; it
        is not a stored setting.
        """
        from ..core.crew_interrupts import (
            format_index,
            format_interrupt,
            format_interrupts,
            format_report,
            parse_crew_interrupts_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_crew_interrupts_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "interrupt":
                text = format_interrupt(primary.get_crew_interrupt(target))
            elif action == "member":
                text = format_interrupts(primary.crew_interrupts(), target)
            elif action == "slice":
                held = primary.crew_interrupts_for_slice(target)
                if held:
                    text = "\n".join(format_interrupt(e) for e in held)
                else:
                    text = "No interrupt records are held."
            elif action == "report":
                text = format_report(primary.crew_interrupt_report(target))
            elif action == "index":
                text = format_index(primary.crew_interrupt_index())
            else:
                text = primary.crew_interrupts_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_crewschedules(self, args: str):
        """M-145: /crewschedules - crew on schedule.

        ``/crewschedules`` shows the crew schedule book
        held this session (the shipped example book -
        four attachment records at the M-144 slice
        boundary, the roadmap's dawn Auditor sweep
        first, and its pinned index - when none is held
        yet); ``/crewschedules attachment
        <attachment-id>`` shows one attachment record;
        ``/crewschedules template <template>`` shows
        the attachments naming one formation;
        ``/crewschedules job <job-id>`` shows the
        attachment naming one job; ``/crewschedules
        report <attachment-id>`` shows one attachment's
        derived report; ``/crewschedules index`` shows
        the attachment index derived from the whole
        book. Reading registers and publishes nothing
        as session news: records are held only when
        they are given through the agent layer, and
        held records are published as
        crew_schedule_attachment, crew_schedule_report
        and crew_schedule_index session events. This
        road starts no timer, runs no job, summons no
        crew, spawns no agent, persists nothing and
        claims no board: the registry holds the
        attachments as data, no record here claims a
        job was ever run with its formation, and there
        is no Part VIII board yet - this surface is
        where the crew on schedule attachments are
        visible. The registry is session state held by
        the agent; it is not a stored setting.
        """
        from ..core.crew_schedules import (
            format_attachment,
            format_attachments,
            format_index,
            format_report,
            parse_crew_schedules_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_crew_schedules_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "attachment":
                text = format_attachment(primary.get_crew_schedule(target))
            elif action == "template":
                text = format_attachments(primary.crew_schedules(), target)
            elif action == "job":
                text = format_attachment(
                    primary.get_crew_schedule_for_job(target))
            elif action == "report":
                text = format_report(primary.crew_schedule_report(target))
            elif action == "index":
                text = format_index(primary.crew_schedule_index())
            else:
                text = primary.crew_schedules_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_conflicts(self, args: str):
        """M-081: /conflicts — the conflict workbench.

        ``/conflicts`` shows the gate (on by default), the
        plain-words explanation, a worked example, and this
        repository's live conflicts with both sides' intent;
        ``/conflicts on`` / ``off`` changes the gate
        (journaled by the agent layer).
        """
        from ..core.conflict_workbench import (
            enabled_from_config,
            format_conflict_workbench,
            format_setting_change,
            parse_conflicts_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_conflicts_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] == "show":
            status = primary.conflict_workbench_status()
            assert status["enabled"] == enabled_from_config(
                primary.config)
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_conflict_workbench(primary.config, primary.project_root)}[/bold cyan]\n"
                     "[dim]Turn the gate off with /conflicts off, "
                     "or back on with /conflicts on.[/dim]\n")
            return
        try:
            record = primary.set_conflict_workbench(request["enabled"])
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[green]{format_setting_change(record)}[/green]\n")

    def _handle_checkpoint(self, args: str):
        """M-075: /checkpoint — named checkpoints.

        ``/checkpoint`` shows the gate (on by default),
        the plain-words explanation, and the whole
        checkpoint tree; ``/checkpoint take <name>``
        freezes the tree and session under a name;
        ``/checkpoint restore <name>`` brings one back
        in one command (a dirty tree refuses unless the
        trailing word ``discard`` throws the un-
        checkpointed changes away on purpose);
        ``/checkpoint on`` / ``off`` changes the gate
        (journaled by the agent layer).
        """
        from ..core.checkpoints import (
            enabled_from_config,
            format_checkpoint_created,
            format_checkpoint_restored,
            format_checkpoints,
            format_setting_change,
            parse_checkpoint_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_checkpoint_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] == "show":
            status = primary.checkpoint_status()
            assert status["enabled"] == enabled_from_config(
                primary.config)
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_checkpoints(primary.config, status['checkpoints'], status['head_id'])}[/bold cyan]\n"
                     "[dim]Freeze the tree with /checkpoint take <name>, "
                     "or bring one back with /checkpoint restore "
                     "<name>.[/dim]\n")
            return
        try:
            if request["action"] == "setting":
                record = primary.set_checkpoints(request["enabled"])
                publish_sync(
                    "agent_chat_chunk", agent_name="Primary",
                    text=f"\n[green]{format_setting_change(record)}[/green]\n")
                return
            if request["action"] == "take":
                taken = primary.take_checkpoint(request["name"])
                publish_sync(
                    "agent_chat_chunk", agent_name="Primary",
                    text=f"\n[green]{format_checkpoint_created(taken)}[/green]\n")
                return
            restored = primary.restore_checkpoint(
                request["name"], request["discard"])
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[green]{format_checkpoint_restored(restored)}[/green]\n")

    def _handle_branch(self, args: str):
        """M-076: /branch — session branching.

        ``/branch`` shows the gate (on by default), the
        plain-words explanation, and a worked fork +
        comparison; ``/branch on`` / ``off`` changes the
        gate (journaled by the agent layer); ``/branch
        fork <index> [name]`` forks the attached session;
        ``/branch list`` lists its branches; ``/branch
        compare <id> <id>`` compares two sessions.
        """
        from ..core.session_branching import (
            enabled_from_config,
            format_branch_list,
            format_branching,
            format_comparison,
            format_fork,
            format_setting_change,
            parse_branch_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_branch_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if request["action"] == "show":
                status = primary.session_branching_status()
                assert status["enabled"] == enabled_from_config(
                    primary.config)
                publish_sync(
                    "agent_chat_chunk", agent_name="Primary",
                    text=f"\n[bold cyan]{format_branching(primary.config)}[/bold cyan]\n"
                         "[dim]Fork with /branch fork <message-index> [name], "
                         "list branches with /branch list, or compare with "
                         "/branch compare <session-id> <session-id>.[/dim]\n")
                return
            if request["action"] == "setting":
                record = primary.set_session_branching(request["enabled"])
                text, style = format_setting_change(record), "green"
            elif request["action"] == "fork":
                record = primary.fork_session(
                    request["at_index"], request["name"])
                text, style = format_fork(record), "green"
            elif request["action"] == "list":
                text = format_branch_list(primary.list_session_branches())
                style = "bold cyan"
            else:
                record = primary.compare_sessions(
                    request["first_id"], request["second_id"])
                text, style = format_comparison(record), "bold cyan"
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[{style}]{text}[/{style}]\n")

    def _handle_autocommit(self, args: str):
        """M-078: /autocommit — auto-commit discipline.

        ``/autocommit`` shows the gate (off by default),
        the plain-words explanation, the protected set,
        the working branch, and worked landing examples;
        ``/autocommit on`` / ``off`` changes the gate and
        ``/autocommit allow-protected`` /
        ``block-protected`` gives or withdraws the standing
        word for protected branches (journaled by the
        agent layer).
        """
        from ..core.auto_commit import (
            enabled_from_config,
            format_auto_commit,
            format_setting_change,
            parse_autocommit_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_autocommit_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] == "show":
            status = primary.auto_commit_status()
            assert status["enabled"] == enabled_from_config(
                primary.config)
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_auto_commit(primary.config)}[/bold cyan]\n"
                     "[dim]Turn the discipline on with /autocommit on, "
                     "or off with /autocommit off.[/dim]\n")
            return
        try:
            if request["action"] == "setting":
                record = primary.set_auto_commit(request["enabled"])
            else:
                record = primary.set_auto_commit_allow_protected(
                    request["allowed"])
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[green]{format_setting_change(record)}[/green]\n")

    def _handle_issueslice(self, args: str):
        """M-083: /issueslice — issue-to-slice.

        ``/issueslice`` shows the gate (on by default), the
        plain-words explanation, the seam's sources, and a
        sample issue planned; ``/issueslice on`` / ``off``
        changes the gate (journaled by the agent layer);
        ``/issueslice github <number>`` fetches that issue
        through the seam and plans it as a slice.
        """
        from ..core.issue_slice import (
            enabled_from_config,
            format_issue_slice,
            format_plan_record,
            format_setting_change,
            parse_issueslice_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_issueslice_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] == "show":
            status = primary.issue_slice_status()
            assert status["enabled"] == enabled_from_config(
                primary.config)
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_issue_slice(primary.config)}[/bold cyan]\n"
                     "[dim]Turn the gate off with /issueslice off, "
                     "or back on with /issueslice on.[/dim]\n")
            return
        if request["action"] == "plan":
            try:
                record = primary.plan_issue_slice(
                    request["source"], request["number"])
            except (ValueError, KeyError, RuntimeError) as e:
                publish_sync("agent_chat_chunk", agent_name="Primary",
                             text=f"\n[red]{e}[/red]\n")
                return
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[green]{format_plan_record(record)}[/green]\n")
            return
        try:
            record = primary.set_issue_slice(request["enabled"])
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[green]{format_setting_change(record)}[/green]\n")

    def _handle_costroute(self, args: str):
        """M-031: /costroute — cost-aware routing, in plain words.

        ``/costroute`` shows the setting (off by default), the
        plain-words explanation, the configured doors with their
        costs-table prices, and the task classes;
        ``/costroute on`` / ``off`` changes the setting (journaled
        by the agent layer); ``/costroute <task-class>`` asks the
        router for a decision for that class and applies it when
        it prefers a cheaper adequate door — applied through the
        agent's journaled model switch, with the decision's own
        reason, and announced here, never silent.
        """
        from ..core.cost_routing import (
            candidate_doors,
            enabled_from_config,
            format_cost_change,
            format_cost_routing,
            format_decision,
            parse_cost_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_cost_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] == "show":
            status = primary.cost_routing_status()
            assert status["enabled"] == enabled_from_config(
                primary.config)
            assert [d["model"] for d in status["doors"]] == [
                d.model for d in candidate_doors(primary.config)]
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_cost_routing(primary.config)}[/bold cyan]\n"
                     "[dim]Decide for a kind of work with "
                     "/costroute <task-class>; turn the setting on "
                     "with /costroute on.[/dim]\n")
            return
        try:
            if request["action"] == "setting":
                record = primary.set_cost_routing(request["enabled"])
                publish_sync(
                    "agent_chat_chunk", agent_name="Primary",
                    text=f"\n[green]{format_cost_change(record)}[/green]\n")
                return
            applied = primary.cost_route(request["task_class"])
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[green]{format_decision(applied['decision'])}[/green]\n")

    def _handle_guardians(self, args: str):
        """M-079: /guardians — README and licence guardians.

        ``/guardians`` shows the guards, the guarded names
        judged, worked refusal / allowed examples, and
        whether the user's explicit word is on record;
        ``/guardians word on`` / ``word off`` gives or takes
        back the word (journaled by the agent layer);
        ``/guardians check <path>`` judges one path under
        every operation.
        """
        from ..core.file_guardians import (
            explicit_from_config,
            format_guard_check,
            format_guardians,
            format_setting_change,
            parse_guardians_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_guardians_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] == "show":
            status = primary.guardian_status()
            assert status["explicit_word"] == explicit_from_config(
                primary.config)
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_guardians(primary.config)}[/bold cyan]\n"
                     "[dim]Give the word with /guardians word on, "
                     "or take it back with /guardians word off.[/dim]\n")
            return
        if request["action"] == "check":
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_guard_check(primary.config, request['path'])}[/bold cyan]\n")
            return
        try:
            record = primary.set_guardian_word(request["enabled"])
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[green]{format_setting_change(record)}[/green]\n")

    def _handle_commitcraft(self, args: str):
        """M-080: /commitcraft — commit craft.

        ``/commitcraft`` shows the gate (on by default),
        the plain-words explanation, and a worked
        split-and-draft example; ``on`` / ``off`` changes
        the gate (journaled by the agent layer);
        ``plan`` drafts the working tree's split by
        concern; ``commit <concern>`` commits one group
        under its drafted message; ``push`` pushes the
        current branch under the house rules (fetch +
        remote-diff first, never force-push, ls-remote
        verification after).
        """
        from ..core.commit_craft import (
            enabled_from_config,
            format_commit_craft,
            format_commit_record,
            format_plan,
            format_push_record,
            format_setting_change,
            parse_commitcraft_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_commitcraft_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] == "show":
            status = primary.commit_craft_status()
            assert status["enabled"] == enabled_from_config(
                primary.config)
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_commit_craft(primary.config)}[/bold cyan]\n"
                     "[dim]Turn the gate off with /commitcraft off, "
                     "or back on with /commitcraft on.[/dim]\n")
            return
        try:
            if request["action"] == "setting":
                record = primary.set_commit_craft(request["enabled"])
                text = format_setting_change(record)
            elif request["action"] == "plan":
                text = format_plan(primary.plan_commit_split())
            elif request["action"] == "commit":
                text = format_commit_record(
                    primary.commit_craft_group(request["concern"]))
            else:
                text = format_push_record(
                    primary.push_with_house_rules())
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[green]{text}[/green]\n")

    def _handle_costroute(self, args: str):
        """M-031: /costroute — cost-aware routing, in plain words.

        ``/costroute`` shows the setting (off by default), the
        plain-words explanation, the configured doors with their
        costs-table prices, and the task classes;
        ``/costroute on`` / ``off`` changes the setting (journaled
        by the agent layer); ``/costroute <task-class>`` asks the
        router for a decision for that class and applies it when
        it prefers a cheaper adequate door — applied through the
        agent's journaled model switch, with the decision's own
        reason, and announced here, never silent.
        """
        from ..core.cost_routing import (
            candidate_doors,
            enabled_from_config,
            format_cost_change,
            format_cost_routing,
            format_decision,
            parse_cost_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_cost_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] == "show":
            status = primary.cost_routing_status()
            assert status["enabled"] == enabled_from_config(
                primary.config)
            assert [d["model"] for d in status["doors"]] == [
                d.model for d in candidate_doors(primary.config)]
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_cost_routing(primary.config)}[/bold cyan]\n"
                     "[dim]Decide for a kind of work with "
                     "/costroute <task-class>; turn the setting on "
                     "with /costroute on.[/dim]\n")
            return
        try:
            if request["action"] == "setting":
                record = primary.set_cost_routing(request["enabled"])
                publish_sync(
                    "agent_chat_chunk", agent_name="Primary",
                    text=f"\n[green]{format_cost_change(record)}[/green]\n")
                return
            applied = primary.cost_route(request["task_class"])
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[green]{format_decision(applied['decision'])}[/green]\n")

    def _handle_prcraft(self, args: str):
        """M-082: /prcraft — PR craft.

        ``/prcraft`` shows the gate (on by default), the
        plain-words explanation, and a worked example over
        a fake GitHub road: a PR fetched as data, its
        review comments fetched as tasks, an unarmed review
        draft refusing to post, and the same draft posting
        once armed with the user's word. ``/prcraft on`` /
        ``off`` changes the gate (journaled by the agent
        layer); ``/prcraft tasks <n>`` fetches PR <n>'s
        review comments as tasks through the user's own gh
        road. Posting itself rides the agent's draft roads
        and only ever at the user's recorded word.
        """
        from ..core.pr_craft import (
            enabled_from_config,
            format_pr_craft,
            format_setting_change,
            format_tasks,
            parse_prcraft_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_prcraft_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] == "show":
            status = primary.pr_craft_status()
            assert status["enabled"] == enabled_from_config(
                primary.config)
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_pr_craft(primary.config)}[/bold cyan]\n"
                     "[dim]Turn the gate off with /prcraft off, "
                     "or back on with /prcraft on.[/dim]\n")
            return
        if request["action"] == "tasks":
            try:
                fetched = primary.fetch_review_tasks(request["number"])
            except (ValueError, KeyError, RuntimeError) as e:
                publish_sync("agent_chat_chunk", agent_name="Primary",
                             text=f"\n[red]{e}[/red]\n")
                return
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_tasks(fetched['tasks'])}[/bold cyan]\n")
            return
        try:
            record = primary.set_pr_craft(request["enabled"])
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[green]{format_setting_change(record)}[/green]\n")

    def _handle_kista(self, args: str):
        """M-032: /kista — key custody, in plain words.

        ``/kista`` shows, for every configured door, where its
        key lives (Kista reference, environment, legacy plain
        text, missing, or not-needed for a local door) and
        whether a key is held — never a key value itself.
        ``/kista adopt [base-url]`` moves that door's stored
        plain-text key into Kista's vault file, leaving only
        its reference in the config; the agent layer owns the
        move (validated first, journaled as a session event).
        """
        from ..core.key_custody import (
            custody_entries,
            format_custody,
            format_custody_change,
            parse_kista_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_kista_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] == "show":
            status = primary.kista_status()
            assert [e["base_url"] for e in status["entries"]] == [
                e.base_url for e in custody_entries(primary.config)]
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_custody(primary.config)}[/bold cyan]\n"
                     "[dim]Move a plain-text key into Kista with "
                     "/kista adopt.[/dim]\n")
            return
        try:
            record = primary.adopt_key_for_kista(request["base_url"])
        except (ValueError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync("agent_chat_chunk", agent_name="Primary",
                     text=f"\n[green]{format_custody_change(record)}[/green]\n")

    def _handle_resume_thought(self, args: str):
        """M-034: /resume-thought — streaming discipline, in plain words.

        ``/resume-thought show`` says whether a partial answer
        is waiting in the conversation (and, plainly, when none
        is) and whether the current model's streaming truth
        opens the resume gate. ``/resume-thought`` (or
        ``resume``) continues the waiting thought through the
        agent layer — journaled first as ``thought_resumed`` —
        and a refusal (no partial waiting, or a model whose
        streaming ability is not known to support resuming) is
        published plainly, changing nothing.
        """
        from ..core.streaming_discipline import (
            can_resume,
            find_partial,
            format_resume_status,
            parse_resume_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_resume_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] == "show":
            partial = primary.salvaged_partial()
            found = find_partial(primary.history_snapshot())
            assert (found is None) == (partial is None)
            decision = can_resume(primary.config.get("model"))
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_resume_status(partial, decision)}[/bold cyan]\n")
            return
        try:
            text = primary.resume_thought()
        except RuntimeError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync("agent_chat_chunk", agent_name="Primary",
                     text=f"\n{text}\n")

    def _handle_retry(self, args: str):
        """M-035: /retry — retry and backoff honesty, in plain words.

        ``/retry`` (or ``/retry show``) shows the plain-words
        explanation, the named bounds the current settings
        imply (budget, waits, planned and worst-case totals),
        the mutating rule and the replay boundaries, and the
        last provider request's retry report — or, plainly,
        that no provider request has been retried yet in this
        session.
        """
        from ..core.retry_honesty import (
            bounds_from_settings,
            format_retry_status,
            parse_retry_args,
        )
        from ..core.runtime import runtime_settings

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_retry_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] == "show":
            status = primary.retry_status()
            assert status["bounds"] == bounds_from_settings(
                runtime_settings(primary.config))
            assert status["report"] is primary.last_retry_report
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_retry_status(status['bounds'], status['report'])}[/bold cyan]\n")
            return

    def _handle_weather(self, args: str):
        """M-036: /weather — rate-limit weather, in plain words.

        ``/weather`` (or ``/weather show``) shows the plain-words
        explanation and, for every door on the crew's shared
        weather board plus the primary's current door, whether
        it is limited and until when, what quota the door
        itself reported, and what is simply unknown.
        """
        from ..core.rate_limit_weather import (
            format_weather_status,
            parse_weather_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_weather_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] == "show":
            status = primary.weather_status()
            board = primary._weather_board
            assert [p["provider"] for p in status["providers"]] == [
                w.provider for w in board.snapshot()]
            assert status["current_provider"] == primary._weather_key()
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_weather_status(board, extra_providers=[status['current_provider']])}[/bold cyan]\n")
            return

    def _handle_vision(self, args: str):
        """M-037: /vision — vision input routing, in plain words.

        ``/vision`` (or ``/vision show``) shows the current
        model's recorded sight truth, the configured doors
        whose models are known to see, and the switch on
        offer. ``/vision switch`` takes that offered switch
        through the primary's journaled M-028 switch.
        """
        from ..core.model_capabilities import load_capabilities
        from ..core.model_switch import format_switch_record
        from ..core.vision_routing import (
            format_vision_status,
            parse_vision_args,
            suggest_switch,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_vision_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] == "show":
            status = primary.vision_status()
            caps = load_capabilities()
            model = primary.config.get("model")
            assert status["vision"] == (
                caps.for_model(model).vision if model else None)
            suggestion = suggest_switch(primary.config, caps)
            assert status["suggestion"] == (
                suggestion.selection() if suggestion is not None else None)
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_vision_status(status)}[/bold cyan]\n")
            return
        try:
            record = primary.apply_vision_switch()
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{format_switch_record(record)}[/bold cyan]\n")

    def _handle_longcontext(self, args: str):
        """M-038: /longcontext — the model's loading strategy, plainly.

        ``/longcontext`` (or ``/longcontext show``) shows the
        current model's long-context strategy, chosen from its
        recorded context size (M-027): map-first for a known
        million-class window, aggressive repo-map + retrieval
        for a known smaller window, and an honest unknown —
        with the shipped default budget — when the size is not
        recorded. ``/longcontext <model>`` previews another
        model's strategy without changing the session.
        """
        from ..core.long_context import (
            format_longcontext_status,
            parse_longcontext_args,
            strategy_for_model,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_longcontext_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        status = primary.context_strategy(request["model"])
        plan = strategy_for_model(request["model"]
                                  if request["model"] is not None
                                  else primary.config.get("model"))
        assert status["plan"] == plan.record()
        assert status["strategy"] == plan.strategy
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{format_longcontext_status(status)}[/bold cyan]\n")

    def _handle_offline(self, args: str):
        """M-040: /offline — offline honesty, in plain words.

        ``/offline`` (or ``/offline show``) shows the session's
        offline assessment over the M-039 health board: online
        when a door answered, the exact offline declaration —
        plus the non-model tools that still work (review,
        metrics, session search) — when a probed board shows
        no door can serve, and an honest unknown when the
        board cannot say.
        """
        from ..core.offline_honesty import (
            assess_board,
            format_offline_status,
            parse_offline_args,
        )
        from ..core.provider_health import Board, HealthEntry

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_offline_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] == "show":
            status = primary.offline_status()
            entries = tuple(HealthEntry(**e)
                            for e in status["board"]["entries"])
            board = Board(entries=entries,
                          generated_at=status["board"]["generated_at"])
            assert status["assessment"] == assess_board(board).record()
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_offline_status(status)}[/bold cyan]\n")
            return

    def _handle_testkit(self, args: str):
        """M-041: /testkit — the new-provider test kit.

        ``/testkit <provider> [base-url]`` runs the five kit
        checks (registry, chat, tools, streaming, errors)
        against the named registry entry's door and states
        the evidence plainly per check, with the verdict —
        passed, failed, or not-proven.
        """
        from ..core.provider_test_kit import (
            format_kit_status,
            parse_kit_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_kit_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] == "run":
            try:
                status = primary.test_kit(request["provider"],
                                          base_url=request["base_url"])
            except KeyError as e:
                publish_sync("agent_chat_chunk", agent_name="Primary",
                             text=f"\n[red]{e}[/red]\n")
                return
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_kit_status(status)}[/bold cyan]\n")
            return

    def _handle_map(self, args: str):
        """M-045: /map — the repo map, visible in the TUI.

        ``/map`` browses M-044's map for the workspace (or
        ranked for the task words given), each file with its
        true rank, its score, and the reasons the coder
        thinks it matters; ``/map show <path>`` gives one
        file's full account (or its honest unmapped state);
        ``/map pin <path>`` / ``/map unpin <path>`` keep the
        user's pins — a pinned file is shown first, with its
        rank and score unchanged — and ``/map pins`` lists
        them.
        """
        from ..context.repo_map import build_repo_map
        from ..context.repo_map_view import (
            build_map_view,
            format_map_change,
            format_map_detail,
            format_map_pins,
            format_map_view,
            parse_map_args,
            pins_from_config,
            resolve_detail,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_map_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] == "list":
            status = primary.repo_map_status(request["query"])
            view = build_map_view(
                build_repo_map(primary.project_root,
                               query=request["query"]),
                pins_from_config(primary.config))
            assert status["view"] == view.record()
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_map_view(status)}[/bold cyan]\n")
            return
        if request["action"] == "detail":
            try:
                status = primary.repo_map_detail(request["path"])
            except ValueError as e:
                publish_sync("agent_chat_chunk", agent_name="Primary",
                             text=f"\n[red]{e}[/red]\n")
                return
            detail = resolve_detail(
                build_repo_map(primary.project_root),
                pins_from_config(primary.config), request["path"])
            assert status["detail"] == detail.record()
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_map_detail(status)}[/bold cyan]\n")
            return
        if request["action"] == "pins":
            status = primary.repo_map_pins()
            assert status["pins"] == list(
                pins_from_config(primary.config))
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_map_pins(status)}[/bold cyan]\n")
            return
        try:
            if request["action"] == "pin":
                record = primary.pin_repo_map_file(request["path"])
            else:
                record = primary.unpin_repo_map_file(request["path"])
        except (ValueError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{format_map_change(record)}[/bold cyan]\n")

    def _handle_ssearch(self, args: str):
        """M-047: /ssearch — structural search, in the TUI.

        ``/ssearch <language> <pattern>`` runs an
        ast-grep-style pattern (``$NAME`` captures one node,
        ``$$$`` / ``$$$NAME`` captures zero or more siblings)
        over every file of that language in the workspace,
        through the M-043 parse foundation, and lists each
        match with its captures. A pattern that does not
        parse, and a language with no honest parse, are
        refused plainly — never text-searched instead.
        Search only; the rewrite is /srewrite (M-048).
        """
        from ..tools.structural_search import (
            format_search_status,
            parse_search_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_search_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            status = primary.structural_search(
                request["pattern"], request["language"])
        except (ValueError, KeyError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{format_search_status(status)}[/bold cyan]\n")
        return

    def _handle_srewrite(self, args: str):
        """M-048: /srewrite — structural rewrite, in the TUI.

        ``/srewrite <language> <pattern> => <replacement>``
        previews the codemod: every match of the pattern
        (M-047) becomes a site with its rendered replacement
        and its own diff preview, and nothing is written.
        ``/srewrite apply ...`` applies the plan through
        the edit journal — a file that changed since the
        plan, and sites overlapping another match, are
        refused plainly in the report, never force-edited.
        A replacement that does not parse or names a
        metavariable the pattern never captures is refused
        the same way.
        """
        from ..tools.structural_rewrite import (
            format_rewrite_status,
            parse_rewrite_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_rewrite_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            status = primary.structural_rewrite(
                request["pattern"], request["replacement"],
                request["language"],
                apply=request["action"] == "apply")
        except (ValueError, KeyError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{format_rewrite_status(status)}[/bold cyan]\n")
        return

    def _handle_lsp(self, args: str):
        """M-049/M-050: /lsp — language-server truth, in the TUI.

        ``/lsp`` (or ``/lsp show``) shows the discovery
        board: which catalogued language servers this
        machine has, and each missing one's install remedy.
        ``/lsp check <path>`` runs the file's language
        server and shows its diagnostics in its own words;
        a file whose server is not installed is reported
        NOT CHECKED with the remedy, never as clean.
        ``/lsp def|refs|hover <path> <line> <character>``
        and ``/lsp symbols [query]`` (M-050) ask the server
        the navigation questions; an absent server is
        reported NOT ANSWERED, never as a found answer.
        ``/lsp rename <path> <line> <character> <new-name>
        [apply]`` and ``/lsp actions <path> <line>
        <character> [apply <n>]`` (M-051) preview a rename
        or the server's code actions; ``apply`` writes the
        plan through the edit journal only.
        """
        from ..integrations.lsp import (
            format_lsp_code_actions,
            format_lsp_diagnostics,
            format_lsp_navigation,
            format_lsp_rename,
            format_lsp_status,
            parse_lsp_args,
        )

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_lsp_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] == "show":
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_lsp_status(primary.lsp_status())}[/bold cyan]\n")
            return
        if request["action"] == "check":
            try:
                status = primary.lsp_diagnostics(request["path"])
            except (ValueError, KeyError, RuntimeError) as e:
                publish_sync("agent_chat_chunk", agent_name="Primary",
                             text=f"\n[red]{e}[/red]\n")
                return
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_lsp_diagnostics(status)}[/bold cyan]\n")
            return
        if request["action"] == "rename":
            try:
                status = primary.lsp_rename(
                    request["path"], request["line"],
                    request["character"], request["new_name"],
                    apply=request["apply"])
            except (ValueError, KeyError, RuntimeError) as e:
                publish_sync("agent_chat_chunk", agent_name="Primary",
                             text=f"\n[red]{e}[/red]\n")
                return
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_lsp_rename(status)}[/bold cyan]\n")
            return
        if request["action"] == "code_actions":
            try:
                status = primary.lsp_code_actions(
                    request["path"], request["line"],
                    request["character"],
                    apply_index=request["apply_index"])
            except (ValueError, KeyError, RuntimeError) as e:
                publish_sync("agent_chat_chunk", agent_name="Primary",
                             text=f"\n[red]{e}[/red]\n")
                return
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_lsp_code_actions(status)}[/bold cyan]\n")
            return
        try:
            if request["action"] == "definition":
                status = primary.lsp_definition(
                    request["path"], request["line"],
                    request["character"])
            elif request["action"] == "references":
                status = primary.lsp_references(
                    request["path"], request["line"],
                    request["character"])
            elif request["action"] == "hover":
                status = primary.lsp_hover(
                    request["path"], request["line"],
                    request["character"])
            else:
                status = primary.lsp_workspace_symbols(
                    request["query"])
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{format_lsp_navigation(status)}[/bold cyan]\n")
        return

    def _handle_truth(self, args: str):
        """M-052: /truth <path> — one file's edit-time truth, in the TUI.

        Shows every leg that truly ran and the file's
        current errors; a leg that cannot run (no language
        server installed, no linter configured) is shown
        as its absence, never as a clean file.
        """
        from ..tools.edit_truth import format_truth_report, parse_truth_args

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_truth_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            status = primary.edit_truth(request["path"])
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{format_truth_report(status)}[/bold cyan]\n")
        return

    def _handle_format(self, args: str):
        """M-053: /format <path> [apply] — the formatter covenant, in the TUI.

        Shows what the project's own configured formatter
        would change in the named (touched) file, with the
        format diff separated from the logic diff; apply
        writes through the edit journal. No configured
        formatter is shown as its absence, never as a
        made-up style, and untouched code is never
        reformatted.
        """
        from ..tools.format_covenant import format_format_report, parse_format_args

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_format_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            status = primary.format_covenant(
                request["path"], apply=request["action"] == "apply")
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{format_format_report(status)}[/bold cyan]\n")
        return

    def _handle_debug(self, args: str):
        """M-054: /debug [show] | /debug run <program> [...] — the debugger, in the TUI.

        Shows the adapter board, or runs one program under
        the adapter and shows the stop, the stack, and the
        variables exactly as the adapter reported them. A
        missing adapter is shown as its absence, never as
        a faked session.
        """
        from ..tools.debugger import (
            format_debug_board, format_debug_report, parse_debug_args)

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_debug_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] == "show":
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_debug_board(primary.debugger_status())}[/bold cyan]\n")
            return
        try:
            status = primary.debug_run(
                request["program"], breakpoints=request["breakpoints"],
                steps=request["steps"],
                stop_on_exception=request["stop_on_exception"])
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{format_debug_report(status)}[/bold cyan]\n")
        return

    def _handle_debug_loop(self, args: str):
        """M-055: /debugloop [show] | /debugloop <test> [...] — the debugger in the loop, in the TUI.

        Re-runs one named failing test under the M-054
        adapter with exception stops on and shows the
        stop's frames and locals as evidence. A missing
        adapter, a re-run that never stops, and the loop
        switched off are each shown as their honest
        status, never as invented evidence.
        """
        from ..tools.debug_loop import (
            format_debug_loop_board, format_debug_loop_report,
            parse_debug_loop_args)

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_debug_loop_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] == "show":
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_debug_loop_board(primary.debugger_status())}[/bold cyan]\n")
            return
        try:
            status = primary.debug_loop(
                request["test"], breakpoints=request["breakpoints"])
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{format_debug_loop_report(status)}[/bold cyan]\n")
        return

    def _handle_test_intel(self, args: str):
        """M-056: /testintel [show] | select <file> ... | history — test intelligence, in the TUI.

        Discovery is pytest's own collection, selection is
        the symbol graph's answer or the honest whole-suite
        fallback, and flaky marks come only from the
        recorded history — each shown as its true status.
        """
        from ..tools.test_intelligence import (
            format_test_intel_board, format_test_intel_history,
            format_test_intel_selection, parse_test_intel_args)

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_test_intel_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] == "show":
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_test_intel_board(primary.test_intel_status())}[/bold cyan]\n")
            return
        if request["action"] == "history":
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_test_intel_history(primary.test_intel_history())}[/bold cyan]\n")
            return
        try:
            status = primary.test_intel_select(request["changed"])
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{format_test_intel_selection(status)}[/bold cyan]\n")
        return

    def _handle_coverage(self, args: str):
        """M-057: /coverage [show] | check <file> ... — coverage sight, in the TUI.

        The board shows whether coverage.py data exists and
        what it totals; a check lays its measured lines over
        the touched files, and a file whose measured lines
        never ran is flagged to the Auditor in the audit log.
        """
        from ..tools.coverage_sight import (
            format_coverage_board, format_coverage_overlay,
            parse_coverage_args)

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_coverage_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        if request["action"] == "show":
            publish_sync(
                "agent_chat_chunk", agent_name="Primary",
                text=f"\n[bold cyan]{format_coverage_board(primary.coverage_status())}[/bold cyan]\n")
            return
        try:
            status = primary.coverage_check(request["changed"])
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{format_coverage_overlay(status)}[/bold cyan]\n")
        return

    def _handle_local_search(self, args: str):
        """M-058: /search [text] <regex> | fuzzy <query> | structural <language> <pattern> — beyond-grep local search, in the TUI.

        One surface, three modes — in-process text, fuzzy
        subsequence, and the M-047 structural engine —
        with results ranked by the symbol graph, every
        result carrying its score and reasons.
        """
        from ..tools.local_search import (
            format_local_search, parse_local_search_args)

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_local_search_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            status = primary.local_search(
                request["query"], mode=request["mode"],
                language=request["language"])
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{format_local_search(status)}[/bold cyan]\n")
        return

    def _handle_web(self, args: str):
        """M-059: /web search <query> | /web fetch <url> — web knowledge tools, in the TUI.

        One search through the configured endpoint or one
        fetched page, results as numbered citations, cited
        into the session journal by the Agent when a
        session is attached.
        """
        from ..tools.web_search import format_web_report, parse_web_args

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_web_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if request["action"] == "search":
                status = primary.web_search(request["query"])
            else:
                status = primary.web_fetch(request["url"])
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{format_web_report(status)}[/bold cyan]\n")
        return

    def _handle_docs(self, args: str):
        """M-060: /docs list | search <query> | read <name> — docs-at-hand, in the TUI.

        The offline shelf: the project's own docs plus
        doc packs under .mythic/docpacks/, searched and
        read with nothing fetched from anywhere.
        """
        from ..tools.docs_at_hand import (
            format_docs_report, parse_docs_args)

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_docs_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if request["action"] == "list":
                status = primary.docs_list()
            elif request["action"] == "search":
                status = primary.docs_search(request["query"])
            else:
                status = primary.docs_read(request["name"])
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{format_docs_report(status)}[/bold cyan]\n")
        return

    def _handle_deps(self, args: str):
        """M-061: /deps [show | <package> | propose <package> <version>] — dependency sight, in the TUI.

        The declared graph from pyproject.toml with honest
        installed truth; a package adds its counted blast
        radius, local changelog mentions and local
        vulnerability-data state; a proposal is data only
        and is never applied.
        """
        from ..tools.dependency_sight import (
            format_deps_report, parse_deps_args)

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_deps_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if request["action"] == "show":
                status = primary.dependency_sight()
            elif request["action"] == "package":
                status = primary.dependency_sight(request["package"])
            else:
                status = primary.dependency_proposal(
                    request["package"], request["version"])
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{format_deps_report(status)}[/bold cyan]\n")
        return

    def _handle_sensing(self, args: str):
        """M-062: /sensing [show | dead | dup] — code sensing, in the TUI.

        A structural report for the Cartographer: dead
        code from the shipped scanner over the workspace's
        packages, and structural duplication clusters.
        Sensing only — nothing is deleted or edited.
        """
        from ..tools.code_sensing import (
            format_sensing_report, parse_sensing_args)

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_sensing_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            status = primary.code_sensing(request["action"])
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{format_sensing_report(status)}[/bold cyan]\n")
        return

    def _handle_types(self, args: str):
        """M-063: /types [show | <path>] — type depth, in the TUI.

        The standing type account from the project's type
        checkers (mypy/pyright, whichever truly exist),
        findings triaged by kind into the review. A
        checker that is not installed is shown as its
        absence, never as a clean file.
        """
        from ..tools.type_depth import (
            format_type_report, parse_types_args)

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_types_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            status = primary.type_depth(request["path"])
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{format_type_report(status)}[/bold cyan]\n")
        return

    def _handle_mojo(self, args: str):
        """M-064: /mojo [show | <path> | knowledge [term]] — Mojo, in the TUI.

        Mojo as a first-class language: the workspace's
        Mojo files scanned structurally (tree-sitter
        grammar where one truly loads — none exists
        today, said plainly), removed syntax flagged
        with its replacement, and the house Mojo skills'
        distilled knowledge searchable.
        """
        from ..tools.mojo_sight import (
            format_mojo_report, parse_mojo_args)

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_mojo_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            status = primary.mojo_sight(
                request["action"], target=request.get("target"),
                term=request.get("term", ""))
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{format_mojo_report(status)}[/bold cyan]\n")
        return

    def _handle_sql(self, args: str):
        """M-065: /sql [show | <db> | explain <db> <query> | migrations] — SQL, in the TUI.

        SQL and data sight: workspace SQLite databases
        read through read-only connections (schemas,
        and EXPLAIN for SELECT queries — explained,
        never executed; writes refused), and migration
        files read as code, never applied.
        """
        from ..tools.sql_sight import (
            format_sql_report, parse_sql_args)

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_sql_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            status = primary.sql_sight(
                request["action"], db=request.get("db"),
                query=request.get("query", ""))
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{format_sql_report(status)}[/bold cyan]\n")
        return

    def _handle_config(self, args: str):
        """M-066: /config [show | <file> | docker] — config/infra, in the TUI.

        Config and infra sight: YAML, TOML, INI and
        systemd unit files, Dockerfiles and compose
        files parsed structurally — never executed —
        with the coder's own no-Docker-law warning
        raised for Docker artifacts on Volmarr's
        projects.
        """
        from ..tools.config_sight import (
            format_config_report, parse_config_args)

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_config_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            status = primary.config_sight(
                request["action"], target=request.get("target"))
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{format_config_report(status)}[/bold cyan]\n")
        return

    def _handle_assets(self, args: str):
        """M-067: /assets [show | <file> | images | archives | large] — assets, in the TUI.

        Binary and asset sight: images described from
        their headers, archives from their member
        listings, large files by size and kind — never
        dumped, decoded or extracted — with the role
        the map notes for each file.
        """
        from ..tools.asset_sight import (
            format_asset_report, parse_assets_args)

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_assets_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            status = primary.asset_sight(
                request["action"], target=request.get("target"))
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{format_asset_report(status)}[/bold cyan]\n")
        return

    def _handle_langpacks(self, args: str):
        """M-068: /langpacks [show | <language>] — language packs, in the TUI.

        Language packs as data: each language's toolchain
        (language server, formatters, test runners) is
        declared in the pack data and reported with a live
        PATH check of each declared binary — described,
        never executed.
        """
        from ..tools.language_packs import (
            format_language_pack_report, parse_langpacks_args)

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_langpacks_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            status = primary.language_packs(
                request["action"], language=request.get("language"))
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{format_language_pack_report(status)}[/bold cyan]\n")
        return

    def _handle_intelcache(self, args: str):
        """M-069: /intelcache [show | <file> | warm | clear] — the cache, in the TUI.

        Parse/graph/LSP results cached per file hash under
        the workspace's .mythic/intelligence-cache/: a
        changed file's entry is evicted on lookup, never
        served; warming writes cache entries only.
        """
        from ..tools.intelligence_cache import (
            format_intelligence_cache_report, parse_intelcache_args)

        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            request = parse_intelcache_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            status = primary.intelligence_cache(
                request["action"], target=request.get("target"))
        except (ValueError, KeyError, RuntimeError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{format_intelligence_cache_report(status)}[/bold cyan]\n")
        return

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
