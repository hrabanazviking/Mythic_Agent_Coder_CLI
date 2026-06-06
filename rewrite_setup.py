import re

with open("mythic_agent/ui/screens/setup_screen.py", "r") as f:
    content = f.read()

# 1. Add SubagentEditorWidget class definition
widget_class = """
from textual.widgets import Widget

class SubagentEditorWidget(Widget):
    \"\"\"A massively robust, self-contained widget for editing subagents.\"\"\"
    
    current_subagents = []
    active_subagent_index = 0
    _loading_ui = False
    
    def compose(self):
        from textual.containers import Horizontal, Vertical
        from textual.widgets import Label, Select, Button, Input, TextArea
        
        yield Label("9. Summon Shield-Maidens & Warriors (Sub-Agents):", classes="step")
        with Horizontal(id="subagents-header"):
            yield Select([], id="subagent-select", prompt="Select a Warrior to Edit")
            yield Button("+ Create New Warrior", id="create-subagent-btn", variant="success")
            
        with Vertical(id="subagent-editor"):
            yield Input(id="active-subagent-name", placeholder="Warrior Name")
            with Horizontal(id="subagent-buttons"):
                yield Button("Save Warrior Edits", id="save-active-subagent-btn", variant="warning")
                yield Button("Reset to Default", id="reset-active-subagent-btn", variant="primary")
                yield Button("Delete Warrior", id="delete-active-subagent-btn", variant="error")
            yield TextArea(id="active-subagent-prompt", classes="step")
            
    def set_subagents(self, subagents: list):
        import copy
        from mythic_agent.constants import DEFAULT_SUBAGENTS
        if not subagents:
            self.current_subagents = copy.deepcopy(DEFAULT_SUBAGENTS)
        else:
            self.current_subagents = copy.deepcopy(subagents)
        self.update_subagent_dropdown(0)
        
    def get_subagents(self) -> list:
        return [sa for sa in self.current_subagents if sa.get("name") and sa.get("prompt")]
        
    def update_subagent_dropdown(self, select_index: int = 0):
        try:
            self._loading_ui = True
            select = self.query_one("#subagent-select", Select)
            options = [(sa.get("name", f"Warrior {i}"), i) for i, sa in enumerate(self.current_subagents)]
            select.set_options(options)
            if 0 <= select_index < len(options):
                select.value = select_index
            elif options:
                select.value = 0
            self.load_subagent(select.value if select.value is not None else 0)
        except Exception as e:
            import logging
            logging.error(f"Dropdown update error: {e}")
        finally:
            self._loading_ui = False
            
    def load_subagent(self, index: int):
        try:
            if not self.current_subagents or index < 0 or index >= len(self.current_subagents):
                return
            self.active_subagent_index = index
            sub_agent = self.current_subagents[index]
            
            self._loading_ui = True
            self.query_one("#active-subagent-name").value = sub_agent.get("name", "") or ""
            prompt_ta = self.query_one("#active-subagent-prompt")
            prompt_text = sub_agent.get("prompt", "") or ""
            if hasattr(prompt_ta, "load_text"):
                prompt_ta.load_text(prompt_text)
            else:
                prompt_ta.text = prompt_text
        except Exception as e:
            pass
        finally:
            self._loading_ui = False
            
    def on_select_changed(self, event):
        if getattr(self, "_loading_ui", False) or event.select.id != "subagent-select":
            return
        if event.value is not None and str(event.value) != "Select.BLANK":
            try:
                self.load_subagent(int(getattr(event.value, "value", event.value)))
            except ValueError:
                pass
                
    def on_button_pressed(self, event):
        if event.button.id == "create-subagent-btn":
            self.current_subagents.append({"name": "New Warrior", "prompt": "You are a helpful warrior."})
            self.update_subagent_dropdown(len(self.current_subagents) - 1)
        elif event.button.id == "save-active-subagent-btn":
            idx = self.active_subagent_index
            if 0 <= idx < len(self.current_subagents):
                self.current_subagents[idx]["name"] = self.query_one("#active-subagent-name").value.strip()
                self.current_subagents[idx]["prompt"] = self.query_one("#active-subagent-prompt").text.strip()
                self.update_subagent_dropdown(idx)
                self.app.notify("Warrior updates saved locally!", severity="information", timeout=3)
        elif event.button.id == "reset-active-subagent-btn":
            import copy
            from mythic_agent.constants import DEFAULT_SUBAGENTS
            idx = self.active_subagent_index
            if 0 <= idx < len(self.current_subagents):
                cname = self.current_subagents[idx].get("name", "")
                default = next((sa for sa in DEFAULT_SUBAGENTS if sa["name"] == cname), None)
                if not default:
                    default = next((sa for sa in DEFAULT_SUBAGENTS if cname in sa["name"]), {"name": "New Warrior", "prompt": "You are a helpful warrior."})
                self.current_subagents[idx] = copy.deepcopy(default)
                self.load_subagent(idx)
        elif event.button.id == "delete-active-subagent-btn":
            if len(self.current_subagents) > 1:
                idx = self.active_subagent_index
                if 0 <= idx < len(self.current_subagents):
                    del self.current_subagents[idx]
                    self.update_subagent_dropdown(0)
"""

# Insert widget_class after imports
import_block_end = content.find("class SetupScreen(Screen):")
content = content[:import_block_end] + widget_class + "\n" + content[import_block_end:]

# Replace compose layout
compose_regex = r'yield Label\("9\. Summon Shield-Maidens & Warriors.*?with Horizontal\(id="setup-buttons"\):'
new_compose = r'''yield SubagentEditorWidget(id="subagent-editor-widget")
            
            with Horizontal(id="setup-buttons"):'''
content = re.sub(compose_regex, new_compose, content, flags=re.DOTALL)

# Replace mounting logic for subagents
mount_regex = r'sub_agents = config\.get\("sub_agents", \[\]\).*?self\.update_subagent_dropdown\(\)'
new_mount = r'''sub_agents = config.get("sub_agents", [])
        self.query_one("#subagent-editor-widget").set_subagents(sub_agents)'''
content = re.sub(mount_regex, new_mount, content, flags=re.DOTALL)

# Remove button handlers from main SetupScreen
button_regex = r'elif event\.button\.id == "create-subagent-btn":.*?self\.delete_active_subagent\(\)'
content = re.sub(button_regex, '', content, flags=re.DOTALL)

# Remove old subagent methods from SetupScreen
methods_regex = r'def update_subagent_dropdown.*?def handle_save\(self\) -> None:'
content = re.sub(methods_regex, 'def handle_save(self) -> None:', content, flags=re.DOTALL)

# Update handle_save to grab from widget
save_regex = r'# Save current state of subagents.*?valid_sub_agents = \[\].*?config\["sub_agents"\] = valid_sub_agents'
new_save = r'''# Save current state of subagents
            valid_sub_agents = self.query_one("#subagent-editor-widget").get_subagents()
            config["sub_agents"] = valid_sub_agents'''
content = re.sub(save_regex, new_save, content, flags=re.DOTALL)

# Remove syncing active editor to memory in handle_save
sync_regex = r'# Sync active editor to memory.*?self\.query_one\("#active-subagent-prompt", TextArea\)\.text\.strip\(\)'
content = re.sub(sync_regex, '', content, flags=re.DOTALL)

with open("mythic_agent/ui/screens/setup_screen.py", "w") as f:
    f.write(content)

