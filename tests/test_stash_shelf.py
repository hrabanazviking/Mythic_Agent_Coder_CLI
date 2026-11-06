"""Tests for M-088: the stash shelf.

TIER: integration
"""

import pytest

from mythic_agent.core import stash_shelf as ss


BASE = {"src/app.py": "x = 1\n", "src/old.py": "gone = True\n"}
WORKING = {"src/app.py": "x = 2\n", "src/new.py": "y = 3\n"}


def _entry(name="half-done fix", base=None, working=None, **kw):
    return ss.build_entry(name, BASE if base is None else base,
                          WORKING if working is None else working, **kw)


def test_build_entry_captures_added_modified_deleted():
    entry = _entry()
    kinds = {c.path: c.kind for c in entry.changes}
    assert kinds == {"src/app.py": "modified",
                     "src/new.py": "added",
                     "src/old.py": "deleted"}
    assert entry.file_count == 3
    assert entry.record()["slice"] == "M-088"
    assert entry.record()["type"] == "stash_shelf_entry"


def test_build_entry_changes_are_sorted_by_path():
    entry = _entry()
    assert [c.path for c in entry.changes] == sorted(
        c.path for c in entry.changes)


def test_build_entry_anchors_match_content():
    entry = _entry()
    for change in entry.changes:
        if change.shelf_content is not None:
            assert change.shelf_anchor == ss.content_anchor(
                change.shelf_content)
        if change.base_content is not None:
            assert change.base_anchor == ss.content_anchor(
                change.base_content)


def test_shelving_nothing_refuses():
    with pytest.raises(ValueError, match="nothing to shelve"):
        ss.build_entry("empty", BASE, dict(BASE))


def test_name_is_stripped_and_kept_as_words():
    entry = _entry(name="  before the auth rework  ")
    assert entry.name == "before the auth rework"


@pytest.mark.parametrize("bad", ["", "   ", "x" * (ss.MAX_NAME_CHARS + 1),
                                 "bad\nname", None, 7])
def test_validate_name_refuses_bad_names(bad):
    with pytest.raises(ValueError):
        ss.validate_name(bad)


@pytest.mark.parametrize("bad", ["/abs/x.py", "../x.py", "a//b.py", ""])
def test_build_entry_refuses_dirty_paths(bad):
    with pytest.raises(ValueError):
        ss.build_entry("n", {bad: "x"}, {bad: "y"})


def test_build_entry_refuses_non_string_text():
    with pytest.raises(ValueError):
        ss.build_entry("n", {"a.py": 1}, {"a.py": 2})


def test_session_id_is_recorded():
    entry = _entry(session_id="session-9")
    assert entry.session_id == "session-9"
    assert entry.record()["session_id"] == "session-9"


def test_clean_tree_returns_the_base_exactly():
    entry = _entry()
    assert ss.clean_tree(BASE, entry) == BASE


def test_clean_tree_refuses_an_entry_from_another_base():
    entry = _entry()
    other = {"src/app.py": "different\n", "src/old.py": "gone = True\n"}
    with pytest.raises(ValueError, match="not shelved against this base"):
        ss.clean_tree(other, entry)


def test_restore_round_trip_brings_the_work_back():
    entry = _entry()
    cleaned = ss.clean_tree(BASE, entry)
    assert ss.restore_tree(entry, BASE, cleaned) == WORKING


def test_restore_deleted_file_removes_it_again():
    entry = _entry()
    restored = ss.restore_tree(entry, BASE, ss.clean_tree(BASE, entry))
    assert "src/old.py" not in restored


def test_restore_conflict_refuses_and_names_the_path():
    entry = _entry()
    moved = dict(BASE)
    moved["src/app.py"] = "someone else's work\n"
    with pytest.raises(ValueError, match="src/app.py"):
        ss.restore_tree(entry, BASE, moved)


def test_restore_conflict_on_an_added_path_refuses():
    entry = _entry()
    moved = dict(BASE)
    moved["src/new.py"] = "clash\n"
    assert ss.restore_conflicts(entry, BASE, moved) == ["src/new.py"]
    with pytest.raises(ValueError):
        ss.restore_tree(entry, BASE, moved)


def test_restore_with_discard_overwrites_on_purpose():
    entry = _entry()
    moved = dict(BASE)
    moved["src/app.py"] = "someone else's work\n"
    restored = ss.restore_tree(entry, BASE, moved, discard=True)
    assert restored == WORKING


def test_restore_refuses_non_bool_discard():
    entry = _entry()
    with pytest.raises(ValueError):
        ss.restore_tree(entry, BASE, dict(BASE), discard="yes")


def test_shelf_refuses_a_duplicate_name():
    shelf = ss.Shelf()
    shelf.shelve(_entry())
    with pytest.raises(ValueError, match="already holds"):
        shelf.shelve(_entry())


