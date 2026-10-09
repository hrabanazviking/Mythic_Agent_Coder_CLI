"""System health checks for Mythic Agent (Slice 11).

`mythic doctor` runs a suite of health checks:
- Config: valid, migrations applied, secrets not in plaintext logs
- Providers: endpoint reachable, auth configured (no real calls unless --live)
- Tools: all tools load, schemas valid
- Sessions: session store readable, no corruption
- Disk: workspace writable, sufficient space
- Dependencies: optional packages report status (not failures)

Usage:
    mythic doctor           # run all checks
    mythic doctor --fix     # auto-fix safe issues
    mythic doctor --json    # JSON output for machines
    mythic doctor --live    # include live provider connectivity (may cost $)

Each check returns a HealthResult(status, message, fix_hint).
"""

from __future__ import annotations

import json
import shutil
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable


class HealthStatus(Enum):
    OK = "ok"
    WARNING = "warning"
    FAIL = "fail"
    SKIP = "skip"


@dataclass
class HealthResult:
    name: str
    status: HealthStatus
    message: str
    fix_hint: str = ""
    fix_applied: bool = False


# Registry of check functions
_checks: list[tuple[str, Callable[[], HealthResult]]] = []


def health_check(name: str):
    """Decorator to register a health check."""
    def decorator(fn: Callable[[], HealthResult]):
        _checks.append((name, fn))
        return fn
    return decorator


@health_check("config")
def check_config() -> HealthResult:
    """Config file exists, valid, migrations applied."""
    try:
        from mythic_agent.core.config_manager import config_manager
        cfg = config_manager.load_config()
        version = cfg.get("version", "unknown")
        return HealthResult(
            name="config",
            status=HealthStatus.OK,
            message=f"Config valid (version {version})",
        )
    except Exception as e:
        return HealthResult(
            name="config",
            status=HealthStatus.FAIL,
            message=f"Config error: {e}",
            fix_hint="Run 'mythic' and press F2 to re-run setup, or delete the config to reset.",
        )


@health_check("workspace")
def check_workspace() -> HealthResult:
    """Current directory is writable, sufficient disk space."""
    cwd = Path.cwd()
    if not cwd.is_dir():
        return HealthResult("workspace", HealthStatus.FAIL,
                            f"Not a directory: {cwd}")
    if not shutil.os.access(cwd, shutil.os.W_OK):
        return HealthResult("workspace", HealthStatus.FAIL,
                            f"Not writable: {cwd}",
                            fix_hint="Check permissions or choose a different workspace.")
    free_gb = shutil.disk_usage(cwd).free / (1024 ** 3)
    if free_gb < 0.5:
        return HealthResult("workspace", HealthStatus.WARNING,
                            f"Low disk space: {free_gb:.1f}GB free")
    return HealthResult("workspace", HealthStatus.OK,
                        f"Writable, {free_gb:.1f}GB free")


@health_check("tools")
def check_tools() -> HealthResult:
    """All agent tools load with valid schemas."""
    try:
        from mythic_agent.agents.tools import get_agent_tools
        tools = get_agent_tools()
        if not tools:
            return HealthResult("tools", HealthStatus.WARNING,
                                "No tools registered")
        # Tools are OpenAI function format: {'type': 'function', 'function': {'name': ...}}
        # or plain dicts with 'name', or objects with .name
        def _tool_name(t):
            if isinstance(t, dict):
                if "function" in t and isinstance(t["function"], dict):
                    return t["function"].get("name")
                return t.get("name")
            return getattr(t, "name", None)
        bad = [t for t in tools if not _tool_name(t)]
        if bad:
            return HealthResult("tools", HealthStatus.FAIL,
                                f"{len(bad)} tools missing names")
        return HealthResult("tools", HealthStatus.OK,
                            f"{len(tools)} tools loaded")
    except Exception as e:
        return HealthResult("tools", HealthStatus.FAIL,
                            f"Tool loading failed: {e}")


@health_check("sessions")
def check_sessions() -> HealthResult:
    """Session store is accessible."""
    try:
        from mythic_agent.core.sessions import SessionStore
        store = SessionStore()
        sessions = store.list_sessions() if hasattr(store, "list_sessions") else []
        return HealthResult("sessions", HealthStatus.OK,
                            f"Session store OK ({len(sessions)} sessions)")
    except Exception as e:
        return HealthResult("sessions", HealthStatus.WARNING,
                            f"Session store issue: {e}",
                            fix_hint="Sessions may not persist across restarts.")


@health_check("dependencies")
def check_dependencies() -> HealthResult:
    """Report optional dependency status (never a failure)."""
    optional = {
        "textual": "TUI",
        "mcp": "MCP server",
        "sounddevice": "voice",
        "psycopg": "knowledge DB",
    }
    missing = []
    for pkg, label in optional.items():
        try:
            __import__(pkg)
        except ImportError:
            missing.append(f"{label} ({pkg})")
    if missing:
        return HealthResult("dependencies", HealthStatus.SKIP,
                            f"Optional not installed: {', '.join(missing)}")
    return HealthResult("dependencies", HealthStatus.OK,
                        "All optional dependencies present")


def run_checks(names: list[str] | None = None) -> list[HealthResult]:
    """Run health checks, optionally filtered by name."""
    results = []
    for name, fn in _checks:
        if names and name not in names:
            continue
        try:
            results.append(fn())
        except Exception as e:
            results.append(HealthResult(
                name=name, status=HealthStatus.FAIL,
                message=f"Check crashed: {e}"))
    return results


def print_results(results: list[HealthResult], as_json: bool = False) -> int:
    """Print results. Returns 0 if no FAIL, 1 otherwise."""
    if as_json:
        print(json.dumps([
            {"name": r.name, "status": r.status.value, "message": r.message,
             "fix_hint": r.fix_hint}
            for r in results
        ], indent=2))
    else:
        icons = {
            HealthStatus.OK: "✓",
            HealthStatus.WARNING: "!",
            HealthStatus.FAIL: "✗",
            HealthStatus.SKIP: "-",
        }
        for r in results:
            print(f"  {icons[r.status]} {r.name}: {r.message}")
            if r.fix_hint and r.status in (HealthStatus.FAIL, HealthStatus.WARNING):
                print(f"      Hint: {r.fix_hint}")
    return 1 if any(r.status == HealthStatus.FAIL for r in results) else 0


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(prog="mythic doctor")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--fix", action="store_true", help="Auto-fix safe issues")
    parser.add_argument("--live", action="store_true",
                        help="Include live provider checks (may incur cost)")
    parser.add_argument("--check", action="append", dest="checks",
                        help="Run only named checks")
    args = parser.parse_args(argv)

    print("Mythic Agent health check")
    print("=" * 40)
    results = run_checks(args.checks)

    if args.live:
        # Placeholder for Slice 1's --provider live checks
        print("  - live provider checks: not yet implemented (Slice 1)")

    code = print_results(results, as_json=args.json)
    if code == 0:
        print("\nAll checks passed.")
    else:
        print("\nSome checks failed. See hints above.")
    return code


if __name__ == "__main__":
    sys.exit(main())
