"""M-076 — Session branching.

TIER: integration

Covers the M-076 surface:

* the pure layer (``mythic_agent.core.session_branching``):
  a fork context is the parent's history up to and
  including the fork message, deep-copied; lineage is
  recorded and read back honestly (root + depth for a
  branch of a branch); two contexts compare by their
  true shared prefix, their first divergence, and each
  side's own messages after it,
* the roadmap's own law, proven: branches share history
  literally, diverge honestly (a checkpoint on one never
  touches the other; a comparison names the divergence),
  and can be compared — including the honest edge cases
  (identical sessions; one session simply continuing the
  shared road, which is no divergence yet),
* ``SessionStore.branch`` / ``branches_of``: a branch is
  an ordinary v1 session (the M-010 golden readers are
  untouched; lineage rides in metadata only), forked
  through the store's own create/checkpoint road,
  journaled as ``session_branched``, released so it can
  be resumed, and the parent is only ever read,
* ``Agent``: the gate status, ``set_session_branching``
  journaled (a failed save restoring the previous value
  and journaling the revert), ``fork_session`` /
  ``compare_sessions`` / ``list_session_branches``; the
  gate off refuses a fork and says so,
* the surfaces: the terminal ``/branch`` and the TUI
  ``/branch`` (system-command road through the
  CommandHandler + chat-screen routing), which share the
  parser and formatters,
* the config contract: ``session_branching`` ships in
  the defaults (True). Its M-009 catalogue entry (S-64)
  is a coordinator integration delta recorded in
  TEAM_LOG.md — the catalogue file is a shared inventory
  surface this team does not edit.
"""

from __future__ import annotations

import copy

import pytest

from mythic_agent.core.session_branching import (
    PLAIN_EXPLANATION,
    SESSION_BRANCHING_SLICE,
    SETTING_KEY,
    branch_info,
    branch_metadata,
    children_of,
    compare_contexts,
    enabled_from_config,
    fork_context,
    format_branch_list,
    format_branching,
    format_comparison,
    format_fork,
    format_setting_change,
    parse_branch_args,
    set_enabled,
    shared_prefix_length,
)
from mythic_agent.core.sessions import (
    SessionStore,
    session_from_dict,
    session_to_dict,
)

MESSAGES = [
    {"role": "system", "content": "You are Mythic."},
    {"role": "user", "content": "Rework the auth module."},
    {"role": "assistant", "content": "Road A: patch it in place."},
    {"role": "user", "content": "Go on."},
    {"role": "assistant", "content": "Road A continues."},
]


def store_for(tmp_path, workspace=None):
    return SessionStore(workspace or tmp_path, tmp_path / "state")


class TestForkContext:
    def test_slice_and_setting_constants(self):
        assert SESSION_BRANCHING_SLICE == "M-076"
        assert SETTING_KEY == "session_branching"
        assert "try the other road" in PLAIN_EXPLANATION

    def test_fork_keeps_up_to_and_including_the_fork_message(self):
        forked = fork_context(MESSAGES, 2)
        assert forked == MESSAGES[:3]
        assert fork_context(MESSAGES, 0) == MESSAGES[:1]
        assert fork_context(MESSAGES, 4) == MESSAGES

    def test_fork_is_a_deep_copy(self):
        messages = copy.deepcopy(MESSAGES)
        forked = fork_context(messages, 2)
        forked[1]["content"] = "changed on the branch"
        assert messages[1]["content"] == "Rework the auth module."

    def test_fork_refuses_an_index_outside_the_session(self):
        with pytest.raises(ValueError, match="no message 5"):
            fork_context(MESSAGES, 5)
        with pytest.raises(ValueError, match="no message -1"):
            fork_context(MESSAGES, -1)

    def test_fork_refuses_a_non_integer_index(self):
        with pytest.raises(ValueError, match="whole"):
            fork_context(MESSAGES, "2")
        with pytest.raises(ValueError, match="whole"):
            fork_context(MESSAGES, True)

    def test_fork_refuses_an_empty_session(self):
        with pytest.raises(ValueError, match="at least one"):
            fork_context([], 0)

    def test_fork_refuses_a_broken_prefix(self):
        broken = [{"role": "system", "content": "s"},
                  {"role": "tool", "tool_call_id": "x",
                   "content": "orphan result"}]
        with pytest.raises(ValueError, match="broken history"):
            fork_context(broken, 1)


