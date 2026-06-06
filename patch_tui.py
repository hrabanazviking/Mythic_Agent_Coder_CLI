import re

with open("mythic_agent/tui.py", "r") as f:
    content = f.read()

# Fix handle_save sub_agents bug and wrap in try/except
handle_save_orig = """    def handle_save(self) -> None:
        # Sync active editor to memory"""
handle_save_new = """    def handle_save(self) -> None:
        try:
            # Sync active editor to memory"""

content = content.replace(handle_save_orig, handle_save_new)

# Fix sub_agents reference and add except block
sub_agents_bug = """        self.app.agent.config["sub_agents"] = sub_agents

        if working_dir:
            from pathlib import Path
            self.app.agent.project_root = Path(working_dir).expanduser().resolve()
        
        self.app.agent.set_model(str(model), str(base_url), str(api_key))
        self.app.switch_screen("main_chat")"""

sub_agents_fix = """        self.app.agent.config["sub_agents"] = valid_sub_agents

        if working_dir:
            from pathlib import Path
            self.app.agent.project_root = Path(working_dir).expanduser().resolve()
        
        self.app.agent.set_model(str(model), str(base_url), str(api_key))
        self.app.switch_screen("main_chat")
        except Exception as e:
            self.app.notify(f"Error saving configuration: {str(e)}", severity="error", timeout=5)"""

content = content.replace(sub_agents_bug, sub_agents_fix)

# Wrap on_button_pressed
button_orig = """    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "fetch-btn":"""
button_new = """    async def on_button_pressed(self, event: Button.Pressed) -> None:
        try:
            if event.button.id == "fetch-btn":"""
content = content.replace(button_orig, button_new)

button_end_orig = """            self.query_one("#primary-agent-name", Input).value = DEFAULT_PRIMARY_NAME
            self.query_one("#system-prompt-input", TextArea).text = DEFAULT_SYSTEM_PROMPT"""
button_end_new = """            self.query_one("#primary-agent-name", Input).value = DEFAULT_PRIMARY_NAME
            self.query_one("#system-prompt-input", TextArea).text = DEFAULT_SYSTEM_PROMPT
        except Exception as e:
            self.app.notify(f"Error handling button press: {str(e)}", severity="error", timeout=5)"""
content = content.replace(button_end_orig, button_end_new)

# Wrap handle_fetch
fetch_orig = """    async def handle_fetch(self) -> None:
        provider_url = self.query_one("#provider-select", Select).value"""
fetch_new = """    async def handle_fetch(self) -> None:
        try:
            provider_url = self.query_one("#provider-select", Select).value"""
content = content.replace(fetch_orig, fetch_new)

fetch_end_orig = """        self.query_one("#loading").display = True
        self.query_one("#fetch-btn").disabled = True
        
        self.fetch_models_bg(provider_url, api_key)"""
fetch_end_new = """        self.query_one("#loading").display = True
        self.query_one("#fetch-btn").disabled = True
        
        self.fetch_models_bg(provider_url, api_key)
        except Exception as e:
            self.query_one("#loading").display = False
            self.query_one("#fetch-btn").disabled = False
            self.app.notify(f"Error preparing fetch: {str(e)}", severity="error", timeout=5)"""
content = content.replace(fetch_end_orig, fetch_end_new)

# Wrap update_subagent_dropdown
update_orig = """    def update_subagent_dropdown(self, select_index: int | None = None) -> None:
        select = self.query_one("#subagent-select", Select)"""
update_new = """    def update_subagent_dropdown(self, select_index: int | None = None) -> None:
        try:
            if not getattr(self, 'current_subagents', None):
                self.current_subagents = copy.deepcopy(DEFAULT_SUBAGENTS)
            select = self.query_one("#subagent-select", Select)"""
content = content.replace(update_orig, update_new)

update_end_orig = """        if select_index is not None:
            self.load_subagent(select_index)
        elif options:
            self.load_subagent(0)"""
update_end_new = """        if select_index is not None:
            self.load_subagent(select_index)
        elif options:
            self.load_subagent(0)
        except Exception as e:
            self._loading_subagent = False
            self.app.notify(f"Error updating dropdown: {str(e)}", severity="error", timeout=5)"""
content = content.replace(update_end_orig, update_end_new)

# Wrap on_select_changed
sel_orig = """    def on_select_changed(self, event: Select.Changed) -> None:
        if getattr(self, '_loading_subagent', False):
            return
        if event.select.id == "subagent-select" and event.value is not None and event.value != getattr(Select, "BLANK", None):
            self.load_subagent(int(event.value))"""
sel_new = """    def on_select_changed(self, event: Select.Changed) -> None:
        if getattr(self, '_loading_subagent', False):
            return
        try:
            if event.select.id == "subagent-select" and event.value is not None and event.value != getattr(Select, "BLANK", None):
                self.load_subagent(int(event.value))
        except Exception as e:
            self.app.notify(f"Error handling selection: {str(e)}", severity="error", timeout=5)"""
content = content.replace(sel_orig, sel_new)

# Wrap load_subagent
load_orig = """    def load_subagent(self, index: int) -> None:
        self.active_subagent_index = index"""
