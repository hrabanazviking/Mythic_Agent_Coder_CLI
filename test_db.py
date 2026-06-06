from mythic_agent.agents.tools import execute_tool
args = {"sql": "SELECT 'ok', count(*) AS docs FROM documents;"}
res = execute_tool("knowledge_db_sql_query", args)
print(res)
