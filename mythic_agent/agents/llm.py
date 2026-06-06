import json
import os
import time
import logging
import threading
import queue
import random
from pathlib import Path
from typing import Any, Callable

from openai import OpenAI

from .tools import execute_tool, get_agent_tools
from ..core.config_manager import config_manager
from ..constants import DEFAULT_SYSTEM_PROMPT
from ..core.secure_api import publish_sync, subscribe
from ..memory.core_memory import CoreMemoryManager
from ..memory.vector_db import get_vector_provider

# Global registry of live sub-agent instances keyed by name.
AGENT_REGISTRY: dict[str, "Agent"] = {}

class Agent:
    def __init__(self, project_root: Path | None = None, name: str = "Primary"):
        self.config = config_manager.load_config()
        self.project_root = project_root
        self.name = name
        
        working_dir_str = self.config.get("working_directory")
        if working_dir_str:
            self.project_root = Path(working_dir_str).expanduser().resolve()
        elif not self.project_root:
            default_wd = config_manager.MYTHIC_DIR / "mythic_longhall"
            default_wd.mkdir(parents=True, exist_ok=True)
            self.project_root = default_wd
            
        self.total_tokens = 0
        if "api_keys" not in self.config:
            self.config["api_keys"] = {}
            
        self.messages = []
        self.inbox = queue.Queue()
        self._lock = threading.Lock()
        self.active_task_start_time = None
        self.rebuild_system_prompt()
        
        self.core_memory = CoreMemoryManager(self.name)
        
        # Initialize Vector DB
        base_url = self.config.get("base_url", config_manager.DEFAULT_BASE_URL)
        api_key = self.get_api_key(base_url)
        provider = self.config.get("vector_db_provider", "lightweight")
        self.vector_db = get_vector_provider(provider, self.name, base_url, api_key)
        
        self.inject_mythic_agents()
        
        # Subscribe to Parity Commands
        subscribe("agent_clear_history", self._handle_clear_history)
        subscribe("agent_compact_history", self._handle_compact_history)
        
    def _handle_clear_history(self, target_agent: str):
        if target_agent == self.name:
            with self._lock:
                # Keep only the system prompt
                if self.messages and self.messages[0].get("role") == "system":
                    self.messages = [self.messages[0]]
                else:
                    self.messages = []
                publish_sync("agent_chat_chunk", agent_name=self.name, text="\n[bold green]Memory cleared. Context window is empty.[/bold green]\n")

    def _handle_compact_history(self, target_agent: str):
        if target_agent == self.name:
            with self._lock:
                if len(self.messages) > 10:
                    forgotten_chunk = self.messages[1:11]
                    if hasattr(self, "vector_db"):
                        try:
                            archive_text = "Archived Context Chunk:\n" + "\n".join(
                                f"{m.get('role', 'unknown').upper()}: {m.get('content', '')}" for m in forgotten_chunk
                            )
                            self.vector_db.insert(archive_text)
                        except Exception as e:
                            logging.error(f"Auto-Archival failed during manual compact: {e}")
                    
                    self.messages = [self.messages[0]] + self.messages[11:]
                    publish_sync("agent_chat_chunk", agent_name=self.name, text="\n[bold yellow]Context Compacted manually. Oldest 10 messages archived to VectorDB.[/bold yellow]\n")
                else:
                    publish_sync("agent_chat_chunk", agent_name=self.name, text="\n[dim]Context is already small. Compaction not necessary.[/dim]\n")

    def get_user_context(self) -> str:
        user_name = self.config.get("user_name", "").strip()
        user_data = self.config.get("user_data", "").strip()
        if not user_name and not user_data:
            return ""
        
        context = "\n\nUSER CONTEXT:\n"
        if user_name:
            context += f"The user's name is {user_name}.\n"
        if user_data:
            context += f"Data about the user:\n{user_data}\n"
        return context

    def rebuild_system_prompt(self) -> None:
        if self.name == "Primary":
            system_prompt = self.config.get("system_prompt", DEFAULT_SYSTEM_PROMPT)
        else:
            sub_agents = self.config.get("sub_agents", [])
            sub_config = next((s for s in sub_agents if s.get("name") == self.name), None)
            system_prompt = sub_config.get("prompt", "You are a helpful sub-agent.") if sub_config else "You are a helpful sub-agent."

        global_rules = self.config.get("global_rules", "").strip()
        status_rule = "You MUST use the `update_status` tool to autosave your current project status and keep track of what is going on."
        diff_rule = "CRITICAL: If you modify any files during your turn, you MUST include a summary of the files changed at the very end of your final response, explicitly showing the (+X, -Y) lines added and removed. The write_file and replace_file_content tools will tell you these numbers upon success. Format it exactly like this:\n[bold cyan]Files Changed:[/bold cyan]\n[green]+ X[/green] [red]- Y[/red] path/to/file.py"
        
        if global_rules:
            system_prompt += f"\n\nGLOBAL RULES (You must strictly follow these):\n{global_rules}\n- {status_rule}\n- {diff_rule}"
        else:
            system_prompt += f"\n\nGLOBAL RULES:\n- {status_rule}\n- {diff_rule}"

        if self.config.get("mythic_engineering_mode"):
            system_prompt += "\n\n=== MYTHIC ENGINEERING MODE PROTOCOL ACTIVATED ===\n"
            
            # Dynamically resolve the path to the skill file relative to the mythic_agent package
            # mythic-agent/mythic_agent/agents/llm.py -> parent.parent.parent -> mythic-agent
            skill_file_path = Path(__file__).parent.parent.parent / "Mythic-Engineering" / "Mythic-Engineering_SKILL.md"
            
            try:
                if skill_file_path.exists():
                    skill_content = skill_file_path.read_text(encoding="utf-8")
                    system_prompt += "\n[CORE PROTOCOL LOADED FROM DISK]\n"
                    system_prompt += skill_content
                else:
                    raise FileNotFoundError("Skill file missing")
            except Exception as e:
                logging.error(f"Failed to load Mythic Engineering skill file: {e}. Using fallback.")
                system_prompt += "\n[FALLBACK CORE PROTOCOL]\n"
                system_prompt += "You are the orchestrator of an Architecture-First, intuition-led, document-guided development process."
                system_prompt += "\n1. Vision before implementation. Architecture before patching."
                system_prompt += "\n2. MD Protocol: Markdown as living memory (README.md, ARCHITECTURE.md, etc)."
                system_prompt += "\n3. ALWAYS delegate and consult your 6 included Sub-Agents (Skald, Architect, Forge Worker, Auditor, Cartographer, Scribe) using the delegate_task tool when tackling large problems."
                system_prompt += "\n4. Reality outranks theory. Refactor by ownership. Invariants matter."

        system_prompt += self.get_user_context()
        
        if hasattr(self, "core_memory"):
            system_prompt += self.core_memory.format_for_prompt()
        
        with self._lock:
            if not self.messages:
                self.messages.append({"role": "system", "content": system_prompt})
            elif self.messages[0].get("role") == "system":
                self.messages[0]["content"] = system_prompt
            else:
                self.messages.insert(0, {"role": "system", "content": system_prompt})
            
    def inject_mythic_agents(self) -> None:
        """Inject the core Mythic Engineering sub-agents if they don't exist."""
        from ..constants import DEFAULT_SUBAGENTS
        
        current_agents = self.config.get("sub_agents", [])
        existing_names = {a.get("name") for a in current_agents}
        
        added = False
        for agent in DEFAULT_SUBAGENTS:
            if agent["name"] not in existing_names:
                current_agents.append(agent)
                added = True
                
        if added:
            self.config["sub_agents"] = current_agents
            self.save_config()
        
    def save_config(self) -> None:
        config_manager.save_config(self.config)
        
    def get_api_key(self, base_url: str) -> str | None:
        stored_key = self.config.get("api_keys", {}).get(base_url)
        if stored_key:
            return stored_key
            
        if "deepseek" in base_url:
            return os.environ.get("DEEPSEEK_API_KEY")
        if "openrouter" in base_url:
            return os.environ.get("OPENROUTER_API_KEY")
        if "anthropic" in base_url:
            return os.environ.get("ANTHROPIC_API_KEY")
            
        return os.environ.get("OPENAI_API_KEY")

    def get_client(self) -> OpenAI:
        base_url = self.config.get("base_url", config_manager.DEFAULT_BASE_URL)
        api_key = self.get_api_key(base_url)
        
        if not api_key:
            logging.warning("No API key found for base URL %s", base_url)
            
        return OpenAI(
            base_url=base_url,
            api_key=api_key or "sk-dummy"
        )
        
    def set_model(self, model: str, base_url: str, api_key: str | None = None) -> None:
        self.config["model"] = model
        self.config["base_url"] = base_url
        if "api_keys" not in self.config:
            self.config["api_keys"] = {}
        if api_key:
            self.config["api_keys"][base_url] = api_key
        self.save_config()

    def fetch_models(self, base_url: str, api_key: str) -> list[str]:
        client = OpenAI(base_url=base_url, api_key=api_key)
        try:
            models_response = client.models.list()
            return [m.id for m in models_response.data]
        except Exception as e:
            raise RuntimeError(f"Failed to fetch models: {e}")



    def chat(self, prompt: str | None) -> str:
        with self._lock:
            if prompt:
                # Continuous Subconscious Recall (Auto-RAG)
                recalled = ""
                if hasattr(self, "vector_db"):
                    try:
                        results = self.vector_db.search(prompt, top_k=2)
                        if results:
                            recalled = "\n\n[Subconscious Recall (Archival Memory)]\n"
                            for r in results:
                                recalled += f"- {r['text']}\n"
                    except Exception as e:
                        logging.error(f"Auto-RAG search failed: {e}")
                
                enriched_prompt = f"{prompt}{recalled}"
                self.messages.append({"role": "user", "content": enriched_prompt})
                
            # Sliding window memory pruner to prevent LLM max_context crashes
            # Alert the agent right before compaction so it autosaves status
            if len(self.messages) == 95:
                self.messages.append({
                    "role": "system", 
                    "content": "[CRITICAL ALERT] Memory capacity approaching 100%. A context compaction event is imminent. You MUST use the `update_status` tool NOW to dump your current task list, open problems, and findings to disk, or they will be permanently forgotten."
                })
                publish_sync("agent_chat_chunk", agent_name=self.name, text="\n[bold yellow][!] Auto-Compaction Warning Triggered. Forcing state dump...[/bold yellow]\n")
                
            # Keep the system prompt at index 0, and retain the last 90 messages.
            if len(self.messages) > 100:
                publish_sync("agent_chat_chunk", agent_name=self.name, text="\n[bold red][!] Context Compacted & Archived.[/bold red]\n")
                
                # Auto-Archival: Save the forgotten chunk to Vector DB
                if hasattr(self, "vector_db"):
                    forgotten_chunk = self.messages[1:11]
                    try:
                        archive_text = "Archived Context Chunk:\n" + "\n".join(
                            f"{m.get('role', 'unknown').upper()}: {m.get('content', '')}" for m in forgotten_chunk
                        )
                        self.vector_db.insert(archive_text)
                    except Exception as e:
                        logging.error(f"Auto-Archival failed: {e}")
                
                self.messages = [self.messages[0]] + self.messages[-90:]
                
            client = self.get_client()
            
            def print_chunk(text: str):
                publish_sync("agent_chat_chunk", agent_name=self.name, text=text)
                
            def print_tool(text: str):
                publish_sync("agent_chat_tool", agent_name=self.name, text=text)
            
            internal_loops = 0
            while True:
                import queue
                try:
                    while True:
                        queued_prompt = self.inbox.get_nowait()
                        if queued_prompt is None:
                            return # Cleanly exit thread
                        self.messages.append({"role": "user", "content": f"New queued message received while you were working:\n{queued_prompt}"})
                        print_chunk(f"\n[dim italic]... received and processed a queued message mid-execution ...[/dim italic]\n")
                except queue.Empty:
                    pass
                    
                internal_loops += 1
                if internal_loops > 15:
                    print_chunk("\n[bold red][!] Infinite tool loop detected. Forcing break.[/bold red]")
                    print_chunk("\n[bold yellow][~] Auto-requesting progress update before continuing...[/bold yellow]")
                    self.messages.append({"role": "user", "content": "Please give a brief update on the progress and then continue."})
                    internal_loops = 0
                    # Do not break, we auto-continue
                    # The next iteration will call the API with the user message

                max_retries = 10
                retry_count = 0
                response = None
                
                while True:
                    try:
                        response = client.chat.completions.create(
                            model=self.config.get("model", config_manager.DEFAULT_MODEL),
                            messages=self.messages,
                            tools=get_agent_tools(),
                            stream=False,
                            timeout=120.0
                        )
                        break
                    except Exception as e:
                        retry_count += 1
                        if retry_count > max_retries:
                            raise e
                        sleep_time = min(60, (2 ** retry_count) + random.uniform(0, 1))
                        print_tool(f"\n[bold red][!] API Error: {e}. Retrying in {sleep_time:.1f}s ({retry_count}/{max_retries})...[/bold red]")
                        time.sleep(sleep_time)
                        
                choice = response.choices[0]
                message = choice.message
                
                if hasattr(response, "usage") and response.usage:
                    self.total_tokens += getattr(response.usage, "total_tokens", 0)
                    publish_sync("agent_token_update", agent_name=self.name, total_tokens=self.total_tokens)
                
                if message.content:
                    logging.info(f"Agent response: {message.content}")
                    print_chunk(message.content)
                    self.messages.append({"role": "assistant", "content": message.content})
                    
                if message.tool_calls:
                    self.messages.append(message)  # Add the assistant's tool calls to context
                    
                    for tool_call in message.tool_calls:
                        name = tool_call.function.name
                        args_str = tool_call.function.arguments
                        try:
                            args = json.loads(args_str)
                            
                            logging.info(f"Tool executing: {name}({args})")
                            
                            if name == "write_file":
                                file_path = args.get("path", "unknown")
                                target_file = (self.project_root / file_path) if self.project_root else Path.cwd() / file_path
                                if target_file.exists():
                                    print_tool(f"\n[bold yellow][~] Edited {file_path}[/bold yellow]")
                                else:
                                    print_tool(f"\n[bold green][+] Created {file_path}[/bold green]")
                            elif name == "read_file":
                                file_path = args.get("path", "unknown")
                                print_tool(f"\n> Reading {file_path} ...")
                            else:
                                print_tool(f"\n> Executing {name} ...")
                                
                            # Notice we pass agent=self to enable recursion tracking
                            result = execute_tool(name, args, self.project_root, None, agent=self)
                        except json.JSONDecodeError as je:
                            logging.error(f"JSONDecodeError parsing tool args: {je}")
                            result = f"Error parsing JSON arguments for tool {name}: {je}. Please fix your JSON syntax and try again."
                            
                        logging.info(f"Tool result: {result}")
                        
                        self.messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result
                        })
                else:
                    break
                    
            return ""

