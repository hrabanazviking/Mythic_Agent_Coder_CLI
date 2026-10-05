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
        command.add_argument("--resume", help="Resume a workspace session by ID")
        command.add_argument("--permission", choices=["read-only", "ask", "trusted"],
                             help="Override configured policy (defaults: run read-only; chat/TUI ask)")
        if name == "run":
            command.add_argument("prompt", nargs="?", help="Task prompt; omit to read stdin")
            command.add_argument("--format", choices=["plain", "json", "jsonl"], default="plain")
    sessions = commands.add_parser("sessions", help="List or export workspace sessions as JSON")
    sessions.add_argument("--workspace", help="Project directory")
    sessions.add_argument("--export", metavar="SESSION_ID", help="Export a complete redacted transcript")
    args = parser.parse_args(argv)
    if args.command == "sessions":
        from .terminal import session_command
        return session_command(args)
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
        engine.initialize(workspace=getattr(args, "workspace", None),
                          model=getattr(args, "model", None),
                          base_url=getattr(args, "base_url", None),
                          resume=getattr(args, "resume", None),
                          permission=getattr(args, "permission", None))
        app = MythicTUI()
        app.run()
    except Exception as e:
        engine.handle_crash(e)
        return 1
    finally:
        engine.close()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
