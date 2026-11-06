"""Tests for M-090: editor bridges lite (pure layer).

TIER: integration
"""

import pytest

from mythic_agent.core import editor_bridge as eb


# --- resolution: the terminal's own precedence ---------------

def test_visual_wins_over_editor():
    choice = eb.resolve_editor(
        {"VISUAL": "code --wait", "EDITOR": "nano"})
    assert choice.source == "VISUAL"
    assert choice.name == "code"
    assert choice.argv == ("code", "--wait")


def test_editor_used_when_visual_absent():
    choice = eb.resolve_editor({"EDITOR": "vim"})
    assert choice.source == "EDITOR"
    assert choice.argv == ("vim",)


def test_whitespace_visual_counts_as_unset():
    choice = eb.resolve_editor({"VISUAL": "  ", "EDITOR": "nano"})
    assert choice.source == "EDITOR"


def test_no_editor_refuses_and_names_the_remedy():
    with pytest.raises(ValueError, match="no editor is configured"):
        eb.resolve_editor({})
    with pytest.raises(ValueError, match="EDITOR"):
        eb.resolve_editor({"VISUAL": "", "EDITOR": " "})


def test_editor_value_split_like_a_shell():
    choice = eb.resolve_editor({"EDITOR": "emacs -nw"})
    assert choice.argv == ("emacs", "-nw")


def test_malformed_editor_value_raises():
    with pytest.raises(ValueError, match="cannot be split"):
        eb.resolve_editor({"EDITOR": "code 'unterminated"})


def test_editor_command_appends_the_scratch_path():
    argv = eb.editor_command({"EDITOR": "nano"}, "/tmp/x.py")
    assert argv == ["nano", "/tmp/x.py"]


def test_editor_command_refuses_without_an_editor():
    with pytest.raises(ValueError, match="no editor is configured"):
        eb.editor_command({}, "/tmp/x.py")


# --- preparation: anchors and scratch names -------------------

def test_file_round_trip_keeps_its_suffix():
    trip = eb.prepare_file_round_trip("src/app.py", "x = 1\n")
    assert trip.kind == "file"
    assert trip.scratch_name.endswith(".py")
    assert trip.record()["label"] == "src/app.py"


def test_file_without_suffix_gets_a_text_suffix():
    trip = eb.prepare_file_round_trip("Makefile", "all:\n")
    assert trip.scratch_name.endswith(".txt")


def test_prompt_round_trip_travels_as_prose():
    trip = eb.prepare_prompt_round_trip("approval draft", "do it\n")
    assert trip.kind == "prompt"
    assert trip.scratch_name.endswith(".md")


def test_scratch_names_differ_for_different_texts():
    one = eb.prepare_file_round_trip("a.py", "x = 1\n")
    two = eb.prepare_file_round_trip("a.py", "x = 2\n")
    assert one.scratch_name != two.scratch_name


def test_prepare_needs_a_path_and_a_label():
    with pytest.raises(ValueError, match="needs a path"):
        eb.prepare_file_round_trip(" ", "x\n")
    with pytest.raises(ValueError, match="needs a label"):
        eb.prepare_prompt_round_trip("", "x\n")


# --- judgement: changed / unchanged / emptied -----------------

def test_unchanged_text_judged_unchanged():
    trip = eb.prepare_file_round_trip("a.py", "x = 1\n")
    outcome = eb.judge_round_trip(trip, "x = 1\n")
    assert outcome.status == "unchanged"
    assert outcome.text == "x = 1\n"


def test_changed_text_judged_changed_with_new_text():
    trip = eb.prepare_prompt_round_trip("chat draft", "hi\n")
    outcome = eb.judge_round_trip(trip, "hi, edited\n")
    assert outcome.status == "changed"
    assert outcome.text == "hi, edited\n"
    record = outcome.record(trip)
    assert record["anchor_before"] != record["anchor_after"]


def test_emptied_file_refuses_and_original_stands():
    trip = eb.prepare_file_round_trip("a.py", "x = 1\n")
    outcome = eb.judge_round_trip(trip, "")
    assert outcome.status == "refused"
    assert outcome.text is None
    assert "never silently truncated" in outcome.reason


