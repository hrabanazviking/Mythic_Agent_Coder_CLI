"""CLI entry point; optional front ends are loaded only when requested."""

import argparse
import sys
from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rich.console import Console

def review_command(args: argparse.Namespace) -> int:
    """Handler for ``mythic review PATH`` (Slice 44)."""
    import json
    from pathlib import Path
    from .tools.review import (
        SEVERITIES, format_issues, review_file, review_project, summary_counts,
    )

    target = Path(args.path)
    if not target.exists():
        print(f"mythic review: path not found: {args.path}", file=sys.stderr)
        return 2
    min_level = SEVERITIES.index(args.severity)
    if target.is_dir():
        results = review_project(target)
        issues = [i for per_file in results.values() for i in per_file]
    else:
        issues = review_file(target)
    issues = [i for i in issues if SEVERITIES.index(i.severity) >= min_level]
    if args.json:
        print(json.dumps([
            {"severity": i.severity, "line": i.line, "message": i.message,
             "check": i.check, "path": i.path}
            for i in issues
        ], indent=2))
    else:
        print(format_issues(issues))
        counts = summary_counts(issues)
        print(f"\n{len(issues)} issue(s): "
              + ", ".join(f"{counts[s]} {s}" for s in SEVERITIES))
    return 1 if any(i.severity == "error" for i in issues) else 0


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


def theme_command(args: "argparse.Namespace") -> int:
    """Implement ``mythic theme --list`` / ``mythic theme --set NAME``."""
    from .core.config_manager import config_manager
    from .ui.themes import get_theme, is_valid_theme, list_themes
    if args.list or not args.set:
        config = config_manager.load_config()
        current = (config.get("ui") or {}).get("theme", "tokyo_night")
        for name in list_themes():
            marker = " *" if name == current else "  "
            print(f"{marker} {name}")
        return 0
    name = args.set
    if not is_valid_theme(name):
        sys.stderr.write(f"Unknown theme: {name}. Available: {', '.join(list_themes())}\n")
        return 2
    get_theme(name)  # validate the definition renders
    config = config_manager.load_config()
    ui_config = config.get("ui") or {}
    ui_config["theme"] = name
    config["ui"] = ui_config
    if not config_manager.save_config(config):
        sys.stderr.write("Failed to save the theme to config.\n")
        return 1
    print(f"Theme set to {name}.")
    return 0

def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "doctor":
        # The doctor command owns its own flags (--provider, --live, --json).
        from .doctor import main as doctor_main
        return doctor_main(argv[1:])
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
    sessions.add_argument("--search", metavar="QUERY",
                          help="Filter sessions by id, status, model, or metadata text")
    theme = commands.add_parser("theme", help="List or apply a color theme")
    theme.add_argument("--list", action="store_true", help="List available themes")
    theme.add_argument("--set", metavar="NAME", help="Set the active theme")
    commands.add_parser("tutorial", help="Run the interactive first-run tutorial")
    review = commands.add_parser("review", help="Statically review Python file(s) for common issues")
    review.add_argument("path", help="Python file or directory to review")
    review.add_argument("--severity", choices=["info", "warning", "error"], default="info",
                        help="Minimum severity to report (default: info)")
    review.add_argument("--json", action="store_true", help="Emit issues as JSON")
    doctor = commands.add_parser("doctor", help="Run system health checks")
    doctor.add_argument("--json", action="store_true", help="JSON output for machines")
    doctor.add_argument("--fix", action="store_true", help="Auto-fix safe issues")
    doctor.add_argument("--live", action="store_true", help="Include live provider checks")
    doctor.add_argument("--check", action="append", dest="checks", help="Run only named checks")
    cache = commands.add_parser("cache", help="Inspect or clear the LLM response cache")
    cache_action = cache.add_mutually_exclusive_group()
    cache_action.add_argument("--stats", action="store_true", help="Show cache statistics (default)")
    cache_action.add_argument("--clear", action="store_true", help="Remove all cached responses")
    cache.add_argument("--json", action="store_true", help="JSON output for machines")
    costs = commands.add_parser("costs", help="Show model API cost ledger")
    costs.add_argument("--workspace", help="Project directory")
    costs.add_argument("--json", action="store_true", help="JSON output for machines")
    metrics = commands.add_parser("metrics", help="Show recorded metrics and traces")
    metrics.add_argument("--workspace", help="Project directory")
    metrics.add_argument("--json", action="store_true", help="JSON output for machines")
    args = parser.parse_args(argv)
    if args.command == "doctor":
        from .doctor import main as doctor_main
        return doctor_main([
            *(["--json"] if args.json else []),
            *(["--fix"] if args.fix else []),
            *(["--live"] if args.live else []),
            *[arg for c in (args.checks or []) for arg in ("--check", c)],
        ])
    if args.command == "sessions":
        from .terminal import session_command
        return session_command(args)
    if args.command == "review":
        return review_command(args)
    if args.command == "theme":
        return theme_command(args)
    if args.command == "tutorial":
        from .onboarding import check_setup, run_tutorial
        issues = check_setup()
        for issue in issues:
            sys.stderr.write(f"[!] {issue} (hint: {issue.fix_hint})\n")
        result = run_tutorial()
        return 0 if result["completed"] else 1
    if args.command == "cache":
        from .core.cache import ResponseCache
        store = ResponseCache()
        if args.clear:
            removed = store.clear()
            if args.json:
                import json as _json
                print(_json.dumps({"cleared": removed}))
            else:
                print(f"Cleared {removed} cached response(s).")
            return 0
        info = store.stats()
        if args.json:
            import json as _json
            print(_json.dumps(info, indent=2))
        else:
            print("LLM response cache:")
            print(f"  Directory : {info['cache_dir']}")
            print(f"  Entries   : {info['entries']}")
            print(f"  Hits      : {info['hits']}")
            print(f"  Misses    : {info['misses']}")
            print(f"  Size      : {info['size_bytes']} bytes")
            print(f"  TTL       : {info['ttl_seconds']}s")
        return 0
    if args.command == "costs":
        from .core.costs import CostTracker
        from .core.workspace import resolve_workspace
        root = resolve_workspace(getattr(args, "workspace", None))
        tracker = CostTracker(root)
        if args.json:
            import json as _json
            print(_json.dumps({"total_usd": tracker.total(),
                               "by_model": tracker.by_model(),
                               "unknown_models": sorted(tracker.unknown_models)}, indent=2))
        else:
            print(tracker.render())
        return 0
    if args.command == "metrics":
        from .core.workspace import resolve_workspace
        root = resolve_workspace(getattr(args, "workspace", None))
        metrics_path = root / ".mythic" / "metrics.json"
        if args.json:
            if metrics_path.exists():
                print(metrics_path.read_text(encoding="utf-8"))
            else:
                import json as _json
                print(_json.dumps({"timers": {}, "counters": {}, "gauges": {}, "traces": []}, indent=2))
        elif metrics_path.exists():
            import json as _json
            from .core.metrics import Metrics
            m = Metrics.from_dict(_json.loads(metrics_path.read_text(encoding="utf-8")))
            print(m.render())
        else:
            print("No metrics recorded yet.")
        return 0
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
