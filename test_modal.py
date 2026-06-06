import asyncio
from textual.app import App
from mythic_agent.tui import SubagentSelectionModal
from mythic_agent.llm import Agent
import os
from pathlib import Path

class TestApp(App):
    def on_mount(self):
        self.agent = Agent(Path.cwd())
        self.push_screen(SubagentSelectionModal(), self.done)
    def done(self, val):
        print("Selected:", val)
        self.exit()

if __name__ == "__main__":
    app = TestApp()
    app.run()
