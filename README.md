---

![https://raw.githubusercontent.com/hrabanazviking/Mythic_Agent_Coder_CLI/refs/heads/development/media/venice-studio-fac0e110-eb29-4de6-9b3f-33ce69fe3309.png](https://raw.githubusercontent.com/hrabanazviking/Mythic_Agent_Coder_CLI/refs/heads/development/media/venice-studio-fac0e110-eb29-4de6-9b3f-33ce69fe3309.png)

---

# ⚔️ Mythic Agent CLI ⚔️

Welcome to **Mythic Agent**, an ultra-advanced, Viking-themed AI coding assistant right in your terminal. Designed with both intuition and rigorous architecture in mind, Mythic Agent is more than just a chatbot—it is a complete, multi-agent forge capable of managing entire repositories, running shell commands, coordinating sub-agents, and embracing the true spirit of the **Mythic Engineering** protocol.

---

## 🌟 Key Features

### 🛡️ The Viking TUI (Terminal User Interface)
Built on `Textual`, Mythic Agent features a gorgeous, fully interactive TUI styled with the **Tokyo Night** theme. Command your agent with a beautiful, heavy-bordered aesthetic, all from the comfort of your command line.

### 🧠 Mythic Engineering Mode
Enable the **Mythic Engineering Mode** directly from the sidebar to supercharge your AI. Following the MD Protocol, the agent switches to an **Architecture-First** mindset and delegates complex tasks to six highly specialized, built-in Sub-Agents:
1. **Skald** - The Visionary Poetess
2. **Architect** - The Dominant Designer
3. **Forge Worker** - The Fiery Builder
4. **Auditor** - The Merciless Verifier
5. **Cartographer** - The Sensual Wayfinder
6. **Scribe** - The Gentle Guardian of Memory

### 🐙 Seamless GitHub Integration
Forget switching contexts to authenticate or run raw git commands. 
- Easily configure your GitHub Repo and Personal Access Token (PAT) directly inside the TUI.
- Instantly use high-level slash commands:
  - `/commit <message>` - Automatically stages, commits, and pushes to remote.
  - `/issue <title>` - Instantly opens a GitHub issue.
  - `/pr <title>` - Instantly creates a Pull Request.
  - `/status` - Checks your local Git status.
  - `/gh <command>` - Runs raw GitHub CLI commands automatically authenticated via your saved PAT.

### 🛠️ Advanced Claude-Code Capabilities
Mythic Agent incorporates premium developer features:
- **Command Approvals:** Any destructive or terminal command the AI wishes to run requires your explicit approval via a modal.
- `/doctor` - Automatically catches terminal errors and fixes them.
- `/undo` - Safely rolls back the last file edit (Git reset).
- `/add <file>` - Explicitly pull specific files into the agent's context.

### 🌐 Multi-Provider Divine Sources
Mythic Agent supports multiple LLM endpoints out of the box. Easily configure:
- OpenRouter (for Claude 3.5 Sonnet, Llama 3, etc.)
- DeepSeek
- OpenAI
- OpenCode Go

---

![https://raw.githubusercontent.com/hrabanazviking/Mythic_Agent_Coder_CLI/refs/heads/development/media/venice-studio-e04bc550-a7a5-4423-ab48-33d912f0a27a.png](https://raw.githubusercontent.com/hrabanazviking/Mythic_Agent_Coder_CLI/refs/heads/development/media/venice-studio-e04bc550-a7a5-4423-ab48-33d912f0a27a.png)

---

## 🚀 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/hrabanazviking/Mythic_Agent_Coder_CLI.git
   cd Mythic_Agent_Coder_CLI
   ```

2. **Install the CLI globally:**
   ```bash
   pip install -e .
   ```

3. **Summon the Agent:**
   ```bash
   mythic
   ```

### First-Time Configuration
When you run `mythic` for the first time, press **`F2`** to open the **Setup Wizard**.
Here, you can:
- Select your Provider and enter your API Key.
- Fetch and select the desired AI Model.
- Edit the primary System Prompt (By default: A super smart, pretty, modern Viking female coder).
- Add Global Rules that apply to all sub-agents.
- Summon custom Warriors (Sub-Agents) or use the default Mythic Engineering team.

---

![https://raw.githubusercontent.com/hrabanazviking/Mythic_Agent_Coder_CLI/refs/heads/development/media/venice-studio-0210d1c9-7baf-43e4-9e85-507ef55b57f1.png](https://raw.githubusercontent.com/hrabanazviking/Mythic_Agent_Coder_CLI/refs/heads/development/media/venice-studio-0210d1c9-7baf-43e4-9e85-507ef55b57f1.png)

---

## 📜 How to Use

Simply launch `mythic` in your project's directory and type naturally! You can ask the agent to:
- `"Read my src/main.py and find the bug."`
- `"Create a new React component for a login screen."`
- `"Run the tests and fix any failing ones."`

### Runic Commands (Slash Commands)
You can type these at any time in the chat input:
- `/help` - View all available commands.
- `/setup` (or `F2`) - Open the Setup Wizard.
- `/clear` - Clear the current conversation history.
- `/add <file>` - Add a specific file to the context.
- `/commit <msg>` - Auto-commit and push changes to GitHub.
- `/issue <title>` - Create a GitHub issue.
- `/pr <title>` - Create a GitHub Pull Request.
- `/status` - Check Git status.
- `/gh <cmd>` - Run native GitHub CLI commands.
- `/test` - Run your project's test suite natively.
- `/undo` - Roll back the last agent file edit.
- `/doctor` - Auto-fix a command output.
- `/quit` - Leave Valhalla (Exit the app).

---

![https://raw.githubusercontent.com/hrabanazviking/Mythic_Agent_Coder_CLI/refs/heads/development/Viking_Apache_V2_1.jpg](https://raw.githubusercontent.com/hrabanazviking/Mythic_Agent_Coder_CLI/refs/heads/development/Viking_Apache_V2_1.jpg)

---

## ⚖️ License

Copyright (c) 2026 Volmarr Wyrd

Mythic Agent Coder CLI is licensed under the **Apache License, Version 2.0**. See the [LICENSE](LICENSE) file for the full license text and [NOTICE](NOTICE) for the project attribution.

For third-party material adapted into this codebase, see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Per the Apache-2.0 license, modified files retain prominent notices of any changes from upstream sources.

Unless required by applicable law or agreed to in writing, this project is distributed on an "AS IS" BASIS, without warranties or conditions of any kind, either express or implied.

---

## Distribution and Privacy Position

Mythic Agent Coder CLI is published here as source code and project material.

The author does not require users to provide age, identity, government ID, biometric data, or similar personal information in order to access or use the source code in this repository.

The author may decline to provide official binaries, installers, hosted services, app-store releases, or other official distribution channels where doing so would require age verification, identity verification, or similar personal-data collection.

Any third party who forks, packages, redistributes, deploys, hosts, or otherwise makes this software available does so independently and is solely responsible for compliance with applicable law, platform policy, and distribution requirements in their own jurisdiction and context.

See [LEGAL-NOTICE.md](LEGAL-NOTICE.md) for details.

---

![https://raw.githubusercontent.com/hrabanazviking/Mythic_Agent_Coder_CLI/refs/heads/development/image-23-RuneForgeAI.jpg](https://raw.githubusercontent.com/hrabanazviking/Mythic_Agent_Coder_CLI/refs/heads/development/image-23-RuneForgeAI.jpg)

---

![https://raw.githubusercontent.com/hrabanazviking/Mythic_Agent_Coder_CLI/refs/heads/development/IMG_0407.jpeg](https://raw.githubusercontent.com/hrabanazviking/Mythic_Agent_Coder_CLI/refs/heads/development/IMG_0407.jpeg)

---