def test_emptied_prompt_is_a_cancellation():
    trip = eb.prepare_prompt_round_trip("chat draft", "hi\n")
    outcome = eb.judge_round_trip(trip, "  \n")
    assert outcome.status == "cancelled"
    assert outcome.text is None


# --- the gate ---------------------------------------------------

def test_gate_absent_means_on_and_malformed_raises():
    assert eb.enabled_from_config({}) is True
    assert eb.enabled_from_config({"editor_bridge": False}) is False
    with pytest.raises(ValueError, match="editor_bridge"):
        eb.enabled_from_config({"editor_bridge": "yes"})


def test_set_enabled_records_the_change():
    enabled, change = eb.set_enabled({}, False)
    assert enabled is False
    assert change.event() == {
        "type": "editor_bridge_setting_changed",
        "from": True, "to": False}
    record = change.record("s1", True)
    assert record["session_id"] == "s1"
    assert record["journaled"] is True


def test_set_enabled_refuses_same_value_and_non_bool():
    with pytest.raises(ValueError, match="already on"):
        eb.set_enabled({}, True)
    with pytest.raises(ValueError, match="on or off"):
        eb.set_enabled({}, "off")


# --- the shared /editor grammar ---------------------------------

def test_parse_editor_args():
    assert eb.parse_editor_args("") == {"action": "show"}
    assert eb.parse_editor_args("on") == {"action": "on"}
    assert eb.parse_editor_args("off") == {"action": "off"}
    assert eb.parse_editor_args("prompt") == {"action": "prompt"}
    assert eb.parse_editor_args("file src/my file.py") == {
        "action": "file", "path": "src/my file.py"}


def test_parse_editor_args_rejects_bad_grammar():
    with pytest.raises(ValueError, match="Usage: /editor"):
        eb.parse_editor_args("file")
    with pytest.raises(ValueError, match="Usage: /editor"):
        eb.parse_editor_args("launch")


# --- formatters ---------------------------------------------------

def test_format_editor_bridge_names_editor_and_setting():
    text = eb.format_editor_bridge({}, {"EDITOR": "nano"})
    assert "Editor bridges lite (M-090)" in text
    assert "Setting: on (editor_bridge)" in text
    assert "Editor: nano (from EDITOR: nano)" in text
    assert "changed" in text


def test_format_editor_bridge_states_absence_honestly():
    text = eb.format_editor_bridge({"editor_bridge": False}, {})
    assert "Setting: off (editor_bridge)" in text
    assert "Editor: none - no editor is configured" in text


def test_format_setting_change_and_round_trip():
    assert eb.format_setting_change({"to": False}) == \
        "Editor bridge is now off."
    trip = eb.prepare_file_round_trip("a.py", "x = 1\n")
    outcome = eb.judge_round_trip(trip, "x = 2\n")
    text = eb.format_round_trip(trip, outcome)
    assert "changed" in text
    assert "a.py" in text

# ---------------------------------------------------------------------
# Agent layer + surfaces (M-090 agent layer, 2026-11-06).
#
# The round-trips run a REAL fake editor: an executable
# python script in tmp_path that receives the scratch
# file as argv[1] and rewrites it the way an editor
# would. Nothing about the editor process is mocked.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore


def store_for(tmp_path, workspace=None):
    return SessionStore(workspace or tmp_path, tmp_path / "state")


def _editor_script(tmp_path, name, lines):
    script = tmp_path / name
    script.write_text("#!/usr/bin/env python3\n" + "\n".join(lines) + "\n",
                      encoding="utf-8")
    script.chmod(0o755)
    return str(script)


def _changing_editor(tmp_path, name="editor_change.py"):
    return _editor_script(tmp_path, name, [
        "import sys",
        "p = sys.argv[1]",
        "t = open(p, encoding='utf-8').read()",
        "open(p, 'w', encoding='utf-8').write("
        "t.replace('x = 1', 'x = 2').replace('hi', 'hello'))",
    ])


def _seed_file(tmp_path):
    (tmp_path / "src").mkdir(exist_ok=True)
    target = tmp_path / "src" / "app.py"
    target.write_text("x = 1\n", encoding="utf-8")
    return target