def test_shelf_get_and_drop():
    shelf = ss.Shelf([_entry()])
    assert shelf.names() == ["half-done fix"]
    dropped = shelf.drop("half-done fix")
    assert dropped.name == "half-done fix"
    assert len(shelf) == 0
    with pytest.raises(ValueError, match="no shelf entry"):
        shelf.get("half-done fix")


def test_shelf_restore_removes_the_entry_by_default():
    shelf = ss.Shelf([_entry()])
    restored = shelf.restore("half-done fix", BASE, dict(BASE))
    assert restored == WORKING
    assert len(shelf) == 0


def test_shelf_restore_with_keep_leaves_the_entry():
    shelf = ss.Shelf([_entry()])
    shelf.restore("half-done fix", BASE, dict(BASE), keep=True)
    assert shelf.names() == ["half-done fix"]


def test_failed_restore_keeps_the_entry_on_the_shelf():
    shelf = ss.Shelf([_entry()])
    moved = dict(BASE)
    moved["src/app.py"] = "moved\n"
    with pytest.raises(ValueError):
        shelf.restore("half-done fix", BASE, moved)
    assert shelf.names() == ["half-done fix"]


def test_journal_round_trip_restores_across_sessions():
    shelf = ss.Shelf([_entry(session_id="session-1"),
                      _entry(name="second", session_id="session-2")])
    rebuilt, corrupt = ss.Shelf.from_journal_text(shelf.to_journal_text())
    assert corrupt == 0
    assert rebuilt.names() == ["half-done fix", "second"]
    restored = rebuilt.restore("half-done fix", BASE, dict(BASE))
    assert restored == WORKING


def test_journal_torn_last_line_is_counted_not_loaded():
    shelf = ss.Shelf([_entry()])
    text = shelf.to_journal_text() + '{"record": {"type": "stash_shelf_e'
    rebuilt, corrupt = ss.Shelf.from_journal_text(text)
    assert corrupt == 1
    assert rebuilt.names() == ["half-done fix"]


def test_journal_tampered_checksum_is_counted_not_loaded():
    shelf = ss.Shelf([_entry()])
    lines = shelf.to_journal_text().splitlines()
    tampered = lines[0].replace("half-done", "half-doneX")
    rebuilt, corrupt = ss.Shelf.from_journal_text(tampered + "\n")
    assert corrupt == 1
    assert len(rebuilt) == 0


def test_journal_empty_text_is_an_empty_shelf():
    rebuilt, corrupt = ss.Shelf.from_journal_text("")
    assert corrupt == 0
    assert len(rebuilt) == 0


def test_entry_from_record_rejects_a_wrong_anchor():
    record = _entry().record()
    record["changes"][0]["shelf_anchor"] = "0" * 64
    with pytest.raises(ValueError, match="anchor mismatch"):
        ss.entry_from_record(record)


def test_gate_absent_means_on_and_malformed_raises():
    assert ss.enabled_from_config({}) is True
    assert ss.enabled_from_config({ss.SETTING_KEY: False}) is False
    with pytest.raises(ValueError):
        ss.enabled_from_config({ss.SETTING_KEY: "yes"})


def test_set_enabled_validates_the_change():
    after, change = ss.set_enabled({}, False)
    assert after is False
    assert change.event()["type"] == "stash_shelf_setting_changed"
    with pytest.raises(ValueError, match="already on"):
        ss.set_enabled({}, True)
    with pytest.raises(ValueError):
        ss.set_enabled({}, "off")


def test_parse_stash_args_grammar():
    assert ss.parse_stash_args("") == {"action": "show"}
    assert ss.parse_stash_args("list") == {"action": "show"}
    assert ss.parse_stash_args("on") == {"action": "on"}
    assert ss.parse_stash_args("off") == {"action": "off"}
    assert ss.parse_stash_args("shelve before the rework") == {
        "action": "shelve", "name": "before the rework"}
    assert ss.parse_stash_args("restore before the rework") == {
        "action": "restore", "name": "before the rework"}
    assert ss.parse_stash_args("drop before the rework") == {
        "action": "drop", "name": "before the rework"}
    with pytest.raises(ValueError, match="usage"):
        ss.parse_stash_args("shelve")
    with pytest.raises(ValueError, match="usage"):
        ss.parse_stash_args("frobnicate x")


def test_format_shelf_entry_names_files_and_kinds():
    text = ss.format_shelf_entry(_entry())
    assert "half-done fix" in text
    assert "modified: src/app.py" in text
    assert "added: src/new.py" in text
    assert "deleted: src/old.py" in text


def test_format_shelf_list_empty_and_full():
    assert "empty" in ss.format_shelf_list(ss.Shelf())
    text = ss.format_shelf_list(ss.Shelf([_entry()]))
    assert "half-done fix" in text


