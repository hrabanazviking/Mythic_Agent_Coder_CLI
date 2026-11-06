"""Tests for M-085: rename/move files as first-class edits."""

import pytest

from mythic_agent.core import rename_move as rm


EXISTING = ["pkg/mod.py", "pkg/__init__.py", "app.py", "docs/guide.md"]


def test_module_name_for_plain_module():
    assert rm.module_name_for("pkg/mod.py") == "pkg.mod"


def test_module_name_for_init_is_package():
    assert rm.module_name_for("pkg/__init__.py") == "pkg"


def test_module_name_for_non_python_is_none():
    assert rm.module_name_for("docs/guide.md") is None


def test_plan_move_happy_path_uses_git_mv():
    plan = rm.plan_move("pkg/mod.py", "pkg/renamed.py", existing=EXISTING)
    assert plan.git_argv == ("git", "mv", "pkg/mod.py", "pkg/renamed.py")
    assert plan.updates == ()
    assert plan.warnings == ()


def test_plan_move_refuses_missing_source():
    with pytest.raises(ValueError, match="does not exist"):
        rm.plan_move("pkg/nope.py", "pkg/x.py", existing=EXISTING)


def test_plan_move_refuses_existing_destination():
    with pytest.raises(ValueError, match="already exists"):
        rm.plan_move("pkg/mod.py", "app.py", existing=EXISTING)


def test_plan_move_refuses_same_path():
    with pytest.raises(ValueError, match="same"):
        rm.plan_move("app.py", "app.py", existing=EXISTING)


@pytest.mark.parametrize("bad", ["/abs/path.py", "../up.py", "a//b.py",
                                 "a/./b.py", "", "  "])
def test_plan_move_refuses_dirty_paths(bad):
    with pytest.raises(ValueError):
        rm.plan_move(bad, "pkg/x.py", existing=EXISTING)


def test_plan_move_refuses_directory_into_itself():
    with pytest.raises(ValueError, match="into itself"):
        rm.plan_move("pkg", "pkg/inner", existing=["pkg"],
                     is_directory=True)


def test_reference_update_rewrites_module_and_path_tokens():
    text = "import pkg.mod\nPATH = 'pkg/mod.py'\n"
    plan = rm.plan_move("pkg/mod.py", "pkg/renamed.py", existing=EXISTING,
                        referencing=["app.py"], texts={"app.py": text})
    assert len(plan.updates) == 1
    update = plan.updates[0]
    assert update.replacements == 2
    assert "import pkg.renamed" in update.new_text
    assert "pkg/renamed.py" in update.new_text


def test_reference_update_leaves_longer_names_alone():
    text = "import pkg.modular\nimport pkg.mod\n"
    plan = rm.plan_move("pkg/mod.py", "pkg/renamed.py", existing=EXISTING,
                        referencing=["app.py"], texts={"app.py": text})
    update = plan.updates[0]
    assert update.replacements == 1
    assert "pkg.modular" in update.new_text


def test_reference_update_for_init_move_rewrites_package():
    text = "from pkg import thing\n"
    plan = rm.plan_move("pkg/__init__.py", "pack/__init__.py",
                        existing=EXISTING, referencing=["app.py"],
                        texts={"app.py": text})
    assert plan.updates[0].new_text == "from pack import thing\n"


def test_referencing_file_without_text_warns():
    plan = rm.plan_move("pkg/mod.py", "pkg/renamed.py", existing=EXISTING,
                        referencing=["app.py"], texts={})
    assert plan.updates == ()
    assert len(plan.warnings) == 1
    assert "not supplied" in plan.warnings[0]


def test_referencing_file_without_token_warns():
    plan = rm.plan_move("pkg/mod.py", "pkg/renamed.py", existing=EXISTING,
                        referencing=["app.py"],
                        texts={"app.py": "nothing here\n"})
    assert plan.updates == ()
    assert "no exact" in plan.warnings[0]


def test_source_itself_is_not_a_reference_target():
    plan = rm.plan_move("pkg/mod.py", "pkg/renamed.py", existing=EXISTING,
                        referencing=["pkg/mod.py"],
                        texts={"pkg/mod.py": "import pkg.mod\n"})
    assert plan.updates == ()
    assert plan.warnings == ()