load_new = """    def load_subagent(self, index: int) -> None:
        try:
            if not getattr(self, 'current_subagents', None) or index < 0 or index >= len(self.current_subagents):
                return
            self.active_subagent_index = index"""
content = content.replace(load_orig, load_new)

load_end_orig = """        self._loading_subagent = True
        self.query_one("#active-subagent-name", Input).value = sub_agent["name"]
        self.query_one("#active-subagent-prompt", TextArea).text = sub_agent["prompt"]
        self._loading_subagent = False"""
load_end_new = """        self._loading_subagent = True
        self.query_one("#active-subagent-name", Input).value = sub_agent["name"]
        self.query_one("#active-subagent-prompt", TextArea).text = sub_agent["prompt"]
        self._loading_subagent = False
        except Exception as e:
            self._loading_subagent = False
            self.app.notify(f"Error loading subagent: {str(e)}", severity="error", timeout=5)"""
content = content.replace(load_end_orig, load_end_new)

# Wrap on_input_changed
inp_orig = """    def on_input_changed(self, event: Input.Changed) -> None:
        if getattr(self, '_loading_subagent', False):
            return
        if event.input.id == "active-subagent-name" and hasattr(self, 'active_subagent_index'):"""
inp_new = """    def on_input_changed(self, event: Input.Changed) -> None:
        if getattr(self, '_loading_subagent', False):
            return
        try:
            if event.input.id == "active-subagent-name" and hasattr(self, 'active_subagent_index'):"""
content = content.replace(inp_orig, inp_new)

inp_end_orig = """            self._loading_subagent = True
            select.set_options(options)
            select.value = self.active_subagent_index
            self._loading_subagent = False"""
inp_end_new = """            self._loading_subagent = True
            select.set_options(options)
            select.value = self.active_subagent_index
            self._loading_subagent = False
        except Exception as e:
            self._loading_subagent = False
            self.app.notify(f"Error handling input: {str(e)}", severity="error", timeout=5)"""
content = content.replace(inp_end_orig, inp_end_new)

# Wrap on_text_area_changed
ta_orig = """    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        if getattr(self, '_loading_subagent', False):
            return
        if event.text_area.id == "active-subagent-prompt" and hasattr(self, 'active_subagent_index'):
            self.current_subagents[self.active_subagent_index]["prompt"] = event.text_area.text"""
ta_new = """    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        if getattr(self, '_loading_subagent', False):
            return
        try:
            if event.text_area.id == "active-subagent-prompt" and hasattr(self, 'active_subagent_index'):
                self.current_subagents[self.active_subagent_index]["prompt"] = event.text_area.text
        except Exception as e:
            self.app.notify(f"Error handling text area: {str(e)}", severity="error", timeout=5)"""
content = content.replace(ta_orig, ta_new)

# Wrap reset_active_subagent
res_orig = """    def reset_active_subagent(self) -> None:
        idx = self.active_subagent_index
        default = next((sa for sa in DEFAULT_SUBAGENTS if sa["name"] == self.current_subagents[idx]["name"]), {"name": "New Warrior", "prompt": "You are a helpful warrior."})
        self.current_subagents[idx] = copy.deepcopy(default)
        self.load_subagent(idx)"""
res_new = """    def reset_active_subagent(self) -> None:
        try:
            idx = getattr(self, 'active_subagent_index', 0)
            if not getattr(self, 'current_subagents', None) or idx >= len(self.current_subagents):
                return
            default = next((sa for sa in DEFAULT_SUBAGENTS if sa["name"] == self.current_subagents[idx]["name"]), {"name": "New Warrior", "prompt": "You are a helpful warrior."})
            self.current_subagents[idx] = copy.deepcopy(default)
            self.load_subagent(idx)
        except Exception as e:
            self.app.notify(f"Error resetting subagent: {str(e)}", severity="error", timeout=5)"""
content = content.replace(res_orig, res_new)

# Wrap delete_active_subagent
del_orig = """    def delete_active_subagent(self) -> None:
        if len(self.current_subagents) > 1:
            del self.current_subagents[self.active_subagent_index]
            self.update_subagent_dropdown(0)"""
del_new = """    def delete_active_subagent(self) -> None:
        try:
            if getattr(self, 'current_subagents', None) and len(self.current_subagents) > 1:
                idx = getattr(self, 'active_subagent_index', 0)
                if idx < len(self.current_subagents):
                    del self.current_subagents[idx]
                    self.update_subagent_dropdown(0)
        except Exception as e:
            self.app.notify(f"Error deleting subagent: {str(e)}", severity="error", timeout=5)"""
content = content.replace(del_orig, del_new)

# Re-indent the contents using a quick regex pass
import re
def indent_try_block(match):
    lines = match.group(0).split('\n')
    indented = []
    for i, line in enumerate(lines):
        if i == 0 or i == len(lines)-1: # try or except
            indented.append(line)
        elif line.strip() == "":
            indented.append(line)
        else:
            indented.append("    " + line)
    return '\n'.join(indented)

with open("mythic_agent/tui.py", "w") as f:
    f.write(content)

