from textual.app import App, ComposeResult
from textual.widgets import Footer, Static
from textual.containers import Horizontal

class TestApp(App):
    CSS = """
    #bottom-bar {
        dock: bottom;
        height: 1;
        width: 100%;
        background: $primary-background;
    }
    #footer {
        width: 1fr;
    }
    #agent-status {
        width: auto;
        color: yellow;
    }
    """
    BINDINGS = [("f3", "test", "Test")]
    def compose(self) -> ComposeResult:
        yield Static("Main body", id="body")
        with Horizontal(id="bottom-bar"):
            yield Footer(id="footer")
            yield Static(" | Active Agents: Skald (10s)", id="agent-status")

if __name__ == "__main__":
    app = TestApp()
    app.run(headless=True)
