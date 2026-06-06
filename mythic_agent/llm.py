import json
import os
from pathlib import Path
from typing import Any, Callable

from openai import OpenAI

from .tools import execute_tool, get_agent_tools

# Global registry of live sub-agent instances keyed by name.
AGENT_REGISTRY: dict[str, "Agent"] = {}

MYTHIC_DIR = Path.home() / ".mythic"
MYTHIC_DIR.mkdir(exist_ok=True)
CONFIG_FILE = MYTHIC_DIR / "config.json"

DEFAULT_MODEL = "deepseek-chat"
DEFAULT_BASE_URL = "https://api.deepseek.com/v1"

def load_config() -> dict[str, Any]:
    old_config = Path.home() / ".mythic_config.json"
    if old_config.exists() and not CONFIG_FILE.exists():
        import shutil
        shutil.copy2(old_config, CONFIG_FILE)
        
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "model": DEFAULT_MODEL, 
        "base_url": DEFAULT_BASE_URL,
        "api_keys": {}
    }

def save_config(config: dict[str, Any]) -> None:
    # Save with 0600 permissions
    CONFIG_FILE.write_text(json.dumps(config, indent=2))
    CONFIG_FILE.chmod(0o600)

def get_user_context(config: dict[str, Any]) -> str:
    user_name = config.get("user_name", "").strip()
    user_data = config.get("user_data", "").strip()
    if not user_name and not user_data:
        return ""
    
    context = "\n\nUSER CONTEXT:\n"
    if user_name:
        context += f"The user's name is {user_name}.\n"
    if user_data:
        context += f"Data about the user:\n{user_data}\n"
    return context

