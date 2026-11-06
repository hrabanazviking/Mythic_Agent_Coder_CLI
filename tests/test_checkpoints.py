"""M-075 — Named checkpoints (Checkpoints v2).

TIER: integration

Covers the M-075 surface:

* the pure layer + store (``mythic_agent.core.checkpoints``):
  a working tree captured as a manifest over a content-
  addressed blob store (files with their modes, symlinks
  as links, cache/VCS directories out of scope), named
  checkpoints forming a tree (each hangs from the head
  it was taken under), session state captured as judged
  data,
* the roadmap's own law, proven: restore is one command;
  a dirty tree (changed since the last take or restore)
  refuses and names the changed files, with the remedy;
  ``discard`` throws the un-checkpointed changes away on
  purpose and counts them; restoring an older checkpoint
  and taking a new one from there grows a branch, and
  the journal view shows the whole tree; a checkpoint is
  whole or refused (oversize file, missing blob),
* ``Agent``: the gate status, ``set_checkpoints``
  journaled as ``checkpoints_setting_changed`` (a failed
  save restoring the previous value and journaling the
  revert), ``take_checkpoint`` capturing the attached
  session's state and journaling ``checkpoint_created``,
  ``restore_checkpoint`` restoring tree + session into
  its own session only, journaling ``checkpoint_restored``
  with its counts; the gate off refuses and says so,
* the surfaces: the terminal ``/checkpoint`` and the TUI
  ``/checkpoint`` (system-command road through the
  CommandHandler + chat-screen routing), which share the
  parser and formatters,
* the config contract: ``checkpoints`` ships in the
  defaults (True). Its M-009 catalogue entry (S-64) is a
  coordinator integration delta in the Hammer campaign
  and lands with the banking regen, so it is not asserted
  here.
"""

from __future__ import annotations

import os

import pytest

from mythic_agent.core import checkpoints
from mythic_agent.core.checkpoints import (
    CHECKPOINTS_SLICE,
    PLAIN_EXPLANATION,
    SETTING_KEY,
    CheckpointStore,
    capture_manifest,
    diff_manifests,
    enabled_from_config,
    format_checkpoint_created,
    format_checkpoint_restored,
    format_checkpoint_tree,
    format_checkpoints,
    format_setting_change,
    parse_checkpoint_args,
    set_enabled,
    tree_hash,
    validate_name,
    validate_session_snapshot,
)
from mythic_agent.core.config_manager import config_manager
from mythic_agent.core.sessions import SessionStore


def write(root, relative, text):
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return target


@pytest.fixture()
def ws(tmp_path, monkeypatch):
    root = tmp_path / "ws"
    root.mkdir()
    monkeypatch.setattr(config_manager, "MYTHIC_DIR",
                        tmp_path / "state")
    return root


@pytest.fixture()
def live_agent(agent, tmp_path, monkeypatch):
    """The conftest agent, with MYTHIC_DIR outside the tree.

    The conftest fixture parks the state dir inside the
    workspace; a checkpoint of that workspace would try
    to freeze its own store, so the state moves out —
    the production shape (``~/.mythic`` vs the project).
    """
    from mythic_agent.agents import llm

    state = tmp_path.parent / (tmp_path.name + "-mythic")
    monkeypatch.setattr(llm.config_manager, "MYTHIC_DIR", state)
    agent._m075_state = state
    return agent


def store_for(tmp_path, workspace=None):
    state = getattr(workspace, "_m075_state", None)
    return SessionStore(workspace or tmp_path,
                        state or tmp_path / "state")


