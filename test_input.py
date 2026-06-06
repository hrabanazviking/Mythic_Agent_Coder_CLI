from textual.app import App, ComposeResult
from textual.widgets import Input, Label
from textual.containers import Vertical

COMMANDS = ["/setup", "/add", "/commit", "/issue", "/pr", "/status", "/gh", "/test", "/undo", "/doctor", "/flirt", "/btw", "/steer", "/stop", "/tutorial", "/quit", "/help", "/exit"]

class TestApp(App):
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("", id="suggestions", markup=True)
            yield Input(id="chat-input")

    def on_input_changed(self, event: Input.Changed) -> None:
        val = event.value
        lbl = self.query_one("#suggestions", Label)
        if val.startswith("/"):
            matches = [c for c in COMMANDS if c.startswith(val.lower())]
            if matches:
                # Highlight the first match, dim the rest
                formatted = []
                for i, m in enumerate(matches[:7]): # Show up to 7
                    if i == 0:
                        formatted.append(f"[bold cyan]{m}[/bold cyan]")
                    else:
                        formatted.append(f"[dim]{m}[/dim]")
                lbl.update(" ".join(formatted))
            else:
                lbl.update("")
        else:
            lbl.update("")

if __name__ == "__main__":
    app = TestApp()
    app.run(headless=True)
