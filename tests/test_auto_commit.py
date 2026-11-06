"""M-078 — Auto-commit discipline (Aider's crown).

TIER: integration

Covers the M-078 surface:

* the pure layer (``mythic_agent.core.auto_commit``): an
  accepted edit set judged into a commit plan — its own
  commit, a written message, exactly the accepted files;
  on an ordinary branch the commit lands there, on a
  protected branch it is planned onto the working branch
  by default, and onto the protected branch itself only
  under the user's explicit standing setting, recorded
  as on-protected,
* the roadmap's own law, proven: protected branches
  (main / master / development / develop, plus any the
  user names) are never committed to unasked; a blank
  message, an empty or escaping file set, and a detached
  head all refuse and commit nothing,
* ``Agent``: the gate + protected-word status and
  journaled setters (a failed save restoring the previous
  value and journaling the revert), and
  ``commit_accepted_edits`` executing a plan against a
  throwaway git repository — never the campaign tree:
  one edit set, one commit; two edit sets, two commits;
  the protected road moves the commit onto the working
  branch and leaves the protected branch untouched,
* the surfaces: the terminal ``/autocommit`` and the TUI
  ``/autocommit`` (system-command road through the
  CommandHandler + chat-screen routing), which share the
  parser and formatters,
* the config contract: the settings ship in the defaults
  (gate off, protected word off, working branch
  mythic/working, the default protected set). The M-009
  catalogue entry (S-64) is a pending integration delta
  recorded in TEAM_LOG.md — the catalogue is a shared
  inventory surface the coordinator regenerates.
"""

from __future__ import annotations

import subprocess

import pytest

from mythic_agent.core.auto_commit import (
    ALLOW_PROTECTED_KEY,
    AUTO_COMMIT_SLICE,
    BRANCH_KEY,
    DEFAULT_PROTECTED,
    DEFAULT_WORKING_BRANCH,
    PLAIN_EXPLANATION,
    PROTECTED_KEY,
    SETTING_KEY,
    allow_protected_from_config,
    build_message,
    enabled_from_config,
    format_auto_commit,
    format_commit_record,
    format_plan,
    format_setting_change,
    is_protected,
    parse_autocommit_args,
    plan_commit,
    protected_from_config,
    set_allow_protected,
    set_enabled,
    validate_files,
    validate_message,
    working_branch_from_config,
)
from mythic_agent.core.sessions import SessionStore

FILES = ["app.py", "test_app.py"]
MESSAGE = "Fix the login redirect\n\nFiles:\n  - app.py\n  - test_app.py"


def store_for(tmp_path, workspace=None):
    return SessionStore(workspace or tmp_path, tmp_path / "state")


def git(root, *args):
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def make_repo(tmp_path):
    """A throwaway git repo on main with one commit."""
    git(tmp_path, "init", "-b", "main")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Slice Test")
    (tmp_path / "app.py").write_text("alpha = 1\n", encoding="utf-8")
    (tmp_path / "test_app.py").write_text("T = 1\n", encoding="utf-8")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "initial")
    return git(tmp_path, "rev-parse", "HEAD")