class TestPureData:
    def test_constants(self):
        assert CHECKPOINTS_SLICE == "M-075"
        assert SETTING_KEY == "checkpoints"
        assert "one command" in PLAIN_EXPLANATION
        assert "discard" in PLAIN_EXPLANATION

    def test_validate_name_keeps_the_users_words(self):
        assert validate_name("  before the auth rework  ") == \
            "before the auth rework"
        with pytest.raises(ValueError, match="needs a name"):
            validate_name("   ")
        with pytest.raises(ValueError, match="at most"):
            validate_name("x" * 81)
        with pytest.raises(ValueError, match="control"):
            validate_name("bad\tname")

    def test_validate_session_snapshot(self):
        assert validate_session_snapshot(None) is None
        good = {"session_id": "s1", "status": "idle",
                "total_tokens": 3,
                "messages": [{"role": "user", "content": "hi"}],
                "outcome": None}
        assert validate_session_snapshot(good)["session_id"] == "s1"
        with pytest.raises(ValueError, match="session id"):
            validate_session_snapshot({"status": "idle"})
        with pytest.raises(ValueError, match="token count"):
            validate_session_snapshot(
                {"session_id": "s1", "status": "idle",
                 "total_tokens": True, "messages": []})
        with pytest.raises(ValueError, match="messages"):
            validate_session_snapshot(
                {"session_id": "s1", "status": "idle",
                 "total_tokens": 0, "messages": "nope"})

    def test_capture_manifest_files_links_and_scope(self, ws):
        write(ws, "app.py", "alpha = 1\n")
        write(ws, "pkg/mod.py", "beta = 2\n")
        write(ws, ".git/config", "[core]\n")
        write(ws, "__pycache__/app.cpython.pyc", "bytes")
        os.symlink("app.py", ws / "alias.py")
        manifest = capture_manifest(ws)
        assert manifest["app.py"]["kind"] == "file"
        assert manifest["pkg/mod.py"]["size"] == 9
        assert manifest["alias.py"] == {
            "kind": "link", "target": "app.py"}
        assert ".git/config" not in manifest
        assert not any("__pycache__" in path for path in manifest)

    def test_capture_refuses_an_oversize_file(self, ws, monkeypatch):
        monkeypatch.setattr(checkpoints, "MAX_FILE_BYTES", 4)
        write(ws, "big.txt", "12345")
        with pytest.raises(ValueError, match="over the"):
            capture_manifest(ws)

    def test_tree_hash_and_diff(self, ws):
        write(ws, "a.txt", "one")
        write(ws, "b.txt", "two")
        first = capture_manifest(ws)
        assert tree_hash(first) == tree_hash(capture_manifest(ws))
        write(ws, "a.txt", "one!")
        write(ws, "c.txt", "three")
        (ws / "b.txt").unlink()
        second = capture_manifest(ws)
        assert tree_hash(first) != tree_hash(second)
        diff = diff_manifests(first, second)
        assert diff == {"added": ["c.txt"],
                        "modified": ["a.txt"],
                        "deleted": ["b.txt"]}


