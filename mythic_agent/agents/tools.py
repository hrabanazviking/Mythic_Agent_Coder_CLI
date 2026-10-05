import os
import re
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

from ..core.workspace import resolve_file
from ..core.edits import EditJournal
from ..core.execution import run_process
from ..core.policy import ToolPolicy
from ..core.runtime import TurnCancelled, runtime_settings

_approval_lock = threading.Lock()

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
                        "recipient": {"type": "string", "description": "The name of the agent to send the message to."},
                        "message": {"type": "string", "description": "The message to send."}
                    },
                    "required": ["recipient", "message"],
                    "additionalProperties": False,
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "core_memory_append",
                "description": "Append text to a block in your Core OS Memory.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "block": {"type": "string", "enum": ["persona", "human", "project", "long_term_notes"], "description": "The memory block to append to."},
                        "content": {"type": "string", "description": "The content to append."}
                    },
                    "required": ["block", "content"],
                    "additionalProperties": False,
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "core_memory_replace",
                "description": "Replace the entire content of a block in your Core OS Memory.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "block": {"type": "string", "enum": ["persona", "human", "project", "long_term_notes"], "description": "The memory block to replace."},
                        "content": {"type": "string", "description": "The new content."}
                    },
                    "required": ["block", "content"],
                    "additionalProperties": False,
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "archival_memory_insert",
                "description": "Insert data into your Archival Vector Memory.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "The text to archive."}
                    },
                    "required": ["text"],
                    "additionalProperties": False,
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "knowledge_db_semantic_search",
                "description": "Perform a semantic vector search against Volmarr's personal Knowledge DB (requires gungnir Tailnet access).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The search query."},
                        "limit": {"type": "integer", "description": "Maximum number of results to return (default: 10)."}
                    },
                    "required": ["query"],
                    "additionalProperties": False,
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "knowledge_db_sql_query",
                "description": "Execute a raw read-only SQL query against Volmarr's personal Knowledge DB (PostgreSQL).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sql": {"type": "string", "description": "The SELECT query to execute."}
                    },
                    "required": ["sql"],
                    "additionalProperties": False,
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "archival_memory_search",
                "description": "Search your Archival Vector Memory for relevant information.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The search query."},
                        "top_k": {"type": "integer", "description": "Number of results to return (default 5)."}
                    },
                    "required": ["query"],
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
        },
        {
            "type": "function",
            "function": {
                "name": "clear_context",
                "description": "Wipe your own short-term memory / chat history after completing a massive task to prevent LLM context bloat.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "delegate_parallel_tasks",
                "description": "Delegate tasks to MULTIPLE sub-agents simultaneously. They will process in parallel.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "delegations": {
                            "type": "array",
                            "description": "A list of delegations",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "sub_agent_name": {"type": "string"},
                                    "task_description": {"type": "string"}
                                },
                                "required": ["sub_agent_name", "task_description"]
                            }
                        }
                    },
                    "required": ["delegations"],
                    "additionalProperties": False,
                }
            }
        }
    ]

def prompt_approval_sync(command: str, tui_app, cancel=None, timeout: float = 300) -> bool:
    if not tui_app:
        return False
    cancel = cancel if cancel is not None else threading.Event()
    deadline = time.monotonic() + timeout
    while not _approval_lock.acquire(timeout=0.05):
        if cancel.is_set():
            raise TurnCancelled("Turn cancelled while waiting for approval")
        if time.monotonic() >= deadline:
            return False
    event = threading.Event()
    result = {"approved": False, "active": True}
    decision_lock = threading.Lock()
    modal = None
    def decide(approved):
        with decision_lock:
            if result["active"]:
                result["approved"] = approved
                event.set()
    try:
        if cancel.is_set():
            raise TurnCancelled("Turn cancelled before approval")
        modal = tui_app.call_from_thread(tui_app.action_request_approval, command,
                                          lambda: decide(True), lambda: decide(False))
        while not event.wait(0.05):
            if cancel.is_set():
                raise TurnCancelled("Turn cancelled during approval")
            if time.monotonic() >= deadline:
                return False
        if cancel.is_set():
            raise TurnCancelled("Turn cancelled during approval")
        return result["approved"]
    finally:
        with decision_lock:
            result["active"] = False
        try:
            if modal is not None and hasattr(tui_app, "action_cancel_approval"):
                tui_app.call_from_thread(tui_app.action_cancel_approval, modal)
        finally:
            _approval_lock.release()

