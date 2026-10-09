# Mythic Agent — VS Code Integration (Slice 38)

Mythic ships as a CLI (`mythic`), so VS Code integration is done with
**tasks + keybindings** — no extension host code required. This gives
you `mythic run` on the current file/selection with results shown in a
VS Code panel.

## Prerequisites

- The `mythic` CLI installed and on your `PATH`
  (`pip install mythic-agent`, or run from a source checkout).
- A Mythic workspace (any project directory).

## 1. Add tasks (`.vscode/tasks.json`)

Create `.vscode/tasks.json` in your project (or copy the example from
`editors/vscode-extension/tasks.json` if present):

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Mythic: run on current file",
      "type": "shell",
      "command": "mythic run --format plain --permission ask --workspace ${workspaceFolder} \"Review ${file} and suggest improvements.\"",
      "presentation": {
        "reveal": "always",
        "panel": "dedicated",
        "clear": true
      },
      "problemMatcher": []
    },
    {
      "label": "Mythic: run on selection",
      "type": "shell",
      "command": "mythic run --format plain --permission ask --workspace ${workspaceFolder} \"Explain the following code: ${selectedText}\"",
      "presentation": { "reveal": "always", "panel": "dedicated", "clear": true },
      "problemMatcher": []
    },
    {
      "label": "Mythic: chat",
      "type": "shell",
      "command": "mythic chat --workspace ${workspaceFolder}",
      "presentation": { "reveal": "always", "panel": "dedicated", "focus": true },
      "problemMatcher": []
    }
  ]
}
```

Run them with **Ctrl+Shift+B** alternatives via *Terminal → Run Task…*.

## 2. Keybindings (`.vscode/keybindings.json` or user keybindings)

```json
[
  {
    "key": "ctrl+alt+m",
    "command": "workbench.action.tasks.runTask",
    "args": "Mythic: run on current file",
    "when": "editorTextFocus"
  },
  {
    "key": "ctrl+alt+shift+m",
    "command": "workbench.action.tasks.runTask",
    "args": "Mythic: run on selection",
    "when": "editorHasSelection"
  }
]
```

## 3. Tips

- Use `--permission read-only` for safe review passes, `ask` when you
  want Mythic to propose (and confirm) edits, `trusted` only in a
  scratch workspace.
- Pipe Mythic's JSON output into follow-up tooling with
  `--format json`: `mythic run --format json "summarize ${file}"`.
- For long sessions, run `mythic chat` in the integrated terminal and
  keep a `mythic sessions` window open in a second panel to resume
  transcripts later.

## 4. Going further (future extension)

A full VS Code extension would wrap these tasks with:

- a sidebar webview streaming `mythic run --format jsonl`,
- inline diff application from Mythic's edit proposals,
- workspace trust integration mapping to `--permission` modes.

The task definitions above remain the stable contract such an
extension would build on.