class TestStore:
    def test_take_list_get_and_head(self, ws):
        write(ws, "app.py", "alpha = 1\n")
        store = CheckpointStore(ws)
        first = store.create("before the auth rework")
        assert first.parent_id is None and first.file_count == 1
        write(ws, "app.py", "alpha = 2\n")
        second = store.create("auth rework done")
        assert second.parent_id == first.id
        assert second.parent_name == "before the auth rework"
        assert store.head().name == "auth rework done"
        assert [c.name for c in store.list_checkpoints()] == [
            "before the auth rework", "auth rework done"]
        assert store.get("before the auth rework").id == first.id
        with pytest.raises(ValueError, match="no checkpoint named"):
            store.get("nope")

    def test_a_name_is_unique(self, ws):
        store = CheckpointStore(ws)
        store.create("freeze")
        with pytest.raises(ValueError, match="already exists"):
            store.create("freeze")

    def test_identical_files_share_one_blob(self, ws):
        write(ws, "a.txt", "same")
        write(ws, "b.txt", "same")
        CheckpointStore(ws).create("freeze")
        blobs = list((config_manager.MYTHIC_DIR / "checkpoints")
                     .rglob("*") )
        blob_files = [p for p in blobs if p.is_file()
                      and p.parent.name == "blobs"]
        assert len(blob_files) == 1

    def test_session_state_is_stored_as_data(self, ws):
        snapshot = {"session_id": "s1", "status": "idle",
                    "total_tokens": 0, "messages": [],
                    "outcome": None}
        store = CheckpointStore(ws)
        checkpoint = store.create("with session", snapshot)
        assert checkpoint.session_id == "s1"
        assert store.get("with session").session == snapshot

    def test_restore_brings_the_tree_back_in_one_command(self, ws):
        write(ws, "app.py", "alpha = 1\n")
        write(ws, "gone.txt", "still here")
        store = CheckpointStore(ws)
        store.create("base")
        write(ws, "app.py", "alpha = 2\n")
        (ws / "gone.txt").unlink()
        write(ws, "new.txt", "added later")
        store.create("changed")
        checkpoint, outcome = store.restore("base")
        assert (ws / "app.py").read_text(encoding="utf-8") == \
            "alpha = 1\n"
        assert (ws / "gone.txt").read_text(encoding="utf-8") == \
            "still here"
        assert not (ws / "new.txt").exists()
        assert outcome.restored == 2 and outcome.removed == 1
        assert outcome.discarded_changes == 0
        assert store.head().name == "base"

    def test_restore_keeps_file_modes(self, ws):
        target = write(ws, "run.sh", "#!/bin/sh\n")
        os.chmod(target, 0o755)
        store = CheckpointStore(ws)
        store.create("base")
        os.chmod(target, 0o644)
        store.create("changed")
        store.restore("base")
        assert os.stat(target).st_mode & 0o777 == 0o755

    def test_dirty_tree_refuses_and_names_the_files(self, ws):
        write(ws, "app.py", "alpha = 1\n")
        store = CheckpointStore(ws)
        store.create("base")
        write(ws, "app.py", "alpha = 2\n")
        with pytest.raises(ValueError, match="un-checkpointed") as err:
            store.restore("base")
        assert "app.py" in str(err.value)
        assert "discard" in str(err.value)
        assert (ws / "app.py").read_text(encoding="utf-8") == \
            "alpha = 2\n"

    def test_discard_restores_and_counts_the_loss(self, ws):
        write(ws, "app.py", "alpha = 1\n")
        store = CheckpointStore(ws)
        store.create("base")
        write(ws, "app.py", "alpha = 2\n")
        write(ws, "extra.txt", "un-checkpointed")
        checkpoint, outcome = store.restore("base", discard=True)
        assert outcome.discarded_changes == 2
        assert (ws / "app.py").read_text(encoding="utf-8") == \
            "alpha = 1\n"
        assert not (ws / "extra.txt").exists()

    def test_a_missing_blob_refuses_before_anything_moves(self, ws):
        write(ws, "app.py", "alpha = 1\n")
        store = CheckpointStore(ws)
        store.create("base")
        write(ws, "app.py", "alpha = 2\n")
        store.create("changed")
        for blob in store.blobs.iterdir():
            blob.unlink()
        with pytest.raises(ValueError, match="damaged"):
            store.restore("base")
        assert (ws / "app.py").read_text(encoding="utf-8") == \
            "alpha = 2\n"

    def test_taking_from_a_restored_checkpoint_grows_a_branch(
            self, ws):
        write(ws, "app.py", "one")
        store = CheckpointStore(ws)
        base = store.create("base")
        write(ws, "app.py", "two")
        store.create("main road")
        store.restore("base")
        write(ws, "app.py", "three")
        branch = store.create("other road")
        assert branch.parent_id == base.id
        tree = format_checkpoint_tree(store.list_checkpoints(),
                                      store.head().id)
        assert "base" in tree and "main road" in tree
        assert "other road" in tree and "*" in tree


