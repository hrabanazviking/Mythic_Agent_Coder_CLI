"""Startup crash recovery for journaled agent sessions.

Moved here from ``mythic_agent.terminal`` (R-002 architecture conformance):
``core/engine.py`` needed this helper, and core must not import the terminal
entry module.  Crash recovery is session infrastructure, so it belongs in
core; ``terminal.py`` re-imports it from here.  Behavior is unchanged.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - typing only, never executed
    from ..agents.llm import Agent


def recover_crashed_sessions(agent: Agent, interactive: bool = False,
                             console: Any = None) -> list[str]:
    """Startup crash check: replay journaled checkpoints left by a dead process.

    When ``interactive`` and stdin is a TTY the user is asked first; otherwise
    recovery is automatic.  Returns the recovered session ids.
    """
    store = getattr(agent, "_session_store", None)
    if store is None:
        return []
    pending = store.check_recovery()
    if not pending:
        return []
    notice = (f"[!] Detected {len(pending)} uncommitted checkpoint(s) from a "
              "previous crash. Session state may otherwise be lost.")
    if console is not None:
        console.print(notice)
    else:
        sys.stderr.write(notice + "\n")
    proceed = True
    if interactive and sys.stdin.isatty():
        try:
            answer = input("Recover them now? [Y/n] ").strip().lower()
        except (EOFError, OSError):
            answer = "n"
        proceed = answer in {"", "y", "yes"}
    if not proceed:
        return []
    recovered = store.recover_pending()
    done = f"[+] Recovered {len(recovered)} crashed session checkpoint(s)."
    if console is not None:
        console.print(done)
    else:
        sys.stderr.write(done + "\n")
    return recovered