class AgentManager:
    """Central orchestrator for all agents, routing and dynamically instantiating subagents."""
    def __init__(self):
        subscribe("ui_chat_request", self.handle_chat_request)
        subscribe("ui_ghost_chat_request", self.handle_ghost_chat_request)
        subscribe("config_reload_requested", self._on_config_reload)
        subscribe("system_command_executed", self._on_system_command)
        
    def _on_system_command(self, command: str, args: str):
        if command == "/stop":
            for name, agent in list(AGENT_REGISTRY.items()):
                agent.inbox.put(None)
                publish_sync("agent_chat_chunk", agent_name="Primary", text=f"\n[bold red]✦ Terminating agent {name}...[/bold red]\n")
                if "[Ghost]" in name:
                    del AGENT_REGISTRY[name]
                    
    def _on_config_reload(self, config: dict):
        for name, agent in AGENT_REGISTRY.items():
            agent.config = config
            agent.rebuild_system_prompt()
            logging.info(f"Hot-reloaded config for live agent: {name}")
        
    def spawn_subagent(self, name: str, project_root: Path | None = None) -> Agent | None:
        if name in AGENT_REGISTRY:
            return AGENT_REGISTRY[name]
            
        config = config_manager.load_config()
        sub_agents = config.get("sub_agents", [])
        sub_config = next((s for s in sub_agents if s.get("name") == name), None)
        
        if not sub_config:
            logging.error(f"Cannot spawn unknown subagent: {name}")
            return None
            
        logging.info(f"Dynamically spawning subagent: {name}")
        sub_agent = Agent(project_root=project_root)
        sub_agent.name = name
        sub_agent.rebuild_system_prompt()
        AGENT_REGISTRY[name] = sub_agent
        threading.Thread(target=self._run_agent_loop, args=(sub_agent,), daemon=True).start()
        
        # Publish creation message to UI
        publish_sync("agent_chat_chunk", agent_name="Primary", text=f"\n[bold green]✦ A new subagent has been awakened: {name}[/bold green]\n")
        return sub_agent

    def spawn_ghost_agent(self, original_agent: Agent) -> Agent:
        ghost_name = f"[Ghost] {original_agent.name}"
        if ghost_name in AGENT_REGISTRY:
            return AGENT_REGISTRY[ghost_name]
            
        logging.info(f"Dynamically spawning ghost agent: {ghost_name}")
        ghost_agent = Agent(project_root=original_agent.project_root)
        ghost_agent.name = ghost_name
        
        # Inherit memory context completely
        import copy
        ghost_agent.messages = copy.deepcopy(original_agent.messages)
        # Re-build system prompt if needed, but it's copied in messages
        
        AGENT_REGISTRY[ghost_name] = ghost_agent
        threading.Thread(target=self._run_agent_loop, args=(ghost_agent,), daemon=True).start()
        
        # Publish creation message to UI
        publish_sync("agent_chat_chunk", agent_name=original_agent.name, text=f"\n[bold magenta]✦ A ghost thread has been spun up to assist you: {ghost_name}[/bold magenta]\n")
        return ghost_agent

    def handle_ghost_chat_request(self, user_input: str, target_agent: str = "Primary"):
        original = AGENT_REGISTRY.get(target_agent)
        if not original:
            # Fallback to normal if it doesn't exist yet
            self.handle_chat_request(user_input, target_agent)
            return
            
        ghost = self.spawn_ghost_agent(original)
        
        # Give the ghost agent awareness of what the original agent is currently doing
        latest_work = [m for m in original.messages if m["role"] in ("assistant", "tool")][-3:]
        if latest_work:
            import json
            awareness = []
            for m in latest_work:
                if m["role"] == "tool":
                    awareness.append(f"Tool Result: {str(m.get('content'))[:200]}...")
                elif "tool_calls" in m and m["tool_calls"]:
                    awareness.append(f"Agent called tools: {[t.function.name for t in m['tool_calls']]}")
                elif "content" in m:
                    awareness.append(f"Agent thought: {str(m['content'])[:200]}...")
                    
            awareness_text = "\n".join(awareness)
            user_input = f"[SYSTEM: For your awareness, your original working copy is currently doing this in the background:\n{awareness_text}]\n\n{user_input}"
            
        ghost.inbox.put(user_input)

    def handle_chat_request(self, user_input: str, target_agent: str = "Primary"):
        agent = AGENT_REGISTRY.get(target_agent)
        
        if not agent and target_agent != "Primary":
            primary = AGENT_REGISTRY.get("Primary")
            root = primary.project_root if primary else None
            agent = self.spawn_subagent(target_agent, root)
            
        if not agent:
            logging.error(f"Target agent {target_agent} could not be resolved.")
            publish_sync("agent_chat_error", agent_name=target_agent, error=f"Agent {target_agent} not found.")
            return
            
        agent.inbox.put(user_input)
        
    def _run_agent_loop(self, agent: "Agent"):
        while True:
            try:
                while True:
                    try:
                        prompt = agent.inbox.get()
                        if prompt is None:
                            publish_sync("agent_chat_chunk", agent_name="Primary", text=f"\n[bold red]✦ The subagent {agent.name} has been terminated and put to rest.[/bold red]\n")
                            return # Cleanly exit thread
                            
                        agent.active_task_start_time = time.time()
                        publish_sync("agent_chat_tool", agent_name=agent.name, text=f"\n[dim][~] {agent.name} began executing a background task...[/dim]")
                        publish_sync("agent_status_changed", agent_name=agent.name, is_active=True)
                        agent.chat(prompt)
                        publish_sync("agent_chat_complete", agent_name=agent.name)
                        
                        elapsed = time.time() - agent.active_task_start_time
                        publish_sync("agent_chat_tool", agent_name=agent.name, text=f"\n[dim][+] {agent.name} finished background task in {elapsed:.1f}s.[/dim]")
                    except Exception as e:
                        logging.exception(f"Error in chat execution for {agent.name}: {e}")
                        publish_sync("agent_chat_error", agent_name=agent.name, error=str(e))
                    finally:
                        agent.active_task_start_time = None
                        publish_sync("agent_status_changed", agent_name=agent.name, is_active=False)
                        if hasattr(agent.inbox, "task_done"):
                            agent.inbox.task_done()
            except Exception as outer_e:
                logging.critical(f"FATAL THREAD ERROR in {agent.name}: {outer_e}. Resurrecting thread...")
                import time
                time.sleep(2)

# Instantiate the singleton router
agent_manager = AgentManager()
