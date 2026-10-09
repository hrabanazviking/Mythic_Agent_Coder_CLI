# Keyboard Shortcuts

All key bindings are registered in `mythic_agent/ui/shortcuts.py`. The table
below lists the defaults; you can override any binding in your config file
(`~/.mythic/config.json`) under `ui.shortcuts.<action>`, e.g.:

```json
{
  "ui": {
    "shortcuts": {
      "quit": "ctrl+x",
      "command_palette": "ctrl+p"
    }
  }
}
```

Key notation follows the Textual style: `ctrl`, `shift`, `alt`/`meta`
modifiers plus the key name (`ctrl+q`, `f1`, `escape`, `enter`, arrow keys).

## TUI (`mythic tui`)

| Action            | Default        | What it does                          |
|-------------------|----------------|---------------------------------------|
| quit              | `ctrl+q`       | Quit the TUI                          |
| help              | `f1`           | Show the help overlay                 |
| clear             | `ctrl+l`       | Clear the conversation view           |
| focus_input       | `ctrl+i`       | Jump the cursor to the input box      |
| scroll_up         | `shift+up`     | Scroll the chat log up                |
| scroll_down       | `shift+down`   | Scroll the chat log down              |
| new_tab           | `ctrl+t`       | Open a new chat tab                   |
| next_tab          | `ctrl+tab`     | Switch to the next tab                |
| prev_tab          | `ctrl+shift+tab` | Switch to the previous tab          |
| close_tab         | `ctrl+w`       | Close the current tab                 |
| command_palette   | `ctrl+k`       | Open the command palette              |
| toggle_sidebar    | `ctrl+b`       | Show/hide the sidebar                 |

## Terminal loop (`mythic chat` / `mythic run`)

| Action          | Default        | What it does                                  |
|-----------------|----------------|-----------------------------------------------|
| interrupt       | `ctrl+c`       | Interrupt the running turn                    |
| suspend         | `ctrl+z`       | Suspend to the shell (POSIX)                  |
| send            | `enter`        | Send the current line                          |
| send_multiline  | `shift+enter`  | Insert a newline instead of sending           |
| history_prev    | `up`           | Previous line from input history              |
| history_next    | `down`         | Next line from input history                  |
| clear_line      | `ctrl+u`       | Clear the current input line                  |

In-chat slash commands (`/help`, `/model`, `/clear`, `/compact`, `/session`,
`/add`, `/stop`, `/undo`, `/quit`) work regardless of key bindings.

## Terminal fallbacks

Some terminals do not deliver every chord above (notably `shift+enter` and
`ctrl+tab`). When that happens, use the in-chat slash commands or override
the binding in config to something your terminal does deliver.
