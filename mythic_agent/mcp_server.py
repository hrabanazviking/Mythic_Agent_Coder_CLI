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
from .memory.vector_db import get_vector_provider
from .agents.llm import agent_manager

# Initialize the MCP Server
mcp = FastMCP("Mythic OS MCP Server")

def get_project_root() -> Path:
    config = config_manager.load_config()
    working_dir_str = config.get("working_directory")
    if working_dir_str:
        return Path(working_dir_str).expanduser().resolve()
    default_wd = config_manager.MYTHIC_DIR / "mythic_longhall"
    default_wd.mkdir(parents=True, exist_ok=True)
    return default_wd

@mcp.tool()
def mythic_core_memory_read(agent_name: str = "Primary") -> str:
    """Read the Core OS Memory block for a specific Mythic agent (default: Primary)."""
    core_memory = CoreMemoryManager(agent_name)
    return core_memory.format_for_prompt()

@mcp.tool()
def mythic_core_memory_append(block_name: str, content: str, agent_name: str = "Primary") -> str:
    """
    Append text to a Core OS Memory block.
    Valid blocks: 'persona', 'human', 'project', 'long_term_notes'.
    """
    core_memory = CoreMemoryManager(agent_name)
    success = core_memory.append(block_name, content)
    if success:
        return f"Successfully appended to the {block_name} block for {agent_name}."
    return f"Failed to append. Invalid block name: {block_name}."

@mcp.tool()
def mythic_archival_search(query: str, top_k: int = 5, agent_name: str = "Primary") -> str:
    """Search the Mythic Vector RAG Subconscious memory for semantic matches."""
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
    root_path = get_project_root()
    sub_agent = agent_manager.spawn_subagent(sub_agent_name, root_path)
    
    if not sub_agent:
        return f"Error: No sub-agent named '{sub_agent_name}' could be spawned."
        
    sub_agent.inbox.put(f"Task from {sender_name}:\n{task_description}")
    return f"Successfully spawned '{sub_agent_name}' in the background and assigned the task. It is now executing autonomously."

def main():
    """Entry point for the MCP server."""
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
