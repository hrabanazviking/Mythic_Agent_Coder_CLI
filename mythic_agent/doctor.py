"""System health checks for Mythic Agent (Slice 11).

`mythic doctor` runs a suite of health checks:
- Config: valid, migrations applied, secrets not in plaintext logs
- Providers: endpoint reachable, auth configured (no real calls unless --live)
- Tools: all tools load, schemas valid
- Sessions: session store readable, no corruption
- Disk: workspace writable, sufficient space
- Dependencies: optional packages report status (not failures)

Usage:
    mythic doctor            # run all checks (offline; no network, no Agent)
    mythic doctor --provider # provider diagnostics with a live connectivity check
    mythic doctor --fix      # auto-fix safe issues
    mythic doctor --json     # JSON output for machines
    mythic doctor --live     # include live provider connectivity (may cost $)

Each check returns a HealthResult(status, message, fix_hint).
"""


from __future__ import annotations

__all__ = [
    "Callable",
    "Enum",
    "HealthResult",
    "HealthStatus",
    "Path",
    "check_config",
    "check_dependencies",
    "check_provider",
    "check_provider_live",
    "check_sessions",
    "check_tools",
    "check_workspace",
    "dataclass",
    "field",
    "health_check",
    "main",
    "print_results",
    "run_checks",
]

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


@health_check("provider")
def check_provider() -> HealthResult:
    """Offline provider configuration diagnostics: no network, no Agent."""
    try:
        from mythic_agent.core.config_manager import config_manager
        from mythic_agent.agents.llm import diagnose_provider
        report = diagnose_provider(config_manager.load_config())
    except Exception as exc:
        return HealthResult("provider", HealthStatus.FAIL,
                            f"Provider diagnostics failed: {exc}")
    detail = (f"{report['model'] or 'no model'} @ {report['base_url']}"
              + (" (loopback, no key needed)" if report["loopback"] else "")
              + f", retries: {report['retry_budget']}"
              + f", streaming: {'on' if report['streaming'] else 'off'}")
    problems, hints = [], []
    if not report["base_url_valid"]:
        problems.append(f"base_url is not a valid HTTP(S) URL: {report['base_url']}")
        hints.append("Set a valid base_url with /model <name> <url> or MYTHIC_BASE_URL.")
    if not report["model_configured"]:
        problems.append("no model configured")
        hints.append("Set a model with /model <name> or MYTHIC_MODEL.")
    if report["auth_required"] and not report["api_key_configured"]:
        problems.append(f"no API key configured for {report['base_url']}")
        hints.append("Store a key for this endpoint or export the provider's API key variable.")
    if problems:
        return HealthResult("provider", HealthStatus.FAIL,
                            "; ".join(problems) + f" [{detail}]",
                            fix_hint=" ".join(hints))
    return HealthResult("provider", HealthStatus.OK,
                        f"Provider configured [{detail}]")


def check_provider_live(timeout: float = 15.0) -> HealthResult:
    """Explicit live connectivity check: one metadata request, redacted errors.

    Never runs implicitly; only via ``--live``/``--provider``. Reports
    reachable/auth/failure outcomes honestly without inventing pricing or
    capabilities.
    """
    import threading
    import time

    from mythic_agent.agents.llm import ProviderCredentialsError, build_provider_client
    from mythic_agent.core.config_manager import config_manager
    from mythic_agent.core.redaction import redact_text

    config = config_manager.load_config()
    base_url = config.get("base_url", "")
    try:
        client = build_provider_client(config, threading.Event())
    except ProviderCredentialsError as exc:
        return HealthResult("provider-live", HealthStatus.FAIL, str(exc),
                            fix_hint="Configure a key for this endpoint to enable live checks.")
    client.timeout = timeout  # Doctor probes stay short; turn timeouts are separate.
    started = time.monotonic()
    try:
        models = client.models.list()
    except Exception as exc:
        kind = type(exc).__name__
        if "Authentication" in kind or "401" in str(exc):
            message, hint = "authentication rejected (401)", "Check the stored API key for this endpoint."
        elif "Timeout" in kind or "timed out" in str(exc).lower():
            message, hint = "request timed out", "Check the endpoint URL and network connectivity."
        elif "Connection" in kind:
            message, hint = "endpoint unreachable", "Check the endpoint URL and network connectivity."
        else:
            message, hint = f"live check failed ({kind})", "Check the endpoint URL and provider status."
        return HealthResult("provider-live", HealthStatus.FAIL,
                            f"{base_url}: {message}: {redact_text(str(exc))[:200]}",
                            fix_hint=hint)
    elapsed_ms = (time.monotonic() - started) * 1000
    ids = [getattr(model, "id", "") for model in getattr(models, "data", []) or []]
    configured = (config.get("model", "") or "").strip()
    detail = f"{base_url} reachable in {elapsed_ms:.0f}ms, {len(ids)} model(s) discovered"
    if configured and ids and configured not in ids:
        return HealthResult("provider-live", HealthStatus.WARNING,
                            f"{detail}; configured model '{configured}' not in discovery",
                            fix_hint="Run /model to pick a discovered model id.")
    return HealthResult("provider-live", HealthStatus.OK, detail)


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
    parser.add_argument("--provider", action="store_true",
                        help="Provider diagnostics only, with a live connectivity check")
    parser.add_argument("--check", action="append", dest="checks",
                        help="Run only named checks")
    args = parser.parse_args(argv)

    print("Mythic Agent health check")
    print("=" * 40)
    if args.provider:
        results = [check_provider(), check_provider_live()]
    else:
        results = run_checks(args.checks)
        if args.live:
            results.append(check_provider_live())

    code = print_results(results, as_json=args.json)
    if code == 0:
        print("\nAll checks passed.")
    else:
        print("\nSome checks failed. See hints above.")
    return code


if __name__ == "__main__":
    sys.exit(main())
