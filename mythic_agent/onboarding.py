"""Interactive first-run tutorial and setup verification.

``mythic tutorial`` walks a new user through the essential flows (provider
config, workspace, chat, TUI, slash commands).  ``check_setup()`` verifies
that the environment is sane and returns a list of human-readable problems
(empty means healthy).
"""


from __future__ import annotations

__all__ = [
    "Any",
    "Callable",
    "ConfigManager",
    "Iterable",
    "Path",
    "SetupIssue",
    "Step",
    "check_setup",
    "dataclass",
    "run_tutorial",
    "tutorial_steps",
]

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from .core.config_manager import ConfigManager


@dataclass
class SetupIssue:
    """One thing wrong (or merely worth knowing) with the current setup."""

    code: str
    message: str
    fix_hint: str

    def __str__(self) -> str:
        return self.message


# ---------------------------------------------------------------------------
# Setup verification
# ---------------------------------------------------------------------------

def check_setup(config: dict[str, Any] | None = None,
                mythic_home: Path | None = None) -> list[SetupIssue]:
    """Verify the environment is ready for a Mythic session.

    Args:
        config: Optional pre-loaded config dict; otherwise loaded from
            ``config_manager``.
        mythic_home: Override the ``~/.mythic`` state directory.

    Returns:
        List of :class:`SetupIssue`; empty means the setup is healthy.
    """
    issues: list[SetupIssue] = []
    manager = ConfigManager(root=mythic_home) if mythic_home is not None else ConfigManager()
    if config is None:
        try:
            config = manager.load_config()
        except Exception as exc:  # keep tutorial robust against broken config
            return [SetupIssue("config_unreadable", f"Could not read config: {exc}",
                               "Delete the broken config file and re-run 'mythic tutorial'.")]

    model = config.get("model") or ""
    if not model:
        issues.append(SetupIssue("no_model", "No default model is configured.",
                                 "Run 'mythic tutorial' or set MYTHIC_MODEL."))
    base_url = config.get("base_url") or ""
    if not base_url:
        issues.append(SetupIssue("no_base_url", "No provider base URL is configured.",
                                 "Run 'mythic tutorial' or set MYTHIC_BASE_URL."))

    key_env = [name for name in os.environ if "API_KEY" in name.upper()]
    if not key_env and not os.environ.get("MYTHIC_API_KEY"):
        issues.append(SetupIssue("no_api_key",
                                 "No API key found in the environment.",
                                 "Export MYTHIC_API_KEY (or your provider's key) before chatting."))

    if shutil.which("git") is None:
        issues.append(SetupIssue("no_git", "git is not on PATH.",
                                 "Install git for workspace versioning features."))

    workspace = config.get("workspace")
    if workspace and not Path(workspace).expanduser().exists():
        issues.append(SetupIssue("bad_workspace",
                                 f"Configured workspace does not exist: {workspace}",
                                 "Update the workspace path in your config or via --workspace."))
    return issues


# ---------------------------------------------------------------------------
# Interactive tutorial
# ---------------------------------------------------------------------------

Step = tuple[str, str]  # (title, body)


def tutorial_steps() -> list[Step]:
    """Return the ordered (title, body) walkthrough steps."""
    return [
        ("Welcome to Mythic Agent",
         "I am your local AI coding harness. I keep your code, memory, and\n"
         "sessions on your own machine. Let's set up the essentials."),
        ("Provider",
         "Point me at any OpenAI-compatible endpoint with a model name and a\n"
         "base URL. The classic incantation:\n"
         "  mythic chat --model <name> --base-url <url>\n"
         "Keys ride along via environment variables like MYTHIC_API_KEY."),
        ("Chat",
         "Start talking with 'mythic chat'. Inside the loop, try these:\n"
         "  /help            show loop commands\n"
         "  /model           view or switch the active model\n"
         "  /clear           start a fresh conversation\n"
         "  Ctrl+C           interrupt a running turn"),
        ("The TUI",
         "Run 'mythic tui' for the full-screen interface with tabs, the\n"
         "command palette (Ctrl+K), and markdown-rendered answers.\n"
         "See docs/SHORTCUTS.md for every key binding."),
        ("Sessions",
         "Every conversation is a session you can resume:\n"
         "  mythic sessions --search <query>   find past work\n"
         "  mythic chat --resume <session-id>  pick it back up"),
        ("Themes",
         "Make it yours:\n"
         "  mythic theme --list        available color themes\n"
         "  mythic theme --set viking_dark   apply one"),
        ("You are ready",
         "Type 'mythic chat' to begin. May your wyrd weave kindly."),
    ]


def _default_io() -> tuple[Callable[[str], str], Callable[[str], None]]:
    return input, print


def run_tutorial(input_fn: Callable[[str], str] | None = None,
                 output_fn: Callable[[str], None] | None = None,
                 config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run the interactive first-run tutorial.

    Args:
        input_fn: Replacement for ``input`` (tests pass a stub).
        output_fn: Replacement for ``print`` (tests pass a stub).
        config: If provided, the provider/model setup answers are merged
            into it instead of being discarded.

    Returns:
        Dict of ``{"completed": bool, "provider": ..., "model": ...}``.
    """
    ask, say = _default_io()
    if input_fn is not None:
        ask = input_fn
    if output_fn is not None:
        say = output_fn

    for title, body in tutorial_steps():
        say(f"\n=== {title} ===")
        say(body)
        reply = ask("Press Enter to continue (or 'q' to quit): ").strip().lower()
        if reply in {"q", "quit", "exit"}:
            return {"completed": False}

    say("\n--- Quick provider setup ---")
    provider = ask("Provider base URL (Enter to skip): ").strip()
    model = ask("Model name (Enter to skip): ").strip()
    result: dict[str, Any] = {"completed": True, "provider": provider or None,
                              "model": model or None}
    if config is not None:
        if provider:
            config["base_url"] = provider
        if model:
            config["model"] = model
        result["config"] = config
    say("\nSetup complete. Type 'mythic chat' and weave something great.")
    return result
