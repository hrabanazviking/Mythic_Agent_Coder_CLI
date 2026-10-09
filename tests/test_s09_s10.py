"""S09 (TUI polish) + S10 (repo workflows) slice tests.

Covers: the ui_thread thread-safety wrapper, small-terminal detection,
commit-scope preview, workspace-scoped gh execution, and token redaction
of command output.

The UI helpers live in mythic_agent.ui and are intentionally free of
Textual imports, so they test without a running application.
"""

import os
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

from mythic_agent import ui as ui_mod
from mythic_agent.agents import command_handler as ch_mod
from mythic_agent.core.policy import ToolPolicy


# ---------------------------------------------------------------------------
# S09: ui_thread / call_from_thread
# ---------------------------------------------------------------------------

class _FakeApp:
    """Stand-in for a Textual App: records marshalled callbacks."""

    def __init__(self):
        self.routed = []

    def call_from_thread(self, callback, *args, **kwargs):
        self.routed.append((callback, args, kwargs))
        return "routed"


@pytest.fixture
def fake_app():
    app = _FakeApp()
    ui_mod.register_app(app)  # registers the current (test) thread as the app thread
    yield app
    ui_mod.unregister_app(app)


def test_ui_thread_calls_directly_on_app_thread(fake_app):
    @ui_mod.ui_thread(app=fake_app)
    def compute(x):
        return x * 2

    assert compute(21) == 42
    assert fake_app.routed == []  # no marshalling needed on the app thread


def test_ui_thread_routes_off_thread_calls(fake_app):
    @ui_mod.ui_thread(app=fake_app)
    def compute(x):
        return x * 2

    holder = {}
    worker = threading.Thread(target=lambda: holder.update(result=compute(21)))
    worker.start()
    worker.join()

    assert holder["result"] == "routed"
    assert len(fake_app.routed) == 1
    callback, args, kwargs = fake_app.routed[0]
    assert args == (21,)
    assert kwargs == {}
    assert callback(21) == 42  # the marshalled payload is the real function


def test_ui_thread_resolves_app_from_self(fake_app):
    class Screenish:
        app = fake_app

        @ui_mod.ui_thread()
        def method(self, x):
            return x + 1

    screen = Screenish()
    assert screen.method(41) == 42
    assert fake_app.routed == []

    holder = {}
    worker = threading.Thread(target=lambda: holder.update(result=screen.method(41)))
    worker.start()
    worker.join()
    assert holder["result"] == "routed"
    assert len(fake_app.routed) == 1


# ---------------------------------------------------------------------------
# S09: small-terminal detection
# ---------------------------------------------------------------------------

def test_terminal_too_small_detects_small_and_large(monkeypatch):
    monkeypatch.setattr(
        ui_mod.shutil, "get_terminal_size",
        lambda fallback=None: os.terminal_size((60, 20)),
    )
    too_small, dims = ui_mod.terminal_too_small()
    assert too_small is True
    assert dims == (60, 20)

    monkeypatch.setattr(
        ui_mod.shutil, "get_terminal_size",
        lambda fallback=None: os.terminal_size((120, 40)),
    )
    too_small, dims = ui_mod.terminal_too_small()
    assert too_small is False
    assert dims == (120, 40)


def test_small_terminal_warning_names_dimensions():
    text = ui_mod.small_terminal_warning(60, 20)
    assert "60x20" in text
    assert "80x24" in text


# ---------------------------------------------------------------------------
# S10: repo workflows — fixtures and helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def handler(monkeypatch, tmp_path):
    from mythic_agent.core.config_manager import config_manager

    monkeypatch.setattr(config_manager, "load_config", lambda: {})
    # Avoid importing the heavy LLM module in this environment.
    monkeypatch.setattr(ch_mod.CommandHandler, "_primary", lambda self: None)
    h = ch_mod.CommandHandler()
    h.project_root = tmp_path
    h.policy = ToolPolicy("trusted")  # authorize effects under test
    return h


@pytest.fixture
def published(monkeypatch):
    events = []
    monkeypatch.setattr(
        ch_mod, "publish_sync",
        lambda event_type, **kwargs: events.append((event_type, kwargs)),
    )
    return events


def _run_fake(recorded, outputs=None):
    outputs = outputs or {}

    def fake(self, command, **kwargs):
        recorded.append((list(command), kwargs))
        key = " ".join(command)
        stdout = outputs.get(key, "")
        return SimpleNamespace(
            returncode=0, stdout=stdout, stderr="",
            status="completed", output=stdout,
        )

    return fake


def test_commit_preview_shows_status_and_diff_stat(handler, published, monkeypatch):
    recorded = []
    monkeypatch.setattr(
        ch_mod.CommandHandler, "_run",
        _run_fake(recorded, {
            "git status --short": " M foo.py\n?? bar.py\n",
            "git diff --stat": " foo.py | 2 +-\n 1 file changed, 1 insertion(+), 1 deletion(-)\n",
        }),
    )

    handler._handle_commit("my feature")

    commands = [" ".join(cmd) for cmd, _ in recorded]
    assert "git add ." not in commands  # preview stages nothing
    assert not any(c.startswith("git commit") for c in commands)
    assert handler._pending_commit == "my feature"

    text = published[-1][1]["text"]
    assert "git status --short" in text
    assert "git diff --stat" in text
    assert "foo.py | 2 +-" in text
    assert "my feature" in text
    assert "/commit --confirm" in text


def test_commit_confirm_executes_add_commit_push(handler, published, monkeypatch):
    recorded = []
    monkeypatch.setattr(ch_mod.CommandHandler, "_run", _run_fake(recorded))

    handler._pending_commit = "my feature"
    handler._handle_commit("--confirm")

    commands = [" ".join(cmd) for cmd, _ in recorded]
    assert commands[0] == "git add ."
    assert commands[1] == "git commit -m my feature"
    assert commands[2] == "git push"
    assert handler._pending_commit is None  # pending cleared after use
    assert any("Successfully committed" in kw["text"] for _, kw in published)


def test_gh_runs_with_workspace_cwd(handler, published, monkeypatch):
    seen = {}

    def fake_run_process(command, workspace, **kwargs):
        seen["command"] = list(command)
        seen["workspace"] = workspace
        return SimpleNamespace(
            status="completed", returncode=0, output="ok", render=lambda: "ok",
        )

    monkeypatch.setattr(ch_mod, "run_process", fake_run_process)

    handler._handle_gh("auth status")

    assert seen["command"][:2] == ["gh", "auth"]
    assert Path(seen["workspace"]) == handler.project_root


def test_gh_output_redacts_tokens(handler, published, monkeypatch):
    fake_token = "ghp_" + "AbCdEfGhIjKlMnOpQr12"  # pattern-shaped, not a real secret
    recorded = []
    monkeypatch.setattr(
        ch_mod.CommandHandler, "_run",
        _run_fake(recorded, {"gh auth status": f"token: {fake_token}\nall good"}),
    )

    handler._handle_gh("auth status")

    text = published[-1][1]["text"]
    assert fake_token not in text
    assert "[REDACTED]" in text
