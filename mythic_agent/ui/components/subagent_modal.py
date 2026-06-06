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
            
            from mythic_agent.core.config_manager import config_manager
            config = config_manager.load_config()
            sub_agents = config.get("sub_agents", [])
            primary_name = config.get("primary_agent_name", "Primary Agent")
            options = [(primary_name, "Primary")]
            for sa in sub_agents:
                options.append((sa["name"], sa["name"]))
                
            yield Select(options, prompt="Select Agent", id="target-agent-select")
            with Horizontal():
                yield Button("Select", id="confirm-subagent", variant="primary")
                yield Button("Cancel", id="cancel-subagent", variant="error")
                
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm-subagent":
            select_widget = self.query_one("#target-agent-select", Select)
            selection = select_widget.value
            if selection is not None and selection is not False and selection != Select.BLANK:
                self.dismiss(str(selection))
            else:
                self.dismiss(None)
        elif event.button.id == "cancel-subagent":
            self.dismiss(None)

    def on_select_changed(self, event: Select.Changed) -> None:
        """Auto-confirm when user picks from the dropdown."""
        if event.value is not None and event.value is not False and event.value != Select.BLANK:
            self.dismiss(str(event.value))
