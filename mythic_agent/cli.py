import sys
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from rich.console import Console
from rich.markdown import Markdown

from .agents.llm import Agent

def print_help(console: Console):
    console.print("[bold cyan]Mythic Agent[/bold cyan] - Commands:")
    console.print("  [green]/help[/green]   - Show this message")
    console.print("  [green]/model[/green]  - Switch models (e.g., /model qwen https://openrouter.ai/api/v1)")
    console.print("  [green]/quit[/green]   - Exit the agent")
    console.print("  [green]/clear[/green]  - Clear conversation history")

from .core.engine import engine
from .ui.main_app import MythicTUI

def main():
    try:
        engine.initialize()
        app = MythicTUI()
        app.run()
    except Exception as e:
        engine.handle_crash(e)
        raise

if __name__ == "__main__":
    main()
