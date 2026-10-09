# Editor Integrations (Slice 38)

Mythic is CLI-first; these integrations call `mythic run` / `mythic chat`
from your editor.

| Editor | Integration | Path |
|---|---|---|
| VS Code | Tasks + keybindings (no extension host code needed) | `vscode-extension/README.md` |
| Vim / Neovim | `:MythicRun`, `:MythicRunBuffer`, `<Leader>mr` mappings | `vim-plugin/mythic.vim` |

Both assume the `mythic` CLI is on your `PATH`.
