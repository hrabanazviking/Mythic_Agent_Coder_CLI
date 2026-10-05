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
    commands = parser.add_subparsers(dest="command")
    for name, help_text in [("run", "Run one task for humans or AI callers"),
                            ("chat", "Start the terminal conversation loop"),
                            ("tui", "Start the optional Textual interface")]:
        command = commands.add_parser(name, help=help_text)
        command.add_argument("--workspace", type=str, help="Project directory (defaults to settings/current directory)")
        command.add_argument("--model", help="Model override for this invocation")
        command.add_argument("--base-url", help="OpenAI-compatible endpoint override")
        if name != "tui":
            command.add_argument("--permission", choices=["read-only", "ask", "trusted"],
                                 help="Tool policy (run: read-only; chat: ask)")
        if name == "run":
            command.add_argument("prompt", nargs="?", help="Task prompt; omit to read stdin")
            command.add_argument("--format", choices=["plain", "json", "jsonl"], default="plain")
    args = parser.parse_args(argv)
    if args.command in {"run", "chat"}:
        from .terminal import chat_loop, run_once
        return run_once(args) if args.command == "run" else chat_loop(args)
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
        if args.command == "tui":
            from .agents.llm import AGENT_REGISTRY
            from .core.workspace import resolve_workspace
            primary = AGENT_REGISTRY["Primary"]
            primary.project_root = resolve_workspace(args.workspace, primary.config)
            if args.model:
                primary.config["model"] = args.model
            if args.base_url:
                primary.config["base_url"] = args.base_url
        app = MythicTUI()
        app.run()
    except Exception as e:
        engine.handle_crash(e)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