class TestPlan:
    def test_slice_and_setting_constants(self):
        assert AUTO_COMMIT_SLICE == "M-078"
        assert SETTING_KEY == "auto_commit"
        assert ALLOW_PROTECTED_KEY == "auto_commit_allow_protected"
        assert BRANCH_KEY == "auto_commit_branch"
        assert PROTECTED_KEY == "auto_commit_protected"
        assert DEFAULT_WORKING_BRANCH == "mythic/working"
        assert "main" in DEFAULT_PROTECTED
        assert "never on the user's protected" in PLAIN_EXPLANATION \
            or "never" in PLAIN_EXPLANATION

    def test_an_ordinary_branch_lands_there(self):
        plan = plan_commit({}, "feature/login", FILES, MESSAGE)
        assert plan.target_branch == "feature/login"
        assert plan.switch_needed is False
        assert plan.on_protected is False
        assert plan.files == tuple(FILES)

    @pytest.mark.parametrize("branch", sorted(DEFAULT_PROTECTED))
    def test_every_default_protected_branch_moves(self, branch):
        plan = plan_commit({}, branch, FILES, MESSAGE)
        assert plan.target_branch == DEFAULT_WORKING_BRANCH
        assert plan.switch_needed is True
        assert plan.on_protected is False

    def test_protected_under_the_standing_word(self):
        config = {"auto_commit_allow_protected": True}
        plan = plan_commit(config, "main", FILES, MESSAGE)
        assert plan.target_branch == "main"
        assert plan.on_protected is True
        assert plan.switch_needed is False

    def test_user_named_protected_branches(self):
        config = {"auto_commit_protected": ["release", "hotfix"]}
        assert is_protected(config, "release") is True
        assert is_protected(config, "main") is False
        plan = plan_commit(config, "hotfix", FILES, MESSAGE)
        assert plan.switch_needed is True

    def test_a_named_working_branch_is_used(self):
        config = {"auto_commit_branch": "work/scratch"}
        plan = plan_commit(config, "main", FILES, MESSAGE)
        assert plan.target_branch == "work/scratch"

    def test_a_protected_working_branch_refuses(self):
        config = {"auto_commit_branch": "main"}
        with pytest.raises(ValueError, match="itself protected"):
            plan_commit(config, "development", FILES, MESSAGE)

    def test_a_detached_head_refuses(self):
        with pytest.raises(ValueError, match="detached head"):
            plan_commit({}, "HEAD", FILES, MESSAGE)
        with pytest.raises(ValueError, match="current branch"):
            plan_commit({}, "", FILES, MESSAGE)

    def test_a_blank_message_refuses(self):
        with pytest.raises(ValueError, match="written message"):
            plan_commit({}, "feature/x", FILES, "   ")
        with pytest.raises(ValueError, match="written message"):
            validate_message("")

    def test_the_file_set_is_judged(self):
        assert validate_files(["./app.py", "app.py", "src//b.py"]) == (
            "app.py", "src/b.py")
        with pytest.raises(ValueError, match="at least one file"):
            validate_files([])
        with pytest.raises(ValueError, match="inside the tree"):
            validate_files(["../outside.py"])
        with pytest.raises(ValueError, match="inside the tree"):
            validate_files(["/abs/path.py"])
        with pytest.raises(ValueError, match="git's own house"):
            validate_files([".git/config"])

    def test_build_message_names_the_files(self):
        message = build_message("Fix the login redirect", FILES)
        assert message.splitlines()[0] == "Fix the login redirect"
        assert "  - app.py" in message and "  - test_app.py" in message
        with pytest.raises(ValueError, match="written message"):
            build_message("  ", FILES)


class TestGate:
    def test_gate_defaults_off_and_validates(self):
        assert enabled_from_config({}) is False
        assert enabled_from_config({"auto_commit": True}) is True
        with pytest.raises(ValueError, match="true or false"):
            enabled_from_config({"auto_commit": "yes"})

    def test_protected_word_defaults_off(self):
        assert allow_protected_from_config({}) is False
        assert allow_protected_from_config(
            {"auto_commit_allow_protected": True}) is True
        with pytest.raises(ValueError, match="true or false"):
            allow_protected_from_config(
                {"auto_commit_allow_protected": 1})

    def test_protected_set_defaults_and_validates(self):
        assert protected_from_config({}) == DEFAULT_PROTECTED
        assert protected_from_config(
            {"auto_commit_protected": ["release"]}) == ("release",)
        with pytest.raises(ValueError, match="list of branch"):
            protected_from_config({"auto_commit_protected": "main"})
        with pytest.raises(ValueError, match="protects nothing"):
            protected_from_config({"auto_commit_protected": []})

    def test_working_branch_defaults_and_validates(self):
        assert working_branch_from_config({}) == "mythic/working"
        with pytest.raises(ValueError, match="cannot name a branch"):
            working_branch_from_config(
                {"auto_commit_branch": "bad name"})

    def test_set_enabled(self):
        value, change = set_enabled({}, True)
        assert value is True and change.before is False
        assert change.event()["type"] == "auto_commit_setting_changed"
        with pytest.raises(ValueError, match="already off"):
            set_enabled({}, False)
        with pytest.raises(ValueError, match="on or off"):
            set_enabled({}, "on")

    def test_set_allow_protected(self):
        value, change = set_allow_protected({}, True)
        assert value is True and change.after is True
        assert change.event()["type"] == (
            "auto_commit_protected_setting_changed")
        with pytest.raises(ValueError, match="already off"):
            set_allow_protected({}, False)