class TestAgentGate:
    def test_status_with_editor(self, agent, monkeypatch):
        monkeypatch.delenv("VISUAL", raising=False)
        monkeypatch.setenv("EDITOR", "nano")
        status = agent.editor_bridge_status()
        assert status["enabled"] is True
        assert status["explanation"] == eb.PLAIN_EXPLANATION
        assert status["editor"]["name"] == "nano"
        assert status["editor"]["source"] == "EDITOR"
        assert status["editor"]["argv"] == ["nano"]
        assert status["editor_error"] is None

    def test_status_without_editor_is_honest(self, agent, monkeypatch):
        monkeypatch.delenv("VISUAL", raising=False)
        monkeypatch.delenv("EDITOR", raising=False)
        status = agent.editor_bridge_status()
        assert status["editor"] is None
        assert "no editor is configured" in status["editor_error"]

    def test_set_without_session(self, agent):
        record = agent.set_editor_bridge(False)
        assert record["journaled"] is False
        assert agent.config["editor_bridge"] is False
        with pytest.raises(ValueError, match="already"):
            agent.set_editor_bridge(False)

    def test_set_journals_on_the_session(self, agent, tmp_path):
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        agent.set_editor_bridge(False)
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "editor_bridge_setting_changed" in types
        agent.close()

    def test_save_failure_restores_and_journals_the_revert(
            self, agent, tmp_path, monkeypatch):
        from mythic_agent.agents import llm

        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        monkeypatch.setattr(llm.config_manager, "save_config",
                            lambda config: False)
        with pytest.raises(RuntimeError, match="could not be saved"):
            agent.set_editor_bridge(False)
        assert agent.config.get("editor_bridge") is not False
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert types[-2:] == ["editor_bridge_setting_changed",
                              "editor_bridge_setting_reverted"]
        agent.close()


class TestFileRoundTrip:
    def test_changed_file_lands_and_journals(self, agent, tmp_path):
        target = _seed_file(tmp_path)
        script = _changing_editor(tmp_path)
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        record = agent.edit_file_in_editor(
            "src/app.py", environ={"EDITOR": script})
        assert record["status"] == "changed"
        assert record["text"] == "x = 2\n"
        assert record["editor"] == script
        assert target.read_text(encoding="utf-8") == "x = 2\n"
        assert record["journaled"] is True
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "editor_round_trip" in types
        agent.close()

    def test_unchanged_writes_nothing(self, agent, tmp_path):
        target = _seed_file(tmp_path)
        before = target.stat()
        script = _editor_script(tmp_path, "editor_noop.py", ["import sys"])
        record = agent.edit_file_in_editor(
            "src/app.py", environ={"EDITOR": script})
        assert record["status"] == "unchanged"
        assert target.read_text(encoding="utf-8") == "x = 1\n"
        assert target.stat().st_mtime_ns == before.st_mtime_ns

    def test_emptied_file_refuses_and_original_stands(self, agent, tmp_path):
        target = _seed_file(tmp_path)
        script = _editor_script(tmp_path, "editor_empty.py", [
            "import sys", "open(sys.argv[1], 'w').write('')"])
        record = agent.edit_file_in_editor(
            "src/app.py", environ={"EDITOR": script})
        assert record["status"] == "refused"
        assert record["text"] is None
        assert target.read_text(encoding="utf-8") == "x = 1\n"

    def test_gate_off_refuses_and_launches_nothing(self, agent, tmp_path):
        target = _seed_file(tmp_path)
        marker = tmp_path / "launched.txt"
        script = _editor_script(tmp_path, "editor_marker.py", [
            "import sys",
            f"open({str(marker)!r}, 'w').write('launched')"])
        agent.set_editor_bridge(False)
        with pytest.raises(ValueError, match="editor bridge is off"):
            agent.edit_file_in_editor(
                "src/app.py", environ={"EDITOR": script})
        assert not marker.exists()
        assert target.read_text(encoding="utf-8") == "x = 1\n"

    def test_no_editor_refuses_naming_the_remedy(self, agent, tmp_path):
        _seed_file(tmp_path)
        with pytest.raises(ValueError, match="no editor is configured"):
            agent.edit_file_in_editor("src/app.py", environ={})

    def test_editor_nonzero_exit_raises_and_writes_nothing(
            self, agent, tmp_path):
        target = _seed_file(tmp_path)
        script = _editor_script(tmp_path, "editor_fail.py", [
            "import sys", "sys.exit(3)"])
        with pytest.raises(ValueError, match="exited with code 3"):
            agent.edit_file_in_editor(
                "src/app.py", environ={"EDITOR": script})
        assert target.read_text(encoding="utf-8") == "x = 1\n"

    def test_missing_file_refuses_plainly(self, agent, tmp_path):
        script = _changing_editor(tmp_path)
        with pytest.raises(ValueError, match="no file at"):
            agent.edit_file_in_editor(
                "src/nope.py", environ={"EDITOR": script})


