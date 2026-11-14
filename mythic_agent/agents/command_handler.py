
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
            elif cmd == "/contextbudget":
                self._handle_contextbudget(args)
            elif cmd == "/mentions":
                self._handle_mentions(args)
            elif cmd == "/instructionfiles":
                self._handle_instruction_files(args)
            elif cmd == "/memorymap":
                self._handle_memory_map(args)
            elif cmd == "/glassbox":
                self._handle_glassbox(args)
            elif cmd == "/graphsearch":
                self._handle_graphsearch(args)
            elif cmd == "/daymemory":
                self._handle_daymemory(args)
            elif cmd == "/crossmemory":
                self._handle_crossmemory(args)
            elif cmd == "/ledger":
                self._handle_ledger(args)
            elif cmd == "/decisions":
                self._handle_decisions(args)
            elif cmd == "/forget":
                self._handle_forget(args)
            elif cmd == "/recipes":
                self._handle_recipes(args)
            elif cmd == "/pins":
                self._handle_pins(args)
            elif cmd == "/thrift":
                self._handle_thrift(args)
            elif cmd == "/endurance":
                self._handle_endurance(args)
            elif cmd == "/multisession":
                self._handle_multisession(args)
            elif cmd == "/handoffsummary":
                self._handle_handoffsummary(args)
            elif cmd == "/memoryxport":
                self._handle_memoryxport(args)
            elif cmd == "/subconscious":
                self._handle_subconscious(args)
            elif cmd == "/contradiction":
                self._handle_contradiction(args)
            elif cmd == "/private":
                self._handle_private(args)
            elif cmd == "/memorydoctor":
                self._handle_memorydoctor(args)
            elif cmd == "/coldstart":
                self._handle_coldstart(args)
            elif cmd == "/workview":
                self._handle_workview(args)
            elif cmd == "/sliceboard":
                self._handle_sliceboard(args)
            elif cmd == "/approvalcards":
                self._handle_approvalcards(args)
            elif cmd == "/fuzzypicker":
                self._handle_fuzzypicker(args)
            elif cmd == "/commandpalace":
                self._handle_commandpalace(args)
            elif cmd == "/promptcraft":
                self._handle_promptcraft(args)
            elif cmd == "/statusline":
                self._handle_statusline(args)
            elif cmd == "/themesgrownup":
                self._handle_themesgrownup(args)
            elif cmd == "/voiceinout":
                self._handle_voiceinout(args)
            elif cmd == "/manners":
                self._handle_manners(args)
            elif cmd == "/skin":
                self._handle_skin(args)
            elif cmd == "/errors":
                self._handle_errors(args)
            elif cmd == "/onboard":
                self._handle_onboard(args)
            elif cmd == "/lessons":
                self._handle_lessons(args)
            elif cmd == "/helpask":
                self._handle_helpask(args)
            elif cmd == "/keymap":
                self._handle_keymap(args)
            elif cmd == "/mouse":
                self._handle_mouse(args)
            elif cmd == "/gallery":
                self._handle_gallery(args)
            elif cmd == "/costs":
                self._handle_costs(args)
            elif cmd == "/theatre":
                self._handle_theatre(args)
            elif cmd == "/panes":
                self._handle_pane(args)
            elif cmd == "/smallterminal":
                self._handle_smallterminal(args)
            elif cmd == "/copyshare":
                self._handle_copyshare(args)
            elif cmd == "/settingsroom":
                self._handle_settingsroom(args)
            elif cmd == "/commandpalette":
                self._handle_commandpalette(args)
            elif cmd == "/uiundo":
                self._handle_uiundo(args)
            elif cmd == "/accessverify":
                self._handle_accessverify(args)
            elif cmd == "/campaigns":
                self._handle_campaigns(args)
            elif cmd == "/intent":
                self._handle_intent(args)
            elif cmd == "/slicing":
                self._handle_slicing(args)
            elif cmd == "/juggernaut":
                self._handle_juggernaut(args)
            elif cmd == "/acceptance":
                self._handle_acceptance(args)
            elif cmd == "/banking":
                self._handle_banking(args)
            elif cmd == "/keepruntime":
                self._handle_keeping(args)
            elif cmd == "/pauselines":
                self._handle_pausing(args)
            elif cmd == "/questionlaw":
                self._handle_questioning(args)
            elif cmd == "/scopesentry":
                self._handle_sentry(args)
            elif cmd == "/mapupkeep":
                self._handle_upkeep(args)
            elif cmd == "/bugrule":
                self._handle_bug(args)
            elif cmd == "/retrospectives":
                self._handle_retro(args)
            elif cmd == "/patterns":
                self._handle_pattern(args)
            elif cmd == "/estimates":
                self._handle_estimate(args)
            elif cmd == "/hall":
                self._handle_campaign(args)
            elif cmd == "/shapes":
                self._handle_shape(args)
            elif cmd == "/mimis":
                self._handle_mimis(args)
            elif cmd == "/resumes":
                self._handle_daybook(args)
            elif cmd == "/milestones":
                self._handle_milestone(args)
            elif cmd == "/log":
                self._handle_log(args)
            elif cmd == "/selfmod":
                self._handle_selfmod(args)
            elif cmd == "/failures":
                self._handle_failtax(args)
            elif cmd == "/dryrun":
                self._handle_dryrun(args)
            elif cmd == "/export":
                self._handle_export(args)
            elif cmd == "/orders":
                self._handle_orders(args)
            elif cmd == "/workflow":
                self._handle_workflow(args)
            elif cmd == "/scaling":
                self._handle_scaling(args)
            elif cmd == "/course":
                self._handle_course(args)
            elif cmd == "/metrics":
                self._handle_metrics(args)
            elif cmd == "/crossapp":
                self._handle_crossapp(args)
            elif cmd == "/mcpclient":
                self._handle_mcpclient(args)
            elif cmd == "/mcpregistry":
                self._handle_mcpregistry(args)
            elif cmd == "/skillsstandard":
                self._handle_skillsstandard(args)
            elif cmd == "/customcommands":
                self._handle_customcommands(args)
            elif cmd == "/pluginbundles":
                self._handle_pluginbundles(args)
            elif cmd == "/vscodecompanions":
                self._handle_vscodecompanions(args)
            elif cmd == "/idecompanions":
                self._handle_idecompanions(args)
            elif cmd == "/rivalimporters":
                self._handle_rivalimporters(args)
            elif cmd == "/samverkbridge":
                self._handle_samverkbridge(args)
            elif cmd == "/samtalbridge":
                self._handle_samtalbridge(args)
            elif cmd == "/kistakeykeeper":
                self._handle_kistakeykeeper(args)
            elif cmd == "/aesirdeepening":
                self._handle_aesirdeepening(args)
            elif cmd == "/githostparity":
                self._handle_githostparity(args)
            elif cmd == "/cibridges":
                self._handle_cibridges(args)
            elif cmd == "/issuetrackers":
                self._handle_issuetrackers(args)
            elif cmd == "/wyrdseam":
                self._handle_wyrdseam(args)
            elif cmd == "/webhookdoors":
                self._handle_webhookdoors(args)
            elif cmd == "/exporteverything":
                self._handle_exporteverything(args)
            elif cmd == "/docsmcp":
                self._handle_docsmcp(args)
            elif cmd == "/bridgeaudit":
                self._handle_bridgeaudit(args)
            elif cmd == "/benchmarkharness":
                self._handle_benchmarkharness(args)
            elif cmd == "/publishedyardstick":
                self._handle_publishedyardstick(args)
            elif cmd == "/regressioncourt":
                self._handle_regressioncourt(args)
            elif cmd == "/performancebudgets":
                self._handle_performancebudgets(args)
            elif cmd == "/platformmatrixfinal":
                self._handle_platformmatrixfinal(args)
            elif cmd == "/securityaudit":
                self._handle_securityaudit(args)
            elif cmd == "/privacyaudit":
                self._handle_privacyaudit(args)
            elif cmd == "/accessibilityfinal":
                self._handle_accessibilityfinal(args)
            elif cmd == "/docscompletion":
                self._handle_docscompletion(args)
            elif cmd == "/readmecare":
                self._handle_readmecare(args)
            elif cmd == "/migrationproof":
                self._handle_migrationproof(args)
            elif cmd == "/strangerfleettest":
                self._handle_strangerfleettest(args)
            elif cmd == "/costofquality":
                self._handle_costofquality(args)
            elif cmd == "/truthfulchangelog":
                self._handle_truthfulchangelog(args)
            elif cmd == "/releaseshaping":
                self._handle_releaseshaping(args)
            elif cmd == "/roadmapaudit":
                self._handle_roadmapaudit(args)
            elif cmd == "/mcpserver":
                self._handle_mcpserver(args)
            elif cmd == "/ceremony":
                self._handle_ceremony(args)
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

    def _handle_contextbudget(self, args: str):
        """M-147: /contextbudget - context budget made visible.

        ``/contextbudget`` shows the context budget
        panel held this session (the shipped example
        panel - seven items at the M-146 slice
        boundary, one of every kind, and its pinned
        meter and panel - when none is held yet);
        ``/contextbudget item <item-id>`` shows one
        context item; ``/contextbudget kind <kind>``
        shows the items of one kind;
        ``/contextbudget meter`` shows the meter
        derived from the whole panel;
        ``/contextbudget panel`` shows the panel
        derived from the whole book. Reading registers
        and publishes nothing as session news: items
        are held only when they are given through the
        agent layer, and held items are published as
        context_budget_item, context_budget_meter and
        context_budget_panel session events. This
        road compiles no context, assembles no prompt,
        calls no model, persists nothing and claims
        no board: the registry holds the items as
        data, holding a panel changes no live context
        assembly, and there is no Part VIII board yet
        - this surface is where the context budget
        account is visible. The registry is session
        state held by the agent; it is not a stored
        setting.
        """
        from ..core.context_budget import (
            format_item,
            format_items,
            format_meter,
            format_panel,
            parse_context_budget_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_context_budget_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "item":
                text = format_item(primary.get_context_budget_item(target))
            elif action == "kind":
                text = format_items(primary.context_budget_panel(), target)
            elif action == "meter":
                text = format_meter(primary.context_budget_meter())
            elif action == "panel":
                text = format_panel(primary.context_budget_view())
            else:
                text = primary.context_budget_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_mentions(self, args: str):
        """M-148: /mentions - the @-mention canon.

        ``/mentions`` shows the mention canon held
        this session (the shipped example canon -
        seven mentions at the M-147 slice boundary,
        one of every kind, its seven pinned plans and
        its one pinned index - when none is held yet);
        ``/mentions mention <mention-id>`` shows one
        mention; ``/mentions kind <kind>`` shows the
        mentions of one kind; ``/mentions plan
        <mention-id>`` shows the plan derived for one
        mention; ``/mentions parse <text>`` shows the
        mentions the grammar reads out of a text,
        holding none of them; ``/mentions index``
        shows the index derived from the whole book.
        Reading registers and publishes nothing as
        session news: mentions are held only when they
        are given through the agent's canon roads, and
        every mention held for the session is journaled
        as a mentions_mention session event, every
        derived plan as a mentions_plan session event
        and every derived index as a mentions_index
        session event. This surface reads no file,
        fetches no page, indexes no symbol, opens no
        session, fetches no issue, compiles no context,
        calls no model and persists nothing - parsing
        and planning pull nothing in by themselves -
        and there is no Part VIII board yet, so the
        canon is visible on this surface, not on a
        board.
        """
        from ..core.mentions import (
            format_index,
            format_mention,
            format_mentions,
            format_plan,
            parse_mentions,
            parse_mentions_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_mentions_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "mention":
                text = format_mention(primary.get_mention(target))
            elif action == "kind":
                text = format_mentions(
                    primary.mentions_canon(), target)
            elif action == "plan":
                text = format_plan(primary.mention_plan(target))
            elif action == "parse":
                parsed = parse_mentions(target)
                text = "\n".join(
                    format_mention(entry) for entry in parsed) \
                    if parsed else "No mentions stand in that text."
            elif action == "index":
                text = format_index(primary.mentions_canon())
            else:
                text = primary.mentions_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_instruction_files(self, args: str):
        """M-149: /instructionfiles - instruction files unified.

        ``/instructionfiles`` shows the instruction files
        held this session (the shipped example book - six
        files at the M-148 slice boundary, of every origin,
        with its one pinned panel - when none is held yet);
        ``/instructionfiles entry <file-id>`` shows one
        entry; ``/instructionfiles origin <origin>`` shows
        the files of one origin; ``/instructionfiles layer
        <layer>`` shows the files at one layer;
        ``/instructionfiles panel`` shows the panel derived
        from the whole book. Reading registers and publishes
        nothing as session news: entries are held only when
        they are given through the agent's canon roads, and
        every entry held for the session is journaled as an
        instruction_files_entry session event and every
        derived panel as an instruction_files_panel session
        event. This surface writes, renames and applies no
        file - a foreign file stays a foreign file, honoured
        on its own turf - and there is no Part VIII board
        yet, so the account is visible on this surface, not
        on a board.
        """
        from ..core.instruction_files import (
            format_entries,
            format_entry,
            format_panel,
            parse_instruction_files_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_instruction_files_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "entry":
                text = format_entry(primary.get_instruction_file(target))
            elif action == "origin":
                text = format_entries(
                    primary.instruction_files_book(), target)
            elif action == "layer":
                text = "\n".join(
                    format_entry(entry) for entry in
                    primary.instruction_files_for_layer(target)) or (
                    "No instruction files are held.")
            elif action == "panel":
                text = format_panel(primary.instruction_files_book())
            else:
                text = primary.instruction_files_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_memory_map(self, args: str):
        """M-150: /memorymap - project memory map (Mythic law).

        ``/memorymap`` shows the project memory map held
        this session (the shipped example book - nine
        facts at the M-149 slice boundary, of every
        section, with its one pinned panel - when none is
        held yet); ``/memorymap entry <entry-id>`` shows
        one entry; ``/memorymap section <section>`` shows
        the entries of one section; ``/memorymap panel``
        shows the panel derived from the whole book, kept
        by the Scribe. Reading registers and publishes
        nothing as session news: entries are held only
        when they are given through the agent's map roads,
        and every entry held for the session is journaled
        as a project_memory_map_entry session event and
        every derived panel as a project_memory_map_panel
        session event. This surface writes and edits no
        project file, and there is no Part VIII board yet,
        so the map is visible on this surface, not on a
        board.
        """
        from ..core.project_memory_map import (
            format_entries,
            format_entry,
            format_panel,
            parse_memory_map_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_memory_map_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "entry":
                text = format_entry(primary.get_memory_map_entry(target))
            elif action == "section":
                text = format_entries(
                    primary.project_memory_map_book(), target)
            elif action == "panel":
                text = format_panel(primary.project_memory_map_book())
            else:
                text = primary.project_memory_map_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_glassbox(self, args: str):
        """M-151: /glassbox - compaction v2, glass-box.

        ``/glassbox`` shows the compaction glass-box
        held this session (the shipped example book -
        three compactions at the M-150 slice boundary,
        one of each shipped road, one holding its
        material by journal reference alone and one
        carrying an edited summary, with its one
        pinned panel - when none is held yet);
        ``/glassbox record <record-id>`` shows one
        record; ``/glassbox versions <record-id>``
        shows one record's summary versions, in order
        - the original first, the current summary
        last; ``/glassbox panel`` shows the panel
        derived from the whole book, its rows in
        journal order. Reading registers and publishes
        nothing as session news: records are held only
        when they are given through the agent's
        glass-box roads, and every record held for the
        session is journaled as a
        compaction_glassbox_record session event and
        every derived panel as a
        compaction_glassbox_panel session event. This
        surface compacts no live context - /compact
        stays the live pruner's own command - and
        there is no Part VIII board yet, so the glass
        box is visible on this surface, not on a board.
        """
        from ..core.compaction_glassbox import (
            format_panel,
            format_record,
            format_versions,
            parse_glassbox_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_glassbox_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "record":
                text = format_record(primary.get_compaction_record(target))
            elif action == "versions":
                text = format_versions(primary.get_compaction_record(target))
            elif action == "panel":
                text = format_panel(primary.compaction_glassbox_book())
            else:
                text = primary.compaction_glassbox_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_graphsearch(self, args: str):
        """M-152: /graphsearch - retrieval over the code graph.

        ``/graphsearch`` shows the graph retrieval
        held this session (the shipped example book -
        one retrieval at the M-151 slice boundary,
        its semantic seed grown one hop into six
        connected pieces, with its one pinned panel -
        when none is held yet); ``/graphsearch node
        <node-id>`` shows one connected piece;
        ``/graphsearch seeds`` shows the latest
        bundle's seeds; ``/graphsearch panel`` shows
        the panel derived from the latest bundle,
        its rows in ranked order. Reading registers
        and publishes nothing as session news:
        bundles are held only when they are given
        through the agent's graph-retrieval roads or
        run over the workspace, and every bundle
        held for the session is journaled as a
        graph_retrieval_bundle session event and
        every derived panel as a
        graph_retrieval_panel session event. This
        surface calls no model and edits no code,
        and there is no Part VIII board yet, so the
        retrieval is visible on this surface, not
        on a board.
        """
        from ..core.graph_retrieval import (
            format_node,
            format_panel,
            format_seeds,
            parse_graphsearch_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_graphsearch_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "node":
                text = format_node(primary.get_graph_retrieval_node(target))
            elif action == "seeds":
                text = format_seeds(primary.graph_retrieval_book())
            elif action == "panel":
                text = format_panel(primary.graph_retrieval_book())
            else:
                text = primary.graph_retrieval_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_daymemory(self, args: str):
        """M-153: /daymemory - session memory across days.

        ``/daymemory`` shows the session memory held
        this session (the shipped example book - one
        situation at the M-152 slice boundary, its
        session paused at the end of its day with
        three map facts, two open slices and two
        standing decisions carried, with its one
        pinned panel - when none is held yet);
        ``/daymemory situation <situation-id>`` shows
        one situation; ``/daymemory memory`` shows the
        latest situation's carried memory;
        ``/daymemory slices`` its open slices;
        ``/daymemory decisions`` its standing
        decisions; ``/daymemory panel`` shows the
        panel derived from the latest situation, its
        rows in panel order. Reading registers and
        publishes nothing as session news: situations
        are held only when they are given through the
        agent's session-memory roads or restored from
        a stored session, and every situation held for
        the session is journaled as a
        session_memory_situation session event and
        every derived panel as a session_memory_panel
        session event. This surface calls no model,
        resumes no live session and replays no
        transcript, and there is no Part VIII board
        yet, so the situation is visible on this
        surface, not on a board.
        """
        from ..core.session_memory import (
            format_decisions,
            format_memory,
            format_panel,
            format_situation,
            format_slices,
            parse_session_memory_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_session_memory_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "situation":
                text = format_situation(
                    primary.get_session_situation(target))
            elif action == "memory":
                text = format_memory(primary.session_memory_book())
            elif action == "slices":
                text = format_slices(primary.session_memory_book())
            elif action == "decisions":
                text = format_decisions(primary.session_memory_book())
            elif action == "panel":
                text = format_panel(primary.session_memory_book())
            else:
                text = primary.session_memory_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_crossmemory(self, args: str):
        """M-154: /crossmemory - cross-project memory.

        ``/crossmemory`` shows the cross-project book
        held this session (the shipped example book -
        three lessons at the M-153 slice boundary, one
        accepted into a sibling project, one on offer
        and one declined, with its one pinned panel -
        when none is held yet); ``/crossmemory lesson
        <lesson-id>`` shows one shared lesson with its
        provenance whole; ``/crossmemory offers``
        shows the book's offers in held order;
        ``/crossmemory accepted <project>`` shows the
        lessons standing accepted into one target
        project; ``/crossmemory panel`` shows the
        exchange panel derived from the whole book,
        its rows in panel order. Reading registers and
        publishes nothing as session news: lessons and
        offers are held only when they are given
        through the agent's cross-project roads or
        offered onward from the session's memory map,
        and every lesson held for the session is
        journaled as a cross_project_lesson session
        event, every offer as a cross_project_offer
        session event and every derived panel as a
        cross_project_panel session event. This
        surface calls no model, writes no project's
        files and enters nothing into any project's
        memory, and there is no Part VIII board yet,
        so the exchange is visible on this surface,
        not on a board.
        """
        from ..core.cross_project_memory import (
            format_accepted,
            format_lesson,
            format_offers,
            format_panel,
            parse_cross_project_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_cross_project_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "lesson":
                text = format_lesson(
                    primary.get_cross_project_lesson(target))
            elif action == "offers":
                text = format_offers(primary.cross_project_book())
            elif action == "accepted":
                text = format_accepted(
                    primary.cross_project_book(), target)
            elif action == "panel":
                text = format_panel(primary.cross_project_book())
            else:
                text = primary.cross_project_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_ledger(self, args: str):
        """M-155: /ledger - the self-improving ledger.

        ``/ledger`` shows the self-improving book held
        this session (the shipped example book - three
        candidates at the M-154 slice boundary, one
        promoted into standing memory under a named
        standing rule, one still a candidate and one
        declined, with its one pinned panel - when none
        is held yet); ``/ledger candidate <candidate-id>``
        shows one candidate memory with its provenance
        whole; ``/ledger decisions`` shows the book's
        promotion decisions in held order; ``/ledger
        standing`` shows the candidates standing as
        standing memories; ``/ledger panel`` shows the
        ledger panel derived from the whole book, its
        rows in panel order. Reading registers and
        publishes nothing as session news: candidates
        and decisions are held only when they are given
        through the agent's self-improving roads or
        captured from the session's memory map, and
        every candidate held for the session is
        journaled as a self_improving_candidate session
        event, every decision as a
        self_improving_decision session event and every
        derived panel as a self_improving_panel session
        event. This surface calls no model, writes no
        project files and updates no live memory, and
        there is no Part VIII board yet, so the ledger
        is visible on this surface, not on a board.
        """
        from ..core.self_improving_ledger import (
            format_candidate,
            format_decisions,
            format_panel,
            format_standing,
            parse_self_improving_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_self_improving_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "candidate":
                text = format_candidate(
                    primary.get_self_improving_candidate(target))
            elif action == "decisions":
                text = format_decisions(primary.self_improving_book())
            elif action == "standing":
                text = format_standing(primary.self_improving_book())
            elif action == "panel":
                text = format_panel(primary.self_improving_book())
            else:
                text = primary.self_improving_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_decisions(self, args: str):
        """M-156: /decisions - decision records.

        ``/decisions`` shows the decision book held
        this session (the shipped example book - three
        records at the M-155 slice boundary, one
        accepted as the project's road, one still
        proposed and one superseded by the accepted
        record, with its one pinned panel - when none
        is held yet); ``/decisions record <record-id>``
        shows one decision record with its provenance
        whole; ``/decisions adr <record-id>`` renders
        one record as the small ADR that would land
        in the project docs; ``/decisions accepted``
        shows the records standing accepted;
        ``/decisions panel`` shows the decision panel
        derived from the whole book, its rows in panel
        order. Reading registers and publishes nothing
        as session news: records are held only when
        they are given through the agent's decision
        roads or drafted from the session's standing
        decisions, and every record held for the
        session is journaled as a decision_record
        session event and every derived panel as a
        decision_panel session event. This surface
        calls no model and writes no project docs,
        and there is no Part VIII board yet, so the
        records are visible on this surface, not on a
        board.
        """
        from ..core.decision_records import (
            format_accepted,
            format_adr,
            format_panel,
            format_record,
            parse_decision_records_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_decision_records_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "record":
                text = format_record(
                    primary.get_decision_record(target))
            elif action == "adr":
                text = format_adr(
                    primary.get_decision_record(target))
            elif action == "accepted":
                text = format_accepted(primary.decision_records_book())
            elif action == "panel":
                text = format_panel(primary.decision_records_book())
            else:
                text = primary.decision_records_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_forget(self, args: str):
        """M-157: /forget - forget and quarantine.

        ``/forget`` shows the forget book held this
        session (the shipped example book - four entries
        at the M-156 slice boundary, two forgotten, one
        quarantined and one restored, with its one pinned
        panel - when none is held yet); ``/forget entry
        <entry-id>`` shows one forget entry with its
        provenance whole; ``/forget forgotten`` shows the
        entries standing forgotten; ``/forget quarantined``
        shows the memories still held apart; ``/forget
        panel`` shows the forget panel derived from the
        whole book, its rows in panel order. Reading
        registers and publishes nothing as session news:
        entries are held only when they are given through
        the agent's forget roads or journaled from the
        session's carried memory, and every entry held
        for the session is journaled as a forget_entry
        session event and every derived panel as a
        forget_panel session event - by class and
        reference only, never the forgotten thing's
        content. This surface calls no model and mutates
        no live memory, and there is no Part VIII board
        yet, so the journal is visible on this surface,
        not on a board.
        """
        from ..core.forget_quarantine import (
            format_entry,
            format_forgotten,
            format_panel,
            format_quarantined,
            parse_forget_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_forget_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "entry":
                text = format_entry(primary.get_forget_entry(target))
            elif action == "forgotten":
                text = format_forgotten(primary.forget_quarantine_book())
            elif action == "quarantined":
                text = format_quarantined(primary.forget_quarantine_book())
            elif action == "panel":
                text = format_panel(primary.forget_quarantine_book())
            else:
                text = primary.forget_quarantine_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_recipes(self, args: str):
        """M-158: /recipes - context recipes.

        ``/recipes`` shows the recipe book held this
        session (the shipped example book - three recipes
        at the M-157 slice boundary, eight pieces bundled,
        with its one pinned panel - when none is held
        yet); ``/recipes recipe <recipe-id>`` shows one
        context recipe with its provenance whole;
        ``/recipes summon <recipe name>`` summons the
        recipe the name names, whole; ``/recipes panel``
        shows the recipe panel derived from the whole
        book, its rows in panel order. Reading registers
        and publishes nothing as session news: recipes are
        held only when they are given through the agent's
        recipe roads or bundled from the session's carried
        memory, and every recipe held or summoned for the
        session is journaled as a context_recipe session
        event and every derived panel as a
        context_recipe_panel session event. This surface
        calls no model and assembles no live context, and
        there is no Part VIII board yet, so the book is
        visible on this surface, not on a board.
        """
        from ..core.context_recipes import (
            format_panel,
            format_recipe,
            parse_recipe_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_recipe_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "recipe":
                text = format_recipe(primary.get_context_recipe(target))
            elif action == "summon":
                text = primary.summon_context_recipe(target)["summon_text"]
            elif action == "panel":
                text = format_panel(primary.context_recipes_book())
            else:
                text = primary.context_recipes_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_pins(self, args: str):
        """M-159: /pins - pinning and protection.

        ``/pins`` shows the pinning book held this
        session (the shipped example book - four pins
        at the M-158 slice boundary, with its one
        pinned panel - when none is held yet);
        ``/pins pin <pin-id>`` shows one pin with its
        provenance whole; ``/pins kind <kind>`` shows
        the pins of one kind; ``/pins panel`` shows
        the pin panel derived from the whole book, its
        rows in panel order. Reading registers and
        publishes nothing as session news: pins are
        held only when they are given through the
        agent's pin roads or protected from the
        session's compactions, and every pin held for
        the session is journaled as a
        pinning_protection_pin session event and every
        derived panel as a pinning_protection_panel
        session event. This surface calls no model and
        compacts nothing, and there is no Part VIII
        board yet, so the book is visible on this
        surface, not on a board.
        """
        from ..core.pinning_protection import (
            format_panel,
            format_pin,
            format_pins,
            parse_pin_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_pin_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "pin":
                text = format_pin(primary.get_pin(target))
            elif action == "kind":
                text = format_pins(
                    primary.pinning_protection_book(), target)
            elif action == "panel":
                text = format_panel(primary.pinning_protection_book())
            else:
                text = primary.pinning_protection_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_thrift(self, args: str):
        """M-160: /thrift - token thrift.

        ``/thrift`` shows the thrift book held this
        session (the shipped example book - four
        records at the M-159 slice boundary, with its
        one pinned panel - when none is held yet);
        ``/thrift record <record-id>`` shows one record
        with its provenance whole; ``/thrift road
        <road>`` shows the records of one road;
        ``/thrift panel`` shows the thrift panel
        derived from the whole book, its rows in panel
        order; ``/thrift costs`` shows the thrift cost
        line derived for the whole book - the line
        mythic costs reports for thrift. Reading
        registers and publishes nothing as session
        news: records are held only when they are given
        through the agent's thrift roads or counted
        from the session's context, and every record
        held for the session is journaled as a
        token_thrift_record session event, every
        derived panel as a token_thrift_panel session
        event and every derived cost line as a
        token_thrift_cost_line session event. This
        surface calls no model and reads no file, and
        there is no Part VIII board yet, so the book is
        visible on this surface, not on a board.
        """
        from ..core.token_thrift import (
            format_cost_line,
            format_panel,
            format_thrift_record,
            format_thrift_records,
            parse_thrift_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_thrift_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "record":
                text = format_thrift_record(
                    primary.get_thrift_record(target))
            elif action == "road":
                text = format_thrift_records(
                    primary.token_thrift_book(), target)
            elif action == "panel":
                text = format_panel(primary.token_thrift_book())
            elif action == "costs":
                text = format_cost_line(primary.token_thrift_book())
            else:
                text = primary.token_thrift_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_endurance(self, args: str):
        """M-161: /endurance - long-session endurance.

        ``/endurance`` shows the endurance book held
        this session (the shipped example book - five
        measurements at the M-160 slice boundary, with
        its one pinned panel - when none is held yet);
        ``/endurance record <record-id>`` shows one
        record with its provenance whole;
        ``/endurance kind <kind>`` shows the records
        of one kind; ``/endurance panel`` shows the
        endurance panel derived from the whole book,
        its rows in panel order; ``/endurance verdict``
        shows the endurance verdict derived for the
        whole book - over budget reported, never
        passed. Reading registers and publishes
        nothing as session news: records are held only
        when they are given through the agent's
        endurance roads or measured from the session's
        memory, and every record held for the session
        is journaled as a long_session_endurance_record
        session event, every derived panel as a
        long_session_endurance_panel session event and
        every derived verdict as a
        long_session_endurance_verdict session event.
        This surface runs no live session and times
        nothing, and there is no Part VIII board yet,
        so the book is visible on this surface, not on
        a board.
        """
        from ..core.long_session_endurance import (
            format_endurance_record,
            format_endurance_records,
            format_panel,
            format_verdict,
            parse_endurance_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_endurance_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "record":
                text = format_endurance_record(
                    primary.get_endurance_record(target))
            elif action == "kind":
                text = format_endurance_records(
                    primary.long_session_endurance_book(), target)
            elif action == "panel":
                text = format_panel(primary.long_session_endurance_book())
            elif action == "verdict":
                text = format_verdict(primary.long_session_endurance_book())
            else:
                text = primary.long_session_endurance_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_multisession(self, args: str):
        """M-162: /multisession - multi-session per project.

        ``/multisession`` shows the multi-session book
        held this session (the shipped example book -
        four sessions at the M-161 slice boundary, with
        its one pinned panel - when none is held yet);
        ``/multisession session <session-id>`` shows one
        session with its provenance whole;
        ``/multisession branch <branch>`` shows the
        session standing on one branch;
        ``/multisession panel`` shows the multi-session
        panel derived from the whole book;
        ``/multisession isolation`` shows the isolation
        verdict derived for the whole book - no journal
        crosstalk, ever. Reading registers and publishes
        nothing as session news: sessions are held only
        when they are given through the agent's
        multi-session roads or stood from the session's
        memory, and every session held for the session
        is journaled as a multi_session_projects_session
        session event, every derived panel as a
        multi_session_projects_panel session event and
        every derived verdict as a
        multi_session_projects_isolation session event.
        This surface spawns no live session, and there
        is no Part VIII board yet, so the book is
        visible on this surface, not on a board.
        """
        from ..core.multi_session_projects import (
            format_isolation,
            format_parallel_session,
            format_parallel_sessions,
            format_panel,
            parse_multisession_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_multisession_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "session":
                text = format_parallel_session(
                    primary.get_parallel_session(target))
            elif action == "branch":
                text = format_parallel_sessions(
                    primary.multi_session_projects_book(), target)
            elif action == "panel":
                text = format_panel(primary.multi_session_projects_book())
            elif action == "isolation":
                text = format_isolation(primary.multi_session_projects_book())
            else:
                text = primary.multi_session_projects_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_handoffsummary(self, args: str):
        """M-163: /handoffsummary - handoff summaries.

        ``/handoffsummary`` shows the handoff book
        held this session (the shipped example book -
        three handoffs at the M-162 slice boundary,
        with its one pinned panel - when none is held
        yet); ``/handoffsummary handoff <handoff-id>``
        shows one handoff with its provenance whole;
        ``/handoffsummary session <session-ref>`` shows
        the handoff ending one session;
        ``/handoffsummary panel`` shows the handoff
        panel derived from the whole book;
        ``/handoffsummary verdict`` shows the handoff
        verdict derived for the whole book - what
        needs you, named first. Reading registers and
        publishes nothing as session news: handoffs are
        held only when they are given through the
        agent's handoff roads or written from the
        session's stand-up, and every handoff held for
        the session is journaled as a
        handoff_summaries_handoff session event, every
        derived panel as a handoff_summaries_panel
        session event and every derived verdict as a
        handoff_summaries_verdict session event. This
        surface sends nothing, and there is no Part
        VIII board yet, so the book is visible on this
        surface, not on a board.
        """
        from ..core.handoff_summaries import (
            format_handoff,
            format_handoffs,
            format_panel,
            format_verdict,
            parse_handoffsummary_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_handoffsummary_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "handoff":
                text = format_handoff(
                    primary.get_handoff_summary(target))
            elif action == "session":
                text = format_handoffs(
                    primary.handoff_summaries_book(), target)
            elif action == "panel":
                text = format_panel(primary.handoff_summaries_book())
            elif action == "verdict":
                text = format_verdict(primary.handoff_summaries_book())
            else:
                text = primary.handoff_summaries_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_memoryxport(self, args: str):
        """M-164: /memoryxport - memory import/export.

        ``/memoryxport`` shows the memory export book
        held this session (the shipped example book -
        two packages at the M-163 slice boundary, one
        packed whole and one map-only, with its one
        pinned panel - when none is held yet);
        ``/memoryxport package <package-id>`` shows one
        package with its provenance whole;
        ``/memoryxport project <project>`` shows the
        packages packing one project;
        ``/memoryxport panel`` shows the memory panel
        derived from the whole book;
        ``/memoryxport verdict`` shows the portability
        verdict derived for the whole book - a partial
        packing named plainly. Reading registers and
        publishes nothing as session news: packages are
        held only when they are given through the agent's
        package roads, exported from the session's map +
        ledger, or held on the import road, and every
        package held for the session is journaled as a
        memory_import_export_package session event, every
        derived panel as a memory_import_export_panel
        session event and every derived verdict as a
        memory_import_export_verdict session event. This
        surface writes no live memory, and there is no
        Part VIII board yet, so the book is visible on
        this surface, not on a board.
        """
        from ..core.memory_import_export import (
            format_package,
            format_packages,
            format_panel,
            format_verdict,
            parse_memoryxport_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_memoryxport_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "package":
                text = format_package(
                    primary.get_memory_package(target))
            elif action == "project":
                text = format_packages(
                    primary.memory_import_export_book(), target)
            elif action == "panel":
                text = format_panel(primary.memory_import_export_book())
            elif action == "verdict":
                text = format_verdict(primary.memory_import_export_book())
            else:
                text = primary.memory_import_export_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_subconscious(self, args: str):
        """M-165: /subconscious - the subconscious v2.

        ``/subconscious`` shows the subconscious book
        held this session (the shipped example book -
        six memories at the M-164 slice boundary, three
        fresh in the core layer and one fading, one
        stale and one faded in the subconscious, with
        its one pinned panel - when none is held yet);
        ``/subconscious memory <memory-id>`` shows one
        memory with its provenance whole;
        ``/subconscious layer <core|subconscious>``
        shows one layer's memories;
        ``/subconscious source <source-kind>`` shows
        the memories earned from one kind;
        ``/subconscious panel`` shows the subconscious
        panel derived from the whole book;
        ``/subconscious verdict`` shows the freshness
        verdict derived for the whole book - a faded
        book named neglected plainly. Reading registers
        and publishes nothing as session news: memories
        are held only when they are given through the
        agent's memory roads, earned on the harvest
        road, or held on the book roads, and every
        memory held for the session is journaled as a
        subconscious_v2_memory session event, every
        derived panel as a subconscious_v2_panel
        session event and every derived verdict as a
        subconscious_v2_verdict session event. This
        surface writes no live memory, and there is no
        Part VIII board yet, so the book is visible on
        this surface, not on a board.
        """
        from ..core.subconscious_v2 import (
            format_memories,
            format_memory,
            format_panel,
            format_verdict,
            parse_subconscious_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_subconscious_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "memory":
                text = format_memory(
                    primary.get_subconscious_memory(target))
            elif action == "layer":
                text = format_memories(
                    primary.subconscious_book(), layer=target)
            elif action == "source":
                text = format_memories(
                    primary.subconscious_book(), source_kind=target)
            elif action == "panel":
                text = format_panel(primary.subconscious_book())
            elif action == "verdict":
                text = format_verdict(primary.subconscious_book())
            else:
                text = primary.subconscious_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_contradiction(self, args: str):
        """M-166: /contradiction - contradiction watch.

        ``/contradiction`` shows the contradiction
        book held this session (the shipped example
        book - four watches at the M-165 slice
        boundary, one over each of the memory map,
        session memory, the subconscious v2 and crew
        memory, with its one pinned panel - when none
        is held yet); ``/contradiction watch
        <watch-id>`` shows one watch with its
        correction shown - the stored claim and the
        newer evidence that replaces it;
        ``/contradiction kind <memory-kind>`` shows
        the watches standing over one holding;
        ``/contradiction panel`` shows the
        contradiction panel derived from the whole
        book; ``/contradiction verdict`` shows the
        correction verdict derived for the whole
        book - a map broadly overturned named plainly.
        Reading registers and publishes nothing as
        session news: watches are held only when they
        are given through the agent's watch roads,
        raised over a subconscious memory on the
        composing road, or held on the book roads,
        and every watch held for the session is
        journaled as a contradiction_watch_watch
        session event, every derived panel as a
        contradiction_watch_panel session event and
        every derived verdict as a
        contradiction_watch_verdict session event.
        This surface overwrites no stored memory, and
        there is no Part VIII board yet, so the book
        is visible on this surface, not on a board.
        """
        from ..core.contradiction_watch import (
            format_panel,
            format_verdict,
            format_watch,
            format_watches,
            parse_contradiction_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_contradiction_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "watch":
                text = format_watch(
                    primary.get_contradiction_watch(target))
            elif action == "kind":
                text = format_watches(
                    primary.contradiction_book(), kind=target)
            elif action == "panel":
                text = format_panel(primary.contradiction_book())
            elif action == "verdict":
                text = format_verdict(primary.contradiction_book())
            else:
                text = primary.contradiction_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_private(self, args: str):
        """M-167: /private - private by architecture.

        ``/private`` shows the privacy book held
        this session (the shipped example book -
        five postings at the M-166 slice boundary,
        four sealed in their stores and one carried
        out through the export bridge the user
        explicitly opened, with its one pinned panel
        - when none is held yet); ``/private posting
        <posting-id>`` shows one posting with its
        boundary shown - the store the memory lives
        in and the one bridge the user opened over
        it, if any; ``/private kind <memory-kind>``
        shows the postings standing over one
        holding; ``/private home <home>`` shows the
        postings living in one store; ``/private
        panel`` shows the privacy panel derived from
        the whole book; ``/private verdict`` shows
        the privacy verdict derived for the whole
        book - a book standing open at the user's own
        hand named plainly. Reading registers and
        publishes nothing as session news: postings
        are held only when they are given through
        the agent's posting roads, raised over a
        contradiction watch on the composing road,
        or held on the book roads, and every posting
        held for the session is journaled as a
        private_by_architecture_posting session
        event, every derived panel as a
        private_by_architecture_panel session event
        and every derived verdict as a
        private_by_architecture_verdict session
        event. This surface moves no memory and
        opens no bridge, and there is no Part VIII
        board yet, so the book is visible on this
        surface, not on a board.
        """
        from ..core.private_by_architecture import (
            format_panel,
            format_posting,
            format_postings,
            format_verdict,
            parse_privacy_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_privacy_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "posting":
                text = format_posting(
                    primary.get_privacy_posting(target))
            elif action == "kind":
                text = format_postings(
                    primary.privacy_book(), kind=target)
            elif action == "home":
                text = format_postings(
                    primary.privacy_book(), home=target)
            elif action == "panel":
                text = format_panel(primary.privacy_book())
            elif action == "verdict":
                text = format_verdict(primary.privacy_book())
            else:
                text = primary.privacy_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_memorydoctor(self, args: str):
        """M-168: /memorydoctor - memory doctor.

        ``/memorydoctor`` shows the doctor book held
        this session (the shipped example book -
        five findings at the M-167 slice boundary,
        four safely repairable and one store-wide
        corruption referred to the user, with its
        one pinned panel - when none is held yet);
        ``/memorydoctor finding <finding-id>`` shows
        one finding with its repair shown - the
        check that raised it, what it saw, and the
        one derived safe repair or the plain word
        that it stands referred; ``/memorydoctor
        check <check>`` shows the findings one check
        raised; ``/memorydoctor store <store>``
        shows the findings over memories living in
        one store; ``/memorydoctor panel`` shows the
        doctor panel derived from the whole book;
        ``/memorydoctor verdict`` shows the doctor
        verdict derived for the whole book;
        ``/memorydoctor repairs`` shows the repairs
        derived from the whole book - what the
        doctor will repair on the held book beside
        what it will not repair at all. Reading
        registers and publishes nothing as session
        news: findings are held only when they are
        given through the agent's finding roads,
        raised over the session's own held books on
        the check-run road, or held on the book
        roads, and every finding held for the
        session is journaled as a
        memory_doctor_finding session event, every
        derived panel as a memory_doctor_panel
        session event, every derived verdict as a
        memory_doctor_verdict session event and
        every applied repair as a
        memory_doctor_repair session event. This
        surface rewrites no live store and deletes
        no memory, and there is no Part VIII board
        yet, so the book is visible on this surface,
        not on a board. The pre-existing ``/doctor``
        surface is the shell-command fixer and keeps
        its own grammar; the memory checks live
        here, beside the other session memory books,
        and on the ``mythic doctor`` CLI as the
        ``memory`` health check over the shipped
        store files.
        """
        from ..core.memory_doctor import (
            format_finding,
            format_findings,
            format_panel,
            format_repairs,
            format_verdict,
            parse_memory_doctor_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_memory_doctor_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "finding":
                text = format_finding(
                    primary.get_memory_finding(target))
            elif action == "check":
                text = format_findings(
                    primary.memory_doctor_book(), check=target)
            elif action == "store":
                text = format_findings(
                    primary.memory_doctor_book(), store=target)
            elif action == "panel":
                text = format_panel(primary.memory_doctor_book())
            elif action == "verdict":
                text = format_verdict(primary.memory_doctor_book())
            elif action == "repairs":
                text = format_repairs(primary.memory_doctor_book())
            else:
                text = primary.memory_doctor_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_coldstart(self, args: str):
        """M-169: /coldstart - cold-start kindness.

        ``/coldstart`` shows the cold-start book
        held this session (the shipped example book
        - three openings at the M-168 slice boundary,
        one huge old project warming in the
        background, one project with no map at all
        and one small fresh project served as it
        stands, with its one pinned panel - when
        none is held yet); ``/coldstart record
        <record-id>`` shows one record with its
        derived plan shown - the evidence it stands
        on and the stages its evidence derives, in
        order; ``/coldstart project <project-ref>``
        shows the opening one project stands under;
        ``/coldstart panel`` shows the readiness
        panel derived from the whole book - what is
        usable now beside what is still rebuilding;
        ``/coldstart verdict`` shows the cold-start
        verdict derived for the whole book;
        ``/coldstart stages`` shows every record's
        derived stage plan. Reading registers and
        publishes nothing as session news: records
        are held only when they are given through
        the agent's record roads, raised over the
        session's own held map on the opening road,
        or held on the book roads, and every record
        held for the session is journaled as a
        cold_start_record session event, every
        derived panel as a cold_start_panel session
        event, every derived verdict as a
        cold_start_verdict session event and every
        marked stage as a cold_start_progress
        session event. This surface starts no
        thread, rebuilds no live map and opens no
        live project, and there is no Part VIII
        board yet, so the book is visible on this
        surface, not on a board.
        """
        from ..core.cold_start import (
            format_panel,
            format_record,
            format_records,
            format_verdict,
            parse_cold_start_args,
            stage_plan_of,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_cold_start_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "record":
                text = format_record(
                    primary.get_cold_start_record(target))
            elif action == "project":
                text = format_record(
                    primary.cold_start_for_project(target))
            elif action == "panel":
                text = format_panel(primary.cold_start_book())
            elif action == "verdict":
                text = format_verdict(primary.cold_start_book())
            elif action == "stages":
                book = primary.cold_start_book()
                text = "\n".join(
                    f"{r.record_id or '-'}: "
                    f"{', '.join(stage_plan_of(r))}"
                    for r in book.records)
            else:
                text = primary.cold_start_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_workview(self, args: str):
        """M-172: /workview - streaming work view.

        ``/workview`` shows the work book held this
        session as a calm narrative stream (the
        shipped example book - six actions at the
        M-171 slice boundary, five done and the
        verdict check still standing started, with
        its one pinned panel - when none is held
        yet); ``/workview event <event-id>`` shows
        one event as its narrative line, its detail
        still held back; ``/workview detail`` shows
        the whole stream with its tool detail, and
        ``/workview detail <event-id>`` shows one
        event with its detail - the one-keystroke
        -away road; ``/workview kind <kind>`` shows
        one kind's actions; ``/workview panel``
        shows the work panel derived from the whole
        book - the stream at a glance, narrative
        only; ``/workview verdict`` shows the work
        verdict derived for the whole book. Reading
        registers and publishes nothing as session
        news: events are held only when they are
        given through the agent's register roads,
        raised over a shipped tool action on the
        streaming road, or held on the book roads,
        and every event held for the session is
        journaled as a work_view_event session
        event, every derived panel as a
        work_view_panel session event and every
        derived verdict as a work_view_verdict
        session event. This surface runs no tool
        and streams nothing live, and the slice
        board is M-173's road, so the book is
        visible on this surface, not on a board.
        """
        from ..core.work_view import (
            format_event,
            format_event_detail,
            format_panel,
            format_stream,
            format_verdict,
            parse_work_view_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_work_view_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "event":
                text = format_event(
                    primary.get_work_view_event(target))
            elif action == "detail" and target is not None:
                text = format_event_detail(
                    primary.get_work_view_event(target))
            elif action == "detail":
                text = format_stream(
                    primary.work_view_book(), detail=True)
            elif action == "kind":
                text = format_stream(
                    primary.work_view_book(), kind=target)
            elif action == "panel":
                text = format_panel(primary.work_view_book())
            elif action == "verdict":
                text = format_verdict(primary.work_view_book())
            else:
                text = primary.work_view_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_sliceboard(self, args: str):
        """M-173: /sliceboard - the slice board.

        ``/sliceboard`` shows the slice board held
        this session as a visible board (the shipped
        example board - seven cards at the M-172
        slice boundary, two banked, M-173 building
        by hand, M-176 re-ordered up, M-175 paused
        and M-177 struck, with its one pinned panel -
        when none is held yet); ``/sliceboard card
        <slice-id>`` shows one effective card;
        ``/sliceboard column <column>`` shows one
        column's cards; ``/sliceboard action
        <action-id>`` shows one held hand action;
        ``/sliceboard panel`` shows the board panel
        derived from the whole board - the board at
        a glance; ``/sliceboard verdict`` shows the
        board verdict derived for the whole board.
        Reading registers and publishes nothing as
        session news: cards and actions are held
        only when they are given through the agent's
        register roads, stood on the board on the
        hand-action road, or held on the board
        roads, and every card held for the session
        is journaled as a slice_board_card session
        event, every hand action as a
        slice_board_action session event, every
        derived panel as a slice_board_panel session
        event and every derived verdict as a
        slice_board_verdict session event. This
        surface runs no build and banks nothing, and
        a hand action on it moves the held board
        alone - the shipped roadmap data is not
        rewritten here.
        """
        from ..core.slice_board import (
            format_action,
            format_board,
            format_card,
            format_panel,
            format_verdict,
            parse_slice_board_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_slice_board_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "card":
                text = format_card(
                    primary.get_slice_board_card(target))
            elif action == "column":
                text = format_board(
                    primary.slice_board_board(), column=target)
            elif action == "action":
                text = format_action(
                    primary.get_slice_board_action(target))
            elif action == "panel":
                text = format_panel(primary.slice_board_board())
            elif action == "verdict":
                text = format_verdict(primary.slice_board_board())
            else:
                text = primary.slice_board_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_approvalcards(self, args: str):
        """M-174: /approvalcards - approval cards perfected.

        ``/approvalcards`` shows the approval cards
        held this session as perfected cards (the
        shipped example book - four cards at the
        M-173 slice boundary, the test run remembered
        at its exact scope, the M-174 commit allowed,
        the costly push calm and awaiting, and the
        one destructive card alarmed and unanswered,
        with its one pinned panel - when none is held
        yet); ``/approvalcards card <card-id>`` shows
        one card whole, its target and consequence as
        their own lines; ``/approvalcards decision
        <decision-id>`` shows one held decision
        record; ``/approvalcards panel`` shows the
        panel derived from the whole book - the cards
        at a glance; ``/approvalcards verdict`` shows
        the verdict derived for the whole book.
        Reading registers and publishes nothing as
        session news: cards and decisions are held
        only when they are given through the agent's
        register roads, stood on a card on the
        deciding road, or held on the book roads, and
        every card held for the session is journaled
        as an approval_card session event, every
        decision as an approval_card_decision session
        event, every derived panel as an
        approval_cards_panel session event and every
        derived verdict as an approval_cards_verdict
        session event. This surface executes no
        approval and saves no remembered approval,
        and renders no live UI - a card held here is
        a question, never the act it asks about.
        """
        from ..core.approval_cards import (
            format_card,
            format_decision,
            format_panel,
            format_verdict,
            parse_approval_cards_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_approval_cards_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "card":
                text = format_card(
                    primary.get_approval_card(target))
            elif action == "decision":
                text = format_decision(
                    primary.get_approval_decision(target))
            elif action == "panel":
                text = format_panel(primary.approval_cards_book())
            elif action == "verdict":
                text = format_verdict(primary.approval_cards_book())
            else:
                text = primary.approval_cards_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_fuzzypicker(self, args: str):
        """M-175: /fuzzypicker - the fuzzy everything picker.

        ``/fuzzypicker`` shows the fuzzy picker held
        this session - files, symbols, commands,
        sessions, models and themes under one fuzzy
        finder grammar (the shipped example book -
        eight candidates at the M-174 slice boundary,
        with its two searches and its one pinned
        panel - when none is held yet);
        ``/fuzzypicker candidate <candidate-id>``
        shows one candidate whole, its kind, source,
        tags and detail as their own lines;
        ``/fuzzypicker search <search-id>`` shows one
        held search record; ``/fuzzypicker find
        <words>`` runs the grammar on the spot under
        an ad-hoc search and shows the derived panel;
        ``/fuzzypicker kind <kind>`` shows the book's
        candidates of one kind; ``/fuzzypicker panel``
        shows the panel derived from the whole book
        under its default search; ``/fuzzypicker
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: candidates and
        searches are held only when they are given
        through the agent's register roads, stood on
        the book on the finding road, or held on the
        book roads, and every candidate held for the
        session is journaled as a fuzzy_picker_candidate
        session event, every search as a
        fuzzy_picker_search session event, every
        derived panel as a fuzzy_picker_panel session
        event and every derived verdict as a
        fuzzy_picker_verdict session event. This
        surface opens nothing the picker finds,
        executes nothing, renders no live UI and banks
        nothing - a match held here is a finding, never
        the act of opening the thing found, and a
        search commits no choice at all.
        """
        from ..core.fuzzy_picker import (
            build_search,
            format_book,
            format_candidate,
            format_panel,
            format_search,
            format_verdict,
            parse_fuzzy_picker_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_fuzzy_picker_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "candidate":
                text = format_candidate(
                    primary.get_fuzzy_candidate(target))
            elif action == "search":
                text = format_search(
                    primary.get_fuzzy_search(target))
            elif action == "find":
                search = build_search({
                    "seq": 1, "text": target,
                    "kind_filter": "all",
                    "detail": "An on-the-spot search from "
                              "the /fuzzypicker surface.",
                    "recorded_on": "2026-11-09",
                    "actor": "the jarl",
                    "source": "fuzzy picker",
                    "origin_session": "session-m175"})
                text = format_panel(
                    primary.fuzzy_picker_book(), search)
            elif action == "kind":
                text = format_book(
                    primary.fuzzy_picker_book(), target)
            elif action == "panel":
                text = format_panel(primary.fuzzy_picker_book())
            elif action == "verdict":
                text = format_verdict(primary.fuzzy_picker_book())
            else:
                text = primary.fuzzy_picker_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_commandpalace(self, args: str):
        """M-176: /commandpalace - the slash-command palace.

        ``/commandpalace`` shows the command palace held
        this session - every shipped command and
        every custom command under one browsing
        grammar (the shipped example book -
        eight entries at the M-175 slice boundary,
        with its two browses and its one pinned
        panel - when none is held yet);
        ``/commandpalace entry <entry-id>``
        shows one entry whole, its kind, source,
        tags and detail as their own lines;
        ``/commandpalace browse <browse-id>`` shows one
        held browse record; ``/commandpalace find
        <words>`` runs the grammar on the spot under
        an ad-hoc browse and shows the derived panel;
        ``/commandpalace kind <kind>`` shows the book's
        entries of one kind; ``/commandpalace panel``
        shows the panel derived from the whole book
        under its default browse; ``/commandpalace
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: entries and
        browses are held only when they are given
        through the agent's register roads, stood on
        the book on the browsing road, or held on the
        book roads, and every entry held for the
        session is journaled as a command_palace_entry
        session event, every browse as a
        command_palace_browse session event, every
        derived panel as a command_palace_panel session
        event and every derived verdict as a
        command_palace_verdict session event. This
        surface opens nothing the palace finds,
        executes nothing, renders no live UI and banks
        nothing - an entry held here is a listing, never
        the act of opening the thing found, and a
        browse commits no choice at all.
        """
        from ..core.command_palace import (
            build_browse,
            format_book,
            format_entry,
            format_panel,
            format_browse,
            format_verdict,
            parse_command_palace_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_command_palace_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "entry":
                text = format_entry(
                    primary.get_palace_entry(target))
            elif action == "browse":
                text = format_browse(
                    primary.get_palace_browse(target))
            elif action == "visit":
                browse = build_browse({
                    "seq": 1, "text": target,
                    "kind_filter": "all",
                    "detail": "An on-the-spot browse from "
                              "the /commandpalace surface.",
                    "recorded_on": "2026-11-09",
                    "actor": "the jarl",
                    "source": "command palace",
                    "origin_session": "session-m176"})
                text = format_panel(
                    primary.command_palace_book(), browse)
            elif action == "kind":
                text = format_book(
                    primary.command_palace_book(), target)
            elif action == "panel":
                text = format_panel(primary.command_palace_book())
            elif action == "verdict":
                text = format_verdict(primary.command_palace_book())
            else:
                text = primary.command_palace_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_promptcraft(self, args: str):
        """M-177: /promptcraft - prompt craft.

        ``/promptcraft`` shows the prompt craft held
        this session - the input box's craft as data:
        multi-line drafts, history per project, pasted
        images and dropped files (the shipped example
        book - eight items at the M-176 slice
        boundary, with its two views and its one
        pinned panel - when none is held yet);
        ``/promptcraft item <item-id>`` shows one item
        whole, its kind, project, words and provenance
        as their own lines; ``/promptcraft view
        <view-id>`` shows one held view record;
        ``/promptcraft project <project>`` derives the
        panel of an on-the-spot view over one project
        and shows it; ``/promptcraft kind <kind>``
        shows the book's items of one kind;
        ``/promptcraft panel`` shows the panel derived
        from the whole book under its default view;
        ``/promptcraft verdict`` shows the verdict
        derived for the whole book. Reading registers
        and publishes nothing as session news: items
        and views are held only when they are given
        through the agent's register roads, stood on
        the book on the viewing road, or held on the
        book roads, and every item held for the
        session is journaled as a prompt_craft_item
        session event, every view as a prompt_craft_view
        session event, every derived panel as a
        prompt_craft_panel session event and every
        derived verdict as a prompt_craft_verdict
        session event. This surface edits no live
        input box, pastes nothing, drops nothing,
        dictates nothing (dictation is M-180's road),
        opens no dropped file, renders no live UI and
        banks nothing - an item held here is a
        finding, never the act of typing, pasting or
        sending the prompt found.
        """
        from ..core.prompt_craft import (
            build_view,
            format_book,
            format_item,
            format_panel,
            format_verdict,
            format_view,
            parse_prompt_craft_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_prompt_craft_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "item":
                text = format_item(
                    primary.get_craft_item(target))
            elif action == "view":
                text = format_view(
                    primary.get_craft_view(target))
            elif action == "project":
                view = build_view({
                    "seq": 1, "project_filter": target,
                    "detail": "An on-the-spot view from "
                              "the /promptcraft surface.",
                    "recorded_on": "2026-11-09",
                    "actor": "the jarl",
                    "source": "prompt craft",
                    "origin_session": "session-m177"})
                text = format_panel(
                    primary.prompt_craft_book(), view)
            elif action == "kind":
                text = format_book(
                    primary.prompt_craft_book(), target)
            elif action == "panel":
                text = format_panel(primary.prompt_craft_book())
            elif action == "verdict":
                text = format_verdict(primary.prompt_craft_book())
            else:
                text = primary.prompt_craft_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")
    def _handle_statusline(self, args: str):
        """M-178: /statusline - status line of truth.

        ``/statusline`` shows the status line held
        this session - the six facts as data: the
        model, the posture, the context meter, the
        cost so far, the crew state and the sandbox
        state (the shipped example book - six facts
        at the M-177 slice boundary, five standing
        measured and the cost fact standing honestly
        unknown, with its two views and its one
        pinned panel - when none is held yet);
        ``/statusline fact <fact-id>`` shows one fact
        whole, its kind, value, words, panel and
        keypress and provenance as their own lines;
        ``/statusline view <view-id>`` shows one held
        view record; ``/statusline kind <kind>``
        shows the book's facts of one kind;
        ``/statusline line`` shows the status line
        derived from the whole book; ``/statusline
        panel`` shows the panel derived from the
        whole book under its default view;
        ``/statusline verdict`` shows the verdict
        derived for the whole book. Reading registers
        and publishes nothing as session news: facts
        and views are held only when they are given
        through the agent's register roads, stood on
        the book on the viewing road, or held on the
        book roads, and every fact held for the
        session is journaled as a status_line_fact
        session event, every view as a
        status_line_view session event, every derived
        panel as a status_line_panel session event
        and every derived verdict as a
        status_line_verdict session event. This
        surface measures nothing live, reads no live
        model, context, cost, crew or sandbox state,
        binds no key, opens no panel, renders no live
        UI, rebuilds no live screen and banks
        nothing - a fact held here is a finding,
        never the live state of the screen it
        describes.
        """
        from ..core.status_line import (
            format_book,
            format_fact,
            format_line,
            format_panel,
            format_verdict,
            format_view,
            parse_status_line_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_status_line_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "fact":
                text = format_fact(
                    primary.get_status_fact(target))
            elif action == "view":
                text = format_view(
                    primary.get_status_view(target))
            elif action == "kind":
                text = format_book(
                    primary.status_line_book(), target)
            elif action == "line":
                text = format_line(primary.status_line_book())
            elif action == "panel":
                text = format_panel(primary.status_line_book())
            elif action == "verdict":
                text = format_verdict(primary.status_line_book())
            else:
                text = primary.status_line_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_themesgrownup(self, args: str):
        """M-179: /themesgrownup - themes grown up.

        ``/themesgrownup`` shows the themes grown up
        held this session - the theme system judged
        under the Design Lawbook discipline as data
        (the shipped example book - five themes at
        the M-178 slice boundary, the three shipped
        themes judged as data beside the
        high-contrast and no-colour themes this
        slice authors, with its two views and its
        one pinned panel - when none is held yet);
        ``/themesgrownup theme <theme-id>`` shows one
        theme whole, its mode, colours, cues, shares
        and provenance as their own lines;
        ``/themesgrownup view <view-id>`` shows one
        held view record; ``/themesgrownup mode
        <mode>`` shows the book's themes of one mode;
        ``/themesgrownup panel`` shows the panel
        derived from the whole book under its
        default view; ``/themesgrownup verdict``
        shows the verdict derived for the whole
        book. Reading registers and publishes nothing
        as session news: themes and views are held
        only when they are given through the agent's
        register roads, stood on the book on the
        viewing road, or held on the book roads, and
        every theme held for the session is journaled
        as a themes_grown_up_theme session event,
        every view as a themes_grown_up_view session
        event, every derived panel as a
        themes_grown_up_panel session event and every
        derived verdict as a themes_grown_up_verdict
        session event. This surface repaints no live
        UI, applies no theme live, renders no live
        UI, measures no running screen and banks
        nothing - a theme held here is a finding,
        never the live face of the app it describes.
        """
        from ..core.themes_grown_up import (
            format_book,
            format_panel,
            format_theme,
            format_verdict,
            format_view,
            parse_themes_grown_up_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_themes_grown_up_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "theme":
                text = format_theme(
                    primary.get_theme_profile(target))
            elif action == "view":
                text = format_view(
                    primary.get_theme_view(target))
            elif action == "mode":
                text = format_book(
                    primary.themes_grown_up_book(), target)
            elif action == "panel":
                text = format_panel(primary.themes_grown_up_book())
            elif action == "verdict":
                text = format_verdict(primary.themes_grown_up_book())
            else:
                text = primary.themes_grown_up_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_voiceinout(self, args: str):
        """M-180: /voiceinout - voice in and out.

        ``/voiceinout`` shows the voice in and out
        held this session - push-to-talk dictation
        for prompts and spoken stand-ups via the
        existing TTS (direct catalog casting, the
        house voice law), voice an extra door and
        never the only door (the shipped example
        book - seven items at the M-179 slice
        boundary, two dictations, two stand-ups and
        three actions, with its two views and its
        one pinned panel - when none is held yet);
        ``/voiceinout dictation <dictation-id>``
        shows one dictation session whole, its
        state, transcript, backends, availability
        and draft as their own lines;
        ``/voiceinout standup <standup-id>`` shows
        one spoken stand-up whole; ``/voiceinout
        action <action-id>`` shows one voice action
        and the text equivalent beside it;
        ``/voiceinout view <view-id>`` shows one
        held view record; ``/voiceinout kind
        <kind>`` shows the book's items of one kind;
        ``/voiceinout panel`` shows the panel
        derived from the whole book under its
        default view; ``/voiceinout verdict`` shows
        the verdict derived for the whole book.
        Reading registers and publishes nothing as
        session news: items and views are held only
        when they are given through the agent's
        register roads, stood on the book on the
        viewing road, or held on the book roads, and
        every dictation held for the session is
        journaled as a voice_in_out_dictation
        session event, every stand-up as a
        voice_in_out_standup session event, every
        action as a voice_in_out_action session
        event, every view as a voice_in_out_view
        session event, every derived panel as a
        voice_in_out_panel session event and every
        derived verdict as a voice_in_out_verdict
        session event. This surface captures no live
        audio, builds no TTS engine, speaks nothing
        live and banks nothing - and it sends no
        prompt: a dictation held here is a draft,
        never a send.
        """
        from ..core.voice_in_out import (
            format_action,
            format_book,
            format_dictation,
            format_panel,
            format_standup,
            format_verdict,
            format_view,
            parse_voice_in_out_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_voice_in_out_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "dictation":
                text = format_dictation(
                    primary.get_dictation_session(target))
            elif action == "standup":
                text = format_standup(
                    primary.get_spoken_standup(target))
            elif action == "action":
                text = format_action(
                    primary.get_voice_action(target))
            elif action == "view":
                text = format_view(
                    primary.get_voice_view(target))
            elif action == "kind":
                text = format_book(
                    primary.voice_in_out_book(), target)
            elif action == "panel":
                text = format_panel(primary.voice_in_out_book())
            elif action == "verdict":
                text = format_verdict(primary.voice_in_out_book())
            else:
                text = primary.voice_in_out_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_manners(self, args: str):
        """M-181: /manners - notifications with manners.

        ``/manners`` shows the notifications manners
        held this session - long jobs announce
        completion (terminal bell/OS notification,
        once), failures announce once with the one
        action that matters, and silence is the
        default posture (the shipped example book -
        seven items at the M-180 slice boundary,
        three jobs, two channels and two rules, with
        its two views and its one pinned panel - when
        none is held yet); ``/manners job <job-id>``
        shows one job whole, its outcome, duration,
        decision, channel and availability as their
        own lines; ``/manners channel <channel-id>``
        shows one notification channel whole;
        ``/manners rule <rule-id>`` shows one manners
        rule and the statement it stands on;
        ``/manners view <view-id>`` shows one held
        view record; ``/manners kind <kind>`` shows
        the book's items of one kind; ``/manners
        panel`` shows the panel derived from the
        whole book under its default view;
        ``/manners verdict`` shows the verdict
        derived for the whole book. Reading registers
        and publishes nothing as session news: items
        and views are held only when they are given
        through the agent's register roads, stood on
        the book on the viewing road, or held on the
        book roads, and every job held for the
        session is journaled as a
        notifications_manners_job session event,
        every channel as a notifications_manners_channel
        session event, every rule as a
        notifications_manners_rule session event,
        every view as a notifications_manners_view
        session event, every derived panel as a
        notifications_manners_panel session event
        and every derived verdict as a
        notifications_manners_verdict session event.
        This surface rings no bell and posts no
        notification - announcements travel the
        agent's announce road, through the seams,
        at most once each.
        """
        from ..core.notifications_manners import (
            format_book,
            format_channel,
            format_job,
            format_panel,
            format_rule,
            format_verdict,
            format_view,
            parse_notifications_manners_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_notifications_manners_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "job":
                text = format_job(
                    primary.get_job_notice(target))
            elif action == "channel":
                text = format_channel(
                    primary.get_channel_notice(target))
            elif action == "rule":
                text = format_rule(
                    primary.get_manners_rule(target))
            elif action == "view":
                text = format_view(
                    primary.get_notifications_view(target))
            elif action == "kind":
                text = format_book(
                    primary.notifications_manners_book(), target)
            elif action == "panel":
                text = format_panel(primary.notifications_manners_book())
            elif action == "verdict":
                text = format_verdict(primary.notifications_manners_book())
            else:
                text = primary.notifications_manners_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_skin(self, args: str):
        """M-182: /skin - the plain-language skin.

        ``/skin`` shows the plain-language skin held
        this session - reports, approvals and stand-ups
        in plain everyday words in Jarl mode, the
        technical detail folded behind the unfold
        keypress (the shipped example book - twelve
        items at the M-181 slice boundary, two
        reports, two approvals, two stand-ups and six
        lexicon terms, with its two views and its one
        pinned panel - when none is held yet);
        ``/skin report <report-id>`` shows one report
        whole; ``/skin approval <approval-id>`` shows
        one approval ask with the one action that
        matters; ``/skin standup <standup-id>`` shows
        one stand-up; ``/skin term <term-id>`` shows
        one lexicon term and its plain words;
        ``/skin view <view-id>`` shows one held view
        record; ``/skin kind <kind>`` shows the book's
        items of one kind; ``/skin panel`` shows the
        panel derived from the whole book under its
        default view; ``/skin verdict`` shows the
        verdict derived for the whole book;
        ``/skin unfold <item-id>`` unfolds one item's
        folded technical detail whole;
        ``/skin register`` names the register the
        session stands in. Reading registers and
        publishes nothing as session news: items and
        views are held only when they are given
        through the agent's register roads, stood on
        the book on the viewing road, or held on the
        book roads, and every report held for the
        session is journaled as a plain_language_report
        session event, every approval as a
        plain_language_approval session event, every
        stand-up as a plain_language_standup session
        event, every term as a plain_language_term
        session event, every view as a
        plain_language_view session event, every
        derived panel as a plain_language_panel
        session event and every derived verdict as a
        plain_language_verdict session event. This
        surface approves nothing and sends nothing -
        rendering and unfolding are words only.
        """
        from ..core.plain_language_skin import (
            format_approval,
            format_book,
            format_panel,
            format_rendering,
            format_report,
            format_standup,
            format_term,
            format_verdict,
            format_view,
            parse_plain_language_skin_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_plain_language_skin_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "report":
                text = format_report(
                    primary.get_skin_report(target),
                    primary.plain_language_skin_book())
            elif action == "approval":
                text = format_approval(
                    primary.get_skin_approval(target),
                    primary.plain_language_skin_book())
            elif action == "standup":
                text = format_standup(
                    primary.get_skin_standup(target),
                    primary.plain_language_skin_book())
            elif action == "term":
                text = format_term(
                    primary.get_skin_term(target))
            elif action == "view":
                text = format_view(
                    primary.get_skin_view(target))
            elif action == "kind":
                text = format_book(
                    primary.plain_language_skin_book(), target)
            elif action == "panel":
                text = format_panel(primary.plain_language_skin_book())
            elif action == "verdict":
                text = format_verdict(primary.plain_language_skin_book())
            elif action == "unfold":
                text = primary.unfold_plain_language_skin_item(
                    target)["text"]
            elif action == "register":
                text = (
                    "Register: "
                    f"{primary.plain_language_skin_register()}")
            else:
                text = primary.plain_language_skin_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_errors(self, args: str):
        """M-183: /errors - error kindness.

        ``/errors`` shows the error book held this
        session - every error told in plain words,
        what happened, what it means and the most
        likely fix, its technical trace folded behind
        the trace keypress, no raw stack ever landing
        unaccompanied (the shipped example book - six
        errors at the M-182 slice boundary, with its
        two views and its one pinned panel - when none
        is held yet); ``/errors error <error-id>``
        shows one error whole, told plainly;
        ``/errors trace <error-id>`` unfolds one
        error's folded trace whole; ``/errors view
        <view-id>`` shows one held view record;
        ``/errors kind <kind>`` shows the book's
        errors of one kind; ``/errors panel`` shows
        the panel derived from the whole book under
        its default view; ``/errors verdict`` shows
        the verdict derived for the whole book.
        Reading registers and publishes nothing as
        session news: errors and views are held only
        when they are given through the agent's
        register roads, stood on the book on the
        viewing road, or held on the book roads, and
        every error held for the session is journaled
        as an error_kindness_error session event,
        every view as an error_kindness_view session
        event, every derived panel as an
        error_kindness_panel session event and every
        derived verdict as an error_kindness_verdict
        session event. This surface fixes nothing and
        sends nothing - telling and unfolding are
        words only.
        """
        from ..core.error_kindness import (
            format_book,
            format_error,
            format_panel,
            format_verdict,
            format_view,
            parse_error_kindness_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_error_kindness_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "error":
                text = format_error(
                    primary.get_kindness_error(target))
            elif action == "trace":
                text = primary.trace_error_kindness_error(
                    target)["text"]
            elif action == "view":
                text = format_view(
                    primary.get_kindness_view(target))
            elif action == "kind":
                text = format_book(
                    primary.error_kindness_book(), target)
            elif action == "panel":
                text = format_panel(primary.error_kindness_book())
            elif action == "verdict":
                text = format_verdict(primary.error_kindness_book())
            else:
                text = primary.error_kindness_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_onboard(self, args: str):
        """M-184: /onboard - onboarding in five minutes.

        ``/onboard`` shows the onboarding book held
        this session - the first run held as data:
        providers detected by named probes, found or
        absent and never faked, Kista key-keeping
        offered as data with its answer, and one tiny
        real task walked in held steps under the
        ordering rule, success before configuration,
        always (the shipped example book - six
        detections at the M-183 slice boundary, with
        its two views, five walk steps, one offer and
        its one pinned panel - when none is held
        yet); ``/onboard detection <detection-id>``
        shows one detection whole; ``/onboard walk``
        shows the walk in held order with its offers;
        ``/onboard offer <offer-id>`` shows one Kista
        offer with its answer; ``/onboard view
        <view-id>`` shows one held view record;
        ``/onboard outcome <outcome>`` shows the
        book's detections of one outcome; ``/onboard
        panel`` shows the panel derived from the
        whole book under its default view; ``/onboard
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: detections and views
        are held only when they are given through the
        agent's register roads, stood on the book on
        the viewing road, or held on the book roads,
        and every detection held for the session is
        journaled as an onboarding_detection session
        event, every view as an onboarding_view
        session event, every derived panel as an
        onboarding_panel session event and every
        derived verdict as an onboarding_verdict
        session event. This surface detects nothing
        live, keeps no key, runs no task and
        configures nothing - holding and telling are
        words only.
        """
        from ..core.onboarding_five import (
            format_book,
            format_detection,
            format_offer,
            format_panel,
            format_verdict,
            format_view,
            format_walk,
            parse_onboarding_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_onboarding_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "detection":
                text = format_detection(
                    primary.get_onboarding_detection(target))
            elif action == "walk":
                text = format_walk(primary.onboarding_five_book())
            elif action == "offer":
                text = format_offer(
                    primary.get_onboarding_offer(target))
            elif action == "view":
                text = format_view(
                    primary.get_onboarding_view(target))
            elif action == "outcome":
                text = format_book(
                    primary.onboarding_five_book(), target)
            elif action == "panel":
                text = format_panel(primary.onboarding_five_book())
            elif action == "verdict":
                text = format_verdict(primary.onboarding_five_book())
            else:
                text = primary.onboarding_five_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_lessons(self, args: str):
        """M-185: /lessons - the tutorial grown.

        ``/lessons`` shows the tutorial book held
        this session - the grown tutorial held as
        data: interactive lessons per feature family,
        ready or blocked and never faked, the scratch
        repo a lesson runs inside held as data, and
        the play in held steps under the scratch-repo
        rule - lessons run inside a scratch repo,
        never against the real workspace (the shipped
        example book - six lessons at the M-184 slice
        boundary, with its two views, five play steps,
        one scratch and its one pinned panel - when
        none is held yet); ``/lessons lesson
        <lesson-id>`` shows one lesson whole;
        ``/lessons play`` shows the play in held order
        with its scratches; ``/lessons scratch
        <scratch-id>`` shows one scratch repo with its
        state; ``/lessons view <view-id>`` shows one
        held view record; ``/lessons readiness
        <readiness>`` shows the book's lessons of one
        readiness; ``/lessons panel`` shows the panel
        derived from the whole book under its default
        view; ``/lessons verdict`` shows the verdict
        derived for the whole book. Reading registers
        and publishes nothing as session news: lessons
        and views are held only when they are given
        through the agent's register roads, stood on
        the book on the viewing road, or held on the
        book roads, and every lesson held for the
        session is journaled as a tutorial_lesson
        session event, every view as a tutorial_view
        session event, every derived panel as a
        tutorial_panel session event and every derived
        verdict as a tutorial_verdict session event.
        This surface runs no lesson, opens no repo and
        writes nothing to any real workspace - holding
        and telling are words only.
        """
        from ..core.tutorial_grown import (
            format_book,
            format_lesson,
            format_scratch,
            format_panel,
            format_verdict,
            format_view,
            format_play,
            parse_tutorial_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_tutorial_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "lesson":
                text = format_lesson(
                    primary.get_tutorial_lesson(target))
            elif action == "play":
                text = format_play(primary.tutorial_grown_book())
            elif action == "scratch":
                text = format_scratch(
                    primary.get_tutorial_scratch(target))
            elif action == "view":
                text = format_view(
                    primary.get_tutorial_view(target))
            elif action == "readiness":
                text = format_book(
                    primary.tutorial_grown_book(), target)
            elif action == "panel":
                text = format_panel(primary.tutorial_grown_book())
            elif action == "verdict":
                text = format_verdict(primary.tutorial_grown_book())
            else:
                text = primary.tutorial_grown_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_helpask(self, args: str):
        """M-186: /helpask - help that answers.

        ``/helpask`` shows the help book held this
        session - help that answers, held as data:
        one help entry per screen and the local docs
        the question box answers from, held whole
        under their standings, current or stale (the
        shipped example book - six docs at the M-185
        slice boundary, with its two views, four
        screen helps and its one pinned panel - when
        none is held yet); ``/helpask doc <doc-id>``
        shows one local doc whole; ``/helpask ask
        <words>`` answers one question from the held
        docs alone - a question no current doc
        answers stands honestly unanswered;
        ``/helpask screen <screen>`` shows the held
        help for that screen, or names it uncovered;
        ``/helpask view <view-id>`` shows one held
        view record; ``/helpask standing <standing>``
        shows the book's docs of one standing;
        ``/helpask panel`` shows the panel derived
        from the whole book under its default view;
        ``/helpask verdict`` shows the verdict
        derived for the whole book; ``/helpask
        coverage`` shows which screens hold help.
        Reading registers and publishes nothing as
        session news: docs and views are held only
        when they are given through the agent's
        register roads, stood on the book on the
        viewing road, or held on the book roads, and
        every doc held for the session is journaled
        as a help_doc session event, every view as a
        help_view session event, every derived panel
        as a help_panel session event and every
        derived verdict as a help_verdict session
        event. This surface searches nothing live,
        calls no model and opens no network - holding
        and telling are words only.
        """
        from ..core.help_answers import (
            format_answer,
            format_book,
            format_coverage,
            format_doc,
            format_panel,
            format_screen,
            format_verdict,
            format_view,
            parse_help_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_help_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "doc":
                text = format_doc(primary.get_help_doc(target))
            elif action == "ask":
                text = format_answer(
                    primary.help_answers_book(), target)
            elif action == "screen":
                text = format_screen(
                    primary.help_answers_book(), target)
            elif action == "view":
                text = format_view(primary.get_help_view(target))
            elif action == "standing":
                text = format_book(
                    primary.help_answers_book(), target)
            elif action == "panel":
                text = format_panel(primary.help_answers_book())
            elif action == "verdict":
                text = format_verdict(primary.help_answers_book())
            elif action == "coverage":
                text = format_coverage(primary.help_answers_book())
            else:
                text = primary.help_answers_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_keymap(self, args: str):
        """M-187: /keymap - keyboard sovereignty.

        ``/keymap`` shows the keymap book held this
        session - keyboard sovereignty, held as data:
        one record per act with the key that reaches
        it and the vim-mode prompt option held as
        data beside them (the shipped example book -
        six acts at the M-186 slice boundary, with
        its two views, two mode records and its one
        pinned panel - when none is held yet);
        ``/keymap act <act-id>`` shows one act whole;
        ``/keymap key <key>`` shows the act one key
        reaches, or names the key unheld;
        ``/keymap area <area>`` shows the book's acts
        of one area; ``/keymap view <view-id>`` shows
        one held view record; ``/keymap mode
        <mode-id>`` shows one held mode record;
        ``/keymap print`` prints the keymap derived
        from the whole book's held acts; ``/keymap
        panel`` shows the panel derived from the
        whole book under its default view; ``/keymap
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: acts and views are
        held only when they are given through the
        agent's register roads, stood on the book on
        the viewing road, or held on the book roads,
        and every act held for the session is
        journaled as a keyboard_act session event,
        every view as a keyboard_view session event,
        every derived panel as a keyboard_panel
        session event and every derived verdict as a
        keyboard_verdict session event. This surface
        presses no keys, renders no live UI and
        changes no prompt mode - holding and telling
        are words only.
        """
        from ..core.keyboard_sovereignty import (
            format_act,
            format_book,
            format_key,
            format_keymap,
            format_mode,
            format_panel,
            format_verdict,
            format_view,
            parse_keyboard_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_keyboard_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "act":
                text = format_act(primary.get_keyboard_act(target))
            elif action == "key":
                text = format_key(
                    primary.keyboard_sovereignty_book(), target)
            elif action == "area":
                text = format_book(
                    primary.keyboard_sovereignty_book(), target)
            elif action == "view":
                text = format_view(primary.get_keyboard_view(target))
            elif action == "mode":
                text = format_mode(
                    primary.keyboard_sovereignty_book().mode_for(target))
            elif action == "print":
                text = format_keymap(primary.keyboard_sovereignty_book())
            elif action == "panel":
                text = format_panel(primary.keyboard_sovereignty_book())
            elif action == "verdict":
                text = format_verdict(primary.keyboard_sovereignty_book())
            else:
                text = primary.keyboard_sovereignty_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_mouse(self, args: str):
        """M-188: /mouse - mouse manners.

        ``/mouse`` shows the mouse book held this
        session - mouse manners, held as data:
        one record per gesture with the road that reaches
        it and the file links held as
        data beside them (the shipped example book -
        six gestures at the M-187 slice boundary, with
        its two views, two link records and its one
        pinned panel - when none is held yet);
        ``/mouse gesture <gesture-id>`` shows one gesture whole;
        ``/mouse road <road>`` shows the gesture one road
        reaches, or names the road unheld;
        ``/mouse area <area>`` shows the book's gestures
        of one area; ``/mouse view <view-id>`` shows
        one held view record; ``/mouse link
        <link-id>`` shows one held link record;
        ``/mouse guide`` shows the guide derived
        from the whole book's held gestures; ``/mouse
        panel`` shows the panel derived from the
        whole book under its default view; ``/mouse
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: gestures and views are
        held only when they are given through the
        agent's register roads, stood on the book on
        the viewing road, or held on the book roads,
        and every gesture held for the session is
        journaled as a mouse_gesture session event,
        every view as a mouse_view session event,
        every derived panel as a mouse_panel
        session event and every derived verdict as a
        mouse_verdict session event. This surface
        moves no pointer, renders no live UI and
        opens no file - holding and telling
        are words only.
        """
        from ..core.mouse_manners import (
            format_gesture,
            format_book,
            format_road,
            format_guide,
            format_link,
            format_panel,
            format_verdict,
            format_view,
            parse_mouse_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_mouse_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "gesture":
                text = format_gesture(primary.get_mouse_gesture(target))
            elif action == "road":
                text = format_road(
                    primary.mouse_manners_book(), target)
            elif action == "area":
                text = format_book(
                    primary.mouse_manners_book(), target)
            elif action == "view":
                text = format_view(primary.get_mouse_view(target))
            elif action == "link":
                text = format_link(
                    primary.mouse_manners_book().link_for(target))
            elif action == "guide":
                text = format_guide(primary.mouse_manners_book())
            elif action == "panel":
                text = format_panel(primary.mouse_manners_book())
            elif action == "verdict":
                text = format_verdict(primary.mouse_manners_book())
            else:
                text = primary.mouse_manners_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_gallery(self, args: str):
        """M-189: /gallery - session gallery.

        ``/gallery`` shows the gallery book held this
        session - session gallery, held as data:
        one record per card with the road that reaches
        it and the file actions held as
        data beside them (the shipped example book -
        six cards at the M-188 slice boundary, with
        its two views, two action records and its one
        pinned panel - when none is held yet);
        ``/gallery card <card-id>`` shows one card whole;
        ``/gallery road <road>`` shows the card one road
        reaches, or names the road unheld;
        ``/gallery outcome <outcome>`` shows the book's cards
        of one outcome; ``/gallery view <view-id>`` shows
        one held view record; ``/gallery action
        <action-id>`` shows one held action record;
        ``/gallery index`` shows the index derived
        from the whole book's held cards; ``/gallery
        panel`` shows the panel derived from the
        whole book under its default view; ``/gallery
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: cards and views are
        held only when they are given through the
        agent's register roads, stood on the book on
        the viewing road, or held on the book roads,
        and every card held for the session is
        journaled as a gallery_card session event,
        every view as a gallery_view session event,
        every derived panel as a gallery_panel
        session event and every derived verdict as a
        gallery_verdict session event. This surface
        moves no pointer, renders no live UI and
        opens no file - holding and telling
        are words only.
        """
        from ..core.session_gallery import (
            format_card,
            format_book,
            format_road,
            format_index,
            format_action,
            format_panel,
            format_verdict,
            format_view,
            parse_gallery_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            action, target = parse_gallery_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if action == "card":
                text = format_card(primary.get_gallery_card(target))
            elif action == "road":
                text = format_road(
                    primary.session_gallery_book(), target)
            elif action == "outcome":
                text = format_book(
                    primary.session_gallery_book(), target)
            elif action == "view":
                text = format_view(primary.get_gallery_view(target))
            elif action == "action":
                text = format_action(
                    primary.session_gallery_book().action_for(target))
            elif action == "index":
                text = format_index(primary.session_gallery_book())
            elif action == "panel":
                text = format_panel(primary.session_gallery_book())
            elif action == "verdict":
                text = format_verdict(primary.session_gallery_book())
            else:
                text = primary.session_gallery_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_costs(self, args: str):
        """M-190: /costs - costs face.

        ``/costs`` shows the costs book held this
        session - costs face, held as data:
        one record per line with the budget that reaches
        it and the file warnings held as
        data beside them (the shipped example book -
        six lines at the M-189 slice boundary, with
        its two views, two warning records and its one
        pinned panel - when none is held yet);
        ``/costs line <line-id>`` shows one line whole;
        ``/costs budget <budget>`` shows the line one budget
        reaches, or names the budget unheld;
        ``/costs scope <scope>`` shows the book's lines
        of one scope; ``/costs view <view-id>`` shows
        one held view record; ``/costs warning
        <warning-id>`` shows one held warning record;
        ``/costs index`` shows the index derived
        from the whole book's held lines; ``/costs
        panel`` shows the panel derived from the
        whole book under its default view; ``/costs
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: lines and views are
        held only when they are given through the
        agent's register budgets, stood on the book on
        the viewing budget, or held on the book budgets,
        and every line held for the session is
        journaled as a costs_line session event,
        every view as a costs_view session event,
        every derived panel as a costs_panel
        session event and every derived verdict as a
        costs_verdict session event. This surface
        moves no pointer, renders no live UI and
        opens no file - holding and telling
        are words only.
        """
        from ..core.costs_face import (
            format_line,
            format_book,
            format_budget,
            format_index,
            format_warning,
            format_panel,
            format_verdict,
            format_view,
            parse_costs_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            warning, target = parse_costs_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if warning == "line":
                text = format_line(primary.get_costs_line(target))
            elif warning == "budget":
                text = format_budget(
                    primary.costs_face_book(), target)
            elif warning == "scope":
                text = format_book(
                    primary.costs_face_book(), target)
            elif warning == "view":
                text = format_view(primary.get_costs_view(target))
            elif warning == "warning":
                text = format_warning(
                    primary.costs_face_book().warning_for(target))
            elif warning == "index":
                text = format_index(primary.costs_face_book())
            elif warning == "panel":
                text = format_panel(primary.costs_face_book())
            elif warning == "verdict":
                text = format_verdict(primary.costs_face_book())
            else:
                text = primary.costs_face_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")



    def _handle_theatre(self, args: str):
        """M-191: /theatre - session theatre.

        ``/theatre`` shows the theatre book held this
        session - session theatre, held as data:
        one record per hunk with the target that reaches
        it and the file comments held as
        data beside them (the shipped example book -
        six hunks at the M-190 slice boundary, with
        its two views, two stance records and its one
        pinned panel - when none is held yet);
        ``/theatre hunk <hunk-id>`` shows one hunk whole;
        ``/theatre target <target>`` shows the hunk one target
        reaches, or names the target unheld;
        ``/theatre kind <kind>`` shows the book's hunks
        of one kind; ``/theatre view <view-id>`` shows
        one held view record; ``/theatre stance
        <stance-id>`` shows one held stance record;
        ``/theatre index`` shows the index derived
        from the whole book's held hunks; ``/theatre
        panel`` shows the panel derived from the
        whole book under its default view; ``/theatre
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: hunks and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every hunk held for the session is
        journaled as a theatre_hunk session event,
        every view as a theatre_view session event,
        every derived panel as a theatre_panel
        session event and every derived verdict as a
        theatre_verdict session event. This surface
        moves no pointer, renders no live UI and
        opens no file - holding and telling
        are words only.
        """
        from ..core.diff_theatre_final import (
            format_hunk,
            format_book,
            format_target,
            format_index,
            format_comment,
            format_panel,
            format_verdict,
            format_view,
            parse_theatre_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_theatre_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "hunk":
                text = format_hunk(primary.get_theatre_hunk(target))
            elif stance == "target":
                text = format_target(
                    primary.diff_theatre_final_book(), target)
            elif stance == "kind":
                text = format_book(
                    primary.diff_theatre_final_book(), target)
            elif stance == "view":
                text = format_view(primary.get_theatre_view(target))
            elif stance == "comment":
                text = format_comment(
                    primary.diff_theatre_final_book().comment_for(target))
            elif stance == "index":
                text = format_index(primary.diff_theatre_final_book())
            elif stance == "panel":
                text = format_panel(primary.diff_theatre_final_book())
            elif stance == "verdict":
                text = format_verdict(primary.diff_theatre_final_book())
            else:
                text = primary.diff_theatre_final_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")
    def _handle_pane(self, args: str):
        """M-192: /panes - session pane.

        ``/pane`` shows the pane book held this
        session - session pane, held as data:
        one record per pane with the target that reaches
        it and the file notes held as
        data beside them (the shipped example book -
        six panes at the M-191 slice boundary, with
        its two layouts, two stance records and its one
        pinned panel - when none is held yet);
        ``/panes pane <pane-id>`` shows one pane whole;
        ``/panes target <target>`` shows the pane one target
        reaches, or names the target unheld;
        ``/panes kind <kind>`` shows the book's panes
        of one kind; ``/panes layout <layout-id>`` shows
        one held layout record; ``/panes stance
        <stance-id>`` shows one held stance record;
        ``/panes index`` shows the index derived
        from the whole book's held panes; ``/pane
        panel`` shows the panel derived from the
        whole book under its default layout; ``/pane
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: panes and layouts are
        held only when they are given through the
        agent's register targets, stood on the book on
        the layouting target, or held on the book targets,
        and every pane held for the session is
        journaled as a pane_pane session event,
        every layout as a pane_layout session event,
        every derived panel as a pane_panel
        session event and every derived verdict as a
        pane_verdict session event. This surface
        moves no pointer, renders no live UI and
        opens no file - holding and telling
        are words only.
        """
        from ..core.multi_pane import (
            format_pane,
            format_book,
            format_target,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_layout,
            parse_pane_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_pane_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "pane":
                text = format_pane(primary.get_pane_pane(target))
            elif stance == "target":
                text = format_target(
                    primary.multi_pane_book(), target)
            elif stance == "kind":
                text = format_book(
                    primary.multi_pane_book(), target)
            elif stance == "layout":
                text = format_layout(primary.get_pane_layout(target))
            elif stance == "note":
                text = format_note(
                    primary.multi_pane_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.multi_pane_book())
            elif stance == "panel":
                text = format_panel(primary.multi_pane_book())
            elif stance == "verdict":
                text = format_verdict(primary.multi_pane_book())
            else:
                text = primary.multi_pane_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_ceremony(self, args: str):
        """M-193: /ceremony - session moment.

        ``/ceremony`` shows the moment book held this
        session - session moment, held as data:
        one record per moment with the target that reaches
        it and the file notes held as
        data beside them (the shipped example book -
        six moments at the M-192 slice boundary, with
        its two views, two stance records and its one
        pinned panel - when none is held yet);
        ``/ceremony moment <moment-id>`` shows one moment whole;
        ``/ceremony target <target>`` shows the moment one target
        reaches, or names the target unheld;
        ``/ceremony kind <kind>`` shows the book's moments
        of one kind; ``/ceremony view <view-id>`` shows
        one held view record; ``/ceremony stance
        <stance-id>`` shows one held stance record;
        ``/ceremony index`` shows the index derived
        from the whole book's held moments; ``/ceremony
        panel`` shows the panel derived from the
        whole book under its default view; ``/ceremony
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: moments and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every moment held for the session is
        journaled as a ceremony_moment session event,
        every view as a ceremony_view session event,
        every derived panel as a ceremony_panel
        session event and every derived verdict as a
        ceremony_verdict session event. This surface
        moves no pointer, renders no live UI and
        opens no file - holding and telling
        are words only.
        """
        from ..core.splash_ceremony import (
            format_moment,
            format_book,
            format_alternative,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_ceremony_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_ceremony_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "moment":
                text = format_moment(primary.get_ceremony_moment(target))
            elif stance == "alternative":
                text = format_alternative(
                    primary.splash_ceremony_book(), target)
            elif stance == "kind":
                text = format_book(
                    primary.splash_ceremony_book(), target)
            elif stance == "view":
                text = format_view(primary.get_ceremony_view(target))
            elif stance == "note":
                text = format_note(
                    primary.splash_ceremony_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.splash_ceremony_book())
            elif stance == "panel":
                text = format_panel(primary.splash_ceremony_book())
            elif stance == "verdict":
                text = format_verdict(primary.splash_ceremony_book())
            else:
                text = primary.splash_ceremony_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_smallterminal(self, args: str):
        """M-194: /smallterminal - session fold.

        ``/smallterminal`` shows the fold book held this
        session - session fold, held as data:
        one record per fold with the target that reaches
        it and the file notes held as
        data beside them (the shipped example book -
        six folds at the M-193 slice boundary, with
        its two views, two stance records and its one
        pinned panel - when none is held yet);
        ``/smallterminal fold <fold-id>`` shows one fold whole;
        ``/smallterminal preserves <preserves>`` shows the fold one target
        reaches, or names the target unheld;
        ``/smallterminal kind <kind>`` shows the book's folds
        of one kind; ``/smallterminal view <view-id>`` shows
        one held view record; ``/smallterminal note
        <note-id>`` shows one held stance record;
        ``/smallterminal index`` shows the index derived
        from the whole book's held folds; ``/smallterminal
        panel`` shows the panel derived from the
        whole book under its default view; ``/smallterminal
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: folds and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every fold held for the session is
        journaled as a grace_fold session event,
        every view as a grace_view session event,
        every derived panel as a grace_panel
        session event and every derived verdict as a
        grace_verdict session event. This surface
        moves no pointer, renders no live UI and
        opens no file - holding and telling
        are words only.
        """
        from ..core.small_terminal_grace import (
            format_fold,
            format_book,
            format_preserves,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_grace_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_grace_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "fold":
                text = format_fold(primary.get_grace_fold(target))
            elif stance == "preserves":
                text = format_preserves(
                    primary.small_terminal_grace_book(), target)
            elif stance == "kind":
                text = format_book(
                    primary.small_terminal_grace_book(), target)
            elif stance == "view":
                text = format_view(primary.get_grace_view(target))
            elif stance == "note":
                text = format_note(
                    primary.small_terminal_grace_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.small_terminal_grace_book())
            elif stance == "panel":
                text = format_panel(primary.small_terminal_grace_book())
            elif stance == "verdict":
                text = format_verdict(primary.small_terminal_grace_book())
            else:
                text = primary.small_terminal_grace_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_copyshare(self, args: str):
        """M-195: /copyshare - session clip.

        ``/copyshare`` shows the clip book held this
        session - session clip, held as data:
        one record per clip with the target that reaches
        it and the file notes held as
        data beside them (the shipped example book -
        six clips at the M-194 slice boundary, with
        its two views, two stance records and its one
        pinned panel - when none is held yet);
        ``/copyshare clip <clip-id>`` shows one clip whole;
        ``/copyshare markdown <markdown>`` shows the clip one target
        reaches, or names the target unheld;
        ``/copyshare kind <kind>`` shows the book's clips
        of one kind; ``/copyshare view <view-id>`` shows
        one held view record; ``/copyshare note
        <note-id>`` shows one held stance record;
        ``/copyshare index`` shows the index derived
        from the whole book's held clips; ``/copyshare
        panel`` shows the panel derived from the
        whole book under its default view; ``/copyshare
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: clips and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every clip held for the session is
        journaled as a share_clip session event,
        every view as a share_view session event,
        every derived panel as a share_panel
        session event and every derived verdict as a
        share_verdict session event. This heading
        moves no pointer, renders no live UI and
        opens no file - holding and telling
        are words only.
        """
        from ..core.copy_share import (
            format_clip,
            format_book,
            format_markdown,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_share_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_share_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "clip":
                text = format_clip(primary.get_share_clip(target))
            elif stance == "markdown":
                text = format_markdown(
                    primary.copy_share_book(), target)
            elif stance == "kind":
                text = format_book(
                    primary.copy_share_book(), target)
            elif stance == "view":
                text = format_view(primary.get_share_view(target))
            elif stance == "note":
                text = format_note(
                    primary.copy_share_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.copy_share_book())
            elif stance == "panel":
                text = format_panel(primary.copy_share_book())
            elif stance == "verdict":
                text = format_verdict(primary.copy_share_book())
            else:
                text = primary.copy_share_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_settingsroom(self, args: str):
        """M-196: /settingsroom - the settings room.

        ``/settingsroom`` shows the settings book held this
        session - the settings room, held as data:
        one record per setting with the meaning that reaches
        it and the notes held as
        data beside them (the shipped example book -
        six settings at the M-195 slice boundary, with
        its two views, two stance records and its one
        pinned panel - when none is held yet);
        ``/settingsroom setting <setting-id>`` shows one setting whole;
        ``/settingsroom meaning <meaning>`` shows the setting one meaning
        reaches, or names the meaning unheld;
        ``/settingsroom section <section>`` shows the book's settings
        of one section; ``/settingsroom view <view-id>`` shows
        one held view record; ``/settingsroom note
        <note-id>`` shows one held stance record;
        ``/settingsroom index`` shows the index derived
        from the whole book's held settings; ``/settingsroom
        panel`` shows the panel derived from the
        whole book under its default view; ``/settingsroom
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: settings and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every setting held for the session is
        journaled as a room_setting session event,
        every view as a room_view session event,
        every derived panel as a room_panel
        session event and every derived verdict as a
        room_verdict session event. This heading
        changes no setting, applies nothing and
        writes no config - holding and telling
        are words only.
        """
        from ..core.settings_room import (
            format_setting,
            format_book,
            format_meaning,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_room_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_room_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "setting":
                text = format_setting(primary.get_room_setting(target))
            elif stance == "meaning":
                text = format_meaning(
                    primary.settings_room_book(), target)
            elif stance == "section":
                text = format_book(
                    primary.settings_room_book(), target)
            elif stance == "view":
                text = format_view(primary.get_room_view(target))
            elif stance == "note":
                text = format_note(
                    primary.settings_room_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.settings_room_book())
            elif stance == "panel":
                text = format_panel(primary.settings_room_book())
            elif stance == "verdict":
                text = format_verdict(primary.settings_room_book())
            else:
                text = primary.settings_room_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_commandpalette(self, args: str):
        """M-197: /commandpalette - the command palette.

        ``/commandpalette`` shows the palette book held this
        session - the command palette, held as data:
        one record per entry with the words that reach
        it and the notes held as
        data beside them (the shipped example book -
        six entries at the M-196 slice boundary, with
        its two views, two stance records and its one
        pinned panel - when none is held yet);
        ``/commandpalette entry <entry-id>`` shows one entry whole;
        ``/commandpalette keywords <keywords>`` shows the entry one set of words
        reaches, or names the words unheld;
        ``/commandpalette kind <kind>`` shows the book's entries
        of one kind; ``/commandpalette view <view-id>`` shows
        one held view record; ``/commandpalette note
        <note-id>`` shows one held stance record;
        ``/commandpalette index`` shows the index derived
        from the whole book's held entries; ``/commandpalette
        panel`` shows the panel derived from the
        whole book under its default view; ``/commandpalette
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: entries and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every entry held for the session is
        journaled as a palette_entry session event,
        every view as a palette_view session event,
        every derived panel as a palette_panel
        session event and every derived verdict as a
        palette_verdict session event. This heading
        executes no command, runs no action and
        navigates nowhere - holding and telling
        are words only.
        """
        from ..core.command_palette import (
            format_entry,
            format_book,
            format_keywords,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_palette_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_palette_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "entry":
                text = format_entry(primary.get_palette_entry(target))
            elif stance == "keywords":
                text = format_keywords(
                    primary.command_palette_book(), target)
            elif stance == "kind":
                text = format_book(
                    primary.command_palette_book(), target)
            elif stance == "view":
                text = format_view(primary.get_palette_view(target))
            elif stance == "note":
                text = format_note(
                    primary.command_palette_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.command_palette_book())
            elif stance == "panel":
                text = format_panel(primary.command_palette_book())
            elif stance == "verdict":
                text = format_verdict(primary.command_palette_book())
            else:
                text = primary.command_palette_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_uiundo(self, args: str):
        """M-198: /uiundo - the command undo.

        ``/uiundo`` shows the undo book held this
        session - the command undo, held as data:
        one record per pane with the words that reach
        it and the notes held as
        data beside them (the shipped example book -
        six panes at the M-197 slice boundary, with
        its two views, two stance records and its one
        pinned panel - when none is held yet);
        ``/uiundo pane <pane-id>`` shows one pane whole;
        ``/uiundo state <state>`` shows the pane one set of words
        reaches, or names the words unheld;
        ``/uiundo kind <kind>`` shows the book's panes
        of one kind; ``/uiundo view <view-id>`` shows
        one held view record; ``/uiundo note
        <note-id>`` shows one held stance record;
        ``/uiundo index`` shows the index derived
        from the whole book's held panes; ``/uiundo
        panel`` shows the panel derived from the
        whole book under its default view; ``/uiundo
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: panes and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every pane held for the session is
        journaled as a undo_pane session event,
        every view as a undo_view session event,
        every derived panel as a undo_panel
        session event and every derived verdict as a
        undo_verdict session event. This heading
        executes no command, runs no action and
        navigates nowhere - holding and telling
        are words only.
        """
        from ..core.ui_undo import (
            format_pane,
            format_book,
            format_state,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_undo_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_undo_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "pane":
                text = format_pane(primary.get_undo_pane(target))
            elif stance == "state":
                text = format_state(
                    primary.ui_undo_book(), target)
            elif stance == "kind":
                text = format_book(
                    primary.ui_undo_book(), target)
            elif stance == "view":
                text = format_view(primary.get_undo_view(target))
            elif stance == "note":
                text = format_note(
                    primary.ui_undo_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.ui_undo_book())
            elif stance == "panel":
                text = format_panel(primary.ui_undo_book())
            elif stance == "verdict":
                text = format_verdict(primary.ui_undo_book())
            else:
                text = primary.ui_undo_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")




    def _handle_accessverify(self, args: str):
        """M-199: /accessverify - the accessibility verification.

        ``/accessverify`` shows the verification book held this
        session - the accessibility verification, held as data:
        one record per gate with the words that reach
        it and the notes held as
        data beside them (the shipped example book -
        six gates at the M-198 slice boundary, with
        its two views, two stance records and its one
        pinned panel - when none is held yet);
        ``/accessverify gate <gate-id>`` shows one gate whole;
        ``/accessverify evidence <evidence>`` shows the gate one set of words
        reaches, or names the words unheld;
        ``/accessverify kind <kind>`` shows the book's gates
        of one kind; ``/accessverify view <view-id>`` shows
        one held view record; ``/accessverify note
        <note-id>`` shows one held stance record;
        ``/accessverify index`` shows the index derived
        from the whole book's held gates; ``/accessverify
        panel`` shows the panel derived from the
        whole book under its default view; ``/accessverify
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: gates and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every gate held for the session is
        journaled as a verify_gate session event,
        every view as a verify_view session event,
        every derived panel as a verify_panel
        session event and every derived verdict as a
        verify_verdict session event. This heading
        executes no command, runs no action and
        navigates nowhere - holding and telling
        are words only.
        """
        from ..core.accessibility_verification import (
            format_gate,
            format_book,
            format_evidence,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_verify_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_verify_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "gate":
                text = format_gate(primary.get_verify_gate(target))
            elif stance == "evidence":
                text = format_evidence(
                    primary.access_verify_book(), target)
            elif stance == "kind":
                text = format_book(
                    primary.access_verify_book(), target)
            elif stance == "view":
                text = format_view(primary.get_verify_view(target))
            elif stance == "note":
                text = format_note(
                    primary.access_verify_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.access_verify_book())
            elif stance == "panel":
                text = format_panel(primary.access_verify_book())
            elif stance == "verdict":
                text = format_verdict(primary.access_verify_book())
            else:
                text = primary.access_verify_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")



    def _handle_campaigns(self, args: str):
        """M-201: /campaigns - campaigns as data.

        ``/campaigns`` shows the campaign book held this
        session - campaigns as data: one record per slice,
        held whole with its title, the part it stands in,
        its state, its evidence held honestly and the
        acceptance checks it carries, and the notes held
        as data beside them (the shipped example book -
        six slices at the M-200 slice boundary, with its
        two views, two stance records and its one pinned
        panel - when none is held yet);
        ``/campaigns slice <slice-id>`` shows one slice whole;
        ``/campaigns checks <checks>`` shows the slice one
        checks line reaches, or names the checks unheld;
        ``/campaigns state <state>`` shows the book's slices
        of one state; ``/campaigns view <view-id>`` shows
        one held view record; ``/campaigns note
        <note-id>`` shows one held stance record;
        ``/campaigns index`` shows the index derived
        from the whole book's held slices; ``/campaigns
        panel`` shows the panel derived from the
        whole book under its default view; ``/campaigns
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: slices and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every slice held for the session is
        journaled as a campaign_slice session event,
        every view as a campaign_view session event,
        every derived panel as a campaign_panel
        session event and every derived verdict as a
        campaign_verdict session event. This heading
        executes no campaign, runs nothing and banks
        nothing - holding and telling are words only.
        """
        from ..core.campaigns import (
            format_slice,
            format_book,
            format_checks,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_campaign_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_campaign_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "slice":
                text = format_slice(primary.get_campaign_slice(target))
            elif stance == "checks":
                text = format_checks(
                    primary.campaigns_book(), target)
            elif stance == "state":
                text = format_book(
                    primary.campaigns_book(), target)
            elif stance == "view":
                text = format_view(primary.get_campaign_view(target))
            elif stance == "note":
                text = format_note(
                    primary.campaigns_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.campaigns_book())
            elif stance == "panel":
                text = format_panel(primary.campaigns_book())
            elif stance == "verdict":
                text = format_verdict(primary.campaigns_book())
            else:
                text = primary.campaigns_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")



    def _handle_intent(self, args: str):
        """M-202: /intent - intent as data.

        ``/intent`` shows the intent book held this
        session - intent as data: one record per slice,
        held whole with its title, the part it stands in,
        its state, its evidence held honestly and the
        acceptance checks it carries, and the notes held
        as data beside them (the shipped example book -
        six slices at the M-200 slice boundary, with its
        two views, two stance records and its one pinned
        panel - when none is held yet);
        ``/intent slice <slice-id>`` shows one slice whole;
        ``/intent checks <checks>`` shows the slice one
        checks line reaches, or names the checks unheld;
        ``/intent state <state>`` shows the book's slices
        of one state; ``/intent view <view-id>`` shows
        one held view record; ``/intent note
        <note-id>`` shows one held stance record;
        ``/intent index`` shows the index derived
        from the whole book's held slices; ``/intent
        panel`` shows the panel derived from the
        whole book under its default view; ``/intent
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: slices and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every slice held for the session is
        journaled as a intent_slice session event,
        every view as a intent_view session event,
        every derived panel as a intent_panel
        session event and every derived verdict as a
        intent_verdict session event. This heading
        executes no intent, runs nothing and banks
        nothing - holding and telling are words only.
        """
        from ..core.intent_capture import (
            format_intent,
            format_book,
            format_citation,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_intent_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_intent_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "intent":
                text = format_intent(primary.get_intent(target))
            elif stance == "citation":
                text = format_citation(
                    primary.intent_book(), target)
            elif stance == "project":
                text = format_book(
                    primary.intent_book(), target)
            elif stance == "view":
                text = format_view(primary.get_intent_view(target))
            elif stance == "note":
                text = format_note(
                    primary.intent_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.intent_book())
            elif stance == "panel":
                text = format_panel(primary.intent_book())
            elif stance == "verdict":
                text = format_verdict(primary.intent_book())
            else:
                text = primary.intent_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")



    def _handle_slicing(self, args: str):
        """M-203: /slicing - the slicing engine as data.

        ``/slicing`` shows the slicing book held this
        session - draft slices as data: one record per
        draft, held whole with the approved intent it
        was drafted from, its one verifiable outcome
        at the house grain and its dependencies, and
        the notes held as data beside them (the shipped
        example book - five drafts at the M-202 slice
        boundary, with its three intent references, its
        two views, two stance records, one shape
        approval and its one pinned panel - when none
        is held yet); ``/slicing draft <draft-id>``
        shows one draft whole; ``/slicing outcome
        <outcome>`` shows the draft one outcome line
        reaches, or names the outcome unheld;
        ``/slicing intent <intent-id>`` shows the book's
        drafts of one intent; ``/slicing view <view-id>``
        shows one held view record; ``/slicing note
        <note-id>`` shows one held stance record;
        ``/slicing index`` shows the index derived
        from the whole book's held drafts; ``/slicing
        panel`` shows the panel derived from the
        whole book under its default view; ``/slicing
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: drafts and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every draft held for the session is
        journaled as a slicing_draft session event,
        every view as a slicing_view session event,
        every derived panel as a slicing_panel
        session event and every derived verdict as a
        slicing_verdict session event. This heading
        builds no slice, executes nothing and banks
        nothing - holding and telling are words only.
        """
        from ..core.slicing_engine import (
            format_draft,
            format_book,
            format_outcome,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_slicing_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_slicing_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "draft":
                text = format_draft(
                    primary.get_slicing_draft(target),
                    primary.slicing_book())
            elif stance == "outcome":
                text = format_outcome(
                    primary.slicing_book(), target)
            elif stance == "intent":
                text = format_book(
                    primary.slicing_book(), target)
            elif stance == "view":
                text = format_view(primary.get_slicing_view(target))
            elif stance == "note":
                text = format_note(
                    primary.slicing_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.slicing_book())
            elif stance == "panel":
                text = format_panel(primary.slicing_book())
            elif stance == "verdict":
                text = format_verdict(primary.slicing_book())
            else:
                text = primary.slicing_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")



    def _handle_juggernaut(self, args: str):
        """M-204: /juggernaut - the juggernaut engine as data.

        ``/juggernaut`` shows the juggernaut book held this
        session - run slices as data: one record per
        run, held whole with the active slice it
        was runed from, its one verifiable phase
        at the house grain and its questions, and
        the notes held as data beside them (the shipped
        example book - five runs at the M-202 slice
        boundary, with its three slice references, its
        two views, two stance records, one trace
        trace and its one pinned panel - when none
        is held yet); ``/juggernaut run <run-id>``
        shows one run whole; ``/juggernaut phase
        <phase>`` shows the run one phase line
        reaches, or names the phase unheld;
        ``/juggernaut slice <slice-id>`` shows the book's
        runs of one slice; ``/juggernaut view <view-id>``
        shows one held view record; ``/juggernaut note
        <note-id>`` shows one held stance record;
        ``/juggernaut index`` shows the index derived
        from the whole book's held runs; ``/juggernaut
        panel`` shows the panel derived from the
        whole book under its default view; ``/juggernaut
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: runs and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every run held for the session is
        journaled as a juggernaut_run session event,
        every view as a juggernaut_view session event,
        every derived panel as a juggernaut_panel
        session event and every derived verdict as a
        juggernaut_verdict session event. This heading
        builds no slice, executes nothing and banks
        nothing - holding and telling are words only.
        """
        from ..core.juggernaut_loop import (
            format_run,
            format_book,
            format_phase,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_juggernaut_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_juggernaut_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "run":
                text = format_run(
                    primary.get_juggernaut_run(target),
                    primary.juggernaut_book())
            elif stance == "phase":
                text = format_phase(
                    primary.juggernaut_book(), target)
            elif stance == "slice":
                text = format_book(
                    primary.juggernaut_book(), target)
            elif stance == "view":
                text = format_view(primary.get_juggernaut_view(target))
            elif stance == "note":
                text = format_note(
                    primary.juggernaut_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.juggernaut_book())
            elif stance == "panel":
                text = format_panel(primary.juggernaut_book())
            elif stance == "verdict":
                text = format_verdict(primary.juggernaut_book())
            else:
                text = primary.juggernaut_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_acceptance(self, args: str):
        """M-205: /acceptance - the acceptance engine as data.

        ``/acceptance`` shows the acceptance book held this
        session - audit slices as data: one record per
        audit, held whole with the active slice it
        was audited from, its one verifiable check
        at the house grain and its claims, and
        the notes held as data beside them (the shipped
        example book - five audits at the M-203 slice
        boundary, with its three slice references, its
        two views, two stance records, one trace
        trace and its one pinned panel - when none
        is held yet); ``/acceptance audit <audit-id>``
        shows one audit whole; ``/acceptance check
        <check>`` shows the audit one check line
        reaches, or names the check unheld;
        ``/acceptance slice <slice-id>`` shows the book's
        audits of one slice; ``/acceptance view <view-id>``
        shows one held view record; ``/acceptance note
        <note-id>`` shows one held stance record;
        ``/acceptance index`` shows the index derived
        from the whole book's held audits; ``/acceptance
        panel`` shows the panel derived from the
        whole book under its default view; ``/acceptance
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: audits and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every audit held for the session is
        journaled as a acceptance_audit session event,
        every view as a acceptance_view session event,
        every derived panel as a acceptance_panel
        session event and every derived verdict as a
        acceptance_verdict session event. This heading
        builds no slice, executes nothing and banks
        nothing - holding and telling are words only.
        """
        from ..core.acceptance_gates import (
            format_audit,
            format_book,
            format_check,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_acceptance_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_acceptance_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "audit":
                text = format_audit(
                    primary.get_acceptance_audit(target),
                    primary.acceptance_book())
            elif stance == "check":
                text = format_check(
                    primary.acceptance_book(), target)
            elif stance == "slice":
                text = format_book(
                    primary.acceptance_book(), target)
            elif stance == "view":
                text = format_view(primary.get_acceptance_view(target))
            elif stance == "note":
                text = format_note(
                    primary.acceptance_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.acceptance_book())
            elif stance == "panel":
                text = format_panel(primary.acceptance_book())
            elif stance == "verdict":
                text = format_verdict(primary.acceptance_book())
            else:
                text = primary.acceptance_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_banking(self, args: str):
        """M-206: /banking - the banking engine as data.

        ``/banking`` shows the banking book held this
        session - banking slices as data: one record per
        banking, held whole with the active slice it
        was bankinged from, its one verifiable check
        at the house grain and its claims, and
        the notes held as data beside them (the shipped
        example book - five bankings at the M-203 slice
        boundary, with its three slice references, its
        two views, two stance records, one trace
        trace and its one pinned panel - when none
        is held yet); ``/banking banking <banking-id>``
        shows one banking whole; ``/banking check
        <check>`` shows the banking one check line
        reaches, or names the check unheld;
        ``/banking slice <slice-id>`` shows the book's
        bankings of one slice; ``/banking view <view-id>``
        shows one held view record; ``/banking note
        <note-id>`` shows one held stance record;
        ``/banking index`` shows the index derived
        from the whole book's held bankings; ``/banking
        panel`` shows the panel derived from the
        whole book under its default view; ``/banking
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: bankings and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every banking held for the session is
        journaled as a banking_banking session event,
        every view as a banking_view session event,
        every derived panel as a banking_panel
        session event and every derived verdict as a
        banking_verdict session event. This heading
        builds no slice, executes nothing and banks
        nothing - holding and telling are words only.
        """
        from ..core.banking_discipline import (
            format_banking,
            format_book,
            format_check,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_banking_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_banking_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "banking":
                text = format_banking(
                    primary.get_banking_banking(target),
                    primary.banking_book())
            elif stance == "check":
                text = format_check(
                    primary.banking_book(), target)
            elif stance == "slice":
                text = format_book(
                    primary.banking_book(), target)
            elif stance == "view":
                text = format_view(primary.get_banking_view(target))
            elif stance == "note":
                text = format_note(
                    primary.banking_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.banking_book())
            elif stance == "panel":
                text = format_panel(primary.banking_book())
            elif stance == "verdict":
                text = format_verdict(primary.banking_book())
            else:
                text = primary.banking_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_keeping(self, args: str):
        """M-207: /keepruntime - the keeping engine as data.

        ``/keepruntime`` shows the keeping book held this
        session - keeping slices as data: one record per
        keeping, held whole with the active slice it
        was keepinged from, its one verifiable check
        at the house grain and its claims, and
        the notes held as data beside them (the shipped
        example book - five keepings at the M-203 slice
        boundary, with its three slice references, its
        two views, two stance records, one trace
        trace and its one pinned panel - when none
        is held yet); ``/keepruntime keeping <keeping-id>``
        shows one keeping whole; ``/keepruntime check
        <check>`` shows the keeping one check line
        reaches, or names the check unheld;
        ``/keepruntime slice <slice-id>`` shows the book's
        keepings of one slice; ``/keepruntime view <view-id>``
        shows one held view record; ``/keepruntime note
        <note-id>`` shows one held stance record;
        ``/keepruntime index`` shows the index derived
        from the whole book's held keepings; ``/keepruntime
        panel`` shows the panel derived from the
        whole book under its default view; ``/keepruntime
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: keepings and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every keeping held for the session is
        journaled as a keeping_keeping session event,
        every view as a keeping_view session event,
        every derived panel as a keeping_panel
        session event and every derived verdict as a
        keeping_verdict session event. This heading
        builds no slice, executes nothing and banks
        nothing - holding and telling are words only.
        """
        from ..core.keeper_runtime import (
            format_keeping,
            format_book,
            format_check,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_keeping_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_keeping_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "keeping":
                text = format_keeping(
                    primary.get_keeping_keeping(target),
                    primary.keeping_book())
            elif stance == "check":
                text = format_check(
                    primary.keeping_book(), target)
            elif stance == "slice":
                text = format_book(
                    primary.keeping_book(), target)
            elif stance == "view":
                text = format_view(primary.get_keeping_view(target))
            elif stance == "note":
                text = format_note(
                    primary.keeping_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.keeping_book())
            elif stance == "panel":
                text = format_panel(primary.keeping_book())
            elif stance == "verdict":
                text = format_verdict(primary.keeping_book())
            else:
                text = primary.keeping_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_pausing(self, args: str):
        """M-208: /pauselines - the pausing engine as data.

        ``/pauselines`` shows the pausing book held this
        session - pausing slices as data: one record per
        pausing, held whole with the active slice it
        was pausinged from, its one verifiable check
        at the house grain and its claims, and
        the notes held as data beside them (the shipped
        example book - five pausings at the M-203 slice
        boundary, with its three slice references, its
        two views, two stance records, one trace
        trace and its one pinned panel - when none
        is held yet); ``/pauselines pausing <pausing-id>``
        shows one pausing whole; ``/pauselines check
        <check>`` shows the pausing one check line
        reaches, or names the check unheld;
        ``/pauselines slice <slice-id>`` shows the book's
        pausings of one slice; ``/pauselines view <view-id>``
        shows one held view record; ``/pauselines note
        <note-id>`` shows one held stance record;
        ``/pauselines index`` shows the index derived
        from the whole book's held pausings; ``/pauselines
        panel`` shows the panel derived from the
        whole book under its default view; ``/pauselines
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: pausings and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every pausing held for the session is
        journaled as a pausing_pausing session event,
        every view as a pausing_view session event,
        every derived panel as a pausing_panel
        session event and every derived verdict as a
        pausing_verdict session event. This heading
        builds no slice, executes nothing and banks
        nothing - holding and telling are words only.
        """
        from ..core.pause_lines import (
            format_pausing,
            format_book,
            format_check,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_pausing_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_pausing_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "pausing":
                text = format_pausing(
                    primary.get_pausing_pausing(target),
                    primary.pausing_book())
            elif stance == "check":
                text = format_check(
                    primary.pausing_book(), target)
            elif stance == "slice":
                text = format_book(
                    primary.pausing_book(), target)
            elif stance == "view":
                text = format_view(primary.get_pausing_view(target))
            elif stance == "note":
                text = format_note(
                    primary.pausing_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.pausing_book())
            elif stance == "panel":
                text = format_panel(primary.pausing_book())
            elif stance == "verdict":
                text = format_verdict(primary.pausing_book())
            else:
                text = primary.pausing_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_questioning(self, args: str):
        """M-209: /questionlaw - the questioning engine as data.

        ``/questionlaw`` shows the questioning book held this
        session - questioning slices as data: one record per
        questioning, held whole with the active slice it
        was questioninged from, its one verifiable check
        at the house grain and its claims, and
        the notes held as data beside them (the shipped
        example book - five questionings at the M-203 slice
        boundary, with its three slice references, its
        two views, two stance records, one trace
        trace and its one pinned panel - when none
        is held yet); ``/questionlaw questioning <questioning-id>``
        shows one questioning whole; ``/questionlaw check
        <check>`` shows the questioning one check line
        reaches, or names the check unheld;
        ``/questionlaw slice <slice-id>`` shows the book's
        questionings of one slice; ``/questionlaw view <view-id>``
        shows one held view record; ``/questionlaw note
        <note-id>`` shows one held stance record;
        ``/questionlaw index`` shows the index derived
        from the whole book's held questionings; ``/questionlaw
        panel`` shows the panel derived from the
        whole book under its default view; ``/questionlaw
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: questionings and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every questioning held for the session is
        journaled as a questioning_questioning session event,
        every view as a questioning_view session event,
        every derived panel as a questioning_panel
        session event and every derived verdict as a
        questioning_verdict session event. This heading
        builds no slice, executes nothing and banks
        nothing - holding and telling are words only.
        """
        from ..core.question_law import (
            format_questioning,
            format_book,
            format_check,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_questioning_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_questioning_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "questioning":
                text = format_questioning(
                    primary.get_questioning_questioning(target),
                    primary.questioning_book())
            elif stance == "check":
                text = format_check(
                    primary.questioning_book(), target)
            elif stance == "slice":
                text = format_book(
                    primary.questioning_book(), target)
            elif stance == "view":
                text = format_view(primary.get_questioning_view(target))
            elif stance == "note":
                text = format_note(
                    primary.questioning_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.questioning_book())
            elif stance == "panel":
                text = format_panel(primary.questioning_book())
            elif stance == "verdict":
                text = format_verdict(primary.questioning_book())
            else:
                text = primary.questioning_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_sentry(self, args: str):
        """M-210: /scopesentry - the sentry engine as data.

        ``/scopesentry`` shows the sentry book held this
        session - sentry slices as data: one record per
        sentry, held whole with the active slice it
        was sentryed from, its one verifiable check
        at the house grain and its claims, and
        the notes held as data beside them (the shipped
        example book - five sentries at the M-203 slice
        boundary, with its three slice references, its
        two views, two stance records, one trace
        trace and its one pinned panel - when none
        is held yet); ``/scopesentry sentry <sentry-id>``
        shows one sentry whole; ``/scopesentry check
        <check>`` shows the sentry one check line
        reaches, or names the check unheld;
        ``/scopesentry slice <slice-id>`` shows the book's
        sentries of one slice; ``/scopesentry view <view-id>``
        shows one held view record; ``/scopesentry note
        <note-id>`` shows one held stance record;
        ``/scopesentry index`` shows the index derived
        from the whole book's held sentries; ``/scopesentry
        panel`` shows the panel derived from the
        whole book under its default view; ``/scopesentry
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: sentries and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every sentry held for the session is
        journaled as a sentry_sentry session event,
        every view as a sentry_view session event,
        every derived panel as a sentry_panel
        session event and every derived verdict as a
        sentry_verdict session event. This heading
        builds no slice, executes nothing and banks
        nothing - holding and telling are words only.
        """
        from ..core.scope_sentry import (
            format_sentry,
            format_book,
            format_check,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_sentry_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_sentry_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "sentry":
                text = format_sentry(
                    primary.get_sentry_sentry(target),
                    primary.sentry_book())
            elif stance == "check":
                text = format_check(
                    primary.sentry_book(), target)
            elif stance == "slice":
                text = format_book(
                    primary.sentry_book(), target)
            elif stance == "view":
                text = format_view(primary.get_sentry_view(target))
            elif stance == "note":
                text = format_note(
                    primary.sentry_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.sentry_book())
            elif stance == "panel":
                text = format_panel(primary.sentry_book())
            elif stance == "verdict":
                text = format_verdict(primary.sentry_book())
            else:
                text = primary.sentry_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_upkeep(self, args: str):
        """M-211: /mapupkeep - the upkeep engine as data.

        ``/mapupkeep`` shows the upkeep book held this
        session - upkeep slices as data: one record per
        upkeep, held whole with the active slice it
        was upkeeped from, its one verifiable check
        at the house grain and its claims, and
        the notes held as data beside them (the shipped
        example book - five upkeeps at the M-203 slice
        boundary, with its three slice references, its
        two views, two stance records, one trace
        trace and its one pinned panel - when none
        is held yet); ``/mapupkeep upkeep <upkeep-id>``
        shows one upkeep whole; ``/mapupkeep check
        <check>`` shows the upkeep one check line
        reaches, or names the check unheld;
        ``/mapupkeep slice <slice-id>`` shows the book's
        upkeeps of one slice; ``/mapupkeep view <view-id>``
        shows one held view record; ``/mapupkeep note
        <note-id>`` shows one held stance record;
        ``/mapupkeep index`` shows the index derived
        from the whole book's held upkeeps; ``/mapupkeep
        panel`` shows the panel derived from the
        whole book under its default view; ``/mapupkeep
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: upkeeps and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every upkeep held for the session is
        journaled as a upkeep_upkeep session event,
        every view as a upkeep_view session event,
        every derived panel as a upkeep_panel
        session event and every derived verdict as a
        upkeep_verdict session event. This heading
        builds no slice, executes nothing and banks
        nothing - holding and telling are words only.
        """
        from ..core.memory_map_upkeep import (
            format_upkeep,
            format_book,
            format_check,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_upkeep_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_upkeep_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "upkeep":
                text = format_upkeep(
                    primary.get_upkeep_upkeep(target),
                    primary.upkeep_book())
            elif stance == "check":
                text = format_check(
                    primary.upkeep_book(), target)
            elif stance == "slice":
                text = format_book(
                    primary.upkeep_book(), target)
            elif stance == "view":
                text = format_view(primary.get_upkeep_view(target))
            elif stance == "note":
                text = format_note(
                    primary.upkeep_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.upkeep_book())
            elif stance == "panel":
                text = format_panel(primary.upkeep_book())
            elif stance == "verdict":
                text = format_verdict(primary.upkeep_book())
            else:
                text = primary.upkeep_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_bug(self, args: str):
        """M-212: /bugrule - the bug engine as data.

        ``/bugrule`` shows the bug book held this
        session - bug slices as data: one record per
        bug, held whole with the active slice it
        was buged from, its one verifiable check
        at the house grain and its claims, and
        the notes held as data beside them (the shipped
        example book - five bugs at the M-203 slice
        boundary, with its three slice references, its
        two views, two stance records, one trace
        trace and its one pinned panel - when none
        is held yet); ``/bugrule bug <bug-id>``
        shows one bug whole; ``/bugrule check
        <check>`` shows the bug one check line
        reaches, or names the check unheld;
        ``/bugrule slice <slice-id>`` shows the book's
        bugs of one slice; ``/bugrule view <view-id>``
        shows one held view record; ``/bugrule note
        <note-id>`` shows one held stance record;
        ``/bugrule index`` shows the index derived
        from the whole book's held bugs; ``/bugrule
        panel`` shows the panel derived from the
        whole book under its default view; ``/bugrule
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: bugs and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every bug held for the session is
        journaled as a bug_bug session event,
        every view as a bug_view session event,
        every derived panel as a bug_panel
        session event and every derived verdict as a
        bug_verdict session event. This heading
        builds no slice, executes nothing and banks
        nothing - holding and telling are words only.
        """
        from ..core.bug_rule import (
            format_bug,
            format_book,
            format_check,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_bug_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_bug_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "bug":
                text = format_bug(
                    primary.get_bug_bug(target),
                    primary.bug_book())
            elif stance == "check":
                text = format_check(
                    primary.bug_book(), target)
            elif stance == "slice":
                text = format_book(
                    primary.bug_book(), target)
            elif stance == "view":
                text = format_view(primary.get_bug_view(target))
            elif stance == "note":
                text = format_note(
                    primary.bug_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.bug_book())
            elif stance == "panel":
                text = format_panel(primary.bug_book())
            elif stance == "verdict":
                text = format_verdict(primary.bug_book())
            else:
                text = primary.bug_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_retro(self, args: str):
        """M-213: /retrospectives - the retro engine as data.

        ``/retrospectives`` shows the retro book held this
        session - retro slices as data: one record per
        retro, held whole with the active slice it
        was held from, its one verifiable check
        at the house grain and its claims, and
        the notes held as data beside them (the shipped
        example book - five retros at the M-203 slice
        boundary, with its three slice references, its
        two views, two stance records, one trace
        trace and its one pinned panel - when none
        is held yet); ``/retrospectives retro <retro-id>``
        shows one retro whole; ``/retrospectives check
        <check>`` shows the retro one check line
        reaches, or names the check unheld;
        ``/retrospectives slice <slice-id>`` shows the book's
        retros of one slice; ``/retrospectives view <view-id>``
        shows one held view record; ``/retrospectives note
        <note-id>`` shows one held stance record;
        ``/retrospectives index`` shows the index derived
        from the whole book's held retros; ``/retrospectives
        panel`` shows the panel derived from the
        whole book under its default view; ``/retrospectives
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: retros and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every retro held for the session is
        journaled as a retro_retro session event,
        every view as a retro_view session event,
        every derived panel as a retro_panel
        session event and every derived verdict as a
        retro_verdict session event. This heading
        builds no slice, executes nothing and banks
        nothing - holding and telling are words only.
        """
        from ..core.retrospectives import (
            format_retro,
            format_book,
            format_check,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_retro_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_retro_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "retro":
                text = format_retro(
                    primary.get_retro_retro(target),
                    primary.retro_book())
            elif stance == "check":
                text = format_check(
                    primary.retro_book(), target)
            elif stance == "slice":
                text = format_book(
                    primary.retro_book(), target)
            elif stance == "view":
                text = format_view(primary.get_retro_view(target))
            elif stance == "note":
                text = format_note(
                    primary.retro_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.retro_book())
            elif stance == "panel":
                text = format_panel(primary.retro_book())
            elif stance == "verdict":
                text = format_verdict(primary.retro_book())
            else:
                text = primary.retro_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_pattern(self, args: str):
        """M-214: /patterns - the pattern engine as data.

        ``/patterns`` shows the pattern book held this
        session - pattern slices as data: one record per
        pattern, held whole with the active slice it
        was held from, its one verifiable check
        at the house grain and its claims, and
        the notes held as data beside them (the shipped
        example book - five patterns at the M-203 slice
        boundary, with its three slice references, its
        two views, two stance records, one trace
        trace and its one pinned panel - when none
        is held yet); ``/patterns pattern <pattern-id>``
        shows one pattern whole; ``/patterns check
        <check>`` shows the pattern one check line
        reaches, or names the check unheld;
        ``/patterns slice <slice-id>`` shows the book's
        patterns of one slice; ``/patterns view <view-id>``
        shows one held view record; ``/patterns note
        <note-id>`` shows one held stance record;
        ``/patterns index`` shows the index derived
        from the whole book's held patterns; ``/patterns
        panel`` shows the panel derived from the
        whole book under its default view; ``/patterns
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: patterns and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every pattern held for the session is
        journaled as a pattern_pattern session event,
        every view as a pattern_view session event,
        every derived panel as a pattern_panel
        session event and every derived verdict as a
        pattern_verdict session event. This heading
        builds no slice, executes nothing and banks
        nothing - holding and telling are words only.
        """
        from ..core.pattern_extraction import (
            format_pattern,
            format_book,
            format_check,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_pattern_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_pattern_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "pattern":
                text = format_pattern(
                    primary.get_pattern_pattern(target),
                    primary.pattern_book())
            elif stance == "check":
                text = format_check(
                    primary.pattern_book(), target)
            elif stance == "slice":
                text = format_book(
                    primary.pattern_book(), target)
            elif stance == "view":
                text = format_view(primary.get_pattern_view(target))
            elif stance == "note":
                text = format_note(
                    primary.pattern_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.pattern_book())
            elif stance == "panel":
                text = format_panel(primary.pattern_book())
            elif stance == "verdict":
                text = format_verdict(primary.pattern_book())
            else:
                text = primary.pattern_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_estimate(self, args: str):
        """M-215: /estimates - the estimate engine as data.

        ``/estimates`` shows the estimate book held this
        session - estimate slices as data: one record per
        estimate, held whole with the active slice it
        was held from, its one verifiable check
        at the house grain and its claims, and
        the notes held as data beside them (the shipped
        example book - five estimates at the M-203 slice
        boundary, with its three slice references, its
        two views, two stance records, one trace
        trace and its one pinned panel - when none
        is held yet); ``/estimates estimate <estimate-id>``
        shows one estimate whole; ``/estimates check
        <check>`` shows the estimate one check line
        reaches, or names the check unheld;
        ``/estimates slice <slice-id>`` shows the book's
        estimates of one slice; ``/estimates view <view-id>``
        shows one held view record; ``/estimates note
        <note-id>`` shows one held stance record;
        ``/estimates index`` shows the index derived
        from the whole book's held estimates; ``/estimates
        panel`` shows the panel derived from the
        whole book under its default view; ``/estimates
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: estimates and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every estimate held for the session is
        journaled as a estimate_estimate session event,
        every view as a estimate_view session event,
        every derived panel as a estimate_panel
        session event and every derived verdict as a
        estimate_verdict session event. This heading
        builds no slice, executes nothing and banks
        nothing - holding and telling are words only.
        """
        from ..core.estimate_honesty import (
            format_estimate,
            format_book,
            format_check,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_estimate_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_estimate_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "estimate":
                text = format_estimate(
                    primary.get_estimate_estimate(target),
                    primary.estimate_book())
            elif stance == "check":
                text = format_check(
                    primary.estimate_book(), target)
            elif stance == "slice":
                text = format_book(
                    primary.estimate_book(), target)
            elif stance == "view":
                text = format_view(primary.get_estimate_view(target))
            elif stance == "note":
                text = format_note(
                    primary.estimate_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.estimate_book())
            elif stance == "panel":
                text = format_panel(primary.estimate_book())
            elif stance == "verdict":
                text = format_verdict(primary.estimate_book())
            else:
                text = primary.estimate_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")



    def _handle_campaign(self, args: str):
        """M-216: /hall - the campaign engine as data.

        ``/hall`` shows the campaign book held this
        session - campaign slices as data: one record per
        campaign, held whole with the active slice it
        was held from, its one verifiable check
        at the house grain and its claims, and
        the notes held as data beside them (the shipped
        example book - five campaigns at the M-203 slice
        boundary, with its three slice references, its
        two views, two stance records, one trace
        trace and its one pinned panel - when none
        is held yet); ``/hall campaign <campaign-id>``
        shows one campaign whole; ``/hall check
        <check>`` shows the campaign one check line
        reaches, or names the check unheld;
        ``/hall slice <slice-id>`` shows the book's
        campaigns of one slice; ``/hall view <view-id>``
        shows one held view record; ``/hall note
        <note-id>`` shows one held stance record;
        ``/hall index`` shows the index derived
        from the whole book's held campaigns; ``/hall
        panel`` shows the panel derived from the
        whole book under its default view; ``/hall
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: campaigns and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every campaign held for the session is
        journaled as a campaign_campaign session event,
        every view as a campaign_view session event,
        every derived panel as a hall_panel
        session event and every derived verdict as a
        hall_verdict session event. This heading
        builds no slice, executes nothing and banks
        nothing - holding and telling are words only.
        """
        from ..core.multi_campaign_hall import (
            format_campaign,
            format_book,
            format_check,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_campaign_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_campaign_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "campaign":
                text = format_campaign(
                    primary.get_hall_campaign(target),
                    primary.hall_book())
            elif stance == "check":
                text = format_check(
                    primary.hall_book(), target)
            elif stance == "repo":
                text = format_book(
                    primary.hall_book(), target)
            elif stance == "view":
                text = format_view(primary.get_hall_view(target))
            elif stance == "note":
                text = format_note(
                    primary.hall_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.hall_book())
            elif stance == "panel":
                text = format_panel(primary.hall_book())
            elif stance == "verdict":
                text = format_verdict(primary.hall_book())
            else:
                text = primary.hall_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_shape(self, args: str):
        """M-217: /shapes - the template engine as data.

        ``/shapes`` shows the template book held this
        session - template slices as data: one record per
        template, held whole with the active slice it
        was held from, its one verifiable check
        at the house grain and its claims, and
        the notes held as data beside them (the shipped
        example book - five templates at the M-203 slice
        boundary, with its three slice references, its
        two views, two stance records, one trace
        trace and its one pinned panel - when none
        is held yet); ``/shapes template <template-id>``
        shows one template whole; ``/shapes check
        <check>`` shows the template one check line
        reaches, or names the check unheld;
        ``/shapes slice <slice-id>`` shows the book's
        templates of one slice; ``/shapes view <view-id>``
        shows one held view record; ``/shapes note
        <note-id>`` shows one held stance record;
        ``/shapes index`` shows the index derived
        from the whole book's held templates; ``/shapes
        panel`` shows the panel derived from the
        whole book under its default view; ``/shapes
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: templates and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every template held for the session is
        journaled as a template_template session event,
        every view as a template_view session event,
        every derived panel as a shape_panel
        session event and every derived verdict as a
        shape_verdict session event. This heading
        builds no slice, executes nothing and banks
        nothing - holding and telling are words only.
        """
        from ..core.campaign_templates import (
            format_template,
            format_book,
            format_check,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_template_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_template_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "template":
                text = format_template(
                    primary.get_shape_template(target),
                    primary.shape_book())
            elif stance == "check":
                text = format_check(
                    primary.shape_book(), target)
            elif stance == "kind":
                text = format_book(
                    primary.shape_book(), target)
            elif stance == "view":
                text = format_view(primary.get_shape_view(target))
            elif stance == "note":
                text = format_note(
                    primary.shape_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.shape_book())
            elif stance == "panel":
                text = format_panel(primary.shape_book())
            elif stance == "verdict":
                text = format_verdict(primary.shape_book())
            else:
                text = primary.shape_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_mimis(self, args: str):
        """M-218: /mimis - the road engine as data.

        ``/mimis`` shows the road book held this
        session - road slices as data: one record per
        road, held whole with the active slice it
        was held from, its one verifiable check
        at the house grain and its claims, and
        the notes held as data beside them (the shipped
        example book - five roads at the M-203 slice
        boundary, with its three slice references, its
        two views, two stance records, one trace
        trace and its one pinned panel - when none
        is held yet); ``/mimis road <road-id>``
        shows one road whole; ``/mimis check
        <check>`` shows the road one check line
        reaches, or names the check unheld;
        ``/mimis slice <slice-id>`` shows the book's
        roads of one slice; ``/mimis view <view-id>``
        shows one held view record; ``/mimis note
        <note-id>`` shows one held stance record;
        ``/mimis index`` shows the index derived
        from the whole book's held roads; ``/mimis
        panel`` shows the panel derived from the
        whole book under its default view; ``/mimis
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: roads and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every road held for the session is
        journaled as a road_road session event,
        every view as a road_view session event,
        every derived panel as a mimis_panel
        session event and every derived verdict as a
        mimis_verdict session event. This heading
        builds no slice, executes nothing and banks
        nothing - holding and telling are words only.
        """
        from ..core.mimisbrunnr_road import (
            format_road,
            format_book,
            format_check,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_road_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_road_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "road":
                text = format_road(
                    primary.get_mimis_road(target),
                    primary.mimis_book())
            elif stance == "check":
                text = format_check(
                    primary.mimis_book(), target)
            elif stance == "concordance":
                text = format_book(
                    primary.mimis_book(), target)
            elif stance == "view":
                text = format_view(primary.get_mimis_view(target))
            elif stance == "note":
                text = format_note(
                    primary.mimis_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.mimis_book())
            elif stance == "panel":
                text = format_panel(primary.mimis_book())
            elif stance == "verdict":
                text = format_verdict(primary.mimis_book())
            else:
                text = primary.mimis_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_daybook(self, args: str):
        """M-219: /resumes - the resume engine as data.

        ``/resumes`` shows the resume book held this
        session - resume slices as data: one record per
        resume, held whole with the active slice it
        was held from, its one verifiable check
        at the house grain and its claims, and
        the notes held as data beside them (the shipped
        example book - five resumes at the M-203 slice
        boundary, with its three slice references, its
        two views, two stance records, one trace
        trace and its one pinned panel - when none
        is held yet); ``/resumes resume <resume-id>``
        shows one resume whole; ``/resumes check
        <check>`` shows the resume one check line
        reaches, or names the check unheld;
        ``/resumes slice <slice-id>`` shows the book's
        resumes of one slice; ``/resumes view <view-id>``
        shows one held view record; ``/resumes note
        <note-id>`` shows one held stance record;
        ``/resumes index`` shows the index derived
        from the whole book's held resumes; ``/resumes
        panel`` shows the panel derived from the
        whole book under its default view; ``/resumes
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: resumes and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every resume held for the session is
        journaled as a resume_resume session event,
        every view as a resume_view session event,
        every derived panel as a daybook_panel
        session event and every derived verdict as a
        daybook_verdict session event. This heading
        builds no slice, executes nothing and banks
        nothing - holding and telling are words only.
        """
        from ..core.interrupts_resumes import (
            format_resume,
            format_book,
            format_check,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_resume_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_resume_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "resume":
                text = format_resume(
                    primary.get_daybook_resume(target),
                    primary.daybook_book())
            elif stance == "check":
                text = format_check(
                    primary.daybook_book(), target)
            elif stance == "pause":
                text = format_book(
                    primary.daybook_book(), target)
            elif stance == "view":
                text = format_view(primary.get_daybook_view(target))
            elif stance == "note":
                text = format_note(
                    primary.daybook_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.daybook_book())
            elif stance == "panel":
                text = format_panel(primary.daybook_book())
            elif stance == "verdict":
                text = format_verdict(primary.daybook_book())
            else:
                text = primary.daybook_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_milestone(self, args: str):
        """M-220: /milestones - the report engine as data.

        ``/milestones`` shows the report book held this
        session - report slices as data: one record per
        report, held whole with the active slice it
        was held from, its one verifiable check
        at the house grain and its claims, and
        the notes held as data beside them (the shipped
        example book - five reports at the M-203 slice
        boundary, with its three slice references, its
        two views, two stance records, one trace
        trace and its one pinned panel - when none
        is held yet); ``/milestones report <report-id>``
        shows one report whole; ``/milestones check
        <check>`` shows the report one check line
        reaches, or names the check unheld;
        ``/milestones slice <slice-id>`` shows the book's
        reports of one slice; ``/milestones view <view-id>``
        shows one held view record; ``/milestones note
        <note-id>`` shows one held stance record;
        ``/milestones index`` shows the index derived
        from the whole book's held reports; ``/milestones
        panel`` shows the panel derived from the
        whole book under its default view; ``/milestones
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: reports and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every report held for the session is
        journaled as a report_report session event,
        every view as a report_view session event,
        every derived panel as a milestone_panel
        session event and every derived verdict as a
        milestone_verdict session event. This heading
        builds no slice, executes nothing and banks
        nothing - holding and telling are words only.
        """
        from ..core.milestone_reports import (
            format_report,
            format_book,
            format_check,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_report_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_report_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "report":
                text = format_report(
                    primary.get_milestone_report(target),
                    primary.milestone_book())
            elif stance == "check":
                text = format_check(
                    primary.milestone_book(), target)
            elif stance == "boundary":
                text = format_book(
                    primary.milestone_book(), target)
            elif stance == "view":
                text = format_view(primary.get_milestone_view(target))
            elif stance == "note":
                text = format_note(
                    primary.milestone_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.milestone_book())
            elif stance == "panel":
                text = format_panel(primary.milestone_book())
            elif stance == "verdict":
                text = format_verdict(primary.milestone_book())
            else:
                text = primary.milestone_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_log(self, args: str):
        """M-221: /log - the entry engine as data.

        ``/log`` shows the entry book held this
        session - entry slices as data: one record per
        entry, held whole with the active slice it
        was held from, its one verifiable check
        at the house grain and its claims, and
        the notes held as data beside them (the shipped
        example book - five entries at the M-203 slice
        day, with its three slice references, its
        two views, two stance records, one trace
        trace and its one pinned panel - when none
        is held yet); ``/log entry <entry-id>``
        shows one entry whole; ``/log check
        <check>`` shows the entry one check line
        reaches, or names the check unheld;
        ``/log slice <slice-id>`` shows the book's
        entries of one slice; ``/log view <view-id>``
        shows one held view record; ``/log note
        <note-id>`` shows one held stance record;
        ``/log index`` shows the index derived
        from the whole book's held entries; ``/log
        panel`` shows the panel derived from the
        whole book under its default view; ``/log
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: entries and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every entry held for the session is
        journaled as a entry_entry session event,
        every view as a entry_view session event,
        every derived panel as a log_panel
        session event and every derived verdict as a
        log_verdict session event. This heading
        builds no slice, executes nothing and banks
        nothing - holding and telling are words only.
        """
        from ..core.build_log import (
            format_entry,
            format_book,
            format_check,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_entry_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_entry_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "entry":
                text = format_entry(
                    primary.get_log_entry(target),
                    primary.log_book())
            elif stance == "check":
                text = format_check(
                    primary.log_book(), target)
            elif stance == "day":
                text = format_book(
                    primary.log_book(), target)
            elif stance == "view":
                text = format_view(primary.get_log_view(target))
            elif stance == "note":
                text = format_note(
                    primary.log_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.log_book())
            elif stance == "panel":
                text = format_panel(primary.log_book())
            elif stance == "verdict":
                text = format_verdict(primary.log_book())
            else:
                text = primary.log_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_selfmod(self, args: str):
        """M-222: /selfmod - the change engine as data.

        ``/selfmod`` shows the change book held this
        session - change slices as data: one record per
        change, held whole with the active slice it
        was held from, its one verifiable check
        at the house grain and its claims, and
        the notes held as data beside them (the shipped
        example book - five changes at the M-203 slice
        tool, with its three slice references, its
        two views, two stance records, one trace
        trace and its one pinned panel - when none
        is held yet); ``/selfmod change <change-id>``
        shows one change whole; ``/selfmod check
        <check>`` shows the change one check line
        reaches, or names the check unheld;
        ``/selfmod slice <slice-id>`` shows the book's
        changes of one slice; ``/selfmod view <view-id>``
        shows one held view record; ``/selfmod note
        <note-id>`` shows one held stance record;
        ``/selfmod index`` shows the index derived
        from the whole book's held changes; ``/selfmod
        panel`` shows the panel derived from the
        whole book under its default view; ``/selfmod
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: changes and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every change held for the session is
        journaled as a change_change session event,
        every view as a change_view session event,
        every derived panel as a selfmod_panel
        session event and every derived verdict as a
        selfmod_verdict session event. This heading
        builds no slice, executes nothing and banks
        nothing - holding and telling are words only.
        """
        from ..core.self_modification import (
            format_change,
            format_book,
            format_check,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_change_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_change_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "change":
                text = format_change(
                    primary.get_selfmod_change(target),
                    primary.selfmod_book())
            elif stance == "check":
                text = format_check(
                    primary.selfmod_book(), target)
            elif stance == "tool":
                text = format_book(
                    primary.selfmod_book(), target)
            elif stance == "view":
                text = format_view(primary.get_selfmod_view(target))
            elif stance == "note":
                text = format_note(
                    primary.selfmod_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.selfmod_book())
            elif stance == "panel":
                text = format_panel(primary.selfmod_book())
            elif stance == "verdict":
                text = format_verdict(primary.selfmod_book())
            else:
                text = primary.selfmod_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_failtax(self, args: str):
        """M-223: /failures - the failure engine as data.

        ``/failures`` shows the failure book held this
        session - failure runs as data: one record per
        failure, held whole with the active run it
        was held from, its one verifiable stage
        at the house grain and its claims, and
        the notes held as data beside them (the shipped
        example book - five failures at the M-203 run
        run, with its three run references, its
        two views, two stance records, one trace
        trace and its one pinned panel - when none
        is held yet); ``/failures failure <failure-id>``
        shows one failure whole; ``/failures stage
        <stage>`` shows the failure one stage line
        reaches, or names the stage unheld;
        ``/failures run <run-id>`` shows the book's
        failures of one run; ``/failures view <view-id>``
        shows one held view record; ``/failures note
        <note-id>`` shows one held stance record;
        ``/failures index`` shows the index derived
        from the whole book's held failures; ``/failures
        panel`` shows the panel derived from the
        whole book under its default view; ``/failures
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: failures and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every failure held for the session is
        journaled as a failure_failure session event,
        every view as a failure_view session event,
        every derived panel as a failtax_panel
        session event and every derived verdict as a
        failtax_verdict session event. This heading
        builds no run, executes nothing and banks
        nothing - holding and telling are words only.
        """
        from ..core.failure_taxonomy import (
            format_failure,
            format_book,
            format_stage,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_failure_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_failure_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "failure":
                text = format_failure(
                    primary.get_failtax_failure(target),
                    primary.failtax_book())
            elif stance == "stage":
                text = format_stage(
                    primary.failtax_book(), target)
            elif stance == "run":
                text = format_book(
                    primary.failtax_book(), target)
            elif stance == "view":
                text = format_view(primary.get_failtax_view(target))
            elif stance == "note":
                text = format_note(
                    primary.failtax_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.failtax_book())
            elif stance == "panel":
                text = format_panel(primary.failtax_book())
            elif stance == "verdict":
                text = format_verdict(primary.failtax_book())
            else:
                text = primary.failtax_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_dryrun(self, args: str):
        """M-224: /dryrun - the rehearsal engine as data.

        ``/dryrun`` shows the rehearsal book held this
        session - rehearsal campaigns as data: one record per
        rehearsal, held whole with the active campaign it
        was held from, its one verifiable stage
        at the house grain and its claims, and
        the notes held as data beside them (the shipped
        example book - five rehearsals at the M-203 campaign
        campaign, with its three campaign references, its
        two views, two stance records, one trace
        trace and its one pinned panel - when none
        is held yet); ``/dryrun rehearsal <rehearsal-id>``
        shows one rehearsal whole; ``/dryrun stage
        <stage>`` shows the rehearsal one stage line
        reaches, or names the stage unheld;
        ``/dryrun campaign <campaign-id>`` shows the book's
        rehearsals of one campaign; ``/dryrun view <view-id>``
        shows one held view record; ``/dryrun note
        <note-id>`` shows one held stance record;
        ``/dryrun index`` shows the index derived
        from the whole book's held rehearsals; ``/dryrun
        panel`` shows the panel derived from the
        whole book under its default view; ``/dryrun
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: rehearsals and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every rehearsal held for the session is
        journaled as a rehearsal_rehearsal session event,
        every view as a rehearsal_view session event,
        every derived panel as a dryrun_panel
        session event and every derived verdict as a
        dryrun_verdict session event. This heading
        builds no campaign, executes nothing and banks
        nothing - holding and telling are words only.
        """
        from ..core.dry_run_campaigns import (
            format_rehearsal,
            format_book,
            format_stage,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_rehearsal_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_rehearsal_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "rehearsal":
                text = format_rehearsal(
                    primary.get_dryrun_rehearsal(target),
                    primary.dryrun_book())
            elif stance == "stage":
                text = format_stage(
                    primary.dryrun_book(), target)
            elif stance == "campaign":
                text = format_book(
                    primary.dryrun_book(), target)
            elif stance == "view":
                text = format_view(primary.get_dryrun_view(target))
            elif stance == "note":
                text = format_note(
                    primary.dryrun_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.dryrun_book())
            elif stance == "panel":
                text = format_panel(primary.dryrun_book())
            elif stance == "verdict":
                text = format_verdict(primary.dryrun_book())
            else:
                text = primary.dryrun_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_export(self, args: str):
        """M-225: /export - the bundle engine as data.

        ``/export`` shows the bundle book held this
        session - bundle campaigns as data: one record per
        bundle, held whole with the active campaign it
        was held from, its one verifiable stage
        at the house grain and its claims, and
        the notes held as data beside them (the shipped
        example book - five bundles at the M-203 campaign
        campaign, with its three campaign references, its
        two views, two stance records, one trace
        trace and its one pinned panel - when none
        is held yet); ``/export bundle <bundle-id>``
        shows one bundle whole; ``/export stage
        <stage>`` shows the bundle one stage line
        reaches, or names the stage unheld;
        ``/export campaign <campaign-id>`` shows the book's
        bundles of one campaign; ``/export view <view-id>``
        shows one held view record; ``/export note
        <note-id>`` shows one held stance record;
        ``/export index`` shows the index derived
        from the whole book's held bundles; ``/export
        panel`` shows the panel derived from the
        whole book under its default view; ``/export
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: bundles and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every bundle held for the session is
        journaled as a bundle_bundle session event,
        every view as a bundle_view session event,
        every derived panel as a export_panel
        session event and every derived verdict as a
        export_verdict session event. This heading
        builds no campaign, executes nothing and banks
        nothing - holding and telling are words only.
        """
        from ..core.campaign_export import (
            format_bundle,
            format_book,
            format_stage,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_bundle_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_bundle_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "bundle":
                text = format_bundle(
                    primary.get_export_bundle(target),
                    primary.export_book())
            elif stance == "stage":
                text = format_stage(
                    primary.export_book(), target)
            elif stance == "campaign":
                text = format_book(
                    primary.export_book(), target)
            elif stance == "view":
                text = format_view(primary.get_export_view(target))
            elif stance == "note":
                text = format_note(
                    primary.export_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.export_book())
            elif stance == "panel":
                text = format_panel(primary.export_book())
            elif stance == "verdict":
                text = format_verdict(primary.export_book())
            else:
                text = primary.export_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_orders(self, args: str):
        """M-226: /orders - the order engine as data.

        ``/orders`` shows the order book held this
        session - order campaigns as data: one record per
        order, held whole with the active campaign it
        was held from, its one verifiable stage
        at the house grain and its claims, and
        the notes held as data beside them (the shipped
        example book - five orders at the M-203 campaign
        campaign, with its three campaign references, its
        two views, two stance records, one trace
        trace and its one pinned panel - when none
        is held yet); ``/orders order <order-id>``
        shows one order whole; ``/orders stage
        <stage>`` shows the order one stage line
        reaches, or names the stage unheld;
        ``/orders campaign <campaign-id>`` shows the book's
        orders of one campaign; ``/orders view <view-id>``
        shows one held view record; ``/orders note
        <note-id>`` shows one held stance record;
        ``/orders index`` shows the index derived
        from the whole book's held orders; ``/orders
        panel`` shows the panel derived from the
        whole book under its default view; ``/orders
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: orders and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every order held for the session is
        journaled as a order_order session event,
        every view as a order_view session event,
        every derived panel as a orders_panel
        session event and every derived verdict as a
        orders_verdict session event. This heading
        builds no campaign, executes nothing and banks
        nothing - holding and telling are words only.
        """
        from ..core.standing_orders import (
            format_order,
            format_book,
            format_stage,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_order_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_order_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "order":
                text = format_order(
                    primary.get_orders_order(target),
                    primary.orders_book())
            elif stance == "stage":
                text = format_stage(
                    primary.orders_book(), target)
            elif stance == "campaign":
                text = format_book(
                    primary.orders_book(), target)
            elif stance == "view":
                text = format_view(primary.get_orders_view(target))
            elif stance == "note":
                text = format_note(
                    primary.orders_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.orders_book())
            elif stance == "panel":
                text = format_panel(primary.orders_book())
            elif stance == "verdict":
                text = format_verdict(primary.orders_book())
            else:
                text = primary.orders_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_workflow(self, args: str):
        """M-227: /workflow - the proposal engine as data.

        ``/workflow`` shows the proposal book held this
        session - proposal campaigns as data: one record per
        proposal, held whole with the active campaign it
        was held from, its one verifiable stage
        at the house grain and its claims, and
        the notes held as data beside them (the shipped
        example book - five proposals at the M-203 campaign
        campaign, with its three campaign references, its
        two views, two stance records, one trace
        trace and its one pinned panel - when none
        is held yet); ``/workflow proposal <proposal-id>``
        shows one proposal whole; ``/workflow stage
        <stage>`` shows the proposal one stage line
        reaches, or names the stage unheld;
        ``/workflow campaign <campaign-id>`` shows the book's
        proposals of one campaign; ``/workflow view <view-id>``
        shows one held view record; ``/workflow note
        <note-id>`` shows one held stance record;
        ``/workflow index`` shows the index derived
        from the whole book's held proposals; ``/workflow
        panel`` shows the panel derived from the
        whole book under its default view; ``/workflow
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: proposals and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every proposal held for the session is
        journaled as a proposal_proposal session event,
        every view as a proposal_view session event,
        every derived panel as a workflow_panel
        session event and every derived verdict as a
        workflow_verdict session event. This heading
        builds no campaign, executes nothing and banks
        nothing - holding and telling are words only.
        """
        from ..core.workflow_default import (
            format_proposal,
            format_book,
            format_stage,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_proposal_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_proposal_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "proposal":
                text = format_proposal(
                    primary.get_workflow_proposal(target),
                    primary.workflow_book())
            elif stance == "stage":
                text = format_stage(
                    primary.workflow_book(), target)
            elif stance == "campaign":
                text = format_book(
                    primary.workflow_book(), target)
            elif stance == "view":
                text = format_view(primary.get_workflow_view(target))
            elif stance == "note":
                text = format_note(
                    primary.workflow_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.workflow_book())
            elif stance == "panel":
                text = format_panel(primary.workflow_book())
            elif stance == "verdict":
                text = format_verdict(primary.workflow_book())
            else:
                text = primary.workflow_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_scaling(self, args: str):
        """M-228: /scaling - the endeavour engine as data.

        ``/scaling`` shows the endeavour book held this
        session - endeavour campaigns as data: one record per
        endeavour, held whole with the active campaign it
        was held from, its one verifiable stage
        at the house grain and its claims, and
        the notes held as data beside them (the shipped
        example book - five endeavours at the M-203 campaign
        campaign, with its three campaign references, its
        two views, two stance records, one trace
        trace and its one pinned panel - when none
        is held yet); ``/scaling endeavour <endeavour-id>``
        shows one endeavour whole; ``/scaling stage
        <stage>`` shows the endeavour one stage line
        reaches, or names the stage unheld;
        ``/scaling campaign <campaign-id>`` shows the book's
        endeavours of one campaign; ``/scaling view <view-id>``
        shows one held view record; ``/scaling note
        <note-id>`` shows one held stance record;
        ``/scaling index`` shows the index derived
        from the whole book's held endeavours; ``/scaling
        panel`` shows the panel derived from the
        whole book under its default view; ``/scaling
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: endeavours and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every endeavour held for the session is
        journaled as a endeavour_endeavour session event,
        every view as a endeavour_view session event,
        every derived panel as a scaling_panel
        session event and every derived verdict as a
        scaling_verdict session event. This heading
        builds no campaign, executes nothing and banks
        nothing - holding and telling are words only.
        """
        from ..core.team_scaling import (
            format_endeavour,
            format_book,
            format_stage,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_endeavour_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_endeavour_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "endeavour":
                text = format_endeavour(
                    primary.get_scaling_endeavour(target),
                    primary.scaling_book())
            elif stance == "stage":
                text = format_stage(
                    primary.scaling_book(), target)
            elif stance == "campaign":
                text = format_book(
                    primary.scaling_book(), target)
            elif stance == "view":
                text = format_view(primary.get_scaling_view(target))
            elif stance == "note":
                text = format_note(
                    primary.scaling_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.scaling_book())
            elif stance == "panel":
                text = format_panel(primary.scaling_book())
            elif stance == "verdict":
                text = format_verdict(primary.scaling_book())
            else:
                text = primary.scaling_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_course(self, args: str):
        """M-229: /course - the lesson engine as data.

        ``/course`` shows the lesson book held this
        session - lesson campaigns as data: one record per
        lesson, held whole with the active campaign it
        was held from, its one verifiable stage
        at the house grain and its claims, and
        the notes held as data beside them (the shipped
        example book - five lessons at the M-203 campaign
        campaign, with its three campaign references, its
        two views, two stance records, one trace
        trace and its one pinned panel - when none
        is held yet); ``/course lesson <lesson-id>``
        shows one lesson whole; ``/course stage
        <stage>`` shows the lesson one stage line
        reaches, or names the stage unheld;
        ``/course campaign <campaign-id>`` shows the book's
        lessons of one campaign; ``/course view <view-id>``
        shows one held view record; ``/course note
        <note-id>`` shows one held stance record;
        ``/course index`` shows the index derived
        from the whole book's held lessons; ``/course
        panel`` shows the panel derived from the
        whole book under its default view; ``/course
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: lessons and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every lesson held for the session is
        journaled as a lesson_lesson session event,
        every view as a lesson_view session event,
        every derived panel as a course_panel
        session event and every derived verdict as a
        course_verdict session event. This heading
        builds no campaign, executes nothing and banks
        nothing - holding and telling are words only.
        """
        from ..core.method_course import (
            format_lesson,
            format_book,
            format_stage,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_lesson_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_lesson_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "lesson":
                text = format_lesson(
                    primary.get_course_lesson(target),
                    primary.course_book())
            elif stance == "stage":
                text = format_stage(
                    primary.course_book(), target)
            elif stance == "campaign":
                text = format_book(
                    primary.course_book(), target)
            elif stance == "view":
                text = format_view(primary.get_course_view(target))
            elif stance == "note":
                text = format_note(
                    primary.course_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.course_book())
            elif stance == "panel":
                text = format_panel(primary.course_book())
            elif stance == "verdict":
                text = format_verdict(primary.course_book())
            else:
                text = primary.course_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_metrics(self, args: str):
        """M-230: /metrics - the reading engine as data.

        ``/metrics`` shows the reading book held this
        session - reading campaigns as data: one record per
        reading, held whole with the active campaign it
        was held from, its one verifiable stage
        at the house grain and its claims, and
        the notes held as data beside them (the shipped
        example book - five readings at the M-203 campaign
        campaign, with its three campaign references, its
        two views, two stance records, one trace
        trace and its one pinned panel - when none
        is held yet); ``/metrics reading <reading-id>``
        shows one reading whole; ``/metrics stage
        <stage>`` shows the reading one stage line
        reaches, or names the stage unheld;
        ``/metrics campaign <campaign-id>`` shows the book's
        readings of one campaign; ``/metrics view <view-id>``
        shows one held view record; ``/metrics note
        <note-id>`` shows one held stance record;
        ``/metrics index`` shows the index derived
        from the whole book's held readings; ``/metrics
        panel`` shows the panel derived from the
        whole book under its default view; ``/metrics
        verdict`` shows the verdict derived for the
        whole book. Reading registers and publishes
        nothing as session news: readings and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every reading held for the session is
        journaled as a reading_reading session event,
        every view as a reading_view session event,
        every derived panel as a metrics_panel
        session event and every derived verdict as a
        metrics_verdict session event. This heading
        builds no campaign, executes nothing and banks
        nothing - holding and telling are words only.
        """
        from ..core.method_metrics import (
            format_reading,
            format_book,
            format_stage,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_reading_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_reading_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "reading":
                text = format_reading(
                    primary.get_metrics_reading(target),
                    primary.metrics_book())
            elif stance == "stage":
                text = format_stage(
                    primary.metrics_book(), target)
            elif stance == "campaign":
                text = format_book(
                    primary.metrics_book(), target)
            elif stance == "view":
                text = format_view(primary.get_metrics_view(target))
            elif stance == "note":
                text = format_note(
                    primary.metrics_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.metrics_book())
            elif stance == "panel":
                text = format_panel(primary.metrics_book())
            elif stance == "verdict":
                text = format_verdict(primary.metrics_book())
            else:
                text = primary.metrics_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_crossapp(self, args: str):
        """M-231: /crossapp - the external engine as data.

        ``/crossapp`` shows the external book held this
        session - external campaigns as data: one record per
        external, held whole with the active campaign it
        was held from, its one verifiable stage
        at the house grain and its claims, and
        the notes held as data beside them (the shipped
        example book - five externals at the M-203 campaign
        campaign, with its three campaign references, its
        two views, two stance records, one trace
        trace and its one pinned panel - when none
        is held yet); ``/crossapp external <external-id>``
        shows one external whole; ``/crossapp stage
        <stage>`` shows the external one stage line
        reaches, or names the stage unheld;
        ``/crossapp campaign <campaign-id>`` shows the book's
        externals of one campaign; ``/crossapp view <view-id>``
        shows one held view record; ``/crossapp note
        <note-id>`` shows one held stance record;
        ``/crossapp index`` shows the index derived
        from the whole book's held externals; ``/crossapp
        panel`` shows the panel derived from the
        whole book under its default view; ``/crossapp
        verdict`` shows the verdict derived for the
        whole book. External registers and publishes
        nothing as session news: externals and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every external held for the session is
        journaled as a external_external session event,
        every view as a external_view session event,
        every derived panel as a crossapp_panel
        session event and every derived verdict as a
        crossapp_verdict session event. This heading
        builds no campaign, executes nothing and banks
        nothing - holding and telling are words only.
        """
        from ..core.cross_app_method import (
            format_external,
            format_book,
            format_stage,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_external_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_external_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "external":
                text = format_external(
                    primary.get_crossapp_external(target),
                    primary.crossapp_book())
            elif stance == "stage":
                text = format_stage(
                    primary.crossapp_book(), target)
            elif stance == "campaign":
                text = format_book(
                    primary.crossapp_book(), target)
            elif stance == "view":
                text = format_view(primary.get_crossapp_view(target))
            elif stance == "note":
                text = format_note(
                    primary.crossapp_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.crossapp_book())
            elif stance == "panel":
                text = format_panel(primary.crossapp_book())
            elif stance == "verdict":
                text = format_verdict(primary.crossapp_book())
            else:
                text = primary.crossapp_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_mcpclient(self, args: str):
        """M-233: /mcpclient - the connection engine as data.

        ``/mcpclient`` shows the connection book held this
        session - connection servers as data: one record per
        connection, held whole with the active server it
        was held from, its one verifiable stage
        at the house grain and its claims, and
        the notes held as data beside them (the shipped
        example book - five connections at the M-203 server
        server, with its three server references, its
        two views, two stance records, one trace
        trace and its one pinned panel - when none
        is held yet); ``/mcpclient connection <connection-id>``
        shows one connection whole; ``/mcpclient stage
        <stage>`` shows the connection one stage line
        reaches, or names the stage unheld;
        ``/mcpclient server <server-id>`` shows the book's
        connections of one server; ``/mcpclient view <view-id>``
        shows one held view record; ``/mcpclient note
        <note-id>`` shows one held stance record;
        ``/mcpclient index`` shows the index derived
        from the whole book's held connections; ``/mcpclient
        panel`` shows the panel derived from the
        whole book under its default view; ``/mcpclient
        verdict`` shows the verdict derived for the
        whole book. Connection registers and publishes
        nothing as session news: connections and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every connection held for the session is
        journaled as a connection_connection session event,
        every view as a connection_view session event,
        every derived panel as a mcpclient_panel
        session event and every derived verdict as a
        mcpclient_verdict session event. This heading
        builds no server, executes nothing and banks
        nothing - holding and telling are words only.
        """
        from ..core.mcp_client import (
            format_connection,
            format_book,
            format_stage,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_connection_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_connection_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "connection":
                text = format_connection(
                    primary.get_mcpclient_connection(target),
                    primary.mcpclient_book())
            elif stance == "stage":
                text = format_stage(
                    primary.mcpclient_book(), target)
            elif stance == "server":
                text = format_book(
                    primary.mcpclient_book(), target)
            elif stance == "view":
                text = format_view(primary.get_mcpclient_view(target))
            elif stance == "note":
                text = format_note(
                    primary.mcpclient_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.mcpclient_book())
            elif stance == "panel":
                text = format_panel(primary.mcpclient_book())
            elif stance == "verdict":
                text = format_verdict(primary.mcpclient_book())
            else:
                text = primary.mcpclient_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_mcpregistry(self, args: str):
        """M-235: /mcpregistry - the listing engine as data.

        ``/mcpregistry`` shows the listing book held this
        session - listing entrys as data: one record per
        listing, held whole with the active entry it
        was held from, its one verifiable stage
        at the house grain and its claims, and
        the notes held as data beside them (the shipped
        example book - five listings at the M-203 entry
        entry, with its three entry references, its
        two views, two stance records, one trace
        trace and its one pinned panel - when none
        is held yet); ``/mcpregistry listing <listing-id>``
        shows one listing whole; ``/mcpregistry stage
        <stage>`` shows the listing one stage line
        reaches, or names the stage unheld;
        ``/mcpregistry entry <entry-id>`` shows the book's
        listings of one entry; ``/mcpregistry view <view-id>``
        shows one held view record; ``/mcpregistry note
        <note-id>`` shows one held stance record;
        ``/mcpregistry index`` shows the index derived
        from the whole book's held listings; ``/mcpregistry
        panel`` shows the panel derived from the
        whole book under its default view; ``/mcpregistry
        verdict`` shows the verdict derived for the
        whole book. Listing registers and publishes
        nothing as session news: listings and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every listing held for the session is
        journaled as a listing_listing session event,
        every view as a listing_view session event,
        every derived panel as a mcpregistry_panel
        session event and every derived verdict as a
        mcpregistry_verdict session event. This heading
        builds no entry, executes nothing and banks
        nothing - holding and telling are words only.
        """
        from ..core.mcp_registry import (
            format_listing,
            format_book,
            format_stage,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_listing_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_listing_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "listing":
                text = format_listing(
                    primary.get_mcpregistry_listing(target),
                    primary.mcpregistry_book())
            elif stance == "stage":
                text = format_stage(
                    primary.mcpregistry_book(), target)
            elif stance == "entry":
                text = format_book(
                    primary.mcpregistry_book(), target)
            elif stance == "view":
                text = format_view(primary.get_mcpregistry_view(target))
            elif stance == "note":
                text = format_note(
                    primary.mcpregistry_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.mcpregistry_book())
            elif stance == "panel":
                text = format_panel(primary.mcpregistry_book())
            elif stance == "verdict":
                text = format_verdict(primary.mcpregistry_book())
            else:
                text = primary.mcpregistry_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_skillsstandard(self, args: str):
        """M-236: /skillsstandard - the pack engine as data.

        ``/skillsstandard`` shows the pack book held this
        session - pack skills as data: one record per
        pack, held whole with the active skill it
        was held from, its one verifiable stage
        at the house grain and its claims, and
        the notes held as data beside them (the shipped
        example book - five packs at the M-203 skill
        skill, with its three skill references, its
        two views, two stance records, one trace
        trace and its one pinned panel - when none
        is held yet); ``/skillsstandard pack <pack-id>``
        shows one pack whole; ``/skillsstandard stage
        <stage>`` shows the pack one stage line
        reaches, or names the stage unheld;
        ``/skillsstandard skill <skill-id>`` shows the book's
        packs of one skill; ``/skillsstandard view <view-id>``
        shows one held view record; ``/skillsstandard note
        <note-id>`` shows one held stance record;
        ``/skillsstandard index`` shows the index derived
        from the whole book's held packs; ``/skillsstandard
        panel`` shows the panel derived from the
        whole book under its default view; ``/skillsstandard
        verdict`` shows the verdict derived for the
        whole book. Pack registers and publishes
        nothing as session news: packs and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every pack held for the session is
        journaled as a pack_pack session event,
        every view as a pack_view session event,
        every derived panel as a skillsstandard_panel
        session event and every derived verdict as a
        skillsstandard_verdict session event. This heading
        builds no skill, executes nothing and banks
        nothing - holding and telling are words only.
        """
        from ..core.skills_standard import (
            format_pack,
            format_book,
            format_stage,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_pack_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_pack_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "pack":
                text = format_pack(
                    primary.get_skillsstandard_pack(target),
                    primary.skillsstandard_book())
            elif stance == "stage":
                text = format_stage(
                    primary.skillsstandard_book(), target)
            elif stance == "skill":
                text = format_book(
                    primary.skillsstandard_book(), target)
            elif stance == "view":
                text = format_view(primary.get_skillsstandard_view(target))
            elif stance == "note":
                text = format_note(
                    primary.skillsstandard_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.skillsstandard_book())
            elif stance == "panel":
                text = format_panel(primary.skillsstandard_book())
            elif stance == "verdict":
                text = format_verdict(primary.skillsstandard_book())
            else:
                text = primary.skillsstandard_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_customcommands(self, args: str):
        """M-237: /customcommands - the template engine as data.

        ``/customcommands`` shows the template book held this
        session - template commands as data: one record per
        template, held whole with the active command it
        was held from, its one verifiable stage
        at the house grain and its claims, and
        the notes held as data beside them (the shipped
        example book - five templates at the M-203 command
        command, with its three command references, its
        two views, two stance records, one trace
        trace and its one pinned panel - when none
        is held yet); ``/customcommands template <template-id>``
        shows one template whole; ``/customcommands stage
        <stage>`` shows the template one stage line
        reaches, or names the stage unheld;
        ``/customcommands command <command-id>`` shows the book's
        templates of one command; ``/customcommands view <view-id>``
        shows one held view record; ``/customcommands note
        <note-id>`` shows one held stance record;
        ``/customcommands index`` shows the index derived
        from the whole book's held templates; ``/customcommands
        panel`` shows the panel derived from the
        whole book under its default view; ``/customcommands
        verdict`` shows the verdict derived for the
        whole book. Template registers and publishes
        nothing as session news: templates and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every template held for the session is
        journaled as a template_template session event,
        every view as a template_view session event,
        every derived panel as a customcommands_panel
        session event and every derived verdict as a
        customcommands_verdict session event. This heading
        builds no command, executes nothing and banks
        nothing - holding and telling are words only.
        """
        from ..core.custom_commands import (
            format_template,
            format_book,
            format_stage,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_template_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_template_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "template":
                text = format_template(
                    primary.get_customcommands_template(target),
                    primary.customcommands_book())
            elif stance == "stage":
                text = format_stage(
                    primary.customcommands_book(), target)
            elif stance == "command":
                text = format_book(
                    primary.customcommands_book(), target)
            elif stance == "view":
                text = format_view(primary.get_customcommands_view(target))
            elif stance == "note":
                text = format_note(
                    primary.customcommands_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.customcommands_book())
            elif stance == "panel":
                text = format_panel(primary.customcommands_book())
            elif stance == "verdict":
                text = format_verdict(primary.customcommands_book())
            else:
                text = primary.customcommands_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_pluginbundles(self, args: str):
        """M-238: /pluginbundles - the bundle engine as data.

        ``/pluginbundles`` shows the bundle book held this
        session - bundle plugins as data: one record per
        bundle, held whole with the active plugin it
        was held from, its one verifiable stage
        at the house grain and its claims, and
        the notes held as data beside them (the shipped
        example book - five bundles at the M-203 plugin
        plugin, with its three plugin references, its
        two views, two stance records, one trace
        trace and its one pinned panel - when none
        is held yet); ``/pluginbundles bundle <bundle-id>``
        shows one bundle whole; ``/pluginbundles stage
        <stage>`` shows the bundle one stage line
        reaches, or names the stage unheld;
        ``/pluginbundles plugin <plugin-id>`` shows the book's
        bundles of one plugin; ``/pluginbundles view <view-id>``
        shows one held view record; ``/pluginbundles note
        <note-id>`` shows one held stance record;
        ``/pluginbundles index`` shows the index derived
        from the whole book's held bundles; ``/pluginbundles
        panel`` shows the panel derived from the
        whole book under its default view; ``/pluginbundles
        verdict`` shows the verdict derived for the
        whole book. Bundle registers and publishes
        nothing as session news: bundles and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every bundle held for the session is
        journaled as a bundle_bundle session event,
        every view as a bundle_view session event,
        every derived panel as a pluginbundles_panel
        session event and every derived verdict as a
        pluginbundles_verdict session event. This heading
        builds no plugin, executes nothing and banks
        nothing - holding and telling are words only.
        """
        from ..core.plugin_bundles import (
            format_bundle,
            format_book,
            format_stage,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_bundle_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_bundle_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "bundle":
                text = format_bundle(
                    primary.get_pluginbundles_bundle(target),
                    primary.pluginbundles_book())
            elif stance == "stage":
                text = format_stage(
                    primary.pluginbundles_book(), target)
            elif stance == "plugin":
                text = format_book(
                    primary.pluginbundles_book(), target)
            elif stance == "view":
                text = format_view(primary.get_pluginbundles_view(target))
            elif stance == "note":
                text = format_note(
                    primary.pluginbundles_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.pluginbundles_book())
            elif stance == "panel":
                text = format_panel(primary.pluginbundles_book())
            elif stance == "verdict":
                text = format_verdict(primary.pluginbundles_book())
            else:
                text = primary.pluginbundles_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_vscodecompanions(self, args: str):
        """M-239: /vscodecompanions - the companion engine as data.

        ``/vscodecompanions`` shows the companion book held this
        session - companion editors as data: one record per
        companion, held whole with the active editor it
        was held from, its one verifiable stage
        at the house grain and its claims, and
        the notes held as data beside them (the shipped
        example book - five companions at the M-203 editor
        editor, with its three editor references, its
        two views, two stance records, one trace
        trace and its one pinned panel - when none
        is held yet); ``/vscodecompanions companion <companion-id>``
        shows one companion whole; ``/vscodecompanions stage
        <stage>`` shows the companion one stage line
        reaches, or names the stage unheld;
        ``/vscodecompanions editor <editor-id>`` shows the book's
        companions of one editor; ``/vscodecompanions view <view-id>``
        shows one held view record; ``/vscodecompanions note
        <note-id>`` shows one held stance record;
        ``/vscodecompanions index`` shows the index derived
        from the whole book's held companions; ``/vscodecompanions
        panel`` shows the panel derived from the
        whole book under its default view; ``/vscodecompanions
        verdict`` shows the verdict derived for the
        whole book. Companion registers and publishes
        nothing as session news: companions and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every companion held for the session is
        journaled as a companion_companion session event,
        every view as a companion_view session event,
        every derived panel as a vscodecompanions_panel
        session event and every derived verdict as a
        vscodecompanions_verdict session event. This heading
        builds no editor, executes nothing and banks
        nothing - holding and telling are words only.
        """
        from ..core.vscode_companions import (
            format_companion,
            format_book,
            format_stage,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_companion_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_companion_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "companion":
                text = format_companion(
                    primary.get_vscodecompanions_companion(target),
                    primary.vscodecompanions_book())
            elif stance == "stage":
                text = format_stage(
                    primary.vscodecompanions_book(), target)
            elif stance == "editor":
                text = format_book(
                    primary.vscodecompanions_book(), target)
            elif stance == "view":
                text = format_view(primary.get_vscodecompanions_view(target))
            elif stance == "note":
                text = format_note(
                    primary.vscodecompanions_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.vscodecompanions_book())
            elif stance == "panel":
                text = format_panel(primary.vscodecompanions_book())
            elif stance == "verdict":
                text = format_verdict(primary.vscodecompanions_book())
            else:
                text = primary.vscodecompanions_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_idecompanions(self, args: str):
        """M-240: /idecompanions - the endpoint engine as data.

        ``/idecompanions`` shows the endpoint book held this
        session - endpoint hosts as data: one record per
        endpoint, held whole with the active host it
        was held from, its one verifiable stage
        at the house grain and its claims, and
        the notes held as data beside them (the shipped
        example book - five endpoints at the M-203 host
        host, with its three host references, its
        two views, two stance records, one trace
        trace and its one pinned panel - when none
        is held yet); ``/idecompanions endpoint <endpoint-id>``
        shows one endpoint whole; ``/idecompanions stage
        <stage>`` shows the endpoint one stage line
        reaches, or names the stage unheld;
        ``/idecompanions host <host-id>`` shows the book's
        endpoints of one host; ``/idecompanions view <view-id>``
        shows one held view record; ``/idecompanions note
        <note-id>`` shows one held stance record;
        ``/idecompanions index`` shows the index derived
        from the whole book's held endpoints; ``/idecompanions
        panel`` shows the panel derived from the
        whole book under its default view; ``/idecompanions
        verdict`` shows the verdict derived for the
        whole book. Endpoint registers and publishes
        nothing as session news: endpoints and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every endpoint held for the session is
        journaled as a endpoint_endpoint session event,
        every view as a endpoint_view session event,
        every derived panel as a idecompanions_panel
        session event and every derived verdict as a
        idecompanions_verdict session event. This heading
        builds no host, executes nothing and banks
        nothing - holding and telling are words only.
        """
        from ..core.ide_companions import (
            format_endpoint,
            format_book,
            format_stage,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_endpoint_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_endpoint_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "endpoint":
                text = format_endpoint(
                    primary.get_idecompanions_endpoint(target),
                    primary.idecompanions_book())
            elif stance == "stage":
                text = format_stage(
                    primary.idecompanions_book(), target)
            elif stance == "host":
                text = format_book(
                    primary.idecompanions_book(), target)
            elif stance == "view":
                text = format_view(primary.get_idecompanions_view(target))
            elif stance == "note":
                text = format_note(
                    primary.idecompanions_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.idecompanions_book())
            elif stance == "panel":
                text = format_panel(primary.idecompanions_book())
            elif stance == "verdict":
                text = format_verdict(primary.idecompanions_book())
            else:
                text = primary.idecompanions_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_rivalimporters(self, args: str):
        """M-241: /rivalimporters - the importer engine as data.

        ``/rivalimporters`` shows the importer book held this
        session - importer sources as data: one record per
        importer, held whole with the active source it
        was held from, its one verifiable stage
        at the house grain and its claims, and
        the notes held as data beside them (the shipped
        example book - five importers at the M-203 source
        source, with its three source references, its
        two views, two stance records, one trace
        trace and its one pinned panel - when none
        is held yet); ``/rivalimporters importer <importer-id>``
        shows one importer whole; ``/rivalimporters stage
        <stage>`` shows the importer one stage line
        reaches, or names the stage unheld;
        ``/rivalimporters source <source-id>`` shows the book's
        importers of one source; ``/rivalimporters view <view-id>``
        shows one held view record; ``/rivalimporters note
        <note-id>`` shows one held stance record;
        ``/rivalimporters index`` shows the index derived
        from the whole book's held importers; ``/rivalimporters
        panel`` shows the panel derived from the
        whole book under its default view; ``/rivalimporters
        verdict`` shows the verdict derived for the
        whole book. Importer registers and publishes
        nothing as session news: importers and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every importer held for the session is
        journaled as a importer_importer session event,
        every view as a importer_view session event,
        every derived panel as a rivalimporters_panel
        session event and every derived verdict as a
        rivalimporters_verdict session event. This heading
        builds no source, executes nothing and banks
        nothing - holding and telling are words only.
        """
        from ..core.rival_importers import (
            format_importer,
            format_book,
            format_stage,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_importer_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_importer_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "importer":
                text = format_importer(
                    primary.get_rivalimporters_importer(target),
                    primary.rivalimporters_book())
            elif stance == "stage":
                text = format_stage(
                    primary.rivalimporters_book(), target)
            elif stance == "source":
                text = format_book(
                    primary.rivalimporters_book(), target)
            elif stance == "view":
                text = format_view(primary.get_rivalimporters_view(target))
            elif stance == "note":
                text = format_note(
                    primary.rivalimporters_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.rivalimporters_book())
            elif stance == "panel":
                text = format_panel(primary.rivalimporters_book())
            elif stance == "verdict":
                text = format_verdict(primary.rivalimporters_book())
            else:
                text = primary.rivalimporters_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_samverkbridge(self, args: str):
        """M-242: /samverkbridge - the exchange engine as data.

        ``/samverkbridge`` shows the exchange book held this
        session - exchange repos as data: one record per
        exchange, held whole with the active repo it
        was held from, its one verifiable stage
        at the house grain and its claims, and
        the notes held as data beside them (the shipped
        example book - five exchanges at the M-203 repo
        repo, with its three repo references, its
        two views, two stance records, one trace
        trace and its one pinned panel - when none
        is held yet); ``/samverkbridge exchange <exchange-id>``
        shows one exchange whole; ``/samverkbridge stage
        <stage>`` shows the exchange one stage line
        reaches, or names the stage unheld;
        ``/samverkbridge repo <repo-id>`` shows the book's
        exchanges of one repo; ``/samverkbridge view <view-id>``
        shows one held view record; ``/samverkbridge note
        <note-id>`` shows one held stance record;
        ``/samverkbridge index`` shows the index derived
        from the whole book's held exchanges; ``/samverkbridge
        panel`` shows the panel derived from the
        whole book under its default view; ``/samverkbridge
        verdict`` shows the verdict derived for the
        whole book. Exchange registers and publishes
        nothing as session news: exchanges and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every exchange held for the session is
        journaled as a exchange_exchange session event,
        every view as a exchange_view session event,
        every derived panel as a samverkbridge_panel
        session event and every derived verdict as a
        samverkbridge_verdict session event. This heading
        builds no repo, executes nothing and banks
        nothing - holding and telling are words only.
        """
        from ..core.samverk_bridge import (
            format_exchange,
            format_book,
            format_stage,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_exchange_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_exchange_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "exchange":
                text = format_exchange(
                    primary.get_samverkbridge_exchange(target),
                    primary.samverkbridge_book())
            elif stance == "stage":
                text = format_stage(
                    primary.samverkbridge_book(), target)
            elif stance == "repo":
                text = format_book(
                    primary.samverkbridge_book(), target)
            elif stance == "view":
                text = format_view(primary.get_samverkbridge_view(target))
            elif stance == "note":
                text = format_note(
                    primary.samverkbridge_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.samverkbridge_book())
            elif stance == "panel":
                text = format_panel(primary.samverkbridge_book())
            elif stance == "verdict":
                text = format_verdict(primary.samverkbridge_book())
            else:
                text = primary.samverkbridge_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_samtalbridge(self, args: str):
        """M-243: /samtalbridge - the dispatch engine as data.

        ``/samtalbridge`` shows the dispatch book held this
        session - dispatch halls as data: one record per
        dispatch, held whole with the active hall it
        was held from, its one verifiable stage
        at the house grain and its claims, and
        the notes held as data beside them (the shipped
        example book - five dispatches at the M-203 hall
        hall, with its three hall references, its
        two views, two stance records, one trace
        trace and its one pinned panel - when none
        is held yet); ``/samtalbridge dispatch <dispatch-id>``
        shows one dispatch whole; ``/samtalbridge stage
        <stage>`` shows the dispatch one stage line
        reaches, or names the stage unheld;
        ``/samtalbridge hall <hall-id>`` shows the book's
        dispatches of one hall; ``/samtalbridge view <view-id>``
        shows one held view record; ``/samtalbridge note
        <note-id>`` shows one held stance record;
        ``/samtalbridge index`` shows the index derived
        from the whole book's held dispatches; ``/samtalbridge
        panel`` shows the panel derived from the
        whole book under its default view; ``/samtalbridge
        verdict`` shows the verdict derived for the
        whole book. Dispatch registers and publishes
        nothing as session news: dispatches and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every dispatch held for the session is
        journaled as a dispatch_dispatch session event,
        every view as a dispatch_view session event,
        every derived panel as a samtalbridge_panel
        session event and every derived verdict as a
        samtalbridge_verdict session event. This heading
        builds no hall, executes nothing and banks
        nothing - holding and telling are words only.
        """
        from ..core.samtal_bridge import (
            format_dispatch,
            format_book,
            format_stage,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_dispatch_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_dispatch_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "dispatch":
                text = format_dispatch(
                    primary.get_samtalbridge_dispatch(target),
                    primary.samtalbridge_book())
            elif stance == "stage":
                text = format_stage(
                    primary.samtalbridge_book(), target)
            elif stance == "hall":
                text = format_book(
                    primary.samtalbridge_book(), target)
            elif stance == "view":
                text = format_view(primary.get_samtalbridge_view(target))
            elif stance == "note":
                text = format_note(
                    primary.samtalbridge_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.samtalbridge_book())
            elif stance == "panel":
                text = format_panel(primary.samtalbridge_book())
            elif stance == "verdict":
                text = format_verdict(primary.samtalbridge_book())
            else:
                text = primary.samtalbridge_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_kistakeykeeper(self, args: str):
        """M-244: /kistakeykeeper - the resolution engine as data.

        ``/kistakeykeeper`` shows the resolution book held this
        session - resolution bridges as data: one record per
        resolution, held whole with the active bridge it
        was held from, its one verifiable stage
        at the house grain and its claims, and
        the notes held as data beside them (the shipped
        example book - five resolutions at the M-203 bridge
        bridge, with its three bridge references, its
        two views, two stance records, one trace
        trace and its one pinned panel - when none
        is held yet); ``/kistakeykeeper resolution <resolution-id>``
        shows one resolution whole; ``/kistakeykeeper stage
        <stage>`` shows the resolution one stage line
        reaches, or names the stage unheld;
        ``/kistakeykeeper bridge <bridge-id>`` shows the book's
        resolutions of one bridge; ``/kistakeykeeper view <view-id>``
        shows one held view record; ``/kistakeykeeper note
        <note-id>`` shows one held stance record;
        ``/kistakeykeeper index`` shows the index derived
        from the whole book's held resolutions; ``/kistakeykeeper
        panel`` shows the panel derived from the
        whole book under its default view; ``/kistakeykeeper
        verdict`` shows the verdict derived for the
        whole book. Resolution registers and publishes
        nothing as session news: resolutions and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every resolution held for the session is
        journaled as a resolution_resolution session event,
        every view as a resolution_view session event,
        every derived panel as a kistakeykeeper_panel
        session event and every derived verdict as a
        kistakeykeeper_verdict session event. This heading
        builds no bridge, executes nothing and banks
        nothing - holding and telling are words only.
        """
        from ..core.kista_keykeeper import (
            format_resolution,
            format_book,
            format_stage,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_resolution_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_resolution_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "resolution":
                text = format_resolution(
                    primary.get_kistakeykeeper_resolution(target),
                    primary.kistakeykeeper_book())
            elif stance == "stage":
                text = format_stage(
                    primary.kistakeykeeper_book(), target)
            elif stance == "bridge":
                text = format_book(
                    primary.kistakeykeeper_book(), target)
            elif stance == "view":
                text = format_view(primary.get_kistakeykeeper_view(target))
            elif stance == "note":
                text = format_note(
                    primary.kistakeykeeper_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.kistakeykeeper_book())
            elif stance == "panel":
                text = format_panel(primary.kistakeykeeper_book())
            elif stance == "verdict":
                text = format_verdict(primary.kistakeykeeper_book())
            else:
                text = primary.kistakeykeeper_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_aesirdeepening(self, args: str):
        """M-245: /aesirdeepening - the deepening as data.

        ``/aesirdeepening`` shows the deepening held this
        session - Aesir's per-role selections as data:
        one record per crew office, naming whether an
        Aesir session is selectable for that role and
        why, beside the capability report held this
        session (the shipped selection book - nine
        offices, six selected - when none is held yet);
        ``/aesirdeepening report`` shows the held
        report, or the silent report while none stands;
        ``/aesirdeepening selections`` shows the whole
        book; ``/aesirdeepening selection <office>``
        shows one office's selection;
        ``/aesirdeepening ask <office> [needs...]
        [model:<name>]`` shows the ask derived for one
        office - never shaped for an unselected office
        or a silent server; ``/aesirdeepening index``
        shows the index derived from the whole book;
        ``/aesirdeepening verdict`` shows the verdict
        derived for the session. Resolution registers
        and publishes nothing as session news on this
        heading: reports and selections are held only
        when they are given through the agent's register
        roads, stood on the book on the viewing road, or
        held on the book roads, and every report held
        for the session is journaled as an
        aesirdeepening_report session event, every
        selection as an aesirdeepening_selection session
        event and every viewed ask as an
        aesirdeepening_ask session event. This heading
        opens no session, calls no model, probes no
        server and rewrites no route - holding and
        telling are words only.
        """
        from ..core.aesir_deepening import (
            format_ask,
            format_selection,
            format_selections,
        )
        from .llm import parse_aesirdeepening_args
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target, needs, model = (
                parse_aesirdeepening_args(args))
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "report":
                text = primary.aesirdeepening_status()[
                    "report_text"]
            elif stance == "selections":
                text = format_selections(
                    primary.aesirdeepening_book())
            elif stance == "selection":
                text = format_selection(
                    primary.get_aesirdeepening_selection(target))
            elif stance == "ask":
                text = format_ask(primary.aesirdeepening_ask(
                    target, needs=needs, model=model))
            elif stance == "index":
                text = primary.aesirdeepening_index()[
                    "index_text"]
            elif stance == "verdict":
                text = primary.aesirdeepening_verdict()[
                    "verdict_text"]
            else:
                text = primary.aesirdeepening_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")

    def _handle_githostparity(self, args: str):
        """M-246: /githostparity - the parity as data.

        ``/githostparity`` shows the parity held this
        session - the forge's git hosts as registry
        entries like providers: one entry per host,
        naming the word that host gives the request
        craft, beside the parity records held this
        session (no record held yet when none is held -
        parity is never claimed without held evidence);
        ``/githostparity hosts`` shows the whole shipped
        host registry; ``/githostparity host <host>``
        shows one host's registry entry;
        ``/githostparity record <host>`` shows the parity
        record held for one host; ``/githostparity
        standing <host>`` shows the standing derived for
        one host - held only on a full legal walk
        resting on held evidence, otherwise open, naming
        its gaps; ``/githostparity index`` shows the
        index derived over every host;
        ``/githostparity verdict`` shows the verdict
        derived for the session. Resolution registers
        and publishes nothing as session news on this
        heading: records are held only when they are
        given through the agent's register roads, stood
        on the book on the viewing road, or held on the
        book roads, and every record held for the
        session is journaled as a githostparity_record
        session event and every viewed standing as a
        githostparity_standing session event. This
        heading calls no host API, clones nothing,
        pushes nothing and probes no network - holding
        and telling are words only.
        """
        from ..core.git_host_parity import (
            format_host,
            format_hosts,
            format_parity,
        )
        from .llm import parse_githostparity_args
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target, needs, model = (
                parse_githostparity_args(args))
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "hosts":
                text = format_hosts(
                    primary.githostparity_hosts())
            elif stance == "host":
                text = format_host(
                    primary.get_githostparity_host(target))
            elif stance == "record":
                text = format_parity(
                    primary.get_githostparity_record(target))
            elif stance == "standing":
                standing = primary.githostparity_standing(
                    target)
                text = (
                    f"{standing.host}: parity "
                    f"{standing.standing} (stage: "
                    f"{standing.stage or 'none'})")
                for gap in standing.gaps:
                    text += f"\n  gap: {gap}"
            elif stance == "index":
                text = primary.githostparity_index()[
                    "index_text"]
            elif stance == "verdict":
                text = primary.githostparity_verdict()[
                    "verdict_text"]
            else:
                text = primary.githostparity_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")
    def _handle_cibridges(self, args: str):
        """M-247: /cibridges - the CI bridges as data.

        ``/cibridges`` shows the bridges held this
        session - the CI providers as registry entries:
        one entry per provider, naming the word that
        provider gives a single run, beside the run
        records held this session (no record held yet
        when none is held - a CI result is a fact only
        when it rests on held evidence); ``/cibridges
        providers`` shows the whole shipped provider
        registry; ``/cibridges provider <provider>``
        shows one provider's registry entry;
        ``/cibridges record <provider> <workflow>``
        shows the run record held for one provider and
        workflow; ``/cibridges standing <provider>
        <workflow>`` shows the standing derived for one
        run - held only on a full legal walk resting on
        held evidence, otherwise open, naming its gaps;
        ``/cibridges draft`` shows the workflow drafts
        held this session and ``/cibridges draft
        <provider> <workflow>`` shows one draft - a
        draft is never applied here, and on Volmarr's
        repos it dispatches manually by default;
        ``/cibridges index`` shows the index derived
        over every held record; ``/cibridges verdict``
        shows the verdict derived for the session.
        Resolution registers and publishes nothing as
        session news on this heading: records are held
        only when they are given through the agent's
        register roads, stood on the book on the viewing
        road, or held on the book roads, and every record
        held for the session is journaled as a
        cibridges_record session event, every viewed
        standing as a cibridges_standing session event
        and every proposed draft as a cibridges_draft
        session event. This heading calls no CI API,
        fetches no run, changes no workflow and probes
        no network - holding and telling are words only.
        """
        from ..core.ci_bridges import (
            format_provider,
            format_providers,
            format_record,
        )
        from .llm import parse_cibridges_args
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target, needs, model = (
                parse_cibridges_args(args))
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "providers":
                text = format_providers(
                    primary.cibridges_providers())
            elif stance == "provider":
                text = format_provider(
                    primary.get_cibridges_provider(target))
            elif stance == "record":
                text = format_record(
                    primary.get_cibridges_record(*target))
            elif stance == "standing":
                standing = primary.cibridges_standing(
                    *target)
                text = (
                    f"{target[0]}/{target[1]}: CI "
                    f"{'held as fact' if standing.held else 'open'} "
                    f"(stage: {standing.stage})")
                for gap in standing.gaps:
                    text += f"\n  gap: {gap}"
            elif stance == "drafts":
                drafts = primary.cibridges_drafts()
                if not drafts:
                    text = (
                        "Workflow drafts: none held this "
                        "session - workflow changes are "
                        "proposed only as drafts, and a "
                        "draft is never applied here.")
                else:
                    text = "\n".join(
                        f"{d.provider}/{d.workflow}: draft - "
                        f"{d.change} (trigger: {d.trigger}; "
                        "a draft is never applied here)"
                        for d in drafts)
            elif stance == "draft":
                d = primary.get_cibridges_draft(*target)
                text = (
                    f"{d.provider}/{d.workflow}: draft - "
                    f"{d.change} (trigger: {d.trigger}; "
                    "a draft is never applied here)")
            elif stance == "index":
                text = primary.cibridges_index()[
                    "index_text"]
            elif stance == "verdict":
                text = primary.cibridges_verdict()[
                    "verdict_text"]
            else:
                text = primary.cibridges_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")
    def _handle_issuetrackers(self, args: str):
        """M-248: /issuetrackers - the issue trackers as data.

        ``/issuetrackers`` shows the bridges held this
        session - the issue trackers as registry entries:
        one entry per tracker, naming the word that
        tracker gives a single issue, beside the issue
        records held this session (no record held yet
        when none is held - an issue is a fact only
        when it rests on held evidence); ``/issuetrackers
        trackers`` shows the whole shipped tracker
        registry; ``/issuetrackers tracker <tracker>``
        shows one tracker's registry entry;
        ``/issuetrackers record <tracker> <issue_key>``
        shows the run record held for one tracker and
        issue_key; ``/issuetrackers standing <tracker>
        <issue_key>`` shows the standing derived for one
        issue - held only on a full legal walk resting on
        held evidence, otherwise open, naming its gaps;
        ``/issuetrackers draft`` shows the write drafts
        held this session and ``/issuetrackers draft
        <tracker> <issue_key>`` shows one draft - a
        draft is never applied here, and on Volmarr's
        repos it stands at approval pending by default;
        ``/issuetrackers index`` shows the index derived
        over every held record; ``/issuetrackers verdict``
        shows the verdict derived for the session.
        Resolution registers and publishes nothing as
        session news on this heading: records are held
        only when they are given through the agent's
        register roads, stood on the book on the viewing
        road, or held on the book roads, and every record
        held for the session is journaled as a
        issuetrackers_record session event, every viewed
        standing as a issuetrackers_standing session event
        and every proposed draft as a issuetrackers_draft
        session event. This heading calls no tracker API,
        fetches no issue, writes nothing to any tracker and probes
        no network - holding and telling are words only.
        """
        from ..core.issue_trackers import (
            format_tracker,
            format_trackers,
            format_record,
        )
        from .llm import parse_issuetrackers_args
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target, needs, model = (
                parse_issuetrackers_args(args))
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "trackers":
                text = format_trackers(
                    primary.issuetrackers_trackers())
            elif stance == "tracker":
                text = format_tracker(
                    primary.get_issuetrackers_tracker(target))
            elif stance == "record":
                text = format_record(
                    primary.get_issuetrackers_record(*target))
            elif stance == "standing":
                standing = primary.issuetrackers_standing(
                    *target)
                text = (
                    f"{target[0]}/{target[1]}: issue "
                    f"{'held as fact' if standing.held else 'open'} "
                    f"(stage: {standing.stage})")
                for gap in standing.gaps:
                    text += f"\n  gap: {gap}"
            elif stance == "drafts":
                drafts = primary.issuetrackers_drafts()
                if not drafts:
                    text = (
                        "Write drafts: none held this "
                        "session - tracker writes are "
                        "proposed only as drafts, and a "
                        "draft is never applied here.")
                else:
                    text = "\n".join(
                        f"{d.tracker}/{d.issue_key}: draft - "
                        f"{d.change} (approval: {d.approval}; "
                        "a draft is never applied here)"
                        for d in drafts)
            elif stance == "draft":
                d = primary.get_issuetrackers_draft(*target)
                text = (
                    f"{d.tracker}/{d.issue_key}: draft - "
                    f"{d.change} (approval: {d.approval}; "
                    "a draft is never applied here)")
            elif stance == "index":
                text = primary.issuetrackers_index()[
                    "index_text"]
            elif stance == "verdict":
                text = primary.issuetrackers_verdict()[
                    "verdict_text"]
            else:
                text = primary.issuetrackers_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")
    def _handle_wyrdseam(self, args: str):
        """M-249: /wyrdseam - the WYRD seam as data.

        ``/wyrdseam`` shows the seam held this session -
        the world-state sources as registry entries: one
        entry per source, naming the word that source
        gives a single telling, beside the node snapshots
        held this session (no snapshot recorded yet when
        none is held - world-state is current only when a
        fresh snapshot rests on held evidence);
        ``/wyrdseam sources`` shows the whole shipped
        source registry; ``/wyrdseam source <source>``
        shows one source's registry entry; ``/wyrdseam
        snapshot <source> <node>`` shows the snapshot held
        for one source and node; ``/wyrdseam standing
        <source> <node>`` shows the standing derived for
        one node - held only on a full legal walk resting
        on held evidence within the fresh limit, otherwise
        open, naming its gaps; ``/wyrdseam advice`` shows
        the campaign advice held this session and
        ``/wyrdseam advice <campaign>`` shows one advice
        draft - advice is never applied here and no
        campaign is rerouted on this road; ``/wyrdseam
        index`` shows the index derived over every held
        snapshot; ``/wyrdseam verdict`` shows the verdict
        derived for the session. Resolution registers and
        publishes nothing as session news on this heading:
        snapshots are held only when they are given
        through the agent's register roads, stood on the
        book on the viewing road, or held on the book
        roads, and every snapshot held for the session is
        journaled as a wyrdseam_snapshot session event,
        every viewed standing as a wyrdseam_standing
        session event and every proposed advice draft as
        a wyrdseam_advice session event. This heading
        calls no WYRD engine API, probes no machine,
        measures no load and reroutes no campaign -
        holding and telling are words only.
        """
        from ..core.wyrd_seam import (
            format_snapshot,
            format_source,
            format_sources,
        )
        from .llm import parse_wyrdseam_args
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target, needs, model = (
                parse_wyrdseam_args(args))
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "sources":
                text = format_sources(
                    primary.wyrdseam_sources())
            elif stance == "source":
                text = format_source(
                    primary.get_wyrdseam_source(target))
            elif stance == "snapshot":
                text = format_snapshot(
                    primary.get_wyrdseam_snapshot(*target))
            elif stance == "standing":
                standing = primary.wyrdseam_standing(
                    *target)
                text = (
                    f"{target[0]}/{target[1]}: world-state "
                    f"{'current as recorded' if standing.held else 'open'} "
                    f"(stage: {standing.stage}; "
                    f"freshness: {standing.freshness})")
                for gap in standing.gaps:
                    text += f"\n  gap: {gap}"
            elif stance == "advices":
                drafts = primary.wyrdseam_advices()
                if not drafts:
                    text = (
                        "Campaign advice: none held this "
                        "session - the seam proposes campaign "
                        "moves only as advice, and advice is "
                        "never applied here.")
                else:
                    text = "\n".join(
                        f"{d.campaign} -> {d.node}: advice - "
                        f"{d.advice} (approval: {d.approval}; "
                        "advice is never applied here)"
                        for d in drafts)
            elif stance == "advice":
                d = primary.get_wyrdseam_advice(target)
                text = (
                    f"{d.campaign} -> {d.node}: advice - "
                    f"{d.advice} (approval: {d.approval}; "
                    "advice is never applied here)")
            elif stance == "index":
                text = primary.wyrdseam_index()[
                    "index_text"]
            elif stance == "verdict":
                text = primary.wyrdseam_verdict()[
                    "verdict_text"]
            else:
                text = primary.wyrdseam_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")
    def _handle_webhookdoors(self, args: str):
        """M-250: /webhookdoors - the webhook doors as data.

        ``/webhookdoors`` shows the doors held this session -
        the webhook sources as registry entries: one
        entry per source, naming the word that source
        gives a single telling, beside the event events
        held this session (no event recorded yet when
        none is held - webhook is current only when a
        fresh event rests on held evidence);
        ``/webhookdoors sources`` shows the whole shipped
        source registry; ``/webhookdoors source <source>``
        shows one source's registry entry; ``/webhookdoors
        event <source> <event>`` shows the event held
        for one source and event; ``/webhookdoors standing
        <source> <event>`` shows the standing derived for
        one event - held only on a full legal walk resting
        on held evidence within the fresh limit, otherwise
        open, naming its gaps; ``/webhookdoors propose`` shows
        the campaign proposal held this session and
        ``/webhookdoors propose <campaign>`` shows one proposal
        draft - proposal is never applied here and no
        campaign is built unbidden on this road; ``/webhookdoors
        index`` shows the index derived over every held
        event; ``/webhookdoors verdict`` shows the verdict
        derived for the session. Resolution registers and
        publishes nothing as session news on this heading:
        events are held only when they are given
        through the agent's register roads, stood on the
        book on the viewing road, or held on the book
        roads, and every event held for the session is
        journaled as a webhookdoors_event session event,
        every viewed standing as a webhookdoors_standing
        session event and every proposed proposal draft as
        a webhookdoors_proposal session event. This heading
        calls no host API, opens no listener,
        starts nothing and builds nothing unbidden -
        holding and telling are words only.
        """
        from ..core.webhook_doors import (
            format_event,
            format_source,
            format_sources,
        )
        from .llm import parse_webhookdoors_args
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target, needs, model = (
                parse_webhookdoors_args(args))
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "sources":
                text = format_sources(
                    primary.webhookdoors_sources())
            elif stance == "source":
                text = format_source(
                    primary.get_webhookdoors_source(target))
            elif stance == "event":
                text = format_event(
                    primary.get_webhookdoors_event(*target))
            elif stance == "standing":
                standing = primary.webhookdoors_standing(
                    *target)
                text = (
                    f"{target[0]}/{target[1]}: webhook "
                    f"{'held as recorded' if standing.held else 'open'} "
                    f"(stage: {standing.stage}; "
                    f"freshness: {standing.freshness})")
                for gap in standing.gaps:
                    text += f"\n  gap: {gap}"
            elif stance == "proposals":
                drafts = primary.webhookdoors_proposals()
                if not drafts:
                    text = (
                        "Campaign proposal: none held this "
                        "session - the doors propose campaign "
                        "moves only as proposals, and a proposal is "
                        "never applied here.")
                else:
                    text = "\n".join(
                        f"{d.campaign} -> {d.event}: proposal - "
                        f"{d.proposal} (approval: {d.approval}; "
                        "proposal is never applied here)"
                        for d in drafts)
            elif stance == "propose":
                d = primary.get_webhookdoors_proposal(target)
                text = (
                    f"{d.campaign} -> {d.event}: proposal - "
                    f"{d.proposal} (approval: {d.approval}; "
                    "proposal is never applied here)")
            elif stance == "index":
                text = primary.webhookdoors_index()[
                    "index_text"]
            elif stance == "verdict":
                text = primary.webhookdoors_verdict()[
                    "verdict_text"]
            else:
                text = primary.webhookdoors_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")
    def _handle_exporteverything(self, args: str):
        """M-251: /exporteverything - the export everything as data.

        ``/exporteverything`` shows the doors held this session -
        the export kinds as registry entries: one
        entry per kind, naming the word that kind
        gives a single telling, beside the record records
        held this session (no record recorded yet when
        none is held - export is current only when a
        fresh record rests on held evidence);
        ``/exporteverything kinds`` shows the whole shipped
        kind registry; ``/exporteverything kind <kind>``
        shows one kind's registry entry; ``/exporteverything
        record <kind> <record>`` shows the record held
        for one kind and record; ``/exporteverything standing
        <kind> <record>`` shows the standing derived for
        one record - held only on a full legal walk resting
        on held evidence within the fresh limit, otherwise
        open, naming its gaps; ``/exporteverything prepare`` shows
        the bundle draft held this session and
        ``/exporteverything prepare <bundle>`` shows one draft
        draft - draft is never exported here and no
        bundle is exported here on this road; ``/exporteverything
        index`` shows the index derived over every held
        record; ``/exporteverything verdict`` shows the verdict
        derived for the session. Resolution registers and
        publishes nothing as session news on this heading:
        records are held only when they are given
        through the agent's register roads, stood on the
        book on the viewing road, or held on the book
        roads, and every record held for the session is
        journaled as a exporteverything_record session record,
        every viewed standing as a exporteverything_standing
        session record and every prepared draft draft as
        a exporteverything_draft session record. This heading
        calls no host API, performs no export,
        starts nothing and exports nothing here -
        holding and telling are words only.
        """
        from ..core.export_everything import (
            format_record,
            format_kind,
            format_kinds,
        )
        from .llm import parse_exporteverything_args
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target, needs, model = (
                parse_exporteverything_args(args))
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "kinds":
                text = format_kinds(
                    primary.exporteverything_kinds())
            elif stance == "kind":
                text = format_kind(
                    primary.get_exporteverything_kind(target))
            elif stance == "record":
                text = format_record(
                    primary.get_exporteverything_record(*target))
            elif stance == "standing":
                standing = primary.exporteverything_standing(
                    *target)
                text = (
                    f"{target[0]}/{target[1]}: export "
                    f"{'held as open' if standing.held else 'open'} "
                    f"(stage: {standing.stage}; "
                    f"freshness: {standing.freshness})")
                for gap in standing.gaps:
                    text += f"\n  gap: {gap}"
            elif stance == "drafts":
                drafts = primary.exporteverything_drafts()
                if not drafts:
                    text = (
                        "Bundle draft: none held this "
                        "session - the doors prepare bundle "
                        "moves only as drafts, and a draft is "
                        "never exported here.")
                else:
                    text = "\n".join(
                        f"{d.bundle} -> {d.record}: draft - "
                        f"{d.draft} (state: {d.state}; "
                        "draft is never exported here)"
                        for d in drafts)
            elif stance == "prepare":
                d = primary.get_exporteverything_draft(target)
                text = (
                    f"{d.bundle} -> {d.record}: draft - "
                    f"{d.draft} (state: {d.state}; "
                    "draft is never exported here)")
            elif stance == "index":
                text = primary.exporteverything_index()[
                    "index_text"]
            elif stance == "verdict":
                text = primary.exporteverything_verdict()[
                    "verdict_text"]
            else:
                text = primary.exporteverything_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")
    def _handle_bridgeaudit(self, args: str):
        """M-253: /bridgeaudit - the bridge permissions audit as data.

        ``/bridgeaudit`` shows the doors held this session -
        the export bridges as registry entries: one
        entry per bridge, naming the word that bridge
        gives a single telling, beside the record records
        held this session (no record recorded yet when
        none is held - export is current only when a
        fresh record rests on held evidence);
        ``/bridgeaudit bridges`` shows the whole shipped
        bridge registry; ``/bridgeaudit bridge <bridge>``
        shows one bridge's registry entry; ``/bridgeaudit
        record <bridge> <record>`` shows the record held
        for one bridge and record; ``/bridgeaudit standing
        <bridge> <record>`` shows the standing derived for
        one record - held only on a full legal walk resting
        on held evidence within the fresh limit, otherwise
        open, naming its gaps; ``/bridgeaudit report`` shows
        the bridge report held this session and
        ``/bridgeaudit report <bridge>`` shows one report
        report - report is never a grant here and no
        bridge is granted here on this road; ``/bridgeaudit
        index`` shows the index derived over every held
        record; ``/bridgeaudit verdict`` shows the verdict
        derived for the session. Resolution registers and
        publishes nothing as session news on this heading:
        records are held only when they are given
        through the agent's register roads, stood on the
        book on the viewing road, or held on the book
        roads, and every record held for the session is
        journaled as a bridgeaudit_record session record,
        every viewed standing as a bridgeaudit_standing
        session record and every reportd report report as
        a bridgeaudit_report session record. This heading
        calls no host API, performs no export,
        starts nothing and exports nothing here -
        holding and telling are words only.
        """
        from ..core.bridge_permissions import (
            format_record,
            format_bridge,
            format_bridges,
        )
        from .llm import parse_bridgeaudit_args
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target, needs, model = (
                parse_bridgeaudit_args(args))
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "bridges":
                text = format_bridges(
                    primary.bridgeaudit_bridges())
            elif stance == "bridge":
                text = format_bridge(
                    primary.get_bridgeaudit_bridge(target))
            elif stance == "record":
                text = format_record(
                    primary.get_bridgeaudit_record(*target))
            elif stance == "standing":
                standing = primary.bridgeaudit_standing(
                    *target)
                text = (
                    f"{target[0]}/{target[1]}: audit "
                    f"{'held as audited' if standing.held else 'open'} "
                    f"(stage: {standing.stage}; "
                    f"freshness: {standing.freshness})")
                for gap in standing.gaps:
                    text += f"\n  gap: {gap}"
            elif stance == "reports":
                reports = primary.bridgeaudit_reports()
                if not reports:
                    text = (
                        "Bridge report: none held this "
                        "session - the doors report bridge "
                        "moves only as reports, and a report is "
                        "never a grant here.")
                else:
                    text = "\n".join(
                        f"{d.bridge} -> {d.record}: report - "
                        f"{d.report} (state: {d.state}; "
                        "report is never a grant here)"
                        for d in reports)
            elif stance == "report":
                d = primary.get_bridgeaudit_report(target)
                text = (
                    f"{d.bridge} -> {d.record}: report - "
                    f"{d.report} (state: {d.state}; "
                    "report is never a grant here)")
            elif stance == "index":
                text = primary.bridgeaudit_index()[
                    "index_text"]
            elif stance == "verdict":
                text = primary.bridgeaudit_verdict()[
                    "verdict_text"]
            else:
                text = primary.bridgeaudit_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_benchmarkharness(self, args: str):
        """M-255: /benchmarkharness - the benchmark harness as data.

        ``/benchmarkharness`` shows the harness held this session -
        the run kinds as registry entries: one
        entry per kind, naming the word that kind
        gives a single run, beside the run records
        held this session (no run recorded yet when
        none is held - a run is passed only when a
        graded run rests on held evidence);
        ``/benchmarkharness kinds`` shows the whole shipped
        harness registry; ``/benchmarkharness kind <kind>``
        shows one kind's registry entry; ``/benchmarkharness
        record <kind> <run>`` shows the record held
        for one kind and run; ``/benchmarkharness standing
        <kind> <run>`` shows the standing derived for
        one run - held only on a full legal walk resting
        on held evidence, with tests all passing and the
        rubric fully met, otherwise
        open, naming its gaps; ``/benchmarkharness report`` shows
        the run reports held this session and
        ``/benchmarkharness report <kind>`` shows one kind's
        report - a report is never inflated here and no
        run is graded here on this road; ``/benchmarkharness
        index`` shows the index derived over every held
        record; ``/benchmarkharness verdict`` shows the verdict
        derived for the session. Resolution registers and
        publishes nothing as session news on this heading:
        records are held only when they are given
        through the agent's register roads, stood on the
        book on the viewing road, or held on the book
        roads, and every record held for the session is
        journaled as a benchmarkharness_record session record,
        every viewed standing as a benchmarkharness_standing
        session record and every held report as
        a benchmarkharness_report session record. This heading
        runs no task, creates no sandbox,
        executes no grading test and inflates nothing here -
        holding and telling are words only.
        """
        from ..core.benchmark_harness import (
            format_record,
            format_kind,
            format_kinds,
        )
        from .llm import parse_benchmarkharness_args
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target, needs, model = (
                parse_benchmarkharness_args(args))
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "kinds":
                text = format_kinds(
                    primary.benchmarkharness_kinds())
            elif stance == "kind":
                text = format_kind(
                    primary.get_benchmarkharness_kind(target))
            elif stance == "record":
                text = format_record(
                    primary.get_benchmarkharness_record(*target))
            elif stance == "standing":
                standing = primary.benchmarkharness_standing(
                    *target)
                text = (
                    f"{target[0]}/{target[1]}: run "
                    f"{'passed as graded' if standing.held else 'open'} "
                    f"(stage: {standing.stage}; "
                    f"grade: {standing.grade})")
                for gap in standing.gaps:
                    text += f"\n  gap: {gap}"
            elif stance == "reports":
                reports = primary.benchmarkharness_reports()
                if not reports:
                    text = (
                        "Run report: none held this "
                        "session - the harness reports run "
                        "moves only as reports, and a report is "
                        "never inflated here.")
                else:
                    text = "\n".join(
                        f"{d.kind} -> {d.run}: report - "
                        f"{d.report} (state: {d.state}; "
                        "report is never inflated here)"
                        for d in reports)
            elif stance == "report":
                d = primary.get_benchmarkharness_report(target)
                text = (
                    f"{d.kind} -> {d.run}: report - "
                    f"{d.report} (state: {d.state}; "
                    "report is never inflated here)")
            elif stance == "index":
                text = primary.benchmarkharness_index()[
                    "index_text"]
            elif stance == "verdict":
                text = primary.benchmarkharness_verdict()[
                    "verdict_text"]
            else:
                text = primary.benchmarkharness_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")


    def _handle_publishedyardstick(self, args: str):
        """M-256: /publishedyardstick - the published yardsticks as data.

        ``/publishedyardstick`` shows the yardsticks held this session -
        the public sets as registry entries: one
        entry per set, naming the word that set
        gives a single run and the standing of its
        licence, beside the run records
        held this session (no run recorded yet when
        none is held - a run is held only when a
        reported run rests on held licence evidence);
        ``/publishedyardstick yardsticks`` shows the whole shipped
        yardstick registry; ``/publishedyardstick yardstick <yardstick>``
        shows one yardstick's registry entry; ``/publishedyardstick
        record <yardstick> <run>`` shows the record held
        for one yardstick and run; ``/publishedyardstick standing
        <yardstick> <run>`` shows the standing derived for
        one run - held only on a full legal walk resting
        on held licence evidence, with the report carrying
        model, cost and date together, otherwise
        open, naming its gaps; ``/publishedyardstick report`` shows
        the run reports held this session and
        ``/publishedyardstick report <yardstick>`` shows one yardstick's
        report - a report is never inflated here and no
        run is graded here on this road; ``/publishedyardstick
        index`` shows the index derived over every held
        record; ``/publishedyardstick verdict`` shows the verdict
        derived for the session. Resolution registers and
        publishes nothing as session news on this heading:
        records are held only when they are given
        through the agent's register roads, stood on the
        book on the viewing road, or held on the book
        roads, and every record held for the session is
        journaled as a publishedyardstick_record session record,
        every viewed standing as a publishedyardstick_standing
        session record and every held report as
        a publishedyardstick_report session record. This heading
        runs no benchmark, downloads no set,
        executes no grading test and inflates nothing here -
        holding and telling are words only.
        """
        from ..core.published_yardstick import (
            format_record,
            format_yardstick,
            format_yardsticks,
        )
        from .llm import parse_publishedyardstick_args
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target, needs, model = (
                parse_publishedyardstick_args(args))
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "yardsticks":
                text = format_yardsticks(
                    primary.publishedyardstick_yardsticks())
            elif stance == "yardstick":
                text = format_yardstick(
                    primary.get_publishedyardstick_yardstick(target))
            elif stance == "record":
                text = format_record(
                    primary.get_publishedyardstick_record(*target))
            elif stance == "standing":
                standing = primary.publishedyardstick_standing(
                    *target)
                text = (
                    f"{target[0]}/{target[1]}: run "
                    f"{'held as reported' if standing.held else 'open'} "
                    f"(stage: {standing.stage}; "
                    f"grade: {standing.grade})")
                for gap in standing.gaps:
                    text += f"\n  gap: {gap}"
            elif stance == "reports":
                reports = primary.publishedyardstick_reports()
                if not reports:
                    text = (
                        "Run report: none held this "
                        "session - the yardsticks report run "
                        "moves only as reports, and a report is "
                        "never inflated here.")
                else:
                    text = "\n".join(
                        f"{d.yardstick} -> {d.run}: report - "
                        f"{d.report} (state: {d.state}; "
                        "report is never inflated here)"
                        for d in reports)
            elif stance == "report":
                d = primary.get_publishedyardstick_report(target)
                text = (
                    f"{d.yardstick} -> {d.run}: report - "
                    f"{d.report} (state: {d.state}; "
                    "report is never inflated here)")
            elif stance == "index":
                text = primary.publishedyardstick_index()[
                    "index_text"]
            elif stance == "verdict":
                text = primary.publishedyardstick_verdict()[
                    "verdict_text"]
            else:
                text = primary.publishedyardstick_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")
    def _handle_regressioncourt(self, args: str):
        """M-257: /regressioncourt - the regression court as data.

        ``/regressioncourt`` shows the parts held this session -
        the public sets as registry entries: one
        entry per set, naming the word that set
        gives a single run and the standing of its
        gate, beside the run records
        held this session (no run recorded yet when
        none is held - a run is held only when a
        reported run rests on held gate evidence);
        ``/regressioncourt parts`` shows the whole shipped
        part registry; ``/regressioncourt part <part>``
        shows one part's registry entry; ``/regressioncourt
        record <part> <run>`` shows the record held
        for one part and run; ``/regressioncourt standing
        <part> <run>`` shows the standing derived for
        one run - held only on a full legal walk resting
        on held gate evidence, with the verdict carrying
        model, cost and date together, otherwise
        open, naming its gaps; ``/regressioncourt verdict`` shows
        the run verdicts held this session and
        ``/regressioncourt verdict <part>`` shows one part's
        verdict - a verdict is never inflated here and no
        run is graded here on this road; ``/regressioncourt
        index`` shows the index derived over every held
        record; ``/regressioncourt verdict`` shows the verdict
        derived for the session. Resolution registers and
        publishes nothing as session news on this heading:
        records are held only when they are given
        through the agent's register roads, stood on the
        book on the viewing road, or held on the book
        roads, and every record held for the session is
        journaled as a regressioncourt_record session record,
        every viewed standing as a regressioncourt_standing
        session record and every held verdict as
        a regressioncourt_verdict session record. This heading
        runs no benchmark, downloads no set,
        executes no grading test and inflates nothing here -
        holding and telling are words only.
        """
        from ..core.regression_court import (
            format_record,
            format_part,
            format_parts,
        )
        from .llm import parse_regressioncourt_args
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target, needs, model = (
                parse_regressioncourt_args(args))
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "parts":
                text = format_parts(
                    primary.regressioncourt_parts())
            elif stance == "part":
                text = format_part(
                    primary.get_regressioncourt_part(target))
            elif stance == "record":
                text = format_record(
                    primary.get_regressioncourt_record(*target))
            elif stance == "standing":
                standing = primary.regressioncourt_standing(
                    *target)
                text = (
                    f"{target[0]}/{target[1]}: run "
                    f"{'held as re-run' if standing.held else 'open'} "
                    f"(stage: {standing.stage}; "
                    f"grade: {standing.grade})")
                for gap in standing.gaps:
                    text += f"\n  gap: {gap}"
            elif stance == "drafts":
                verdicts = primary.regressioncourt_drafts()
                if not verdicts:
                    text = (
                        "Run verdict: none held this "
                        "session - the parts verdict run "
                        "moves only as verdicts, and a verdict is "
                        "never inflated here.")
                else:
                    text = "\n".join(
                        f"{d.battery} -> {d.entry}: verdict - "
                        f"{d.verdict} (state: {d.state}; "
                        "verdict is never inflated here)"
                        for d in verdicts)
            elif stance == "draft":
                d = primary.get_regressioncourt_draft(target)
                text = (
                    f"{d.battery} -> {d.entry}: verdict - "
                    f"{d.verdict} (state: {d.state}; "
                    "verdict is never inflated here)")
            elif stance == "index":
                text = primary.regressioncourt_index()[
                    "index_text"]
            elif stance == "verdict":
                text = primary.regressioncourt_verdict()[
                    "verdict_text"]
            else:
                text = primary.regressioncourt_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")
    def _handle_performancebudgets(self, args: str):
        """M-258: /performancebudgets - the performance budgets as data.

        ``/performancebudgets`` shows the measures held this session -
        the public sets as registry entries: one
        entry per set, naming the word that set
        gives a single run and the standing of its
        gate, beside the run records
        held this session (no run recorded yet when
        none is held - a run is held only when a
        reported run rests on held gate evidence);
        ``/performancebudgets measures`` shows the whole shipped
        measure registry; ``/performancebudgets measure <measure>``
        shows one measure's registry entry; ``/performancebudgets
        record <measure> <run>`` shows the record held
        for one measure and run; ``/performancebudgets standing
        <measure> <run>`` shows the standing derived for
        one run - held only on a full legal walk resting
        on held gate evidence, with the verdict carrying
        model, cost and date together, otherwise
        open, naming its gaps; ``/performancebudgets verdict`` shows
        the run verdicts held this session and
        ``/performancebudgets verdict <measure>`` shows one measure's
        verdict - a verdict is never inflated here and no
        run is graded here on this road; ``/performancebudgets
        index`` shows the index derived over every held
        record; ``/performancebudgets verdict`` shows the verdict
        derived for the session. Resolution registers and
        publishes nothing as session news on this heading:
        records are held only when they are given
        through the agent's register roads, stood on the
        book on the viewing road, or held on the book
        roads, and every record held for the session is
        journaled as a performancebudgets_record session record,
        every viewed standing as a performancebudgets_standing
        session record and every held verdict as
        a performancebudgets_verdict session record. This heading
        runs no benchmark, downloads no set,
        executes no grading test and inflates nothing here -
        holding and telling are words only.
        """
        from ..core.performance_budgets import (
            format_record,
            format_measure,
            format_measures,
        )
        from .llm import parse_performancebudgets_args
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target, needs, model = (
                parse_performancebudgets_args(args))
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "measures":
                text = format_measures(
                    primary.performancebudgets_measures())
            elif stance == "measure":
                text = format_measure(
                    primary.get_performancebudgets_measure(target))
            elif stance == "record":
                text = format_record(
                    primary.get_performancebudgets_record(*target))
            elif stance == "standing":
                standing = primary.performancebudgets_standing(
                    *target)
                text = (
                    f"{target[0]}/{target[1]}: run "
                    f"{'held as measured' if standing.held else 'open'} "
                    f"(stage: {standing.stage}; "
                    f"grade: {standing.grade})")
                for gap in standing.gaps:
                    text += f"\n  gap: {gap}"
            elif stance == "reports":
                verdicts = primary.performancebudgets_reports()
                if not verdicts:
                    text = (
                        "Run verdict: none held this "
                        "session - the measures verdict run "
                        "moves only as verdicts, and a verdict is "
                        "never inflated here.")
                else:
                    text = "\n".join(
                        f"{d.book} -> {d.entry}: verdict - "
                        f"{d.report} (state: {d.state}; "
                        "verdict is never inflated here)"
                        for d in verdicts)
            elif stance == "report":
                d = primary.get_performancebudgets_report(target)
                text = (
                    f"{d.book} -> {d.entry}: verdict - "
                    f"{d.report} (state: {d.state}; "
                    "verdict is never inflated here)")
            elif stance == "index":
                text = primary.performancebudgets_index()[
                    "index_text"]
            elif stance == "verdict":
                text = primary.performancebudgets_verdict()[
                    "verdict_text"]
            else:
                text = primary.performancebudgets_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")
    def _handle_platformmatrixfinal(self, args: str):
        """M-259: /platformmatrixfinal - the platform matrix final as data.

        ``/platformmatrixfinal`` shows the cells held this session -
        the public sets as registry entries: one
        entry per set, naming the word that set
        gives a single run and the standing of its
        gate, beside the run records
        held this session (no run recorded yet when
        none is held - a run is held only when a
        reported run rests on held gate evidence);
        ``/platformmatrixfinal cells`` shows the whole shipped
        cell registry; ``/platformmatrixfinal cell <cell>``
        shows one cell's registry entry; ``/platformmatrixfinal
        record <cell> <run>`` shows the record held
        for one cell and run; ``/platformmatrixfinal standing
        <cell> <run>`` shows the standing derived for
        one run - held only on a full legal walk resting
        on held gate evidence, with the verdict carrying
        model, cost and date together, otherwise
        open, naming its gaps; ``/platformmatrixfinal verdict`` shows
        the run verdicts held this session and
        ``/platformmatrixfinal verdict <cell>`` shows one cell's
        verdict - a verdict is never inflated here and no
        run is graded here on this road; ``/platformmatrixfinal
        index`` shows the index derived over every held
        record; ``/platformmatrixfinal verdict`` shows the verdict
        derived for the session. Resolution registers and
        publishes nothing as session news on this heading:
        records are held only when they are given
        through the agent's register roads, stood on the
        book on the viewing road, or held on the book
        roads, and every record held for the session is
        journaled as a platformmatrixfinal_record session record,
        every viewed standing as a platformmatrixfinal_standing
        session record and every held verdict as
        a platformmatrixfinal_verdict session record. This heading
        runs no benchmark, downloads no set,
        executes no grading test and inflates nothing here -
        holding and telling are words only.
        """
        from ..core.platform_matrix_final import (
            format_record,
            format_cell,
            format_cells,
        )
        from .llm import parse_platformmatrixfinal_args
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target, needs, model = (
                parse_platformmatrixfinal_args(args))
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "cells":
                text = format_cells(
                    primary.platformmatrixfinal_cells())
            elif stance == "cell":
                text = format_cell(
                    primary.get_platformmatrixfinal_cell(target))
            elif stance == "record":
                text = format_record(
                    primary.get_platformmatrixfinal_record(target))
            elif stance == "standing":
                standing = primary.platformmatrixfinal_standing(
                    target)
                text = (
                    f"{target}: "
                    f"{'held as answered' if standing.held else 'open'} "
                    f"(stage: {standing.stage}; "
                    f"grade: {standing.grade})")
                for gap in standing.gaps:
                    text += f"\n  gap: {gap}"
            elif stance == "reports":
                verdicts = primary.platformmatrixfinal_reports()
                if not verdicts:
                    text = (
                        "Run verdict: none held this "
                        "session - the cells verdict run "
                        "moves only as verdicts, and a verdict is "
                        "never inflated here.")
                else:
                    text = "\n".join(
                        f"{d.book} -> {d.entry}: verdict - "
                        f"{d.report} (state: {d.state}; "
                        "verdict is never inflated here)"
                        for d in verdicts)
            elif stance == "report":
                d = primary.get_platformmatrixfinal_report(target)
                text = (
                    f"{d.book} -> {d.entry}: verdict - "
                    f"{d.report} (state: {d.state}; "
                    "verdict is never inflated here)")
            elif stance == "index":
                text = primary.platformmatrixfinal_index()[
                    "index_text"]
            elif stance == "verdict":
                text = primary.platformmatrixfinal_verdict()[
                    "verdict_text"]
            else:
                text = primary.platformmatrixfinal_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")
    def _handle_securityaudit(self, args: str):
        """M-260: /securityaudit - the security audit as data.

        ``/securityaudit`` shows the areas held this session -
        the public sets as registry entries: one
        entry per set, naming the word that set
        gives a single run and the standing of its
        gate, beside the run records
        held this session (no run recorded yet when
        none is held - a run is held only when a
        reported run rests on held gate evidence);
        ``/securityaudit areas`` shows the whole shipped
        area registry; ``/securityaudit area <area>``
        shows one area's registry entry; ``/securityaudit
        record <area> <run>`` shows the record held
        for one area and run; ``/securityaudit standing
        <area> <run>`` shows the standing derived for
        one run - held only on a full legal walk resting
        on held gate evidence, with the verdict carrying
        model, cost and date together, otherwise
        open, naming its gaps; ``/securityaudit verdict`` shows
        the run verdicts held this session and
        ``/securityaudit verdict <area>`` shows one area's
        verdict - a verdict is never inflated here and no
        run is graded here on this road; ``/securityaudit
        index`` shows the index derived over every held
        record; ``/securityaudit verdict`` shows the verdict
        derived for the session. Resolution registers and
        publishes nothing as session news on this heading:
        records are held only when they are given
        through the agent's register roads, stood on the
        book on the viewing road, or held on the book
        roads, and every record held for the session is
        journaled as a securityaudit_record session record,
        every viewed standing as a securityaudit_standing
        session record and every held verdict as
        a securityaudit_verdict session record. This heading
        runs no benchmark, downloads no set,
        executes no grading test and inflates nothing here -
        holding and telling are words only.
        """
        from ..core.security_audit import (
            format_record,
            format_area,
            format_areas,
        )
        from .llm import parse_securityaudit_args
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target, needs, model = (
                parse_securityaudit_args(args))
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "areas":
                text = format_areas(
                    primary.securityaudit_areas())
            elif stance == "area":
                text = format_area(
                    primary.get_securityaudit_area(target))
            elif stance == "record":
                text = format_record(
                    primary.get_securityaudit_record(target))
            elif stance == "standing":
                standing = primary.securityaudit_standing(
                    target)
                text = (
                    f"{target}: "
                    f"{'held as answered' if standing.held else 'open'} "
                    f"(stage: {standing.stage}; "
                    f"grade: {standing.grade})")
                for gap in standing.gaps:
                    text += f"\n  gap: {gap}"
            elif stance == "reports":
                verdicts = primary.securityaudit_reports()
                if not verdicts:
                    text = (
                        "Run verdict: none held this "
                        "session - the areas verdict run "
                        "moves only as verdicts, and a verdict is "
                        "never inflated here.")
                else:
                    text = "\n".join(
                        f"{d.book} -> {d.entry}: verdict - "
                        f"{d.report} (state: {d.state}; "
                        "verdict is never inflated here)"
                        for d in verdicts)
            elif stance == "report":
                d = primary.get_securityaudit_report(target)
                text = (
                    f"{d.book} -> {d.entry}: verdict - "
                    f"{d.report} (state: {d.state}; "
                    "verdict is never inflated here)")
            elif stance == "index":
                text = primary.securityaudit_index()[
                    "index_text"]
            elif stance == "verdict":
                text = primary.securityaudit_verdict()[
                    "verdict_text"]
            else:
                text = primary.securityaudit_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")
    def _handle_privacyaudit(self, args: str):
        """M-261: /privacyaudit - the privacy audit as data.

        ``/privacyaudit`` shows the surfaces held this session -
        the public sets as registry entries: one
        entry per set, naming the word that set
        gives a single run and the standing of its
        gate, beside the run records
        held this session (no run recorded yet when
        none is held - a run is held only when a
        reported run rests on held gate evidence);
        ``/privacyaudit surfaces`` shows the whole shipped
        surface registry; ``/privacyaudit surface <surface>``
        shows one surface's registry entry; ``/privacyaudit
        record <surface> <run>`` shows the record held
        for one surface and run; ``/privacyaudit standing
        <surface> <run>`` shows the standing derived for
        one run - held only on a full legal walk resting
        on held gate evidence, with the verdict carrying
        model, cost and date together, otherwise
        open, naming its gaps; ``/privacyaudit verdict`` shows
        the run verdicts held this session and
        ``/privacyaudit verdict <surface>`` shows one surface's
        verdict - a verdict is never inflated here and no
        run is graded here on this road; ``/privacyaudit
        index`` shows the index derived over every held
        record; ``/privacyaudit verdict`` shows the verdict
        derived for the session. Resolution registers and
        publishes nothing as session news on this heading:
        records are held only when they are given
        through the agent's register roads, stood on the
        book on the viewing road, or held on the book
        roads, and every record held for the session is
        journaled as a privacyaudit_record session record,
        every viewed standing as a privacyaudit_standing
        session record and every held verdict as
        a privacyaudit_verdict session record. This heading
        runs no benchmark, downloads no set,
        executes no grading test and inflates nothing here -
        holding and telling are words only.
        """
        from ..core.privacy_audit import (
            format_record,
            format_surface,
            format_surfaces,
        )
        from .llm import parse_privacyaudit_args
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target, needs, model = (
                parse_privacyaudit_args(args))
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "surfaces":
                text = format_surfaces(
                    primary.privacyaudit_surfaces())
            elif stance == "surface":
                text = format_surface(
                    primary.get_privacyaudit_surface(target))
            elif stance == "record":
                text = format_record(
                    primary.get_privacyaudit_record(target))
            elif stance == "standing":
                standing = primary.privacyaudit_standing(
                    target)
                text = (
                    f"{target}: "
                    f"{'held as answered' if standing.held else 'open'} "
                    f"(stage: {standing.stage}; "
                    f"grade: {standing.grade})")
                for gap in standing.gaps:
                    text += f"\n  gap: {gap}"
            elif stance == "reports":
                verdicts = primary.privacyaudit_reports()
                if not verdicts:
                    text = (
                        "Run verdict: none held this "
                        "session - the surfaces verdict run "
                        "moves only as verdicts, and a verdict is "
                        "never inflated here.")
                else:
                    text = "\n".join(
                        f"{d.book} -> {d.entry}: verdict - "
                        f"{d.report} (state: {d.state}; "
                        "verdict is never inflated here)"
                        for d in verdicts)
            elif stance == "report":
                d = primary.get_privacyaudit_report(target)
                text = (
                    f"{d.book} -> {d.entry}: verdict - "
                    f"{d.report} (state: {d.state}; "
                    "verdict is never inflated here)")
            elif stance == "index":
                text = primary.privacyaudit_index()[
                    "index_text"]
            elif stance == "verdict":
                text = primary.privacyaudit_verdict()[
                    "verdict_text"]
            else:
                text = primary.privacyaudit_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")
    def _handle_accessibilityfinal(self, args: str):
        """M-262: /accessibilityfinal - the accessibility final gate as data.

        ``/accessibilityfinal`` shows the checks held this session -
        the public sets as registry entries: one
        entry per set, naming the word that set
        gives a single run and the standing of its
        gate, beside the run records
        held this session (no run recorded yet when
        none is held - a run is held only when a
        reported run rests on held gate evidence);
        ``/accessibilityfinal checks`` shows the whole shipped
        check registry; ``/accessibilityfinal check <check>``
        shows one check's registry entry; ``/accessibilityfinal
        record <check> <run>`` shows the record held
        for one check and run; ``/accessibilityfinal standing
        <check> <run>`` shows the standing derived for
        one run - held only on a full legal walk resting
        on held gate evidence, with the verdict carrying
        model, cost and date together, otherwise
        open, naming its gaps; ``/accessibilityfinal verdict`` shows
        the run verdicts held this session and
        ``/accessibilityfinal verdict <check>`` shows one check's
        verdict - a verdict is never inflated here and no
        run is graded here on this road; ``/accessibilityfinal
        index`` shows the index derived over every held
        record; ``/accessibilityfinal verdict`` shows the verdict
        derived for the session. Resolution registers and
        publishes nothing as session news on this heading:
        records are held only when they are given
        through the agent's register roads, stood on the
        book on the viewing road, or held on the book
        roads, and every record held for the session is
        journaled as a accessibilityfinal_record session record,
        every viewed standing as a accessibilityfinal_standing
        session record and every held verdict as
        a accessibilityfinal_verdict session record. This heading
        runs no benchmark, downloads no set,
        executes no grading test and inflates nothing here -
        holding and telling are words only.
        """
        from ..core.accessibility_final import (
            format_record,
            format_check,
            format_checks,
        )
        from .llm import parse_accessibilityfinal_args
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target, needs, model = (
                parse_accessibilityfinal_args(args))
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "checks":
                text = format_checks(
                    primary.accessibilityfinal_checks())
            elif stance == "check":
                text = format_check(
                    primary.get_accessibilityfinal_check(target))
            elif stance == "record":
                text = format_record(
                    primary.get_accessibilityfinal_record(target))
            elif stance == "standing":
                standing = primary.accessibilityfinal_standing(
                    target)
                text = (
                    f"{target}: "
                    f"{'held as answered' if standing.held else 'open'} "
                    f"(stage: {standing.stage}; "
                    f"grade: {standing.grade})")
                for gap in standing.gaps:
                    text += f"\n  gap: {gap}"
            elif stance == "reports":
                verdicts = primary.accessibilityfinal_reports()
                if not verdicts:
                    text = (
                        "Run verdict: none held this "
                        "session - the checks verdict run "
                        "moves only as verdicts, and a verdict is "
                        "never inflated here.")
                else:
                    text = "\n".join(
                        f"{d.book} -> {d.entry}: verdict - "
                        f"{d.report} (state: {d.state}; "
                        "verdict is never inflated here)"
                        for d in verdicts)
            elif stance == "report":
                d = primary.get_accessibilityfinal_report(target)
                text = (
                    f"{d.book} -> {d.entry}: verdict - "
                    f"{d.report} (state: {d.state}; "
                    "verdict is never inflated here)")
            elif stance == "index":
                text = primary.accessibilityfinal_index()[
                    "index_text"]
            elif stance == "verdict":
                text = primary.accessibilityfinal_verdict()[
                    "verdict_text"]
            else:
                text = primary.accessibilityfinal_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")
    def _handle_docscompletion(self, args: str):
        """M-263: /docscompletion - the docs completion as data.

        ``/docscompletion`` shows the guides held this session -
        the public sets as registry entries: one
        entry per set, naming the word that set
        gives a single run and the standing of its
        gate, beside the run records
        held this session (no run recorded yet when
        none is held - a run is held only when a
        reported run rests on held gate evidence);
        ``/docscompletion guides`` shows the whole shipped
        guide registry; ``/docscompletion guide <guide>``
        shows one guide's registry entry; ``/docscompletion
        record <guide> <run>`` shows the record held
        for one guide and run; ``/docscompletion standing
        <guide> <run>`` shows the standing derived for
        one run - held only on a full legal walk resting
        on held gate evidence, with the verdict carrying
        model, cost and date together, otherwise
        open, naming its gaps; ``/docscompletion verdict`` shows
        the run verdicts held this session and
        ``/docscompletion verdict <guide>`` shows one guide's
        verdict - a verdict is never inflated here and no
        run is graded here on this road; ``/docscompletion
        index`` shows the index derived over every held
        record; ``/docscompletion verdict`` shows the verdict
        derived for the session. Resolution registers and
        publishes nothing as session news on this heading:
        records are held only when they are given
        through the agent's register roads, stood on the
        book on the viewing road, or held on the book
        roads, and every record held for the session is
        journaled as a docscompletion_record session record,
        every viewed standing as a docscompletion_standing
        session record and every held verdict as
        a docscompletion_verdict session record. This heading
        runs no benchmark, downloads no set,
        executes no grading test and inflates nothing here -
        holding and telling are words only.
        """
        from ..core.docs_completion import (
            format_record,
            format_guide,
            format_guides,
        )
        from .llm import parse_docscompletion_args
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target, needs, model = (
                parse_docscompletion_args(args))
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "guides":
                text = format_guides(
                    primary.docscompletion_guides())
            elif stance == "guide":
                text = format_guide(
                    primary.get_docscompletion_guide(target))
            elif stance == "record":
                text = format_record(
                    primary.get_docscompletion_record(target))
            elif stance == "standing":
                standing = primary.docscompletion_standing(
                    target)
                text = (
                    f"{target}: "
                    f"{'held as answered' if standing.held else 'open'} "
                    f"(stage: {standing.stage}; "
                    f"grade: {standing.grade})")
                for gap in standing.gaps:
                    text += f"\n  gap: {gap}"
            elif stance == "reports":
                verdicts = primary.docscompletion_reports()
                if not verdicts:
                    text = (
                        "Run verdict: none held this "
                        "session - the guides verdict run "
                        "moves only as verdicts, and a verdict is "
                        "never inflated here.")
                else:
                    text = "\n".join(
                        f"{d.book} -> {d.entry}: verdict - "
                        f"{d.report} (state: {d.state}; "
                        "verdict is never inflated here)"
                        for d in verdicts)
            elif stance == "report":
                d = primary.get_docscompletion_report(target)
                text = (
                    f"{d.book} -> {d.entry}: verdict - "
                    f"{d.report} (state: {d.state}; "
                    "verdict is never inflated here)")
            elif stance == "index":
                text = primary.docscompletion_index()[
                    "index_text"]
            elif stance == "verdict":
                text = primary.docscompletion_verdict()[
                    "verdict_text"]
            else:
                text = primary.docscompletion_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")
    def _handle_readmecare(self, args: str):
        """M-264: /readmecare - the README care as data.

        ``/readmecare`` shows the sections held this session -
        the public sets as registry entries: one
        entry per set, naming the word that set
        gives a single run and the standing of its
        gate, beside the run records
        held this session (no run recorded yet when
        none is held - a run is held only when a
        reported run rests on held gate evidence);
        ``/readmecare sections`` shows the whole shipped
        section registry; ``/readmecare section <section>``
        shows one section's registry entry; ``/readmecare
        record <section> <run>`` shows the record held
        for one section and run; ``/readmecare standing
        <section> <run>`` shows the standing derived for
        one run - held only on a full legal walk resting
        on held gate evidence, with the verdict carrying
        model, cost and date together, otherwise
        open, naming its gaps; ``/readmecare verdict`` shows
        the run verdicts held this session and
        ``/readmecare verdict <section>`` shows one section's
        verdict - a verdict is never inflated here and no
        run is graded here on this road; ``/readmecare
        index`` shows the index derived over every held
        record; ``/readmecare verdict`` shows the verdict
        derived for the session. Resolution registers and
        publishes nothing as session news on this heading:
        records are held only when they are given
        through the agent's register roads, stood on the
        book on the viewing road, or held on the book
        roads, and every record held for the session is
        journaled as a readmecare_record session record,
        every viewed standing as a readmecare_standing
        session record and every held verdict as
        a readmecare_verdict session record. This heading
        runs no benchmark, downloads no set,
        executes no grading test and inflates nothing here -
        holding and telling are words only.
        """
        from ..core.readme_care import (
            format_record,
            format_section,
            format_sections,
        )
        from .llm import parse_readmecare_args
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target, needs, model = (
                parse_readmecare_args(args))
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "sections":
                text = format_sections(
                    primary.readmecare_sections())
            elif stance == "section":
                text = format_section(
                    primary.get_readmecare_section(target))
            elif stance == "record":
                text = format_record(
                    primary.get_readmecare_record(target))
            elif stance == "standing":
                standing = primary.readmecare_standing(
                    target)
                text = (
                    f"{target}: "
                    f"{'held as answered' if standing.held else 'open'} "
                    f"(stage: {standing.stage}; "
                    f"grade: {standing.grade})")
                for gap in standing.gaps:
                    text += f"\n  gap: {gap}"
            elif stance == "reports":
                verdicts = primary.readmecare_reports()
                if not verdicts:
                    text = (
                        "Report: none held this "
                        "session - README reports move only as "
                        "moves only as reports, and a report is "
                        "never inflated here.")
                else:
                    text = "\n".join(
                        f"{d.book} -> {d.entry}: report - "
                        f"{d.report} (state: {d.state}; "
                        "a report is never inflated here)"
                        for d in verdicts)
            elif stance == "report":
                d = primary.get_readmecare_report(target)
                text = (
                    f"{d.book} -> {d.entry}: report - "
                    f"{d.report} (state: {d.state}; "
                    "a report is never inflated here)")
            elif stance == "index":
                text = primary.readmecare_index()[
                    "index_text"]
            elif stance == "verdict":
                text = primary.readmecare_verdict()[
                    "verdict_text"]
            else:
                text = primary.readmecare_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")
    def _handle_migrationproof(self, args: str):
        """M-265: /migrationproof - the Migration proof as data.

        ``/migrationproof`` shows the areas held this session -
        the public sets as registry entries: one
        entry per set, naming the word that set
        gives a single run and the standing of its
        gate, beside the run records
        held this session (no run recorded yet when
        none is held - a run is held only when a
        reported run rests on held gate evidence);
        ``/migrationproof areas`` shows the whole shipped
        area registry; ``/migrationproof area <area>``
        shows one area's registry entry; ``/migrationproof
        record <area> <run>`` shows the record held
        for one area and run; ``/migrationproof standing
        <area> <run>`` shows the standing derived for
        one run - held only on a full legal walk resting
        on held gate evidence, with the verdict carrying
        model, cost and date together, otherwise
        open, naming its gaps; ``/migrationproof verdict`` shows
        the run verdicts held this session and
        ``/migrationproof verdict <area>`` shows one area's
        verdict - a verdict is never inflated here and no
        run is graded here on this road; ``/migrationproof
        index`` shows the index derived over every held
        record; ``/migrationproof verdict`` shows the verdict
        derived for the session. Resolution registers and
        publishes nothing as session news on this heading:
        records are held only when they are given
        through the agent's register roads, stood on the
        book on the viewing road, or held on the book
        roads, and every record held for the session is
        journaled as a migrationproof_record session record,
        every viewed standing as a migrationproof_standing
        session record and every held verdict as
        a migrationproof_verdict session record. This heading
        runs no benchmark, downloads no set,
        executes no grading test and inflates nothing here -
        holding and telling are words only.
        """
        from ..core.migration_proof import (
            format_record,
            format_area,
            format_areas,
        )
        from .llm import parse_migrationproof_args
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target, needs, model = (
                parse_migrationproof_args(args))
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "areas":
                text = format_areas(
                    primary.migrationproof_areas())
            elif stance == "area":
                text = format_area(
                    primary.get_migrationproof_area(target))
            elif stance == "record":
                text = format_record(
                    primary.get_migrationproof_record(target))
            elif stance == "standing":
                standing = primary.migrationproof_standing(
                    target)
                text = (
                    f"{target}: "
                    f"{'held as answered' if standing.held else 'open'} "
                    f"(stage: {standing.stage}; "
                    f"grade: {standing.grade})")
                for gap in standing.gaps:
                    text += f"\n  gap: {gap}"
            elif stance == "reports":
                verdicts = primary.migrationproof_reports()
                if not verdicts:
                    text = (
                        "Report: none held this "
                        "session - Migration reports move only as "
                        "moves only as reports, and a report is "
                        "never inflated here.")
                else:
                    text = "\n".join(
                        f"{d.book} -> {d.entry}: report - "
                        f"{d.report} (state: {d.state}; "
                        "a report is never inflated here)"
                        for d in verdicts)
            elif stance == "report":
                d = primary.get_migrationproof_report(target)
                text = (
                    f"{d.book} -> {d.entry}: report - "
                    f"{d.report} (state: {d.state}; "
                    "a report is never inflated here)")
            elif stance == "index":
                text = primary.migrationproof_index()[
                    "index_text"]
            elif stance == "verdict":
                text = primary.migrationproof_verdict()[
                    "verdict_text"]
            else:
                text = primary.migrationproof_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")
    def _handle_strangerfleettest(self, args: str):
        """M-266: /strangerfleettest - the Stranger fleet test as data.

        ``/strangerfleettest`` shows the exercises held this session -
        the public sets as registry entries: one
        entry per set, naming the word that set
        gives a single run and the standing of its
        gate, beside the run records
        held this session (no run recorded yet when
        none is held - a run is held only when a
        reported run rests on held gate evidence);
        ``/strangerfleettest exercises`` shows the whole shipped
        exercise registry; ``/strangerfleettest exercise <exercise>``
        shows one exercise's registry entry; ``/strangerfleettest
        record <exercise> <run>`` shows the record held
        for one exercise and run; ``/strangerfleettest standing
        <exercise> <run>`` shows the standing derived for
        one run - held only on a full legal walk resting
        on held gate evidence, with the verdict carrying
        model, cost and date together, otherwise
        open, naming its gaps; ``/strangerfleettest verdict`` shows
        the run verdicts held this session and
        ``/strangerfleettest verdict <exercise>`` shows one exercise's
        verdict - a verdict is never inflated here and no
        run is graded here on this road; ``/strangerfleettest
        index`` shows the index derived over every held
        record; ``/strangerfleettest verdict`` shows the verdict
        derived for the session. Resolution registers and
        publishes nothing as session news on this heading:
        records are held only when they are given
        through the agent's register roads, stood on the
        book on the viewing road, or held on the book
        roads, and every record held for the session is
        journaled as a strangerfleettest_record session record,
        every viewed standing as a strangerfleettest_standing
        session record and every held verdict as
        a strangerfleettest_verdict session record. This heading
        runs no benchmark, downloads no set,
        executes no grading test and inflates nothing here -
        holding and telling are words only.
        """
        from ..core.stranger_fleet_test import (
            format_record,
            format_exercise,
            format_exercises,
        )
        from .llm import parse_strangerfleettest_args
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target, needs, model = (
                parse_strangerfleettest_args(args))
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "exercises":
                text = format_exercises(
                    primary.strangerfleettest_exercises())
            elif stance == "exercise":
                text = format_exercise(
                    primary.get_strangerfleettest_exercise(target))
            elif stance == "record":
                text = format_record(
                    primary.get_strangerfleettest_record(target))
            elif stance == "standing":
                standing = primary.strangerfleettest_standing(
                    target)
                text = (
                    f"{target}: "
                    f"{'held as answered' if standing.held else 'open'} "
                    f"(stage: {standing.stage}; "
                    f"grade: {standing.grade})")
                for gap in standing.gaps:
                    text += f"\n  gap: {gap}"
            elif stance == "reports":
                verdicts = primary.strangerfleettest_reports()
                if not verdicts:
                    text = (
                        "Report: none held this "
                        "session - Fleet reports move only as "
                        "moves only as reports, and a report is "
                        "never inflated here.")
                else:
                    text = "\n".join(
                        f"{d.book} -> {d.entry}: report - "
                        f"{d.report} (state: {d.state}; "
                        "a report is never inflated here)"
                        for d in verdicts)
            elif stance == "report":
                d = primary.get_strangerfleettest_report(target)
                text = (
                    f"{d.book} -> {d.entry}: report - "
                    f"{d.report} (state: {d.state}; "
                    "a report is never inflated here)")
            elif stance == "index":
                text = primary.strangerfleettest_index()[
                    "index_text"]
            elif stance == "verdict":
                text = primary.strangerfleettest_verdict()[
                    "verdict_text"]
            else:
                text = primary.strangerfleettest_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")
    def _handle_costofquality(self, args: str):
        """M-267: /costofquality - the Cost-of-quality report as data.

        ``/costofquality`` shows the routes held this session -
        the public sets as registry entries: one
        entry per set, naming the word that set
        gives a single run and the standing of its
        gate, beside the run records
        held this session (no run recorded yet when
        none is held - a run is held only when a
        reported run rests on held evidence);
        ``/costofquality routes`` shows the whole shipped
        route registry; ``/costofquality route <route>``
        shows one route's registry entry; ``/costofquality
        record <route> <run>`` shows the record held
        for one route and run; ``/costofquality standing
        <route> <run>`` shows the standing derived for
        one run - held only on a full legal walk resting
        on held evidence, with the verdict carrying
        model, cost and date together, otherwise
        open, naming its gaps; ``/costofquality verdict`` shows
        the run verdicts held this session and
        ``/costofquality verdict <route>`` shows one route's
        verdict - a verdict is never inflated here and no
        run is graded here on this road; ``/costofquality
        index`` shows the index derived over every held
        record; ``/costofquality verdict`` shows the verdict
        derived for the session. Resolution registers and
        publishes nothing as session news on this heading:
        records are held only when they are given
        through the agent's register roads, stood on the
        book on the viewing road, or held on the book
        roads, and every record held for the session is
        journaled as a costofquality_record session record,
        every viewed standing as a costofquality_standing
        session record and every held verdict as
        a costofquality_verdict session record. This heading
        runs no benchmark, downloads no set,
        executes no grading test and inflates nothing here -
        holding and telling are words only.
        """
        from ..core.cost_of_quality import (
            format_record,
            format_route,
            format_routes,
        )
        from .llm import parse_costofquality_args
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target, needs, model = (
                parse_costofquality_args(args))
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "routes":
                text = format_routes(
                    primary.costofquality_routes())
            elif stance == "route":
                text = format_route(
                    primary.get_costofquality_route(target))
            elif stance == "record":
                text = format_record(
                    primary.get_costofquality_record(target))
            elif stance == "standing":
                standing = primary.costofquality_standing(
                    target)
                text = (
                    f"{target}: "
                    f"{'held as answered' if standing.held else 'open'} "
                    f"(stage: {standing.stage}; "
                    f"grade: {standing.grade})")
                for gap in standing.gaps:
                    text += f"\n  gap: {gap}"
            elif stance == "reports":
                verdicts = primary.costofquality_reports()
                if not verdicts:
                    text = (
                        "Report: none held this "
                        "session - Cost reports move only as "
                        "moves only as reports, and a report is "
                        "never inflated here.")
                else:
                    text = "\n".join(
                        f"{d.book} -> {d.entry}: report - "
                        f"{d.report} (state: {d.state}; "
                        "a report is never inflated here)"
                        for d in verdicts)
            elif stance == "report":
                d = primary.get_costofquality_report(target)
                text = (
                    f"{d.book} -> {d.entry}: report - "
                    f"{d.report} (state: {d.state}; "
                    "a report is never inflated here)")
            elif stance == "index":
                text = primary.costofquality_index()[
                    "index_text"]
            elif stance == "verdict":
                text = primary.costofquality_verdict()[
                    "verdict_text"]
            else:
                text = primary.costofquality_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")
    def _handle_truthfulchangelog(self, args: str):
        """M-268: /truthfulchangelog - the Truthful changelog as data.

        ``/truthfulchangelog`` shows the families held this session -
        the public sets as registry entries: one
        entry per set, naming the word that set
        gives a single run and the standing of its
        gate, beside the run records
        held this session (no run recorded yet when
        none is held - a run is held only when a
        reported run rests on held evidence);
        ``/truthfulchangelog families`` shows the whole shipped
        family registry; ``/truthfulchangelog family <family>``
        shows one family's registry entry; ``/truthfulchangelog
        record <family> <run>`` shows the record held
        for one family and run; ``/truthfulchangelog standing
        <family> <run>`` shows the standing derived for
        one run - held only on a full legal walk resting
        on held evidence, with the verdict carrying
        model, changelog and date together, otherwise
        open, naming its gaps; ``/truthfulchangelog verdict`` shows
        the run verdicts held this session and
        ``/truthfulchangelog verdict <family>`` shows one family's
        verdict - a verdict is never inflated here and no
        run is graded here on this road; ``/truthfulchangelog
        index`` shows the index derived over every held
        record; ``/truthfulchangelog verdict`` shows the verdict
        derived for the session. Resolution registers and
        publishes nothing as session news on this heading:
        records are held only when they are given
        through the agent's register roads, stood on the
        book on the viewing road, or held on the book
        roads, and every record held for the session is
        journaled as a truthfulchangelog_record session record,
        every viewed standing as a truthfulchangelog_standing
        session record and every held verdict as
        a truthfulchangelog_verdict session record. This heading
        runs no test, downloads no set,
        executes no grading test and inflates nothing here -
        holding and telling are words only.
        """
        from ..core.truthful_changelog import (
            format_record,
            format_family,
            format_families,
        )
        from .llm import parse_truthfulchangelog_args
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target, needs, model = (
                parse_truthfulchangelog_args(args))
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "families":
                text = format_families(
                    primary.truthfulchangelog_families())
            elif stance == "family":
                text = format_family(
                    primary.get_truthfulchangelog_family(target))
            elif stance == "record":
                text = format_record(
                    primary.get_truthfulchangelog_record(target))
            elif stance == "standing":
                standing = primary.truthfulchangelog_standing(
                    target)
                text = (
                    f"{target}: "
                    f"{'held as answered' if standing.held else 'open'} "
                    f"(stage: {standing.stage}; "
                    f"grade: {standing.grade})")
                for gap in standing.gaps:
                    text += f"\n  gap: {gap}"
            elif stance == "reports":
                verdicts = primary.truthfulchangelog_reports()
                if not verdicts:
                    text = (
                        "Report: none held this "
                        "session - Changelog reports move only as "
                        "moves only as reports, and a report is "
                        "never inflated here.")
                else:
                    text = "\n".join(
                        f"{d.book} -> {d.entry}: report - "
                        f"{d.report} (state: {d.state}; "
                        "a report is never inflated here)"
                        for d in verdicts)
            elif stance == "report":
                d = primary.get_truthfulchangelog_report(target)
                text = (
                    f"{d.book} -> {d.entry}: report - "
                    f"{d.report} (state: {d.state}; "
                    "a report is never inflated here)")
            elif stance == "index":
                text = primary.truthfulchangelog_index()[
                    "index_text"]
            elif stance == "verdict":
                text = primary.truthfulchangelog_verdict()[
                    "verdict_text"]
            else:
                text = primary.truthfulchangelog_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")
    def _handle_releaseshaping(self, args: str):
        """M-269: /releaseshaping - the Release shaping as data.

        ``/releaseshaping`` shows the releases held this session -
        the public sets as registry entries: one
        entry per set, naming the word that set
        gives a single run and the standing of its
        gate, beside the run records
        held this session (no run recorded yet when
        none is held - a run is held only when a
        reported run rests on held evidence);
        ``/releaseshaping releases`` shows the whole shipped
        release registry; ``/releaseshaping release <release>``
        shows one release's registry entry; ``/releaseshaping
        record <release> <run>`` shows the record held
        for one release and run; ``/releaseshaping standing
        <release> <run>`` shows the standing derived for
        one run - held only on a full legal walk resting
        on held evidence, with the verdict carrying
        model, release and date together, otherwise
        open, naming its gaps; ``/releaseshaping verdict`` shows
        the run verdicts held this session and
        ``/releaseshaping verdict <release>`` shows one release's
        verdict - a verdict is never inflated here and no
        run is graded here on this road; ``/releaseshaping
        index`` shows the index derived over every held
        record; ``/releaseshaping verdict`` shows the verdict
        derived for the session. Resolution registers and
        publishes nothing as session news on this heading:
        records are held only when they are given
        through the agent's register roads, stood on the
        book on the viewing road, or held on the book
        roads, and every record held for the session is
        journaled as a releaseshaping_record session record,
        every viewed standing as a releaseshaping_standing
        session record and every held verdict as
        a releaseshaping_verdict session record. This heading
        runs no test, downloads no set,
        executes no grading test and inflates nothing here -
        holding and telling are words only.
        """
        from ..core.release_shaping import (
            format_record,
            format_release,
            format_releases,
        )
        from .llm import parse_releaseshaping_args
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target, needs, model = (
                parse_releaseshaping_args(args))
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "releases":
                text = format_releases(
                    primary.releaseshaping_releases())
            elif stance == "release":
                text = format_release(
                    primary.get_releaseshaping_release(target))
            elif stance == "record":
                text = format_record(
                    primary.get_releaseshaping_record(target))
            elif stance == "standing":
                standing = primary.releaseshaping_standing(
                    target)
                text = (
                    f"{target}: "
                    f"{'held as answered' if standing.held else 'open'} "
                    f"(stage: {standing.stage}; "
                    f"grade: {standing.grade})")
                for gap in standing.gaps:
                    text += f"\n  gap: {gap}"
            elif stance == "reports":
                verdicts = primary.releaseshaping_reports()
                if not verdicts:
                    text = (
                        "Report: none held this "
                        "session - Release reports move only as "
                        "moves only as reports, and a report is "
                        "never inflated here.")
                else:
                    text = "\n".join(
                        f"{d.book} -> {d.entry}: report - "
                        f"{d.report} (state: {d.state}; "
                        "a report is never inflated here)"
                        for d in verdicts)
            elif stance == "report":
                d = primary.get_releaseshaping_report(target)
                text = (
                    f"{d.book} -> {d.entry}: report - "
                    f"{d.report} (state: {d.state}; "
                    "a report is never inflated here)")
            elif stance == "index":
                text = primary.releaseshaping_index()[
                    "index_text"]
            elif stance == "verdict":
                text = primary.releaseshaping_verdict()[
                    "verdict_text"]
            else:
                text = primary.releaseshaping_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")
    def _handle_roadmapaudit(self, args: str):
        """M-270: /roadmapaudit - the Roadmap audit as data.

        ``/roadmapaudit`` shows the parts held this session -
        the public sets as registry entries: one
        entry per set, naming the word that set
        gives a single run and the standing of its
        gate, beside the run records
        held this session (no run recorded yet when
        none is held - a run is held only when a
        reported run rests on held evidence);
        ``/roadmapaudit parts`` shows the whole shipped
        part registry; ``/roadmapaudit part <part>``
        shows one part's registry entry; ``/roadmapaudit
        record <part> <run>`` shows the record held
        for one part and run; ``/roadmapaudit standing
        <part> <run>`` shows the standing derived for
        one run - held only on a full legal walk resting
        on held evidence, with the verdict carrying
        model, part and date together, otherwise
        open, naming its gaps; ``/roadmapaudit verdict`` shows
        the run verdicts held this session and
        ``/roadmapaudit verdict <part>`` shows one part's
        verdict - a verdict is never inflated here and no
        run is graded here on this road; ``/roadmapaudit
        index`` shows the index derived over every held
        record; ``/roadmapaudit verdict`` shows the verdict
        derived for the session. Resolution registers and
        publishes nothing as session news on this heading:
        records are held only when they are given
        through the agent's register roads, stood on the
        book on the viewing road, or held on the book
        roads, and every record held for the session is
        journaled as a roadmapaudit_record session record,
        every viewed standing as a roadmapaudit_standing
        session record and every held verdict as
        a roadmapaudit_verdict session record. This heading
        runs no test, downloads no set,
        executes no grading test and inflates nothing here -
        holding and telling are words only.
        """
        from ..core.roadmap_audit import (
            format_record,
            format_part,
            format_parts,
        )
        from .llm import parse_roadmapaudit_args
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target, needs, model = (
                parse_roadmapaudit_args(args))
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "parts":
                text = format_parts(
                    primary.roadmapaudit_parts())
            elif stance == "part":
                text = format_part(
                    primary.get_roadmapaudit_part(target))
            elif stance == "record":
                text = format_record(
                    primary.get_roadmapaudit_record(target))
            elif stance == "standing":
                standing = primary.roadmapaudit_standing(
                    target)
                text = (
                    f"{target}: "
                    f"{'held as answered' if standing.held else 'open'} "
                    f"(stage: {standing.stage}; "
                    f"grade: {standing.grade})")
                for gap in standing.gaps:
                    text += f"\n  gap: {gap}"
            elif stance == "reports":
                verdicts = primary.roadmapaudit_reports()
                if not verdicts:
                    text = (
                        "Report: none held this "
                        "session - Part reports move only as "
                        "moves only as reports, and a report is "
                        "never inflated here.")
                else:
                    text = "\n".join(
                        f"{d.book} -> {d.entry}: report - "
                        f"{d.report} (state: {d.state}; "
                        "a report is never inflated here)"
                        for d in verdicts)
            elif stance == "report":
                d = primary.get_roadmapaudit_report(target)
                text = (
                    f"{d.book} -> {d.entry}: report - "
                    f"{d.report} (state: {d.state}; "
                    "a report is never inflated here)")
            elif stance == "index":
                text = primary.roadmapaudit_index()[
                    "index_text"]
            elif stance == "verdict":
                text = primary.roadmapaudit_verdict()[
                    "verdict_text"]
            else:
                text = primary.roadmapaudit_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")
    def _handle_docsmcp(self, args: str):
        """M-252: /docsmcp - the docs MCP pattern as data.

        ``/docsmcp`` shows the doors held this session -
        the export projects as registry entries: one
        entry per project, naming the word that project
        gives a single telling, beside the record records
        held this session (no record recorded yet when
        none is held - export is current only when a
        fresh record rests on held evidence);
        ``/docsmcp projects`` shows the whole shipped
        project registry; ``/docsmcp project <project>``
        shows one project's registry entry; ``/docsmcp
        record <project> <record>`` shows the record held
        for one project and record; ``/docsmcp standing
        <project> <record>`` shows the standing derived for
        one record - held only on a full legal walk resting
        on held evidence within the fresh limit, otherwise
        open, naming its gaps; ``/docsmcp propose`` shows
        the bridge proposal held this session and
        ``/docsmcp propose <bridge>`` shows one proposal
        proposal - proposal is never attached here and no
        bridge is attached here on this road; ``/docsmcp
        index`` shows the index derived over every held
        record; ``/docsmcp verdict`` shows the verdict
        derived for the session. Resolution registers and
        publishes nothing as session news on this heading:
        records are held only when they are given
        through the agent's register roads, stood on the
        book on the viewing road, or held on the book
        roads, and every record held for the session is
        journaled as a docsmcp_record session record,
        every viewed standing as a docsmcp_standing
        session record and every proposed proposal proposal as
        a docsmcp_proposal session record. This heading
        calls no host API, performs no export,
        starts nothing and exports nothing here -
        holding and telling are words only.
        """
        from ..core.docs_mcp_pattern import (
            format_record,
            format_project,
            format_projects,
        )
        from .llm import parse_docsmcp_args
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target, needs, model = (
                parse_docsmcp_args(args))
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "projects":
                text = format_projects(
                    primary.docsmcp_projects())
            elif stance == "project":
                text = format_project(
                    primary.get_docsmcp_project(target))
            elif stance == "record":
                text = format_record(
                    primary.get_docsmcp_record(*target))
            elif stance == "standing":
                standing = primary.docsmcp_standing(
                    *target)
                text = (
                    f"{target[0]}/{target[1]}: attachment "
                    f"{'held as bridge' if standing.held else 'open'} "
                    f"(stage: {standing.stage}; "
                    f"freshness: {standing.freshness})")
                for gap in standing.gaps:
                    text += f"\n  gap: {gap}"
            elif stance == "proposals":
                proposals = primary.docsmcp_proposals()
                if not proposals:
                    text = (
                        "Bridge proposal: none held this "
                        "session - the doors propose bridge "
                        "moves only as proposals, and a proposal is "
                        "never attached here.")
                else:
                    text = "\n".join(
                        f"{d.bridge} -> {d.record}: proposal - "
                        f"{d.proposal} (state: {d.state}; "
                        "proposal is never attached here)"
                        for d in proposals)
            elif stance == "propose":
                d = primary.get_docsmcp_proposal(target)
                text = (
                    f"{d.bridge} -> {d.record}: proposal - "
                    f"{d.proposal} (state: {d.state}; "
                    "proposal is never attached here)")
            elif stance == "index":
                text = primary.docsmcp_index()[
                    "index_text"]
            elif stance == "verdict":
                text = primary.docsmcp_verdict()[
                    "verdict_text"]
            else:
                text = primary.docsmcp_status()["screen"]
        except (KeyError, ValueError) as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        publish_sync(
            "agent_chat_chunk", agent_name="Primary",
            text=f"\n[bold cyan]{text}[/bold cyan]\n")
    def _handle_mcpserver(self, args: str):
        """M-234: /mcpserver - the exposure engine as data.

        ``/mcpserver`` shows the exposure book held this
        session - exposure services as data: one record per
        exposure, held whole with the active service it
        was held from, its one verifiable stage
        at the house grain and its claims, and
        the notes held as data beside them (the shipped
        example book - five exposures at the M-203 service
        service, with its three service references, its
        two views, two stance records, one trace
        trace and its one pinned panel - when none
        is held yet); ``/mcpserver exposure <exposure-id>``
        shows one exposure whole; ``/mcpserver stage
        <stage>`` shows the exposure one stage line
        reaches, or names the stage unheld;
        ``/mcpserver service <service-id>`` shows the book's
        exposures of one service; ``/mcpserver view <view-id>``
        shows one held view record; ``/mcpserver note
        <note-id>`` shows one held stance record;
        ``/mcpserver index`` shows the index derived
        from the whole book's held exposures; ``/mcpserver
        panel`` shows the panel derived from the
        whole book under its default view; ``/mcpserver
        verdict`` shows the verdict derived for the
        whole book. Exposure registers and publishes
        nothing as session news: exposures and views are
        held only when they are given through the
        agent's register targets, stood on the book on
        the viewing target, or held on the book targets,
        and every exposure held for the session is
        journaled as a exposure_exposure session event,
        every view as a exposure_view session event,
        every derived panel as a mcpserver_panel
        session event and every derived verdict as a
        mcpserver_verdict session event. This heading
        builds no service, executes nothing and banks
        nothing - holding and telling are words only.
        """
        from ..core.mcp_server_v2 import (
            format_exposure,
            format_book,
            format_stage,
            format_index,
            format_note,
            format_panel,
            format_verdict,
            format_view,
            parse_exposure_args,
        )
        primary = self._primary()
        if primary is None:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text="\n[dim]Agent is not initialized yet.[/dim]\n")
            return
        try:
            stance, target = parse_exposure_args(args)
        except ValueError as e:
            publish_sync("agent_chat_chunk", agent_name="Primary",
                         text=f"\n[red]{e}[/red]\n")
            return
        try:
            if stance == "exposure":
                text = format_exposure(
                    primary.get_mcpserver_exposure(target),
                    primary.mcpserver_book())
            elif stance == "stage":
                text = format_stage(
                    primary.mcpserver_book(), target)
            elif stance == "service":
                text = format_book(
                    primary.mcpserver_book(), target)
            elif stance == "view":
                text = format_view(primary.get_mcpserver_view(target))
            elif stance == "note":
                text = format_note(
                    primary.mcpserver_book().note_for(target))
            elif stance == "index":
                text = format_index(primary.mcpserver_book())
            elif stance == "panel":
                text = format_panel(primary.mcpserver_book())
            elif stance == "verdict":
                text = format_verdict(primary.mcpserver_book())
            else:
                text = primary.mcpserver_status()["screen"]
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
