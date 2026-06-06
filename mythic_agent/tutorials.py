TUTORIALS = {
    "vibecoding": """# 🎸 The Art of Vibe Coding
Vibe coding is the practice of programming with AI where you focus on the *intent* and *architecture* (the vibe) rather than the strict syntax. 
When using Mythic Agent, you are a Vibe Coder. You tell the agent what you want to achieve, review the proposed changes, and orchestrate the team of sub-agents to build complex systems.

## How to Vibe Code with Mythic:
1. **Be Descriptive:** Don't just say "fix it". Say "the TUI layout is broken on the right side, fix the flexbox."
2. **Delegate:** Use sub-agents. Have a `Scribe` write your docs while a `Cartographer` maps out the architecture.
3. **Use the tools:** Use `/commit`, `/status`, and `/undo` to quickly version control your vibes without leaving the chat.
4. **Don't sweat the syntax:** Let the AI write the boilerplate. You are the architect.
""",
    
    "mythic": """# ⚔️ Using Mythic Agent
Mythic Agent is an advanced autonomous CLI coder.

## Quick Start
1. Press `F2` to open the Setup Wizard. Configure your API key and Working Directory.
2. Type `/help` to see all commands.
3. Chat naturally to generate code, read files, or run terminal commands.

## Advanced Features
- **Sub-agents:** Press `F3` to switch your active chat to a sub-agent.
- **Auto-accept:** Turn on 'Auto-accept security permissions' in the Setup menu to let the AI run commands without asking.
- **Mythic Engineering Mode:** Applies rigid, structured architecture rules to the AI's output.
""",

    "theory": """# 🧠 Basic Coding Theory
No matter what language you use, some concepts are universal.

## 1. Variables and Memory
Variables are boxes that hold data. The computer stores these boxes in RAM. In strongly-typed languages, a box can only hold one type of thing (like an integer). In dynamically-typed languages, the box can change types.

## 2. Control Flow
Code executes top-to-bottom unless you change the flow.
* **If/Else Statements:** Make decisions (Branching).
* **Loops (For/While):** Repeat code until a condition is met.

## 3. Functions
Functions are reusable blocks of code. You give them inputs (parameters), they do work, and they return outputs. They keep your code DRY (Don't Repeat Yourself).
""",

    "python": """# 🐍 Python Basics
Python is dynamically typed and uses whitespace (indentation) to define code blocks.

## The Basics
```python
# Variables and Data Types
name = "Viking"  # string
age = 30         # int
is_coder = True  # boolean

# Functions
def greet(user_name):
    print(f"Hail, {user_name}!")

# Control Flow
if age >= 18:
    greet(name)
```

## Why Python?
Python is the lingua franca of AI, machine learning, and rapid scripting. It emphasizes readability.
""",

    "go": """# 🐹 Go (Golang) Basics
Go is a statically typed, compiled language designed by Google for high-concurrency systems.

## The Basics
```go
package main

import "fmt"

func main() {
    // Variables
    name := "Viking" // Type inferred as string
    age := 30
    
    // Control Flow
    if age >= 18 {
        greet(name)
    }
}

func greet(userName string) {
    fmt.Printf("Hail, %s!\\n", userName)
}
```

## Why Go?
Go compiles directly to fast machine code, has garbage collection, and makes handling thousands of parallel tasks (Goroutines) incredibly simple.
"""
}
