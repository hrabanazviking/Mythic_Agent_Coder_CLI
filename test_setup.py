import asyncio
from textual.app import App, ComposeResult
from mythic_agent.ui.screens.setup_screen import SetupScreen

class TestApp(App):
    def on_mount(self) -> None:
        self.push_screen(SetupScreen())

if __name__ == "__main__":
    app = TestApp()
    asyncio.run(app.run_async(headless=True))