class TestPromptRoundTrip:
    def test_changed_prompt_returns_text_and_writes_no_file(
            self, agent, tmp_path):
        script = _changing_editor(tmp_path)
        record = agent.edit_prompt_in_editor(
            "hi\n", environ={"EDITOR": script})
        assert record["status"] == "changed"
        assert record["text"] == "hello\n"
        assert record["kind"] == "prompt"
        assert list(agent._editor_bridge_dir().iterdir()) == []

    def test_emptied_prompt_is_cancelled(self, agent, tmp_path):
        script = _editor_script(tmp_path, "editor_empty.py", [
            "import sys", "open(sys.argv[1], 'w').write('')"])
        record = agent.edit_prompt_in_editor(
            "hi\n", environ={"EDITOR": script})
        assert record["status"] == "cancelled"
        assert record["text"] is None


class TestTerminalSurface:
    def test_show_and_set(self, agent, monkeypatch):
        from mythic_agent.terminal import _slash

        monkeypatch.delenv("VISUAL", raising=False)
        monkeypatch.setenv("EDITOR", "nano")
        _, _, text = _slash(agent, "/editor")
        assert "Editor bridges lite (M-090)" in text
        assert "Setting: on (editor_bridge)" in text
        _, _, text = _slash(agent, "/editor off")
        assert "Editor bridge is now off." in text
        assert agent.config["editor_bridge"] is False
        _, _, text = _slash(agent, "/editor on")
        assert "Editor bridge is now on." in text

    def test_file_via_the_terminal(self, agent, tmp_path, monkeypatch):
        from mythic_agent.terminal import _slash

        target = _seed_file(tmp_path)
        script = _changing_editor(tmp_path)
        monkeypatch.delenv("VISUAL", raising=False)
        monkeypatch.setenv("EDITOR", script)
        _, _, text = _slash(agent, "/editor file src/app.py")
        assert "changed" in text
        assert target.read_text(encoding="utf-8") == "x = 2\n"

    def test_prompt_via_the_terminal_is_an_honest_refusal(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/editor prompt")
        assert "holds no draft" in text
        assert "Nothing was sent." in text

    def test_usage_error_is_the_message(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/editor frobnicate")
        assert "Usage: /editor" in text


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


class TestEditorCommand:
    def test_show_is_default(self, handler, agent):
        handler._handle_editor("")
        assert "Editor bridges lite (M-090)" in _published_text(handler)

    def test_set_via_the_handler(self, handler, agent):
        handler._handle_editor("off")
        assert "Editor bridge is now off." in _published_text(handler)
        assert agent.config["editor_bridge"] is False

    def test_file_via_the_handler(self, handler, agent, tmp_path,
                                  monkeypatch):
        target = _seed_file(tmp_path)
        script = _changing_editor(tmp_path)
        monkeypatch.delenv("VISUAL", raising=False)
        monkeypatch.setenv("EDITOR", script)
        handler._handle_editor("file src/app.py")
        assert "changed" in _published_text(handler)
        assert target.read_text(encoding="utf-8") == "x = 2\n"

    def test_prompt_refusal_is_published(self, handler, agent):
        handler._handle_editor("prompt")
        assert "Nothing was sent." in _published_text(handler)

    def test_usage_error_is_published(self, handler, agent):
        handler._handle_editor("frobnicate")
        assert "Usage: /editor" in _published_text(handler)


class TestChatScreenRouting:
    def test_editor_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/editor off", _FakeLog())
        assert calls == [("/editor", "off")]
