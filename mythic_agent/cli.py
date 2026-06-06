import sys
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from rich.console import Console
from rich.markdown import Markdown

from .llm import Agent

def print_help(console: Console):
    console.print("[bold cyan]Mythic Agent[/bold cyan] - Commands:")
    console.print("  [green]/help[/green]   - Show this message")
    console.print("  [green]/model[/green]  - Switch models (e.g., /model qwen https://openrouter.ai/api/v1)")
    console.print("  [green]/quit[/green]   - Exit the agent")
    console.print("  [green]/clear[/green]  - Clear conversation history")

import logging
import os

from .tui import run_tui

def main():
    MYTHIC_DIR = Path.home() / ".mythic"
    MYTHIC_DIR.mkdir(exist_ok=True)
    log_file = MYTHIC_DIR / "agent.log"
    logging.basicConfig(
        filename=str(log_file),
        filemode="a",
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    logging.info("Starting Mythic Agent...")
    try:
        run_tui()
    except Exception as e:
        logging.exception("Fatal error in TUI:")
        
        import traceback
        import datetime
        import platform
        import sys
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        crash_file = Path.cwd() / f"mythic_crash_{timestamp}.txt"
        
        try:
            with crash_file.open("w", encoding="utf-8") as f:
                f.write("=== MYTHIC AGENT CRASH REPORT ===\n")
                f.write(f"Date: {datetime.datetime.now().isoformat()}\n")
                f.write(f"Python Version: {sys.version}\n")
                f.write(f"Platform: {platform.platform()}\n")
                f.write("\n=== TRACEBACK ===\n")
                f.write(traceback.format_exc())
            print(f"\n[!] Mythic Agent crashed. A crash report was saved to: {crash_file}\n")
        except Exception:
            pass # If writing the crash report fails, just fall through
            
        raise

if __name__ == "__main__":
    main()