class TestCompare:
    def test_shared_prefix_counts_whole_messages(self):
        other = copy.deepcopy(MESSAGES)
        other[3] = {"role": "user", "content": "Other road."}
        assert shared_prefix_length(MESSAGES, other) == 3
        assert shared_prefix_length(MESSAGES, MESSAGES) == 5

    def test_identical_sessions(self):
        result = compare_contexts(MESSAGES, copy.deepcopy(MESSAGES))
        assert result.identical is True
        assert result.diverged_at is None and result.shared == 5
        assert result.first_only == () and result.second_only == ()

    def test_divergence_is_named_with_each_side(self):
        branch = fork_context(MESSAGES, 2) + [
            {"role": "user", "content": "Try the other road."}]
        result = compare_contexts(MESSAGES, branch)
        assert result.shared == 3 and result.diverged_at == 3
        assert [m["content"] for m in result.first_only] == [
            "Go on.", "Road A continues."]
        assert [m["content"] for m in result.second_only] == [
            "Try the other road."]
        record = result.record("a" * 32, "b" * 32)
        assert record["type"] == "session_branch_compared"
        assert record["first_only"] == 2 and record["second_only"] == 1
        assert record["identical"] is False

    def test_a_continuation_is_no_divergence_yet(self):
        result = compare_contexts(MESSAGES, MESSAGES[:3])
        assert result.diverged_at is None
        assert result.identical is False
        assert result.shared == 3 and len(result.first_only) == 2

    def test_compare_refuses_non_lists(self):
        with pytest.raises(ValueError, match="two message lists"):
            compare_contexts("nope", MESSAGES)


class TestLineage:
    def test_metadata_records_parent_fork_and_root(self):
        info = branch_metadata("a" * 32, 2, MESSAGES[2],
                               name="  the other road  ")
        assert info["parent_session_id"] == "a" * 32
        assert info["fork_index"] == 2 and info["fork_role"] == "assistant"
        assert info["branch_name"] == "the other road"
        assert info["root_session_id"] == "a" * 32 and info["depth"] == 1
        assert branch_info({"branch": info}) == info

    def test_a_branch_of_a_branch_keeps_the_root(self):
        parent = branch_metadata("a" * 32, 2, MESSAGES[2])
        child = branch_metadata("b" * 32, 1, MESSAGES[1],
                                parent_branch=parent)
        assert child["root_session_id"] == "a" * 32
        assert child["depth"] == 2

    def test_no_lineage_is_the_honest_answer_for_a_plain_session(self):
        assert branch_info({}) is None
        assert branch_info({"agent_name": "Primary"}) is None

    def test_malformed_lineage_raises(self):
        partial = branch_metadata("a" * 32, 2, MESSAGES[2])
        del partial["depth"]
        with pytest.raises(ValueError, match="missing 'depth'"):
            branch_info({"branch": partial})
        info = branch_metadata("a" * 32, 2, MESSAGES[2])
        info["depth"] = 0
        with pytest.raises(ValueError, match="'depth'"):
            branch_info({"branch": info})
        with pytest.raises(ValueError, match="branch lineage"):
            branch_metadata("not-an-id", 2, MESSAGES[2])
        with pytest.raises(ValueError, match="must be words"):
            branch_metadata("a" * 32, 2, MESSAGES[2], name="  ")

    def test_children_of_picks_direct_children_only(self):
        rows = [
            {"id": "b" * 32, "created_at": "t", "status": "idle",
             "metadata": {"branch": branch_metadata(
                 "a" * 32, 2, MESSAGES[2], name="one")}},
            {"id": "c" * 32, "created_at": "t", "status": "idle",
             "metadata": {"branch": branch_metadata(
                 "b" * 32, 1, MESSAGES[1])}},
            {"id": "d" * 32, "created_at": "t", "status": "idle",
             "metadata": {}},
        ]
        children = children_of("a" * 32, rows)
        assert [c["session_id"] for c in children] == ["b" * 32]
        assert children[0]["branch_name"] == "one"
        assert children_of("a" * 32, []) == []