def test_record_carries_slice_and_command():
    plan = rm.plan_move("app.py", "main.py", existing=EXISTING)
    record = plan.record()
    assert record["slice"] == "M-085"
    assert record["command"] == ["git", "mv", "app.py", "main.py"]
    assert record["type"] == "file_moved"


def test_format_move_plan_names_history_and_updates():
    plan = rm.plan_move("pkg/mod.py", "pkg/renamed.py", existing=EXISTING,
                        referencing=["app.py"],
                        texts={"app.py": "import pkg.mod\n"})
    rendered = rm.format_move_plan(plan)
    assert "git mv pkg/mod.py pkg/renamed.py" in rendered
    assert "app.py: 1 replacement(s)" in rendered


def test_enabled_defaults_on_and_reads_stored_bool():
    assert rm.enabled_from_config({}) is True
    assert rm.enabled_from_config({"rename_move": False}) is False


def test_enabled_malformed_raises():
    with pytest.raises(ValueError, match="true or false"):
        rm.enabled_from_config({"rename_move": "yes"})


def test_set_enabled_roundtrip_and_noop_refusal():
    enabled, change = rm.set_enabled({}, False)
    assert enabled is False
    assert change.event()["type"] == "rename_move_setting_changed"
    with pytest.raises(ValueError, match="already"):
        rm.set_enabled({}, True)


def test_parse_move_and_gate_words():
    assert rm.parse_rename_args("") == {"action": "show"}
    assert rm.parse_rename_args("off") == {"action": "off"}
    parsed = rm.parse_rename_args("a/b.py c/d.py")
    assert parsed == {"action": "move", "source": "a/b.py",
                      "destination": "c/d.py"}


def test_parse_refuses_bad_grammar():
    with pytest.raises(ValueError, match="usage"):
        rm.parse_rename_args("only-one")
    with pytest.raises(ValueError, match="usage"):
        rm.parse_rename_args("a b c")


# ---------------------------------------------------------------------
# Agent layer + surfaces (keeper restart tick, 2026-11-06).
# ---------------------------------------------------------------------

import subprocess

from mythic_agent.core.sessions import SessionStore


def store_for(tmp_path, workspace=None):
    return SessionStore(workspace or tmp_path, tmp_path / "state")


def _git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args],
                          check=True, capture_output=True, text=True)


def _seed_repo(tmp_path):
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "pkg" / "mod.py").write_text("thing = 1\n", encoding="utf-8")
    (tmp_path / "app.py").write_text("import pkg.mod\n", encoding="utf-8")
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "-c", "user.email=t@example.com", "-c",
         "user.name=T", "commit", "-qm", "seed")


class TestAgentGate:
    def test_status(self, agent):
        status = agent.rename_move_status()
        assert status["enabled"] is True
        assert status["explanation"] == rm.PLAIN_EXPLANATION

    def test_set_without_session(self, agent):
        record = agent.set_rename_move(False)
        assert record["journaled"] is False
        assert agent.config["rename_move"] is False
        with pytest.raises(ValueError, match="already"):
            agent.set_rename_move(False)

    def test_set_journals_on_the_session(self, agent, tmp_path):
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        agent.set_rename_move(False)
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "rename_move_setting_changed" in types
        agent.close()

    def test_save_failure_restores_and_journals_the_revert(
            self, agent, tmp_path, monkeypatch):
        from mythic_agent.agents import llm

        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        monkeypatch.setattr(llm.config_manager, "save_config",
                            lambda config: False)
        with pytest.raises(RuntimeError, match="could not be saved"):
            agent.set_rename_move(False)
        assert agent.config.get("rename_move") is not False
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert types[-2:] == ["rename_move_setting_changed",
                              "rename_move_setting_reverted"]
        agent.close()