class TestGateParserFormatters:
    def test_enabled_from_config(self):
        assert enabled_from_config({}) is True
        assert enabled_from_config({"checkpoints": False}) is False
        with pytest.raises(ValueError, match="true or false"):
            enabled_from_config({"checkpoints": "yes"})

    def test_set_enabled(self):
        value, change = set_enabled({}, False)
        assert value is False and change.before is True
        with pytest.raises(ValueError, match="already on"):
            set_enabled({}, True)
        with pytest.raises(ValueError, match="on or off"):
            set_enabled({}, "off")

    def test_parse_args(self):
        assert parse_checkpoint_args("") == {"action": "show"}
        assert parse_checkpoint_args("tree") == {"action": "show"}
        assert parse_checkpoint_args("on") == {
            "action": "setting", "enabled": True}
        assert parse_checkpoint_args("off") == {
            "action": "setting", "enabled": False}
        assert parse_checkpoint_args(
            "take before the auth rework") == {
            "action": "take", "name": "before the auth rework"}
        assert parse_checkpoint_args("restore base") == {
            "action": "restore", "name": "base", "discard": False}
        assert parse_checkpoint_args("restore base discard") == {
            "action": "restore", "name": "base", "discard": True}
        with pytest.raises(ValueError, match="Usage"):
            parse_checkpoint_args("sideways")
        with pytest.raises(ValueError, match="Usage"):
            parse_checkpoint_args("restore")

    def test_format_checkpoints_shows_gate_tree_and_usage(self, ws):
        store = CheckpointStore(ws)
        empty = format_checkpoints({}, [], None)
        assert "Named checkpoints (M-075)" in empty
        assert "No checkpoints yet" in empty
        write(ws, "app.py", "alpha = 1\n")
        store.create("base")
        text = format_checkpoints({}, store.list_checkpoints(),
                                   store.head().id)
        assert "Setting: on (checkpoints)" in text
        assert "base" in text and "Usage: /checkpoint" in text

    def test_format_setting_change(self):
        record = {"from": True, "to": False}
        assert format_setting_change(record) == \
            "Checkpoints: on -> off."

    def test_format_created_and_restored(self):
        created = format_checkpoint_created(
            {"name": "base", "parent_name": None, "files": 3,
             "bytes": 42, "session_captured": True})
        assert "'base' taken" in created
        assert "Session state captured" in created
        restored = format_checkpoint_restored(
            {"name": "base", "restored": 2, "removed": 1,
             "unchanged": 4, "discarded_changes": 1,
             "session_restored": True})
        assert "2 file(s) written back" in restored
        assert "discarded" in restored
        assert "Session state restored" in restored


class TestAgentGate:
    def test_status(self, live_agent):
        status = live_agent.checkpoint_status()
        assert status["enabled"] is True
        assert status["explanation"] == PLAIN_EXPLANATION
        assert status["count"] == 0 and status["head"] is None

    def test_set_without_session(self, live_agent):
        record = live_agent.set_checkpoints(False)
        assert record["journaled"] is False
        assert live_agent.config["checkpoints"] is False
        with pytest.raises(ValueError, match="already off"):
            live_agent.set_checkpoints(False)

    def test_set_journals_on_the_session(self, live_agent, tmp_path):
        store = SessionStore(tmp_path, live_agent._m075_state)
        session_id = live_agent.attach_session(store)
        live_agent.set_checkpoints(False)
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "checkpoints_setting_changed" in types
        live_agent.close()

    def test_save_failure_restores_and_journals_the_revert(
            self, live_agent, tmp_path, monkeypatch):
        from mythic_agent.agents import llm

        store = SessionStore(tmp_path, live_agent._m075_state)
        session_id = live_agent.attach_session(store)
        monkeypatch.setattr(llm.config_manager, "save_config",
                            lambda config: False)
        with pytest.raises(RuntimeError, match="could not be saved"):
            live_agent.set_checkpoints(False)
        assert live_agent.config.get("checkpoints") is not False
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert types[-2:] == ["checkpoints_setting_changed",
                              "checkpoints_setting_reverted"]
        live_agent.close()


