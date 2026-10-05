"""CLI entry point; optional front ends are loaded only when requested."""

import argparse
import sys
from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rich.console import Console

def print_help(console: "Console") -> None:
    console.print("[bold cyan]Mythic Agent[/bold cyan] - Commands:")
    console.print("  [green]/help[/green]   - Show this message")
    console.print("  [green]/model[/green]  - Switch models (e.g., /model qwen https://openrouter.ai/api/v1)")
    console.print("  [green]/quit[/green]   - Exit the agent")
    console.print("  [green]/clear[/green]  - Clear conversation history")

def package_version() -> str:
    """Use installed metadata without initializing settings or workers."""
    try:
        return version("mythic-agent")
    except PackageNotFoundError:
        return "0.1.0 (source checkout)"

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mythic", description="Mythic Agent: a local AI coding harness."
    )
    parser.add_argument("--version", action="version", version=package_version())
    parser.parse_args(argv)
    try:
        from .ui.main_app import MythicTUI
    except ImportError as exc:
        sys.stderr.write(
            "The terminal UI requires the tui extra. "
            "Install with: pip install 'mythic-agent[tui]'\n"
        )
        sys.stderr.write(f"Unavailable dependency: {exc.name}\n")
        return 2

    from .core.engine import engine
    try:
        engine.initialize()
        app = MythicTUI()
        app.run()
    except Exception as e:
        engine.handle_crash(e)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
