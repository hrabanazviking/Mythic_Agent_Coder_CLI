from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Label, Select, Button

class SubagentSelectionModal(ModalScreen[str]):
    """Modal to select a subagent to chat with."""
    CSS = """
    SubagentSelectionModal {
        align: center middle;
        background: $background 80%;
    }
    #subagent-dialog {
        padding: 1 2;
        width: 60;
        height: auto;
        border: thick $primary;
        background: $surface;
    }
    """
    def compose(self) -> ComposeResult:
        with Vertical(id="subagent-dialog"):
            yield Label("[bold cyan]⚔️ Select Target Warrior (Agent)[/bold cyan]\n")
            
            sub_agents = self.app.agent.config.get("sub_agents", [])
            options = [("Primary Agent", "Primary")]
            for sa in sub_agents:
                options.append((sa["name"], sa["name"]))
                
            yield Select(options, prompt="Select Agent", id="target-agent-select")
            with Horizontal():
                yield Button("Select", id="confirm-subagent", variant="primary")
                yield Button("Cancel", id="cancel-subagent", variant="error")
                
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm-subagent":
            selection = self.query_one("#target-agent-select", Select).value
            if selection and selection != getattr(Select, "BLANK", None):
                self.dismiss(str(selection))
            else:
                self.dismiss(None)
        elif event.button.id == "cancel-subagent":
            self.dismiss(None)