class TestStoreBranch:
    def test_branch_shares_history_and_records_lineage(self, tmp_path):
        store = store_for(tmp_path)
        parent_id = store.create(copy.deepcopy(MESSAGES),
                                 {"agent_name": "Primary"})
        branch_id = store.branch(parent_id, 2, name="the other road")
        branch = store.load(branch_id)
        assert branch["context"] == MESSAGES[:3]
        assert branch["status"] == "idle"
        info = branch_info(branch["metadata"])
        assert info["parent_session_id"] == parent_id
        assert info["fork_index"] == 2 and info["depth"] == 1
        assert info["root_session_id"] == parent_id
        assert branch["metadata"]["agent_name"] == "Primary"
        events = store.export(branch_id)["events"]
        branched = [e for e in events if e["type"] == "session_branched"]
        assert len(branched) == 1
        assert branched[0]["parent_session_id"] == parent_id
        assert branched[0]["shared_messages"] == 3
        store.release(parent_id)

    def test_the_parent_is_only_read(self, tmp_path):
        store = store_for(tmp_path)
        parent_id = store.create(copy.deepcopy(MESSAGES), {})
        before = store.load(parent_id)
        store.branch(parent_id, 2)
        after = store.load(parent_id)
        assert after["context"] == before["context"]
        assert branch_info(after["metadata"]) is None
        types = [e["type"] for e in store.export(parent_id)["events"]]
        assert "session_branched" not in types
        store.release(parent_id)

    def test_a_branch_is_a_plain_v1_session(self, tmp_path):
        store = store_for(tmp_path)
        parent_id = store.create(copy.deepcopy(MESSAGES), {})
        branch_id = store.branch(parent_id, 2)
        record = store.load(branch_id)
        assert record["schema_version"] == 1
        rebuilt = session_from_dict(session_to_dict(record))
        assert rebuilt["context"] == MESSAGES[:3]
        assert store.export(branch_id)["events"]
        store.release(parent_id)

    def test_the_branch_lease_is_released_for_resume(self, tmp_path):
        store = store_for(tmp_path)
        parent_id = store.create(copy.deepcopy(MESSAGES), {})
        branch_id = store.branch(parent_id, 2)
        data = store.resume(branch_id)  # would raise SessionBusy if leased
        assert data["context"] == MESSAGES[:3]
        store.release(branch_id)
        store.release(parent_id)

    def test_branches_diverge_honestly(self, tmp_path):
        store = store_for(tmp_path)
        parent_id = store.create(copy.deepcopy(MESSAGES), {})
        branch_id = store.branch(parent_id, 2)
        store.resume(branch_id)
        branch_context = fork_context(MESSAGES, 2) + [
            {"role": "user", "content": "Try the other road."}]
        store.checkpoint(branch_id, branch_context, "idle", 0)
        store.release(branch_id)
        parent_context = copy.deepcopy(MESSAGES) + [
            {"role": "user", "content": "And then?"}]
        store.checkpoint(parent_id, parent_context, "idle", 0)
        result = compare_contexts(store.load(parent_id)["context"],
                                  store.load(branch_id)["context"])
        assert result.shared == 3 and result.diverged_at == 3
        assert len(result.first_only) == 3 and len(result.second_only) == 1
        # The parent's road never leaked into the branch.
        assert store.load(branch_id)["context"] == branch_context
        store.release(parent_id)

    def test_branches_of_and_branching_a_branch(self, tmp_path):
        store = store_for(tmp_path)
        parent_id = store.create(copy.deepcopy(MESSAGES), {})
        branch_id = store.branch(parent_id, 2, name="first")
        child_id = store.branch(branch_id, 1, name="second")
        children = store.branches_of(parent_id)
        assert [c["session_id"] for c in children] == [branch_id]
        grandchildren = store.branches_of(branch_id)
        assert [c["session_id"] for c in grandchildren] == [child_id]
        info = branch_info(store.load(child_id)["metadata"])
        assert info["root_session_id"] == parent_id and info["depth"] == 2
        store.release(parent_id)

    def test_branch_refuses_a_bad_fork(self, tmp_path):
        store = store_for(tmp_path)
        parent_id = store.create(copy.deepcopy(MESSAGES), {})
        with pytest.raises(ValueError, match="no message 9"):
            store.branch(parent_id, 9)
        with pytest.raises(ValueError, match="not found"):
            store.branch("f" * 32, 1)
        assert store.branches_of(parent_id) == []
        store.release(parent_id)


