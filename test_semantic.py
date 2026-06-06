from mythic_agent.agents.tools import execute_tool
args = {"query": "Viking history and gods", "limit": 2}
res = execute_tool("knowledge_db_semantic_search", args)
print(res)