class TestSurface:
    def test_parse_args(self):
        assert parse_autocommit_args("") == {"action": "show"}
        assert parse_autocommit_args("on") == {
            "action": "setting", "enabled": True}
        assert parse_autocommit_args("off") == {
            "action": "setting", "enabled": False}
        assert parse_autocommit_args("allow-protected") == {
            "action": "protected_setting", "allowed": True}
        assert parse_autocommit_args("block-protected") == {
            "action": "protected_setting", "allowed": False}
        with pytest.raises(ValueError, match="Usage"):
            parse_autocommit_args("sideways")

    def test_format_plan_names_the_landing(self):
        plan = plan_commit({}, "feature/login", FILES, MESSAGE)
        assert "lands on branch 'feature/login'" in format_plan(plan)
        plan = plan_commit({}, "main", FILES, MESSAGE)
        text = format_plan(plan)
        assert "protected branch 'main'" in text
        assert "mythic/working" in text
        plan = plan_commit({"auto_commit_allow_protected": True},
                           "main", FILES, MESSAGE)
        assert "on-protected" in format_plan(plan)

    def test_format_auto_commit_shows_the_worked_example(self):
        text = format_auto_commit({})
        assert "Auto-commit discipline (M-078)" in text
        assert "Setting: off (auto_commit)" in text
        assert "feature/login" in text
        assert "mythic/working" in text
        assert "Usage: /autocommit" in text

    def test_format_setting_change(self):
        record = {"key": SETTING_KEY, "from": False, "to": True}
        assert format_setting_change(record) == "Auto-commit: off -> on."
        record = {"key": ALLOW_PROTECTED_KEY, "from": False, "to": True}
        assert format_setting_change(record) == (
            "Auto-commit on protected branches: blocked -> allowed.")

    def test_format_commit_record(self):
        record = {"committed": True, "commit": "abc1234",
                  "target_branch": "mythic/working", "branch": "main",
                  "on_protected": False, "switched": True,
                  "files": FILES, "message": MESSAGE, "reason": ""}
        text = format_commit_record(record)
        assert "abc1234" in text and "mythic/working" in text
        record = {"committed": False, "commit": None,
                  "target_branch": "main", "branch": "main",
                  "on_protected": False, "switched": False,
                  "files": FILES, "message": MESSAGE,
                  "reason": "nothing to commit"}
        assert "nothing committed" in format_commit_record(record)