def test_format_stash_shelf_show_surface_exercises_the_road():
    text = ss.format_stash_shelf({})
    assert "M-088" in text
    assert "half-done fix" in text or "3 file" in text or "file(s)" in text
    assert "on" in text
    off = ss.format_stash_shelf({ss.SETTING_KEY: False})
    assert "off" in off


def test_format_setting_change_words():
    assert ss.format_setting_change({"to": True}) == (
        "The stash shelf is now on.")
    assert ss.format_setting_change({"to": False}) == (
        "The stash shelf is now off.")


# ---------------------------------------------------------------------
# Agent layer + surfaces (keeper restart tick, 2026-11-06).
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore


def store_for(tmp_path, workspace=None):
    return SessionStore(workspace or tmp_path, tmp_path / "state")


def _seed(agent, tmp_path):
    """A clean base, then work-in-progress on top of it."""
    (tmp_path / "src").mkdir(exist_ok=True)
    (tmp_path / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "src" / "old.py").write_text("gone = True\n",
                                             encoding="utf-8")
    agent.stash_shelf_status()  # the first read establishes the base
    (tmp_path / "src" / "app.py").write_text("x = 2\n", encoding="utf-8")
    (tmp_path / "src" / "new.py").write_text("y = 3\n", encoding="utf-8")
    (tmp_path / "src" / "old.py").unlink()


class TestAgentGate:
    def test_status(self, agent):
        status = agent.stash_shelf_status()
        assert status["enabled"] is True
        assert status["explanation"] == ss.PLAIN_EXPLANATION
        assert status["count"] == 0
        assert status["corrupt_lines"] == 0

    def test_set_without_session(self, agent):
        record = agent.set_stash_shelf(False)
        assert record["journaled"] is False
        assert agent.config["stash_shelf"] is False
        with pytest.raises(ValueError, match="already"):
            agent.set_stash_shelf(False)

    def test_set_journals_on_the_session(self, agent, tmp_path):
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        agent.set_stash_shelf(False)
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "stash_shelf_setting_changed" in types
        agent.close()

    def test_save_failure_restores_and_journals_the_revert(
            self, agent, tmp_path, monkeypatch):
        from mythic_agent.agents import llm

        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        monkeypatch.setattr(llm.config_manager, "save_config",
                            lambda config: False)
        with pytest.raises(RuntimeError, match="could not be saved"):
            agent.set_stash_shelf(False)
        assert agent.config.get("stash_shelf") is not False
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert types[-2:] == ["stash_shelf_setting_changed",
                              "stash_shelf_setting_reverted"]
        agent.close()