def auto_git_commit(root_path: Path, file_path: Path, message: str, *, policy: ToolPolicy | None = None, cancel=None) -> str | None:
    if not (policy or ToolPolicy("read-only")).authorize("git_commit", {"path": str(file_path), "message": message}):
        return "Permission denied for git_commit; no operation was performed."
    if not (root_path / ".git").exists():
        return
    try:
        for command in (["git", "add", str(file_path)], ["git", "commit", "-m", message]):
            result = run_process(command, root_path, cancel=cancel, timeout=15)
            if result.status != "completed":
                return result.render()
    except subprocess.TimeoutExpired:
        import logging
        logging.warning(f"auto_git_commit timed out for {file_path}")
    except Exception as e:
        import logging
        logging.exception(f"auto_git_commit failed: {e}")

def truncate_output(output: str, max_length: int = 20000) -> str:
    """Compatibility wrapper: tool output is no longer silently truncated."""
    return output


def _timeout_output(exc: subprocess.TimeoutExpired) -> str:
    output = exc.stdout or exc.stderr or ""
    return output.decode("utf-8", errors="replace") if isinstance(output, bytes) else output


def _validate_value(value: Any, schema: dict[str, Any], label: str) -> None:
    kind = schema.get("type")
    valid = {
        "string": isinstance(value, str), "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
    }
    if kind and not valid.get(kind, False):
        raise ValueError(f"{label} must be {kind}")
    if kind == "object":
        properties = schema.get("properties", {})
        missing = set(schema.get("required", [])) - value.keys()
        if missing:
            raise ValueError(f"{label} missing required arguments: {', '.join(sorted(missing))}")
        if schema.get("additionalProperties") is False and value.keys() - properties.keys():
            raise ValueError(f"{label} contains unknown arguments")
        for key, item in value.items():
            if key in properties:
                _validate_value(item, properties[key], f"{label}.{key}")
    elif kind == "array" and "items" in schema:
        for index, item in enumerate(value):
            _validate_value(item, schema["items"], f"{label}[{index}]")


def validate_tool_arguments(name: str, arguments: dict[str, Any]) -> None:
    functions = {tool["function"]["name"]: tool["function"] for tool in get_agent_tools()}
    if name not in functions:
        raise ValueError(f"Unknown tool {name}")
    _validate_value(arguments, functions[name]["parameters"], name)


