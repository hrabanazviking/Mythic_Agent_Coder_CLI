import re

with open("mythic_agent/ui/screens/setup_screen.py", "r") as f:
    content = f.read()

# 1. Add import
import_patch = "from mythic_agent.ui.components.subagent_editor import SubagentEditorWidget\nfrom mythic_agent.constants"
content = content.replace("from mythic_agent.constants", import_patch)

# 2. Replace layout
start_str = '            yield Label("9. Summon Shield-Maidens & Warriors (Sub-Agents):", classes="step")'
end_str = '            with Horizontal(id="setup-buttons"):'

start_idx = content.find(start_str)
end_idx = content.find(end_str)

new_layout = '            yield SubagentEditorWidget(id="subagent-editor-widget")\n\n'
content = content[:start_idx] + new_layout + content[end_idx:]

# 3. Fix on_mount
old_mount = '''        sub_agents = config.get("sub_agents", [])
        if not sub_agents:
            self.current_subagents = copy.deepcopy(DEFAULT_SUBAGENTS)
        else:
            self.current_subagents = copy.deepcopy(sub_agents)
            
        self.update_subagent_dropdown()'''

new_mount = '''        sub_agents = config.get("sub_agents", [])
        self.query_one("#subagent-editor-widget").set_subagents(sub_agents)'''
content = content.replace(old_mount, new_mount)

# 4. Remove subagent button presses from handle_button_pressed
button_start = content.find('            elif event.button.id == "create-subagent-btn":')
button_end = content.find('            elif event.button.id == "reset-rules-btn":')
content = content[:button_start] + content[button_end:]

# 5. Remove spaghetti methods
methods_to_remove = [
    "    def update_subagent_dropdown(self, select_index: int | None = None) -> None:",
    "    def on_select_changed(self, event: Select.Changed) -> None:",
    "    def load_subagent(self, index: int) -> None:",
    "    def on_input_changed(self, event: Input.Changed) -> None:",
    "    def on_text_area_changed(self, event: TextArea.Changed) -> None:",
    "    def reset_active_subagent(self) -> None:",
    "    def delete_active_subagent(self) -> None:"
]

for method_sig in methods_to_remove:
    start_idx = content.find(method_sig)
    if start_idx != -1:
        # find the next method definition
        next_def_idx = content.find("    def ", start_idx + 10)
        content = content[:start_idx] + content[next_def_idx:]

# 6. Update handle_save
old_save = '''            # Save current state of subagents
            valid_sub_agents = []
            for sa in self.current_subagents:
                if sa.get("name") and sa.get("prompt"):
                    valid_sub_agents.append(sa)
            config["sub_agents"] = valid_sub_agents'''

new_save = '''            # Save current state of subagents
            config["sub_agents"] = self.query_one("#subagent-editor-widget").get_subagents()'''
content = content.replace(old_save, new_save)

old_sync = '''            # Sync active editor to memory
            if hasattr(self, 'active_subagent_index'):
                self.current_subagents[self.active_subagent_index]["name"] = self.query_one("#active-subagent-name", Input).value.strip()
                self.current_subagents[self.active_subagent_index]["prompt"] = self.query_one("#active-subagent-prompt", TextArea).text.strip()
                
            base_url = self.query_one("#provider-select", Select).value'''
content = content.replace(old_sync, '            base_url = self.query_one("#provider-select", Select).value')

with open("mythic_agent/ui/screens/setup_screen.py", "w") as f:
    f.write(content)

