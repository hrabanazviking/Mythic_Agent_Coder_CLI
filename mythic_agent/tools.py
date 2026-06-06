import os
import re
import subprocess
from pathlib import Path
from typing import Any

def get_agent_tools() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read the contents of a file.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to the file to read."}
                    },
                    "required": ["path"],
                    "additionalProperties": False,
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "write_file",
                "description": "Write or overwrite the contents of a file.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to the file."},
                        "content": {"type": "string", "description": "Content to write."}
                    },
                    "required": ["path", "content"],
                    "additionalProperties": False,
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "run_command",
                "description": "Run a shell command in the project directory.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "The shell command to execute."}
                    },
                    "required": ["command"],
                    "additionalProperties": False,
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "list_dir",
                "description": "List the contents of a directory.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to the directory."}
                    },
                    "required": ["path"],
                    "additionalProperties": False,
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "replace_file_content",
                "description": "Replace a specific block of text in a file.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to the file."},
                        "target_content": {"type": "string", "description": "The exact content to replace."},
                        "replacement_content": {"type": "string", "description": "The new content to insert."}
                    },
                    "required": ["path", "target_content", "replacement_content"],
                    "additionalProperties": False,
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "grep_search",
                "description": "Search for a regex pattern within a directory or file.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Directory or file to search in."},
                        "query": {"type": "string", "description": "The regex pattern to search for."}
                    },
                    "required": ["path", "query"],
                    "additionalProperties": False,
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "update_status",
                "description": "Auto-save your current status to keep track of what is going on, current projects, and their statuses.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project": {"type": "string", "description": "The name of the project or task."},
                        "status": {"type": "string", "description": "A comprehensive markdown summary of what is going on and the current status."}
                    },
                    "required": ["project", "status"],
                    "additionalProperties": False,
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "delegate_task",
                "description": "Delegate a task to a configured sub-agent.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sub_agent_name": {"type": "string", "description": "The name of the sub-agent."},
                        "task_description": {"type": "string", "description": "Detailed description of the task."}
                    },
                    "required": ["sub_agent_name", "task_description"],
                    "additionalProperties": False,
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "send_message",
                "description": "Send a message to another agent (e.g. back to Primary, or to a sub-agent).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "recipient": {"type": "string", "description": "Name of the agent to receive the message (use 'Primary' for the main user agent)."},
                        "message": {"type": "string", "description": "The message content."}
                    },
                    "required": ["recipient", "message"],
                    "additionalProperties": False,
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "github_execute",
                "description": "Run a GitHub CLI (gh) command. e.g. 'gh issue list' or 'gh pr create'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "The gh command to run (must start with gh)."}
                    },
                    "required": ["command"],
                    "additionalProperties": False,
                }
            }
        }
    ]

def prompt_approval_sync(command: str, tui_app) -> bool:
    if not tui_app:
        return True # Fallback if UI not connected
        
    if tui_app.agent.config.get("auto_accept_permissions", False):
        return True
        
    import threading
    event = threading.Event()
    result = {"approved": False}
    
    def on_approve():
        result["approved"] = True
        event.set()
        
    def on_reject():
        result["approved"] = False
        event.set()
        
    tui_app.call_from_thread(tui_app.action_request_approval, command, on_approve, on_reject)
    event.wait()
    return result["approved"]