class TestAgentCheckpoints:
    def test_take_and_restore_with_the_session(
            self, live_agent, tmp_path):
        target = write(tmp_path, "app.py", "alpha = 1\n")
        store = SessionStore(tmp_path, live_agent._m075_state)
        session_id = live_agent.attach_session(store)
        live_agent.add_context("first words")
        record = live_agent.take_checkpoint("before the auth rework")
        assert record["session_captured"] is True
        assert record["journaled"] is True
        target.write_text("alpha = 2\n", encoding="utf-8")
        live_agent.add_context("second words")
        live_agent.take_checkpoint("auth rework done")
        restored = live_agent.restore_checkpoint(
            "before the auth rework")
        assert target.read_text(encoding="utf-8") == "alpha = 1\n"
        assert restored["session_restored"] is True
        contents = [m.get("content") for m in live_agent.messages]
        assert "first words" in contents
        assert "second words" not in contents
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "checkpoint_created" in types
        assert "checkpoint_restored" in types
        live_agent.close()

    def test_dirty_tree_refuses_through_the_agent(
            self, live_agent, tmp_path):
        target = write(tmp_path, "app.py", "alpha = 1\n")
        live_agent.take_checkpoint("base")
        target.write_text("alpha = 2\n", encoding="utf-8")
        with pytest.raises(ValueError, match="un-checkpointed"):
            live_agent.restore_checkpoint("base")
        record = live_agent.restore_checkpoint("base", discard=True)
        assert record["discarded_changes"] == 1
        assert target.read_text(encoding="utf-8") == "alpha = 1\n"

    def test_gate_off_refuses_and_says_so(self, live_agent, tmp_path):
        write(tmp_path, "app.py", "alpha = 1\n")
        live_agent.set_checkpoints(False)
        with pytest.raises(ValueError, match="checkpoints are off"):
            live_agent.take_checkpoint("base")
        with pytest.raises(ValueError, match="checkpoints are off"):
            live_agent.restore_checkpoint("base")

    def test_session_state_stays_with_its_own_session(
            self, live_agent, tmp_path):
        target = write(tmp_path, "app.py", "alpha = 1\n")
        snapshot = {"session_id": "someone-elses-session",
                    "status": "idle", "total_tokens": 0,
                    "messages": [{"role": "user",
                                  "content": "not yours"}],
                    "outcome": None}
        CheckpointStore(tmp_path).create("foreign", snapshot)
        store = SessionStore(tmp_path, live_agent._m075_state)
        session_id = live_agent.attach_session(store)
        target.write_text("alpha = 2\n", encoding="utf-8")
        CheckpointStore(tmp_path).create("current")
        record = live_agent.restore_checkpoint("foreign")
        assert record["session_restored"] is False
        assert "someone-elses-session" in record["session_note"]
        assert target.read_text(encoding="utf-8") == "alpha = 1\n"
        contents = [m.get("content") for m in live_agent.messages]
        assert "not yours" not in contents
        live_agent.close()


class TestTerminalSurface:
    def test_show_and_set(self, live_agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(live_agent, "/checkpoint")
        assert "Named checkpoints (M-075)" in text
        _, _, text = _slash(live_agent, "/checkpoint off")
        assert "on -> off" in text
        assert live_agent.config["checkpoints"] is False
        _, _, text = _slash(live_agent, "/checkpoint on")
        assert "off -> on" in text

    def test_take_and_restore(self, live_agent, tmp_path):
        from mythic_agent.terminal import _slash

        target = write(tmp_path, "app.py", "alpha = 1\n")
        _, _, text = _slash(
            live_agent, "/checkpoint take before the auth rework")
        assert "taken" in text
        target.write_text("alpha = 2\n", encoding="utf-8")
        _, _, text = _slash(live_agent, "/checkpoint restore "
                            "before the auth rework discard")
        assert "restored" in text
        assert target.read_text(encoding="utf-8") == "alpha = 1\n"

    def test_usage_error_is_the_message(self, live_agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(live_agent, "/checkpoint sideways")
        assert "Usage" in text


@pytest.fixture()
def handler(live_agent, monkeypatch):
    from mythic_agent.agents import command_handler as handler_module
    from mythic_agent.agents.command_handler import CommandHandler
    from mythic_agent.agents.llm import AGENT_REGISTRY

    published = []
    monkeypatch.setattr(
        handler_module, "publish_sync",
        lambda event, **kwargs: published.append((event, kwargs)))
    AGENT_REGISTRY["Primary"] = live_agent
    instance = CommandHandler.__new__(CommandHandler)
    instance.published = published
    yield instance
    AGENT_REGISTRY.pop("Primary", None)


def _published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestCheckpointCommand:
    def test_show_is_default(self, handler, live_agent):
        handler._handle_checkpoint("")
        assert "Named checkpoints (M-075)" in _published_text(handler)

    def test_take_via_the_handler(self, handler, live_agent, tmp_path):
        write(tmp_path, "app.py", "alpha = 1\n")
        handler._handle_checkpoint("take base")
        assert "taken" in _published_text(handler)
        assert live_agent.checkpoint_status()["count"] == 1

    def test_usage_error_is_published(self, handler, live_agent):
        handler._handle_checkpoint("sideways")
        assert "Usage" in _published_text(handler)


class TestChatScreenRouting:
    def test_checkpoint_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/checkpoint take base", _FakeLog())
        assert calls == [("/checkpoint", "take base")]


class TestConfigContract:
    def test_defaults_ship_on(self):
        import yaml
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        defaults = yaml.safe_load(
            (root / "mythic_agent/data/config_defaults.yaml")
            .read_text(encoding="utf-8"))
        assert defaults["checkpoints"] is True
