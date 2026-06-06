from mythic_agent.tui import MythicTUI
from mythic_agent.llm import Agent
agent = Agent()
app = MythicTUI(agent)
app.run(headless=True, inline=True)