class TestAgentGate:
    def test_status(self, agent):
        status = agent.auto_commit_status()
        assert status["enabled"] is False
        assert status["allow_protected"] is False
        assert status["working_branch"] == "mythic/working"
        assert "main" in status["protected"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_set_without_session(self, agent):
        record = agent.set_auto_commit(True)
        assert record["journaled"] is False
        assert agent.config["auto_commit"] is True
        with pytest.raises(ValueError, match="already on"):
            agent.set_auto_commit(True)

    def test_set_journals_on_the_session(self, agent, tmp_path):
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        agent.set_auto_commit(True)
        agent.set_auto_commit_allow_protected(True)
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "auto_commit_setting_changed" in types
        assert "auto_commit_protected_setting_changed" in types
        agent.close()

    def test_save_failure_restores_and_journals_the_revert(
            self, agent, tmp_path, monkeypatch):
        from mythic_agent.agents import llm

        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        monkeypatch.setattr(llm.config_manager, "save_config",
                            lambda config: False)
        with pytest.raises(RuntimeError, match="could not be saved"):
            agent.set_auto_commit(True)
        assert agent.config.get("auto_commit") is not True
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert types[-2:] == ["auto_commit_setting_changed",
                              "auto_commit_setting_reverted"]
        agent.close()


class TestAgentCommit:
    def test_gate_off_refuses_and_commits_nothing(
            self, agent, tmp_path):
        make_repo(tmp_path)
        (tmp_path / "app.py").write_text("alpha = 2\n", encoding="utf-8")
        with pytest.raises(ValueError, match="auto-commit is off"):
            agent.commit_accepted_edits(["app.py"], "Change alpha")
        assert git(tmp_path, "status", "--porcelain") != ""

    def test_one_edit_set_one_commit_on_a_working_branch(
            self, agent, tmp_path):
        make_repo(tmp_path)
        git(tmp_path, "switch", "-c", "feature/login")
        agent.set_auto_commit(True)
        (tmp_path / "app.py").write_text("alpha = 2\n", encoding="utf-8")
        record = agent.commit_accepted_edits(["app.py"], "Change alpha")
        assert record["committed"] is True
        assert record["target_branch"] == "feature/login"
        assert record["on_protected"] is False
        assert git(tmp_path, "log", "-1", "--format=%s") == "Change alpha"
        assert "app.py" in git(tmp_path, "log", "-1", "--format=%b")
        assert git(tmp_path, "status", "--porcelain") == ""

    def test_two_edit_sets_land_as_two_commits(
            self, agent, tmp_path):
        make_repo(tmp_path)
        git(tmp_path, "switch", "-c", "feature/login")
        agent.set_auto_commit(True)
        (tmp_path / "app.py").write_text("alpha = 2\n", encoding="utf-8")
        first = agent.commit_accepted_edits(["app.py"], "Change alpha")
        (tmp_path / "app.py").write_text("alpha = 3\n", encoding="utf-8")
        second = agent.commit_accepted_edits(["app.py"], "Change alpha again")
        assert first["commit"] != second["commit"]
        subjects = git(tmp_path, "log", "--format=%s").splitlines()
        assert subjects[:3] == ["Change alpha again", "Change alpha",
                                "initial"]

    def test_only_the_accepted_files_are_committed(
            self, agent, tmp_path):
        make_repo(tmp_path)
        git(tmp_path, "switch", "-c", "feature/login")
        agent.set_auto_commit(True)
        (tmp_path / "app.py").write_text("alpha = 2\n", encoding="utf-8")
        (tmp_path / "test_app.py").write_text("T = 2\n", encoding="utf-8")
        agent.commit_accepted_edits(["app.py"], "Change alpha only")
        lines = git(tmp_path, "status", "--porcelain").splitlines()
        assert any(line.endswith("test_app.py") for line in lines)
        assert not any(line.endswith(" app.py") for line in lines)

    def test_protected_branch_moves_to_the_working_branch(
            self, agent, tmp_path):
        initial = make_repo(tmp_path)
        agent.set_auto_commit(True)
        (tmp_path / "app.py").write_text("alpha = 2\n", encoding="utf-8")
        record = agent.commit_accepted_edits(["app.py"], "Change alpha")
        assert record["committed"] is True
        assert record["switched"] is True
        assert record["target_branch"] == "mythic/working"
        assert git(tmp_path, "branch", "--show-current") == "mythic/working"
        assert git(tmp_path, "rev-parse", "main") == initial
        assert git(tmp_path, "log", "-1", "--format=%s") == "Change alpha"

    def test_protected_branch_under_the_standing_word(
            self, agent, tmp_path):
        make_repo(tmp_path)
        agent.set_auto_commit(True)
        agent.set_auto_commit_allow_protected(True)
        (tmp_path / "app.py").write_text("alpha = 2\n", encoding="utf-8")
        record = agent.commit_accepted_edits(["app.py"], "Change alpha")
        assert record["on_protected"] is True
        assert record["target_branch"] == "main"
        assert git(tmp_path, "branch", "--show-current") == "main"
        assert git(tmp_path, "log", "-1", "--format=%s") == "Change alpha"

    def test_nothing_to_commit_is_an_honest_record(
            self, agent, tmp_path):
        make_repo(tmp_path)
        git(tmp_path, "switch", "-c", "feature/login")
        agent.set_auto_commit(True)
        record = agent.commit_accepted_edits(["app.py"], "Change alpha")
        assert record["committed"] is False
        assert "nothing" in record["reason"]

    def test_a_blank_message_commits_nothing(self, agent, tmp_path):
        make_repo(tmp_path)
        git(tmp_path, "switch", "-c", "feature/login")
        agent.set_auto_commit(True)
        (tmp_path / "app.py").write_text("alpha = 2\n", encoding="utf-8")
        with pytest.raises(ValueError, match="written message"):
            agent.commit_accepted_edits(["app.py"], "   ")
        assert git(tmp_path, "log", "--format=%s").splitlines() == [
            "initial"]

    def test_the_commit_is_journaled(self, agent, tmp_path):
        make_repo(tmp_path)
        git(tmp_path, "switch", "-c", "feature/login")
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        agent.set_auto_commit(True)
        (tmp_path / "app.py").write_text("alpha = 2\n", encoding="utf-8")
        record = agent.commit_accepted_edits(["app.py"], "Change alpha")
        assert record["journaled"] is True
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "auto_commit_committed" in types
        agent.close()

    def test_not_a_repository_refuses(self, agent, tmp_path):
        agent.set_auto_commit(True)
        (tmp_path / "app.py").write_text("alpha = 1\n", encoding="utf-8")
        with pytest.raises(ValueError, match="needs a git repository"):
            agent.commit_accepted_edits(["app.py"], "Change alpha")


class TestTerminalSurface:
    def test_show_and_set(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/autocommit")
        assert "Auto-commit discipline (M-078)" in text
        _, _, text = _slash(agent, "/autocommit on")
        assert "off -> on" in text
        assert agent.config["auto_commit"] is True
        _, _, text = _slash(agent, "/autocommit allow-protected")
        assert "blocked -> allowed" in text
        _, _, text = _slash(agent, "/autocommit block-protected")
        assert "allowed -> blocked" in text
        _, _, text = _slash(agent, "/autocommit off")
        assert "on -> off" in text

    def test_usage_error_is_the_message(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/autocommit sideways")
        assert "Usage" in text


@pytest.fixture()
def handler(agent, monkeypatch):
    from mythic_agent.agents import command_handler as handler_module
    from mythic_agent.agents.command_handler import CommandHandler
    from mythic_agent.agents.llm import AGENT_REGISTRY

    published = []
    monkeypatch.setattr(
        handler_module, "publish_sync",
        lambda event, **kwargs: published.append((event, kwargs)))
    AGENT_REGISTRY["Primary"] = agent
    instance = CommandHandler.__new__(CommandHandler)
    instance.published = published
    yield instance
    AGENT_REGISTRY.pop("Primary", None)


def _published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestAutoCommitCommand:
    def test_show_is_default(self, handler, agent):
        handler._handle_autocommit("")
        assert "Auto-commit discipline (M-078)" in _published_text(handler)

    def test_set_via_the_handler(self, handler, agent):
        handler._handle_autocommit("on")
        assert "off -> on" in _published_text(handler)
        assert agent.config["auto_commit"] is True

    def test_usage_error_is_published(self, handler, agent):
        handler._handle_autocommit("sideways")
        assert "Usage" in _published_text(handler)


class TestChatScreenRouting:
    def test_autocommit_routes_as_system_command(self, monkeypatch):
        from mythic_agent.ui.screens import chat_screen
        from mythic_agent.ui.screens.chat_screen import MainChatScreen

        class _FakeLog:
            def __init__(self):
                self.lines = []

            def write(self, *args, **kwargs):
                self.lines.append(" ".join(str(a) for a in args))

        calls = []
        monkeypatch.setattr(
            chat_screen.SecureAPI, "publish_system_command",
            staticmethod(lambda cmd, args: calls.append((cmd, args))))
        screen = MainChatScreen.__new__(MainChatScreen)
        screen.handle_command("/autocommit off", _FakeLog())
        assert calls == [("/autocommit", "off")]


class TestConfigContract:
    def test_defaults_ship_the_discipline_off(self):
        import yaml
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        defaults = yaml.safe_load(
            (root / "mythic_agent/data/config_defaults.yaml")
            .read_text(encoding="utf-8"))
        assert defaults["auto_commit"] is False
        assert defaults["auto_commit_allow_protected"] is False
        assert defaults["auto_commit_branch"] == "mythic/working"
        assert "main" in defaults["auto_commit_protected"]