def execute_tool(name: str, arguments: dict[str, Any], project_root: Path | None = None, tui_app: Any = None, agent: Any = None, *, policy: ToolPolicy | None = None) -> str:
    root_path = project_root if project_root is not None else Path.cwd()
    if agent:
        root_path = agent.project_root or root_path
    root_path = Path(root_path).resolve()
    try:
        validate_tool_arguments(name, arguments)
    except ValueError as exc:
        return f"Error: {exc}"
    cancel = getattr(agent, "_cancel", None)
    if cancel is not None and cancel.is_set():
        raise TurnCancelled("Tool cancelled before execution")
    effective_policy = policy or getattr(agent, "tool_policy", None) or ToolPolicy("read-only")
    if not effective_policy.authorize(name, arguments):
        from ..core.secure_api import publish_sync
        publish_sync("agent_tool_denied", agent_name=getattr(agent, "name", "External"), tool_name=name)
        return f"Permission denied for {name}; no operation was performed."
    if cancel is not None and cancel.is_set():
        raise TurnCancelled("Tool cancelled after approval")

    if name == "read_file":
        try:
            path = resolve_file(root_path, arguments["path"])
            return path.read_text(encoding="utf-8")
        except Exception as exc:
            return f"Failed to read file: {exc}"
            
    if name == "write_file":
        try:
            path = resolve_file(root_path, arguments["path"], write=True)
            old_content = path.read_text(encoding="utf-8") if path.exists() else ""
            new_content = arguments["content"]
            import difflib
            diff = list(difflib.ndiff(old_content.splitlines(), new_content.splitlines()))
            added = sum(line.startswith("+ ") for line in diff)
            removed = sum(line.startswith("- ") for line in diff)
            EditJournal(root_path).write(arguments["path"], new_content)
            return f"Successfully wrote to {path} (+{added} lines, -{removed} lines)"
        except Exception as exc:
            return f"Failed to write file: {exc}"

    if name == "run_command":
        command = arguments.get("command", "")
        try:
            settings = runtime_settings(getattr(agent, "config", {}))
            from ..core.secure_api import publish_sync
            def progress(text):
                publish_sync("agent_command_output", agent_name=getattr(agent, "name", "External"), text=text)
            result = run_process(command, root_path, shell=True, cancel=cancel,
                                 timeout=settings["command_timeout"], grace=settings["process_kill_grace"],
                                 progress=progress)
            return result.render()
        except Exception as exc:
            return f"Command failed: {exc}"
            
    if name == "list_dir":
        try:
            path = resolve_file(root_path, arguments["path"])
            return "\n".join(sorted(os.listdir(path)))
        except Exception as exc:
            return f"Failed to list directory: {exc}"

    if name == "replace_file_content":
        try:
            path = resolve_file(root_path, arguments["path"], write=True)
            content = path.read_text(encoding="utf-8")
            target = arguments["target_content"]
            replacement = arguments["replacement_content"]
            if not target or content.count(target) != 1:
                return "Error: target_content must match exactly one nonempty block."
            import difflib
            new_content = content.replace(target, replacement, 1)
            diff = list(difflib.ndiff(content.splitlines(), new_content.splitlines()))
            added = sum(line.startswith("+ ") for line in diff)
            removed = sum(line.startswith("- ") for line in diff)
            EditJournal(root_path).replace(arguments["path"], target, replacement)
            return f"Successfully replaced content in {path} (+{added} lines, -{removed} lines)"
        except Exception as exc:
            return f"Failed to replace content: {exc}"

    if name == "grep_search":
        query = arguments["query"]
        try:
            path = resolve_file(root_path, arguments["path"])
            pattern = re.compile(query)
            results = []
            files_to_search = []
            if path.is_file():
                files_to_search = [path]
            else:
                exclude_dirs = {".git", ".venv", "node_modules", "__pycache__"}
                for root, dirs, files in os.walk(path):
                    dirs[:] = [d for d in dirs if not d.startswith(".") and d not in exclude_dirs]
                    for f in files:
                        if not f.startswith("."):
                            files_to_search.append(Path(root) / f)
                
            for p in files_to_search:
                try:
                    p = resolve_file(root_path, str(p))
                    content = p.read_text(encoding="utf-8")
                    for i, line in enumerate(content.splitlines(), 1):
                        if pattern.search(line):
                            results.append(f"{p.relative_to(root_path)}:{i}:{line.strip()}")
                except (UnicodeDecodeError, ValueError, OSError):
                    continue
            return "\n".join(results) if results else "No matches found."
        except Exception as exc:
            return f"Search failed: {exc}"
            
    if name == "github_execute":
        command = arguments.get("command", "")
        if not command.startswith("gh "):
            return "Error: Command must start with 'gh '"
        try:
            config = getattr(agent, "config", {})
            gh_token = config.get("github", {}).get("token", "")
            env = os.environ.copy()
            if gh_token:
                env["GH_TOKEN"] = gh_token
                
            import shlex
            cmd_list = shlex.split(command)
            settings = runtime_settings(config)
            result = run_process(cmd_list, root_path, cancel=cancel, env=env,
                                 timeout=settings["github_timeout"], grace=settings["process_kill_grace"])
            return result.render()
        except FileNotFoundError:
            return "Error: 'gh' CLI not found. Please install the GitHub CLI."
        except Exception as exc:
            return f"GitHub command failed: {exc}"

    if name == "update_status":
        project = arguments.get("project", "default")
        status = arguments.get("status", "")
        from ..core.config_manager import config_manager
        status_dir = config_manager.MYTHIC_DIR / "status"
        status_dir.mkdir(parents=True, exist_ok=True)
        safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', project)
        status_file = status_dir / f"{safe_name}.md"
        try:
            status_file.write_text(status, encoding="utf-8")
            return f"Successfully auto-saved status for project '{project}' to {status_file}"
        except Exception as e:
            return f"Failed to save status: {e}"

    if name == "delegate_parallel_tasks":
        delegations = arguments.get("delegations", [])
        sender = agent.name if agent else "Primary"
        
        if agent:
            depth = getattr(agent, "_delegation_depth", 0)
            if depth > 5:
                return "Error: Maximum delegation recursion depth exceeded."
        else:
            depth = 0
            
        from .llm import agent_manager
        
        successes = []
        for d in delegations:
            sub_name = d.get("sub_agent_name")
            task = d.get("task_description")
            
            sub_agent = agent_manager.spawn_subagent(sub_name, root_path, policy=effective_policy, tui_app=tui_app)
            if not sub_agent:
                successes.append(f"Failed to spawn {sub_name}.")
                continue
                
            sub_agent._delegation_depth = depth + 1
            sub_agent.inbox.put(f"Task from {sender}:\n{task}")
            successes.append(f"Delegated to {sub_name}.")
            
        return "\n".join(successes)

    if name == "delegate_task":
        sub_name = arguments.get("sub_agent_name", "")
        task = arguments.get("task_description", "")
        sender = arguments.get("sender", agent.name if agent else "Primary")
        
        if agent:
            depth = getattr(agent, "_delegation_depth", 0)
            if depth > 5:
                return "Error: Maximum delegation recursion depth exceeded. You cannot delegate this task any further. You must complete it yourself."
        else:
            depth = 0
            
        from .llm import agent_manager
        
        sub_agent = agent_manager.spawn_subagent(sub_name, root_path, policy=effective_policy, tui_app=tui_app)
        if not sub_agent:
            return f"Error: No sub-agent named {sub_name} is configured or could be spawned."
            
        sub_agent._delegation_depth = depth + 1
            
        sub_agent.inbox.put(f"Task from {sender}:\n{task}")
        
        return f"Task delegated to {sub_name} in the background. It will message you when done."

    if name == "send_message":
        recipient = arguments.get("recipient", "")
        message = arguments.get("message", "")
        sender = arguments.get("sender", agent.name if agent else "Unknown")
        
        from .llm import AGENT_REGISTRY, agent_manager
        from ..core.secure_api import publish_sync
        
        target_agent = None
        if recipient.lower() == "primary":
            # Primary handles messages via the TUI event loop, not the daemon thread
            pass
        else:
            target_agent = agent_manager.spawn_subagent(recipient, root_path, policy=effective_policy, tui_app=tui_app)
            if not target_agent:
                return f"Error: Agent {recipient} not found or not active."
            
        # Push message directly to their inbox if they are a subagent
        if target_agent and hasattr(target_agent, "inbox"):
            target_agent.inbox.put(f"Message from {sender}:\n{message}")
        
        publish_sync("subagent_message_received", sender=sender, recipient=recipient, message=message)
            
        return f"Message sent to {recipient}."
        
    if name == "clear_context":
        if agent:
            agent._handle_clear_history(agent.name)
            return "Context clear requested; stored transcript retained."
        return "Context clear failed."

    if name == "core_memory_append":
        block = arguments.get("block")
        content = arguments.get("content")
        if agent and hasattr(agent, "core_memory"):
            if agent.core_memory.append(block, content):
                return f"Successfully appended to {block} block in core memory."
            return f"Error: Block {block} not found."
        return "Error: Core memory not initialized."

    if name == "core_memory_replace":
        block = arguments.get("block")
        content = arguments.get("content")
        if agent and hasattr(agent, "core_memory"):
            if agent.core_memory.replace(block, content):
                return f"Successfully replaced {block} block in core memory."
            return f"Error: Block {block} not found."
        return "Error: Core memory not initialized."

    if name == "archival_memory_insert":
        text = arguments.get("text")
        if agent and hasattr(agent, "vector_db"):
            agent.vector_db.insert(text)
            return "Successfully inserted into archival memory."
        return "Error: Archival memory not initialized."

    if name == "archival_memory_search":
        query = arguments.get("query")
        top_k = arguments.get("top_k", 5)
        if agent and hasattr(agent, "vector_db"):
            results = agent.vector_db.search(query, top_k=top_k)
            if not results:
                return "No relevant memories found."
            output = "Archival Search Results:\n"
            for idx, r in enumerate(results):
                output += f"{idx+1}. (Score: {r['score']:.2f}) {r['text']}\n"
            return output
        return "Error: Archival memory not initialized."

    if name == "knowledge_db_semantic_search":
        query = arguments.get("query")
        limit = arguments.get("limit", 10)
        
        try:
            import requests
            import psycopg
            
            # 1. Get embedding from Ollama
            embed_url = "http://gungnir:11434/api/embed"
            payload = {"model": "nomic-embed-text", "input": query}
            resp = requests.post(embed_url, json=payload, timeout=10.0)
            resp.raise_for_status()
            vector = resp.json().get("embeddings", [[]])[0]
            if not vector:
                return "Failed to retrieve embeddings from Ollama."
                
            # 2. Connect to PostgreSQL
            pwd_file = Path.home() / ".pg-knowledge-password"
            if pwd_file.exists():
                pwd = pwd_file.read_text().strip()
            else:
                pwd = os.environ.get("PG_KNOWLEDGE_PASSWORD", "")
                if not pwd:
                    return "Error: No database password found. Set PG_KNOWLEDGE_PASSWORD env var or create ~/.pg-knowledge-password"
                
            conn_str = f"postgresql://volmarr:{pwd}@gungnir:5432/knowledge"
            
            # 3. Execute search
            with psycopg.connect(conn_str) as conn:
                with conn.cursor() as cur:
                    sql = """
                    SELECT c.id, c.text, d.title,
                           1 - (c.embedding <=> %s::vector) AS similarity
                    FROM chunks c
                    JOIN documents d ON c.document_id = d.id
                    ORDER BY c.embedding <=> %s::vector
                    LIMIT %s;
                    """
                    # Convert vector to string format pgvector expects
                    vector_str = "[" + ",".join(str(f) for f in vector) + "]"
                    cur.execute(sql, (vector_str, vector_str, limit))
                    rows = cur.fetchall()
                    
            if not rows:
                return "No results found in Knowledge DB."
                
            output = f"Semantic Search Results for '{query}':\n\n"
            for row in rows:
                chunk_id, text, title, sim = row
                output += f"--- Result (Similarity: {sim:.3f}) ---\nDocument: {title}\nChunk ID: {chunk_id}\n\n{text}\n\n"
            return output
        except Exception as e:
            return f"Knowledge DB semantic search failed: {e}"

    if name == "knowledge_db_sql_query":
        sql = arguments.get("sql")
        try:
            import psycopg
            pwd_file = Path.home() / ".pg-knowledge-password"
            if pwd_file.exists():
                pwd = pwd_file.read_text().strip()
            else:
                pwd = os.environ.get("PG_KNOWLEDGE_PASSWORD", "")
                if not pwd:
                    return "Error: No database password found. Set PG_KNOWLEDGE_PASSWORD env var or create ~/.pg-knowledge-password"
                
            conn_str = f"postgresql://volmarr:{pwd}@gungnir:5432/knowledge"
            
            # Enforce read-only
            if any(forbidden in sql.upper() for forbidden in ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "GRANT", "REVOKE"]):
                return "Error: Only read-only SELECT queries are allowed via this tool."
                
            with psycopg.connect(conn_str) as conn:
                with conn.cursor() as cur:
                    cur.execute(sql)
                    try:
                        rows = cur.fetchall()
                        colnames = [desc[0] for desc in cur.description] if cur.description else []
                    except psycopg.ProgrammingError:
                        return "Query executed successfully, but returned no rows."
                        
            if not rows:
                return "Query returned 0 rows."
                
            output = " | ".join(colnames) + "\n"
            output += "-" * len(output) + "\n"
            for row in rows:
                output += " | ".join(str(val) for val in row) + "\n"
                
            return truncate_output(output)
        except Exception as e:
            return f"Knowledge DB SQL query failed: {e}"

    return f"Error: Unknown tool {name}"