class TestShelveRestore:
    def test_shelve_cleans_the_tree_and_journals_on_disk(
            self, agent, tmp_path):
        _seed(agent, tmp_path)
        record = agent.shelve_stash("half-done fix")
        assert record["files"] == 3
        assert (tmp_path / "src" / "app.py").read_text(
            encoding="utf-8") == "x = 1\n"
        assert not (tmp_path / "src" / "new.py").exists()
        assert (tmp_path / "src" / "old.py").read_text(
            encoding="utf-8") == "gone = True\n"
        journal = agent._stash_shelf_dir() / "shelf.journal"
        assert "half-done fix" in journal.read_text(encoding="utf-8")
        status = agent.stash_shelf_status()
        assert status["names"] == ["half-done fix"]

    def test_shelve_journals_on_the_session(self, agent, tmp_path):
        _seed(agent, tmp_path)
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        record = agent.shelve_stash("wip")
        assert record["journaled"] is True
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "stash_shelved" in types
        agent.close()

    def test_shelving_nothing_refuses(self, agent, tmp_path):
        (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
        agent.stash_shelf_status()
        with pytest.raises(ValueError, match="nothing to shelve"):
            agent.shelve_stash("empty")
        assert agent.stash_shelf_status()["count"] == 0

    def test_duplicate_name_refuses(self, agent, tmp_path):
        _seed(agent, tmp_path)
        agent.shelve_stash("wip")
        (tmp_path / "src" / "app.py").write_text("x = 5\n",
                                                encoding="utf-8")
        with pytest.raises(ValueError, match="already holds"):
            agent.shelve_stash("wip")

    def test_restore_round_trip_across_instances(self, agent, tmp_path):
        from mythic_agent.agents import llm

        _seed(agent, tmp_path)
        agent.shelve_stash("wip")
        other = llm.Agent(project_root=tmp_path)
        assert other.stash_shelf_status()["names"] == ["wip"]
        record = other.restore_stash("wip")
        assert record["files"] == 3
        assert (tmp_path / "src" / "app.py").read_text(
            encoding="utf-8") == "x = 2\n"
        assert (tmp_path / "src" / "new.py").read_text(
            encoding="utf-8") == "y = 3\n"
        assert not (tmp_path / "src" / "old.py").exists()
        assert other.stash_shelf_status()["count"] == 0

    def test_restore_conflict_refuses_then_discard_applies(
            self, agent, tmp_path):
        _seed(agent, tmp_path)
        agent.shelve_stash("wip")
        (tmp_path / "src" / "app.py").write_text("x = 9\n",
                                                encoding="utf-8")
        with pytest.raises(ValueError, match="src/app.py"):
            agent.restore_stash("wip")
        assert agent.stash_shelf_status()["count"] == 1
        record = agent.restore_stash("wip", discard=True)
        assert record["discarded"] == 1
        assert (tmp_path / "src" / "app.py").read_text(
            encoding="utf-8") == "x = 2\n"

    def test_drop_removes_without_touching_the_tree(
            self, agent, tmp_path):
        _seed(agent, tmp_path)
        agent.shelve_stash("wip")
        record = agent.drop_stash("wip")
        assert record["name"] == "wip"
        assert agent.stash_shelf_status()["count"] == 0
        assert (tmp_path / "src" / "app.py").read_text(
            encoding="utf-8") == "x = 1\n"
        with pytest.raises(ValueError, match="no shelf entry"):
            agent.drop_stash("wip")

    def test_gate_off_refuses_but_the_shelf_stays_readable(
            self, agent, tmp_path):
        _seed(agent, tmp_path)
        agent.shelve_stash("wip")
        agent.set_stash_shelf(False)
        status = agent.stash_shelf_status()
        assert status["enabled"] is False
        assert status["names"] == ["wip"]
        (tmp_path / "src" / "app.py").write_text("x = 7\n",
                                                encoding="utf-8")
        with pytest.raises(ValueError, match="stash shelf is off"):
            agent.shelve_stash("more")
        with pytest.raises(ValueError, match="stash shelf is off"):
            agent.restore_stash("wip")

    def test_torn_journal_line_is_counted_not_hidden(
            self, agent, tmp_path):
        _seed(agent, tmp_path)
        agent.shelve_stash("wip")
        journal = agent._stash_shelf_dir() / "shelf.journal"
        with journal.open("a", encoding="utf-8") as handle:
            handle.write('{"record": {"name": "tor')
        status = agent.stash_shelf_status()
        assert status["corrupt_lines"] == 1
        assert status["names"] == ["wip"]


class TestTerminalSurface:
    def test_show_and_set(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/stash")
        assert "The stash shelf (M-088)" in text
        assert "Setting: on (stash_shelf)" in text
        assert "The stash shelf is empty." in text
        _, _, text = _slash(agent, "/stash off")
        assert "The stash shelf is now off." in text
        assert agent.config["stash_shelf"] is False
        _, _, text = _slash(agent, "/stash on")
        assert "The stash shelf is now on." in text

    def test_shelve_restore_and_drop_via_the_terminal(
            self, agent, tmp_path):
        from mythic_agent.terminal import _slash

        _seed(agent, tmp_path)
        _, _, text = _slash(agent, "/stash shelve half-done fix")
        assert "Shelved 'half-done fix'" in text
        assert (tmp_path / "src" / "app.py").read_text(
            encoding="utf-8") == "x = 1\n"
        _, _, text = _slash(agent, "/stash")
        assert "half-done fix" in text
        _, _, text = _slash(agent, "/stash restore half-done fix")
        assert "Restored 'half-done fix'" in text
        assert (tmp_path / "src" / "app.py").read_text(
            encoding="utf-8") == "x = 2\n"
        _seed(agent, tmp_path)
        agent.shelve_stash("second")
        _, _, text = _slash(agent, "/stash drop second")
        assert "Dropped 'second'" in text

    def test_usage_error_is_the_message(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/stash frobnicate")
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


class TestStashCommand:
    def test_show_is_default(self, handler, agent):
        handler._handle_stash("")
        assert "The stash shelf (M-088)" in _published_text(handler)

    def test_set_via_the_handler(self, handler, agent):
        handler._handle_stash("off")
        assert "The stash shelf is now off." in _published_text(handler)
        assert agent.config["stash_shelf"] is False

    def test_shelve_via_the_handler(self, handler, agent, tmp_path):
        _seed(agent, tmp_path)
        handler._handle_stash("shelve wip")
        assert "Shelved 'wip'" in _published_text(handler)
        assert (tmp_path / "src" / "app.py").read_text(
            encoding="utf-8") == "x = 1\n"

    def test_usage_error_is_published(self, handler, agent):
        handler._handle_stash("frobnicate")
        assert "usage" in _published_text(handler)


class TestChatScreenRouting:
    def test_stash_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/stash off", _FakeLog())
        assert calls == [("/stash", "off")]