class TestAgentMove:
    def test_preview_plans_and_moves_nothing(self, agent, tmp_path):
        _seed_repo(tmp_path)
        shown = agent.preview_rename_move("pkg/mod.py", "pkg/renamed.py")
        assert shown["type"] == "file_moved"
        assert shown["command"] == ["git", "mv", "pkg/mod.py",
                                    "pkg/renamed.py"]
        assert shown["reference_updates"] == [
            {"path": "app.py", "replacements": 1}]
        assert (tmp_path / "pkg" / "mod.py").exists()
        assert not (tmp_path / "pkg" / "renamed.py").exists()
        assert (tmp_path / "app.py").read_text(
            encoding="utf-8") == "import pkg.mod\n"

    def test_move_executes_and_updates_references(
            self, agent, tmp_path):
        _seed_repo(tmp_path)
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        record = agent.rename_move_file("pkg/mod.py", "pkg/renamed.py")
        assert not (tmp_path / "pkg" / "mod.py").exists()
        assert (tmp_path / "pkg" / "renamed.py").read_text(
            encoding="utf-8") == "thing = 1\n"
        assert (tmp_path / "app.py").read_text(
            encoding="utf-8") == "import pkg.renamed\n"
        assert record["journaled"] is True
        assert record["reference_updates"] == [
            {"path": "app.py", "replacements": 1}]
        events = store.export(session_id)["events"]
        moved = [e for e in events if e["type"] == "file_moved"]
        assert moved and moved[-1]["destination"] == "pkg/renamed.py"
        from mythic_agent.core.edits import EditJournal
        assert "app.py" in EditJournal(tmp_path).undo()
        _git(tmp_path, "add", "-A")
        _git(tmp_path, "-c", "user.email=t@example.com", "-c",
             "user.name=T", "commit", "-qm", "rename")
        log = _git(tmp_path, "log", "--follow", "--format=%s",
                   "--", "pkg/renamed.py").stdout
        assert "seed" in log
        agent.close()

    def test_gate_off_refuses_and_moves_nothing(self, agent, tmp_path):
        _seed_repo(tmp_path)
        agent.set_rename_move(False)
        with pytest.raises(ValueError, match="rename/move is off"):
            agent.rename_move_file("pkg/mod.py", "pkg/renamed.py")
        assert (tmp_path / "pkg" / "mod.py").exists()
        assert not (tmp_path / "pkg" / "renamed.py").exists()

    def test_missing_source_refuses(self, agent, tmp_path):
        _seed_repo(tmp_path)
        with pytest.raises(ValueError, match="does not exist"):
            agent.rename_move_file("pkg/nope.py", "pkg/x.py")

    def test_untracked_source_refuses_and_moves_nothing(
            self, agent, tmp_path):
        _seed_repo(tmp_path)
        (tmp_path / "loose.py").write_text("x = 1\n", encoding="utf-8")
        with pytest.raises(RuntimeError, match="git mv refused"):
            agent.rename_move_file("loose.py", "moved.py")
        assert (tmp_path / "loose.py").exists()
        assert not (tmp_path / "moved.py").exists()


class TestTerminalSurface:
    def test_show_and_set(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/rename")
        assert "Rename/move files (M-085)" in text
        assert "Setting: on (rename_move)" in text
        _, _, text = _slash(agent, "/rename off")
        assert "Rename/move is now off." in text
        assert agent.config["rename_move"] is False
        _, _, text = _slash(agent, "/rename on")
        assert "Rename/move is now on." in text

    def test_move_via_the_terminal(self, agent, tmp_path):
        from mythic_agent.terminal import _slash

        _seed_repo(tmp_path)
        _, _, text = _slash(agent, "/rename pkg/mod.py pkg/renamed.py")
        assert "Moved: pkg/mod.py -> pkg/renamed.py" in text
        assert (tmp_path / "pkg" / "renamed.py").exists()

    def test_usage_error_is_the_message(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/rename only-one")
        assert "usage" in text


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


class TestRenameCommand:
    def test_show_is_default(self, handler, agent):
        handler._handle_rename("")
        assert "Rename/move files (M-085)" in _published_text(handler)

    def test_set_via_the_handler(self, handler, agent):
        handler._handle_rename("off")
        assert "Rename/move is now off." in _published_text(handler)
        assert agent.config["rename_move"] is False

    def test_move_via_the_handler(self, handler, agent, tmp_path):
        _seed_repo(tmp_path)
        handler._handle_rename("pkg/mod.py pkg/renamed.py")
        assert "Moved: pkg/mod.py" in _published_text(handler)
        assert (tmp_path / "pkg" / "renamed.py").exists()

    def test_usage_error_is_published(self, handler, agent):
        handler._handle_rename("only-one")
        assert "usage" in _published_text(handler)


class TestChatScreenRouting:
    def test_rename_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/rename off", _FakeLog())
        assert calls == [("/rename", "off")]