class TestGateAndSurface:
    def test_gate_defaults_on_and_validates(self):
        assert enabled_from_config({}) is True
        assert enabled_from_config({"session_branching": False}) is False
        with pytest.raises(ValueError, match="true or false"):
            enabled_from_config({"session_branching": "yes"})

    def test_set_enabled(self):
        value, change = set_enabled({}, False)
        assert value is False and change.before is True
        with pytest.raises(ValueError, match="already on"):
            set_enabled({}, True)
        with pytest.raises(ValueError, match="on or off"):
            set_enabled({}, "off")

    def test_parse_args(self):
        assert parse_branch_args("") == {"action": "show"}
        assert parse_branch_args("on") == {
            "action": "setting", "enabled": True}
        assert parse_branch_args("off") == {
            "action": "setting", "enabled": False}
        assert parse_branch_args("list") == {"action": "list"}
        assert parse_branch_args("fork 2") == {
            "action": "fork", "at_index": 2, "name": None}
        assert parse_branch_args("fork 2 the other road") == {
            "action": "fork", "at_index": 2, "name": "the other road"}
        assert parse_branch_args(
            "compare " + "a" * 32 + " " + "b" * 32) == {
            "action": "compare", "first_id": "a" * 32,
            "second_id": "b" * 32}
        with pytest.raises(ValueError, match="Usage"):
            parse_branch_args("sideways")
        with pytest.raises(ValueError, match="Usage"):
            parse_branch_args("fork")
        with pytest.raises(ValueError, match="whole"):
            parse_branch_args("fork two")
        with pytest.raises(ValueError, match="hexadecimal"):
            parse_branch_args("compare nope " + "b" * 32)

    def test_format_branching_shows_the_worked_example(self):
        text = format_branching({})
        assert "Session branching (M-076)" in text
        assert "Setting: on (session_branching)" in text
        assert "diverge at message 3" in text
        assert "Usage: /branch" in text

    def test_format_fork_comparison_and_list(self):
        record = {"parent_session_id": "a" * 32,
                  "branch_session_id": "b" * 32, "fork_index": 2,
                  "branch_name": "the other road",
                  "shared_messages": 3}
        text = format_fork(record)
        assert "b" * 32 in text and "shares the first 3" in text
        comparison = compare_contexts(MESSAGES, MESSAGES[:3]).record(
            "a" * 32, "b" * 32)
        text = format_comparison(comparison)
        assert "no divergence yet" in text
        listing = {"parent_session_id": "a" * 32, "branches": [{
            "session_id": "b" * 32, "branch_name": None,
            "fork_index": 2, "fork_role": "assistant", "depth": 1,
            "status": "idle"}]}
        text = format_branch_list(listing)
        assert "Branches of " + "a" * 32 + ": 1" in text
        assert "forked at message 2" in text
        empty = format_branch_list(
            {"parent_session_id": "a" * 32, "branches": []})
        assert "none yet" in empty

    def test_format_setting_change(self):
        record = {"from": True, "to": False}
        assert format_setting_change(record) == (
            "Session branching: on -> off.")


def _grow(agent):
    agent._append_message({"role": "user", "content": "Rework auth."})
    agent._append_message(
        {"role": "assistant", "content": "Road A: patch it."})
    agent._append_message({"role": "user", "content": "Go on."})


class TestAgentGate:
    def test_status(self, agent):
        status = agent.session_branching_status()
        assert status["enabled"] is True
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_set_without_session(self, agent):
        record = agent.set_session_branching(False)
        assert record["journaled"] is False
        assert agent.config["session_branching"] is False
        with pytest.raises(ValueError, match="already off"):
            agent.set_session_branching(False)

    def test_set_journals_on_the_session(self, agent, tmp_path):
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        agent.set_session_branching(False)
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "session_branching_setting_changed" in types
        agent.close()

    def test_save_failure_restores_and_journals_the_revert(
            self, agent, tmp_path, monkeypatch):
        from mythic_agent.agents import llm

        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        monkeypatch.setattr(llm.config_manager, "save_config",
                            lambda config: False)
        with pytest.raises(RuntimeError, match="could not be saved"):
            agent.set_session_branching(False)
        assert agent.config.get("session_branching") is not False
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert types[-2:] == ["session_branching_setting_changed",
                              "session_branching_setting_reverted"]
        agent.close()