class Agent:
    def __init__(self, project_root: Path | None = None):
        self.config = load_config()
        self.project_root = project_root
        
        working_dir_str = self.config.get("working_directory")
        if working_dir_str:
            self.project_root = Path(working_dir_str).expanduser().resolve()
        elif not self.project_root:
            default_wd = MYTHIC_DIR / "mythic_longhall"
            default_wd.mkdir(parents=True, exist_ok=True)
            self.project_root = default_wd
            
        self.total_tokens = 0
        if "api_keys" not in self.config:
            self.config["api_keys"] = {}
        system_prompt = self.config.get("system_prompt", "You are Mythic, an expert AI programming assistant. You have access to local tools. ALWAYS use tools to accomplish tasks (e.g. read_file, write_file, replace_file_content, run_command). Do not tell the user to run commands; run them yourself.")
        
        global_rules = self.config.get("global_rules", "").strip()
        status_rule = "You MUST use the `update_status` tool to autosave your current project status and keep track of what is going on."
        if global_rules:
            system_prompt += f"\n\nGLOBAL RULES (You must strictly follow these):\n{global_rules}\n- {status_rule}"
        else:
            system_prompt += f"\n\nGLOBAL RULES:\n- {status_rule}"
            
        if self.config.get("mythic_engineering_mode"):
            system_prompt += "\n\nMYTHIC ENGINEERING MODE PROTOCOL ACTIVATED:"
            system_prompt += "\nYou are the orchestrator of an Architecture-First, intuition-led, document-guided development process."
            system_prompt += "\n1. Vision before implementation. Architecture before patching."
            system_prompt += "\n2. MD Protocol: Markdown as living memory (README.md, ARCHITECTURE.md, etc)."
            system_prompt += "\n3. ALWAYS delegate and consult your 6 included Sub-Agents (Skald, Architect, Forge Worker, Auditor, Cartographer, Scribe) using the delegate_task tool when tackling large problems."
            system_prompt += "\n4. Reality outranks theory. Refactor by ownership. Invariants matter."
            
        system_prompt += get_user_context(self.config)
            
        self.messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        self.inject_mythic_agents()
            
    def inject_mythic_agents(self) -> None:
        """Inject the 6 core Mythic Engineering sub-agents if they don't exist."""
        mythic_agents = [
            {"name": "Architect", "prompt": "You are the Architect. You design the overall software architecture, file structure, and technical vision. Always plan before coding. Enforce invariants."},
            {"name": "Skald", "prompt": "You are the Skald. You act as the Project Manager and communicator, summarizing status, maintaining living memory (MD Protocol), and keeping the team aligned."},
            {"name": "Forge_Worker", "prompt": "You are the Forge Worker. You write robust, optimized, and secure code based on the Architect's designs. You build the components."},
            {"name": "Auditor", "prompt": "You are the Auditor. You review code for security vulnerabilities, memory leaks, edge cases, and compliance with the Architect's invariants."},
            {"name": "Cartographer", "prompt": "You are the Cartographer. You map out the system, dependencies, and external APIs. You handle deep codebase search and context gathering."},
            {"name": "Scribe", "prompt": "You are the Scribe. You write beautiful, comprehensive documentation, API references, and inline comments."}
        ]
        
        current_agents = self.config.get("sub_agents", [])
        existing_names = {a.get("name") for a in current_agents}
        
        added = False
        for agent in mythic_agents:
            if agent["name"] not in existing_names:
                current_agents.append(agent)
                added = True
                
        if added:
            self.config["sub_agents"] = current_agents
            self.save_config()
        
    def save_config(self) -> None:
        save_config(self.config)
        
    def get_api_key(self, base_url: str) -> str | None:
        """Get the stored API key for a given base_url, or fallback to env vars."""
        stored_key = self.config["api_keys"].get(base_url)
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
        base_url = self.config.get("base_url", DEFAULT_BASE_URL)
        api_key = self.get_api_key(base_url)
        
        if not api_key:
            print("[Warning] No API key found.")
            
        return OpenAI(
            base_url=base_url,
            api_key=api_key or "sk-dummy"
        )
        
    def set_model(self, model: str, base_url: str, api_key: str | None = None) -> None:
        self.config["model"] = model
        self.config["base_url"] = base_url
        if api_key:
            self.config["api_keys"][base_url] = api_key
        save_config(self.config)

    def fetch_models(self, base_url: str, api_key: str) -> list[str]:
        """Fetch the list of available models from a provider's OpenAI-compatible endpoint."""
        client = OpenAI(base_url=base_url, api_key=api_key)
        try:
            models_response = client.models.list()
            return [m.id for m in models_response.data]
        except Exception as e:
            raise RuntimeError(f"Failed to fetch models: {e}")

    def chat(self, prompt: str | None, print_chunk: Callable[[str], None], print_tool: Callable[[str], None]) -> str:
        if prompt:
            self.messages.append({"role": "user", "content": prompt})
        client = self.get_client()
        
        while True:
            max_retries = 3
            retry_count = 0
            response = None
            
            while True:
                try:
                    response = client.chat.completions.create(
                        model=self.config.get("model", DEFAULT_MODEL),
                        messages=self.messages,
                        tools=get_agent_tools(),
                        stream=False
                    )
                    break
                except Exception as e:
                    retry_count += 1
                    if retry_count > max_retries:
                        raise e
                    import time
                    print_tool(f"\n[bold red][!] API Error: {e}. Retrying {retry_count}/{max_retries}...[/bold red]")
                    time.sleep(2)
                    
            choice = response.choices[0]
            message = choice.message
            
            if hasattr(response, "usage") and response.usage:
                self.total_tokens += getattr(response.usage, "total_tokens", 0)
                tui = getattr(self, "tui_app", None)
                if tui:
                    tui.call_from_thread(tui.update_token_count, self.total_tokens)
            
            if message.content:
                import logging
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
                    except json.JSONDecodeError:
                        args = {}
                        
                    import logging
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
                    result = execute_tool(name, args, self.project_root, getattr(self, "tui_app", None))
                    logging.info(f"Tool result: {result}")
                    
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result
                    })
            else:
                break
                
        return ""