def auto_git_commit(root_path: Path, file_path: Path, message: str) -> None:
    if not (root_path / ".git").exists():
        return
    try:
        subprocess.run(["git", "add", str(file_path)], cwd=str(root_path), capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", message], cwd=str(root_path), capture_output=True, check=True)
    except Exception as e:
        import logging
        logging.exception(f"auto_git_commit failed: {e}")

def execute_tool(name: str, arguments: dict[str, Any], project_root: Path | None = None, tui_app: Any = None) -> str:
    root_path = project_root if project_root is not None else Path.cwd()
    
    if name == "read_file":
        path = root_path / arguments.get("path", "")
        try:
            return path.read_text(encoding="utf-8")
        except Exception as exc:
            return f"Failed to read file: {exc}"
            
    if name == "write_file":
        path = root_path / arguments.get("path", "")
        try:
            auto_git_commit(root_path, path, f"Auto-backup before write_file to {path.name}")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(arguments.get("content", ""), encoding="utf-8")
            auto_git_commit(root_path, path, f"Agent wrote {path.name}")
            return f"Successfully wrote to {path}"
        except Exception as exc:
            return f"Failed to write file: {exc}"
            
    if name == "run_command":
        command = arguments.get("command", "")
        if tui_app:
            approved = prompt_approval_sync(command, tui_app)
            if not approved:
                return f"Command execution REJECTED by the user."
        try:
            result = subprocess.run(
                command, shell=True, cwd=str(root_path),  # nosec B602
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )
            return result.stdout or f"Command executed with exit code {result.returncode}"
        except Exception as exc:
            return f"Command failed: {exc}"
            
    if name == "list_dir":
        path = root_path / arguments.get("path", ".")
        try:
            items = os.listdir(path)
            return "\n".join(sorted(items))
        except Exception as exc:
            return f"Failed to list directory: {exc}"
            
    if name == "replace_file_content":
        path = root_path / arguments.get("path", "")
        target = arguments.get("target_content", "")
        replacement = arguments.get("replacement_content", "")
        try:
            content = path.read_text(encoding="utf-8")
            if target not in content:
                return "Error: target_content not found in the file."
            if content.count(target) > 1:
                return "Error: target_content found multiple times. Please provide a more unique block."
            
            auto_git_commit(root_path, path, f"Auto-backup before replace_file_content in {path.name}")
            new_content = content.replace(target, replacement)
            path.write_text(new_content, encoding="utf-8")
            auto_git_commit(root_path, path, f"Agent replaced content in {path.name}")
            return f"Successfully replaced content in {path}"
        except Exception as exc:
            return f"Failed to replace content: {exc}"
            
    if name == "grep_search":
        path = root_path / arguments.get("path", "")
        query = arguments.get("query", "")
        try:
            import re
            pattern = re.compile(query)
            results = []
            if path.is_file():
                files_to_search = [path]
            else:
                files_to_search = path.rglob("*")
                
            for p in files_to_search:
                if p.is_file() and not p.name.startswith("."):
                    try:
                        content = p.read_text(encoding="utf-8")
                        for i, line in enumerate(content.splitlines(), 1):
                            if pattern.search(line):
                                results.append(f"{p.relative_to(root_path)}:{i}:{line.strip()}")
                    except UnicodeDecodeError:
                        pass
            return "\n".join(results) if results else "No matches found."
        except Exception as exc:
            return f"Search failed: {exc}"
            
    if name == "github_execute":
        command = arguments.get("command", "")
        if not command.startswith("gh "):
            return "Error: Command must start with 'gh '"
        try:
            tui = getattr(tui_app, "app", tui_app)
            config = tui.agent.config if tui else {}
            gh_token = config.get("github", {}).get("token", "")
            env = os.environ.copy()
            if gh_token:
                env["GH_TOKEN"] = gh_token
                
            import shlex
            cmd_list = shlex.split(command)
            result = subprocess.run(
                cmd_list, cwd=str(root_path), 
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                env=env
            )
            return result.stdout or f"GitHub command executed with exit code {result.returncode}"
        except Exception as exc:
            return f"GitHub command failed: {exc}"

    if name == "update_status":
        project = arguments.get("project", "default")
        status = arguments.get("status", "")
        status_dir = Path.home() / ".mythic" / "status"
        status_dir.mkdir(parents=True, exist_ok=True)
        safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', project)
        status_file = status_dir / f"{safe_name}.md"
        try:
            status_file.write_text(status, encoding="utf-8")
            return f"Successfully auto-saved status for project '{project}' to {status_file}"
        except Exception as e:
            return f"Failed to save status: {e}"

    if name == "delegate_task":
        sub_name = arguments.get("sub_agent_name", "")
        task = arguments.get("task_description", "")
        sender = arguments.get("sender", "Primary")
        
        tui = getattr(tui_app, "app", tui_app)
        config = tui.agent.config if tui else {}
        sub_agents = config.get("sub_agents", [])
        sub_config = next((s for s in sub_agents if s.get("name") == sub_name), None)
        
        if not sub_config:
            return f"Error: No sub-agent named {sub_name} is configured."
            
        import threading
        def run_subagent():
            from .llm import Agent, AGENT_REGISTRY
            if sub_name not in AGENT_REGISTRY:
                sub_agent = Agent(project_root=root_path)
                sub_agent.name = sub_name
                
                sub_system_prompt = sub_config.get("prompt", "You are a helpful sub-agent.")
                global_rules = config.get("global_rules", "").strip()
                status_rule = "You MUST use the `update_status` tool to autosave your current project status and keep track of what is going on."
                if global_rules:
                    sub_system_prompt += f"\n\nGLOBAL RULES (You must strictly follow these):\n{global_rules}\n- {status_rule}"
                else:
                    sub_system_prompt += f"\n\nGLOBAL RULES:\n- {status_rule}"
                    
                sub_agent.messages = [{"role": "system", "content": sub_system_prompt}]
                sub_agent.tui_app = tui
                AGENT_REGISTRY[sub_name] = sub_agent
            else:
                sub_agent = AGENT_REGISTRY[sub_name]
                
            if tui:
                tui.call_from_thread(tui.update_agent_status, sub_name, True)
                
            def noop_print(chunk): pass
            def noop_tool(chunk): pass
            
            try:
                sub_agent.chat(f"Task from {sender}:\n{task}", noop_print, noop_tool)
            finally:
                if tui:
                    tui.call_from_thread(tui.update_agent_status, sub_name, False)
                    
        threading.Thread(target=run_subagent, daemon=True).start()
        return f"Task delegated to {sub_name} in the background. It will message you when done."

    if name == "send_message":
        recipient = arguments.get("recipient", "")
        message = arguments.get("message", "")
        sender = arguments.get("sender", "Unknown")
        
        from .llm import AGENT_REGISTRY
        if recipient not in AGENT_REGISTRY:
            return f"Error: Agent {recipient} not found or not active."
            
        target_agent = AGENT_REGISTRY[recipient]
        target_agent.messages.append({"role": "user", "content": f"Message from {sender}:\n{message}"})
        
        if recipient == "Primary" and tui_app:
            tui_app.call_from_thread(tui_app.notify_message, message, sender)
            
        return f"Message sent to {recipient}."

    return f"Error: Unknown tool {name}"
