"""Tool declaration schemas shared by the agent layer and core validation.

``get_agent_tools()`` used to live in ``mythic_agent.agents.tools``; it is
pure declaration data (JSON-schema-style tool definitions, no agent logic),
but ``core/validation.py`` needs the schemas to validate tool arguments
*before* execution.  Keeping the table here removes the core -> agents
dependency inversion while ``agents.tools`` re-exports the same symbol, so
all existing import sites keep working unchanged.
"""

from __future__ import annotations

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