class TestAgentBranch:
    def test_fork_without_a_session_refuses(self, agent):
        with pytest.raises(ValueError, match="no session is attached"):
            agent.fork_session(1)

    def test_fork_compare_and_list(self, agent, tmp_path):
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        _grow(agent)
        record = agent.fork_session(2, name="the other road")
        branch_id = record["branch_session_id"]
        assert record["parent_session_id"] == session_id
        assert record["fork_index"] == 2
        assert record["shared_messages"] == 3
        assert record["journaled"] is True
        branch = store.load(branch_id)
        assert branch["context"] == store.load(session_id)["context"][:3]
        assert branch_info(branch["metadata"])["branch_name"] == (
            "the other road")
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "session_branch_forked" in types
        listing = agent.list_session_branches()
        assert listing["count"] == 1
        assert listing["branches"][0]["session_id"] == branch_id
        comparison = agent.compare_sessions(session_id, branch_id)
        assert comparison["shared_messages"] == 3
        assert comparison["diverged_at"] is None
        assert comparison["identical"] is False
        agent.close()

    def test_gate_off_refuses_a_fork_and_creates_nothing(
            self, agent, tmp_path):
        store = store_for(tmp_path)
        agent.attach_session(store)
        _grow(agent)
        agent.set_session_branching(False)
        with pytest.raises(ValueError, match="session branching is off"):
            agent.fork_session(1)
        assert agent.list_session_branches()["count"] == 0
        agent.close()

    def test_compare_and_list_work_with_the_gate_off(
            self, agent, tmp_path):
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        _grow(agent)
        branch_id = agent.fork_session(1)["branch_session_id"]
        agent.set_session_branching(False)
        assert agent.compare_sessions(
            session_id, branch_id)["shared_messages"] == 2
        assert agent.list_session_branches()["count"] == 1
        agent.close()


class TestTerminalSurface:
    def test_show_and_set(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/branch")
        assert "Session branching (M-076)" in text
        _, _, text = _slash(agent, "/branch off")
        assert "on -> off" in text
        assert agent.config["session_branching"] is False
        _, _, text = _slash(agent, "/branch on")
        assert "off -> on" in text

    def test_fork_list_and_compare(self, agent, tmp_path):
        from mythic_agent.terminal import _slash

        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        _grow(agent)
        _, _, text = _slash(agent, "/branch fork 2 other road")
        assert "Branched session" in text and "shares the first 3" in text
        branch_id = agent.list_session_branches()["branches"][0][
            "session_id"]
        _, _, text = _slash(agent, "/branch list")
        assert branch_id in text
        _, _, text = _slash(
            agent, f"/branch compare {session_id} {branch_id}")
        assert "shared history: 3" in text
        agent.close()

    def test_usage_error_is_the_message(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/branch sideways")
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


class TestBranchCommand:
    def test_show_is_default(self, handler, agent):
        handler._handle_branch("")
        assert "Session branching (M-076)" in _published_text(handler)

    def test_set_via_the_handler(self, handler, agent):
        handler._handle_branch("off")
        assert "on -> off" in _published_text(handler)
        assert agent.config["session_branching"] is False

    def test_fork_via_the_handler(self, handler, agent, tmp_path):
        store = store_for(tmp_path)
        agent.attach_session(store)
        _grow(agent)
        handler._handle_branch("fork 1")
        assert "Branched session" in _published_text(handler)
        assert agent.list_session_branches()["count"] == 1
        agent.close()

    def test_usage_error_is_published(self, handler, agent):
        handler._handle_branch("sideways")
        assert "Usage" in _published_text(handler)


class TestChatScreenRouting:
    def test_branch_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/branch list", _FakeLog())
        assert calls == [("/branch", "list")]


class TestConfigContract:
    def test_defaults_ship_on(self):
        import yaml
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        defaults = yaml.safe_load(
            (root / "mythic_agent/data/config_defaults.yaml")
            .read_text(encoding="utf-8"))
        assert defaults["session_branching"] is True
