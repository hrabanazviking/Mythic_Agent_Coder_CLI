import os
import re
from pathlib import Path

# Important: We must set up the logging or UI correctly to avoid crashes if UI is missing
os.environ["MYTHIC_HEADLESS_MODE"] = "1"

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    raise ImportError("MCP library is not installed. Please install it using `pip install mcp`.")

from .core.config_manager import config_manager
from .memory.core_memory import CoreMemoryManager
from .memory.scopes import scope_for_root
from .memory.vector_db import get_vector_provider
from .agents.llm import agent_manager
from .core.policy import ToolPolicy, policy_mode

# Initialize the MCP Server
mcp = FastMCP("Mythic OS MCP Server")

def machine_policy() -> ToolPolicy:
    return ToolPolicy(policy_mode(config_manager.load_config(), machine=True))

def _permission(name: str, arguments: dict, policy: ToolPolicy | None = None) -> str | None:
    if not (policy or machine_policy()).authorize(name, arguments):
        return f"Permission denied for {name}; no operation was performed. Configure an explicit trusted machine policy to allow mutations."
    return None

def _agent_name(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[\w -]{1,80}", value):
        raise ValueError("Invalid agent name")
    return value

def get_project_root() -> Path:
    from .core.workspace import resolve_workspace
    return resolve_workspace(config=config_manager.load_config())


def _scoped_memory(agent_name: str) -> CoreMemoryManager:
    """Core memory for an agent, namespaced to the current workspace."""
    return CoreMemoryManager(
        _agent_name(agent_name),
        workspace_id=scope_for_root(get_project_root()).workspace_id,
    )

@mcp.tool()
def mythic_core_memory_read(agent_name: str = "Primary") -> str:
    """Read the Core OS Memory block for a specific Mythic agent (default: Primary)."""
    denied = _permission("core_memory_read", {"agent_name": agent_name})
    if denied:
        return denied
    core_memory = _scoped_memory(agent_name)
    return core_memory.format_for_prompt()

@mcp.tool()
def mythic_core_memory_append(block_name: str, content: str, agent_name: str = "Primary") -> str:
    """
    Append text to a Core OS Memory block.
    Valid blocks: 'persona', 'human', 'project', 'long_term_notes'.
    """
    denied = _permission("core_memory_append", {"agent_name": agent_name, "block": block_name, "content": content})
    if denied:
        return denied
    core_memory = _scoped_memory(agent_name)
    success = core_memory.append(block_name, content)
    if success:
        return f"Successfully appended to the {block_name} block for {agent_name}."
    return f"Failed to append. Invalid block name: {block_name}."

@mcp.tool()
def mythic_archival_search(query: str, top_k: int = 5, agent_name: str = "Primary") -> str:
    """Search the Mythic Vector RAG Subconscious memory for semantic matches."""
    denied = _permission("archival_memory_search", {"query": query, "top_k": top_k})
    if denied:
        return denied
    agent_name = _agent_name(agent_name)
    config = config_manager.load_config()
    base_url = config.get("base_url", config_manager.DEFAULT_BASE_URL)
    api_keys = config.get("api_keys", {})
    api_key = api_keys.get(base_url, os.environ.get("OPENAI_API_KEY"))
    provider = config.get("vector_db_provider", "lightweight")
    
    vector_db = get_vector_provider(provider, agent_name, base_url, api_key)
    results = vector_db.search(query, top_k=top_k)
    
    if not results:
        return "No relevant memories found in archival storage."
    
    output = "Archival Search Results:\n"
    for idx, r in enumerate(results):
        output += f"{idx+1}. (Score: {r['score']:.2f}) {r['text']}\n"
    return output

@mcp.tool()
def mythic_archival_insert(text: str, agent_name: str = "Primary") -> str:
    """Insert a new persistent memory into the Mythic Vector RAG Subconscious."""
    denied = _permission("archival_memory_insert", {"text": text, "agent_name": agent_name})
    if denied:
        return denied
    agent_name = _agent_name(agent_name)
    config = config_manager.load_config()
    base_url = config.get("base_url", config_manager.DEFAULT_BASE_URL)
    api_keys = config.get("api_keys", {})
    api_key = api_keys.get(base_url, os.environ.get("OPENAI_API_KEY"))
    provider = config.get("vector_db_provider", "lightweight")
    
    vector_db = get_vector_provider(provider, agent_name, base_url, api_key)
    vector_db.insert(text)
    return "Successfully inserted memory into the Archival Vector Database."

@mcp.tool()
def mythic_update_project_status(project_name: str, status_markdown: str) -> str:
    """Create or update a markdown status file for a specific project."""
    denied = _permission("update_status", {"project": project_name, "status": status_markdown})
    if denied:
        return denied
    status_dir = config_manager.MYTHIC_DIR / "status"
    status_dir.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', project_name)
    status_file = status_dir / f"{safe_name}.md"
    try:
        status_file.write_text(status_markdown, encoding="utf-8")
        return f"Successfully saved status for project '{project_name}' to {status_file}"
    except Exception as e:
        return f"Failed to save project status: {e}"

@mcp.tool()
def mythic_delegate_to_subagent(sub_agent_name: str, task_description: str, sender_name: str = "ExternalAgent") -> str:
    """
    Spawn a Mythic Sub-Agent (e.g. 'Skald', 'Architect', 'Forge Worker') in the background
    and assign them a task. They will run completely autonomously.
    """
    policy = machine_policy()
    denied = _permission("delegate_task", {"sub_agent_name": sub_agent_name, "task_description": task_description}, policy)
    if denied:
        return denied
    root_path = get_project_root()
    sub_agent = agent_manager.spawn_subagent(sub_agent_name, root_path, policy=policy)
    
    if not sub_agent:
        return f"Error: No sub-agent named '{sub_agent_name}' could be spawned."
        
    sub_agent.inbox.put(f"Task from {sender_name}:\n{task_description}")
    return f"Successfully spawned '{sub_agent_name}' in the background and assigned the task. It is now executing autonomously."


# --- Slice 7 (S13): Task lifecycle + capabilities tools ---

@mcp.tool()
def mythic_task_status(task_id: str) -> str:
    """Get the status of a task by ID. Returns state, parent, result/error if finished."""
    denied = _permission("task_status", {"task_id": task_id})
    if denied:
        return denied
    try:
        from .agents.tasks import get_registry
        task = get_registry().get(task_id)
        if not task:
            return f"Error: no task with ID '{task_id}'"
        import json
        return json.dumps({
            "task_id": task.task_id,
            "name": task.name,
            "state": task.state.value,
            "parent_id": task.parent_id,
            "result": str(task.result)[:500] if task.result else None,
            "error": task.error,
        })
    except ImportError:
        return "Error: task registry not available"


@mcp.tool()
def mythic_task_cancel(task_id: str) -> str:
    """Cancel a running task and its children."""
    denied = _permission("task_cancel", {"task_id": task_id})
    if denied:
        return denied
    try:
        from .agents.tasks import get_registry
        get_registry().cancel(task_id)
        return f"Task '{task_id}' cancelled (children included)."
    except ImportError:
        return "Error: task registry not available"


@mcp.tool()
def mythic_capabilities() -> str:
    """List Mythic Agent capabilities: version, interfaces, tools, providers."""
    import json
    try:
        from importlib.metadata import version
        ver = version("mythic-agent")
    except Exception:
        ver = "unknown"
    try:
        from .agents.tools import get_agent_tools
        tools = get_agent_tools()
        tool_names = []
        for t in tools:
            if isinstance(t, dict):
                fn = t.get("function", {})
                tool_names.append(fn.get("name", t.get("name", "?")))
            else:
                tool_names.append(getattr(t, "name", "?"))
    except Exception:
        tool_names = []
    return json.dumps({
        "version": ver,
        "api_version": "1.0",
        "interfaces": ["tui", "terminal-chat", "run-cli", "mcp-stdio"],
        "tools": tool_names,
        "features": ["sessions", "permissions", "tasks", "doctor", "completions"],
    }, indent=2)


def main():
    """Entry point for the MCP server."""
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
